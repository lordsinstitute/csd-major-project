"""CSV and PDF export: content, filters, limits and privacy."""

import csv
import io

from tests.helpers import add_record, seed_three
from utils.export_utils import CSV_HEADERS, _safe_cell, build_pdf


def read_csv(response):
    """Parse a CSV response (the file starts with a UTF-8 byte order mark)."""
    text = response.get_data().decode("utf-8-sig")
    return list(csv.reader(io.StringIO(text)))


# -------------------------------------------------------------------- CSV
def test_csv_download_headers_and_row(app, auth_client, farmer):
    add_record(app, farmer["id"], batch_name="Alpha")
    response = auth_client.get("/export/csv")

    assert response.status_code == 200
    assert response.mimetype == "text/csv"
    disposition = response.headers["Content-Disposition"]
    assert "attachment" in disposition
    assert "poultry_records_" in disposition and ".csv" in disposition
    assert response.headers["Cache-Control"] == "no-store"
    assert response.get_data().startswith(b"\xef\xbb\xbf")

    rows = read_csv(response)
    assert rows[0] == CSV_HEADERS
    assert len(rows) == 2
    today = __import__("datetime").date.today().strftime("%d-%m-%Y")
    assert rows[1] == [
        today, "Ramesh", "Green Valley Poultry", "Alpha",
        "100", "10", "2", "Salmonella", "91.00", "High",
    ]


def test_csv_newest_first(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    rows = read_csv(auth_client.get("/export/csv"))
    assert [row[3] for row in rows[1:]] == ["Charlie", "Bravo", "Alpha"]


def test_csv_uses_history_filters(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    rows = read_csv(auth_client.get("/export/csv", query_string={"disease": "Salmonella"}))
    assert [row[3] for row in rows[1:]] == ["Bravo"]


def test_csv_blocks_formula_injection(app, auth_client, farmer):
    add_record(app, farmer["id"], batch_name="=1+1")
    rows = read_csv(auth_client.get("/export/csv"))
    assert rows[1][3] == "'=1+1"


def test_safe_cell_only_changes_dangerous_text():
    assert _safe_cell("=SUM(A1)") == "'=SUM(A1)"
    assert _safe_cell("+1") == "'+1"
    assert _safe_cell("-1") == "'-1"
    assert _safe_cell("@name") == "'@name"
    assert _safe_cell("Batch A") == "Batch A"
    assert _safe_cell(5) == 5


def test_csv_limit_is_applied(app, auth_client, farmer, monkeypatch):
    monkeypatch.setattr("routes.export.MAX_EXPORT_ROWS", 2)
    for name in ("One", "Two", "Three"):
        add_record(app, farmer["id"], batch_name=name)
    rows = read_csv(auth_client.get("/export/csv"))
    assert len(rows) == 3  # header + 2 records


def test_csv_only_contains_own_records(app, auth_client, farmer, second_farmer):
    add_record(app, farmer["id"], batch_name="MineOnly")
    add_record(app, second_farmer["id"], batch_name="TheirsOnly")
    body = auth_client.get("/export/csv").get_data(as_text=True)
    assert "MineOnly" in body
    assert "TheirsOnly" not in body


def test_export_without_records_redirects_with_message(auth_client):
    response = auth_client.get("/export/csv")
    assert response.status_code == 302
    assert "/history" in response.headers["Location"]

    page = auth_client.get("/export/pdf", follow_redirects=True)
    assert "no records to export" in page.get_data(as_text=True)


# -------------------------------------------------------------------- PDF
def test_pdf_download(app, auth_client, farmer):
    seed_three(app, farmer["id"])
    response = auth_client.get("/export/pdf")
    assert response.status_code == 200
    assert response.mimetype == "application/pdf"
    assert response.get_data().startswith(b"%PDF")
    assert ".pdf" in response.headers["Content-Disposition"]


def test_pdf_survives_special_characters(app, auth_client, farmer):
    add_record(app, farmer["id"], batch_name="<b>Rock & Roll</b>")
    response = auth_client.get("/export/pdf")
    assert response.status_code == 200
    assert response.get_data().startswith(b"%PDF")


def test_pdf_with_many_records_spans_pages(app, auth_client, farmer):
    for number in range(60):
        add_record(app, farmer["id"], batch_name=f"Batch{number:02d}")
    response = auth_client.get("/export/pdf")
    assert response.status_code == 200
    assert response.get_data().startswith(b"%PDF")


def test_build_pdf_accepts_empty_filters_and_truncation_note(app, auth_client, farmer):
    add_record(app, farmer["id"])
    with app.app_context():
        from sqlalchemy import select

        from database.db import db
        from models import DiseaseRecord

        records = list(db.session.execute(select(DiseaseRecord)).scalars())
        for record in records:
            record.farmer  # load the relationship while the session is open
        content = build_pdf(
            records, "Test Farm", {}, truncated=True, row_limit=1
        )
    assert content.startswith(b"%PDF")