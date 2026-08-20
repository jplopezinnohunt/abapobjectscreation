# SAP Program Variant Forensic Methodology

**Domain**: Closing Activities / Configuration Audit  
**Discovered**: Session #078 (2026-06-05)  
**Evidence tier**: TIER_1 — direct P01 production extraction  
**Applies to**: Any ABAP report/program with SAP selection-screen variants

---

## What Are SAP Variants?

A SAP **variant** saves the selection-screen parameter values for an ABAP program so it can be re-run repeatedly with the same inputs. They are the mechanism by which accountants run `F.05 / SAPF100` for specific company codes, account ranges, and currency types each month-end.

Understanding a program's variants tells you:
- **Who** is expected to run it (variant owner = ENAME in VARI)
- **For which company codes** (BUKRS selection parameter)
- **For which accounts** (HKONT range — P_ or S_ parameter)
- **How broad the scope is** (number of VARIS selection rows)
- **Whether coverage is complete** (missing variants = missing revaluation)

---

## SAP Variant Table Architecture

> ⛔ **CORREGIDO s102 (2026-08-20). Lo que decía esta sección era falso y bloqueaba el análisis.**
> Se afirmaba que VARI/VARID/VARIS son **pool tables (VARPOOL)** y que **"no hay workaround vía RFC"**.
> Medido con `DD02L`: las tres son **`TRANSP`**. Y el workaround existe, funciona en P01 y no necesita
> `S_DEVELOP`. El texto original se conserva abajo tachado por trazabilidad (CP-001).

| Table | Type (DD02L) | Content | RFC_READ_TABLE |
|-------|--------------|---------|----------------|
| `VARID` | **TRANSP** | Variant directory (REPORT, VARIANT, TRANSPORT, ENVIRONMNT, PROTECTED) | ✅ multi-campo |
| `VARIT` | TRANSP | Variant texts (VTEXT) | ✅ |
| `VARI` | **TRANSP** | El contenido real, en `CLUSTD` — **tipo X, 2.886 bytes**, cluster serializado | ❌ campo RAW |
| `VARIS` | TRANSP | Solo 4 campos (MANDT, REPORT, DYNNR, VARIANT). **No contiene rangos.** Vacía aquí | ❌ irrelevante |

**Por qué fallaba, de verdad:** no por arquitectura de pool, sino porque el contenido está en un campo
**RAW** que `RFC_READ_TABLE` no devuelve, y porque `VARIS` no es la tabla de rangos que creíamos.

**La vía correcta — `RS_VARIANT_CONTENTS_RFC`** (remote-enabled, read-only, funciona sobre P01):

```python
r = conn.call("RS_VARIANT_CONTENTS_RFC", REPORT="SAPF100", VARIANT="UNES_DEPOSIT", VALUTAB=[])
# VALUTAB: SELNAME · KIND (P=parámetro, S=select-option) · SIGN (I/E) · OPTION (EQ/BT…) · LOW · HIGH
```

Se descubrió preguntándole al sistema, no recordando:
`RFC_READ_TABLE` sobre `TFDIR WHERE FMODE = 'R' AND FUNCNAME LIKE '%VARI%'`.

<details><summary>Texto original (refutado, conservado por trazabilidad)</summary>

~~VARPOOL is a SAP table pool — a physical storage optimization where multiple logical tables share
one database table. RFC_READ_TABLE can read the VARIANT field only; adding any second field causes
`TABLE_WITHOUT_DATA` (AD-718). This is architecture, not authorization — no workaround via
RFC_READ_TABLE.~~

</details>

---

## What You CAN Extract via RFC

### Always available — variant names

```python
result = conn.call('RFC_READ_TABLE',
    QUERY_TABLE='VARI',       # or 'VARIS'
    FIELDS=[{'FIELDNAME': 'VARIANT'}],
    OPTIONS=[{'TEXT': f"REPORT = '{program}'"}],
    ROWCOUNT=500
)
variants = sorted(set(row['WA'].strip() for row in result['DATA'] if row['WA'].strip()))
```

`VARI` returns **one row per variant** (deduplicate gives unique list).  
`VARIS` returns **one row per selection criterion** per variant — count gives scope complexity.

### Selection complexity metric (VARIS row count per variant)

```python
from collections import Counter
result = conn.call('RFC_READ_TABLE', QUERY_TABLE='VARIS',
    FIELDS=[{'FIELDNAME': 'VARIANT'}],
    OPTIONS=[{'TEXT': f"REPORT = '{program}'"}], ROWCOUNT=1000)
counts = Counter(row['WA'].strip() for row in result['DATA'])
```

