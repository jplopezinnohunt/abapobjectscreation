---
name: SAP Transport Order Intelligence
description: >
  Two-scenario protocol for reading, classifying, and reasoning about SAP transport
  orders. Scenario A: Single transport pre-import review (should this go to production?).
  Scenario B: Bulk historical CTS mining (pattern analysis across thousands of transports).
  Covers transport anatomy, OBJFUNC semantics, module-specific risk, Fiori domain
  objects, Security objects, artifact detection, and AI classification pipeline.
  Use this skill whenever analyzing the content or impact of any SAP transport request.
---

# SAP Transport Order Intelligence Skill

> **Source authority**: Julio's Architecture Knowledge Base (March 2026) + Module Supplement (HR, PSM-FM, PS, Bank, FI) + UNESCO CTS 10-year mining experience + Web research on Fiori/Security transport chains.

---

## NEVER Do This

> [!CAUTION]
> - **Never trust SE09/SE10 as the truth** — it shows what was registered, NOT what was exported. Always cross-check with export log RC.
> - **Never transport T001B (Posting Periods) to production** — it immediately overwrites which accounting periods are open. Use OB52 directly in production.
> - **Never transport NROB (Number Ranges) to production** — it resets current number counters causing duplicate FI/MM/SD document numbers.
> - **Never assume OBJFUNC blank = safe** — blank is standard overwrite, but D=delete and M=wipe+recreate require explicit human approval.
> - **Never treat TABU entries without E071K — the analysis is incomplete** without the specific row keys.
> - **Never transport AGR_USERS (user role assignments) if CUA is active** — it overwrites user assignments globally.
> - **Never transport PROJ or PRPS (PS Master Data)** — project definitions and WBS elements should never travel via CTS. Investigate origin if found.
> - **Never transport FMDERIVE values to production directly** — transport structure only; set values manually in production.
> - **Never transport SICF node activation states via standard transport** — use mass activation tool RS_ICF_SERV_MASS_PROCESSING.

---

## The Two Scenarios

### SCENARIO A — Single Transport Pre-Import Review
*Question: "Should this transport go to production?"*

Used when reviewing a specific TRKORR before import into QA or Production. Goal: produce a RISK SCORE and SIGN-OFF REQUIREMENT for each transport.

### SCENARIO B — Bulk Historical CTS Mining
*Question: "What patterns do I see across 10 years of transports?"*

Used for intelligence dashboards (like `cts_dashboard.html`). Goal: classify tens of thousands of E071 rows into modules, risk tiers, object categories, and contributor patterns.

Both scenarios use the same underlying data model but different analytics.

---

## Part 1 — Transport Anatomy: The Three Layers of Truth

| Layer | Where | What it tells you |
|-------|-------|-------------------|
| **Database (E07x)** | Tables E070, E071, E071K, E07T, E070C | Request header, object list, table keys, client info |
| **Cofile (K\*.SID)** | `/usr/sap/trans/cofiles/` | Command manifest — what R3trans will DO |
| **Datafile (R\*.SID)** | `/usr/sap/trans/data/` | Actual binary payload — real exported data |

### Key E07x Tables

| Table | Purpose | Critical Fields |
|-------|---------|-----------------|
| **E070** | Request/Task header | `TRKORR`, `TRFUNCTION` (K/W/T/R/S), `TRSTATUS`, `TARSYSTEM`, `AS4USER`, `AS4DATE` |
| **E071** | Object list | `PGMID`, `OBJECT`, `OBJ_NAME`, `OBJFUNC`, `LOCKFLAG` |
| **E071K** | Table row keys | `TABKEY` — for TABU objects: which specific rows travel. **MANDATORY to read.** |
| **E07T** | Description text | `AS4TEXT` — human-readable transport description |
| **E070C** | Client info | Source client of customizing request |
| **TADIR** | Repository index | `DEVCLASS` (package), `SRCSYSTEM` — cross-ref for package ownership |

### The PGMID / OBJECT / OBJ_NAME Triple

| PGMID | OBJECT | Example OBJ_NAME | Meaning |
|-------|--------|-----------------|---------|
| R3TR | PROG | ZMYREPORT | Full ABAP program: source + text + properties |
| LIMU | REPT | ZMYREPORT | ONLY the text elements (subobject — avoid) |
| R3TR | TABU | T001 | Table content rows (data). Keys in E071K. |
| R3TR | TABL | ZMYTABLE | Table DEFINITION (DDIC structure, fields). No data. |
| R3TR | CLAS | ZCL_HR_FIORI | Full ABAP class: all methods, attributes, interfaces |
| R3TR | FUGR | ZFGR_NAME | Entire function group — ALL FMs replaced on import |
| LANG | PROG | ZMYREPORT | Language-specific translations only |

> [!IMPORTANT]
> **R3TR = full/group object. LIMU = subobject (a piece).** Always transport R3TR. A LIMU-only transport leaves a partially-consistent object in the target.

---

## Part 2 — Request Types (E070.TRFUNCTION)

