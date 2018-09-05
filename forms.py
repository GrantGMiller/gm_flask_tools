from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    FileField,
    TextAreaField,
    HiddenField,
)
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    authToken = HiddenField('authToken', validators=[DataRequired()])
    submit = SubmitField('Send Login Email Now')


