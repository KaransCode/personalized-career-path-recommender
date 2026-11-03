"""Graph-based scoring: roles reachable via LEADS_TO from the candidate's
current/most-recent role get a boost."""


def compute_graph_scores(role_names: list[str], next_roles: list[str], boost: float = 1.0) -> dict[str, float]:
    """next_roles are roles directly reachable from the candidate's current
    role (via get_next_roles). They get `boost`; everything else gets 0.0.
    Scores are then min-max scaled to [0, 1] for consistent blending."""
    raw_scores = {role: (boost if role in next_roles else 0.0) for role in role_names}
    max_score = max(raw_scores.values()) if raw_scores else 0.0
    if max_score == 0:
        return {role: 0.0 for role in role_names}
    return {role: score / max_score for role, score in raw_scores.items()}
