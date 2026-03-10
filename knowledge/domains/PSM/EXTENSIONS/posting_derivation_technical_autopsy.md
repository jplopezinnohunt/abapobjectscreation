# Posting Derivation Technical Autopsy (UNESCO)

## 1. Executive Summary
This document details the **Posting Derivation** logic within UNESCO's SAP Fund Management (FM-BCS) implementation. This logic governs the determination of **FM Account Assignments** (Commitment Item, Fund Center, Fund, Functional Area) during the initial financial posting (FI, CO, MM, etc.). This is distinct from **AVC Derivation**, which groups these account assignments into Availability Control objects.

## 2. Global Derivation Strategy (`APPL: FM / SUBCLASS: 01`)
The posting derivation is managed via the **`FMOA`** strategy in the FM application environment. Key configurations identified in P01:

| Component | Technical Name | Functional Purpose |
| :--- | :--- | :--- |
| **Strategy ID** | `FMOA` | Main strategy for FM Object Assignment. |
| **Environment** | `SAP` (Active) / `ICTP DERIVATION` / `UBO DERIVATION` | Business-unit specific derivation contexts. |
| **Callback Rep** | `RFMOADERIVE` | Standard SAP callback program for orchestration. |

## 3. Active Rule Sets (Rule-Based Mappings)
Within the **`SAP`** environment (the primary Posting Derivation flow), the following custom rule tables have been identified as the "Truth Tables" for account assignments:

### 3.1 G/L to Commitment Item & Fund Center (`FMDERIVE002`)
*   **Purpose**: Maps Financial Accounting (FI) entries to FM.
*   **Source Fields**: Company Code (`UNES`), G/L Account, Cost Center.
*   **Target Fields**: Commitment Item, Fund Center.
*   **Observations**: Many entries map G/L ranges directly to Commitment Items (e.g., `18111000`).

### 3.2 G/L to Fund & Fund Center (`FMDERIVE003`)
*   **Purpose**: Strategic determination of Funds based on accounting entries.
*   **Source Fields**: Company Code (`UNES`), G/L Account.
*   **Target Fields**: Fund (e.g., `GEF`, `PFF`, `OPF`, `MBF`).

### 3.3 UNESCO Dynamic Output Mapping (`FMFMOAP013500062`)
*   **Purpose**: Likely related to Results-Based Budgeting (RBB) output codes.
*   **Target Fields**: Map 10-character codes (UNESCO Outputs) to FM account assignments.

## 4. Derived FM Account Assignments (High-Level Mapping)
The system prioritizes assignments in the following sequence:
1.  **G/L Mapping**: Direct mapping from `SKB1` (Infotype fields).
2.  **Cost Object Mapping**: Derivation from CO objects (Cost Centers, WBS Elements) using the `RFFMMDAC_*` callbacks.
3.  **Custom Rule Overrides**: Application of table-based rules (`FMDERIVE*`).

## 5. Hardcoded Custom Logic (`ZXFMDTU02`)
The system utilizes the standard user-exit **`FMDERIVE`** (Include `ZXFMDTU02`) to implement complex, non-tabular logic. Key hardcoded rules discovered:

### 5.1 Force-Derivation by G/L Account
*   **Fund Center Override**: G/L `0007042011` is hardcoded to derive Fund Center **`BOC`** and Fund **`630PLF9000`**.
*   **UNESCO Global Pool**: G/Ls `0006045011`, `0007045011`, and `0006045014` are forced to Fund Center **`UNESCO`** and Fund **`GEF`**.
*   **Asset Management**: Transaction `OASV` triggers a specific mapping where the Fund is derived from the Business Area (`GSBER`).

### 5.2 Business Area Logic (UNESCO Specific)
*   The exit contains logic to automatically set Business Area **`PFF`** for Fund Types **`114`** and **`115`** by querying the Fund Master (`FMFINCODE`).

### 5.3 Posting Blocks & Validations
*   **WBS Element Restrictions**: For the `PFF` fund, the system explicitly blocks the use of WBS Elements and mandates a Cost Center.
*   **Historical Fund Blocks**: Postings on funds starting with `149*` are blocked for Procurement transactions (`ME21`, `ME51`, etc.).
*   **Period Control**: Transaction-specific period checks are implemented for ALV/FI transactions using custom tables `YFMXCHKP` and `YXTCODE`.

## 6. Relationships Between Master Data & Postings
| Source Object | Target FM Object | Mechanism |
| :--- | :--- | :--- |
| **G/L Account** | Commitment Item | `FMMD` strategy / `SKB1-FIPOS` |
| **Cost Center** | Fund Center | `FMOA` Step 0001 (`FMDT_READ_MD_ACCOUNT_COMPANY`) |
| **WBS Element** | Fund Center | `FMOA` / `RFFMMDAC_WBS_FC` |
| **Asset** | Account Assignment | `FMOA` / Step 0003 (`FMDT_READ_MD_ASSET`) |

## 6. Access Control & Authorization Logic
The system implements a **Dynamic Authorization Filter** for maintaining derivation rules. This is orchestrated in `YFM_COCKPIT`:

*   **Logic**: The system reads the user's roles (`BAPI_USER_GET_DETAIL`) and looks for the pattern: `YS:FM:M:EXB_DERIV_RULE___:[####]`.
*   **Impact**: The 4-character suffix (e.g., `UBO `, `HEQ `) is passed as a filter to the standard derivation tools (`FMAVCDERIAOR`, etc.) via BDC.
*   **Security Principle**: This restricts "Regional Admins" or "Business Unit Admins" to editing ONLY the derivation rules belonging to their specific organizational area.

## 7. Extension Point: `YCL_FM_SPENDING_AUTH`
While primarily related to AVC, this class and the table `YTFM_FUND_CPL` (Complementary Fund) provide a "Super-Hierarchy" used in UNESCO's reporting (YFM1, YFM3). It ensures that even if a Fund is derived via posting, it is correctly categorized within the UNESCO appropriation line hierarchy.

---
*Created by: Antigravity*
*Date: 2026-03-09*
