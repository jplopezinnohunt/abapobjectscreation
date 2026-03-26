---
name: SAP Enhancement Extraction & Classification
description: >
  Protocol for extracting source code from SAP Composite Enhancement
  Implementations (SE20 / ENHO object type) via Python RFC, and classifying
  them by functional domain and Fiori service impact. Use this skill whenever
  you need to reverse-engineer or knowledge-capture SAP enhancements.
---

# SAP Enhancement Extraction & Classification

## What Is a Composite Enhancement Implementation?

In SAP, a **Composite Enhancement** (`ENHC` in TADIR) groups one or more
**Enhancement Implementations** (`ENHO`). You discover them via:
- **SE20** → "Find Enhancements" → "Composite Enhancement Implementation"
- **TADIR** query: `OBJECT = 'ENHC'` or `OBJECT = 'ENHO'`, `OBJ_NAME LIKE 'Z%'`

Each composite can contain:
- **BAdI implementations** (most common for HCM Fiori)
- **Classic user exits** (screen exits, function exits)
- **Source code plug-ins** (ABAP class-based)

> [!CAUTION]
> **NEVER** try to read enhancement source via `REPOSRC` or `SXS_ATTR` —
> both tables are authorization-restricted in UNESCO SAP (TABLE_WITHOUT_DATA error).
> Use `TRDIR` + `SIW_RFC_READ_REPORT` instead. `ENHLOG` is also not always populated.

---

## Prerequisites

- Python RFC connection working (`sap_utils.get_sap_connection()`)
- `SIW_RFC_READ_REPORT` RFC accessible (confirmed for D01)
- `RFC_READ_TABLE` on `TADIR` and `TRDIR` (confirmed working)
- Target script: `Zagentexecution/mcp-backend-server-python/extract_composite_enhancements.py`

---

## Domain Classification Schema

Use this taxonomy when tagging each enhancement:

| Domain Code | Meaning | Typical Enhancement Prefix |
|---|---|---|
| `HCM / ASR` | HR Adaptive Services / Forms | `ZHR_`, `ZENH_PA`, `YHR_` |
| `HCM / Personal Data` | Infotype 0002, My Personal Data Fiori | `ZHR_PERS_DATA`, `YCL_HRPA_UI_CONVERT_0002` |
| `HCM / Fiori (generic)` | Any direct Fiori HCM extension | `ZHR_FIORI_*`, `YHR_ENH_HRFIORI` |
| `HCM / Payroll` | Payroll logic, PRAA, UNJSPF | `ZHR_PENSION`, `Y_ENH_PRAA`, `YHR_ENH_HUNCPFM0` |
| `HCM / Workflow` | PA Workflow, Internship, ASR WF | `ZENH_PAWF_*` |
| `HCM / SuccessFactors` | SF/BTP integration | `ZCOMP_ENH_SF` |
| `HCM / HR Core` | HR Core+ integration | `YHR_ENH_HRCOREPLUS` |
| `FI / General` | FI substitutions, exits | `YFI_ENH`, `ZFIX_*` |
| `FI / AP` | Accounts Payable, payment runs | `YCEI_FI_SUPPLIERS_PAYMENT`, `YENH_RFBIBL00` |
| `FI / DMEE` | Payment medium / file format | `YENH_FI_DMEE` |
| `PSM / FM` | Funds Management | `YFM_ENH` |
| `PS / Project System` | Project & WBS | `YPS_ENH` |
| `RE-FX` | Real Estate Flexible | `ZENH_REFX_*` |
| `Procurement / PO` | MM purchasing | `Z_ICTP_PO_*` |
| `Output / Documents` | DOCX, Smart Forms | `ZENH_DOCX` |

---

## Fiori Impact Decision Rules

Mark `fiori_impact = True` when **any** of these apply:

1. Enhancement name contains `FIORI`, `HCMFAB`, `ASR`, `HRPA_UI`
2. Description mentions "Fiori", "app", "family member", "personal data"
3. Known BAdI interfaces: `HCMFAB_B_*`, `HCMFAB_B_COMMON`
4. Infotype UI conversion: `YCL_HRPA_UI_CONVERT_*` (affects PA26/PA30 Fiori)
5. SuccessFactors integration (`ZCOMP_ENH_SF`) — may affect OData/BTP iFlow

