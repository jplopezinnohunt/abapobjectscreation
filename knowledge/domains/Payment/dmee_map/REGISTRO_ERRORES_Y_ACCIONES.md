# Dirección estructurada ISO 20022 — registro de errores y acciones

**Tema de trabajo** · deadline **14-11-2026** · dominio Payment · abierto 2026-08-19
Incidente: `INC-PSTLADR-NOV2026` · claims 499–516 · drill: `python brain_v2/load_domain.py dmee`

Todo lo de aquí está **medido**, no supuesto, y cada línea dice contra qué se midió. Lo que se
descartó lleva la medida que lo descartó, para que no se reabra.

---

## A. CONFIGURACIÓN — los árboles DMEE

| # | Error posible | Estado | Acción |
|---|---|---|---|
| A1 | **CGI `CdtrAgt`: orden ISO roto** (`Ctry` primero) → el rechazo del 21-jul | ✅ **RESUELTO** | Hecho. v5 y un pago real pasan XSD y reglas, hoy y en modo noviembre |
| A2 | **SEPA `Dbtr`: orden ISO roto** (`Ctry` antes de `CtrySubDvsn`), latente | ✅ **RESUELTO** | Hecho. `ORDER=0` en los 7 árboles vivos |
| A3 | **`REACT_LEV` apagado en los 1.364 nodos** → una dirección parcial sale sin que nada avise; el error aparece días después en el portal del banco | 🔴 **ABIERTO** | Encender **nivel 1 (aviso)** en los nodos de dirección. Nivel 2 bloquearía la corrida: no se activa sin decisión de Tesorería |
| A4 | **SEPA `Dbtr/StrtNm` mapea `FPAYHX-AUST2`** = *"Issuer on the Form"*, y es el único de sus 8 hermanos que no va por `Y_FI_DMEE_ADR` | 🟡 **REVISAR** | Comprobar qué emite de verdad contra un fichero SEPA generado. Huele a resto de una prueba |
| A5 | Híbridos `estructurado + AdrLine` en CITI `UltmtCdtr` y SEPA `Dbtr` | ⚪ **INERTE — NO TOCAR** | Los `AdrLine` están apagados con `campo <> mismo campo`, que nunca es cierto. **Trampa**: si alguien "arregla" esa condición, enciende el híbrido y Citi falla el pago |
| A6 | CITI `UltmtCdtr #2` es rama muerta (misma condición imposible) | ⚪ **INERTE — NO TOCAR** | Igual que A5 |
| A7 | **Un nodo puede pasar a `NODE_TYPE=TECH` al editarlo** y deja de emitir etiqueta con el mapping intacto | 🟢 **MECANIZADO** | Pasó con `Ctry` de CGI y borró el dato en silencio. `dmee_tree_map.py` ya lo marca con la clase `TECNICO` |

## B. DATO MAESTRO — proveedores

| # | Error posible | Medida | Acción |
|---|---|---|---|
| B1 | **Proveedores sin `CtrySubDvsn`** — Citi lo documenta *"both fields are mandatory"* en su Línea 2 | **8.149** pagados por fichero, en **todos** los rails (CITI 4.357 · CGI 4.114 · SEPA 3.354 · ICTP 3.354) | 🔴 Cargar `ADRC-REGION`. Empezar por los **399 listos** de US/CA (`FIXB_1_CARGAR_region.csv`) |
| B2 | **Código postal comodín** (`99999-9999`, `Z9Z 9Z9`, `00000`) → derivar la región produce un estado **falso** con toda la confianza | **68** proveedores, 64 de ellos `VS9*` | 🟡 Preguntar. **No derivar**: `DISERA Laurel Anne` vive en New York y su `99999` cae en el rango de Alaska |
| B3 | **País incoherente**: `Tim FRANCIS` paga como US y su ficha ADRC dice `FR`, París | 1 proveedor | 🟡 Mirar aparte — no es un problema de región |
| B4 | Región **mal colocada**, dentro de la ciudad (`Montreal Quebec`, `Holland, MI`) | 159 de los 467 US/CA | ⚪ **BAJA**: Citi concatena `TwnNm`+coma+`CtrySubDvsn`, así que producen la **misma** Línea 2 que la versión partida. Inocuo para Citi; importa para conformidad ISO general |

## C. DATO MAESTRO — empleados

