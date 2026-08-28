# La NATURALEZA de una cuenta bancaria — y por qué decide qué extracto esperar

**Dominio:** Treasury_EBS · **Sesión:** s108 (2026-08-28) · **Origen:** INC-000013624
**Medido en vivo en P01.** Ventana 2025-01-01 → hoy.
**Instrumento:** `Zagentexecution/quality_checks/bank_account_nature_model.py`

---

## La pregunta que lo abrió

El censo de canales dejó **12 cuentas vivas que no reciben ningún extracto**, y cuatro eran
mandatos de inversión de Northern Trust. Pregunta obvia: *¿no reciben porque son de inversión?
¿Y no habría que clasificarlas como subgrupo?*

Antes de crear un subgrupo hay que mirar si el sistema ya lo tiene. **Lo tiene a medias, y no
por donde parecía.**

## Lo que YA existe — y lo que en realidad clasifica

### La jerarquía YBANK (`SETLEAF`, transacción GS02)

El doc del dominio la presentaba como la lista maestra de cuentas bancarias. Medido, sus hojas
clasifican por **GEOGRAFÍA × DIVISA**, no por naturaleza:

| Nodo | Qué agrupa de verdad | Cuentas |
|---|---|---:|
| `YBANK_ACCOUNTS_HQ_EUR` / `_USD` / `_OTH` | sede, por divisa | 9 / 9 / 6 |
| `YBANK_ACCOUNTS_FO_USD` / `_OTH` / `_EUR` / `_XAFXOF` | terreno, por divisa | 51 / 60 / 4 / 8 |
| `YBANK_ACCOUNTS_SIGHT_EUR` / `_USD` | **a la vista / ahorro** ← sí es naturaleza | 5 / 2 |
| `YBANK_ACCOUNTS_DEPOSIT` | **depósito a plazo** ← sí es naturaleza | 4 |

**El dato que rompe la hipótesis:** los tres mandatos de Northern Trust —

```
0001095041  NTB01-USD04  MANDATE PIMCO       ⎫
0001095051  NTB01-USD05  MANDATE JP MORGAN   ⎬  YBANK_ACCOUNTS_HQ_USD
0001095061  NTB01-USD06  RAMP                ⎭
```

— están en **el mismo cajón** que `SOG01-USDD1` y `CIT04-USD04`, que son las cuentas
**operativas generales** de la sede. Y `NTB02-EUR02` (IMIP) convive en `_HQ_EUR` con
`SOG01-EUR01` (General Operations) y con `NTB02-EUR01`, la del incidente.

**YBANK no separa una cartera de inversión de una cuenta corriente.**

### Los dos nodos que sí son de naturaleza, y sus límites

- **`_SIGHT`** — 6 cuentas de banco casa reales (SOG03-EURD1, BNP01-EURD1, SOG05-EURD1,
  CRA01-EURD1, CIC01-EURD4, SCB14-USDD1). Útil y fiable. Un GL (`0001089911`) no cuelga de
  ninguna cuenta.
- **`_DEPOSIT`** — 4 mayores del rango `404xxxx` y **ninguno es una cuenta de banco casa**. Es
  un conjunto de *mayores de depósito a plazo*, no de cuentas bancarias. No sirve para
  clasificar el parque.

### `SKB1-FDLEV` (nivel de planificación) tampoco

Reparte los 549 mayores de banco de UNES en `B0` (392) y `B1` (157), así que sí discrimina
algo — pero **las ocho cuentas de Northern Trust son `B0`, mandatos incluidos**. No separa
colocado de disponible.

### Y YBANK solo cubre UNES

**32 de las 167 cuentas vivas están fuera de todo set YBANK**, y son casi todas de los
institutos (IBE, ICBA, ICTP, IIEP, MGIE, UBO). La "lista maestra de cuentas bancarias" que usan
GS02 y los informes de tesorería es, de hecho, **la lista maestra de UNES**.

