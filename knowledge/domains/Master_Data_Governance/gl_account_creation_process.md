# Alta de cuentas de mayor en UNESCO — el proceso, y lo que dispara cada tipo

**Dominio**: `Master_Data_Governance` (**cross-dominio**) · **Proceso**: `P2D` — *Prospect-to-Data (Master data)*
**Toca**: FI · Closing_Activities · Treasury · Payment · PS/PSM · Transport_Intelligence
**Nivel de evidencia**: TIER_1 — lectura en vivo de P01/D01/V01, s102 (2026-08-20/21)
**Caso de origen**: [INC-000016262](../../incidents/INC-MMF-BNPPB-2026_mmf_gl_creation_and_revaluation.md)
**Por qué existe este doc**: el conocimiento del proceso vivía **solo dentro de un incidente**. Un
incidente es un caso; esto es el proceso. El formulario `AM 3-11` aparecía 2 veces en todo el brain,
las dos en ese incidente.

---

## 1. La cadena, y quién hace qué

```
SOLICITANTE            FRA                MASTER DATA UNIT        ← y aquí acaba el proceso oficial
(Tesorería / MO)   →   valida        →    crea la cuenta (FS00)
formulario AM 3-11     el formulario      p.ej. MP_BOUA
                                              │
                                              ▼
                                     TAREAS POSTERIORES según el TIPO
                                     — sin dueño formal, y ahí se pierden
```

**El punto débil medido:** el proceso termina cuando la cuenta existe. Las tareas que la hacen
*funcionar* —revaluación, mapeo al balance, alineación de entornos— caen fuera y llegan por correo,
como una petición suelta a quien la reciba.

## 2. El formulario `AM 3-11` es la AUTORIDAD DE REGISTRO

No la nota de traslado. Medido en INC-000016262: el correo pedía revaluar **las dos** cuentas
nuevas; el formulario firmado de una de ellas marcaba **`GL to be revaluated = NO`** y apuntaba a
otra cuenta de referencia. Los datos dieron la razón al formulario.

| Campo | Para qué sirve de verdad |
|---|---|
| **`GL account to use as reference`** | la plantilla. **Cada cuenta puede apuntar a una distinta** — no asumir que dos cuentas del mismo correo comparten referencia |
| **`GL to be revaluated` YES/NO** | dispara toda la configuración FX. **Nadie lo lee**: se generalizó de memoria y se contradijo el formulario |
| **`Account group`** | decide el bloque de numeración y las tareas posteriores (§3) |
| **`Company Codes`** | ComboBox ActiveX; el valor vive en `xl/activeX/activeX1.bin`, no en una celda |
| **`Account Currency`** | **se deja en blanco a menudo** y lo rellena por criterio quien crea. En INC-000016262 acertó, pero eso es suerte, no proceso |

**Cómo leerlo sin abrir Excel:** el estado de las casillas está en `xl/ctrlProps/ctrlProp*.xml`
(`checked="Checked"`) y su posición en los anclajes del `<control>` de `xl/worksheets/sheet1.xml`.
El formulario arrastra **dos juegos de casillas superpuestos** (layout 2013 y 2017): si ambos
coinciden, la lectura es fiable.

## 3. ⭐ Qué dispara cada tipo de cuenta — la matriz que no existía

El grupo de cuenta y el bloque de numeración deciden el trabajo posterior. Rangos **medidos** en
`P01_SKA1` (chart UNES):

| Tipo | `KTOKS` | Rango real | Tareas posteriores |
|---|---|---|---|
| **Banco** | `BANK` | `1000131`–`1683713` | banco casa (`FI12`/`T012K`) · sub-cuenta de ajuste · `FBZP` · variante `UNES_UNBA` |
| **Conciliación AP/AR** | `OTHR`/`COLL` | `2xxxxxx` | OB09 con **cuenta de ajuste separada** (`2031000`→`2031800`) · variante `UNES_OI_AR/AP` |
| **Inversión / balance** | `OTHR` | `404xxxx` | posición de balance (FSV) · **OB09 auto-referencia** · variante `UNES_DEPOSIT` |
| **Resultado** | `P&L` | `6011101`–`7099999` | elemento de coste |

