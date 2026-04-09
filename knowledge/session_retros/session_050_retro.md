# Session #050 Retrospective
**Date:** 2026-04-09 | **Duration:** ~3 hours | **Type:** Brain v3 validation + incident methodology bootstrap
**Focus:** H35 — validate Brain v3 in real session work + design incident-processing way of working

## What Happened

Session opened as a continuation of the support-incident workstream from Sessions #047–#049 (INC-000006073, Travel BusA). User asked for three things up front:
1. Promote the vendor-master KTOKK↔AKONT inconsistency to a recurring check (not a one-off finding from INC-000006073).
2. Formalize the way we processed INC-000006073 as a reusable methodology — skill + subagent.
3. Mid-session add: evaluate the new brain v3 model and propose improvements.

The session pivoted twice during execution, both times because of user pushback that exposed how I was failing to use the brain I had loaded.

**Pivot 1** — I started building a vendor-integrity check from scratch instead of reading the existing INC-000006073 analysis doc. The user said: "this is because you do not read the final report... all the analysis was done." Reading the report showed the conclusion was already there: 62 IIEP cross-funded travelers checked, 1 broken (Katja), the rest covered by GGB1 rule `3IIEP###002`. I had been re-deriving what was already known.

**Pivot 2** — I asked: why did the brain not surface the report? User replied: "If we have a brain with all the context, why are you not using it?" Then deeper: "the real question is what do you NOT have classified that's not in the context?" This forced me to instrument the brain itself rather than just patch the symptoms.

## Deliverables (12)

| # | Deliverable | Type |
|---|------------|------|
| 1 | [brain_v2/incidents/incidents.json](../../brain_v2/incidents/incidents.json) — first-class incident records (Layer 11), seeded with INC-000006073 | Brain |
| 2 | [brain_v2/build_brain_state.py](../../brain_v2/build_brain_state.py) — added Layer 11 (incidents), Layer 12 (blind_spots), `_coverage` metric, force-include of referenced names | Tool |
| 3 | Enriched `indexes.by_incident` from list-of-objects to dict with status, doc, root_cause_summary, fix_immediate, related_objects | Brain |
| 4 | [Zagentexecution/quality_checks/vendor_master_integrity_check.py](../../Zagentexecution/quality_checks/vendor_master_integrity_check.py) — recurring DQ check with CLI args + GGB1 cross-check | Tool |
| 5 | [.agents/skills/sap_incident_analyst/SKILL.md](../../.agents/skills/sap_incident_analyst/SKILL.md) — 7-step incident processing protocol with anti-patterns + checklist | Skill |
| 6 | [.claude/agents/incident-analyst.md](../../.claude/agents/incident-analyst.md) — Opus-powered subagent owning the full workflow autonomously | Subagent |
| 7 | [knowledge/incidents/INC-000006073_travel_busarea.md](../incidents/INC-000006073_travel_busarea.md) — moved from `domains/FI/`, canonical location | Reorg |
| 8 | [knowledge/domains/FI/ggb1_substitution_tables_distinction.md](../domains/FI/ggb1_substitution_tables_distinction.md) — clears the YTFI_BA_SUBST vs GB901/GB922 confusion that bit me mid-session | Knowledge |
| 9 | Updated [knowledge/domains/BusinessPartner/README.md](../domains/BusinessPartner/README.md) — KTOKK is not enforced + integrity check pointer | Knowledge |
| 10 | [.agents/workflows/session_close_protocol.md](../../.agents/workflows/session_close_protocol.md) — added **Phase 4b: Capture SAP Learnings** as a mandatory pre-commit gate | Governance |
| 11 | [CLAUDE.md](../../CLAUDE.md) — updated brain section with 12 layers, mandatory traversal order, Phase 4b reference, incident workflow | Governance |
| 12 | 7 new feedback rules: `feedback_brain_first_then_grep`, `feedback_blind_spots_are_first_class`, `feedback_force_include_referenced_names`, `feedback_incident_class_systemic_check`, `feedback_incident_processing_workflow`, `feedback_incident_doc_canonical_structure`, `feedback_extract_before_speculate` | Rules |

## Hypotheses Tested

