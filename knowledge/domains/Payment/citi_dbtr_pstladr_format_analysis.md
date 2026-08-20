# Formato `/CITI/XML/UNESCO/DC_V3_01` — Dbtr `PstlAdr`: estructura, defectos y compliance

> ⚠️ **El mismo eje, y con deadline vivo.** La rama de dirección estructurada de este árbol ramifica por `FPAYHX-UBISO`, el país de NUESTRO banco casa — exactamente el eje doméstico/internacional que documenta [`../Treasury/house_bank_operating_roles.md`](../Treasury/house_bank_operating_roles.md). Antes de dimensionar `INC-PSTLADR-NOV2026`, correr `python brain_v2/house_bank_roles.py --country <ISO2>` y preguntar qué banco lo exige y si domina ese corredor. Es la pregunta que no se hizo para Egipto.

**Formato (DMEE TREE_ID / FORMI):** `/CITI/XML/UNESCO/DC_V3_01`
**Fuente de datos:** **P01 (PRODUCCIÓN)** — `SYSID P01`, host `HQ-SAP-P`, RFC read-only (SNC/SSO).
- Uso del formato: `REGUT.DTFOR` + `DFPAYG.FORMI` (P01, toda la historia 2019-2026).
- Estructura del árbol: `DMEE_TREE_NODE` / `DMEE_TREE_COND` (D01 V000; idéntico en V001).
**Verificado:** 2026-06-15. **Anclas:** [[reference_zsapfpaym_replay_and_citi_ubiso]] · [[identify_payment_run_from_medium]].

> NOTA de fuente: el análisis se hizo primero en **V01 (validación)** pero V01 es un SUBSET (~52%: 2,301 vs 4,431 medios). La conclusión se **re-verificó en P01** y es idéntica. Para cifras de producción, usar P01.

## 1. Quién paga por este formato (P01, toda la historia)

El formato CITI se paga **EXCLUSIVAMENTE** por 3 países de banco (clearing) — verificado año por año, sin excepción:

| BANKS (país banco) | Medios | Ente (ZBUKR) | House bank | Nodo Dbtr | Dirección |
|---|---|---|---|---|---|
| **US** | 1,870 | UNES | CIT04 (USD) | #3 | ✅ completa |
| **CA** | 772 | UNES | CIT21 (CAD) | #3 | ✅ completa |
| **BR** | 1,789 | UBO | CIT01 (Worldlink) | #4 | ❌ **incompleta** |
| **TOTAL** | **4,431** | UNES 2,147 · UBO 1,789 · UIS 495 | | | |

**Cero otros países de banco** (no GB/CH/etc.) en 8 años. `UBISO` = `FPAYHX-UBISO` = data element **`INTCA`** (ISO-2). 1 anomalía: 1 grupo `UNES/SOG01` ruteó a CITI (misroute, no produjo medio con país distinto).

### Por año (P01) — foco 2024-2026

| Año | US #3 ✅ | CA #3 ✅ | BR #4 ❌ | Total |
|---|---|---|---|---|
| 2024 | 361 | 202 | 526 | 1,089 |
| 2025 | 334 | 193 | 472 | 999 |
| 2026 | 139 | 82 | 201 | 422 |
| **TOTAL** | **834** | **477** | **1,199** | **2,510** |

Contexto histórico: CITI arrancó US-only (completo) en 2019-2020; CA y BR entran en 2022; el flujo
BR/Worldlink (incompleto, #4) creció y se estabilizó en ~48% del volumen CITI. Solo US/CA/BR en los 8 años
(2019-2026), cero otros países de banco. (Unidad: medios/archivos; pagos individuales ~16× — 2024: 8,472 pagos BR.)

## 2. Estructura del Dbtr — 4 nodos `PstlAdr` (D01)

El `Dbtr` (N_6528960200) tiene 4 `PstlAdr`. Todos sourcean del exit `FI_CGI_DMEE_EXIT_W_BADI`, que arma la dirección del **ente pagador** desde `T001(BUKRS=i_fpayh-zbukr) -> ADRC` (NO es fija: UNES→Paris, UBO→Brasil, UIS→Montreal).

> ⚠️ **CORRECCIÓN 2026-06-17 (2 pasadas):** (a) probe `probe_pstladr_nodes_full.py` halló la condición de #1 en
> 2-letras (la versión vieja decía 3-letras); (b) el **XML BR real** (replay D01 20210924/UBO) probó que **#1 NO
> renderiza** (Dbtr trae 1 solo `PstlAdr`) → **#1 está DESACTIVADO** (el flag no vive en `DMEE_TREE_COND`, por eso
> leer solo la condición engañó en la pasada (a)). Versión activa = **V000** (confirmado usuario). Tabla real abajo.

| # (orden árbol) | NODE_ID | Tipo | Condición (V000) | Dispara | Estado |
|---|---|---|---|---|---|
| #1 | N_1531351640 | no-estruct legacy | `<> US AND <> CA AND <> PR AND <> ''` (2-letras) **pero NODO DESACTIVADO** | nunca (off) | **apagado** — no renderiza (probado XML BR real). Sin acción |
| #2 | N_1905437260 | **estructurado** | `<> US AND <> CA AND <> PR` (2-letras) | **BR/resto** | **ACTIVO** — PstCd/TwnNm con `=SE`→suprimidos = **D-2** |
| #3 | N_4078824850 | no-estruct (3 AdrLine) | `= USA OR CAN OR PRO` (3-letras → nunca) | nunca | muerto; higiene opcional |
| #4 | N_5197213060 | **estructurado** | `= US OR CA OR PR` (2-letras) | **US/CA/PR** | **ACTIVO** — completo ✅ |

