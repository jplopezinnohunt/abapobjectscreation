---
name: Cost Recovery BOR (Budget Original Reservation) Posting Analysis 2025–2026
description: The budget-side (BOR) counterpart of the Personnel Cost Recovery analysis. ENTR/B1/9F original-budget documents on cost-recovery funds (incl. CRP pool 633CRP9003), MULESOFT vs human, mapped to the Y_FMKU_0050_CREATE_WITH_COMMIT feed.
type: project
created: 2026-06-26
source: P01 Gold DB (fmbh / fmbl / fmifiit_full / bkpf)
---

# Cost Recovery — BOR Posting Analysis (2025–2026)

## 0. Two sides of the same operation (clears the earlier confusion)
- **FI side (money)** — `cost_recovery_analysis.py`: 4,211 docs / 8,490 lines, all `VRGNG=RFBU`, `WRTTP=66` (actuals), `BLART` R1/JV. Charges staff (`FIPEX=11`) / consultants (`FIPEX=13`), credits recovery revenue. **No BOR here.**
- **Budget side (BOR)** — THIS analysis: the spending authority that lets those funds be charged. = FM **budget entry document**, `PROCESS_UI='ENTR'` (enter original budget), `VALTYPE='B1'`, `BUDCAT='9F'`. Stored in **`FMBH`** (header) + **`FMBL`** (lines).

There was **no prior standalone "Cost Recovery BOR" artifact** — this is the budget-side companion built now.

## 1. BOR documents ON cost-recovery funds — 2025 / 2026
Cost-recovery funds (from FI side): **389 (2025)**, **179 (2026)**. Of those, the ones that received an original-budget (BOR) document:

| Year | Creator | BOR docs | BOR lines | funds covered |
|---|---|--:|--:|--:|
| 2025 | **MULESOFT** | 149 | 149 | 68 |
| 2025 | human | 48 | 142 | 36 |
| 2026 | **MULESOFT** | 9 | 9 | 6 |
| 2026 | human | 7 | 18 | 4 |

- **MULESOFT docs = 1 line each** → atomic per-fund pushes from Core Planner (Salesforce) via `Y_FMKU_0050_CREATE_WITH_COMMIT`.
- **Human docs = multi-line** (~3 lines) → manual budget entry in FMBB with per-commitment-item splits.
- 2026 is low because the 2026-2027 biennium budget load is still ramping.

## 2. Whole-population BOR (ENTR) trend — when MuleSoft took over
`fmbh PROCESS_UI='ENTR'` by DOCYEAR / creator: MuleSoft BOR creation **starts 2023 (4), ramps 2024 (1,903), 2025 (1,923), 2026 (1,102), 2027 (624)**. Pre-2024 = 100% human. ⇒ the Salesforce→MuleSoft BOR feed went live ~2024.

## 3. Real BOR postings on cost-recovery funds (examples)
| Year | Creator | Doc | Ln | FiscYr | Fund | FundsCtr | CmmtItem | BudCat | ValType |
|---|---|---|---|---|---|---|---|---|---|
| 2025 | A_MULUGETA | 1000000626 | 1 | 2025 | **633CRP9003** (CRP pool) | ADM | TC | 9F | B1 |
| 2025 | AB_SALL | 1000019731 | 1–2 | 2025 | 549AFG5001 | FEJ | TC, 80 | 9F | B1 |
| 2026 | M_SARMENTO-G | 1000003016 | 1–3 | 2026 | 264GLO0312 | KGEM | **11, 13, 80** | 9F | B1 |
| 2026 | M_SARMENTO-G | 1000003009 | 3–5 | 2026 | 200TAJ0402 | TEC | 13, 50, 80 | 9F | B1 |
| 2026 | MULESOFT | 2000042546 | 1 | 2026 | 235RAF1001 | JUB | TC | 9F | B1 |

Commitment items `11`/`13` = the **same staff/consultant dimensions** the FI cost-recovery charges hit (`FIPEX 11/13`). The CRP pool `633CRP9003` gets its budget via BOR (A_MULUGETA).

## 4. ⚠️ Amounts — NOT in the Gold extract
Our `fmbl` extract has dimensions only (no `WTP01..WTP16`/`WTTRC`). **Per-document BOR amounts require a live `FMBL` read (SSO).** The structural/volume analysis above is complete from Gold; amounts are the one gap.

## 6. CORRECTION + the REAL CRP pattern (from live screenshots, verified in Gold)
The CRP cost-recovery budget is **NOT** `ENTR` (original budget). It is posted as **monthly budget SUPPLEMENTS** — `PROCESS_UI='SUPL'`. Verified on 20 real 2025 docs:

**Header (FMBH) — one document per month:**
| Field | Value |
|---|---|
| PROCESS_UI | **SUPL** (supplement / KBN0) |
| VERSION | 000 |
| TECHORG | **BWB** (Budgeting Workbench = FMBB, interactive) |
| DOCTYPE / LAYOUTVAR | 1000 / Z10000 |
| TEXT50 | `CRP month of <MON> <YYYY>` (+ `part N` when split) |
| DOCDATE / POSTDATE | month-end |
| CRTUSER | **G_KAPEKOVA / B_WANG (humans, budget office)** — NOT MuleSoft |

**Lines (FMBL) — one per office that recovered that month** (3→398 lines/doc, grows through the year):
| Field | Value |
|---|---|
| FUND | `633CRP****` (CRP pool family; `633CRP9003` = shared pool) — 179 distinct |
| FUNDSCTR | office code (87 distinct: YAO, BGK, NAI, HAR…) |
| CMMTITEM | **TC** (always) |
| FUNCAREA / GRANT_NBR | blank |
| BUDCAT / VALTYPE | **9F / B1** |
| PERIOD | **016** (annual budget bucket) |

**The amount source (self-financing loop, corroborated):** FI posts the actual recovery (`WRTTP=66`) on `633CRP*` funds each month; the budget office reads the recovered total per office and posts the matching SUPL supplement so each office gets spending authority = what it recovered. Monthly FI recovery tracks the supplement docs (period 012/Dec = 1,020 FI lines / 76 offices ↔ Dec doc = 398 lines). Real JAN-2025 per-line amounts (Σ `WRTTP=66 TRBTR` by fund+office): `633CRP9003/DHE = 35,648`, `/DAK = 31,125.78`, `/IDT = 30,772.87`…

## 7. HOW TO CREATE "the others" (the recipe)
For a target month M:
1. **Compute lines** — aggregate FI recovery `SUM(TRBTR)` where `WRTTP='66' AND FONDS LIKE '633CRP%' AND PERIO=M`, grouped by `(FONDS, FISTL)`. Each group → one budget line.
2. **Build header** — PROCESS=SUPL (supplement), VERSION=000, doc type 1000, TEXT50=`CRP month of <MON> <YYYY>`, DOC/POST date = month-end. Split into `part N` if line count is large (they do).
3. **Build each line** — FUND=`<633CRP fund>`, FUNDSCTR=`<office>`, CMMTITEM=`TC`, BUDCAT=`9F`, VALTYPE=`B1`, PERIOD=`016`, FISCYEAR=`<budget yr>`, AMOUNT=`<recovered total>`, CUR=USD.
4. **Post** — today: manual FMBB (TECHORG=BWB) by budget office. Programmatic: budget entry-document BAPI / `Y_FMKU_0050_CREATE_WITH_COMMIT` with **process = SUPPLEMENT**.

⚠️ **Amount caveat:** Gold `fmbl` has no amount column, so the supplement amount = FI-recovery hypothesis is corroborated by shape (offices + monthly growth) but **not byte-verified**. To confirm exactly: live `FMBL` read of `WTP016` and compare to FI `WRTTP=66` per fund/office/month.

## 5. Example payload to feed `Y_FMKU_0050_CREATE_WITH_COMMIT`
⚠️ The FM is a **custom MuleSoft wrapper; its interface is NOT extracted** (KU-2026-094). Below is the **business payload** from real doc `1000003016`, laid over the **standard FM Budget Entry Document (object 0050)** structure the wrapper near-certainly delegates to. Exact ABAP parameter names unverified until SE37/ADT read on D01.

```
HEADER:  PROCESS='ENTR'  VERSION='000'  BUDGET_CATEGORY='9F'  VALUE_TYPE='B1'
         FM_AREA='UNES'  DOC_DATE='20260212'  POSTING_DATE='20260212'  SENDER='MULESOFT'
ITEMS (one per commitment item):
  001  FY=2026  FUND='264GLO0312'  FUNDS_CTR='KGEM'  CMMT_ITEM='11'  AMOUNT=<staff>     CUR='USD'
  002  FY=2026  FUND='264GLO0312'  FUNDS_CTR='KGEM'  CMMT_ITEM='13'  AMOUNT=<consult>   CUR='USD'
  003  FY=2026  FUND='264GLO0312'  FUNDS_CTR='KGEM'  CMMT_ITEM='80'  AMOUNT=<other>     CUR='USD'
  # _WITH_COMMIT ⇒ wrapper runs BAPI_TRANSACTION_COMMIT internally
```

## Evidence
- Gold DB `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`: `fmbh`, `fmbl`, `fmifiit_full`, `bkpf`.
- Prior FI side: `knowledge/domains/PSM/project_cost_recovery_analysis.md`.
- BOR↔FM hypothesis: `brain_v2/agi/known_unknowns.json` KU-2026-094; claims #146/#154/#221.
