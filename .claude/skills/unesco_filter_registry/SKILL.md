---
name: UNESCO ABAP Filter Logic Registry
description: Living database of hardcoded and metadata-driven filter logic discovered inside UNESCO SAP programs and reports. Used to avoid redundant analysis and enable cross-program reuse of filter mappings.
domains:
  functional: [*]
  module: [*]
  process: [*]
---

# UNESCO ABAP Filter Logic Registry

## Purpose

Every SAP ABAP program or report embeds its own **filter logic** — hardcoded value lists, custom grouping tables, conditional mappings, and domain-specific constants that control how data is selected, bucketed, and displayed. These filters are rarely documented and are buried deep in class methods, includes, and custom configuration tables.

This skill serves as a **centralized, reusable registry** of all filter logic elements discovered during program analysis. When analyzing a new report or program, the agent **MUST**:

1. **Check this registry first** to see if a filter element has already been catalogued.
2. **Reuse existing entries** instead of re-documenting the same logic.
3. **Add new entries** whenever a previously unknown filter is discovered.
4. **Cross-reference** filters that appear in multiple programs to track shared logic.

---

## Protocol: When Analyzing a New SAP Program

When the agent is asked to analyze or reverse-engineer any ABAP program, report, class, or function module, it MUST follow this protocol:

### Step 1 — Scan for Filter Logic
Look for any of these patterns in the source code:
- `SELECT ... WHERE field IN (list)` or `WHERE field = 'value'`
- Internal table filtering with `LOOP AT ... WHERE`
- `CASE` / `IF` statements that branch on domain values (e.g., `WRTTP`, `BSTAT`, `VBTYP`, `BLART`)
- Reads from custom configuration/grouping tables (e.g., `YTFM_WRTTP_GR`, `ZTAB_*`)
- Constants or hardcoded value lists in class attributes or `DATA` declarations

### Step 1.5 — Analyze Selection Screen Filters (Business Scope)
> **Selection filters always tell us something important.** They define what the report is *built for*.

Before diving into code logic, examine every selection screen parameter and ask:
- What does this filter **restrict**? (organizational unit, fund type, document category, etc.)
- What is the **default value**? (defaults reveal the primary intended use case)
- Is it **mandatory**? (mandatory filters = core business constraints that must be preserved)
- What is **excluded** when this filter is applied? (understanding what's excluded reveals the report's scope boundaries)

### Step 2 — Check This Registry
Before documenting a filter, check if it already exists in the **Filter Catalog** below. If found:
- Note the cross-reference (which other programs use the same filter)
- Update the entry if the new program reveals additional values or special cases

### Step 3 — Register New Filters
Add any new filter logic to the appropriate section of the catalog using the standard entry format.

### Step 4 — Update the Source Analysis
In the program's technical analysis document (e.g., `knowledge/domains/xxx_technical_analysis.md`), reference this registry instead of duplicating filter details.

---

## Standard Entry Format

Each filter entry in the catalog MUST follow this format:

```
### [FILTER_ID] — [Human-readable name]
- **Field**: `ABAP_FIELD_NAME` (Table: `TABLE_NAME`)
- **Domain**: `DOMAIN_NAME` (if applicable)
- **Type**: Hardcoded | Config-Table-Driven | Mixed
- **Config Table**: `TABLE_NAME` (if Type is Config-Table-Driven)
- **Discovered In**: Program/Class where first found
- **Also Used In**: Other programs sharing this filter (updated over time)

| Value | Description | Group/Bucket | Notes |
| :---: | :--- | :--- | :--- |
| `XX` | ... | ... | ... |
```

---

## Filter Catalog

### WRTTP_FM — Funds Management Value Type Grouping
- **Field**: `RWRTTP` (Table: `FMIT`)
- **Domain**: `FM_WRTTP`
- **Type**: Config-Table-Driven
- **Config Table**: `YTFM_WRTTP_GR` (Custom UNESCO table that maps WRTTP values into reporting groups)
- **Discovered In**: `YCL_YFM1_BCS_BL` (Transaction `YFM1`, Program `YFM1_BCS_V3`)
- **Also Used In**: *(To be updated as more programs are analyzed)*

