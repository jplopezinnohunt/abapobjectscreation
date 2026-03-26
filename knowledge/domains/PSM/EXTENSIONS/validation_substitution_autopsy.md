# UNESCO Custom Post-Processing & Validation Autopsy

This document captures the business rules that manipulate financial postings and enforce data integrity across FM, PS, and BI systems.

## 1. The FM Substitution Engine (Derivations)
UNESCO uses **`ZXFMDTU02`** to silently substitute (derive) Account Assignments when users leave them blank or to avoid data entry errors for sensitive GL accounts.

| Trigger GL Account | Target Fund | Target Fund Center | Business Rationale |
| :--- | :--- | :--- | :--- |
| `0007042011` | `630PLF9000` | `BOC` | Forces BOC administrative funds for specific reconciliation accounts. |
| `00060450*` | `GEF` | `UNESCO` | Global Environment (GEF) default for operational personnel costs. |
| `00070450*` | `GEF` | `UNESCO` | Global Environment (GEF) default for operational personnel costs. |
| `000704301*` | `645ASH9000` | `BFM` | BFM central management for internal chargeback accounts. |
| `0007043021` | `401NHF1091` | `HED` | Special "HED" sector mapping for WBS derived from Fund ID. |

---

## 2. The FM-PS Hard-Point Validation
The **"10-Digit Glue"** ensures that donor funds follow project structures mathematically.

*   **Rule Location**: [`ZXFMYU22`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMYU22_RPY.abap)
*   **Enforcement**: For all **Extra-Budgetary Funds (101-112)**, the first 10 characters of the WBS Element (POSID) **MUST** exactly match the Fund ID (GEBER).
*   **Impact**: Prevents a project from spending budget allocated to a different donor fund.

---

## 3. Period Control: The UNESCO FM Fiscal Gate
Standard SAP FI closing is *not* the final authority at UNESCO. 

*   **Table**: [`YFMXCHKP`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/knowledge/code_analysis_control_matrix.md)
*   **Logic**: If `ACTIV = 'X'` in this custom table for a given `BUKRS` and `GJAHR`, the FM system blocks all postings regardless of Open/Closed status in `OB52`.
*   **Current State (2025)**: All major institutes (`IBE`, `UNES`, `UIS`, `UIL`) have 2025 active in the gate, enforcing tight fiscal control for the new year.

---

## 4. The "God Mode" Bypass (YXUSER)
A single custom table, **`YXUSER`**, stores the list of users authorized to violate all of the above rules.

*   **Authority Type 'FM'**: Bypasses the 10-digit validation and period controls.
*   **Authority Type 'FRTL'**: Allows users to exceed the **2000 USD / 2% hardware tolerance cap** on Funds Reservations (FR).
*   **Active Users**: Currently, only **`HIPER`** holds the 'FM' master bypass key.

---

## 5. The Analytics Bridge (BI Enrichment)
While the backend enforces these rules, the BI system (**`ZXRSAU01`**) standardizes them for reporting.

1.  **USD Transformation**: BKPF-HWAE2 is prioritized as the reporting currency.
2.  **Date Alignment**: Recalculates "Real" posting dates to account for parking/release delays, ensuring the 10-digit PS correlations are historically accurate.
3.  **WBS Mapping**: Re-verifies the 10-digit link in BI-extracted data to maintain reporting continuity even if data was bypassed via `YXUSER`.