## Conclusión: la naturaleza NO está modelada

Vive en el **texto libre** de `T012T-TEXT1` y en la cabeza de la gente. Por eso el modelo se
deriva con **grado de evidencia explícito** — lo que decide es el grado, no la etiqueta:

| Grado | Qué significa | Se puede usar para |
|---|---|---|
| `CONFIG` | sale de configuración del sistema (un set YBANK) | decidir |
| `TEXTO` | sale del nombre que alguien escribió | orientar, y **preguntar** |
| `NINGUNA` | no hay señal | **solo preguntar** |

### El parque hoy, 167 cuentas vivas

| Naturaleza | Grado | Canal | n |
|---|---|---|---:|
| A_LA_VISTA | CONFIG | electrónico | 6 |
| A_LA_VISTA | TEXTO | sin extracto | 1 |
| **MANDATO_INVERSION** | **TEXTO** | **sin extracto** | **4** |
| OPERATIVA | TEXTO | electrónico | 10 |
| TRANSFERENCIA | TEXTO | electrónico | 5 |
| **SIN_CLASIFICAR** | **NINGUNA** | todos | **141** |

**141 de 167 sin clasificar. Ese es el hallazgo**, no un fallo del instrumento: el 84 % del
parque no tiene ninguna señal de qué clase de cuenta es.

## La correlación que sí se sostiene

**Las 4 cuentas de mandato son exactamente las 4 que no reciben extracto.** Correlación
perfecta, sin excepciones en ninguno de los dos sentidos:

| Cuenta | Texto | Canal |
|---|---|---|
| UNES/NTB01-USD04 | NORTHERN TRUST - UNESCO MANDATE PIMCO - USD | sin extracto |
| UNES/NTB01-USD05 | NORTHERN TRUST - UNESCO MANDATE JP MORGAN - USD | sin extracto |
| UNES/NTB01-USD06 | NORTHERN TRUST - UNESCO RAMP - USD | sin extracto |
| UNES/NTB02-EUR02 | NORTHERN TRUST - UNESCO IMIP - EUR | sin extracto |

Y el control que le da valor: **el mismo banco custodio, Northern Trust, tiene otras cuatro
cuentas que sí reciben extracto diario** — `NTB01-USD01` (PFF Nessim Habif), `USD02` (Cash
Pool), `USD03` (ASHI USD) y `NTB02-EUR01` (ASHI EUR, la del incidente). Es decir: **el corte no
es el banco, es la cuenta.** Dentro de un custodio conviven cuentas de efectivo, que llevan
MT940, y carteras gestionadas, que no.

> ⚠️ **Por eso `ASHI` y `PFF` NO son marcadores de inversión** aunque lo parezcan. Son
> **fondos** (seguro médico post-empleo, participation fund) cuyas cuentas de efectivo reciben
> extracto a diario. Meterlos en la lista de marcadores clasificaría como inversión cuatro
> cuentas operativas — incluida la del incidente. Los marcadores fiables son nombres de
> **gestora o programa**: `MANDATE`, `PIMCO`, `MORGAN`, `RAMP`, `IMIP`.

## ¿Y el balance? Tampoco — pero sí tiene el sitio donde ponerlas

Tercer candidato, y el más interesante: la **versión de balance** (FSV). Una posición de balance
sí es una afirmación sobre la naturaleza de lo que hay ahí. Medido sobre **FS10**, la versión que
UNES ejecuta de verdad (derivada de la variante de `RFBILA00`, no de `T011`):

| Grupo | Posición FS10 |
|---|---|
| **Mandato** — PIMCO · JP Morgan · RAMP · IMIP | `1.1.1.1 Cash with Banks` |
| **Efectivo del mismo custodio** — Nessim Habif · Cash Pool · ASHI USD · ASHI EUR | `1.1.1.1 Cash with Banks` |
| **Operativas** — SOG01-EUR01 · SOG01-USDD1 · CIT04-USD04 | `1.1.1.1 Cash with Banks` |
| **A la vista / ahorro** — SOG03-EURD1 · BNP01-EURD1 · SCB14-USDD1 | `1.1.1.1 Cash with Banks` |