| Type | Code | Scope | Typical Objects |
|------|------|-------|----------------|
| **Workbench** | K | Client-independent (all clients) | PROG, CLAS, FUGR, TABL, VIEW, DTEL, DOMA, DEVC, TRAN, SICF, IWSG, IWOM, SUCU |
| **Customizing** | W | Client-specific | TABU rows, SOBJ, logical objects via SPRO |
| **Transport of Copies** | T | One-time manual. No lock. | Emergency patches, lateral copies |
| **Relocation with development** | R | Object moves packages. Original locked. | TADIR re-assignment |
| **Relocation without development** | S | Package change, less traceable | |

---

## Part 3 — OBJFUNC: The Action Flag (Most Misunderstood Field)

> [!WARNING]
> Most consultants ignore OBJFUNC. It changes the nature of the transport completely.

| OBJFUNC | Action | Full Behavior |
|---------|--------|---------------|
| **` ` (blank)** | Standard transport | Object exported as-is. If exists in target → overwrite. If not → create. |
| **D** | Delete | Object was deleted in source before release. R3trans removes it from target. ONLY works if object does NOT exist in source at export time. |
| **M** | Delete + Recreate | **CRITICAL for TABU**: ALL rows of the table in target are deleted first, then source rows inserted. Entire table wipe. |
| **K** | Key-based selection | Only rows matching E071K keys are transported. Standard for selective TABU. |
| **I** | Insert all rows | Additive — doesn't delete existing target rows. Risky if keys overlap. |

> [!CAUTION]
> **The Ghost Entry Trap**: Developer creates a TABU entry → saves to transport → deletes before release. SE09/E071 still shows the entry. OBJFUNC=' ' (blank). R3trans finds nothing at export time → nothing travels. Always verify via export log, not the object list.

---

## Part 4 — Object Type Classification Taxonomy

### 4.1 Development / Repository Objects (Workbench Request K)

| OBJECT | Name | Risk | New vs Modified |
|--------|------|------|-----------------|
| PROG | ABAP Program | MEDIUM | New: full program created. Modified: source/text/attributes changed. Whole PROG transported. |
| CLAS | ABAP Class | MEDIUM | New: complete OO class. Modified: any method/attribute/interface. Full class contract may change silently. |
| FUGR | Function Group | HIGH | Modified: transporting FUGR replaces ALL FMs in target — not just the changed one. |
| TABL | DB Table Definition | HIGH | New: empty table created. Modified: field change. Field deletion breaks programs using the table. |
| VIEW | DB/Maint View | MEDIUM | Modified: selection or joins changed. Maintenance view change affects SM30 access. |
| DTEL | Data Element | LOW | Modified: usually label. High risk only if domain/type assignment changed. |
| DOMA | Domain | HIGH | Fixed values added/removed → validation logic changes for ALL fields using this domain. |
| TRAN | Transaction | LOW | New: t-code entry. Modified: program/screen changed. |
| DEVC | Package | LOW | Package metadata. Rarely causes issues. |
| NROB | Number Range | CRITICAL | Logical object. Resets current number counter in target → duplicate document numbers. |
| XPRA | Post-Import Program | HIGH | **EXECUTES after import**. Review code before import. Not just code — it runs. |
| ENQU | Lock Object | MEDIUM | Locking granularity changed → deadlocks or missing locks. |
| INTF | ABAP Interface | MEDIUM | Modified: interface contract changed → all implementing classes must be re-transported. |
| SHLP | Search Help | LOW | F4 help behavior changes. |

### 4.2 Customizing / Table Content Objects (Customizing Request W)

> [!WARNING]
> TABU looks simple but semantic meaning depends entirely on WHICH table it points to. Always check E071K.

| Table (OBJ_NAME) | Module | New vs Modified — Business Impact |
|-----------------|--------|-----------------------------------|
| T030 / T030R | FI | CRITICAL: G/L account determination. Modified = future financial postings go to wrong accounts silently. |
| T001B | FI | CRITICAL: posting period status. **Never transport to production.** Import = immediate period lock/unlock. |
| T001 | FI | New row = new company code (rare). Modified = currency/country high risk. |
| SKA1 | FI | New GL account at chart of accounts level. Modified = P&L vs Balance Sheet reclassification. |
| SKB1 | FI | Company-code GL properties. Modified = open item management on live account with balances = data inconsistency. |
| T011 / FAGL_T011 | FI | Financial Statement Version. Modified = balance sheet report shows different results immediately. |
| T004F | FI | Field Status Groups. Modified optional→required field = all posting transactions that didn't provide it fail. |
| T003 | FI | Document Types. Modified = reversal doc type change → can prevent reversal of posted documents. |
| T880 | FI | Global company parameters. Always CRITICAL post go-live. |
| T512W | HR | CRITICAL: Wage type valuation. Modified = payroll calculation changes for all employees. |
| T511 | HR | Wage type catalog. New = new wage type. Without this, T512W has no meaning. |
| T549A | HR | Payroll accounting areas. Modified = payroll period logic changes. Can prevent payroll from running. |
| T549Q | HR | Payroll periods calendar. Modified = period end dates changed. Requires payroll sign-off. |
| T510 | HR | Pay scale groups. Modified = salary amount changes → all TARIF employees recalculated next run. |
| T554S / T554C | HR | Absence types/valuation. Modified payroll relevance → retroactive corrections triggered. |
| T043 | PSM | AVC Tolerance Keys. Increased tolerance = less budget enforcement. Requires CFO sign-off. |
| FMCI / FM01 | PSM | Commitment Items + FM Area. Together = FM structural reconfiguration. High sequencing risk. |
| T012 / T012K | Bank | House banks and accounts. Modified = GL reconciliation account for payments. |
| T042Z | Bank | Payment method-country. Modified = DMEE format changes on next F110 run. |
| T001W | MM | Plant definition. New = new plant. Modified = MM/PP impact. |
| T156 | MM | Movement types. Modified = account determination/reversal changed. Affects goods movements. |
| TVARVC | Basis | Program parameters/variants. Modified = background job selection behavior changes silently. |
| UST04 | Security | User authorization profile assignments. New/deleted = user gets or loses access. |
| PROJ / PRPS | PS | **ALARM: master data in transport.** Should never be in CTS. Investigate immediately. |

