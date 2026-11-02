"""Detailed analytics for the Analytics page: totals, breakdowns, insights."""

from datetime import date, timedelta

from flask import current_app
from sqlalchemy import case, desc, func, select

from database.db import db
from models import DiseaseRecord, Farmer
from utils.analytics import HEALTHY_LABEL, TOP_N, get_monthly_trend

BATCH_LIMIT = 15

# Value in the query string -> label shown in the period dropdown
PERIODS = {
    "all": "All time",
    "30": "Last 30 days",
    "90": "Last 90 days",
    "365": "Last 12 months",
}


def parse_period(value):
    """Return a valid period key; anything unknown becomes "all"."""
    return value if value in PERIODS else "all"


def _filter(stmt, farmer_id, period):
    """Restrict a statement to one farmer and to the chosen time period."""
    if farmer_id is not None:
        stmt = stmt.where(DiseaseRecord.farmer_id == farmer_id)
    if period != "all":
        start = date.today() - timedelta(days=int(period))
        stmt = stmt.where(DiseaseRecord.date >= start)
    return stmt


def _disease_case_expr():
    """SQL expression that is 1 for a diseased scan and 0 for a healthy one."""
    return case((DiseaseRecord.predicted_disease != HEALTHY_LABEL, 1), else_=0)


def _dead_share(sick, dead):
    """
    Percent of affected birds that died.

    Sick and dead birds are counted separately in every record, so the
    affected birds are sick + dead. This avoids using total_birds, which
    would count the same flock again on every scan.
    """
    affected = sick + dead
    return round(dead * 100 / affected, 1) if affected else 0.0


def get_totals(farmer_id=None, period="all"):
    """Return the numbers for the four summary cards."""
    stmt = select(
        func.count(DiseaseRecord.id),
        func.coalesce(func.sum(_disease_case_expr()), 0),
        func.coalesce(func.sum(DiseaseRecord.sick_birds), 0),
        func.coalesce(func.sum(DiseaseRecord.dead_birds), 0),
        func.coalesce(func.avg(DiseaseRecord.confidence), 0),
    )
    scans, cases, sick, dead, avg_conf = db.session.execute(
        _filter(stmt, farmer_id, period)
    ).one()
    sick, dead = int(sick), int(dead)
    return {
        "scans": int(scans),
        "disease_scans": int(cases),
        "sick_birds": sick,
        "dead_birds": dead,
        "dead_share": _dead_share(sick, dead),
        "avg_confidence": round(float(avg_conf), 1),
    }


def get_disease_breakdown(farmer_id=None, period="all"):
    """Return scans, sick birds and dead birds for every class (fixed order)."""
    stmt = select(
        DiseaseRecord.predicted_disease,
        func.count(DiseaseRecord.id),
        func.coalesce(func.sum(DiseaseRecord.sick_birds), 0),
        func.coalesce(func.sum(DiseaseRecord.dead_birds), 0),
    ).group_by(DiseaseRecord.predicted_disease)
    rows = db.session.execute(_filter(stmt, farmer_id, period)).all()
    by_name = {
        name: (int(scans), int(sick), int(dead)) for name, scans, sick, dead in rows
    }

    result = []
    for label in current_app.config["CLASSES"]:
        scans, sick, dead = by_name.get(label, (0, 0, 0))
        result.append(
            {
                "disease": label,
                "scans": scans,
                "sick": sick,
                "dead": dead,
                "dead_share": _dead_share(sick, dead),
            }
        )
    return result


def get_farm_breakdown(farmer_id=None, period="all"):
    """Return per-farm scans, disease cases, sick and dead birds (top 10)."""
    dead_expr = func.coalesce(func.sum(DiseaseRecord.dead_birds), 0)
    stmt = (
        select(
            Farmer.farm_name,
            func.count(DiseaseRecord.id),
            func.coalesce(func.sum(_disease_case_expr()), 0),
            func.coalesce(func.sum(DiseaseRecord.sick_birds), 0),
            dead_expr.label("dead"),
        )
        .join(Farmer, Farmer.id == DiseaseRecord.farmer_id)
        .group_by(Farmer.id, Farmer.farm_name)
        .order_by(desc("dead"), Farmer.farm_name)
        .limit(TOP_N)
    )
    rows = db.session.execute(_filter(stmt, farmer_id, period)).all()
    return [
        {
            "farm": farm,
            "scans": int(scans),
            "disease_cases": int(cases),
            "sick": int(sick),
            "dead": int(dead),
        }
        for farm, scans, cases, sick, dead in rows
    ]


