---
name: master-data-sync
description: |
  Alinea MASTER DATA de P01 (fuente, read-only) hacia D01 / V01: cuentas GL, centros
  de coste, fondos, centros gestores, proyectos/WBS. Mide primero el hueco real leyendo
  EN VIVO los dos sistemas, y escribe SIEMPRE por la API ESTANDAR del objeto — nunca
  con INSERT plano en tablas estandar.
  Usalo cuando: se crea master data en P01 y hay que replicarla; se pregunta "esta D01/V01
  alineado?"; una prueba falla en dev porque falta una cuenta/fondo/centro; o hay que
  cuantificar la deriva entre sistemas.
  NO escribe nunca en P01. NO despliega ABAP. NO crea objetos nuevos de negocio: replica
  lo que ya existe en produccion.
  Ejemplos:
  - "Crearon 2 GL en P01, alinea D01 y V01"
  - "¿Cuanto ha derivado V01 respecto a P01 en cuentas?"
  - "Sincroniza los fondos del bienio a D01"
  - "Falta el centro de coste en dev para probar esto"
tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - TodoWrite
---

# master-data-sync — replicar master data de P01 a los no productivos

## ⛔ Las tres reglas que no se negocian

1. **P01 es FUENTE, jamás destino.** Ni un write, por ningún canal.
2. **API estándar, nunca INSERT plano.** `RFC_ABAP_INSTALL_AND_RUN` con `INSERT` solo es
   legítimo sobre **tablas propias `Y*`/`Z*`**. Sobre master data estándar está **prohibido**:
   salta derivación, rangos de numeración, validez, jerarquía y checks de consistencia, y deja
   un registro que parece bien en la tabla y está roto para el proceso.
3. **Verificar releyendo.** Un `BAPIRET2` sin errores no prueba que se escribió. La prueba es el
   readback campo a campo contra P01.

## Matriz de canales — MEDIDA en P01, no recordada

| Objeto | Lectura (P01) | Escritura (D01 / V01) |
|---|---|---|
| **Cuentas GL** | `GL_ACCT_MASTER_GET_COA_RFC` + `GL_ACCT_MASTER_GET_CCODE_RFC` | **`GL_ACCT_MASTER_SAVE_RFC`** |
| **Centros de coste** | `BAPI_COSTCENTER_GETDETAIL1` | `BAPI_COSTCENTER_CREATEMULTIPLE` / `_CHANGEMULTIPLE` |
| **Fondos** | `FM_FUND_GET_DETAIL_RFC` | `FM_FUND_CREATE_RFC` / `FM_FUND_CHANGE_RFC` |
| **Centros gestores** | `FM_FUNDS_CTR_GET_DETAILS_RFC` | `FM_FUNDS_CTR_CREATE_RFC` |
| **Proyectos / WBS** | `BAPI_PROJECTDEF_GETDETAIL` + `PRPS` | `BAPI_PROJECT_MAINTAIN` + `BAPI_TRANSACTION_COMMIT` |
| **Variantes de programa** | `RS_VARIANT_CONTENTS_RFC` | `RS_VARIANT_DELETE_RFC` + `RS_CREATE_VARIANT_RFC` (borrar y recrear; `RS_VARIANT_CHANGE_RFC` NO vale). ⚠️ fechas externo→interno |
| **Versión de balance (FSV)** | `RFC_READ_TABLE` | sin API — `OB58` + transporte, o **EXC-001** |
| **Tablas propias `YT*`** | `RFC_READ_TABLE` | `RFC_ABAP_INSTALL_AND_RUN` INSERT — único uso legítimo |

- **Centros de beneficio: NO se usan en UNESCO.** Fuera de alcance aunque el BAPI exista.
- **Elementos de coste:** `BAPI_COSTELEMENT_CREATEMULTIPLE` **no** está remote-enabled aquí.
  Resolver el canal antes de prometerlo.

**Si un skill dice "no hay canal", no le creas: pregúntale al sistema.**
`RFC_READ_TABLE` sobre `TFDIR WHERE FMODE = 'R' AND FUNCNAME LIKE '%<TEMA>%'`.
Así se recuperó `GL_ACCT_MASTER_SAVE_RFC`, que el skill daba por inexistente.

## ☠️ El flag de simulación es INVERSO entre APIs

