"""Standardize extracted resume fields: casing, whitespace, synonyms."""

SYNONYMS = {
    "ml": "machine learning",
    "ai": "artificial intelligence",
    "nlp": "natural language processing",
    "react.js": "react",
    "reactjs": "react",
    "nodejs": "node.js",
    "postgres": "postgresql",
    "js": "javascript",
    "ts": "typescript",
    "genai": "generative ai",
    "llms": "llm",
    "k8s": "kubernetes",
    "retrieval-augmented generation": "rag",
    "sklearn": "scikit-learn",
    "pyspark": "spark",
    "powerbi": "power bi",
}


def normalize_skill(skill: str) -> str:
    cleaned = skill.strip().lower()
    return SYNONYMS.get(cleaned, cleaned)


def normalize_skills(skills: list[str]) -> list[str]:
    normalized = {normalize_skill(s) for s in skills}
    return sorted(normalized)


def normalize_role(role: str) -> str:
    return " ".join(role.strip().split())


def normalize_roles(roles: list[str]) -> list[str]:
    normalized = [normalize_role(r) for r in roles]
    seen = set()
    unique = []
    for r in normalized:
        key = r.lower()
        if key not in seen:
            seen.add(key)
            unique.append(r)
    return unique


def normalize_candidate(candidate: dict) -> dict:
    return {
        "name": candidate.get("name", "").strip(),
        "skills": normalize_skills(candidate.get("skills", [])),
        "roles": normalize_roles(candidate.get("roles", [])),
        "years_experience": candidate.get("years_experience", 0.0),
    }
