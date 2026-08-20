# El rol operativo de los bancos casa — quién es doméstico, quién cruza, quién no emite fichero

**Dominio**: Treasury · Payment_BCM · Procurement_P2P · FI
**Estado**: VERIFICADO, medido sobre REGUH + LFBK + T042Z + T001 — Sesión #102 (2026-08-20)
**Herramienta**: `python brain_v2/house_bank_roles.py` → `brain_v2/house_bank_roles.json` (paso 2d de `rebuild_all.py`)
**Claims**: 530 · 531

---

## 0. Por qué existe este documento

Es el **AS-RUN** del que [`house_bank_configuration.md`](house_bank_configuration.md) es el AS-DESIGNED. Aquél dice *cómo se da de alta un banco casa*; éste dice *qué papel juega cada uno de los que ya existen*, derivado de lo que hacen y no de lo que dice su ficha.

Nace de un fallo concreto y caro. En agosto de 2026 Citibank avisó de que exigiría Purpose of Payment para Egipto. Se analizó, se construyó y se probó extremo a extremo. Diez días después Société Générale confirmó que no había nada que hacer: **el canal de Citi no lleva ese flujo**.

El dato estaba medido desde el 2026-08-17 —claims 492 y 493, *"EGYPT IS 93.9% SOCGEN"*, *"cola de Citi 2,0%"*— y aun así la pregunta no se hizo, porque vivía disperso en prosa en vez de ser una **propiedad consultable del modelo**.

> No faltaba una regla que recordar. Faltaba modelo.

---

## 1. El eje que ya estaba y no leíamos: doméstico vs internacional

**El purpose code es un requisito CROSS-BORDER.** Un pago doméstico —mismo sistema bancario a los dos lados— no lo necesita: el banco local no lo pide. Esa es la razón de fondo por la que el aviso de Citi no nos vinculaba, y no una particularidad egipcia.

Y la clasificación **ya está en SAP**, en el texto del método de pago (`T042Z-TEXT1`, país FR):

| Método | Texto | Eje | Formato |
|---|---|---|---|
| `L` | *Payments in US in USD only* | **DOMÉSTICO US** | `/CITI/XML/UNESCO/DC_V3_01` |
| `N` | *Payments outside US non-EUR* | **INTERNACIONAL** | `/CGI_XML_CT_UNESCO` |
| `H` | *Euro Payments France* | **DOMÉSTICO FR** | `/CMI101` |
| `I` | *Euro Payment SEPA zone* | **ZONA** | `/CMI101` |
| `J` | *Euro Payment outside SEPA-zone* | **INTERNACIONAL** | `/CGI_XML_CT_UNESCO` |
| `S` | *SEPA Payment* | ZONA | `/SEPA_CT_UNES` |
| `3` | *Manual cheque (Pre-Numbered)* | — | ninguno (`XSCHK='X'`) |

La frase con la que BFM cerró el caso de Egipto —*"USD payments through Citibank are only used for domestic, US, payments"*— **es literalmente el nombre del método `L`**. Llevábamos meses leyendo los métodos como claves de enrutado y nunca como lo que también son: **una afirmación sobre qué clase de pago es cada uno**.

---

## 2. Cómo se deriva el rol de un banco — todo medido, nada declarado

| Propiedad | Derivación |
|---|---|
| País del banco casa | `REGUH-UBNKS` — es **nuestro** banco, no el del beneficiario (claim 489) |
| **Doméstico** | % de sus pagos donde el país del banco del **beneficiario** (`LFBK-BANKS`) coincide con el suyo |
| **Papel / cheque** | % por métodos con `T042Z-XSCHK='X'` → **no hay fichero SAP que corregir** |
| Formato | `T042Z-FORMI` → el árbol DMEE |
| ¿Despacha PPC? | Por el país del banco casa: sólo `FR` selecciona `YCL_IDFI_CGI_DMEE_FR`, la única clase que llama al constructor (claim 494) |

**Trampa medida y corregida:** `T042Z` se clava por el país de la **sociedad que paga** (`T001-LAND1`), no por el del banco casa. UNES es francesa, así que sus métodos resuelven contra `LAND1='FR'` aunque el banco esté en Egipto. Usando el país del banco, `CIT19` salía con 0% de cheque cuando es el **100%**.

### Clasificación

```
cheque > 50%          -> PAPEL - no emite fichero
doméstico >= 80%      -> DOMÉSTICO (país)
doméstico <= 20%      -> CROSS-BORDER
resto                 -> MIXTO
```

---

## 3. El caso que lo motivó, en una línea

