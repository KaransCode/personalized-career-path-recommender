"""Pull structured entities (name, skills, roles, experience) out of raw
resume text using spaCy + simple heuristics."""
import json
import re
from pathlib import Path

import spacy

_SKILLS_PATH = Path(__file__).resolve().parent.parent / "data" / "skills.json"

# Common resume section headers / job-title-ish keywords used as weak
# signals for role extraction. This is intentionally pragmatic, not a
# full NER-trained model.
_ROLE_KEYWORDS = [
    "engineer", "developer", "scientist", "analyst", "manager", "intern",
    "consultant", "architect", "designer", "lead", "specialist",
]

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def _load_skills_taxonomy() -> list[str]:
    with open(_SKILLS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_name(text: str, doc=None) -> str:
    """Best-effort candidate name: first PERSON entity, else first line."""
    doc = doc or _get_nlp()(text[:1000])
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text.strip()
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    return first_line.strip()[:80]


def extract_skills(text: str, taxonomy: list[str] | None = None) -> list[str]:
    """Match resume text against a known skills taxonomy (case-insensitive,
    whole-word/phrase match)."""
    taxonomy = taxonomy or _load_skills_taxonomy()
    lowered = text.lower()
    found = []
    for skill in taxonomy:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill.lower()) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, lowered):
            found.append(skill.lower())
    return sorted(set(found))


def extract_roles(text: str) -> list[str]:
    """Pull role/job-title-like lines using keyword heuristics."""
    roles = []
    for line in text.splitlines():
        clean = line.strip()
        if not clean or len(clean) > 80:
            continue
        lowered = clean.lower()
        if any(kw in lowered for kw in _ROLE_KEYWORDS):
            # Strip trailing dates/company info after a pipe or dash-date pattern
            candidate = re.split(r"\s[-–|]\s", clean)[0].strip()
            if 2 <= len(candidate.split()) <= 6:
                roles.append(candidate)
    # de-duplicate while preserving order
    seen = set()
    unique_roles = []
    for r in roles:
        key = r.lower()
        if key not in seen:
            seen.add(key)
            unique_roles.append(r)
    return unique_roles


def extract_years_experience(text: str) -> float:
    """Regex-based extraction of total years of experience from date
    ranges like 'Jan 2022 - Mar 2024' or '2021-2023'. Falls back to an
    explicit 'X years of experience' phrase if present."""
    explicit = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?\s+of\s+experience", text, re.I)
    if explicit:
        return float(explicit.group(1))

    year_ranges = re.findall(r"(20\d{2}|19\d{2})\s*[-–to]{1,3}\s*(20\d{2}|present|current)", text, re.I)
    total_months = 0
    from datetime import datetime
    current_year = datetime.now().year
    for start, end in year_ranges:
        start_year = int(start)
        end_year = current_year if end.lower() in ("present", "current") else int(end)
        if end_year >= start_year:
            total_months += (end_year - start_year) * 12
    return round(total_months / 12, 1)


def extract_entities(text: str) -> dict:
    doc = _get_nlp()(text[:5000])  # cap for performance on long resumes
    taxonomy = _load_skills_taxonomy()
    return {
        "name": extract_name(text, doc=doc),
        "skills": extract_skills(text, taxonomy),
        "roles": extract_roles(text),
        "years_experience": extract_years_experience(text),
    }