| # | Hypothesis | Result |
|---|-----------|--------|
| H50.1 | The brain has the analysis doc linked but the agent will not use it without an explicit "brain-first" rule | **CONFIRMED.** I globbed for `INC-000006073*` and re-derived analysis even though `objects.ZCL_IM_TRIP_POST_FI_CM00A.knowledge_docs[0]` and `objects.PA0001.knowledge_docs[3]` both pointed at the analysis doc. The brain works only if the protocol forces traversal. **FALS-003 falsified.** |
| H50.2 | A meaningful share of objects the brain talks about are not classified as first-class entities | **CONFIRMED.** 20 of 82 referenced names (24%) were missing from `objects[]` — including PA0027 (the literal root-cause infotype of INC-000006073), GB901/GB922 (the GGB1 config tables already in Gold DB), and BAPI_ACC_EMPLOYEE_PAY_POST. Brain coverage was 75.6% before the force-include fix (which raised object count from 102 → 136). |
| H50.3 | The 7-step incident workflow can be captured as a skill+subagent reproducible by a fresh agent | **TBD.** Will be tested by **FALS-005** when the user passes the next incident in Session #051. |

## What Went Right

1. **User pushback shaped a dramatically better outcome.** Both pivots improved the session. The first pivot stopped me from rebuilding analysis. The second pivot turned a tactical "fix the link" into a structural "instrument the brain for blind spots".
2. **The blind-spot detector immediately surfaced 20 entries** including the most damning ones (PA0027, GB901, GB922). Without it, the brain would keep claiming "full intelligence" while missing root-cause objects.
3. **Phase 4b in the close protocol turns SAP-knowledge capture into a gate**, not a habit. This addresses the underlying failure mode that the in-conversation SAP discoveries (GGB1 vs YTFI_BA_SUBST) only get persisted when the agent remembers — which is unreliable.
4. **The integrity check works on the seed case.** Threshold 5%, rank-based, GGB1 cross-check via YTFI_BA_SUBST → flags Katja exactly (4.4% share, GGB1=NO).

## What Went Wrong

1. **Re-derived conclusions already in the brain.** Spent ~30 minutes rebuilding the SCSA→AKONT analysis with SQL when the answer was already in `T077K.annotations` and the analysis doc. Root cause: I followed the session-start ceremony but didn't traverse the inline annotations after loading.
2. **Confused YTFI_BA_SUBST with GB901/GB922.** I cross-checked vendors against the wrong substitution table for ~20 minutes before realizing the conclusion in the report contradicted my own check. This was a SAP knowledge gap that's now captured in [ggb1_substitution_tables_distinction.md](../domains/FI/ggb1_substitution_tables_distinction.md).
3. **Initial integrity check threshold was too tight (2%).** Katja's share is 4.4%, so the threshold missed her on the first run. Fixed to 5% + rank-based outlier rule.
4. **Brain coverage metric did not exist before this session.** Without it, "brain v3 is comprehensive" was an assertion, not a measurement. 75.6% is a much more honest baseline.

## Brain v3 Model Evaluation (mid-session pivot)

| Aspect | Before #050 | After #050 | Notes |
|---|---|---|---|
| Object count | 102 | 136 | Force-include caught 34 previously-filtered objects |
| Layers | 10 | 12 | +incidents (Layer 11), +blind_spots (Layer 12) |
| Coverage metric | none | `_coverage.pct_classified = 75.6%` | New visibility — we know what we don't know |
| `by_incident` | list of object names | dict with status/doc/summary/fix/related | Now actionable from the index alone |
| Incident-as-first-class | implicit only | explicit Layer 11 with full record | Agent can read incidents[id] and act |
| Blind-spot detector | none | walks annotations/claims/incidents and lists referenced-but-missing names | Surfaces what needs extraction |
| Brain-first rule | not enforced | `feedback_brain_first_then_grep` (CRITICAL) | Closes the failure mode that sparked this session |

The architecture itself was sound; the failure was procedural. The agent was given a beautiful brain and a vague "read it" instruction, with no forcing function for traversal. Phase 4b + the brain-first rule + the blind-spot detector together close that gap.

