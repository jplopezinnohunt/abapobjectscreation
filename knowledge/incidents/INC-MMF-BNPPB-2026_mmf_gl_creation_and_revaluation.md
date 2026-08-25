# INC-000016262 — Alta de 2 GL de fondo monetario BNP PB y su tratamiento de revaluación

> **Número de ticket real: `INC-000016262`**, recuperado el 2026-08-20 del texto del transporte
> `D01K9B0FXP` ("INC-000016262 New Account MMF investments Revaluation") — el correo no lo traía,
> por eso este doc nació con el id provisional `INC-MMF-BNPPB-2026`, que se conserva como alias
> para no romper los enlaces del brain.

**Status** (~~2026-08-20~~ **RETIRADO 2026-08-26**, se conserva por trazabilidad): ~~ANALIZADO — decisión tomada con evidencia live. **PENDIENTE de ejecución**: (1) OB09/T030H + variante `UNES_DEPOSIT` para 4041018 · (2) sync P01→D01/V01 (script escrito, bloqueado por permisos) · (3) respuesta a Jeannette sobre 4041019~~
**Status 2026-08-26**: ANALIZADO — decisión tomada con evidencia live. ⚠️ **El transporte `D01K9B0FXP` figura LIBERADO e importado a 2026-08-25**, así que la acción (1) ya no se puede ejecutar como estaba escrita («corregir `LKORR` en D01 antes de liberar»): **no está medido qué `LKORR` tiene hoy `T030H` en P01 para `0004041018` — se desconoce**. PENDIENTE: (1) re-leer `T030H` en P01 y, si llegó el valor malo, corregir por **transporte nuevo** · (2) variante `UNES_DEPOSIT` en D01/V01 (H113) · (3) respuesta a Jeannette sobre 4041019 · (4) re-medir el alcance del transporte sobre la **orden padre** con `--entity-field HKONT`
**Type**: Track B — acción operativa (el qué se sabe; hacerlo bien es el trabajo)
**Date opened**: 2026-07-27 · **Analizado**: 2026-08-20 (s102)
**Requester**: Thavry ENG (FIN/Treasury, Middle Office) → Jeannette La (BFM-TRS) → Pablo
**Ejecutado en P01 por**: MP_BOUA (Master Data), 2026-07-27 — el agente nunca escribe P01
**Verificado por**: agente, lectura live `RFC_READ_TABLE` sobre P01 / D01 / V01
**System**: P01 (fuente) · D01 + V01 (destinos) · **Entidad**: UNES · **Chart**: UNES
**Dominio**: Closing Activities (revaluación FX) + FI (GL master data)
**Docs relacionados**: [fx_revaluation_process.md](../domains/Closing_Activities/fx_revaluation_process.md)
**Precedente exacto**: JP_LOPEZ sincronizó 4041015/16/17 de P01 a D01 el 2026-04-03 (skill `sap_master_data_sync`, 880 registros, gap 0)
**Incidente hermano**: [INC-FXREVAL-OB09](../domains/Closing_Activities/fx_revaluation_process.md) — mismo dominio, el otro patrón de revaluación

---

## 0. Estado de ejecución

| # | Acción | Estado |
|---|---|---|
| 1 | Crear 4041018 + 4041019 en UNES/P01 | ✅ **HECHO** por MP_BOUA 2026-07-27 — y **bien**: la EUR quedó con `WAERS=EUR` |
| 2 | **Variante `UNES_DEPOSIT` en P01** | ✅ **HECHO 2026-08-20** — verificado: 17 entradas `EQ`, `4041018` dentro |
| 3 | OB09/T030H en **D01**, para transportar | ⚠️ **HECHO CON DEFECTO** — `LKORR=0004041017` en CURTP 10 y 30; debe ser `0004041018`. **Medición válida (nota 2026-08-26)**: se leyó el valor a los dos lados, no la produjo el clasificador. Pero la remediación cambió — ver «El transporte» |
| 4 | OB09/T030H en **P01** | ⏳ se cierra **al liberar el transporte `D01K9B0FXP`**, no a mano — ⚠️ **enmendado 2026-08-26**: `D01K9B0FXP` es una **TAREA** (la orden padre no la ha barrido nadie) y a 2026-08-25 figura **ya liberado e importado**; ver «El transporte» |
| 5 | Revaluación de 4041019 | ⛔ **NO PROCEDE** — formulario `NO`, referencia 4041016 sin T030H, y es USD en sociedad USD |
| 6 | Sync de cuentas P01 → D01 / V01 | ✅ **HECHO 2026-08-20** — 2 en D01 y 33 en V01, readback campo a campo OK |
| 7 | Variante en D01 y V01 | ❌ **PENDIENTE** — siguen sin `4041018`; no se transportan (`VARID.TRANSPORT='F'`). Ver H113 |

