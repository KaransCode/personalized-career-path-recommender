"""Flask API tying together ingestion, graph, and recommender layers.

Also serves the multi-page frontend, so the whole app is available at
http://localhost:5000/ with no separate web server.
"""
import json
import os
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from flask import Flask, request, jsonify, send_from_directory, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename

from ingestion.pipeline import parse_resume
from graph.connection import get_driver
from graph.loader import insert_candidate
from graph.queries import (
    get_candidate_skills,
    get_candidate_current_role,
    get_next_roles,
    get_all_roles_with_skills,
    get_skill_gap,
)
from graph.seed_data import ROLES, LEADS_TO
from recommender.ranker import recommend

ALLOWED_EXTENSIONS = {"pdf"}
FRONTEND_DIR = os.path.join(ROOT, "frontend")
DETAILS_PATH = os.path.join(ROOT, "data", "role_details.json")
TRENDS_PATH = os.path.join(ROOT, "data", "trends.json")
GUIDE_PATH = os.path.join(ROOT, "data", "skills_guide.json")
FRONTEND_EXTENSIONS = (".html", ".css", ".js", ".svg", ".png", ".ico")

app = Flask(__name__, static_folder=None)
CORS(app)


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_role_details() -> dict:
    return load_json(DETAILS_PATH)


def build_roles_payload() -> dict:
    """Merge the seeded role/skill data with descriptions and salary bands.
    Read on each request so edits to role_details.json show up immediately."""
    details = load_role_details()
    trends = load_json(TRENDS_PATH)["roles"]
    roles = []
    for name, skills in ROLES.items():
        d = details["roles"].get(name, {})
        roles.append({
            "name": name,
            "category": d.get("category", "Other"),
            "overview": d.get("overview", ""),
            "description": d.get("description", ""),
            "responsibilities": d.get("responsibilities", []),
            "tools": d.get("tools", []),
            "required_skills": skills,
            "salary_lpa": d.get("salary_lpa", [None, None, None, None]),
            "leads_to": [b for a, b in LEADS_TO if a == name],
            "led_from": [a for a, b in LEADS_TO if b == name],
            "trend": trends.get(name),
        })
    return {"meta": details["_meta"], "roles": roles}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def error_response(message: str, status_code: int):
    response = jsonify({"error": message})
    response.status_code = status_code
    return response


# ---------------------------------------------------------------- API

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/roles", methods=["GET"])
def roles():
    return jsonify(build_roles_payload())


@app.route("/trends", methods=["GET"])
def trends():
    return jsonify(load_json(TRENDS_PATH))


@app.route("/skills-guide", methods=["GET"])
def skills_guide():
    return jsonify(load_json(GUIDE_PATH))


@app.route("/roles/<path:role_name>", methods=["GET"])
def role_detail(role_name):
    for role in build_roles_payload()["roles"]:
        if role["name"].lower() == role_name.lower():
            return jsonify(role)
    return error_response(f"Role '{role_name}' not found.", 404)


@app.route("/upload-resume", methods=["POST"])
def upload_resume():
    if "file" not in request.files:
        return error_response("No file part in the request. Expected form field 'file'.", 400)

    file = request.files["file"]
    if file.filename == "":
        return error_response("No file selected.", 400)

    if not allowed_file(file.filename):
        return error_response("Only PDF files are supported.", 400)

    filename = secure_filename(file.filename)
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = os.path.join(tmp_dir, filename)
        file.save(tmp_path)

        try:
            candidate_dict = parse_resume(tmp_path)
        except Exception as exc:
            return error_response(f"Failed to parse resume: {exc}", 422)

    driver = get_driver()
    try:
        candidate_id = insert_candidate(driver, candidate_dict)
    except Exception as exc:
        return error_response(f"Failed to store candidate in graph database: {exc}", 502)

    return jsonify({"candidate_id": candidate_id, **candidate_dict}), 201


@app.route("/recommendations/<candidate_id>", methods=["GET"])
def recommendations(candidate_id):
    driver = get_driver()

    skills = get_candidate_skills(driver, candidate_id)
    if not skills:
        return error_response(f"Candidate '{candidate_id}' not found or has no skills on record.", 404)

    current_role = get_candidate_current_role(driver, candidate_id)
    next_roles = get_next_roles(driver, current_role) if current_role else []
    role_skills = get_all_roles_with_skills(driver)

    try:
        top = int(request.args.get("top", 5))
    except ValueError:
        top = 5
    top = max(1, min(top, len(role_skills)))

    candidate_dict = {"skills": skills}
    recs = recommend(candidate_dict, role_skills, next_roles=next_roles, top_k=top)

    return jsonify({"candidate_id": candidate_id, "recommendations": recs})


@app.route("/skill-gap/<candidate_id>/<role_name>", methods=["GET"])
def skill_gap(candidate_id, role_name):
    driver = get_driver()

    skills = get_candidate_skills(driver, candidate_id)
    if not skills:
        return error_response(f"Candidate '{candidate_id}' not found.", 404)

    role_skills = get_all_roles_with_skills(driver)
    if role_name not in role_skills:
        return error_response(f"Role '{role_name}' not found.", 404)

    missing = get_skill_gap(driver, candidate_id, role_name)
    return jsonify({"candidate_id": candidate_id, "role": role_name, "missing_skills": missing})


# ----------------------------------------------------------- Frontend

@app.route("/")
def home():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def frontend_files(filename):
    if not filename.endswith(FRONTEND_EXTENSIONS):
        abort(404)
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    # use_reloader=False avoids the Windows auto-reloader restarting mid-request
    app.run(host="0.0.0.0", port=port, debug=(os.getenv("FLASK_ENV") == "development"), use_reloader=False)
