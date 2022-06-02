from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,BooleanField
from wtforms.validators import DataRequired,Email,EqualTo,Length

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