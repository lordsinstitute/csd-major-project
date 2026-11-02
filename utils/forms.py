"""WTForms definitions with server-side validation."""

import re
from datetime import date

from flask import current_app
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from sqlalchemy import select
from wtforms import (
    BooleanField,
    DateField,
    IntegerField,
    PasswordField,
    StringField,
    SubmitField,
)
from wtforms.validators import (
    DataRequired,
    EqualTo,
    InputRequired,
    Length,
    NumberRange,
    Regexp,
    ValidationError,
)

from database.db import db
from models import Farmer
from utils.image_utils import has_allowed_extension

EMAIL_PATTERN = r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$"
PHONE_PATTERN = r"^\+?[0-9]{10,15}$"
MAX_BIRDS = 1_000_000


def _clean_text(value):
    """Strip whitespace from text input."""
    return value.strip() if isinstance(value, str) else value


def _clean_email(value):
    """Strip whitespace and lowercase an email address."""
    return value.strip().lower() if isinstance(value, str) else value


def _clean_phone(value):
    """Remove spaces and dashes from a phone number."""
    if isinstance(value, str):
        return re.sub(r"[\s\-()]", "", value)
    return value


def validate_password_strength(form, field):
    """Require minimum length, at least one letter and one digit."""
    password = field.data or ""
    min_length = current_app.config["PASSWORD_MIN_LENGTH"]
    if len(password) < min_length:
        raise ValidationError(
            f"Password must be at least {min_length} characters long."
        )
    if not re.search(r"[A-Za-z]", password):
        raise ValidationError("Password must contain at least one letter.")
    if not re.search(r"[0-9]", password):
        raise ValidationError("Password must contain at least one number.")


class RegistrationForm(FlaskForm):
    """Farmer registration form."""

    name = StringField(
        "Full Name",
        filters=[_clean_text],
        validators=[DataRequired(), Length(min=2, max=100)],
    )
    email = StringField(
        "Email",
        filters=[_clean_email],
        validators=[
            DataRequired(),
            Length(max=150),
            Regexp(EMAIL_PATTERN, message="Enter a valid email address."),
        ],
    )
    phone = StringField(
        "Phone Number",
        filters=[_clean_phone],
        validators=[
            DataRequired(),
            Regexp(
                PHONE_PATTERN,
                message="Enter a valid phone number (10-15 digits).",
            ),
        ],
    )
    farm_name = StringField(
        "Farm Name",
        filters=[_clean_text],
        validators=[DataRequired(), Length(min=2, max=150)],
    )
    password = PasswordField(
        "Password", validators=[DataRequired(), validate_password_strength]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords do not match."),
        ],
    )
    submit = SubmitField("Create Account")

    def validate_email(self, field):
        """Reject an email that is already registered."""
        existing = db.session.execute(
            select(Farmer).filter_by(email=field.data)
        ).scalar_one_or_none()
        if existing is not None:
            raise ValidationError("This email is already registered.")


class LoginForm(FlaskForm):
    """Farmer login form."""

    email = StringField(
        "Email",
        filters=[_clean_email],
        validators=[DataRequired(), Length(max=150)],
    )
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Keep me logged in")
    submit = SubmitField("Log In")


class ScanForm(FlaskForm):
    """Image upload form with batch details and bird counts."""

    batch_name = StringField(
        "Batch Name",
        filters=[_clean_text],
        validators=[DataRequired(), Length(min=1, max=100)],
    )
    scan_date = DateField(
        "Date of Scan",
        default=date.today,
        validators=[DataRequired(message="Enter a valid date.")],
    )
    total_birds = IntegerField(
        "Total Birds",
        validators=[
            InputRequired(message="Enter the total number of birds."),
            NumberRange(min=1, max=MAX_BIRDS),
        ],
        render_kw={"min": 1, "inputmode": "numeric"},
    )
    sick_birds = IntegerField(
        "Sick Birds",
        validators=[
            InputRequired(message="Enter the number of sick birds (0 if none)."),
            NumberRange(min=0, max=MAX_BIRDS),
        ],
        render_kw={"min": 0, "inputmode": "numeric"},
    )
    dead_birds = IntegerField(
        "Dead Birds",
        validators=[
            InputRequired(message="Enter the number of dead birds (0 if none)."),
            NumberRange(min=0, max=MAX_BIRDS),
        ],
        render_kw={"min": 0, "inputmode": "numeric"},
    )
    image = FileField(
        "Chicken Faeces Image",
        validators=[FileRequired(message="Please choose an image to upload.")],
        render_kw={"accept": "image/png,image/jpeg"},
    )
    submit = SubmitField("Upload Image")

    def validate_scan_date(self, field):
        """The scan date cannot be in the future."""
        if field.data and field.data > date.today():
            raise ValidationError("Date cannot be in the future.")

    def validate_sick_birds(self, field):
        """Sick birds cannot exceed the flock size."""
        total = self.total_birds.data
        if total is not None and field.data is not None and field.data > total:
            raise ValidationError("Sick birds cannot exceed total birds.")

    def validate_dead_birds(self, field):
        """Sick and dead birds are counted separately, so together they fit the flock."""
        total = self.total_birds.data
        sick = self.sick_birds.data
        if None in (total, sick, field.data):
            return
        if sick + field.data > total:
            raise ValidationError(
                "Sick and dead birds together cannot exceed total birds."
            )

    def validate_image(self, field):
        """Check the file extension against the allowed list."""
        allowed = current_app.config["ALLOWED_EXTENSIONS"]
        if not has_allowed_extension(field.data.filename, allowed):
            raise ValidationError("Only JPG, JPEG and PNG files are allowed.")