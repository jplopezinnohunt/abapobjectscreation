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

## ⛔ EL CANAL DE ESCRITURA — API ESTÁNDAR, NUNCA INSERT PLANO (corregido s102, 2026-08-20)

**`RFC_ABAP_INSTALL_AND_RUN` con `INSERT` directo está PROHIBIDO para master data ESTÁNDAR.**
Solo es legítimo para **tablas propias `Y*`/`Z*`**. Las secciones "4-Step Method" y "Script Location"
de más abajo prescribían INSERT plano sobre SKA1/SKAT/SKB1: **eso es incorrecto y no se usa.**
`METHOD.md` del sync FM ya lo decía en junio ("Verified write channels — NOT flat INSERT for
standard master"); este skill nunca se alineó.

Por qué importa, más allá de la regla: la API estándar rellena **derivación, rangos de numeración,
validez, jerarquía y checks de consistencia**. Un `INSERT` los salta todos y deja un registro que
parece correcto en la tabla y está roto para el proceso.

### Matriz de canales — MEDIDA en P01 (`TFDIR WHERE FMODE='R'`), no recordada

| Objeto | Lectura (P01, read-only) | Escritura (D01 / V01) |
|---|---|---|
| **Cuentas GL** (SKA1/SKAT/SKB1) | `GL_ACCT_MASTER_GET_COA_RFC` (plan + textos) · `GL_ACCT_MASTER_GET_CCODE_RFC` (sociedad) | **`GL_ACCT_MASTER_SAVE_RFC`** |
| **Centros de coste** | `BAPI_COSTCENTER_GETDETAIL1` | `BAPI_COSTCENTER_CREATEMULTIPLE` · `_CHANGEMULTIPLE` |
| **Fondos** (FMFINCODE/FMFINT) | `FM_FUND_GET_DETAIL_RFC` | `FM_FUND_CREATE_RFC` · `FM_FUND_CHANGE_RFC` |
| **Centros gestores** (FMFCTR) | `FM_FUNDS_CTR_GET_DETAILS_RFC` | `FM_FUNDS_CTR_CREATE_RFC` |
| **Proyectos / WBS** (PROJ/PRPS) | `BAPI_PROJECTDEF_GETDETAIL` + `PRPS` | `BAPI_PROJECT_MAINTAIN` + `BAPI_TRANSACTION_COMMIT` |
| **Versión de balance (FSV)** `FAGL_011PC/QT/ZC/SC` | `RFC_READ_TABLE` (**no** le afecta `CCCOPYLOCK`) | **sin API.** `OB58` en D01 + transporte D01→V01 · o **EXC-001** (peldaño 3, autorizada) |
| **Tablas propias `YTFM_*`, `YTFI_*`** | `RFC_READ_TABLE` | `RFC_ABAP_INSTALL_AND_RUN` INSERT — **único uso legítimo sin excepción** |

**Centros de beneficio: NO se usan en UNESCO** (dirección de JP, s102). `BAPI_PROFITCENTER_CREATE`
existe y está remote-enabled, pero está fuera de alcance. No sincronizar.

**Elementos de coste:** `BAPI_COSTELEMENT_CREATEMULTIPLE` **no** está remote-enabled en P01. Medido.
Antes de sincronizarlos hay que resolver el canal — no asumir que hay uno.

### ☠️ LA TRAMPA DEL FLAG DE SIMULACIÓN — es INVERSA entre APIs

| FM | Flag | Si lo OMITES |
|---|---|---|
| `FM_FUND_CREATE_RFC` / `FM_FUND_CHANGE_RFC` | `I_FLG_TESTRUN` (**default `'X'`**) | **simulación silenciosa**: 0 filas, `ET_MESSAGES` vacío, parece éxito |
| `GL_ACCT_MASTER_SAVE_RFC` | `TESTMODE` (**default vacío**) | **ESCRITURA REAL** |

Las dos direcciones muerden. **Pasa el flag SIEMPRE de forma explícita**, en los dos sentidos, y
verifica releyendo — nunca por código de retorno.

### 🪜 LA ESCALERA DE CANALES — qué usar cuando no hay API (s102)

No es binario "API o INSERT". Hay **tres peldaños**, y se baja solo cuando el de arriba no existe:

| # | Canal | Cuándo | Respeta el framework | Graba en orden |
|---|---|---|---|---|
| **1** | **API estándar** (BAPI / FM RFC del objeto) | existe un FM en `TFDIR FMODE='R'` | ✅ | según el objeto |
| **2** | **BC-Set** (`SCPRMP_UPDATE_BCSET_REMOTE` → `SCPR_ACTIV_MN_REMOTE_SUB`) | **customizing sin API** | ✅ escribe por el framework | ✅ `TASK_CUST_EXP` |
| **3** | `RFC_ABAP_INSTALL_AND_RUN` INSERT | tablas propias `Y*`/`Z*` · **y EXCEPCIÓN AUTORIZADA** (abajo) | ❌ | ❌ |

---

## ⚖️ EXCEPCIONES AUTORIZADAS — el peldaño 3 sobre tablas estándar

**Prohibido por defecto. Permitido solo bajo este régimen, y declarándolo.**

### Qué es exactamente la técnica
`RFC_ABAP_INSTALL_AND_RUN` **genera e instala un report ABAP al vuelo** (p. ej. `REPORT Z_GL_COPY.`)
con sentencias `INSERT` y lo ejecuta. No deja un objeto ABAP permanente —de ahí la impresión de que
"no hay ABAP"— pero **sí se genera y ejecuta código ABAP** en cada lote. Es la técnica con la que se
hizo el sync de GL del **2026-04-03** (`copy_gl_accounts_p01_to_d01.py`, hoy en `_obsolete/`) y es
de la misma familia que causó **INC-CLASS-LOSS**.

### Cuándo se puede autorizar
Cuando se cumplen **las tres**:
1. No existe API estándar (comprobado en `TFDIR WHERE FMODE='R'`, no de memoria).
2. El peldaño 2 (BC-Set) no es viable — p. ej. exige un bootstrap manual que no se puede hacer ahora.
3. **JP lo autoriza explícitamente para ese caso concreto.** No hay autorización permanente ni
   extensible a "casos parecidos".

### Las diez puertas — todas obligatorias, todas en el código, no en la intención

| # | Puerta |
|---|---|
| G1 | **Destino ∈ {D01, V01}. P01 jamás.** Rechazo cableado por nombre de sistema, no por parámetro |
| G2 | **Origen = P01 leído EN VIVO.** Nunca valores escritos a mano, nunca del Gold DB (su caché va meses por detrás) |
| G3 | **Solo `INSERT` de filas AUSENTES.** Nada de `UPDATE` ni `DELETE` sobre filas existentes: eso exige humano |
| G4 | **Lista blanca de tablas literal en el script.** Nunca un nombre de tabla por parámetro libre |
| G5 | **PRE-readback a fichero** antes de tocar nada, y **POST-readback campo a campo contra P01**. Aborta ante cualquier diferencia |
| G6 | **Orden referencial declarado y forzado** (para la FSV: `FAGL_011PC` → `FAGL_011QT` → `FAGL_011ZC` → `FAGL_011SC`) |
| G7 | **Dry-run por defecto**; `--commit` explícito para escribir |
| G8 | **Tope de filas** y aborto si la clave ya existe en destino |
| G9 | **Registro auditable** de cada invocación: quién autorizó, cuándo, qué claves, resultado |
| G10 | **Declarar las claves escritas** y registrarlas después en una orden de customizing; verificar con `Zagentexecution/quality_checks/config_transport_prerelease_check.py` |

### El coste que NO desaparece, y cómo se paga
Un `INSERT` en crudo **no queda en ninguna orden de transporte**. Y D01 es el **origen** de los
transportes hacia P01: customizing escrito así es invisible para CTS, así que D01 deja de ser una
fuente fiel. **G10 es la que paga esa deuda**: tras escribir, se registran las claves en una orden
de customizing (`SE01` → lista de objetos → `R3TR TABU <tabla>` + claves) y se pasa el check de
pre-liberación, que además detecta la clase de defecto "clave intrusa" del caso Indonesia.

Sin G10 el sistema queda alineado en el dato y desalineado en la trazabilidad — que es exactamente
el problema que estábamos intentando arreglar.

### 📋 REGISTRO DE EXCEPCIONES AUTORIZADAS — lista cerrada

**Lo que no está en esta tabla, NO está autorizado.** No se extiende por analogía, ni a "otra tabla
de customizing parecida", ni a otra sociedad, ni a otro destino. Cada ampliación es una fila nueva
con fecha y autorización explícita de JP.

| id | Alcance | Tablas | Destinos | Operación | Autorizada por | Fecha | Estado |
|---|---|---|---|---|---|---|---|
| **EXC-001** | **Versión de balance (FSV)**, chart `UNES` | `FAGL_011PC` · `FAGL_011QT` · `FAGL_011ZC` · `FAGL_011SC` | **D01, V01** | **solo `INSERT` de filas ausentes** | JP | 2026-08-20 | 🟢 vigente, sin ejecutar |

**Fuera de EXC-001, explícitamente NO autorizado** (aunque el mecanismo sea el mismo y la tentación
grande): `T030H`/OB09 · variantes de F.05 · `T011`/`T011T` · maestro de GL, centros de coste, fondos,
centros gestores y proyectos —esos **sí** tienen API estándar y van por el peldaño 1— y cualquier
tabla en P01, sin excepción posible.

### Por qué el riesgo es menor en el caso FSV concreto (y por qué eso no elimina las puertas)
El contenido se copia **verbatim de P01**, que es consistente por construcción; se insertan filas
ausentes, no se modifican existentes; el destino nunca es producción; y hay un comparador
determinista (`fsv_alignment_check.py`) que **prueba** el resultado antes y después. Eso hace la
excepción defendible. No la hace automática: las diez puertas siguen siendo obligatorias, porque lo
que falla no es el caso bien pensado — es el siguiente, hecho por analogía.

**El peldaño 2 es el que faltaba en este proyecto** y es el mecanismo genérico para actualizar
tablas cuando no hay RFC ni BAPI: en vez de escribir la tabla por debajo, se le entregan los
valores al framework de customizing, que los aplica con sus checks y los graba en una orden.

#### Estado del peldaño 2 — medido s102, y tiene UN hueco

| Paso | FM | RFC | Estado |
|---|---|---|---|
| Leer origen | `RFC_READ_TABLE` | ✅ | funciona, **no** afectado por `T000.CCCOPYLOCK` |
| **Crear** el BC-Set | `SCPR_CTC_DB_SAVE_BCSET` · `SCPR_PRSET_MN_BCSET_SAVE` · `SCPR_EXT_BCSET_WRITE` · `SCPR_TEMPL_MN_CREATE_WITH_*` | ❌ **ninguno remote-enabled** (`FMODE` en blanco) | 🔴 **paso manual, una vez por sistema**: `SCPR20`/`SCPR3` |
| Poblarlo | `SCPRMP_UPDATE_BCSET_REMOTE` | ✅ | actualiza uno **existente**; con id inexistente es **no-op silencioso** (devuelve tablas vacías, sin excepción) |
| Simular | `SCPR_ACTIV_MN_REMOTE_SUB` con `SIMULATION_ON='X'` | ✅ | |
| Activar | mismo FM sin simulación | ✅ | devuelve la orden en `TASK_CUST_EXP` |

**Gotcha que cuesta una hora:** `PROTO_HANDLE` **no puede ir vacío** — es un GUID de 32 caracteres
(`SCPR_HANDL` / dominio `SCPR_GUID`). Con vacío devuelve el genérico
`WRONG_PARAMETERS / SCPR 273 "Function module call error"` con **cualquier** `ACTIVATION_TYPE`, lo
que parece un problema de tipo de activación y no lo es. Con un GUID válido el error pasa a
`NO_BCSET / SCPR 223`, que ya es información.

**Conclusión operativa:** el mecanismo es genérico y reutilizable para **cualquier** tabla de
customizing, pero exige **un bootstrap manual**: crear una vez a mano un BC-Set `Z` vacío en cada
destino. A partir de ahí, todo el bucle es RFC y repetible. SAP no expone la creación por RFC a
propósito: crear un BC-Set es una actividad de desarrollo, no de ejecución.

### Reglas transversales de todos los canales
1. **Verifica releyendo, no por `RETURN`.** Un `BAPIRET2` sin errores no prueba que se escribió.
2. **`BAPI_*` necesita `BAPI_TRANSACTION_COMMIT`** explícito (`WAIT='X'`); en error, `ROLLBACK`.
3. **Primero 1 registro**, comparación campo a campo contra P01, y solo después el lote.
4. **`pyrfc` rechaza `'00000000'` en campos DATS** — convertir a `''` antes de la llamada.
5. **Dependencias primero**: centros gestores antes que fondos; plan de cuentas antes que sociedad.

## Direction

**Always P01 → non-prod target.** Source = P01 (production, read-only). Target = **D01 (dev) or V01
(validation)** — same scripts, target is an argument. Never write P01.

**Reusable FM-model scripts** (target-parameterized, proven P01→D01 s093):
`Zagentexecution/tasks/2026_06_29_fm_model_sync/` — `fund_center_sync.py <TGT>`, `fund_sync.py <TGT>`,
`METHOD.md`. Run centers BEFORE funds (dependency). For V01 add `SAP_V01_*` to the RFC `.env`.

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

### Step 3: Copy via la API ESTÁNDAR del objeto (ver la matriz de canales arriba)

Para cuentas GL:

```python
# LECTURA en P01 (read-only)
coa  = src.call("GL_ACCT_MASTER_GET_COA_RFC",   ACCOUNT_COA={"CHRT_ACCTS": "UNES", "GL_ACCOUNT": saknr})
cc   = src.call("GL_ACCT_MASTER_GET_CCODE_RFC", ACCOUNT_CCODE={"COMP_CODE": "UNES", "GL_ACCOUNT": saknr})

# ESCRITURA en D01 / V01 — TESTMODE EXPLÍCITO SIEMPRE (su default vacío = escritura real)
res = tgt.call("GL_ACCT_MASTER_SAVE_RFC",
               ACCOUNT_COA=coa["ACCOUNT_COA"],
               ACCOUNT_NAMES=coa["ACCOUNT_NAMES"],      # todos los idiomas
               ACCOUNT_CCODES=[cc["ACCOUNT_CCODE"]],
               TESTMODE="X" if dry_run else "")
# y DESPUÉS: releer con GET_*_RFC en el destino y comparar campo a campo. Nunca fiarse de RETURN.
```

<details><summary>❌ Método antiguo (INSERT plano) — PROHIBIDO para master data estándar</summary>

⛔ Lo de abajo **solo vale para tablas propias `Y*`/`Z*`**. Aplicarlo a SKA1/SKAT/SKB1 salta la
derivación, los rangos de numeración y los checks de consistencia. Se conserva por trazabilidad.

#### (legacy) Copy via RFC_ABAP_INSTALL_AND_RUN

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

</details>

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
| `BAPI_GL_ACCOUNT_CREATE` | Does not exist in UNESCO system — **confirmado s102**: no aparece en `TFDIR` |
| `GL_ACCT_MASTER_MAINTAIN_RFC` | Raises NOT_FOUND — needs FS00 dialog session memory. **Es el FM equivocado**: el de escritura es `GL_ACCT_MASTER_SAVE_RFC` (ver matriz arriba) |
| BDC via `RFC_CALL_TRANSACTION_USING` + FS00 | User rejected batch input approach |
| `CSKBD` / `CSKBZ` extraction | TABLE_NOT_AVAILABLE — structures, not tables |
| `RFC_ABAP_INSTALL_AND_RUN` INSERT sobre SKA1/SKAT/SKB1 | ⛔ **PROHIBIDO** (s102). Salta derivación, rangos de numeración y checks. Solo para tablas propias `Y*`/`Z*` |

> **Cómo se recuperó el canal correcto (s102):** no consultando este skill —que estaba mal— sino
> preguntándole al sistema: `RFC_READ_TABLE` sobre `TFDIR WHERE FMODE = 'R' AND FUNCNAME LIKE
> '%ACCT_MASTER%'`. Ese es el reflejo a repetir cuando un skill diga "no existe canal": **el skill
> puede estar equivocado; el diccionario del sistema no.**

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
| 2026-06-29 | FMFINCODE, FMFINT, FMFCTR, FMFCTRT, FMCI, YTFM_FUND_C5, YTFM_FUND_CPL | ~63K gap counted (~16.7K scoped C5/43) | Gap analysis + write channels verified (claim #283/#284) |
| 2026-06-29 | FMFINCODE + FMFINT (E2E test) | 10 funds | E2E PROVEN: FM_FUND_CREATE_RFC (TESTRUN=' ') → 10/10 created in D01, verified field-by-field vs P01. Ready for mass C5/43 (5,349 funds) |

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

### Write method by object type — VERIFIED EMPIRICALLY ON D01 (s093 2026-06-29)

**SUPERSEDES the earlier "direct INSERT for FMFINCODE" guess.** Standard FM master must use the
standard RFC-enabled create FMs (probed REMOTE-OK on D01) — NOT flat table INSERT, which would leave
the BCS model inconsistent (derivation, validity, number ranges, hierarchy). This does NOT violate the
never-modify-standard-objects rule: we call SAP's own API, we do not write standard tables by hand.

| Object | Write method (verified) | Why |
|--------|-------------|-----|
| FMFINCODE + FMFINT | **`FM_FUND_CREATE_RFC`** (one call: `IS_FUND_DATA`+`IS_FUND_TEXT`) | Read source via `FM_FUND_GET_DETAIL_RFC` (P01). Map `FMFINCODE`→`FMFUND_DATA`, `FMFINT`→`FMFUND_TEXT` by field name (subset). Key via `I_FM_AREA`+`I_FUND` (external assignment = same FINCODE as P01). |
| FMFCTR + FMFCTRT + hierarchy | **`FM_FUNDS_CTR_CREATE_RFC`** (`IT_FUNDS_CTR_DATA`+`IT_FUNDS_CTR_TEXT`+`IS_FUNDS_CTR_HIVARNT`) | Handles hierarchy variant natively. Read via `FM_FUNDS_CTR_GET_DETAILS_RFC`. **E2E not yet run — test before mass (hierarchy risk).** |
| YTFM_FUND_C5 / FUND_CPL / OUTPUT(_T) | Direct INSERT via `RFC_ABAP_INSTALL_AND_RUN` | Z/Y own objects — INSERT is the correct path |

#### ⛔ GOTCHA — `I_FLG_TESTRUN` defaults to `'X'` (false-positive create)

Both `FM_FUND_CREATE_RFC` and `FM_FUNDS_CTR_CREATE_RFC` have `I_FLG_TESTRUN` **default = `'X'`**. If you
pass only `I_FLG_COMMIT='X'` and omit TESTRUN, the FM **simulates and writes NOTHING** — yet returns
`ET_MESSAGES` EMPTY (no error, no success). Looks like success, persists zero rows.
- **To persist:** pass `I_FLG_TESTRUN=' '` AND `I_FLG_COMMIT='X'`.
- **ET_MESSAGES is empty even on a real create** → "OK"/subrc proves nothing. **Raw read-back of
  FMFINCODE is mandatory** (same class of defect as MODIFY-vs-UPDATE persistence lesson).
- E2E proven s093: 10/10 C5/43 funds created in D01 and verified field-by-field (TYPE/PROFIL/DATAB/
  DATBIS/FINUSE/ZZOUTPUT) + FMFINT text against P01.

#### Scope lever — biennium C5/43
Dimensions WITH a biennium link (FMFINCODE/FMFINT, YTFM_FUND_C5, YTFM_FUND_CPL) scope to the active
biennium via the YTFM_FUND_C5 `C5_ID='43'` (2026-2027) fund set → ~16.7K rows (−74% vs full 63K), and
D01 is near-empty for the current biennium (only 115 of 5,464 active funds present). Dimensions WITHOUT
a biennium (FMFCTR, YTFM_OUTPUT, TFKB) cannot be scoped — sync the full current-master gap.

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
