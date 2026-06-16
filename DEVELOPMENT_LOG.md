# PsychoTIX — Development Log

**Project:** Psychopharmacology Treatment, Interactions and Experience  
**File:** `psychopharmacology_tool.html`  
**Reference sheet:** `PsychoRx_Drug_Database.xlsx`  
**Folder:** `Psychiatric Drugs Receptor Clinical Profiles/`  
**© Dr James Rucker, King's College London, 2026**

---

## Purpose

A single-file HTML tool for psychopharmacologists to explore receptor binding profiles, clinical effects, active metabolites, enzyme interactions, and drug–drug interactions for psychiatric medications. Designed for educational and clinical reference use. Runs locally in any browser — no server or internet connection required.

---

## Session 1 — Initial Build

**Key decisions made:**
- Single-file HTML (no backend, no install) for portability
- Built-in curated dataset rather than live API, to ensure clinical accuracy and offline use
- Radar (spider) chart as primary visualisation — shows receptor profile shape at a glance
- All four major drug classes included from the start: antipsychotics, antidepressants, mood stabilisers, anxiolytics/hypnotics/stimulants
- Affinity scale 0–10 derived from published Ki values (not raw Ki — log-scaled and dose-adjusted)
- Three dose tiers (Low / Medium / High) for each drug, reflecting free brain concentration estimates at typical clinical doses

**Initial drug database (37 drugs):**
- Antipsychotics: quetiapine, olanzapine, clozapine, risperidone, aripiprazole, ziprasidone, lurasidone, cariprazine, haloperidol
- SSRIs: fluoxetine, sertraline, escitalopram
- SNRIs: venlafaxine, duloxetine
- TCAs: amitriptyline, nortriptyline, clomipramine
- Atypical antidepressants: mirtazapine, bupropion, trazodone, vortioxetine
- MAOIs: phenelzine, tranylcypromine, isocarboxazid, selegiline
- Mood stabilisers: lithium, lamotrigine, valproate
- Anxiolytics/hypnotics: diazepam, zolpidem, buspirone
- Stimulants/ADHD: methylphenidate, amphetamine, atomoxetine

**Receptors tracked (14):**
D2, D1, H1, 5-HT2A, 5-HT2C, 5-HT1A, NET, SERT, DAT, M1, α1, α2, GABA-A, μ-Opioid

**Scoring methodology (visible via ℹ️ in header):**

| Score | Ki range | Clinical relevance |
|-------|----------|-------------------|
| 9–10 | <1 nM | Dominant, clinically defining |
| 7–8 | 1–10 nM | High — major clinical contribution |
| 5–6 | 10–100 nM | Moderate — meaningful at therapeutic doses |
| 3–4 | 100 nM–1 μM | Low — may contribute at high doses |
| 1–2 | 1–10 μM | Minimal — unlikely clinically relevant |
| 0 | >10 μM / none | No meaningful binding |

Transporter scores (NET/SERT/DAT) use IC₅₀ for reuptake inhibition. MAOIs use functional monoamine accumulation as proxy. Sources: ChEMBL, PDSP Ki database, Stahl's Prescriber's Guide, published human PET occupancy studies.

**Initial views:**
- **Radar** — spider chart per drug, all three dose tiers overlaid; or per-drug at selected dose when multiple drugs shown
- **Compare** — aggregate radar overlay + heatmap table
- **Effects** — clinical effects grouped by receptor mechanism

---

## Session 2 — Active Metabolites

**Added 9 active metabolites** as separate searchable entries with full receptor profiles, plus overlay toggle on parent drug radar card:

| Metabolite | Parent | Key clinical significance |
|---|---|---|
| Norquetiapine | Quetiapine | Potent NET inhibitor (Ki ~12 nM) + 5-HT2A antagonist — drives mid-dose antidepressant effect |
| Norfluoxetine | Fluoxetine | t½ 4–16 days — responsible for self-tapering washout |
| Paliperidone | Risperidone | Primary active metabolite; also standalone drug (Invega) |
| Desvenlafaxine | Venlafaxine | More balanced SERT:NET than parent; standalone as Pristiq |
| Desmethylclomipramine | Clomipramine | Potent NET inhibitor — shifts profile from SERT to NE over time |
| Nortriptyline (from AMI) | Amitriptyline | Standalone drug; predominantly NET |
| Dehydro-aripiprazole | Aripiprazole | ~40% D2 activity; relevant in CYP2D6 poor metabolisers |
| Hydroxybupropion | Bupropion | 3–10× parent plasma levels; carries much of the NET/DAT effect |
| l-Amphetamine | Selegiline | Explains oral vs transdermal stimulant side effect difference |

**Metabolite UI features:**
- Searchable by name (marked with ◆ in results, MET tag on chips)
- Clickable pills in sidebar Detail tab to add to chart
- Radar overlay toggle (dashed lines) on parent drug card
- Sidebar shows parent→metabolite and metabolite→parent navigation

---

## Session 3 — Interaction Types (Agonist/Antagonist etc.)

**Added 8 interaction type categories** with symbols and colours:

| Type | Symbol | Colour | Description |
|---|---|---|---|
| Antagonist | ⊗ | Red | Blocks receptor, no intrinsic activity |
| Inverse Agonist | ⊖ | Dark red | Suppresses constitutive receptor activity |
| Partial Agonist | ◑ | Yellow | Submaximal efficacy — functional antagonist in high-tone states |
| Agonist | ● | Green | Full receptor activation |
| Reuptake Inhibitor | ⟳ | Blue | Blocks transporter |
| Releaser | ↑↑ | Light green | Reverses transporter — floods synapse |
| PAM | ⊕ | Teal | Positive allosteric modulator (GABA-A site) |
| Indirect | ~ | Grey | Via enzyme inhibition or downstream signalling |

**Every drug's `interactions` map** specifies the type for each receptor it acts at.

**Visible in:**
- Radar chart point colours (each point coloured by its interaction type, transparent if affinity = 0 at that dose)
- Interaction legend badges on each radar card
- Sidebar Detail panel: each receptor shown with type badge + specific clinical consequence text
- Heatmap: interaction symbol below each affinity score
- Compare view: interaction legend at top

**Key clinical distinctions now encoded:**
- Olanzapine/clozapine = **inverse agonist** at 5-HT2A vs quetiapine/risperidone = **antagonist**
- Aripiprazole/cariprazine = **partial agonist** at D2 vs haloperidol = **antagonist**
- Amphetamine = **releaser** vs methylphenidate = **reuptake inhibitor**
- Benzodiazepines/valproate = **PAM** at GABA-A
- Lithium/lamotrigine = **indirect** (no direct receptor binding)