| FM | Flag | Si lo omites |
|---|---|---|
| `FM_FUND_CREATE_RFC` / `_CHANGE_RFC` | `I_FLG_TESTRUN` (default **`'X'`**) | **simula en silencio**: 0 filas, mensajes vacíos, parece éxito |
| `GL_ACCT_MASTER_SAVE_RFC` | `TESTMODE` (default **vacío**) | **escribe de verdad** |

Pásalo **siempre explícito**, en los dos sentidos.

## Estructuras aplanadas: la trampa de las API `GL_ACCT_MASTER_*`

Sobre RFC estas API no exponen los campos planos de DDIC. Exponen **estructuras anidadas**:

```python
ACCOUNT_COA   = {"KEYY": {"KTOPL": "UNES", "SAKNR": "0004041018"},
                 "DATA": {...}, "INFO": {...}, "ACTION": "I"}
ACCOUNT_NAMES = [{"KEYY": {"KTOPL","SAKNR","SPRAS"}, "DATA": {"TXT20","TXT50"}, "ACTION": "I"}]
ACCOUNT_CCODE = {"KEYY": {"BUKRS": "UNES", "SAKNR": ...}, "DATA": {WAERS, XOPVW, FDLEV, ...}}
```

Pasar `{"KTOPL": ...}` plano da `RFC_INVALID_PARAMETER: field 'KTOPL' not found`.
Cuando la forma no sea obvia, **introspecciona**: `conn.get_function_description(FM)` y recorre
`parameter['type_description'].fields` recursivamente. `RFC_GET_FUNCTION_INTERFACE` da los tipos
DDIC pero **no** la forma aplanada que ve RFC.

**`ACTION` es obligatorio.** `'I'` = alta, `'U'` = modificación. Sin él, la API responde
`FH502 "Internal error: Import of table SKA1 not possible"` — que suena a fallo técnico y es solo
la acción vacía. `'U'` sobre una cuenta inexistente devuelve `FH058`, lo que confirma la semántica.

## Método

1. **Medir el hueco EN VIVO.** Nunca del Gold DB: su caché va meses por detrás y el propio skill
   lo prohíbe. `Zagentexecution/tasks/2026_08_20_mmf_gl_sync/gl_alignment_check.py` lo hace para
   GL sobre P01/D01/V01 y **fecha cada hueco con `ERDAT`**, que es lo que separa "deriva nueva" de
   "nunca llegó" y permite falsar un "esto estaba alineado a fecha X".
2. **Declarar el alcance por sociedad.** No es lo mismo el plan de cuentas (KTOPL) que la extensión
   a sociedad (BUKRS). Un hueco en SKB1 sin hueco en SKA1 es deriva de **extensión**, no de alta.
3. **Dry-run con el flag de test explícito** y leer los mensajes: los `W` suelen ser aceptables
   (moneda, visualización de partidas), los `E` no.
4. **Primero 1 registro**, readback campo a campo, y solo después el lote.
5. **Readback obligatorio** al final. Diferencias esperadas: solo la metadata de creación
   (`ERDAT`/`ERNAM`) — el destino sella la suya.
6. **Dependencias primero**: centros gestores antes que fondos; plan de cuentas antes que sociedad.

## Gotchas medidos
- `pyrfc` rechaza `'00000000'` en campos DATS: convertir a `''`.
- P01 rechaza `ROWSKIPS`: leer con `ROWCOUNT=0` y **particionar** (por `BUKRS`, `SPRAS`, `FIKRS`).
- `TABLE_WITHOUT_DATA` significa **cero filas**, no un fallo. Distinguirlo de "no pudimos ver".
- `BAPI_*` necesita `BAPI_TRANSACTION_COMMIT(WAIT='X')`; en error, `ROLLBACK`.
- Un objeto puede existir en el plan de cuentas y **no** estar extendido a la sociedad:
  `GET_CCODE` devuelve `NOT_EXISTING`. Es un dato, no un error.

## Artefactos
- Skill: `.agents/skills/sap_master_data_sync/SKILL.md` (matriz de canales, corregida s102)
- Método FM: `Zagentexecution/tasks/2026_06_29_fm_model_sync/METHOD.md`
- GL: `Zagentexecution/tasks/2026_08_20_mmf_gl_sync/gl_master_sync.py` + `gl_alignment_check.py`

## Al cerrar
Registrar en el skill lo aprendido: qué canal se usó, qué mensajes salieron, y **cualquier
afirmación del skill que resultara falsa** — es lo que más caro sale a la siguiente sesión.
