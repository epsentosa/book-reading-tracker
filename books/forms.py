from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms import BooleanField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import EqualTo
from wtforms.validators import Length

class RegistrationForm(FlaskForm):
    name = StringField(validators =[DataRequired()])
    email = StringField(validators=[DataRequired(),Email()])
    password = PasswordField(validators = [Length(min=7)])
    repeat_password = PasswordField(validators = [DataRequired(),EqualTo('password')])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField(validators=[DataRequired(), Email()])
    password = PasswordField(validators=[DataRequired()])
    remember = BooleanField(validators= [DataRequired()])
    submit = SubmitField('Login')

class SearchForm(FlaskForm):
    search = StringField(validators=[DataRequired()])
    submit = SubmitField('Search')