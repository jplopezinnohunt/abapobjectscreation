# INC-PSTLADR-NOV2026 — La dirección estructurada de noviembre rompe la NÓMINA, no los proveedores

**Estado:** OPEN · **Severidad:** GRAVE · **Deadline duro:** 14-11-2026 · **Dominio:** Payment
**Abierto:** 2026-08-19 · **Origen:** análisis del rechazo bancario de `/CGI_XML_CT_UNESCO`

---

## 1. El problema en una frase

Desde el **14 de noviembre de 2026** la dirección postal sin estructurar queda prohibida en
los ficheros de pago ISO 20022. **804 empleados a los que seguimos pagando en 2026 no tienen
ciudad en ningún sitio**, y `<TwnNm>` es obligatorio cuando se emite `<PstlAdr>`. Sus pagos
de nómina no tendrán de dónde sacar el dato.

## 2. Por qué esto NO es lo que creíamos

La sospecha inicial era el maestro de proveedores. **Medido, los proveedores están sanos.**
La avería está en nómina, y en el lado banco (que se trata aparte, ver §7).

| Origen | Líneas 2024+ | Receptores | Sin ciudad | Sin código postal |
|---|---:|---:|---|---|
| **FI-AP** — proveedores | 612.206 | 29.382 | **0 (0%)** | 276 (0,9%) |
| **HR-PY** — nómina | 343.268 | 5.128 | **1.016 (19%)** | 2.354 (45%) |
| FI-AR | 139.994 | 1 | 0 receptores / 93% de líneas | 93% de líneas |
| TR-CM-BT | 1.481 | 1 | 0 | 0 |

De los 1.016 empleados sin ciudad, **804 siguen cobrando en 2026**. En líneas: 52.727 (15%)
sin ciudad y 164.368 (47%) sin código postal.

## 3. Dónde vive el dato (y por qué se nos escapó)

Los pagos de nómina llevan `DORIGIN = 'HR-PY'` y en `REGUH` el receptor es un **`PERNR`, no un
`LIFNR`** — esos números **no existen en LFA1**. La dirección no viene de LFA1/ADRC sino del
infotipo HR, y viaja dentro del propio `REGUH` en `ZSTRA` / `ZORT1` / `ZPSTL` / `ZLAND`.

Ejemplo real (PERNR 10154618): `ZSTRA='16 Rue Ganneron'` `ZORT1='Paris'` `ZPSTL='75018'` `ZLAND='FR'`.

Cualquier auditoría de calidad de direcciones que mire LFA1 + ADRC **da los pagos de nómina
por inexistentes** — que es exactamente el error que cometí antes de mirar `DORIGIN`.

## 4. Dónde está concentrado

Las líneas sin ciudad, por país:

```
CM 2.960   BR 2.855   SN 2.568   IN 2.404   AF 2.361
ZW 2.285   TH 2.138   KE 1.920   ML 1.862   IQ 1.509
```

Camerún, Brasil, Senegal, India, Afganistán, Zimbabue, Tailandia, Kenia, Malí, Irak. **Son
oficinas de terreno, no la sede.** No es un fallo de carga: es que el alta de personal en
terreno nunca exigió ciudad.

## 5. Por qué hoy no falla y en noviembre sí

Dos motivos que se suman:

1. **DMEE no escribe la etiqueta cuando el campo está vacío.** No hay error, simplemente sale
   una dirección parcial. El banco la acepta mientras la forma sin estructurar siga permitida.
2. **La comprobación de nodo obligatorio vacío de DMEE está apagada.** `REACT_LEV_SCREEN` y
   `REACT_LEV_EXIT` están vacíos en los **1.364 nodos** de `/CGI_XML_CT_UNESCO`,
   `/CITI/XML/UNESCO/DC_V3_01` y `/SEPA_CT_UNES`, sin una sola excepción. Nada avisa en la
   corrida de pagos; el error aparece días después en el portal del banco.

A partir del 14-11-2026 esa dirección parcial deja de aceptarse.

## 6. Qué hay que hacer

1. **Sacar la lista nominal de los 804 empleados vivos sin ciudad**, por oficina, y devolverla
   a RR.HH. de terreno para que se complete en el infotipo. Es dato de personal — lo corrige
   RR.HH., no Finanzas, y no se puede parchear en el árbol DMEE.
2. **Decidir qué hacer con el código postal.** 45% de los empleados no lo tiene. Hay que
   confirmar si `PstCd` es obligatorio para el rail que paga cada oficina, porque la respuesta
   cambia el tamaño del trabajo de 804 a 2.354.
3. **Encender `REACT_LEV` en los nodos de dirección** para que la corrida avise ANTES de mandar
   el fichero. Nivel 1 (aviso) primero — nivel 2 (error) bloquearía la nómina, y eso no se
   activa sin decisión de Tesorería.
4. **Mirar el receptor único de FI-AR**: 131.530 líneas (93%) sin ciudad concentradas en una
   sola ficha. Es una anomalía barata de arreglar y no debería quedar suelta.

