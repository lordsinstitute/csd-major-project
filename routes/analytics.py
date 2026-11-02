"""Analytics blueprint: detailed farm and disease analytics page."""

from flask import Blueprint, render_template, request
from flask_login import current_user, login_required

from utils.analytics import scope_farmer_id
from utils.analytics_report import PERIODS, get_analytics_data, parse_period

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
@login_required
def index():
    """Show totals, breakdown tables and charts for the chosen period."""
    period = parse_period(request.args.get("period"))
    farmer_id = scope_farmer_id(current_user)
    data = get_analytics_data(farmer_id, period)

    return render_template(
        "analytics.html",
        data=data,
        period=period,
        periods=PERIODS,
        shared_view=farmer_id is None,
    )