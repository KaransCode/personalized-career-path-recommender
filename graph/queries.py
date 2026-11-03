"""Read queries used by the recommender and API layers."""


def get_candidate_skills(driver, candidate_id: str) -> list[str]:
    query = """
    MATCH (c:Candidate {candidate_id: $candidate_id})-[:HAS_SKILL]->(s:Skill)
    RETURN s.name AS skill
    """
    with driver.session() as session:
        result = session.run(query, candidate_id=candidate_id)
        return [record["skill"] for record in result]


def get_candidate_current_role(driver, candidate_id: str) -> str | None:
    """Best-effort 'current role' = most recently held role node, if any."""
    query = """
    MATCH (c:Candidate {candidate_id: $candidate_id})-[:HELD_ROLE]->(r:Role)
    RETURN r.name AS role
    LIMIT 1
    """
    with driver.session() as session:
        result = session.run(query, candidate_id=candidate_id)
        record = result.single()
        return record["role"] if record else None


def get_matching_roles(driver, candidate_id: str, limit: int = 10) -> list[dict]:
    """Roles ranked by number of overlapping skills with the candidate."""
    query = """
    MATCH (c:Candidate {candidate_id: $candidate_id})-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(r:Role)
    WITH r, count(DISTINCT s) AS overlap
    MATCH (r)-[:REQUIRES_SKILL]->(all_s:Skill)
    WITH r, overlap, count(DISTINCT all_s) AS total_required
    RETURN r.name AS role, overlap, total_required,
           toFloat(overlap) / total_required AS match_ratio
    ORDER BY overlap DESC, match_ratio DESC
    LIMIT $limit
    """
    with driver.session() as session:
        result = session.run(query, candidate_id=candidate_id, limit=limit)
        return [dict(record) for record in result]


def get_next_roles(driver, current_role: str) -> list[str]:
    """Roles directly reachable via LEADS_TO from the given role."""
    query = """
    MATCH (r:Role {name: $current_role})-[:LEADS_TO]->(next:Role)
    RETURN next.name AS role
    """
    with driver.session() as session:
        result = session.run(query, current_role=current_role)
        return [record["role"] for record in result]


def get_skill_gap(driver, candidate_id: str, target_role: str) -> list[str]:
    """Skills required by target_role that the candidate does NOT have."""
    query = """
    MATCH (r:Role {name: $target_role})-[:REQUIRES_SKILL]->(s:Skill)
    WHERE NOT EXISTS {
        MATCH (c:Candidate {candidate_id: $candidate_id})-[:HAS_SKILL]->(s)
    }
    RETURN s.name AS skill
    ORDER BY skill
    """
    with driver.session() as session:
        result = session.run(query, target_role=target_role, candidate_id=candidate_id)
        return [record["skill"] for record in result]


def get_role_skills(driver, role_name: str) -> list[str]:
    query = """
    MATCH (r:Role {name: $role_name})-[:REQUIRES_SKILL]->(s:Skill)
    RETURN s.name AS skill
    """
    with driver.session() as session:
        result = session.run(query, role_name=role_name)
        return [record["skill"] for record in result]


def get_all_roles_with_skills(driver) -> dict[str, list[str]]:
    """Used by the recommender to build TF-IDF vectors for every role."""
    query = """
    MATCH (r:Role)-[:REQUIRES_SKILL]->(s:Skill)
    RETURN r.name AS role, collect(s.name) AS skills
    """
    with driver.session() as session:
        result = session.run(query)
        return {record["role"]: record["skills"] for record in result}
