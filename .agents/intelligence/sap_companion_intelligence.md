# SAP Companion Intelligence Document
**UNESCO SAP Development & Monitoring Toolkit — Complete Reference**

---

## 1. Three-Pillar Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                  AGENT SAP CAPABILITY STACK                      │
├──────────────────┬──────────────────┬───────────────────────────┤
│  PILLAR 1        │  PILLAR 2        │  PILLAR 3                 │
│  Python RFC      │  ADT REST API    │  Fiori Tools CLI          │
│  (SNC/SSO)       │  (HTTP Basic)    │  (npx/CLI)                │
├──────────────────┼──────────────────┼───────────────────────────┤
│ Table reads      │ Read/Write ABAP  │ Scaffold Fiori apps       │
│ Mass data        │ Classes         │ Modify manifest.json      │
│ Active users     │ Programs         │ Read OData metadata       │
│ BDC sessions     │ Includes         │ Visualize services        │
│ Background jobs  │ Function Groups  │ App structure analysis    │
│ Short dumps      │ BSP file store   │                           │
│ RFC functions    │ CDS Views        │                           │
│                  │ Transport mgmt   │                           │
│                  │ ABAP Unit tests  │                           │
│                  │ ATC checks       │                           │
│                  │ abapGit repos    │                           │
│                  │ Runtime dumps    │                           │
│                  │ Data preview     │                           │
└──────────────────┴──────────────────┴───────────────────────────┘
```

---

## 2. System Routing Rules

| System | Purpose | Auth | Host |
|--------|---------|------|------|
| **D01** | Development — code deploy, BSP extract, ADT write | Password + SNC | `HQ-SAP-D01.HQ.INT.UNESCO.ORG:80` |
| **P01** | Production — data, monitoring, BDC, users, uploads | **SNC/SSO only** (no password) | `172.16.4.100:8000` |

> **Rule**: Never use D01 data for monitoring. Never write code to P01 directly (use CTS).

---

## 3. VS Code Plugin Intelligence

| Plugin | Role | Key Capability |
|--------|------|----------------|
| `murbani.vscode-abap-remote-fs` | Core ADT client | Filesystem access to SAP via ADT |
| `saposs.sap-ux-sap-systems-ext` | Credential store | Windows Credential Manager integration |
| `sapse.sap-ux-fiori-elements-ext` | Fiori Elements | Page Map, FE page modification |
| `sapse.sap-ux-annotation-modeler-ext` | Annotations | OData annotation editing |
| `sapse.sap-ux-service-modeler-ext` | Service Modeler | OData service visualization |
| `sapse.sap-ux-application-modeler-ext` | App Modeler | Fiori app structure |

**Discovered ADT endpoint (confirmed working):**
```
http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80    client=350
Auth: Basic jp_lopez / (D01 password from .env)
```

---

## 4. Full ADT Endpoint Map

### Source Code (Read + Write)
```
/sap/bc/adt/oo/classes/{name}                    → CLASS
/sap/bc/adt/oo/interfaces/{name}                 → INTERFACE
/sap/bc/adt/programs/programs/{name}             → PROGRAM
/sap/bc/adt/programs/includes/{name}             → INCLUDE
/sap/bc/adt/functions/groups/{fg}/fmodules/{fn}  → FUNCTION MODULE
/sap/bc/adt/enhancements/{name}                  → ENHANCEMENT
/sap/bc/adt/xslt/{name}                          → XSLT
```

### DDIC
```
/sap/bc/adt/ddic/tables/{name}                   → TABLE
/sap/bc/adt/ddic/dataelements/{name}             → DATA ELEMENT
/sap/bc/adt/ddic/domains/{name}                  → DOMAIN
/sap/bc/adt/ddic/ddl/...                         → CDS VIEW
```

### BSP / Fiori / UI5
```
/sap/bc/adt/filestore/ui5-bsp/objects/{app}/content  → BSP/UI5 file store ✅
/sap/bc/adt/bsp/applications/{app}/pages/{page}      → BSP page source
```

### Operations
```
/sap/bc/adt/datapreview/freestyle               → OSQL query (like SE16N)
/sap/bc/adt/repository/nodestructure            → Package tree browser
/sap/bc/adt/repository/informationsystem/search → Object search
/sap/bc/adt/activation                          → Activate any object
/sap/bc/adt/checkruns                           → Syntax check
/sap/bc/adt/abapunit/testruns                   → ABAP Unit tests
/sap/bc/adt/atc/runs                            → ATC code quality
```

### Transport & Git
```
/sap/bc/adt/cts/transportrequests               → CTS transport list
/sap/bc/adt/cts/transportchecks                 → Transport checks
/sap/bc/adt/abapgit/repos                       → abapGit repositories
```

### Monitoring
```
/sap/bc/adt/runtime/dumps                       → Short dumps (ST22)
/sap/bc/adt/runtime/traces/abaptraces           → Performance traces
/sap/bc/adt/debugger/breakpoints                → Breakpoints
```

---

## 5. System Monitor Reports

```bash
# Always default to P01 for real data:
python sap_system_monitor.py --report health       --system P01
python sap_system_monitor.py --report users        --system P01   # SM04
python sap_system_monitor.py --report transactions --system P01   # TSTC + TH_WPINFO
python sap_system_monitor.py --report obsolete     --system P01   # REPOSRC age
python sap_system_monitor.py --report dumps        --system P01   # ST22/SNAP
python sap_system_monitor.py --report bdc          --system P01   # SM35/APQI
python sap_system_monitor.py --report jobs         --system P01   # SM37/TBTCO

