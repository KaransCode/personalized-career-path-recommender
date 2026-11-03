"""Top-level entry point: PDF path -> clean candidate dict."""
from .parser import extract_text_from_pdf
from .extractor import extract_entities
from .normalizer import normalize_candidate


def parse_resume(pdf_path: str) -> dict:
    """Chain parsing -> extraction -> normalization for a single resume."""
    raw_text = extract_text_from_pdf(pdf_path)
    entities = extract_entities(raw_text)
    return normalize_candidate(entities)