**Interpretation:**
| VARIS rows | Meaning |
|-----------|---------|
| 0 | Variant has no selection options — will run with default/empty selections (risky) |
| 2–4 | Minimal scope: company code + currency type only |
| 6 | Standard: company code + account range + currency + date + mode flags |
| 7+ | Extended criteria (SAP-delivered variants, or complex custom scopes) |

---

## What Requires ABAP Code (D01 only — not P01)

To get full variant content (VTEXT, ENAME, ADATE, selection values), use `RFC_ABAP_INSTALL_AND_RUN` on D01:

```python
code = """
REPORT ZVAR_READ.
DATA: lt_vari TYPE TABLE OF vari, ls_vari TYPE vari,
      lt_varid TYPE TABLE OF varid, ls_varid TYPE varid,
      lt_varis TYPE TABLE OF varis, ls_varis TYPE varis.
SELECT * FROM vari  INTO TABLE lt_vari  WHERE report = 'PROGRAM'.
SELECT * FROM varid INTO TABLE lt_varid WHERE report = 'PROGRAM'.
SELECT * FROM varis INTO TABLE lt_varis WHERE report = 'PROGRAM'.
LOOP AT lt_vari  INTO ls_vari.  WRITE: / 'V~', ls_vari-variant,  '~', ls_vari-vtext, '~', ls_vari-ename, '~', ls_vari-adate. ENDLOOP.
LOOP AT lt_varid INTO ls_varid. WRITE: / 'D~', ls_varid-variant, '~', ls_varid-selname, '~', ls_varid-kind, '~', ls_varid-low, '~', ls_varid-high. ENDLOOP.
LOOP AT lt_varis INTO ls_varis. WRITE: / 'S~', ls_varis-variant, '~', ls_varis-selname, '~', ls_varis-sign, '~', ls_varis-option, '~', ls_varis-low, '~', ls_varis-high. ENDLOOP.
"""
result = conn.call('RFC_ABAP_INSTALL_AND_RUN',
    PROGRAM=[{'LINE': line[:72]} for line in code.split('\n')])
writes = result.get('WRITES', [])
```

**Blocked on P01** — requires `S_DEVELOP` authorization which is not granted on production.  
**Works on D01** — development system has this authorization.

---

## Step-by-Step Forensic Protocol

### Phase 1: Discovery
1. Extract variant names from VARI (single field read)
2. Count VARIS rows per variant (complexity metric)
3. Identify SAP-delivered variants (`SAP&*` prefix) — exclude from operational analysis

### Phase 2: Coverage Analysis
4. Map variants to company codes from naming convention (e.g., `BUKRS_TYPE`)
5. Check: does every BUKRS have the expected variant types?
6. Flag: any BUKRS completely missing = that company code's accounts never processed

### Phase 3: Risk Cross-Reference (Gold DB)
7. For FX programs: join T030H × SKB1 to find blocked adjustment accounts
8. Check if active HKONTs (XSPEB blank) have blocked LKORR (XSPEB='X')
9. Those HKONTs will generate runtime errors if they fall within variant scope

### Phase 4: Execution Verification (BKPF)
10. Query BKPF with `TCODE = program's posting TCODE` to verify variants are actually running
11. Check all expected BUKRS appear in BKPF results
12. Measure CPUDT - BUDAT lag to assess timeliness
13. Identify missing months or missing BUKRS = variant never ran

### Phase 5: Reversal Analysis
14. Check BKPF for BUDAT = first day of month with same TCODE
15. If reversal docs present → reversal works (same or different variant)
16. If reversal docs missing → reversal not performed → BS accounts double-counted

---

## Variant Naming Convention Patterns

**UNESCO SAPF100 specific** (generalizable to other programs):

| Suffix | Type | Account Scope | Reversal Risk |
|--------|------|---------------|---------------|
| `_OI` | Open Items | AR/AP subledger items | Low — open items self-reverse when cleared |
| `_UNBA` | Unbalanced GL | Balance-sheet accounts without OI management | High — must reverse manually |
| `_OI_AR/AP` | AR/AP subledger only | Creditor + debtor items | Low |
| `_OI_G/L` | G/L OI only | G/L open-item managed accounts | Low |
| `_DEPOSIT` | Bank/cash accounts | Cash + bank balance-sheet GL | High — errors if LKORR blocked |
| `GRP CUR` | Group currency | Cross-currency consolidation | Medium |
| `SAP&*` | SAP standard | Internal audit — not operational | N/A |