#### Group: Budget
Records with these WRTTP values are accumulated into the **Budget** bucket (column `HSL_BUDGET_INIT`).

| WRTTP | SAP Description | Notes |
| :---: | :--- | :--- |
| `01` | Original Budget (Plan) | Initial approved allocation for the fiscal year. |
| `02` | Budget Supplements | Additional allocations approved after the original. |
| `03` | Budget Returns | Budget given back. Sign is typically negative. |
| `04` | Budget Transfers (From) | Budget transferred out. Sign is typically negative. |
| `05` | Budget Transfers (To) | Budget received from another fund/item. |
| `06` | Released Budget | Portion released for spending. May differ from total if release strategy is active. |
| `11` | Current Budget | Net current budget after supplements, returns, and transfers. |
| `12` | Budget Carry-Forward | Unspent budget rolled over from the previous fiscal year. |
| `13` | Special Budget | Ad-hoc or exceptional allocations. |
| `14` | Budget Freeze | Temporarily frozen. Reduces availability without actual spending. |
| `61` | Budget Update (Debit) | ⚠️ Context-dependent. See Special Cases below. |
| `62` | Budget Update (Credit) | ⚠️ Context-dependent. Reverse of `61`. |
| `63` | Plan Commitment | Budget-level commitment planning (not an actual commitment). |
| `64` | Plan Actual | Budget-level actual planning figure (not actual spending). |
| `65` | Statistical Budget | Informational only. Not availability-controlled. |

#### Group: Actual (Expenditure)
Records with these WRTTP values are accumulated into the **Actual/Expenditure** bucket (column `HSL_EXPENDITURE`).

| WRTTP | SAP Description | Notes |
| :---: | :--- | :--- |
| `54` | Down Payments | Advance payments before invoice receipt. Treated as actual. |
| `57` | Actual (Invoice/Payment) | Core expenditure value — invoices posted and paid. |
| `58` | Revenue | Income posted. Sign typically negative (credit). |
| `66` | Statistical Actual | ⚠️ Context-dependent. See Special Cases below. |

#### Group: Commitment
Records with these WRTTP values are accumulated into the **Commitment** bucket (column `HSL_COMMITMENT`).

| WRTTP | SAP Description | Notes |
| :---: | :--- | :--- |
| `50` | Purchase Requisitions | Earliest stage of commitment. Internal request. |
| `51` | Purchase Orders | Legally binding vendor order. Strongest commitment form. |
| `52` | Reservations / Earmarked Funds | Pre-committed funds, not yet tied to procurement. Common in UN/Public Sector. |
| `53` | Funds Precommitments | Preliminary commitments (e.g., contract negotiations). |
| `55` | Travel Commitments | Funds committed for travel (UNESCO Travel Module). |

#### Special Cases
> [!WARNING]
> **WRTTP `61`, `62`, `66`** are context-dependent. Their group assignment is fully controlled by `YTFM_WRTTP_GR` configuration entries. The mapping above reflects the most common UNESCO setup. **Always verify `YTFM_WRTTP_GR` in the target system** before assuming a group assignment.

---

### FINCTYPE_FM — Fund Type / Budget Category (Business Scope Filter)
- **Field**: `FINCTYPE` (Table: `FMFINCODE`)
- **Domain**: `FM_FINCTYPE`
- **Type**: Master-Data-Driven (values come from Fund Master classification)
- **Selection Screen**: Used as a selection parameter to **scope the entire report** to a specific budget category
- **Discovered In**: `YFM1_BCS_V3` selection screen → `YCL_YFM1_BCS_BL->SET_SELECTION_VALUES` (Transaction `YFM1`)
- **Also Used In**: *(To be updated as more programs are analyzed)*

