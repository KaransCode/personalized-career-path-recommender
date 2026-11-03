"""Turn skill lists into TF-IDF vectors so candidate <-> role similarity
can be computed with cosine similarity."""
from sklearn.feature_extraction.text import TfidfVectorizer


def _skills_to_doc(skills: list[str]) -> str:
    """Treat a skill list as a space-joined 'document'. Multi-word skills
    are joined with underscores so they act as single tokens."""
    return " ".join(skill.replace(" ", "_") for skill in skills)


def build_vectorizer_and_matrix(role_skills: dict[str, list[str]], candidate_skills: list[str]):
    """Fit a TfidfVectorizer over [candidate_doc] + [role docs] and return
    (vectorizer, candidate_vector, role_vectors, role_names)."""
    role_names = list(role_skills.keys())
    role_docs = [_skills_to_doc(role_skills[name]) for name in role_names]
    candidate_doc = _skills_to_doc(candidate_skills)

    corpus = [candidate_doc] + role_docs
    vectorizer = TfidfVectorizer()
    matrix = vectorizer.fit_transform(corpus)

    candidate_vector = matrix[0:1]
    role_vectors = matrix[1:]
    return candidate_vector, role_vectors, role_names
