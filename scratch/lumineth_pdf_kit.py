"""Boîte à outils de mise en page PDF pour les fiches Lumineth.

Reprend la charte graphique de ``scratch/build_pdf.py`` (parchemin / or / bleu nuit,
titres en OldEnglish) mais en A4 portrait, orientée texte plutôt que grands tableaux.

Le contenu d'un document est décrit sous forme de blocs ``(type, ...)`` et rendu par
``build_document`` — voir ``scratch/build_lumineth_pdfs.py`` pour les documents eux-mêmes.
"""
from __future__ import annotations

import os
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    NextPageTemplate, PageBreak, Flowable, KeepTogether,
)

pdfmetrics.registerFont(TTFont("OldEnglish", "C:/Windows/Fonts/OLDENGL.TTF"))

PAGE_W, PAGE_H = A4

# --- palette (identique à build_pdf.py) -------------------------------------
INK_BLACK    = colors.HexColor("#0b0d13")
NIGHT_BLUE   = colors.HexColor("#161a2b")
GOLD         = colors.HexColor("#b8912f")
GOLD_BRIGHT  = colors.HexColor("#f0cf6b")
GOLD_DIM     = colors.HexColor("#8a6d24")
PARCHMENT    = colors.HexColor("#f3ead6")
PARCHMENT_2  = colors.HexColor("#e9dcc0")
PARCHMENT_3  = colors.HexColor("#ded0ac")
STEEL        = colors.HexColor("#4a4536")
BLOOD_GREEN  = colors.HexColor("#2f6b32")
BLOOD_RED    = colors.HexColor("#8c1f1f")
QUARTZ       = colors.HexColor("#4a3f9e")

MARGIN = 16 * mm
TOP_MARGIN = 24 * mm
BOTTOM_MARGIN = 15 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

OUT_DIR = "scratch/output"

# --- styles ------------------------------------------------------------------
cover_title = ParagraphStyle(
    "cover_title", fontName="OldEnglish", fontSize=34, leading=40,
    textColor=GOLD_BRIGHT, alignment=TA_CENTER,
)
cover_subtitle = ParagraphStyle(
    "cover_subtitle", fontName="Times-Italic", fontSize=14, leading=19,
    textColor=PARCHMENT, alignment=TA_CENTER, spaceBefore=6,
)
cover_meta = ParagraphStyle(
    "cover_meta", fontName="Times-Roman", fontSize=10, leading=14,
    textColor=GOLD, alignment=TA_CENTER, spaceBefore=14,
)
cover_body = ParagraphStyle(
    "cover_body", fontName="Times-Roman", fontSize=10.5, leading=15,
    textColor=PARCHMENT_2, alignment=TA_LEFT, spaceBefore=8,
)
h1 = ParagraphStyle(
    "h1", fontName="OldEnglish", fontSize=21, leading=25,
    textColor=NIGHT_BLUE, spaceBefore=2, spaceAfter=5,
)
h2 = ParagraphStyle(
    "h2", fontName="Times-Bold", fontSize=12.5, leading=15,
    textColor=QUARTZ, spaceBefore=9, spaceAfter=3,
)
h3 = ParagraphStyle(
    "h3", fontName="Times-BoldItalic", fontSize=10.8, leading=13.5,
    textColor=NIGHT_BLUE, spaceBefore=6, spaceAfter=2,
)
body = ParagraphStyle(
    "body", fontName="Times-Roman", fontSize=9.8, leading=13.2,
    textColor=INK_BLACK, spaceAfter=4, alignment=TA_LEFT,
)
body_small = ParagraphStyle(
    "body_small", fontName="Times-Roman", fontSize=8.6, leading=11.4,
    textColor=STEEL, spaceAfter=3,
)
lead = ParagraphStyle(
    "lead", fontName="Times-Italic", fontSize=10.2, leading=14,
    textColor=STEEL, spaceAfter=6,
)
bullet = ParagraphStyle(
    "bullet", parent=body, leftIndent=9, bulletIndent=1, spaceAfter=2.5,
)
cell = ParagraphStyle(
    "cell", fontName="Times-Roman", fontSize=8.4, leading=10.6, textColor=INK_BLACK,
)
cell_b = ParagraphStyle(
    "cell_b", fontName="Times-Bold", fontSize=8.4, leading=10.6, textColor=NIGHT_BLUE,
)
cell_head = ParagraphStyle(
    "cell_head", fontName="Times-Bold", fontSize=8.2, leading=10.2, textColor=GOLD_BRIGHT,
)
box_title = ParagraphStyle(
    "box_title", fontName="Times-Bold", fontSize=9.6, leading=12,
    textColor=GOLD_BRIGHT, spaceAfter=2,
)
box_body = ParagraphStyle(
    "box_body", fontName="Times-Roman", fontSize=9.2, leading=12.4, textColor=PARCHMENT_2,
)
note_title = ParagraphStyle(
    "note_title", fontName="Times-Bold", fontSize=9.6, leading=12,
    textColor=NIGHT_BLUE, spaceAfter=2,
)
note_body = ParagraphStyle(
    "note_body", fontName="Times-Roman", fontSize=9.2, leading=12.4, textColor=INK_BLACK,
)


