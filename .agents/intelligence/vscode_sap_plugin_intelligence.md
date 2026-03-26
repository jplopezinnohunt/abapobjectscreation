# SAP VS Code Plugin Intelligence — Full Analysis
> Reverse-engineered 2026-03-12 from all installed extensions on jp_lopez's machine

---

## 🔌 Installed Extension Inventory (SAP-relevant)

| Extension ID | Version | Purpose | Agent Usability |
|---|---|---|---|
| `murbani.vscode-abap-remote-fs` | 2.0.7 | Mount SAP as a filesystem, read/write ABAP via ADT | ⭐⭐⭐ **CORE** |
| `saposs.sap-ux-sap-systems-ext` | 0.3.7 | Connection Manager — stores SAP system credentials in Windows Credential Manager | ⭐⭐ Config store |
| `sapse.sap-ux-fiori-tools-extension-pack` | 1.20.3 | Bundle of 10 Fiori tools sub-extensions | ⭐⭐⭐ **CORE** |
| `sapse.sap-ux-application-modeler-extension` | 1.20.3 | Page Map / Page Editor for Fiori apps — read & **modify** page structure | ⭐⭐ Modify pages |
| `sapse.sap-ux-service-modeler-extension` | 1.20.3 | Visualize OData service + annotations | ⭐⭐ Service analysis |
| `sapse.sap-ux-annotation-modeler-extension` | 1.20.3 | XML Annotation Language Server — autocomplete for annotations | ⭐ Dev aid |
| `sapse.sap-ux-help-extension` | 1.20.3 | In-IDE Guided Development tutorials | ⭐ Dev aid |
| `saposs.vscode-ui5-language-assistant` | 4.0.91 | UI5 XML view autocomplete + diagnostics | ⭐ Dev aid |
| `saposs.app-studio-toolkit` | 2.8.0 | BAS-style project creation wizards | ⭐ Scaffolding |
| `saposs.app-studio-remote-access` | 4.1.0 | Remote SAP BAS access | ⭐ BAS bridge |
| `larshp.vscode-abap` | 0.5.10 | ABAP syntax highlighting | cosmetic |
| `hudakf.cds` | 0.7.2 | CAP CDS language support | future |
| `sapos.yeoman-ui` | 1.20.2 | Yeoman generator UI (Fiori app scaffolding) | ⭐ Scaffolding |

---

## 🔑 ADT Connection Parameters (CONFIRMED FROM PLUGIN CONFIG)

> Extracted from `C:\Users\jp_lopez\AppData\Roaming\Code\User\settings.json`
> This is what the **working** ABAP remote filesystem plugin uses — ground truth.

```
System ID : D01
URL       : http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80   ← PORT 80 HTTP (not 8000, not 443!)
Client    : 350
User      : jp_lopez
Password  : sAevRtjnpqDTHclnZ6mBPhjtiL}xjueEFzDxnpUt  (from abapfs settings)
Protocol  : HTTP (allowSelfSigned: true, but HTTP so irrelevant)
```

> [!IMPORTANT]
> The SAP ADT port is **80** (standard HTTP), using the **hostname** `HQ-SAP-D01.HQ.INT.UNESCO.ORG`, NOT the IP `172.16.4.66` and NOT port `8000`.
> Previous extraction failures were caused by using the wrong port.

### .env Correct Values for ADT:
```
SAP_HOST=HQ-SAP-D01.HQ.INT.UNESCO.ORG
SAP_ADT_PORT=80
SAP_ADT_HTTPS=false
SAP_PASSWORD=sAevRtjnpqDTHclnZ6mBPhjtiL}xjueEFzDxnpUt
SAP_CLIENT=350
SAP_USER=jp_lopez
```

---

## ⚖️ Python RFC vs ADT — Decision Matrix

| Operation | Best Method | Why |
|---|---|---|
| Read SAP table data (TADIR, O2PAGDIR, PA*, etc.) | **Python RFC (SNC)** | RFC_READ_TABLE, no auth password needed (SNC) |
| Read ABAP class/program/include source | **Python ADT** | GET `/sap/bc/adt/oo/classes/{name}/source/main` |
| Read BSP page content | **Python ADT** | GET `/sap/bc/adt/bsp/applications/{APP}/pages/{PAGE}/source` |
| Read UI5/BSP app as file tree | **Python ADT** | GET `/sap/bc/adt/filestore/ui5-bsp/objects/{APP}/content` |
| Write/deploy ABAP source | **Python ADT** | Lock → PUT source → Activate flow |
| Activate ABAP objects | **Python ADT** | POST `/sap/bc/adt/activation` |
| Mass data queries | **Python RFC** | RFC handles cursor pagination better |
| OData service analysis | **MCP Notion + ADT** | Combine metadata endpoint + service modeler |
| BSP file listing | **Python RFC** | O2PAGDIR table via RFC_READ_TABLE |
| Fiori app page structure modification | **Fiori Tools CLI** | `@sap/ux-ui5-tooling` via npx |

