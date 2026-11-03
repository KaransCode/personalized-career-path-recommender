import glob
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.pipeline import parse_resume

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample_resumes")


def _sample_pdfs():
    return sorted(glob.glob(os.path.join(SAMPLE_DIR, "*.pdf")))


def test_sample_resumes_exist():
    assert len(_sample_pdfs()) >= 2, "Need at least 2 sample resume PDFs for testing"


def test_parse_resume_returns_expected_keys():
    for pdf_path in _sample_pdfs():
        result = parse_resume(pdf_path)
        assert set(["name", "skills", "roles", "years_experience"]).issubset(result.keys())


def test_parse_resume_extracts_nonempty_skills():
    for pdf_path in _sample_pdfs():
        result = parse_resume(pdf_path)
        assert len(result["skills"]) > 0, f"No skills extracted from {pdf_path}"


def test_parse_resume_extracts_nonempty_roles():
    for pdf_path in _sample_pdfs():
        result = parse_resume(pdf_path)
        assert len(result["roles"]) > 0, f"No roles extracted from {pdf_path}"


def test_parse_resume_years_experience_is_numeric():
    for pdf_path in _sample_pdfs():
        result = parse_resume(pdf_path)
        assert isinstance(result["years_experience"], (int, float))
        assert result["years_experience"] >= 0
