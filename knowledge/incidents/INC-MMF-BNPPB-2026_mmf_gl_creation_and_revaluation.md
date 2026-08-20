# INC-MMF-BNPPB-2026 — Alta de 2 GL de fondo monetario BNP PB y su tratamiento de revaluación

**Status**: ANALIZADO — decisión tomada con evidencia live. **PENDIENTE de ejecución**: (1) OB09/T030H + variante `UNES_DEPOSIT` para 4041018 · (2) sync P01→D01/V01 (script escrito, bloqueado por permisos) · (3) respuesta a Jeannette sobre 4041019
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
| 2 | OB09/T030H para 4041018 (CURTP 10 y 30) | ❌ **PENDIENTE** — 0 filas hoy |
| 3 | Añadir 4041018 al rango de la variante F.05 `UNES_DEPOSIT` | ❌ **PENDIENTE** — y es el paso que se olvida |
| 4 | Revaluación de 4041019 | ⛔ **NO PROCEDE** — el formulario firmado dice NO |
| 5 | Sync P01 → D01 (2 cuentas) y V01 (2, o 4 con la deriva) | ❌ **PENDIENTE** |

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
| 4 | Variante F.05 **`UNES_DEPOSIT`** | añadir 4041018 al rango |

**El paso 4 es el que se olvida.** `T030H` dice *dónde* postear la diferencia; la **variante**
decide *si* la cuenta entra en el cálculo. Configurar solo OB09 produce una revaluación que **nunca
corre, en silencio** — el mismo modo de fallo que dejó a ICTP sin valorar julio y noviembre de 2025.

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

1. **⚠️ `4041014` (MMF USD JPMorgan) tiene `T030H` con exposición nula.** Solo mueve USD en una
   sociedad USD: configuración sin efecto. 4041015 y 4041016, también USD, no la tienen. La
   población es **inconsistente**: tres cuentas USD, una con config y dos sin ella. Ninguna de las
   tres puede generar diferencia de cambio, así que no hay daño — pero sí hay ruido de config que
   contradice la regla.
2. **V01 lleva 2 cuentas de deriva** (4041015, 4041016) desde 2024, que sí llegaron a D01.
3. **El rango de `UNES_DEPOSIT` no es auditable offline** — ver §10.

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
- **El rango de la variante `UNES_DEPOSIT` no es legible por RFC.** `sapf100_vari` / `sapf100_varid`
  están en el registro (42/21 filas) pero **el contenido está vacío**: VARI/VARIS son pool tables y
  RFC solo devuelve el nombre. Es `KU-2026-070-02`. Se lee en pantalla F.05 o vía
  `RFC_ABAP_INSTALL_AND_RUN` en D01 (en P01 lo bloquea S_DEVELOP).
- **No verificado**: si MP_BOUA usó transporte para el alta, y si el rango actual de `UNES_DEPOSIT`
  ya cubre 4041018 por casualidad (el rango descrito es "4041011 > 4041013", con 4041017 dentro por
  medios que no hemos leído).
