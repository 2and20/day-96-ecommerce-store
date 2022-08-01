from flask_wtf import FlaskForm, Form
from wtforms import (StringField, TextAreaField, IntegerField,
                     BooleanField,RadioField, EmailField, PasswordField,
                     SubmitField, validators)
from wtforms.validators import InputRequired, Length


class LoginForm(FlaskForm):
    username = EmailField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8)])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    firstname = StringField("* First Name", validators=[InputRequired()])
    lastname = StringField("* Last Name", validators=[InputRequired()])
    username = EmailField("* Email", validators=[InputRequired()])
    password = PasswordField("* Password", validators=[InputRequired(), Length(min=8)])
    address1 = StringField("* Address", validators=[InputRequired()])
    address2 = StringField("Address (cont'd)")
    city = StringField("* City", validators=[InputRequired()])
    postcode = StringField("* Postcode", validators=[InputRequired()])
    submit = SubmitField("Register")

