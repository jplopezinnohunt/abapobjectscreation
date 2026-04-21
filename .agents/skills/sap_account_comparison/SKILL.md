---
name: SAP Account Comparison & Adjustment Between Systems
description: >
  Compare G/L account master data (SKA1/SKB1/SKAT) between P01 and D01 field-by-field,
  identify mismatches (account group, house bank, flags, texts), and adjust D01 to match P01.
  Extends sap_master_data_sync with UPDATE capability (not just INSERT). Handles KTOKS, XINTB,
  HBKID, multi-language SKAT texts. Used for house bank configuration alignment.
domains:
  functional: [FI]
  module: [FI]
  process: [B2R]
---

# SAP Account Comparison & Adjustment Between Systems

## Purpose

When new G/L accounts are created during house bank configuration, they may be created
differently in P01 (by MD team) vs D01 (by config team). This skill detects and fixes
all field-level divergences.

## Relationship to Other Skills

- **sap_master_data_sync** — Handles bulk INSERT of missing records (P01 → D01)
- **This skill** — Handles field-level UPDATE of existing records + targeted INSERT of missing accounts
- **house_bank_configuration** — The business process that triggers this comparison

## Scope

| Table | Key | What We Compare |
|-------|-----|----------------|
| SKA1 | KTOPL + SAKNR | KTOKS (account group), BILKT, GVTYP, XBILK |
| SKB1 | BUKRS + SAKNR | WAERS, FDLEV, XKRES, XINTB, HBKID, HKTID, ALTKT, MWSKZ |
| SKAT | SPRAS + KTOPL + SAKNR | TXT20, TXT50, MCOD1 (all languages E/F/P) |

## Method

### Step 1: Deep Extract (ALL fields)

Unlike sap_master_data_sync which extracts selected fields, this skill extracts
ALL fields for targeted accounts to catch every divergence.

```python
from rfc_helpers import get_connection

ACCOUNTS = ['0001065421', '0001165421', '0001065424', '0001165424']

for sys_id in ['P01', 'D01']:
    guard = get_connection(sys_id)
    for acct in ACCOUNTS:
        # SKA1
        result = guard.call('RFC_READ_TABLE', QUERY_TABLE='SKA1',
            DELIMITER='|',
            OPTIONS=[{'TEXT': f"KTOPL = 'UNES' AND SAKNR = '{acct}'"}])
        # SKB1
        result = guard.call('RFC_READ_TABLE', QUERY_TABLE='SKB1',
            DELIMITER='|',
            OPTIONS=[{'TEXT': f"BUKRS = 'UNES' AND SAKNR = '{acct}'"}])
        # SKAT (all languages)
        result = guard.call('RFC_READ_TABLE', QUERY_TABLE='SKAT',
            DELIMITER='|',
            OPTIONS=[{'TEXT': f"KTOPL = 'UNES' AND SAKNR = '{acct}'"}])
```

### Step 2: Field-by-Field Comparison

For each account present in BOTH systems, compare every field:

```python
for field in all_fields:
    p01_val = p01_data.get(field, '')
    d01_val = d01_data.get(field, '')
    if p01_val != d01_val:
        print(f"  MISMATCH {field}: P01={p01_val!r} D01={d01_val!r}")
```

**Expected differences (ignore):**
- ERDAT, ERNAM, AEDAT, AENAM — creation/change metadata
- BSTAT — may differ during transport

**Unexpected differences (fix):**
- KTOKS, XINTB, HBKID, HKTID, WAERS, FDLEV — functional fields

### Step 3: Fix D01 via RFC_ABAP_INSTALL_AND_RUN

**For UPDATE (existing record, wrong field values):**

```python
def build_update_ska1(saknr, field, value):
    return [
        'REPORT Z_FIX_SKA1.',
        'DATA: ls TYPE ska1.',
        'SELECT SINGLE * FROM ska1 INTO ls',
        f"  WHERE ktopl = 'UNES' AND saknr = '{saknr}'.",
        'IF sy-subrc = 0.',
        f"  ls-{field.lower()} = '{value}'.",
        '  UPDATE ska1 FROM ls.',
        '  IF sy-subrc = 0.',
        "    WRITE: / 'OK'.",
        '  ELSE.',
        "    WRITE: / 'FAIL'.",
        '  ENDIF.',
        'ENDIF.',
        'COMMIT WORK.',
    ]
```

**For INSERT (missing account):**

Use the sap_master_data_sync pattern (build_insert_abap).

### Step 4: Verify

Re-extract D01 LIVE and re-compare. Expected: 0 mismatches on functional fields.

## Common Mismatches Found

| Field | Table | Typical Cause |
|-------|-------|--------------|
| KTOKS | SKA1 | D01 created with wrong account group (OTHR vs BANK) |
| XINTB | SKB1 | "Post automatically only" flag not set in D01 |
| HBKID | SKB1 | House bank ID differs (old vs new bank) |
| TXT20/TXT50 | SKAT | Short text abbreviated differently, or FR/PT texts not updated |

## HBKID Special Case

When replacing one house bank with another (e.g., ECO09 → UBA01):
- P01 may still show the OLD house bank until transport arrives
- D01 may already show the NEW house bank
- This is an EXPECTED divergence during transition — document it, don't "fix" it

## Scripts

```
Zagentexecution/mcp-backend-server-python/
  uba01_gl_comparison.py              # Deep comparison for UBA01 accounts
  h29_skat_diff.py                    # SKAT text divergence extractor
  h29_skat_update.py                  # SKAT text sync executor
```

## NEVER Do This

1. NEVER write to P01 — always P01(read) → D01(write)
2. NEVER update ERDAT/ERNAM — those are audit fields
3. NEVER "fix" HBKID during bank transition without confirming intent
4. NEVER skip multi-language check — FR and PT texts often diverge silently

## Session Log

| Date | Accounts | Findings | Result |
|------|----------|----------|--------|
| 2026-04-07 | 1065421/1165421/1065424/1165424 | 2 missing in D01, KTOKS/XINTB/HBKID/texts mismatched | Pending fix |
