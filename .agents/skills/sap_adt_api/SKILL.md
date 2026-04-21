---
name: SAP ADT REST API Integration
description: Guidelines for programmatically deploying ABAP objects (Classes, Programs, Includes, Function Groups, BSP, OData Services) via the SAP ABAP Development Tools (ADT) REST API — the same interface used by the VSCode ABAP extension and Eclipse ADT. This is the PREFERRED method over RFC hacks or browser automation for source code operations.
domains:
  functional: [*]
  module: [BASIS, CTS]
  process: []
---

# SAP ADT REST API Integration

## Why ADT API?

The SAP ADT REST API is the **official, clean interface** for source code operations. It is used by:
- The **VSCode ABAP extension** (abap-remote-fs)
- **Eclipse ABAP Development Tools**
- The **mcp-abap-abap-adt-api** MCP server ([github.com/mario-andreschak/mcp-abap-abap-adt-api](https://github.com/mario-andreschak/mcp-abap-abap-adt-api))

> [!IMPORTANT]
> **Always prefer ADT API over RFC hacks** for source code writes. RFC functions like `RPY_PROGRAM_UPDATE`, `SIW_RFC_WRITE_REPORT` are often non-remote or dialog-dependent. ADT API handles locking, transport recording, and activation cleanly.

---

## 1. Prerequisites

- SAP ICF service `/sap/bc/adt` must be **active** (can check via SICF or test URL)
- User needs `S_DEVELOP` authorization
- Basic Auth over HTTP. **No SNC** for ADT (ADT uses HTTP, not RFC).

> [!IMPORTANT]
> **Confirmed working endpoint for D01** (reverse-engineered from ABAP remote filesystem VS Code plugin `settings.json`):
> - URL: `http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80`  (port **80**, NOT 8000 or 443)
> - Use **hostname**, NOT IP `172.16.4.66`
> - Protocol: **HTTP** (not HTTPS)

### Environment Variables Required
```
SAP_HOST=HQ-SAP-D01.HQ.INT.UNESCO.ORG   # Hostname, not IP!
SAP_CLIENT=350
SAP_USER=jp_lopez
SAP_PASSWORD=<password>                  # Plain password for HTTP Basic Auth
SAP_ADT_PORT=80                          # Port 80 HTTP — confirmed from abapfs plugin
SAP_ADT_HTTPS=false
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

## 12. Integration Status (Session #017)

| Integration | Status | Notes |
|-------------|--------|-------|
| `sap_adt_client.py` (custom Python) | ✅ Active | Stdlib only, proven on D01 |
| `mcp-abap-abap-adt-api` (MCP server) | 🟡 Not integrated | Available but not connected |
| VSCode ABAP Remote FS | ✅ Working | Confirmed same D01 endpoint |
| ADT→RFC fallback | ✅ Documented | Use RFC for reads, ADT for writes |
