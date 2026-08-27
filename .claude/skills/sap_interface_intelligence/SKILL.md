---
name: SAP Interface Intelligence
description: >
  Complete mapping of all inbound and outbound connections to/from UNESCO SAP systems.
  Covers RFC destinations (SM59/RFCDES), ICF services (SICF), OData/Gateway services,
  IDocs/ALE, database connections (DBCON), web services (SOAMANAGER), PI/PO proxies,
  and direct table access. Answers: what connects to SAP, how, and why.
domains:
  functional: [Integration]
  module: [BASIS]
  process: []
---

# SAP Interface Intelligence

## Purpose

Build a complete **connectivity map** of UNESCO's SAP landscape:
1. **Inbound**: What systems call SAP? (RFC, OData, IDoc, HTTP, DB)
2. **Outbound**: What does SAP call? (RFC destinations, web services, PI/PO)
3. **Internal**: Cross-client, cross-system RFC (D01↔P01, P01↔Y1)
4. **Protocol**: How does each connection work? (RFC, HTTP, SOAP, IDoc, tRFC)
5. **Security**: Auth method per connection (SNC, Basic, SSO, Certificate)

## NEVER Do This

1. NEVER expose RFC destination passwords — RFCDES stores them encrypted, don't try to decrypt
2. NEVER deactivate ICF services without understanding downstream impact — Fiori apps depend on them
3. NEVER assume RFCDES is complete — some connections use hardcoded destinations in code
4. NEVER ignore tRFC/qRFC queues (SM58/SMQ1/SMQ2) — stuck entries indicate broken interfaces
5. NEVER extract EDIDC without date filter — IDoc tables can be enormous (10M+ rows)
6. **NEVER read "0 observed calls" as "unused" without checking the destination's TRANSPORT** — see
   the next section. Our own boundary algorithm published 40 such verdicts it could not support.

## What the boundary measurement CAN and CANNOT see (s106, claim 620)

`process_mining/interface_boundary.py` (algorithm F1) is how we tell live from dead at the boundary.
Its entire evidence base is **`rsau_audit_history.PARAMX` — the Security Audit Log, which records
RFC calls.** That is narrower than "all traffic", and the gap is not academic:

| RFCTYPE | Transport | Can F1 see it? |
|---|---|---|
| `3` ABAP · `I` internal · `T` TCP/IP · `2` `S` `M` | RFC runtime | **YES** — a call writes PARAMX |
| `G` HTTP external · `H` HTTP | `cl_http_client` | **NO** — writes no RFC audit row |
| `L` logical · `X` driver | pointer / driver entry | **UNCERTAIN** — not confirmed to emit PARAMX |

So for a type `G`/`H` destination, `observed_calls: 0` means **we cannot see**, never *nobody uses
it*. F1 now emits those in a separate `unobservable` bucket (40 of them) instead of `dead` (187).
Rows carry an `observability` field; `L`/`X` rows in `dead` carry a `caveat`.

**The trap that produced this, worth remembering because it repeats:** F1's comment claims *"DEAD is
now a fact rather than an artefact"* after the 400,000-row sample was removed. Removing the sample
fixed the **coverage** of the source. It could not fix its **applicability**. Those are different
properties, and conflating them is how a blind spot gets published as a finding.

**To decide live/dead for an HTTP destination you need a different source** — ICM/HTTP log, the
consuming application's own evidence, or reading the ABAP that calls it. Not this one.

## RoleManagement (RM) — an external system we integrate with, owned by another project

The case that exposed the above. `svc-prod-role.hq.int.unesco.org` sat in `dead` with 0 calls while
being, per its owning project, a live production dependency.

- **RM is NOT UNESDIR.** In UNESCO's SoapUI tree `RoleManagement` and `Unesdir` are **sibling
  services**. Our integration map already knows UNESDIR (the directory): `ZLFNA1_DOWNLOAD_FOR_UNESDIR`
  (FILE out, vendor master, daily) and `YHR_CREATE_MAIL_FROM_UNESDIR` (DBCON in, 93% failure).
  RM is a different service and is **not** in the map as a flow.