### 4.3 SAP-Generated Artifacts (False Positives — Do Not Misinterpret)

| Artifact Object | Parent Object | Auto-Generated By | Risk if NOT transported |
|-----------------|--------------|-------------------|------------------------|
| TABU TDDAT | Custom Table (TABL) | SE54 (table maintenance generator) | SM30 inaccessible — auth group missing |
| FUGR Z\*_MAINT / Z\*_GEN | Maintenance View | SE54 | SM30 maintenance fails |
| SICF nodes | OData service (SEGW) | Service activation | Fiori app returns HTTP 404 |
| IWSG / IWOM | SEGW OData project | SEGW project build | 'Service not found' in Fiori Launchpad |
| LIMU REPT | PROG | Text element modification | Code/text inconsistency → runtime dumps |
| XPRA | Data migration | Explicit developer add | Migration step skipped silently |
| TABU CWBNTCUST | OSS Note | SNOTE application | Note shown as not implemented |

> [!WARNING]
> **FUGR Overwrite Trap**: A FUGR from SE54 (auto-generated) replaces ALL FMs in the group. If target has FM A, B, C, D and source only has A, B, C — after import D is GONE. Always compare FUGR contents before importing.

---

## Part 5 — Module-Specific Intelligence

### 5.1 HR / HCM — The Most Different Module

HR transport behavior is fundamentally different from all other modules:
- **PA tables (PA0001–PA9999)** = operational employee data. NOT transported via CTS. Transporting PA data rows is exceptional and dangerous.
- **PD/OM tables (HRP1000–HRP1999)** = Org Management objects. NOT via standard CTS. Use **RHMOVE30** (creates a PD data file with evaluation path).

**After any OM transport via RHMOVE30:**
1. Run **RHINTE10** — syncs PD objects into PA integration tables (T528T, T527X)
2. Run **RHINTE20** — consistency check between PA and PD
3. Run **RHINTE30** — updates infotype 0001 for employees when OM data changes

**Payroll Schema and PCR (Most Dangerous HR Objects):**

| Object | Transport Type | Risk |
|--------|---------------|------|
| Payroll Schema (e.g. ZU00) | R3TR PROG (special) | CRITICAL. Modifies entire payroll calculation sequence. |
| PCR (Personnel Calc Rule) | R3TR PROG (special) | HIGH. Single wrong PCR corrupts payroll result table (RT). |
| Feature (PINCH, TARIF, etc.) | R3TR DECI | HIGH. Decision tree for schema/PCR/WT selection. |

> [!CAUTION]
> PCRs are versioned. Transporting TR1 AFTER TR2 OVERWRITES the newer change. Never skip, never re-transport an old version. Before any payroll transport to production: run `PC00_M99_CALC_SIMU` on a sample population.

### 5.2 PSM-FM — Budget Control Is the Risk

- **FMDERIVE** is a special export (not SE09): use FM → Derivation → Extras → Transport
- Transport structure ONLY, not values — values reference master data that may not exist in target
- Error FINB_TR032 = RFC/TLOGOCHECK issue → check SAP Note 666322

**BCS Activation Sequence (irreversible):**
1. Activate EA-PS extension (cross-client workbench TR)
2. Activate BCS (replaces Former Budgeting — one-time, cannot undo)
3. FM Area (FM01) → Commitment Item hierarchy → Fund Center hierarchy
4. FMDERIVE structure (no values) → AVC tolerance keys (T043)

### 5.3 PS — Master Data vs Customizing Test

| If you see... | Status | Action |
|--------------|--------|--------|
| TABU PROJ | Always master data | **Remove from transport immediately** |
| TABU PRPS | Always master data | **Remove from transport immediately** |
| TABU RPSCO | Always reporting table | **Remove — meaningless to transport** |
| TABU OPS_BUKRS | Customizing — OK | Transport as normal |
| TABU T420 | Customizing — OK | Budget profile, transport as normal |
| NROB (project number ranges) | CRITICAL | **Never transport. Set manually.** |