class SectionMarker(Flowable):
    """Flowable invisible : met à jour le titre courant affiché dans le bandeau."""

    def __init__(self, doc, title):
        super().__init__()
        self.doc = doc
        self.title = title

    def wrap(self, aw, ah):
        return (0, 0)

    def draw(self):
        self.doc.section_title = self.title


class HRule(Flowable):
    """Filet doré pleine largeur."""

    def __init__(self, width=CONTENT_W, thickness=0.7, color=GOLD_DIM, space=3):
        super().__init__()
        self.width = width
        self.thickness = thickness
        self.color = color
        self.space = space

    def wrap(self, aw, ah):
        return (self.width, self.thickness + 2 * self.space)

    def draw(self):
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(self.thickness)
        self.canv.line(0, self.space, self.width, self.space)


def _ornaments(c, m):
    c.setFillColor(GOLD)
    for x, y in [(m, m), (PAGE_W - m, m), (m, PAGE_H - m), (PAGE_W - m, PAGE_H - m)]:
        c.circle(x, y, 1.4 * mm, fill=1, stroke=0)


def _make_cover_bg(subtitle):
    def draw(c, doc):
        c.saveState()
        c.setFillColor(INK_BLACK)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        m = 9 * mm
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.5)
        c.rect(m, m, PAGE_W - 2 * m, PAGE_H - 2 * m, fill=0, stroke=1)
        c.setStrokeColor(GOLD_DIM)
        c.setLineWidth(0.55)
        c.rect(m + 3 * mm, m + 3 * mm, PAGE_W - 2 * m - 6 * mm, PAGE_H - 2 * m - 6 * mm,
               fill=0, stroke=1)
        _ornaments(c, m)
        c.setFillColor(GOLD)
        c.setFont("Times-Italic", 9)
        c.drawCentredString(PAGE_W / 2, m + 7 * mm, subtitle)
        c.restoreState()
    return draw


def _make_page_bg(running_head):
    def draw(c, doc):
        c.saveState()
        c.setFillColor(PARCHMENT)
        c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
        m = 7 * mm
        c.setStrokeColor(GOLD)
        c.setLineWidth(1.2)
        c.rect(m, m, PAGE_W - 2 * m, PAGE_H - 2 * m, fill=0, stroke=1)
        c.setStrokeColor(GOLD_DIM)
        c.setLineWidth(0.45)
        c.rect(m + 2 * mm, m + 2 * mm, PAGE_W - 2 * m - 4 * mm, PAGE_H - 2 * m - 4 * mm,
               fill=0, stroke=1)
        _ornaments(c, m)

        band_h = 8.5 * mm
        c.setFillColor(NIGHT_BLUE)
        c.rect(m, PAGE_H - m - band_h, PAGE_W - 2 * m, band_h, fill=1, stroke=0)
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.6)
        c.line(m, PAGE_H - m - band_h, PAGE_W - m, PAGE_H - m - band_h)
        c.setFont("Times-Bold", 8.6)
        c.setFillColor(GOLD_BRIGHT)
        c.drawString(m + 4 * mm, PAGE_H - m - band_h + 2.9 * mm, running_head)
        c.setFont("Times-Italic", 8.2)
        c.setFillColor(GOLD)
        c.drawRightString(PAGE_W - m - 4 * mm, PAGE_H - m - band_h + 2.9 * mm,
                          getattr(doc, "section_title", ""))

        c.setFillColor(STEEL)
        c.setFont("Times-Italic", 8)
        c.drawCentredString(PAGE_W / 2, m + 2.5 * mm, f"— {doc.page} —")
        c.restoreState()
    return draw


# --- fabrication de blocs -----------------------------------------------------

def dark_box(title, text, width=CONTENT_W):
    """Encadré bleu nuit / or — pour les points d'attention."""
    inner = []
    if title:
        inner.append(Paragraph(title, box_title))
    inner.append(Paragraph(text, box_body))
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NIGHT_BLUE),
        ("BOX", (0, 0), (-1, -1), 0.9, GOLD),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def light_box(title, text, width=CONTENT_W, accent=GOLD):
    """Encadré parchemin clair, filet coloré à gauche."""
    inner = []
    if title:
        inner.append(Paragraph(title, note_title))
    inner.append(Paragraph(text, note_body))
    t = Table([[inner]], colWidths=[width])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PARCHMENT_2),
        ("BOX", (0, 0), (-1, -1), 0.5, GOLD_DIM),
        ("LINEBEFORE", (0, 0), (0, -1), 2.4, accent),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def data_table(header, rows, col_widths, align_right=(), bold_first=True,
               font_size=8.4, head_bg=NIGHT_BLUE):
    """Tableau parchemin/or. ``rows`` = listes de chaînes (balisage Paragraph accepté)."""
    data = [[Paragraph(h, cell_head) for h in header]]
    for r in rows:
        line = []
        for i, v in enumerate(r):
            st = cell_b if (bold_first and i == 0) else cell
            line.append(Paragraph(str(v), st))
        data.append(line)
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), head_bg),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [PARCHMENT, PARCHMENT_2]),
        ("GRID", (0, 0), (-1, -1), 0.3, GOLD_DIM),
        ("BOX", (0, 0), (-1, -1), 0.8, GOLD),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    for c in align_right:
        style.append(("ALIGN", (c, 0), (c, -1), "RIGHT"))
    t.setStyle(TableStyle(style))
    return t