---

## Session 4 — MAOIs Added

Added all four MAOIs with appropriate notes on irreversible enzyme inhibition:
- Phenelzine (MAO-A/B + GABA-T inhibitor — unique GABA mechanism)
- Tranylcypromine (MAO-A/B + amphetamine-like DA/NE release — more activating)
- Isocarboxazid (MAO-A/B — intermediate profile)
- Selegiline (MAO-B selective at 6mg patch; loses selectivity at 9–12mg)

**MAOI-specific notes:**
- Affinities shown are functional/indirect (MAO inhibition → monoamine accumulation), not direct receptor Ki
- Cards flagged with ★ notation
- Selegiline's dose slider demonstrates selectivity shift: low dose = dopaminergic only; high dose = full monoamine profile

---

## Session 5 — Layout Redesign (Option A — Tabbed Sidebar)

**Problem:** Sidebar became overcrowded with search, chips, dose slider, receptor mechanisms, enzyme data, and clinical notes all stacked vertically.

**Solution:** Three-tab sidebar + dose slider moved to main header:

**Sidebar tabs:**
- **Search** — drug/receptor/effect search + selected drug chips
- **Detail** — clinical effects at current dose + receptor mechanism breakdown (interaction type + clinical consequence per receptor)
- **Metabolism** — enzyme substrate/inhibitor/inducer data + clinical notes

**Main panel tabs (4):**
- **Radar** — spider chart(s)
- **Compare** — aggregate radar + heatmap
- **Effects** — clinical effects grouped
- **Interactions** — DDI checker + metabolism summary table (extracted from Compare)

**Auto-behaviours:**
- Clicking a drug chip auto-switches sidebar to Detail tab
- Clicking "Metabolism" tab in sidebar shows enzyme data for focused drug

---

## Session 6 — Enzyme Metabolism & DDI Checker

**Added `metabolism` object to every drug** with fields:
- `substrate`: enzymes that metabolise this drug, with potency (major/moderate/minor)
- `inhibits`: enzymes this drug inhibits, raising co-substrate levels
- `induces`: enzymes this drug induces, lowering co-substrate levels
- `note`: clinical pearls (pharmacogenomics, special cases)

**Enzyme database (11 entries):** CYP1A2, CYP2B6, CYP2C9, CYP2C19, CYP2D6, CYP3A4, CYP3A5, UGT, MAO-A, MAO-B, FMO, CES1

**Sidebar Metabolism tab shows:**
- Substrate of (blue pills) — Major/Moderate/Minor
- Inhibits (red pills)
- Induces (green pills)
- Clinical pharmacogenomics notes (e.g. atomoxetine: ~10× exposure in CYP2D6 poor metabolisers)

**Interactions tab — DDI checker:**
- Automatically detects CYP substrate/inhibitor/inducer overlaps between all selected drugs
- Severity-coded: ⚠ High, △ Moderate, ○ Low
- Special detection: MAOI + serotonergic agent → serotonin syndrome warning
- Example: fluoxetine (strong CYP2D6 inhibitor) + haloperidol (major CYP2D6 substrate) → High severity flagged

**Notable specific interactions encoded:**
- Fluvoxamine + clozapine/olanzapine (CYP1A2 — can 5–10× antipsychotic levels)
- Valproate + lamotrigine (UGT inhibition — doubles lamotrigine; halve dose)
- Valproate + carbamazepine (epoxide hydrolase — raises CBZ-epoxide → toxicity)
- Carbamazepine autoinduction
- Lithium: renal not CYP — NSAIDs/ACEi/thiazides raise levels

---

## Session 7 — Per-Drug Dose Selection

**Problem:** Single global dose slider applied to all drugs simultaneously.

**Change:** Each drug chip now has independent L / M / H dose buttons.

- `drugDoseLevels` map stores dose per drug id
- Default = Medium (2) on add
- All views (radar, compare, effects, interactions, detail panel) use `getDoseFor(drugId)` instead of global `doseLevel`
- Heatmap and aggregate views show each drug's dose label (e.g. "quetiapine low dose")
- Dose range shown as tooltip on hover of L/M/H buttons
- Clinical use case: compare quetiapine Low (sedation profile) vs olanzapine High (antipsychotic profile) side by side

---

## Session 8 — Drug Database Expansion (+23 drugs)

**Added to reach 52 drugs total:**

**Antipsychotics (+4):** loxapine, amisulpride, brexpiprazole, iloperidone

**SSRIs (+3):** citalopram, paroxetine, fluvoxamine

**SNRIs (+2):** levomilnacipran, milnacipran

**TCAs (+2):** imipramine, doxepin

**Atypical antidepressants (+2):** agomelatine, vilazodone

**Mood stabilisers (+2):** carbamazepine, oxcarbazepine

**Benzodiazepines (+3):** lorazepam, clonazepam, alprazolam

**Standalone TCA (+1):** desipramine

**Notable pharmacological points captured:**
- Amisulpride: no CYP metabolism (renal), selective D2/D3 only, no H1/M1/5-HT2A — unique radar shape
- Agomelatine: no monoamine transporter activity at all; MT1/MT2 agonism not shown (not a classic receptor); hepatotoxicity monitoring requirement
- Fluvoxamine: sigma-1 agonism noted; dangerous CYP1A2 inhibitor (contraindicated with clozapine at high doses)
- Lorazepam: no CYP — direct glucuronidation, preferred in liver disease
- Oxcarbazepine: prodrug → licarbazepine (MHD)
- Levomilnacipran: most noradrenergic SNRI (NET:SERT ~2:1)

---

## Session 9 — Metabolite Audit & New Metabolites

**Systematic audit** of all 52 drugs against known clinically significant active metabolites.

**Added 7 new metabolites:**

