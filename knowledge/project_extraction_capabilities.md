---
name: SAP Data Extraction Pipeline Architecture
description: Complete extraction pipeline -- 4 scripts, 21 tables, checkpoint pattern, auto-reconnect, adaptive field-splitting, SQLite loader with indexes. Updated Session #010.
type: project
---

## Extraction Pipeline Architecture (Session #010 -- MAJOR UPDATE)

### Gold DB Status: 1.8 GB, 25 tables, 10M+ rows
**Canonical path**: `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`

### Completed Tables (Session #010)

| Pipeline | Table | Rows | Status |
|----------|-------|------|--------|
| **FI** | bkpf | 1,677,531 | Loaded + indexed |
| **FI (Celonis)** | bsik | 8,015 | Loaded + indexed |
| **FI (Celonis)** | bsak | 739,910 | Loaded + indexed |
| **FI (Celonis)** | bsid | 4,677 | Loaded + indexed |
| **FI (Celonis)** | bsad | 211,201 | Loaded + indexed |
| **FI (Celonis)** | bsis | 2,291,246 | Loaded + indexed |
| **FI (Celonis)** | bsas | 1,480,715 | Loaded + indexed |
| **MM** | ekko | 68,861 | Loaded + indexed |
| **MM** | ekpo | 190,927 | Loaded + indexed |
| **MM** | ekbe | 482,532 | Loaded + indexed |
| **MM** | essr | 710,574 | Loaded + indexed |
| **PSM** | fmifiit_full | 2,070,523 | Pre-existing |
| **PSM** | funds | 64,799 | Pre-existing |
| **PSM** | + 12 others | ~232K | Pre-existing |
| **TOTAL** | | **~10M+** | |

### Pending Tables

| Pipeline | Table | Script | Notes |
|----------|-------|--------|-------|
| MM | ESLL | `extract_ekko_ekpo_parallel.py` | Entry sheet lines, single-file extract |
| Audit | CDHDR | `extract_cdhdr.py` | Change doc headers |
| Audit | CDPOS | `extract_cdhdr.py` | Change doc items |
| P2P | EBAN | `extract_p2p_complement.py` | Purchase requisitions |
| P2P | RBKP | `extract_p2p_complement.py` | Invoice doc headers |
| P2P | RSEG | `extract_p2p_complement.py` | Invoice doc lines |
| B2R | FMIOI | `extract_p2p_complement.py` | FM commitments |
| B2R | FMBH | `extract_p2p_complement.py` | FM budget headers |
| B2R | FMBL | `extract_p2p_complement.py` | FM budget lines |

### Four Extraction Scripts + One Loader

| Script | Tables | Pipeline |
|--------|--------|----------|
| `extract_bkpf_bseg_parallel.py` | BKPF + 6 Celonis tables | FI |
| `extract_ekko_ekpo_parallel.py` | EKKO, EKPO, EKBE, ESSR, ESLL | MM |
| `extract_cdhdr.py` | CDHDR, CDPOS | Change Audit |
| `extract_p2p_complement.py` | EBAN, RBKP, RSEG, FMIOI, FMBH, FMBL | P2P + B2R |
| `extraction_status.py` | ALL tables | Status + SQLite Loader |

### Shared Module: `rfc_helpers.py`
All 4 scripts import from this shared module:
- `get_connection("P01")` -- returns ConnectionGuard with auto-reconnect
- `rfc_read_paginated(conn, table, fields, where)` -- auto field-splitting + pagination

### Key Design Decisions

1. **Checkpoint-per-month pattern** -- JSON files like `BKPF_2024_01.json`. Safe to resume.
2. **Single-file exceptions** -- ESLL, ESSR (all years), CDPOS (key-based from CDHDR)
3. **Max 2 RFC connections per process** -- `threading.Semaphore(2)`
4. **Batch size 5,000 rows** -- proven with 2M FMIFIIT
5. **Throttle 3s between calls** -- proven safe on P01
6. **Celonis BSEG replacement** -- 6 transparent tables instead of cluster table
7. **Auto-reconnect on VPN drops** -- ConnectionGuard with 3 retries, escalating wait
8. **Adaptive field-splitting** -- auto-detects max chunk size (8->4->2) per table
9. **Error-safe checkpoints** -- errored periods do NOT checkpoint (allows retry on resume)
10. **BUDAT for filtering** -- works on all transparent tables (NOT CPUDT, which returned 0 rows)

