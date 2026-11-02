"""History blueprint: searchable, filterable, paginated list of scans."""

from flask import Blueprint, current_app, render_template, request, url_for
from flask_login import current_user, login_required

from database.db import db
from utils.analytics import scope_farmer_id
from utils.history_query import RISK_LEVELS, build_history_statement, parse_filters

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
@login_required
def index():
    """Show the scan history with search, filters and pagination."""
    filters = parse_filters(request.args)
    farmer_id = scope_farmer_id(current_user)
    statement = build_history_statement(filters, farmer_id)

    per_page = current_app.config["RECORDS_PER_PAGE"]
    page = max(request.args.get("page", 1, type=int), 1)

    pagination = db.paginate(
        statement, page=page, per_page=per_page, error_out=False
    )
    # A page number beyond the last page falls back to the last page
    if pagination.pages and page > pagination.pages:
        pagination = db.paginate(
            statement, page=pagination.pages, per_page=per_page, error_out=False
        )

    # Only the filters that are in use are kept in the page links
    active_filters = {key: value for key, value in filters.items() if value}

    def page_url(number):
        """Build a link to another page that keeps the current filters."""
        return url_for("history.index", page=number, **active_filters)

    return render_template(
        "history.html",
        pagination=pagination,
        records=pagination.items,
        filters=filters,
        export_filters=active_filters,
        has_filters=bool(active_filters),
        page_url=page_url,
        diseases=current_app.config["CLASSES"],
        risk_levels=RISK_LEVELS,
        shared_view=farmer_id is None,
    )