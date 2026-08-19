# INC-PSTLADR-NOV2026 — Dirección estructurada obligatoria: dos arreglos, dos poblaciones, dos dueños

**Estado:** OPEN · **Severidad:** GRAVE · **Deadline duro:** 14-11-2026 · **Dominio:** Payment
**Abierto:** 2026-08-19 · **Origen:** análisis del rechazo bancario de `/CGI_XML_CT_UNESCO`

---

## 1. El problema en una frase

Desde el **14 de noviembre de 2026** la dirección postal sin estructurar queda prohibida en los
ficheros de pago ISO 20022. Dos poblaciones distintas no la tienen, por motivos distintos, y las
corrige gente distinta:

| | Población | Qué falta | Lo corrige |
|---|---:|---|---|
| **FIX A — Empleados** | **943 vivos** | la **ciudad**, y en el 45% el código postal | RR.HH. de la oficina de terreno |
| **FIX B — Proveedores** | **941** (301 urgentes) | la **región** (`CtrySubDvsn`) en el rail CITI | Compras / Finanzas |

**No se solapan y no se arreglan igual.** El resto del documento los trata por separado.

## 2. El formato NO es el problema (ya está resuelto)

| Rail | Estado del árbol DMEE |
|---|---|
| `/CGI_XML_CT_UNESCO` | **cerrado** — v5 y el replay de un pago real pasan XSD y reglas, hoy y en modo noviembre |
| `/CITI/XML/UNESCO/DC_V3_01` | **conforme** — 0 pagos exceden 35 char, 0 sin calle, 0 sin ciudad; el híbrido de `UltmtCdtr` está inerte |
| `/SEPA_CT_UNES` | **abierto** — `Dbtr` tiene `Ctry` antes de `CtrySubDvsn`: el mismo defecto `xs:sequence` que tumbó CGI. Latente porque `CtrySubDvsn` viene vacío. Nodos `N_2225746230` ↔ `N_7471680250` |

Lo que queda es dato maestro, no configuración.

## 3. Por qué hoy no falla y en noviembre sí

Tres motivos que se suman, y el tercero invalida cualquier tranquilidad basada en el histórico:

1. **DMEE no escribe la etiqueta cuando el campo está vacío.** No hay error: sale una dirección
   parcial y ya está.
2. **La comprobación de nodo obligatorio vacío de DMEE está apagada.** `REACT_LEV_SCREEN` y
   `REACT_LEV_EXIT` vacíos en los **1.364 nodos** de los tres árboles, sin una sola excepción.
   Nada avisa en la corrida; el error aparece días después en el portal del banco.
3. **La regla aún no está en vigor.** Que hoy los acepten no es evidencia de nada — es ausencia
   de control, no conformidad. Todo lo de aquí está medido contra el texto publicado.

---

# FIX A — EMPLEADOS (nómina)

**Dueño: RR.HH. de la oficina de terreno.** No es dato de Finanzas y no se parchea en DMEE.

## A.1 La medida

| Origen | Líneas 2024+ | Receptores | Sin ciudad | Sin código postal |
|---|---:|---:|---|---|
| **HR-PY** — nómina | 343.268 | 5.128 | **1.016 (19%)** | 2.354 (45%) |
| FI-AP — proveedores | 612.206 | 29.382 | 0 (0%) | 276 (0,9%) |
| FI-AR | 139.994 | 1 | 93% de líneas | 93% de líneas |
| TR-CM-BT | 1.481 | 1 | 0 | 0 |

De los 1.016 empleados sin ciudad, **804 seguían cobrando en 2026** medido sobre "nunca tuvo
ciudad"; **943** medido sobre la dirección del **pago más reciente**, que es el criterio correcto
porque es la que viajaría en noviembre. En líneas: 52.727 (15%) sin ciudad, 164.368 (47%) sin
código postal.

## A.2 Dónde vive el dato, y por qué se nos escapó