**PS-FM Integration Sequence**: FM structure first → FMDERIVE strategy → PS Configuration (project profiles, network types) → Status profiles → PS Number Ranges (NEVER transport).

### 5.4 Bank — DMEE Is the Silent Payment Stopper

- DMEE tree = workbench object (looks like config, behaves like code)
- Modified DMEE transport overwrites target tree completely
- **OBPM4 (selection variants) is NEVER transported** — must be manually recreated in each system after any DMEE transport to production
- FBZP dependency chain: must transport in order Level 1→2→3→4 (see T042A → T042B → T042Z → T042C) or F110 runtime errors

---

## Part 6 — Fiori Domain Transport Chain

Fiori objects are the most fragmented in CTS because they span frontend, backend, and platform layers simultaneously.

### 6.1 Object Layer Map

| Layer | CTS Object | Transport Type | Notes |
|-------|-----------|---------------|-------|
| **UI5 Application Code (BSP)** | R3TR WAPA | Workbench (K) | Full BSP app. Uploaded via `/UI5/UI5_REPOSITORY_LOAD` or SE80. |
| **OData Service Group** | R3TR IWSG | Workbench (K) | Gateway registration. Missing in target = 'Service not found'. Auto-generated by SEGW. |
| **OData Model Group** | R3TR IWOM | Workbench (K) | Service metadata. Modified = API consumers may break. Auto-generated by SEGW. |
| **ICF Service Node** | R3TR SICF | Workbench (K) | HTTP entry point for Fiori. Missing = 404. **Activation state does NOT transport** — requires `RS_ICF_SERV_MASS_PROCESSING`. |
| **Launchpad Catalog (CONF scope)** | /UI2/ TABU entries | Workbench (K) | System-wide. Managed via `/UI2/FLPCM_CONF`. |
| **Launchpad Group (CUST scope)** | /UI2/ TABU entries | Customizing (W) | Client-specific. Managed via `/UI2/FLPCM_CUST`. |
| **DPC/MPC Extension Classes** | R3TR CLAS | Workbench (K) | ZCL_\*_DPC_EXT, ZCL_\*_MPC_EXT. Never modify base (SAP-generated). |
| **Auth Check Assignments** | R3TR SUCU | Workbench (K) | Auth check per t-code. Modified = security impact. |

### 6.2 Fiori Transport Pattern Recognition

| If E071 contains... | Interpretation | Action Required |
|--------------------|---------------|-----------------|
| R3TR SICF + R3TR IWSG together | OData service registration + HTTP path | Verify service activated in target via `/IWFND/MAINT_SERVICE` after import |
| R3TR WAPA (BSP) only, no SICF/IWSG | Frontend code without gateway registration | Gateway won't serve the app. Check if SICF/IWSG are in a separate TR. |
| R3TR CLAS ZCL_\*\_DPC_EXT | OData backend logic change | Check which GET_ENTITY/CREATE methods were modified. API impact. |
| TABU /UI2/CHIP or /UI2/PAGE_CT | Launchpad tile catalog entry | Verify tile still points to correct intent after import. |
| R3TR WAPA + CLAS ZCL_\*\_MPC_EXT | Both UI and schema changed | High risk: app and API structure changed together. Test end-to-end. |
| LIMU WAPP or LIMU WAPD | Individual BSP page (subobject) | Risk of partial transport. Always prefer the full R3TR WAPA. |

### 6.3 SICF Activation — The Hidden Step After Every Fiori Transport

SICF node activation state is **not transported** via standard CTS. After any Fiori-related transport to a new system:

```abap
" Mass activate SICF nodes — run in target system
" Step 1: In source, export active services to CSV
REPORT RS_ICF_SERV_ADMIN_TASKS.  " Filter to /sap/bc/ui5_ui5 and /sap/opu/odata paths

" Step 2: In target, import and activate from CSV
REPORT RS_ICF_SERV_MASS_PROCESSING.
```

Or manually: SICF transaction → navigate to node → Activate.

### 6.4 Fiori Transport Order of Operations

```
1. ABAP Backend Classes (DPC_EXT, MPC_EXT, ZCL_*)  ← transport first
2. OData Service (IWSG, IWOM via SEGW)              ← transport second
3. ICF Service Node (SICF)                          ← transport structure; activate manually
4. BSP Application (WAPA)                           ← transport last
5. Launchpad Catalog/Group (/UI2/...)               ← customizing TR, separate
6. SICF Mass Activation (RS_ICF_SERV_MASS_PROCESSING) ← post-import manual step
```

---

## Part 7 — Security / Authorization Transport Chain

### 7.1 The Role Object Stack (Logical Object — E071K is Empty)

Security roles are **logical objects** in SAP. This means:
- E071K shows NO entries for role transports
- Key resolution is DYNAMIC — happens at R3trans export time
- A role transport reads across multiple tables automatically

Tables included in a role logical object transport:

| Table | Content |
|-------|---------|
| AGR_DEFINE | Role header definition |
| AGR_1251 | Authorization object assignments and field values |
| AGR_1252 | Org-level values for derived roles |
| AGR_TEXTS | Role description text |
| AGR_TCODES | Transaction codes assigned to role |
| AGR_USERS | User assignments (OPTIONAL — handle carefully) |

### 7.2 Security Transport Types

| Scenario | What to Transport | PFCG Option |
|----------|------------------|-------------|
| New role | Role + generated profile | Include profile in TR |
| Modified single role | Role + profile (regenerate first!) | Regenerate in PFCG before releasing |
| Modified parent role | Parent + ALL child (derived) roles | Transport all together |
| Child role org-level change only | Child role only | Parent unchanged — exclude it |
| Composite role — added/removed single role | Composite only | Do NOT check "Also Transport Single Roles" |
| Deleting a role | Transport deletion via CTS | Do not delete directly in production |

> [!IMPORTANT]
> **Always regenerate the authorization profile in PFCG before releasing a role transport.** A role transport without a regenerated profile leaves an inconsistent state in the target.

### 7.3 Post-Import Security Actions (MANDATORY)

After importing any role transport to a new system:
1. **Run PFCG_TIME_DEPENDENCY** (or SU10) — user master comparison to activate new profiles
2. **Run SU25** if SU24 values changed — update role auth proposals from new check indicators
3. Verify with SU53 that users can access intended transactions without auth failures

### 7.4 SU24 — The Hidden Transport Layer

SU24 (authorization check assignment per transaction) controls which auth objects are proposed when building roles in PFCG. If custom transactions (ZTCODE) are transported without updated SU24 entries:
- PFCG will NOT propose the correct auth objects
- Developers must manually add auth objects to the role
- Causes inconsistent role builds across systems

> **Transport SU24 changes alongside the TRAN object for any new custom Z-transaction.**

### 7.5 Security Pattern Recognition in E071

| E071 Pattern | Interpretation | Action |
|-------------|---------------|--------|
| AGR_\* objects (AGR_DEFINE, AGR_1251) | Role transport | Security review. Full role overwrite in target — all auth values replaced. |
| R3TR SUCU | Authorization check assignments | Audit: was a check REMOVED? Check removal can be exploited. |
| TABU UST04 | User profile assignments | Security CRITICAL. User gets or loses access immediately on import. |
| AGR_\* + TABU UST04 in same TR | Role AND user assignment together | Requires SE- / GRC / Audit sign-off. Two separate expert reviews needed. |
| R3TR PROF | Generated authorization profile | Transport alongside AGR_* — otherwise profile inconsistency in target |
| E071.OBJECT='SUCU' with OBJFUNC='D' | Auth check REMOVED | Security alarm: a program/t-code is no longer checked. |

---

## Part 8 — Cross-Module Pattern Recognition (Instant Risk Signal Table)

Use this table when a transport spans multiple modules (most critical transports do):

| E071 Pattern | Module | Immediate Signal |
|-------------|--------|-----------------|
| TABU T512W + TABU T511 together | HR | Payroll wage type defined AND valued. Require payroll simulation sign-off. |
| TABU T549Q + TABU T549A | HR | Payroll period calendar + area change. Never import during open payroll period. |
| R3TR DECI (Feature) | HR | Schema/PCR selection logic. Compare feature source vs. target before import. |
| R3TR PROG with name ZU\* or Z\*00 | HR | Likely a payroll schema. Treat as CRITICAL, not generic PROG. |
| FMDERIVE in TR | PSM-FM | Check if values included → verify master data alignment source vs. target. |
| TABU T043 | PSM-FM | AVC tolerance change. Requires CFO sign-off. |
| TABU FMCI + TABU FM01 together | PSM-FM | FM structural reconfiguration. High sequencing risk. |
| TABU PROJ or TABU PRPS | PS | ALARM: master data in transport. Investigate origin immediately. |
| R3TR DMEE + TABU T042Z together | Bank | Payment format + method-country change. Verify OBPM1/OBPM4 manually afterward. |
| TABU T012 + TABU T012K | Bank | House bank + account. Verify T012K-HKONT exists in target chart of accounts. |
| TABU T001B | FI | ALARM: posting period status. NEVER import to production. Escalate to FI Controller. |
| TABU T030 + TABU T042Z same TR | FI + Bank | Two CRITICAL objects: account determination AND payment format. Split into two TRs. |
| TABU SKB1 with OBJFUNC='M' | FI | Mass wipe + recreate of GL account data. Pre-import backup required. |
| FAGL_SCENARIO + FAGL_T001L | FI/New GL | Parallel ledger structure change. UAT sign-off + migration assessment. |
| R3TR IWSG + R3TR SICF + R3TR WAPA | Fiori | Full Fiori service registration + activation + UI code. Verify end-to-end after import. |
| AGR_\* + R3TR SUCU | Security | Role definition change + auth check change. Double security review. |
| R3TR XPRA (any transport) | Any | Post-import program EXECUTES. Code review mandatory before import. |
| OBJFUNC='D' or 'M' any object | Any | CRITICAL destructive action. Explicit human approval required. |
| R3TR NROB (any transport) | Any | CRITICAL. Number range overwrite. Manual correction required afterward. |