## SAP Learnings This Session (Phase 4b)

| Learning | Promoted to |
|---|---|
| **YTFI_BA_SUBST is NOT the GGB1 condition table** — it is the persistence layer for the user-friendly maintenance transaction `YFI_BASU_MOD`, read by exit `YCL_FI_ACCOUNT_SUBST_READ` from form `U910` in `YRGGBS00`. The actual GGB1 rules live in **GB901** (conditions) + **GB922** (substitution values) + **GB02C** (header registry). Cross-checking AKONT against YTFI_BA_SUBST does NOT tell you whether standard GGB1 would catch it. | [knowledge/domains/FI/ggb1_substitution_tables_distinction.md](../domains/FI/ggb1_substitution_tables_distinction.md) (new) |
| **T077K does NOT store the AKONT mapping for vendor account groups** — it carries field-status strings (FAUS*) but not the AKONT field. The KTOKK→AKONT relationship is a *data observation* (modal AKONT for each KTOKK group across LFB1) and is not SAP-enforced. KTOKK and AKONT can drift independently. | [knowledge/domains/BusinessPartner/README.md](../domains/BusinessPartner/README.md) — added "KTOKK is NOT enforced against AKONT" section |
| **GB901, GB922, GB02C are extracted in Gold DB but NOT modeled as brain objects** — they are blind spots even though their data has been queried multiple times. The brain talks about "GGB1 rule 3IIEP###002" without having the rule rows accessible from the graph. | KU-022 (triage blind spots), `feedback_force_include_referenced_names` |
| **PA0027 subtype 02 expirations are silent failure points for the BAdI BusA fallback chain** — `ZCL_IM_TRIP_POST_FI_CM00A.abap:37` does `CHECK sy-subrc IS INITIAL` which exits without warning when no current PA0027-02 record is found. The systemic question (how many other employees have expired PA0027-02 records?) is not yet quantified. | INC-000006073 doc — followup #3 |
| **The full GGB1 chain at UNESCO has multiple steps** (Step 001 = Y-exit, Step 002 = standard rule, Step 003 = unconditional). The unconditional Step 003 may execute *after* the BAPI mandatory field check rejects empty GSBER, depending on internal sequencing. This is unverified but matters for any GSBER-related incident. | [ggb1_substitution_tables_distinction.md](../domains/FI/ggb1_substitution_tables_distinction.md) — section "GGB1 chain at UNESCO" |
| **`vendor_master_integrity_check.py` is the first recurring DQ check promoted from an incident.** Pattern: distil incident root cause to a SQL signature, run against full Gold DB, count violations, escalate to `Zagentexecution/quality_checks/<class>_check.py` with CLI args. This is the new template for class generalization. | `feedback_incident_class_systemic_check` (CRITICAL rule) |

## AGI Self-Assessment Score

| AGI Requirement | Before | After | Notes |
|---|---|---|---|
| Knows what it knows | 9/10 | 9/10 | 136 objects (was 102), 26 claims |
| Knows what it doesn't know | 9/10 | 10/10 | +blind_spots layer (20 entries), +KU-022, +KU-023 |
| Knows what it was wrong about | 9/10 | 9/10 | 15 superseded (no new this session) |
| Testable predictions | 8/10 | 9/10 | 6 pending falsification (was 4) |
| Self-correction | 9/10 | 9/10 | 58 rules (was 50) |
| Cross-domain reasoning | 9/10 | 9/10 | Object-centric inline maintained |
| Persists across sessions | 10/10 | 10/10 | git-tracked, single rebuild |
| Inter-agent collaboration | 8/10 | 9/10 | +incident-analyst subagent owns the workflow |
| Source data bug detection | 9/10 | 9/10 | DQ-001 promoted to RECURRING |
| Open question tracking | 10/10 | 10/10 | All open KUs in brain_state |
| **Failure-mode visibility** (NEW) | 0/10 | 9/10 | Coverage metric + blind-spot detector make the gap visible |

**Total: 90/100 → 101/110 (added one criterion)**

## PMO Updates