def get_batch_breakdown(farmer_id=None, period="all"):
    """Return the batches with the most disease cases (top 15)."""
    cases_expr = func.coalesce(func.sum(_disease_case_expr()), 0)
    dead_expr = func.coalesce(func.sum(DiseaseRecord.dead_birds), 0)
    stmt = (
        select(
            DiseaseRecord.batch_name,
            Farmer.farm_name,
            func.count(DiseaseRecord.id),
            cases_expr.label("cases"),
            func.coalesce(func.sum(DiseaseRecord.sick_birds), 0),
            dead_expr.label("dead"),
            func.max(DiseaseRecord.date).label("last_scan"),
        )
        .join(Farmer, Farmer.id == DiseaseRecord.farmer_id)
        .group_by(Farmer.id, Farmer.farm_name, DiseaseRecord.batch_name)
        .order_by(desc("cases"), desc("dead"), DiseaseRecord.batch_name)
        .limit(BATCH_LIMIT)
    )
    rows = db.session.execute(_filter(stmt, farmer_id, period)).all()
    return [
        {
            "batch": batch,
            "farm": farm,
            "scans": int(scans),
            "disease_cases": int(cases),
            "sick": int(sick),
            "dead": int(dead),
            "last_scan": last_scan,
        }
        for batch, farm, scans, cases, sick, dead, last_scan in rows
    ]


def get_trend_insight(trend):
    """
    Summarise the monthly trend in plain words.

    Returns None when there are no disease cases in the last 12 months.
    """
    labels = trend["labels"]
    cases = trend["disease_cases"]
    if sum(cases) == 0:
        return None

    # Latest month that reached the highest number of disease cases
    peak_value = max(cases)
    peak_index = len(cases) - 1 - cases[::-1].index(peak_value)

    current, previous = cases[-1], cases[-2]
    current_label, previous_label = labels[-1], labels[-2]

    if current > previous:
        direction = "up"
        message = (
            f"Disease cases increased from {previous} in {previous_label} "
            f"to {current} in {current_label}."
        )
    elif current < previous:
        direction = "down"
        message = (
            f"Disease cases decreased from {previous} in {previous_label} "
            f"to {current} in {current_label}."
        )
    else:
        direction = "flat"
        message = (
            f"Disease cases stayed at {current} in both {previous_label} "
            f"and {current_label}."
        )

    return {
        "direction": direction,
        "message": message,
        "peak_month": labels[peak_index],
        "peak_cases": peak_value,
    }


def get_analytics_data(farmer_id=None, period="all"):
    """Collect everything the Analytics page needs into one dictionary."""
    diseases = get_disease_breakdown(farmer_id, period)
    farms = get_farm_breakdown(farmer_id, period)
    trend = get_monthly_trend(farmer_id)

    charts = {
        "disease": {
            "labels": [row["disease"] for row in diseases],
            "sick": [row["sick"] for row in diseases],
            "dead": [row["dead"] for row in diseases],
        },
        "dead_share": {
            "labels": [row["disease"] for row in diseases],
            "values": [row["dead"] for row in diseases],
        },
        "farms": {
            "labels": [row["farm"] for row in farms],
            "values": [row["dead"] for row in farms],
        },
        "monthly": {
            "labels": trend["labels"],
            "disease_cases": trend["disease_cases"],
        },
    }

    return {
        "totals": get_totals(farmer_id, period),
        "diseases": diseases,
        "farms": farms,
        "batches": get_batch_breakdown(farmer_id, period),
        "insight": get_trend_insight(trend),
        "charts": charts,
    }