**Resultado real por destino (PROBADO en XML):** US/CA/PR → #4 → completo ✅. **BR → solo #2** (#1 apagado) →
**1 `<PstlAdr>` sin PstCd/TwnNm** = **D-2**. **NO hay duplicado** (D-1 era un falso positivo de mi re-análisis por
condición; el "D-1 resuelto" original era correcto).

## 3. Defectos encontrados

### D-1 (RESUELTO — confirmado por output real 2026-06-17) — NO hay duplicado
El nodo legacy #1 (`N_1531351640`) está **desactivado** y no renderiza: el XML BR real trae **un solo `<PstlAdr>`** en
el Dbtr (el del #2 estructurado). Una pasada intermedia (2026-06-17) lo marcó erróneamente "abierto/vivo" por leer solo
`DMEE_TREE_COND` (la condición sigue siendo `<>US/CA/PR` pero el nodo está apagado a nivel nodo, no por condición).
**Lección:** para saber si un nodo DMEE renderiza, el output real > la condición. _(texto previo conservado abajo como histórico)_
<!-- Histórico (re-análisis intermedio del 2026-06-17, REFUTADO por el XML BR real): se afirmó que #1 seguía VIVO y
duplicaba. El output real probó que NO (1 solo PstlAdr). Conservado solo como registro del error. -->
Regla útil (apagar un nodo): `= <valor inexistente>` o `campo <> mismo_campo`; NUNCA `<> <valor inexistente>` (siempre prendido).

### D-2 (PROBADO pero SIN IMPACTO — config se deja, decisión usuario 2026-06-17)
En el nodo estructurado de "resto" **`N_1905437260`** (el que dispara para BR), los tags hijo `PstCd` y `TwnNm` tienen
condición `FPAYHX-UBISO = 'SE'` → solo emiten para Suecia. Como **SE nunca ocurre** (0 pagos), `PstCd`/`TwnNm` se
**eliminan siempre** para no-US/CA/PR. **CONFIRMADO end-to-end** en el XML BR real (replay D01 20210924/UBO): el Dbtr
*UNESCO Brazilian Office* salió con `StrtNm·BldgNb·CtrySubDvsn·Ctry` pero **sin `PstCd` ni `TwnNm`**.
**DECISIÓN:** **sin impacto operativo** — el flujo BR/Worldlink es **doméstico** (BRL, beneficiarios locales vía bancos
BR), **no** cross-border SWIFT → CBPR+ no aplica; los 83K pagos clearean OK. **Se deja la config como está.** El framing
previo "compliance / riesgo de rechazo" estaba sobredimensionado para este flujo doméstico. Fix futuro (si se decide):
quitar `=SE` (zero-riesgo, no hay SE; `ADRC` de UBO ya trae calle/región → postal+ciudad saldrían).

**Impacto (P01):** afecta **exclusivamente el flujo BR/UBO Worldlink** = **1,789 medios / ~40% del volumen CITI histórico** (~48% en 2024-2026). Esos pagos emiten Dbtr sin código postal ni ciudad. `<TwnNm>` es **obligatorio** ISO 20022 / CBPR+ → riesgo de rechazo bancario.

| Caso | Nodo | Emite | Completo |
|---|---|---|---|
| US, CA (PR=0) | #3 | StrtNm·BldgNb·**PstCd·TwnNm**·CtrySubDvsn·Ctry | ✅ |
| BR (todo lo no-US/CA/PR) | #4 | StrtNm·BldgNb·CtrySubDvsn·Ctry — **SIN PstCd, SIN TwnNm** | ❌ |
| SE (0 pagos) | #4 | todo (gracias al `=SE`) | nunca ocurre |

**Fix propuesto:** en #4, quitar el `= SE` de `PstCd` y `TwnNm` (dejarlos incondicionales como en #3) → así BR/UBO emite dirección completa. Confirmar antes que el exit los llene (que no queden tags vacíos).

## 4. Estado Dbtr `PstlAdr` — los 4 árboles UNESCO (D01 V000, 2026-06-15)

Escaneo cruzado del subárbol Dbtr de los 4 formatos:

| Árbol | Nodos | Dbtr PstlAdr | Mecanismo | Estado |
|---|---|---|---|---|
| `/CITI/XML/UNESCO/DC_V3_01` | 639 | **4** (2 viejos no-estruct + 2 estruct) | cond `UBISO` US/CA/PR vs resto; `PstCd`/`TwnNm` con `=SE` | D-1 resuelto (kill-switch); **D-2 abierto** (BR/UBO sin PstCd/TwnNm) |
| `/SEPA_CT_UNES` | 111 | **1** estructurado | **sin condición** (siempre emite) | ✅ **limpio** |
| `/CGI_XML_CT_UNESCO` | 631 | **1** estructurado | tags gated por `<-PstlAdr_More_Nodes> = 'SPACE'` (flag **dinámico** del exit) | ✅ **benigno** (≠ bug `=SE`) — confirmar con replay |
| `/CGI_XML_CT_UNESCO_1` | 632 | **1** (twin de CGI, mismo NODE_ID) | idem | ✅ idem |

**Conclusión (revisada 2026-06-17):** CITI tenía el bug del `=SE`. **SEPA limpio.** **CGI NO tiene el mismo bug:** su
gate `<-PstlAdr_More_Nodes> = 'SPACE'` compara contra un **valor DINÁMICO calculado por el exit** (`FI_CGI_DMEE_EXIT_W_BADI`),
NO contra una constante muerta como `=SE`. Es el patrón **estándar SAP de overflow**: si la dirección **cabe** estructurada →
flag=SPACE → emite estructurado (caso normal); solo si **desborda** → no-estructurado. Para direcciones normales **emite
estructurado**. La diferencia con `=SE`: `=SE` siempre suprime (Suecia nunca ocurre); el flag CGI suprime solo en overflow real.

**Verificación empírica (lección "output real > condición"):** replay CGI D01 **20250326/T0001/100** (FORMI
`/CGI_XML_CT_UNESCO`, 2 pagos UNES/SOG01 FR/USD) → mirar `<Dbtr><PstlAdr>`: se espera completo (Place de Fontenoy·75007·
PARIS·FR). Si completo → gate benigno confirmado, **nada que ajustar en CGI**.

## 5. Cdtr (beneficiario) — 2 `PstlAdr` (formato `/CITI/XML/UNESCO/DC_V3_01`, D01 V000)

A diferencia del Dbtr (4 nodos con defectos), el **Cdtr está SANO**. 2 `PstlAdr` bajo `Cdtr N_3576433990`
(el otro nodo `Cdtr N_3255409070` tiene 0):

| # | NODE_ID | Condición (`FPAYHX-UBISO`) | Tipo | Dispara para |
|---|---|---|---|---|
| 1 | N_2368849090 | `<> RU AND <> JP AND <> US AND <> CA AND <> PR` | **híbrido** (estruct + 3× `AdrLine` de `FPAYH-ZNME2/3/4`, cond `<> ''`) | el resto (= **BR** para CITI) |
| 2 | N_1496761000 | `= US OR CA OR PR` | **estructurado puro** (sin AdrLine) | US/CA/PR |

Fuentes de tags: `BldgNb` ← exit `/CITIPMW/V3_GET_CDTR_BLDG`; `Ctry` ← `FPAYHX-ZLISO` (país del **beneficiario**,
no UBISO); `StrtNm`/`PstCd`/`TwnNm`/`CtrySubDvsn` = contenedores (poblados por exits CITIPMW).

**Veredicto Cdtr (vs Dbtr):**
- ✅ Códigos **2-letras** correctos (RU/JP/US/CA/PR) — NO tiene el bug 3-letras del Dbtr.
- ✅ **No hay duplicado** (#1 y #2 mutuamente excluyentes) ni supresión `=SE`.
- ⚠️ **Split legítimo**: para BR (#1) el Cdtr sale **híbrido** (estruct + AdrLine de nombres); para US/CA (#2)
  **estructurado puro**. Acá el condicional SÍ tiene sentido (la dirección del beneficiario varía por destino).
- ⚠️ **Hueco RU/JP (muerto)**: ni #1 (excluye RU/JP) ni #2 (solo US/CA/PR) cubren `UBISO=RU` o `JP` → si
  ocurriera, Cdtr sin `PstlAdr`. Pero UBISO para CITI es solo US/CA/BR → nunca pasa (defensivo, como PR/SE).

**Contraste CITI Dbtr vs Cdtr:** Dbtr = 4 PstlAdr, bug 3-letras, `=SE` (D-2 compliance abierto). Cdtr = 2
PstlAdr limpios, 2-letras, sin supresión → **sano** (solo el hueco RU/JP teórico). El problema de compliance
del formato es **solo del Dbtr**, no del Cdtr.

### XML tags del Cdtr (recursivo) — #1 vs #2

Estructura interna **idéntica** entre #1 y #2, salvo que #1 agrega 3 `<AdrLine>` al final:

| Tag XML | #1 (BR/resto) | #2 (US/CA/PR) | Fuente / lógica interna |
|---|---|---|---|
| `<StrtNm>` | ✅ | ✅ | PO Box (`ZPFAC`≠'') → `"PO BOX"`+`ZPFAC`; si no → `Housenum`+`Street` (exit `V3_CGI_CRED_STREET`) |
| `<BldgNb>` | ✅ | ✅ | exit `V3_GET_CDTR_BLDG` |
| `<PstCd>` | ✅ | ✅ | `POBoxPc` (`ZPST2`) ó `CityPc` (exit `V3_POSTALCODE`) |
| `<TwnNm>` | ✅ | ✅ | PO Box/City × payroll/vendor (exit `V3_*_CRED_CITY` ó `ZORT1`) |
| `<CtrySubDvsn>` | ✅ | ✅ | exit `V3_CGI_CRED_REGION` (vendor) ó `ZREGI` (payroll) |
| `<Ctry>` | ✅ | ✅ | `FPAYHX-ZLISO` |
| `<AdrLine>` ×3 | ⚠️ overflow de NOMBRE (`ZNME2/3/4`) | ❌ | **única diferencia #1 vs #2** |

**Qué es el `<AdrLine>` del Cdtr #1**: `ZNME1/2/3/4` = data element `FPM_NAME`, **"Name of the Payee"** (NO
dirección). El `<Nm>` toma `ZNME1`; el **overflow del nombre** (nombre > 40 chars, sufijos tipo `LTDA`) se
desborda a `ZNME2/3/4` → `<AdrLine>` (cond `<>''`). Es un workaround de overflow de nombre, **semánticamente
name-in-address**. Población real (BR/UBO 2024-26, 82,392 pagos): `ZNME2`≠'' = **3,913 (4.7%)**, `ZNME3` 0.2%,
`ZNME4` 0%. → en **95.3% el AdrLine no sale → #1 ≡ #2** (estructura pura); en 4.7% lleva nombre en tag de dirección.

Lógica interna (igual en ambos): maneja **PO Box vs calle** (`ZPFAC`) y **payroll vs vendor** (nodo `HR='P'` →
campos directos `ZORT1/ZREGI/ZPFOR`; si no → exits CITIPMW). Cada tag estructurado tiene varias ramas pero
**siempre emite una** → ningún tag queda vacío → **sin hueco de compliance** (a diferencia del Dbtr `=SE`).

Impacto real: US/CA → #2 (estructurado puro); BR → #1 (estructurado; +AdrLine solo si nombre largo, 4.7%). Ambos
**completos**. RU/JP = hueco muerto (UBISO nunca RU/JP).

> 🔑 **IMPORTANTE (usuario, 2026-06-15) — solución al overflow de nombre:** para este caso (nombre del
> beneficiario > 40 chars que se desborda de `ZNME1` a `ZNME2/3/4` → `<AdrLine>`) **se creó una FUNCIÓN en
> OTRO MODELO que COMBINA los nombres** (`ZNME1..4`) en uno solo. _Detalle a completar:_ nombre de la función ·
> en qué modelo/sistema · qué produce (¿un único `<Nm>` concatenado? ¿elimina el name-in-address del AdrLine?).
> Esto resuelve el name-in-address semántico del Cdtr #1.

**Volumen por nodo (P01, 2024-2026)** — mismo split por `UBISO` que el Dbtr:

| Nodo Cdtr | Dispara | Tipo | Pagos | Medios |
|---|---|---|---|---|
| #2 N_1496761000 | US+CA | estructurado puro | **73,529** (US 65,838 + CA 7,691) | 1,311 |
| #1 N_2368849090 | BR | estructurado + 3 AdrLine | **82,392** | 1,199 |
| | | Total | 155,921 | 2,510 |

≈ 47% estructura pura (US/CA), 53% híbrido (BR/Worldlink). Ambos completos.

## 6. Cdtr `<PstlAdr>` — detalle de cada XML tag (ambos nodos, D01 V000)

Los 2 nodos (#1 N_2368849090 BR/resto, #2 N_1496761000 US/CA/PR) tienen **estructura interna idéntica**;
#1 sólo agrega los 3 `<AdrLine>`. Cada tag estructurado es un contenedor con ramas internas.

**Nodos técnicos que gobiernan la lógica:**
- `HR` (HR_Payment) ← `FPAYH-LAUFI` ("Additional Identification"=run id): `HR='P'` → **payroll** vs vendor.
- `ZPFAC` ("PO Box") → **apartado postal vs calle**.
- `HOUSENUMBER` ← `FPAYHX-REF02` (buffer user-defined). `XSCHK` ("Is a Check Created?") → rama de cheque.

| Tag XML | #1 (BR/resto) | #2 (US/CA) | Fuente / lógica interna |
|---|---|---|---|
| `<StrtNm>` | ✅ | ✅ | PO Box → `"PO BOX"`+`ZPFAC`; calle → `Housenum`(REF02) + `Street`(exit V3_CGI_CRED_STREET) |
| `<BldgNb>` | ✅ | ✅ | exit `V3_GET_CDTR_BLDG` |
| `<PstCd>` | ✅ | ✅ | PO Box → `ZPST2` ("PO Box Postal Code"); normal → exit `V3_POSTALCODE` |
| `<TwnNm>` | ✅ | ✅ | payroll → `ZPFOR`/`ZORT1`; vendor → exits; PO Box/City según `XSCHK`/`HR` |
| `<CtrySubDvsn>` | ✅ | ✅ | vendor → exit `V3_CGI_CRED_REGION`; payroll → `ZREGI` ("Regional code of payee") |
| `<Ctry>` | ✅ | ✅ | `FPAYHX-ZLISO` ("Country ISO code", 2 chars) |
| `<AdrLine>` ×3 | ✅ ← `ZNME2/3/4` | ❌ | **"Name of the Payee"** (overflow de NOMBRE) — **única diferencia** |

**Patrones transversales:** (1) **PO Box vs calle** (`ZPFAC`); (2) **payroll vs vendor** (`HR` desde `LAUFI`):
payroll usa campos directos (`ZPFOR/ZORT1/ZREGI/ZNME1`), vendor usa exits CITIPMW; (3) **cheque** (`XSCHK`) en
TwnNm. La **única diferencia #1 vs #2** = los 3 `<AdrLine>` (nombre).

### Los 3 drivers — dónde y cómo afectan (máximo detalle)

| Driver | Qué es | Controla (tags/átomos) |
|---|---|---|
| **`ZPFAC`** ("PO Box", FPAYH) | apartado postal vs calle | **SOLO `<StrtNm>`**: `Housenum`(REF02)+`Street`(exit) si `ZPFAC=''`; `"PO BOX"`+`POBOXNUM`(=ZPFAC) si `ZPFAC<>''` |
| **`HR`** (=`FPAYH-LAUFI` offset0 len1; `'P'`=payroll) | payroll vs vendor | `<Nm>` (ZNME1 exit ↔ ZNME1_HR directo) · `<TwnNm>` (City exit ↔ ZORT1) · `<CtrySubDvsn>` (exit REGION ↔ ZREGI). Payroll = campos directos del empleado; vendor = exits CITIPMW |
| **`XSCHK`** ("Is a Check Created?", FPAYHX) | cheque vs transferencia | **SOLO `<TwnNm>`**: `POBoxCity`(exit PO_CITY) si `XSCHK='X'`; `City`(exit CRED_CITY) si no (`POCITY` vacío) |

**NO dependen de driver:** `<BldgNb>` (exit, siempre) · `<PstCd>` (POBoxPc=ZPST2 por **param `=2`**, CityPc=exit — NO ZPFAC) · `<Ctry>` (ZLISO, siempre) · `<AdrLine>` (ZNME2/3/4, cond `<>''`).

🔑 **Hallazgo:** el "PO Box" **NO** tiene un switch único — está fragmentado en **3**: `<StrtNm>` por `ZPFAC`,
`<TwnNm>` (ciudad) por `XSCHK`, `<PstCd>` (postal) por **param `=2`**. Y `HR` (payroll) corre en paralelo. Una
dirección con apartado activa sus 3 partes por 3 condiciones distintas → frágil/inconsistente.

**Realidad BR/UBO (P01):** los 3 drivers están todos en "default" → `HR` nunca `'P'` (LAUFI=`BUBO`/`00..B`,
nunca payroll), `ZPFAC` 0% (0/82,684 con PO Box), `XSCHK` no-cheque (método `R` Worldlink). → para BR la
dirección **siempre** sale por los exits vendor/calle/city. Las ramas payroll/PO-Box/cheque son defensivas
(otros flujos: nóminas, apartados, cheques — no ocurren en Citi/UBO). [US/CA podrían disparar alguna — no
verificado.]

## 7. Código fuente de los exits CITIPMW — la dirección sale de `ADRC` (maestro de vendor)

**Hallazgo (exits explorados a fondo, código en `extracted_code/FI/DMEE_full_inventory/CITIPMW_V3_*`):** los
tags estructurados del Cdtr NO sacan el valor de campos `Z*` — lo sacan del **maestro de dirección del vendor
`ADRC`**. Todos los `V3_*CRED_*` siguen la **misma jerarquía de 3 niveles**:
1. **One-time/CPD vendor** (`FPAYH-GPA1T='14'`) → `BSEC` (dirección tipeada al postear; clave de `DOC1R` → `READ_BSEC`).
2. **Vendor normal** → `ADRC` por `FPAYH-ZADNR` (nº dirección), **versión internacional** (`nation = FPAYHX-NATION`).
3. **Fallback** (solo HR `FPAYP-DOC2T='03'` / F111 `DOC2T='05'` / payment-request `FPAYH-DORIGIN='FI-AP-PR'`, si quedó vacío) → `FPAYH-Z*`.

| XML tag | Exit | One-time → BSEC | Vendor → ADRC (nation) | Fallback → FPAYH |
|---|---|---|---|---|
| `<StrtNm>` | `V3_CGI_CRED_STREET` | `BSEC-STRAS` | **`ADRC-STREET`** | `ZSTRA` |
| `<BldgNb>` | `V3_GET_CDTR_BLDG` | (skip) | **`ADRC-BUILDING`** | — |
| `<PstCd>` | `V3_POSTALCODE` | — | (lee FPAYH directo) | `ZPST2` (PO box) / `ZPSTL` |
| `<TwnNm>` City | `V3_EXIT_CGI_CRED_CITY` | `BSEC-ORT01` | **`ADRC-CITY1`** | `ZORT1` |
| `<TwnNm>` PObox | `V3_CGI_CRED_PO_CITY` | `BSEC-ORT01` | **`ADRC-PO_BOX_CTY`** | `ZPFOR` |
| `<CtrySubDvsn>` | `V3_CGI_CRED_REGION` | `BSEC-REGIO` | **`ADRC-REGION`** | `ZREGI` |
| `<Nm>` | `V3_EXIT_CGI_CRED_NAME` | `BSEC-NAME1` | **`ADRC-NAME1`** (+ `CTGYPURP='TRAD'` → busca doc reemplazo en `REGUP`) | `ZNME1` |
| `<Ctry>` | (sin exit) | — | — | `FPAYHX-ZLISO` directo |

**Implicaciones:**
1. La dirección del beneficiario viene del **maestro de vendor (LFA1→ADRC)**, **versión internacional** (`nation`) — NO de campos de pago. Esto importa: si el ADRC del vendor está incompleto, la dirección estructurada sale incompleta.
2. Los `Z*` (ZSTRA/ZORT1/ZREGI/ZNME1) son **fallback solo** para nómina/F111/payment-request, no para AP normal.
3. `<PstCd>` es la excepción: lee `FPAYH` (`ZPSTL`/`ZPST2`) directo, sin ADRC.
4. El branch tree-level `HR='P'` (payroll → `_HR` atoms directos) coincide con el fallback interno del exit (DOC2T='03') — payroll usa campos directos por ambas vías.

## 8. Resultado del test-tool Citibank (2026-06-26) — validacion externa

**Fecha de upload:** 2026-06-18. **Fecha de evaluacion:** 2026-06-26.

3 archivos subidos al validador oficial de Citibank:

| Archivo | Resultado |
|---|---|
| `xmlUNESCODVV3_BR.in` | **PASS** |
| `XMLUNESCODVV3_USALPAY_test.in` | **PASS** |
| `xmlUNESCODVV3_US.in` ("For US") | **FAIL** |

**Conclusion critica:** El FAIL del archivo US **NO fue por la direccion estructurada**. El contacto de Citi confirmo explicitamente que el fallo fue por un **campo de referencia de pago faltante** (`CtgyPurp/Prtry`, ver seccion 9). **La remediacion de direccion estructurada (D-1 kill-switch + analisis D-2) paso el validador del banco.** Evidencia TIER_1 = validador oficial del banco.

Claim: #265 (`brain_v2/claims/claims.json`).

## 9. CtgyPurp/Prtry en flujo US — DATO FALTANTE puntual, NO defecto de formato (corregido en P01)

**Fallo detectado:** Citibank test-tool 2026-06-26, archivo `xmlUNESCODVV3_US.in`.

| Campo | Valor |
|---|---|
| XPath | `PmtInf[1].CdtTrfTxInf[1].PmtTpInf[1].CtgyPurp[1].Prtry[1]` |
| Tipo | Data Validation |
| Country | TN |
| PIUID | 949 |
| Payment Method | WIRE |
| Trans.Ref | UNES0002000018 |
| Requerimiento Citi | AlphaNumeric, exactamente 11 chars (min=11, max=11), **Mandatory** |
| Valor ejemplo Citi | `/REF/0825/C` |
| Error | Value not present |

**Diagnostico CORREGIDO en P01 (2026-06-26, TIER_1) — el nodo SÍ se llena en produccion; el fallo es dato faltante, NO el formato.**

> ⚠️ Un diagnostico previo (sobre el arbol `/CGI_XML_CT_UNESCO` de **D01**) concluyo erroneamente que el nodo quedaba vacio por diseño (`CLEAR C_VALUE` en `CL_IDFI_CGI_DMEE_FALLBACK`). Eso es del arbol CGI/SocGen, **NO** del arbol CITI. Corregido leyendo el arbol correcto en **P01**.

En el **arbol CITI real de P01** (`DMEE_TREE_NODE` TREE_ID=`/CITI/XML/UNESCO/DC_V3_01`, version **000 = activa**, 610 nodos) el `CtgyPurp/Prtry` **SÍ esta mapeado a un campo runtime**:

| NODE_ID | TECH_NAME | MP_SC_TAB | MP_SC_FLD | REF_NAME | LEN |
|---|---|---|---|---|---|
| `N_6555567710` | `Prtry` | **FPAYHX** | **CTGYPURP_PRTY** | CPP | 35 |

La rama CITI usa una familia de campos `FPAYHX-*_PRTY` (todos len 35): `SVCLVL_PRTY` (SLP), `LCLINSTRM_PRTY` (LP), `PURP_PRTY`, **`CTGYPURP_PRTY` (CPP)**, `DLVRYMTD_PRTY`, `CDTR_ACCT_TP_PRTY`. El nodo `CtgyPurp/Prtry` **no tiene condicion propia** (DMEE_TREE_COND vacio para `N_6555567710`): se emite con el valor de `FPAYHX-CTGYPURP_PRTY`; si ese campo viene **vacio**, el elemento se suprime → Citi lo reporta como mandatorio ausente.

**Por tanto:** produccion llena el nodo normalmente. Prueba: **153 archivos US (UNES/US) en 2026, el ultimo HOY 2026-06-26** (`LAUFD=20260626/00002B`, USD 6,898,042.58, archivo `UNES_CITI_03XMLUSDDOM0919.in`), `STATUS` sin rechazo; histórico 1.884 medios desde 2019-07. **Si el formato rechazara siempre, no se pagaria nada — y se paga.** El FAIL del test-tool es un **caso puntual con `FPAYHX-CTGYPURP_PRTY` vacio** para ese pago (factura/run sin el dato) — consistente con la hipotesis de facturas incompletas al momento de simular.

**Pendiente (la verdadera pregunta abierta):** ¿quien llena `FPAYHX-CTGYPURP_PRTY` y desde que dato? Es un campo append custom poblado por un exit del medium (familia `CITIPMW V3` / Event 05), no extraido aun localmente (`grep CTGYPURP_PRTY` sobre `*.abap` = 0 hits). Hay que leer en P01 el exit registrado y su campo fuente (probable: indicador/campo del documento, como el patron PPC `REGUP-LZBKZ`). Eso confirma exactamente por que el caso de prueba salio vacio.

**Contexto critico — gap preexistente, NO regresion:** la especificacion funcional PPC v2.0 (M. Spronk), pagina 16, dice explicitamente: _"The development is only for the XML file of Societé Generale. If Citibank requires this, all the requirements and developments should be reviewed"_ (`Zagentexecution/analysis/payment_purpose_code_extracted.txt:1110-1111`). El PPC apunta a `RmtInf/Ustrd` e `InstrForCdtrAgt/InstrInf`, NO a `CtgyPurp/Prtry`. Este requerimiento de Citi es exactamente el gap de extension Citi que el spec PPC ya identifico como pendiente de revision.

Claims: #266 **SUPERSEDED** por el hallazgo P01 (el nodo NO esta vacio por diseño; mapea `FPAYHX-CTGYPURP_PRTY`) + #267 (scope SocGen-only, TIER_1, sigue valido).
KU: `KU-2026-CITI-CTGYPURP-PRTRY` → reorientado: la pregunta ya no es "por que el branch US queda vacio" sino "**quien llena `FPAYHX-CTGYPURP_PRTY` y desde que dato del documento**".
Probe P01 del arbol: `scratchpad/probe_p01_citi_tree_ctgypurp.py` (nodo `N_6555567710`, v000). Conteo+medios: `probe_p01_citi_ctgypurp.py` / `probe_p01_us_real_xml.py`.

## Probes (read-only)
`probe_p01_citi_banks.py`, `probe_p01_citi_byyear.py`, `probe_citi_dbtr_sys.py`, `probe_child_conds.py`,
`probe_ubiso_len.py`, `probe_ubiso_breakdown.py`, `probe_by_country.py` (en `Zagentexecution/mcp-backend-server-python/`).

---

## 10. CtgyPurp/Prtry — traza COMPLETA de investigación (preservada, CP-001/CP-002)

> Se conserva la evolución del diagnóstico END-TO-END: la hipótesis inicial (código fallback), la corrección con el árbol REAL de P01, y la respuesta a las dos dudas del usuario (drift + hermanos). No borrar las versiones previas — son la traza.

### 10.1 Análisis inicial — hipótesis (árbol `CGI_XML_CT_UNESCO` / fallback) — LUEGO SUPERSEDED

Primer análisis, hecho sobre el árbol **equivocado** (`/CGI_XML_CT_UNESCO` de D01) y el código estándar `CL_IDFI_CGI_DMEE_FALLBACK`:

- Se separaron 2 nodos hermanos dentro de `CtgyPurp`:
  - `CtgyPurp/Cd` → código ISO estándar (SALA, SUPP, TREA, DIVI…). Fuente: pago de nómina → `FPAYH-PURP_CODE`; resto → customizing de category purpose / `DTWS2`.
  - `CtgyPurp/Prtry` (el que falla) → código propietario (`/REF/0825/C`). En el fallback estándar el handler hacía:
    ```abap
    WHEN '<PmtInf><CdtTrfTxInf><PmtTpInf><CtgyPurp><Prtry>'.
    *   This node defines the Category Purpose for the payment - Proprietary
        CLEAR C_VALUE.        " ← sale vacío
    ```
- **Conclusión inicial (INCORRECTA para CITI):** "el Prtry se deja vacío por diseño; nada en el flujo US lo escribe; mismo patrón que el PPC de SocGen (desarrollo pendiente del lado Citi)". Se asoció al spec PPC v2.0 p.16 ("if Citibank requires this, all developments should be reviewed").
- **Por qué se superó:** ese `CLEAR C_VALUE` pertenece al árbol/clase **CGI/SocGen (fallback)**, NO al árbol **CITI** que realmente usa US. El formato del fallo es `/CITI/XML/UNESCO/DC_V3_01`, otro árbol. (El razonamiento SocGen-PPC sigue siendo válido como contexto histórico, pero NO es la causa del fallo Citi.)

### 10.2 Corrección — árbol CITI REAL de P01 (TIER_1, 2026-06-26)

Leído `DMEE_TREE_NODE` TREE_ID=`/CITI/XML/UNESCO/DC_V3_01` en **P01** (versión **000 = activa**, 610 nodos). El nodo del XPath de Citi SÍ está mapeado:

```
CtgyPurp (N_3460219500)  →  hijos hermanos (choice ISO 20022, Cd XOR Prtry):
   ├─ Cd     (N_6232264240)  map = FPAYHX / CTGYPURP        ref=CP   len=4
   └─ Prtry  (N_6555567710)  map = FPAYHX / CTGYPURP_PRTY   ref=CPP  len=35   ← el que Citi exige
```

- El `Prtry` **no tiene condición propia** (`DMEE_TREE_COND` vacío para `N_6555567710`): se emite con el valor de `FPAYHX-CTGYPURP_PRTY`; si ese campo runtime viene vacío, el elemento se suprime → Citi lo marca "Value not present".
- Producción llena el nodo normalmente: **153 medios US (UNES/US) en 2026, el último HOY 2026-06-26** (`20260626/00002B`, USD 6.898.042,58, `UNES_CITI_03XMLUSDDOM0919.in`), sin rechazo. Histórico **1.884 medios** desde 2019-07. **Si rechazara siempre, no se pagaría nada — y se paga.**
- ➡️ El FAIL del test-tool es un **caso puntual con `FPAYHX-CTGYPURP_PRTY` vacío** para ese pago (factura/run sin el dato) — consistente con la hipótesis de factura incompleta al simular.

### 10.3 Duda usuario A — ¿el formato/árbol está desalineado con producción? → NO (en este segmento)

Comparado el nodo `CtgyPurp` entre **P01 y D01**:
- **Mapeo IDÉNTICO** en P01 (v000) y en las **3 versiones de D01 (000/001/002)**: `Cd→FPAYHX/CTGYPURP`, `Prtry→FPAYHX/CTGYPURP_PRTY`. **Sin drift en este segmento.**
- Diferencia estructural general: D01 tiene versiones 001/002 que P01 no tiene activas (P01 solo 000). Si el archivo de PRUEBA se hubiera generado con otra versión/sistema, podría diferir en OTROS nodos — pero el segmento `CtgyPurp` está alineado en todos.
- Observación: en el árbol, el único `CtgyPurp` cuelga de `PmtInf/PmtTpInf` (nivel batch), mientras el XPath del error Citi lo cita en `CdtTrfTxInf/PmtTpInf` (nivel transacción). Diferencia de nivel a revisar, pero el mapeo del campo es el mismo.

### 10.4 Duda usuario B — ¿Cd y Prtry son hermanos; en P01 se llena uno y el otro no hace falta? → SÍ

- Son **hermanos en un choice ISO 20022**: va `<Cd>` **O** `<Prtry>`, nunca ambos.
- Cada uno mapea a un campo FPAYHX distinto: `CTGYPURP` (ISO, 4) vs `CTGYPURP_PRTY` (propietario, 35).
- Citi exige el **`Prtry`**. **Pregunta abierta real:** ¿cuál de los dos se está llenando en los pagos US REALES que sí pasan? Posible que producción emita el `<Cd>` (aceptado por Citi en el canal real) y el test-tool exija el `<Prtry>`. No se pudo leer el valor runtime (XML efímero, share sin acceso, `FPAYHX` no persiste).

### 10.5 ORIGEN DEFINITIVO — tabla de configuración `/CITIPMW/PMWV3` (TIER_1, 2026-06-26)

**Cadena de código verificada línea por línea (D01, RPY_FUNCTIONMODULE_READ_NEW → NEW_SOURCE):**
- `TFPM042FB` registra para FORMI=`/CITI/XML/UNESCO/DC_V3_01` solo **EVENT 05 → `/CITIPMW/V3_PAYMEDIUM_DMEE_05`**. Pero `_05` llena **solo direcciones/bank codes** (REF01–REF06, REF03=SEPA, REF04=DTAID/T045T, REF05=clearing) — **NO toca `CtgyPurp`**. (Corrige una afirmación previa errónea de que `_05` llenaba CtgyPurp.)
- El que llena los `*_PRTY` es **`/CITIPMW/V3_PAYMEDIUM_DMEE_06`** (export `FPAYHX_CREF`). En su línea 22 hace `PERFORM read_zcitipmw` (include `/CITIPMW/LPMWV3F01`), que ejecuta:
  ```abap
  CLEAR /CITIPMW/PMWV3.                                  " hygiene del work-area ANTES del SELECT
  SELECT SINGLE * INTO X_ZCITIPMWV3 FROM /CITIPMW/PMWV3  " config por clave
    WHERE BUKRS=ZBUKR AND HBKID=... AND HKTID=... AND BANKS(ubiso)=... AND ZLSCH(rzawe)=... AND UZAWE=... AND DTAWS=...
  ```
  Luego `_06` línea 47-50 hace `MOVE-CORRESPONDING v_zcitipmw_v3ref01 TO es_fpayhx_cref` → así se llena `FPAYHX-CTGYPURP_PRTY`.
- **El valor NO sale del documento/factura — sale de la tabla de CUSTOMIZING `/CITIPMW/PMWV3`** (data element `/CITIPMW/V3CTGYPURP_PRTY`).
- **Ningún CLEAR borra `CTGYPURP_PRTY`.** El `CLEAR /CITIPMW/PMWV3` (línea 236) limpia el work-area justo antes del SELECT (lo repuebla de inmediato). El único CLEAR real de valor (líneas 28-35 de `_06`) borra `LCLINSTRM_CD` cuando `LCLINSTRM_PRTY` existe (regla XOR), **no** CtgyPurp. Prueba de que la cadena corre: `LCLINSTRM_PRTY=CITI499` SÍ está configurado para US y sale por esta misma ruta.

**Valores leídos (P01 y D01, 2026-06-26) para US (`UNES/CIT04/USD04/US`, 9 filas, todos los métodos):**

| Campo | Valor US (idéntico en P01 y D01) |
|---|---|
| `CTGYPURP` (Cd) | **vacío** |
| `CTGYPURP_PRTY` (Prtry) ← el que Citi pide | **vacío** |
| `LCLINSTRM_PRTY` | **`CITI499`** (WIRE) / `CITI2` (ACH) / `CITI949` (WorldLink) — POBLADO |
| `SVCLVL_PRTY`, `PURP_PRTY` | vacíos |

BR y CA: `CTGYPURP_PRTY` también vacío en todas sus filas.

**Conclusiones firmes (cierran el caso):**
1. **NO hay drift** entre D01 y P01: la config US es idéntica; `CTGYPURP_PRTY` **vacío en ambos**. Nunca se ha poblado.
2. **NO es "se llenó después"**: el campo no depende del documento ni de una fecha; depende de esta celda de config, que está vacía para US en los dos sistemas hoy.
3. **Los archivos US reales NO emiten `<CtgyPurp>`** (ni Cd ni Prtry) — coincide con los XML regenerados. US sí emite el Local Instrument (`CITI499`/`CITI2`/`CITI949`).
4. **Y aún así se pagan** (153 medios 2026, hoy USD 6.9M, sin rechazo) → **Citi en el canal productivo real NO exige `CtgyPurp/Prtry`; solo el test-tool lo marca mandatorio.** El validador del test es más estricto que el procesamiento real. (O Citi introdujo un requisito nuevo que la config aún no refleja.)

### 10.6 Cómo se cierra — es CONFIGURACIÓN, no desarrollo

1. **Confirmar con Citi** qué es `/REF/0825/C` (valor fijo vs. referencia derivada). Patrón `/REF/MMYY/x` sugiere referencia — pedir definición oficial.
2. **Poblar la celda de config** `/CITIPMW/PMWV3.CTGYPURP_PRTY` para las filas US WIRE (igual que ya está `LCLINSTRM_PRTY=CITI499`), vía su transacción de mantenimiento en **D01**, y **transportar a P01**. NO requiere tocar código ni el árbol DMEE (el nodo `N_6555567710` ya mapea ese campo).
3. (Opcional) Confirmar con Citi si realmente es bloqueante en el canal real o solo en el test-tool — define la urgencia.

**Probes P01/D01 de esta traza:** `probe_p01_citi_ctgypurp.py` (medios), `probe_p01_us_real_xml.py` (conteo+lectura), `probe_p01_citi_tree_ctgypurp.py` (rama árbol), `probe_citi_ctgypurp_drift.py` (P01 vs D01 árbol + hermanos), `probe_p01_ctgypurp_source.py` (DD03L+TFPM042FB→exit), `probe_citipmw_config_us.py` (tabla config US P01 vs D01). Todos en `scratchpad/`.