def render(doc, blocks):
    """Transforme une liste de blocs déclaratifs en flowables reportlab."""
    story = []
    for b in blocks:
        kind = b[0]
        if kind == "section":                       # nouvelle section + saut de page
            story.append(SectionMarker(doc, b[1]))
            story.append(PageBreak())
            story.append(Paragraph(b[1], h1))
            story.append(HRule())
        elif kind == "section_here":                # nouvelle section sans saut de page
            story.append(SectionMarker(doc, b[1]))
            story.append(Paragraph(b[1], h1))
            story.append(HRule())
        elif kind == "h2":
            story.append(Paragraph(b[1], h2))
        elif kind == "h3":
            story.append(Paragraph(b[1], h3))
        elif kind == "p":
            story.append(Paragraph(b[1], body))
        elif kind == "lead":
            story.append(Paragraph(b[1], lead))
        elif kind == "small":
            story.append(Paragraph(b[1], body_small))
        elif kind == "ul":
            for item in b[1]:
                story.append(Paragraph(item, bullet, bulletText="\u2022"))
            story.append(Spacer(1, 3))
        elif kind == "ol":
            for i, item in enumerate(b[1], 1):
                story.append(Paragraph(item, bullet, bulletText=f"{i}."))
            story.append(Spacer(1, 3))
        elif kind == "table":
            _, header, rows, widths = b[:4]
            opts = b[4] if len(b) > 4 else {}
            story.append(data_table(header, rows, widths, **opts))
            story.append(Spacer(1, 5))
        elif kind == "box":
            story.append(Spacer(1, 2))
            story.append(dark_box(b[1], b[2]))
            story.append(Spacer(1, 5))
        elif kind == "note":
            accent = b[3] if len(b) > 3 else GOLD
            story.append(Spacer(1, 2))
            story.append(light_box(b[1], b[2], accent=accent))
            story.append(Spacer(1, 5))
        elif kind == "keep":
            story.append(KeepTogether(render(doc, b[1])))
        elif kind == "rule":
            story.append(HRule())
        elif kind == "spacer":
            story.append(Spacer(1, b[1] * mm))
        elif kind == "pagebreak":
            story.append(PageBreak())
        else:
            raise ValueError(f"bloc inconnu : {kind}")
    return story


def build_document(filename, title, cover_title_text, cover_sub, cover_paragraphs,
                   running_head, blocks, cover_footer="Compendium Lumineth"):
    """Assemble et écrit un PDF : page de garde sombre puis pages parchemin."""
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, filename)
    doc = BaseDocTemplate(
        path, pagesize=A4, title=title, author="AoSPy",
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN,
    )
    doc.section_title = ""
    cover_frame = Frame(22 * mm, 22 * mm, PAGE_W - 44 * mm, PAGE_H - 44 * mm, id="cover")
    text_frame = Frame(MARGIN, BOTTOM_MARGIN, CONTENT_W,
                       PAGE_H - TOP_MARGIN - BOTTOM_MARGIN, id="text")
    doc.addPageTemplates([
        PageTemplate(id="Cover", frames=[cover_frame], onPage=_make_cover_bg(cover_footer)),
        PageTemplate(id="Text", frames=[text_frame], onPage=_make_page_bg(running_head)),
    ])

    story = [Spacer(1, 34 * mm), Paragraph(cover_title_text, cover_title)]
    if cover_sub:
        story.append(Paragraph(cover_sub, cover_subtitle))
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        f"Registre établi le {date.today().strftime('%d/%m/%Y')} — "
        "données Wahapedia du 26/05/2026", cover_meta))
    story.append(Spacer(1, 8 * mm))
    for para in cover_paragraphs:
        story.append(Paragraph(para, cover_body))
    # Le saut de page est indispensable : sans lui, le début du premier bloc
    # continue de couler dans le cadre de la couverture (texte sombre sur fond noir).
    story.append(NextPageTemplate("Text"))
    story.append(PageBreak())
    story += render(doc, blocks)
    doc.build(story)
    return path