---

## Step-by-Step Extraction Protocol

### Step 1: Discover via TADIR

```python
# Find all custom composite enhancements
rows = safe_rfc_read_table(conn, "TADIR",
    ["OBJECT = 'ENHC'", " AND OBJ_NAME LIKE 'Z%'"],
    fields=["OBJECT", "OBJ_NAME", "DEVCLASS", "AUTHOR", "CREATED_ON"]
)
# Also run for Y* prefix
```

Expected output: list of `ENHC` entries with package (`DEVCLASS`).

### Step 2: Resolve Includes via TRDIR

```python
# Composite enhancements do NOT always have a REPOSRC entry.
# Scan TRDIR with the enhancement name as prefix:
trdir = safe_rfc_read_table(conn, "TRDIR",
    [f"NAME LIKE '{enh_name}%'"],
    fields=["NAME", "SUBC"]
)
# SUBC = 'I' → Include (the actual source)
# SUBC = 'K' → Class pool (has CM-includes for methods)
```

### Step 3: Read Source via SIW_RFC_READ_REPORT

```python
result = conn.call("SIW_RFC_READ_REPORT", I_NAME=include_name)
lines  = result.get("E_TAB_CODE", [])
# Save to: extracted_code/ENHO/<ENH_NAME>/<include>.abap
```

> [!IMPORTANT]
> For **class-based implementations** (SUBC='K'), the methods are in
> CM-includes named `<CLASSNAME>=========CM001`, `CM002`, etc.
> Always scan TRDIR for `NAME LIKE '<CLASS>%CM%'` and read each one.

### Step 4: Classify and Save

Each enhancement gets its own folder under `extracted_code/ENHO/<NAME>/`
with `_summary.json` containing:

```json
{
  "name": "ZHR_PERS_DATA",
  "domain": "HCM / Personal Data",
  "fiori_impact": true,
  "notes": "HCMFAB_B_MYPERSONALDATA BAdI area",
  "extracted_objects": ["ZHR_PERS_DATA_ENHO.abap", "ZCL_...CM001.abap"]
}
```

### Step 5: Run the Master Script

```powershell
# Extract all 27 known enhancements
.\venv\Scripts\python.exe extract_composite_enhancements.py

# Extract a single one
.\venv\Scripts\python.exe extract_composite_enhancements.py ZHR_PENSION
```

Output folder: `extracted_code/ENHO/`
Master report: `extracted_code/ENHO/_COMPOSITE_ENH_REPORT.json`

---

## Known Accessible SAP Tables for Enhancement Discovery

| Table | Description | Access |
|---|---|---|
| `TADIR` | Repository object directory | OK via RFC_READ_TABLE |
| `TRDIR` | ABAP program directory (includes) | OK via RFC_READ_TABLE |
| `ENHLOG` | Enhancement implementation log | Partially available |
| `REPOSRC` | Source code repository | **BLOCKED** (TABLE_WITHOUT_DATA) |
| `SXS_ATTR` | Enhancement spot attributes | **BLOCKED** (TABLE_WITHOUT_DATA) |
| `SXS_ENHLOG` | Spot enhancement log | **NOT AVAILABLE** (TABLE_NOT_AVAILABLE) |

---

## You Know It Worked When

- `extracted_code/ENHO/<NAME>/` folder exists with at least one `.abap` file
- `_summary.json` is present for each enhancement
- `_COMPOSITE_ENH_REPORT.json` shows a Fiori impact table
- Console prints `[DONE] N objects saved` for each enhancement

---

## Known Failures & Self-Healing

