---
name: SAP Data Extraction (Layer 2)
description: >
  Orchestrates RFC-based extraction of SAP transactional data into SQLite.
  Covers FI (BKPF + Celonis BSEG replacement), MM (EKKO/EKPO/EKBE/ESSR),
  PSM (FMIFIIT, funds), and CTS transports. Uses pyrfc with SNC/SSO (P01).
  Gold DB: ~2.5 GB, 42 tables + 1 view, 24M+ rows.
---

# SAP Data Extraction Skill -- Layer 2

## Purpose

Extract SAP transactional and master data via RFC into a local SQLite database
for offline analysis, cross-domain joins, and brain graph enrichment.

---

## NEVER Do This

> [!CAUTION]
> - **NEVER query FMIFIIT without WRTTP filter** -- raw data includes internal value types that inflate numbers
> - **NEVER assume SAP column names** -- always `PRAGMA table_info()` or DD03L first
> - **NEVER run extractions against P01 without SNC/SSO** -- no password auth on production
> - **NEVER extract more than 2 concurrent RFC connections per process** -- SAP connection pool limit
> - **NEVER store SQLite copies outside the canonical path** -- one DB, one truth
> - **BSEG IS READABLE in P01** (declustered). Do NOT include MANDT in WHERE clause. Use it for PROJK (WBS internal key). The Celonis UNION pattern (BSIK+BSAK+BSID+BSAD+BSIS+BSAS) is still the primary approach for bulk data, but BSEG can be queried directly for specific fields like PROJK.
> - **NEVER re-extract a full table to add missing fields** -- use enrichment pattern: ALTER TABLE + fetch missing fields by existing keys (BUKRS+BELNR+GJAHR+BUZEI) per period
> - **NEVER rely on SGTXT text parsing for structured fields** -- WBS, cost center, fund center MUST come from proper fields via JOINs
> - **NEVER use CPUDT for date filtering on BS* tables** -- use BUDAT (posting date)
> - **NEVER use unicode in print() statements** -- cp1252 crashes threads silently on Windows
> - **NEVER checkpoint errored periods** -- skip checkpoint on error so resume retries them
> - **NEVER hardcode MAX_FIELDS_PER_CALL=8** -- use adaptive split (8->4->2) for wide tables like ESSR
> - **NEVER extract data before 2024** -- scope is 2024-2026 only unless explicitly asked
> - **NEVER launch extraction without probing size first** -- ROWCOUNT=50000 with 2 key fields to estimate
> - **NEVER accumulate >100K rows in RAM** -- stream to SQLite per month, `del rows` after each batch
> - **NEVER use rfc_read_paginated for months that fail with DATA_LOSS** -- fall back to day-by-day extraction (no ROWSKIPS). See below.

---

## Canonical Paths

```
Zagentexecution/
├── sap_data_extraction/
│   └── sqlite/
│       └── p01_gold_master_data.db    <- THE ONLY COPY (~2.5 GB, 42 tables + 1 view)
├── mcp-backend-server-python/
│   ├── rfc_helpers.py                  <- Shared: ConnectionGuard + rfc_read_paginated
│   ├── extract_bkpf_bseg_parallel.py  <- FI: BKPF + 6 Celonis tables (DONE)
│   ├── extract_ekko_ekpo_parallel.py  <- MM: EKKO+EKPO+EKBE+ESSR+ESLL (DONE except ESLL)
│   ├── extract_cdhdr.py               <- Audit: CDHDR+CDPOS (DONE - 7.8M rows)
│   ├── extract_p2p_complement.py      <- P2P: EBAN+RBKP+RSEG (DONE) + B2R: FMIOI+FMBH+FMBL (DONE)
│   ├── enrich_bsis_bsas_fields.py     <- Enrichment: +13 fields to BSIS/BSAS by doc key
│   ├── enrich_fmifiit_objnrz.py       <- Enrichment: +OBJNRZ to FMIFIIT for WBS linkage
│   ├── run_overnight_extraction.py    <- Orchestrator (FI + MM combined)
│   ├── extraction_status.py           <- Status dashboard + SQLite loader
│   └── extracted_data/                <- JSON checkpoint landing zone
```

---

## Shared Module: rfc_helpers.py

