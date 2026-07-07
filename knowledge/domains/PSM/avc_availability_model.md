---
name: AVC Availability Model (PSM-FM BCS) — how UNESCO's Availability Control actually computes "available"
description: The end-to-end, code+config+data-VERIFIED model of how SAP BCS Availability Control (AVC) calculates the available amount at posting time in UNESCO's system. Standard read FM, the exact formula, ledger 9H=PAYMENT budget, the control-object derivation/rollup (ABADR/AFMA), the totals model, activity groups, why hand-rolling fails, the create-BAPI landscape, and the dual-AVC→Fund-AVC decision input. Built 2026-06-23 by reading the live ABAP source + config + Gold DB.
type: project
---

# AVC Availability Model (PSM-FM BCS)

> **Verified, not guessed.** Every claim below was confirmed by reading the live ABAP source on P01
> (via RFC `RPY_FUNCTIONMODULE_READ_NEW`), the AVC customizing tables, and the Gold DB data. This is the
> source of truth for the UNESCO Fund-AVC model and the input to the **dual-AVC → Fund-AVC** decision.

## TL;DR — the formula
```
available_for_posting = consumable_budget − consumed_amount
  consumable_budget = consumable_bdgt_posted + consumable_bdgt_reserved      (RRCTY=1 Plan)
  consumed_amount   = consumed_amount_posted + consumed_amount_reserved      (RRCTY=0 Actual)
```
Computed BY THE SYSTEM **per derived control object** (NOT per posting leaf), per fiscal year, on the active
AVC ledger. UNESCO's active ledger = **9H = PAYMENT budget** (BUDCAT 9F). Tolerance profile 9HZ00001 = 100% Error
→ the check **blocks the posting** if the new consumption would exceed available.

## The standard function chain (read from source)
| FM / method | Role | RFC? |
|---|---|---|
| **`FMAVC_READ_TOTALS_FOR_ADDRESS`** | the read API — orchestrates derive→read→compute; returns `E_T_TOTALS` (consumable/consumed/available). Formula at src lines 565-590. IMPORT: I_FM_AREA, I_GJAHR, I_S_ADDRESS, **I_FLG_PAYMENT_BUDGET** / I_FLG_COMMITMENT_BUDGET. | ❌ not remote |
| `FMAVC_DERI_CONTROL_OBJECT` | derive the Availability Control Object (ACO) address from the posting address | ❌ |
| `FMAVC_CALL_DERIVATION_ACO` → **`ABADR_DERIVE_CHARACTERISTICS`** | the actual rollup engine — runs strategy **AFMA** + address rule, also resolves cover groups (FMCE_*) and grant | ❌ |
| `FMAVC_SELECT_ANNUAL_TOTALS_ACO` → `FMAVC_SELECT_DB_TOTALS_ACO` | read the ACO totals, split by **ARCTY** (consumable/consumed) × **WFSTATE** (posted/reserved/earmarked) | ❌ |
| AVC posting check (fn-group FMAVC) | compares new consumption vs available+tolerance; blocks | ❌ |

**None of the FMAVC_* FMs are RFC-enabled** (TFDIR FMODE='' for all 94). To call them externally: a temp ABAP
snippet via `RFC_ABAP_INSTALL_AND_RUN` (works on V01/D01 — has S_DEVELOP; **not P01** = prod), or run report
**`FMAVCR`**. Verified live on V01: `447RAF2040/NAI/80/2018` → consumable 44,972.75 − consumed 44,177.32 =
**available 795.43 USD** (matches the formula exactly).

## The AVC ledger (config: `fmavcldgract` / `fmavcldgratt` / `fmavcbudfil*`)
- **9H = PAYMENT-budget AVC ledger** (corrected — earlier assumed "commitment"). Evidence: 9H filters
  VALTYPE=B1, BUDTYPE 3000/4000; UNESCO budgets in **BUDCAT '9F' = Payment Budget**; standard delivers
  9H=payment / 9I=commitment. UNESCO runs **payment-budget availability control only** (9I not active).
- Active on all 9 institutes (LDGRSTAT='S', from FY2001, IGNORE_REVENUES='X').
- Address rule (ABADRENV) = **`9HZ00001`**; tolerance profile **9HZ00001** (ICTP=ZIT1, UBO=Z002, UIL=Z001,
  rest=Z000); strategy = **AFMA**.

## The totals model (table `FMAVCT`)
Real structure on P01: **77 fields**. Natural key (11 fields): RCLNT, RLDNR, RRCTY, RVERS, RYEAR, ROBJNR, COBJNR, SOBJNR, RTCUR, DRCRK, RPMAX. Amounts come in 3 currency families each with carry-forward + 16 period buckets: TSL** (transaction), HSL** (FM-area/local), KSL** (group/CO). Annual figure per row = HSLVT + sum(HSL01..HSL16).

