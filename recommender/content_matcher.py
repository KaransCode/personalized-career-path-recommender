"""Cosine similarity between a candidate vector and every role vector."""
from sklearn.metrics.pairwise import cosine_similarity

from .vectorizer import build_vectorizer_and_matrix


def content_similarity_scores(role_skills: dict[str, list[str]], candidate_skills: list[str]) -> list[tuple[str, float]]:
    """Return [(role_name, similarity_score), ...] sorted descending."""
    candidate_vector, role_vectors, role_names = build_vectorizer_and_matrix(role_skills, candidate_skills)
    sims = cosine_similarity(candidate_vector, role_vectors)[0]
    scored = list(zip(role_names, (float(s) for s in sims)))
    return sorted(scored, key=lambda x: x[1], reverse=True)
