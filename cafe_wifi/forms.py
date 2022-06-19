from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField


class CreateCafeForm(FlaskForm):
    name = StringField('Cafe name', validators=[DataRequired()])
    map_url = StringField('Map URL', validators=[DataRequired(), URL()])
    img_url = StringField('Cafe Image URL', validators=[DataRequired(), URL()])
    location = StringField('Location', validators=[DataRequired()])
    seats = StringField('Seats', validators=[DataRequired()])
    coffee_price = StringField('Coffee Price', validators=[DataRequired()])
    has_sockets = BooleanField('Has Sockets')
    has_toilet = BooleanField('Has Toilet')
    has_wifi = BooleanField('Has Wi-Fi')
    can_take_calls = BooleanField('Can Take Calls')
    submit = SubmitField('Submit Post')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password')
    submit = SubmitField('Let me in!')


class RegisterForm(FlaskForm):
    email = StringField('Email', validators=[Email()])
    name = StringField('Name', validators=[DataRequired()])
    password = PasswordField('Password')
    submit = SubmitField('Sign me up!')


class CommentForm(FlaskForm):
    text = CKEditorField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Submit Comment')
