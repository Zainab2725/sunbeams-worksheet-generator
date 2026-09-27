"""
pdf_exporter.py

Turns the AI-generated worksheet JSON into a printable PDF using
fpdf2, with a Urdu-script-capable font embedded (e.g. Noto Nastaliq
Urdu) so both English and Urdu render correctly.

Urdu is a right-to-left, cursive-joining script, so raw Unicode text
does NOT render correctly in most PDF libraries by default. We use
arabic_reshaper + python-bidi to shape and reorder Urdu text before
handing it to fpdf2. If those packages aren't available, we fall back
to printing the raw string (readable in the app, may look broken in
the PDF) rather than crashing the whole export.

IMPORTANT: You must supply a .ttf font that supports Urdu/Nastaliq
script (e.g. download "Noto Nastaliq Urdu" from Google Fonts) and
place it at fonts/NotoNastaliqUrdu.ttf relative to this project.
"""

import os
from fpdf import FPDF

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _RTL_SUPPORT = True
except ImportError:
    _RTL_SUPPORT = False

FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "fonts", "NotoNastaliqUrdu.ttf")
FONT_NAME = "NotoNastaliqUrdu"


def _shape_urdu(text: str) -> str:
    """Reshape + reorder Urdu/Arabic-script text for correct PDF rendering."""
    if not text:
        return text
    if not _RTL_SUPPORT:
        return text
    try:
        reshaped = arabic_reshaper.reshape(text)
        return get_display(reshaped)
    except Exception:
        return text


def _contains_urdu(text: str) -> bool:
    """Rough check: does this string contain Arabic-script (Urdu) characters?"""
    return any("\u0600" <= ch <= "\u06FF" for ch in text)


class WorksheetPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        self._font_loaded = False
        if os.path.exists(FONT_PATH):
            self.add_font(FONT_NAME, "", FONT_PATH)
            self._font_loaded = True

    def _set_font_for_text(self, text: str, size: int, style: str = ""):
        if self._font_loaded:
            self.set_font(FONT_NAME, style, size)
        else:
            # Fallback -- will not render Urdu correctly, but keeps the
            # PDF export from crashing if the font file isn't present yet.
            self.set_font("Helvetica", style, size)

    def write_line(self, text: str, size: int = 12, style: str = ""):
        display_text = _shape_urdu(text) if _contains_urdu(text) else text
        self._set_font_for_text(text, size, style)
        self.multi_cell(0, 8, display_text)
        self.ln(1)


def export_worksheet_pdf(worksheet: dict, output_path: str = "worksheet.pdf") -> str:
    """
    Builds a printable PDF from the worksheet dict:
      - Page 1+: title, bilingual instructions, questions
      - Final page: answer key (kept separate so it can be withheld from students)
    Returns the output_path written.
    """
    pdf = WorksheetPDF()

    if not pdf._font_loaded:
        print(
            "WARNING: Urdu font not found at "
            f"{os.path.abspath(FONT_PATH)}. Urdu text will not render "
            "correctly. Download 'Noto Nastaliq Urdu' from Google Fonts "
            "and place it at that path."
        )

    # --- Questions page(s) ---
    pdf.add_page()
    pdf.write_line(worksheet.get("worksheet_title", "Worksheet"), size=16, style="B")
    pdf.ln(2)

    if worksheet.get("instructions_english"):
        pdf.write_line(worksheet["instructions_english"], size=11)
    if worksheet.get("instructions_urdu"):
        pdf.write_line(worksheet["instructions_urdu"], size=11)
    pdf.ln(4)

    for i, question in enumerate(worksheet.get("questions", []), start=1):
        pdf.write_line(f"{i}. {question}", size=12)
        pdf.ln(2)

    # --- Answer key page (separate, teacher-only) ---
    pdf.add_page()
    pdf.write_line("Answer Key / Teacher Copy", size=14, style="B")
    pdf.ln(2)
    for i, answer in enumerate(worksheet.get("answer_key", []), start=1):
        pdf.write_line(f"{i}. {answer}", size=12)
        pdf.ln(1)

    pdf.output(output_path)
    return output_path


if __name__ == "__main__":
    sample = {
        "worksheet_title": "Urdu Practice: کھانا",
        "instructions_english": "Read and complete each item below.",
        "instructions_urdu": "نیچے دیے گئے ہر سوال کو پڑھیں اور مکمل کریں۔",
        "questions": ["Write the letter کھ with a short vowel.", "Join کھ + ا"],
        "answer_key": ["کھ", "کھا"],
    }
    path = export_worksheet_pdf(sample, "sample_worksheet.pdf")
    print(f"Written: {path}")