---

## Part 9 — Pre-Import Safety Checklist (Scenario A)

Use before any transport import to QA or Production:

| # | Check | How to Verify | Risk If Skipped |
|---|-------|--------------|-----------------|
| 1 | Request type (K vs W) | E070.TRFUNCTION | Wrong client scope |
| 2 | Contains XPRA? | E071 WHERE OBJECT='XPRA' | Post-import program runs unreviewed |
| 3 | Contains NROB? | E071 WHERE OBJECT='NROB' | Number range overwrite — duplicate doc numbers |
| 4 | OBJFUNC='D' or 'M'? | E071 WHERE OBJFUNC IN ('D','M') | Unintended deletion or mass table wipe |
| 5 | Contains T030 or T001B? | E071K WHERE OBJ_NAME IN ('T030','T001B') | Silent G/L change or posting period lockout |
| 6 | Security objects (AGR_*, SUCU)? | E071 WHERE OBJECT LIKE 'AGR%' OR OBJECT='SUCU' | Role overwrite — access changes unexpectedly |
| 7 | HR payroll objects? | E071K WHERE OBJ_NAME IN ('T512W','T549A','T549Q') | Wrong payroll calculation in production |
| 8 | Fiori objects (SICF, IWSG, WAPA)? | E071 WHERE OBJECT IN ('SICF','IWSG','WAPA') | SICF may need manual activation post-import |
| 9 | FUGR: compare source vs. target FMs | SE37 in target before import | FMs silently deleted from target |
| 10 | Export log RC < 8? | `/usr/sap/trans/log/<SID>K<num>.SID` or SE09 log | Incomplete objects in production |

---

## Part 10 — AI Classification Pipeline (Scenario B — Bulk Mining)

### Step 1: Extract Full Transport Record from E07x

```python
# Confirmed working RFC pattern for UNESCO D01
SELECT a~trkorr, a~trfunction, a~trstatus, c~as4text,
       a~tarsystem, a~as4user, a~as4date,
       b~pgmid, b~object, b~obj_name,
       b~objfunc, b~lockflag,
       d~devclass
FROM e070 AS a
INNER JOIN e071 AS b ON a~trkorr = b~trkorr
INNER JOIN e07t AS c ON c~trkorr = a~trkorr
LEFT JOIN tadir AS d ON d~obj_name = b~obj_name
                     AND d~object = <TADIR_OBJECT_TYPE>  # Map obj_type → TADIR type!
INTO TABLE @DATA(et_transport)
WHERE a~as4date IN @s_date
AND b~object IN @s_obj.
```

> [!IMPORTANT]
> **TADIR object type mapping is mandatory**: `TABU → TABL`, `VDAT → VIEW`, `CLAS → CLAS`, `PROG → PROG`, `FUGR → FUGR`. Without the correct OBJECT type filter in the TADIR join, you get wrong packages.

### Step 2: Object Classification

For each E071 row, classify into:

```python
CATEGORY = {
    'DEV':          ['PROG', 'CLAS', 'FUGR', 'TABL', 'VIEW', 'DTEL', 'DOMA', 'ENQU', 'INTF', 'TRAN'],
    'CUSTOMIZING':  ['TABU', 'SOBJ'],
    'PLATFORM':     ['SICF', 'IWSG', 'IWOM', 'WAPA', 'SUCU'],
    'SECURITY':     ['SUCU', 'PROF'],  # + any AGR_* obj_name pattern
    'SCHEMA':       ['NROB', 'DEVC'],
    'ARTIFACT':     ['TDDAT'],         # + auto-FUGR Z*_MAINT pattern
    'DANGEROUS':    [],                # OBJFUNC in ('D', 'M')
    'EXECUTABLE':   ['XPRA'],
}

IMPACT_TIER = {
    'CRITICAL': ['T030', 'T001B', 'NROB', 'T043', 'T880', 'T512W', 'T549Q'],  # + OBJFUNC M/D
    'HIGH':     ['T011', 'SKA1', 'SKB1', 'TABL', 'DOMA', 'XPRA', 'T510'],
    'MEDIUM':   ['PROG', 'CLAS', 'FUGR', 'SICF', 'IWSG', 'T003', 'T004F'],
    'LOW':      ['TRAN', 'DEVC', 'DTEL', 'TVARVC'],
}

MODULE_MAP = {
    # HR
    'T511': 'HR', 'T512W': 'HR', 'T512Z': 'HR', 'T510': 'HR', 'T549A': 'HR',
    'T549Q': 'HR', 'T554S': 'HR', 'T554C': 'HR', 'T503': 'HR', 'T001P': 'HR',
    # PSM-FM
    'FMCI': 'PSM-FM', 'FM01': 'PSM-FM', 'FMZUOB': 'PSM-FM', 'T043': 'PSM-FM',
    # PS
    'OPST': 'PS', 'OPS_BUKRS': 'PS', 'T420': 'PS', 'PROJ': 'PS-ALARM', 'PRPS': 'PS-ALARM',
    # Bank
    'T012': 'BANK', 'T012K': 'BANK', 'T042': 'BANK', 'T042Z': 'BANK', 'T042I': 'BANK',
    # FI/GL
    'T030': 'FI-CRITICAL', 'T001B': 'FI-CRITICAL', 'T030R': 'FI-CRITICAL',
    'T001': 'FI', 'SKA1': 'FI', 'SKB1': 'FI', 'T011': 'FI', 'T003': 'FI',
    'T077S': 'FI', 'T880': 'FI', 'T004F': 'FI', 'T004': 'FI',
}
```

