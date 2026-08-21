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

| Table | Type (DD02L) | Content | RFC_READ_TABLE? |
|-------|--------------|---------|-----------------|
| `VARID` | **TRANSP** | Variant directory: REPORT, VARIANT, TRANSPORT, ENVIRONMNT, PROTECTED | ✅ **multi-field, funciona** |
| `VARIT` | TRANSP | Variant texts (VTEXT) | ✅ |
| `VARI` | **TRANSP** | The actual content — in `CLUSTD`, **type X, 2.886 bytes**: a serialized cluster | ❌ el campo es RAW |
| `VARIS` | TRANSP | Only 4 fields (MANDT, REPORT, DYNNR, VARIANT) — **no ranges at all**; empty here | ❌ irrelevante |

> ⚠️ **CORRECCIÓN (s102, 2026-08-20).** Versiones anteriores de este skill afirmaban que
> VARI/VARID/VARIS son **pool tables** y que "no hay workaround vía RFC". **Las dos cosas son falsas.**
> `DD02L.TABCLASS` dice `TRANSP` para las tres. Lo que impide leer el contenido con `RFC_READ_TABLE`
> no es la arquitectura de pool: es que **el contenido vive en un campo RAW** (`VARI.CLUSTD`), y
> `VARIS` simplemente no contiene rangos. **Y sí existe workaround, sin `S_DEVELOP` y sobre P01.**
> La afirmación errónea bloqueó durante sesiones un análisis que tarda segundos.

### ✅ EL MÉTODO: `RS_VARIANT_CONTENTS_RFC` (remote-enabled, funciona en P01)

```python
r = conn.call("RS_VARIANT_CONTENTS_RFC", REPORT="SAPF100", VARIANT="UNES_DEPOSIT", VALUTAB=[])
for x in r["VALUTAB"]:            # SELNAME · KIND · SIGN · OPTION · LOW · HIGH
    if x["LOW"].strip() or x["HIGH"].strip():
        print(x["SELNAME"], x["KIND"], x["SIGN"], x["OPTION"], x["LOW"], x["HIGH"])
```

`KIND`: `P` = parámetro simple · `S` = select-option. `SIGN` `I`/`E` = incluir/excluir.
`OPTION` `EQ`/`BT`/… Devuelve **también** los parámetros de pantalla (fechas, flags de modo,
método de valoración), no solo los rangos de cuentas — que es donde está la mitad del proceso.

**Cómo se descubrió, y cómo repetirlo con cualquier otro FM:** pregúntale al sistema en vez de
recordar. `RFC_READ_TABLE` sobre `TFDIR WHERE FMODE = 'R' AND FUNCNAME LIKE '%VARI%'` lista los FM
remote-enabled. Ahí aparecen `RS_VARIANT_CONTENTS_RFC` y `RS_VARIANT_CONTENTS_255_RFC`.
Ojo: `RS_VARIANT_CONTENTS` **sin** el sufijo `_RFC` existe pero **falla** al serializar su parámetro
EXPORT `SP` de tipo `SYLDB_SP`; `RS_VARIANT_TEXTS` y `GET_SELECTIONS_OF_VARIANT` no existen.

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

### Step 3 — Decode Variant Content → **usa `RS_VARIANT_CONTENTS_RFC`** (arriba)

Es la vía de primera elección: funciona en **P01**, es **read-only** y **no necesita `S_DEVELOP`**.
Lo de abajo queda como plan B histórico para un sistema donde ese FM no exista.

<details><summary>Plan B (legacy): RFC_ABAP_INSTALL_AND_RUN en D01</summary>

⚠️ Este método **no lee el contenido real**: `SELECT * FROM varis` devuelve una tabla que no tiene
rangos, y `VARI-CLUSTD` sale como binario. Se conserva solo por trazabilidad de cómo se intentó.
Requiere `S_DEVELOP`, bloqueado en P01.

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

</details>

---

## ✍️ ESCRIBIRLAS: alinear variantes entre sistemas (probado 2026-08-21)

No se transportan (`VARID.TRANSPORT='F'`) pero **sí se escriben por RFC** — peldaño 1, API estándar,
sin excepción. `RS_VARIANT_DELETE_RFC` (VARIANT es CHANGING, `USE_EXCEPTIONS='X'`) +
`RS_CREATE_VARIANT_RFC`. **`RS_VARIANT_CHANGE_RFC` no sirve**: sin tabla de contenido, es de diálogo,
así que modificar = borrar y recrear.

Herramienta: `Zagentexecution/tasks/2026_08_21_variant_alignment/variant_align.py`.
Resultado en UNESCO: **21/21 variantes de SAPF100 idénticas a P01 en D01 y V01**.

**Dos trampas que corrompen sin dar error:** (1) las fechas salen en formato externo `31.07.2026` y
entran en interno `20260731` — mandarlas tal cual escribe basura (`20.7..31.0`); (2) lo que no se
envía se rellena con defectos en silencio. Snapshot PRE + readback POST no son ceremonia: cazaron
las dos.

