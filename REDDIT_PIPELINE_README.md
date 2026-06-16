# Reddit Data Pipeline — PsychoTIX

## What's here

| File | Purpose |
|------|---------|
| `drug_synonyms.json` | 751 synonyms → 222 canonical drug IDs (brand names, slang, abbreviations) |
| `effect_taxonomy.json` | 13 effect categories with keyword lists and Reddit-specific indicators |
| `reddit_ingestion.py` | Normalises raw Reddit data → standard JSONL records |
| `receptor_experience_inference.py` | Computes receptor→experience lift from JSONL records |

---

## Step 1 — Ingest Reddit data

```bash
python reddit_ingestion.py \
  --input   /path/to/reddit_dump.json \
  --output  records.jsonl

# Or a directory of files:
python reddit_ingestion.py \
  --input   /path/to/dump_dir/ \
  --output  records.jsonl

# Filter to psychiatry/drug subreddits only:
python reddit_ingestion.py \
  --input   dump.json \
  --output  records.jsonl \
  --filter-subreddits
```

Expected Reddit formats: JSON array, JSONL (one object per line), CSV.
Each record needs at minimum: `id`, `subreddit`, `title`/`selftext`/`body`, `created_utc`.

Output (`records.jsonl`) is one JSON object per line:
```json
{"id": "t1_abc123", "subreddit": "antidepressants", "text": "...",
 "drugs_found": ["fluoxetine"], "effects_raw": ["felt tired"], "timestamp": 1700000000, "source": "post"}
```

---

## Step 2 — Run receptor→experience inference

```bash
python receptor_experience_inference.py \
  --records records.jsonl \
  --tool    psychopharmacology_tool.html \
  --output  receptor_experience_results.json \
  --report  receptor_experience_reddit_report.html
```

Opens `receptor_experience_reddit_report.html` in a browser to explore results.

### How lift works

For each `(receptor, effect_category)` pair:

```
lift = P(effect | receptor score ≥ 5) / P(effect | receptor score < 5)
```

- **lift > 2** — strong association (receptor reliably predicts the experience)
- **lift 1.3–2** — moderate association
- **lift ~1** — no relationship
- **lift < 1** — effect avoided when receptor active

Minimum 5 co-occurrences required; Laplace smoothing = 0.5 to avoid division by zero.

---

## Adding synonyms

Edit the `MANUAL_SYNONYMS` dict in `reddit_ingestion.py` (around line 60) or directly
add entries to `drug_synonyms.json` under `synonyms` (lowercase only):

```json
"seroquel": "quetiapine",
"kwetiapine": "quetiapine"
```

---

## Expected Reddit data format

If data arrives as Pushshift-style dumps, each object looks like:

```json
{
  "id": "abc123",
  "subreddit": "antidepressants",
  "title": "Sertraline week 4 update",
  "selftext": "Feeling much better, still some nausea...",
  "created_utc": 1700000000,
  "score": 42,
  "author": "throwaway..."
}
```

Comments are similar but have `body` instead of `selftext`/`title`, and have `link_id`.

---

## Next steps (once data arrives)

1. Run ingestion → check `records.jsonl` record count and drug hit rate
2. Run inference → look at lift table for receptors with well-characterised drugs
3. Validate against `receptor_experience_analysis.html` (our existing knowledge-based analysis)
4. Add NLP-based effect phrase extraction (replace current keyword heuristics)
