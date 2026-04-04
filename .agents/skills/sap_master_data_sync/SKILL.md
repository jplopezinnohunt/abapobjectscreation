---
name: SAP Master Data Sync (P01 → D01)
description: >
  Compare and synchronize SAP master data tables between P01 (production) and D01 (development).
  Covers GL accounts (SKA1/SKAT/SKB1), cost elements (CSKA/CSKU/CSKB), and extensible to
  cost centers, profit centers, functional areas, WBS elements. Proven pattern: extract both
  systems, compare in SQLite by key, INSERT missing records via RFC_ABAP_INSTALL_AND_RUN.
  Session 2026-04-03: 880 records synced (69 SKA1, 69 SKAT, 450 SKB1, 26 CSKA, 92 CSKU, 174 CSKB).
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
