---
name: SAP Fiori Extension Architecture Discovery
description: Protocol for discovering how any SAP standard Fiori app is protected (frontend UI5/BSP layer and backend OData layer) and identifying the valid extension points. Use this before modifying, extending, or cloning any Fiori app.
domains:
  functional: [*]
  module: [*]
  process: []
---

# SAP Fiori Extension Architecture Discovery Skill

## The Core Concept

Every standard SAP Fiori app has **two independent protection layers**:

1. **Frontend Layer** — The UI5/BSP app code is hash-protected by SAP's Content Security Policy. Direct modifications break the app.
2. **Backend Layer** — The OData MPC (schema) and DPC (logic) base classes contain a literal ABAP warning "NEVER MODIFY THIS CLASS." They are overwritten by SAP support packs.

Understanding this is **mandatory** before any Fiori extension or cloning work.

---

## Layer 1: Backend Extension Discovery Protocol

### Step 1 — Find the DPC/MPC Classes
```python
# RFC_READ_TABLE on TADIR
query_table("TADIR", options=f"OBJECT = 'CLAS' AND OBJ_NAME LIKE '%{APP_KEYWORD}%DPC%'", fields=["OBJ_NAME"])
```

### Step 2 — List All Extension Hook Methods
```python
# RFC_READ_TABLE on SEOCOMPO (class component list)
query_table("SEOCOMPO", options=f"CLSNAME = '{DPC_EXT_CLASS}'", fields=["CMPNAME", "CMPTYPE"])
# CMPTYPE=1 = method. Look for ENRICH_*, CHECK_*, EXECUTE_ACTION_* methods
```

### Step 3 — Check for Existing UNESCO Enhancements
```python
query_table("TADIR", options=f"OBJECT = 'ENHO' AND OBJ_NAME LIKE 'Z%{APP_KEYWORD}%'", fields=["OBJ_NAME"])
```

### Step 4 — Read What Was Overridden
```python
query_table("ENHOBJ", options=f"ENHNAME = '{ENHO_NAME}'", fields=["OBJ_TYPE", "OBJ_NAME"])
```

### Step 5 — Read the Method Source
```python
# Find all method includes first
query_table("TRDIR", options=f"NAME LIKE '{DPC_EXT_CLASS}CM0%'", fields=["NAME"])
# Then read each with RPY_PROGRAM_READ
read_report("{DPC_EXT_CLASS}CM001")
```

### Extension Options (in order of risk)
| Option | Mechanism | Risk |
|---|---|---|
| BAdI Implementation | Implement the app BAdI (`HCMFAB_B_*`) | 🟢 Low — upgrade-safe |
| Enhancement Spot (ENHO) | Override full method body | 🟡 Medium — conflicts possible |
| Full Clone (new SEGW) | New `Z*_SRV` + `ZCL_*_DPC_EXT` | 🟢 Low — fully independent |

---

## Layer 2: Frontend Extension Discovery Protocol

Standard SAP Fiori apps are BSP applications. The JS/XML code is namespace-protected.

### Step 1 — Identify the BSP App Name
```python
query_table("TADIR", options=f"OBJECT = 'WAPA' AND OBJ_NAME LIKE '%{APP_KEYWORD}%'", fields=["OBJ_NAME", "DEVCLASS"])
```

### Step 2 — Check If a Customer Adaptation Exists
Look for a Z/Y-prefix BSP or an adaptation project (a `manifest.json` with `sap.ui5.extends.component`).

### Step 3 — Read the manifest.json
Try to fetch from BSP URL or read from `O2PAGCON` table.
Look for:
- `sap.ui5.extends.component` → app wraps a standard app
- `sap.ui5.extends.extensions` → what views/controllers are overridden

### Step 4 — Identify Extension Points in Standard Views
Standard Fiori apps pre-declare `<ExtensionPoint name="..."/>` in XML views. These are the **only** safe injection points. If a section has none, you cannot inject without breaking the hash.

### VS Code Tooling for Frontend Extension
Use **SAP Fiori Tools** extension pack in VS Code:
- `@sap/generator-fiori` — create new Fiori apps from templates
- "Adaptation Project" generator — creates a wrapper over a standard app
  - Adds `manifest.json` with `extends.component`
  - Creates Extension Point fragments
  - Creates Controller Extension JS files

---

## Combined Architecture Pattern

```
Frontend (BSP/UI5 App)
  Standard BSP: <APP_NAME>     🔒 Hash-protected
    └── <ExtensionPoint>       ← Only safe injection point
  
  Adaptation Project (Z-layer) ✅ Your code
    └── manifest.json (extends standard)
    └── Custom XML fragments (injected at Extension Points)
    └── Controller extensions (JS overrides)
         │
         │ OData calls
         ▼
Backend (ABAP Gateway)
  MPC Base                     🔒 FROZEN / auto-generated
  MPC_EXT                      ✅ Add new OData properties/entities here
  DPC Base                     🔒 FROZEN
  DPC_EXT (ENRICH_* hooks)     ✅ Call BAdI → your code runs here
    └── BAdI Implementation    ← Safest custom code home
    └── OR: ENHO Enhancement   ← Override full methods (careful!)
```

---

## Key ABAP Warning to Know
Every SAP-generated MPC method contains:
```abap
*& !!!NEVER MODIFY THIS CLASS. IN CASE YOU WANT TO CHANGE THE MODEL
*&       DO THIS IN THE MODEL PROVIDER SUBCLASS!!!
```

## Key BAdI Pattern to Know
Every ENRICH_* method in DPC_EXT follows:
```abap
METHOD enrich_<entity>.
  IF <badi_var> IS INITIAL. RETURN. ENDIF.  " Skip if no custom impl
  CALL BADI <badi_var>->enrich_<entity>      " Delegate to custom code
    CHANGING cs_entity = entity.
ENDMETHOD.
```
