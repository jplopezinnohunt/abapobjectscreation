---
name: SAP ADT REST API Integration
description: UNIFIED reference + decision skill for programmatic deployment of ABAP/DDIC objects on UNESCO ECC 6.0 EhP8 — covers ADT REST (proven for source code, S/4HANA-only for DDIC), DDIF wrapper (proven for DDIC on EhP8), abapGit (mastery + install playbook for multi-object lifecycle), and all RFC/Playwright alternatives. Decision matrix per object type + workflow. Used by abapobjectscreation, unescrp, and any UNESCO SAP project that deploys Z code.
domains:
  functional: [*]
  module: [BASIS, CTS]
  process: []
---

# SAP ABAP/DDIC Deployment — Unified Skill (abapGit + ADT REST + DDIF + RFC)

> [!NOTE]
> **Skill name kept as `sap_adt_api`** because that's the name multiple projects already load. Scope has expanded: now covers abapGit + ADT REST + DDIF wrapper + RFC/Playwright alternatives + the decision matrix to pick the right tool per task. All capabilities live here — no need to consult separate skills.

## 🏛️ ARCHITECTURAL STANDARD — abapGit-first (when installed)

**abapGit is the DEFAULT deployment path for any object type it supports** (170+ types — DDIC, source code, enhancements, OData, BSP, etc.). DDIF wrapper / ADT REST / RFC alternatives are **bridges or fallbacks** for cases abapGit cannot cover OR for the period until abapGit is installed.

**Priority order (apply this hierarchy for any deployment task):**

1. **abapGit** — default for supported types when installed. Industry standard, TADIR/CTS correct by default, version-controlled, atomic multi-object, forward-compatible to S/4HANA, cross-system sync, PR-reviewable.
2. **ADT REST** — for source code (PROG/CLAS/INTF/FUGR/FUNC/INCLUDE/ENHO/XSLT/BSP). Available on all kernels including EhP8. Use while abapGit not yet installed.
3. **DDIF wrapper** — DDIC bridge (TABL/DTEL/DOMA) ONLY while abapGit not yet installed on EhP8. Deprecates when abapGit lands or system migrates to S/4HANA.
4. **RFC / Playwright** — for objects no other tool covers: customizing rows (SM30), RFC destinations (SM59), SICF, RZ10, BOR, PFCG user assignments.

**Current operational reality (2026-05-25):** **abapGit STANDALONE is INSTALLED on D01** — dev edition install attempted and ABORTED with `SAPSQL_DATA_LOSS` (NW 7.40 EhP8 incompatibility with `main` branch). The canonical, always-up-to-date status doc — **read this before any abapGit work on D01** — is `knowledge/operational_state/abapgit_d01_status.md`. Quick summary: `ZABAPGIT_STANDALONE` PROG in `$TMP`, 151,660 lines, REPOSRC `r3state = A` (active). Installed via workstation-bridge architecture (no BASIS, no STRUST): workstation downloaded the official standalone source from `raw.githubusercontent.com/abapGit/build/main/zabapgit_standalone.prog.abap` (4.86 MB) and pushed via RFC `RPY_PROGRAM_INSERT` (`SOURCE_EXTENDED = ABAPTXT255` table, 32.3s). See §19 for the exact playbook. **Usable via SAPGUI SE38 → `ZABAPGIT_STANDALONE` for human-driven workflows on ANY object type abapGit supports (170+ types — tables, classes, programs, ENHO, BSP, OData, etc.)**. For agent-driven RFC class-level API access, dev edition install is the next step (§19.4).

See [[feedback-abapgit-is-the-standard-when-installed]].

