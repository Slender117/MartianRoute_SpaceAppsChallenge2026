"""Convierte el reporte Markdown (subconjunto) a PDF con ReportLab."""

import re
import sys
from pathlib import Path

from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Image,
    KeepTogether,
    ListFlowable,
    ListItem,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

FONTS = "C:/Windows/Fonts/"
pdfmetrics.registerFont(TTFont("Body", FONTS + "arial.ttf"))
pdfmetrics.registerFont(TTFont("Body-Bold", FONTS + "arialbd.ttf"))
pdfmetrics.registerFont(TTFont("Body-Italic", FONTS + "ariali.ttf"))
pdfmetrics.registerFont(TTFont("Body-BoldItalic", FONTS + "arialbi.ttf"))
pdfmetrics.registerFont(TTFont("Mono", FONTS + "consola.ttf"))
pdfmetrics.registerFontFamily(
    "Body", normal="Body", bold="Body-Bold", italic="Body-Italic", boldItalic="Body-BoldItalic"
)

ACCENT = colors.HexColor("#b4532f")
INK = colors.HexColor("#222222")
MUTED = colors.HexColor("#666666")
CODE_BG = colors.HexColor("#f4efec")
RULE = colors.HexColor("#e2d6cf")

base = ParagraphStyle("base", fontName="Body", fontSize=10, leading=14.5, textColor=INK, alignment=TA_LEFT)
S = {
    "h1": ParagraphStyle("h1", parent=base, fontName="Body-Bold", fontSize=22, leading=27, textColor=ACCENT, spaceAfter=10),
    "h2": ParagraphStyle("h2", parent=base, fontName="Body-Bold", fontSize=15, leading=19, textColor=ACCENT, spaceBefore=16, spaceAfter=6),
    "h3": ParagraphStyle("h3", parent=base, fontName="Body-Bold", fontSize=12, leading=16, spaceBefore=10, spaceAfter=4),
    "p": ParagraphStyle("p", parent=base, spaceAfter=6),
    "cell": ParagraphStyle("cell", parent=base, fontSize=8.5, leading=11),
    "cellh": ParagraphStyle("cellh", parent=base, fontName="Body-Bold", fontSize=8.5, leading=11, textColor=colors.white),
    "code": ParagraphStyle("code", parent=base, fontName="Mono", fontSize=7.8, leading=10),
    "cap": ParagraphStyle("cap", parent=base, fontSize=8.5, textColor=MUTED, spaceAfter=10, alignment=1, spaceBefore=3),
}


def inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r'<font face="Mono" size="8.8" backColor="#f4efec">\1</font>', text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    return text.replace("²", "<super>2</super>")


def table(rows: list[str], width: float):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], cells[2:]
    data = [[Paragraph(inline(c), S["cellh"]) for c in header]]
    data += [[Paragraph(inline(c), S["cell"]) for c in r] for r in body]
    lens = [max(len(r[i]) if i < len(r) else 0 for r in cells) for i in range(len(header))]
    weights = [min(max(l, 9), 60) for l in lens]
    widths = [width * w / sum(weights) for w in weights]
    t = Table(data, colWidths=widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#faf6f4")]),
                ("GRID", (0, 0), (-1, -1), 0.4, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def image(path: Path, caption: str, width: float):
    w, h = PILImage.open(path).size
    draw_w = min(width * 0.55, w)
    draw_h = draw_w * h / w
    return KeepTogether([Image(str(path), draw_w, draw_h), Paragraph(caption, S["cap"])])


def build(md_path: Path, pdf_path: Path) -> None:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    doc = SimpleDocTemplate(
        str(pdf_path), pagesize=LETTER, leftMargin=2 * cm, rightMargin=2 * cm,
        topMargin=2 * cm, bottomMargin=2 * cm, title="Reporte de desarrollo: WazeMars",
        author="Equipo WazeMars",
    )
    width = doc.width
    story = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            j = i + 1
            while not lines[j].startswith("```"):
                j += 1
            pre = Preformatted("\n".join(lines[i + 1 : j]), S["code"])
            t = Table([[pre]], colWidths=[width])
            t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), CODE_BG),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 6),
                                   ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
            story += [t, Spacer(1, 8)]
            i = j + 1
        elif line.startswith("|"):
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            story += [table(lines[i:j], width), Spacer(1, 10)]
            i = j
        elif m := re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line):
            story.append(image(md_path.parent / m.group(2), m.group(1), width))
            i += 1
        elif m := re.match(r"(#{1,3}) (.*)", line):
            story.append(Paragraph(inline(m.group(2)), S[f"h{len(m.group(1))}"]))
            i += 1
        elif re.match(r"(\s*)(- |\d+\. )", line):
            while i < len(lines) and re.match(r"(\s*)(- |\d+\. )", lines[i]):
                indent = len(lines[i]) - len(lines[i].lstrip())
                m2 = re.match(r"\s*(- |\d+\. )(.*)", lines[i])
                bullet = "•" if m2.group(1) == "- " else m2.group(1).strip()
                parts = [inline(m2.group(2))]
                i += 1
                # continuación indentada sin viñeta
                while i < len(lines) and lines[i].startswith("   ") and lines[i].strip() and not re.match(r"\s*(- |\d+\. )", lines[i]):
                    parts.append(inline(lines[i].strip()))
                    i += 1
                left = 16 + indent * 5
                style = ParagraphStyle("li", parent=S["p"], leftIndent=left, bulletIndent=left - 12, spaceAfter=3)
                story.append(Paragraph("<br/>".join(parts), style, bulletText=bullet))
            story.append(Spacer(1, 4))
        elif line.strip() == "":
            i += 1
        else:
            # párrafo: une líneas consecutivas; las que terminan un bloque de metadatos se separan
            j = i
            parts = []
            while j < len(lines) and lines[j].strip() and not re.match(r"(#|\||```|- |\d+\. |!\[)", lines[j]):
                parts.append(inline(lines[j]))
                j += 1
            story.append(Paragraph("<br/>".join(parts), S["p"]))
            i = j

    def footer(canvas, doc_):
        canvas.saveState()
        canvas.setFont("Body", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(2 * cm, 1.2 * cm, "WazeMars · Reporte de desarrollo")
        canvas.drawRightString(LETTER[0] - 2 * cm, 1.2 * cm, f"Página {doc_.page}")
        canvas.restoreState()

    doc.build(story, onFirstPage=footer, onLaterPages=footer)


if __name__ == "__main__":
    build(Path(sys.argv[1]), Path(sys.argv[2]))
