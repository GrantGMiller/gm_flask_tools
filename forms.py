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
    username = StringField('Email', validators=[DataRequired()])
    ID = HiddenField('ID', validators=[DataRequired()])
    submit = SubmitField('Send Login Email Now')


class SignUpForm(LoginForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    confirmPassword = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField('Sign Up')


class SettingsForm(FlaskForm):
    emailNotifications = BooleanField('Subscribe to the newsletter.')
    submit = SubmitField('Save')


class UploadSongForm(FlaskForm):
    file = FileField()
    lyrics = TextAreaField(label="Lyrics")
