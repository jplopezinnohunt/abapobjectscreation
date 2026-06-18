---
name: SAP Program Variant Analysis
description: >
  Forensic analysis of any ABAP program's variants in SAP production.
  Extracts variant inventory from VARI/VARIS (pool tables), decodes selection
  criteria scope, cross-references account selections with SKB1 blocks and
  T030H configuration, identifies coverage gaps and error-generating variants.
  Proven on SAPF100 (F.05 FX Revaluation) at UNESCO — Session #078.
domains:
  functional: [Finance, Controlling, Any]
  module: [FI, CO, BC]
  process: [Closing, Configuration Audit]
tier: project
maturity: production
origin_session: 78
last_updated_session: 78
triggers:
  - variant analysis
  - VARI VARID VARIS
  - program variants
  - F.05 variants
  - SAPF100 variant
  - which variant runs for which company code
  - variant coverage gap
  - variant forensic
  - variant selection criteria
subtopics:
  - pool_table_extraction
  - variant_naming_patterns
  - account_block_cross_reference
  - reversal_variant_analysis
  - coverage_gap_detection
---

# SAP Program Variant Analysis

## When to Use This Skill

- User asks "which variants exist for program X?"
- Analyzing a month-end close process and need to know which company codes have variants configured
- Forensic: a program errors during execution — need to know which variant triggered it and why
- Auditing whether all company codes have required variant coverage
- Checking if a variant's account selection range includes blocked/closed accounts

## Core Concept — What Is a SAP Variant?

A SAP variant saves selection-screen parameter values for a report/program so it can be re-run with the same inputs without re-entering them. Key tables:

| Table | Type | Content | RFC Readable? |
|-------|------|---------|---------------|
| `VARI` | Pool (VARPOOL) | Variant header: name, text, owner, dates | Key field only (VARIANT) |
| `VARID` | Pool (VARPOOL) | Selection parameter values (P_ parameters) | Key field only (VARIANT) |
| `VARIS` | Pool (VARPOOL) | Selection options (S_ parameters, ranges) | Key field only (VARIANT) |

**Critical limitation**: VARI/VARID/VARIS are pool tables. RFC_READ_TABLE can only reliably return the primary key field (VARIANT). Multi-field reads fail with `TABLE_WITHOUT_DATA` (AD-718). This is not an authorization issue — it is the pool table architecture.

## Extraction Methodology

### Step 1 — Get All Variant Names (always works)

```python
conn = get_connection('P01')
result = conn.call('RFC_READ_TABLE',
    QUERY_TABLE='VARI',
    DELIMITER='|',
    FIELDS=[{'FIELDNAME': 'VARIANT'}],
    OPTIONS=[{'TEXT': f"REPORT = '{program}'"}],
    ROWCOUNT=500
)
variants = sorted(set(row['WA'].strip() for row in result['DATA'] if row['WA'].strip()))
```

### Step 2 — Count Selection Criteria per Variant (VARIS, single field)

```python
result = conn.call('RFC_READ_TABLE',
    QUERY_TABLE='VARIS',
    DELIMITER='|',
    FIELDS=[{'FIELDNAME': 'VARIANT'}],
    OPTIONS=[{'TEXT': f"REPORT = '{program}'"}],
    ROWCOUNT=1000
)
from collections import Counter
criteria_counts = Counter(row['WA'].strip() for row in result['DATA'])
```

A variant with 0 VARIS rows has no S_ selection ranges. A variant with many rows has complex account/company code selections.

### Step 3 — Decode Variant Content (when RFC_ABAP_INSTALL_AND_RUN is authorized)

If `S_DEVELOP` authorization exists on the target system (typically D01, not P01):

