# Session #044 Retro — House Bank Configuration Process Discovery

**Date:** 2026-04-07
**Duration:** Extended session (~6 hours)
**Previous:** #043 (House bank UBA01 creation, Treasury domain)
**Model:** Claude Opus 4.6 (1M context) via Claude Code

---

## Hypotheses (declared during session)

| # | Hypothesis | Status | Evidence |
|---|---|---|---|
| H1: OBA1 config only needed for clearing accounts (11*) | **FALSIFIED** | Bank accounts (10*) hold real cash — must be revalued. Gold DB: only 6 of 219 non-USD bank accounts have T030H (3%). This is the #1 finding. |
| H2: XINTB=X is the standard for bank accounts (ECO09 benchmark) | **FALSIFIED** | 1 of 353 KTOKS=BANK accounts has XINTB=X (NTB02 investment). 73 CASH accounts (190*) have it intentionally. INCIDENT: Ingrid Wettie reported F5562 error on UBA01. |
| H3: T018V is USD-only | **FALSIFIED** | 69% USD, 20% EUR, 11% other (CHF/JPY/GBP). 33 non-USD entries across SOG03, CIC01, etc. |
| H4: Only 2 paying banks exist (CIT21, ECO09) | **FALSIFIED** | 10 banks in T042I. Correct classification: ~9 HQ_PAYING (T042A+OBPM4) + 1 FO_LOCAL (ECO09 — method 3 local check, no DMEE, replenished from HQ) |
| H5: GS02 sets can only be maintained manually per system | **FALSIFIED** | GRW_SET workbench transport carries full set definition. D01K9B0F5F imported to P01 successfully. No delta transport available. |

---

## Deliverables

| # | Deliverable | Status | Location |
|---|---|---|---|
| 1 | YBANK sets D01=P01 alignment confirmed | SHIPPED | `ybank_sets_full_comparison.py` |
| 2 | Transport D01K9B0F5F analysis + import confirmed | SHIPPED | Sets arrived in P01, 158 entries matched |
| 3 | V01 connection configured (hq-sap-v01:00:350) | SHIPPED | `.env` updated |
| 4 | V01 missing G/L 1165421 created (SKA1+SKB1+SKAT) | SHIPPED | Via RFC |
| 5 | D01 XINTB fixed on 4 UBA01 accounts | SHIPPED | Via RFC |
| 6 | D01 SKAT French+Portuguese texts fixed (ECOBANK→UBA) | SHIPPED | Via RFC |
| 7 | Gold DB: T030H(1014), T035D(151), T018V(108), T012T(1049) extracted | SHIPPED | `p01_gold_master_data.db` |
| 8 | Bank classification: 211 banks → 7 categories | SHIPPED | `house_bank_classification.py` + JSON |
| 9 | Full pattern discovery: 9 patterns (P1-P9) + 9 controls (C1-C9) | SHIPPED | SKILL.md rewritten |
| 10 | 3-system comparison script (D01/V01/P01) | SHIPPED | `uba01_3system_comparison.py` |
| 11 | 680 GL cross-system comparison (SKA1/SKB1/SKAT) | SHIPPED | `all_gl_3system_compare.py` — 499 field differences found |
| 12 | House bank configuration companion HTML | SHIPPED | `companions/house_bank_configuration_companion.html` |
| 13 | SKILL.md rewritten with form fields, decision flow, OBA1 deep explanation | SHIPPED | `.agents/skills/sap_house_bank_configuration/SKILL.md` |
| 14 | **CRITICAL FINDING: T030H systemic gap** | SHIPPED | 213/219 non-USD bank accounts (3%) missing OBA1 valuation |

**Closure math:** 14 deliverables shipped, 0 new PMO items added. Net closure: +14.

---

## Discoveries

### #1 CRITICAL — T030H Systemic Gap (OBA1 Valuation)
**213 of 219 non-USD bank accounts (10*) have NO T030H valuation config (3% coverage).** 48 of 204 non-USD clearing accounts (11*) also missing (76% coverage). Impact: FAGL_FC_VAL skips these accounts at month-end — FX gains/losses on real cash balances in 80+ currencies at 80+ field offices are NOT reflected in financial statements. Material financial reporting gap. Affects SOG01, SOG03, CIC01, BNP01, all ECO banks, all CIT field offices, all SCB field offices.

### #2 — XINTB Pattern + Incident
Only 1 of 353 KTOKS=BANK G/Ls has XINTB=X. Production standard is empty. UBA01 was configured with XINTB=X following a misread of ECO09 benchmark → Ingrid Wettie hit F5562 error. P01 fixed by MD team same day, D01 fixed via RFC. **RULE: NEVER set XINTB=X on bank accounts.**

### #3 — GRW_SET Transport Process
GS02 sets can be transported via GRW_SET workbench object. Transport carries FULL set (not delta) — overwrites target. Pre-requisite: systems must be aligned before first transport. SETHEADER audit trail must be updated when syncing via RFC (Phase 4 in `ybank_setleaf_sync.py`).

