"""Builds the CSV and PDF files for the record export (all in memory)."""

import csv
import io
from datetime import datetime
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

HEALTHY_LABEL = "Healthy"

CSV_HEADERS = [
    "Date",
    "Farmer",
    "Farm",
    "Batch",
    "Total Birds",
    "Sick Birds",
    "Dead Birds",
    "Disease",
    "Confidence (%)",
    "Risk Level",
]

PDF_HEADERS = [
    "Date",
    "Farmer",
    "Farm",
    "Batch",
    "Disease",
    "Confidence",
    "Risk",
    "Total",
    "Sick",
    "Dead",
]

# Column widths in millimetres (total 267 mm = A4 landscape minus margins)
PDF_COLUMN_WIDTHS_MM = [22, 35, 40, 32, 28, 24, 20, 22, 22, 22]

# Characters that make Excel treat a cell as a formula
_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

PRIMARY_GREEN = colors.HexColor("#2e7d32")
LIGHT_GREEN = colors.HexColor("#f1f8f2")


def _safe_cell(value):
    """
    Neutralise spreadsheet formula injection in text cells.

    A farmer could type a batch name such as =HYPERLINK(...). Excel would run
    it when the CSV is opened, so text starting with a formula character gets
    a leading apostrophe. Numbers are left unchanged.
    """
    if isinstance(value, str) and value.startswith(_FORMULA_PREFIXES):
        return "'" + value
    return value


def _date_text(record):
    """Format a record date as DD-MM-YYYY."""
    return record.date.strftime("%d-%m-%Y")


def build_csv(records):
    """
    Return the records as CSV bytes.

    The file is UTF-8 with a byte order mark so Excel shows non-English
    names correctly.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADERS)

    for record in records:
        writer.writerow(
            [
                _date_text(record),
                _safe_cell(record.farmer.name),
                _safe_cell(record.farmer.farm_name),
                _safe_cell(record.batch_name),
                record.total_birds,
                record.sick_birds,
                record.dead_birds,
                record.predicted_disease,
                f"{record.confidence:.2f}",
                record.risk_level,
            ]
        )
    return buffer.getvalue().encode("utf-8-sig")


def summarise(records):
    """Return totals used in the PDF summary line."""
    diseased = sum(1 for r in records if r.predicted_disease != HEALTHY_LABEL)
    return {
        "scans": len(records),
        "diseased": diseased,
        "healthy": len(records) - diseased,
        "sick": sum(r.sick_birds for r in records),
        "dead": sum(r.dead_birds for r in records),
    }


def describe_filters(filters):
    """Turn the active filters into one readable line for the PDF."""
    parts = []
    if filters.get("q"):
        parts.append(f"Search: {filters['q']}")
    if filters.get("disease"):
        parts.append(f"Disease: {filters['disease']}")
    if filters.get("risk"):
        parts.append(f"Risk: {filters['risk']}")
    if filters.get("date_from"):
        parts.append(f"From: {filters['date_from']}")
    if filters.get("date_to"):
        parts.append(f"To: {filters['date_to']}")
    return " | ".join(parts) if parts else "None (all records)"


def _cell(text, style):
    """Wrap text in a Paragraph so long values wrap inside the column."""
    return Paragraph(escape(str(text)), style)


def _draw_footer(canvas, doc):
    """Draw the page number and app name at the bottom of every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(
        15 * mm, 8 * mm, "PoultryScan - Poultry Disease Detection and Farm Analytics"
    )
    canvas.drawRightString(
        landscape(A4)[0] - 15 * mm, 8 * mm, f"Page {doc.page}"
    )
    canvas.restoreState()


def build_pdf(records, scope_label, filters, truncated=False, row_limit=0):
    """
    Return the records as a PDF report (bytes).

    scope_label - text such as the farm name or "All farms"
    filters     - the validated filter dictionary from parse_filters()
    truncated   - True when more records matched than row_limit allows
    """
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=16 * mm,
        title="Poultry Disease Records",
        author="PoultryScan",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], fontSize=18,
        textColor=PRIMARY_GREEN, alignment=0, spaceAfter=4,
    )
    meta_style = ParagraphStyle(
        "ReportMeta", parent=styles["Normal"], fontSize=9,
        textColor=colors.HexColor("#444444"), leading=13,
    )
    head_style = ParagraphStyle(
        "CellHead", parent=styles["Normal"], fontSize=8, leading=10,
        textColor=colors.white, fontName="Helvetica-Bold",
    )
    body_style = ParagraphStyle(
        "CellBody", parent=styles["Normal"], fontSize=8, leading=10,
    )
    note_style = ParagraphStyle(
        "Note", parent=styles["Normal"], fontSize=8, leading=11,
        textColor=colors.HexColor("#b71c1c"),
    )

    summary = summarise(records)
    generated = datetime.now().strftime("%d-%m-%Y %H:%M")

    story = [
        Paragraph("Poultry Disease Records Report", title_style),
        Paragraph(
            f"<b>Scope:</b> {escape(scope_label)} &nbsp;&nbsp; "
            f"<b>Generated:</b> {generated}",
            meta_style,
        ),
        Paragraph(f"<b>Filters:</b> {escape(describe_filters(filters))}", meta_style),
        Paragraph(
            f"<b>Scans:</b> {summary['scans']} &nbsp;&nbsp; "
            f"<b>Healthy:</b> {summary['healthy']} &nbsp;&nbsp; "
            f"<b>Diseased:</b> {summary['diseased']} &nbsp;&nbsp; "
            f"<b>Sick birds:</b> {summary['sick']} &nbsp;&nbsp; "
            f"<b>Dead birds:</b> {summary['dead']}",
            meta_style,
        ),
    ]

    if truncated:
        story.append(
            Paragraph(
                f"Only the newest {row_limit} matching records are included. "
                "Use filters to narrow the report.",
                note_style,
            )
        )
    story.append(Spacer(1, 6 * mm))

    rows = [[_cell(name, head_style) for name in PDF_HEADERS]]
    for record in records:
        rows.append(
            [
                _cell(_date_text(record), body_style),
                _cell(record.farmer.name, body_style),
                _cell(record.farmer.farm_name, body_style),
                _cell(record.batch_name, body_style),
                _cell(record.predicted_disease, body_style),
                _cell(f"{record.confidence:.1f}%", body_style),
                _cell(record.risk_level, body_style),
                _cell(record.total_birds, body_style),
                _cell(record.sick_birds, body_style),
                _cell(record.dead_birds, body_style),
            ]
        )

    table = Table(
        rows,
        colWidths=[width * mm for width in PDF_COLUMN_WIDTHS_MM],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), PRIMARY_GREEN),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_GREEN]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cfd8d3")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    story.append(table)

    document.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    return buffer.getvalue()