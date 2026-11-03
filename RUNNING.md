# Running the Career Path Recommender (v3)

Flask serves the website itself, so you only run one server.

## First time after this update

The update adds 10 new roles and new skills, so **re-run the seed script once**
(it is safe to re-run; every write is a MERGE):

```bash
conda activate career-reco
docker-compose up -d neo4j        # Docker Desktop must be running
python graph/run_seed.py          # adds the new roles, skills and career links
python api/app.py
```

Open **http://localhost:5000/** in your browser.

Then **upload your resume again**. The expanded skill list (`data/skills.json`)
only applies to resumes parsed after the update.

## Pages

| Page | Address | What it does |
|---|---|---|
| Home | `/` | Upload a resume, see trending roles |
| Results | `/results.html` | Ranked roles, radar and "learn these first" charts, target role, skill adder, learning plan, Save as PDF |
| Explore | `/explore.html` | Search, filter, sort, compare 3 roles, Cards or Map view |
| Role | `/role.html?name=Data Scientist` | Overview, market outlook, skills, roadmap, pay by experience, career path |
| Trends | `/trends.html` | What is in demand now, rising skills, pay vs demand chart, sources |

Shortcuts: **Ctrl+K** (or `/`) opens search. **Theme** in the top bar switches between
Auto, Light, Dark, Midnight, Forest and Sunset.

## API endpoints

- `GET /roles`, `GET /roles/<name>`: roles with overview, skills, pay bands, career links, trend
- `GET /trends`: market trend data with sources
- `GET /skills-guide`: learning weeks and prerequisites per skill
- `POST /upload-resume`, `GET /recommendations/<id>?top=30`, `GET /skill-gap/<id>/<role>`, `GET /health`

## Editing content (no restart needed, just refresh)

| File | What it holds |
|---|---|
| `data/role_details.json` | Descriptions, tools, pay bands (INR LPA for 0-2, 2-5, 5-8, 8+ years) |
| `data/trends.json` | Momentum, outlook score, notes, themes, sources. Update `as_of` when you edit |
| `data/skills_guide.json` | Weeks and prerequisites used by the roadmap |
| `data/skills.json` | Skills the resume parser can recognise |
| `graph/seed_data.py` | Roles, required skills, career ladders (re-run `run_seed.py` after editing) |

Role names must match between `role_details.json`, `trends.json` and `seed_data.py`.

## Troubleshooting

| Symptom | Fix |
|---|---|
| "Can't reach the API" | `python api/app.py` is not running |
| New roles missing from your results | You haven't re-run `python graph/run_seed.py` |
| Upload fails with a graph database error | Neo4j is not running |
| Old design still shows | Hard refresh with Ctrl+F5 |
| Results says the resume is no longer in the database | Upload it again |
