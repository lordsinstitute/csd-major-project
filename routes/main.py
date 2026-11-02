"""Main blueprint: landing redirect, dashboard page and dashboard data API."""

from flask import Blueprint, jsonify, redirect, render_template, url_for
from flask_login import current_user, login_required

from utils.analytics import get_dashboard_data, get_summary, scope_farmer_id

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Send visitors to the dashboard or the login page."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return redirect(url_for("auth.login"))


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """Render the dashboard with summary cards (charts load through the API)."""
    summary = get_summary(scope_farmer_id(current_user))
    return render_template("dashboard.html", summary=summary)


@main_bp.route("/api/dashboard-data")
@login_required
def dashboard_data():
    """Return all chart datasets as JSON for Chart.js."""
    data = get_dashboard_data(scope_farmer_id(current_user))
    response = jsonify(data)
    response.headers["Cache-Control"] = "no-store"
    return response