from __future__ import annotations

import io
import re
from datetime import datetime, timezone
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Arabic font registration ───────────────────────────────────────────────────
_FONTS_DIR = Path(__file__).parent.parent / "assets" / "fonts"
_AMIRI     = _FONTS_DIR / "Amiri-Regular.ttf"

_ARABIC_FONT = "Helvetica"   # fallback if Amiri not found

if _AMIRI.exists():
    try:
        pdfmetrics.registerFont(TTFont("Amiri", str(_AMIRI)))
        _ARABIC_FONT = "Amiri"
    except Exception:
        pass

# ── Arabic text helpers ────────────────────────────────────────────────────────
_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")


def _has_arabic(text: str) -> bool:
    return bool(_ARABIC_RE.search(text))


def _prep_arabic(text: str) -> str:
    """Reshape Arabic letters and apply the BiDi algorithm so ReportLab renders them correctly."""
    if not text or not _has_arabic(text):
        return text
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display
        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def _arabic_para(text: str, style: ParagraphStyle) -> Paragraph:
    """Return a Paragraph with Arabic text properly shaped, right-aligned, Arabic font."""
    prepped = _prep_arabic(text)
    ar_style = ParagraphStyle(
        style.name + "_ar",
        parent=style,
        fontName=_ARABIC_FONT,
        alignment=TA_RIGHT,
        wordWrap="RTL",
    )
    return Paragraph(prepped, ar_style)


def _smart_para(text: str, style: ParagraphStyle) -> Paragraph:
    """Return an Arabic or normal paragraph depending on content."""
    if _has_arabic(text):
        return _arabic_para(text, style)
    return Paragraph(text, style)


# ── Colour palette ─────────────────────────────────────────────────────────────
BRAND_BLUE    = colors.HexColor("#1E3A5F")
BRAND_BLUE_LT = colors.HexColor("#2E5BA8")
BRAND_LIGHT   = colors.HexColor("#F1F5F9")
BORDER_GREY   = colors.HexColor("#CBD5E1")
TEXT_MUTED    = colors.HexColor("#64748B")
TEXT_DARK     = colors.HexColor("#1E293B")
WHITE         = colors.white

ATS_COLOURS = {
    1: colors.HexColor("#DC2626"),
    2: colors.HexColor("#EA580C"),
    3: colors.HexColor("#D97706"),
    4: colors.HexColor("#2563EB"),
    5: colors.HexColor("#16A34A"),
}
ATS_BG = {
    1: colors.HexColor("#FEF2F2"),
    2: colors.HexColor("#FFF7ED"),
    3: colors.HexColor("#FFFBEB"),
    4: colors.HexColor("#EFF6FF"),
    5: colors.HexColor("#F0FDF4"),
}
ATS_LABELS = {
    1: "Cat 1 — Resuscitation  (Immediate)",
    2: "Cat 2 — Emergency  (≤ 10 min)",
    3: "Cat 3 — Urgent  (≤ 30 min)",
    4: "Cat 4 — Semi-urgent  (≤ 60 min)",
    5: "Cat 5 — Non-urgent  (≤ 120 min)",
}

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm
COL_W  = PAGE_W - 2 * MARGIN


# ── Formatters ─────────────────────────────────────────────────────────────────

def _fmt_ts(iso: str | None) -> str:
    if not iso:
        return "—"
    try:
        if iso.endswith("Z"):
            iso = iso[:-1] + "+00:00"
        dt = datetime.fromisoformat(iso).astimezone(timezone.utc)
        return dt.strftime("%d %b %Y  %H:%M UTC")
    except Exception:
        return iso


def _fmt_dur(seconds: int | None) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(seconds, 60)
    return f"{m} min {s:02d} sec"


def _fmt_vital(value: object, unit: str) -> str:
    return f"{value} {unit}" if value is not None else "—"


def _page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(TEXT_MUTED)
    canvas.drawCentredString(PAGE_W / 2, 12 * mm, f"TRIBOT Triage Report  ·  Page {doc.page}")
    canvas.restoreState()


# ── Styles ─────────────────────────────────────────────────────────────────────