## 6-bis. SECCIÓN 2 — Proveedores: el `CtrySubDvsn` del rail CITI

Añadida 2026-08-19. **Ésta sí es de proveedores**, a diferencia de la sección 1.

### Qué exige Citi que no exige SocGen

Los dos bancos no consumen la dirección igual. SocGen la lee estructurada. **Citi la
aplana en tres líneas de 35 caracteres** (reglas GOLD 2026-05-06, hoja `499_US_WIRE`):

| Línea Citi | Se compone de |
|---|---|
| Target Address Line 1 | `BldgNb` + espacio + `StrtNm` |
| Target Address Line 2 | `TwnNm` + coma + `CtrySubDvsn` — *"both fields are mandatory"* |
| Target Address Line 3 | `PstCd` + `Ctry` |

> *"Overall max length of 35 characters. If exceeds 35 characters payment will reject."*
> *"Partial addresses will not be accepted. Street name, city and country are required."*

`CtrySubDvsn` es obligatorio **para Citi**, no para SocGen. Por eso este riesgo vive
sólo en el rail CITI.

### La medida

De 11.185 pagos del rail CITI en 2026, **5.239 (46%) van sin `CtrySubDvsn`**:

| Población | Pagos | Receptores distintos | Dónde está el hueco |
|---|---:|---:|---|
| **Proveedores** (FI-AP) | 2.640 | **941** | Ficha ADRC existe, `REGION` vacío |
| Nómina (HR-PY) | 2.578 | — | Sin ficha ADRC (son PERNR) → sección 1 |
| Clientes (FI-AR) | 21 | — | |

**`ADRC-REGION` está poblado en CERO de los 5.239.** No es que el árbol pierda el dato:
el dato no existe. Descartada la hipótesis de que bastara con dos mappings.

Por país: US 551 · BR 351 · FR 319 · MG 250 · CA 173 · MM 100.

### Por dónde empezar

**301 proveedores de US y Canadá, 724 pagos.** Ahí el estado o la provincia no es un
adorno: `NEW YORK` sin `NY`, `AURORA` sin `CO`, no son direcciones completas. En el
resto de países la subdivisión suele ser prescindible, y Citi la exige por formato más
que por necesidad postal.

Los más repetidos: `GRAEBEL COMPANIES INC` (AURORA, US, 19 pagos) · `UNITED NATIONS`
(NEW YORK, 16) · `UNICEF` (NEW YORK, 13) · `COMINAR REAL ESTATE` (Montreal, CA, 14).

### Un patrón que abarata el trabajo

`COMINAR` tiene `CITY1='Montreal Quebec'`. La región **existe, pegada dentro de la
ciudad**. Igual que `WASHINGTON, DC`, `Holland, MI`, `Etobicoke, Ontario`. En muchos
casos no hay que averiguar el dato: hay que **separarlo** de donde está.

Y una casualidad afortunada, que conviene conocer antes de dimensionar: como Citi
concatena `TwnNm` + coma + `CtrySubDvsn` en una sola línea, un `CITY1='Holland, MI'`
produce **exactamente la misma Línea 2** que la versión bien partida. **Para Citi es
inocuo.** Sólo importa para la conformidad ISO en general y para los rails que sí
consumen estructurado.

Eso significa que los 941 no son todos igual de urgentes: **primero los que no tienen
la región en ninguna parte**, después los que la tienen mal colocada.

### Lo que NO hay que hacer

Lanzar una campaña sobre las direcciones de **bancos**. Se descartó con medida: en el
rail CGI el 100% de los 8.419 pagos lleva BIC, y el manual de SocGen dice que *"if
filled in, name and address are ignored"*. El único sitio donde la dirección del banco
identifica de verdad son los **898 pagos de CITI sin BIC** (8%).

## 7. Qué NO es este incidente

El desastre del **lado banco** (`BNKA`: 77% de ciudades sucias en los 2.886 bancos que usamos,
`PROVZ` vacío al 99%, `ADRNR` poblado en 1 de 183.227) es un problema distinto, con dueño
distinto y solución distinta. Va aparte. Aquí sólo se trata la dirección del **receptor**.

## 8. Evidencia

- `REGUH` P01, `LAUFD >= 20240101`, 1.096.949 líneas — medido 2026-08-19
- `LFA1` (320.885) + `ADRC` (339.859) P01 — proveedores 99% ciudad limpia
- `DMEE_TREE_NODE` D01 — `REACT_LEV_*` vacío en los 1.364 nodos
- Mapa completo: `knowledge/domains/Payment/dmee_map/DMEE_CONFIG_POR_FORMATO.md`
- Claims 504–509

## 9. Lección

**Una auditoría de calidad de datos que no parte por el origen del pago miente.** Mirando sólo
LFA1+ADRC el veredicto era "99% sano" y el 35% de las líneas de pago ni aparecía en la foto,
porque los receptores de nómina no son proveedores. El primer corte de cualquier medida sobre
`REGUH` tiene que ser `DORIGIN`.
