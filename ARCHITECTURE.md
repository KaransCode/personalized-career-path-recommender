# Architecture

## Pipeline overview

```
 PDF Resume
     │
     ▼
[1] Ingestion (/ingestion)
   parser.py    -> raw text (PyPDF2)
   extractor.py -> name, skills, roles, years_experience (spaCy + regex)
   normalizer.py -> lowercased, synonym-mapped, de-duplicated fields
     │
     ▼
[2] Knowledge Graph (/graph, Neo4j)
   (:Candidate)-[:HAS_SKILL]->(:Skill)
   (:Role)-[:REQUIRES_SKILL]->(:Skill)
   (:Candidate)-[:HELD_ROLE]->(:Role)
   (:Role)-[:LEADS_TO]->(:Role)
     │
     ▼
[3] Recommender (/recommender)
   vectorizer.py      -> TF-IDF vectors over skill lists
   content_matcher.py -> cosine similarity: candidate vs. every role
   graph_signal.py     -> boost for roles reachable via LEADS_TO
   ranker.py           -> final_score = 0.6*content + 0.4*graph, top 5
     │
     ▼
[4] API (/api, Flask)
   POST /upload-resume            -> parse + store candidate, return candidate_id
   GET  /recommendations/<id>     -> ranked role recommendations
   GET  /skill-gap/<id>/<role>    -> missing skills for a target role
     │
     ▼
[5] Frontend (/frontend, plain HTML/CSS/JS)
   Upload form -> skill tags -> recommendation cards
```

## Why Neo4j over a relational database

The core relationships this project needs to reason about — "which roles
share overlapping required skills," "what roles typically follow this one
(LEADS_TO)," and "what's the shortest skill-gap path to a target role" —
are naturally graph traversals, not table joins.

- **Career adjacency is a graph problem.** `LEADS_TO` chains
  (Data Analyst → Data Scientist → ML Engineer → Deep Learning Engineer)
  are the kind of variable-depth traversal that Cypher expresses in one
  line, but which requires recursive CTEs or repeated self-joins in SQL
  and gets slower as the chain grows.
- **Skill overlap is a shared-neighbor query.** "Roles that share the most
  `REQUIRES_SKILL` neighbors with a candidate's `HAS_SKILL` set" is a
  natural `MATCH` pattern in Neo4j (see `get_matching_roles` in
  `graph/queries.py`); in a relational schema it becomes a multi-table
  join with `GROUP BY`/`HAVING` that's harder to read and reason about as
  the schema grows (e.g. adding certifications or education nodes later).
- **The schema is expected to grow organically.** Adding new node types
  (e.g. `:Certification`, `:Company`, `:Industry`) and relationships is a
  matter of adding new `MERGE` patterns, without the schema migrations a
  relational model would need for new join tables.

The trade-off: for pure aggregate reporting (e.g. "average years of
experience across all candidates"), a relational store or even pandas
would be simpler than Cypher. This project doesn't need that, so the
graph model's traversal strengths outweigh that cost here.