| # | Error posible | Medida | Acción |
|---|---|---|---|
| C1 | ~~818 empleados sin ciudad no podrán cobrar~~ | Cobran **sólo por cheque** (métodos `O` y `U`, `XSCHK='X'`). **Cero** van en fichero ISO | ⚫ **DESCARTADO.** Un cheque no lleva `<PstlAdr>` |
| C2 | **Empleados en fichero sin código postal** | **1.127 de 2.704 (41%)** | 🟡 **DECIDIR.** `PstCd` es *"strongly recommended"* para SocGen y condicional para Citi — no es obligatorio |
| C3 | `FI-AR`: un único receptor con 131.530 líneas (93%) sin ciudad | 1 ficha | 🟡 Anomalía barata de mirar, no debería quedar colgando |

## D. DATO MAESTRO — bancos

| # | Error posible | Medida | Acción |
|---|---|---|---|
| D1 | ~~Campaña de limpieza de `BNKA`: 77% de ciudades sucias en 2.886 bancos~~ | En CGI **8.419 de 8.419 pagos llevan BIC** (100%), y SocGen: *"if filled in, name and address are ignored"* | ⚫ **DESCARTADO** para CGI. No gastar ahí |
| D2 | **Agentes sin BIC** — ahí la dirección **es** la identificación | **898** pagos en CITI (8%) | 🟡 Único sitio donde la dirección de banco importa de verdad. Acotar y mirar |
| D3 | `BNKA` **no tiene campo de código postal** → `PstCd` de un agente no es emitible por la vía del árbol, se limpie lo que se limpie | estructural | ⚪ Conocerlo. La única vía sería `BNKA-ADRNR → ADRC` + exit, y `ADRNR` está poblado en **20 de 1.387.671** |

## E. DEFECTOS QUE NINGÚN VALIDADOR VE

| # | Error posible | Medida | Acción |
|---|---|---|---|
| E1 | **Dato semánticamente falso, estructuralmente perfecto**: `TwnNm='CAMBRIDGE CB23BZ'`, `'NEW YORKNY 10167'` — ciudad + código postal en un campo | 77% de los bancos usados | ⚪ Sólo lo arregla el dato maestro. En CGI da igual: hay BIC |
| E2 | Ciudad con el estado dentro en las **partes** (`WASHINGTON, DC`, `Holland, MI`) | 113 de 11.185 pagos CITI (1%) | ⚪ Inocuo para Citi por la concatenación |

## F. PROCESO

| # | Error posible | Estado | Acción |
|---|---|---|---|
| F1 | **No se valida antes de enviar.** El fichero sale, Tesorería lo sube al portal, y el error vuelve días después. Costó 7 semanas y dos rechazos | 🔴 **ABIERTO** | Meter `pain001_address_validator.py` en el ciclo, **antes** del envío. Existe y ya reprodujo offline el mensaje literal del banco |
| F2 | Medir calidad de dirección **sin mirar el canal** produce incidentes inexistentes | 🟢 **REGLA** | Todo corte sobre `REGUH` se parte por `DORIGIN` (quién cobra) **y** por `T042Z` (`FORMI` = va en fichero, `XSCHK` = cheque). Pasó dos veces hoy |
| F3 | Tomar "hoy lo aceptan" como conformidad | 🟢 **REGLA** | `feedback_grace_period_acceptance_is_not_evidence`. Con deadline normativo se mide contra el texto publicado y se usa `--after-nov2026` siempre |

---

## Lo siguiente, por orden

1. **B1** — cargar los 399 de US/CA. Es el único frente con alcance, fecha y fichero listo.
2. **F1** — meter el validador en el ciclo antes del envío. Barato y evita el próximo rechazo.
3. **A3** — `REACT_LEV` nivel 1, para enterarnos en la corrida y no en el portal.
4. **B2 / C2 / D2** — las tres decisiones que necesitan que alguien responda, no que alguien programe.

## Herramientas dejadas

| Herramienta | Para qué |
|---|---|
| `Zagentexecution/quality_checks/dmee_tree_map.py` | El mapa de los 7 árboles vivos: estructura, mapping, exits, condiciones y configuración PPC detrás. Genera `DMEE_CONFIG_POR_FORMATO.md` |
| `Zagentexecution/quality_checks/pain001_address_validator.py` | Valida un fichero: XSD (autoridad) + reglas de banco, con modo `--after-nov2026` y la regla condicional del BIC |
| `Zagentexecution/quality_checks/structured_address_readiness.py` | Quién no va a poder cobrar: nominal, priorizado por volumen, partido por `DORIGIN` |