### Step 3: Is New vs Modified Detection

```python
def is_new_in_target(obj_name, object_type, tadir_target_cache):
    """Object is NEW if it doesn't exist in target TADIR."""
    key = (object_type, obj_name)
    return key not in tadir_target_cache

def signal_from_description(as4text):
    """Heuristic from transport description."""
    as4text_lower = as4text.lower()
    if any(w in as4text_lower for w in ['create', 'initial', 'new', 'baseline']):
        return 'NEW'
    if any(w in as4text_lower for w in ['fix', 'correction', 'patch', 'change', 'sprint']):
        return 'MODIFIED'
    return 'UNKNOWN'
```

### Step 4: LLM Prompt Pattern for Single Transport Review (Scenario A)

```
You are an SAP BASIS and functional transport expert.
Analyze the following transport request and provide:
1. Is each object NEW or MODIFIED in the target system?
2. Is each object an auto-generated artifact or intentional development?
3. Business impact of importing this transport to production.
4. CRITICAL risks: account determination, number ranges, deletions, payroll, budget.
5. Required sign-offs before production import.

Transport data: [E070+E071+E071K JSON]
Target TADIR snapshot: [relevant OBJ_NAME entries from target]
Module context: [FI | HR | PSM | Fiori | Security | ...]
OBJFUNC summary: [list any non-blank OBJFUNC values]
```

### Key AI Rules (Encoded from Experience)

- Never trust the object list alone — always cross-reference with export log RC code
- TABU entries require E071K key data to be meaningful
- Logical objects (AGR_\*, NROB) have empty E071K — different resolution logic
- OBJFUNC must always be explicitly checked — blank is NOT the same as safe
- FUGR requires comparison of ALL function modules in the group, not just the changed FM
- **Always flag these for human sign-off regardless of AI confidence**: T030, T030R, T001B, NROB, XPRA, OBJFUNC D/M, AGR_\* with SUCU, T512W during open payroll, PROJ/PRPS

---

## Part 11 — RFC Extraction Code (Confirmed Working on UNESCO D01)

```python
# Extract E071 with TADIR join for package — UNESCO pattern
from pyrfc import Connection
import os
from dotenv import load_dotenv

load_dotenv()
conn = Connection(
    ashost=os.getenv('SAP_HOST'),
    sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'),
    user=os.getenv('SAP_USER'),
    passwd=os.getenv('SAP_PASSWORD')
)

# E071 objects
result = conn.call('RFC_READ_TABLE',
    QUERY_TABLE='E071',
    OPTIONS=[{'TEXT': "TRKORR LIKE 'D01K9%'"}],  # adjust pattern
    FIELDS=[
        {'FIELDNAME': 'TRKORR'}, {'FIELDNAME': 'PGMID'},
        {'FIELDNAME': 'OBJECT'}, {'FIELDNAME': 'OBJ_NAME'},
        {'FIELDNAME': 'OBJFUNC'}, {'FIELDNAME': 'LOCKFLAG'}
    ],
    ROWCOUNT=5000
)

# E071K for TABU keys
keys_result = conn.call('RFC_READ_TABLE',
    QUERY_TABLE='E071K',
    OPTIONS=[{'TEXT': "TRKORR LIKE 'D01K9%' AND OBJECT = 'TABU'"}],
    FIELDS=[
        {'FIELDNAME': 'TRKORR'}, {'FIELDNAME': 'OBJ_NAME'},
        {'FIELDNAME': 'TABKEY'}
    ],
    ROWCOUNT=5000
)

# TADIR package lookup — OBJECT type filter is MANDATORY
# Map obj_type → TADIR OBJECT: TABU→TABL, VDAT→VIEW, PROG→PROG, CLAS→CLAS
TADIR_TYPE_MAP = {
    'TABU': 'TABL', 'CLAS': 'CLAS', 'PROG': 'PROG', 'FUGR': 'FUGR',
    'TABL': 'TABL', 'VIEW': 'VIEW', 'DTEL': 'DTEL', 'DOMA': 'DOMA',
    'TRAN': 'TRAN', 'DEVC': 'DEVC', 'SICF': 'SICF', 'IWSG': 'IWSG',
    'IWOM': 'IWOM', 'WAPA': 'WAPA', 'ENQU': 'ENQU', 'INTF': 'INTF',
}
# Skip: SOTR, VARX, LIMU (GUID keys or subobject — RFC_READ_TABLE fails with SAPSQL_DATA_LOSS)
SKIP_TADIR_TYPES = {'SOTR', 'VARX', 'LIMU', 'LANG', 'NROB'}
```

