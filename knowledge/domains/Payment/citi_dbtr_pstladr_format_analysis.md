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

## Probes (read-only)
`probe_p01_citi_banks.py`, `probe_p01_citi_byyear.py`, `probe_citi_dbtr_sys.py`, `probe_child_conds.py`,
`probe_ubiso_len.py`, `probe_ubiso_breakdown.py`, `probe_by_country.py` (en `Zagentexecution/mcp-backend-server-python/`).