> [!IMPORTANT]
> **This is a business scope filter, not just a data filter.** It determines the *type of financial data* the report covers. Setting it to Regular Budget means the entire report — budget, expenditure, commitments, available balance — reflects only Regular Budget operations. It fundamentally changes the financial picture.

| Value | UNESCO Classification | Description | Notes |
| :---: | :--- | :--- | :--- |
| `RB` | **Regular Budget** | Core UNESCO budget funded by Member State assessed contributions. | ⭐ **Default/primary scope for YFM1.** This is the main target of the report. |
| `XB` | Extrabudgetary | Funds from voluntary contributions, donor agreements, and external funding sources. | Separate reporting track. Often has its own reports. |
| `TF` | Trust Funds | Earmarked funds held in trust for specific purposes or donors. | Typically managed under separate governance rules. |
| `SA` | Special Accounts | Funds for specific operational purposes (e.g., revolving funds, staff welfare). | Limited scope, specialized reporting. |
| `SC` | Self-Financed | Revenue-generating activities (e.g., publications, training fees). | May have different budget control rules. |
| *(others)* | *(Organization-specific)* | Additional fund types may exist in UNESCO's `FMFINCODE` configuration. | Verify via `SE16` on `FMFINCODE` with field `FINCTYPE`. |

#### How This Filter Works in the Data Flow
1. **Selection Screen**: User selects `FINCTYPE` (or it defaults to `RB`).
2. **`SET_SELECTION_VALUES`**: The range is stored in the class.
3. **`READ_DATA_FROM_DB`**: When querying `FMIT`, the program joins with `FMFINCODE` and applies the `FINCTYPE` filter to restrict which funds are included.
4. **Result**: Only `FMIT` records whose `RFONDS` belongs to a fund of the selected `FINCTYPE` in `FMFINCODE` are processed.

---

### SCENARIO_ASR — HCM Process Scenario Filter (Business Scope)
- **Field**: `SCENARIO` (Table: `T5ASRSCENARIOS`)
- **Type**: Config-Table-Driven
- **Config Table**: `T5ASRSCENARIOS`
- **Discovered In**: `ZHR_PROCESS_AND_FORMS_SRV` (DPC Class: `ZCL_ZHR_PROCESS_AND_FO_DPC_EXT`)
- **Purpose**: Restricts the OData service behavior to specific UNESCO HR processes (Birth, Marriage, etc.).

| Value | UNESCO HR Process | Logic Class | Workflow Task |
| :---: | :--- | :--- | :--- |
| `ZHR_BIRTH_CHILD` | **Birth of a Child** | `ZCL_HRFIORI_BIRTH_OF_A_CHILD` | `WS98100032` |
| `ZHR_MARRIAGE` | Marriage Status Change | `ZCL_CIVIL_STATUS` | `WS*` |
| `ZHR_ADOPTION` | Child Adoption | `ZCL_NEW_ADOPTION` | `WS*` |

---

### FMPS_LINK — The 10-Digit Glue (WBS to Fund)
- **Fields**: `PRPS-POSID(10)` vs `FMFINCODE-GEBER`
- **Type**: Structural (Hard Link)
- **Discovered In**: `ZXFMYU22` (FM Account Assignment Validation)
- **Purpose**: Enforces donor budget integrity by matching the project code to the fund code.
- **Rule**: If `PRPS-POSID(1) to (10)` <> `I_COBL-GEBER`, show error message `ZFI:009`.

---

### YXUSER_BYPASS — Global Validation Safety Valve
- **Field**: `UNAME` (Table: `YXUSER`)
- **Type**: Config-Table-Driven
- **XTYPE Value**: `FM` (Validation Bypass) | `FRTL` (FR Tolerance Bypass) | `BC` (U913 special-budget-code bypass)
- **Discovered In**: `ZXFMYU22`, `ZXFMCU17`; `BC` in `YRGGBS00::U913` (s111)
- **Logic**: If `SELECT SINGLE * FROM YXUSER WHERE XTYPE = '<type>' AND UNAME = SY-UNAME` finds a match, the gated validations are skipped.
- **Live content (P01, 2026-08-30, Gold DB `yxuser`)**: **1 row — `FM`/`HIPER`.** Nobody holds `FRTL` or `BC` today. [claim 649]

