"""Insert a parsed candidate (Phase 1 output) into the graph."""
import uuid


def insert_candidate(driver, candidate_dict: dict) -> str:
    """Create a (:Candidate) node with HAS_SKILL edges to matching/created
    (:Skill) nodes, and HELD_ROLE edges to matching/created (:Role) nodes.
    Returns the generated candidate_id."""
    candidate_id = str(uuid.uuid4())
    with driver.session() as session:
        session.run(
            """
            CREATE (c:Candidate {
                candidate_id: $candidate_id,
                name: $name,
                years_experience: $years_experience
            })
            """,
            candidate_id=candidate_id,
            name=candidate_dict.get("name", ""),
            years_experience=candidate_dict.get("years_experience", 0.0),
        )

        for skill in candidate_dict.get("skills", []):
            session.run(
                """
                MERGE (s:Skill {name: $skill})
                WITH s
                MATCH (c:Candidate {candidate_id: $candidate_id})
                MERGE (c)-[:HAS_SKILL]->(s)
                """,
                skill=skill, candidate_id=candidate_id,
            )

        for role in candidate_dict.get("roles", []):
            session.run(
                """
                MERGE (r:Role {name: $role})
                WITH r
                MATCH (c:Candidate {candidate_id: $candidate_id})
                MERGE (c)-[:HELD_ROLE]->(r)
                """,
                role=role, candidate_id=candidate_id,
            )

    return candidate_id
