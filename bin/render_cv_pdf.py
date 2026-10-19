#!/usr/bin/env python3
"""Render the concise academic CV from the site's maintained content.

Install dependencies: python -m pip install -r bin/requirements-cv.txt
Run: python bin/render_cv_pdf.py --date 2026-10-19

The PDF contains the CV data plus a curated selection of journal articles;
it links to the complete bibliography. Both delivery and hosting copies are
written by default. Pass --site-copy '' to disable the hosting copy.
"""

from __future__ import annotations

import argparse
from datetime import date, datetime
from html import escape
from pathlib import Path
import re
import shutil
from zoneinfo import ZoneInfo

import bibtexparser
from pylatexenc.latex2text import LatexNodes2Text
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
import yaml


ROOT = Path(__file__).resolve().parents[1]
SITE = "https://mhaut.github.io"
INK = colors.HexColor("#172A3A")
ACCENT = colors.HexColor("#176B78")
MUTED = colors.HexColor("#536473")
LINE = colors.HexColor("#D5E0E5")
LATEX = LatexNodes2Text()

# A purposeful selection: recent methods, applications and a foundational review.
# Metadata is always read from papers.bib, never copied into this generator.
SELECTED_DOIS = (
    "10.1016/j.eswa.2026.133926",
    "10.1109/tgrs.2026.3741200",
    "10.1016/j.engappai.2026.115757",
    "10.3390/electronics15184074",
    "10.1109/mgrs.2026.3716182",
    "10.1109/jstars.2026.3707402",
    "10.1109/tgrs.2025.3624287",
    "10.1016/j.isprsjprs.2019.09.006",
)


def plain(value: object) -> str:
    """Normalize typographic dashes and YAML values for consistent PDF text."""
    return str(value or "").translate(str.maketrans({"\u2010": "-", "\u2011": "-", "\u2012": "-", "\u2013": "-", "\u2014": "-", "\u2212": "-"}))


def link(url: str, label: str) -> str:
    if url.startswith("/"):
        url = SITE + url
    return f'<a href="{escape(url, quote=True)}" color="#176B78">{escape(plain(label))}</a>'


def markup(value: object) -> str:
    """Render the limited Markdown used by the maintained CV data safely."""
    text = plain(value)
    pieces = []
    end = 0
    for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
        pieces.append(escape(text[end : match.start()]))
        pieces.append(link(match.group(2), match.group(1)))
        end = match.end()
    pieces.append(escape(text[end:]))
    return "".join(pieces)


def register_fonts(font_dir: Path | None) -> None:
    candidates = [font_dir] if font_dir else [
        Path("/usr/share/fonts/truetype/dejavu"),
        Path("/usr/local/share/fonts/dejavu"),
        Path.home() / ".fonts",
    ]
    folder = next((p for p in candidates if p and (p / "DejaVuSans.ttf").is_file()), None)
    if folder is None:
        raise SystemExit("DejaVu fonts were not found. Install fonts-dejavu-core or pass --font-dir.")
    for face, filename in (
        ("CV", "DejaVuSans.ttf"),
        ("CV-Bold", "DejaVuSans-Bold.ttf"),
        ("CV-Italic", "DejaVuSans-Oblique.ttf"),
        ("CV-BoldItalic", "DejaVuSans-BoldOblique.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(face, str(folder / filename)))
    pdfmetrics.registerFontFamily("CV", normal="CV", bold="CV-Bold", italic="CV-Italic", boldItalic="CV-BoldItalic")


def make_styles() -> dict[str, ParagraphStyle]:
    body = ParagraphStyle("Body", fontName="CV", fontSize=9.1, leading=13.1, textColor=INK, spaceAfter=4.5, alignment=TA_LEFT)
    return {
        "body": body,
        "service": ParagraphStyle("Service", parent=body, spaceAfter=2.5),
        "small": ParagraphStyle("Small", parent=body, fontSize=8.1, leading=11.4, textColor=MUTED, spaceAfter=3),
        "entry": ParagraphStyle("Entry", parent=body, fontSize=9.25, leading=13.2, spaceAfter=3),
        "date": ParagraphStyle("Date", parent=body, fontSize=8.6, leading=12.5, textColor=ACCENT),
        "section": ParagraphStyle("Section", parent=body, fontName="CV-Bold", fontSize=11.7, leading=16, textColor=ACCENT, spaceBefore=13, spaceAfter=6, keepWithNext=True),
        "name": ParagraphStyle("Name", parent=body, fontName="CV-Bold", fontSize=25, leading=32, spaceAfter=4),
        "label": ParagraphStyle("Label", parent=body, fontSize=10.8, leading=16, spaceAfter=8),
        "publication": ParagraphStyle("Publication", parent=body, fontSize=8.5, leading=12.1, spaceAfter=2),
    }


def para(text: str, styles: dict, style: str = "body") -> Paragraph:
    return Paragraph(text, styles[style])


def period(item: dict) -> str:
    start = plain(item.get("start_date", ""))[:4]
    end = plain(item.get("end_date", ""))[:4]
    if item.get("end_date") == "present":
        end = "present"
    return start if start == end or not end else f"{start} - {end}"


def timeline(dates: str, content: list, styles: dict, gap: float = 7) -> KeepTogether:
    table = Table([[para(escape(dates), styles, "date"), content]], colWidths=[27 * mm, 145 * mm], hAlign="LEFT")
    table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (0, -1), 9), ("RIGHTPADDING", (1, 0), (1, -1), 0), ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0)]))
    return KeepTogether([table, Spacer(1, gap)])