| Error | Cause | Fix |
|---|---|---|
| `TABLE_WITHOUT_DATA` on `REPOSRC` | Auth restricted | Use `TRDIR` + `SIW_RFC_READ_REPORT` instead |
| `TABLE_NOT_AVAILABLE` on `SXS_ENHLOG` | Table not exposed via RFC | Skip; use `ENHLOG` only |
| `UnicodeEncodeError: charmap` on Windows | Non-ASCII chars in `print()` | Use ASCII-only output; set `PYTHONIOENCODING=utf-8` or use `-> ` instead of `→` |
| `SIW_RFC_READ_REPORT` returns empty | Enhancement has no program include | Try reading CLAS CP include: `<CLASSNAME>=========CP` |
| TRDIR returns 0 rows | Enhancement is purely metadata (no ABAP) | Log as "metadata-only"; check ENHLOG for implementation class |
| `ENHC` not found in TADIR | Name is wrong or it's an `ENHO` type | Try both `ENHC` and `ENHO` object types in TADIR |

---

## Full UNESCO Enhancement Inventory (27 Known, as of 2026-03)

### Fiori-Impacting (High Priority)

| Enhancement | Domain | Fiori Service / App |
|---|---|---|
| `ZCL_HCMFAB_ASR_PROCESS` | HCM / ASR | Fiori HR Forms (ASR scenarios) |
| `ZCOMP_ENH_SF` | HCM / SuccessFactors | OData / BTP iFlow |
| `ZENH_PAWF_INT_AGREE` | HCM / Workflow | Fiori Inbox / ASR |
| `ZHR_FIORI_0021` | HCM / Fiori | HCMFAB_MYFAMILYMEMBERS OData |
| `ZHR_PENSION` | HCM / Payroll | Fiori Personal Data / Payroll |
| `ZHR_PERS_DATA` | HCM / Personal Data | HCMFAB_B_MYPERSONALDATA BAdI |
| `YCL_HRPA_UI_CONVERT_0002_UN` | HCM / PA | Fiori My Personal Data (IT0002) |
| `YCL_HRPA_UI_CONVERT_0006_UN` | HCM / PA | Fiori Address Management (IT0006) |
| `YENH_INFOTYPE` | HCM / Infotypes | Fiori PA apps (PA26/PA30) |
| `YHR_ENH_HRCOREPLUS` | HCM / HR Core | HR Foundation Fiori apps |
| `YHR_ENH_HRFIORI` | HCM / Fiori | Generic Fiori HCM enhancement |

### Non-Fiori (Backend / Classic)

| Enhancement | Domain | Notes |
|---|---|---|
| `Z_ICTP_PO_HOSTGUEST` | Procurement / PO | Host/guest PO printing |
| `ZENH_DOCX` | Output | DOCX generation |
| `ZENH_REFX_CONTRACT_UNESCO` | RE-FX | Contract validations |
| `ZFIX_EXCHANGERATE` | FI / Treasury | Exchange rate fix |
| `ZHR_SPAU_PA` | HCM / PA | SPAU screen adaptation |
| `ZHR_SPAU_PY_CPSIT_PGM_001` | HCM / Payroll | SPAU upgrade adjustment |
| `Y_ENH_PRAA` | HCM / Payroll | Payment run |
| `YCEI_FI_SUPPLIERS_PAYMENT` | FI / AP | Supplier payments |
| `YENH_FI_DMEE` | FI / DMEE | Payment medium |
| `YENH_HRFPM_ARCH` | HCM / Archiving | HR Forms archiving |
| `YENH_RFBIBL00` | FI / Batch Input | FI batch posting |
| `YFI_ENH` | FI / General | FI extensions |
| `YFI_ENH_ARGA` | FI / AR | Gov. AR logic |
| `YFM_ENH` | PSM / FM | Funds Management |
| `YHR_ENH_HUNCPFM0` | HCM / UNJSPF | Pension fund interface |
| `YPS_ENH` | PS | Project System |

---

## Adding New Enhancements

When a new enhancement is found in SE20, add it to the `ENHANCEMENTS` list in
`extract_composite_enhancements.py` following the schema:

```python
{
    "name":        "ZXXX_MY_ENH",
    "description": "Short description from SE20",
    "domain":      "HCM / Fiori",    # Use domain table above
    "fiori_impact": True,             # Apply decision rules above
    "notes":       "What BAdI/service this touches"
},
```

Then re-run the master script. The `_COMPOSITE_ENH_REPORT.json` is cumulative.
