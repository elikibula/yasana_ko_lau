from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.http import HttpResponse
from PIL import Image, ImageDraw, ImageFont


PAGE_WIDTH = 1240
PAGE_HEIGHT = 1754
MARGIN = 86
NAVY = (27, 42, 74)
GOLD = (201, 168, 76)
EARTH = (139, 94, 60)
CREAM = (253, 250, 245)
TEXT = (31, 41, 55)
MUTED = (92, 104, 120)
LINE = (220, 210, 190)


def _font(size, bold=False):
    names = ["arialbd.ttf" if bold else "arial.ttf", "calibrib.ttf" if bold else "calibri.ttf"]
    for name in names:
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


FONT_TITLE = _font(42, bold=True)
FONT_H1 = _font(30, bold=True)
FONT_H2 = _font(22, bold=True)
FONT_BODY = _font(18)
FONT_BODY_BOLD = _font(18, bold=True)
FONT_SMALL = _font(14)
FONT_SMALL_BOLD = _font(14, bold=True)


def _text(value):
    if value in (None, ""):
        return "-"
    return " ".join(str(value).replace("\r", " ").replace("\n", " ").split())


def _wrap(draw, text, font, width):
    words = _text(text).split()
    lines = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines or ["-"]


class ReportPdf:
    def __init__(self, title, subtitle, meta_rows, filename):
        self.title = title
        self.subtitle = subtitle
        self.meta_rows = meta_rows
        self.filename = filename
        self.pages = []
        self.page = None
        self.draw = None
        self.y = 0
        self.page_number = 0
        self._new_page(first=True)

    def _new_page(self, first=False):
        self.page_number += 1
        self.page = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), CREAM)
        self.draw = ImageDraw.Draw(self.page)
        self.pages.append(self.page)
        self._draw_bands()
        self._draw_header(first=first)
        self.y = 370 if first else 210

    def _draw_bands(self):
        colors = [NAVY, GOLD, EARTH, GOLD]
        block = PAGE_WIDTH // 24
        for i in range(24):
            self.draw.rectangle((i * block, 0, (i + 1) * block, 28), fill=colors[i % len(colors)])
            self.draw.rectangle((i * block, PAGE_HEIGHT - 28, (i + 1) * block, PAGE_HEIGHT), fill=colors[(i + 1) % len(colors)])

    def _draw_header(self, first=False):
        self.draw.rectangle((0, 28, PAGE_WIDTH, 172 if first else 145), fill=NAVY)
        logo_path = Path(settings.BASE_DIR) / "static" / "images" / "LauLogo.png"
        if logo_path.exists():
            with Image.open(logo_path) as logo:
                logo.thumbnail((112, 112))
                x = MARGIN
                y = 46
                if logo.mode == "RGBA":
                    self.page.paste(logo, (x, y), logo)
                else:
                    self.page.paste(logo.convert("RGB"), (x, y))
        self.draw.text((MARGIN + 135, 58), "YASANA KO LAU", font=FONT_H1, fill=GOLD)
        self.draw.text((MARGIN + 135, 96), "Provincial Council Report", font=FONT_BODY, fill=CREAM)
        self.draw.text((PAGE_WIDTH - MARGIN - 120, 96), f"Page {self.page_number}", font=FONT_SMALL, fill=CREAM)
        if first:
            self.draw.text((MARGIN, 210), self.title, font=FONT_TITLE, fill=NAVY)
            for index, line in enumerate(_wrap(self.draw, self.subtitle, FONT_BODY, PAGE_WIDTH - (MARGIN * 2))[:3]):
                self.draw.text((MARGIN, 270 + (index * 28)), line, font=FONT_BODY, fill=TEXT)
            self._draw_meta_box(330)

    def _draw_meta_box(self, y):
        box_h = 26 + (len(self.meta_rows) * 30)
        self.draw.rounded_rectangle((MARGIN, y, PAGE_WIDTH - MARGIN, y + box_h), radius=12, fill=(255, 255, 255), outline=LINE)
        cy = y + 16
        for label, value in self.meta_rows:
            self.draw.text((MARGIN + 24, cy), _text(label).upper(), font=FONT_SMALL_BOLD, fill=EARTH)
            self.draw.text((MARGIN + 260, cy), _text(value), font=FONT_SMALL, fill=TEXT)
            cy += 30

    def _ensure_space(self, needed):
        if self.y + needed > PAGE_HEIGHT - 90:
            self._new_page()

    def page_break(self):
        self._new_page()

    def section(self, title):
        self._ensure_space(78)
        self.draw.rounded_rectangle((MARGIN, self.y, PAGE_WIDTH - MARGIN, self.y + 52), radius=8, fill=NAVY)
        self.draw.text((MARGIN + 18, self.y + 14), _text(title), font=FONT_H2, fill=GOLD)
        self.y += 70

    def key_values(self, rows):
        label_w = 360
        value_w = PAGE_WIDTH - (MARGIN * 2) - label_w - 32
        for label, value in rows:
            label_lines = _wrap(self.draw, label, FONT_SMALL_BOLD, label_w - 24)
            value_lines = _wrap(self.draw, value, FONT_BODY, value_w - 24)
            line_count = max(len(label_lines), len(value_lines))
            row_h = max(48, 18 + (line_count * 25))
            self._ensure_space(row_h + 8)
            self.draw.rounded_rectangle((MARGIN, self.y, PAGE_WIDTH - MARGIN, self.y + row_h), radius=6, fill=(255, 255, 255), outline=LINE)
            ly = self.y + 14
            for line in label_lines:
                self.draw.text((MARGIN + 16, ly), line, font=FONT_SMALL_BOLD, fill=EARTH)
                ly += 22
            vy = self.y + 14
            for line in value_lines:
                self.draw.text((MARGIN + label_w + 16, vy), line, font=FONT_BODY, fill=TEXT)
                vy += 25
            self.y += row_h + 8

    def child_rows(self, rows):
        if not rows:
            self.key_values([("Records", "No records")])
            return
        for index, row in enumerate(rows, start=1):
            self._ensure_space(42)
            self.draw.text((MARGIN, self.y), f"Record {index}", font=FONT_BODY_BOLD, fill=NAVY)
            self.y += 32
            self.key_values(row)
            self.y += 8

    def audit_trail(self, rows):
        self.page_break()
        self.section("Audit Trail")
        if not rows:
            self.key_values([("iTukutuku", "E se bera ni dua na veivakadonui e volai.")])
            return
        self.child_rows(rows)

    def bytes(self):
        output = BytesIO()
        first, *rest = self.pages
        first.save(output, format="PDF", save_all=True, append_images=rest, resolution=150.0)
        return output.getvalue()


def report_pdf_response(title, subtitle, meta_rows, sections, child_sections, filename, audit_rows=None):
    pdf = ReportPdf(title, subtitle, meta_rows, filename)
    for section_title, rows in sections:
        pdf.section(section_title)
        pdf.key_values(rows)
    for section_title, rows in child_sections:
        pdf.section(section_title)
        pdf.child_rows(rows)
    if audit_rows is not None:
        pdf.audit_trail(audit_rows)

    response = HttpResponse(pdf.bytes(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