Los pagos de nómina llevan `DORIGIN = 'HR-PY'` y en `REGUH` el receptor es un **`PERNR`, no un
`LIFNR`** — esos números **no existen en LFA1**. La dirección no viene de LFA1/ADRC sino del
infotipo HR, y viaja dentro del propio `REGUH` en `ZSTRA` / `ZORT1` / `ZPSTL` / `ZLAND`.

Ejemplo real (PERNR 10154618): `ZSTRA='16 Rue Ganneron'` `ZORT1='Paris'` `ZPSTL='75018'` `ZLAND='FR'`.

Cualquier auditoría que mire LFA1 + ADRC **da los pagos de nómina por inexistentes** — el 35% de
las líneas de pago. Es el error que se cometió antes de partir por `DORIGIN`.

## A.3 Dónde está concentrado

```
CM 2.960   BR 2.855   SN 2.568   IN 2.404   AF 2.361
ZW 2.285   TH 2.138   KE 1.920   ML 1.862   IQ 1.509
```

Camerún, Brasil, Senegal, India, Afganistán, Zimbabue, Tailandia, Kenia, Malí, Irak. **Oficinas de
terreno, no la sede.** No es un fallo de carga: el alta de personal en terreno nunca exigió ciudad.

## A.4 Pasos

1. **Sacar la lista nominal de los 943**, por oficina, y devolverla a RR.HH. de terreno para que
   completen el infotipo.
   `python Zagentexecution/quality_checks/structured_address_readiness.py --origin HR-PY --solo-vivos --csv nomina.csv`
2. **Decidir el código postal.** 45% no lo tiene. Confirmar si `PstCd` es exigible en el rail que
   paga cada oficina — la respuesta mueve el alcance de 943 a 2.354.
3. **Anomalía suelta de FI-AR**: un único receptor con 131.530 líneas (93%) sin ciudad. Barato de
   mirar y no debería quedar colgando.

---

# FIX B — PROVEEDORES (`CtrySubDvsn` del rail CITI)

**Dueño: Compras / Finanzas.** Vive **sólo en el rail CITI**, y conviene entender por qué.

## B.1 Los dos bancos no consumen la dirección igual

SocGen la lee estructurada. **Citi la aplana en tres líneas de 35 caracteres** (reglas GOLD
2026-05-06, hoja `499_US_WIRE`):

| Línea Citi | Se compone de |
|---|---|
| Target Address Line 1 | `BldgNb` + espacio + `StrtNm` |
| Target Address Line 2 | `TwnNm` + coma + `CtrySubDvsn` — *"both fields are mandatory"* |
| Target Address Line 3 | `PstCd` + `Ctry` |

> *"Overall max length of 35 characters. If exceeds 35 characters payment will reject."*
> *"Partial addresses will not be accepted. Street name, city and country are required."*

`CtrySubDvsn` es obligatorio **para Citi**, no para SocGen. De ahí que este arreglo no toque a CGI.

## B.2 La medida

De 11.185 pagos del rail CITI en 2026, **5.239 (46%) van sin `CtrySubDvsn`**:

| Población | Pagos | Receptores distintos | Dónde está el hueco |
|---|---:|---:|---|
| **Proveedores** (FI-AP) | 2.640 | **941** | Ficha ADRC existe, `REGION` vacío |
| Nómina (HR-PY) | 2.578 | — | Sin ficha ADRC (son PERNR) → **FIX A** |
| Clientes (FI-AR) | 21 | — | |

**`ADRC-REGION` está poblado en CERO de los 5.239.** No es que el árbol pierda el dato: el dato no
existe. Descartada la hipótesis de que bastara con dos mappings.

Por país: US 551 · BR 351 · FR 319 · MG 250 · CA 173 · MM 100.

## B.3 Por dónde empezar

**301 proveedores de US y Canadá, 724 pagos.** Ahí el estado o la provincia es parte de la
dirección: `NEW YORK` sin `NY` o `AURORA` sin `CO` no están completas. En el resto de países la
subdivisión suele ser prescindible y Citi la exige por formato más que por necesidad postal.