---

> Posting-perimeter context for the three entries below (validation architecture, live rule map,
> diagnosis method): see the unified `sap_validation_substitution` skill.

### YFMXCHK_XCHECK — Per-Fund Control Multiplexer (6 rules in one letter)
- **Fields**: `FIKRS` + `GEBER` + `XCHECK` (Table: `YFMXCHK`, 3,115 rows P01 — Gold DB `yfmxchk`)
- **Type**: Config-Table-Driven
- **Discovered In**: `ZXFMDTU02`, `ZXFMYU22`, `YFM_ACCTCHK`, `YRGGBS00::U913`
- **Full semantics**: [claim 648] · autopsy: `knowledge/domains/PSM/EXTENSIONS/validation_substitution_autopsy.md`

| XCHECK | Rows | Effect | Where |
| :---: | ---: | :--- | :--- |
| `Y` | 3,003 | **LIVE mass rule (11/2025, DBM/CF-simulation)**: fund blocked from FUTURE-year postings (`GJAHR > current` → hard E `ZFI 009`) | `ZXFMDTU02:320`, `YFM_ACCTCHK:112` |
| `T` | 38 | "Special budget codes" for FI validation `U913` — **path effectively dead** (GB931 step 002: `BUDAT≤31.12.2011` + check FALSE) [claim 649] | `YRGGBS00:961-987` |
| `F` | 35 | Fund EXEMPT from the rest of ZXFMDTU02 checks (D.Tal 02/2010) | `ZXFMDTU02:512` |
| `H` | 28 | Fund exempt from TBP1C/BPJA budget-structure check | `ZXFMYU22:184` |
| `D` | 9 | **Not funds**: `GEBER` holds an FR/PO NUMBER THRESHOLD (`FIKRS`='FR'/'PO' tags the doc type); blocks past-year commitments | `ZXFMDTU02:424-455` |
| `Z` | 2 | Tech fund fully blocked (BFM 03/2024) | `ZXFMDTU02:306` |

---

### YFMXCHKP_GATE — The UNESCO FM Fiscal Gate (currently OFF)
- **Fields**: `BUKRS` + `CHTYP` + `ACTIV` + `GJAHR` + `MONAT` (Table: `YFMXCHKP`, 11 rows P01 — Gold DB `yfmxchkp`)
- **Type**: Config-Table-Driven
- **Readers**: only `ZXFMDTU02` (CHTYP `FY`/`BB`/`BE`) and `YFM_ACCTCHK` (`FY`/`BB`) — bypass is auth object `Y_FMUECLO` field `YFLAG`, NOT YXUSER.
- **Live state (2026-08-30)**: all reader-backed variants INACTIVE (FY: UNES 2025/12 ACTIV blank; BE: UNES 2023/12 blank; BB: no row). The only 9 ACTIVE rows are `CHTYP='CM'` — **no reader in the extracted corpus**, and `MONAT=00` would block nothing anyway. [claim 650]

#### ASR Conditional Logic (Pattern: Age Restriction)
Discovered in `ZCL_HRFIORI_BIRTH_OF_A_CHILD`:
- **Variable**: `lv_year` (derived from `I0021_FGBDT`)
- **Condition**: `IF lv_year >= 18`
- **Effect**: Makes field `I0021_EDUAT` mandatory (`ui_attribute = 'M'`).
- **Reuse Pattern**: UNESCO uses this pattern to enforce education attendance checks in all dependent-related Fiori apps.

---

### BLART_FI — FI Document Type Filter (Payment & Posting)
- **Field**: `BLART` (Table: `BKPF`)
- **Domain**: `BLART`
- **Type**: Config-Table-Driven (T003 defines types)
- **Discovered In**: payment_process_mining.py, fi_domain_agent queries
- **Also Used In**: All BKPF queries, P2P process mining, payment E2E event log