```
python brain_v2/house_bank_roles.py --country EG

CORREDOR -> beneficiarios con banco en EG   6.884 líneas
  SOG01   FR   93,1%   MIXTO                            PPC SÍ
  UNI01   IT    2,1%   MIXTO                            PPC no
  CIT19   EG    0,9%   PAPEL - cheque, sin fichero SAP  PPC no
```

El aviso vino del banco que mueve el **0,9%** del corredor, en cheque prenumerado — que no es ni RTGS ni CBFT, que es lo que el aviso vinculaba.

**El protocolo que esto establece:** ante un requisito de un banco, correr `--country <ISO2>` **antes** de diseñar nada. Si el que avisa no domina la fila, ésa es la primera pregunta al negocio, no la última.

---

## 4. Lo que el eje destapó: el 20% que captura y tira

Aplicando la misma clasificación a los nueve países con purpose code configurado (`--ppc-exposure`):

| País | Líneas | Renderiza | Doméstico | Otros | Sin banco casa |
|---|---:|---:|---:|---:|---:|
| AE | 3.323 | 79% | 0% | 4% | 18% |
| BH | 636 | 82% | 0% | 4% | 14% |
| CN | 9.916 | 81% | 0% | 4% | 15% |
| ID | 3.301 | 85% | 0% | 4% | 11% |
| **IN** | 9.220 | **70%** | 0% | **18%** | 12% |
| **JO** | 7.977 | 83% | **2%** | 4% | 12% |
| **MA** | 3.106 | 77% | **1%** | 9% | 14% |
| MY | 4.516 | 84% | 0% | 4% | 11% |
| PH | 5.404 | 83% | 0% | 4% | 13% |

**47.399 líneas capturadas, sólo el 80% renderiza.** Casi 9.500 pagos obligan al empleado a rellenar un código que se descarta.

### La asimetría estructural que lo causa

`u917` bloquea por el país del banco del **beneficiario**, sin mirar por dónde sale el dinero. El renderizado depende de por dónde sale. **Las dos mitades no coinciden.**

Y el caso más puro es el doméstico: **171 líneas** (`JO` 150 vía `SCB07`/`CIT26`, `MA` 21 vía `CIT06`) son pagos **de un banco casa local a un beneficiario local** — doméstico jordano, doméstico marroquí. El control los bloquea si falta el código; el banco local nunca lo habría pedido; y no renderiza, porque el banco casa no está en FR.

> Se obliga a rellenar un campo cross-border en un pago que no cruza ninguna frontera, y luego se tira.

**El arreglo no es técnico ni urgente**, pero es una decisión que debería tomarse a propósito: o `u917` mira también el país del banco casa, o se acepta la sobre-captura sabiendo cuánta es.

---

## 4b. Tres capas, tres ejes — y la aprobación no mira el banco

| Capa | Se clava en | Consecuencia |
|---|---|---|
| **Captura** — `u917` bloquea | el país del banco del **BENEFICIARIO** | no mira por dónde sale el dinero |
| **Fichero** — BAdI → árbol DMEE | el país de **NUESTRO** banco casa (`FPAYHX-UBISO`) | sólo la familia FR despacha purpose codes |
| **Aprobación** — BCM | `ZBUKR` + techo de importe | **el banco casa no entra** |

Medido sobre las tablas BCM del Gold DB: `bcm_grouping_rule_selop` decide por `ZBUKR` (29), `DORIGIN` (29), `ZLAND` (10), `ZBNKS` (6), `AMT_RULECU` (6), `ZIBAN`, `RZAWE`, `KUNNR`, `DTAWS`, `LIFNR`, `CRVAL`; y `bcm_node_selection_criteria` por `RULE_ID` (23), `ZBUKR` (22), `MAXPAYAMT_RULECURR` (22). **`HBKID` no aparece en ninguna de las dos.**

BCM sí distingue el **destino** —usa `ZLAND` y `ZBNKS` para agrupar el lote— pero **quién aprueba** se decide por sociedad e importe. Un pago doméstico desde una oficina de campo y uno transfronterizo desde el hub de París siguen la misma lógica si coinciden sociedad y banda de importe.

Puede ser política deliberada y defendible —el riesgo se mide por importe, no por corredor— pero **no está escrito en ningún sitio**, así que no consta que se haya decidido a propósito. `claim 532`

## 4c. La topología: hub, regional, oficina de campo

Un concentrador no se distingue de una cuenta de oficina por el **volumen** sino por la **diversidad de destinos**.

