# Cómo entra el extracto de cada banco — el censo por sociedad

**Dominio:** Treasury_EBS · **Sesión:** s108 (2026-08-28) · **Origen:** INC-000013624
**Medido en vivo en P01 por RFC.** Ventana **2025-01-01 → hoy**. Instrumento:
`Zagentexecution/quality_checks/bank_statement_channel_census.py`

---

## Por qué existe

Diagnosticando INC-000013624 apareció algo que no estaba escrito en ningún sitio: **el parque
de cuentas bancarias no es homogéneo.** Hay cuentas cuyo extracto entra por fichero y cuentas
cuyo extracto **lo teclea una persona**. Se distinguen por `FEBKO.EFART` (`E` / `M`).

No es un detalle técnico. Cambia **qué configuración hace falta**, **qué se puede romper** y,
sobre todo, **quién se entera cuando deja de entrar**:

| | necesita `T028B` | qué falla | quién lo detecta hoy |
|---|---|---|---|
| **ELECTRÓNICO** | **sí**, con el número de cuenta actual | cambia el número → deja de entrar en silencio | **nadie** (era el incidente) |
| **MANUAL** | **no** — medido: 116 extractos sin esa fila | la persona deja de teclear | **nadie** |
| **SIN EXTRACTO** | — | no se sabe si aplica o si se dejó de hacer | **nadie lo ha declarado nunca** |

## El mapa — 404 cuentas, 237 cerradas por texto, **167 vivas**

Se parte **por sociedad** a propósito: cada una opera su parque de bancos de forma distinta, y
el agregado lo esconde — un total dominado por UNES hace desaparecer a las demás.

| Sociedad | ELEC | MANU | MIXTO | SIN EXTR. | vivas | perfil |
|---|---:|---:|---:|---:|---:|---|
| **UNES** | 99 | **8** | 26 | 11 | **144** | mixto: 26 % con intervención manual |
| IIEP | 5 | 0 | 0 | 0 | 5 | todo automático |
| UIL | 4 | 0 | 0 | 1 | 5 | todo automático |
| UBO | 3 | 0 | 0 | 0 | 3 | todo automático |
| IBE | 2 | 0 | 0 | 0 | 2 | todo automático |
| ICBA | 1 | 0 | 1 | 0 | 2 | mixto: 50 % |
| ICTP | 2 | 0 | 0 | 0 | 2 | todo automático |
| MGIE | 2 | 0 | 0 | 0 | 2 | todo automático |
| UIS | 2 | 0 | 0 | 0 | 2 | todo automático |

**Toda la complejidad está en UNES.** Los institutos son casos limpios y automáticos. Cualquier
proceso que se defina aquí es, en la práctica, un proceso de UNES.

> **Por qué partir por sociedad no es cosmética:** `CBE01-ETB02` existe en **ICBA** y en
> **UNES**. La de ICBA recibe 543 extractos diarios; la de UNES, cero desde 2025. Mismo banco,
> misma cuenta, comportamiento opuesto. En un total agregado esa cuenta figuraría como "activa".

## Los tres canales

### 1 · ELECTRÓNICO — 120 cuentas

Fichero MT940 → Coupa → job `EBS INTEGRATION` (ver
[ebs_file_pipeline_and_jobs.md](ebs_file_pipeline_and_jobs.md)). **Requiere fila en `T028B`
con el número de cuenta ACTUAL.** Estado hoy: **1 sin fila** — `UNES/NTB02-EUR01`, el incidente.
Mudas para su propio ritmo: **1**, la misma.

> ## ⚠️ CORRECCIÓN 2026-08-28 (mismo día) — las cifras de abajo SUBESTIMAN entre 5 y 10 veces
>
> Un cruce de instrumentos midió la población de verdad: **no son 8 cuentas manuales y 4
> personas, son 39 cuentas (34 vivas), 41 usuarios, 802 extractos y 13.942 líneas.**
>
> **Causa:** la etiqueta `canal` se deriva de que *existan* extractos E y M, así que una cuenta
> **97 % tecleada a mano sale MIXTO** y desaparece. Caso puro: **SOG06 (Haití)** tiene 55
> extractos tecleados con **9.623 líneas — el 69 % de todo lo tecleado a mano en UNESCO** —
> frente a 5 electrónicos con **cero** líneas en FEBEP. Es 100 % manual de hecho y figuraba como
> MIXTO. Segundo defecto: el filtro usaba un porcentaje **redondeado**, así que 1 extracto
> tecleado entre 500 daba `0` y salía de la población.
>
> **Y se cae un argumento que publiqué:** «1.712 líneas frente a 11.669 de una sola cuenta
> electrónica» ya no desmonta la oportunidad — son **13.942 frente a 11.669, comparables**.
> Tampoco la confirma: la restricción sigue aguas arriba, en que el banco emita MT940.
>
> Las dos causas están corregidas en el instrumento. Claims 642 y 643.

