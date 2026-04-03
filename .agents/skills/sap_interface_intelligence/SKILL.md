---
name: SAP Interface Intelligence
description: >
  Complete mapping of all inbound and outbound connections to/from UNESCO SAP systems.
  Covers RFC destinations (SM59/RFCDES), ICF services (SICF), OData/Gateway services,
  IDocs/ALE, database connections (DBCON), web services (SOAMANAGER), PI/PO proxies,
  and direct table access. Answers: what connects to SAP, how, and why.
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

**Use the `integration_diagram` skill** — see `.agents/skills/integration_diagram/SKILL.md`.

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
