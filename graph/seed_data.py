"""Seed the graph with common data/tech roles, their required skills, and
typical LEADS_TO career progressions. Safe to re-run: every write is a MERGE."""

ROLES = {
    "Data Analyst": ["sql", "excel", "python", "data analysis", "data visualization", "tableau", "power bi"],
    "Business Intelligence Analyst": ["sql", "power bi", "tableau", "data visualization", "data analysis", "etl"],
    "Data Engineer": ["python", "sql", "etl", "spark", "hadoop", "airflow", "aws"],
    "Data Scientist": ["python", "machine learning", "statistics", "pandas", "numpy", "scikit-learn", "sql"],
    "Machine Learning Engineer": ["python", "machine learning", "deep learning", "tensorflow", "pytorch", "docker", "aws"],
    "Deep Learning Engineer": ["python", "deep learning", "pytorch", "tensorflow", "computer vision", "natural language processing"],
    "NLP Engineer": ["python", "natural language processing", "deep learning", "pytorch", "machine learning"],
    "Computer Vision Engineer": ["python", "computer vision", "deep learning", "pytorch", "tensorflow"],
    "MLOps Engineer": ["docker", "kubernetes", "aws", "machine learning", "git", "airflow"],
    "AI Research Engineer": ["python", "deep learning", "machine learning", "statistics", "pytorch", "tensorflow"],
    "Backend Developer": ["python", "java", "sql", "rest api", "flask", "django", "git"],
    "Full Stack Developer": ["javascript", "react", "node.js", "sql", "rest api", "git"],
    "Frontend Developer": ["javascript", "typescript", "react", "git"],
    "Android Developer": ["kotlin", "android development", "jetpack compose", "room database", "mvvm", "firebase", "sqlite"],
    "Software Engineer": ["python", "java", "git", "sql", "rest api", "agile"],
    "DevOps Engineer": ["docker", "kubernetes", "aws", "linux", "git", "azure"],
    "Cloud Engineer": ["aws", "azure", "gcp", "docker", "kubernetes", "linux"],
    "Database Administrator": ["sql", "postgresql", "mysql", "mongodb", "neo4j"],
    "Product Analyst": ["sql", "data analysis", "data visualization", "communication", "excel"],
    "Engineering Manager": ["leadership", "communication", "agile", "python", "git"],
    "Generative AI Engineer": ["python", "generative ai", "prompt engineering", "rag", "langchain", "vector databases", "docker"],
    "Agentic AI Developer": ["python", "agentic ai", "langgraph", "rag", "rest api", "prompt engineering", "git"],
    "Analytics Engineer": ["sql", "dbt", "snowflake", "data modeling", "python", "git", "etl"],
    "Cybersecurity Analyst": ["cybersecurity", "networking", "linux", "siem", "incident response", "python"],
    "QA Automation Engineer": ["selenium", "python", "testing", "ci/cd", "git", "rest api", "agile"],
    "Site Reliability Engineer": ["linux", "kubernetes", "python", "monitoring", "ci/cd", "aws", "terraform"],
    "Data Architect": ["sql", "data modeling", "etl", "aws", "spark", "snowflake", "leadership"],
    "Technical Product Manager": ["product management", "sql", "communication", "agile", "data analysis", "roadmapping"],
    "UI/UX Designer": ["figma", "ux research", "wireframing", "prototyping", "communication", "css"],
    "Flutter Developer": ["flutter", "dart", "firebase", "rest api", "git", "state management"],
}

# Typical career-progression edges: (from_role, to_role)
LEADS_TO = [
    ("Data Analyst", "Data Scientist"),
    ("Data Analyst", "Business Intelligence Analyst"),
    ("Data Analyst", "Product Analyst"),
    ("Business Intelligence Analyst", "Data Engineer"),
    ("Data Scientist", "Machine Learning Engineer"),
    ("Data Scientist", "AI Research Engineer"),
    ("Machine Learning Engineer", "Deep Learning Engineer"),
    ("Machine Learning Engineer", "MLOps Engineer"),
    ("Deep Learning Engineer", "NLP Engineer"),
    ("Deep Learning Engineer", "Computer Vision Engineer"),
    ("Data Engineer", "MLOps Engineer"),
    ("Data Engineer", "Cloud Engineer"),
    ("Backend Developer", "Full Stack Developer"),
    ("Backend Developer", "Software Engineer"),
    ("Frontend Developer", "Full Stack Developer"),
    ("Full Stack Developer", "Software Engineer"),
    ("Android Developer", "Software Engineer"),
    ("Software Engineer", "Engineering Manager"),
    ("Software Engineer", "DevOps Engineer"),
    ("DevOps Engineer", "Cloud Engineer"),
    ("Cloud Engineer", "MLOps Engineer"),
    ("Database Administrator", "Data Engineer"),
    ("Machine Learning Engineer", "Generative AI Engineer"),
    ("NLP Engineer", "Generative AI Engineer"),
    ("Generative AI Engineer", "Agentic AI Developer"),
    ("Backend Developer", "Generative AI Engineer"),
    ("Data Analyst", "Analytics Engineer"),
    ("Analytics Engineer", "Data Engineer"),
    ("Data Engineer", "Data Architect"),
    ("Cloud Engineer", "Cybersecurity Analyst"),
    ("Software Engineer", "QA Automation Engineer"),
    ("QA Automation Engineer", "DevOps Engineer"),
    ("DevOps Engineer", "Site Reliability Engineer"),
    ("Cloud Engineer", "Site Reliability Engineer"),
    ("Product Analyst", "Technical Product Manager"),
    ("Software Engineer", "Technical Product Manager"),
    ("Frontend Developer", "UI/UX Designer"),
    ("Android Developer", "Flutter Developer"),
    ("Flutter Developer", "Software Engineer"),
]


def seed_roles_and_skills(driver):
    with driver.session() as session:
        for role_name, skills in ROLES.items():
            session.run("MERGE (r:Role {name: $role_name})", role_name=role_name)
            for skill in skills:
                session.run(
                    """
                    MERGE (s:Skill {name: $skill})
                    WITH s
                    MATCH (r:Role {name: $role_name})
                    MERGE (r)-[:REQUIRES_SKILL]->(s)
                    """,
                    skill=skill, role_name=role_name,
                )


def seed_progressions(driver):
    with driver.session() as session:
        for from_role, to_role in LEADS_TO:
            session.run(
                """
                MATCH (a:Role {name: $from_role})
                MATCH (b:Role {name: $to_role})
                MERGE (a)-[:LEADS_TO]->(b)
                """,
                from_role=from_role, to_role=to_role,
            )


def seed_all(driver):
    seed_roles_and_skills(driver)
    seed_progressions(driver)
