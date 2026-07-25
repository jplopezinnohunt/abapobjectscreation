# SQLite Contents — Complete Reference
> Deep-inspected 2026-03-15. Every table, every schema, real sample rows.
> **This is the ground truth of what is in SQLite.**

---

## DATABASE 1: p01_gold_master_data.db (503 MB — PRIMARY)

---

### FM/FI Integration (NEW 2026-03-15)

#### `fmifiit_full` — 2,070,523 rows ✅
**SAP source:** FMIFIIT (FM FI Integration Item — full transactional data)
**Extraction:** Period-based batching (PERIO 001-016), 7 fund areas × 3 years
**Verified:** 21/21 area/year counts match volume anchors; 0 null keys; 99.9% FONDS join; 100% FISTL join

| Column | Type | Notes |
|--------|------|-------|
| FIKRS | TEXT | (K) FM Area — UNES, IBE, ICTP, IIEP, UBO, MGIE, UIS |
| GJAHR | TEXT | (K) Fiscal year — 2024, 2025, 2026 |
| FMBELNR | TEXT | (K) FM document number |
| FMBUZEI | TEXT | (K) FM line item number |
| BTART | TEXT | (K) Budget transaction type |
| RLDNR | TEXT | (K) Ledger |
| STUNR | TEXT | (K) Item number |
| FONDS | TEXT | Fund code → JOIN `funds.FINCODE` (99.9% match) |
| FISTL | TEXT | Fund center → JOIN `fund_centers.FICTR` (100% match) |
| FIPEX | TEXT | Commitment item |
| FAREA | TEXT | Functional area |
| WRTTP | TEXT | Value type |
| TWAER | TEXT | Currency key (USD, EUR, GHS, IDR, etc.) |
| FKBTR | TEXT | Amount in FM area currency |
| TRBTR | TEXT | Transaction currency amount |
| PERIO | TEXT | Posting period (001-016, SAP special periods included) |
| STATS | TEXT | Status |
| VRGNG | TEXT | FM transaction type |
| BUKRS | TEXT | Company code |
| HKONT | TEXT | G/L account |
| PRCTR | TEXT | Profit center |
| GRANT_NBR | TEXT | Grant number |
| MEASURE | TEXT | Funded program |
| KNBELNR | TEXT | Linked FI doc number → future JOIN to `BKPF.BELNR` |
| KNGJAHR | TEXT | Linked FI doc year |
| KNBUZEI | TEXT | Linked FI doc line |
| SGTXT | TEXT | Item text |

**Indexes:** `(FIKRS, GJAHR)`, `(FONDS)`, `(FISTL)`, `(KNBELNR)`

**Volume breakdown:**
| Year | UNES | IBE | UBO | ICTP | IIEP | MGIE | UIS | Total |
|------|------|-----|-----|------|------|------|-----|-------|
| 2024 | 857,633 | 6,012 | 18,367 | 32,775 | 20,950 | 4,207 | 5,109 | 945,053 |
| 2025 | 895,226 | 4,503 | 18,570 | 29,613 | 21,341 | 3,632 | 5,416 | 978,301 |
| 2026 | 134,568 | 792 | 3,215 | 4,268 | 3,032 | 550 | 744 | 147,169 |

Sample: `UNES | 2024 | 0605331093 | MBF | MBF | 15.35- | GHS | 001 | 8100000078`

---

### PSM / Fund Management

#### `funds` — 64,799 rows ✅
**SAP source:** FMFCT (FM Fund Master)
| Column | Type | Notes |
|--------|------|-------|
| FIKRS | TEXT | Fund area (UNES, IBE, UBO, ICTP, IIEP, MGIE, UIS) |
| FINCODE | TEXT | Fund code (e.g. AAFRA2023, 125GEF0000) |
| TYPE | TEXT | Fund type (100, 200, etc.) |
| ERFDAT | TEXT | Creation date YYYYMMDD |
| ERFNAME | TEXT | Creator user ID |

