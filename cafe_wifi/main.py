from flask import Flask, render_template, redirect, url_for, flash
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask import abort, request
from sqlalchemy.ext.declarative import declarative_base
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from flask_gravatar import Gravatar
from functools import wraps
from forms import CreateCafeForm, LoginForm, RegisterForm, CommentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

ckeditor = CKEditor(app)
Bootstrap(app)
Base = declarative_base()

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


# CONFIGURE TABLE
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(150))
    name = db.Column(db.String(100))
    cafes = relationship('Cafe', back_populates='author')
    assessments = relationship('Assessment', back_populates='assessment_author')
    reviews = relationship('Reviews', back_populates='review_author')


class Cafe(db.Model):
    __tablename__ = 'cafe'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=False, nullable=False)
    location = db.Column(db.String(250), nullable=False)
    map_url = db.Column(db.String(500), nullable=False)
    img_url = db.Column(db.String(500), nullable=False)
    seats = db.Column(db.String(50), nullable=False)
    coffee_price = db.Column(db.String(50), nullable=False)
    has_sockets = db.Column(db.Boolean(), nullable=False)
    has_toilet = db.Column(db.Boolean(), nullable=False)
    has_wifi = db.Column(db.Boolean(), nullable=False)
    can_take_calls = db.Column(db.Boolean(), nullable=False)

    author = relationship('User', back_populates='cafes')
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # # ***************Parent Relationship*************#
    assessments = relationship('Assessment', back_populates='parent_cafe')
    reviews = relationship('Reviews', back_populates='parent_cafe')


class Assessment(db.Model):
    __tablename__ = 'assessment'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    assessment_author = relationship('User', back_populates='assessments')
    # ***************Child Relationship*************#
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafe.id'))
    parent_cafe = relationship('Cafe', back_populates='assessments')
    assessment = db.Column(db.Integer)


class Reviews(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    review_author = relationship('User', back_populates='reviews')
    # ***************Child Relationship*************#
    cafe_id = db.Column(db.Integer, db.ForeignKey('cafe.id'))
    parent_cafe = relationship('Cafe', back_populates='reviews')
    text = db.Column(db.Text, nullable=False)


def average_assessment(index):
    assessments = Assessment.query.filter_by(cafe_id=index)
    sum_assessments = 0
    len_assessments = (len(list(assessments)))
    for assessment in assessments:
        sum_assessments += assessment.assessment
        return round(sum_assessments / len_assessments, 1)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Create admin-only decorator
def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # If id is not 1 then return abort with 403 error
        if current_user.id != 1:
            return abort(403)
        # Otherwise continue with the route function
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    cafe_db = db.session.query(Cafe).all()
    return render_template('index.html', cafe_db=cafe_db, logged_in=current_user.is_authenticated)


@app.route('/post/<int:index>', methods=['GET', 'POST'])
def show_cafe(index):
    comment_form = CommentForm()
    requested_post = Cafe.query.get(index)
    assessment = Assessment.query.filter_by(author_id=current_user.id, cafe_id=index).first()
    if comment_form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to login or register to comment.')
            return redirect(url_for('login'))
        else:
            new_review = Reviews(
                review_author=current_user,
                parent_cafe=requested_post,
                text=comment_form.text.data,
            )
            db.session.add(new_review)
            db.session.commit()
            return redirect(url_for('show_cafe', index=index))

    elif request.method == 'POST':
        if assessment:
            assessment = Assessment.query.filter_by(author_id=current_user.id, cafe_id=index).first()
            assessment.assessment = request.form['rating']
            db.session.commit()

            return redirect(url_for('show_cafe', index=index))

        else:
            new_assessment = Assessment(
                assessment_author=current_user,
                assessment=request.form['rating'],
                parent_cafe=requested_post,
            )
            db.session.add(new_assessment)
            db.session.commit()
            return redirect(url_for('show_cafe', index=index))

    return render_template('show_cafe.html',
                           cafe=requested_post,
                           logged_in=current_user.is_authenticated,
                           comment_form=comment_form,
                           user_rating=assessment,
                           assessment=average_assessment(index),
                           reviews=Reviews.query.filter_by(cafe_id=index).all(),
                           )


@app.route('/new-cafe', methods=['GET', 'POST'])
def add_cafe():
    form = CreateCafeForm()
    if form.validate_on_submit():
        new_cafe = Cafe(
            author=current_user,
            name=form.name.data,
            map_url=form.map_url.data,
            img_url=form.img_url.data,
            location=form.location.data,
            seats=form.seats.data,
            coffee_price=form.coffee_price.data,
            has_sockets=form.has_sockets.data,
            has_toilet=form.has_toilet.data,
            has_wifi=form.has_wifi.data,
            can_take_calls=form.can_take_calls.data,
        )
        db.session.add(new_cafe)
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('add_cafe.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/delete/<int:post_id>')
@admin_only
def delete_cafe(post_id):
    post_to_delete = Cafe.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead!")
            return redirect(url_for('login'))
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('register.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()
        # Email doesn't exist
        if not user:
            flash("That email does not exist, please try again.")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        # Email exists and password correct
        else:
            login_user(user)
            return redirect(url_for('home'))
    return render_template('login.html', form=form, logged_in=current_user.is_authenticated)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
