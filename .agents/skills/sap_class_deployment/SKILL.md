---
name: SAP Class Deployment
description: >
  ABAP class creation and method deployment via RFC. Covers VSEOCLASS structure-based
  class creation, 6 CCIMP (implementation include) writing strategies, method deployment,
  and post-deployment verification. Proven on CRP OData service (ZCL_Z_CRP_SRV_DPC_EXT).
---

# SAP Class Deployment

## Purpose

Create and deploy ABAP classes and methods programmatically via RFC, without using SE24 GUI.
This skill covers the full lifecycle: create class definition, write method implementations,
activate, and verify.

## NEVER Do This

1. NEVER create a class without checking TADIR first — `check_class_exists.py` or `check_tadir.py`
2. NEVER write CCIMP without understanding the class component structure — read CP first via `read_cp.py`
3. NEVER skip activation after writing — inactive code is invisible to runtime
4. NEVER deploy to P01 (production) — deployment is D01 only
5. NEVER assume transport — always check/create transport request before writes

## Script Location

```
Zagentexecution/mcp-backend-server-python/
  create_class_rfc.py              # Class creation via SEOC_CREATE_COMPLETE
  create_class_vseoclass.py        # Class creation with VSEOCLASS structure
  direct_create_complete.py        # Direct class creation (simplified)
  final_class_creation.py          # Battle-tested creation flow
  force_class_definition.py        # Force class definition via RFC
  force_definition_rfc.py          # Force definition alternative
  deploy_crp_classes.py            # CRP-specific class deployment
  deploy_crp_to_sap.py             # CRP domain service deployment
  deploy_final.py                  # Final deployment orchestrator
  deploy_methods_rfc.py            # Method-level deployment
  insert_and_activate.py           # Insert code + activate
  write_ccimp_abap_bridge.py       # CCIMP via ABAP bridge pattern
  write_ccimp_c255.py              # CCIMP with C255 character handling
  write_ccimp_correct.py           # CCIMP correct-format writer
  write_ccimp_insert_report.py     # CCIMP via INSERT_REPORT RFC
  write_ccimp_like.py              # CCIMP via LIKE pattern
  write_ccimp_siw.py               # CCIMP via SIW_RFC_WRITE_REPORT
  write_method_cm.py               # Method CM (include) writer
  write_via_bridge.py              # Write via ABAP bridge
  activate_and_deploy.py           # Activation wrapper
```

## Class Creation Flow

### Step 1: Verify Class Doesn't Exist
```python
# check_class_exists.py / check_seo_existence.py
conn.call("RFC_READ_TABLE",
    QUERY_TABLE="VSEOCLASS",
    FIELDS=[{"FIELDNAME":"CLSNAME"}],
    OPTIONS=[{"TEXT":"CLSNAME = 'ZCL_MY_CLASS'"}])
```

### Step 2: Create Class Definition
```python
# Key RFC: SEO_CLASS_CREATE_COMPLETE or SEOC_CREATE_COMPLETE
conn.call("SEO_CLASS_CREATE_COMPLETE",
    DEVCLASS="ZPACKAGE",
    OVERWRITE="X",
    VERSION=1,
    CLASS={
        "CLSNAME": "ZCL_MY_CLASS",
        "VERSION": "1",
        "LANGU": "E",
        "DESCRIPT": "My custom class",
        "CATEGORY": "00",   # General
        "EXPOSURE": "2",    # Public
        "STATE": "1",       # Implemented
        "CLSFINAL": "",     # Not final
        "CLSABSTRCT": "",   # Not abstract
        "UNICODE": "X"
    })
```

### Step 3: Write Method Implementation (CCIMP)

CCIMP = Class Implementation Include. This is where method code lives.

**6 Writing Strategies** (in order of reliability):

| Strategy | File | When to Use |
|----------|------|-------------|
| SIW_RFC_WRITE_REPORT | `write_ccimp_siw.py` | Most reliable for full includes |
| INSERT_REPORT | `write_ccimp_insert_report.py` | Standard SAP report insertion |
| ABAP Bridge | `write_ccimp_abap_bridge.py` | When direct write fails |
| C255 | `write_ccimp_c255.py` | Wide lines (>72 chars) |
| Correct format | `write_ccimp_correct.py` | Standard-width ABAP |
| LIKE pattern | `write_ccimp_like.py` | Copy from template |