### Session #010 Learnings (Critical)

#### 1. BSEG is a cluster table -- NEVER extract directly
Use BSIK+BSAK+BSID+BSAD+BSIS+BSAS transparent tables (Celonis pattern).
BSEG has no BUDAT/MONAT at DB level, and TABLE_WITHOUT_DATA masks buffer errors.

#### 2. BUDAT not CPUDT for date filtering
CPUDT (CPU date) returned 0 rows on all BS* tables. BUDAT (posting date) works.

#### 3. Auto-reconnect saves extractions
VPN drops mid-extraction are normal (UNESCO network). ConnectionGuard in rfc_helpers.py
detects connection-closed/timeout errors and reconnects up to 3 times with escalating
wait (10s, 20s, 30s). Saved 100+ hours of manual restarts.

#### 4. Adaptive field-splitting for wide tables
ESSR has fields so wide that even 8 fields overflow the 512-byte buffer.
rfc_helpers.py now auto-detects the right chunk size by halving: 8->4->2->1.
This fixed ESSR (710K rows) after multiple 0-row failures.

#### 5. Windows cp1252 crashes threads silently
Unicode characters (arrows, box-drawing, emojis) in print() crash Python threads on
Windows. ALL extraction scripts use ASCII-only output. Rule: NEVER use unicode in
print statements in extraction code.

#### 6. Error-safe checkpoints prevent data loss
If rfc_read_paginated errors with 0 rows, do NOT write checkpoint. Otherwise, on
resume the script skips that period thinking it's "done with 0 rows" when it actually
failed. Fixed in all 4 extraction scripts.

#### 7. Future months are instant (0 rows)
Months beyond current date return TABLE_WITHOUT_DATA immediately. For completed
tables, create empty checkpoints for remaining future months to show 36/36.

#### 8. ESSR needs full-table extract (no date filter)
ESSR entries created years ago are still active. Date-based extraction (2024-2026)
returns 0 rows. Extract with no WHERE clause to get all 710K rows.

### Execution Commands
```bash
# Status check
python extraction_status.py

# Extract FI (BKPF + Celonis BSEG replacements)
python extract_bkpf_bseg_parallel.py --table BSIS    # Single table
python extract_bkpf_bseg_parallel.py                  # All FI tables

# Extract MM
python extract_ekko_ekpo_parallel.py --table EKPO     # Single table

# Extract Change Docs
python extract_cdhdr.py

# Extract P2P + B2R
python extract_p2p_complement.py

# Load into SQLite
python extraction_status.py --load BKPF               # Single table
python extraction_status.py --clear BKPF               # Drop + reload
```

### Table Size Actuals (Session #010)

| Table | Estimated | Actual | Surprise |
|-------|-----------|--------|----------|
| BKPF | ~500K | 1,677,531 | 3x larger |
| BSEG cluster | ~2M | N/A | Replaced by 6 tables |
| BSIS | Unknown | 2,291,246 | Largest Celonis table |
| BSAS | Unknown | 1,480,715 | Second largest |
| BSAK | Unknown | 739,910 | |
| ESSR | <100K | 710,574 | 7x larger (all years) |
| EKBE | ~200K | 482,532 | 2.4x larger |
| BSAD | Unknown | 211,201 | |
| EKPO | Unknown | 190,927 | |
| EKKO | ~68K | 68,861 | As expected |
| BSIK | Unknown | 8,015 | Small |
| BSID | Unknown | 4,677 | Small |

### Critical Rules
- NEVER query FMIFIIT without WRTTP filter (join ytfm_wrttp_gr)
- ALWAYS PRAGMA table_info() before querying -- SAP column names are non-standard
- FM columns: FKBTR (not HSL), PERIO (not POPER), FMBELNR (not BELNR)
- FM-FI bridge: `FMIFIIT.KNBELNR = BKPF.BELNR`
- P2P chain: `EBAN.BANFN -> EKKO.EBELN -> EKPO -> EKBE -> RBKP.BELNR -> RSEG`
- BSEG replacement: `BSIK+BSAK (vendor) + BSID+BSAD (customer) + BSIS+BSAS (GL)`
