---
name: SAP Incident Analyst
description: |
  Way of working for processing UNESCO SAP support incidents end-to-end. Takes
  an email (.eml or pasted text) as input and produces a brain-grade root cause
  document plus brain annotations. Built from the INC-000006073 success
  pattern (Sessions #047-#049).
trigger:
  - User pastes/attaches an email with INC- number
  - User says "incident", "ticket", "PRRW failure", "F110 error", "RW609", "ZFI020", etc.
  - User says "I'm passing the next incident"
mandatory_inputs:
  - Email body (text or .eml file)
  - Any embedded screenshots (the agent must inspect images)
mandatory_outputs:
  - knowledge/incidents/INC-<id>_<slug>.md (canonical 7-section structure)
  - brain_v2/incidents/incidents.json updated with first-class record
  - brain_v2/annotations/annotations.json + claims.json + agi/* updated
  - brain_v2/rebuild_all.py executed and validated
  - PMO ticket and follow-up known_unknowns recorded
---

# SAP Incident Analyst — Skill Reference

## Why This Skill Exists

UNESCO's support team forwards incidents as emails. Each one needs root cause
analysis, fix proposal, and brain enrichment so the next similar incident is
faster. INC-000006073 was the proof-of-concept (Travel BusA, Sessions #047-49):
2 sessions of work, 34 ABAP files extracted, 5 config tables added to Gold DB,
1 new domain created (Travel). The pattern below distils that experience into
a reusable workflow.

## CRITICAL — Execution Mode (updated Session #051, INC-000005240)

**The MAIN agent executes this workflow directly. Do NOT delegate the 7-step
protocol to the `incident-analyst` subagent.**

Why: on INC-000005240, the main agent delegated the workflow to the subagent.
The subagent:
- Lost the raw .eml (received only a file path and a 400-word summary request)
- Conflated "HQ" (office code, current ticket) with "UNESCO" (fund center
  default from INC-000006073 in brain memory)
- Pursued a completely wrong mechanism (FMDERIVE / ZXFMDTU02_RPY fund center
  hardcoding) and produced a full 330-line analysis doc on the wrong defect
- Burned 154K tokens before hitting plan mode
- Proposed running `rebuild_all.py` with provisional claims, which would have
  poisoned the brain with a rejected hypothesis

**Subagents are ONLY used for narrow, mechanical sub-tasks** — e.g., "grep
YRGGBS00 for every form that writes XREF2 and return line numbers". Never
hand over parse / brain lookup / code trace / root cause.

## Core Principles

1. **Brain before grep.** The brain already knows. (See `feedback_brain_first_then_grep`.)
2. **Read the email in the main agent.** Never hand a `.eml` path to a subagent and trust its summary. The main agent parses the user's own words directly. (See `feedback_read_emails_in_main_agent`.)
3. **User language before code.** Translate the user's own-language symptom to SAP fields BEFORE searching code. Same keyword can mean different things in different incidents. (See `feedback_user_term_to_sap_field_translation`.)
4. **PSM/EXTENSIONS is the FI substitution home.** For any FI substitution/validation/BTE/exit incident, read `knowledge/domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md` + `validation_substitution_matrix.md` + `basu_mod_technical_autopsy.md` at the START of the investigation. These docs are misfiled under PSM historically but are the authoritative FI framework reference. (See `feedback_psm_extensions_is_fi_substitution_home`.)
5. **Understand before diagnose.** Write "how it should work" before "why it fails". If you can't draw the intended flow with `file.abap:line` citations, you haven't earned a root cause. (See `feedback_process_before_root_cause`.)
6. **Empirical > theoretical.** For substitution/validation behavior, run `CDPOS` + `AUGBL` + live RFC `BSAK`/`BSAS`/`BSIS` reads FIRST. Use GB901/GB922/GB93/GB931 content to EXPLAIN observed behavior, not to PREDICT it. (See `feedback_empirical_over_theoretical_substitution`.)
7. **`bseg_union` has no XREF columns.** Never claim XREF state from Gold DB `bseg_union` — its schema does not include XREF1/XREF2/XREF3. Go to live RFC BSAK/BSAS/etc. (See `feedback_bseg_union_has_no_xref`.)
8. **Distinguish REAL from METADATA BSEG lines.** BSCHL=27/37 zero-balancing clearing pairs are metadata, not real business events. Count real lines for severity, metadata lines for completeness. (See `feedback_metadata_vs_real_bseg_lines`.)
9. **Provisional until confirmed.** Every claim, annotation, and incident record written during investigation is marked `status: provisional`.
10. **No learning capture mid-investigation.** Do NOT update knowledge domain docs, feedback rules, or brain_v2 layers while the investigation is still in flight. ONLY at the finalization stage after user confirms. The incident report itself is the one exception. (See `feedback_no_learning_capture_mid_investigation`.)
11. **Rebuild only after finalization.** `rebuild_all.py` runs as the LAST step, after the user has confirmed all conclusions. Never mid-investigation. (See `feedback_brain_rebuild_after_finalized`.)
12. **Main agent holds context.** Do not delegate the 7-step workflow to a subagent. Use subagents only for narrow, deterministic sub-tasks. (See `feedback_main_agent_holds_incident_context`.)

## The 7-Step Incident Processing Protocol

### Step 1 — PARSE the email

Extract from the email body and any screenshots:

| Field | Where to find it |
|---|---|
| Ticket ID | Subject line, body header (INC-\d{9}) |
| Reporter | "From:" or signature |
| Transaction code | Body / screenshot title bar (PRRW, F110, FB02, ME21N…) |
| Document number | Posting run, FI document, PO, IDoc |
| Master data IDs | Vendor, customer, employee, GL, cost center |
| Error messages | Status bar text, error log screenshot — **capture full ID + text** |
| Date / time | Header timestamp |
| Affected entity | Company code, fund, business area mentioned |

If the email contains screenshots, **read the image** — do not paraphrase. The
key info (BUKRS, GSBER, GL account, line item) is often only in the image.

Save the parsed payload to `Zagentexecution/incidents/<INC-id>_intake.json`.

#### MANDATORY: User term → SAP field translation table

Before anything else, write a table mapping the user's own words to SAP
fields. Put it in Section 1 of the analysis doc. This prevents the
cross-incident keyword confusion that broke INC-000005240:

| User says | SAP field / object (to verify) | Confidence |
|---|---|---|
| "reference key" | BSEG-XREF1 / BSEG-XREF2 / BKPF-XBLNR? | MEDIUM — confirm from screenshot or follow-up |
| "HQ" / "JAK" | **office code** for UNESCO field offices (distinct from fund center "UNESCO" in FMDERIVE — do NOT conflate with INC-000006073) | HIGH |
| "fund" / "budget" | FM fund center (FICTR) OR fund (FUND) OR WBS element (PS_POSID)? | LOW until clarified |

Every row should say **what the field is**, **where it's maintained**, and
**what mechanism populates it**. If a keyword has more than one plausible
mapping, list all of them until the code trace eliminates the wrong ones.

**Never assume a keyword in this incident means the same thing as in a past
incident.** Even if two tickets share the string "HQ", the mechanism may be
completely different. Translate every time.

### Step 2 — BRAIN LOOKUP (read FIRST, grep LAST)

Open `brain_v2/brain_state.json` and traverse in this exact order:

1. **`incidents`** (Layer 11) — does an incident with this ID already exist? If yes, READ `incidents[id].analysis_doc` immediately and continue from where the previous session left off. **Do not re-derive.**

2. **`indexes.by_incident[id]`** — gives status, root_cause_summary, related_objects, doc path. Even if the incident is new, check by transaction code: a sibling incident on the same TCODE may share root cause.

3. **`indexes.by_domain[domain]`** — list of objects in the affected domain.

4. For each object you suspect is involved (transaction → known programs, error message → known caller), open `objects[X]` and read:
   - `annotations` — past findings on this object
   - `claims` — verified facts
   - `incidents` — other incidents this object participated in
   - `knowledge_docs` — analysis docs that already discuss it
   - `read_by` / `reads_tables` / `calls_fms` — relationship graph

5. **`blind_spots`** — if any of the suspected objects appears here, the brain knows about it but does not have it as a first-class entity. **Treat extraction as a prerequisite to continuing the investigation** (rule `feedback_extract_before_speculate`).

6. **`data_quality`** — does any DQ entry match this incident's table or field? A known DQ issue often IS the root cause (DQ-001 → INC-000006073).

7. **`known_unknowns`** — does any KU match? An open KU means we predicted this gap.

8. **`rules`** (`feedback_*`) — read any rule whose `id` mentions the affected domain, table, or technique.

Only after all of the above produce nothing useful do you grep `knowledge/`.

### Step 3 — GOLD DB PULL

For every entity mentioned in the email (vendor, document, master record), pull
the live row from Gold DB. **Always `PRAGMA table_info` first** — column names
vary across SAP releases.

**Substitution/validation incidents — mandatory table extractions at start:**

For any incident touching substitution / validation / BTE / custom exit, the following tables MUST be available (Gold DB first, RFC if missing). This list was compiled from INC-000005240 (Session #051) and `feedback_extract_ggb_tables_for_substitution_incidents`:

| Table | Purpose | Status as of Session #051 |
|---|---|---|
| `GB01` | Boolean class field definitions (per-class table/field whitelist) | RFC-accessible |
| `GB02` / `GB02C` | Boolean class header (MSGID, MULTILINE) | Gold DB has GB02C (10 rows) |
| `GB93` | **Validation rule header** — `VALID` / `BOOLCLASS` / `MSGID` | RFC-accessible, 17 rows at UNESCO |
| `GB931` | **Validation steps** — VALID + VALSEQNR + CONDID + CHECKID + VALSEVERE + VALMSG | RFC-accessible, 12 rows for `VALID='UNES'` |
| `GB905` / `GB921` | Substitution step header (links SUBSTID+step to prerequisite BOOLID) | **Empty at UNESCO** — substitution prerequisite linkage is implicit via naming convention |
| `GB922` | **Substitution step bodies** — SUBSTID + SUBSEQNR + SUBSFIELD + EXITSUBST | Gold DB has (218 rows; 17 for `SUBSTID='UNESCO'`) |
| `GB901` | **Boolean expressions** (BOOLEXP bodies keyed by BOOLID) | Gold DB has (583 rows) |
| `GB903` | Boolean expression SHORTNAME / SETID registry | Gold DB has (3 rows — sparse at UNESCO) |
| `T80D` | **Form pool registration** — ARBGB + FORMPOOL (e.g., `GBLS`/`GBLR` → `YRGGBS00`) | Gold DB has (8 rows) |

**BOOLID naming convention at UNESCO (decoded Session #051):** `<prefix><name><separator><seq>`:
- Prefix `1` = Validation **CONDID** (prerequisite). Example: `1UNES###009`
- Prefix `2` = Validation **CHECKID** (assertion). Example: `2UNES###009`
- Prefix `3` = Substitution step prerequisite. Example: `3UNESCO#005`
- 4-char names pad with `###`; 6-char names pad with `#`

**Gold DB schema gotchas:**
- **`bseg_union` has NO XREF1 / XREF2 / XREF3 columns.** Never claim XREF state from it. Go to live RFC BSAK/BSAS/BSIS for XREF values.
- `bkpf.TCODE` stores the *commit-time* TCODE, not the dialog entry code. `F-53` dialog postings are stored as `TCODE='FBZ2'` (per SE93 parameter transaction `TSTC`). Always check SE93 before filtering by TCODE.

```bash
python -c "
import sqlite3
c = sqlite3.connect('Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db').cursor()
c.execute('PRAGMA table_info(LFB1)')
print([r[1] for r in c.fetchall()])
c.execute(\"SELECT * FROM LFB1 WHERE LIFNR=?\", (vendor.zfill(10),))
for r in c.fetchall(): print(r)
"
```

If a table or column is **missing from Gold DB**, run `sap_data_extraction`
skill to extract it. Do not speculate. (Rule `feedback_extract_before_speculate`.)

### Step 4 — CODE TRACE

For each program/class in the suspected execution chain (from brain
`reads_tables` / `calls_fms` edges), check `extracted_code/`:

```
extracted_code/SAP_STANDARD/<DOMAIN>/      # SAP standard ABAP
extracted_code/UNESCO_CUSTOM_LOGIC/<DOMAIN>/  # UNESCO Y/Z code
```

If a needed file is missing, extract it via `sap_adt_api` skill (D01) or
`RPY_PROGRAM_READ` (P01). Add it to `brain_v2/output/brain_v2_graph.json` via
`code_ingestor.py` so the next incident benefits.

**Cite line numbers** in the analysis doc — every claim about behavior must
point to `file.abap:line`.

### Step 4.5 — PROCESS UNDERSTANDING (insert BEFORE root cause)

Before hypothesizing why it fails, write "how it should work" as a numbered
flow. This is the narrative that answers: *if I were debugging this on paper,
what sequence of events happens when a correctly-configured posting fires?*

Format:
```
1. User opens TCODE → SAP builds draft BKPF/BSEG in memory
2. Substitution callpoint 0002 fires → walks the step chain for BUKRS=X
3. Form F1 reads <TABLE> where <KEY> → sets <FIELD>
4. Form F2 validates <FIELD> against <LOOKUP TABLE>
5. Document commits → downstream effects (ZLSCH, workflow, BTE, etc.)
```

Every step cites `file.abap:line`. If you cannot draw this flow with
citations, you don't yet understand the process well enough to find the
root cause. Go back to Step 4 CODE TRACE.

**Rule (feedback_process_before_root_cause, SESSION #051):** never write
"Why it fails" before "How it should work". The INC-000005240 subagent
produced a full root-cause analysis on a mechanism that didn't even touch
the fields in the symptom because it skipped this step.

### Step 5 — ROOT CAUSE RECONSTRUCTION

Walk the execution chain step-by-step:
- What triggers? (TCODE, event, batch job)
- What table is read? Via which key?
- What field decides the next branch?
- Where does the chain diverge between OK and FAIL cases?

Build the **case-OK vs case-FAIL** comparison table. If you cannot point to
the exact line where OK and FAIL diverge, you do not have the root cause yet.

**Every claim, annotation, and incident record produced during this step is
marked `status: provisional`.** It becomes `confirmed` only after the user
reviews and approves the root cause in Step 8.

### Step 6 — CLASS GENERALIZATION (rule `feedback_incident_class_systemic_check`)

The root cause is for one row, one document, one vendor. The defect is for a
**class** of rows. Distil the root cause into a SQL signature:

> "Vendor with KTOKK=SCSA AND LFB1.AKONT NOT IN (modal AKONT for that KTOKK)"

Run it against Gold DB. Count violations. If >1 row matches, the incident is
not a one-off — escalate to a recurring check under
`Zagentexecution/quality_checks/<class>_check.py`.

### Step 7 — BRAIN ANNOTATION (provisional)

Every incident MUST update the brain so the next session benefits. The
mandatory annotations, **all marked `status: provisional`**:

| Layer | What to add | Status field |
|---|---|---|
| `brain_v2/incidents/incidents.json` | First-class record with status, root_cause_summary, fix_path, related_objects, analysis_doc | `status: "provisional"` |
| `brain_v2/annotations/annotations.json` | One annotation per object touched, tagged with `incident: INC-id` | include `provisional: true` in the annotation body |
| `brain_v2/claims/claims.json` | Claims with evidence trail, tier starts at `TIER_3_provisional` | promote to `TIER_1` only after user confirmation |
| `brain_v2/agi/known_unknowns.json` | Open questions raised by this incident | `status: "open"` |
| `brain_v2/agi/data_quality_issues.json` | Source data bugs uncovered | `investigation_confidence: "low"\|"medium"\|"high"` |
| `brain_v2/agi/falsification_log.json` | Predictions for similar incidents | `status: "pending"` |

**DO NOT run `rebuild_all.py` at this step.** Rebuild happens only at Step 10
after the user has confirmed the root cause. (Rule `feedback_brain_rebuild_after_finalized`.)

### Step 8 — USER CONFIRMATION GATE

Present findings to the user. The presentation must include:

1. The one-line symptom (user's words + your SAP-field translation)
2. The "how it should work" flow with citations
3. The "case OK vs case FAIL" diverge table
4. The proposed root cause (single paragraph, cited)
5. The class-generalization count (how many other rows share the defect)
6. The fix options (tactical / strategic / question for business)

Wait for the user to explicitly confirm. If the user corrects direction,
go back to the step they indicate — never skip forward on the assumption
that the correction is minor.

### Step 9 — FINALIZE + REBUILD

Only after user confirmation:
1. Flip every `provisional: true` to `provisional: false` / `confirmed: true`
2. Promote claims from `TIER_3_provisional` to `TIER_1`
3. Move `known_unknowns` that were resolved to `resolved: true` with the
   incident ID as resolver
4. Run `python brain_v2/rebuild_all.py` — and only now
5. Validate `_coverage.pct_classified` did NOT decrease
6. Validate `blind_spots` did NOT grow

### Step 10 — WRONG-PATH TRIAGE (if the investigation went sideways)

If mid-investigation you discovered you were chasing the wrong mechanism
(like the FMDERIVE subagent on INC-000005240):

1. Mark every artifact from the wrong path `status: wrong_mechanism`
2. If the wrong-path work revealed a *separate* real defect, file it as an
   **observation** (not an incident) at `knowledge/observations/<slug>.md`
3. Revert or reject the wrong `incidents.json` record with a short reason
4. Write a feedback rule capturing the pattern that caused the confusion
   (same keyword different mechanism, same field different exit, etc.)
5. Never leave a rejected hypothesis in the brain as a fact

## Canonical Document Structure

`knowledge/incidents/INC-<id>_<slug>.md` MUST follow the **13-section
structure** proven on INC-000006073 (updated from the legacy 7-section
outline after Session #051):

1. **Issue — As Received**
   - 1.1 Email (verbatim)
   - 1.2 The Question (what the user really wants to know)
   - 1.3 Context (prior custom development / session history of affected objects)
   - 1.4 Ticket Summary (field/value table)
   - **1.5 User term → SAP field translation table (MANDATORY, see Step 1)**
2. **Executive Summary** (symptom / root cause / one-line fix / why-it-worked-before, 2-3 sentences + internal validation chain)
3. **How [the affected mechanism] Works at UNESCO** — the domain primer. Written BEFORE Section 4.
   - 3.0 What the mechanism is and why it matters
   - 3.1 Components and tables
   - 3.2 The intended flow (numbered, with file:line citations)
   - 3.3 Custom framework components
4. **Investigation: Why [the failure]** — component-by-component, each subsection cites code file:line and Gold DB query
5. **System Execution Chain (Technical Detail) — From Source Code**
   - 5.1 The N-step chain
   - 5.2 Step-by-step Case OK vs Case FAIL
   - 5.3 The Code (exact lines)
6. **Why It Worked Before vs Why It Fails Now** (the variable that changed) — OR — *Why It Has Always Been Wrong*
7. **Broken Safety Nets** (what should have caught this)
8. **Evidence** (Gold DB query results, master data rows, config table rows — each subsection has a query + count + rows)
9. **Root Cause — Final** (single paragraph, backed by Sections 5-8, no hedging)
10. **Fix Recommendation**
    - Tactical (immediate)
    - Strategic (structural)
    - Question for the business (if there's ambiguity about intent)
11. **Class Map** (e.g., "Office Code → XREF Map") — every related entity the code touches, documented
12. **Extracted Code Assets (this session)** — every source file pulled, with one-line description
13. **Data Sources** — Gold DB tables queried, row counts, extraction dates

Reference: [knowledge/incidents/INC-000006073_travel_busarea.md](../../knowledge/incidents/INC-000006073_travel_busarea.md) is the gold-standard worked example.

## Anti-Patterns

| Don't | Do |
|---|---|
| Grep `knowledge/` for the incident first | Read `brain_state.incidents` first |
| Re-derive root cause from raw data | Read existing annotations/claims for involved objects |
| Speculate about missing tables/code | Extract them, then resume |
| Fix only the one row | Distil to SQL signature + run against full Gold DB |
| Save the analysis doc and stop | Update brain layers + rebuild + validate coverage |
| Pick threshold heuristics without checking the report | Follow the report's already-stated scope (e.g., 62/61/1 for INC-000006073) |

## Validation Checklist (run before closing the incident)

- [ ] `knowledge/incidents/INC-<id>_<slug>.md` follows 7-section structure
- [ ] Every behavioral claim cites a file:line
- [ ] Class generalization SQL runs against Gold DB and the count is in the doc
- [ ] `brain_v2/incidents/incidents.json` has a first-class record
- [ ] `brain_v2/rebuild_all.py` succeeds and `pct_classified` did NOT drop
- [ ] At least one new known_unknown OR one resolved known_unknown
- [ ] If a recurring check was created, it lives under `Zagentexecution/quality_checks/`
- [ ] If a new domain was discovered, `knowledge/domains/<NEW>/README.md` exists
- [ ] Stale references to old document paths are fixed (`grep` for old slug)

## Example: INC-000006073 (the seed)

This skill exists because INC-000006073 worked. Read it as the worked example:
- **Email**: 3 screenshots, RW609 + ZFI020, vendor 10133079
- **Brain lookup**: 0% coverage initially (Travel domain didn't exist) — drove the extraction
- **Gold DB pull**: PA0001, PA0027, PTRV_SCOS, LFB1
- **Code extracted**: 34 SAP standard files, 6 UNESCO custom files (24K+ lines)
- **Root cause**: 2 factors + 3 broken safety nets, all proved from source
- **Class generalization**: 62 IIEP travelers checked, 1 broken
- **Brain enrichment**: Travel domain born, 27 new objects, 16 DQ issues, GB901/GB922 added to Gold DB

Doc: [knowledge/incidents/INC-000006073_travel_busarea.md](../../knowledge/incidents/INC-000006073_travel_busarea.md)

## Related Skills

- `sap_data_extraction` — pull missing tables to Gold DB
- `sap_adt_api` — pull missing code from D01
- `sap_master_data_sync` — fix master data drift
- `sap_house_bank_configuration` — for treasury/payment incidents
- `sap_payment_bcm_agent` — for payment workflow incidents
- `sap_class_deployment` — for ABAP fixes that need to be coded

## Subagent Usage — CORRECTED (Session #051)

**Previous guidance was wrong.** Do NOT delegate the full 7-step workflow to
the `incident-analyst` subagent. The main agent is the executor.

The subagent definition at `.claude/agents/incident-analyst.md` is retained
as a **prompt template / process reference** that the main agent can read
for itself. It is not to be invoked via the Agent tool for the whole
workflow.

Acceptable subagent uses:
- Narrow mechanical searches ("grep all forms in YRGGBS00 that write XREF2")
- Parallel independent lookups ("pull all USR05 rows for these 50 users")
- Any task where the output is a deterministic list, not a judgment call

Unacceptable subagent uses:
- Parsing the email (main agent must read the .eml)
- Brain lookup (main agent must do the brain reasoning in its own context)
- Code trace (main agent must cite the lines it reads)
- Root cause reconstruction (context must stay with the main agent)
- Writing the analysis doc
- Updating brain layers

## AGI Layer Interaction Rules (added Session #051)

The AGI layers (`known_unknowns`, `falsification_log`, `data_quality_issues`,
`superseded`, `user_questions`) must interact with incidents as follows:

| Layer | During investigation | After user confirms |
|---|---|---|
| `known_unknowns` | Add new entries with `status: "open"`, `source_incident: INC-id` | Flip resolved ones to `status: "resolved"`, `resolver: INC-id` |
| `falsification_log` | Add predictions with `status: "pending"`, `prediction_date` | Mark correct predictions `confirmed`, wrong ones `falsified` |
| `data_quality_issues` | Add with `investigation_confidence: "low"` if not yet verified | Promote to `"high"` only after user confirms |
| `superseded` | If this incident replaces an older understanding, add the old claim/annotation here with `superseded_by: INC-id` | — |
| `user_questions` | If the investigation cannot proceed without a business answer, add to `open` | Close with the user's answer as evidence |

An incident cannot be `closed` if it left any `user_questions` unanswered.
An incident cannot be `finalized` if any of its claims are still
`provisional`.
