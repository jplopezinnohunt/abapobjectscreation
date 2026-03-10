# HCM Data Flow & Authorization Connectivity (UNESCO)

This document maps the journey of a data field from the Fiori UI down to the SAP database and the security gates (Authorization Objects) it must pass.

## 1. Field Connectivity Map: PA0002 (Personal Data)

| Fiori UI Field (OData Property) | UI Structure Field (HCMT_BSP_PA_XX_R0002) | DB Field (PA0002) | Description |
| :--- | :--- | :--- | :--- |
| `LastName` | `LAST_NAME` | `NACHN` | Last Name |
| `FirstName` | `FIRST_NAME` | `VORNA` | First Name |
| `BirthDate` | `BIRTH_DATE` | `GBDAT` | Date of Birth |
| `Nationality` | `NATIONALITY` | `NATIO` | Nationality |
| `Gender` | `GENDER` | `GESCH` | Gender Key |
| `ZZREGGR` (UNESCO) | `ZZREGGR` | `ZZREGGR` | Regional Group (Custom) |

---

## 2. Authorization Layer (Security Gates)

The Fiori app uses the **HR decoupled framework (HRPA)**. All data access is intercepted by the **HR Master Data Authorization Manager**.

### Core Authorization Objects checked:
| Object | Field | Value / Usage | Purpose |
| :--- | :--- | :--- | :--- |
| **`P_ORGIN`** | `INFTY` | `0002`, `0021`, etc | Primary check for Infotype access. |
| | `SUBTY` | `*` | Subtype access (e.g., Child vs Spouse). |
| | `AUTHC` | `R` (Read) / `W` (Write) | Operation type. |
| **`P_PERNR`** | `AUTHC` | `R` / `W` | **The "Self-Service" Gate**: Controls if the user can view/edit their own personnel number. Essential for ESS apps. |
| | `PSIGN` | `I` (Include) | |
| **`P_ORGXX`** | | | Extended organizational check (if active at UNESCO). |

---

## 3. The Connectivity Path (End-to-End)

```mermaid
graph TD
    subgraph UI["🖥️ Fiori Frontend"]
        V_LAST["UI Field: Last Name"]
    end

    subgraph GATEWAY["🌐 OData / Gateway Layer"]
        ODATA["Z_HCMFAB_MYPERSONALDATA_SRV"]
        DPC["ZCL_Z_HCMFAB_MYPERSONA_DPC_EXT"]
    end

    subgraph ENGINE["🔷 HCM Feeder Engine"]
        FEEDER["CL_HCMFAB_PERSINFO_FEEDER"]
        UI_STRUC["Structure: HCMT_BSP_PA_XX_R0002"]
        CONV["Conv Class: CL_HRPA_UI_CONVERT_0002_XX"]
    end

    subgraph HRPA["🛡️ Decoupled Logic & Security"]
        XSS_ADP["CL_HRPA_PERNR_INFTY_XSS"]
        BL_LOGIC["CL_HRPA_MASTERDATA_BL"]
        AUTH_MAN["HR Master Data Auth Manager"]
        P_ORGIN["Auth: P_ORGIN / P_PERNR"]
    end

    subgraph DB["💾 Database Layer"]
        PA0002["Table: PA0002\n(Field: NACHN)"]
    end

    %% Flow
    V_LAST -->|Property: LastName| ODATA
    ODATA --> DPC
    DPC --> FEEDER
    FEEDER -->|Maps to| UI_STRUC
    UI_STRUC -->|Internal Mapping| CONV
    CONV -->|Requests via| XSS_ADP
    XSS_ADP -->|Triggers| BL_LOGIC
    BL_LOGIC -->|Security Check| AUTH_MAN
    AUTH_MAN -.->|Validates| P_ORGIN
    BL_LOGIC -->|Final Fetch| PA0002
```

---

## 4. The Workflow Staging Path (Parked Action)

For actions involving a "Parking" step (e.g., Offboarding, Birth of Child):

| Stage | Action / Event | Target Table | Logic |
| :--- | :--- | :--- | :--- |
| **Draft** | User Clicks 'Save' | `ASR Buffer` / `zthrfiori_hreq` | Values are stored as XML or Staging rows. No PA update. |
| **Workflow** | `SAP_WAPI_START_WORKFLOW` | `SWWWIHEAD` | The Request ID links UI context to the workitem. |
| **Posting** | Final Approval | `HR_INFOTYPE_OPERATION` | Data is finally moved to `PA0021` or `PA0016`. |

---

## 5. How to Debug Field Discrepancies
1. **Wrong Value?**: Check the Conversion Class `CL_HRPA_UI_CONVERT_XXXX_XX`. The mapping logic from `PAxxxx` to `HCMT_BSP_...` lives there (methods `OUTPUT_CONVERSION` and `INPUT_CONVERSION`).
2. **Missing Field?**: Verify table **`T588M`** (Screen Modification). If it's hidden there for the UNESCO molga, the Feeder will hide it in Fiori.
3. **No Authorization?**: Use transaction `SU53` in the backend immediately after the Fiori error. Look specifically for failed `P_ORGIN` or `P_PERNR` checks with the user's PERNR.
4. **Audit Gap?**: Use `ZCL_HRFIORI_PF_COMMON` methods to retrieve the original staged JSON/XML if the final posting failed.
