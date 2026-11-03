import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ingestion.pipeline import parse_resume
from recommender.ranker import recommend
from graph.seed_data import ROLES, LEADS_TO

SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sample_resumes")


def _next_roles_for(role_name):
    return [to_r for (from_r, to_r) in LEADS_TO if from_r == role_name]


def test_recommend_returns_top5_with_valid_scores():
    candidate = parse_resume(os.path.join(SAMPLE_DIR, "resume_1.pdf"))
    recs = recommend(candidate, ROLES, next_roles=_next_roles_for("Data Analyst"))

    assert len(recs) == 5
    for rec in recs:
        assert set(["role", "score", "explanation", "missing_skills"]).issubset(rec.keys())
        assert 0.0 <= rec["score"] <= 1.0
        assert isinstance(rec["explanation"], str) and len(rec["explanation"]) > 0


def test_recommend_top_role_is_relevant_for_data_scientist_resume():
    candidate = parse_resume(os.path.join(SAMPLE_DIR, "resume_1.pdf"))
    recs = recommend(candidate, ROLES, next_roles=_next_roles_for("Data Scientist"))
    top_roles = [r["role"] for r in recs]
    # resume_1 is a Data Scientist / Data Analyst profile — expect a
    # data-flavoured role in the top 5, not something unrelated like
    # Android Developer.
    assert any(r in top_roles for r in ["Data Scientist", "Data Analyst", "Machine Learning Engineer", "Business Intelligence Analyst"])


def test_recommend_top_role_is_relevant_for_android_resume():
    candidate = parse_resume(os.path.join(SAMPLE_DIR, "resume_3.pdf"))
    recs = recommend(candidate, ROLES, next_roles=_next_roles_for("Android Developer"))
    top_roles = [r["role"] for r in recs]
    assert "Android Developer" in top_roles


def test_recommend_scores_are_sorted_descending():
    candidate = parse_resume(os.path.join(SAMPLE_DIR, "resume_2.pdf"))
    recs = recommend(candidate, ROLES)
    scores = [r["score"] for r in recs]
    assert scores == sorted(scores, reverse=True)
