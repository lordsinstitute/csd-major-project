"""Search and filter logic for the history page (reused by the exports)."""

from datetime import date

from flask import current_app
from sqlalchemy import or_, select
from sqlalchemy.orm import contains_eager

from models import DiseaseRecord, Farmer

RISK_LEVELS = ("High", "Medium", "Low")
MAX_SEARCH_LENGTH = 100


def _valid_date_string(value):
    """Return the value as an ISO date string, or an empty string if invalid."""
    if not value:
        return ""
    try:
        return date.fromisoformat(value.strip()).isoformat()
    except ValueError:
        return ""


def parse_filters(args):
    """
    Read and validate the filter values from the query string.

    Every value is returned as a string. Anything invalid is replaced with an
    empty string, so a tampered URL can never break the query.
    """
    search = (args.get("q") or "").strip()[:MAX_SEARCH_LENGTH]

    disease = args.get("disease") or ""
    if disease not in current_app.config["CLASSES"]:
        disease = ""

    risk = args.get("risk") or ""
    if risk not in RISK_LEVELS:
        risk = ""

    date_from = _valid_date_string(args.get("date_from"))
    date_to = _valid_date_string(args.get("date_to"))

    # If the range is the wrong way round, swap it instead of showing nothing
    if date_from and date_to and date_from > date_to:
        date_from, date_to = date_to, date_from

    return {
        "q": search,
        "disease": disease,
        "risk": risk,
        "date_from": date_from,
        "date_to": date_to,
    }


def _like_pattern(text):
    """Build a LIKE pattern that treats %, _ and backslash as plain text."""
    escaped = (
        text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    )
    return f"%{escaped}%"


def build_history_statement(filters, farmer_id=None):
    """
    Return the SELECT statement for the history list.

    farmer_id restricts the rows to one farmer (None means every farmer).
    Newest scans come first.
    """
    stmt = (
        select(DiseaseRecord)
        .join(Farmer, DiseaseRecord.farmer_id == Farmer.id)
        .options(contains_eager(DiseaseRecord.farmer))
        .order_by(DiseaseRecord.date.desc(), DiseaseRecord.id.desc())
    )

    if farmer_id is not None:
        stmt = stmt.where(DiseaseRecord.farmer_id == farmer_id)

    if filters["q"]:
        pattern = _like_pattern(filters["q"])
        stmt = stmt.where(
            or_(
                DiseaseRecord.batch_name.ilike(pattern, escape="\\"),
                Farmer.name.ilike(pattern, escape="\\"),
                Farmer.farm_name.ilike(pattern, escape="\\"),
                DiseaseRecord.predicted_disease.ilike(pattern, escape="\\"),
            )
        )

    if filters["disease"]:
        stmt = stmt.where(DiseaseRecord.predicted_disease == filters["disease"])

    if filters["risk"]:
        stmt = stmt.where(DiseaseRecord.risk_level == filters["risk"])

    if filters["date_from"]:
        stmt = stmt.where(
            DiseaseRecord.date >= date.fromisoformat(filters["date_from"])
        )

    if filters["date_to"]:
        stmt = stmt.where(
            DiseaseRecord.date <= date.fromisoformat(filters["date_to"])
        )

    return stmt