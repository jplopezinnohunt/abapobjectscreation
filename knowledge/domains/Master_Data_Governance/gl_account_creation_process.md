# Alta de cuentas de mayor en UNESCO — el proceso, y lo que dispara cada tipo

**Dominio**: `Master_Data_Governance` (**cross-dominio**) · **Proceso**: `P2D` — *Prospect-to-Data (Master data)*
**Toca**: FI · Closing_Activities · Treasury · Payment · PS/PSM · Transport_Intelligence
**Nivel de evidencia**: TIER_1 — lectura en vivo de P01/D01/V01, s102 (2026-08-20/21)
**Caso de origen**: [INC-000016262](../../incidents/INC-MMF-BNPPB-2026_mmf_gl_creation_and_revaluation.md)
**Por qué existe este doc**: el conocimiento del proceso vivía **solo dentro de un incidente**. Un
incidente es un caso; esto es el proceso. El formulario `AM 3-11` aparecía 2 veces en todo el brain,
las dos en ese incidente.

---

## 0. El REGISTRO de objetos de datos maestros

Este dominio no es una carpeta, es un **registro de tipos de objeto**. Cuando alguien pregunta
por gobierno de datos maestros, esto es lo que tiene que aparecer. Fuente estructurada y
consultable: [`brain_v2/master_data_registry.json`](../../../brain_v2/master_data_registry.json) ·
companion generado: `companions/master_data_governance.html`.

| Objeto | Tablas | Tx | Canal de escritura (MEDIDO en TFDIR de D01, 2026-08-21) | Estado |
|---|---|---|---|---|
| **Cuenta de mayor** | `SKA1 · SKB1 · SKAT` | FS00 | `GL_ACCT_MASTER_SAVE_RFC` | MECANIZADO |
| **Banco casa** | `T012 · T012K` | FI12 | `—` | canal medido, SIN ejecutor |
| **Centro de coste** | `CSKS · CSKT` | KS01 | `BAPI_COSTCENTER_CREATEMULTIPLE · _CHANGEMULTIPLE` | canal medido, SIN ejecutor |
| **Centro gestor (FM)** | `FMFCTR · FMFCTRT` | FMSA | `BAPI_0051_UPDATE` | canal medido, SIN ejecutor |
| **Clase de coste** | `CSKA · CSKB` | KA01 | `BAPI_COSTELEM_CREATEMULTIPLE · _CHANGEMULTIPLE` | canal medido, SIN ejecutor |
| **Fondo (FM)** | `FMFINCODE · FMFINT` | FM5I | `BAPI_0050_CREATE` | canal medido, SIN ejecutor |
| **Proveedor / interlocutor comercial** | `LFA1 · LFB1 · BUT000` | XK01 / BP | `BAPI_BUPA_CENTRAL_CHANGE y familia` | canal medido, SIN ejecutor |
| **Proyecto / elemento PEP** | `PROJ · PRPS` | CJ20N | `BAPI_BUS2001_CREATE (definicion) · BAPI_BUS2054_CREATE_MULTI (PEP) · BAPI_PROJECTDEF_CREATE` | canal medido, SIN ejecutor |
| **Posicion presupuestaria (FM)** | `FMCI · FMCIT` | FMCIA | `—` | SIN canal RFC |
| **Centro de beneficio** | `CEPC · CEPCT` | — | `BAPI_PROFITCENTER_CREATE (existe, pero no se usa)` | no aplica |

**Solo 1 de 10 está mecanizado de punta a punta.** Los otros 7 con canal medido tienen el FM
comprobado y nadie ha escrito el ejecutor — que es una brecha honesta, no una promesa.

**Dos creencias corregidas al medir:** las *clases de coste* se daban por SIN CANAL y sí lo tienen
(`BAPI_COSTELEM_CREATEMULTIPLE`); y los `BAPI_BANKDETAIL*` **no** sirven para el banco casa —
son datos bancarios de interlocutor. **Centros de beneficio: UNESCO no los usa.**

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

### La asimetría que causa la desalineación

El maestro y su configuración **viajan en sentidos opuestos**, y por eso nadie los ve como un
solo proceso:

