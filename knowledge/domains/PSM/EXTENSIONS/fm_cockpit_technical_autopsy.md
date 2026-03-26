# Technical Autopsy: Fund Management Cockpit (YFM_COCKPIT)

## Overview
- **Program**: `YFM_COCKPIT`
- **Module Pool**: `YFM_COCKPIT` (Package `YB`)
- **Main Developer**: Franck Guillou (2019)
- **Business Use**: Simplifies the manual effort required to set up and update "Budget Availability Control (AVC) Rules" for specific FM Funds.

## 1. Process Flow & Next-Step Logic
The cockpit is a wizard-like interface that orchestrates three main SAP standard transactions:
1.  **Step 1: Create/Update Rule** (`FMAVCDERIAOR`)
    - Automates the entry into the Derivation Tool for Availability Control.
    - Uses Batch Input (`BDC_TAB`) triggered by `BATCH_FILTER` to pre-select environment `9HZ00001` and the user's authorized FM Area.
2.  **Step 2: Reinitialize Budget** (`FMAVCREINIT`)
    - After changing derivation rules (e.g., adding a new grant to an AVC object), the system requires re-initialization of AVC total tables to reflect the new mapping.
3.  **Step 3: Verify Budget Structure** (`FMAVCR02`)
    - Final validation step to ensure the availability control is functioning as expected for the modified range.

## 2. Security & FM Area Filtering
The cockpit implements a custom security filter based on the user's SAP Role:
*   **Logic**: It searches for a role matching `YS:FM:M:EXB_DERIV_RULE___:xxxx`.
*   **Mapping**: The last 4 characters of the role name are harvested as the `LV_FMAREA`.
*   **Impact**: Users can only manage rules within the FM areas assigned to their specific security profile.

## 3. Reference Documentation (Guide)
*   **BDS Object**: `ZDOC_HELP_GUIDE` (Class type `OT`, Object Key `HELP_GUIDE`)
*   **Function**: Method `OPEN_DOC` retrieves a PDF guide from the SAP Business Document Service (BDS) and opens it in Microsoft Word/Acrobat using the custom class `YCL_SAP_TO_WORD`.

## 4. Key Components
| Include | Purpose |
| :--- | :--- |
| `YFM_COCKPITTOP` | Global data, BDC structures, and transaction codes. |
| `YFM_COCKPITF01` | Core logic for `POPUP_TO_CONFIRM` and `BATCH_FILTER`. |
| `YFM_COCKPITI01` | PAI logic for user interactions. |
| `YFM_COCKPITO01` | PBO logic for screen rendering. |