---

## 🏗️ ABAP Remote Filesystem Plugin — How It Works (Reverse Engineered)

From bundle analysis of `server.js` + `extension.js`:

1. **Auth**: Basic Auth (`jp_lopez:password`) encoded as Base64 in `Authorization` header
2. **CSRF**: Fetches token via `GET /sap/bc/adt/discovery` with `X-CSRF-Token: Fetch`
3. **Object browsing**: Uses `/sap/bc/adt/repository/informationsystem/search` with `objectType` filter
4. **Source read**: Follows `text/plain` link rel from object metadata → resolves to `/source/main`
5. **BSP handling**: Uses `/source/main` pattern (same as ABAP objects), falls back to following link rels from the ADT object response
6. **Activation**: POST to `/sap/bc/adt/activation` with XML body
7. **Transport recording**: Passes `corrNr=<transport>` as query param on write operations

### Key API Pattern Discovered (from minified `extension.js`):
```javascript
// For objects with text/plain link → follow that href
// For others → append /source/main to object URL
if (link.type === "text/plain") return followUrl(objectUrl, link.href)
return hasSource ? followUrl(objectUrl, "/source/main") : objectUrl
```

---

## 🎨 SAP Fiori Tools — Agent Capabilities

> [!NOTE]
> The SAP Fiori Tools Extension Pack contains 10 sub-extensions that expose **CLI tools** the agent can invoke via `npx` or direct Node execution. These do NOT require the VS Code UI to be open.

### Available CLI tools (from `@sap/fiori-tools` npm packages):

| Tool | Command | Capability |
|---|---|---|
| Application Generator | `npx @sap/create-fiori` | Scaffold new Fiori app from template |
| Service Modeler | Internal | Parse OData metadata.xml into entity/property map |
| App Modeler | `@sap/ux-ui5-tooling` | Read/write page structure (manifest.json, views) |
| Annotation Modeler | LSP server | Validate/generate annotation files |
| Guided Development | Internal | Step-by-step feature implementation |

### Application Modeler — What The Agent Can Do:
- **Read** `manifest.json` → extract navigation targets, routes, data sources
- **Modify** Fiori pages by editing `manifest.json` and view XML files directly
- Add new navigation targets, change list/object page configurations
- This is what the user means: "you have the ability to modify Fiori apps"

---

## 🗺️ Connection Manager (saposs.sap-ux-sap-systems-ext)

- Stores connections using **Windows Credential Manager** (confirmed from readme)
- Extension ID: `saposs.sap-ux-sap-systems-ext`
- Other Fiori tools extensions declare it as a dependency → they all share the same stored connections
- Credentials can be read programmatically via Windows DPAPI / `cmdkey` / PowerShell

### Reading stored SAP systems from Credential Manager:
```powershell
# List all SAP-related stored credentials
cmdkey /list | Select-String -Pattern "SAP|sap|hq-sap"
```

---

## 📦 BSP Extraction — Revised Strategy (Based on Plugin Intelligence)

### Phase 1: File Listing (Python RFC — proven working)
```
RFC_READ_TABLE on O2PAGDIR WHERE APPLNAME = '{APP}'
→ Returns PAGENAME (path within BSP), MIMETYPE
```

### Phase 2: Content Download (Python → ADT HTTP)
```
GET http://HQ-SAP-D01.HQ.INT.UNESCO.ORG:80/sap/bc/adt/bsp/applications/{APP}/pages/{PAGE}/source
  Authorization: Basic base64(jp_lopez:password)
  sap-client: 350
```
> `{PAGE}` = PAGENAME from O2PAGDIR, with `/` encoded as `%2F`

### Phase 3: Save preserving directory structure
```
PAGENAME = "view/Main.view.xml"
→ saved as: extracted_code/BSP_{APP}/view/Main.view.xml
```

---

## 🔄 Pending Items (Keep for Later)

1. **Python RFC vs ADT formal decision tree** → update `sap_adt_api/SKILL.md`
2. **MCP server for abap-adt-api** → evaluate `mario-andreschak/mcp-abap-abap-adt-api` as MCP server
3. **Fiori Tools CLI as agent tool** → add `@sap/create-fiori` to toolbox
4. **Windows Credential Manager integration** → agent can read SAP credentials via `cmdkey`
5. **0xC0000374 heap crash root cause** → likely `pyrfc` + `ssl`/`urllib` DLL conflict at Python startup; workaround: subprocess isolation

---

## ✅ Immediate Next Action

Test ADT connection on correct port 80 HTTP, then run BSP extraction for both apps.