Sample: `IBE | AAFRA2023 | 100 | 20231211 | C_LEROY`

---

#### `fund_centers` — 764 rows ✅
**SAP source:** FMFCTR (FM Fund Center)
| Column | FIKRS | FICTR | ERFDAT | ERFNAME |
|--------|-------|-------|--------|---------|
Sample: `IBE | ADM | 20060123 | B_GRUJIC`

---

#### `proj` — 13,878 rows ✅
**SAP source:** PROJ (PS Projects)
| Column | Type | Notes |
|--------|------|-------|
| PSPID | TEXT | Project code |
| POST1 | TEXT | Description |
| VBUKR | TEXT | Company code |
| VERNR | TEXT | Person responsible number |
| ERDAT | TEXT | Creation date |
| PSPNR | TEXT | Internal project number (key for PRPS.PSPHI join) |

Sample: `1 | Major Programme 1 (Education) | UNES | 00000153 | 20020118 | 00000035`

---

#### `prps` — 58,516 rows ✅
**SAP source:** PRPS (PS WBS Elements)
| Column | Type | Notes |
|--------|------|-------|
| POSID | TEXT | WBS code |
| POST1 | TEXT | Description |
| PBUKR | TEXT | Company code |
| VERNR | TEXT | Person responsible |
| ERDAT | TEXT | Creation date |
| PSPHI | TEXT | Parent project PSPNR (FK → proj.PSPNR) |
| PSPNR | TEXT | Own internal number |
| OBJNR | TEXT | Object number for CO linkage (e.g. PR00000106) |

**JOIN:** `prps.PSPHI = proj.PSPNR` (WBS → Project)
**JOIN:** `prps.OBJNR` → COEP/RPSCO for cost data (when extracted)

---

#### `movements_summary` — 18,975 rows ✅
**SAP source:** FMIFIIT (FM FI Integration Item — aggregated summary)
| Column | Type | Notes |
|--------|------|-------|
| FIKRS | TEXT | Fund area |
| GJAHR | TEXT | Fiscal year |
| FONDS | TEXT | Fund code |
| FISTL | TEXT | Fund center |
| BTART | TEXT | Business transaction type |
| HSL_SUM | REAL | Total amount |
| COUNT | INTEGER | Number of line items |

> NOTE: This is a pre-aggregated view. For line-level detail, use `fmifiit_full`.

---

#### `fmbdt_summary` — 19,008 rows ✅
**SAP source:** FMBDT (FM Budget)
| Cols | RFIKRS | RYEAR | RFUND | RFUNDSCTR | COUNT |
Sample: `UNES | 2024 | 000REV9000 | UNESCO | 30`

---

#### `fmavct_summary` — 19,111 rows ✅
**SAP source:** FMAVCT (FM Availability Control)
| Cols | RFIKRS | RYEAR | RFUND | RFUNDSCTR | COUNT |
Sample: `UNES | 2024 | 000REV9000 | OPS | 1`

---

#### `ytfm_fund_cpl` — 6,368 rows ✅
**SAP source:** YTFM_FUND_CPL (UNESCO Custom — Fund-Ceiling coupling)
| Column | FIKRS | FINCODE | ALINE | NONIBF |
Sample: `MGIE | 633CRP9100 | EDU | X` (X = Non-IBF fund)

---

#### `ytfm_wrttp_gr` — 66 rows ✅
**SAP source:** YTFM_WRTTP_GR (UNESCO Custom — Value Type Groups)
| Column | WRTTP_GRP | SEQNR | WRTTP |
Sample: `BLOCKED | 01 | 80`, `ALLOT | 00 | ""`

---

### CTS / TADIR

