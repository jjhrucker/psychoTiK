"""
receptor_experience_inference.py
=================================
Empirical receptor → experience inference from Reddit data.

Takes the JSONL output of reddit_ingestion.py and the receptor profiles
embedded in psychopharmacology_tool.html, then computes lift statistics
linking receptor activity to reported effects.

Method
------
For each (receptor, mechanism, effect_category) triple:

    P(effect | receptor active)   = fraction of drug-dose records where
                                    receptor score >= threshold AND effect reported

    P(effect | receptor inactive) = fraction where receptor score < threshold
                                    AND effect reported

    lift = P(effect | active) / P(effect | inactive + smoothing)

A lift > 1 indicates the receptor's activity predicts the effect above base rate.

Output
------
    receptor_experience_results.json  — full lift table
    receptor_experience_report.html   — visual report (extends the existing
                                        receptor_experience_analysis.html style)

Usage
-----
    python receptor_experience_inference.py \\
        --records records.jsonl \\
        --tool    psychopharmacology_tool.html \\
        --output  receptor_experience_results.json
"""

import json
import re
import sys
import argparse
import math
import collections
from pathlib import Path

# ─── Load helper data ─────────────────────────────────────────────────────────
_SCRIPT_DIR = Path(__file__).parent
_SYN_PATH   = _SCRIPT_DIR / "drug_synonyms.json"
_TAX_PATH   = _SCRIPT_DIR / "effect_taxonomy.json"

with open(_SYN_PATH) as f:
    _SYN_DATA = json.load(f)
SYNONYM_DICT = _SYN_DATA["synonyms"]
DRUG_INFO    = _SYN_DATA["drug_info"]

with open(_TAX_PATH) as f:
    TAXONOMY = json.load(f)


# ─── Extract receptor profiles from HTML tool ─────────────────────────────────

def extract_receptor_profiles(html_path: str) -> dict:
    """
    Returns:
        {drug_id: {receptor_id: [score_low, score_med, score_high]}}
    """
    with open(html_path) as f:
        content = f.read()

    def extract_js_block(text, start_marker, open_char='{'):
        idx = text.find(start_marker)
        if idx == -1:
            return None
        open_idx = text.find(open_char, idx)
        close_char = '}' if open_char == '{' else ']'
        depth = 0
        for i in range(open_idx, len(text)):
            if text[i] == open_char:
                depth += 1
            elif text[i] == close_char:
                depth -= 1
                if depth == 0:
                    return text[open_idx:i+1]
        return None

    # Extract DRUGS array
    drugs_raw = extract_js_block(content, 'const DRUGS = [', '[')
    if not drugs_raw:
        raise ValueError("Could not find DRUGS array in HTML")

    # Parse drug IDs and their receptor entries
    # Each drug has: receptors: { receptor_id: [lo, med, hi], ... }
    profiles = {}

    # Split by drug entry
    blocks = re.split(r'\{\s*id:', drugs_raw[1:])
    for block in blocks:
        m_id = re.match(r"\s*'([^']+)'", block)
        if not m_id:
            continue
        drug_id = m_id.group(1)

        # Find receptors block
        rec_idx = block.find('receptors:')
        if rec_idx == -1:
            continue
        rec_start = block.find('{', rec_idx)
        depth = 0
        rec_end = rec_start
        for i in range(rec_start, len(block)):
            if block[i] == '{':
                depth += 1
            elif block[i] == '}':
                depth -= 1
                if depth == 0:
                    rec_end = i + 1
                    break
        rec_str = block[rec_start:rec_end]

        # Parse receptor entries: key: [n, n, n]
        receptor_entries = re.findall(r"'?([a-zA-Z0-9_]+)'?\s*:\s*\[([^\]]+)\]", rec_str)
        drug_receptors = {}
        for rid, vals_str in receptor_entries:
            vals = [float(v.strip()) for v in vals_str.split(',') if v.strip()]
            if len(vals) == 3:
                drug_receptors[rid] = vals
        profiles[drug_id] = drug_receptors

    print(f"Extracted receptor profiles for {len(profiles)} drugs")
    return profiles


# ─── Effect categorisation ────────────────────────────────────────────────────

# Build keyword → category lookup from taxonomy
_KW_MAP = {}
for cat_id, cat in TAXONOMY.items():
    if cat_id.startswith('_'):
        continue
    for kw in cat.get('domains', []):
        _KW_MAP[kw.lower()] = cat_id
    for kw in cat.get('reddit_indicators', []):
        _KW_MAP[kw.lower()] = cat_id

def categorise_text(text: str) -> set[str]:
    """Return set of effect category IDs found in text."""
    tl = text.lower()
    found = set()
    for kw, cat in _KW_MAP.items():
        if kw in tl:
            found.add(cat)
    return found


