---
name: Cost Recovery AVC / Disponible Control Model (PSM-FM BCS)
description: Empirically verified model (P01+D01, 2026-06-29) of how SAP FM Availability Control (AVC) governs the "Disponible" (available budget) for UNESCO cost-recovery (CR) projects. Covers the CR control address, FMBL B1 budget type, RIB mechanism, cover fund family, D01 gap, and fund validity sync.
type: project
domain: PSM / Cost_Recovery_CRP
evidence_tier: TIER_1
created_session: s-2026-06-29
cross_links:
  - knowledge/domains/PSM/avc_availability_model.md
  - knowledge/domains/PSM/project_cost_recovery_analysis.md
  - companions/cost_recovery_bor_model.html
  - Zagentexecution/tasks/2026_06_29_fm_model_sync/fund_family_sync.py
  - claims: [#286, #287, #288, #289, #290, #291, #292]
---

# Cost Recovery AVC / Disponible Control Model

> **All claims verified empirically on P01 and D01 via live RFC reads 2026-06-29.**
> This doc extends `avc_availability_model.md` (general AVC model) with the CR-specific
> regime. "Disponible" = the AVC-available amount that must be positive for a cost-recovery
> posting to go through. "Para recuperar el costo el proyecto debe tener disponible."

## TL;DR — the CR-specific AVC address

Cost-recovery (CR) project disponible is controlled at a **control address**, NOT at the posting
leaf address. For the 5 CR test projects verified (567KEN2000, 537RAF4006, 218MAR2000, 263KEN5000,
235MAG5003):

```
FMAVCT rows found at:
  RFUNDSCTR = NAI            (NOT the project's own posting fund center)
  RCMMTITEM = 10', 11, 13, 20, 30, 40, 50, 80, TC   (the control commitment items)
```

This is the standard EXBO/Extrabudgetary AVC derivation regime: donor/XB funds control at detailed
CI level (with rollup exceptions to TC/PC/NPC), unlike OPF funds which collapse to TC only. See
`avc_availability_model.md` section "Two regimes" for the derivation engine (AFMA, strategy 9HZ00001).

## CR budget is FMBL VALTYPE=B1, NOT BPGE/BPJA WRTTP43

| Where | For CR funds | Why |
|-------|-------------|-----|
| **BPGE** (overall budget) | WRTTP43 = 0 | CR funds have NO entered overall budget |
| **BPJA** (annual budget) | WRTTP43 = 0 | Same — zero annual entered budget |
| **FMBL** (budget entry documents) | VALTYPE=**B1**, BUDTYPE=4000 | CR budget lives HERE |

FMBL CR budget characteristics (verified P01 2026-06-29):
- **VALTYPE** = B1 (Payment Budget — same category as the AVC ledger 9H which filters VALTYPE=B1/B2)
- **BUDTYPE** = 4000 (supplement; also ENTR/COSD/CORV/SEND/RECV processes observed)
- **PERIO** = control address fund center **NAI** + the control commitment items above
- **Fiscal years active**: 2024, 2025, 2026 for main CR funds; 263KEN5000/235MAG5003 multi-biennium
  from 2024
- **Period amounts**: in FMBL.TVAL01..TVAL16 (period-level columns, see claim #275)

**What this means for scripts:** Any budget read that looks only at BPGE/BPJA WRTTP43 will show
ZERO for CR funds. This is a FALSE NEGATIVE. The correct read for CR disponible is via FMAVCT
(control address NAI + CR CIs) or via `FMAVC_READ_TOTALS_FOR_ADDRESS` against the derived ACO.

## TWO DISTINCT PROCESSES — assignment vs recovery (do NOT conflate)

The disponible is **ASSIGNED** to the project by a person; the **recovery is a SEPARATE process**.
Earlier framing ("RIB revenue generates the disponible") was WRONG — corrected 2026-06-29 (user).

### (1) Budget assignment — where the first disponible comes from  ← the answer
Someone enters the spending authority with a **manual budget entry document** (FMBB), verified in FMBL:

| Field | Value |
|-------|-------|
| PROCESS | **ENTR** (Enter) |
| BUDTYPE | **3000** (original/entry — distinct from the 4000 used by recovery moves) |
| VALTYPE | **B1** |
| Commitment item | **TC** (total/control CI) + **80** |
| Fund center | NAI (control address) |
| Per fiscal year | yes |

Verified ENTR assignments (P01, B1/3000, CI TC+80):
| Project | Year | Disponible assigned |
|---------|------|--------------------|
| 567KEN2000 | 2025 | 990,099 (TC 908,348 + CI80 81,751) |
| 263KEN5000 | 2024 | 1,120,400 (TC 1,047,102 + CI80 73,298) |
| 235MAG5003 | 2024 | 577,529 (TC 539,747 + CI80 37,782) |

(B1 stores these with a trailing-minus sign convention; the magnitude is the assigned amount.)

### (2) Cost recovery — a SEPARATE downstream process
Once the project has disponible, the recovery happens via its own processes (BUDTYPE 4000):
**COSD** (cost distribution) and **CORV** (cost-recovery revenue), plus SEND/RECV transfers, and the
FI revenue postings (R1/JV docs, GL 7046013/7034011, see `project_cost_recovery_analysis.md`).
These MOVE against the assigned disponible — they do NOT create it.

Standard FM interfaces for the CR disponible:
| FM | Purpose | RFC-enabled? |
|----|---------|--------------|
| `FM_RIB_AVAILABLE_REVENUE` | Available revenue (the revenue side of RIB) | verify before calling |
| `FMAVC_READ_TOTALS_FOR_ADDRESS` | AVC consumable/consumed/available per address; key import: I_S_ADDRESS (FMKU_S_DIMPART = FUND/FUNDSCTR/CMMTITEM/FUNCAREA/GRANT_NBR/MEASURE/USERDIM/BUDGET_PD) | NOT RFC (call via RFC_ABAP_INSTALL_AND_RUN on D01/V01) |
| `FMAVC_GET_CD_ACTIVATION` | Check if AVC is active for a given control | NOT RFC |

Rule: **never INSERT FMAVCT directly** (hard rule from `feedback_avc_real_from_standard_not_handrolled`).
The disponible comes from the STANDARD, not hand-rolled arithmetic.

## Cover fund family — 633CRP9000 and 633CRP9003

Two "credit" cover funds back the CR coverage (see also claim #268 for 633CRP9003):

| Fund | Name | TYPE | BPJA WRTTP43 active through | Since 2019 |
|------|------|------|-----------------------------|-----------|
| **633CRP9000** | Cost Recovery Cover (TYPE 303) | 303 | Through 2018 (last year = 2008-2018) | ZERO entered budget |
| **633CRP9003** | Cost Recovery Policy (TYPE 304) | 304 | Through 2018 (years 2016-2018 only) | ZERO entered budget |

**Interpretation**: Since 2019, these cover funds have ZERO entered (BPGE/BPJA) budget. Current
availability is entirely revenue/cover-driven, not entered-budget-driven. The AVC "disponible"
for CR is fed by incoming R1 revenue postings (RIB), NOT by annual budget entries.

**D01 fund validity gap (fixed 2026-06-29):**
- 633CRP9003 DATBIS was 2018 in D01 vs 2027 in P01 → EXPIRED in D01
- Fix: FM_FUND_CHANGE_RFC (validity extension) + FM_FUND_CREATE_RFC (new fund creation)
- Session result: **14 CR funds created + 4 validity-extended in D01** (633CRP9200 left longer
  in D01 because SAP refuses shortening when budget exists)
- Reusable script: `Zagentexecution/tasks/2026_06_29_fm_model_sync/fund_family_sync.py`

## D01 disponible gap = 100% for CR test projects

| What | P01 (source) | D01 (gap) |
|------|-------------|-----------|
| FMBL B1 budget lines for CR test funds | Present (2024-2026) | **ZERO rows** |
| FMAVCT control rows (NAI + CR CIs) | Present | **ZERO rows** |
| AVC disponible for CR projects | Positive | **Zero → blocks CR postings** |

**Consequence**: D01 cannot currently process cost-recovery postings for these 5 test funds.
Any CRP testing in D01 will fail at AVC. This is a test-environment gap, not a P01 defect.

**How to fix D01**: Load the CR budget via the standard CR budget entry process:
- Tcode **FMBB** (manual budget entry) OR
- **`BAPI_0050_CREATE`** (budget entry document BAPI, object type 0050) OR
- **`Y_FMKU_0050_CREATE_WITH_COMMIT`** (UNESCO RFC wrapper over BAPI_0050_CREATE)

Replicate the **ENTR assignment** (process **ENTR**, BUDTYPE **3000**, VALTYPE **B1**, control fund center
**NAI**, commitment item per the fund's real P01 lines — usually **TC**+80, but some spread across detailed
CIs/PC, e.g. 537RAF4006). That gives the project its disponible. Do this FIRST; the recovery (COSD/CORV) is
a separate process, not needed to make the project spendable. **Do NOT use WRTTP43 overall budget.**

### VERIFIED BAPI_0050_CREATE recipe (executed P01→D01 2026-06-29)
HEADER: `FM_AREA='UNES', VERSION='000', DOCTYPE='2000', PROCESS='ENTR', DOCSTATE='1', DOCDATE=today`
— **omit PSTNG_DATE** (budgetary ledger not active → FMKU020 error if passed).
ITEM (per address): `ITEM_NUM (string '001'..), FISC_YEAR, BUDCAT='9F', BUDTYPE='3000', FUND, FUNDS_CTR='NAI',
CMMT_ITEM, FUNC_AREA, VALTYPE='B1', TRANS_CURR='USD', TOTAL_AMOUNT (positive magnitude), DISTKEY='1'`.
Then `BAPI_TRANSACTION_COMMIT(WAIT='X')` (BAPI does not auto-commit). TESTRUN='X' first.
Required-field gotchas hit in order: ITEM_NUM must be string; DOCSTATE='1' (else FMKU048); DISTKEY='1'
(else FMBAPI010); no PSTNG_DATE (else FMKU020).

**Result (5 CR test funds, docs 2000000250-254):** disponible now present in D01 — FMBL ENTR lines +
FMAVCT rows both non-zero for all 5. Total assigned 3,638,028 USD (567KEN2000 990,099 / 537RAF4006 450,000 /
218MAR2000 500,000 / 263KEN5000 1,120,400 / 235MAG5003 577,529). Script:
`Zagentexecution/tasks/2026_06_29_fm_model_sync/budget_assign_entr.py <TGT> <test|commit> [FUND] [YEAR]`
(idempotent — skips funds that already have ENTR for the given year in target).

### Budget is ANNUAL — each fiscal year needs its own disponible
Verified in D01: a 2025 ENTR creates FMAVCT only for RYEAR=2025; it does NOT make the fund spendable in
2026. In P01, FY2026 has **no fresh ENTR** — the 2026 disponible arrives via year-end **budget
carryforward** (residual 2025→2026). To make a fund spendable in a target year in D01, post the ENTR with
`FISC_YEAR=<year>` (the script's 4th arg forces the FY). **Done for 2026** (the active posting/test year):
docs 2000000255-259, same per-fund amounts/addresses → all 5 now have FMAVCT RYEAR=2026 disponible.
(For a faithful replica of P01's 2026 *residual* one would carry forward instead; the full-envelope ENTR
is the dev-enablement choice.)

This is DISTINCT from the ~98 regular funds with the ~212M D01 overall-budget gap (those use
WRTTP43 BPGE/BPJA, separate concern addressed in claim #283).

## Gotcha: SAP trailing-minus format

SAP amounts from RFC calls use **trailing minus**: `75695.67-` (not `-75695.67`).
Any parsing script must handle this — `float('75695.67-')` raises ValueError.
Correct: `s.strip(); if s.endswith('-'): val = -float(s[:-1]) else: val = float(s)`

## Evidence index

| Evidence | Source |
|----------|--------|
| FMAVCT rows (P01) showing NAI + CR CIs for 5 test funds | Live RFC read P01 2026-06-29 |
| FMBL B1 budget lines (P01) for CR test funds 2024-2026 | Live RFC read P01 2026-06-29 |
| BPGE/BPJA WRTTP43=0 for CR test funds | Gold DB + P01 RFC 2026-06-29 |
| FMAVCT = 0 rows in D01 for CR test funds | Live RFC read D01 2026-06-29 |
| 633CRP9003 DATBIS=2018 in D01 vs 2027 in P01 | FM_FUND_SHOW_RFC on both systems |
| 14+4 fund fix via FM_FUND_CREATE_RFC / FM_FUND_CHANGE_RFC | Zagentexecution/tasks/2026_06_29_fm_model_sync/fund_family_sync.py |
| FMAVC_READ_TOTALS_FOR_ADDRESS source (V01 live call) | avc_availability_model.md — 795.43 USD verified |

## Related knowledge
- `avc_availability_model.md` — general AVC model (formula, ledger 9H, AFMA derivation, FMAVC_* chain)
- `project_cost_recovery_analysis.md` — FI posting patterns (R1 docs, GL accounts, doc number ranges)
- `companions/cost_recovery_bor_model.html` — E2E BOR flow visual
- Claims: #268 (633CRP9003 pool), #269 (BOR E2E), #270 (Y_FMKU_0050_CREATE_WITH_COMMIT),
  #275 (FMBL TVAL period amounts), #277 (MuleSoft BAPI_0050 calls)
- Claims: #253-#259 (general AVC model), #283 (FM model P01-D01 gap — regular funds)