### El transporte — `D01K9B0FXP`
~~`TRFUNCTION=Q` (customizing) · `TRSTATUS=D` (modificable, **sin liberar**)~~ **RETIRADO 2026-08-26**
(clasificación y estado caducados — ver la enmienda inmediatamente debajo) · JP_LOPEZ 2026-08-20 ·
texto *"INC-000016262 New Account MMF investments Revaluation"*.

> **Enmienda 2026-08-26 — qué es y en qué estado está.** `D01K9B0FXP` es `TRFUNCTION=Q` = **TAREA**,
> no orden. Lo analizado fue la tarea; lo que se libera es su **ORDEN padre**
> (`E070 WHERE STRKORR='D01K9B0FXP'`), que **nadie ha barrido** — si lleva otras tareas, de otro
> usuario o de otro tema, sus claves viajan junto al OB09 sin que nadie las haya visto.
> **Estado a 2026-08-25: ya está LIBERADO e importado (`TRSTATUS='R'`)** — medido en la corrida
> registrada en `brain_v2/methods/algorithms.json:1310`. La línea «`TRSTATUS=D` modificable, sin
> liberar» es del 2026-08-20 y está caducada.
> **Sobrevive** el hecho de fondo: OB09/`T030H` llega a P01 **por transporte**, no a mano — se leyó
> de `E070`/`E07T`, no del clasificador defectuoso.

~~`config_transport_prerelease_check.py`: **2 VIAJA · 0 INTRUSA · 0 NO-OP · 2 DERIVA**. Alcance limpio,
sin claves ajenas.~~ **RETIRADO 2026-08-26** — motivo: «alcance limpio, sin claves ajenas» era FALSO
**POR VACUIDAD** (se conserva el texto para que se pueda leer qué se creyó y por qué).

`config_transport_prerelease_check.py` sobre la **tarea** `D01K9B0FXP`: **2 VIAJA · 2 DERIVA**.
⚠️ **El alcance NO está verificado: se desconoce si el transporte lleva claves ajenas.** El
`0 INTRUSA` es vacío, no medido — en `T030H` el check deriva la entidad como el 1er campo clave tras
`MANDT` (= `KTOPL`), y en D01 sólo existe `UNES`, así que la condición INTRUSA
(`Zagentexecution/quality_checks/config_transport_prerelease_check.py:210`) no puede cumplirse nunca;
el discriminador real, `HKONT`, no se mira. Una cuenta ajena habría salido `[VIAJA]` y el resumen
habría impreso igualmente «OK — ninguna clave ajena». Además se corrió sobre la TAREA; la ORDEN
padre, que es lo que se libera, no la ha mirado nadie. **Pendiente de re-medir** resolviendo
`E070 WHERE STRKORR` y con `--entity-field HKONT`.

Pero el valor que exporta lleva `LKORR=0004041017`.

> ~~**La mecánica que salva esto:** un transporte de tabla guarda la **CLAVE** y exporta el **VALOR al
> LIBERAR**. Corregir `LKORR` en D01 **antes** de liberar hace que el transporte lleve ya lo correcto
> — no hay que tocarlo, borrarlo ni rehacerlo.~~ **RETIRADO 2026-08-26** — la mecánica sigue siendo
> cierta, pero la ventana que explotaba ya está cerrada.

