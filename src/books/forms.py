from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms import PasswordField
from wtforms import SubmitField
from wtforms import BooleanField
from wtforms import IntegerField
from wtforms import DateField
from wtforms import TextAreaField
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

class AddBook(FlaskForm):
    tittle = TextAreaField(validators=[DataRequired()])
    num_pages = IntegerField(validators=[DataRequired()])
    publication_date = DateField(validators=[DataRequired()])
    isbn = StringField()
    publisher = StringField(validators=[DataRequired()])
    author = StringField(validators=[DataRequired()])
    submit = SubmitField('Add Tittle')
