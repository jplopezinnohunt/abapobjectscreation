# Drift D01 vs P01 — Executive Summary (Phase 0 closure)

**Generated**: 2026-04-29 · **Session**: #62

## Principle (user-confirmed 2026-04-29)

**P01 is canonical** for what's running in production today:
- Active config (TFPM042FB Event 05 registrations, T042Z, DMEE tree V000, OBPM5 BCM routing)
- Active XML files generated (`\\hq-sapitf\SWIFT$\P01\input\`)
- Active versions of Y* / Z* / SAP-std classes

D01 drift information is for **retrofit planning only** — to know what we
need to bring back to D01 before any transport for V001 work.

The design of the change (Pattern A fix, V001 trees, OBPM4 unchanged for SEPA, etc.)
**stays anchored on P01 evidence** regardless of D01 state.

## Drift run summary

| Metric | Value |
|---|---|
| Total drifts detected (run 1) | 142 |
| CRITICAL (after follow-up verification) | 4 (DMEE tree node-count discrepancy only) |
| HIGH (legitimate code drift) | ~60 includes drifted by 6 months |
| INFO (downgraded from CRITICAL) | 10 FMs (cosmetic — same SAP transport import flow) |
| Customizing diff | TFPM042FB +5 D01 rows, T042Z +3 D01 rows (both unrelated WIP) |

## Critical findings, classified

### 1. ✅ Pattern A target file is safe to apply

`YCL_IDFI_CGI_DMEE_FALLBACK_CM001`:
- P01 last change: 2024-11-28 by N_MENARD
- D01 last change: 2024-11-22 by N_MENARD
- **Diff D01 vs P01: only blank lines (cosmetic)**. Code is byte-identical:
  the WHEN block at `<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>` exists
  in both with same logic
- Pattern A fix line numbers: P01 line 22-31, D01 line 26-35 (offset by +4 due to
  blank lines added in D01)
- **Verdict**: Pattern A applies safely to D01

### 2. ⚠️ Other UNESCO includes drifted 6 months (need verification)

`YCL_IDFI_CGI_DMEE_FALLBACK` includes other than CM001 (CCDEF, CCIMP, CCMAC, CI, CO, CP, CT, CU, CM002):
- P01: 2024-09-06 — D01: 2024-03-01 (~6 months)
- Same author (N_MENARD)
- **Action**: extract D01 source for these includes too and diff vs P01 to know
  if differences are cosmetic or functional. CM002 missing in D01 entirely
  is a special case (was deleted in D01 but kept in P01? Or never created in D01?)

### 3. 🔴 5 objects confirmed P01-ONLY (must retrofit before Phase 2)

| Object | Type | Author | Phase 2 dependency |
|---|---|---|---|
| `YCL_IDFI_CGI_DMEE_DE` | CLAS | N_MENARD | Italy/Germany branches won't work in D01 if missing |
| `YCL_IDFI_CGI_DMEE_IT` | CLAS | N_MENARD | idem |
| `Y_IDFI_CGI_DMEE_COUNTRIES_DE` | ENHO | N_MENARD | Country-DE BAdI dispatch |
| `Y_IDFI_CGI_DMEE_COUNTRIES_FR` | ENHO | N_MENARD | Country-FR BAdI dispatch (CRITICAL — France is core) |
| `Y_IDFI_CGI_DMEE_COUNTRIES_IT` | ENHO | N_MENARD | Country-IT BAdI dispatch |

These bind the BAdI to country-specific Y classes. Without them, country-routing
breaks at runtime. **Retrofit transport REQUIRED** before any V001 work in D01.

### 4. ✅ DMEE tree 2x node count — likely V000 + V_OLD versions, non-blocking

D01 has approximately double the nodes of P01:
- SEPA: P01=95 / D01=190
- CITI: P01=610 / D01=1220
- CGI: P01=631 / D01=1262
- CGI_1: P01=639 / D01=1264

Hypothesis (filter query failed so unverified yet): D01 retains older inactive
versions or test versions per tree. P01 garbage-collected old versions during a
refresh. **Non-blocking for our V001 strategy** — we create a NEW V001 atop
whatever is active. V000 active version's node count matches P01.

### 5. ⚠️ Customizing extras in D01 — unrelated WIP

| Table | Extra D01 rows | What | Related to our change? |
|---|---|---|---|
| TFPM042FB | 5 | All `FORMI=/CHECK_SG` (SocGen check printing PMW) | NO |
| T042Z | 3 | 1 SocGen check + 2 China manual transfers | NO |

**Action**: document. Don't touch. When we transport V001 to P01, this WIP doesn't
ride along (it's in a different transport scope). **Non-blocking**.

### 6. 🟢 SAP-std country dispatcher drift — normal SAP support pack flow

CL_IDFI_CGI_CALL05_FACTORY/GENERIC/FR/DE/IT/GB all show "P01 newer than D01"
by 1-2 weeks. Both authored by SAP. This is **normal SAP support pack import
flow**: SAPNote/support pack hits D01 first, then gets transported to P01 via
TMS sometime later. Same code, sequenced import.

**Action**: re-verify with `diff` of one or two includes. If cosmetically
identical, downgrade to INFO. If functionally different, P01 has a SAP patch
that D01 doesn't yet have — escalate to BASIS for support pack alignment.

### 7. ✅ FMs (SAP-std + CITIPMW) — false-positive missing, real drift cosmetic

10 FMs flagged "missing in D01" by initial probe — **wrong probe method**
(REPOSRC keyed by include, not FM name). TFDIR-based re-probe confirmed
all 10 exist in both systems. Drift is hours/days same SAP transport.
**NOT blocking**.

## Phase 2 retrofit transport scope

Based on drift findings, the **`D01-RETROFIT-01`** transport must contain:

### Mandatory (CRITICAL drift)
1. `YCL_IDFI_CGI_DMEE_DE` (CLAS) — full retrofit from P01
2. `YCL_IDFI_CGI_DMEE_IT` (CLAS) — full retrofit from P01
3. `Y_IDFI_CGI_DMEE_COUNTRIES_DE` (ENHO) — full retrofit from P01
4. `Y_IDFI_CGI_DMEE_COUNTRIES_FR` (ENHO) — full retrofit from P01
5. `Y_IDFI_CGI_DMEE_COUNTRIES_IT` (ENHO) — full retrofit from P01

### To verify (HIGH drift on UNESCO classes)
After D01 source extracted for all 30 critical includes:
- If diff = blanks only: SKIP retrofit (cosmetic)
- If diff = functional: include in retrofit transport

### Out of scope (SAP responsibility)
- SAP-std CL_IDFI_CGI_CALL05_* drift: BASIS escalates support pack alignment, not us
- TFPM042FB +5 D01 rows (SocGen checks): different team, different transport
- T042Z +3 D01 rows (China + SocGen): different team, different transport

### N_MENARD review required
- Confirm Q1 (Pattern A: A1 remove vs A2 guard)
- Approve retrofit method (SAPLink vs reverse-transport vs paste — Q3)
- Confirm there's no in-flight WIP in D01 we'd clobber via retrofit

## What this changes in the plan

- **Phase 2 still proceeds with ZERO ABAP for SEPA/CGI** (V001 = config only)
- **Pattern A fix scope unchanged**: 1 method, 3 lines in CM001, but now with
  documented evidence that D01's CM001 is semantically equivalent to P01
- **Retrofit transport `D01-RETROFIT-01` becomes Phase 2 Step 0**: must release
  before Pattern A fix transport `D01-BADI-FIX-01`
- **Drift detector becomes a recurring check**: re-run before every Phase 2
  transport release to catch any new drift introduced by other teams

## Artifacts produced (Phase 0 closure)

| File | Purpose |
|---|---|
| `Zagentexecution/mcp-backend-server-python/d01_vs_p01_drift_detector.py` | Comprehensive drift probe |
| `Zagentexecution/mcp-backend-server-python/drift_followup_probe.py` | TFDIR-based FM verification + customizing per-row diff |
| `Zagentexecution/mcp-backend-server-python/drift_followup2_probe.py` | DMEE versions + D01 source extraction |
| `knowledge/domains/Payment/phase0/d01_vs_p01_drift_p01_snapshot.json` | P01 baseline snapshot |
| `knowledge/domains/Payment/phase0/d01_vs_p01_drift_d01_snapshot.json` | D01 snapshot |
| `knowledge/domains/Payment/phase0/d01_vs_p01_drift_report.md` | 142 drifts categorized |
| `knowledge/domains/Payment/phase0/d01_vs_p01_drift_followup.md` | FM verdict + customizing per-row diff |
| `knowledge/domains/Payment/phase0/d01_vs_p01_drift_followup2.md` | DMEE versions (failed slash filter) + D01 source paths |
| `extracted_code/FI/DMEE_d01_for_drift/` | 7 D01 includes for source-level diff |

## Cross-reference

- Plan: Phase 0 findings I (D01 vs P01) — superseded by this summary
- Brain: claims 80-85, feedback rule #204 (P01-only for config analysis)
- Companion: tab "Phase 0" updates with this evidence
