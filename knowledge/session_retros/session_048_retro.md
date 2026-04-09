# Session #048 Retrospective
**Date:** 2026-04-08/09 | **Duration:** ~8 hours | **Type:** Incident Response + Domain Creation + Brain Architecture

## What Happened

INC-000006073 — IIEP traveler Katja HINZ's travel advance posting failed. Investigation went from email screenshots → root cause confirmed from SAP source code → 2 new domains (Travel, BusinessPartner) → complete BP data model extraction (2.5M rows) → Brain annotation framework → Code Brain strategy.

## Deliverables (14)

| # | Deliverable | Type |
|---|---|---|
| 1 | INC-000006073 analysis v2 — 13 sections, executive summary, source:line references | Knowledge |
| 2 | 34 SAP standard ABAP files extracted (24,559 lines) — HRTS function group, RPRAPA00, RPRTRV* | Code |
| 3 | Travel domain (`knowledge/domains/Travel/`) — README, 48 brain edges, derivation chain | Domain |
| 4 | Business Partner domain (`knowledge/domains/BusinessPartner/`) — README, BP→vendor→GL chain | Domain |
| 5 | 21 BP/vendor/customer tables extracted to Gold DB (2.5M rows, ALL fields on wide tables) | Data |
| 6 | PTRV_SCOS (14K) + PTRV_SHDR (14K) + GB922 (218) + T077K (47) to Gold DB | Data |
| 7 | `extract_bp_full.py` — canonical BP extraction script (DDIF + rfc_read_paginated, all fields) | Tool |
| 8 | Brain annotation framework (`brain_v2/annotations/`) — annotate, search, recover | Tool |
| 9 | Annotation ingestor wired into Brain build (Phase 6 in cli.py) | Tool |
| 10 | 30 objects annotated, 41 annotations seeded (session #048 + historical recovery) | Knowledge |
| 11 | Code Brain Strategy doc (`Brain_Architecture/code_brain_strategy.md`) | Architecture |
| 12 | Historical annotation recovery plan (`brain_v2/annotations/recover_historical_annotations.md`) | Plan |
| 13 | 6 feedback rules saved | Feedback |
| 14 | PMO updated: H34 (HIGH) + G55-G58 (backlog) | PMO |

## Root Cause (INC-000006073)

Two factors combined, invisible for 10+ years:
1. **Intercompany trip** (new): `LHRTSF01.abap:852` `IF epk-bukst = epk-bukrs` — only fills GSBER for same-company
2. **Wrong vendor type** (since 2016): KTOKK=SCSA → AKONT=2021011 → not covered by GGB1

Three broken safety nets: BAdI PA0027-02 expired (2021), ZXTRVU05 commented out (Konakov 2018), GGB1 missing GL 2021011.

## Gold DB Growth

| Metric | Before | After |
|---|---|---|
| Tables | 93 | ~120 |
| Rows | ~30M | ~35M |
| Key additions | — | LFA1(316K/147c), LFB1(327K/78c), KNA1(12.5K/189c), ADRC(335K/99c), BNKA(419K), LFBK(202K), ADR6(302K), ADR2(290K), TIBAN(111K), LFC1(106K), + 11 more |

## What Went Well

1. **Root cause to source:line** — LHRTSF01:852, CM00A:37, ZXTRVU05:63, LHRTSU05:155. Not hypotheses — confirmed from extracted code.
2. **Two domains in one session** — Travel + BusinessPartner, both with full architecture docs.
3. **Parallel extraction** — 5 concurrent RFC connections, filled freed slots immediately.
4. **Annotation framework shipped** — objects now accumulate intelligence across sessions.
5. **SAP cross-reference discovery** — D010TAB/WBCROSS/D010INC = SAP's own dependency graph. 100% accuracy, no regex parsing needed.

## What Went Wrong

1. **Wrote extraction scripts from scratch 4 times.** Should have reused `rfc_read_paginated` pattern immediately. Wasted ~1 hour on bash quotes, wrong field probes, column name sanitization.
2. **Sequential extraction initially.** 22 tables one-by-one when 5 parallel cuts time by 4x.
3. **PTRV_SCOS extracted with 8/35 fields.** Needs re-extraction with DDIF for all fields.
4. **4,030 ABAP nodes in Brain have ZERO edges.** `tables_read`/`fms_called` in metadata but never materialized as graph edges. Annotation ingestor now fixes this.
5. **41 annotations recovered from 47 sessions — should be 200+.** Historical recovery was partial. H34 must do deep review.
6. **Some annotations are intermediate, not final conclusions.** Session close protocol now requires tracing learning arc to find FINAL conclusion before annotating.

## Key Architectural Decision: Code Brain Strategy

Programs + tables + config relationships are the **backbone** of the Brain. Not 52K fund nodes. 

Three approaches researched:
- **SAP cross-reference tables** (D010TAB, WBCROSS, D010INC) — RECOMMENDED. SAP already maintains 100% accurate dependency graph. Just extract it.
- **ACE (ABAP Code Explorer)** — open source, field-level slicing. Good for deep dives.
- **SAP Knowledge Graph / Cerebro** — commercial, 452K tables + 80K CDS views. For S/4 migration path.

Decision: Extract D010TAB + WBCROSS in H34, replace regex parser with cross-reference data.

## Feedback Rules Created (6)

1. `feedback_reuse_extraction_pattern.md` — never write extraction from scratch
2. `feedback_extraction_is_skill_not_code.md` — "extract" = skill invocation
3. `feedback_parallel_extraction.md` — max 5 concurrent RFC
4. `feedback_brain_code_tables_are_backbone.md` — programs+tables = Brain backbone
5. `feedback_session_close_annotations.md` — annotate every object at session close, FINAL conclusions only
6. `project_business_partner_domain.md` — BP domain architecture

## PMO Updates

| # | Type | Task |
|---|---|---|
| **H34** | HIGH (NEW) | Code Brain v2: SAP cross-reference extraction + annotation framework + 200+ historical annotations |
| G55 | Backlog (NEW) | BP Conversion Readiness: research vendor→BP migration strategies |
| G56 | Backlog (NEW) | Travel discovery: KTOKK anomalies + GGB1 coverage gaps across all company codes |
| G57 | Backlog (NEW) | Brain ingestion: Travel + BP domains (48+ edges, 69 ABAP files) |
| G58 | Backlog (NEW) | Re-extract PTRV_SCOS/PTRV_SHDR with ALL fields |

**Net: +5 items, 0 closed. Justified: first real incident resolution + Brain architecture breakthrough.**

## What We Can Do Next (Priority Order)

### H34 — Brain Rebuild (next session, HIGH)
1. Extract D010TAB + WBCROSS + D010INC from P01 → Gold DB (SAP cross-reference = complete dependency graph)
2. Run `python -m brain_v2 build` — picks up 34 new SAP standard files + 21 new tables + annotation ingestor
3. Deep review ALL 34 session retros — trace learning arcs per object → final conclusions → 200+ annotations
4. Materialize 4,030 ABAP metadata edges (tables_read/fms_called → real graph edges)
5. Validate: `brain_v2 impact LFA1` should show full chain to GGB1 rules
6. Validate: `brain_v2 depends ZCL_IM_TRIP_POST_FI` should show PA0027 + HR_READ_INFOTYPE

### G56 — Travel/BP Discovery (after H34)
1. Cross LFB1.AKONT with GB901 conditions → find ALL GLs with vendors but no GGB1 rule
2. Cross LFA1.KTOKK with PERSG (need PA0001 extract) → find all wrong vendor account groups
3. Impact: systematic INC-000006073 prevention across all 9 company codes

### G55 — BP Conversion Readiness (research)
1. Read SAP help docs on vendor→BP migration
2. Analyze: 559 BUT000 vs 316K LFA1 = <1% converted. CVI_VEND_LINK = 0 rows.
3. Output: readiness assessment with data-backed gap analysis

### INC-000006073 — Close the Ticket
1. Send analysis to Travel/HR team
2. Question: Was COMP_CODE=UNES intentional?
3. Fix: PA30 (PA0027-02) for immediate unblock + YFI_BASU_MOD (GL 2021011) for structural fix