All extraction scripts import from this module:

```python
from rfc_helpers import get_connection, rfc_read_paginated

conn = get_connection("P01")  # Returns ConnectionGuard with auto-reconnect
rows = rfc_read_paginated(conn, "BKPF", fields, where, batch_size=5000, throttle=3.0)
```

### Key Features
- **ConnectionGuard**: Wraps pyrfc.Connection. Detects VPN drops/timeouts and reconnects
  up to 3 times with escalating wait (10s, 20s, 30s).
- **Adaptive field-splitting**: RFC_READ_TABLE has 512-byte line buffer. Auto-detects max
  fields per call by halving from 8 down to 2. Fixed ESSR (710K rows).
- **TABLE_WITHOUT_DATA handling**: Empty periods return this RFC error -- treated as 0 rows.
- **Proven defaults**: batch_size=5000, throttle=3.0 (from 2M FMIFIIT extraction).

---

## CRITICAL: SAPSQL_DATA_LOSS Pagination Bug (Session #013)

RFC_READ_TABLE throws `SAPSQL_DATA_LOSS` on certain months. This is NOT a field width issue — it's a **pagination bug** in ROWSKIPS.

**Symptoms**: Same fields work with ROWCOUNT=5 but fail during paginated extraction. Always the same months fail (Feb, Apr, Jun, Sep, Nov).

**Root cause**: SAP ABAP kernel cursor positioning loses data when ROWSKIPS is used on large tables.

**Workaround — Extract by DAY (no pagination needed)**:
```python
# When rfc_read_paginated fails with DATA_LOSS on a month:
for day in range(1, 32):
    dt = f'{year}{month:02d}{day:02d}'
    result = conn.call('RFC_READ_TABLE', QUERY_TABLE=table,
        DELIMITER='|', ROWCOUNT=50000,
        FIELDS=[{'FIELDNAME': f} for f in fields],
        OPTIONS=[{'TEXT': f"BUDAT = '{dt}'"}])
    # Parse and insert directly to SQLite — don't accumulate in RAM
```

**Affected tables confirmed**: FMIOI, TBTCO, EDIDC. Any table with >50K rows/month is at risk.

**Extraction size probe protocol** (ALWAYS do this first):
```python
# Step 1: Probe — NEVER extract blind
result = conn.call('RFC_READ_TABLE', QUERY_TABLE=table, DELIMITER='|',
    ROWCOUNT=50000, FIELDS=[{'FIELDNAME': key_field}], OPTIONS=[])
n = len(result.get('DATA', []))
# If n == 50000, table has >50K rows — use month partitioning
# If month fails with DATA_LOSS — use day-by-day workaround
# If table >100K rows — stream to SQLite, never accumulate in RAM
```

---

## Gold DB Schema (Session #034 -- 42 tables + 1 view + 12 comparison tables)

### FI Tables (Session #010)

| SQLite Table | SAP Source | Rows | Key Join Fields |
|---|---|---:|---|
| `bkpf` | BKPF | 1,677,531 | BELNR+GJAHR (PK), BUDAT, TCODE, AWKEY |
| `bsik` | BSIK | 8,015 | BELNR+GJAHR, LIFNR, BUDAT |
| `bsak` | BSAK | 739,910 | BELNR+GJAHR, LIFNR, BUDAT, AUGDT |
| `bsid` | BSID | 4,677 | BELNR+GJAHR, KUNNR, BUDAT |
| `bsad` | BSAD | 211,201 | BELNR+GJAHR, KUNNR, BUDAT, AUGDT |
| `bsis` | BSIS | 2,291,246 | BELNR+GJAHR, HKONT, BUDAT |
| `bsas` | BSAS | 1,480,715 | BELNR+GJAHR, HKONT, BUDAT, AUGDT |

### MM Tables (Session #010)

| SQLite Table | SAP Source | Rows | Key Join Fields |
|---|---|---:|---|
| `ekko` | EKKO | 68,861 | EBELN (PK), BEDAT, LIFNR |
| `ekpo` | EKPO | 190,927 | EBELN+EBELP |
| `ekbe` | EKBE | 482,532 | EBELN+EBELP, BUDAT, BELNR |
| `essr` | ESSR | 710,574 | LBLNI, EBELN, PACKNO |

