"""Graph schema: constraints for (:Candidate), (:Skill), (:Role)."""

CONSTRAINTS = [
    "CREATE CONSTRAINT candidate_id IF NOT EXISTS FOR (c:Candidate) REQUIRE c.candidate_id IS UNIQUE",
    "CREATE CONSTRAINT skill_name IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE",
    "CREATE CONSTRAINT role_name IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE",
]


def apply_schema(driver):
    with driver.session() as session:
        for stmt in CONSTRAINTS:
            session.run(stmt)
