# Retro — DMEE structured-address forensics (CITI / CGI / SEPA) · 2026-06-17

**Scope:** forensic analysis of UNESCO's DMEE payment-format trees (structured `PstlAdr`), party-by-party
(Dbtr · UltmtDbtr · Cdtr · UltmtCdtr) across the 3 models (CITI, CGI, SEPA), driven by the goal "structured
address to all". Validated end-to-end against 3 real generated `pain.001` XMLs (US, ALPAY, BR).
**Outcome: ZERO config changes needed.** All knowledge persisted (brain docs + companion + memory).

## What we concluded (final)

| Item | Verdict |
|---|---|
| **D-2** — CITI Dbtr BR sin `PstCd`/`TwnNm` (nodo `N_1905437260`, gate `=SE`) | Real defecto, **PROBADO** en XML BR, pero **SIN impacto operativo** (flujo doméstico BR, no cross-border SWIFT → CBPR+ no aplica). **Config se deja como está** (decisión usuario). |
| **D-1** — supuesto `PstlAdr` duplicado para BR | **RETRACTADO** — XML BR real = 1 solo `PstlAdr`; nodo legacy `N_1531351640` está desactivado. |
| **UltmtDbtr** | **Nm-only por diseño** (ISO 20022) — no es gap, sin add. Confirmado: 0 `UltmtDbtr` en los 3 XML reales. |
| **CGI Dbtr** gate `-PstlAdr_More_Nodes = SPACE` | **Benigno** (flag dinámico de overflow del exit, ≠ constante muerta `=SE`) → emite estructurado para direcciones normales. Confirmación empírica (replay `20250326/T0001`) parqueada por el usuario. |
| Cdtr · UltmtCdtr · SEPA | completos / por diseño — sin acción. |

## Phase 4b — SAP learnings (lo que el próximo agente necesita saber)

1. **Para saber si un nodo DMEE renderiza, el OUTPUT REAL > la condición.** `DMEE_TREE_COND` **no** captura la
   desactivación a nivel de nodo: un nodo puede estar apagado por un flag que NO está en la tabla de condiciones,
   así que leer solo la condición da **falsos positivos** (me pasó con el D-1). Si el artefacto es repleable
   (`ZSAPFPAYM_REPLAY`), generarlo y leer el XML real. → nueva regla `feedback_real_output_beats_config_for_rendering`.
2. **Gate de constante-muerta vs gate dinámico.** `UBISO='SE'` (Suecia, que nunca ocurre) = **siempre suprime = bug**.
   `-PstlAdr_More_Nodes='SPACE'` (flag de overflow calculado por el exit) = **benigno**, emite estructurado salvo
   overflow real. No alarmar por el segundo tipo.
3. **`UltmtDbtr`/`UltmtCdtr` (parte última) son Nm-only por diseño ISO 20022** — identificables solo por nombre.
   Un `UltmtDbtr` estructurado (si existe, p.ej. en CGI) vive a **nivel transacción** (`CdtTrfTxInf/UltmtDbtr/PstlAdr`),
   no a nivel `PmtInf`. No es un gap a "rellenar".
4. **El BAdI `FI_CGI_DMEE_EXIT_W_BADI` es ANGOSTO.** El override UNESCO es solo: (a) `FALLBACK->get_credit` →
   `Cdtr/Nm`+`Cdtr/StrtNm` (name-overflow, Pattern A); (b) clases país `FR/DE/IT->get_value` → PPC (purpose code,
   `get_tag_value_from_custo` sobre `mt_ppc_cus`, **no** dirección). Todo lo demás "BADI" = SAP-estándar leyendo el
   buffer `FPAYHX_FREF` (poblado por Event 05). CITIPMW `V3_*` (solo CITI) lee `ADRC` del vendor directo.