```python
code = """
REPORT ZVAR_READ.
DATA: lt_vari  TYPE TABLE OF vari,
      lt_varid TYPE TABLE OF varid,
      lt_varis TYPE TABLE OF varis,
      ls_vari  TYPE vari,
      ls_varid TYPE varid,
      ls_varis TYPE varis.
SELECT * FROM vari  INTO TABLE lt_vari  WHERE report = 'PROGRAM_NAME'.
SELECT * FROM varid INTO TABLE lt_varid WHERE report = 'PROGRAM_NAME'.
SELECT * FROM varis INTO TABLE lt_varis WHERE report = 'PROGRAM_NAME'.
LOOP AT lt_vari  INTO ls_vari.  WRITE: / 'V~', ls_vari-variant, '~', ls_vari-vtext, '~', ls_vari-ename, '~', ls_vari-adate. ENDLOOP.
LOOP AT lt_varid INTO ls_varid. WRITE: / 'D~', ls_varid-variant, '~', ls_varid-selname, '~', ls_varid-kind, '~', ls_varid-low, '~', ls_varid-high. ENDLOOP.
LOOP AT lt_varis INTO ls_varis. WRITE: / 'S~', ls_varis-variant, '~', ls_varis-selname, '~', ls_varis-sign, '~', ls_varis-option, '~', ls_varis-low, '~', ls_varis-high. ENDLOOP.
"""
result = conn.call('RFC_ABAP_INSTALL_AND_RUN',
    PROGRAM=[{'LINE': line[:72]} for line in code.split('\n')]
)
writes = result.get('WRITES', [])
```

**Note**: `RFC_ABAP_INSTALL_AND_RUN` requires `S_DEVELOP` authorization. On P01 production this is blocked. Use D01 or a test system.

### Step 4 — Cross-Reference with Business Objects (Gold DB)

Once variant names are known, cross-reference with Gold DB to identify risk:

**For FX programs (SAPF100, FAGL_FCV):**
```sql
-- Which variants would hit blocked LKORR accounts?
SELECT t.HKONT, t.CURTP, t.LKORR, s.XSPEB, s.BUKRS
FROM T030H t
JOIN SKB1 s ON s.SAKNR = t.LKORR AND s.XSPEB = 'X'
WHERE t.KTOPL = 'UNES'
  AND (t.XSPEB = '' OR t.XSPEB IS NULL)  -- source HKONT is active
```

**For any program with account selections:**
```sql
-- Are any accounts in the likely selection range blocked?
SELECT SAKNR, BUKRS, XSPEB, XLOEB
FROM SKB1
WHERE SAKNR BETWEEN :low AND :high
  AND (XSPEB = 'X' OR XLOEB = 'X')
```

## Naming Convention Patterns