| Metabolite | Parent | Why clinically important |
|---|---|---|
| Norclozapine | Clozapine | Only antipsychotic metabolite with M1 AGONISM (pro-cognitive); D2 partial agonist; ~50% of clozapine plasma levels |
| Amoxapine | Loxapine | Major metabolite; standalone antidepressant; strong NET + D2 antagonism |
| mCPP | Trazodone | 5-HT2C AGONIST (anxiogenic) — opposite to parent trazodone; explains paradoxical anxiety with chronic use; dramatically elevated by CYP2D6 inhibitors |
| Desipramine | Imipramine | Most selective NET inhibitor of all TCAs; also standalone drug |
| CBZ-10,11-Epoxide | Carbamazepine | Active anticonvulsant + neurotoxic; accumulates when valproate co-prescribed (epoxide hydrolase inhibition) |
| Licarbazepine/MHD | Oxcarbazepine | True active form — oxcarbazepine is a prodrug; standalone as eslicarbazepine (Aptiom) |
| Nordiazepam | Diazepam | t½ 36–200h; explains prolonged diazepam clinical effect; further metabolised to oxazepam and temazepam |

**Skipped (minor/inactive):** desmethylsertraline, desmethylmirtazapine, nordoxepin, alprazolam hydroxy metabolites, clonazepam 7-amino (urine marker only), lorazepam glucuronide (inactive), phenelzine metabolites (mechanism not receptor-based)

**Desipramine also added as standalone drug** (after nortriptyline in TCA section).

---

## Session 10 — Radar Point Colour Bug Fix

**Bug:** All radar points on quetiapine chart appeared as reuptake inhibitor blue (light blue), regardless of actual interaction type.

**Root cause:** `buildPointColors()` was called once and shared across all three dose-level datasets. Receptors with 0 affinity at a given dose (e.g. NET at low dose for quetiapine) were still rendered with their interaction type colour.

**Fix:** 
- `buildPointColors(entry, baseColor, doseIdx)` now takes a dose index parameter
- Points with value = 0 at that dose render as `'transparent'`
- Each dose dataset (Low/Medium/High) gets its own colour array computed for its specific dose index
- Net result: quetiapine D2/H1/5-HT2A show red (antagonist); 5-HT1A yellow (partial agonist); NET/SERT blue (reuptake inhibitor) only on Medium/High lines where norquetiapine is active

---

## Session 11 — Excel Reference Sheet

**Generated:** `PsychoRx_Drug_Database.xlsx`

**Three sheets:**

1. **Drug List** — all 60 drugs + 16 metabolites with columns:
   - Drug Name, Brand Name(s), Class, Type (Drug/Metabolite), Parent Drug
   - Dose Low / Medium / High
   - Key Receptors (antagonised), Key Receptors (agonised/partially agonised)
   - Enzyme Substrate, Enzyme Inhibits/Induces
   - Colour-coded by drug class

2. **Add New Drug** — blank template rows with yellow tint, guidance text in row 3, for adding new agents

3. **Receptor & Enzyme Key** — reference table for all 14 receptors and 11 enzymes with clinical significance notes

---

## Current Database Summary

**52 drugs + 16 active metabolites = 68 total searchable entries**

| Category | Count |
|---|---|
| Atypical antipsychotics | 12 |
| Typical antipsychotics | 1 |
| SSRIs | 6 |
| SNRIs | 4 |
| TCAs | 6 |
| Atypical/novel antidepressants | 6 |
| MAOIs | 4 |
| Mood stabilisers/anticonvulsants | 5 |
| Benzodiazepines/hypnotics/anxiolytics | 6 |
| Stimulants/ADHD | 3 |
| **Active metabolites** | **16** |

---

## Search Modes

### By Drug
- Searches name, brand, class
- Metabolites searchable (marked ◆)

### By Receptor
- Type receptor name/label → shows drugs active at that receptor with affinity scores and interaction type symbols
- Type interaction type keyword (antagonist, partial agonist, reuptake, releaser, PAM, indirect) → shows receptor × mechanism pairs → click to drill into drug list

### By Effect
- Searches clinical effect descriptions
- Returns all drugs across all dose tiers with that effect

---

## Known Limitations / Future Considerations

- Receptor affinities are curated estimates, not raw Ki values — intended for relative comparison, not absolute pharmacokinetic modelling
- MAOI affinities represent functional monoamine consequences, not direct binding
- Agomelatine's melatonin receptor agonism (MT1/MT2) is not represented in the receptor panel (panel covers monoaminergic/GABAergic targets only)
- Sigma-1 receptor (relevant for fluvoxamine, some antipsychotics) not currently in receptor panel
- D3 receptor (relevant for cariprazine, aripiprazole) not shown separately from D2
- 5-HT3, 5-HT7 (relevant for vortioxetine) not currently tracked
- No pharmacokinetic parameters (Tmax, t½, protein binding) — only dose ranges
- Dose tiers are broad clinical approximations; individual PK variability (CYP polymorphisms, hepatic/renal function) not modelled

**Potential additions for future sessions:**
- Additional receptors: sigma-1, D3, 5-HT3, 5-HT7, κ-opioid
- Additional drugs: clonidine, guanfacine, naltrexone, buprenorphine, ketamine/esketamine, psilocybin, MDMA (PTSD indication), newer antipsychotics (lumateperone, pimavanserin)
- User-importable drug data from Excel sheet
- Export current view as PDF/image
- Print-optimised layout

---

## File Structure

```
Psychiatric Drugs Receptor Clinical Profiles/
├── psychopharmacology_tool.html    ← Main tool (single file, open in browser)
├── PsychoRx_Drug_Database.xlsx     ← Reference/data entry spreadsheet
└── DEVELOPMENT_LOG.md              ← This file
```

---

---

## Session 12 — Global Drug Database Expansion (+109 drugs)

**Source:** Neuropsychiatric_Drugs_Global.xlsx — 12 drug category sheets covering global availability

**Cross-reference results:**
- Already in tool: 56 drugs
- Newly added: 109 drugs
- Skipped (biologics, withdrawn, too niche, no receptor profile): 77

**New drugs added by category:**

**Additional typical antipsychotics (11):** chlorpromazine, fluphenazine, perphenazine, trifluoperazine, droperidol, sulpiride, pimozide, zuclopenthixol, flupenthixol, thiothixene, prochlorperazine

**Additional atypical antipsychotics (7):** asenapine, lumateperone, pimavanserin, zotepine, blonanserin, perospirone, xanomeline-trospium

**Additional antidepressants (16):** moclobemide, reboxetine, mianserin, maprotiline, nefazodone, tianeptine, lofepramine, dosulepin, protriptyline, amoxapine (standalone), esketamine, ketamine (IV), zuranolone, brexanolone, dapoxetine, psilocybin

**Additional ADHD/wakefulness (11):** lisdexamfetamine, dextroamphetamine, dexmethylphenidate, modafinil, armodafinil, solriamfetol, pitolisant, viloxazine, guanfacine, clonidine, sodium oxybate

