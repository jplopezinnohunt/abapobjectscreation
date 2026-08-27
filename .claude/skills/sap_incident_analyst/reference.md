# sap_incident_analyst — referencia detallada

> Extraído de `SKILL.md` para que su cuerpo no ocupe contexto en cada turno.
> Lo carga quien lo necesite; el índice está en `SKILL.md`.

## Canonical Document Structure — TRACK A (diagnosis)

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

**Both tracks — non-negotiable:**
- [ ] A **first-class record exists in `brain_v2/incidents/incidents.json`**, not just a doc on
      disk. A doc without a record is invisible to Step 2 BRAIN LOOKUP — the next agent will
      re-derive from zero. Verify with
      `python Zagentexecution/quality_checks/incident_record_coverage_check.py` (exit 0 = clean).
- [ ] `analysis_doc` in the record points at the real path

**Track B additionally:**
- [ ] The authority document is cited by reference number and effective date
- [ ] Every operation in the B5 spec has a matching B7 live readback line
- [ ] The drift sweep ran against the full population, not just the changed row
- [ ] Open items are listed with owners, and the status reflects them (not `CLOSED`)
- [ ] If this is occurrence ≥2 of the scenario: a procedure doc + a recurring check exist

**Track A:**
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