def _styles() -> dict:
    base = getSampleStyleSheet()

    def S(name: str, **kw) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "report_title": S("rt",  fontSize=22, textColor=WHITE,
                          fontName="Helvetica-Bold", leading=26),
        "report_sub":   S("rs",  fontSize=9,  textColor=colors.HexColor("#CBD5E1"),
                          leading=13),
        "meta_label":   S("ml",  fontSize=7.5, textColor=colors.HexColor("#94A3B8"),
                          fontName="Helvetica-Bold"),
        "meta_value":   S("mv",  fontSize=8.5, textColor=WHITE,
                          fontName="Helvetica-Bold"),
        "section":      S("sec", fontSize=10, textColor=BRAND_BLUE,
                          fontName="Helvetica-Bold", spaceBefore=14, spaceAfter=5),
        "body":         S("body", fontSize=9, textColor=TEXT_DARK, leading=14),
        "muted":        S("muted", fontSize=7.5, textColor=TEXT_MUTED, leading=12),
        "chat_sender":  S("cs",  fontSize=8,  textColor=TEXT_MUTED,
                          fontName="Helvetica-Bold"),
        "chat_text":    S("ct",  fontSize=9,  textColor=TEXT_DARK, leading=14),
        "chat_trans":   S("ctr", fontSize=8,  textColor=TEXT_MUTED, leading=12),
        "ats_text":     S("ats", fontSize=10, fontName="Helvetica-Bold"),
        "footer":       S("foot", fontSize=7.5, textColor=TEXT_MUTED,
                          alignment=TA_CENTER),
    }


# ── Shared table style ─────────────────────────────────────────────────────────