**Las 352 cuentas de banco de UNES caen en UNA sola posición.** Las únicas excepciones: `UNDP`
(`1.1.7.3 UNDP Accounts`) y dos sin posición, que son **cuentas cerradas** (`BKT01-USD01`,
`JPS01-USD01`) — o sea, ningún hueco real de cobertura.

### Lo llamativo: las posiciones para inversión SÍ existen, y están vacías de cuentas de banco

```
1.1.1    Cash and Cash Equivalents
  1.1.1.1  Cash with Banks          ← aquí están las 352
1.1.2    Investments
  1.1.2.1  Short Term Deposits      ← existe
1.2.1    Investments
  1.2.1.1  Other Investments        ← existe
```

El balance tiene estructura para separar inversión de tesorería, **corriente y no corriente**, y
ninguna cuenta de banco casa la usa.

### Qué significa y qué NO significa

**No es automáticamente un error contable, y no se afirma que lo sea.** Hay una lectura
perfectamente correcta: en una cuenta de custodia, lo que SAP lleva como cuenta bancaria es la
**pata de efectivo** del mandato; los títulos no están en FI como cuenta de banco. Si el saldo de
esas cuatro cuentas es efectivo, `Cash with Banks` es donde va.

**Lo que sí es una pregunta abierta para Finanzas/Tesorería**, con la evidencia delante: las
cuatro cuentas de mandato **no reciben extracto bancario** y se presentan como *Cash and Cash
Equivalents*. Si su saldo es efectivo, ¿por qué no llega extracto? Y si no lo es, la posición de
balance no es la que les toca. **Las dos preguntas no pueden ser ambas “no pasa nada”.**

### Conclusión sobre dónde vive la clasificación

Tres sitios candidatos, los tres medidos, **ninguno la lleva**:

| Candidato | Qué clasifica de verdad |
|---|---|
| YBANK (Report Painter, GS02) | geografía × divisa. Y lo consume **un solo informe**, `ZAVERAGE` |
| `SKB1-FDLEV` | reparte B0/B1, pero las 8 de Northern Trust son B0 |
| **FSV / balance (FS10)** | **todo en `Cash with Banks`** — aunque tiene posiciones de inversión sin usar |

La naturaleza de la cuenta no está en ninguna parte del sistema. Está en el texto libre.

## Lo que esto cambia para el EBS

La naturaleza **decide qué extracto esperar**, y por tanto **cuándo el silencio es una alarma**:

| Naturaleza | Extracto esperado | El silencio es… |
|---|---|---|
| OPERATIVA / TRANSFERENCIA | electrónico, cadencia diaria | **alarma a los pocos días** |
| A_LA_VISTA / AHORRO | cadencia baja | normal hasta bastante tiempo |
| **MANDATO_INVERSION** | **plausible que ninguno** | **normal — pero hay que declararlo** |
| terreno con banco sin MT940 | manual (FF67), cadencia mensual | alarma contra su propio ritmo |

Sin esta capa, la vigilancia de canal sólo puede comparar cada cuenta **contra su propio
historial** — que es lo que hace hoy `bank_statement_channel_census.py`, y funciona para las
que ya recibían. **No sirve para las 12 que nunca han recibido nada**: ahí no hay historial
contra el que comparar, y sin naturaleza declarada no se distingue *«no aplica»* de *«nunca se
configuró»*.

## Cuál de los tres clasifica mejor: YBANK, y con distancia

