#!/usr/bin/env python3
"""
PsychoRx Reddit Experience Pipeline
=====================================
Fetches Reddit posts about psychiatric drugs via the public JSON API,
extracts structured experience data using Claude, and outputs an HTML
review interface.

Usage:
    python3 reddit_experience_pipeline.py

Requirements:
    pip install anthropic requests
"""

import subprocess, sys
def ensure(pkg):
    try: __import__(pkg)
    except ImportError:
        print(f"Installing {pkg}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--break-system-packages", "-q"])

ensure("anthropic")
ensure("requests")

import json, time, re, os
import requests
import anthropic
from datetime import datetime

# ── CONFIGURATION ─────────────────────────────────────────────────────────────

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
if not ANTHROPIC_API_KEY:
    ANTHROPIC_API_KEY = input("Enter your Anthropic API key: ").strip()
# Strip accidental whitespace
ANTHROPIC_API_KEY = ANTHROPIC_API_KEY.strip()

DRUGS = [
    { "id": "sertraline",      "name": "Sertraline",      "brands": ["Zoloft","Lustral"],          "class": "SSRI",                    "subreddits": ["antidepressants","depression","mentalhealth"] },
    { "id": "venlafaxine",     "name": "Venlafaxine",     "brands": ["Effexor","Efexor"],          "class": "SNRI",                    "subreddits": ["antidepressants","depression"] },
    { "id": "amitriptyline",   "name": "Amitriptyline",   "brands": ["Elavil","Tryptizol"],        "class": "TCA",                     "subreddits": ["antidepressants","ChronicPain","migraine"] },
    { "id": "phenelzine",      "name": "Phenelzine",      "brands": ["Nardil"],                    "class": "MAOI",                    "subreddits": ["antidepressants","depression","MAOIs"] },
    { "id": "mirtazapine",     "name": "Mirtazapine",     "brands": ["Remeron","Zispin"],          "class": "NaSSA",                   "subreddits": ["antidepressants","depression","insomnia"] },
    { "id": "haloperidol",     "name": "Haloperidol",     "brands": ["Haldol","Serenace"],         "class": "Typical antipsychotic",   "subreddits": ["antipsychotics","schizophrenia","psychiatry"] },
    { "id": "quetiapine",      "name": "Quetiapine",      "brands": ["Seroquel"],                  "class": "Atypical antipsychotic",  "subreddits": ["antipsychotics","bipolar","schizophrenia","depression"] },
    { "id": "lithium",         "name": "Lithium",         "brands": ["Priadel","Eskalith"],        "class": "Mood stabiliser",         "subreddits": ["bipolar","lithium","depression"] },
    { "id": "methylphenidate", "name": "Methylphenidate", "brands": ["Ritalin","Concerta"],        "class": "Stimulant",               "subreddits": ["ADHD","adhdmeds"] },
    { "id": "diazepam",        "name": "Diazepam",        "brands": ["Valium"],                    "class": "Benzodiazepine",          "subreddits": ["benzodiazepines","anxiety","BenzoRecovery"] },
]

POSTS_PER_DRUG  = 80   # target posts per drug
MAX_POST_CHARS  = 1200  # truncate very long posts
DELAY_BETWEEN   = 2.0  # seconds between Reddit requests (be polite)
OUTPUT_FILE     = os.path.join(os.path.dirname(__file__), "reddit_experience_review.html")

DOMAINS = ["mood", "cognition", "perception", "sleep", "body", "motivation", "arousal", "autonomic"]

EXTRACTION_PROMPT = """You are a clinical pharmacologist extracting structured experience data from Reddit posts about psychiatric medications.

Drug: {drug_name} ({drug_class})
Brand names: {brands}

Below are {n_posts} Reddit posts from users discussing their personal experience with this drug.
Extract a structured list of reported effects. For each distinct effect:
- Assign it to one domain: mood | cognition | perception | sleep | body | motivation | arousal | autonomic
- Classify valence: benefit | side_effect | variable
- Classify onset: acute (hours-days) | subacute (days-weeks) | chronic (weeks-months)
- Write a concise effect description (max 8 words, clinical but readable)
- Note approximate dose tier if mentioned: low | medium | high | unknown
- Count how many posts mention this effect (source_count)
- Include one short direct quote (under 20 words) that best illustrates this effect

Important rules:
- Only include effects mentioned in at least 2 posts, OR particularly striking/specific ones from 1 post
- Ignore effects clearly due to the underlying illness rather than the drug
- Be conservative about causal attribution — note uncertainty where present
- Do NOT include effects about other drugs mentioned in passing
- Focus on first-person experiential language, not clinical trial language

Return ONLY valid JSON in this exact format:
{{
  "effects": [
    {{
      "domain": "mood",
      "effect_text": "Reduced anxiety within first week",
      "valence": "benefit",
      "onset": "subacute",
      "dose_tier": "medium",
      "source_count": 12,
      "example_quote": "felt calmer within about a week, like the edge was taken off"
    }}
  ]
}}

POSTS:
{posts_text}"""

