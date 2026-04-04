# Session #035 Retrospective
**Date:** 2026-04-03/04
**Type:** CO Table Extraction + Integration Archaeology v2
**Duration:** ~2 sessions (VPN interruption overnight)
**Model:** Claude Opus 4.6 (1M context)

---

## Accomplishments

1. **B2 closed** — BSEG is not a table, it's a JOIN (bseg_union VIEW). Golden Query covers 85.9% WBS via FMIFIIT.OBJNRZ. Resolved by design.

2. **B3 closed — CO tables fully extracted to Gold DB (3,451,708 rows)**
   - COOI: 772,933 rows (22 fields) — 2024: 287K, 2025: 309K, 2026: 177K
   - COEP: 2,551,859 rows (23 fields) — 2024: 1.1M, 2025: 1.2M, 2026: 248K
   - RPSCO: 126,916 rows (47 fields) — 2024: 47K, 2025: 48K, 2026: 32K
   - Anchor estimate was 1.6M — actual 2x larger (3.45M)

3. **Third integration vector discovered: File-based jobs (~8,700 runs)**
   - 9 external systems: SWIFT banks, COUPA, EBS/MT940, SuccessFactors EC, TULIP, UNESDIR, Data Hub, BW, MBF
   - COUPA has DUAL integration: file posting (348 runs) + BDC (3 sessions)

4. **SuccessFactors EC is ACTIVE (not "planned")**
   - ECPAO_OM_OBJECT_EXTRACTION: 43 parallel jobs, 1,290+ runs
   - ECPAO_EMPL_EXTRACTION: 3 jobs, 51 runs
   - G41 closed — SF EC live in production

5. **Complete Integration Map built: 37 flows, 18+ systems, 8 channels, 10 open questions**
   - [integration_map_complete.md](../../knowledge/domains/Integration/integration_map_complete.md)
   - Every flow documented with: channel, method, source, target, artifact, volume, status

6. **New systems discovered**
   - UNJSPF (UN Pension Fund) — SOAP/XI via UNICC
   - BOC Invoice WF — registered gateway program
   - AWS (EC2 + S3) — HTTP:80 (security concern: no HTTPS)
   - Data Hub — unknown target for FM/HR data exports
   - MBF (Medical Benefits Fund) — eligibility file

7. **IDoc traffic analyzed**: 19,400 docs across 4 flows (BW=11.8K, MuleSoft=4.4K, ExchRate=988, LSMW=2.1K)

---

## Discoveries

1. **COOI/COEP much larger than anchored** — Anchor said 385K/616K, actual 773K/2.55M. Anchors were likely total without year filter or used object-scoped approach.
2. **COEP has PERIO field** — enables period-by-period extraction, critical for VPN resilience.
3. **RPSCO is pivoted** — WLP01-16 + WTP01-16 (plan + actual per period). No PERIO field, uses PERBL.
4. **COOI cost element = SAKTO** (not KSTAR). COEP cost element = KSTAR. Different field names for same concept.
5. **Payment Status Reports = 3-step job chain**: SWIFT ACK upload (UNES + IIEP) then bank report import (SocGen + 2x Citi).
6. **Exchange rates source unknown** — P01 broadcasts to D01/V01 via IDoc, but who feeds P01? `YFI_FILE_RATES_TMS` ran once. Possibly manual or ECB feed.
7. **LSMW Jan 2025** — 1,840 procurement objects (SES + PO + contracts) loaded in 2 days. Migration or annual process?
8. **AWS HTTP:80** — CSI_AWS_EC2 and CSI_AWS_S3 use HTTP, not HTTPS. Security red flag or test destinations.

---

## What Went Well

- **Period-by-period extraction** solved VPN resilience problem. Fresh connection per period = no data loss on VPN drops.
- **DD03L-first approach** caught 7 invalid field names before extraction started (KSTAR, BELNR, BUZEI not in COOI).
- **Job/IDoc mining from Gold DB** — all integration discovery done without live SAP access, purely from existing extracted tables (TBTCO, TBTCP, EDIDC, RFCDES, TFDIR_CUSTOM).

---

## What Could Be Better

1. **Re-extracted COOI 2024** — had it from test run but script didn't check for existing data. Fixed mid-session with skip logic.
2. **COEP year-at-once approach failed** — 1.1M rows in memory + split-field + VPN drop = lost everything. Should have started with period-by-period from the beginning.
3. **Anchor counts were wrong** — trusted Session #005 anchors (385K/616K/637K) without questioning. Actual was 2x larger. Lesson: always probe count before estimating time.
4. **Multiple background processes left running** — VPN dropped, processes hung for hours. Should have set shorter timeouts.

---

## Verification Check (Principle 8)

**Assumption challenged:** "37 integration flows are complete." 
- [INFERRED] — We only see traffic that leaves traces in EDIDC/TBTCO/RFCDES. Synchronous RFC calls from external systems (.NET apps) leave NO trace in these tables. The 334 RFC-enabled FMs could be called millions of times and we'd never see it. The 37 flows are what's VISIBLE, not what's TOTAL.

**Gap identified:** HTTP destinations with GUID names (DEE7059..., E13895..., etc.) — ~20 destinations. We didn't investigate any of them. They could be active integrations to unknown systems.

**Claim probed:** "SuccessFactors EC is active" — [VERIFIED] 1,290+ ECPAO job runs in mar 2026 confirms it's not test data. But: we don't know if EC Payroll is actually PROCESSING the extracted data. Extraction is confirmed; consumption is inferred.

---

## PMO Reconciliation

### Closed this session:
- ~~B2~~ — BSEG PROJK (resolved by design)
- ~~B3~~ — CO tables (3.45M rows extracted)
- ~~G41~~ — SuccessFactors EC (confirmed active)
- ~~42~~ — CO tables in completed archive

### New items added:
- **G45** — Update connectivity diagram with file-based integration tier
- **G46** — Update `sap_interface_intelligence` skill with file-based vector
- **G47** — Investigate Data Hub target system

### New memory files:
- `project_coupa_file_integration.md` — COUPA file-based integration discovery
- `project_file_based_integrations.md` — Full file-based integration analysis (5 tiers)

### Count:
- Before: 1B | 12H | 47G = 60 items
- Closed: B2, B3, G41 = -3
- Added: G45, G46, G47 = +3
- After: **1B | 12H | 47G = 60 items** (net zero, but blocking reduced from 3 to 1)

---

## Pending -> Next Session

1. **Integration map companion HTML** — build interactive visual from integration_map_complete.md (37 flows, 8 channels)
2. **Investigate the 10 open questions** from integration map (exchange rate source, Data Hub identity, LSMW origin, AWS security, etc.)
3. **Update connectivity diagram** (G45) — add file-based tier, correct SuccessFactors status
4. **H29** — SKAT 510 text differences (quick win from #034)
5. **H21** — Currency conversion script (TCURR data ready)
6. **B10** — Evaluate/close 3 stale skills

---

## Session Self-Score

| Dimension | Score | Reasoning |
|-----------|-------|-----------|
| Discovery value | 9/10 | Third integration vector + SF EC active + 6 new systems + complete integration map |
| Data extraction | 8/10 | 3.45M CO rows but VPN issues caused rework |
| Efficiency | 6/10 | VPN drops, re-extractions, wrong anchor estimates. Period-by-period should have been default |
| Knowledge capture | 9/10 | integration_map_complete.md is the most structured integration doc yet |