### Step 4: Activate
```python
# Via ADT REST API (most reliable)
# POST /sap/bc/adt/activation
# Or via RFC: RS_WORKING_OBJECTS_ACTIVATE
```

### Step 5: Verify Deployment
```python
# verify_final_deployment.py / deep_verify.py
# Checks: TADIR entry, TRDIR entry, REPOSRC source, method includes exist
```

## VSEOCLASS Structure Fields

| Field | Description | Typical Value |
|-------|-------------|---------------|
| CLSNAME | Class name | ZCL_MY_CLASS |
| VERSION | Version | 1 (active) |
| LANGU | Language | E |
| DESCRIPT | Description | Free text |
| CATEGORY | Category | 00 (general) |
| EXPOSURE | Visibility | 2 (public) |
| STATE | State | 1 (implemented) |
| CLSFINAL | Final | X or blank |
| CLSABSTRCT | Abstract | X or blank |
| UNICODE | Unicode | X |

## Class Component Structure

SAP classes have typed includes (components):

| Include Type | Suffix | Contains |
|-------------|--------|----------|
| Public section | `=====CP` | Public declarations |
| Protected section | `=====CO` | Protected declarations |
| Private section | `=====CI` | Private declarations |
| Implementation | `=====CCIMP` | Method implementations |
| Macros | `=====CCMAC` | Macro definitions |
| Local types | `=====CCDEF` | Local type definitions |
| Test classes | `=====CCAU` | ABAP Unit tests |

## CRP Deployment (Proven Pattern)

The CRP (Certificate Request & Provisioning) OData service was the first full deployment:

```
ZCL_Z_CRP_SRV_DPC_EXT  (DPC Extension class)
  - Overrides: ENTITYSET_GET_ENTITYSET, ENTITY_GET_ENTITY
  - Transport: D01K9B0EWT
  - Package: ZCRP
```

## Verification Scripts

| Script | What It Checks |
|--------|----------------|
| `verify_code_pasted.py` | Source code matches expected content |
| `verify_final_deployment.py` | TADIR + TRDIR + REPOSRC + method includes |
| `verify_final_deployment_v3.py` | Enhanced verification with diff |
| `deep_verify.py` | Full deep verification (all components) |
| `final_verify.py` / `final_verify_v2.py` | Final pass verification |

## Companion Inspection Tools

| Script | Purpose |
|--------|---------|
| `check_class_exists.py` | VSEOCLASS lookup |
| `check_seo_existence.py` | SEO repository check |
| `check_cp_trdir.py` | Class public section in TRDIR |
| `check_dpc_trdir.py` | DPC class in TRDIR |
| `inspect_classes_w.py` | Class component listing |
| `inspect_seo_tables.py` | SEO table structure |
| `get_seoclass_fields.py` | VSEOCLASS field names |
| `get_seoclasstx_fields.py` | SEOCLASSTX (text) field names |
| `read_cp.py` / `read_ccimp.py` | Read class sections |

## Known Failures & Self-Healing

| Error | Cause | Fix |
|-------|-------|-----|
| `Class already exists` | VSEOCLASS entry present | Use OVERWRITE='X' |
| `Transport required` | Object not in transport | Create transport first, pass CORRNUM |
| `CCIMP write returns 0 lines` | Wrong include name format | Check exact include name via TRDIR |
| `Activation fails` | Syntax error in CCIMP | Read source back, fix syntax, re-write |
| `SIW_RFC not found` | Missing function module | Fall back to INSERT_REPORT |
| `Lock conflict` | Object locked by another user | Check SM12, wait or break lock |

## Known Limitation: Inactive Metadata

If a class exists in `SEOCLASSDF` with `state=1` (inactive) but **no CCIMP include**:
1. `read_ccimp.py` returns empty — no implementation include exists
2. ADT API returns 404 for the class source URL
3. **Workaround**: Activate the class skeleton via SE24 or ADT POST first, THEN write CCIMP
4. Alternative: Use ABAP bridge pattern (`write_ccimp_abap_bridge.py`) to force-create the include

This edge case occurs when a class was created via RFC but never activated. The class definition exists but has no runtime artifacts.

## You Know It Worked When

1. `check_class_exists.py` returns the class with correct description
2. `read_ccimp.py` shows the method source code you deployed
3. ADT syntax check returns 0 errors
4. Activation succeeds (no inactive objects remain)
5. Class is callable via RFC or OData at runtime