| Tipo | Criterio | Ejemplos |
|---|---|---|
| **HUB GLOBAL** | ≥150 destinos | `SOG01` FR — 209 países, 1.925.633 líneas, 2 sociedades |
| **HUB REGIONAL** | 15–149 destinos | `UNI01` IT 148 · `DEU01` DE 109 · `CIT01` BR 87 · `CIT04` US 76 |
| **LOCAL (oficina de campo)** | un destino ≥70% y doméstico ≥60% | `BRA01` BR 99% · `ECO02` CI 98% · `CIT07` CD · `ECO04` ML · `CIT05` HT · `BLN01` SD |
| **CORREDOR ESTRECHO** | <15 destinos, ninguno dominante | cuentas acotadas o en desuso |
| **SIN DESTINO CONOCIDO** | 0 destinos resolubles | `WEL01` · `CHA01` · `SCB14` · `DNB01` |

**Los locales pagan doméstico entre el 81% y el 99%** — son exactamente los pagos que ningún requisito cross-border debería tocar.

Y `SIN DESTINO CONOCIDO` hay que nombrarlo en vez de esconderlo: sus beneficiarios no tienen registro en `LFBK`, así que **no es que no paguen, es que no lo vemos**, y ningún control que dependa del país del banco del beneficiario puede actuar sobre ellos.

> Página legible y generada: [`companions/unesco_bank_operation_design.html`](../../../companions/unesco_bank_operation_design.html) — construida por `scripts/build_bank_operation_design.py`, paso 2e del rebuild.

## 5. Dónde más aplica este eje — la cadena

El rol del banco es el **driver**; de él cuelgan los medios y los extractos:

```
BANCO CASA (rol operativo)  <- este documento
   |
   +-- ALTA Y CONFIGURACIÓN ......... house_bank_configuration.md   (AS-DESIGNED)
   +-- PAISAJE DE PAGO .............. payment_full_landscape.md
   +-- MEDIO DE PAGO ................ e2e_vendor_payment_to_medium.md
   |      método -> T042Z FORMI -> árbol DMEE -> fichero (o cheque, y entonces no hay fichero)
   +-- PURPOSE CODE ................. ../Procurement/p2p_purpose_of_payment_e2e.md
   |      cross-border sí, doméstico no
   +-- DIRECCIÓN ESTRUCTURADA ....... ../Payment/citi_dbtr_pstladr_format_analysis.md
   |      el árbol CITI ramifica por UBISO ∈ {US,CA,PR} -> el MISMO eje
   +-- EXTRACTO BANCARIO ............ bank_statement_ebs_architecture.md
```

### ⚠️ Aplicación inmediata: `INC-PSTLADR-NOV2026`

La rama de dirección estructurada del árbol CITI **ya ramifica por `FPAYHX-UBISO`** — el país de nuestro banco casa. Es exactamente el mismo eje, con un deadline vivo el **2026-11-14**.

La pregunta que no hicimos para Egipto hay que hacerla aquí **antes**, y ahora hay herramienta:

> ¿Qué banco exige la dirección estructurada, para qué corredor, y ese banco domina ese corredor?

No se afirma aquí que el alcance esté mal — se afirma que **la pregunta debe hacerse explícitamente y no está hecha**.

---

## 6. Cómo re-derivarlo

```bash
python brain_v2/house_bank_roles.py                  # censo completo
python brain_v2/house_bank_roles.py --country EG     # quién sirve un corredor
python brain_v2/house_bank_roles.py --bank CIT19     # ficha de un banco
python brain_v2/house_bank_roles.py --ppc-exposure   # capturado vs renderizado
```

Se regenera en el paso 2d de `rebuild_all.py`. Artefacto consultable: `brain_v2/house_bank_roles.json`.

## 7. Límites de esta medida, dichos explícitos

1. **`renderiza` acota por arriba.** Asume que un banco casa FR llega al árbol CGI; uno que pague por método de cheque tampoco produce fichero. La cobertura real es igual o menor.
2. **`sin banco casa`** son líneas de `REGUH` sin `HBKID`. Se cuentan a propósito: excluirlas subía la cobertura publicada del 80% al 92%. Un total correcto con un desglose incompleto es peor que no tener desglose.
3. **`LFBK` sin `BVTYP`.** El join toma cualquier banco del proveedor; un proveedor con varias cuentas puede contarse en más de un corredor. Afecta a los márgenes, no al orden de magnitud.
4. **La clasificación doméstico/internacional del §1 se lee del TEXTO del método.** Es la intención declarada por quien lo configuró, no una propiedad que SAP imponga. Coincide con el comportamiento medido, pero son dos cosas distintas y conviene no fundirlas.

---

**Regla que gobierna esto:** `feedback_a_regulatory_notice_binds_a_channel_not_a_country` (CRITICAL).
**Relacionado:** [[house_bank_configuration]] · [[payment_full_landscape]] · [[bank_statement_ebs_architecture]] · [[p2p_purpose_of_payment_e2e]] · [[citi_dbtr_pstladr_format_analysis]]