# Development system:
python sap_system_monitor.py --report health       --system D01
```

### P01 Health Snapshot (2026-03-12)

| Object Type | P01 Count | D01 Count | Delta |
|------------|-----------|-----------|-------|
| Programs (PROG) | 826 | 1000 | +174 in dev |
| Classes (CLAS) | 142 | 266 | +124 in dev |
| Function Groups (FUGR) | 181 | 231 | |
| Transactions (TRAN) | 165 | 194 | |
| Tables (TABL) | 604 | 815 | |
| Data Elements (DTEL) | 645 | 770 | |
| **Fiori Apps (WAPA)** | **0** | **13** | **None in prod yet!** |

---

## 6. Batch Input (BDC) — Complete Intelligence (Session #002, 2026-03-12)

**All sessions, last 90 days, P01 Production:**

### Session Types by Origin (NO MORE UNKNOWNS)

| Origin | Sessions | Transaction | Source |
|--------|:--------:|------------|--------|
| Travel (`TRIP_MODIFY`) | **1,180** | PR05/TRIP | Real users + ALE. NOT Allos. |
| **Allos PRAA*** | **135** | **PA30/PA40** | `BBATCH` service user. **← REPLACE** |
| Payroll posting (numeric) | hundreds | PC00_M99_CIPE / PCP0 | SAP Y1 → P01 via ALE. NOT Allos. |
| Coupa (`COUPA0000272–0000283`) | 12 | PA30 | Coupa procurement → SAP HR. **← REPLACE API** |
| `SZORME-RFC` | 22 | TBD | External RFC system. Investigate. |
| `SAS-RFC` | 17 | TBD | External RFC. Investigate. |
| Support Cost | 13 | FMBB/FB01 | Finance batch. |
| `HUNUPSR0` | 11 | PA30/PA40 | Standard HR mass update. |

### Numeric Session Name Decoder

```
Pattern: [PERNR][PayrollArea][RunID]
Example: 10155259V901 = PERNR=10155259, Area=V9, Run=01

PROGID=MSSY1 = SAP Logical System "MSSY1" = HCM Payroll backend (not a program)
Transaction: PC00_M99_CIPE (International Payroll Posting to FI)
```

### Allos Replacement Roadmap

```
Priority 1: PRAA* sessions (135/quarter)
  Sessions: PRAAUNESC_SC, PRAAUNESU_SC, PRAAUNESU_ST, PRAAUBOU_SC
  Transaction: PA30/PA40
  BAPI: BAPI_EMPLOYEE_ENQUEUE + HR_MAINTAIN_MASTERDATA
  → One Fiori mass HR update app replaces all

Priority 2: Coupa integration (12/quarter)
  Sessions: COUPA0000272–0000283
  Transaction: PA30 — Coupa driving SAP HR screen!
  → Expose BAPI/REST endpoint to Coupa directly

Priority 3: SZORME-RFC + SAS-RFC (39/quarter)
  → First: identify via RFCDES. Then: BAPI replacement.
```

### Key APQI/APQD Technical Facts

```
APQD is PURGED after successful processing (QSTATE=S/F).
→ Only ERROR sessions (QSTATE=E) have live field-level data.
→ To capture field data: python bdc_full_inventory.py --state E

PROGID in APQI = Logical System Name (not ABAP program name!)
  MSSY1 = UNESCO SAP HCM system Y1 (payroll backend)
  SY1   = SAP system itself (ALE queue processor)
  R0    = Standard ABAP program

