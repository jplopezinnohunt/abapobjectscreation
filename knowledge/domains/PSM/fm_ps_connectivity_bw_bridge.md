# UNESCO SAP FM-PS Connectivity & BW Bridge

This document details the "System Glue" that ensures data integrity between Fund Management (FM), the Project System (PS), and the Business Warehouse (BW).

## 1. The FM-PS "10-Digit" Hard Link
The fundamental rule connecting Funds to WBS Elements is enforced in the **FM Account Assignment Validation** logic.

*   **Logic File**: [`ZXFMYU22`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMYU22_RPY.abap)
*   **Target Scope**: Fund Types **101 to 112** (Extra-Budgetary / Donor Projects).
*   **The Rule**: The **first 10 characters** of the WBS element (PRPS-POSID) **MUST** exactly match the Fund ID (FMFINCODE-GEBER).

### Technical Enforcement
```abap
362:   CLEAR PRPS.
363:   SELECT SINGLE *
364:         FROM PRPS
365:         WHERE PSPNR = I_COBL-PS_PSP_PNR.
366:   IF PRPS-POSID(10) <> I_COBL-GEBER.
367:     MESSAGE ID 'ZFI' TYPE 'E' NUMBER '009'
368:            WITH 'Incorrect WBS-element or Fund!' ' Please check.'.
369:   ENDIF.
```

---

## 2. The BI/BW Reporting Bridge
While the 10-digit rule ensures transactional integrity, the **BW Extraction Logic** manipulates these fields to provide accurate financial metrics (Converted to USD).

*   **Extraction Logic**: [`ZXRSAU01`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/BI_REPORTING/ZXRSAU01_RPY.abap)
*   **Master Data Logic**: [`ZXRSAU02`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/extracted_code/UNESCO_CUSTOM_LOGIC/BI_REPORTING/ZXRSAU02_RPY.abap)

### Key BW Manipulations:
1.  **USD Normalization**: Forces conversion to `BKPF-HWAE2` (Secondary Local Currency) for UNESCO's global reports.
2.  **Date Alignment**: Recalculates the "Real" Posting Date to ensure fiscal periods in BW match the actual transaction time, regardless of when the document was parked or posted.
3.  **Project State Enrichment**: Attaches custom attributes from `ZXRSAU02` to the Project Hierarchy, enabling BI users to filter reports by UNESCO-specific metadata (Sectors, Divisions) not present in standard SAP.

---

## 3. Governance & Bypass (The Control Key)
The integrity of this entire model depends on the **`YXUSER`** table.

*   **Exception Type**: `XTYPE = 'FM'` or `XTYPE = 'FRTL'`.
*   **Impact**: Users listed in this table bypass the 10-digit validation and the hardware tolerance caps (2%).
*   **Audit Risk**: An unauthorized entry in `YXUSER` can break the FM-PS link for any project, allowing budget to be misaligned between the Project and its associated Fund.
