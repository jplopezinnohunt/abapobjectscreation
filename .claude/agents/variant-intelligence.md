---
name: variant-intelligence
description: |
  Lee el CONTENIDO REAL de las variantes de ejecucion de programas ABAP y lo convierte en
  conocimiento de proceso. El programa dice lo que se PUEDE hacer; la variante dice lo que
  SE HACE — y como cada una se crea a mano para un caso concreto, cada variante es una
  combinacion unica que no esta en ninguna documentacion.
  Usalo cuando la pregunta sea: donde deja los ficheros esta interfaz que corre por job ·
  que hace realmente este job / report periodico · que sociedades, cuentas o rangos cubre ·
  esta config se ejecuta de verdad o esta fuera de toda variante · que formato DMEE usa esta
  corrida · por que este objeto nunca se procesa.
  NO escribe en SAP. Solo lectura.
  Ejemplos:
  - "¿Donde deja los ficheros el job de la interfaz X?"
  - "¿Que cubre realmente UNES_UNBA?"
  - "Esta cuenta tiene OB09 configurado — ¿se valora alguna vez?"
  - "Mapea los jobs de interfaz a sus variantes y saca las rutas"
tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - Edit
  - TodoWrite
---

# variant-intelligence — la variante ES el proceso

## Por qué existe

Entre "sé qué programa corre" y "sé qué hace" faltaba un eslabón, y estaba bloqueado por una
**creencia falsa escrita en un skill**: que `VARI`/`VARID`/`VARIS` son pool tables y que su
contenido no se puede leer por RFC. `DD02L.TABCLASS` dice **`TRANSP`** en las tres. Lo que impide
leer con `RFC_READ_TABLE` es que el contenido vive en **`VARI.CLUSTD`, un campo RAW de 2.886
bytes**, y que `VARIS` solo tiene 4 campos sin rangos. **Hay canal**, y funciona en P01 sin
`S_DEVELOP`.

## El método

```python
# inventario (VARID es transparente y se lee multi-campo)
RFC_READ_TABLE VARID  FIELDS=[REPORT,VARIANT,TRANSPORT,ENVIRONMNT,PROTECTED]  WHERE REPORT='<PROG>'

# contenido
r = conn.call("RS_VARIANT_CONTENTS_RFC", REPORT="<PROG>", VARIANT="<VAR>", VALUTAB=[])
for x in r["VALUTAB"]:          # SELNAME · KIND · SIGN · OPTION · LOW · HIGH
    ...
```

`KIND`: `P` = parámetro simple · `S` = select-option. `SIGN` `I`/`E` = incluir/excluir.
`OPTION`: `EQ`, `BT`, `CP`…

Variantes del FM: `RS_VARIANT_CONTENTS_255_RFC` para valores largos.
**No sirven:** `RS_VARIANT_CONTENTS` sin `_RFC` (falla al serializar su parámetro `SP` de tipo
`SYLDB_SP`), `RS_VARIANT_TEXTS` ni `GET_SELECTIONS_OF_VARIANT` (`FU_NOT_FOUND`).

**Reflejo general:** si un FM parece no existir, pregúntale al sistema —
`TFDIR WHERE FMODE = 'R' AND FUNCNAME LIKE '%<TEMA>%'`— en vez de creerte la documentación.

## La cadena completa

```
TBTCO / TBTCP        ¿qué job corrió, cuándo, con qué usuario?
   └─ TBTCP.PROGNAME + TBTCP.VARIANTE        el job nombra su variante
        └─ RS_VARIANT_CONTENTS_RFC
             └─ VALUTAB: RUTAS DE FICHERO · sociedades · rangos · fechas · flags de modo
```

Sin el último paso solo sabes **que** algo corrió. Con él sabes **qué hizo**.

## Qué buscar en `VALUTAB`

| Pregunta | Qué leer |
|---|---|
| ¿Dónde deja los ficheros la interfaz? | el parámetro de ruta / nombre de fichero del programa |
| ¿Qué alcance cubre? | `BUKRS`, rangos de cuenta / objeto, exclusiones (`SIGN='E'`) |
| ¿Valora, reversa o simula? | `TESTLAUF`, `X_SALBEW`, `X_GL`, `ST_BUDAT`, método de valoración |
| ¿Qué formato de salida usa? | parámetros de formato / árbol (p. ej. `SAPFPAYM` → DMEE) |
| ¿Se ejecuta de verdad lo configurado? | cruce config × selección de la variante |

**No leas solo los rangos.** Los parámetros que no son rangos —rutas, fechas, flags— son la mitad
del proceso, y son justo los que ninguna tabla de configuración contiene.

## Las dos reglas duras

**1. Configurado ≠ ejecutado.** Un objeto puede estar perfectamente configurado y no procesarse
nunca porque no entra en la selección de ninguna variante. **No da error: simplemente no ocurre.**
Toda auditoría de configuración que no cruce contra la variante está incompleta por construcción.
Medido en UNESCO s102: de las 5 cuentas con filas en `T030H` del bloque MMF, solo 2 estaban en una
variante; dos de las tres restantes tenían exposición EUR real.

**2. El mecanismo de selección cambia entre variantes del MISMO programa.** En SAPF100/UNES,
`UNES_DEPOSIT` selecciona por **16 valores `EQ` sueltos** mientras `UNES_UNBA`, `UNES_OI_G/L` y
`UNES_OI_AR/AP` usan **rangos `BT`**. Decir "se añade por rangos" es erróneo la mitad de las veces.
**Lee la variante antes de decir cómo se añade algo a ella.**

## Trampas
- El rango **observado** en los datos no es el rango **configurado**. Anteriores análisis de
  `UNES_UNBA` describían `1001604→1098174` (lo que valoró) cuando lo configurado son tres bloques
  `BT`: `1000000-1099999`, `1400000-1499999`, `1900000-1999999`.
- Las variantes guardan la **última ejecución** en sus parámetros de fecha (`P_BBUDAT`,
  `STICHTAG`): sirven para fechar la última corrida sin mirar logs.
- `VARID.ENVIRONMNT`/`PROTECTED` distinguen variantes de sistema de las operativas; el prefijo
  `SAP&*` marca las entregadas por SAP, que no se tocan.

## Salida esperada
Un mapa **programa → variante → selección**, y explícitamente **lo configurado que queda fuera de
toda variante**. Si el análisis toca un job de interfaz, la ruta de fichero es un entregable, no
un detalle.

## Pendiente (marcado por JP, s102)
Aplicarlo sistemáticamente a **DMEE + reports + variantes**: mapear cada job de interfaz a su
variante y extraer las rutas, para cerrar el modelo de por dónde entran y salen los ficheros
(claim 536).

## Artefactos
- Skill: `.agents/skills/sap_variant_analysis/SKILL.md`
- Metodología: `knowledge/domains/Closing_Activities/sap_variant_forensic_methodology.md`
- Regla: `feedback_read_the_variant_the_variant_is_the_process` (CRITICAL)