> **Enmienda 2026-08-26 — la ventana «corregir antes de liberar» ya no está abierta.**
> A 2026-08-25 `D01K9B0FXP` figura **liberado e importado** (`brain_v2/methods/algorithms.json:1310`).
> **No está medido qué `LKORR` tiene hoy `T030H` en P01 para `0004041018`** — se desconoce hasta
> releer `T030H WHERE KTOPL='UNES' AND HKONT='0004041018'` en P01 (CURTP 10 y 30). Si llegó el valor
> malo, la corrección ya **no** es un cambio en D01 antes de liberar sino un **transporte nuevo**.
> Lo que **sí sobrevive** es la medición: «`LKORR=0004041017` en CURTP 10 y 30; debe ser
> `0004041018`» se obtuvo imprimiendo el **valor** de cada clave leído de la tabla entera en los dos
> sistemas, ruta independiente de los defectos del clasificador (lo vio un humano leyendo la línea,
> no el check — `algorithms.json:1306`).

Las 2 `[DERIVA]`: `0001122421` y `0001122424` tienen fila en P01 y no en D01. Preexistente, este
transporte no la corrige.

> **Nota 2026-08-26 — esto SOBREVIVE a los defectos del check, no volver a abrirlo.** `DERIVA` se
> calcula (`config_transport_prerelease_check.py:223-224`) como las claves **fuera** del transporte
> con valor distinto entre sistemas, leyendo las **dos tablas enteras**: esa ruta no pasa por
> `main_ents` ni por `idx`, así que el eje de entidad colapsado (defecto B) no la toca, y no depende
> de si el `TRKORR` es orden o tarea (defecto A tampoco la toca). El único acoplamiento teórico
> sería un troceo malo del `TABKEY` (defecto C), descartado aquí: las 2 claves del transporte
> **casaron** contra la tabla y se imprimió su valor a los dos lados. Confirmación independiente:
> `.agents/intelligence/PMO_BRAIN.md:28` (H114) reporta las mismas `0001122421` / `0001122424` con
> fila en P01 y no en D01.

---

## 1. La petición, y dónde se tuerce