APQI fixed-width parser: use parse_fixed() from bdc_full_inventory.py
```

---

## 7. Tool Capabilities — Quick Reference

### Key Scripts

| Script | Purpose | System |
|--------|---------|--------|
| `sap_adt_client.py` | Full ADT REST client for all ABAP object R/W | D01 |
| `extract_bsp_via_adt.py` | Download complete BSP/UI5 apps | D01 |
| `sap_system_monitor.py` | **HIGH-LEVEL** 7-report dashboard | **P01 (default)** |
| `bdc_full_inventory.py` | **DEEP BDC** — all sessions, full decode, no limit | **P01** |
| `bdc_deep_analysis.py` | **FORENSIC BDC** — APQD drill, PROGID scan | **P01** |
| `sap_brain.py` | Knowledge graph builder + querier | both |

### `sap_adt_client.py` — Full Method List

```python
client = from_env("D01")     # Development (password auth)
client = from_env("P01")     # Production (SSO — no password)

# Source code R/W
client.get_source(uri)                          # Read any source
client.write_class_source(name, src, transport) # Class write+activate
client.write_program_source(name, src)          # Program write+activate
client.write_include_source(name, src)          # Include write+activate
client.write_function_source(fg, fn, src)       # Function module
client.upload_bsp_file(app, path, content)      # BSP/UI5 file upload

# Discovery
client.search_object(query, obj_type)           # Find any object
client.get_package_tree(package)                # Browse packages
client.get_object_types()                       # All type IDs

# Operations
client.data_preview(sql)                        # OSQL query (SE16N)
client.get_transports()                         # Open CTS requests
client.syntax_check(source, uri)                # Syntax validation
client.run_unit_tests(uri)                      # ABAP Unit
client.activate(uri, name, type_id)             # Activate object

# Monitoring
client.get_runtime_dumps()                      # ST22 short dumps
client.get_runtime_traces()                     # Performance traces
client.get_abapgit_repos()                      # abapGit repos
```

### RFC Tables — Key Intelligence Sources

| Table | Transaction | Data |
|-------|------------|------|
| `APQI` | SM35 | BDC session headers (GROUPID, PROGID, CREATOR, QSTATE) |
| `APQD` | SM35 | BDC field-level data — **PURGED after success** |
| `TBTCO` | SM37 | Background job headers |
| `SNAP` | ST22 | Short dump records |
| `REPOSRC` | SE38 | Program last change date |
| `TSTC` | SE93 | Transaction codes |
| `USR02` | SU01 | User last login |
| `TADIR` | SE80 | Object repository (all objects) |
| `PA0001` | PA20 | HR: Org assignment (PERNR → name/org) |
| `RGDIR` | PC_PAYRESULT | Payroll result directory |
| `RFCDES` | SM59 | RFC destinations |

---

## 8. Authentication Summary

```
D01 Development:
  RFC  → SNC (p:CN=D01)
  ADT  → HTTP Basic (jp_lopez + D01 password from .env)

P01 Production:
  RFC  → SNC (p:CN=P01) ← SSO, no password needed ✅
  ADT  → Not configured yet (would need P01 ADT setup)
```

> [!IMPORTANT]
> P01 password is intentionally blank in `.env`. SSO via SNC handles P01 auth.
> D01 password ≠ P01 password (each SAP system maintains independent passwords).

---

## 9. Transactions — Not Covered by ADT

ADT has no native endpoint for transaction code management. Use:

| Task | Method |
|------|--------|
| List custom transactions | `RFC_READ_TABLE` on `TSTC WHERE TCODE LIKE 'Z%'` |
| Create transaction | RFC insert into `TSTC` + `TSTCT` via WebGUI (SE93) |
| Transaction usage | `TH_WPINFO` (live) or `SM20` security audit log |

---

## 10. PMO Brain — Tasks & Project Tracking

> Full file: [PMO_BRAIN.md](./PMO_BRAIN.md) | Update every session.

### 🔴 Critical — Next Session

| # | Task |
|---|------|
| 1 | Fix `RFC_SYSTEM_INFO` parsing — health report shows `?` |
| 2 | Extract OData services → `HCM/Fiori_Apps/Offboarding/services/` |
| 3 | Identify `SZORME-RFC` + `SAS-RFC` source systems (check RFCDES) |
| 4 | Design Fiori replacement for `PRAA*` (PA30 infotype update app) |

### 🟡 High Priority

| # | Task |
|---|------|
| 5 | Extract Benefits BSP app → `HCM/Fiori_Apps/Benefits/bsp/` |
| 6 | Run P01 transaction usage report |
| 7 | P01 runtime dumps report |
| 8 | Document Coupa integration — replace COUPA* BDC with BAPI |

### Session Log

| Date | Key Achievements |
|------|-----------------|
| 2026-03-12 (AM) | P01 SSO, 7-report monitor, BDC analysis, brain (55n/66e), domain structure, skill_creator, PROJECT_MEMORY, PMO_BRAIN |
| 2026-03-12 (BDC) | Full BDC inventory (no limit), numeric sessions = payroll posting resolved, COUPA* discovery, SZORME/SAS-RFC discovery, tool separation confirmed |

---

*Last updated: 2026-03-12 Session #002 | BDC complete decode done*