- **What it is:** the registry of *who may act*. SOAP 1.1, `http://unesco.org/rolemanagement`,
  binding `BasicHttpBinding_Facade`, 4 operations (`GetRoleMembers`,
  `GetCertifyingOfficersByEmployeeEmail`, `GetPlaces`, `GetEmployeeMemberships`).
- **Who calls it — TWO consumers, not one.** This list said "CRP" until s106 and was incomplete;
  the second one was found by reading ABAP, not docs:
  1. the CRP app on D01 clnt 350, package ZCRP — via the `CallUnesdir` FunctionImport
  on OData service `ZPSM_PROC_FORMS_SRV` → SM59 `UNESDIR_PROD` → `cl_http_client`.
  2. **the FI payment-release workflow** — `WS90000003`/`WS90000002`, rule `90000001`, doc types
     `KR/KA/KT/ER/IT`. Chain: invoice posted with payment block `BSEG-ZLSPR` → event `BSEGCREATED`
     → `Z_GET_CERTIF_OFFICER_UNESDIR` → **typed SOAP proxy** `zrole_mgtco_facade` with
     `logical_port_name = 'LP_ROLE_MGT'` → RM → approval lifts the block → F110 picks it up.
     Source: `extracted_code/FI/Payment_Workflow/Z_GET_CERTIF_OFFICER_UNESDIR.abap`. Fallback when
     no actor resolves: table `ZFI_PAYREL_EMAIL` — **2 rows**.

- ⛔ **THE NAME LIES, AND THAT IS WHY NOBODY FOUND THIS CONSUMER.** Every FI artefact labels this
  dependency **UNESDIR** — the FM is `Z_GET_CERTIF_OFFICER_UNESDIR`, the trace field is
  `unesdir_subrc` — **and it is RM.** The discriminator is technical and admits no doubt: UNESDIR
  is reached by **DBCON/SQL** (`YHR_CREATE_MAIL_FROM_UNESDIR`); this is a **SOAP consumer proxy
  with a logical port**, and its operation (`get_certifying_officers_by_emp`), binding
  (`…_facade`) and namespace match RM exactly. Two artefacts state it wrongly and are corrected
  here rather than in place, because they are owned elsewhere:
  `companions/payment_bcm_companion.html` ("SharePoint WCF + SQL" — imprecise) and
  `.claude/skills/sap_payment_bcm_agent/SKILL.md:277` ("reads **UNESCO LDAP (UNESdir)**" —
  **incorrect**). This is *the alias that gives zero* INVERTED: the false name does not hide a
  file's existence, it hides **the identity of the dependency**. Searching for RM consumers by the
  name "RM" could never have found this one.

- 💡 **A SECOND EVIDENCE SOURCE FOR TRAFFIC, independent of the RFC audit log — LEAD, NOT DATA.**
  `Z_WF_GET_CERTIFYING_OFFICER.abap` writes a trace row per call attempt:
  `ycl_bc_trace_table( iv_tr_obj = 'WF_PAYMENT' )` carrying `unesdir_subrc`. If table
  `ysbc_trace_payment` has rows, RM→FI traffic can be **counted without `PARAMX`** — which would
  turn part of the `UNOBSERVABLE` bucket (see the section above / claim 620) into a measured
  number for this one consumer. **Nobody has read that table**; only the code that writes it.
  Verify before citing.

- ❓ **Still unverified:** that `LP_ROLE_MGT` resolves to `svc-prod-role.hq.int.unesco.org`. The
  logical port is configured in SOAMANAGER and that config is not in the repo. RM's identity here
  rests on operation + binding + namespace, **not** on the host.
- ⛔ **Bank signatories do NOT go through RM.** RM's role catalogue happens to contain a role *named*
  `BANK_SIGNATORY`; that is a name, not a mechanism. UNESCO bank signature authority is **SAP
  standard** — RY nodes, `HRP1001` RELAT 007, role `BNK_APP`, execution via `OOCU_RESP` — and is
  owned by the `bcm-signatory-panel` agent. A previous session opened a false gap by grepping the
  foreign name against a brain that stores the concept under SAP's names, and reading the 0 as a
  hole. That is *the alias that gives zero* (`braintoolbox.yaml`).

