---
name: SAP Master Data Sync (P01 → D01)
description: >
  Compare and synchronize SAP master data tables between P01 (production) and D01 (development).
  Covers GL accounts (SKA1/SKAT/SKB1), cost elements (CSKA/CSKU/CSKB), and extensible to
  cost centers, profit centers, functional areas, WBS elements. Proven pattern: extract both
  systems, compare in SQLite by key, INSERT missing records via RFC_ABAP_INSTALL_AND_RUN.
  Session 2026-04-03: 880 records synced (69 SKA1, 69 SKAT, 450 SKB1, 26 CSKA, 92 CSKU, 174 CSKB).
  FM model extension evaluated 2026-06-29 (s093): gap of ~63K rows confirmed (claim #283).
domains:
  functional: [FI, PSM, FM]
  module: [FI, FM, CTS]
  process: [P2D, B2R]
---

# SAP Master Data Sync (P01 → D01)

## Purpose

Keep D01 (development) master data aligned with P01 (production). Production accumulates
GL accounts, cost elements, and other config that never gets transported back to dev.
This skill extracts, compares, and copies the delta programmatically.

## Direction

**Always P01 → D01.** Source = P01 (production, read-only). Target = D01 (development, write).

## Supported Tables

### GL Accounts

| Table | Key Fields | Level | Content |
|-------|-----------|-------|---------|
| SKA1 | KTOPL + SAKNR | Chart of Accounts | GL master record |
| SKAT | SPRAS + KTOPL + SAKNR | Chart of Accounts | GL account texts |
| SKB1 | BUKRS + SAKNR | Company Code | GL per company code |

### Cost Elements

| Table | Key Fields | Level | Content |
|-------|-----------|-------|---------|
| CSKA | KTOPL + KSTAR | Chart of Accounts | Cost element master |
| CSKU | SPRAS + KTOPL + KSTAR | Chart of Accounts | Cost element texts |
| CSKB | KOKRS + KSTAR + DATBI | Controlling Area | Cost element per CO area |

### Extensible To (same pattern)

| Table | Key Fields | Domain |
|-------|-----------|--------|
| CSKS + CSKT | KOKRS + KOSTL | Cost Centers |
| CEPC + CEPCT | KOKRS + PRCTR | Profit Centers |
| TFKB + TFKBT | FKBER | Functional Areas |
| FMFCTR + FMFCTRT | FIKRS + FICTR | Fund Management Centers |
| PRPS | POSID | WBS Elements |

## 4-Step Method

### Step 1: Extract Both Systems

```python
import sys
sys.path.insert(0, 'Zagentexecution/mcp-backend-server-python')
from rfc_helpers import get_connection, rfc_read_paginated

# Extract from LIVE system (not Gold DB cache)
for sys_id in ['P01', 'D01']:
    guard = get_connection(sys_id)
    rows = rfc_read_paginated(guard, table, fields, where,
                               batch_size=5000, throttle=1.0)
    # Save to SQLite as {sys_id}_{table} (e.g., P01_SKA1, D01_SKA1)
    save_to_sqlite(rows, f'{sys_id}_{table}', DB_PATH)
    guard.close()
```

**Rules:**
- Always extract LIVE before comparing — never trust cached Gold DB for gap analysis
- Use `rfc_read_paginated` — handles field-splitting for wide tables automatically
- SKAT/CSKU: filter `SPRAS = 'E'` for English, or no filter for all languages
- Save to Gold DB as `{system}_{table}` naming convention

### Step 2: Compare in SQLite

```sql
-- Find records in P01 but not D01 (by key fields)
SELECT COUNT(*) FROM P01_SKA1 p
WHERE NOT EXISTS (
    SELECT 1 FROM D01_SKA1 d
    WHERE d.KTOPL = p.KTOPL AND d.SAKNR = p.SAKNR
);
```

**Rules:**
- Compare by PRIMARY KEY fields only (see table above)
- Report: total per table, breakdown by grouping field (BUKRS, KOKRS, KTOPL)
- Also check reverse (D01-only) — these are typically test entries
- Present comparison to user for confirmation before any writes

### Step 3: Copy via RFC_ABAP_INSTALL_AND_RUN

```python
def build_insert_abap(table_name, cols, rows):
    """Generate ABAP INSERT statements for a batch of rows."""
    abap = [
        'REPORT Z_MD_SYNC.',
        f'DATA: ls TYPE {table_name.lower()},',
        '      lv_ok TYPE i.',
        '',
    ]
    for row in rows:
        d = dict(zip(cols, row))
        abap.append('CLEAR ls.')
        abap.append('ls-mandt = sy-mandt.')
        for fld in cols:
            val = d.get(fld, '')
            if val:
                v = val.replace("'", "''")  # escape quotes
                line = f"ls-{fld.lower()} = '{v}'."
                if len(line) <= 72:
                    abap.append(line)
        abap += [
            'ls-erdat = sy-datum.',
            'ls-ernam = sy-uname.',
            f'INSERT {table_name.lower()} FROM ls.',
            'IF sy-subrc = 0. ADD 1 TO lv_ok. ENDIF.',
            '',
        ]
    abap += [
        'COMMIT WORK.',
        f"WRITE: / '{table_name} OK:', lv_ok.",
    ]
    return abap

# Execute on D01
guard = get_connection('D01')
src = [{'LINE': line[:72]} for line in abap_lines]
res = guard.call('RFC_ABAP_INSTALL_AND_RUN', PROGRAM=src)
for w in res.get('WRITES', []):
    print(w.get('ZEILE', ''))
```

**Rules:**
- **Batch size:** 10-15 rows per RFC call (ABAP 72-char line limit, ~1000 lines max)
- **Throttle:** 2 seconds between batches
- **ERDAT/ERNAM:** Set to `sy-datum`/`sy-uname` (creation metadata will differ from P01)
- **COMMIT WORK** at end of each batch — not per row
- **Single quotes** in data: escape with `''` (ABAP literal escaping)
- **Line length:** truncate to 72 chars max (RFC_ABAP_INSTALL_AND_RUN limit)
- **No transport request** — direct table INSERT (dev system only)
- **Test 1 account first** — always run a single record, verify field-by-field against P01, then proceed with bulk

### Step 4: Verify

```python
# Re-extract D01 LIVE after inserts
guard = get_connection('D01')
rows = rfc_read_paginated(guard, table, fields, '', batch_size=5000, throttle=1.0)
# Re-save to SQLite, rerun Step 2 comparison
# Expected: P01-only count = 0
```

**Rules:**
- Always re-extract D01 LIVE after inserts — never trust batch output alone
- Verify gap = 0 for all tables
- D01 total will be >= P01 total (D01 has dev-only/test entries + STEM company code)

## NEVER Do This

1. **NEVER write to P01** — P01 is read-only source, D01 is the target
2. **NEVER skip the test insert** — always verify 1 record field-by-field before bulk
3. **NEVER trust Gold DB cache for gap analysis** — always extract LIVE before comparing
4. **NEVER use BDC/batch input** — RFC_ABAP_INSTALL_AND_RUN with direct INSERT is faster and more reliable
5. **NEVER skip COMMIT WORK** — without it, inserts are lost on session close
6. **NEVER exceed 72 chars per ABAP line** — RFC_ABAP_INSTALL_AND_RUN truncates silently
7. **NEVER copy D01-only records to P01** — those are test/dev entries (e.g., STEM company code)
8. **NEVER assume CSKBD/CSKBZ are tables** — they are structures/views, not extractable via RFC_READ_TABLE

## Non-Working Approaches (Proven Failures)

| Approach | Why It Failed |
|----------|--------------|
| `BAPI_GL_ACCOUNT_CREATE` | Does not exist in UNESCO system |
| `GL_ACCT_MASTER_MAINTAIN_RFC` | Raises NOT_FOUND — needs FS00 dialog session memory |
| BDC via `RFC_CALL_TRANSACTION_USING` + FS00 | User rejected batch input approach |
| `CSKBD` / `CSKBZ` extraction | TABLE_NOT_AVAILABLE — structures, not tables |

## Script Location

```
Zagentexecution/sap_data_extraction/scripts/
  extract_gl_costel_comparison.py     # Extract SKA1/SKAT/SKB1/CSKA/CSKU/CSKB from both systems
  copy_gl_accounts_p01_to_d01.py      # Copy GL accounts (template for cost elements too)
```

## Field-by-Field Verification Pattern

After test insert of 1 record, compare ALL fields between P01 and D01:

```python
for sys_id in ['P01', 'D01']:
    guard = get_connection(sys_id)
    result = guard.call('RFC_READ_TABLE', QUERY_TABLE=table, DELIMITER='|',
        FIELDS=[{'FIELDNAME': f} for f in all_fields],
        OPTIONS=[{'TEXT': f"SAKNR = '{test_saknr}'"}],
        ROWCOUNT=1)
    # Parse and compare field by field
    # Expected: all functional fields match, only ERDAT/ERNAM differ
```

**Expected differences (OK):**
- ERDAT: P01 shows original creation date, D01 shows today
- ERNAM: P01 shows original creator, D01 shows JP_LOPEZ

**Unexpected differences (NOT OK):**
- Any functional field mismatch = bug in INSERT logic

## UNESCO Context

- **Chart of Accounts:** UNES (single, shared across all company codes)
- **Controlling Areas:** IBE, ICBA, ICTP, IIEP, MGIE, UBO, UIL, UIS, UNES, US01
- **Company Codes:** 9 in P01, 10 in D01 (STEM is D01-only, new company code)
- **Account Groups:** BANK, COLL, OTHR, P&L, UNDP (T077S)
- **Typical gap:** ~50-70 GL accounts, ~25 cost elements accumulate in P01 between syncs

## Session Log

| Date | Tables | Records | Result |
|------|--------|---------|--------|
| 2026-04-03 | SKA1, SKAT, SKB1, CSKA, CSKU, CSKB | 880 | Gap = 0, all verified |
| 2026-06-29 | FMFINCODE, FMFINT, FMFCTR, FMFCTRT, FMCI, YTFM_FUND_C5, YTFM_FUND_CPL | ~63K gap counted | Gap analysis only — write phase NOT executed yet (requires full-field re-extraction; claim #283) |

## FM Model Extension (PSM/FM domain) — Evaluated s093 2026-06-29

The proven GL/CE sync pattern extends to Fund Management master data, with **important differences
in write method** per SAP object type.

### Gap summary (claim #283, point-in-time 2026-06-29)

| SAP table | Gold DB table | P01 count | D01 count | GAP | Notes |
|-----------|--------------|-----------|-----------|-----|-------|
| FMFINCODE | funds | 67,408 | 47,885 | **19,523** | UNES=14,809 dominant |
| FMFINT | FMFINT | 67,410 | ~47,887 | **19,523** | mirrors FMFINCODE |
| FMFCTR | fund_centers | 787 | 655 | **135** | UNES=110; D01 has +3 dev-only |
| FMFCTRT | fund_centers_text | 787 | 655 | **135** | mirrors FMFCTR |
| FMCI | commitment_items | 205 | 232 | 0 P01-only | D01 has +27 dev-only |
| FMCIT | commitment_items_text | 205 | 232 | 0 P01-only | same |
| TFKB | functional_areas | 9 | 9 | 0 | identical |
| YTFM_FUND_C5 | ytfm_fund_c5 | 17,598 | 100 | **17,564** | UNES=14,214 dominant |
| YTFM_FUND_CPL | ytfm_fund_cpl | 6,368 | 24 | **6,345** | UNES=6,234 |
| YTFM_OUTPUT | ytfm_output | +6 gap | | 6 | low priority |
| YTFM_C5 | ytfm_c5 | — | — | 0 | no sync needed |
| YTFM_WRTTP_GR | ytfm_wrttp_gr | — | — | 0 | no sync needed |

### Write method by object type

| Object | Write method | Why |
|--------|-------------|-----|
| FMFINCODE (funds) | Direct INSERT via RFC_ABAP_INSTALL_AND_RUN | Flat table, no hierarchy; same pattern as SKA1 |
| FMFINT (fund text) | Direct INSERT | Same; key FIKRS+FINCODE+SPRAS |
| FMFCTR (fund centers) | BAPI_0050_CREATE or direct INSERT | Fund centers participate in hierarchies (FMFCTRHIER); prefer BAPI to preserve hierarchy links. Verify BAPI availability on ECC 6.0 EhP8 before coding. |
| FMFCTRT (fund center text) | Direct INSERT | Text table, no hierarchy |
| YTFM_FUND_C5 / YTFM_FUND_CPL | Direct INSERT | Z/Y own objects — INSERT is correct path |
| YTFM_OUTPUT / YTFM_OUTPUT_T | Direct INSERT | Own objects |

### CRITICAL: Gold DB funds table is KEY-ONLY (claim #284)

The gold `funds` table has only 5 columns: FIKRS, FINCODE, TYPE, ERFDAT, ERFNAME.
Real FMFINCODE has ~30 fields. **DO NOT use the Gold DB cache as the write source.**
The write phase MUST re-extract FMFINCODE live from P01 with full field list before INSERT to D01.

### Extraction constraint (claim #244 — applies to BOTH P01 and D01)

Both P01 and D01 RFC_READ_TABLE are wrapped by class SAIS which **REJECTS ROWSKIPS** (rc=5,
OPTION_NOT_VALID). Confirmed empirically on D01 FMFINCODE/FMFINT during s093.

```python
# CORRECT pattern for FM tables on P01 or D01
for fikrs in ['IBE', 'ICBA', 'ICTP', 'IIEP', 'MGIE', 'UBO', 'UIL', 'UIS', 'UNES']:
    rows = guard.call('RFC_READ_TABLE',
        QUERY_TABLE='FMFINCODE',
        OPTIONS=[{'TEXT': f"FIKRS = '{fikrs}'"}],
        ROWCOUNT=0,       # ROWCOUNT=0 = all rows
        ROWSKIPS=0,       # NEVER set > 0
        FIELDS=[...])     # full field list from live extraction
```
