"""Combine content similarity + graph signal into one ranked list with
human-readable explanations."""

CONTENT_WEIGHT = 0.6
GRAPH_WEIGHT = 0.4
TOP_K = 5


def _explanation(role: str, overlap: list[str], required: list[str], is_next_role: bool) -> str:
    parts = [f"Matches {len(overlap)}/{len(required)} required skills"]
    if is_next_role:
        parts.append("one step from your current role via typical progression")
    return "; ".join(parts) + "."


def rank_roles(
    candidate_skills: list[str],
    role_skills: dict[str, list[str]],
    content_scores: list[tuple[str, float]],
    graph_scores: dict[str, float],
    next_roles: list[str],
    top_k: int = TOP_K,
) -> list[dict]:
    content_lookup = dict(content_scores)
    candidate_skill_set = set(candidate_skills)

    combined = []
    for role in role_skills:
        content_score = content_lookup.get(role, 0.0)
        graph_score = graph_scores.get(role, 0.0)
        final_score = CONTENT_WEIGHT * content_score + GRAPH_WEIGHT * graph_score

        required = role_skills[role]
        overlap = [s for s in required if s in candidate_skill_set]
        missing = [s for s in required if s not in candidate_skill_set]

        combined.append({
            "role": role,
            "score": round(final_score, 4),
            "explanation": _explanation(role, overlap, required, role in next_roles),
            "missing_skills": sorted(missing),
        })

    combined.sort(key=lambda x: x["score"], reverse=True)
    return combined[:top_k]


def recommend(candidate_dict: dict, role_skills: dict[str, list[str]], next_roles: list[str] | None = None, top_k: int = TOP_K) -> list[dict]:
    """Full pipeline: candidate + role/skill data -> ranked recommendations.

    `role_skills` and `next_roles` are normally sourced from Neo4j via
    graph/queries.py (get_all_roles_with_skills, get_next_roles), but are
    passed explicitly here so this function stays testable without a live
    database connection.
    """
    from .content_matcher import content_similarity_scores
    from .graph_signal import compute_graph_scores

    next_roles = next_roles or []
    candidate_skills = candidate_dict.get("skills", [])

    content_scores = content_similarity_scores(role_skills, candidate_skills)
    graph_scores = compute_graph_scores(list(role_skills.keys()), next_roles)

    return rank_roles(candidate_skills, role_skills, content_scores, graph_scores, next_roles, top_k=top_k)