**A NEW CHANNEL CLASS none of our 10 covers:** `CallUnesdir` (and its twin `CallSalesforce`) is a
**generic HTTP passthrough exposed as an OData FunctionImport** — the *caller* supplies destination,
SOAPAction and the whole envelope; the only control is a substring allowlist (`UNESDIR_*`, else
forced to `UNESDIR_PROD`). Two consequences: you **cannot** characterise what leaves through it by
reading the channel's code, and it is confused-deputy surface sitting in a package of ours. Consistent
with H71 — the control has to live at the CALL and DATA layer, not the role layer.

> **Source, not copied here (ADR-007 — each project owns its data):** the full skill + visual
> companion live in the CRP project at
> `unescrp/.claude/skills/crp/unesdir-role-management/` (README + `api-reference.md` +
> `wsdl-reference.md` + `unesdir-role-management.html`), validated against the real hooks and DPC
> in their session S-208 (2026-08-27, CODE-READ — D01 was unreachable, so shape not runtime).
> **Read it there; do not fork it here.** Claims 619 / 620 / 621.

## Connection Types

### 1. RFC Destinations (SM59)

**Table**: `RFCDES` (RFC Destination Configuration)

| Field | Purpose |
|-------|---------|
| RFCDEST | Destination name (e.g., P01CLNT350, MSSY1) |
| RFCTYPE | Type: 3=ABAP, H=HTTP, G=External, T=TCP/IP, I=Internal |
| RFCOPTIONS | Connection parameters (host, port, client, etc.) |
| RFCHOST | Target host |
| RFCSERVICE | Target service/port |
| RFCSYSID | Target system ID |
| RFCCLIENT | Target client |
| RFCSAMEUSR | Same user flag (SSO) |
| RFCSNC | SNC enabled flag |

**Extraction**:
```python
conn = get_connection("P01")
fields = ["RFCDEST", "RFCTYPE", "RFCHOST", "RFCSERVICE",
          "RFCSYSID", "RFCCLIENT", "RFCSAMEUSR", "RFCSNC"]
rows = rfc_read_paginated(conn, "RFCDES", fields, "", batch_size=5000)
```

**RFC Types**:
| Type | Code | Example | Protocol |
|------|------|---------|----------|
| ABAP Connection | 3 | P01CLNT350, Y1CLNT100 | RFC (SAP-to-SAP) |
| HTTP Connection | H | ES_*, GATEWAY_* | HTTP/HTTPS |
| External Program | G | External RFC server | TCP/IP |
| TCP/IP Connection | T | Print, email servers | TCP |
| Internal | I | Same-system calls | Internal |

### 2. ICF Services (SICF)

**Table**: `ICFSERVICE` (Internet Communication Framework)

| Field | Purpose |
|-------|---------|
| ICF_NAME | Service name |
| ICFPARGUID | Parent GUID (tree structure) |
| ICF_DOCU | Documentation |
| ICFACTIVE | Active flag (X = active) |
| ICF_CCLIEN | Client-specific |

**Key Service Paths**:
| Path | Purpose | Critical |
|------|---------|----------|
| `/sap/bc/adt` | ABAP Development Tools (ADT) | YES — code deployment |
| `/sap/opu/odata` | OData Gateway | YES — all Fiori apps |
| `/sap/bc/bsp` | BSP applications | YES — UI5/Fiori frontend |
| `/sap/bc/webdynpro` | Web Dynpro | Legacy apps |
| `/sap/bc/srt` | Web Services Runtime | SOAP services |
| `/sap/bc/gui/sap/its/webgui` | WebGUI | Browser-based SAP GUI |
| `/sap/public/bc/icf/login` | Login service | Authentication |

**Extraction**:
```python
fields = ["ICF_NAME", "ICFPARGUID", "ICFACTIVE", "ICF_DOCU"]
rows = rfc_read_paginated(conn, "ICFSERVICE", fields, "", batch_size=5000)
```

### 3. OData / Gateway Services

**Discovery via ADT**:
```python
# List all registered OData services
GET /sap/bc/adt/businessservices/odataservices
Accept: application/atom+xml

# Specific service metadata
GET /sap/opu/odata/sap/{SERVICE_NAME}/$metadata
```

