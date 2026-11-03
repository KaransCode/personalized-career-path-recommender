# Personalized Career Path Recommender

An academic project that turns a resume (PDF) into personalized career-path
recommendations using NLP extraction, a Neo4j knowledge graph of
roles/skills, and a hybrid content + graph-based recommender.

## Pipeline

```
Resume PDF -> NLP extraction (spaCy) -> Neo4j knowledge graph
           -> Recommender (TF-IDF + graph signal) -> Flask API -> Frontend
```

## Project structure

```
/ingestion     resume parsing & entity extraction
/graph         Neo4j schema, seed data, queries
/recommender   TF-IDF content matching + graph-based scoring
/api           Flask app exposing the pipeline
/data          sample resumes & skill taxonomy
/tests         pytest suite
/frontend      minimal demo UI (plain HTML/CSS/JS)
```

## Running locally (without Docker)

```bash
python3.11 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
cp .env.example .env            # edit if your local Neo4j creds differ

# start a local Neo4j instance yourself, or use docker-compose for just neo4j:
docker-compose up -d neo4j

python graph/run_seed.py        # populate the graph with roles/skills
python api/app.py               # starts Flask on :5000
```

Visit `http://localhost:5000/health` — should return `{"status": "ok"}`.

## Running everything with Docker

```bash
docker-compose up --build
```

Then open the frontend at `http://localhost:8080` and upload a resume.

## Status

See `EVALUATION.md` for known limitations and `ARCHITECTURE.md` for design
rationale.
