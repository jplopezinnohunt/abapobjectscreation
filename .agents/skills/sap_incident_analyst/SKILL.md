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

**The single most important rule:** read the brain BEFORE you grep. The brain
already knows. (See `feedback_brain_first_then_grep`.)

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

### Step 5 — ROOT CAUSE RECONSTRUCTION

Walk the execution chain step-by-step:
- What triggers? (TCODE, event, batch job)
- What table is read? Via which key?
- What field decides the next branch?
- Where does the chain diverge between OK and FAIL cases?

Build the **case-OK vs case-FAIL** comparison table. If you cannot point to
the exact line where OK and FAIL diverge, you do not have the root cause yet.

### Step 6 — CLASS GENERALIZATION (rule `feedback_incident_class_systemic_check`)

The root cause is for one row, one document, one vendor. The defect is for a
**class** of rows. Distil the root cause into a SQL signature:

> "Vendor with KTOKK=SCSA AND LFB1.AKONT NOT IN (modal AKONT for that KTOKK)"

Run it against Gold DB. Count violations. If >1 row matches, the incident is
not a one-off — escalate to a recurring check under
`Zagentexecution/quality_checks/<class>_check.py`.

### Step 7 — BRAIN ANNOTATION

Every incident MUST update the brain so the next session benefits. The
mandatory annotations:

| Layer | What to add |
|---|---|
| `brain_v2/incidents/incidents.json` | First-class record with status, root_cause_summary, fix_path, related_objects, analysis_doc |
| `brain_v2/annotations/annotations.json` | One annotation per object touched, tagged with `incident: INC-id` |
| `brain_v2/claims/claims.json` | Verified facts with evidence trail |
| `brain_v2/agi/known_unknowns.json` | Open questions raised by this incident |
| `brain_v2/agi/data_quality_issues.json` | Source data bugs uncovered |
| `brain_v2/agi/falsification_log.json` | Predictions for similar incidents |

Then run `python brain_v2/rebuild_all.py` to regenerate `brain_state.json`.
Validate `_coverage.pct_classified` did NOT decrease.

## Canonical Document Structure

`knowledge/incidents/INC-<id>_<slug>.md` MUST follow this 7-section structure
(proven on INC-000006073):

1. **Issue — As Received** (email text, screenshots, ticket header table)
2. **Executive Summary** (2-3 sentences + internal validation chain)
3. **Domain Primer** (how the affected mechanism works at UNESCO — only background needed for the report)
4. **Investigation** (component-by-component, each subsection cites code file:line and Gold DB query)
5. **Why It Worked Before vs Why It Fails Now** (the variable that changed)
6. **Fix Recommendation** (immediate / structural / preventive)
7. **Evidence + Class Generalization** (Gold DB query + count + escalation to recurring check)

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

## Subagent

For autonomous incident processing, delegate to the `incident-analyst`
subagent (`.claude/agents/incident-analyst.md`). It owns the full 7-step
workflow and has the brain plus extraction skills wired up.