**Tables**:
| Table | Purpose |
|-------|---------|
| `/IWBEP/I_SRV_RT` | Gateway service runtime registration |
| `/IWBEP/I_V_SERVIC` | Service catalog view |
| `/IWFND/I_MED_SRV` | Frontend server service registration |
| `/IWFND/C_CONFIG` | Gateway configuration |

**Known UNESCO OData Services**:
| Service | Domain | DPC Class |
|---------|--------|-----------|
| Z_HCMFAB_ADDRESS_SRV | HCM | ZCL_Z_HCMFAB_ADDRESS_DPC_EXT |
| ZHCMFAB_MYFAMILYMEMBERS_SRV | HCM | CL_HCMFAB_MYFAMIL_M_DPC_EXT |
| Z_HCMFAB_MYPERSONALDATA_SRV | HCM | ZCL_Z_HCMFAB_MYPERS_DPC_EXT |
| ZHR_PROCESS_AND_FORMS_SRV | HCM | ZCL_ZHR_PROCESS_AND_DPC_EXT |
| ZHCMFAB_BEN_ENROLLMENT_SRV | HCM | CL_HCMFAB_BEN_ENROLLME_DPC_EXT |
| Z_CRP_SRV | PSM | ZCL_Z_CRP_SRV_DPC_EXT |

### 4. IDocs / ALE (Application Link Enabling)

**Tables**:
| Table | Purpose | Key Fields |
|-------|---------|------------|
| EDIDC | IDoc control record (header) | DOCNUM, IDOCTP, MESTYP, SNDPRT, RCVPRT, STATUS |
| EDID2/EDID4 | IDoc data segments | DOCNUM, SEGNUM, SDATA |
| EDIDS | IDoc status records | DOCNUM, STATUS, STAPA, STATYP |
| IDOCTP | IDoc type definitions | IDOCTYP, DESCRP |
| TBD52 | Partner profiles (WE20) | RCVPRT, RCVPRN, MESTYP |

**IDoc Status Codes** (key ones):
| Status | Direction | Meaning |
|--------|-----------|---------|
| 03 | Outbound | Data passed to port |
| 12 | Outbound | Dispatch OK |
| 51 | Inbound | Application document not posted |
| 53 | Inbound | Application document posted |
| 64 | Inbound | IDoc ready to be transferred |

**Extraction Strategy**:
```python
# ALWAYS filter by date — EDIDC can be huge
fields = ["DOCNUM", "IDOCTP", "MESTYP", "SNDPRT", "SNDPRN",
          "RCVPRT", "RCVPRN", "STATUS", "CREDAT", "CRETIM"]
where = "CREDAT >= '20240101'"
rows = rfc_read_paginated(conn, "EDIDC", fields, where, batch_size=5000)
```

### 5. Web Services (SOAMANAGER)

**Tables**:
| Table | Purpose |
|-------|---------|
| SRT_MSERV_RES | Web service runtime |
| SRT_RES_INBO | Inbound web service resources |
| SPRX_OBJECT | Service proxy objects |

**Discovery via ADT**:
```
GET /sap/bc/adt/ws/services     # Inbound SOAP services
GET /sap/bc/adt/ws/consumers    # Outbound SOAP consumers
```

### 6. Database Connections (DBCON)

**Table**: `DBCON` (External Database Connections)

| Field | Purpose |
|-------|---------|
| CON_NAME | Connection name |
| DBMS | Database type (ORA, HDB, MSS, etc.) |
| DBHOST | Database host |
| DBNAME | Database/schema name |

```python
fields = ["CON_NAME", "DBMS", "DBHOST", "DBNAME"]
rows = rfc_read_paginated(conn, "DBCON", fields, "", batch_size=100)
```

### 7. tRFC / qRFC Queues (SM58, SMQ1, SMQ2)

**Tables**:
| Table | Purpose |
|-------|---------|
| ARFCSSTATE | tRFC status (SM58) |
| TRFCQOUT | Outbound qRFC queue (SMQ1) |
| TRFCQIN | Inbound qRFC queue (SMQ2) |