5. **Cada partido tiene N nodos `PstlAdr` por `UBISO`, no 1.** CITI Dbtr = 4 (US/CA=#`N_5197213060` completo;
   BR=#`N_1905437260` con `=SE`; #`N_1531351640` legacy apagado; #`N_4078824850` 3-letras muerto). CGI = 1/partido (limpio).
6. **`UBISO` = `FPAYHX-UBISO` = `REGUH-UBNKS` = país del banco que paga (clearing)**, NO el del beneficiario. Selecciona el nodo.
7. **Domestic ≠ cross-border para compliance.** El flujo BR/Worldlink es doméstico (BRL, bancos locales) → el mandato
   CBPR+ de dirección estructurada NO aplica. No asumir "reject risk" sin confirmar que es correspondencia cross-border SWIFT.
8. **RFC gotchas (D01):** `DMEE_TREE_HEAD` NO es legible por `RFC_READ_TABLE` (TABLE_WITHOUT_DATA); leer `DMEE_TREE_NODE`
   con TODOS los campos excede 512 bytes (DATA_BUFFER_EXCEEDED) → pedir subconjunto; WHERE largo con NODE_ID rompe el
   parser → filtrar en Python; nombres de campo vía `DD03L`. La versión DMEE activa no es RFC-legible → confírmala el usuario (V000).
9. **Escenarios D01 replayables (en README del replay):** BR `20210924/UBO/100` (muestra D-2) · 2023 `20231215/USDI/100`
   (=fuente del ALPAY, US-cleared, alt-payee vía `EMPFG`) · CGI `20250326/T0001/100` (verificar gate, parqueado).

## Qué hice MAL (auto-crítica)

- **Sobredimensioné el impacto del D-2** ("ALTO / CBPR+ reject") sin chequear que el flujo BR es doméstico. El usuario
  lo corrigió → sin impacto.
- **Alarmé con el D-1 duplicado + "versión activa sin confirmar"** leyendo solo `DMEE_TREE_COND`; el XML real lo refutó.
- **Propuse "ADD UltmtDbtr CITI ← copiar CGI"** antes de que el usuario aclarara que es Nm-only por diseño.
- Patrón común a los 3: **afirmé desde la config/estructura sin el output real ni el contexto de negocio.** → la regla nueva.
- Lo que SÍ funcionó: corregir rápido y sin defensividad cuando el usuario aportó evidencia (los XML, la pantalla SAP, "no tenemos SE").

## Phase 4b checklist

- [x] ¿Asunciones SAP equivocadas? → SÍ, documentadas (D-1, impacto D-2, UltmtDbtr, gate CGI). Las notas previas se
  corrigieron in-place marcando el error (no se borró el histórico del razonamiento).
- [x] ¿Comportamiento UNESCO no registrado? → SÍ: BAdI angosto + PPC dispatch + name-overflow Pattern A + Event 05 buffer. En `dmee_formats_model_comparison.md` §7-8.
- [x] ¿Anotación que contradice una previa? → SÍ: D-1 "duplicado" → retractado; marcado como falso positivo, no borrado.
- [ ] ¿Tablas citadas sin extraer? → N/A (DMEE_TREE_* se leyeron en vivo; no van al Gold DB).
- [ ] ¿Código citado sin extraer? → N/A (clases BAdI ya en `extracted_code/FI/DMEE/`).
- [x] ¿Falta una feedback rule? → SÍ, añadida: `feedback_real_output_beats_config_for_rendering` (#157).
- [x] ¿CLAUDE.md load-bearing? → No tocado.

## Qué hacer MEJOR la próxima — acuerdo de trabajo

Para DMEE / cualquier config que GENERA output:
> **config-read → HIPÓTESIS (no hecho) → replay output real → impacto evaluado CON el negocio → recién ahí persistir como hecho.**

1. **Output real primero, no al final.** Si la verificación es barata (replay de minutos), conseguir 1 sample por
   escenario ANTES de escribir/commitear la conclusión. (Regla #157 — aplicarla desde el minuto cero.)
2. **Separar "existe" de "importa".** Hecho estructural ("falta el tag") ≠ juicio de impacto ("riesgo compliance").
   Antes de poner severidad: 1 pregunta al dueño del negocio (cross-border vs doméstico; ¿el valor X ocurre?).
3. **Taggear MEDIDO vs INFERIDO vs ASUMIDO + confianza** en cada claim (regla ya existente — usarla). No afirmar inferencias como hechos.
4. **No persistir conclusiones sin verificar.** Marcar HIPÓTESIS hasta confirmar; evita el churn write→rewrite y que el brain tenga un hecho falso aunque sea brevemente.
5. **Batch probes/ediciones.** Menos pasos, más grandes (un probe que saca toda la estructura de una).

## Open / parked

- **CGI replay `20250326/T0001/100`** — confirmar Dbtr completo (esperado benigno). Parqueado por el usuario ("eso será después").
- **CGI CdtrAgt** (dirección del banco) marcado no-estructurado en el companion — solo si el scope incluye dirección de banco.
- Cdtr name-overflow → función combina-nombres (cosmético, opcional).

## Artefactos tocados (commits 84eb041 → 2798d75)

`knowledge/domains/Payment/dmee_formats_model_comparison.md` (§7 nodos + §8 BAdI + §9 impacto + §10 validación XML) ·
`knowledge/domains/Payment/citi_dbtr_pstladr_format_analysis.md` (§2/§3/§4 corregidos) ·
`companions/BCM_StructuredAddressChange.html` · `extracted_code/FI/SAPFPAYM/ZSAPFPAYM_REPLAY/README_REPLAY.md` (escenarios D01) ·
probes `probe_pstladr_nodes_full.py` / `probe_pstladr_paths.py` · memoria `reference_dmee_2models_party_matrix.md` ·
`brain_v2/agent_rules/feedback_rules.json` (#157).