**Addiction/opioid pharmacology (10):** methadone, buprenorphine, naltrexone, naloxone, acamprosate, disulfiram, nalmefene, varenicline, baclofen, lofexidine

**PTSD (1):** prazosin

**Dementia/cognition (4):** donepezil, rivastigmine, galantamine, memantine

**Parkinson's/movement (11):** pramipexole, ropinirole, rotigotine, rasagiline, safinamide, amantadine, tetrabenazine, valbenazine, deutetrabenazine, trihexyphenidyl, benztropine

**Additional anxiolytics/hypnotics (10):** chlordiazepoxide, oxazepam, temazepam, hydroxyzine, suvorexant, lemborexant, daridorexant, zopiclone, eszopiclone, zaleplon

**Anticonvulsants/mood stabilisers (13):** topiramate, pregabalin, gabapentin, levetiracetam, zonisamide, lacosamide, eslicarbazepine, cenobamate, phenytoin, phenobarbital, ethosuximide, clobazam, cannabidiol (CBD), brivaracetam

**Migraine (12):** sumatriptan, rizatriptan, zolmitriptan, naratriptan, eletriptan, frovatriptan, almotriptan, lasmiditan, ubrogepant, rimegepant, atogepant, zavegepant, dihydroergotamine

**Notable pharmacological highlights:**
- Xanomeline-trospium (Cobenfy): first antipsychotic with no D2 activity — M1/M4 muscarinic agonism
- Pimavanserin: selective 5-HT2A/2C inverse agonist — no D2, designed for Parkinson's psychosis
- Lumateperone: D1 agonism + SERT inhibition + D2 partial agonism — novel multimodal profile
- Pitolisant: H3 inverse agonist — first non-stimulant, non-scheduled wakefulness agent
- Lasmiditan: 5-HT1F agonist (ditan) — no vasoconstriction, safe in cardiovascular disease
- Gepants (ubrogepant, rimegepant, atogepant, zavegepant): CGRP receptor antagonists — novel migraine class
- Zuranolone/brexanolone: neurosteroid GABA-A PAM — first drugs for postpartum/major depression via this mechanism
- Psilocybin: 5-HT2A agonist — breakthrough therapy designation, included as emerging licensed therapy
- DORAs (suvorexant, lemborexant, daridorexant): orexin receptor antagonists — mechanistically distinct insomnia class
- Cenobamate: dual GABA-A PAM (novel site) + Na+ channel — 20% seizure-free rate in refractory focal epilepsy
- Tianeptine: μ-opioid partial agonist — explains abuse potential of extended-release formulation
- Benztropine: unique among anticholinergics — also inhibits DAT (reuptake inhibitor)

**Current database: 161 drugs + 16 metabolites = 177 total searchable entries**

---

## Session 13 — New Receptors, Beta-Blockers, Experiential Effects

### New receptors added (panel now 24 axes)

Six new receptors added to the radar: **D3, 5-HT3, 5-HT7, σ1 (Sigma-1), nACh (α4β2 nicotinic), OX1/2 (Orexin)**. Plus **CB1** and **H2** on request. All 165 drugs updated with values for each new receptor.

Clinically significant patterns now visible:
- Fluvoxamine's σ1 agonism (6–9) — unique among SSRIs, explains neuroprotective/antidepressant augmentation properties
- Cariprazine's D3 dominance (8–10) — highest of any antipsychotic, now clearly differentiated from aripiprazole
- Vortioxetine's full multimodal profile: 5-HT3 antagonism (6–9) + 5-HT7 antagonism (4–7)
- DORAs (suvorexant/lemborexant/daridorexant): only OX1/2 antagonism — completely distinct from BZDs/Z-drugs on radar
- Varenicline: nACh partial agonism (7–10) now shows as primary mechanism
- Mirtazapine: 5-HT3 antagonism (7–9) explains antiemetic properties and why it reduces SSRI-induced nausea
- Memantine: 5-HT3 antagonism alongside NMDA antagonism

### Beta-blockers added (4 drugs)

Added propranolol, atenolol, metoprolol, and nadolol with **β1 and β2** as new receptor axes.

Key pharmacological distinctions encoded:
- Propranolol: non-selective β1+β2 + 5-HT1A antagonism + highest lipophilicity → best CNS penetration → most effective for tremor, akathisia, performance anxiety
- Atenolol: β1-selective, hydrophilic → minimal CNS entry → least useful for psychiatric indications
- Metoprolol: β1-selective, moderate lipophilicity; strong CYP2D6 substrate — fluoxetine/paroxetine co-prescription causes bradycardia (flagged in DDI checker)
- Nadolol: non-selective like propranolol but hydrophilic → peripheral mechanism only

Psychiatric indications covered: performance anxiety (PRN), akathisia, lithium tremor, essential tremor, alcohol withdrawal tremor, PTSD nightmares, migraine prevention.

### Single-drug radar — dose-responsive behaviour

**Bug fixed:** single-drug radar previously always showed all three dose lines regardless of the dose selected on the chip.

**New behaviour:** radar shows only the selected dose by default, matching the L/M/H chip selection. A "Compare all dose levels" toggle restores the three-line overlay view. The chart title now shows the active dose level and dose range in the matching colour (green=Low, blue=Medium, red=High).

### Experience tab — new fifth main panel tab

Added a patient-experience oriented view alongside the mechanistic Effects tab. Organised by 9 experiential domains:
- Mood & Emotion, Arousal & Energy, Sleep, Anxiety & Fear, Thought & Cognition, Perception & Reality, Motivation & Reward, Bodily & Somatic, Autonomic & Performance

Each effect is labelled as **Therapeutic** (green), **Side effect** (red), or **Variable** (yellow), with onset timing (acute/days/weeks). Respects per-drug dose selection.

Initial coverage: 25 drugs with full experiential profiles. Others show "no data yet" notice.

### Receptor ↔ Experience bidirectional linking

**Experience tab → receptors:** each effect card shows "via: [receptor badges]" beneath it, colour-matched to the radar spoke colours. E.g. "Sleep onset improved" shows H1 in yellow; "Sedation" shows H1 + α1.

**Detail sidebar → experiences:** each receptor row in the mechanism panel now shows up to 4 patient-experience chips below the mechanistic description. E.g. H1 antagonism row shows "Sleep onset improved · Sedation / daytime drowsiness · Appetite increased · Nausea reduced".