> [!WARNING]
> Stuck entries in these tables indicate broken interfaces. Cross-reference with RFCDES
> to identify which destination is failing.

### 8. Known Cross-System Connections (UNESCO)

| Source | Destination | Protocol | Purpose |
|--------|-------------|----------|---------|
| P01 | Y1 (HCM) | RFC (MSSY1) | Payroll cross-posting |
| D01 | P01 | RFC (P01CLNT350) | Indirect data access |
| External | P01 | OData/HTTP | Fiori apps (Launchpad) |
| P01 | BW | RFC | BW extraction (RSA7) |
| P01 | PI/PO | IDoc/SOAP | External partner integration |
| Allos (Excel) | P01 | BDC/SM35 | Batch data upload |
| PBC Engine | P01 | RFC/BAPI | Budget reservations (FMRESERV) |

## Extraction Plan (Priority Order)

### Phase 1: RFC Destinations (Quick Win)
```bash
# Small table, immediate value
python -c "
from rfc_helpers import get_connection, rfc_read_paginated
conn = get_connection('P01')
rows = rfc_read_paginated(conn, 'RFCDES',
    ['RFCDEST','RFCTYPE','RFCHOST','RFCSERVICE','RFCSYSID','RFCCLIENT','RFCSNC'],
    '', batch_size=5000)
print(f'RFC destinations: {len(rows)}')
"
```

### Phase 2: ICF Services
```bash
# All active ICF services
python -c "
from rfc_helpers import get_connection, rfc_read_paginated
conn = get_connection('P01')
rows = rfc_read_paginated(conn, 'ICFSERVICE',
    ['ICF_NAME','ICFPARGUID','ICFACTIVE'],
    \"ICFACTIVE = 'X'\", batch_size=5000)
print(f'Active ICF services: {len(rows)}')
"
```

### Phase 3: OData Service Catalog
```bash
# Via ADT — list all registered OData services
python sap_adt_client.py --action list --type IWSV
```

### Phase 4: IDoc History (Date-Filtered)
```bash
# Large table — ALWAYS filter by CREDAT
python -c "
from rfc_helpers import get_connection, rfc_read_paginated
conn = get_connection('P01')
rows = rfc_read_paginated(conn, 'EDIDC',
    ['DOCNUM','IDOCTP','MESTYP','SNDPRN','RCVPRN','STATUS','CREDAT'],
    \"CREDAT >= '20240101'\", batch_size=5000)
print(f'IDocs (2024+): {len(rows)}')
"
```

### Phase 5: DBCON + Queue Status
```bash
# Small tables
# DBCON, ARFCSSTATE, TRFCQOUT, TRFCQIN
```

## Analysis Queries (Post-Extraction)

```sql
-- RFC destination inventory by type
SELECT RFCTYPE,
  CASE RFCTYPE
    WHEN '3' THEN 'ABAP (SAP-to-SAP)'
    WHEN 'H' THEN 'HTTP'
    WHEN 'G' THEN 'External Program'
    WHEN 'T' THEN 'TCP/IP'
    WHEN 'I' THEN 'Internal'
  END as type_desc,
  COUNT(*) as count
FROM rfcdes GROUP BY RFCTYPE;

-- Active OData services with DPC classes
SELECT service_name, dpc_class, version, is_active
FROM odata_services WHERE is_active = 'X';

-- IDoc volume by type and direction
SELECT IDOCTP, MESTYP,
  SUM(CASE WHEN STATUS < 40 THEN 1 ELSE 0 END) as outbound,
  SUM(CASE WHEN STATUS >= 40 THEN 1 ELSE 0 END) as inbound
FROM edidc WHERE CREDAT >= '20240101'
GROUP BY IDOCTP, MESTYP ORDER BY outbound + inbound DESC;

-- Cross-system connectivity map
SELECT RFCDEST, RFCTYPE, RFCSYSID, RFCCLIENT, RFCSNC
FROM rfcdes WHERE RFCTYPE = '3'
ORDER BY RFCSYSID;
```

## Known Failures & Self-Healing