# ── REDDIT FETCHER ─────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": "PsychoRx-Research/1.0 (academic pharmacology review; python/requests)"
}

# Arctic Shift API — Pushshift-compatible archive, no auth required
# Docs: https://arctic-shift.quanticdev.com
ARCTIC_BASE = "https://arctic-shift.quanticdev.com/api"

def fetch_posts_arctic(drug, target=80):
    """Fetch posts via Arctic Shift (Pushshift archive). No credentials needed."""
    all_posts = []
    search_terms = [drug["name"]] + drug["brands"]
    subreddits_str = ",".join(drug["subreddits"])

    for term in search_terms:
        if len(all_posts) >= target:
            break
        url = f"{ARCTIC_BASE}/posts/search"
        params = {
            "q": term,
            "subreddit": subreddits_str,
            "limit": min(50, target - len(all_posts)),
            "sort": "score",
            "sort_type": "desc",
        }
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=20)
            if r.status_code == 429:
                print(f"  Rate limited — waiting 15s...")
                time.sleep(15)
                r = requests.get(url, headers=HEADERS, params=params, timeout=20)
            if r.status_code != 200:
                print(f"  Arctic Shift HTTP {r.status_code} for '{term}' — trying fallback")
                continue
            data = r.json()
            posts = data.get("data", [])
            for p in posts:
                title    = p.get("title", "")
                body     = p.get("selftext", "") or ""
                subreddit = p.get("subreddit", "")
                full = (title + " " + body).lower()
                if len(body) < 50: continue
                if body in ("[deleted]", "[removed]"): continue
                if not any(t.lower() in full for t in [drug["name"]] + drug["brands"]): continue
                fp_words = ["i ", "i've", "i'm", "my ", "me ", "myself", "i feel", "i felt", "i took", "i started", "i stopped"]
                if not any(w in full for w in fp_words): continue
                post_text = f"[r/{subreddit}] {title}\n{body[:MAX_POST_CHARS]}"
                all_posts.append(post_text)
            print(f"  Arctic Shift '{term}': {len(posts)} raw → {len(all_posts)} kept so far")
            time.sleep(DELAY_BETWEEN)
        except Exception as e:
            print(f"  Arctic Shift error for '{term}': {e}")

    # Fallback: try Reddit's old.reddit.com JSON (sometimes less restricted)
    if len(all_posts) < 5:
        print(f"  Trying Reddit old.reddit fallback...")
        all_posts += fetch_posts_reddit_fallback(drug, target - len(all_posts))

    # Deduplicate
    seen = set()
    unique = []
    for p in all_posts:
        key = p[:80]
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique[:target]


def fetch_posts_reddit_fallback(drug, target=30):
    """Fallback: browse subreddit .json directly (no search, just top posts, filter by drug name)."""
    all_posts = []
    for subreddit in drug["subreddits"][:3]:
        if len(all_posts) >= target:
            break
        url = f"https://old.reddit.com/r/{subreddit}/top.json"
        params = {"t": "all", "limit": 50}
        try:
            r = requests.get(url, headers=HEADERS, params=params, timeout=15)
            if r.status_code != 200:
                continue
            data = r.json()
            posts = data.get("data", {}).get("children", [])
            for p in posts:
                pd = p.get("data", {})
                title = pd.get("title", "")
                body  = pd.get("selftext", "") or ""
                full  = (title + " " + body).lower()
                if len(body) < 50: continue
                if body in ("[deleted]", "[removed]"): continue
                if not any(t.lower() in full for t in [drug["name"]] + drug["brands"]): continue
                fp_words = ["i ", "i've", "i'm", "my ", "me ", "myself"]
                if not any(w in full for w in fp_words): continue
                all_posts.append(f"[r/{subreddit}] {title}\n{body[:MAX_POST_CHARS]}")
            time.sleep(DELAY_BETWEEN)
        except Exception as e:
            print(f"  Fallback error r/{subreddit}: {e}")
    return all_posts


