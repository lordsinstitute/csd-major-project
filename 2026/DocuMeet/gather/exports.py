from __future__ import annotations

from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from .domain import speaker_name, timestamp


def transcript_txt(meeting: dict) -> str:
    review = "Reviewed" if meeting.get("reviewed") else "Draft - speaker assignments need review"
    header = [meeting["title"], "=" * min(70, max(8, len(meeting["title"]))),
              f"Recorded: {datetime.fromisoformat(meeting['created']).astimezone():%d %b %Y, %H:%M}",
              f"Duration: {timestamp(meeting['duration'])}", f"Status: {review}", ""]
    for seg in meeting["segments"]:
        label = speaker_name(meeting, seg["speaker"])
        if seg.get("overlap"):
            label += " [overlapping speech - review]"
        header += [f"[{timestamp(seg['start'])} - {timestamp(seg['end'])}] {label}", seg["text"], ""]
    return "\n".join(header)


def export_txt(meeting: dict, path: str | Path):
    Path(path).write_text(transcript_txt(meeting), encoding="utf-8")


def export_pdf(meeting: dict, path: str | Path):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    # Windows system font supports participant names beyond ASCII; fallback is portable.
    font = "Helvetica"
    for candidate in [Path("C:/Windows/Fonts/segoeui.ttf"), Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")]:
        if candidate.exists():
            if "DocuMeetText" not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont("DocuMeetText", str(candidate)))
            font = "DocuMeetText"
            break
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("DocuMeetTitle", fontName=font, fontSize=24, leading=31, textColor=colors.HexColor("#20243d"), spaceAfter=14))
    styles.add(ParagraphStyle("DocuMeetMeta", fontName=font, fontSize=9, leading=14, textColor=colors.HexColor("#697085")))
    styles.add(ParagraphStyle("DocuMeetLabel", fontName=font, fontSize=9, leading=14, textColor=colors.HexColor("#5254cb"), spaceBefore=12, spaceAfter=4, keepWithNext=True))
    styles.add(ParagraphStyle("DocuMeetBody", fontName=font, fontSize=10, leading=16, alignment=TA_LEFT, splitLongWords=True))
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48,
                            title=meeting["title"], author="DocuMeet · Local meeting workspace")
    safe = lambda s: escape(str(s)).replace("\n", "<br/>")
    story = [Paragraph(safe(meeting["title"]), styles["DocuMeetTitle"]),
             Paragraph(f"DocuMeet / MEETING TRANSCRIPT · {timestamp(meeting['duration'])}", styles["DocuMeetMeta"]),
             Paragraph("Reviewed transcript" if meeting.get("reviewed") else "Draft: speaker assignments need review", styles["DocuMeetMeta"]), Spacer(1, 12)]
    for seg in meeting["segments"]:
        name = safe(speaker_name(meeting, seg["speaker"]))
        warning = " · Overlapping speech: review" if seg.get("overlap") else ""
        story += [Paragraph(f"{timestamp(seg['start'])} - {timestamp(seg['end'])} &nbsp; / &nbsp; {name}{warning}", styles["DocuMeetLabel"]),
                  Paragraph(safe(seg["text"]), styles["DocuMeetBody"])]

    def footer(canvas, document):
        canvas.setFont(font, 8)
        canvas.setFillColor(colors.HexColor("#7b8190"))
        canvas.drawString(48, 28, "DocuMeet · Processed locally")
        canvas.drawRightString(A4[0] - 48, 28, f"Page {document.page}")
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
