---
name: UNESCO ABAP Filter Logic Registry
description: Living database of hardcoded and metadata-driven filter logic discovered inside UNESCO SAP programs and reports. Used to avoid redundant analysis and enable cross-program reuse of filter mappings.
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
- **XTYPE Value**: `FM` (Validation Bypass) | `FRTL` (Hardware Tolerance Bypass)
- **Discovered In**: `ZXFMYU22`, `ZXFMCU17`
- **Logic**: If `SELECT SINGLE * FROM YXUSER WHERE XTYPE = 'FM' AND UNAME = SY-UNAME` finds a match, **ALL** validations in the include are skipped.

#### ASR Conditional Logic (Pattern: Age Restriction)
Discovered in `ZCL_HRFIORI_BIRTH_OF_A_CHILD`:
- **Variable**: `lv_year` (derived from `I0021_FGBDT`)
- **Condition**: `IF lv_year >= 18`
- **Effect**: Makes field `I0021_EDUAT` mandatory (`ui_attribute = 'M'`).
- **Reuse Pattern**: UNESCO uses this pattern to enforce education attendance checks in all dependent-related Fiori apps.

---

## Filter Catalog (Placeholders)

As new programs are analyzed, new filter entries will be added below following the Standard Entry Format.

<!-- 
### BSTAT_XX — Document Status Filter
- **Field**: `BSTAT` (Table: `BKPF`)
- **Discovered In**: (pending)

### VBTYP_XX — SD Document Category
- **Field**: `VBTYP` (Table: `VBAK`)
- **Discovered In**: (pending)

### BLART_XX — Document Type Filter
- **Field**: `BLART` (Table: `BKPF`)
- **Discovered In**: (pending)
-->

---

> [!TIP]
> **Cross-Program Insight**: When the same filter (e.g., `WRTTP_FM`) appears in multiple programs, compare the value lists. Discrepancies reveal program-specific business rules or legacy exceptions that must be documented.
