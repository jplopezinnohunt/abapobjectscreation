# Technical Autopsy: BI/BW Data Extraction (PSM-FM)

## Overview
- **Includes**: [`ZXRSAU01`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXRSAU01_RPY.abap), [`ZXRSAU02`](file:///c:/Users/jp_lopez/projects/abapobjectscreation/ZXRSAU02_RPY.abap)
- **Enhancement**: `RSR00001` (BW Service: Customer-Specific Exit)
- **Primary Objective**: Enriches SAP's standard FM and Project System (PS) data sources with UNESCO-specific master data (Donors, Sectors, Regions) and calculated analytical dates.

## 1. Enrichment Logic: FM Actuals & Commitments
*   **Data Sources**: `0PU_IS_PS_32` (Actuals), `0PU_IS_PS_31` (Commitments).
*   **Analytical Posting Date (`ZZPOST_DATE`)**:
    - **Logic**: For procurement transactions (PO, PR, Contracts), the system doesn't just use the FI posting date. It traverses the relationship from `FMIFIIT` back to the source document (`EKKO`, `EKET`, `KBLP`) to find the **true budget consumption date**.
    - **Purpose**: Essential for mid-biennium vs. end-of-biennium financial reporting.
*   **USD Currency Conversion (`ZZDMBE2`)**:
    - Calculated specifically for UNESCO's USD reporting. It retrieves secondary ledger amounts from `BSEG` to ensure accuracy.

## 2. Enrichment Logic: Fund & Project Master Data
*   **Data Source**: `0FUND_PU_ATTR` (Fund Attributes).
*   **Project Linkage**: Converts the Fund ID (`FINCODE`) to a Project System internal ID (`PSPNR`) using standard conversion exits (`CONVERSION_EXIT_KONPD_INPUT`).
*   **Support Cost Calculation (`SCPERC`)**:
    - **Method**: Instead of reading a static field, the exit dynamically calculates the average Support Cost rate.
    - **Formula**: It reads budget allocations from `BPGE` for specific categories (`Personnel`, `Operational`, `Travel`) and weights the PSC rates from `PRPS-YYE_POUR_xx` accordingly.
*   **Status History**: Tracks the project through its lifecycle (REL, TECO, CLSD) by reading table `JCDS` to capture exactly when each status change occurred.

## 3. Organizational Attributes (UNESCO Custom Fields)
*   **Region/Sector/Donor**: Pulled directly from `PRPS-USR00` (Region), `PRPS-USR01` (Country), `PRPS-USR02` (Sector).
*   **Country Mapping**: Uses a custom table `YBW_PSCOUNTRY` to map internal UNESCO country codes to standard ISO codes.
*   **Workflow Metadata**: Pulls `ZZIBF` and `ZZOUTPUT` from `YTFM_FUND_C5`.

## 4. Key Components
| Include | Purpose |
| :--- | :--- |
| `ZXRSAU01` | Enrichment of Transactional Data (Actuals, Commitments, Budget). |
| `ZXRSAU02` | Enrichment of Master Data (Fund, Project, Position, Employee). |
| `ZXRSA_UTILS` | (Presumed) Helper library for currency and date calculations. |
