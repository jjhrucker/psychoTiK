"""
reddit_ingestion.py
===================
PsychoTIX Reddit Data Ingestion Pipeline

Normalises raw Reddit data (JSON dump, CSV, or JSONL) into a standardised
record format ready for receptor→experience analysis.

Usage
-----
    python reddit_ingestion.py --input data.json --output records.jsonl
    python reddit_ingestion.py --input dump.csv --output records.jsonl --format csv
    python reddit_ingestion.py --input comments/ --output records.jsonl --format dir

Output format (one JSON object per line in records.jsonl)
---------
    {
        "id":           "t1_abc123",          # original Reddit ID
        "subreddit":    "antidepressants",
        "text":         "...",                 # post title + body or comment body
        "drugs_found":  ["fluoxetine", ...],   # canonical drug IDs
        "effects_raw":  ["felt tired", ...],   # raw effect phrases (future NLP)
        "timestamp":    1700000000,
        "source":       "post" | "comment"
    }
"""

import json
import re
import csv
import sys
import os
import argparse
from pathlib import Path

# ─── Load synonym dictionary ───────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent
_SYN_PATH = _SCRIPT_DIR / "drug_synonyms.json"

with open(_SYN_PATH) as f:
    _SYN_DATA = json.load(f)

SYNONYM_DICT = _SYN_DATA["synonyms"]   # lowercase synonym → drug_id
DRUG_INFO    = _SYN_DATA["drug_info"]  # drug_id → {canonical_name, drug_class, synonyms}

# Pre-compile a regex for fast drug detection
# Sort by length descending so longer phrases match first (e.g. "adderall xr" before "adderall")
_sorted_syns = sorted(SYNONYM_DICT.keys(), key=len, reverse=True)
_escaped = [re.escape(s) for s in _sorted_syns]
_DRUG_RE = re.compile(r'\b(' + '|'.join(_escaped) + r')\b', re.IGNORECASE)


def find_drugs(text: str) -> list[str]:
    """Return list of unique canonical drug IDs mentioned in text."""
    matches = _DRUG_RE.findall(text)
    drug_ids = set()
    for m in matches:
        did = SYNONYM_DICT.get(m.lower())
        if did:
            drug_ids.add(did)
    return sorted(drug_ids)


# ─── Effect phrase extraction ──────────────────────────────────────────────────
# Simple heuristic: look for phrases around known effect keywords.
# This is a seed approach; swap in an NLP model when available.

_EFFECT_KEYWORDS = [
    r'feel\w*\s+\w+', r'felt\s+\w+', r'made me\s+[\w\s]+', r'makes me\s+[\w\s]+',
    r'(sleep|slept|sleeping)\s+[\w\s]*', r'(tired|exhausted|wired|alert)\w*',
    r'(anxious|anxiet\w+|panic\w*|calm\w*|relax\w*)',
    r'(depress\w+|mood\w*|happy|sad|low\b)',
    r'(nausea|nauseous|sick|vomit\w*)',
    r'(weight\s+\w+|gain\w*\s+weight|lost\s+weight)',
    r'(brain\s+fog|foggy|concentrat\w+|focus\w*)',
    r'(sex\w*|libido\w*|orgasm\w*)',
    r'(energy\w*|motivat\w+|fatigue\w*|lethar\w+)',
]
_EFFECT_RE = re.compile('|'.join(_EFFECT_KEYWORDS), re.IGNORECASE)


def extract_effect_phrases(text: str) -> list[str]:
    """Extract candidate effect phrases from text."""
    phrases = []
    for m in _EFFECT_RE.finditer(text):
        phrase = m.group(0).strip().lower()
        # Clean up — cap at 6 words
        words = phrase.split()[:6]
        phrases.append(' '.join(words))
    return list(set(phrases))


# ─── Subreddits of interest ────────────────────────────────────────────────────
RELEVANT_SUBREDDITS = {
    # Substances / psychedelics
    "Drugs", "DrugNerds", "PsychedelicStudies", "RationalPsychonaut",
    "Psychonaut", "Psychedelics", "LSD", "psilocybin", "DMT", "MDMA",
    "ketamine", "DXM", "researchchemicals",
    # Prescription / psychiatric
    "antidepressants", "benzodiazepines", "quittingklonopin", "ssris",
    "PsychiatricMedication", "Antipsychotics", "bipolar", "BipolarReddit",
    "depression", "Anxiety", "OCD", "ADHD", "mentalhealth",
    "buprenorphine", "suboxone", "methadone", "opiates", "opioids",
    "Nootropics", "zolpidem", "sleepingpills",
    # Clinical
    "AskPsychiatry", "psychiatry",
}