### 2 · MANUAL — 8 cuentas · **el hueco de proceso**

Alguien las teclea en FF67. La columna *quién* es **un usuario con nombre y apellidos**:

| Cuenta | Texto | Último | n | Ritmo | Mudo | Quién |
|---|---|---|---:|---|---:|---|
| UNES/BTE01-USD01 | UNESCO TEHRAN - USD | 2025-12-12 | 6 | esporádica | **259 d** | B_TASHAKORI |
| UNES/BTE01-EUR01 | UNESCO TEHERAN - EUR | 2026-04-01 | 8 | esporádica | **149 d** | B_TASHAKORI |
| UNES/ECO08-ZWG01 | UNESCO HARARE - ZWG | 2026-06-16 | 10 | mensual | **73 d** | R_MUSAKWA |
| UNES/BMN01-EUR01 | UNESCO HAVANA - EUR | 2026-07-28 | 49 | mensual | 31 d | J_MONTANO-PU |
| UNES/BMN01-CUP02 | UNESCO HAVANA - CUP | 2026-08-14 | 63 | mensual | 14 d | J_MONTANO-PU |
| UNES/BLN01-USD01 | (Jartum) | 2026-08-18 | 168 | semanal | 10 d | K_ABDULLAH |
| UNES/BLN01-SDD01 | (Jartum) | 2026-08-20 | 126 | semanal | 8 d | K_ABDULLAH |
| UNES/BTE01-IRR02 | UNESCO TEHRAN - IRR | 2026-08-25 | 40 | mensual | 3 d | B_TASHAKORI |

**Son cuatro personas sosteniendo ocho cuentas.** Todas en oficinas de terreno con contexto
difícil (Teherán, Harare, La Habana, Jartum) — probablemente por eso son manuales: bancos que
no emiten MT940, o canales que no llegan.

### 3 · MIXTO — 27 cuentas

Entran por fichero, pero **también** hay entradas a mano. El usuario dominante es `JOBBATCH`,
así que lo manual es la **excepción**, no el modo de operación — entre 0 % y 7 % de los
extractos. Los que más: `SCB16-GHS01` 7 %, `CIT14-MXN01` 6 %, `ECO01-XAF01` 3 %.

**No confundir MIXTO con MANUAL.** Una cuenta MIXTA al 1 % es una cuenta automática con una
corrección puntual; una MANUAL al 100 % es un proceso humano completo.

### 4 · SIN EXTRACTO — 12 cuentas vivas

Ni un extracto desde 2025. **No es un defecto por sí mismo** — puede que ese banco no mande
nada. El problema es que **nadie lo ha declarado**, así que no se distingue *«no aplica»* de
*«se dejó de hacer»*:

| Cuenta | Texto |
|---|---|
| UNES/NTB01-USD04 | NORTHERN TRUST - UNESCO MANDATE PIMCO - USD |
| UNES/NTB01-USD05 | NORTHERN TRUST - UNESCO MANDATE JP MORGAN - USD |
| UNES/NTB01-USD06 | NORTHERN TRUST - UNESCO RAMP - USD |
| UNES/NTB02-EUR02 | NORTHERN TRUST - UNESCO IMIP - EUR |
| UNES/BRA01-BRL01 · BRL02 | UNESCO BRASILIA (+ DEPOSIT) |
| UNES/DEU01-EUR01 · DEU02-EUR01 | UNESCO U.I.E / UIL HAMBURG |
| UIL/DEU01-EUR02 | UNESCO UIL - HAMBURG - EUR2 |
| UNES/CBE01-ETB02 | UNESCO IICBA ADDIS ABABA - RESIDENT - ETB |
| UNES/UBS02-CHF01 | UNESCO IBE - CHF |
| UNES/UNDP-UNDP | UNDP NEW YORK |

Las cuatro de Northern Trust son **cuentas de mandato de inversión** (PIMCO, JP Morgan, RAMP,
IMIP) — y son **exactamente** las cuatro que no reciben nada, sin excepción en ninguno de los
dos sentidos. El control que le da valor: el mismo custodio tiene otras cuatro cuentas que sí
reciben a diario (PFF Nessim Habif, Cash Pool, ASHI USD y ASHI EUR, la del incidente). **El
corte no es el banco: es la cuenta.**