### #4 — Bank Classification (7 categories)
From 211 banks: HQ_PAYING (~9), FO_LOCAL_DISBURSEMENT (1 = ECO09), EBS_CONFIG (56), INVESTMENT/COUPON (2), INTER_AGENCY (1 = UNDP), PENDING/DORMANT (5), CLOSED (117). ECO09 is FO local — pays by check (method 3), replenished from HQ centrally, no DMEE file.

### #5 — V01 Is a Real Separate System
V01 was previously falling back to D01 connection (same host/client). Now properly configured: hq-sap-v01:00:350 via SNC/SSO. Full 3-system comparison revealed 499 field-level differences — V01 is significantly out of sync (missing 4 GLs, old texts, old HBKID assignments, 102 GLs not blocked).

### #6 — 3 Validation Agents Found Significant Errors
Three independent agents validated our claims against Gold DB. Key corrections: T030H count was 1,014 not 891. T018V is multi-currency not USD-only. T042I has 10 banks not 2. XOPVW is 99% not 85%. The "zero revaluation risk" claim was wrong — 86 active partial T030H entries have multi-currency postings.

---

## Failures/Corrections

1. **XINTB set wrong on UBA01** — followed ECO09 benchmark without checking production reality. ECO09 itself doesn't have XINTB=X. Pattern P3 caught it in data but accounts were already configured. Fixed same day after Ingrid's report.
2. **Multiple claims falsified by validation agents** — T030H count, T018V currency distribution, T042I bank count, revaluation risk assessment were all wrong in initial analysis. Corrected after 3-agent validation.
3. **OBA1 rule was wrong** — stated 10* bank accounts only need "optional" valuation. Bank accounts hold real cash — valuation is MANDATORY. Corrected after user pointed out banks should value balances.

---

## Verification Check

- **Assumption challenged:** "ECO09 is a standard paying bank like CIT21" — FALSIFIED. ECO09 is FO local disbursement (T042I method 3 but no T042A). Pays locally, replenished centrally.
- **Gap identified:** 97% of non-USD bank accounts missing OBA1 valuation — this was not visible until we combined T030H extraction with T012K account mapping.
- **Claim probed:** "XINTB=X is the benchmark pattern" — FALSIFIED by Gold DB (1 of 353) and by production incident (F5562 error). The claim was wrong, the ECO09 benchmark was misread.

---

## Pending -> Next Session

1. **P01: Release transport D01K9B0F5K** (OBA1 T030H fix for UBA01 clearing accounts)
2. **T030H systemic gap remediation plan** — produce detailed report for TRS/Finance listing every affected account with suggested values
3. **V01 SKAT text cleanup** — 244 text differences vs D01/P01 (cosmetic)
4. **V01 sync assessment** — 499 field-level differences, decide what to sync
5. **Companion final review** — verify all corrected data is reflected
6. **Session retro commit**

---

## Artifacts Created

### Scripts
- `uba01_oba1_sets_review.py` — OBA1 + SETLEAF D01 vs P01
- `ybank_sets_full_comparison.py` — Full entry-by-entry YBANK sets comparison
- `ybank_consistency_check.py` — SETHEADER/SETNODE/SETLEAF/SETLINE consistency
- `setheader_probe2.py` — SETHEADER audit fields
- `transport_analyze_D01K9B0F5F.py` — Transport analysis
- `transport_keys_D01K9B0F5F.py` — Transport key decoder
- `transport_status_check.py` — Transport status checker
- `extract_missing_bank_tables.py` — Extract T030H/T035D/T018V/T012T to Gold DB
- `house_bank_gold_analysis.py` — Gold DB bank analysis
- `house_bank_classification.py` — Bank classification (7 categories)
- `house_bank_full_matrix.py` — Full 13-step compliance matrix
- `t030h_deep_analysis.py` — T030H deep analysis (revaluation risk)
- `house_bank_pattern_discovery.py` — Pattern discovery (P1-P9)
- `uba01_full_check_both.py` — 15-check compliance D01+P01
- `uba01_3system_comparison.py` — Full 3-system comparison
- `all_gl_3system_compare.py` — 680 GL cross-system SKA1/SKB1/SKAT comparison
- `uba01_fix_xintb_d01.py` — XINTB fix
- `uba01_xintb_check.py` — XINTB verification
- `uba01_gl_full_compare.py` — Field-by-field GL comparison

### Companions
- `companions/house_bank_configuration_companion.html` — Bank config intelligence companion with OBA1 deep dive

### Skill Updates
- `.agents/skills/sap_house_bank_configuration/SKILL.md` — Major rewrite: 18 checks, 9 patterns, 9 controls, form fields, decision flow, OBA1 deep explanation, systemic gap finding

### Gold DB Additions
- T030H (1,014 rows), T035D (151 rows), T018V (108 rows), T012T (1,049 rows)