def section(title: str, styles: dict) -> list:
    return [para(escape(title.upper()), styles, "section"), HRFlowable(width="100%", thickness=0.6, color=LINE, spaceAfter=7)]


def full_date(value: object) -> str:
    value = plain(value)
    return value[:10] if len(value) >= 10 else value


def bibliography() -> list[dict]:
    library = bibtexparser.parse_file(str(ROOT / "_bibliography/papers.bib"))
    entries = {}
    for entry in library.entries:
        if entry.entry_type == "article":
            fields = {field.key: field.value for field in entry.fields}
            entries[fields.get("doi", "").lower()] = fields
    missing = [doi for doi in SELECTED_DOIS if doi not in entries]
    if missing:
        raise SystemExit("Selected articles missing from papers.bib: " + ", ".join(missing))
    return [entries[doi] for doi in SELECTED_DOIS]


def decode_bib(text: str) -> str:
    return plain(LATEX.latex_to_text(text)).replace("\n", " ")


def abbreviated_authors(value: str) -> str:
    authors = []
    for name in value.split(" and "):
        name = decode_bib(name).strip()
        if "," in name:
            family, given = name.split(",", 1)
            initials = " ".join(word[0] + "." for word in given.split() if word)
            name = f"{initials} {family}"
        text = escape(name)
        if "Haut" in name:
            text = f"<b>{text}</b>"
        authors.append(text)
    return ", ".join(authors)