Cadena: Thavry ENG adjunta 2 formularios **AM 3-11** ("estas dos cuentas van bajo cash and cash
equivalent") → Jeannette pide el alta a MP_BOUA → MP_BOUA crea → Jeannette escribe a Pablo:

> *"2 new GL's have been created in UNES. **Theses GLs have to be revaluated.** Could you please
> take action knowing that these GLs are **similar to GL 4041017** already revaluated."*

**La nota contradice a los formularios.** Leído el estado real de las casillas dentro del XLSX
(`xl/ctrlProps/*.xml` + anclajes de celda), no su apariencia:

| Campo | 4041018 EUR MMF BNP PB | 4041019 USD MMF BNP PB |
|---|---|---|
| Acción | CREATE GL | CREATE GL |
| Grupo de cuenta | Other balance sheet a/c | Other balance sheet a/c |
| GL de referencia | **4041017** | **4041016** ← no 4041017 |
| **GL to be revaluated** | **YES** | **NO** |

Doble confirmación: el formulario arrastra dos juegos de casillas superpuestos (layout 2013 y
2017) y **ambos coinciden en cada campo**.

Regla Track B B1: *la autoridad de registro es el formulario firmado, no la nota del solicitante.*
Jeannette generalizó "similar a 4041017" a las dos cuentas; el formulario de la USD apunta a 4041016.

## 2. Precedente

`sap_master_data_sync`, sesión 2026-04-03: JP_LOPEZ copió **4041015 / 4041016 / 4041017** de P01 a
D01 (`D01_SKA1.ERDAT=20260403`, `ERNAM=JP_LOPEZ`, frente a `P01_SKA1.ERDAT=20240927`,
`ERNAM=MP_BOUA`). Mismo rango de cuentas, misma operación. Gap final 0.

## 3. Mecanismo de selección del objetivo — qué tipo de cuenta es esto

**BNP Paribas aquí NO es banco casa.** Medido en P01:

- `T012` de UNES tiene **BNP01 y BNP02, ambos `BANKS='FR'`**. El fondo es **BP2S LUX / BNP Paribas
  Insticash**, Luxemburgo — IBAN `LU46 3280791019TFN978` (EUR) y `LU86 3280791019TFN840` (USD).
  Es el custodio del fondo, no el banco operativo francés.
- De los **350 GL de banco casa** de UNES en `T012K`, **ninguno es 4041xxx**.
- `SKB1.HBKID` y `HKTID` vacíos en las 9 cuentas 40410xx.
- El formulario deja House bank ID / Bank account ID en blanco y marca *Other balance sheet a/c*.

⇒ **Cuenta de inversión (fondo monetario) bajo cash equivalents, no cuenta bancaria operativa.**
⇒ **No aplica el checklist de house bank** (FI12 / T012K / FBZP / sub-cuenta de ajuste).

### El tipo de cuenta decide el patrón de revaluación

Cruce de los 944 HKONT de `T030H` (KTOPL=UNES, CURTP 10) contra `T012K` y `KTOKS`:

| Tipo de cuenta | Cómo se identifica | Patrón `T030H` | Variante F.05 |
|---|---|---|---|
| Banco casa operativo | en `T012K` / `HBKID` lleno, `KTOKS=BANK` | auto-reval **251** · main→sub **8** | `UNES_UNBA` |
| Conciliación AP/AR (2xxxxxx) | `OTHR`/`COLL`, sin HBKID | main → cuenta de ajuste (**130 + 43**) | fuera de ambas |
| **Inversión / balance no-banco (4041xxx)** | sin HBKID, no en `T012K`, `KTOKS=OTHR` | **auto-revaluación** (`LKORR` = ella misma) | **`UNES_DEPOSIT`** |

> **Corrección al modelo existente.** `fx_revaluation_process.md` §4 presenta main→sub como *el*
> patrón bancario. Medido: eso solo se cumple en **8 de 259** filas de banco casa — precisamente los
> pares Banco de Chile / Ecobank del `INC-FXREVAL-OB09`. El patrón dominante de banco casa también
> es auto-revaluación. Quien realmente usa main→sub es la **conciliación AP/AR**. Extiende el
> claim #205, que registraba 2 patrones donde hay 3.

## 4. Lectura previa en vivo (P01 / D01 / V01, read-only)

Sonda: `scratchpad/mmf_launch/probe_mmf_live.py`. `ROWCOUNT=0` sin `ROWSKIPS` (el wrapper de P01
los rechaza), `WHERE` por cuenta.

| Cuenta | Texto | WAERS | HBKID | ¿banco casa? | `T030H` | Patrón |
|---|---|---|---|---|---|---|
| 4041011 | Term Deposits Principal | USD | — | no | 2 filas | auto-reval |
| 4041012 | Term Accounts Principal Current | USD | — | no | 2 filas | auto-reval |
| 4041013 | Short Term Deposits Principal | USD | — | no | 2 filas | auto-reval |
| 4041014 | MMF USD JPMorgan | USD | — | no | 2 filas | auto-reval ⚠️ |
| 4041015 | MMF USD ASHI JPMorgan | USD | — | no | 0 | sin config |
| 4041016 | MMF USD BlackRock | USD | — | no | 0 | sin config |
| **4041017** | **MMF EUR BlackRock** | **EUR** | — | no | **2 filas** | **auto-reval** |
| **4041018** | **MMF EUR BNP PB** | **EUR** | — | no | **0** | **falta** |
| **4041019** | **MMF USD BNP PB** | **USD** | — | no | 0 | correcto |

- `T001.WAERS` de UNES = **USD**. Una cuenta USD en sociedad USD **no tiene nada que revaluar**.
- **4041018 vs su referencia 4041017: idénticas en todos los campos funcionales de SKB1.**
  MP_BOUA la creó con `WAERS=EUR` **pese a que el formulario dejó *Account Currency* en blanco** —
  es decir, acertó por criterio, no por especificación. Eso es suerte, no proceso.
- **4041019 vs su referencia 4041016: idénticas.** Y 4041016 no tiene `T030H`. Coherente.
- `GLT0` confirma la exposición: 4041017 mueve **solo EUR** (402,7 M EUR en 2025);
  4041014/15/16 mueven **solo USD**.

### Gap contra los no productivos
| | faltan |
|---|---|
| P01 → **D01** | 2 — `4041018`, `4041019` |
| P01 → **V01** | 4 — `4041015`, `4041016`, `4041018`, `4041019` |

V01 está **más atrasado**: le faltan además las dos de 2024 que sí llegaron a D01 en abril.

## 5. Especificación del cambio

### 4041018 (EUR) — SÍ se revalúa. Plantilla = 4041017, leída en vivo:

| # | Qué | Valor |
|---|---|---|
| 1 | `SKB1.WAERS` | **EUR** — ✅ ya correcto, verificado |
| 2 | OB09/T030H `CURTP 10` | `LKORR=0004041018` · `LSREA=LSBEW=0006045011` · `LHREA=LHBEW=0007045011` |
| 3 | OB09/T030H `CURTP 30` | `LKORR=0004041018` · los cuatro campos `=0005022012` |
| 4 | Variante F.05 **`UNES_DEPOSIT`** | añadir 4041018 como **valor EQ suelto** en `SKONTO` |

**El paso 4 es el que se olvida.** `T030H` dice *dónde* postear la diferencia; la **variante**
decide *si* la cuenta entra en el cálculo. Configurar solo OB09 produce una revaluación que **nunca
corre, en silencio** — el mismo modo de fallo que dejó a ICTP sin valorar julio y noviembre de 2025.

### Cómo selecciona cada variante — leído en vivo, no supuesto

`RS_VARIANT_CONTENTS_RFC` (remote-enabled) sobre P01, las 4 variantes de UNES:

| Variante | Método | Selección `SKONTO` | Modo |
|---|---|---|---|
| **`UNES_DEPOSIT`** | `BWMET1=UNOI`, `X_GL=X` | **16 valores EQ sueltos**: 2021053 · **4041013** · **4041017** · 4043011/12/13/14/25/26 · 5091010/14/15/16/19/20/23 | reversión 01.08.2026 → **Modo A** |
| `UNES_OI_G/L` | `BWMET1=UNOI`, `X_GL=X` | `BT` 1100000–1199999 · 1500000–1599999 · 1700000–1799999, menos 3 exclusiones | reversión → Modo A |
| `UNES_OI_AR/AP` | `BWMET1=UNOI`, AR+AP+GL | `BT` 2031000–2031999 · 2100000–2100999 + sueltos, con exclusiones | reversión → Modo A |
| `UNES_UNBA` | `X_SALBEW=X` | `BT` 1000000–1099999 · 1400000–1499999 · 1900000–1999999 | `ST_BUDAT=00.00.0000` → **Modo B, sin reversión** |

**`UNES_DEPOSIT` no trabaja por rangos: es una lista de valores sueltos.** Ningún rango va a absorber
4041018 — hay que añadir la línea. Las otras tres sí usan `BT`, y los tres bloques de `UNES_UNBA`
(1xxxxxx, 14xxxxx, 19xxxxx) no alcanzan a 404xxxx bajo ninguna circunstancia.

**4041018 no está en NINGUNA de las cuatro.** Verificado una por una.

### 4041019 (USD) — NO se revalúa
Formulario `GL to be revaluated = NO`; referencia declarada 4041016; 4041016 sin `T030H`; la cuenta
solo puede mover USD en una sociedad USD. **Devolver por escrito a Jeannette con la evidencia antes
de ejecutar nada.**

### Sync P01 → D01 / V01
`Zagentexecution/tasks/2026_08_20_mmf_gl_sync/mmf_gl_sync.py` — parametrizado `--systems` y
`--accounts`, dry-run por defecto. SKA1 (18 campos, 125 b), SKAT (7, 113 b), SKB1 (42, 223 b): los
tres caben enteros en el buffer de 512 b, no hace falta field-split. INSERT vía
`RFC_ABAP_INSTALL_AND_RUN`, lote de 1 primero y verificación campo a campo, según el patrón probado.

## 6. Ejecución
Pendiente. El agente **no escribe P01**. D01/V01 los escribe el script anterior, hoy **bloqueado por
el clasificador de permisos** incluso en dry-run.

## 7. Lectura posterior
Pendiente: readback campo a campo contra P01, esperando divergencia **solo** en `ERDAT`/`ERNAM`
(el destino sella su propia creación).

## 8. Barrido de la población (B8) — el ticket es la ocasión, no el alcance

1. **🔴 Tres cuentas con `T030H` que no están en ninguna variante — la clase de defecto, viva.**
   De las 5 cuentas 40410xx con filas en `T030H`, solo **4041013 y 4041017** aparecen en
   `UNES_DEPOSIT`. Las otras tres están configuradas y **nunca se valoran**:

   | Cuenta | `T030H` | ¿en alguna variante? | Exposición en `GLT0` | Lectura |
   |---|---|---|---|---|
   | `4041011` Term Deposits Principal | sí | **no** | **EUR en 2023, 2024 y 2025** | 🔴 candidato real |
   | `4041012` Term Accounts Principal Current | sí | **no** | EUR en 2023 y 2024 | 🟠 candidato |
   | `4041014` MMF USD JPMorgan | sí | **no** | solo USD | 🟢 inocuo (sin exposición) |

   **No lo declaro defecto todavía**: puede que Treasury las dejara fuera a propósito. Es una
   pregunta para ellos, no una conclusión. Lo que sí es un hecho es que hoy la config de OB09 de
   esas tres no se ejecuta. `glt0_p01` llega hasta 2025, así que el estado 2026 no está medido.
2. **`4041014` no es una cuenta de banco, y el bloque 404xxxx tampoco.** Rangos reales por grupo
   de cuenta en UNES: **BANK 1000131–1683713** (918 cuentas), OTHR 1000991–9999999 (995),
   COLL 2011011–4049011 (59), P&L 6011101–7099999 (491). El bloque 404 es **inversiones y activos**:
   4041xxx depósitos y fondos monetarios · 4043xxx ETF, bonos, letras y mandatos · 4044xxx intereses
   devengados · 4045011 fondo de renovación · 4049011 conciliación BP (única COLL) · 4054xxx
   provisiones · 4060000–4068xxx activo fijo. Las 9 cuentas 40410xx son `KTOKS=OTHR`, ninguna `BANK`.
   Lo que hacía parecer bancaria a 4041014 era encontrarla en `T030H` junto a cuentas de banco.
3. **V01 lleva 2 cuentas de deriva** (4041015, 4041016) desde 2024, que sí llegaron a D01.
4. **`UNES_DEPOSIT` contiene mucho más que 4041xxx**: de sus 16 cuentas solo 2 lo son. El resto son
   4043xxx (ETF y bonos), 5091xxx y una 2021053. La descripción del brain era incompleta — ver §10.

## 9. Cierre y promoción

### Claims a promover
1. **Regla MMF: EUR se revalúa, USD no** — evidencia en las 9 cuentas (`T030H` + `GLT0` + `T001.WAERS=USD`). TIER_1.
2. **Taxonomía de 3 patrones de revaluación por tipo de cuenta** (§3) — extiende y corrige el claim #205. TIER_1.
3. **Clase de defecto: "OB09 configurado pero fuera del rango de variante"** = revaluación silenciosamente no ejecutada.
4. **`T030H` con exposición nula** (4041014) — configuración sin efecto.
5. **`gold_refresh.py` procesa solo specs `curated`** — ver §10. TIER_1.

### Candidato a check mecanizado
El formulario AM 3-11 lleva el campo *GL to be revaluated* y **nadie lo lee**: Jeannette lo
generalizó de memoria y contradijo el formulario firmado; MP_BOUA acertó la moneda que el formulario
dejó en blanco. Check propuesto: formulario → `SKB1.WAERS` → `T030H` → rango de variante.
Segundo avistamiento del patrón ⇒ toca gate (regla #172).

## 10. Lo que NO se puede ver, y no es "no hay nada"

- **`gold_refresh.py` no refrescó nada y devolvió exit 0.** Corrido hoy para `FI master_data`,
  `FI text` y `Config config`: imprimió "DONE." con el sync log **vacío**. Causa: filtra
  `curated = [s for s in specs if s.get("source") == "curated"]` y después `if not curated: continue`
  **sin imprimir nada**. Solo 28 de las 318 entradas del registro son `curated`; las de FI y Config
  son `auto`, sin `sap`/`key`/`fields`, así que se saltan en silencio. `_gold_sync_log` sigue con su
  última fila del **2026-06-30**. Es exactamente la regla #180: *un no-op silencioso es un defecto
  silencioso*. **Arreglo mínimo: imprimir lo que se salta y por qué.** Mientras tanto, el Gold DB
  **sigue sin las cuentas nuevas** y cualquier análisis de gap debe leer LIVE.
- ✅ **`KU-2026-070-02` CERRADO — el contenido de las variantes SÍ es auditable por RFC.** Lo que era
  cierto: `sapf100_vari`/`sapf100_varid` están vacías en el Gold DB; `VARI` guarda el contenido en
  **`CLUSTD`, tipo X de 2.886 bytes** (cluster binario que `RFC_READ_TABLE` no devuelve) y `VARIS`
  solo tiene 4 campos, sin rangos. Lo que era falso: que por eso no se pudiera leer.
  **`RS_VARIANT_CONTENTS_RFC` está remote-enabled** (`TFDIR.FMODE='R'`) y devuelve `VALUTAB` con
  `SELNAME/KIND/SIGN/OPTION/LOW/HIGH`. Preguntado al sistema, no supuesto: `TFDIR WHERE FMODE='R'`.
  `RS_VARIANT_CONTENTS` (sin `_RFC`) falla al serializar su parámetro `SP` de tipo `SYLDB_SP`;
  `RS_VARIANT_TEXTS` y `GET_SELECTIONS_OF_VARIANT` devuelven `FU_NOT_FOUND`.
  **Consecuencia: el cruce `T030H` × variante ya es mecanizable.**
- ✅ **`KU-CA-002` CERRADO** — `UNES_UNBA` lleva `X_SALBEW='X'` y `ST_BUDAT=00.00.0000`: valoración de
  saldos sin reversión = **Modo B intencionado**, no un defecto. Confirmado leyendo la variante.
- ⚠️ **Corrección a `fx_revaluation_process.md` §5**, que decía que `UNES_DEPOSIT` "cubre solo cuentas
  4041xxx OTHR (EUR, 1 activa = 0004041017)". De sus **16** cuentas solo **2** son 4041xxx (4041013 y
  4041017); el resto son 4043xxx, 5091xxx y una 2021053. Y decía que `UNES_UNBA` cubre
  "0001001604 → 0001098174": ese era el rango **observado** en las 82 cuentas que valoró, no el
  **configurado**, que son tres bloques `BT` (1000000–1099999, 1400000–1499999, 1900000–1999999).
- **No legible por RFC**: `T077S` devuelve `TABLE_WITHOUT_DATA`, así que los rangos de numeración
  **configurados** por grupo de cuenta no se han leído. Los de §8 son los rangos **observados** en
  los datos, que no es lo mismo.
- **No verificado**: si MP_BOUA usó transporte para el alta en P01. Y `glt0_p01` llega hasta 2025:
  el estado de saldos 2026 de 4041011/4041012 no está medido.


## Instrumento nacido de este incidente (s102, 2026-08-21)

`Zagentexecution/quality_checks/fsv_coverage_check.py` — responde la pregunta que aqui se contesto a mano: **¿la cuenta nueva cae en alguna posicion del balance?** Deriva de las variantes de `RFBILA00` que version se EJECUTA para la sociedad (`BILAVERS` + `SD_BUKRS`), descarta las que no tienen intervalos para el plan, y con `--ref <cuenta>` distingue una version SELECTIVA de un hueco real.

```bash
python Zagentexecution/quality_checks/fsv_coverage_check.py 4041018 4041019 --ref 4041016
```

Resultado 2026-08-21: **FS10, 0 de 2 sin posicion** — ambas en `1.1.1.1`, cubiertas por el intervalo preexistente `4041015-4041019`. El proceso completo, en [`gl_account_creation_process.md`](../domains/Master_Data_Governance/gl_account_creation_process.md).
