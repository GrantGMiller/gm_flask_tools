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


class DigitalSignageForm(FlaskForm):
    folder = StringField('Content Folder', validators=[DataRequired()])
    submit = SubmitField('Submit')


class AddDigitalSignagePlayerForm(FlaskForm):
    hostname = StringField('IP Address/Hostname', validators=[DataRequired()])

class ExampleForm(FlaskForm):
    hostname = StringField('IP Address/Hostname', validators=[DataRequired()])