def fetch_posts(drug, target=80):
    """Main fetch dispatcher."""
    return fetch_posts_arctic(drug, target)


# ── CLAUDE EXTRACTOR ──────────────────────────────────────────────────────────

def extract_effects(drug, posts):
    """Send posts to Claude for structured extraction."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    posts_text = "\n\n---\n\n".join(posts)
    prompt = EXTRACTION_PROMPT.format(
        drug_name=drug["name"],
        drug_class=drug["class"],
        brands=", ".join(drug["brands"]),
        n_posts=len(posts),
        posts_text=posts_text,
    )

    print(f"  Sending {len(posts)} posts to Claude for extraction...")
    try:
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = message.content[0].text.strip()
        # Extract JSON even if there's surrounding text
        match = re.search(r'\{[\s\S]*\}', raw)
        if match:
            return json.loads(match.group(0))
        else:
            print(f"  Warning: could not parse JSON from Claude response")
            return {"effects": []}
    except Exception as e:
        print(f"  Extraction error: {e}")
        return {"effects": []}


# ── HTML REVIEW INTERFACE ──────────────────────────────────────────────────────

def build_html(results):
    """Build a standalone HTML review interface from extraction results."""

    drug_sections = ""
    for drug_id, data in results.items():
        drug      = data["drug"]
        effects   = data["effects"]
        n_posts   = data["n_posts"]
        if not effects:
            continue

        # Group by domain
        by_domain = {}
        for e in effects:
            d = e.get("domain", "body")
            by_domain.setdefault(d, []).append(e)

        domain_html = ""
        for domain, effs in sorted(by_domain.items()):
            effs_sorted = sorted(effs, key=lambda x: -x.get("source_count", 1))
            rows = ""
            for e in effs_sorted:
                valence = e.get("valence","")
                vc = {"benefit":"#3ecf8e","side_effect":"#e05c5c","variable":"#f5c542"}.get(valence,"#888")
                rows += f"""
                <tr class="effect-row" data-drug="{drug_id}" data-domain="{domain}" data-valence="{valence}">
                  <td><input type="checkbox" class="accept-cb" checked title="Include in output"></td>
                  <td class="effect-text" contenteditable="true">{e.get("effect_text","")}</td>
                  <td><span style="color:{vc};font-weight:600">{valence.replace("_"," ")}</span></td>
                  <td>{e.get("onset","")}</td>
                  <td>{e.get("dose_tier","unknown")}</td>
                  <td style="text-align:center;font-weight:600">{e.get("source_count",1)}</td>
                  <td class="quote-cell"><em style="color:#aaa;font-size:11px">"{e.get("example_quote","")}"</em></td>
                </tr>"""
            domain_html += f"""
            <tr class="domain-header">
              <td colspan="7" style="padding:6px 8px;background:#1a1f3a;color:#8eb8ff;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.07em">{domain}</td>
            </tr>{rows}"""

        drug_sections += f"""
        <div class="drug-section" id="ds-{drug_id}">
          <div class="drug-header">
            <span class="drug-name">{drug["name"]}</span>
            <span class="drug-class">{drug["class"]}</span>
            <span class="post-count">{n_posts} posts analysed · {len(effects)} effects extracted</span>
          </div>
          <table class="effects-table">
            <thead>
              <tr>
                <th style="width:30px">✓</th>
                <th>Effect</th>
                <th style="width:100px">Valence</th>
                <th style="width:90px">Onset</th>
                <th style="width:80px">Dose tier</th>
                <th style="width:60px">Posts</th>
                <th>Example quote</th>
              </tr>
            </thead>
            <tbody>{domain_html}</tbody>
          </table>
        </div>"""

    nav_items = "".join(
        f'<button class="nav-btn" onclick="scrollTo(\'{d["id"]}\')">{d["name"]}</button>'
        for d in DRUGS if d["id"] in results and results[d["id"]]["effects"]
    )

    # Embed results as JSON for export
    results_json = json.dumps(results, indent=2)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PsychoRx — Reddit Experience Review</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: #0d1117; color: #c9d1d9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; font-size: 13px; }}
  header {{ background: #161b22; border-bottom: 1px solid #30363d; padding: 16px 24px; display: flex; align-items: center; gap: 16px; position: sticky; top: 0; z-index: 100; }}
  header h1 {{ font-size: 16px; font-weight: 700; color: #fff; }}
  header p {{ font-size: 12px; color: #8b949e; }}
  .nav {{ background: #0d1117; border-bottom: 1px solid #21262d; padding: 8px 24px; display: flex; gap: 6px; flex-wrap: wrap; position: sticky; top: 57px; z-index: 99; }}
  .nav-btn {{ background: #21262d; border: 1px solid #30363d; color: #c9d1d9; padding: 4px 12px; border-radius: 20px; cursor: pointer; font-size: 11px; }}
  .nav-btn:hover {{ background: #30363d; }}
  .main {{ max-width: 1200px; margin: 0 auto; padding: 24px; }}
  .toolbar {{ display: flex; gap: 10px; margin-bottom: 20px; align-items: center; flex-wrap: wrap; }}
  .toolbar button {{ background: #238636; border: none; color: #fff; padding: 7px 16px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; }}
  .toolbar button.secondary {{ background: #21262d; border: 1px solid #30363d; color: #c9d1d9; }}
  .toolbar button:hover {{ opacity: 0.85; }}
  .filter-group {{ display: flex; gap: 6px; margin-left: auto; }}
  .filter-btn {{ background: #21262d; border: 1px solid #30363d; color: #8b949e; padding: 4px 10px; border-radius: 12px; cursor: pointer; font-size: 11px; }}
  .filter-btn.active {{ border-color: #58a6ff; color: #58a6ff; background: #1f2d3d; }}
  .drug-section {{ background: #161b22; border: 1px solid #30363d; border-radius: 8px; margin-bottom: 24px; overflow: hidden; }}
  .drug-header {{ padding: 14px 16px; background: #1c2128; display: flex; align-items: center; gap: 12px; }}
  .drug-name {{ font-size: 16px; font-weight: 700; color: #fff; }}
  .drug-class {{ font-size: 11px; padding: 2px 8px; border-radius: 10px; background: #1f2d3d; color: #58a6ff; border: 1px solid #1f4068; }}
  .post-count {{ font-size: 11px; color: #8b949e; margin-left: auto; }}
  .effects-table {{ width: 100%; border-collapse: collapse; }}
  .effects-table th {{ background: #1c2128; padding: 8px; text-align: left; font-size: 11px; color: #8b949e; border-bottom: 1px solid #30363d; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; }}
  .effects-table td {{ padding: 7px 8px; border-bottom: 1px solid #21262d; vertical-align: top; }}
  .effect-row:hover {{ background: #1c2128; }}
  .effect-row.rejected {{ opacity: 0.35; }}
  .effect-text {{ color: #e6edf3; }}
  .effect-text:focus {{ outline: 1px solid #58a6ff; border-radius: 3px; }}
  .quote-cell {{ max-width: 280px; word-wrap: break-word; }}
  .accept-cb {{ cursor: pointer; width: 14px; height: 14px; }}
  .domain-header td {{ font-size: 10px !important; }}
  .output-area {{ display: none; background: #0d1117; border: 1px solid #30363d; border-radius: 6px; padding: 16px; margin-top: 16px; }}
  .output-area pre {{ font-size: 11px; color: #3ecf8e; overflow-x: auto; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }}
  .stats-bar {{ display: flex; gap: 20px; padding: 10px 16px; background: #0d1117; border-bottom: 1px solid #21262d; font-size: 11px; color: #8b949e; }}
  .stats-bar span b {{ color: #c9d1d9; }}
</style>
</head>
<body>
<header>
  <div>
    <h1>PsychoRx — Reddit Experience Review</h1>
    <p>Generated {datetime.now().strftime("%Y-%m-%d %H:%M")} · Review and accept/reject extracted effects before incorporating into the tool</p>
  </div>
</header>
<div class="nav">{nav_items}</div>
<div class="main">
  <div class="toolbar">
    <button onclick="exportAccepted()">Export accepted effects (JSON)</button>
    <button class="secondary" onclick="toggleAll(true)">Accept all</button>
    <button class="secondary" onclick="toggleAll(false)">Reject all</button>
    <div class="filter-group">
      <span style="font-size:11px;color:#8b949e;align-self:center">Filter:</span>
      <button class="filter-btn active" onclick="filterValence('all',this)">All</button>
      <button class="filter-btn" onclick="filterValence('benefit',this)" style="color:#3ecf8e">Benefits</button>
      <button class="filter-btn" onclick="filterValence('side_effect',this)" style="color:#e05c5c">Side effects</button>
      <button class="filter-btn" onclick="filterValence('variable',this)" style="color:#f5c542">Variable</button>
    </div>
  </div>
  {drug_sections}
  <div class="output-area" id="outputArea">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
      <span style="font-size:12px;font-weight:600;color:#58a6ff">Accepted effects (JSON)</span>
      <button onclick="copyOutput()" style="font-size:11px;padding:3px 10px;background:#21262d;border:1px solid #30363d;color:#c9d1d9;border-radius:4px;cursor:pointer">Copy</button>
    </div>
    <pre id="outputPre"></pre>
  </div>
</div>
<script>
const RAW_RESULTS = {results_json};

function scrollTo(drugId) {{
  document.getElementById('ds-' + drugId)?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
}}

// Checkbox → visual rejection
document.querySelectorAll('.accept-cb').forEach(cb => {{
  cb.addEventListener('change', function() {{
    this.closest('tr').classList.toggle('rejected', !this.checked);
  }});
}});

function toggleAll(state) {{
  document.querySelectorAll('.accept-cb').forEach(cb => {{
    cb.checked = state;
    cb.closest('tr').classList.toggle('rejected', !state);
  }});
}}

function filterValence(valence, btn) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.effect-row').forEach(row => {{
    const rv = row.dataset.valence;
    row.style.display = (valence === 'all' || rv === valence) ? '' : 'none';
  }});
}}

function exportAccepted() {{
  const output = {{}};
  document.querySelectorAll('.effect-row').forEach(row => {{
    const cb = row.querySelector('.accept-cb');
    if (!cb.checked) return;
    const drugId = row.dataset.drug;
    const domain = row.dataset.domain;
    const valence = row.dataset.valence;
    const effectText = row.querySelector('.effect-text').innerText.trim();
    const onsetCell = row.cells[3].innerText.trim();
    const doseTier  = row.cells[4].innerText.trim();
    const count     = parseInt(row.cells[5].innerText.trim()) || 1;
    const quote     = row.querySelector('.quote-cell em')?.innerText?.replace(/^"|"$/g,'').trim() || '';

    if (!output[drugId]) output[drugId] = [];
    output[drugId].push([domain, effectText, valence, onsetCell, doseTier, count, quote]);
  }});

  document.getElementById('outputPre').textContent = JSON.stringify(output, null, 2);
  const area = document.getElementById('outputArea');
  area.style.display = 'block';
  area.scrollIntoView({{ behavior: 'smooth' }});
}}

function copyOutput() {{
  const text = document.getElementById('outputPre').textContent;
  navigator.clipboard.writeText(text).then(() => alert('Copied to clipboard'));
}}
</script>
</body>
</html>"""


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("PsychoRx Reddit Experience Pipeline")
    print("=" * 40)

    results = {}

    for drug in DRUGS:
        print(f"\n[{drug['name']}] ({drug['class']})")
        print(f"  Fetching posts...")
        posts = fetch_posts(drug, target=POSTS_PER_DRUG)
        print(f"  Got {len(posts)} posts")

        if len(posts) < 5:
            print(f"  Too few posts — skipping extraction")
            results[drug["id"]] = {"drug": drug, "effects": [], "n_posts": len(posts)}
            continue

        extracted = extract_effects(drug, posts)
        effects = extracted.get("effects", [])
        print(f"  Extracted {len(effects)} effects")

        results[drug["id"]] = {
            "drug": drug,
            "effects": effects,
            "n_posts": len(posts),
        }

        # Small delay between drugs to avoid rate limits
        time.sleep(1)

    print(f"\nBuilding HTML review interface...")
    html = build_html(results)
    with open(OUTPUT_FILE, "w") as f:
        f.write(html)

    print(f"\nDone. Open this file in your browser:")
    print(f"  {OUTPUT_FILE}")

    # Summary
    total_effects = sum(len(r["effects"]) for r in results.values())
    print(f"\nSummary:")
    for drug_id, data in results.items():
        print(f"  {data['drug']['name']}: {data['n_posts']} posts → {len(data['effects'])} effects")
    print(f"\nTotal effects extracted: {total_effects}")


if __name__ == "__main__":
    main()
