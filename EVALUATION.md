# Evaluation & Known Limitations

## Informal precision@3 check

Five candidate profiles (three parsed from the sample resumes, two
synthetic skill-only profiles) were each manually labeled with a
"reasonable" target role, then run through `recommend()`. The target role
appeared in the top 3 recommendations in **4 out of 5 cases (80%)**.

| Candidate | Labeled target role | Top 3 returned | Hit? |
|---|---|---|---|
| resume_1.pdf | Data Scientist | Data Scientist, Business Intelligence Analyst, Product Analyst | ✅ |
| resume_2.pdf | Machine Learning Engineer | DevOps Engineer, Engineering Manager, Computer Vision Engineer | ❌ |
| resume_3.pdf | Android Developer | Software Engineer, Android Developer, Backend Developer | ✅ |
| synthetic (DBA skills) | Database Administrator | Database Administrator, Data Engineer, Software Engineer | ✅ |
| synthetic (DevOps skills) | DevOps Engineer | Cloud Engineer, DevOps Engineer, MLOps Engineer | ✅ |

Full machine-readable results: `data/eval_results.json`.

The one miss (resume_2.pdf) is informative: the resume's extracted role
history includes "Software Engineer Intern", which pulled `Engineering
Manager`/`DevOps Engineer` career-progression boosts into the mix and
diluted the pure skill-content signal toward Machine Learning Engineer.
This is a real limitation of the fixed 0.6/0.4 content/graph weighting,
not a bug — see below.

**This is an informal sanity check on 5 hand-labeled examples, not a
rigorous benchmark.** A production evaluation would need a much larger
labeled dataset and standard IR metrics (precision@k, recall@k, NDCG)
computed with cross-validation.

## Known limitations

- **Cold-start for new roles.** A role with no seeded `REQUIRES_SKILL`
  edges gets a zero vector and can never be recommended, regardless of
  candidate fit.
- **No real labeled dataset.** The recommender is tuned against a small,
  manually seeded taxonomy of ~20 roles and ~60 skills; it has not been
  validated against real hiring outcomes or a large resume corpus.
- **Limited synonym coverage.** `normalizer.py` only maps a handful of
  common synonyms (ML → machine learning, JS → JavaScript, etc.). Skills
  phrased unusually in a resume may simply not match the taxonomy.
- **Resume parsing accuracy depends on format.** `extractor.py` uses
  keyword/regex heuristics for role and date extraction rather than a
  trained NER model, so heavily designed resumes (multi-column layouts,
  graphics-heavy templates, scanned images) will parse worse than plain
  text-based PDFs like the samples used here.
- **Fixed content/graph weighting.** The 0.6/0.4 blend in `ranker.py` is a
  reasonable default, not a learned or validated weighting — as seen in
  the resume_2.pdf miss above, it can occasionally let graph-adjacency
  scores outweigh a strong content match.

## What a production version would add

- OCR fallback (e.g. Tesseract) for scanned/image-based resumes.
- A much larger, ideally auto-updated skill taxonomy (e.g. sourced from a
  labor-market skills ontology such as ESCO or O*NET) instead of the
  ~60-skill seed list.
- A user feedback loop (e.g. "was this recommendation useful?") to learn
  and adjust the content/graph weighting over time instead of a fixed
  0.6/0.4 split.
- Bias auditing — checking whether the recommender systematically
  under/over-recommends certain roles for candidates with particular
  educational or regional backgrounds, given that role-adjacency data was
  manually seeded and could encode the seed author's assumptions.
