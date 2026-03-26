---
name: SAP Fiori Tools — App Modification & Service Reading
description: Guidelines for using the SAP Fiori Tools VS Code extensions and their underlying CLI tools to read Fiori app structure, visualize OData services, modify page layouts, and scaffold new applications. This is the THIRD skill pillar alongside Python RFC and ADT API.
---

# SAP Fiori Tools — App Modification & Service Reading

## Why This Skill Exists

The user's VS Code environment has the full **SAP Fiori Tools Extension Pack v1.20.3** installed.
These are NOT just UI tools — they expose **CLI-executable Node.js libraries** the agent can
invoke directly to read and modify Fiori applications without opening a browser.

> [!IMPORTANT]
> **Three Skill Pillars — Always pick the right one:**
> | Task | Use This Skill |
> |---|---|
> | Read SAP table data, mass extraction | `sap_reverse_engineering` (Python RFC) |
> | Read/Write ABAP source, BSP files | `sap_adt_api` (ADT REST HTTP) |
> | Modify Fiori app pages, read OData, scaffold | **This skill** (Fiori Tools CLI) |

---

## 1. Installed Extensions & Their CLI Capabilities

### 1.1 ABAP Remote Filesystem (`murbani.vscode-abap-remote-fs` v2.0.7)
**The most powerful agent tool.** Mounts SAP as a virtual filesystem via ADT.

**Confirmed ADT Connection (D01):**
```
URL      : http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80
Client   : 350
User     : jp_lopez
Auth     : HTTP Basic (password from settings.json or Windows Credential Manager)
```

**What it can do for the agent:**
- Browse full ABAP object tree as files
- Read/write any ABAP object source (classes, programs, BSP pages, UI5 apps)
- Uses exact same ADT endpoints as `sap_adt_api` skill — they are interchangeable

### 1.2 SAP Fiori Tools Extension Pack (`sapse.sap-ux-fiori-tools-extension-pack` v1.20.3)
Bundle of 10 extensions. The underlying npm packages can be used as CLI tools:

```
@sap/ux-ui5-tooling          — Fiori app tooling (build, serve, deploy)
@sap/ux-specification        — UI5 control spec for autocomplete
@sap/create-fiori            — Yeoman-based app generator
@sap/fiori-generator         — Template-based Fiori scaffolding
```

### 1.3 Application Modeler (`sapse.sap-ux-application-modeler-extension` v1.20.3)
Reads and modifies **Fiori app page structure** (Page Map, Page Editor).

**What it manages:**
- `manifest.json` — routes, navigation targets, data sources, models
- `webapp/ext/` — extension fragments and controllers
- `annotations/` — local and backend annotation files
- Fiori Elements page types: ListReport, ObjectPage, AnalyticalListPage

**Agent can modify Fiori apps by directly editing:**
```
manifest.json          → navigation, routing, service binding
webapp/view/*.xml      → UI5 views (direct XML manipulation)
webapp/controller/*.js → event handlers
webapp/ext/            → Fiori Elements extensions
```

### 1.4 Service Modeler (`sapse.sap-ux-service-modeler-extension` v1.20.3)
Visualizes OData services and their annotations.

**CLI approach — read metadata directly:**
```python
# ADT: GET /sap/opu/odata/{namespace}/{SRV_NAME}/$metadata
# Returns full EDMX describing all EntitySets, Properties, Associations
```

### 1.5 Connection Manager (`saposs.sap-ux-sap-systems-ext` v0.3.7)
Stores SAP system connection info in **Windows Credential Manager**.

**Agent can read stored systems via PowerShell:**
```powershell
cmdkey /list | Select-String -Pattern "SAP|sap|hq-sap|unesco"
# Then use DPAPI or SecretClient to retrieve passwords
```

---

## 2. Fiori App Structure — What the Agent Can Read & Modify

### Standard Fiori App Directory Layout:
```
webapp/
├── manifest.json          ← MASTER CONFIG — routes, OData sources, navigation
├── index.html             ← Entry point (BSP: served by SAP ICF)
├── Component.js           ← UI5 Component definition
├── view/
│   ├── App.view.xml       ← Root view
│   ├── Main.view.xml      ← Main list/object page
│   └── Detail.view.xml    ← Detail page
├── controller/
│   ├── Main.controller.js ← Event handlers
│   └── Detail.controller.js
├── model/
│   └── models.js          ← OData model initialization
├── i18n/
│   └── i18n.properties    ← Translations
└── localService/
    └── mainService/
        └── metadata.xml   ← Local OData metadata copy
```

### Key manifest.json Sections (for agent modifications):

```json
{
  "sap.app": {
    "dataSources": {
      "mainService": {
        "uri": "/sap/opu/odata/sap/{SRV_NAME}/",
        "type": "OData",
        "settings": { "odataVersion": "2.0" }
      }
    }
  },
  "sap.ui5": {
    "models": {
      "": { "dataSource": "mainService" }
    },
    "routing": {
      "routes": [...],
      "targets": {...}
    }
  }
}
```

---

## 3. Workflow: Reading a Fiori App from SAP

### Step 1: Get file list via RFC
```python
# O2PAGDIR WHERE APPLNAME = '{APP_NAME}'
# Returns: PAGENAME (relative path), MIMETYPE
```

### Step 2: Download each file via ADT
```
GET http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80/sap/bc/adt/bsp/applications/{APP}/pages/{PAGE}/source
Authorization: Basic base64(jp_lopez:password)
sap-client=350
```

### Step 3: Parse manifest.json
```python
import json
manifest = json.load(open('extracted_code/BSP_{APP}/manifest.json'))
odata_uri = manifest['sap.app']['dataSources']['mainService']['uri']
```

### Step 4: Fetch OData metadata
```
GET http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80{odata_uri}$metadata?sap-client=350
Authorization: Basic base64(...)
```

---

## 4. Workflow: Modifying a Fiori App

### Option A — Direct File Edit (Recommended for cloning)
1. Extract BSP files to local (via ADT download)
2. Modify `manifest.json`, views, controllers locally
3. Upload via ADT PUT to target BSP app

### Option B — Fiori Tools CLI (for scaffolding)
```bash
npx @sap/create-fiori --config config.json
```

### Option C — ADT Write Flow (for individual file updates)
```
1. GET CSRF token
2. POST {BSP_APP_URI}?_action=LOCK → lockHandle
3. PUT  .../pages/{PAGE}/source    (with lockHandle)
4. POST /sap/bc/adt/activation
5. DELETE lock
```

---

## 5. OData Service Reading via ADT

```python
# Read OData $metadata directly (no RFC needed)
url = f"http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80/sap/opu/odata/sap/{SRV}/$metadata?sap-client=350"
# Returns EDMX XML with all entities, properties, associations, function imports
```

---

## 6. Known Working Configurations

| System | ADT URL | Client | Auth |
|---|---|---|---|
| D01 | `http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80` | 350 | Basic Auth, jp_lopez |
| P01 | `http://HQ-SAP-P01.HQ.INT.UNESCO.ORG:80` | 350 | Basic Auth, jp_lopez |

> [!TIP]
> The port 80 configuration was **reverse-engineered from the ABAP remote filesystem VS Code plugin settings** at:
> `C:\Users\jp_lopez\AppData\Roaming\Code\User\settings.json`
> This is ground truth — it's what the working plugin uses in production daily.