Implemented via `RECEPTOR_EXPERIENCE_MAP`: receptor × interaction type → list of experiential effects. Consistent colour coding throughout (same colour on radar point, mechanism badge, "via" tag, and domain card).

### Experience search in sidebar

Extended "By Effect" search to cover three result types:

- **experience** (green tag) — patient-reported effect text. Substring match, so "sedation" finds "Pronounced sedation", "Sedation / daytime drowsiness" etc. Results show the actual matched text. Clicking opens a drill-down list of drugs with that effect at the relevant dose; adding a drug automatically sets it to the dose where that effect occurs.
- **domain** (blue tag) — the 9 experiential domains. Clicking a domain shows all effects within it, then drill-down to drugs.
- **clinical** (no tag) — existing CLINICAL_EFFECTS diagnostic terms (unchanged).

### Bug fixes

1. **Radar point colours** — fixed `buildPointColors()` to take a dose index parameter; points with zero affinity at a given dose now render transparent, preventing incorrect colour bleed across dose tiers.

2. **Experiential search exact-match bug** — `filterByExperience` was using exact string equality, so searching "sedation" returned nothing. Fixed to substring matching throughout (search, drill-down, and "add all").

3. **Missing side effects at medium dose** — systematic audit found sedation, weight gain, anticholinergic effects etc. were only listed in the `low` dose tier for olanzapine, quetiapine, haloperidol, mirtazapine and others. Full audit confirmed 19/25 drugs were already complete after fix; the 6 apparent gaps (initial anxiety for SSRIs, dissociation for esketamine etc.) are clinically accurate — they reflect genuinely transient effects.

---

## Current Database Summary

**165 drugs + 16 active metabolites = 181 total searchable entries**
**24 receptor axes on radar**
**25 drugs with full experiential profiles**

| Category | Count |
|---|---|
| Atypical antipsychotics | 13 |
| Typical antipsychotics | 12 |
| SSRIs | 6 |
| SNRIs | 4 |
| TCAs | 7 |
| Atypical/novel antidepressants | 10 |
| MAOIs | 4 |
| Mood stabilisers/anticonvulsants | 14 |
| Benzodiazepines/hypnotics/anxiolytics | 12 |
| Stimulants/wakefulness/ADHD | 11 |
| Beta-blockers | 4 |
| Addiction/opioid pharmacology | 10 |
| Dementia/cognition | 4 |
| Parkinson's/movement | 11 |
| Migraine | 13 |
| Psychedelics/novel | 4 |
| **Active metabolites** | **16** |

---

---

## Session 14 — Psychedelics, Receptor Expansion, UX Polish

### New drug class: Psychedelics & Entactogens (8 drugs)

