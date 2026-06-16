# Formato `/CITI/XML/UNESCO/DC_V3_01` — Dbtr `PstlAdr`: estructura, defectos y compliance

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

| # | NODE_ID | Tipo | Condición | Estado |
|---|---|---|---|---|
| 1 | N_1531351640 | no-estruct/hybrid | (era `<> USA AND <> CAN AND <> PRO` 3-letras → SIEMPRE disparaba) | **apagado** vía kill-switch `UBISO <> UBISO`; borrar en V001 |
| 2 | N_4078824850 | no-estruct (3 AdrLine) | `= 'USA' OR 'CAN' OR 'PRO'` (3-letras → nunca matchea) | muerto; borrar en V001 |
| 3 | N_5197213060 | **estructurado** | `= 'US' OR 'CA' OR 'PR'` (2-letras OK) | **ACTIVO** — US/CA/PR |
| 4 | N_1905437260 | **estructurado** | `<> 'US' AND <> 'CA' AND <> 'PR'` (2-letras OK) | **ACTIVO** — resto |

## 3. Defectos encontrados

### D-1 (RESUELTO) — duplicado de PstlAdr por código de país inconsistente
`UBISO` es ISO-**2** (`US`). Los nodos viejos #1/#2 comparaban contra **3 letras** (`USA/CAN/PRO`) → en un `<>` (nodo #1) eso es SIEMPRE verdadero → #1 disparaba para todos → 2 `<PstlAdr>` en el Dbtr (uno viejo + uno estructurado). **Fix aplicado:** kill-switch `UBISO <> UBISO` (siempre falso) en #1; #2 ya estaba muerto. Pendiente V001: **borrar #1 y #2**.
Regla: para apagar un nodo, `= <valor inexistente>` o `campo <> mismo_campo`; NUNCA `<> <valor inexistente>` (eso lo deja siempre prendido).

### D-2 (ABIERTO — COMPLIANCE) — `PstCd`/`TwnNm` suprimidos para no-US/CA/PR
En el nodo **#4** (resto), los tags hijo `PstCd` y `TwnNm` tienen condición `FPAYHX-UBISO = 'SE'` → solo emiten para Suecia. Como **SE nunca ocurre** (0 pagos), `PstCd` y `TwnNm` se **eliminan siempre** para todos los pagos no-US/CA/PR.

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
| `/CGI_XML_CT_UNESCO` | 631 | **1** estructurado | tags gated por `NODE -PstlAdrMore (N_2326418530) = 'SPACE'` | ⚠️ **PENDIENTE** |
| `/CGI_XML_CT_UNESCO_1` | 632 | **1** (twin de CGI, mismo NODE_ID) | idem | ⚠️ idem |

**Conclusión:** CITI era el peor caso (4 nodos, código 3-letras, =SE). **SEPA está limpio.** El **formato pendiente = `/CGI_XML_CT_UNESCO`** (+ twin `_1`): su Dbtr emite estructurado **solo si `-PstlAdrMore` está vacío** (patrón "structured-si-no-hay-overflow"). Riesgo análogo al `=SE`: si `-PstlAdrMore` nunca está vacío en prod, el estructurado se suprimiría.

**Pendiente para cerrar CGI** (mismo tratamiento que CITI):
1. Qué calcula el exit para el nodo técnico `-PstlAdrMore` (N_2326418530) y si está vacío para los pagos reales → ¿emite estructurado?
2. País de banco · cuenta · año del formato CGI (P01) — es el formato grande no-Citi (EUR/SocGen, probablemente más países que US/CA/BR).

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

## Probes (read-only)
`probe_p01_citi_banks.py`, `probe_p01_citi_byyear.py`, `probe_citi_dbtr_sys.py`, `probe_child_conds.py`,
`probe_ubiso_len.py`, `probe_ubiso_breakdown.py`, `probe_by_country.py` (en `Zagentexecution/mcp-backend-server-python/`).
