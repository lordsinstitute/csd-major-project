"""Database queries that power the dashboard cards and charts."""

from datetime import date

from flask import current_app
from sqlalchemy import case, desc, func, select

from database.db import db
from models import DiseaseRecord, Farmer

HEALTHY_LABEL = "Healthy"
MONTHS_SHOWN = 12
TOP_N = 10


def scope_farmer_id(farmer):
    """
    Return the farmer id to filter by, or None for the shared "all" view.

    Controlled by the DASHBOARD_SCOPE config setting.
    """
    if current_app.config.get("DASHBOARD_SCOPE", "own") == "all":
        return None
    return farmer.id


def _apply_scope(stmt, farmer_id):
    """Restrict a select statement to one farmer when farmer_id is given."""
    if farmer_id is not None:
        stmt = stmt.where(DiseaseRecord.farmer_id == farmer_id)
    return stmt


def _disease_case_expr():
    """SQL expression that is 1 for a diseased scan and 0 for a healthy one."""
    return case((DiseaseRecord.predicted_disease != HEALTHY_LABEL, 1), else_=0)


def _last_months(count=MONTHS_SHOWN):
    """Return a list of (year, month) tuples ending with the current month."""
    today = date.today()
    year, month = today.year, today.month
    months = []
    for _ in range(count):
        months.append((year, month))
        month -= 1
        if month == 0:
            month = 12
            year -= 1
    months.reverse()
    return months


def get_summary(farmer_id=None):
    """Return the numbers shown on the four dashboard cards."""
    stmt = select(
        func.count(DiseaseRecord.id),
        func.coalesce(
            func.sum(
                case((DiseaseRecord.predicted_disease == HEALTHY_LABEL, 1), else_=0)
            ),
            0,
        ),
        func.coalesce(func.sum(DiseaseRecord.sick_birds), 0),
        func.coalesce(func.sum(DiseaseRecord.dead_birds), 0),
    )
    total, healthy, sick, dead = db.session.execute(
        _apply_scope(stmt, farmer_id)
    ).one()

    total, healthy = int(total), int(healthy)
    diseased = total - healthy
    return {
        "total_scans": total,
        "healthy_cases": healthy,
        "disease_cases": diseased,
        "sick_birds": int(sick),
        "dead_birds": int(dead),
        "healthy_percent": round(healthy * 100 / total, 1) if total else 0,
        "disease_percent": round(diseased * 100 / total, 1) if total else 0,
    }


def get_disease_counts(farmer_id=None):
    """Return how many times each class was predicted (fixed class order)."""
    stmt = select(
        DiseaseRecord.predicted_disease, func.count(DiseaseRecord.id)
    ).group_by(DiseaseRecord.predicted_disease)
    rows = db.session.execute(_apply_scope(stmt, farmer_id)).all()
    counts = {name: int(total) for name, total in rows}

    labels = list(current_app.config["CLASSES"])
    return {
        "labels": labels,
        "values": [counts.get(label, 0) for label in labels],
    }


def get_healthy_vs_diseased(farmer_id=None):
    """Return the healthy and diseased scan counts for the doughnut chart."""
    summary = get_summary(farmer_id)
    return {
        "labels": ["Healthy", "Diseased"],
        "values": [summary["healthy_cases"], summary["disease_cases"]],
    }


def get_monthly_trend(farmer_id=None):
    """Return disease cases and total scans for each of the last 12 months."""
    months = _last_months()
    first_year, first_month = months[0]
    start_date = date(first_year, first_month, 1)

    month_expr = func.strftime("%Y-%m", DiseaseRecord.date)
    stmt = (
        select(
            month_expr,
            func.count(DiseaseRecord.id),
            func.coalesce(func.sum(_disease_case_expr()), 0),
        )
        .where(DiseaseRecord.date >= start_date)
        .group_by(month_expr)
    )
    rows = db.session.execute(_apply_scope(stmt, farmer_id)).all()
    by_month = {key: (int(total), int(diseased)) for key, total, diseased in rows}

    labels, disease_cases, total_scans = [], [], []
    for year, month in months:
        key = f"{year:04d}-{month:02d}"
        total, diseased = by_month.get(key, (0, 0))
        labels.append(date(year, month, 1).strftime("%b %Y"))
        total_scans.append(total)
        disease_cases.append(diseased)

    return {
        "labels": labels,
        "disease_cases": disease_cases,
        "total_scans": total_scans,
    }


def get_batch_comparison(farmer_id=None):
    """Return the batches with the most disease cases (top 10)."""
    cases_expr = func.coalesce(func.sum(_disease_case_expr()), 0)
    stmt = (
        select(DiseaseRecord.batch_name, cases_expr.label("cases"))
        .group_by(DiseaseRecord.batch_name)
        .order_by(desc("cases"), DiseaseRecord.batch_name)
        .limit(TOP_N)
    )
    rows = db.session.execute(_apply_scope(stmt, farmer_id)).all()
    return {
        "labels": [row[0] for row in rows],
        "values": [int(row[1]) for row in rows],
    }


def get_disease_sick_dead(farmer_id=None):
    """Return total sick and dead birds for each disease class."""
    stmt = select(
        DiseaseRecord.predicted_disease,
        func.coalesce(func.sum(DiseaseRecord.sick_birds), 0),
        func.coalesce(func.sum(DiseaseRecord.dead_birds), 0),
    ).group_by(DiseaseRecord.predicted_disease)
    rows = db.session.execute(_apply_scope(stmt, farmer_id)).all()
    totals = {name: (int(sick), int(dead)) for name, sick, dead in rows}

    labels = list(current_app.config["CLASSES"])
    return {
        "labels": labels,
        "sick": [totals.get(label, (0, 0))[0] for label in labels],
        "dead": [totals.get(label, (0, 0))[1] for label in labels],
    }


def get_farm_dead_birds(farmer_id=None):
    """Return dead bird totals per farm (top 10)."""
    dead_expr = func.coalesce(func.sum(DiseaseRecord.dead_birds), 0)
    stmt = (
        select(Farmer.farm_name, dead_expr.label("dead"))
        .join(Farmer, Farmer.id == DiseaseRecord.farmer_id)
        .group_by(Farmer.id, Farmer.farm_name)
        .order_by(desc("dead"), Farmer.farm_name)
        .limit(TOP_N)
    )
    rows = db.session.execute(_apply_scope(stmt, farmer_id)).all()
    return {
        "labels": [row[0] for row in rows],
        "values": [int(row[1]) for row in rows],
    }


def get_dashboard_data(farmer_id=None):
    """Collect every dashboard dataset into one dictionary."""
    return {
        "summary": get_summary(farmer_id),
        "disease_counts": get_disease_counts(farmer_id),
        "healthy_vs_diseased": get_healthy_vs_diseased(farmer_id),
        "monthly_trend": get_monthly_trend(farmer_id),
        "batch_comparison": get_batch_comparison(farmer_id),
        "disease_sick_dead": get_disease_sick_dead(farmer_id),
        "farm_dead_birds": get_farm_dead_birds(farmer_id),
    }