⚠️ **`404xxxx` NO es de bancos**, aunque aparezca junto a cuentas de banco en `T030H`. Es el bloque
de **inversiones y activo**: `4041xxx` depósitos y fondos monetarios · `4043xxx` ETF, bonos y
mandatos · `4044xxx` intereses devengados · `4054xxx` provisiones · `4060000`–`4068xxx` activo fijo.

⚠️ **Un banco con nombre conocido no es un banco casa.** Comprobarlo en `T012K`, no por el nombre:
el fondo BP2S Luxemburgo no tiene nada que ver con `BNP01`/`BNP02`, que son de Francia.

## 4. La revaluación FX: tres condiciones, no una

Una cuenta se revalúa **solo si se cumplen las tres**. Fallar en la tercera es el defecto silencioso
más caro de este dominio.

1. **Tiene exposición**: partidas abiertas (`BSIS`) en moneda ≠ `T001.WAERS` de la sociedad. La
   moneda de *transacción* de `GLT0` **no** sirve: dice en qué se movió algo, no que quede abierto.
2. **Está en `T030H`** (OB09) — dice **dónde** se postea la diferencia. Patrón por tipo:
   auto-referencia (`LKORR` = ella misma) para inversión y para la mayoría de bancos casa;
   main→sub para conciliación AP/AR.
3. **Está en el rango de selección de una variante de F.05** — decide **si** entra en el cálculo.

> **Configurar 2 sin 3 no da ningún error: la cuenta simplemente no se valora nunca.**
> Y ojo con el mecanismo: `UNES_DEPOSIT` selecciona por **valores sueltos `EQ`**, no por rangos.
> Añadir una cuenta ahí es una línea nueva, no ampliar un intervalo.

## 5. El alta dispara alineación en TRES sistemas, por CUATRO canales distintos

Crear la cuenta en P01 **no alinea nada más**. Cada pieza viaja por su propio camino:

| Pieza | Canal | ¿lo trae la copia de la cuenta? |
|---|---|---|
| Maestro (`SKA1`/`SKAT`/`SKB1`) | `GL_ACCT_MASTER_SAVE_RFC` | — es la copia |
| Posición de balance (FSV) | sin API → `OB58` + transporte, o excepción autorizada | **NO** |
| `T030H` / OB09 | **transporte** de customizing | **NO** |
| Variante de F.05 | `RS_CREATE_VARIANT_RFC` (no se transporta: `VARID.TRANSPORT='F'`) | **NO** |

Detalle: en la FSV los intervalos se definen por rango, así que **una cuenta nueva puede quedar
mapeada sola** si cae dentro de uno existente — pasó con `4041015–4041019`. Pero **un rango no cubre
nada si la fila del rango no existe en ese sistema**, y esa ausencia no se ve mirando la cuenta.

Ejecutores y método: [`knowledge/alignment_executors_model.md`](../../alignment_executors_model.md).

## 6. Checklist para el próximo alta

1. Leer el **formulario**, no la nota. Casilla por casilla, y **una referencia por cuenta**.
2. Verificar cómo quedó creada: `SKB1.WAERS`, `KTOKS`, `XOPVW`, `FDLEV`, `FIPOS` — contra su referencia.
3. Determinar el **tipo** (§3) y de ahí las tareas posteriores.
4. Si toca revaluación: las **tres** condiciones (§4), y la variante es la que se olvida.
5. Comprobar la **posición de balance**: puede estar ya cubierta por un intervalo.
6. Alinear D01/V01 por los **cuatro canales** (§5) — no basta con copiar la cuenta.
7. Verificar con: `ob09_vs_variant_check.py` · `fsv_alignment_check.py` · `gl_alignment_check.py`.

## 7. Lo que este dominio todavía no sabe
- **Quién es el dueño de las tareas posteriores.** Hoy llegan por correo a quien las reciba.
- Si el `AM 3-11` se archiva en algún sitio consultable, o vive solo en la cadena de correo.
- Si `FRA` valida el campo `GL to be revaluated`, o solo el alta.
