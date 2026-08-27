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

## ✍️ Y TAMBIÉN SE ESCRIBEN — alinear variantes entre sistemas

Probado 2026-08-21. Las variantes **no se transportan** (`VARID.TRANSPORT='F'`), así que divergen;
pero **sí se escriben por RFC**, con API estándar. Es peldaño 1: no hace falta excepción.

| Paso | FM | Nota |
|---|---|---|
| Leer | `RS_VARIANT_CONTENTS_RFC` | funciona también en P01 (`CCCOPYLOCK` no le afecta) |
| Borrar | `RS_VARIANT_DELETE_RFC` | `VARIANT` es **CHANGING**, `USE_EXCEPTIONS='X'` |
| Crear | `RS_CREATE_VARIANT_RFC` | `CURR_REPORT`, `CURR_VARIANT`, `VARI_DESC`, `VARI_CONTENTS`, `VARI_TEXT` |

**`RS_VARIANT_CHANGE_RFC` NO sirve** — su interfaz es `REPORT` + `VARIANT` + `VALUE_OR_ATTR`, sin
tabla de contenido: es de diálogo. Modificar una existente = **borrar y recrear**, que es
destructivo y exige snapshot PRE y verificación POST.

Herramienta: `Zagentexecution/tasks/2026_08_21_variant_alignment/variant_align.py`
(dry-run por defecto · `--targets` · `--variants ALL` · snapshot PRE a disco · restauración
automática si la creación falla · verificación POST releyendo).

### ☠️ Las dos trampas que rompen datos sin dar error

1. **Formato de fecha externo vs interno.** `RS_VARIANT_CONTENTS_RFC` devuelve `31.07.2026`;
   `RS_CREATE_VARIANT_RFC` espera `20260731`. Mandarlo tal cual **no falla: escribe basura**
   (`20.7..31.0`). Ocurrió en V01 sobre `P_BBUDAT`, `P_BLDAT`, `STICHTAG` y `ST_BUDAT` — que
   además **eran idénticos a P01** y quedaron rotos por copiarlos. Convertir siempre antes de crear.
2. **Lo que no se envía se rellena con defectos, en silencio.** Una variante creada con 2 líneas
   salió con 9 parámetros de pantalla a cero. Copiar solo la selección de cuentas **pierde el
   método de valoración, las fechas y los flags de modo**.

En ambos casos lo que salva es el diseño, no la suerte: **snapshot PRE en fichero y readback POST**.

### La divergencia NO es homogénea — clasificar antes de copiar
| Clase | Campos | Qué significa |
|---|---|---|
| **Selección** | `SKONTO`, `AKONTO` | qué objetos se procesan — el proceso |
| **Modo/config** | `PAR_BNAM` (sesión batch), `PA_WEREF`/`PA_WEREN`, `BWMET1`, `X_GL`, `X_SALBEW` | **cambia el comportamiento** |
| **Residuo** | `P_BBUPEM`/`P_SBUPEM`, fechas, `P_LVIEW`, handles de log | estado de la última corrida |

"Hazlas idénticas" no es una instrucción segura por defecto: puede borrar nombres de sesión batch y
voltear banderas de alcance. **Clasificar, presentar y dejar decidir.** En UNESCO la decisión fue
igualar todo lo que existe en P01 — para que en el futuro las variantes sí se puedan transportar.

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

## A quién le pasas el trabajo (s107)

| le pasas a | cuándo |
|---|---|
| `brain-steward` | cuando el contenido de una variante revela una **regla de negocio** que no está en ninguna configuración — es el caso que más se pierde, porque vive en un parámetro y no en un customizing |
| `fx-revaluation-scope` | cuando la variante que lees es de `RFBILA00`/`SAPF100`: él decide qué cuentas quedan dentro y fuera, tú sólo dices qué ejecuta la sociedad |
| `mining-arbiter` | cuando dos sistemas dan contenidos distintos para la misma variante y hay que decidir cuál es el bueno |


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
- Skill: `.agents/skills/sap_job_intelligence/SKILL.md` — **la otra mitad del par.** Tú lees la
  VARIANTE (qué se hace); ese skill lee el JOB (`TBTCO`/`TBTCP`: quién lo programó, cada cuánto,
  qué encadena, cómo falla). Mapear jobs de interfaz a sus variantes — que es tu tarea declarada
  para cerrar el modelo de rutas de ficheros — necesita las dos: una variante sin job no se
  ejecuta nunca, y un job sin variante no dice qué cubre. Conectado s106 (claim 622).
- Metodología: `knowledge/domains/Closing_Activities/sap_variant_forensic_methodology.md`
- Regla: `feedback_read_the_variant_the_variant_is_the_process` (CRITICAL)