def _data_table_style(ats_row: int | None = None, ats_colour=None) -> TableStyle:
    cmds = [
        ("FONTNAME",      (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",      (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 8.5),
        ("TEXTCOLOR",     (0, 0), (0, -1), TEXT_MUTED),
        ("TEXTCOLOR",     (2, 0), (2, -1), TEXT_MUTED),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [BRAND_LIGHT, WHITE]),
        ("BOX",           (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("INNERGRID",     (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]
    if ats_row is not None and ats_colour is not None:
        cmds += [
            ("TEXTCOLOR", (1, ats_row), (1, ats_row), ats_colour),
            ("FONTNAME",  (1, ats_row), (1, ats_row), "Helvetica-Bold"),
        ]
    return TableStyle(cmds)


# ── Main entry point ───────────────────────────────────────────────────────────

def generate_session_pdf(
    session: dict,
    patient: dict,
    messages: list[dict],
    summary: str,
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=22 * mm,
    )

    S = _styles()
    story: list = []
    col_widths = [COL_W * w for w in [0.20, 0.30, 0.20, 0.30]]

    ats_cat    = session.get("ats_category")
    ats_colour = ATS_COLOURS.get(ats_cat, colors.HexColor("#64748B"))
    ats_bg     = ATS_BG.get(ats_cat, BRAND_LIGHT)
    ats_text   = ATS_LABELS.get(ats_cat, "Not assigned") if ats_cat else "Not assigned"
    generated_at = datetime.now(timezone.utc).strftime("%d %b %Y  %H:%M UTC")
    session_id   = session.get("id", "—")

    # ── Header banner ──────────────────────────────────────────────────────────
    header = Table(
        [[
            [
                Paragraph("TRIBOT", S["report_title"]),
                Paragraph("Emergency Triage Session Report", S["report_sub"]),
            ],
            [
                Paragraph("GENERATED", S["meta_label"]),
                Paragraph(generated_at, S["meta_value"]),
                Spacer(1, 4),
                Paragraph("SESSION ID", S["meta_label"]),
                Paragraph((session_id[:18] + "…") if len(session_id) > 18 else session_id,
                           S["meta_value"]),
            ],
        ]],
        colWidths=[COL_W * 0.55, COL_W * 0.45],
    )
    header.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BRAND_BLUE),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.append(header)
    story.append(Spacer(1, 10))

    # ── ATS badge ──────────────────────────────────────────────────────────────
    badge = Table([[Paragraph(f"▶  ATS  {ats_text}", S["ats_text"])]], colWidths=[COL_W])
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), ats_bg),
        ("TEXTCOLOR",     (0, 0), (-1, -1), ats_colour),
        ("BOX",           (0, 0), (-1, -1), 1.5, ats_colour),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(badge)
    story.append(Spacer(1, 3))
    story.append(Paragraph(
        f"Nurse confirmed: {'Yes ✓' if session.get('nurse_confirmed_ats') else 'No'}",
        S["muted"],
    ))
    story.append(Spacer(1, 8))

    # ── Clinical summary ───────────────────────────────────────────────────────
    story.append(Paragraph("Clinical Summary", S["section"]))
    summary_box = Table(
        [[_smart_para(summary or "Summary not available.", S["body"])]],
        colWidths=[COL_W],
    )
    summary_box.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F0F9FF")),
        ("BOX",           (0, 0), (-1, -1), 0.5, colors.HexColor("#BAE6FD")),
        ("LINEBEFORE",    (0, 0), (0, -1), 3, BRAND_BLUE_LT),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("TOPPADDING",    (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ]))
    story.append(summary_box)
    story.append(Paragraph(
        "AI-generated — for reference only. Verify all clinical details.", S["muted"],
    ))
    story.append(Spacer(1, 6))

    # ── Patient information ────────────────────────────────────────────────────
    story.append(Paragraph("Patient Information", S["section"]))
    lang_label = "Arabic" if patient.get("patient_language") == "ar" else "English"
    pt = Table(
        [
            ["Full Name",   patient.get("full_name", "—"), "MRN",       patient.get("mrn", "—")],
            ["Language",    lang_label,                    "Patient ID", patient.get("id", "—")],
        ],
        colWidths=col_widths,
    )
    pt.setStyle(_data_table_style())
    story.append(pt)

    # ── Session details ────────────────────────────────────────────────────────
    story.append(Paragraph("Session Details", S["section"]))
    avg_conf = session.get("avg_translation_confidence")
    conf_display = f"{avg_conf:.1f}%" if avg_conf is not None else "—"
    st = Table(
        [
            ["Started",      _fmt_ts(session.get("started_at")),
             "Ended",         _fmt_ts(session.get("ended_at"))],
            ["Duration",     _fmt_dur(session.get("duration_seconds")),
             "Avg Confidence", conf_display],
            ["ATS Category", ats_text,
             "Nurse Confirmed", "Yes ✓" if session.get("nurse_confirmed_ats") else "No"],
        ],
        colWidths=col_widths,
    )
    st.setStyle(_data_table_style(ats_row=2, ats_colour=ats_colour))
    story.append(st)

    # ── Vital signs ────────────────────────────────────────────────────────────
    story.append(Paragraph("Vital Signs", S["section"]))
    bp = (
        f"{session.get('bp_systolic')} / {session.get('bp_diastolic')} mmHg"
        if session.get("bp_systolic") else "—"
    )
    vt = Table(
        [
            ["Blood Pressure", bp,
             "Heart Rate",     _fmt_vital(session.get("heart_rate"), "bpm")],
            ["Temperature",    _fmt_vital(session.get("temperature"), "°F"),
             "Resp. Rate",     _fmt_vital(session.get("respiratory_rate"), "br/min")],
            ["SpO2",           _fmt_vital(session.get("spo2"), "%"), "", ""],
        ],
        colWidths=col_widths,
    )
    vt.setStyle(_data_table_style())
    story.append(vt)

    # ── Chat transcript ────────────────────────────────────────────────────────
    story.append(Paragraph("Conversation Transcript", S["section"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GREY, spaceAfter=6))

    if not messages:
        story.append(Paragraph("No messages recorded.", S["muted"]))
    else:
        for msg in messages:
            is_clinician = msg.get("sender") == "clinician"
            original     = msg.get("original_text") or ""
            translated   = msg.get("translated_text") or ""
            confidence   = msg.get("confidence")
            src_lang     = (msg.get("source_language") or "").upper()
            tgt_lang     = (msg.get("target_language") or "").upper()
            ts_str       = _fmt_ts(msg.get("created_at"))

            conf_str    = f"  ✓ {confidence:.0f}%" if confidence is not None else ""
            sender_name = "Clinician" if is_clinician else "Patient"
            lang_tag    = f"({src_lang} → {tgt_lang})" if src_lang and tgt_lang else ""
            row_bg      = colors.HexColor("#EFF6FF") if is_clinician else WHITE
            accent_col  = BRAND_BLUE if is_clinician else BORDER_GREY

            sender_line = Paragraph(
                f"<b>{sender_name}</b>"
                f"  <font color='#94A3B8' size='7.5'>{ts_str}{conf_str}</font>",
                S["chat_sender"],
            )
            original_para   = _smart_para(original,   S["chat_text"])
            translated_para = _smart_para(translated,  S["chat_trans"])

            if lang_tag and not _has_arabic(translated):
                translated_para = Paragraph(
                    f"<i>{translated}</i>  "
                    f"<font color='#94A3B8' size='7.5'>{lang_tag}</font>",
                    S["chat_trans"],
                )

            inner = Table(
                [[[sender_line, Spacer(1, 3), original_para, Spacer(1, 3), translated_para]]],
                colWidths=[COL_W - 6 * mm],
            )
            inner.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), row_bg),
                ("TOPPADDING",    (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ]))

            bubble = Table([[[inner]]], colWidths=[COL_W])
            bubble.setStyle(TableStyle([
                ("LEFTPADDING",   (0, 0), (-1, -1), 0),
                ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
                ("TOPPADDING",    (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("BOX",           (0, 0), (-1, -1), 0.75,
                 BRAND_BLUE if is_clinician else BORDER_GREY),
                ("LINEBEFORE",    (0, 0), (0, -1), 3, accent_col),
            ]))

            story.append(KeepTogether([bubble, Spacer(1, 5)]))

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GREY, spaceAfter=5))
    story.append(Paragraph(
        f"TRIBOT Clinical Documentation System  ·  Session {session_id}  ·  {generated_at}",
        S["footer"],
    ))

    doc.build(story, onFirstPage=_page_number, onLaterPages=_page_number)
    return buf.getvalue()