**How to compute available = budget − consumed (VERIFIED 2026-06-30):**
Budget address and its consumption are **separate rows** sharing the consuming-object `COBJNR` but differing in `ROBJNR` (the responsible/budget object), grouped by cover group `RCVRGRP_9`.
Example: 9H/2026/UNES/3110111021/PAX/TC — ROBJNR ...3870146 (budget) = 4,500.00 USD; ROBJNR ...3870148 (consumption) = 547.65 USD → **available = 3,952.35 USD** (claims #341, #342).
- **RRCTY** = secondary discriminator (0=Actual=consumed, 1=Plan=consumable) — coexists with the ROBJNR split.
- **WFSTATE_9** = posted (P) / reserved (R) / earmarked.

**ALLOCTYPE_9** (data element BUAVC_ALLOCTYPE) domain values: KBFC=Hard commitments/allocated budget; SEEC/SENC/REEC/RENC/RSEC/RSNC = sender/receiver cover-element legs; ACCG/RIBC/ARIB/RIBL = cover-group legs. For **all 9 UNESCO FM areas KBFC is the only value in use** (FY2024-2026, 48,543 rows — claim #343). UNESCO does not use cover-element or cover-group splitting.

- Consumption enters via the **activity groups `FMAVCATGR`** (map consumption WRTTP→AVC amount type:
  50 PO→20, 51 PR→30, 54 invoice→40, 60/61/04 actuals→40/60, reservations etc.).
- ~~Our Gold-DB `fmavct_*` slice kept only ALLOCTYPE_9=KBFC+HSL01~~ — **REMEDIATED 2026-06-30**: Gold DB `fmavct_2024/2025/2026` now carry 38 columns including the full natural key. The prior 7-col schema collided ~36% of rows and could not resolve budget vs consumed (claims #341).

## Gold DB / Pipeline — AVC layer (added 2026-06-30)
The AVC layer is now part of the **recurring PSM_FM gold pipeline** (claim #344):
- **Script**: `scripts/extraction/psm_avc_refresh.py` (subcommands: `config` | `totals` | `all`)
- **Registered**: `brain_v2/gold_table_registry.json` — `source=curated`, `delta=external` (skipped by `gold_refresh.py`; owned exclusively by `psm_avc_refresh.py`)
- **Config tables** (BUAVCTOLASS, FMAVCATGR_001/002, FMAVCBUDFILTB/H, FMAVCLDGRACT/ATT/GAT): cadence = weekly
- **Totals** (FMAVCT): cadence = same as `fmifiit_full` (daily-ish; balances drift daily)
- **Freshness**: queryable via `_gold_sync_log` and `_config_frontier_manifest` (`extracted_at 2026-06-30`)
- **Drift evidence**: BUAVCTOLASS grew 34→36 rows between 2026-06-19 and 2026-06-30 in 11 days — confirms staleness risk was real.

**RFC extraction pattern** for wide FMAVCT (claim #345): field-split into <=7-col groups, RFC-read each group, recombine by row position with an equal-rowcount guard. Necessary because RFC_READ_TABLE has a 512-byte WA buffer. P01 rejects ROWSKIPS (claim #244) — use ROWCOUNT=0 partitioned by RFIKRS x RYEAR.

## The AVC CONTROL KEY — 4 dimensions, Fund Area is mandatory (user correction 2026-07-07)
The AVC control object is addressed by a **4-part key**, NOT 3-part:

> **Fund Area (`RFIKRS`) + Fund (`RFUND`) + Fund Center (`RFUNDSCTR`) + Commitment Item (`RCMMTITEM`)** — per fiscal year (`RYEAR`), ledger **9H**, version, and record type `RRCTY` (budget vs actual).

**Fund Area is NOT optional.** Fund Center and Commitment Item codes (`TC`, `11`, `13`, `VNI`, `HEQ`, `NAI`, …)
are **area-scoped and repeat across the 9 FM areas** (UNES, ICTP, IIEP, UBO, MGIE, UIS, UIL, ICBA, IBE — see
`fmavct_2026` row counts). Any AVC read, group-by, or join that keys on `(Fund, FundCenter, CmmtItem)` **without
`FIKRS` collides control objects across institutes** — this is the root of the "no considera las claves de control"
problems. The standard read API `FMAVC_READ_TOTALS_FOR_ADDRESS` **requires `I_FM_AREA` (FIKRS)** as a mandatory
import for exactly this reason. Gold DB `fmavct_2024/2025/2026` carry all four as explicit columns
(`RFIKRS/RFUND/RFUNDSCTR/RCMMTITEM`); always include `RFIKRS` in any query key. Refines claims #338 (3-part
framing) and #341 (technical storage key hides the address inside `ROBJNR`). Claim #346.

## The control-object DERIVATION / ROLLUP — the crux (PROVEN from config + data)
The ACO is a **derived, rolled-up address**, NOT the posting leaf. Strategy **AFMA / 9HZ00001** has **8 steps**
(`tabadrs`/`tabadrsf`):
1. **MOVE "CI: General Rule OPF - AVC on TC"** → sets ACO commitment item to **`TC`** (regular-budget/OPF funds
   collapse all commitment items to a single control node TC) + maps specific control funds.
2. TABLE "Determine if EXBO Fund from Budget Profile".
3. MOVE "General Rule EXBO - AVC @ Line Item Level" (extrabudgetary/donor funds control at detailed CI).
4-6. MOVE CDO→`10'`, CDCE→`11`, CDSP→`13` (specific CI remaps).
7. DRULE "Exception Rule EXBO - AVC @ TC or PC or NPC".
8. MOVE "TC for FTypes 093, 094, 095".

**Data proof (FMAVCT control objects, UNES 2026):** CI distribution = **TC 6,550** (dominant) · 80 1,015 · 20 500 ·
PC 407 · 50 296 · 30 212 · 40 188 · 11 153 · 10' 132 · 13 65 · NPC 11. TC dominates because OPF funds roll up to it.
**Two regimes:** OPF (regular budget) → AVC aggregated at **TC**; EXBO (donor/XB) → AVC at **line-item** (detailed CI), with exceptions to TC/PC/NPC.

## Why hand-rolling AVC FAILS (don't re-derive — rule)
- `committed_vs_available_detector.py` re-derived AVC as `fmifiit WRTTP 66−54 + bpja−coep−cooi` → nonsense
  (fund 196EAR4042 pool −$12.9M vs reality positive). REFUTED.
- A leaf-level `Σ(Plan)−Σ(Actual)` per (fund,fundsctr,cmmtitem) gives 23.7% spurious negatives (MBF −$110M)
  because (a) the control object is **derived/rolled-up** (budget at TC, consumption rolls up), and (b) signs/
  distribution (budget distributed negative-at-parent). **Only the standard FM / FMAVCR gives the exact figure.**
  See [[feedback_avc_real_from_standard_not_handrolled]] (sibling of GL-from-GLT0-not-BSIS).

## The reservation / create-BAPI landscape
- A funds reservation (earmarked funds, FMX1) consumes budget → triggers AVC. But the **standard create is NOT
  RFC**: `FI_PSO_EARMARKED_FUNDS2_CREATE` (FMODE='', has **I_CHECK** check-only mode) → `FMFR_CREATE_FROM_DATA`
  (**I_FLG_CHECKONLY** runs AVC without COMMIT) — clean, data-driven, NOT batch input.
- `BAPI_0050_CREATE` = **budget entry document** (not earmarked funds; PROCESS ENTR/SUPL). `BAPI_0051_GET_TOTALS`
  = budget totals only (no consumption). Neither gives AVC available.
- ⚠️ **UNESCO's `ZRFC_FRESERVATION_CREATE` does BDC of FMX1** (`CALL TRANSACTION USING t_bdc`, OKCODEs /00/EPF23/=SAVE)
  — a fragile batch-input anti-pattern where the clean standard API (`FMFR_CREATE_FROM_DATA` + checkonly) exists.
  Improvement candidate (G_CONFORMANCE / H_IMPROVE): replace the BDC with `FMFR_CREATE_FROM_DATA`.

## Dual AVC → Fund AVC (the strategic decision input)
- UNESCO currently runs **dual availability control**: PS budget AVC (project/WBS) + FM/Fund AVC (this model, 9H).
- The FM/Fund side is fully mapped here. To evaluate dropping PS AVC, the remaining work is the **PS-side config**
  (PS budget profile + PS availability control) and the overlap analysis — NOT yet done (don't guess).
- The **control-object derivation (AFMA, OPF→TC) is the heart of Fund AVC** — any redesign must preserve or
  consciously change that aggregation level.

## Evidence index
ABAP source (RPY read on P01): FMAVC_READ_TOTALS_FOR_ADDRESS (836 ln), FMAVC_DERI_CONTROL_OBJECT (963 ln),
FMAVC_CALL_DERIVATION_ACO (1024 ln), FMAVC_SELECT_ANNUAL_TOTALS_ACO (271 ln), FMFR_CREATE_FROM_DATA, ZRFC_FRESERVATION_CREATE.
Config: fmavcldgract/att, fmavcbudfil*, fmavcatgr, tabadrs/tabadrsf (AFMA/9HZ00001, 8 steps).
Data (2026-06-30 refresh): fmavct_2024 (18,838 rows / 38 cols, 9 FM areas), fmavct_2025 (16,112), fmavct_2026 (13,593), fmioi, bpja.
Pipeline: scripts/extraction/psm_avc_refresh.py; registry: brain_v2/gold_table_registry.json PSM_FM curated section.
Live read: FMAVC_READ_TOTALS_FOR_ADDRESS on V01 (795.43 USD); ROBJNR-pair example: 9H/2026/UNES/3110111021/PAX/TC = 4500-547.65=3952.35 USD (P01, 2026-06-30).
Claims: #341 (77 fields / 38-col schema), #342 (ROBJNR-pair available formula), #343 (ALLOCTYPE_9 values + KBFC-only for all 9 areas), #344 (AVC layer pipeline registration), #345 (field-split RFC pattern).