| Drug | Class | Key pharmacological note |
|---|---|---|
| DMT | Tryptamine | Endogenous; short-acting; σ1 agonism; 5-HT2A >> 5-HT1A |
| 5-MeO-DMT | Tryptamine | Higher 5-HT1A than DMT — more ego-dissolution, less visual |
| LSD | Lysergamide | Most complex receptor profile; β-arrestin kinetics explain duration; high 5-HT2B |
| DOI | Phenethylamine (DOx) | Highest 5-HT2B of any psychedelic; amphetamine-like DAT/NET; 16–30h |
| Mescaline | Phenethylamine | Weaker 5-HT2A than LSD; some DA/NE reuptake; prominent nausea |
| 2C-B | Phenethylamine (2C-x) | Hybrid: 5-HT2A agonist + SERT/NET/DAT inhibition; 4–6h |
| MDMA | Entactogen | Monoamine releaser (SERT>>NET>DAT); Breakthrough Therapy for PTSD |
| Methylone | Cathinone | Reuptake inhibitor (vs MDMA's releaser mechanism); less empathogenic, higher abuse potential |

### New receptor axes (panel now 26 total)

- **5-HT2B** — cardiac valvulopathy risk with chronic agonism (DOI >> LSD > 2C-B > DMT); triptans have 5-HT2B agonism
- **5-HT1B** — triptan mechanism; autoreceptor modulating serotonin release; modulates psychedelic experience quality

All 173 drugs and 16 metabolites updated with 5-HT2B and 5-HT1B values.

### Drug colour distinctness system

Fixed: psychedelics were all assigned similar purple shades, making multi-drug radar charts unreadable.

**Distinct colour palette per psychedelic:**
- DMT: violet `#9040d0`, 5-MeO-DMT: teal `#20c0a0`, LSD: amber `#e0a000`, DOI: orange-red `#e04000`, 2C-B: magenta `#c000c0`, MDMA: hot pink `#e04080`, methylone: wine `#a04060`, psilocybin: deep violet `#7030c0`

**Runtime distinctness check:** `getDrugColor()` now detects when any two selected drugs have colours within 100 RGB units and auto-reassigns from a 15-colour maximally-separated palette.

### Interaction type colouring — default receptor map

Added `DEFAULT_RECEPTOR_ITYPE` — a fallback map specifying the most common interaction type per receptor (e.g. 5-HT2B → agonist, OX → antagonist, nACh → antagonist). Previously, if a drug had activity at a receptor not explicitly in its `interactions` map, the point defaulted to the drug's base colour instead of the interaction type colour. Now all 26 axes colour correctly.

### Single-drug radar — dose-responsive behaviour

Changed so chart shows only the selected dose by default (matching the L/M/H chip). "Compare all dose levels" toggle restores the three-line overlay. Chart title now shows active dose level and range in the matching colour.

### Compare view — aggregate radar enlarged

Aggregate radar moved to full width at 520px height (was half-width at 280px). Drug contributions panel moved below the chart. Point radius increased to 4 for readability.

### Split-circle plugin for overlapping interaction types

When two drugs with **different interaction types** at the same receptor have points within 10px of each other on the canvas, a custom Chart.js plugin draws a **split circle** (pie-chart sectors) so both interaction type colours are visible simultaneously. Works per-cluster — two overlapping drugs get a half-circle split; three get thirds; a distant third drug gets its own independent point.

### Dose labels — "dose" suffix added everywhere

"High" → "High dose" throughout — chart legends, card subtitles, contribution panels. Prevents misreading "Psilocybin (High)" as "high receptor affinity" rather than "high dose selected."

### CONTRAINDICATED DDI severity level

Added a 🚫 CONTRAINDICATED tier (above ⚠ High) displayed in bright red with distinctive background. Specific combinations flagged:
- **Absolutely contraindicated:** MAOI + any SERT reuptake inhibitor (SSRIs, SNRIs, clomipramine) — serotonin syndrome; MAOI + monoamine releasers (amphetamine, MDMA, methylone) — catastrophic; MAOI + triptans; two MAOIs together; MAOI + stimulant (hypertensive crisis)
- **High risk (⚠):** MAOI + mirtazapine (lower serotonin syndrome risk); CYP interactions
- **Correctly not flagged:** MAOI + benzodiazepines, MAOI + beta-blockers, MAOI + mood stabilisers

### Keyboard navigation in search

Arrow keys navigate results, Enter adds the highlighted (or first) item, Escape clears. Focused result highlighted in accent colour.

### Experience search — bug fixes

1. **onclick double-quote bug:** `JSON.stringify("Low mood lifted")` produces `"Low mood lifted"` with double quotes inside `onclick="..."` — the HTML attribute was terminated at the first inner quote. Fixed to use single-quoted JS strings.

2. **Search input re-trigger bug:** `filterByExperience` and `filterByExperienceDomain` were setting `searchInput.value` which fired `oninput` → `onSearch()` and immediately overwrote the sub-list. Fixed by not setting input value in those functions.

3. **Behaviour change:** clicking an experience result now directly adds all matching drugs at their relevant dose and switches to the Experience tab. No second click required.

4. **Dose selection on experience search:** when drugs are added via experience search, they are set to the lowest dose tier where that effect appears. "Low mood lifted" → medium dose for antidepressants (correct: therapeutic doses required). "Sleep onset improved" → low dose for sedating drugs. "Psychosis controlled" → high dose for antipsychotics.

---

## Current Database Summary

**173 drugs + 16 active metabolites = 189 total searchable entries**
**26 receptor axes on radar**
**25 drugs with full experiential profiles**

| Category | Count |
|---|---|
| Atypical antipsychotics | 16 |
| Typical antipsychotics | 12 |
| SSRIs | 6 |
| SNRIs | 4 |
| TCAs | 9 |
| Atypical/novel/psychedelic antidepressants | 18 |
| MAOIs | 4 |
| Mood stabilisers/anticonvulsants | 14 |
| Benzodiazepines/hypnotics/anxiolytics | 13 |
| Stimulants/wakefulness/ADHD | 11 |
| Beta-blockers | 4 |
| Addiction/opioid | 10 |
| Dementia/cognition | 4 |
| Parkinson's/movement | 13 |
| Migraine | 13 |
| Psychedelics/entactogens | 8 |
| **Active metabolites** | **16** |

---

---

## Session 15 — Spider Plot Rebuild, UI Cleanup, Search Fixes

### Spider plot rendering — complete rebuild

The previous custom canvas plugin (`mechanismFillPlugin`) used `destination-out` compositing to erase and redraw points with greyscale mechanism fills. On a transparent canvas this punched visible holes through to the HTML background, breaking the chart entirely.

**Solution:** Removed all custom canvas drawing. Replaced with Chart.js native per-point property arrays:
- `pointStyle[]` — Chart.js built-in shapes (circle, triangle, rectRot, rect, cross, star, crossRot)
- `pointBackgroundColor[]` — white fill for all visible points
- `pointBorderColor[]` — drug colour (from `getDrugColor()`)
- `pointRadius[]` — 9 for active receptors, 0 for zero-affinity

**Encoding principle (finalised):**
- **Shape = mechanism** (agonist=●, antagonist=▲, inverse agonist=◆, partial agonist=■, reuptake inhibitor=+, releaser=★, PAM=✕, binding-only=○)
- **Colour = drug & dose** (each drug gets a unique colour; metabolites use yellow)
- No colour encoding of mechanism at all — cleaner, unambiguous

**`buildPointStyles(entry, drugColor, doseIdx)`** — central function returning per-receptor `{style, bg, border, radius}` arrays. Used for all four rendering contexts (radar view, compare view, detail view, metabolite overlays).

### Connecting lines removed; filled area retained

`borderWidth: 0` removes the lines between receptor points while `backgroundColor` fill is preserved. The filled polygon area conveys the overall profile shape; the connecting lines added no information and cluttered the chart.

### Charts enlarged

`chart-wrap` height increased to 560px; `charts-grid` minimum column width increased to 560px.

### Mechanism legend redesigned

Replaced small grey text with a prominent styled legend box showing:
- Shape symbols with labels for all 8 mechanism types
- Divider + "Colour = drug & dose" section with colour swatches per selected drug

CSS classes: `.mechanism-legend`, `.mechanism-legend-title`, `.mechanism-legend-item`

### `indirect` / unknown binding — hollow circle

Receptors where binding data exists but mechanism is uncharacterised previously showed a `-` dash (Chart.js `dash` pointStyle). Changed to:
- Spider plot: hollow circle (white bg=transparent, border=drug colour)
- Heatmap: `○` symbol
- Legend: "Binding only (mechanism unknown)" entry added

Rationale: suppressing the point entirely was misleading (implied no activity); a hollow circle honestly signals "affinity confirmed, functional consequence unknown."

### Metabolite overlays — mechanism shapes added

Previously metabolite datasets used flat `pointRadius: 2` with no shape variation. Now routed through `buildPointStyles()` — metabolite points show the same shape encoding as parent drugs, with yellow border colour.

### Heatmap moved to its own tab

Heatmap extracted from Compare view into a dedicated "Heatmap" tab. Compare view now contains only the aggregate radar overlay.

**Heatmap layout transposed:** receptors now run top-to-bottom (rows), drugs left-to-right (columns) — more readable for wide drug sets.

**Heatmap symbols updated** to use `MECHANISM_SYMBOL` characters (●▲◆■+★✕○) consistent with the spider plot legend. Legend added below the heatmap.

### Left sidebar — Detail and Metabolism tabs removed

Detail and Metabolism tabs removed from the sidebar. Left pane is now exclusively: search (By Drug / By Receptor / By Effect) + selected drug chips. The `renderSidebarDetail()` function is retained internally but guarded with null checks so it silently no-ops when the target DOM elements are absent.

### Receptor search — fixed

**Bug:** Typing "5-HT" returned only propranolol. Root cause: the combined-query loop iterated all interaction types, stripped their label words from the query, and the loose substring match on the remainder falsely matched receptor IDs (propranolol has 5-HT1B activity).

**Fix:** Combined-query loop now only fires when stripping the interaction type word meaningfully shortened the query (guard: `recPart.length >= q.length - 1 → continue`). This ensures the combined path requires both a receptor name AND an interaction type keyword to be present in the query.

Result: "5-HT" now correctly returns all 7 serotonin receptors (5-HT1A through 5-HT7).

### Receptor search results — cleaned up

- Removed interaction type coloured badge pills from receptor search results (hangover from old encoding system)
- Receptor name colour coding removed — plain white text
- Each receptor result now shows: receptor name | drug count (right-aligned) | description text below
- Drug lists within receptor results now use `MECHANISM_SYMBOL` characters instead of old `it.symbol` coloured icons
- Receptor colour fix: 5-HT1B (`#6a7fe8`) and 5-HT2B (`#8b6dd6`) were near-black — updated to visible purple/blue shades

### Ki data Excel file

**Generated:** `PsychoRx_Ki_Data.xlsx` — new file separate from `PsychoRx_Drug_Database.xlsx`

Three sheets:
1. **Affinity Scores (0–10)** — 173 drugs × 32 receptors. Colour-coded cells by mechanism type (green intensity = agonist strength, red = antagonist, yellow = partial agonist, cyan = reuptake inhibitor). Mechanism abbreviation column per receptor (AGO, pAGO, invAGO, ANT, RI, REL, PAM, IND).
2. **Mechanism Key** — abbreviation → full name → symbol → description
3. **Sources & Methodology** — primary references (PDSP Ki database, Owens 1997, Kroeze 2003, Stahl, Nichols 2016, etc.) + explanation of Ki → 0–10 conversion formula

---

## File Structure

```
Psychiatric Drugs Receptor Clinical Profiles/
├── psychopharmacology_tool.html    ← Main tool (single file, open in browser)
├── PsychoRx_Drug_Database.xlsx     ← Drug list reference sheet
├── PsychoRx_Ki_Data.xlsx           ← Ki affinity data + sources (new)
└── DEVELOPMENT_LOG.md              ← This file
```

---

*Log maintained by Claude (Anthropic). Update this file at the start of each session with what was changed and why.*

---

## Session — 2026-06-08

### Drugs added (10 new)

**Cannabinoid:**
- `thc` — Δ9-Tetrahydrocannabinol (Dronabinol / Nabilone / Nabiximols). CB1 partial agonist [7,9,10]; broad downstream dopaminergic, GABAergic, opioid, glutamatergic effects indirect. Three dose tiers reflect therapeutic vs. psychotomimetic range.

**Parkinson's / Neurological (8 new drugs):**
- `levodopa_carbidopa` — Gold standard PD treatment. D1/D2 agonist (indirect via precursor); receptor scores represent net dopaminergic tone.
- `entacapone` — Peripheral COMT inhibitor; adjunct to levodopa; no hepatotoxicity; orange urine (harmless).
- `tolcapone` — Central + peripheral COMT inhibitor; more potent than entacapone; black box hepatotoxicity — LFT monitoring mandatory.
- `opicapone` — Once-nightly peripheral COMT inhibitor; no hepatotoxicity; currently preferred in UK/Europe.
- `apomorphine` — Potent D1/D2/D3 agonist; SC pen for acute OFF rescue or continuous pump; domperidone pretreatment mandatory; not an opioid.
- `cabergoline` — Ergot D2/D3 agonist; preferred for prolactinoma; 5-HT2B agonism → cardiac valvulopathy risk at PD doses (echocardiogram required).
- `biperiden` — Anticholinergic (M1); common in Europe/global settings for antipsychotic-induced EPS; IM/IV for acute dystonia.
- `riluzole` — ALS/MND disease-modifying; antiglutamatergic (Na-channel + NMDA + glutamate release inhibition); off-label for OCD and TRD.

**Total drug count: 222**

### Receptor axes — unchanged (38 total)
SERT, NET, DAT, 5HT1A, 5HT1B, 5HT2A, 5HT2B, 5HT2C, 5HT3, 5HT4, 5HT6, 5HT7, A1, A2, B1, B2, D1, D2, D3, D4, H1, H2, M1, M2, M3, M4, nACh, GABA, NMDA, Sig1, OX, Mu, KOR, DOR, CB1, NK1, MT, VMAT2

### DRUG_EXPERIENCE updated
All 9 new drugs now have experience entries (low/medium/high dose tiers). Total coverage: 222/222.

### UI changes

**Effects tab — receptor colour coding removed**
Receptor label text `<span class="mech-receptor">` previously had `style="color:${r.color}"`. Removed inline style. Plain text now.

**Receptor Mechanism Summary — colour coding removed**
- Receptor label span: `color:${rec?.color}` removed → plain text
- Dot indicator: `background:${rec?.color}` → `background:var(--text3)` (neutral grey)

**Radar chart — clinical threshold ring**
Custom Chart.js plugin `radarThresholdPlugin` registered globally via `Chart.register()`.
- Draws a dashed amber ring (`rgba(180,160,80,0.45)`) at score=4 on all radar charts
- Labelled "clinical threshold" in small text at top of ring
- Rationale: score ≥4 corresponds to meaningful receptor occupancy at typical clinical doses; consistent with the threshold used in the Experience/Effects tab filter


---

## Session — 2026-06-11

### Patient Reports tab — new feature

Added a new **Patient Reports** tab (`patientreports`) as a seventh right-pane view, distinct from the authoritative `experience` tab. Core design rationale: patient self-report data is epistemologically different from curated clinical/pharmacological data and should not be presented in the same layer.

**Data structure:**
- New `PATIENT_REPORTS` object; schema per effect: `[domain, text, valence, onset, dose_tier, post_count, quote]`
- Data is synthetic proof-of-concept generated from knowledge of typical patient report corpora (Reddit, drugs.com, PatientsLikeMe) — not a live scrape
- Post counts are indicative of relative reporting frequency, not clinical incidence rates

**UI features:**
- Persistent source notice (non-peer-reviewed, lay descriptions, distinct from authoritative tab)
- Data volume indicator per drug: colour-coded tier badge + raw post count + effect count
  - High ≥50 posts (green), Moderate 20–49 (blue), Low 5–19 (amber), Minimal <5 (red)
- Explicit no-data state for uncovered drugs — names the drug, explains possible reasons, notes coverage will expand
- Effects grouped by domain (mood, cognition, body, sleep, etc.), sorted by post count descending
- Patient quotes shown inline in italic beneath each effect
- Valence colour-coded: benefit (green), side effect (red), variable (amber)

**Bug fix:**
- Destructuring offset error in render loop: `([,,effect_text...])` was skipping two indices instead of one, landing all fields off by one (showing `"undefined"` for effect text). Fixed to `([, effect_text...])`.

**Coverage — 84 drugs across three tiers:**

*Tier 1 (17 drugs):* fluoxetine, citalopram, escitalopram, paroxetine, duloxetine, olanzapine, risperidone, aripiprazole, clozapine, lamotrigine, valproate, bupropion, lorazepam, clonazepam, alprazolam, amphetamine, atomoxetine — plus original 10 (sertraline, venlafaxine, amitriptyline, phenelzine, mirtazapine, haloperidol, quetiapine, lithium, methylphenidate, diazepam)

*Tier 2 (22 drugs):* trazodone, buspirone, clomipramine, imipramine, nortriptyline, doxepin, fluvoxamine, pregabalin, gabapentin, topiramate, naltrexone, buprenorphine, methadone, zolpidem, zopiclone, propranolol, psilocybin, mdma, ketamine, lisdexamfetamine, modafinil, melatonin

*Tier 3 (34 drugs):* lurasidone, cariprazine, brexpiprazole, ziprasidone, amisulpride, vortioxetine, agomelatine, moclobemide, carbamazepine, levetiracetam, cannabidiol, thc, pramipexole, ropinirole, levodopa_carbidopa, amantadine, suvorexant, lemborexant, esketamine, varenicline, acamprosate, disulfiram, donepezil, memantine, lsd, hydroxyzine, promethazine, diphenhydramine, tramadol, guanfacine, clonidine, naloxone, prazosin, sodium_oxybate

Remaining ~138 drugs intentionally uncovered — absent data shown as explicit no-data notice.

### Supporting file
`reddit_experience_review.html` — standalone HTML review interface generated as proof-of-concept for the patient experience data pipeline. Contains same 84-drug dataset with accept/reject checkboxes, valence filter, editable text, and JSON export. Created as evaluation of pipeline structure before integration.

### Tab restructure — Receptor Affinity & Pharmacokinetics

**Receptor Affinity tab** (was two separate tabs):
- Radar and Heatmap combined under a single "Receptor Affinity" top-level tab
- Sub-buttons (Radar / Heatmap) rendered via `renderReceptorAffinitySubNav()` injected into the content area via `prepend()` — not in the header
- Sub-nav uses `.ra-subnav` / `.ra-subnav-btn` CSS pattern

**Pharmacokinetics tab** (new top-level tab absorbing two existing tabs):
- Three sub-tabs: **Metabolism** (new), **Interactions** (existing DDI checker, unchanged), **Starting / Stopping** (existing PK tab, renamed)
- Sub-nav rendered via `renderPKSubNav()` using same CSS pattern

**Metabolism sub-tab** (new):
- Per-drug cards showing metabolising enzyme substrates (colour-coded by strength: red=strong, yellow=moderate, blue=minor), inhibitor/inducer tags with directional arrows, and a clinical notes box
- `METABOLISER_STATUS` lookup table: 6 enzyme systems (CYP2D6, CYP2C19, CYP2C9, CYP3A4, CYP1A2, UGT) with per-drug PM/IM/UM fold-change data and clinical action notes
- Metaboliser status table: PM / IM / UM columns with fold-change badges and plain-English clinical notes
- Notable entries: codeine/tramadol CYP2D6 prodrug reversal (PM = no efficacy, UM = toxicity risk); citalopram/escitalopram CYP2C19 PM QTc dose caps; clozapine/olanzapine CYP1A2 smoking-induced induction; lamotrigine UGT valproate interaction
- Drugs without genotype data show an explicit DDI-dominated note
- EM (extensive metaboliser, normal reference) not shown — fold changes are vs. EM baseline

**VIEW_PARENT map** updated: radar/heatmap → receptoraffinity; metabolism/interactions/pk → pharmacokinetics

---

## Session — 2026-06-11 (continued)

### Rename: PsychoRx → PsychoTIX

Tool renamed throughout:
- Browser tab title: "PsychoTIX — Psychopharmacology Treatment, Interactions and Experience"
- Header h1: "PsychoTIX" with subtitle "Psychopharmacology Treatment, Interactions and Experience"
- Copyright line added to header: "© Dr James Rucker, King's College London, 2026"

### Tab restructure — Experience tab

Top-level tabs reduced from five to three: **Receptor Affinity** | **Pharmacokinetics** | **Experience**

**Experience tab** has two sub-tabs (rendered via `renderExperienceSubNav()`):
- **Clinical Effects** — existing effects view, unchanged
- **Patient Experience & Reports** — combined wrapper (`renderPatientExperienceView`) with a second-level internal toggle:
  - *Subjective Experience* — curated clinical experience data (existing `renderExperienceView`)
  - *Patient Reports* — patient self-report layer (existing `renderPatientReportsView`)

**Bug fix — sub-nav class collision:**
Internal toggle originally used class `ra-subnav`, same as the outer sub-nav. `renderExperienceSubNav` called `container.querySelector('.ra-subnav')` and removed + replaced it on every render, clobbering the inner toggle before Patient Reports content could display. Fixed by assigning the inner toggle the distinct class `exp-inner-subnav`.

### Heatmap redesign

Complete rebuild of `renderHeatmapView`:

**Previous design:** drug-coloured dot + score number + mechanism symbol as separate lines per cell. Cell background was neutral. Affinity communicated through opacity of the dot only.

**New design — proper heatmap:**
- **Cell colour = mechanism type** — each pharmacological action has a distinct hue:
  - Green (agonist), amber (partial agonist), deep red (inverse agonist), red (antagonist), blue (reuptake inhibitor), lime (releaser), teal (PAM), slate (indirect)
- **Colour intensity = affinity score** — linear mapping, score 1 → ~18% opacity, score 10 → 100% opacity; same hue, varying saturation gives immediate visual read of binding strength
- **Cell content** — mechanism symbol + numeric score, with auto-contrasting text (dark on light cells, white on dark)
- **Receptor grouping** — rows grouped by family (Transporters, Serotonin, Dopamine, etc.) with labelled divider rows
- **Drug column headers** — coloured underline in drug's assigned colour + dose tier label
- **Legend** — shows only mechanisms present in current selection + affinity intensity scale strip (1–10 gradient)
- Tooltip on hover: drug name, receptor, mechanism label, score

### Empty title fix

Removed "Receptor Profiles" placeholder text from the content title `<h2>` — now starts blank before any drug is added.