---

## You Know It Worked When (Scenario A)

- Every E071 row has a CATEGORY, IMPACT_TIER, and MODULE assigned
- OBJFUNC='D' or 'M' rows are flagged CRITICAL with explicit message
- Any transport containing T030, T001B, or NROB has a mandatory sign-off requirement
- Security objects (AGR_\*) have a security review flag
- Fiori objects (SICF) include post-import manual activation note
- Export log RC has been checked (not just the object list)

## You Know It Worked When (Scenario B)

- CTS dashboard shows module breakdown (HR, FI, PSM, Fiori, Security) with accurate counts
- TABU entries are separated: is_content (TABU/TDAT operational data) vs structural (TABL, scheme config)
- TADIR packages resolved with correct OBJECT type filter (no wrong DEVCLASS)
- Objects in "General IMG" bucket < 30% of total (good classification coverage)
- Contributors graph matches E070.AS4USER actual data

---

## Known Failures & Self-Healing

| Error | Cause | Fix |
|-------|-------|-----|
| Wrong DEVCLASS returned from TADIR join | Missing OBJECT type filter — same OBJ_NAME appears as TABL, DOMA, DTEL | Map obj_type → TADIR OBJECT explicitly. Cache in SQLite. |
| `SAPSQL_DATA_LOSS` from RFC_READ_TABLE on SOTR | SOTR uses GUID keys (binary/hex) — RFC_READ_TABLE fails reading binary data | Skip SOTR, VARX object types for TADIR lookup |
| E071K empty for AGR_\* (role) objects | Logical objects have dynamic key resolution — not stored in E071K | Normal behavior for logical objects. Keys resolved at R3trans export time. |
| SICF transport imported but app returns 404 | SICF activation state not transported via CTS | Run `RS_ICF_SERV_MASS_PROCESSING` in target manually |
| F110 payment run creates no file after DMEE transport | OBPM4 selection variants are system-specific and not transported | Manually recreate OBPM4 variants in target after DMEE transport |
| Payroll results wrong after PCR transport | Older PCR version transported over newer one (wrong TR sequence) | Verify TR sequence. Always transport PCRs in chronological order. |
| 'Commitment item not assigned' after FMDERIVE transport | FMDERIVE values reference FM objects that don't exist in target | Transport FMDERIVE structure only; set derivation values manually in target |
| User keeps getting authorization error after role transport | Profile not regenerated before transport release | Regenerate profile in PFCG source system, then re-release TR |
| 'Module not found for SM30 maintenance' | SE54-generated FUGR not included in transport | Include the auto-generated FUGR alongside the custom table TABL |
| buildConfig() undefined → blank dashboard sections | JS function renamed but init block not updated | Always search + replace old function name in ALL call sites after rename |

---

## Skill Update Protocol — Living Knowledge System

> [!IMPORTANT]
> **This skill is NOT static. It MUST evolve with every transport analysis.**
> Knowledge, rules, and conclusions are seeds — each new analysis refines them.

### Expert Seed Documents (Foundation of This Skill)
| Document | Size | Contents |
|----------|------|----------|
| `doc_reference.txt` | 28 KB | Transport anatomy, OBJFUNC semantics, PGMID/OBJECT taxonomy, AI design patterns (603 paragraphs) |
| `doc_supplement.txt` | 31 KB | Module-specific risks: HR payroll PCR, PSM FMDERIVE, PS master data, Bank DMEE, FI T001B (423 paragraphs) |

**Location**: `Zagentexecution/mcp-backend-server-python/`
**These documents seeded this skill. But the skill must GROW beyond them.**

### After EVERY Transport Analysis Session, Update:
1. Any new table → module mapping discovered → add to Part 4.2 + MODULE_MAP
2. Any new cross-module pattern identified → add to Part 8
3. Any new artifact type found → add to Part 4.3
4. Any new failure mode + fix → add to Known Failures table
5. Any new RFC extraction trick confirmed on D01/P01 → add to Part 11
6. Any UNESCO-specific custom object type → extend the taxonomy
7. Any new risk pattern not covered by the seed documents → add to Pre-Import Checklist

### The Agent Learning Loop
```
SEED: doc_reference.txt + doc_supplement.txt (expert rules)
  ↓
ANALYZE: Each new transport or batch of transports
  ↓
DISCOVER: New patterns, new risks, new module mappings
  ↓
UPDATE: This SKILL.md + Graph Brain (new edges) + Vector Brain (new embeddings)
  ↓
VERIFY: Pattern Brain algorithms detect trends across 7,745+ transports
  ↓
REFINE: Agent gets smarter → better classification → fewer misses
  ↓
(loop back to ANALYZE with enhanced knowledge)
```

### What "Living" Means Concretely
- Session #003: CTS extraction pipeline built → 7,745 transports classified
- Session #004: Module domain classification improved → "General IMG" reduced from 45% to <30%
- Session #005b: Living Knowledge principle formalized → skill now self-updates
- **Future**: Each new transport analyzed feeds back new rules, mappings, and edge cases