Pero **esa naturaleza no está modelada en ninguna parte** — se lee del texto libre. La
jerarquía YBANK, que parecía el sitio, clasifica por geografía y divisa: los tres mandatos
están en `YBANK_ACCOUNTS_HQ_USD`, el mismo cajón que las cuentas operativas de la sede. Modelo
completo y qué habría que declarar:
[bank_account_nature_model.md](bank_account_nature_model.md).

---

> ⚠️ **Una cuenta nueva NO aparece en FF67 hasta que llega su primer extracto — y eso no es un
> defecto.** La lista de cuentas de FF67 es **historial de extractos recibidos**, no configuración.
> Probado el 2026-08-28: ofrece el par `(SP0000000MX7, UNO10)`, que **no existe en `T012K`** —NTB01
> usa hoy `SP0000000MXL`— pero sí en `FEBKO.ABSND`, con 10 extractos cuyo último es del
> **05.03.2015**. Una lista derivada de configuración no puede producir eso.
> **Ante «la cuenta nueva no está en FF67»: no revises la ficha del banco, comprueba si ha llegado
> algún extracto.** (claim 639 · INC-000013624)

## Los procesos que hay que definir

Cuatro, en orden de coste de no tenerlos.

### P1 · Vigilancia del canal — el único que ya está resuelto

Una cuenta que deja de recibir no dispara nada. Ni el estado del job (siempre verde), ni la
ficha del banco (siempre correcta), ni FF67 (muestra el pasado). **Resuelto** con
`bank_statement_channel_census.py` + `house_bank_ebs_wiring_check.py`: comparan cada cuenta
contra **su propio ritmo** (diaria / semanal / mensual), que es lo que hace la señal utilizable
— 30 días de silencio es alarma en una cuenta diaria y rutina en una mensual.

**Falta:** decidir **con qué periodicidad se corre y quién lo mira.** Un instrumento que nadie
ejecuta es un instrumento que no existe.

### P2 · El extracto manual no tiene dueño declarado ni cadencia esperada

Ocho cuentas dependen de cuatro personas nombradas, y **no hay ningún sitio donde esté escrito
que esa persona es la responsable, ni cada cuánto debe hacerlo.** Se deduce del log, a
posteriori. `BTE01-USD01` lleva **259 días** sin extracto y nadie lo ha preguntado.

Hay que declarar, por cuenta manual: **responsable · suplente · cadencia esperada · qué hacer
si se incumple**. Y entonces la vigilancia de P1 puede comparar contra algo.

### P3 · «Sin extracto» no está declarado — no se distingue no-aplica de olvido

12 cuentas vivas. Hace falta **un campo o una convención** que diga, por cuenta, si se espera
extracto y por qué canal. Hoy la única marca de estado que existe es `CLOSED` en el texto
(§ apéndice de [ebs_file_pipeline_and_jobs.md](ebs_file_pipeline_and_jobs.md)) — que no es un
campo, es una costumbre.

**El formulario de alta ya pregunta esto** («*Bank statement electronically uploaded? Yes/No*»,
ver el skill). La respuesta **no se guarda en ninguna parte del sistema**. Guardarla es la
mitad del trabajo de P3.

### P4 · El cambio de número de cuenta

**Definido** en [house_bank_configuration.md](house_bank_configuration.md) §2b tras este
incidente. Era el que faltaba y costó un canal parado 11 días.

---

## Cómo se corre

```bash
python Zagentexecution/quality_checks/bank_statement_channel_census.py
python Zagentexecution/quality_checks/bank_statement_channel_census.py --bukrs UNES --json censo.json
```

Por defecto: **todas las sociedades, desde 2025-01-01**. Las dos cosas son decisiones de
método, no comodidad — mirar más atrás arrastra cuentas que ya no existen y **fechas basura**
(`FEBKO` tiene extractos con `AZDAT` en el año 2207 y 2208: un 2022 mal tecleado, que envenena
cualquier cálculo de «último extracto» si no se filtra).

---

**Relacionados:** [ebs_file_pipeline_and_jobs.md](ebs_file_pipeline_and_jobs.md) ·
[house_bank_configuration.md](house_bank_configuration.md) ·
[bank_statement_ebs_architecture.md](bank_statement_ebs_architecture.md) ·
[../../incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md](../../incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md)