def render(output: Path, updated: date, font_dir: Path | None) -> None:
    register_fonts(font_dir)
    styles = make_styles()
    cv = yaml.safe_load((ROOT / "_data/cv.yml").read_text())["cv"]
    sections = cv["sections"]
    articles = bibliography()
    story = []

    story.append(para("Juan M. Haut", styles, "name"))
    story.append(para(markup(cv["label"]), styles, "label"))
    story.append(para("Department of Computer and Communication Technology<br/>University of Extremadura | Hyperspectral Computing Laboratory (HyperComp)", styles))
    story.append(para(" | ".join([link("mailto:" + cv["email"], cv["email"]), link(SITE, "Website"), link("https://scholar.google.com/citations?user=zLffeY8AAAAJ", "Google Scholar"), link("https://orcid.org/0000-0001-6701-961X", "ORCID"), link("https://github.com/mhaut", "GitHub")]), styles, "small"))
    story.append(para("Cáceres, Spain | ORCID: 0000-0001-6701-961X", styles, "small"))
    story.append(Spacer(1, 8))
    summary = cv["summary"].split("See the [publication list]")[0].strip()
    story.append(para(markup(summary), styles))

    story.extend(section("Academic appointments", styles))
    for job in sections["Experience"]:
        content = [para(f'<b>{markup(job["position"])}</b>', styles, "entry"), para(f'{markup(job["company"])} | {markup(job["location"])}', styles, "small")]
        if job.get("summary"):
            content.append(para(markup(job["summary"]), styles, "small"))
        if job.get("start_date") == 2026:
            content.extend(para(markup(value), styles, "small") for value in job.get("highlights", []))
        story.append(timeline(period(job), content, styles, gap=5))

    story.extend(section("Education", styles))
    for education in sections["Education"]:
        content = [para(f'<b>{markup(education["studyType"])} in {markup(education["area"])}</b> | {markup(education["institution"])}', styles, "entry")]
        if education["studyType"] == "PhD":
            content.append(para("International Mention; Sobresaliente Cum Laude; Outstanding Doctoral Award.<br/>Supervisors: Antonio Plaza and Javier Plaza.", styles, "small"))
        story.append(timeline(period(education), content, styles, gap=4))

    story.append(PageBreak())
    story.extend(section("Research leadership", styles))
    for project in sections.get("Projects", []):
        content = [para(f'<b>{markup(project["name"])}</b>', styles, "entry"), para(markup(project.get("summary", "")), styles)]
        if project.get("highlights"):
            content.append(para("; ".join(markup(value) for value in project["highlights"]), styles, "small"))
        content.append(para(f'{escape(full_date(project["start_date"]))} to {escape(full_date(project["end_date"]))}', styles, "small"))
        story.append(KeepTogether(content + [Spacer(1, 4)]))

    story.extend(section("Professional service", styles))
    for item in sections.get("Professional Service", []):
        story.append(para(markup(item["bullet"]), styles, "service"))

    story.extend(section("Awards and distinctions", styles))
    for award in sections.get("Awards", []):
        awarder = award.get("awarder", "").replace("University of Extremadura", "UEx")
        content = [para(f'<b>{markup(award["title"])}</b> | {markup(awarder)}', styles, "entry")]
        story.append(timeline(plain(award.get("date", ""))[:4], content, styles, gap=4))

    story.extend(section("Technical expertise", styles))
    for skill in sections.get("Skills", []):
        story.append(para(f'<b>{markup(skill["name"])}:</b> {markup(skill["keywords"])}', styles, "small"))

    story.extend(section("Accreditations and languages", styles))
    for certificate in sections.get("Certificates", []):
        story.append(para(f'{escape(full_date(certificate["date"]))} | <b>{markup(certificate["name"])}</b> | {markup(certificate["issuer"])}', styles, "small"))
    story.append(Spacer(1, 2))
    story.append(para(" | ".join(f'<b>{markup(item["name"])}</b>: {markup(item["summary"])}' for item in sections.get("Languages", [])), styles, "small"))

    story.append(PageBreak())
    story.extend(section("Selected journal articles", styles))
    story.append(para(f'A selection of {len(articles)} journal articles illustrating recent methods, applications and foundational work. Complete publications and current citation metrics: {link(SITE + "/publications/", "publication list")} and {link("https://scholar.google.com/citations?user=zLffeY8AAAAJ", "Google Scholar")}.', styles, "small"))
    story.append(Spacer(1, 8))
    for number, paper in enumerate(articles, 1):
        title = escape(decode_bib(paper["title"]))
        journal = escape(decode_bib(paper["journal"]))
        venue = f'<i>{journal}</i>'
        if paper.get("volume"):
            venue += f', {escape(paper["volume"])}'
            if paper.get("number"):
                venue += f'({escape(paper["number"])})'
        if paper.get("pages"):
            venue += f', {escape(plain(paper["pages"]).replace("--", "-"))}'
        venue += f' ({escape(paper["year"])}).'
        note = escape(decode_bib(paper.get("note", "")))
        content = [para(f'<b>{number:02d}. {title}</b>', styles, "publication"), para(abbreviated_authors(paper["author"]), styles, "publication"), para(venue + (" " + note if note else ""), styles, "publication"), para(link("https://doi.org/" + paper["doi"], "doi:" + paper["doi"]), styles, "small"), Spacer(1, 7)]
        story.append(KeepTogether(content))

    output.parent.mkdir(parents=True, exist_ok=True)
    date_label = updated.strftime("%d %B %Y").lstrip("0")

    def decorate(canvas, document):
        canvas.saveState()
        width, height = A4
        if document.page > 1:
            canvas.setFont("CV-Bold", 8.5)
            canvas.setFillColor(INK)
            canvas.drawString(19 * mm, height - 15 * mm, "JUAN M. HAUT")
            canvas.setFont("CV", 8)
            canvas.setFillColor(MUTED)
            canvas.drawRightString(width - 19 * mm, height - 15 * mm, "ACADEMIC CURRICULUM VITAE")
            canvas.setStrokeColor(LINE)
            canvas.line(19 * mm, height - 18 * mm, width - 19 * mm, height - 18 * mm)
        canvas.setStrokeColor(LINE)
        canvas.line(19 * mm, 16 * mm, width - 19 * mm, 16 * mm)
        canvas.setFont("CV", 7.2)
        canvas.setFillColor(MUTED)
        canvas.drawString(19 * mm, 11 * mm, f"Concise academic CV | Updated {date_label}")
        canvas.drawRightString(width - 19 * mm, 11 * mm, str(document.page))
        canvas.restoreState()

    document = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=19 * mm, leftMargin=19 * mm, topMargin=24 * mm, bottomMargin=23 * mm, title="Juan M. Haut - Concise Academic CV", author=cv["name"], subject=f"Academic curriculum vitae, updated {updated.isoformat()}", pageCompression=1, invariant=1)
    document.build(story, onFirstPage=decorate, onLaterPages=decorate)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/pdf/juan-m-haut-cv.pdf")
    parser.add_argument("--site-copy", default=str(ROOT / "assets/pdf/juan-m-haut-cv.pdf"))
    parser.add_argument("--date", type=date.fromisoformat, default=datetime.now(ZoneInfo("Europe/Madrid")).date())
    parser.add_argument("--font-dir", type=Path, help="Directory containing the four DejaVu Sans TTF faces")
    args = parser.parse_args()
    render(args.output, args.date, args.font_dir)
    if args.site_copy:
        hosted = Path(args.site_copy)
        hosted.parent.mkdir(parents=True, exist_ok=True)
        if hosted.resolve() != args.output.resolve():
            shutil.copyfile(args.output, hosted)
    print(f"Created {args.output}")


if __name__ == "__main__":
    main()