# ─── Record builders ───────────────────────────────────────────────────────────

def _make_record(post_id, subreddit, text, timestamp, source):
    drugs = find_drugs(text)
    effects = extract_effect_phrases(text) if drugs else []
    return {
        "id":          post_id,
        "subreddit":   subreddit,
        "text":        text[:2000],   # cap at 2000 chars to keep file size manageable
        "drugs_found": drugs,
        "effects_raw": effects,
        "timestamp":   timestamp,
        "source":      source,
    }


def _text_from_post(post: dict) -> str:
    title = post.get("title", "") or ""
    body  = post.get("selftext", "") or post.get("body", "") or ""
    return (title + " " + body).strip()


def _filter_record(rec: dict, min_drugs: int = 1) -> bool:
    """Return True if record should be kept."""
    if len(rec["drugs_found"]) < min_drugs:
        return False
    text = rec["text"]
    # Skip very short posts
    if len(text.split()) < 10:
        return False
    # Skip deleted/removed posts
    if text.strip() in ("[deleted]", "[removed]", ""):
        return False
    return True


# ─── Format-specific loaders ──────────────────────────────────────────────────

def load_json(path: str):
    """Load a JSON array of post/comment objects, or newline-delimited JSON."""
    with open(path) as f:
        first_char = f.read(1)
        f.seek(0)
        if first_char == '[':
            data = json.load(f)
        else:
            # JSONL
            data = [json.loads(line) for line in f if line.strip()]
    return data


def process_json(path: str, output_file, subreddit_filter=None):
    data = load_json(path)
    count = 0
    for item in data:
        sub = item.get("subreddit", "")
        if subreddit_filter and sub not in subreddit_filter:
            continue
        text = _text_from_post(item)
        if not text:
            continue
        post_id  = item.get("id", item.get("name", ""))
        ts       = item.get("created_utc", item.get("timestamp", 0))
        source   = "comment" if "link_id" in item else "post"
        rec = _make_record(post_id, sub, text, ts, source)
        if _filter_record(rec):
            output_file.write(json.dumps(rec) + "\n")
            count += 1
    return count


def process_csv(path: str, output_file, subreddit_filter=None):
    """Process a CSV with columns: id, subreddit, title, body/selftext, created_utc."""
    count = 0
    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            sub = row.get("subreddit", "")
            if subreddit_filter and sub not in subreddit_filter:
                continue
            title = row.get("title", "") or ""
            body  = row.get("selftext", row.get("body", "")) or ""
            text  = (title + " " + body).strip()
            if not text:
                continue
            post_id = row.get("id", "")
            ts = float(row.get("created_utc", row.get("timestamp", 0)) or 0)
            source = "comment" if row.get("link_id") else "post"
            rec = _make_record(post_id, sub, text, ts, source)
            if _filter_record(rec):
                output_file.write(json.dumps(rec) + "\n")
                count += 1
    return count


def process_directory(path: str, output_file, subreddit_filter=None):
    """Process all .json / .jsonl / .csv files in a directory."""
    total = 0
    for fname in sorted(os.listdir(path)):
        fpath = os.path.join(path, fname)
        if fname.endswith(('.json', '.jsonl')):
            n = process_json(fpath, output_file, subreddit_filter)
        elif fname.endswith('.csv'):
            n = process_csv(fpath, output_file, subreddit_filter)
        else:
            continue
        print(f"  {fname}: {n} records kept")
        total += n
    return total


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PsychoTIX Reddit ingestion pipeline")
    parser.add_argument("--input",  required=True,  help="Input file or directory")
    parser.add_argument("--output", required=True,  help="Output JSONL file")
    parser.add_argument("--format", default="auto",
                        choices=["auto", "json", "jsonl", "csv", "dir"],
                        help="Input format (default: auto-detect)")
    parser.add_argument("--filter-subreddits", action="store_true",
                        help="Only keep posts from RELEVANT_SUBREDDITS list")
    args = parser.parse_args()

    subreddit_filter = RELEVANT_SUBREDDITS if args.filter_subreddits else None
    fmt = args.format

    if fmt == "auto":
        if os.path.isdir(args.input):
            fmt = "dir"
        elif args.input.endswith(".csv"):
            fmt = "csv"
        else:
            fmt = "json"

    print(f"Processing {args.input} → {args.output} (format={fmt})")

    with open(args.output, "w") as out_f:
        if fmt == "dir":
            total = process_directory(args.input, out_f, subreddit_filter)
        elif fmt == "csv":
            total = process_csv(args.input, out_f, subreddit_filter)
        else:
            total = process_json(args.input, out_f, subreddit_filter)

    print(f"Done. {total} records written to {args.output}")


if __name__ == "__main__":
    main()