#### `cts_transports` — 7,745 rows ✅
**Source:** cts_batch_2017-2026.json (D01 transport system)
| Column | Type | Notes |
|--------|------|-------|
| trkorr | TEXT | Transport order key |
| year | INTEGER | Year |
| trstatus | TEXT | Status |
| trfunction | TEXT | W=Workbench, K=Customizing |
| as4user | TEXT | Transport owner (100% filled) |
| as4date | TEXT | Creation date (100% filled) |
| as4text | TEXT | Description |
| obj_count | INTEGER | Number of E071 objects |

#### `cts_objects` — 108,290 rows ✅
**Source:** E071 objects from CTS batch files
| Column | Type | Notes |
|--------|------|-------|
| trkorr | TEXT | FK → cts_transports |
| pgmid | TEXT | Program ID (R3TR, CORR) |
| object | TEXT | Object type code |
| obj_name | TEXT | Object name |
| change_cat | TEXT | Derived category |

#### `tadir_enrichment` — 4,168 rows ✅
**Source:** tadir_cache.sqlite (correct TADIR data)
| Column | obj_type | obj_name | devclass |
54% have devclass populated (2,231 entries)

#### `volume_anchors` — 66 rows ✅
**Source:** RFC row counts from SAP P01
| Column | table_name | year | fund_area | row_count |

---

### EMPTY TABLES (not yet extracted)

| Table | SAP Source | Expected Rows | Notes |
|-------|-----------|---------------|-------|
| `cooi` | COOI | ~385K | CO internal orders |
| `coep` | COEP | ~615K | CO actual postings |
| `rpsco` | RPSCO | ~637K | PS cost planning |
| `jest` | JEST | unknown | Object status |

### DEPRECATED TABLES (can be dropped)

| Table | Notes |
|-------|-------|
| `fmifiit_raw_data` | Replaced by `fmifiit_full` |
| `projects` | Old v1 schema, use `proj` |
| `wbs_elements` | Old v1 schema, use `prps` |

---

## DATABASE 2: p01_master_data_v2.db (5.7 MB — SUPERSEDED)

Data duplicated in p01_gold_master_data.db. **Do not use for analysis.**

---

## DATABASE 3: tadir_cache.sqlite (0.37 MB)

Used by CTS dashboard. 4,168 rows of TADIR object→package mappings.

---

## TABLE JOIN MAP

```sql
-- FM document spending by fund (NEW - full detail!)
SELECT f.FINCODE, fi.GJAHR, fi.PERIO, fi.FKBTR, fi.TWAER, fi.SGTXT
FROM funds f
JOIN fmifiit_full fi ON f.FIKRS = fi.FIKRS AND f.FINCODE = fi.FONDS
WHERE fi.FIKRS = 'UNES' AND fi.GJAHR = '2024'

-- Fund spending summary by period
SELECT FONDS, PERIO, COUNT(*) as docs, SUM(CAST(FKBTR AS REAL)) as total
FROM fmifiit_full
WHERE FIKRS='UNES' AND GJAHR='2025'
GROUP BY FONDS, PERIO

-- FM to FI document link (ready for BKPF join)
SELECT fi.FMBELNR, fi.KNBELNR, fi.KNGJAHR, fi.FKBTR
FROM fmifiit_full fi
WHERE fi.KNBELNR != '' AND fi.FIKRS='UNES'

-- Fund ceiling rules
SELECT f.FINCODE, c.ALINE, c.NONIBF
FROM funds f
JOIN ytfm_fund_cpl c ON f.FIKRS = c.FIKRS AND f.FINCODE = c.FINCODE

-- Projects → WBS Elements
SELECT p.PSPID, p.POST1, w.POSID, w.POST1
FROM proj p
JOIN prps w ON p.PSPNR = w.PSPHI

-- CTS Objects by transport
SELECT t.trkorr, t.year, o.object, o.obj_name, o.change_cat
FROM cts_transports t
JOIN cts_objects o ON t.trkorr = o.trkorr
WHERE t.year = 2024 AND o.change_cat LIKE 'Workbench%'
```