| Error | Cause | Fix |
|-------|-------|-----|
| `RFCDES auth error` | S_RFC authorization missing | Check S_RFC for RFC_READ_TABLE on RFCDES |
| `EDIDC timeout` | Too many rows without date filter | ALWAYS use CREDAT filter |
| `ICFSERVICE returns 0` | Table name varies by version | Use `ICFSERVLOC` (confirmed P01) |
| `/IWBEP/ tables not found` | Gateway not installed or different namespace | Check via ADT endpoint instead |
| `DBCON empty` | No external DB connections configured | Normal — not all systems use DBCON |

## Integration Points

- **Brain**: INTERFACE nodes with CONNECTS_TO edges in sap_brain.py
- **Transport Intel**: RFC destination changes tracked in transports (OBJTYPE=DEST)
- **System Monitor**: Stuck tRFC/qRFC visible in health report
- **BDC Intel**: Cross-system BDC sessions use RFC destinations (MSSY1)
- **Process Mining**: Interface events feed cross-system process flows
- **Coordinator**: Routes "what connects to SAP" / "how does X integrate" queries here

## EXTRACTION DONE (Session #013)

| Table | Rows | Key Findings |
|-------|------|-------------|
| **rfcdes** | 239 | 75 ABAP(SAP-to-SAP), 50 TCP/IP, 38 External, 2 HTTP, 68 Internal |
| **icfservice** (ICFSERVLOC) | 6,477 | 5,822 active, 655 inactive |
| **edidc** | 19,400 | Top: RSINFO(9.4K BW), PROJECT02(4.4K PS), EXCHANGE_RATE(988) |

### Key Findings

**RFC Types breakdown**:
- 75 ABAP connections (type 3) — SAP-to-SAP including Y1, BW, PI
- 50 TCP/IP (type T) — external servers, printers
- 38 External programs (type G) — RFC servers
- Only 2 HTTP (type H) — minimal direct web service use

**IDoc patterns**:
- RSINFO (9.4K) — BW extraction requests, daily
- PROJECT02 (4.4K) — PS master data replication to BW
- EXCHANGE_RATE (988) — daily exchange rates, critical for UNESCO multi-currency
- BUS1504/1505 — WBS element create/change (spikes Jan 2025)

### EDIDC DATA_LOSS Note
Same pagination bug as FMIOI — even months fail. Use day-by-day workaround for complete extraction.

## Visualization Standard

**Use the `integration_diagram` skill** — see `.claude/skills/integration_diagram/SKILL.md`.

Pure CSS/SVG, no vis.js. Hub-and-spoke with functional zones, orthogonal 90° connections, dark theme + neon accents. Reference implementation: `Zagentexecution/mcp-backend-server-python/connectivity_diagram.html`.

## Pending Work

1. **Interface deep dive** — for each RFCDEST type 3 (75 SAP-to-SAP), identify target system, purpose
2. **OData service catalog** — extract /IWBEP/I_SRV_RT via RFC or ADT
3. **Connectivity diagram** — D01↔P01↔Y1↔BW↔PI visual map
4. **Brain integration** — INTERFACE nodes with CONNECTS_TO edges

## You Know It Worked When

1. ~~RFCDES extracted~~ DONE (239 destinations)
2. ~~ICF services mapped~~ DONE (6,477 services, 5,822 active)
3. ~~IDoc baseline established~~ DONE (19,400 IDocs, 9 types)
4. OData catalog extracted — all registered Gateway services listed
5. Cross-system map built — D01↔P01↔Y1↔BW↔PI connections visualized
6. Connectivity diagram can answer: "If system X goes down, what breaks?"
7. **(Session #037)** Agent recognizes file-based batch integration as a first-class channel — see "File-Based Integration Vector" section below.
8. **(Session #055)** Agent can answer per-integration "which SAP element (FM/IDoc/program+variant/endpoint) is used" — see "Session #055 Integration Element Audit" below.

---


## Referencia detallada

Lo que sigue vive en **[reference.md](reference.md)** y se carga sólo si hace
falta — una skill cargada se queda en contexto todo el turno, así que aquí
queda lo que se lee ANTES de actuar y allí el detalle:

- **Session #055 Integration Element Audit**
- **File-Based Integration Vector (routed Session #037 via skill_coordinator)**
