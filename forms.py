from flask_wtf import FlaskForm, Form
from wtforms import (StringField, TextAreaField, IntegerField,
                     BooleanField,RadioField, EmailField, PasswordField,
                     SubmitField, URLField, DecimalField, validators)
from wtforms.validators import InputRequired, Length


class LoginForm(FlaskForm):
    username = EmailField("Email", validators=[InputRequired()])
    password = PasswordField("Password", validators=[InputRequired(), Length(min=8)])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    # If you want to get their address to send a physical item,
    # I'll need to add validators=[InputRequired()] to the
    # address lines on form. Left as email/firstname only for now
    # also add the * at start of text to show required
    firstname = StringField("* First Name", validators=[InputRequired()])
    lastname = StringField("Last Name")
    username = EmailField("* Email", validators=[InputRequired()])
    password = PasswordField("* Password", validators=[InputRequired(),Length(min=8)])
    address1 = StringField("Address")
    address2 = StringField("Address (cont'd)")
    city = StringField("City")
    postcode = StringField("Postcode")
    submit = SubmitField("Register")

class ItemForm(FlaskForm):
    item_name = StringField("* Item Name", validators=[InputRequired()])
    item_image = URLField("* Image URL", validators=[InputRequired()])
    item_desc = TextAreaField("* Item Description", validators=[InputRequired()])
    item_price = DecimalField("* Item Price", validators=[InputRequired()])
    submit = SubmitField("Add New Item")
