"""Authentication blueprint: register, login and logout."""

from urllib.parse import urljoin, urlparse

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from database.db import db
from extensions import limiter
from models import Farmer
from utils.forms import LoginForm, RegistrationForm

auth_bp = Blueprint("auth", __name__)

# A real hash used to keep login timing similar when the email is unknown
_DUMMY_HASH = generate_password_hash("timing-protection-dummy-value")

def _login_limit():
    """Rate limit string for login attempts (read from config)."""
    return current_app.config["LOGIN_RATE_LIMIT"]


def _register_limit():
    """Rate limit string for registrations (read from config)."""
    return current_app.config["REGISTER_RATE_LIMIT"]

def _is_safe_redirect(target):
    """Return True only if the target URL points back to this site."""
    if not target:
        return False
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit(_register_limit, methods=["POST"])
def register():
    """Register a new farmer account."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = RegistrationForm()
    if form.validate_on_submit():
        farmer = Farmer(
            name=form.name.data,
            email=form.email.data,
            phone=form.phone.data,
            farm_name=form.farm_name.data,
        )
        farmer.set_password(form.password.data)
        db.session.add(farmer)
        try:
            db.session.commit()
        except IntegrityError:
            # Covers a race where the same email was registered concurrently
            db.session.rollback()
            form.email.errors.append("This email is already registered.")
        else:
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit(_login_limit, methods=["POST"])
def login():
    """Log a farmer in after verifying the email and password hash."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        farmer = db.session.execute(
            select(Farmer).filter_by(email=form.email.data)
        ).scalar_one_or_none()

        if farmer is not None and farmer.check_password(form.password.data):
            login_user(farmer, remember=form.remember.data)
            flash(f"Welcome back, {farmer.name}!", "success")
            next_page = request.args.get("next")
            if _is_safe_redirect(next_page):
                return redirect(next_page)
            return redirect(url_for("main.dashboard"))

        if farmer is None:
            # Perform a dummy hash check so timing does not reveal
            # whether the email exists
            from werkzeug.security import check_password_hash

            check_password_hash(_DUMMY_HASH, form.password.data)

        # One generic message for both wrong email and wrong password
        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Log the current farmer out (POST only, CSRF protected)."""
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))