> [!IMPORTANT]
> **STATUS 2026-05-24 — D01 ADT UNBLOCKED.** BASIS restored HTTP auth for `jp_lopez`. Live probe confirms HTTPS:443 reaches `/sap/bc/adt/discovery` with HTTP 200 and a real CSRF token (`1zg1TQh…`). 217 ADT collections enumerated. The previously documented 401 (2026-04-10 → 2026-05-24) is RESOLVED. The endpoint switched from `http:80` to `https:443` as part of the fix — see updated prereqs below.
>
> **Silent-401 bug in `sap_adt_client._request`** (described in session #75 retro) is also fixed: error responses no longer poison `self._csrf_token`, and `fetch_csrf()` now raises `RuntimeError` with diagnostic detail when discovery fails to authenticate.

## 🛑 CRITICAL — NEVER MODIFY STANDARD SAP OBJECTS

**HARD RULE, severity CRITICAL.** The agent MUST NEVER use ADT REST, DDIF wrapper, abapGit, RFC FMs, or any other path to modify, alter, append to, or change activation of objects NOT in Z*/Y*/customer namespace. Applies to:
- Tables (BSEG, BKPF, LFA1, KNA1, MARA, DD02L, TADIR, T001, etc.)
- Classes (CL_*, IF_*, CX_* without Z/Y prefix)
- Function modules (BAPI_*, SAPL* function group internals)
- Programs (SAP*, RV*, RM*, RP*)
- DDIC primitives (MANDT, MATNR, LIFNR, KUNNR, BUKRS, GJAHR, CHAR*, NUMC*)

Why CRITICAL: SAP licensing forbids it (SSCR keys required), upgrades overwrite via SPDD/SPAU (manual readjustment cost), UNESCO BASIS will refuse on principle, TADIR-EDTFLAG poisoning can break SE11 system-wide.

Refuse + offer alternative (append structure, BAdI, ENHO, user exit, customer include) in Z namespace.

See [[feedback-never-modify-standard-objects]] for full rule.

## 🛑 SCOPE RULE — NEW OBJECTS = D01 ONLY (mandatory)

**For ANY new ABAP/DDIC object work (create table, DE, domain, class, program, FM, index, etc.), the agent works EXCLUSIVELY in D01. NEVER touches P01.**

This is stricter than the broader no-prod-writes rule:
- **No P01 writes** — obvious
- **No P01 reads in the context of new-object creation** — no "let me check if it already exists in P01", no "preflight against prod". Logically unnecessary: by the transport model, if an object doesn't exist in D01 it cannot exist in P01.
- **The only legitimate P01 read in a creation context** is post-transport verification (object created in D01 → transported → confirm it landed). Even then prefer STMS confirmation over RFC probe.
- **Legitimate non-creation P01 reads** (incident diagnosis, process mining, data extraction) are unaffected.

Code consequence: when working on new objects, hardcode `from_env("D01")`. Do not parameterize the system.

See [[feedback-new-objects-only-in-d01-never-p01]].

## 🛑 ADT-FIRST PRINCIPLE — qualified by kernel version

**For SOURCE CODE objects (PROG, CLAS, INTF, FUGR, FUNC, INCLUDE, ENHO, XSLT, BSP):** use ADT REST. Available on ECC 6.0 EhP8 (NW 7.40) and beyond.

**For DDIC objects:** capability depends on kernel version. Verify against `adt_discovery()` before using.

### DDIC capability matrix — confirmed empirically against D01 (NW 7.40 / EhP8) 2026-05-24

| DDIC object | ADT REST endpoint | EhP8 (NW 7.40) | NW 7.50+ / S/4HANA |
|---|---|---|---|
| Data Element (DTEL) | `/sap/bc/adt/ddic/dataelements` | 🟡 Endpoint present, write untested | ✅ Documented |
| Structure (TABL/DS) | `/sap/bc/adt/ddic/structures` | 🟡 Endpoint present, write untested | ✅ Documented |
| Domain (DOMA) | `/sap/bc/adt/ddic/domains` | ❌ Not in discovery | ✅ Documented |
| View | `/sap/bc/adt/ddic/views` | 🟡 Endpoint present, write untested | ✅ Documented |
| TypeGroup | `/sap/bc/adt/ddic/typegroups` | 🟡 Endpoint present, write untested | ✅ Documented |
| CDS Sources (DDLS) | `/sap/bc/adt/ddic/ddl/sources` | ✅ Endpoint present (read-only on EhP8 historically) | ✅ Full |
| **Transparent Table (TABL/DT)** | **`/sap/bc/adt/ddic/tables`** | **❌ Returns HTTP 404 — endpoint missing** | ✅ Full |
| **Secondary Index** | **`/sap/bc/adt/ddic/tables/{t}/indexes`** | **❌ Returns HTTP 404 — endpoint missing** | ✅ Full |
| Database Conversion | `/sap/bc/adt/ddic/tables/{t}/database-conversions` | ❌ Depends on table endpoint | ✅ Full |

**Implication:** on UNESCO's ECC 6.0 EhP8 systems (D01, P01), `create_table`, `define_table`, `update_table_fields`, `add_table_field`, `remove_table_field`, `modify_table_field`, `update_table_metadata`, `create_index`, `drop_index`, `convert_table` will return HTTP 404. These methods are preserved for the S/4HANA migration path — **do not delete them**, but **do not invoke them on EhP8 systems**.

### Correct path for TABL + INDEX on ECC 6.0 EhP8

Use the **`DDIF_*_PUT` via `RFC_ABAP_INSTALL_AND_RUN`** pattern. This is **not** the architectural debt I previously labeled it — on EhP8 it is the **only** path. The pain points (opaque RC=2, IN-list parser bug) are real and must be mitigated by the wrapper, not avoided.

**Mitigation pattern for `DDIF_TABL_PUT` failures:**
1. **Pre-flight every dependency** with single-equality `RFC_READ_TABLE` queries (NOT IN-lists — the 72-char OPTIONS bug breaks them on EhP8):
   - Domain exists? `SELECT FROM DD01L WHERE DOMNAME EQ '<x>'`
   - DE exists? `SELECT FROM DD04L WHERE ROLLNAME EQ '<x>'`
   - DE active? `AS4LOCAL EQ 'A'`
2. **Synthesize an ABAP program** that calls `DDIF_DOMA_PUT` → `DDIF_DOMA_ACTIVATE` → `DDIF_DTEL_PUT` → `DDIF_DTEL_ACTIVATE` → `DDIF_TABL_PUT` → `DDIF_TABL_ACTIVATE` **in order**, with explicit `EXCEPTIONS` for each call.
3. **Parse the `WRITE` output** to convert each call's `SY-SUBRC` into a structured Python dict — never bubble up an opaque RC=2.
4. **Run via `RFC_ABAP_INSTALL_AND_RUN`**, capture the spool / report list, return same shape as `define_table()` would.

`DDIF_TABL_PUT` exception map (the 5 causes of RC=2 / RC=3 the agent must distinguish):

| RC | EXCEPTION | Cause | Recovery |
|---|---|---|---|
| 1 | `not_executed` | TBL_NAME malformed | Validate name length + character set |
| 2 | `name_inconsistent` | Name conflicts with existing TADIR, OR referenced DE/DOMA missing | Run pre-flight first |
| 3 | `tabl_inconsistent` | Structure invalid (PK not first, NOTNULL gap, CHAR with missing DTEL) | Validate field order, key flags, DE resolvability |
| 4 | `put_failure` | DB-level (transport blocked, lock held) | Retry after lock release, verify TR open |
| 5 | `put_refused` | No DEVCLASS, no authorization | Verify package exists, `S_DEVELOP` granted |

### DDIC migration plan (when UNESCO moves to S/4HANA or NW 7.5x)

The methods `define_table`, `update_table_fields`, `create_index`, `drop_index`, `convert_table` are **already implemented in `sap_adt_client.py`**. When the kernel upgrades, callers automatically gain the ADT-REST path without code changes — just remove the EhP8 guard. Keep them as forward-compatible scaffolding.

### What about other ABAP code objects? — Still ADT-first

For PROG, CLAS, INTF, FUGR, FUNC, INCLUDE, ENHO, XSLT, BSP: **ADT works on EhP8**. Confirmed by working endpoints in discovery and historical successful deploys via `sap_adt_client.write_class_source` / `write_program_source` / `write_function_source` / `set_class_include_source`. The "ADT-first" principle is unchanged for these.

## Why ADT API? (when it works)

The SAP ADT REST API is the **official, clean interface** for source code operations. It is used by:
- The **VSCode ABAP extension** (abap-remote-fs)
- **Eclipse ABAP Development Tools**
- The **mcp-abap-abap-adt-api** MCP server ([github.com/mario-andreschak/mcp-abap-abap-adt-api](https://github.com/mario-andreschak/mcp-abap-abap-adt-api))

> [!IMPORTANT]
> **When ADT is available, prefer it over RFC hacks** for source code writes. ADT handles locking, transport recording, and activation cleanly. **But verify ADT auth first with a quick GET probe** — if 401, fall back to RFC.

## Current working alternative — RFC paths

Until ADT auth is restored, use these working patterns:

| Operation | RFC alternative | Status |
|---|---|---|
| Read program source | `RPY_PROGRAM_READ` | ✓ works |
| Insert/update report | `INSERT REPORT lt_src FROM DIRECTORY ENTRY trdir` (run via `RFC_ABAP_INSTALL_AND_RUN`) | ✓ works (used for Y_FI_DMEE_ADR v6, ZSAPFPAYM_REPLAY) |
| Generate / activate report | `GENERATE REPORT 'name'` (run via `RFC_ABAP_INSTALL_AND_RUN`) | ✓ works |
| Update FUPARAREF | `UPDATE fupararef SET reference = 'X' WHERE ...` (run via `RFC_ABAP_INSTALL_AND_RUN`) | ✓ works (required after INSERT REPORT for FM interface metadata) |
| Class CCIMP / Method source | `SEO_CLASS_CREATE_*` + RFC INSERT REPORT to CCIMP include | ✓ works (6 strategies in `sap_class_deployment` skill) |
| BSP application upload | abapGit pull from GitHub OR Playwright SE38/SE80 | ✓ works (see `sap-github-pull-deployment.md` in unescrp skill) |
| Read O2PAGCON (BSP page source) | ADT only — currently blocked | ✗ blocked |

## Auth diagnostic — run this first

```python
import sys; sys.path.insert(0, 'Zagentexecution/mcp-backend-server-python')
from sap_adt_client import from_env
c = from_env('D01')
status, body, headers = c._request("GET", "/sap/bc/adt/discovery")
print(f"ADT HTTP status: {status}")
# 200 → ADT works, proceed
# 401 → ADT blocked, fall back to RFC paths
```

> **Watch out:** `c.fetch_csrf()` will print `"CSRF token obtained: ..."` even on 401 if SAP echoes a token in the error headers. The token will be **empty string** when auth actually failed. Check `status == 200` explicitly, not just whether a token came back.

---

## 1. Prerequisites

- SAP ICF service `/sap/bc/adt` must be **active** (can check via SICF or test URL)
- User needs `S_DEVELOP` authorization
- Basic Auth over HTTP. **No SNC** for ADT (ADT uses HTTP, not RFC).

> [!IMPORTANT]
> **Confirmed working endpoint for D01 (2026-05-24, post-BASIS-unblock):**
> - URL: `https://HQ-SAP-D01.HQ.INT.UNESCO.ORG:443`  (port **443 HTTPS**, was previously 80 HTTP before the BASIS fix)
> - Use **hostname**, NOT IP `172.16.4.66`
> - Protocol: **HTTPS** (not HTTP)
> - SSL cert verification: disabled in `sap_adt_client` (`verify_ssl=False`) because UNESCO uses internal CA

### Environment Variables Required
```
SAP_HOST=HQ-SAP-D01.HQ.INT.UNESCO.ORG   # Hostname, not IP!
SAP_CLIENT=350
SAP_USER=jp_lopez
SAP_PASSWORD=<password>                  # Plain password for HTTP Basic Auth
SAP_ADT_PORT=443                         # HTTPS port (was 80 before 2026-05-24 BASIS fix)
SAP_ADT_HTTPS=true
```

### ⚖️ When to Use ADT vs Python RFC

| Operation | Best Tool | Reason |
|---|---|---|
| Read table data (TADIR, O2PAGDIR, PA*, Z*) | **Python RFC (SNC)** | No password needed; faster for mass reads |
| Read BSP page source | **Python ADT** | RFC_READ_TABLE cannot read O2PAGCON content |
| Read ABAP class/program source | **Python ADT** | Clean, official, no dialog issues |
| Write/deploy ABAP source | **Python ADT** | Lock→Write→Activate flow is the only reliable method |
| BSP file listing | **Python RFC** | O2PAGDIR readable via RFC_READ_TABLE |
| Activate ABAP objects | **Python ADT** | POST /sap/bc/adt/activation |
| Mass data extraction | **Python RFC** | RFC handles pagination via ROWSKIPS |
| Fiori app structure modification | **Fiori Tools CLI** | See sap_fiori_tools skill |

---

## 2. Python Client

Use **`sap_adt_client.py`** in `Zagentexecution/mcp-backend-server-python/`. It requires **only stdlib** (`urllib`, `ssl`, `base64`) — no `requests` or `pyrfc` needed.

```python
from sap_adt_client import from_env
client = from_env()
client.fetch_csrf()  # Initialize session
```

---

## 3. Workflow for ALL Source Code Operations

```
1. fetch_csrf()          → GET /sap/bc/adt/discovery  (X-CSRF-Token: Fetch)
2. search_object(name)   → GET /sap/bc/adt/repository/informationsystem/search
3. lock(uri)             → POST {uri}?_action=LOCK&accessMode=MODIFY  → lockHandle
4. set_source(uri, code) → PUT  {uri}/source/main  (X-adtcore-locktoken: {lockHandle})
5. syntax_check(code)    → POST /sap/bc/adt/checkruns
6. activate(uri, name)   → POST /sap/bc/adt/activation  (XML body with object ref)
7. unlock(uri, handle)   → DELETE /sap/bc/adt/locks/{lockHandle}
```

---

## 4. URL Patterns by ABAP Object Type

| Object Type      | ADT URI Pattern                                              | Source Suffix     | Type ID   |
|-----------------|--------------------------------------------------------------|-------------------|-----------|
| **Class**        | `/sap/bc/adt/oo/classes/{CLASS_NAME}`                       | `/source/main`    | `CLAS/OC` |
| **Interface**    | `/sap/bc/adt/oo/interfaces/{INTF_NAME}`                     | `/source/main`    | `INTF/OI` |
| **Program**      | `/sap/bc/adt/programs/programs/{PROG_NAME}`                 | `/source/main`    | `PROG/P`  |
| **Include**      | `/sap/bc/adt/programs/includes/{INCL_NAME}`                 | `/source/main`    | `PROG/I`  |
| **Func Group**   | `/sap/bc/adt/functions/groups/{FUGR_NAME}`                  | `/source/main`    | `FUGR/F`  |
| **Function**     | `/sap/bc/adt/functions/groups/{FUGR}/fmodules/{FUNC}`       | `/source/main`    | `FUGR/FF` |
| **BSP App**      | `/sap/bc/adt/bsp/applications/{APP}/pages/{PAGE}`           | `/source`         | `WAPA`    |
| **UI5/BSP App**  | `/sap/bc/adt/filestore/ui5-bsp/objects/{APP}`               | `/content`        | —         |
| **DDIC Table**   | `/sap/bc/adt/ddic/tables/{TABLE_NAME}`                      | —                 | `TABL`    |
| **Data Element** | `/sap/bc/adt/ddic/dataelements/{DTEL_NAME}`                 | —                 | `DTEL`    |
| **Domain**       | `/sap/bc/adt/ddic/domains/{DOMA_NAME}`                      | —                 | `DOMA`    |
| **OData Svc**    | `/sap/bc/adt/businessservices/odataservices/{SRV}`          | —                 | `IWSV`    |
| **Svc Binding**  | `/sap/bc/adt/businessservices/binding/{NAME}`               | —                 | `SRVB`    |
| **Gateway Svc**  | `/sap/bc/adt/gwservices/groups/{GRP}`                       | —                 | `IWSG`    |
| **ENHO**         | `/sap/bc/adt/enhancements/{ENHO_NAME}`                      | `/source/main`    | `ENHO`    |
| **XSLT**         | `/sap/bc/adt/xslt/{XSLT_NAME}`                             | `/source/main`    | `XSLT`    |

> [!TIP]
> For **ABAP class implementation** (CCIMP include), write to the **class URI's `/source/main`** directly — not to the CCIMP include name. ADT handles dispatching to the correct include internally.

---

## 5. Activation XML Body

```xml
<?xml version="1.0" encoding="utf-8"?>
<adtcore:objects xmlns:adtcore="http://www.sap.com/adt/core"
                 xmlns:atom="http://www.w3.org/2005/Atom">
  <atom:link href="/sap/bc/adt/oo/classes/ZCL_MY_CLASS"
    rel="http://www.sap.com/adt/relations/activation"
    adtcore:name="ZCL_MY_CLASS"
    adtcore:type="CLAS/OC" />
</adtcore:objects>
```

Content-Type: `application/vnd.sap.adt.activation.request+xml`

---

## 6. CSRF Token Flow

```python
# 1. GET request WITH header X-CSRF-Token: Fetch
# 2. Response HEADER contains: X-CSRF-Token: <actual_token>
# 3. Use that token on all subsequent POST/PUT/DELETE requests
```

---

## 7. Error Patterns and Mitigations

| Error                        | Cause                              | Fix                                      |
|------------------------------|------------------------------------|------------------------------------------|
| `401 Unauthorized`           | Wrong user/pass or ICF not active  | Check creds, activate SICF `/sap/bc/adt` |
| `403 Forbidden (CSRF)`       | Missing or stale CSRF token        | Re-fetch CSRF via GET /discovery         |
| `404 Not Found`              | Object doesn't exist yet           | Create via SE24/SE80 first or POST       |
| `423 Locked`                 | Object locked by another user      | SM12 to release, or use that session     |
| `NAME_NOT_ALLOWED`           | Object not in system at all        | Must create metadata first (SE24/SE80)   |
| `Screen output (dialog)`     | RFC called a dialog FM             | Use ADT API instead of RFC               |
| `Remote type resolution err` | RFC parameter type not resolvable  | Use ADT API instead of RFC               |

---

## 8. Known Issues: Classes with Inactive Metadata

If a class exists in `SEOCLASSDF` with `state=1` (inactive) but **no CCIMP include**:
1. The ADT API will return `404` for the class source URL
2. You must first activate the class **skeleton** via SE24 or ADT POST to create the include
3. Then use the ADT PUT workflow to write the implementation

**Workaround via ABAP bridge (last resort):**
```python
# Create the CCIMP include skeleton first via RFC bridge
# Then use ADT API to write source
```

---

## 9. OData/Gateway Service Operations via ADT

For OData service registration/activation (SEGW-equivalent via API):
- Use `/sap/bc/adt/gwservices/` endpoint family
- SEGW-generated classes (DPC, MPC, DPC_EXT, MPC_EXT) are regular ABAP classes → use `CLAS/OC` type
- Register service: POST to `/sap/bc/adt/businessservices/odataservices`
- The **safer approach** remains using the SEGW WebGUI via Playwright for service registration, but **source code** for DPC_EXT and MPC_EXT can be written via ADT

---

## 10. mcp-abap-abap-adt-api MCP Server

There is an existing MCP server that already wraps the `abap-adt-api` JavaScript library:
- **Repository**: [mario-andreschak/mcp-abap-abap-adt-api](https://github.com/mario-andreschak/mcp-abap-abap-adt-api)
- **Tools**: `searchObject`, `getObjectSource`, `setObjectSource`, `lock`, `unLock`, `activate`, `syntaxCheckCode`, `transportInfo`, `GetTable`, `GetStructure`
- **Already uses**: `/sap/bc/adt/oo/classes/{name}/source/main` pattern

> [!NOTE]
> Consider integrating `mcp-abap-abap-adt-api` into our MCP server stack as an additional MCP server for ABAP object management. This would give the agent `searchObject`, `setObjectSource`, `activate` as native MCP tools.

---

## 11. CSRF Token Handling Best Practice

The CSRF token flow is critical and error-prone. Key rules:
1. **Always fetch fresh** before the first write operation in a session
2. **Token expires** after ~30 minutes of inactivity — re-fetch on 403
3. **Store in session** — `sap_adt_client.py` handles this via `self.csrf_token`
4. **Never cache across sessions** — each Python process needs its own token

```python
# Pattern for robust CSRF handling
client = from_env()
client.fetch_csrf()  # Always first
try:
    client.set_source(uri, code, lock_handle)
except Exception as e:
    if '403' in str(e):
        client.fetch_csrf()  # Re-fetch on expiry
        client.set_source(uri, code, lock_handle)  # Retry
```

---

## 12. Integration Status (Session #076, 2026-05-24)

| Integration | Status | Notes |
|-------------|--------|-------|
| `sap_adt_client.py` (custom Python) | ✅ Active | Stdlib only, 46 public methods (22 original + 24 added 2026-05-24) |
| D01 HTTPS ADT auth (`jp_lopez`) | ✅ Unblocked | Was 401 from 2026-04-10 to 2026-05-24; BASIS restored |
| Silent-401 bug (`_request` + `fetch_csrf`) | ✅ Fixed | No longer caches CSRF from error responses; `fetch_csrf` raises on failure |
| `mcp-abap-abap-adt-api` (MCP server) | 🟡 Not integrated | Available but not connected — we use Python client instead |
| VSCode ABAP Remote FS | ✅ Working | Confirmed same D01 endpoint |
| ADT→RFC fallback | ⚠️ Last resort | RFC only when ADT 4xx; for DDIC operations, fix ADT auth instead |

---

## 13. DDIC Table & Index Handler (added Session #076)

> [!CAUTION]
> **NOT USABLE ON ECC 6.0 EhP8** — empirically confirmed 2026-05-24. The methods below return HTTP 404 on UNESCO's D01 / P01 systems. They are preserved as forward-compatible scaffolding for the S/4HANA migration path. **For TABL + INDEX work on EhP8 today, use the `DDIF_*_PUT via RFC_ABAP_INSTALL_AND_RUN` pattern per §0 (ADT-FIRST PRINCIPLE qualifier above).**

This is the canonical pattern for NW 7.50+ / S/4HANA. Atomic, structured errors, no opaque RCs.

### 13.1 Define a table from scratch (one call)

```python
from sap_adt_client import from_env
c = from_env("D01")

trkorr = c.create_transport("ZCRP cert tables")

result = c.define_table(
    name="ZCRP_CERTHEAD",
    description="CRP Certificate Header",
    package="ZCRP",
    transport=trkorr,
    fields=[
        {"name": "MANDT",   "key": True,  "data_element": "MANDT"},
        {"name": "CERT_ID", "key": True,  "data_element": "CHAR20"},
        {"name": "CERT_RQ", "key": False, "data_element": "CHAR7"},
        {"name": "CERT_NR", "key": False, "data_element": "CHAR7"},
        {"name": "ERDAT",   "key": False, "data_element": "ERDAT"},
    ],
)
# {'table': 'ZCRP_CERTHEAD',
#  'phases': {'create': 200, 'lock': 'OK',
#             'set_source': 200, 'activate': 'OK'}}
```

If a referenced data element (e.g. `CHAR7`) does not exist, the `set_source` phase fails with HTTP 400 + `<adtcore:message>Data element CHAR7 does not exist</adtcore:message>` — explicit and actionable, no RC=2 ambiguity.

### 13.2 Pre-create the DDIC chain if needed

```python
# Verify the DE chain BEFORE defining the table (ADT-first preflight)
if not c.search_object("CHAR7", "DTEL"):
    c.create_domain("CHAR7",       "Char 7", "ZCRP", trkorr)
    c.create_data_element("CHAR7", "Char 7", "ZCRP", trkorr)
# Now safe to call define_table()
```

### 13.3 Append a field to an existing table

```python
c.add_table_field(
    "ZCRP_CERTHEAD",
    {"name": "CERT_STATUS", "key": False, "data_element": "CHAR1"},
    transport=trkorr,
)
```

### 13.4 Create a secondary index

```python
c.create_index(
    table="ZCRP_CERTHEAD",
    index_id="Z01",
    description="By certificate number",
    fields=["CERT_NR"],
    unique=False,
    transport=trkorr,
)
# {'table': 'ZCRP_CERTHEAD', 'index': 'Z01',
#  'phases': {'create': 200, 'lock': 'OK',
#             'set_source': 200, 'activate': 'OK'}}
```

### 13.5 Why this REPLACES the ABAP-program pattern

| Aspect | Legacy (`RFC_ABAP_INSTALL_AND_RUN + DDIF_TABL_PUT`) | ADT (`define_table`) |
|---|---|---|
| Error reporting | RC=2 ambiguous (covers 5 root causes) | HTTP 4xx + structured XML body with `<adtcore:message>` |
| Pre-validation | Manual `RFC_READ_TABLE` per dependency (fragile IN-list parser bug on ECC 6.0) | `search_object()` returns clean list; `validate_new_object()` available |
| Atomicity | Program can leave DE created but TABL skeleton orphaned | Explicit `try/finally` with lock release; phases in result dict |
| Transport | Manual NEW REQUEST in BDC, or no transport | `create_transport()` + `corrNr` on every call |
| Activation | `DDIF_*_ACTIVATE` separate, errors silent | `activate(uri, ...)` returns activation result XML |
| Migration cost | N programs, N RC interpretation paths | One Python call per object |

---

## 14. Session #076 expansion — all new methods

24 methods added 2026-05-24. All additive; the 22 pre-existing methods (`fetch_csrf`, `search_object`, `get_source`, `set_source`, `lock`, `unlock`, `syntax_check`, `activate`, `write_class_source`, `write_program_source`, …) are unchanged.

| Group | Method | Purpose |
|---|---|---|
| Capability | `adt_discovery()` | Self-introspect — list 217+ collections this server supports |
| Generic creation | `create_object(type_id, name, desc, package, transport, parent)` | Covers 14 ABAP types via one entry point |
| DDIC primitives | `create_table`, `create_structure`, `create_data_element`, `create_domain`, `create_interface`, `create_message_class`, `create_function_group`, `create_package` | Skeleton-only creators (use `define_table` for atomic flow) |
| **DDIC handler** | `define_table()`, `build_table_source_xml()`, `add_table_field()` | **Atomic table create + fields + activate — replaces `DDIF_TABL_PUT` programs** |
| **DDIC handler** | `create_index()`, `build_index_source_xml()` | **Atomic secondary index create + activate** |
| Class includes | `class_include_uri()`, `set_class_include_source()`, `create_test_include()` | Proper `/sap/bc/adt/oo/classes/{name}/includes/{type}` scheme — closes 7 historical `write_ccimp_*.py` workarounds |
| Transport CI/CD | `create_transport()`, `transport_release()` | End-to-end TR lifecycle from Python |
| Debugger | `debugger_set_breakpoint`, `debugger_listen`, `debugger_attach`, `debugger_step`, `debugger_stack`, `debugger_variables`, `debugger_set_variable` | External breakpoint workflow — live incident diagnosis |
| ATC | `atc_run()`, `atc_worklist()` | Code Inspector quality gate before transport release |

### 14.1 NOT supported by ADT (must use Playwright SAPGUI)

| Object | Reason | Path |
|---|---|---|
| BOR (Business Object Repository, SWO1) | Legacy SAP, no public ADT endpoint | `lib/sap-transactions/SwoAutomation.js` (TBD) |
| Workflows (SWDD, SWE2/SWEC) | No public ADT endpoint for workflow editor | Playwright on SWDD; read-only via PFTAB/SWWWIHEAD |
| RFC destinations (SM59) | No public ADT endpoint | Playwright on SM59 |
| SLG1 application log read | Not in ADT | Use `BAL_LOG_SEARCH` RFC |
| Background jobs (SM37) | Not in ADT | Use `BAPI_XBP_*` RFC family |

### 14.2 NEW: BOPF business objects ARE supported

D01 discovery showed `/sap/bc/adt/bopf/businessobjects` is reachable. BOPF (Business Object Processing Framework) is the modern successor to BOR. New business objects should use BOPF + RAP, not legacy BOR.

---

## 15. DDIF Wrapper (RFC + DDIF_*_PUT) — the canonical path for DDIC on EhP8

This is the working, production-ready path for creating tables / data elements / domains on UNESCO's ECC 6.0 EhP8 systems. Same return-dict shape as the ADT methods, so callers stay portable when UNESCO migrates to S/4HANA.

> [!IMPORTANT]
> **VERIFIED END-TO-END 2026-05-24 against live D01.** Both DTEL and TABL creation flows produce ACTIVE objects with clean TADIR rows (no orphan). The DDIF wrapper remains the canonical RFC-headless path for single-object DDIC creation. **As of 2026-05-25, abapGit standalone is also available on D01** (see §16) — it becomes the STANDARD for any multi-object atomic deploy and for any object type the DDIF wrapper doesn't cover (CLAS/FUGR/ENHO/BSP/etc.).
>
> **Verified artifacts on D01 (`$TMP` package, owner JP_LOPEZ, 2026-05-24):**
> - DE `ZADTPYTST` (domain CHAR7, active) — created via `define_data_element_via_ddif`
> - TABL `ZADTPYTBL` (3 fields: MANDT/TKEY/TESTFLD, active, TRANSP) — created via `define_table_via_ddif`
> - Both have TADIR rows with `edtflag='X'`, `orphan=False`. The TR_TADIR_INTERFACE injection works.

### 15.1 Why this exists

- ADT REST endpoints for DDIC creation (`/sap/bc/adt/ddic/tables`, `/sap/bc/adt/ddic/tables/*/indexes`) shipped in NW 7.50. EhP8 = NW 7.40 → these endpoints return HTTP 404 (confirmed 2026-05-24 against D01 with empirical POST probe).
- The only available path on EhP8 is `DDIF_TABL_PUT` / `DDIF_DTEL_PUT` / `DDIF_DOMA_PUT` via `RFC_ABAP_INSTALL_AND_RUN`.
- That raw pattern has two well-known pain points (the **TADIR-orphan bug** and the **opaque RC=2 ambiguity**) that the wrapper mitigates.

### 15.2 TADIR-orphan bug — what it is and how the wrapper fixes it

**Symptom:** `DDIF_TABL_PUT` returns SY-SUBRC=0, the structure builds in DD02L/DD03L/DD09L, but the TADIR row is missing or has blank DEVCLASS. Result: object can't be transported, doesn't show up in SE03/SE10, and may give "functional but no TADIR" errors later.

**Empirical evidence on D01** (2026-05-24): 3 zombie tables in `AS4LOCAL='N'` state, all inherited from prior runs of this pattern without TADIR registration:
- `ZCRP_ATTACH` — inactive zombie
- `ZCRP_AUTH_AUDIT` — inactive zombie  
- `ZCRP_GL_MAP` — inactive zombie

**Wrapper mitigation:**
1. Calls `TR_TADIR_INTERFACE` with explicit PGMID/OBJECT/OBJ_NAME/DEVCLASS/AUTHOR **BEFORE** `DDIF_*_PUT`. Forces TADIR row creation cleanly.
2. Calls `RS_CORR_INSERT` with `SUPPRESS_DIALOG='X'` + `KORRNUM=<trkorr>` to add to a specific transport request (no popups in RFC context).
3. Calls `DDIF_*_PUT` with all 5 EXCEPTIONS named explicitly.
4. Calls `DDIF_*_ACTIVATE` with its EXCEPTIONS.
5. Post-creation: calls `verify_tadir()` (RFC read of TADIR) to confirm DEVCLASS is non-blank — flags the result as `orphan: True` if it is, so the caller knows manual SE03 cleanup is needed.

### 15.3 Opaque RC=2 — what it is and how the wrapper fixes it

**Symptom:** `DDIF_TABL_PUT` returns SY-SUBRC=2 and you have no idea why. The official `EXCEPTION` named `name_inconsistent` covers 5 different root causes:

| RC | Exception | Cause | Recovery |
|---|---|---|---|
| 1 | `not_executed` | TBL_NAME malformed | Validate charset/length |
| 2 | `name_inconsistent` | Name conflicts with existing TADIR OR referenced DE/DOMA missing | Re-run preflight (`preflight_data_element` + `preflight_domain` for every DE/dom in the field list) |
| 3 | `tabl_inconsistent` | PK not first / NOTNULL gap / CHAR with missing DTEL | Validate field order, key flags, DE resolvability |
| 4 | `put_failure` | Lock active, TR not open | Liberate lock (SM12), verify TR open |
| 5 | `put_refused` | DEVCLASS missing, no `S_DEVELOP` | Validate package + auth |

**Wrapper mitigation:**
- Pre-flight every referenced DE with `preflight_table_chain(fields)` using single-equality `RFC_READ_TABLE` queries against `DD04L` and `DD01L` (NEVER IN-lists — the 72-char OPTIONS bug breaks them on EhP8).
- Synthesizes ABAP that emits `PUT_RC=<n>` `CORR_RC=<n>` `ACT_RC=<n>` `TADIR_RC=<n>` markers in WRITES.
- Parses each marker → maps SY-SUBRC to named exception via internal dict (`_DDIF_TABL_PUT_RC` etc.) → returns structured Python dict with one phase per FM call.

### 15.4 Methods exposed

| Method | Purpose |
|---|---|
| `preflight_data_element(name)` | DD04L lookup (single-equality). Returns `{exists, active, domain}`. |
| `preflight_domain(name)` | DD01L lookup. Returns `{exists, active, datatype, leng}`. |
| `preflight_table_chain(fields)` | Bulk preflight every DE in a field list. Returns `{ready, missing_des, inactive_des, checked_count}`. |
| `verify_tadir(name, obj_class)` | Post-creation TADIR sanity. Returns `{exists, devclass, author, orphan}` — `orphan=True` flags the historical bug. |
| `define_domain_via_ddif(name, desc, datatype, leng, package, transport, decimals)` | Atomic domain create — TADIR → PUT → CORR → ACTIVATE → verify. |
| `define_data_element_via_ddif(name, desc, domain, package, transport, text_short)` | Atomic DTEL create — same chain. |
| `define_table_via_ddif(name, desc, package, fields, transport, delivery_class, skip_preflight)` | Atomic table create — preflight chain + same atomic chain. |

### 15.4b Live-verified example — DE + TABL chain (2026-05-24)

This is the actual proof, not pseudocode. Reproducible: run it again and you'll get the same result (assuming ZADTPYTST/ZADTPYTBL already cleaned up between runs).

```python
from sap_adt_client import from_env
c = from_env("D01")

# ── STEP 1: create a custom DE (CHAR7-backed) ────────────────────────────────
de_result = c.define_data_element_via_ddif(
    name="ZADTPYTST",
    description="ADT-py test DE",
    domain="CHAR7",          # CHAR7 verified to exist via preflight
    package="$TMP",
    transport="",            # $TMP = no transport (RS_CORR_INSERT will rc=4, expected)
    text_short="ADT test",
)
# de_result["phases"] →
#   {"rfc_call": "OK", "abap_compile": "OK",
#    "tadir_interface": {"rc": 0, "status": "OK"},
#    "put": {"rc": 0, "exception": "OK", "explanation": "DE written (inactive)"},
#    "corr_insert": {"rc": 4, "status": "FAILED"},      # OK in $TMP context
#    "activate": "OK",
#    "verify_tadir": {"exists": True, "orphan": False, "devclass": "$TMP", ...}}

# ── STEP 2: create a TABL using that DE for a field ──────────────────────────
tbl_result = c.define_table_via_ddif(
    name="ZADTPYTBL",
    description="ADT-py test table",
    package="$TMP",
    transport="",
    fields=[
        {"name": "MANDT",   "key": True,  "data_element": "MANDT"},
        {"name": "TKEY",    "key": True,  "data_element": "CHAR10"},
        {"name": "TESTFLD", "key": False, "data_element": "ZADTPYTST"},  # ← uses the DE we just made
    ],
)
# tbl_result["phases"] →
#   {"preflight": {"ready": True, "missing_des": [], "inactive_des": [], "checked_count": 3},
#    "rfc_call": "OK", "abap_compile": "OK",
#    "tadir_interface": {"rc": 0, "status": "OK"},
#    "put": {"rc": 0, "exception": "OK", "explanation": "Object written successfully"},
#    "corr_insert": {"rc": 4, "status": "FAILED"},      # OK in $TMP context
#    "activate": "OK",
#    "verify_tadir": {"exists": True, "orphan": False, "object": "TABL", ...}}
```

Verification via direct RFC reads (cross-check):

```
DD02L | ZADTPYTBL | A (active) | TRANSP | JP_LOPEZ
DD03L | 0001 | MANDT   | X | MANDT     | A
DD03L | 0002 | TKEY    | X | CHAR10    | A
DD03L | 0003 | TESTFLD |   | ZADTPYTST | A
```

The TABL is ACTIVE in DDIC, all 3 fields persisted with correct positions, key flags, and DE references. The TADIR row has `edtflag='X'`, `devclass='$TMP'`, `author='JP_LOPEZ'`, `orphan=False`. This is what "working" looks like.

### 15.4c `$TMP` vs transportable package — what differs

| Phase | `$TMP` package | Transportable package + open TR |
|---|---|---|
| `tadir_interface` | rc=0 (creates TADIR with devclass=$TMP) | rc=0 (same, devclass=ZCRP/etc) |
| `put` | rc=0 | rc=0 |
| `corr_insert` | **rc=4 expected** (cancelled — nothing to record) | rc=0 (object recorded in TR's E071) |
| `activate` | rc=0 | rc=0 |
| Object behavior | Active in DD02L/DD03L, **cannot be transported** | Active + listed in TR for transport to QAS/PRD |

For real deployment to flow through STMS to QAS/PRD, you MUST pass `transport=<TRKORR>` and use a transportable package. `$TMP` is for development scratch and tests only.

### 15.5 Canonical workflow on EhP8

```python
import sys
sys.path.insert(0, r"c:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\mcp-backend-server-python")
from sap_adt_client import from_env

c = from_env("D01")   # ← MANDATORY: D01 ONLY for new objects (R-D01-ONLY)

trkorr = "D01K9B0CBF"  # open workbench TR — create via SE10 if needed

fields = [
    {"name": "MANDT",   "key": True,  "data_element": "MANDT"},
    {"name": "CERT_ID", "key": True,  "data_element": "CHAR20"},
    {"name": "CERT_RQ", "key": False, "data_element": "CHAR7"},
    {"name": "CERT_NR", "key": False, "data_element": "CHAR7"},
    {"name": "ERDAT",   "key": False, "data_element": "ERDAT"},
]

# 1) Preflight EVERY DE — never IN-list, always single-equality
pf = c.preflight_table_chain(fields)
print(pf)
# {'ready': True, 'missing_des': [], 'inactive_des': [], 'checked_count': 5}

# 2) If missing_des: create the chain Domain → DE first
for de in pf["missing_des"]:
    # CHAR<N>: domain = CHAR<N> (datatype CHAR, length N)
    if de.startswith("CHAR"):
        c.define_domain_via_ddif(de, f"Char {de[4:]}", "CHAR", int(de[4:]), "ZCRP", trkorr)
        c.define_data_element_via_ddif(de, f"Char {de[4:]}", de, "ZCRP", trkorr)
    else:
        raise RuntimeError(f"Manual DE design needed for {de}")

# 3) Create the table — atomic, structured result
result = c.define_table_via_ddif(
    name="ZCRP_CERTHEAD",
    description="CRP Certificate Header",
    package="ZCRP",
    transport=trkorr,
    fields=fields,
)
print(result)
# {
#   'table': 'ZCRP_CERTHEAD',
#   'transport': 'D01K9B0CBF',
#   'phases': {
#     'preflight':       {'ready': True, ...},
#     'rfc_call':        'OK',
#     'abap_compile':    'OK',
#     'tadir_interface': {'rc': 0, 'status': 'OK'},
#     'put':             {'rc': 0, 'exception': 'OK', 'explanation': '...'},
#     'corr_insert':     {'rc': 0, 'status': 'OK'},
#     'activate':        'OK',
#     'verify_tadir':    {'exists': True, 'devclass': 'ZCRP',
#                         'author': 'JP_LOPEZ', 'orphan': False}
#   }
# }
```

### 15.5b Bugs fixed in Session #076 — apply both if running an older copy

**Bug #1 — WRITES table field name.** If you see `phases.put: "UNKNOWN — no PUT_RC marker in WRITES"`, your `_run_abap_program` reads the wrong field. On EhP8, `RFC_ABAP_INSTALL_AND_RUN` returns WRITES rows with field name `ZEILE` (German "Zeile" = line), not `TAB`/`MESSAGE` as the original code assumed. Fixed in `sap_adt_client.py:1678-1693` — fallback chain `ZEILE` → `TAB` → `MESSAGE` → any non-empty string.

**Bug #2 — EDTFLAG poisoning (TK035 trap).** *Verified empirically against D01 2026-05-24.* The wrapper called `TR_TADIR_INTERFACE` with `IV_SET_EDTFLAG='X'`, which marks the new object as "non-standard editor only". Result: object created, active in DDIC, TADIR clean — but SE11 refuses to open with message **TK035** ("You cannot edit object TABL X with the standard editor"). Fixed by changing `'X'` → `' '` at 3 sites: `sap_adt_client.py:1829` (DOMA), `:1915` (DTEL), `:2031` (TABL). All 3 lines now read `"    iv_set_edtflag       = ' '",  # ' ' = SE11-editable; 'X' = locked (TK035 trap, session #76)`.

**If you have already-poisoned objects from an old wrapper version**, repair via direct TADIR update:

```python
src = [
    "REPORT z_fix_edtflag.",
    "UPDATE tadir SET edtflag = ' '",
    "  WHERE pgmid = 'R3TR'",
    "    AND ( ( object = 'TABL' AND obj_name = 'YOUR_TBL1' )",
    "       OR ( object = 'DTEL' AND obj_name = 'YOUR_DE1' )",
    "       OR ( object = 'DOMA' AND obj_name = 'YOUR_DOM1' ) ).",
    "WRITE: / 'TADIR_UPDATED=', sy-dbcnt.",
    "COMMIT WORK.",
]
client._run_abap_program(src, 'Z_FIX_EDTFLAG')
```

**Diagnostic to find all poisoned objects in `$TMP`:**
```python
conn.call('RFC_READ_TABLE', QUERY_TABLE='TADIR', DELIMITER='|',
    OPTIONS=[{'TEXT': "DEVCLASS EQ '$TMP' AND EDTFLAG EQ 'X' AND AUTHOR EQ '<your-user>'"}],
    FIELDS=[{'FIELDNAME':'PGMID'},{'FIELDNAME':'OBJECT'},{'FIELDNAME':'OBJ_NAME'}])
```

**Architectural lesson (TIER_1):** abapGit deliberately defaults `iv_set_edtflag = abap_false` (`zif_abapgit_tadir.intf.abap:47`) and uses `RS_CORR_INSERT` (which never touches EDTFLAG) for all regular DDIC objects. `TR_TADIR_INTERFACE` with EDTFLAG=X is only correct for IDoc segments / generated proxies / objects with truly non-standard editors. See [`abapgit_integration/SKILL.md`](../abapgit_integration/SKILL.md) §9.1 for the full TADIR/EDTFLAG explanation.

**Verified live on D01 2026-05-24:**
- `ZADTPYTST` (DTEL), `ZADTPYTBL` (TABL), `ZADTPYTB2` (TABL) — all 3 confirmed SE11-editable after the EDTFLAG fix + TADIR repair. User confirmed "Funciono".

### 15.6 If any phase fails

The `phases` dict tells you exactly which step broke and why. Concrete recovery by phase:

| Phase | Status | Recovery |
|---|---|---|
| `preflight` | `ready=False`, `missing_des=[X]` | Create X first via `define_data_element_via_ddif` |
| `rfc_call` | `FAILED: ...` | Check VPN, pyrfc install, RFC creds in .env |
| `abap_compile` | `ERROR: ...` | The synthesized ABAP has a syntax issue → file a bug |
| `tadir_interface` | `rc != 0` | Check devclass exists + `S_DEVELOP` granted |
| `put` | `exception: name_inconsistent` | Re-run preflight (must be a DE not in your list) |
| `put` | `exception: tabl_inconsistent` | Check PK fields are at positions 0001..N first |
| `put` | `exception: put_refused` | Auth issue → SU53 |
| `corr_insert` | `rc != 0` | Transport not open / not yours — check SE10 |
| `activate` | `FAILED rc=2` | Incompatible structural change → manual SE14 conversion |
| `verify_tadir` | `orphan: True` | Object active but TADIR DEVCLASS blank → SE03 "Change Object Directory Entries" manual fix |

### 15.7 Cleanup of existing zombies (one-time)

Three zombie tables exist on D01 from prior runs without TADIR fix:
```
ZCRP_ATTACH       AS4LOCAL=N
ZCRP_AUTH_AUDIT   AS4LOCAL=N
ZCRP_GL_MAP       AS4LOCAL=N
```
Decision pending: activate (if needed by the project) or delete via `DDIF_TABL_DELETE` by RFC. Not blocking — they don't interfere with new creations.

### 15.8 When UNESCO migrates to S/4HANA

The methods `define_table` / `create_index` / `update_table_fields` / `add_table_field` / `convert_table` (S/4HANA-only, ADT REST native) are already implemented in the same client. To switch, callers update one import line and remove the `_via_ddif` suffix — same field-list shape, same return-dict shape. Forward-compatible.

### 15.9 Where abapGit fits

abapGit is a third deployment path with broader scope than ADT REST or the DDIF wrapper. Full mastery integrated below as §16-§24. **Status: INSTALLED on D01 as of 2026-05-25** — `ZABAPGIT_STANDALONE` active in `$TMP`. Installation required NO BASIS ticket and NO STRUST — workstation-bridge architecture (workstation fetches GitHub source, RFC pushes via `RPY_PROGRAM_INSERT`). abapGit is now the STANDARD for: multi-object atomic deploys (1 ZIP / 1 TR), Git lifecycle of Z code, D01↔workstation source sync, ANY of the 170+ supported object types where DDIF/ADT bridges are incomplete.

---

## 16. abapGit Overview + Install Status

abapGit is a Git client running INSIDE SAP. Reads/writes DDIC + ABAP objects to a /src tree on a Git remote OR offline ZIP. Production-tested for 10 years across 50K+ installs.

**Status on UNESCO D01 — 2026-05-25 empirical probe (10-way TADIR/TRDIR/TDEVC/TFDIR check + READ REPORT smoke test):**
- `TADIR PROG ZABAPGIT_STANDALONE` ✅ 1 row, package `$TMP`, AUTHOR `JP_LOPEZ`, CREATED_ON 20260525
- `TRDIR ZABAPGIT_STANDALONE` ✅ 1 row, SUBC=1 (executable)
- REPOSRC `r3state = A` (active) ✅
- `READ REPORT 'ZABAPGIT_STANDALONE' INTO ...` → 151,660 lines, first line `REPORT zabapgit_standalone LINE-SIZE 100.` ✅
- `TADIR ZCL_ABAPGIT*` = 0 (expected — standalone bundles all classes as LOCAL `LCL_*` privates inside the report; dev edition would expose them as `ZCL_*`)
- `TDEVC ZABAPGIT` = 0 (expected — using `$TMP`, no custom package)
- `TFDIR ZABAPGIT*_RFC*` = 0 (expected — no RFC wrappers yet; see §19.4 for next step)

→ **INSTALLED AS STANDALONE — usable via SAPGUI SE38 today for ALL object types abapGit supports.** For agent-driven RFC class-level API access (calling `cl_abapgit_objects=>serialize` from Python), dev edition install is the next strategic step.

**Install method actually used:** workstation-bridge architecture, no BASIS, no STRUST. See §19 for the exact playbook.

**Minimum kernel:** NW 7.02 SP08 (UNESCO's NW 7.40 is comfortably above — confirmed working).

## 17. abapGit Capability Inventory

Single dispatch rule: object type `X` → class `ZCL_ABAPGIT_OBJECT_X`. 170+ object types supported.

| Domain | Types | Status NW 7.40 |
|---|---|---|
| **DDIC** | TABL, TABL/DS (structure), DTEL, DOMA, TTYP, VIEW, SHLP, ENQU, INDX (embedded in TABL) | ✅ Full |
| **Source code** | PROG, INCLUDE, CLAS (+ all sub-includes), INTF, FUGR (+ all FMs + all includes), FUGS, MSAG, XSLT | ✅ Full |
| **Enhancements** | ENHO, ENHS, ENHC | ✅ Full |
| **Web/UI** | WAPA (BSP), WDYA, WDYN, SICF, SMIM | ✅ Full |
| **OData/Gateway** | IWSV, IWSG, IWMO | ✅ Full |
| **RAP (S/4HANA)** | SRVD, SRVB, BDEF, DDLS, DCLS, DDLX | 🟡 partial / ❌ NW 7.5+ |
| **Authorizations** | SUSO, SUSC, AGR, SUSH | ✅ Full |
| **Other** | TRAN, NROB, DOCT, SOBJ, WAPF, SHI*, 25+ AFF types | ✅ Most |

**NOT supported (use other tools):** BOR (legacy), RFC destinations (SM59), SICF activation state, STRUST certs, T-table row data (use SM30 + customizing TR), PFCG user assignments, number range intervals, RZ10/RZ11 parameters.

## 18. abapGit DECISION MATRIX — when to use which tool

### 18.1 By object type + task — abapGit-first priority order

**Read the columns left→right: STANDARD (abapGit) → BRIDGE (current EhP8 reality) → FUTURE (S/4HANA).** The middle column is what we use TODAY because abapGit is not yet installed. The left column is what we SHOULD be using and is the strategic target.

| Task | Object | **STANDARD = abapGit (target)** | BRIDGE today on D01 EhP8 (abapGit not installed) | FUTURE on S/4HANA |
|---|---|---|---|---|
| Create 1 table | TABL | abapGit pull `.tabl.xml` | DDIF wrapper §15 (bridge) | abapGit OR ADT REST §13 |
| Modify table structure | TABL | abapGit re-pull with updated `.tabl.xml` | TBD DDIF wrapper extension | abapGit OR ADT REST |
| Create 5+ DDIC objects atomically | many | **abapGit shines** — 1 ZIP / 1 TR | DDIF wrapper N× sequential (lose atomicity) | abapGit OR ADT REST |
| Create DE / domain | DTEL/DOMA | abapGit pull `.dtel.xml` / `.doma.xml` | DDIF wrapper (bridge) | abapGit OR ADT REST |
| Create secondary index | INDX | abapGit pull (embedded in `.tabl.xml`) | TBD DDIF wrapper | abapGit OR ADT REST |
| Create class with CCIMP/CCDEF/CCAU | CLAS | abapGit pull `.clas.abap` + sub-includes | ADT REST §15 `set_class_include_source` (bridge) | abapGit OR ADT REST |
| Create program + includes | PROG | abapGit pull `.prog.abap` + includes | ADT REST `write_program_source` (bridge) | abapGit OR ADT REST |
| Create FUGR + FMs | FUGR/FUNC | abapGit pull (1-shot all FMs in 1 TR) | ADT REST `write_function_source` (FG must pre-exist) | abapGit OR ADT REST |
| BSP / UI5 deploy | WAPA | abapGit pull `.wapa.xml` + assets | `@sap-ux/deploy-tooling` (Fiori Tools) | abapGit OR ADT REST |
| OData service registration | IWSV/IWSG | abapGit pull (regenerates from CLAS) | Playwright SEGW + /IWFND/MAINT_SERVICE (bridge) | abapGit OR ADT REST `publish_service_binding` |
| Enhancement implementation | ENHO | abapGit pull `.enho.xml` | ADT REST (bridge) | abapGit OR ADT REST |
| RAP business object | BDEF/SRVD/SRVB | abapGit pull (on NW 7.5+ only) | ❌ not on EhP8 | abapGit OR ADT REST `create_object` |
| CDS view | DDLS | abapGit pull `.ddls.asddls` | 🟡 partial on 7.40 SP08+ | abapGit OR ADT REST |
| Number range objects | NROB | abapGit pull `.nrob.xml` | RFC `NUMBER_RANGE_OBJECT_*` (bridge) | abapGit OR ADT REST |
| Message classes | MSAG | abapGit pull `.msag.xml` | RFC `RPY_MESSAGE_*` (bridge) | abapGit OR ADT REST `create_object('MSAG/N')` |
| Customizing rows (T-tables) | — | ❌ NOT abapGit scope | SM30 + customizing TR | Same |
| Auth objects + roles | SUSO/AGR | abapGit pull (careful w/ TR planning) | Manual SU21/PFCG | Same |
| RFC dest / SICF / SM59 / RZ10 | — | ❌ NOT abapGit scope | Manual GUI / Playwright | Same |

**Read the table this way:** for every row where abapGit appears in column 1 (STANDARD), the moment abapGit is installed on D01, **migrate the workflow to abapGit and deprecate the bridge tool for that row**. The bridges are not equivalents — they are temporary substitutes.

### 18.2 By workflow goal

| Goal | Recommended tool |
|---|---|
| Quick one-shot create of table or DE | DDIF wrapper §15 |
| Atomic multi-object DDIC deploy (5+ objects, all-or-nothing) | abapGit (if installed) |
| Version control of ABAP source (history, blame, diff) | abapGit only |
| PR-based code review | abapGit only |
| Disaster recovery — rebuild package from external source | abapGit offline ZIP only |
| Replicate D01 → QAS without STMS forward path | abapGit only |
| CI/CD: Git commit → SAP deploy automatically | abapGit + abapgit-api-rfc add-on |
| Branch-based parallel dev on Z code | abapGit |
| Move Z package between landscapes | abapGit export ZIP |
| Refactor with rollback confidence | abapGit (git revert + re-pull) |

### 18.3 Decision flow — abapGit-first

```
Need to create/modify DDIC or ABAP code in D01?
│
├── 1. abapGit installed on D01?
│   ├── YES → USE ABAPGIT (default for any supported type — DDIC, source, ENHO, BSP, etc.)
│   └── NO  → escalate BASIS ticket (§19, STRATEGIC PRIORITY)
│             continue below with BRIDGE tools meanwhile
│
├── 2. Object type abapGit supports (per §17 inventory)?
│   ├── YES (would use abapGit if installed):
│   │     ├── DDIC (TABL/DTEL/DOMA/INDX/VIEW/SHLP/ENQU/TTYP) → DDIF wrapper §15 (bridge)
│   │     ├── Source (PROG/CLAS/INTF/FUGR/FUNC/INCLUDE/ENHO/XSLT) → ADT REST §15 (bridge)
│   │     ├── BSP/UI5 (WAPA) → @sap-ux/deploy-tooling (bridge)
│   │     └── OData (IWSV/IWSG) → Playwright SEGW (bridge)
│   │
│   └── NO (abapGit can't cover): →
│         ├── Customizing rows (T-tables) → SM30 + customizing TR
│         ├── RFC destinations → Manual SM59 (or Playwright if recurring)
│         ├── SICF / RZ10 / BOR / PFCG user assignments → Manual GUI
│         └── Number range intervals (data) → RFC NUMBER_RANGE_INTERVAL_*
│
└── 3. Multi-object atomic? → Strong argument to install abapGit NOW (sequential bridge calls lose atomicity)
```

## 19. abapGit INSTALL PLAYBOOK — workstation-bridge architecture (NO BASIS, NO STRUST)

> [!IMPORTANT]
> **Component 1 (standalone) was installed 2026-05-25 with NO BASIS ticket and NO STRUST.** The workstation-bridge architecture (workstation fetches GitHub, RFC pushes to SAP) eliminates the SAP→GitHub HTTPS dependency that previously required BASIS. Component 2 (dev edition) and Component 3 (RFC API add-on) follow the same architecture and also do not need BASIS.

Three components — Component 1 ✅ DONE, Components 2-3 next:

| Step | Component | Status | Effort | Network |
|---|---|---|---|---|
| 1 | `ZABAPGIT_STANDALONE` (single program, ~150K lines) | ✅ **DONE 2026-05-25** | 15 min actual | None (workstation→RFC) |
| 2 | abapGit **developer version** (full `ZCL_ABAPGIT_*` Z-package, **required** for RFC class-level API) | ⏳ Next | 30 min | None (offline ZIP via standalone) |
| 3 | `abapgit-api-rfc` add-on (`ZABAPGIT_API_RFC_*` FMs for Python headless) | ⏳ After step 2 | 15 min | Same |

**Standalone alone covers:** all human-driven workflows via SAPGUI SE38 → `ZABAPGIT_STANDALONE` for ANY of the 170+ object types (§17). Tables, classes, programs, ENHO, BSP, OData services — all maintainable now.

**Standalone does NOT cover:** programmatic RFC calls to `cl_abapgit_objects=>serialize` from Python — those classes are LOCAL to the standalone report (`LCL_*`). Step 2 (dev edition) installs them as global `ZCL_ABAPGIT_*` TADIR objects.

### 19.1 Step 1 (DONE) — `ZABAPGIT_STANDALONE` install

Actual method used 2026-05-25 (not SE38 paste, not BASIS ticket — fully scripted, ~32s wall-clock):

**Scripts archived in `Zagentexecution/abapgit_install/`:**
- `zabapgit_standalone_2026-05-25.abap` — pinned source copy (151,660 lines, 4.86 MB)
- `install_via_rpy_v2.py` — the working installer
- `check_abapgit_installed.py` — 10-way TADIR/TRDIR/TDEVC/TFDIR probe (canonical verification)
- `verify_abapgit_state.py` — REPOSRC + READ REPORT smoke test

**Algorithm:**
```python
# 1. Workstation fetches official build from GitHub (no SAP HTTPS involved)
curl https://raw.githubusercontent.com/abapGit/build/main/zabapgit_standalone.prog.abap \
     -o zabapgit_standalone.abap

# 2. (Optional) Pre-clean if a prior PROG exists in $TMP
conn.call("RFC_ABAP_INSTALL_AND_RUN", MODE="F", PROGRAM=[
    {"LINE": "REPORT zdelete_zabapgit."},
    {"LINE": "DELETE REPORT 'ZABAPGIT_STANDALONE'."},
])

# 3. Insert via RPY_PROGRAM_INSERT — uses SOURCE_EXTENDED (ABAPTXT255, 255-char lines)
source_tab = [{"LINE": l} for l in open("zabapgit_standalone.abap").read().splitlines()]
conn.call("RPY_PROGRAM_INSERT",
          PROGRAM_NAME       = "ZABAPGIT_STANDALONE",
          TITLE_STRING       = "abapGit standalone bootstrap",
          SUPPRESS_DIALOG    = "X",            # auto-activates with SUPPRESS_DIALOG=X + $TMP
          DEVELOPMENT_CLASS  = "$TMP",
          SOURCE_EXTENDED    = source_tab)
```

**Why this path** (instead of the ADT REST `set_source` that's documented for source uploads elsewhere in this skill):
- ADT REST PUT `/sap/bc/adt/programs/programs/{name}/source/main` returns HTTP 423 `Resource INCLUDE not locked` on NW 7.40 EhP8 for PROGs in `$TMP`, regardless of lock URL (shell vs source/main) or lockHandle position (header vs qs param). The lock returned by `?_action=LOCK` is rejected by the subsequent PUT. Empirically reproduced 3 times 2026-05-25. **This is a kernel-version limitation, not a wrapper bug.**
- `RPY_PROGRAM_INSERT` is SAP-standard, RFC-enabled (FMODE='R' in TFDIR), accepts wide ABAPTXT255 source, and auto-activates with `SUPPRESS_DIALOG='X'` for `$TMP` objects. Bypass complete.

**Verification commands** (run after install):
```bash
python Zagentexecution/mcp-backend-server-python/check_abapgit_installed.py
# Expect: TADIR PROG ZABAPGIT* = 1, TRDIR ZABAPGIT* = 1

python Zagentexecution/abapgit_install/verify_abapgit_state.py
# Expect: REPOSRC r3state = A, READ REPORT lines = 151,660
```

### 19.2 Step 2 (next) — install developer edition offline via standalone

Workstation-bridge, no BASIS, no STRUST:

```
[Workstation]                                            [D01]
1. curl https://github.com/abapGit/abapGit/archive/main.zip -o abapgit_dev.zip
2. Upload ZIP to D01 filesystem path /usr/sap/D01/SYS/global/abapgit_install.zip
   via SXPG_COMMAND_EXECUTE / file_put via RFC                ↓
                                                              ZABAPGIT_STANDALONE
                                                              → New offline repo
                                                              → target package $ABAPGIT (local)
                                                              → Import ZIP from filesystem path
                                                              → "Pull (objects only)"
                                                              → deserialize ~1000 objects
                                                              → activate all
3. Verify: check_abapgit_installed.py should now show
   `TADIR ZCL_ABAPGIT* > 100` (was 0)
```

After step 2 completes, `cl_abapgit_objects=>serialize( )` is callable from any Z program (and from any Z RFC FM wrapper we build). The 4-FM workstation-bridge wrapper plan (Z_ABAPGIT_SERIALIZE / DESERIALIZE / ZIP_PACKAGE / UNZIP_TO_PACKAGE) becomes implementable.

### 19.3 Step 3 (after 2) — `abapgit-api-rfc` add-on

Optional. Pre-built RFC FMs from `https://github.com/abapGit/abapgit-api-rfc`. Same install pattern as step 2 (offline ZIP via standalone). Gives `ZABAPGIT_API_RFC_LINK`, `ZABAPGIT_API_RFC_PULL`, `ZABAPGIT_API_RFC_SWITCHBRANCH` ready to call from Python.

### 19.4 Alternative — build our own thin Z FM wrappers instead of using `abapgit-api-rfc`

After step 2, we have `cl_abapgit_objects=>*` and `zcl_abapgit_zip=>*` as global classes. A 4-FM wrapper (each ~30 LoC) exposes them for the workstation-bridge architecture without the third-party add-on:

| FM | Wraps | Purpose |
|---|---|---|
| `Z_ABAPGIT_SERIALIZE` | `cl_abapgit_objects=>serialize` | object → XML+source files (returned as table of strings) |
| `Z_ABAPGIT_DESERIALIZE` | `cl_abapgit_objects=>deserialize` | XML+source → object created in target package |
| `Z_ABAPGIT_ZIP_PACKAGE` | `zcl_abapgit_zip=>encode_files` | package → XSTRING ZIP (workstation receives ZIP) |
| `Z_ABAPGIT_UNZIP_TO_PACKAGE` | `zcl_abapgit_zip=>load` + deserialize | XSTRING ZIP → package (workstation sends ZIP) |

Decision (use `abapgit-api-rfc` vs build our own) deferred until step 2 is done.

## 20. abapGit WORKFLOWS

### 20.1 Offline pull (no internet from D01 — recommended)

```
[Local dev]                                  [D01]
git clone repo                                 ZABAPGIT_STANDALONE
git archive HEAD → repo.zip                          ↑
       ↓                                              │ New Offline → package → Import ZIP
scp/Teams/shared drive ────────────────────────→ ZIP loaded
                                                      ↓
                                              deserialize per file
                                                      ↓
                                              TR assigned, objects activated
```

### 20.2 RFC-headless pull (CI/CD, requires abapgit-api-rfc)

```python
from pyrfc import Connection

# Link once
conn.call('ZABAPGIT_API_RFC_LINK',
    ABAP_PACKAGE='ZCRP',
    GIT_REPO_URL='https://gitlab.unesco.org/sap/zcrp-objects.git',
    GIT_USER='deploy-bot',
    GIT_PASSWORD=os.environ['GH_PAT'],
    BRANCH='refs/heads/main')

# Pull every deploy
result = conn.call('ZABAPGIT_API_RFC_PULL',
    ABAP_PACKAGE='ZCRP',
    GIT_USER='deploy-bot',
    GIT_PASSWORD=os.environ['GH_PAT'],
    CORRNR='D01K9B0XXXX')

errors = [r for r in result['RETURN'] if r['TYPE'] == 'E']
```

**Critical caveat:** PULL FM auto-decides Y on all overwrite-local + warning-package decisions. It WILL silently overwrite local SE11 edits.

### 20.3 Online pull (HTTPS from SAP to Git)

Same as 20.2 but requires STRUST trust for github.com + SICF activation of `/sap/bc/abapgit`. UNESCO probably blocked by firewall — use offline.

### 20.4 Push (SAP → Git)

Only via UI. NO `_PUSH` FM in abapgit-api-rfc. Devs commit from `ZABAPGIT_STANDALONE` → Stage → Commit → Push (online) or Download ZIP (offline).

### 20.5 Branch switch

```python
conn.call('ZABAPGIT_API_RFC_SWITCHBRANCH',
    ABAP_PACKAGE='ZCRP',
    BRANCH_NAME='feature/cert-redesign',
    GIT_USER='deploy-bot',
    GIT_PASSWORD=os.environ['GH_PAT'])
# Then PULL to materialize
```

## 21. abapGit SERIALIZATION FORMAT

### 21.1 Repo root `.abapgit.xml`

```xml
<?xml version="1.0" encoding="utf-8"?>
<asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">
 <asx:values>
  <DATA>
   <MASTER_LANGUAGE>E</MASTER_LANGUAGE>
   <STARTING_FOLDER>/src/</STARTING_FOLDER>
   <FOLDER_LOGIC>PREFIX</FOLDER_LOGIC>
  </DATA>
 </asx:values>
</asx:abap>
```

**Important:** `.abapgit.xml` does NOT have outer `<abapGit serializer="...">` wrapper. All other object files DO.

### 21.2 Object envelope (every file except `.abapgit.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<abapGit version="v1.0.0" serializer="LCL_OBJECT_TABL" serializer_version="v1.0.0">
 <asx:abap xmlns:asx="http://www.sap.com/abapxml" version="1.0">
  <asx:values>
   <!-- type-specific structure -->
  </asx:values>
 </asx:abap>
</abapGit>
```

### 21.3 Per-type structures (canonical, observed in github.com/abapGit-tests/*)

- **TABL** — `<DD02V>` + `<DD09L>` + `<DD03P_TABLE>` + optional `<DD05M_TABLE>` `<DD08V_TABLE>` `<DD12V_TABLE>` `<DD17V_TABLE>` `<DD35V_TABLE>` `<DD36M_TABLE>` `<I18N_LANGS>` `<DD02_TEXTS>`
- **DTEL** — `<DD04V>` + optional `<I18N_LANGS>` `<DD04_TEXTS>`
- **DOMA** — `<DD01V>` + optional `<DD07V_TAB>` (fixed values) `<I18N_LANGS>` `<DD01_TEXTS>`
- **VIEW** — `<DD25V>` + `<DD26V_TABLE>` + `<DD27P_TABLE>` + `<I18N_LANGS>` `<DD25_TEXTS>`
- **SHLP** — `<DD30V>` + `<DD32P_TABLE>` + (collective only) `<DD31V_TAB>` `<DD33V_TAB>`
- **TTYP** — `<DD40V>` + optional `<DD42V_TAB>` `<DD43V_TAB>`
- **ENQU** — `<DD25V>` (reused) + `<DD26E_TABLE>` + `<DD27P_TABLE>`
- **Package `.devc.xml`** — `<DEVC><CTEXT>description</CTEXT></DEVC>`. Package name derived from folder.

### 21.4 Encoding rules (mandatory — get one wrong = silent import failure)

- **UTF-8 with BOM** (`xEF BB BF`)
- **LF line endings only** (no CRLF — `git config core.autocrlf false`)
- **2-space indent, no tabs**
- **Final newline at EOF**

abapGit's deserializer uses `accept_data_loss` — field order doesn't matter, missing fields tolerated. Python-generated XML viable without modeling every DDIC field.

## 22. abapGit TADIR/CTS handling — the EDTFLAG lesson

**Why this matters:** the EDTFLAG bug we just fixed (§15.5b) was rooted in a misunderstanding of TADIR conventions. abapGit gets this right by default.

### 22.1 EDTFLAG mechanics

- `TADIR.EDTFLAG = 'X'` → object refuses standard editor (SE11 raises message TK035 "You cannot edit object X with the standard editor")
- Set by `TR_TADIR_INTERFACE` parameter `IV_SET_EDTFLAG`
- abapGit interface defaults to `abap_false` ([zif_abapgit_tadir.intf.abap:47](https://github.com/abapGit/abapGit/blob/main/src/objects/core/zif_abapgit_tadir.intf.abap#L47))
- abapGit only flips it to `X` for IDoc segments (where `SEGMENT_CREATE` doesn't write TADIR itself)

### 22.2 RS_CORR_INSERT — abapGit's canonical path (preferred over TR_TADIR_INTERFACE for regular objects)

```abap
CALL FUNCTION 'RS_CORR_INSERT'
  EXPORTING
    object              = 'TABLZMYTAB'       " CONCATENATED: type + name
    object_class        = 'DICT'             " 'DICT' for DDIC, 'APPL' for source
    devclass            = 'ZCRP'
    master_language     = sy-langu
    mode                = 'I'                " I=insert, R=repair, D=delete
    global_lock         = abap_true
    suppress_dialog     = abap_true          " MANDATORY in RFC context
    korrnum             = 'D01K9B0XXXX'      " target TR (blank for $TMP)
  EXCEPTIONS
    cancelled = 1 permission_failure = 2 unknown_objectclass = 3.
```

- Writes TADIR (EDTFLAG stays blank — no TK035 trap)
- Inserts object into the TR's E071
- Suppresses popup (RFC-safe)
- `$TMP`: pass `korrnum=''`, returns OK without TR

### 22.3 Inactive (AS4LOCAL='N') is NOT required

`DDIF_TABL_PUT` writes N; `DDIF_TABL_ACTIVATE` promotes N→A and deletes N. When SE11 opens an A-only table for edit, it lazily creates N from A. **Missing N is not a bug.** Our DDIF wrapper produces A-only and SE11 opens fine (post-EDTFLAG-fix).

### 22.4 Auto-activation pattern

abapGit defers activation to a batch:
1. Per-object `DDIF_*_PUT` (queued in `gt_objects TYPE TABLE OF dwinactiv`)
2. After all objects in step: `DD_MASS_ACT_C3` with `frcact=X` (resolves cross-dependencies)
3. Fallback: `RS_WORKING_OBJECTS_ACTIVATE` (NW 7.40 SP-dependent dispatch)

Our DDIF wrapper activates inline per call. Both correct; abapGit's batch is better for cross-object chains.

## 23. abapGit LIMITATIONS + GOTCHAS

### 23.1 NW 7.40 specific
- No PUSH FM (devs push from UI)
- No offline-ZIP upload FM (ZIP import is UI-only)
- RAP types fail (BDEF, SRVD, SRVB, DCLS, DDLX — NW 7.51+)
- CDS DDLS partial (NW 7.40 SP08+)
- `DD_MASS_ACT_C3` may not exist on early SPs — abapGit dispatches dynamically with try/catch

### 23.2 abapGit policy
- **PULL is destructive** — auto-Y on overwrite-local. Don't point at packages with manual edits.
- One package per repo
- No coordination across SAP systems (git IS the source of truth)
- Customizing T-tables row-level NOT supported (object level yes)

### 23.3 abapgit-api-rfc requirements
- **Developer version REQUIRED** (standalone alone insufficient)
- Auth: `S_RFC` for `ZABAPGIT_API_RFC`, `S_DEVELOP` (ACTVT 01/02), `S_TRANSPRT` if transportable
- WP timeout risk on large pulls — use batch for big repos

## 24. abapGit PYTHON INTEGRATION (proposed wrappers for sap_adt_client.py)

When abapGit is installed, add these methods:

```python
# Online repo operations (require abapgit-api-rfc installed)
def abapgit_link(package, git_repo_url, git_user, git_password, branch='', folder_logic='PREFIX', starting_folder='/src/') -> dict
def abapgit_pull(package, git_user, git_password, transport='') -> dict
def abapgit_switch_branch(package, branch_name, git_user, git_password) -> dict
def abapgit_unlink(package) -> dict

# Status (read-only, only dev version needed)
def abapgit_repo_status(package) -> dict
def abapgit_serialize_package(package, out_dir) -> dict  # via Z_ABAPGIT_SERIALIZE_PACKAGE

# Local-only artifact builder (pure Python, no SAP)
def serialize_to_abapgit_format(objects_def: list, out_dir: str, package: str, ...) -> str

# Orchestrator
def abapgit_push_via_git_remote(out_dir, git_remote, branch, git_user, git_password, target_package, transport='') -> dict
```

Result-dict shape (consistent across all wrappers):
```python
{
    'success': bool,
    'messages': [{'type':'I'|'W'|'E', 'message': str, ...}, ...],
    'phases': {'migration': [...], 'lookup': [...], 'checks': [...], 'deserialize': [...], 'error': [...]},
    'package': str, 'transport': str, 'objects_deserialized': int,
}
```

### 24.1 Worked example — create `ZCRP_CERTHEAD` via abapGit (when installed)

```python
import os, subprocess
from sap_adt_client import from_env, serialize_to_abapgit_format, abapgit_link, abapgit_pull

# 1) Build local /src tree
objects = [{
    'type':'TABL', 'name':'ZCRP_CERTHEAD',
    'description':'CRP certification header',
    'delivery_class':'A', 'data_class':'APPL0',
    'fields':[
        {'name':'MANDT',   'rollname':'MANDT',       'key':True,  'notnull':True},
        {'name':'CERT_ID', 'rollname':'ZCRP_CERTID', 'key':True,  'notnull':True},
        {'name':'CERT_DT', 'rollname':'DATS'},
        {'name':'STATUS',  'rollname':'CHAR1'},
    ],
}]
serialize_to_abapgit_format(objects, out_dir='./build/zcrp-repo',
    package='ZCRP', folder_logic='PREFIX', starting_folder='/src/', master_language='E')

# 2) Push to internal Git remote
for cmd in [['git','init'],['git','add','.'],['git','commit','-m','ZCRP_CERTHEAD'],
            ['git','remote','add','origin','https://gitlab.unesco.org/sap/zcrp-objects.git'],
            ['git','push','-u','origin','main']]:
    subprocess.run(cmd, cwd='./build/zcrp-repo', check=True)

# 3) Link + pull on D01 (D01 only — per scope rule)
c = from_env('D01')
abapgit_link(package='ZCRP',
    git_repo_url='https://gitlab.unesco.org/sap/zcrp-objects.git',
    git_user='deploy-bot', git_password=os.environ['GITLAB_PAT'],
    branch='refs/heads/main')

result = abapgit_pull(package='ZCRP',
    git_user='deploy-bot', git_password=os.environ['GITLAB_PAT'],
    transport='D01K9B0XXXX')

assert result['success'], result['messages']
```

End state: `ZCRP_CERTHEAD` active in D01, TADIR clean (EDTFLAG=' '), on TR, SE11-editable, ready to transport to QAS/PRD via STMS.

## 26. OPERATIONAL RUNBOOK — Audit + Repair + Control (mandatory discipline)

This section is the operational discipline for any DDIC deployment via DDIF wrapper. Apply BEFORE and AFTER every deploy. Goal: zero "raro" findings.

### 26.1 Defect classes empirically observed in D01

| Defect class | Symptom | Detection query | Repair |
|---|---|---|---|
| **EDTFLAG poisoning** | TADIR.EDTFLAG='X' → SE11 raises TK035 on open | `RFC_READ_TABLE TADIR WHERE EDTFLAG EQ 'X' AND OBJECT EQ 'TABL'` | `UPDATE tadir SET edtflag=' ' WHERE ... + COMMIT WORK` |
| **TADIR-orphan** | DD02L has rows but TADIR missing OR DEVCLASS blank | `verify_tadir(name,'TABL')` returns `exists=False` or `orphan=True` | `TR_TADIR_INTERFACE` with explicit DEVCLASS + `iv_set_edtflag=' '` |
| **Inactive zombie** | DD02L AS4LOCAL='N' only, no 'A' row → table not really created | DD02L returns 1 row with AS4LOCAL='N' | Either re-activate (`DDIF_TABL_ACTIVATE`) or delete (`DDIF_TABL_DELETE`) |
| **Pattern incomplete** | DD02L=[A] only, DD09L=[A] only (missing 'L' / 'N' rows that production tables have) | DD02L returns 1 row with 'A', DD09L returns 1 row with 'A' | Cosmetic — table works in SE11. Recreate with current wrapper if cleanliness matters. |
| **Wrong namespace** | OBJ_NAME starts with anything other than Z*/Y*/customer-ns → standard object | Check name pattern | **REFUSE** — never modify standard (see [[feedback-never-modify-standard-objects]]) |

### 26.2 PRE-DEPLOY checklist (run BEFORE `define_*_via_ddif`)

```python
# 1. Verify D01 system (not P01)
assert c.host.endswith('D01.HQ.INT.UNESCO.ORG'), 'WRONG SYSTEM — must be D01'

# 2. Verify object name is Z* / Y* / customer namespace
assert name.upper().startswith(('Z', 'Y', '/')), f'REFUSED: {name} not in customer namespace'

# 3. Verify package is non-standard
assert package.upper().startswith(('Z', 'Y', '$', '/')), f'REFUSED: {package} not customer package'

# 4. Verify transport is open and modifiable (for non-$TMP)
if package != '$TMP':
    assert transport, 'transport required for non-TMP package'
    # OPTIONAL: check E070 for transport status='D' (modifiable)

# 5. Preflight DE chain
pf = c.preflight_table_chain(fields)
assert pf['ready'], f"missing DEs: {pf['missing_des']}, inactive: {pf['inactive_des']}"

# 6. Verify target doesn't already exist as zombie
existing = c.verify_tadir(name, 'TABL')
if existing['exists']:
    # decide: skip, delete-and-recreate, or abort
    raise RuntimeError(f'{name} already in TADIR — explicit decision needed')
```

### 26.3 POST-DEPLOY verification (run AFTER `define_*_via_ddif`)

```python
result = c.define_table_via_ddif(name, ..., fields=fields)

# Required: all phases OK
assert result['phases']['preflight']['ready'], 'preflight failed'
assert result['phases']['put']['rc'] == 0, f"PUT failed: {result['phases']['put']}"
assert result['phases']['activate'] == 'OK', 'ACTIVATE failed'

# Required: TADIR clean, no orphan, no EDTFLAG poisoning
vt = result['phases']['verify_tadir']
assert vt['exists'], 'TADIR row missing'
assert vt['orphan'] is False, f'TADIR orphan: devclass={vt["devclass"]}'
assert vt.get('edtflag', '') == '', f'EDTFLAG poisoned: {vt["edtflag"]!r}'

# Recommended: DD02L state matches production pattern (A + N)
# (Skip if not critical; pattern-incomplete is functional, just cosmetically different)
```

### 26.4 SCHEDULED AUDIT (run periodically, e.g., weekly)

```python
def audit_d01_jp_lopez_objects():
    """Find every JP_LOPEZ-owned DDIC object in D01 and classify state."""
    conn = c._get_rfc_connection()

    # 1. EDTFLAG poisoning across our owned objects
    poisoned = conn.call('RFC_READ_TABLE', QUERY_TABLE='TADIR', DELIMITER='|',
        OPTIONS=[{'TEXT': "AUTHOR EQ 'JP_LOPEZ' AND EDTFLAG EQ 'X' AND OBJECT EQ 'TABL'"}],
        FIELDS=[{'FIELDNAME':'OBJ_NAME'},{'FIELDNAME':'DEVCLASS'}])

    # 2. Inactive zombies (DD02L AS4LOCAL='N' only)
    # Iterate each TABL we own, check DD02L states

    # 3. Pattern-incomplete (A only, no L in DD09L)
    # Iterate each TABL, check DD09L

    # Return structured report
    return {
        'poisoned': poisoned,
        'zombies': [...],
        'incomplete': [...],
        'clean': [...],
    }
```

### 26.5 REPAIR procedures (one per defect class)

**Class A — EDTFLAG poisoning:**
```python
src = [
    "REPORT z_fix_edt.",
    "UPDATE tadir SET edtflag = ' '",
    "  WHERE pgmid = 'R3TR' AND object = 'TABL'",
    "    AND obj_name IN ('NAME1','NAME2',...).",
    "WRITE: / 'FIXED=', sy-dbcnt.",
    "COMMIT WORK.",
]
client._run_abap_program(src, 'Z_FIX_EDT')
```

**Class B — TADIR-orphan:**
```python
src = [
    "REPORT z_fix_tadir.",
    "CALL FUNCTION 'TR_TADIR_INTERFACE'",
    "  EXPORTING wi_tadir_pgmid='R3TR' wi_tadir_object='TABL'",
    "    wi_tadir_obj_name='YOUR_TBL' wi_tadir_devclass='ZCRP'",
    "    wi_tadir_author=sy-uname wi_tadir_masterlang='E'",
    "    iv_set_edtflag=' '",   # CRITICAL: blank, NOT 'X'
    "  EXCEPTIONS OTHERS=99.",
    "WRITE: / 'TADIR_RC=', sy-subrc.",
]
```

**Class C — Inactive zombie (AS4LOCAL='N' only):**

Two options:
- Re-activate via `DDIF_TABL_ACTIVATE` if structure is correct
- Delete via `DDIF_TABL_DELETE` and recreate cleanly with fixed wrapper

```python
# Option C-a: try to activate
src = [
    "REPORT z_act.",
    "CALL FUNCTION 'DDIF_TABL_ACTIVATE'",
    "  EXPORTING name = 'YOUR_TBL'",
    "  EXCEPTIONS OTHERS = 99.",
    "WRITE: / 'ACT_RC=', sy-subrc.",
]

# Option C-b: delete + recreate
src = [
    "REPORT z_del.",
    "CALL FUNCTION 'DDIF_TABL_DELETE'",
    "  EXPORTING name = 'YOUR_TBL'",
    "  EXCEPTIONS OTHERS = 99.",
    "WRITE: / 'DEL_RC=', sy-subrc.",
    "COMMIT WORK.",
]
# Then call c.define_table_via_ddif(...) fresh
```

**Class D — Pattern incomplete (A only, no L):**

Cosmetic. SE11 works. If perfect parity with production needed, delete + recreate.

### 26.6 GOLD-STATE reference

A table created with the **current fully-fixed wrapper** should match this pattern (proven 2026-05-25 with ZADTPYTB3):

| Table | Expected state |
|---|---|
| TADIR | 1 row, EDTFLAG=' ', GENFLAG=' ', DELFLAG=' ', DEVCLASS set correctly |
| DD02L | 2 rows: AS4LOCAL='A' + AS4LOCAL='N' |
| DD02T | 2 rows: per-language description for A + N |
| DD09L | 2 rows: AS4LOCAL='A' + AS4LOCAL='L' (technical settings active + log) |
| DD03L | N×2 rows: fields × versions |
| DDLOG | 0 rows (no activation errors) |
| E071 | 0 rows for $TMP; ≥1 row for transportable |
| `verify_tadir.orphan` | `False` |
| `verify_tadir.edtflag` | `''` |

If a new deploy doesn't match the GOLD pattern: investigate before declaring success.

### 26.7 Known broken-and-repaired log (D01, owner JP_LOPEZ, 2026-05-25)

| Object | Originally | Repaired to | Repair date | Notes |
|---|---|---|---|---|
| ZADTPYTBL | EDTFLAG=X, A-only | EDTFLAG=' ', A-only (still pattern-incomplete) | 2026-05-24 | test artifact, $TMP |
| ZADTPYTB2 | EDTFLAG=X, A-only | EDTFLAG=' ', A-only (still pattern-incomplete) | 2026-05-24 | test artifact, $TMP |
| ZADTPYTST | EDTFLAG=X | EDTFLAG=' ' | 2026-05-24 | DTEL, $TMP |
| ZADTPYTB3 | (created clean) | GOLD state | 2026-05-25 | first table with fully-fixed wrapper |
| ZCRP_CERT | EDTFLAG=X (poisoned by someone) | EDTFLAG=' ' | 2026-05-25 | production data preserved |
| **ZCRP_CERTHEAD** | EDTFLAG=X, **N-only (never activated)** | EDTFLAG=' ', **still N-only** | 2026-05-25 partial | needs decision: activate or delete+recreate |
| ZCRP_ATTACH, ZCRP_AUTH_AUDIT, ZCRP_GL_MAP | Inactive zombies (different owner) | Not yet addressed | — | author probably different — separate investigation |

---

## 25. References (primary sources)

### abapGit source (cite file:line when quoting)
- Object framework: https://github.com/abapGit/abapGit/blob/main/src/objects/zif_abapgit_object.intf.abap
- Object base: https://github.com/abapGit/abapGit/blob/main/src/objects/zcl_abapgit_objects_super.clas.abap (152-177: corr_insert)
- Factory: https://github.com/abapGit/abapGit/blob/main/src/objects/zcl_abapgit_objects.clas.abap (366-370: dispatch; 847-931: deserialize_step)
- Activation: https://github.com/abapGit/abapGit/blob/main/src/objects/core/zcl_abapgit_objects_activation.clas.abap
- CTS API: https://github.com/abapGit/abapGit/blob/main/src/cts/zcl_abapgit_cts_api.clas.abap (610-644: insert_transport_object)
- TADIR (EDTFLAG default = false): https://github.com/abapGit/abapGit/blob/main/src/objects/core/zif_abapgit_tadir.intf.abap (47)
- TABL serializer: https://github.com/abapGit/abapGit/blob/main/src/objects/tabl/zcl_abapgit_object_tabl.clas.abap
- Build/standalone: https://github.com/abapGit/build/blob/main/zabapgit_standalone.prog.abap

### abapgit-api-rfc
- Repo: https://github.com/abapGit/abapgit-api-rfc
- PULL FM: https://raw.githubusercontent.com/abapGit/abapgit-api-rfc/main/src/zabapgit_api_rfc.fugr.zabapgit_api_rfc_pull.abap
- LINK FM: https://raw.githubusercontent.com/abapGit/abapgit-api-rfc/main/src/zabapgit_api_rfc.fugr.zabapgit_api_rfc_link.abap

### docs.abapgit.org
- Install: https://docs.abapgit.org/user-guide/getting-started/install.html
- Repo settings: https://docs.abapgit.org/user-guide/repo-settings/dot-abapgit.html
- Import ZIP: https://docs.abapgit.org/user-guide/projects/offline/import-zip.html
- File formats: https://docs.abapgit.org/development-guide/serializers/file-formats.html

### Canonical test repos (serialization examples)
- TABL: https://github.com/abapGit-tests/TABL
- DTEL: https://github.com/abapGit-tests/DTEL
- DOMA: https://github.com/abapGit-tests/DOMA
- VIEW: https://github.com/abapGit-tests/VIEW

### SAP authoritative
- TADIR-EDTFLAG: https://www.sapdatasheet.org/abap/tabl/tadir-edtflag.html
- TK035 message: https://www.sapdatasheet.org/abap/msag/tk-035.html
- DDIF_TABL_PUT: https://www.sapdatasheet.org/abap/func/DDIF_TABL_PUT.html
- RS_CORR_INSERT: https://www.se80.co.uk/sapfms/r/rs_c/rs_corr_insert.htm
- TR_TADIR_INTERFACE: https://www.sapdatasheet.org/abap/func/tr_tadir_interface.html
- SAP KBA 3356317 (TK035 + generated tables)

### Internal evidence
- `sap_adt_client.py:1555-2089` — DDIF wrapper (verified live 2026-05-24)
- Brain claims #192-199 — empirical EhP8 capability gaps + bug fixes
- `knowledge/session_retros/session_076_retro.md` — full session learnings