```
MAESTRO (SKA1/SKB1/SKAT)      P01 ──▶ D01 · V01     nace en PRODUCCIÓN, se rellena hacia atrás
CONFIG  (OB09 · variante ·    D01 ──▶ V01 ──▶ P01   nace en DESARROLLO, sube por transporte
         FSV · intervalos)
```

El usuario crea la cuenta **directamente en P01** y solo nos avisa **cuando hace falta revaluar**.
Las altas que no la llevan no generan aviso: nadie sabe que existen hasta que algo falla en dev.
Eso no es un olvido puntual, es la mecánica del proceso — y se mide.

| Sistema | Cuentas de P01 que faltaban (medido 2026-08-20) |
|---|---|
| D01 | 2 |
| V01 | **33** |

Las 33 son el sedimento de todas las altas sobre las que nunca hubo correo. **Corolario: el paso 0
no puede ser una notificación, tiene que ser un barrido programado.**

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

## 6. ⭐ EL PROCESO OPERATIVO — 7 pasos, cada uno con su instrumento

Propuesto por JP como 3 pasos (alinear → configurar revaluación → controlar variante) y revisado
con lo medido en s102: le faltaba un paso **antes** (nadie dispara el proceso) y dos **después**
(el balance y el transporte). Los pasos 2 y 3 de la propuesta original son **un solo gate**.

| # | Paso | Por qué | Instrumento |
|---|---|---|---|
| **0** | **DETECTAR la deriva** | El aviso solo llega si hay revaluación; las demás altas son invisibles. 33 cuentas de retraso en V01 | `gl_alignment_check.py` — **programado**, no bajo demanda |
| **1** | **ALINEAR maestro P01 → D01/V01** | La cuenta debe existir donde se prueba, o la config no se puede probar | `gl_master_sync.py` (API estándar `GL_ACCT_MASTER_SAVE_RFC`) |
| **2** | **DECIDIR si revalúa** | El tipo NO decide esto | las 3 condiciones de §4, leídas del `AM 3-11` + `SKB1.WAERS` vs `T001.WAERS` + exposición viva |
| **3** | **CONFIGURAR el gate completo: OB09 *y* variante** | Son inseparables: OB09 solo = no corre y no avisa; variante sola = F.05 falla | `ob09_vs_variant_check.py` (cruza `T030H` × variante × exposición) |
| **4** | **COMPROBAR cobertura en el balance** | Se asigna por INTERVALO: entra sola o cae en *Not assigned*, y el balance cuadra igual | `fsv_coverage_check.py <cuenta>` |
| **5** | **TRANSPORTAR con control de alcance** | Un transporte de tabla guarda la CLAVE y exporta el VALOR al liberar: arrastra vecinos | `config_transport_prerelease_check.py <TRKORR>` |
| **6** | **BARRER la población** | La ocasión es el ticket; el alcance es todo | `--sweep` de los pasos 3 y 4 |

**El tipo de cuenta entra en el paso 3, no en el 2.** Inversión, banco u otra determinan el
*método* de valoración y las *cuentas de contrapartida* de `T030H` — no si hay que valorar.

**Prueba de que el paso 2 no es el tipo:** `4041018` y `4041019` son ambas de inversión, dadas de
alta el mismo día, con el mismo formulario. La 18 revalúa y la 19 no — porque la 19 está en USD
sobre una sociedad en USD. Mismo tipo, decisión opuesta.

**Prueba de que el paso 6 hace falta:** el barrido de la población encontró `4041011` — 10 M EUR
netos abiertos, `T030H` configurado, **en ninguna variante de F.05**. Nadie la había pedido.

### Antes de empezar, sobre el papel
1. Leer el **formulario**, no la nota. Casilla por casilla, y **una referencia por cuenta**.
2. Verificar cómo quedó creada: `SKB1.WAERS`, `KTOKS`, `XOPVW`, `FDLEV`, `FIPOS` — contra su referencia.

## 7. Lo que este dominio todavía no sabe
- **Quién es el dueño de las tareas posteriores.** Hoy llegan por correo a quien las reciba.
- Si el `AM 3-11` se archiva en algún sitio consultable, o vive solo en la cadena de correo.
- Si `FRA` valida el campo `GL to be revaluated`, o solo el alta.