**Clasifica antes de copiar**: selección (`SKONTO`/`AKONTO`) · modo (`PAR_BNAM`, `PA_WEREF`/`PA_WEREN`,
`BWMET1`) · residuo de la última corrida (periodos, fechas). "Hazlas idénticas" puede borrar nombres
de sesión batch y voltear banderas de alcance.

## 🔑 POR QUÉ ESTO IMPORTA MÁS QUE LAS VARIANTES — la variante ES el proceso

Una variante no es una comodidad de usuario: **es dónde se instancia el proceso**. El programa dice
lo que se *puede* hacer; la variante dice lo que **se hace de verdad**, y como cada una se crea a mano
para un caso concreto, **cada variante es una combinación única** que no está en ninguna
documentación. Leerlas convierte "sé qué programa corre" en "sé qué hace, sobre qué, con qué
parámetros y con qué resultado".

### La cadena que desbloquea

```
TBTCO/TBTCP (¿qué job corrió, cuándo, con qué usuario?)
   └─ TBTCP.PROGNAME + TBTCP.VARIANTE      ← el job nombra la variante
        └─ RS_VARIANT_CONTENTS_RFC(REPORT, VARIANT)
             └─ VALUTAB: rutas de fichero, sociedades, rangos de cuentas, fechas, flags de modo
```

**Sin el último paso, un análisis de jobs solo sabe QUE algo corrió. Con él, sabe QUÉ hizo.**

### Casos de uso (no solo cierre)

| Pregunta | Qué se lee en la variante |
|---|---|
| **¿Dónde deja los ficheros esta interfaz?** | el parámetro de ruta / nombre de fichero del programa que lanza el job |
| ¿Qué sociedades y qué rango cubre este job? | `BUKRS`, rangos de cuenta/objeto |
| ¿Este job revalúa, reversa, o simula? | flags de modo (`X_SALBEW`, `X_GL`, `ST_BUDAT`, `TESTLAUF`) |
| ¿Qué formato/árbol DMEE usa esta corrida de pagos? | parámetros de `SAPFPAYM` / programas de medio de pago |
| ¿Coincide lo configurado con lo que se ejecuta? | cruce config (p.ej. `T030H`) × selección de la variante |
| ¿Por qué este objeto nunca se procesa? | está en la config pero **fuera de la selección** — fallo silencioso |

### La regla que sale de aquí

**Un objeto puede estar perfectamente configurado y no procesarse nunca porque no entra en la
selección de ninguna variante.** No da error: simplemente no ocurre. Medido en UNESCO s102: de las 5
cuentas `40410xx` con filas en `T030H`, solo 2 están en una variante. Cualquier auditoría de
configuración que no cruce contra la variante es incompleta por construcción.

### Cuidado — el mecanismo de selección cambia entre variantes del MISMO programa

En SAPF100/UNES: `UNES_DEPOSIT` selecciona por **16 valores `EQ` sueltos**, mientras `UNES_UNBA`,
`UNES_OI_G/L` y `UNES_OI_AR/AP` usan **rangos `BT`**. Asumir "se añade por rangos" es erróneo la
mitad de las veces. **Lee la variante antes de decir cómo se añade algo a ella.**

### Pendiente (exploración futura, marcada por JP s102)
Aplicar esto sistemáticamente a **DMEE + reports + variantes**: mapear cada job de interfaz a su
variante y extraer las rutas de fichero, para cerrar el modelo de "por dónde entran y salen los
ficheros" que hoy está a medias (claim 536).

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

---

## Where these tables are defined — read before querying them

Every gold table this skill names is defined in **`knowledge/gold_db_table_catalog.md`**:
real SAP name, what it is, how we use it, key, and provenance. **The catalogue also records
the TRAPS**, and each one produces a confident wrong number when missed:

- **`reguh`** — `XVORL='X'` marks **F110 PROPOSALS, not payments** (358,106 of 3,707,737,
  9.7%). `PERNR` is populated on 1,195,826 rows (32%) — those are **employee** payments, not
  vendors. `KUNNR` is part of the SAP key and was not extracted (1,748 key collisions).
- **`fmioi`** — FM commitments. **Never hand-roll availability from `WRTTP`**: that approach
  is REFUTED. AVC availability comes from the standard (`FMAVCT`/`FMAVCR`). FMIOI answers
  what is *committed*, never what is *left*.
- **`cdhdr_history`** — read this one. The `cdhdr` copy is a **superseded, scope-filtered
  snapshot** (57 object classes against 72) and reports **zero PBC change activity where
  there are 3,449,049**.
- **`bkpf`/`bseg`** — `bseg` is a **JOIN via the Golden Query**, never extracted or enriched.

Claims: **#386** (CDHDR) · **#387** (REGUH, FMIOI) · **#388** (PBC write path).

**When a table here has no maintenance transaction, do not guess what writes it** — run
algorithm **A8**, `process_mining/attribute_changes_to_programs.py`, which derives the write
path and its channel from the logs.