Los más repetidos: `GRAEBEL COMPANIES INC` (AURORA, US, 19 pagos) · `UNITED NATIONS` (NEW YORK,
16) · `UNICEF` (NEW YORK, 13) · `COMINAR REAL ESTATE` (Montreal, CA, 14).

## B.4 Un patrón que abarata el trabajo

`COMINAR` tiene `CITY1='Montreal Quebec'`. La región **existe, pegada dentro de la ciudad**. Igual
que `WASHINGTON, DC`, `Holland, MI`, `Etobicoke, Ontario`. En muchos casos no hay que averiguar el
dato: hay que **separarlo** de donde está.

Y una casualidad que conviene conocer antes de dimensionar: como Citi concatena `TwnNm` + coma +
`CtrySubDvsn` en una sola línea, un `CITY1='Holland, MI'` produce **exactamente la misma Línea 2**
que la versión bien partida. **Para Citi es inocuo.** Sólo importa para la conformidad ISO general
y para los rails que sí consumen estructurado.

Así que los 941 no son igual de urgentes: **primero los que no tienen la región en ninguna parte**,
después los que la tienen mal colocada.

## B.5 Pasos

1. **Los 301 de US/CA** (724 pagos) → completar `ADRC-REGION` con el estado/provincia.
2. **Los 640 restantes**, separando antes los que ya llevan la región dentro de `CITY1` — ésos son
   cosmética para Citi y pueden esperar.
3. Re-medir con
   `python Zagentexecution/quality_checks/structured_address_readiness.py --origin FI-AP --csv proveedores.csv`

---

## 4. Lo que NO hay que hacer (descartado con medida)

**Una campaña sobre las direcciones de BANCOS.** `BNKA` tiene 77% de ciudades sucias en los 2.886
bancos que usamos, `PROVZ` vacío al 99% y `ADRNR` poblado en 1 de 183.227 — pero:

- en el rail CGI **el 100% de los 8.419 pagos lleva BIC**, y el manual de SocGen dice
  *"BIC is recommended (if filled in, name and address are ignored)"*;
- `BNKA` **no tiene campo de código postal**, así que `PstCd` de un agente no es emitible por la
  vía del árbol haga lo que haga el maestro.

El único sitio donde la dirección del banco identifica de verdad son los **898 pagos de CITI sin
BIC** (8%). Ahí sí, y sólo ahí.

## 5. Evidencia

- `REGUH` P01, `LAUFD >= 20240101`, 1.096.949 líneas — medido 2026-08-19
- `REGUT` P01 2026 por `DTFOR` — atribución de rail
- `LFA1` (320.885) + `ADRC` (339.859) P01
- `DMEE_TREE_NODE` D01 — `REACT_LEV_*` vacío en los 1.364 nodos
- Reglas de banco: `ISOXML CREDIT V3_FormatRules_GOLD_2026May06` hoja `499_US_WIRE` filas 598-608
  y 645-655 · `202601 TECHNICAL BROCH_FR_pain.001.001.03_Cross border CT.docx` fila CdtrAgt/BIC
- Mapa de árboles: `knowledge/domains/Payment/dmee_map/DMEE_CONFIG_POR_FORMATO.md`
- Claims 504–513

## 6. Lecciones

**Una auditoría de calidad de direcciones que no parte por `DORIGIN` miente.** Mirando sólo
LFA1+ADRC el veredicto era "99% sano" y el 35% de las líneas de pago no aparecía en la foto, porque
los receptores de nómina son PERNR y no existen en LFA1.

**"Hoy lo aceptan" no es evidencia cuando la norma no está en vigor.** Se reportó que Citi no
rechazaría el fichero apoyándose en que 11.185 pagos pasaron en 2026. Era ausencia de control, no
conformidad. Regla `feedback_grace_period_acceptance_is_not_evidence`.

**Un fichero válido puede llevar un dato falso.** `TwnNm='CAMBRIDGE CB23BZ'` pasa cualquier
esquema y no es una ciudad. Ningún validador lo ve; sólo el dato maestro lo arregla. Es la razón
de que los dos FIX sigan siendo trabajo real aunque los ficheros salgan verdes.