| | Dimensiones | Cuentas que discrimina | ¿Nodo de naturaleza? |
|---|---|---|---|
| **YBANK** | 3 niveles, 10 hojas, 158 valores | **135 de 167** | **Sí — `_SIGHT`** (6 cuentas, fiable) |
| `SKB1-FDLEV` | 2 valores (B0/B1) | binario; las 8 de NT son B0 | no |
| FSV / balance | 1 posición para 352 cuentas | ninguna | no, aunque las posiciones existan |

Los otros dos no es que clasifiquen peor: **para esta pregunta no clasifican nada.**

### Por qué YBANK es además el sitio correcto para extender

- **Radio de explosión casi nulo.** Lo consume un solo informe (`ZAVERAGE`) y sólo el nodo raíz.
  Añadir `YBANK_ACCOUNTS_MANDATE` bajo `_HQ` no rompe nada porque nada más lo lee.
- **El precedente existe y funciona:** `_SIGHT` es un nodo de naturaleza conviviendo con los de
  geografía, y es fiable.
- **El pago es inmediato:** `bank_account_nature_model.py` ya gradúa la pertenencia a un set como
  evidencia `CONFIG` y el texto libre como `TEXTO`. Declarar el nodo mueve esas 4 cuentas de
  *«lo deduzco del nombre»* a *«está declarado»* **sin tocar una línea de código**, y la
  vigilancia del canal deja de marcarlas como hueco.

### Lo que hay que saber antes de tocarlo

- **Sólo cubre UNES** — 32 cuentas vivas fuera, casi todas de institutos. Extenderlo no las
  alcanza; para ellas hace falta otra decisión.
- **`_DEPOSIT` es un MAL precedente**: es un nodo de naturaleza que **no contiene cuentas de
  banco casa**, sino 4 mayores del rango `404xxxx`. Copiar ese patrón repite el error.
- **Se transporta como contenido completo de tabla** (`TDAT GRW_SET`), no como delta:
  **alinear D01 y P01 antes**, o el destino pierde lo que tuviera y el origen no se entera.

## Lo que hay que decidir (no lo decide el agente)

**1 · Declarar la naturaleza donde se pueda consultar.** Hoy se adivina del texto. La forma
coherente con lo que ya existe es **extender YBANK con nodos de naturaleza** —
`YBANK_ACCOUNTS_MANDATE` junto a los `_SIGHT` y `_DEPOSIT` que ya están— en lugar de inventar
una tabla nueva. Extender, no re-inventar.

**2 · Confirmar con Tesorería las 4 de mandato.** La hipótesis *«no llevan extracto porque son
carteras»* es plausible y está sin confirmar. Si es correcta, se declara y dejan de aparecer
como hueco para siempre. Si no lo es, son cuatro cuentas de inversión sin conciliar.

**3 · Las 7 «sin extracto» sin clasificar** — ésas sí son preguntas abiertas de verdad:
`UIL/DEU01-EUR02`, `UNES/BRA01-BRL01`, `UNES/CBE01-ETB02`, `UNES/DEU01-EUR01`,
`UNES/DEU02-EUR01`, `UNES/UBS02-CHF01`, `UNES/UNDP-UNDP`.

**4 · YBANK no cubre a los institutos.** 32 cuentas fuera. O se extiende, o se dice
explícitamente que la jerarquía es de UNES y los institutos se miden por otra vía.

---

## Cómo se corre

```bash
python Zagentexecution/quality_checks/bank_account_nature_model.py
python Zagentexecution/quality_checks/bank_account_nature_model.py --bukrs UNES --json modelo.json
```

Tres niveles: **sociedad → banco → cuenta**. Por defecto todas las sociedades, ventana
2025-2026.

---

**Relacionados:** [bank_statement_channels_by_company.md](bank_statement_channels_by_company.md) ·
[house_bank_operating_roles.md](house_bank_operating_roles.md) (el papel de PAGO de cada banco;
esto es el papel de TENENCIA) · [house_bank_configuration.md](house_bank_configuration.md) ·
[../../incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md](../../incidents/INC-000013624_ebs_ntb02_account_change_orphans_t028b.md)