**General patterns (any program):**
- Single prefix `{BUKRS}` → company-code-specific
- No prefix → global / cross-company-code
- `_TEST` or `_BAK` suffix → test/backup variants, usually stale
- `SAP&` prefix → SAP-delivered, do not modify

---

## Common Defects Found by This Analysis

| Defect | Signal | Impact |
|--------|--------|--------|
| Missing `_UNBA` variant for a BUKRS | No variant of that type in VARI | Balance-sheet FX accounts silently excluded |
| Blocked LKORR in T030H | T030H.LKORR has XSPEB='X' in SKB1 | Runtime error at next execution |
| Stale account range | VARI.ADATE old vs new account creation date | New accounts excluded from scope |
| No reversal evidence in BKPF | BUDAT=day-1 docs missing | Balance sheet overstated for the month |
| ZWG/new currency in blocked state | New HKONT with blocked LKORR from creation | Growing undetected exposure |
| 0 VARIS rows | No selection criteria saved | Program runs with empty screen = processes everything or nothing |

---

## UNESCO-Specific Results — SAPF100 (Session #078)

### Variant Count
- **21 operational variants** (VARI): 2–4 per company code
- **6 SAP-delivered variants** (VARIS only): `SAP&AUDIT_*`, `SAP&FW_*`
- **Total VARIS rows**: 164 selection criteria records

### Key Findings

**Finding 1: UNES_DEPOSIT = primary error generator**
- This variant explicitly targets bank/deposit accounts in UNES
- 6 active HKONT accounts have blocked LKORR (T030H × SKB1 cross-reference)
- Accounts: 0001010571, 0001010574, 0001110571, 0001110574, 0001143254, 0001194316
- Error on EVERY run (valuation + reversal)
- Fix: OBA1 / transaction KDF → update LKORR to active account

**Finding 2: ICTP missing ICTP_UNBA**
- All other 8 company codes have both `_OI` and `_UNBA` variants
- ICTP only has `ICTP_OI`
- ICTP balance-sheet FX accounts are structurally excluded from monthly revaluation
- Independent of the timing gap issue (Jul+Nov 2025, May 2026 missed months)

**Finding 3: No dedicated reversal variants**
- Reversal not done via a separate variant
- Same variants used for both valuation (BUDAT=month-end) and reversal (BUDAT=day-1)
- Confirmed by BKPF: TCODE=FBB1, USNAM=accountant, for both document types
- Risk: if accountant reverses wrong period or uses wrong variant, silent error

**Finding 4: ZWG account added 2024, LKORR already blocked**
- HKONT 0001194316 (Zimbabwe Gold currency) created ~Apr 2024
- T030H entry exists with LKORR 0001194314
- LKORR is already XSPEB='X' — was never set up correctly
- UNES_DEPOSIT covers this account → error every run since 2024

---

## Related Skills and Knowledge

- Skill: `sap_house_bank_configuration` — when blocked accounts are bank GL accounts, check house bank config
- Skill: `sap_account_comparison` — compare G/L account flags between D01 and P01
- Knowledge: `knowledge/domains/Closing_Activities/fx_revaluation_closing_calendar_2025.md` — execution timing context
- Knowledge: `knowledge/domains/Closing_Activities/README.md` — domain overview
- Table: `T030H` — FX account determination (OBA1/KDF configuration)
- Table: `SKB1.XSPEB` — G/L account block flag at company-code level

---

## Applicable Programs

This methodology applies to any ABAP program that uses variants for periodic execution:

| Program | Transaction | Variants Analyze For |
|---------|------------|---------------------|
| `SAPF100` | F.05 | FX revaluation — company code + account scope |
| `FAGL_FCV` | FAGL_FCV | New GL FX revaluation (S/4HANA) |
| `SAPF124` | F.13 | Automatic clearing — account scope per run |
| `RFFOUS_C` / `RFFOAVIS` | F110 | Payment program — house bank + payment methods |
| `RFEBBU00` | FF.5 | Bank statement import — bank account selection |
| `SAPF010` | F.01 | Financial statements — G/L account range |
| `RSUSR003` | SU10 | User maintenance — org object selection |

The same extraction pattern (VARI/VARIS single-field read + naming convention decode + BKPF verification) applies to all.