# ─── Core lift analysis ───────────────────────────────────────────────────────

DOSE_LEVELS = ['low', 'medium', 'high']   # indices 0, 1, 2

def run_analysis(records_path: str,
                 profiles: dict,
                 threshold: float = 5.0,
                 smoothing: float = 0.5) -> dict:
    """
    For each record that mentions a drug, look up that drug's receptor scores
    and build co-occurrence counts: receptor active/inactive × effect present/absent.

    Args:
        records_path:  JSONL file from reddit_ingestion.py
        profiles:      {drug_id: {receptor_id: [lo, med, hi]}}
        threshold:     receptor score >= threshold = 'active' (default 5/10)
        smoothing:     Laplace smoothing for lift denominator

    Returns:
        {receptor_id: {effect_cat: {lift, p_active, p_inactive, n_active, n_inactive}}}
    """
    # Accumulators: receptor × active/inactive × effect present/absent
    # counts[receptor_id][active_bool][cat_id] = count
    counts = collections.defaultdict(lambda: {
        True:  collections.Counter(),   # receptor active, effect present
        False: collections.Counter(),   # receptor inactive, effect present
    })
    total_active   = collections.Counter()  # receptor_id → n records where active
    total_inactive = collections.Counter()  # receptor_id → n records where inactive

    n_records = 0
    n_skipped  = 0

    with open(records_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue

            drugs = rec.get("drugs_found", [])
            if not drugs:
                n_skipped += 1
                continue

            text = rec.get("text", "")
            effect_cats = categorise_text(text)

            # Use medium dose (index 1) as default proxy
            for drug_id in drugs:
                if drug_id not in profiles:
                    continue
                drug_receptors = profiles[drug_id]

                for receptor_id, scores in drug_receptors.items():
                    score = scores[1]  # medium dose
                    active = score >= threshold

                    if active:
                        total_active[receptor_id] += 1
                    else:
                        total_inactive[receptor_id] += 1

                    for cat in effect_cats:
                        counts[receptor_id][active][cat] += 1

            n_records += 1

    print(f"Processed {n_records} records ({n_skipped} skipped — no drugs found)")

    # Compute lift for each receptor × effect pair
    results = {}

    for receptor_id in counts:
        n_act  = total_active[receptor_id]
        n_inact = total_inactive[receptor_id]
        if n_act == 0:
            continue

        receptor_results = {}
        all_cats = set(counts[receptor_id][True].keys()) | set(counts[receptor_id][False].keys())

        for cat in all_cats:
            k_act   = counts[receptor_id][True][cat]
            k_inact = counts[receptor_id][False][cat]

            p_act   = (k_act + smoothing) / (n_act + smoothing)
            p_inact = (k_inact + smoothing) / (n_inact + smoothing)
            lift    = p_act / p_inact if p_inact > 0 else float('inf')

            # Only keep results with at least 5 co-occurrences
            if k_act < 5:
                continue

            receptor_results[cat] = {
                "lift":       round(lift, 3),
                "p_active":   round(p_act, 4),
                "p_inactive": round(p_inact, 4),
                "n_active_with_effect":  k_act,
                "n_inactive_with_effect": k_inact,
                "n_records_active":   n_act,
                "n_records_inactive": n_inact,
            }

        if receptor_results:
            results[receptor_id] = receptor_results

    return results


# ─── Report generator ─────────────────────────────────────────────────────────

def generate_html_report(results: dict, output_path: str):
    """Generate an HTML report in the style of receptor_experience_analysis.html."""

    cat_labels = {k: v.get('label', k) for k, v in TAXONOMY.items() if not k.startswith('_')}

    rows = []
    for receptor_id, cats in sorted(results.items()):
        for cat_id, stats in sorted(cats.items(), key=lambda x: -x[1]['lift']):
            rows.append({
                'receptor': receptor_id,
                'category': cat_id,
                'cat_label': cat_labels.get(cat_id, cat_id),
                **stats
            })

    rows_json = json.dumps(rows)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Receptor → Experience: Empirical Analysis (Reddit)</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #0e1117; color: #c9d1d9; margin: 0; padding: 20px; }}
  h1 {{ font-size: 18px; margin-bottom: 4px; }}
  h2 {{ font-size: 14px; color: #8b949e; font-weight: 400; margin-top: 0; }}
  .controls {{ display: flex; gap: 12px; margin: 16px 0; flex-wrap: wrap; }}
  .controls input, .controls select {{ background: #161b22; border: 1px solid #30363d; color: #c9d1d9;
    padding: 6px 10px; border-radius: 6px; font-size: 13px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 12px; }}
  th {{ background: #161b22; padding: 8px 12px; text-align: left; color: #8b949e;
        border-bottom: 2px solid #30363d; cursor: pointer; }}
  td {{ padding: 7px 12px; border-bottom: 1px solid #21262d; }}
  tr:hover td {{ background: #1c2128; }}
  .lift-high {{ color: #3ecf8e; font-weight: 700; }}
  .lift-mid  {{ color: #f5c542; }}
  .lift-low  {{ color: #8b949e; }}
  .bar {{ display: inline-block; height: 8px; border-radius: 4px; background: #3ecf8e; vertical-align: middle; }}
  .note {{ font-size: 11px; color: #6e7681; margin-top: 20px; }}
</style>
</head>
<body>
<h1>Receptor → Experience: Empirical Analysis (Reddit data)</h1>
<h2>Lift statistic: how much more likely is an effect category in posts mentioning drugs with active receptor, vs inactive?</h2>

<div class="controls">
  <input id="searchInput" placeholder="Filter receptor..." oninput="filterTable()">
  <select id="catFilter" onchange="filterTable()">
    <option value="">All categories</option>
    {''.join(f'<option value="{k}">{v}</option>' for k, v in sorted(cat_labels.items()))}
  </select>
  <select id="sortCol" onchange="sortTable()">
    <option value="lift">Sort by lift</option>
    <option value="receptor">Sort by receptor</option>
    <option value="n_active_with_effect">Sort by n (co-occurrences)</option>
  </select>
</div>

<table id="mainTable">
  <thead>
    <tr>
      <th>Receptor</th>
      <th>Effect Category</th>
      <th>Lift</th>
      <th>P(effect|active)</th>
      <th>P(effect|inactive)</th>
      <th>N (active+effect)</th>
      <th>N (active records)</th>
    </tr>
  </thead>
  <tbody id="tableBody"></tbody>
</table>

<div class="note">
  Lift &gt; 1 = effect over-represented when receptor is active (score ≥ 5/10 at medium dose).
  Minimum 5 co-occurrences required. Smoothing = 0.5. Source: Reddit posts/comments.
</div>

<script>
const DATA = {rows_json};
let filtered = [...DATA];

function liftClass(l) {{
  if (l >= 2) return 'lift-high';
  if (l >= 1.3) return 'lift-mid';
  return 'lift-low';
}}

function render(rows) {{
  const tbody = document.getElementById('tableBody');
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><code>${{r.receptor}}</code></td>
      <td>${{r.cat_label}}</td>
      <td class="${{liftClass(r.lift)}}">${{r.lift.toFixed(2)}}
        <span class="bar" style="width:${{Math.min(60, (r.lift-1)*30)}}px;margin-left:6px"></span>
      </td>
      <td>${{(r.p_active*100).toFixed(1)}}%</td>
      <td>${{(r.p_inactive*100).toFixed(1)}}%</td>
      <td>${{r.n_active_with_effect}}</td>
      <td>${{r.n_records_active}}</td>
    </tr>
  `).join('');
}}

function filterTable() {{
  const q = document.getElementById('searchInput').value.toLowerCase();
  const cat = document.getElementById('catFilter').value;
  filtered = DATA.filter(r =>
    (!q || r.receptor.toLowerCase().includes(q)) &&
    (!cat || r.category === cat)
  );
  sortTable();
}}

function sortTable() {{
  const col = document.getElementById('sortCol').value;
  filtered.sort((a, b) => col === 'receptor' ? a.receptor.localeCompare(b.receptor) : b[col] - a[col]);
  render(filtered);
}}

sortTable();
</script>
</body>
</html>
"""
    with open(output_path, 'w') as f:
        f.write(html)
    print(f"HTML report written to {output_path}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PsychoTIX receptor→experience inference")
    parser.add_argument("--records",   required=True, help="JSONL records from reddit_ingestion.py")
    parser.add_argument("--tool",      required=True, help="psychopharmacology_tool.html path")
    parser.add_argument("--output",    default="receptor_experience_results.json")
    parser.add_argument("--report",    default="receptor_experience_reddit_report.html")
    parser.add_argument("--threshold", type=float, default=5.0,
                        help="Receptor score threshold for 'active' (0–10, default 5)")
    parser.add_argument("--smoothing", type=float, default=0.5)
    args = parser.parse_args()

    profiles = extract_receptor_profiles(args.tool)
    results  = run_analysis(args.records, profiles, args.threshold, args.smoothing)

    with open(args.output, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"Results written to {args.output}")

    generate_html_report(results, args.report)


if __name__ == "__main__":
    main()
