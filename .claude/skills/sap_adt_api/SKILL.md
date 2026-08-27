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


## Referencia detallada

Lo que sigue vive en **[reference.md](reference.md)** y se carga sólo si hace
falta — una skill cargada se queda en contexto todo el turno, así que aquí
queda lo que se lee ANTES de actuar y allí el detalle:

- **14. Session #076 expansion — all new methods**
- **15. DDIF Wrapper (RFC + DDIF_*_PUT) — the canonical path for DDIC on EhP8**
- **16. abapGit Overview + Install Status**
- **18. abapGit DECISION MATRIX — when to use which tool**
- **19. abapGit INSTALL PLAYBOOK — workstation-bridge architecture (NO BASIS, NO STRUST)**
- **20. abapGit WORKFLOWS**
- **21. abapGit SERIALIZATION FORMAT**
- **22. abapGit TADIR/CTS handling — the EDTFLAG lesson**
- **23. abapGit LIMITATIONS + GOTCHAS**
- **24. abapGit PYTHON INTEGRATION (proposed wrappers for sap_adt_client.py)**
- **26. OPERATIONAL RUNBOOK — Audit + Repair + Control (mandatory discipline)**
- **25. References (primary sources)**
