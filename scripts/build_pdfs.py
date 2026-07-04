#!/usr/bin/env python3
"""Render the Kestrel markdown documents to PDF.

Usage (from the repo root):
    uv run --with reportlab python scripts/build_pdfs.py

Outputs:
    sla/carrier-sla.pdf             <- sla/carrier-sla.md
    policies/on-call-policy.pdf     <- policies/on-call-policy.md

Only the markdown subset used in these documents is supported: headings, paragraphs,
bullet and numbered lists, pipe tables, fenced code blocks, **bold** and `inline code`.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
JOBS = [
    ("sla/carrier-sla.md", "sla/carrier-sla.pdf", "Kestrel Carrier SLA Summary"),
    ("policies/on-call-policy.md", "policies/on-call-policy.pdf", "Kestrel On-Call Policy"),
]
INK = colors.HexColor("#1f2933")
ACCENT = colors.HexColor("#1b5e8c")
RULE = colors.HexColor("#c5ced6")
HEAD_BG = colors.HexColor("#e6eef4")


def make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=base["BodyText"], fontName="Helvetica",
                          fontSize=9.5, leading=13.5, textColor=INK, alignment=TA_LEFT,
                          spaceAfter=5)
    return {
        "body": body,
        "h1": ParagraphStyle("h1", parent=body, fontName="Helvetica-Bold", fontSize=20,
                             leading=24, textColor=ACCENT, spaceAfter=10),
        "h2": ParagraphStyle("h2", parent=body, fontName="Helvetica-Bold", fontSize=13,
                             leading=17, textColor=ACCENT, spaceBefore=10, spaceAfter=5),
        "h3": ParagraphStyle("h3", parent=body, fontName="Helvetica-Bold", fontSize=10.5,
                             leading=14, spaceBefore=6, spaceAfter=3),
        "cell": ParagraphStyle("cell", parent=body, fontSize=8.3, leading=10.5, spaceAfter=0),
        "cellh": ParagraphStyle("cellh", parent=body, fontName="Helvetica-Bold", fontSize=8.3,
                                leading=10.5, spaceAfter=0),
        "code": ParagraphStyle("code", parent=body, fontName="Courier", fontSize=8,
                               leading=10, backColor=colors.HexColor("#f3f5f7"),
                               borderPadding=4, spaceAfter=7),
    }


def inline(text: str) -> str:
    """Convert the inline markdown subset to reportlab paragraph markup."""
    out = escape(text)
    out = re.sub(r"`([^`]+)`", r'<font face="Courier" size="8.5">\1</font>', out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)
    return out


def split_row(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def build_table(rows: list[str], st: dict[str, ParagraphStyle], width: float) -> Table:
    header, *body = [split_row(r) for r in rows if not re.match(r"^\|[\s:|-]+\|$", r.strip())]
    data = [[Paragraph(inline(c), st["cellh"]) for c in header]]
    for row in body:
        row += [""] * (len(header) - len(row))
        data.append([Paragraph(inline(c), st["cell"]) for c in row[: len(header)]])
    table = Table(data, colWidths=[width / len(header)] * len(header), repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), HEAD_BG),
        ("GRID", (0, 0), (-1, -1), 0.4, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return table


def list_flowable(items: list[str], ordered: bool, st: dict[str, ParagraphStyle]):
    return ListFlowable(
        [ListItem(Paragraph(inline(i), st["body"]), leftIndent=14) for i in items],
        bulletType="1" if ordered else "bullet",
        bulletFontSize=8 if not ordered else 9,
        leftIndent=14,
    )


def parse(md: str, st: dict[str, ParagraphStyle], width: float) -> list:
    flow: list = []
    lines = md.splitlines()
    i = 0
    para: list[str] = []

    def flush_para() -> None:
        if para:
            flow.append(Paragraph(inline(" ".join(para)), st["body"]))
            para.clear()

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_para()
            i += 1
            code: list[str] = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            flow.append(Preformatted("\n".join(code), st["code"]))
        elif stripped.startswith("|"):
            flush_para()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i])
                i += 1
            flow += [build_table(rows, st, width), Spacer(1, 6)]
            continue
        elif m := re.match(r"^(#{1,3})\s+(.*)", stripped):
            flush_para()
            flow.append(Paragraph(inline(m.group(2)), st[f"h{len(m.group(1))}"]))
        elif re.match(r"^([-*]|\d+\.)\s+", stripped):
            flush_para()
            ordered = bool(re.match(r"^\d+\.", stripped))
            items: list[str] = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
                # continuation lines belong to the previous item
                while i < len(lines) and lines[i].startswith("  ") and lines[i].strip() \
                        and not re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                    items[-1] += " " + lines[i].strip()
                    i += 1
            flow.append(list_flowable(items, ordered, st))
            continue
        elif not stripped:
            flush_para()
        else:
            para.append(stripped)
        i += 1
    flush_para()
    return flow


def footer(title: str):
    def draw(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#6b7785"))
        canvas.drawString(20 * mm, 12 * mm, f"Kestrel Freight  |  {title}")
        canvas.drawRightString(A4[0] - 20 * mm, 12 * mm, f"Page {doc.page}")
        canvas.setStrokeColor(RULE)
        canvas.line(20 * mm, 16 * mm, A4[0] - 20 * mm, 16 * mm)
        canvas.restoreState()
    return draw


def render(src: Path, dst: Path, title: str) -> int:
    st = make_styles()
    doc = SimpleDocTemplate(str(dst), pagesize=A4, title=title, author="Kestrel Freight",
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=22 * mm)
    width = A4[0] - 40 * mm
    flow = parse(src.read_text(encoding="utf-8"), st, width)
    doc.build(flow, onFirstPage=footer(title), onLaterPages=footer(title))
    return doc.page


def main() -> int:
    for rel_src, rel_dst, title in JOBS:
        pages = render(ROOT / rel_src, ROOT / rel_dst, title)
        print(f"wrote {rel_dst} ({pages} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
