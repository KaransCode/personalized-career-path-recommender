"""Extract raw text from a PDF resume using PyPDF2."""
from PyPDF2 import PdfReader


def extract_text_from_pdf(pdf_path: str) -> str:
    """Return the concatenated text of every page in the PDF."""
    reader = PdfReader(pdf_path)
    pages_text = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages_text.append(text)
    return "\n".join(pages_text)