### PSM Tables (Pre-existing)

| SQLite Table | SAP Source | Rows | Key Join Fields |
|---|---|---:|---|
| `fmifiit_full` | FMIFIIT | 2,070,523 | FONDS->funds.FINCODE, KNBELNR->BKPF.BELNR |
| `funds` | FMFCT | 64,799 | FINCODE (PK), FIKRS |
| `fund_centers` | FMFCTR | 764 | FICTR (PK), FIKRS |
| `proj` | PROJ | 13,878 | PSPNR (PK) |
| `prps` | PRPS | 58,516 | PSPNR, PSPHI->proj.PSPNR |
| `cts_transports` | E070 | 7,745 | TRKORR (PK) |
| `cts_objects` | E071 | 108,290 | TRKORR->cts_transports.TRKORR |
| `ytfm_wrttp_gr` | Custom | 66 | WRTTP filter groups |
| + 6 summary tables | | ~63K | Aggregated views |

### P2P Complement (Session #011 + #013)

| SQLite Table | SAP Source | Rows | Key Join Fields |
|---|---|---:|---|
| `eban` | EBAN | 23,160 | BANFN (PR number) |
| `rbkp` | RBKP | 126,428 | BELNR+GJAHR (invoice header) |
| `rseg` | RSEG | 162,539 | BELNR+GJAHR+BUZEI (invoice item) |
| `esll` | ESLL | 2,888,567 | PACKNO+INTROW (entry sheet lines) |

### B2R / FM Tables (Session #013)

| SQLite Table | SAP Source | Rows | Key Join Fields |
|---|---|---:|---|
| `fmioi` | FMIOI | 1,813,943 | REFBN+REFBT+RFPOS (FM open items) |
| `fmbh` | FMBH | 286,984 | DOCNR (FM budget header) |
| `fmbl` | FMBL | 319,335 | DOCNR+DOCLN (FM budget lines) |
| `cdhdr` | CDHDR | 7,810,913 | OBJECTCLAS+OBJECTID+CHANGENR |

### Ops / Interface Tables (Session #013)

| SQLite Table | SAP Source | Rows | Key Join Fields |
|---|---|---:|---|
| `tbtco` | TBTCO | 58,778 | JOBNAME+JOBCOUNT (job headers) |
| `tbtcp` | TBTCP | 84,975 | JOBNAME+JOBCOUNT+STEPCOUNT (job steps) |
| `rfcdes` | RFCDES | 239 | RFCDEST (RFC destinations) |
| `icfservice` | ICFSERVLOC | 6,477 | ICF_NAME (HTTP services) |
| `edidc` | EDIDC | 19,400 | DOCNUM (IDoc headers) |

### Views

| View | Sources | Rows | Purpose |
|---|---|---:|---|
| `bseg_union` | bsad+bsak+bsas+bsid+bsik+bsis | 4,735,764 | 32 columns + source_table |

### P01 vs D01 Comparison Tables (Session #034)

| SQLite Table | SAP Source | System | Rows | Purpose |
|---|---|---|---:|---|
| `P01_SKA1` | SKA1 | P01 | 2,491 | GL master (Chart of Accounts) |
| `D01_SKA1` | SKA1 | D01 | 2,500 | GL master (Chart of Accounts) |
| `P01_SKAT` | SKAT | P01 | 2,491 | GL texts (English) |
| `D01_SKAT` | SKAT | D01 | 2,500 | GL texts (English) |
| `P01_SKB1` | SKB1 | P01 | 9,249 | GL per company code (38 fields) |
| `D01_SKB1` | SKB1 | D01 | 9,802 | GL per company code (38 fields) |
| `P01_CSKA` | CSKA | P01 | 535 | Cost element master |
| `D01_CSKA` | CSKA | D01 | 541 | Cost element master |
| `P01_CSKU` | CSKU | P01 | 1,599 | Cost element texts (all languages) |
| `D01_CSKU` | CSKU | D01 | 1,607 | Cost element texts (all languages) |
| `P01_CSKB` | CSKB | P01 | 3,800 | Cost element per CO area |
| `D01_CSKB` | CSKB | D01 | 3,808 | Cost element per CO area |