#### Group: Invoice Documents (Input to Payment)
| BLART | Description | Number Range | Payment Check |
|-------|-------------|-------------|---------------|
| `KR` | Supplier Invoices FI | 64 | Payment Validation Workflow |
| `RE` | Invoice-Gross (MM) | 51 | Rule: MM only |
| `KA` | Supplier Advances | 62 | Payment Validation Workflow |
| `KG` | Credit Memo (Vendor) | 17 | Payment Validation Workflow |
| `KT` | Temp Supplier Payments | 70 | Payment Validation Workflow |
| `ER` | Expense Reimbursement | 69 | Payment Validation Workflow |
| `IT` | Invoice IC Transfer | 95 | Payment Validation Workflow |
| `MF` | MBF Postings | 81 | Payment Validation Workflow |
| `PS` | Prosper Requests | 44 | Payment Validation Workflow |

#### Group: Payment Documents (Output of F110/F111)
| BLART | Description | Number Range | Notes |
|-------|-------------|-------------|-------|
| `ZP` | Payment Posting | 20 | F110/F111 output — auto-posted |
| `CP` | Payments Cheque | 34 | Cheque payments (ICTP + field offices) |
| `KZ` | Payment to Vendor | 14 | Manual payment (F-53) |

#### Group: Auto-Blocked at Posting (Not Payable)
| BLART | Description | Number Range |
|-------|-------------|-------------|
| `AB` | Accounting Document | 01 |
| `AC` | Asset Accounting | 73 |
| `FO` | Fixed Order | 40 |
| `JV` | Joint Venture | 92 |
| `KG` | Credit Memo (used also as blocked for some configs) | 17 |
| `SN` | Supernumerary Postings | 65 | **Exception: NOT auto-blocked — audit gap** |
| `RE` | Invoice Gross (MM) | 51 | Blocked; post via MM only |
| `ZP` | Payment | 20 | Blocked; post via payment program only |

**Key rule**: `BLART IN ('KR','RE','KA','KG')` = invoice filter for process mining. `BLART IN ('ZP','KZ','CP')` = payment filter.

---

### BCM_RULE — BCM Payment Grouping Rule Filter
- **Field**: Rule identifier (Table: `BNK_BATCH_HEADER.BCM_RULE` or equivalent)
- **Type**: Config-Table-Driven (BCM customizing)
- **Discovered In**: BNK_BATCH_HEADER analysis (Session #021), Blueprint BCM
- **Priority**: Lower number = higher priority (evaluated first)

| Rule | Priority | Origin | Key Criteria | Dual Control |
|------|----------|--------|-------------|--------------|
| `UNES_AP_IK` | 0 | FI-AP/FI-AR | Method L + InstrKey B1 | Yes |
| `UNES_AR_BP` | 1 | FI-AR | Customer 600000-699999 | Yes |
| `UNES_TR_TR` | 1 | TR-CM-BT | Treasury transfers | **No (1 validation)** |
| `UNES_AP_EX` | 2 | FI-AP/FI-AR-PR | Embargo country list | Yes |
| `UNES_AP_ST` | 3 | FI-AP/FI-AR | Catch-all standard AP | Yes |
| `PAYROLL` | 1 (STEPS) | HR-PY | All payroll runs | Yes (PAY+TRS) |

**Additional grouping**: All rules also group by `VALUT` (value date) → one payment file per execution date.

---

## Filter Catalog (Pending Discovery)

As new programs are analyzed, new filter entries will be added following the Standard Entry Format.

Known pending: BSTAT (document status), VBTYP (SD category), FRGCO (release codes for payments)

---

> [!TIP]
> **Cross-Program Insight**: When the same filter (e.g., `WRTTP_FM`) appears in multiple programs, compare the value lists. Discrepancies reveal program-specific business rules or legacy exceptions that must be documented.
