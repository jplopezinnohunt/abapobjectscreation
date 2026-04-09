# Session #050 Plan
**Date:** 2026-04-09 | **Type:** Brain validation + incident methodology bootstrap
**Focus:** H35 — Validate Brain v3 in real session work + design incident-processing way of working

## Entry Context

User reframed the session at the start:
1. We worked an incident in the previous sessions (INC-000006073). User wants this formalized as a way of working.
2. The vendor master data inconsistency surfaced by INC-000006073 (KTOKK ↔ AKONT) needs to be added as a pending check.
3. Build a strong solution: support skill + dedicated subagent for incident processing.
4. Mid-session add: evaluate how the new brain v3 model works and look for improvements.

## Success Criteria

- [ ] Vendor master KTOKK↔AKONT inconsistency is a first-class recurring DQ check
- [ ] Incident processing workflow is captured as a skill + subagent (not just memory)
- [ ] INC-000006073 is upgraded to a first-class brain record (not just a doc in a domain folder)
- [ ] Brain v3 self-evaluation produces concrete improvements actually shipped this session
- [ ] FALS-003 (knowledge_docs links useful?) and FALS-004 (rules sufficient?) get first data points

## Plan

### Track A — Vendor master integrity check
- Update DQ-001 from "1 vendor" to "class of defect — recurring check"
- Add KU-020 for unquantified scope across 316K vendors
- Add FALS-006 to test the recurring-check hypothesis
- Build `Zagentexecution/quality_checks/vendor_master_integrity_check.py` (CLI args, GGB1 cross-check)

### Track B — Incident methodology
- Add 4 feedback rules: class generalization, 7-step workflow, doc canonical structure, extract-before-speculate
- Move INC-000006073_travel_busarea_analysis.md → knowledge/incidents/INC-000006073_travel_busarea.md
- Fix stale path references (Travel README, brain_edges, brain rule strings)

### Track C — Brain v3 first-class incidents layer
- New `brain_v2/incidents/incidents.json` collection
- Update `build_brain_state.py` to load it as Layer 11
- Enrich `indexes.by_incident` from list-of-objects to dict-with-status-doc-fix

### Track D — Brain v3 evaluation (mid-session pivot, user-driven)
- Question: "what do you NOT have classified that's not in the context?"
- Build automatic blind-spot detector (Layer 12)
- Force-include any object referenced from annotations/claims/incidents
- Add `_coverage` metric showing pct_classified
- Add 3 brain feedback rules: brain-first-then-grep, blind-spots-are-first-class, force-include-referenced-names
- Add KU-022 (triage blind spots), KU-023 (TADIR-wide coverage gap)

### Track E — Skill + subagent
- Create `.agents/skills/sap_incident_analyst/SKILL.md` with the 7-step protocol
- Create `.claude/agents/incident-analyst.md` (Opus, owns full workflow autonomously)

### Track F — Close
- Final brain rebuild + validate (coverage stable or higher)
- Plan + retro + PMO update + commit

## Hypotheses to Test

- **H50.1**: The brain has the analysis doc linked but won't use it without an explicit "brain-first" rule. (RESULT: confirmed — I globbed before reading the brain link, even though it was there.)
- **H50.2**: ~25% of objects the brain talks about are not classified as first-class entities. (RESULT: confirmed — 75.6% coverage, 20 blind spots including PA0027.)
- **H50.3**: The 7-step incident workflow can be captured as a skill+subagent reproducible by a fresh agent. (RESULT: TBD until next incident — FALS-005.)