> **Naming convention:** `{SYSTEM}_{TABLE}` (e.g., P01_SKA1, D01_SKB1).
> Gap = 0 after sync (2026-04-03). See `sap_master_data_sync` skill.

### Enriched Tables (Session #016)

| Table | Enrichment | New Fields |
|---|---|---|
| `bsis` | +13 fields (KOSTL, AUFNR, PRCTR, FKBER, SGTXT, EBELN, EBELP, MWSKZ, AUGDT, AUGBL, ZFBDT, ZTERM, PS_PSP_PNR) | 16→29 columns |
| `bsas` | +13 fields (same as BSIS) | 16→29 columns |
| `fmifiit_full` | +1 field (OBJNRZ for WBS linkage) | 27→28 columns, 2025 only |

---

## Golden Query (Session #016)

The canonical JOIN for FI document analysis:

```sql
SELECT
  b.BUKRS, b.BELNR, b.GJAHR, b.BLART, b.BKTXT, b.XBLNR, b.BUDAT, b.MONAT, b.USNAM, b.TCODE,
  u.BUZEI, u.BSCHL, u.HKONT, u.SHKZG, u.DMBTR, u.WRBTR, u.WAERS, u.GSBER, u.KOSTL, u.AUFNR,
  u.source_table,
  f.FISTL, f.FONDS, f.FIPEX, f.FKBTR, f.WRTTP, f.VRGNG, f.GRANT_NBR, f.OBJNRZ, f.SGTXT,
  p.POSID AS WBS_ELEMENT, p.POST1 AS WBS_DESCRIPTION
FROM bseg_union u
  JOIN bkpf b     ON u.BUKRS = b.BUKRS AND u.BELNR = b.BELNR AND u.GJAHR = b.GJAHR
  LEFT JOIN fmifiit_full f ON u.BUKRS = f.BUKRS AND u.BELNR = f.KNBELNR
                           AND u.GJAHR = f.KNGJAHR AND u.BUZEI = f.KNBUZEI
  LEFT JOIN prps p ON f.OBJNRZ = p.OBJNR
```

**JOIN keys:**
- bseg_union → bkpf: BUKRS + BELNR + GJAHR
- bseg_union → fmifiit_full: BUKRS + BELNR=KNBELNR + GJAHR=KNGJAHR + **BUZEI=KNBUZEI** (line-level)
- fmifiit_full → prps: OBJNRZ = OBJNR (WBS element)

**LEFT JOIN mandatory** — BSAS clearing lines have no FM data.

### Enrichment Pattern

When fields are missing from an already-extracted table:
```python
# 1. ALTER TABLE to add new column(s)
# 2. For each period, fetch ONLY the missing fields using existing keys
# 3. UPDATE existing rows
# 4. One period at a time — never all at once
# Scripts: enrich_bsis_bsas_fields.py, enrich_fmifiit_objnrz.py
```

---

## Celonis BSEG Replacement Pattern

BSEG has been **declustered** in P01 (readable via RFC_READ_TABLE). However, the Celonis 6-table UNION remains the primary bulk extraction approach. Use BSEG directly only for specific fields (e.g., PROJK for WBS) that aren't in the secondary index tables.

| Table | Content | KOART | Filter |
|-------|---------|-------|--------|
| BSIK | Vendor open items | K | BUDAT |
| BSAK | Vendor cleared items | K | BUDAT |
| BSID | Customer open items | D | BUDAT |
| BSAD | Customer cleared items | D | BUDAT |
| BSIS | GL open items | S | BUDAT |
| BSAS | GL cleared items | S | BUDAT |

Create a UNION VIEW in SQLite for BSEG queries:
```sql
CREATE VIEW bseg AS
SELECT *, 'K' as KOART FROM bsik
UNION ALL SELECT *, 'K' as KOART FROM bsak
UNION ALL SELECT *, 'D' as KOART FROM bsid
UNION ALL SELECT *, 'D' as KOART FROM bsad
UNION ALL SELECT *, 'S' as KOART FROM bsis
UNION ALL SELECT *, 'S' as KOART FROM bsas;
```

---

## Join Relationships

