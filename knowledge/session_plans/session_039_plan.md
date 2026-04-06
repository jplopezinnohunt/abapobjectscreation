# Session #039 Plan

**Date:** 2026-04-05 (continued from #038, same day)
**Previous:** #038 (committed as ae54fbe, 15/15 deliverables, 2 confirmed / 3 falsified hypotheses)
**Main agent:** Claude Opus 4.6 (1M context)

---

## Hypothesis (what this session will prove)

- **H1:** The ABAP 72-char truncation pattern discovered in #038 (`h29_skat_update.py run_batch()`) is generalizable and belongs as a named failure mode in `sap_class_deployment` skill. Testable by: skill doc cites the exact safety rail code + the SELECT SINGLE+UPDATE FROM ls replacement pattern.
- **H2:** The extended `RECONNECTABLE_ERRORS` list in `rfc_helpers.py` (RFC_CLOSED, broken, WSAE*, connection reset) is canonical reconnect behavior that should be documented in `sap_data_extraction` skill so future extraction scripts reuse it instead of re-discovering it.
- **H3:** The SEPA `<Purp><Cd>` PurposeCode literal that H18 has been chasing for 11 sessions is NOT in ABAP source at all — it lives in the DMEE format tree (table `DMEE_TREE_NODES`, referenced by `DMEE_TREES`). Testable by: RFC query returns the literal `<Purp>` or `Cd` element with a populated value on at least one tree row for DMEE format Z_CGI or equivalent UNESCO format.

## Deliverables (shippable artifacts, named)

1. `.agents/skills/sap_class_deployment/SKILL.md` — new "Common failure modes" subsection with: (a) 72-char ABAP line limit via RFC_ABAP_INSTALL_AND_RUN, (b) silent truncation symptom, (c) `SELECT SINGLE` + `UPDATE … FROM ls` replacement pattern, (d) `raise SystemExit` safety rail in batch loop. Evidence: `h29_skat_update.py` session #038.
2. `.agents/skills/sap_data_extraction/SKILL.md` — new "Reconnect patterns" subsection citing the full RECONNECTABLE_ERRORS list from `rfc_helpers.py` with rationale per pattern. Reference the 141-batch H29 run as the validating case.
3. `Zagentexecution/mcp-backend-server-python/h18_dmee_tree_probe.py` — read `DMEE_TREE_NODES` via RFC_READ_TABLE for DMEE formats matching UNESCO CGI (SEPA CT). Filter on attributes containing `Purp` / `Cd` / `PurposeCode`. Output CSV to `knowledge/domains/Payment/h18_dmee_tree_nodes.csv`.
4. `knowledge/domains/Payment/h18_dmee_tree_findings.md` — short markdown with: format tree IDs found, count of Purp/Cd nodes, the literal value if located, and the follow-on path if not. Must either ship H18 as CLOSED (Cd literal found) or strike H18 as INVESTIGATED AND CLOSED with the honest "value is dynamic/field-referenced not literal" finding.
5. `.session_state.json` updated with #039 baseline + end counts.
6. `knowledge/session_retros/session_039_retro.md` — plan-vs-retro diff.

## Out of scope (declared)

- Full DMEE format tree documentation (only the `Purp/Cd` question for UNESCO CGI format)
- #037 ghost audit (−1 baseline drift) — deferred, low priority
- PMO stale-name cleanup across all H-items — deferred, needs dedicated pass
- H19/H21/H22/H23 bank recon work — out of scope, different domain session
- New skill creation — this session only UPDATES existing skills

## Success criteria (testable at close)

- [ ] H1: `sap_class_deployment/SKILL.md` diff shows the 72-char subsection with working code sample copy-pasted from h29_skat_update.py
- [ ] H2: `sap_data_extraction/SKILL.md` diff shows RECONNECTABLE_ERRORS table with at least 6 patterns (RFC_CLOSED, connection to partner, broken, WSAECONNRESET, WSAETIMEDOUT, connection reset)
- [ ] H3: `h18_dmee_tree_probe.py` runs against D01 via SNC, returns >=1 row, output CSV exists
- [ ] Deliverable 4 exists with either a CONFIRMED or CLOSED verdict — no "needs more investigation" escape hatch
- [ ] `items_shipped >= items_added` — target: strike H18 (1 shipped), no new items added
- [ ] `.session_state.json` updated with end counts
- [ ] Plan-vs-retro diff in session_039_retro.md

## What a reasonable reviewer would ask to kill

- **"Skill routing is just documentation churn"** — Defense: #038 audit flagged this explicitly as Principle 5 gap. Code has the fix, docs lag. A future session hitting the same 72-char bug without the skill doc will re-discover it. Cost of doc = 30 min, cost of re-discovery = hours + risk of silent corruption.
- **"H18 is a zombie, why keep investigating?"** — Defense: #038 falsified the ABAP path and declared DMEE_TREE_NODES as the next path. This session tests that hypothesis. Either we ship or we kill with honest negative finding — no further deferral allowed.
- **"You're combining two unrelated tasks"** — Defense: both derive from #038 unfinished work. Skill routing is 30 min of docs, H18 is 1-2h of investigation. One plan, sequential execution, atomic close.
- **"DMEE tree may also not have the literal — what then?"** — Defense: if H3 falsifies, H18 still closes with a DOCUMENTED negative result (the Cd value is dynamic/runtime-computed, not static in configuration). Zombie closes either way.

## Execution order

1. Phase A (skill routing, ~30 min): Read both skill files → Edit both with new subsections → verify edits
2. Phase B (H18 probe, ~1-2h): Write probe script → run against D01 → analyze output → write findings doc → strike/update PMO H18
3. Phase C (close): Update `.session_state.json` → write retro → commit

## Start/end counts

- Start: B=0 H=7 G=21 = 28 items (inherited from #038 close)
- End target: B=0 H=6 G=21 = 27 items (H18 struck)
- Net closure: +1 (H18 shipped) / 0 added / 0 partial
