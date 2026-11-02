"""Export blueprint: download the filtered records as CSV or PDF."""

from datetime import datetime
from io import BytesIO

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    request,
    send_file,
    url_for,
)
from flask_login import current_user, login_required

from database.db import db
from utils.analytics import scope_farmer_id
from utils.export_utils import build_csv, build_pdf
from utils.history_query import build_history_statement, parse_filters

export_bp = Blueprint("export", __name__)

# Safety limit so one download cannot exhaust server memory
MAX_EXPORT_ROWS = 5000


def _load_records(filters, farmer_id):
    """
    Return (records, truncated) for the current filters.

    One extra row is requested to find out whether the limit cut the list.
    """
    statement = build_history_statement(filters, farmer_id).limit(MAX_EXPORT_ROWS + 1)
    records = list(db.session.execute(statement).scalars().all())
    truncated = len(records) > MAX_EXPORT_ROWS
    return records[:MAX_EXPORT_ROWS], truncated


def _file_response(content, mimetype, extension):
    """Send in-memory bytes as a download with a time-stamped file name."""
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    response = send_file(
        BytesIO(content),
        mimetype=mimetype,
        as_attachment=True,
        download_name=f"poultry_records_{stamp}.{extension}",
    )
    # Personal farm data must never be stored by a shared cache
    response.headers["Cache-Control"] = "no-store"
    return response


def _prepare_export():
    """
    Read filters and load the matching records.

    Returns (filters, farmer_id, records, truncated), or None when there is
    nothing to export (a message is flashed in that case).
    """
    filters = parse_filters(request.args)
    farmer_id = scope_farmer_id(current_user)
    records, truncated = _load_records(filters, farmer_id)

    if not records:
        flash("There are no records to export for the current filters.", "warning")
        return None
    return filters, farmer_id, records, truncated


@export_bp.route("/export/csv")
@login_required
def export_csv():
    """Download the filtered records as a CSV file."""
    prepared = _prepare_export()
    if prepared is None:
        return redirect(url_for("history.index", **request.args))

    _filters, _farmer_id, records, truncated = prepared
    if truncated:
        flash(
            f"The export was limited to the newest {MAX_EXPORT_ROWS} records. "
            "Use filters to export the rest.",
            "info",
        )
    return _file_response(build_csv(records), "text/csv", "csv")


@export_bp.route("/export/pdf")
@login_required
def export_pdf():
    """Download the filtered records as a PDF report."""
    prepared = _prepare_export()
    if prepared is None:
        return redirect(url_for("history.index", **request.args))

    filters, farmer_id, records, truncated = prepared
    scope_label = current_user.farm_name if farmer_id is not None else "All farms"

    try:
        content = build_pdf(
            records, scope_label, filters,
            truncated=truncated, row_limit=MAX_EXPORT_ROWS,
        )
    except Exception:  # report generation must never show a stack trace
        current_app.logger.exception("PDF export failed")
        flash("The PDF could not be created. Please try again.", "danger")
        return redirect(url_for("history.index", **request.args))

    return _file_response(content, "application/pdf", "pdf")