| # | Type | Action |
|---|---|---|
| ~~H35~~ | HIGH (CLOSED) | Validate Brain v3 in real session work — DONE. Brain v3 used for the entire session, including a self-evaluation that produced 12 deliverables and 7 new feedback rules. FALS-001 to FALS-004 still pending (need session #51 data). |
| **H36 (NEW)** | HIGH | Triage 20 brain blind spots from `brain_state.blind_spots` — split into "extract me" (PA0027, ZCL_IM_TRIP_POST_FI_CM006, ZCL_IDFI_CGI_DMEE_FR), "model from existing data" (GB901/GB922 — already in Gold DB, just need brain modeling), and "pseudo-references to drop" (LHRTSF01:852, inst_fund_ba_wbs_cc, GB901:2IIEP###001) |
| **H37 (NEW)** | HIGH | Process the next incident the user passes using the new sap_incident_analyst skill + incident-analyst subagent. Resolves FALS-005. Validates the 7-step protocol on a fresh case. |
| **G65 (NEW)** | BACKLOG | Run `vendor_master_integrity_check.py` against full master and produce a remediation report. Resolves FALS-006 + KU-020. |
| **G66 (NEW)** | BACKLOG | Build a similar recurring check for PA0027 subtype 02 expirations across the employee master. Quantifies the scope of the BAdI safety net failure that contributed to INC-000006073. |
| **G67 (NEW)** | BACKLOG | Build a TADIR-wide brain coverage metric that compares `brain_state.objects` against the total `Y*/Z*` object count in production, not just the closed-loop coverage. Resolves KU-023. |

## Closure Math

| Metric | Start | End | Delta |
|---|---|---|---|
| BLOCKING | 0 | 0 | 0 |
| HIGH | 3 (H25, H26, H35) | 4 (H25, H26, H36, H37) | -1 closed (H35), +2 added (H36, H37) = +1 net |
| BACKLOG | 29 | 32 | +3 (G65, G66, G67) |
| **Total** | **32** | **36** | **+4 net** |

**Items shipped: 1 (H35)** | **Items added: 5 (H36, H37, G65, G66, G67)** | **Net: -4 (failure per closure rule)**

**Honest justification for net-negative:** H36/H37 are direct consequences of the brain-evaluation pivot — they are the things this session *discovered we need to do* but explicitly did not do. Same for G65–G67. The session shipped a significant brain architecture upgrade + a complete incident-processing infrastructure (skill + subagent + protocol + checks), but the discovery scope outpaced the closure. Acknowledged.

The closure rule remains a useful pressure: H36 and H37 must move in Session #051.

## Validation Pending

| FALS | Test |
|---|---|
| FALS-001 | brain_state.json size ≤ 5% of context at session #54 — currently 5.3% (already at the limit) |
| FALS-002 | Time-to-first-action faster than reading CLAUDE.md + MEMORY.md — partially confirmed this session |
| FALS-003 | Did I use knowledge_docs links? **FALSIFIED** — I globbed instead. Caused this session's pivot. Fix: brain-first rule. |
| FALS-004 | Are 50 rules enough? — 8 new rules added this session. On pace for >20 in 10 sessions. **Likely to falsify.** |
| FALS-005 | Does the incident-analyst subagent reproduce INC-000006073-quality output on a fresh incident? — pending Session #051 |
| FALS-006 | Does the integrity check find ≥5 vendors beyond Katja? — pending full scan |

## What We Can Do Next (Priority Order)

### H37 — Process next incident with new infrastructure (next session, HIGH)
1. User passes incident as .eml or pasted email
2. Invoke `incident-analyst` subagent or follow `sap_incident_analyst` skill
3. Track every step against the protocol — note any deviations or improvements needed
4. Output: `knowledge/incidents/INC-<id>_<slug>.md` + brain update + skill refinement based on what was missing

### H36 — Brain blind-spot triage (next session, HIGH)
1. Read `brain_state.blind_spots`
2. For each MISSING entry decide: extract / model from existing / drop
3. PA0027 is the highest priority — it was the literal root cause of INC-000006073 and is still not in the brain

### H25/H26 — Still pending from #029 (zombie items)
T028A/T028E + T012K UKONT extraction. Low effort, requires VPN. Should be killed if not done by session #55.