UNESCO SAPF100 variants follow this pattern (discovered Session #078):

| Pattern | Meaning | Account Scope |
|---------|---------|---------------|
| `{BUKRS}_OI` | Open Items | AR/AP subledger open items |
| `{BUKRS}_UNBA` | Unbalanced GL accounts | Balance-sheet accounts without open-item mgmt |
| `{BUKRS}_OI_AR/AP` | AR/AP open items only | Creditor/debtor subledger |
| `{BUKRS}_OI_G/L` | G/L open items only | G/L open-item managed accounts |
| `{BUKRS}_DEPOSIT` | Bank/deposit accounts | Cash + bank balance-sheet accounts |
| `{BUKRS} GRP CUR` | Group currency | Cross-currency group revaluation |
| `SAP&AUDIT_*` | SAP-delivered audit variants | Internal SAP use, not operational |
| `SAP&FW_*` | SAP financial working capital | Internal SAP use |

Other programs may use different conventions. Always decode from the variant text (VTEXT field in VARI — readable via RFC_ABAP_INSTALL_AND_RUN on D01).

## What to Look For — Analysis Checklist

### 1. Coverage gaps
- Does every company code have the expected variant types?
- For FX programs: does each BUKRS have both `_OI` and `_UNBA`?
- Any BUKRS completely missing? (No variant = no revaluation)

### 2. Error-generating variants
- Which variants target accounts that are blocked in SKB1 (XSPEB='X')?
- Named patterns: `_DEPOSIT` variants cover bank accounts → high risk if closed banks remain in T030H

### 3. Reversal variants
- Does a separate reversal variant exist, or is reversal done via runtime flag?
- If no reversal variant: confirm in BKPF that BUDAT=day-1 documents exist (reversal postings)
- Missing reversal docs = the accountant forgot to reverse = BS account overstated

### 4. Stale variants
- VARI.ADATE = last modified date. A variant not modified since account creation may miss new GL accounts (e.g., new currency accounts added in 2024 not included in 2018-era variant range)

### 5. SAP-delivered vs custom
- `SAP&*` prefix = SAP-delivered. Not to be modified. Not used in UNESCO monthly close.
- All UNESCO operational variants have no prefix

### 6. VARIS row count anomalies
- Standard: 6 VARIS rows per variant (company code + account range + currency type + date + flags + mode)
- 2 rows: minimal/narrow scope (e.g., `UBO GRP CUR` — only specifies BUKRS + currency type)
- 7 rows: SAP-delivered variants have extra criteria
- 0 rows: variant exists in VARI but has no selection criteria in VARIS → will run with empty selections (risky — may process all accounts system-wide)

## UNESCO-Specific Findings (Session #078 — SAPF100)

### Variant Inventory
21 UNESCO operational variants + 6 SAP-delivered:

| Company Code | Variants | Issue |
|-------------|----------|-------|
| IBE | IBE_OI, IBE_UNBA | Clean |
| ICBA | ICBA_OI, ICBA_UNBA | Clean |
| ICTP | ICTP_OI only | **⚠ No ICTP_UNBA — balance-sheet accounts not covered** |
| IIEP | IIEP_OI, IIEP_UNBA | Clean |
| MGIE | MGIE_OI, MGIE_UNBA | Clean |
| UBO | UBO GRP CUR, UBO_OI_AR/AP, UBO_OI_G/L, UBO_UNBA | 4 variants (most complex) |
| UIL | UIL_OI, UIL_UNBA | Clean |
| UIS | UIS_OI, UIS_UNBA | Clean |
| UNES | UNES_DEPOSIT, UNES_OI_AR/AP, UNES_OI_G/L, UNES_UNBA | **UNES_DEPOSIT hits 6 blocked bank accounts** |

### Error-Generating Variant: UNES_DEPOSIT
- Targets bank/deposit accounts in UNES company code
- 6 active HKONTs have blocked LKORR (T030H→SKB1 cross-reference)
- Every run (valuation + reversal) generates "Account XXXX is blocked for posting"
- Fix: OBA1/KDF → update LKORR to active account, or unblock the LKORR account

### Reversal Pattern
No dedicated reversal variants exist. Accountants use the same variant for both valuation (BUDAT=month-end) and reversal (BUDAT=day-1) by checking the reversal flag at runtime. Confirmed by BKPF: TCODE=FBB1 appears for both types under the same USNAM.

### ZWG Alert
HKONT 0001194316 (Zimbabwe Gold, ZWG, new since Apr 2024) has LKORR 0001194314 already blocked. The UNES_DEPOSIT variant covers this account. Growing undetected FX exposure.

## Reusable Extraction Script

See: `Zagentexecution/mcp-backend-server-python/extract_sapf100_variants.py`

Parameterize by changing `PROGRAM = "SAPF100"` to any program name.

## Gold DB Tables Used

| Table | Purpose |
|-------|---------|
| `sapf100_vari` | SAPF100 variant headers (created by extraction script) |
| `sapf100_varid` | SAPF100 VARID rows (partial — pool table limitation) |
| `T030H` | FX account determination (KTOPL=UNES, 1,014 rows) |
| `SKB1` | Company-code GL accounts with XSPEB block flag |
| `P01_SKA1` | Chart-of-accounts GL data (KTOKS for account type) |
| `bkpf` | Document headers — verify actual execution (TCODE=FBB1) |
| `bsis` | Document line items — verify which HKONTs were actually posted |