```sql
-- FM to FI bridge (ENABLED -- BKPF now loaded)
SELECT f.*, b.BLDAT, b.BUDAT, b.USNAM, b.TCODE
FROM fmifiit_full f
JOIN bkpf b ON f.KNBELNR = b.BELNR AND f.KNGJAHR = b.GJAHR AND f.BUKRS = b.BUKRS;

-- P2P chain: PR -> PO -> GR -> Invoice
-- EBAN.BANFN -> EKKO.EBELN -> EKPO -> EKBE -> RBKP.BELNR -> RSEG

-- PO to GR/SES history
SELECT k.EBELN, k.LIFNR, k.BEDAT, p.EBELP, p.TXZ01,
       e.VGABE, e.BUDAT as GR_DATE, e.MENGE, e.BELNR as GR_DOC
FROM ekko k
JOIN ekpo p ON k.EBELN = p.EBELN
JOIN ekbe e ON p.EBELN = e.EBELN AND p.EBELP = e.EBELP;

-- Entry sheets to POs
SELECT s.LBLNI, s.EBELN, s.EBELP, s.STATUS, s.ERDAT
FROM essr s
JOIN ekpo p ON s.EBELN = p.EBELN AND s.EBELP = p.EBELP;

-- WRTTP filter (ALWAYS apply for FMIFIIT)
SELECT f.* FROM fmifiit_full f
JOIN ytfm_wrttp_gr w ON f.WRTTP = w.WRTTP;
```

---

## Extraction Protocol

### Step 1: Verify Connectivity
```bash
cd Zagentexecution/mcp-backend-server-python
python -c "from rfc_helpers import get_connection; c=get_connection('P01'); print('OK'); c.close()"
```

### Step 2: Run Extraction
```bash
# Single table
python extract_bkpf_bseg_parallel.py --table BSIS
python extract_ekko_ekpo_parallel.py --table EKPO

# Full pipelines
python run_overnight_extraction.py           # FI + MM
python extract_cdhdr.py                       # Change docs
python extract_p2p_complement.py             # P2P + B2R
```

### Step 3: Load into SQLite
```bash
python extraction_status.py --load BKPF       # Single table
python extraction_status.py --load all         # All tables
python extraction_status.py --clear BKPF       # Drop + reload
```

### Step 4: Verify
```bash
python extraction_status.py                    # Full status report
```

---

## Completed Extractions

All tables listed in schema above are DONE.

## Known Gotchas (Session #013 Learnings)

| Issue | Solution |
|-------|----------|
| ICFSERVICE returns 0 rows | Use table name `ICFSERVLOC` instead |
| TBTCP returns 0 with many fields | Use max 6 fields: JOBNAME,JOBCOUNT,STEPCOUNT,PROGNAME,VARIANT,AUTHCKNAM |
| TBTCO only ~14 days in P01 | P01 has job log cleanup active — cannot get 2-year history |
| FMIOI DATA_LOSS on even months | Use day-by-day extraction (see workaround above) |
| ESLL 2.9M rows / 619MB JSON | Use ijson streaming for load, never json.load() |
| FMBH loaded with wrong fields | Always check JSON keys match DB columns before INSERT |
| B2R extraction (FMIOI/FMBH/FMBL) initially returned 0 rows | Date field/filter was wrong — always verify date field name via DD03L before extracting |
| FMIFIIT OBJNRZ enrichment partial | Only 2025 done (976K rows, ~73% populated). 2024+2026 pending. Run `enrich_fmifiit_objnrz.py` |

---

## Critical Column Name Gotchas

| Concept | Correct Column | Table | NOT This |
|---------|---------------|-------|----------|
| Fund code | FINCODE | funds | RFONDS |
| FM amount | FKBTR | fmifiit_full | HSL |
| Period | PERIO | fmifiit_full | POPER |
| FM doc number | FMBELNR | fmifiit_full | BELNR |
| FI doc link | KNBELNR | fmifiit_full | BELNR |
| Fund center | FICTR | fund_centers | FCTR |
| Fund area | FIKRS | multiple | FKRS |
| Date filter | BUDAT | BS* tables | CPUDT |

---

## Two-System Rule

| System | Auth | Use |
|--------|------|-----|
| D01 (Dev) | Password | Code deploy, ADT API, testing |
| P01 (Prod) | SNC/SSO only | Data extraction, monitoring |
