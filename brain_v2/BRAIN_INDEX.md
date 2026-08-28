# BRAIN INDEX (L1 lean bootstrap — read THIS first, drill the rest)

> Tiered loading (s079). This ~4KB index replaces reading the full ~400K-token brain_state.json at
> bootstrap. Load this, then DRILL on demand via `python brain_v2/graph_queries.py <cmd>`. Read the full
> brain_state.json ONLY when you need depth this index doesn't give.

## ⛔ THIS INDEX ORIENTS YOU. IT DOES NOT MAKE YOU COMPETENT ON A TOPIC.
**The moment a topic or domain is named, run the DOMAIN LOAD and read every part it emits —
before proposing, diagnosing or answering anything:**
```
python brain_v2/load_domain.py <topic>     # dmee · "purpose of payment" · avc · ebs · Payment_BCM · --list
```
It emits ONE ordered payload: domain docs + companions (prose) + claims + incidents + annotations +
rules + code objects + Gold tables + capability rows, chunked into `part_NN.md`, plus a PERIPHERAL
list of what it deliberately left out. A `graph_queries` drill returns fragments; this returns the
domain. Measured on DMEE: 40 docs + 20 companions + 165 claims + 11 incidents that no drill surfaces.
**Do not wait to be asked** — rule `feedback_load_the_domain_before_you_reason` (CRITICAL, s100).

## 🏛️ ROOT — THE INSTALLATION (what this whole brain is ABOUT)
`brain_v2/installation/installation.json`. Two roots, different kinds: **L0 core_principles = the
AGENT's constitution** (how we work) · **installation = the SUBJECT** (what we model). Anchor, not
container — it holds identity, axes, pointers and the firing order; never content a store owns.
- **UNESCO — United Nations Educational, Scientific and Cultural Organization** — UN specialised agency (public sector, non-profit, multi-currency, multi-country)
- **SAP ERP 6.0 EhP8 (ECC) — NOT S/4HANA** · character: public-sector finance: budget-and-grants, not manufacturing or sales
- Systems: **P01** (production) · **D01** (development) · **V01** (validation) · **SBP** (satellite — Solution Manager (ABAP, instancia 01) + AS JAVA que sirve ADS (50300))
  · ⚠️ There is no QA system between D01 and P01. Recorded here because it is a STRUCTURAL risk of the installation itself, not of any one change.
- **FIRING ORDER** (deterministic, steps 0–1 mandatory before ANY scope answer — rule #171):
  installation → profile → operation → capability → delta → evidence

## 🇺🇳 THE UNESCO PROFILE — what this tenant IS (read before answering anything about scope)
`brain_v2/system_profile/unesco_system_profile.json` — the base fact-sheet. Profile = the SYSTEM;
capability_model = our KNOWLEDGE of it. Never re-derive this from cvers/logs mid-conversation.
- **Platform:** SAP ERP 6.0 EhP8 (ECC) — NOT S/4HANA · 177 components installed
  (**installed ≠ implemented** — most ship by default: ~60 country HR versions + industry solutions).
- **PRODUCTIVE modules:** FI, PSM_FM, PS, CO, MM, HCM, FI_AA, RE_FX, PM, SD, TRM, Treasury_EBS, Payment_BCM, Travel, BusinessPartner, PBC
- **Configured / marginal:** WM
- **NOT used:** QM, CS, GM
- **Third-party add-ons ACTIVE:** EPI_USE_Labs, ACL_Data_Link (each = a licence + an independent DATA-EXIT channel)
- **⚡ HOW IT OPERATES:** UNESCO does NOT operate SAP by dialog. 80.6% of business RFC traffic is driven by EXTERNAL satellite applications. SAP is a read-dominant SYSTEM-OF-RECORD that feeds satellites and receives concentrated writes.
  Satellites: MuleSoft 1.62M · BRIDGE_RFC_ORION 875K · Named_user_portal 501K · RFC_SSIS 123
- **Integration:** 37 flows / 18+ external systems ·
  detail in `knowledge/domains/Integration/integration_map_complete.md` + `knowledge/system_operating_model_rfc.md`
- ⚠️ **executed_objects_domain_map has NO bucket for RE_FX nor for third-party namespaces (/EPIUSE/, /ACLDL/, /WINSHTLQ/, /GBX01/) — 3,893 objects / 4.56M execs (40% of volume) ...**

## 🎯 THE PROCESS SPINE — B2R is the heart, and it is measured that way
Ranked by domains served, not by opinion. This tenant exists to run **budget-to-report**:
public-sector finance, not manufacturing or sales.
- **B2R** — 8 domains: CO, Closing_Activities, Cost_Recovery_CRP, FI, PBC, PS, PSM, Treasury · avg coverage 64%
- **H2R** — 7 domains: FI, HCM, HR-Workflows, PBC, PY-Finance, Payment_BCM, Travel · avg coverage 60%
- **T2R** — 5 domains: Closing_Activities, FI, Payment_BCM, TRM, Treasury · avg coverage 69%
- **P2P** — 5 domains: FI, PM, Payment_BCM, Procurement, Treasury · avg coverage 65%
- **P2D** — 3 domains: BusinessPartner, FI, Master_Data_Governance · avg coverage 54%
- **A2R** — 1 domains: FI_AA · none measured
- **O2C** — 1 domains: SD · none measured
- **Cross-cutting by construction** (serve NO single process because they touch all): Integration, Output, Support, Transport_Intelligence
- **⚠️ Stranded** (no process AND not technical — neither in a flow nor across one): RE-FX

## 🔗 LOS CIRCUITOS DECLARADOS — el ORDEN, no solo quien participa
`domains` dice QUIEN participa; `stages` dice EN QUE ORDEN y DONDE PUEDE PARARSE.
Son campos distintos a proposito: la pertenencia es un conjunto, el circuito es una
secuencia, y confundirlos es la restriccion de CASO UNICO que el driver OCEL 2.0
nombra como el defecto a evitar.

- **P2P — Procure-to-Pay**: 12 etapas
  `10_requisition_po -> 20_goods_receipt -> 30_service_entry_sheet -> 40_invoice_mm -> 45_fi_doc_payment_block -> 50_ppc -> 60_wf_approval_rm -> 70_f110 -> 80_bcm -> 85_pago_manual_f53 -> 90_file_to_bank -> 95_ack_statement`
  ⛔ **puede PARARSE en**: `60_wf_approval_rm` (metodo de pago O o U -> el WF NO termina: repone el bloqueo a 'W' (blo), `80_bcm` (IBC17 Fallido / IBC06 Rechazado son paradas reales del circuito)
  ◇ condicionales (no siempre ocurren): `30_service_entry_sheet`, `50_ppc`, `80_bcm`, `85_pago_manual_f53`
  · junta declarada: 45_fi_doc_payment_block: 40_invoice_mm (p2p_process_mining, termina en 'Invoice Posted') y 45 (payment_bcm_companion, empieza en 'FI document posted')
  · junta declarada: 50_ppc: p2p_purpose_of_payment.html no tiene arista con NINGUNA de las otras 4 piezas del circuito en companion_graph.json

El grafo de companions lleva estas etapas como aristas **`SIGUE_A`**, separadas de
las de PARECIDO: la similitud de vocabulario NO puede expresar secuencia -- dos
etapas contiguas comparten poco vocabulario justo porque son distintas.
Vigilado por `python Zagentexecution/quality_checks/process_circuit_check.py`.

## 🔌 INTEGRATION — the richest surface, and the one that explains the operating model
**SAP here is a system-of-record fed by satellites, not a dialog system.** Any answer about how
the system is used that assumes people in screens is wrong before it starts.
- **668 interface records** (derived, queryable — `brain_v2/interface_inventory.json`):
  RFC_INBOUND_OBSERVED 255 · RFC_DESTINATION 239 · RFC_CUSTOM_FM 105 · BATCH_INPUT 25 · FILE 20 · IDOC 9 · WEB_SERVICE 8 · WEBSERVICE 4 · DBCON 2 · HTTP_SERVICE 1
- **The boundary is mostly dead:** 238 RFC destinations configured,
  **11 live**, **187 dead**,
  **321 undeclared** — traffic crossing with no configuration entry.
- **…and 40 are UNOBSERVABLE, not dead** — HTTP destinations
  driven by `cl_http_client`, whose calls write no row in the RFC audit log that this measurement
  reads. They were counted as dead until s106 (claim 620). **A zero there means we cannot see, never
  that nobody uses it** — deciding live/dead for those needs a different source.
- **Write channels, derived per object class:** DIALOG 64 · RFC_INBOUND 40 · BATCH_JOB 19 · FILE 6 · PROGRAM 2 · WEBSERVICE_UNDETECTABLE 2 · BATCH_INPUT 1
- **An empty transaction code is a POINTER, not a gap** — usually a BAPI/RFC whose design never set
  one. Reading it as 'batch' loses the interface.
- **What CANNOT be seen:** inbound web-service CALLS. The SOAP monitor is off, so existence and
  activation are verified and execution is not. UNVERIFIED, never 'unused'.

## 🔐 SECURITY — a COLUMN, not a domain (that is why searching for it fails)
`E_AUTH` has content in **5 of 21** domains: FI, PSM_FM, Payment_BCM, Procurement_P2P, Treasury_EBS.
It is ONE missing model capability, not 21 separate gaps — closing it once lifts every row.
- **Known and verified:** portal-as-user RFC writes carry SoD conflicts. Root: `S_RFC=*` plus a
  custom write FM that skips the object check, so the control has to live at the CALL and DATA
  layer, not at the role layer.
- **What that means for any answer about roles:** the role model is NOT the control surface here.
  A clean SU01/PFCG picture does not mean segregation holds.
- Claims touching authorization: 21 · drill: `graph_queries.py capability E_AUTH`
- **Posture store** `brain_v2/security_posture.json` — 3 ready · 2 missing input · 2 findings already stored as RECORDS.
- **Cannot see yet:** role_content, auth_defaults — MISSING_INPUT means WE CANNOT SEE, never 'there is nothing'.

## 📈 MATURITY OF THE METHOD — 65.3%, measured from artifacts
Not a self-assessment: each dimension is derived from what is on disk.
- **Weakest:** **DURABILITY** 0.10 · **VERIFY** 0.40 · **ANALYZE** 0.48
- **Strongest:** MODEL_FIDELITY 0.98 · CONSOLIDATE 0.95 · ESCALATE 0.93
- **Read this together with the capability grid.** Two independent instruments agree: strong at
  COLLECTING, weak at VERIFYING. We know precisely what the system DOES and little about what it
  SHOULD do — which is the same finding as the near-empty `S_STANDARD_REF` column.

## 🔍 ¿ENTENDEMOS LO QUE EL SISTEMA EJECUTA? — 0.72% sin clasificar
Cuatro superficies, porque ejecutar no es solo un programa: lo que corre, lo que CAMBIA, lo que
corre solo, y lo que ENTRA por RFC — esta ultima es la mayor y la que no esta en SLGREPNA.
- **objects** — 29,348,937 ejec · tecnico 86.9% · negocio 7.4% · sin clasificar **0.0%**
- **changes** — 2,881,752 ejec · tecnico 13.2% · negocio 84.5% · sin clasificar **0.0%**
- **jobs** — 235,523 ejec · tecnico 54.7% · negocio 18.2% · sin clasificar **0.2%**
- **rfc** — 12,974,845 ejec · tecnico 52.5% · negocio 34.7% · sin clasificar **2.5%**
- **TECNICO es una respuesta, no un hueco** (el despachador y el planificador son fontaneria).
  El hueco real es SIN CLASIFICAR: 324,909 de 45,441,057.
- **Situar no es explicar:** solo el **75.6%** de las ejecuciones de negocio llega a grado 3
  (alguien lo escribio con evidencia). Ese salto no lo da ningun algoritmo.
- Movimiento: **no se movio** desde la ultima corrida — eso ES el hallazgo · sin cadena de proceso: RE_FX, Output (stranded, no olvido)
- **354 objetos por explorar** (36 custom) —
  la lista es `brain_v2/comprehension_index.json` → `keep_exploring`, ordenada por ejecuciones,
  y es el trabajo del agente `log-process-discovery`.
- Lo aprendido sobre COMO explorar (no sobre el dato) vive aparte, en
  `brain_v2/methods/algorithm_memory.json`: INSTRUMENT · SUBSTRATE · CARRIER · TRAP.

## 🗄️ LO QUE HAY, Y CON QUÉ COMANDO SE ABRE
Este bloque existe porque **solo se encuentra lo que ya se sabe que existe**. Medido: los
claims eran 98% invisibles desde aquí, los docs de dominio 96%, y las memorias de método
**100%**. Las reglas eran el único store sano — porque este índice las enumera. Aquí está el
inventario del resto; el contenido se abre con su comando.

| Store | Cuánto | Cómo se abre |
|---|---:|---|
| **claims** | 642 | `python brain_v2/graph_queries.py search <termino>` |
| **docs de dominio** | 149 | `python brain_v2/load_domain.py <tema>` — **carga el dominio ENTERO** |
| **companions** | 44 | `companions/how_unesco_works.html` los indexa todos |
| **incidentes** | 16 | `python brain_v2/graph_queries.py incident <id>` |
| **reglas** | 258 | `brain_v2/agent_rules/feedback_rules.json` |
| **memorias de MÉTODO** | 172 | `brain_v2/methods/algorithm_memory.json` — INSTRUMENT · SUBSTRATE · CARRIER · TRAP |
| **algoritmos** | 105 | `brain_v2/methods/algorithms.json` — lee su `failure_mode` ANTES de correrlo |

- ⚠️ **Las memorias de MÉTODO son el store que nos hace mejores y nadie apuntaba a él.** Dicen
  qué campo miente, qué lectura produce una respuesta segura y falsa, hasta dónde ve un
  instrumento. Léelas antes de medir algo nuevo.
- 🔍 **Gate de alcanzabilidad:** `python Zagentexecution/quality_checks/artifact_reachability_check.py`
  — comprueba que cada artefacto prometido por un algoritmo exista, lo lea alguien, y se llegue
  a él. En su primera corrida: **24 invisibles y 4 ausentes de 31**.

## 🧭 LOS 105 ANÁLISIS QUE EXISTEN, Y DÓNDE DEJAN SU RESULTADO
El gate de alcanzabilidad encontró **24 artefactos invisibles de 31**: existían, se regeneraban
en cada rebuild, eran correctos, y **no se llegaba a ellos desde ningún sitio**. Se generaban
para nadie. Esta tabla se genera de `algorithms.json`, que ya sabía qué hace cada uno y dónde
lo deja — solo que nadie lo publicaba.

⚠️ = el algoritmo está marcado FRAGILE o WEAK: **lee su `failure_mode` antes de usar su salida.**

**logs**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A19_log_reality_filter` | classify every identifier the audit log carries into OBJECT / GENERATED IN | -- | `brain_v2/log_reality.json` |
| `A20_comprehension_index` | measure whether the EXECUTION SURFACE is closed, across the FOUR surfaces  | BusinessPartner, FI_AA, Integration, Output +4 | `brain_v2/comprehension_index.json` |
| `A22_domain_composition` | abrir un dominio: de que objetos esta hecho, quien lo conduce, cuando, por | BusinessPartner, FI_AA, Integration, Output +4 | `brain_v2/domain_composition.json` |
| `A23_channel_discovery_by_traffic` | descubrir canales de entrada por su TRAFICO y no por su configuracion, y s | BusinessPartner, FI_AA, Integration, Output +4 | `brain_v2/interface_inventory.json` |
| `A3_two_axis_classification` | explain every call on two independent axes — PROCESS (from the object name | Treasury | `Zagentexecution/sap_data_extraction/sqlite/job_classification.json` |
| `A4_ordered_classifier_ladder` | ordered rule chain (package -> software component -> overlay -> name -> te | Treasury | `Zagentexecution/sap_data_extraction/sqlite/job_classification.json` |
| `A5_adaptive_learning_loop` | auto-resolve unknown calls by function group / naming / app domain, LEARN  | BusinessPartner, FI_AA, Travel | `process_mining/learned_rules.json` |
| `A7_concept_drift` | monthly activity profile per domain as RATES PER DAY (executions, distinct | -- | `brain_v2/drift_signals.json` |
| `A8_change_to_executor_attribution` | join a STATE-CHANGE stream to an EXECUTION stream on (user, day, hour) to  | -- | `brain_v2/change_attribution.json` |

**process events**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A21_case_spine` | probar, clase a clase, si el identificador de caso del log de cambios (CDH | -- | `brain_v2/case_spine.json` |
| `A24_document_lifecycle` | seguir un documento como CASO -- cuantas veces se toca, quien, cuanto vive | -- | `brain_v2/document_lifecycle.json` |
| `B1_dfg_discovery` | build the process map from an event log — activities as nodes, observed tr | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +12 | `brain_v2/claims/claims.json` |
| `B2_variant_analysis` | group cases by exact path, rank by frequency and cost — the long tail is w | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +12 | `brain_v2/claims/claims.json` |
| `B3_performance_bottleneck` | cycle time per transition; waiting versus processing | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +12 | `brain_v2/claims/claims.json` |
| `B4_declarative_conformance` | state the normative rules, classify every case against them, quantify the  | -- | `Zagentexecution/sap_data_extraction/process_discovery/p2p_conformance.json` |
| `B5_ocel2_object_centric` | one event references MULTIPLE object types, with no forced single-case not | -- | `Zagentexecution/sap_data_extraction/process_discovery/p2p_ocel2_summary.json` |

**repository**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A9_business_rules_from_source` | extract the DECISIONS that live in code rather than in configuration — qua | Travel | `brain_v2/business_rules.json` |
| `C1c_custom_fm_domain` | custom Z/Y function module -> canonical domain, via the curated tfdir_cust | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, HR-Workflows +8 | `brain_v2/code_inventory.json` |
| `C2_ascent_with_provenance_rung` | climb from any object to the installation, ALWAYS recording which rung of  | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +7 | `brain_v2/capability_model/capability_model.json` |
| `C5_source_identity_and_integrity` | resolve a SAP object name to the file that actually holds its BODY, across | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, HR-Workflows +8 | `brain_v2/code_inventory.json` |
| `C6_routine_level_behaviour_extraction` | split a source file into ROUTINES with line ranges and derive, per routine | BusinessPartner, Cost_Recovery_CRP, HR-Workflows, Integration +7 | `brain_v2/code_sections.json` |

**model**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `E1_crossing` | join profile x capability x claims x documents x companions through an exp | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +12 | `brain_v2/claims/claims.json` |
| `E2_coherence` | compare what the macro asserts top-down against what the detail evidences  | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +7 | `brain_v2/capability_model/capability_model.json` |
| `E3_trigger_evaluation` | compare state against thresholds across accumulation / maturity / interpre | -- | `brain_v2/methods/trigger_state.json` |
| `P1_profile_composition` | compose the installation profile from 18 COMPONENTS, each bound to the alg | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +7 | `brain_v2/capability_model/capability_model.json` |

**interfaces**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `F1_interface_boundary_analysis` | enumerate the boundary (RFCDES / EDIDC / TBTCP / ICFSERVICE) and CORRELATE | Treasury | `brain_v2/interface_boundary.json` |
| `F2_satellite_derivation` | group boundary endpoints into SATELLITES by call signature, resolve what e | BusinessPartner, Integration, Procurement, Travel +1 | `brain_v2/satellites.json` |

**rsau_audit_history (Go...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A45_actor_attribution_per_account` | Dice, cuenta por cuenta, SI UNA ACCION SE PUEDE ATAR A UNA PERSONA. PARAMX | Integration | `brain_v2/security_posture.json` |
| `A49_tier2_sod` | Descubre QUE PERSONAS CONCRETAS ejecutaron de verdad las dos mitades de un | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +12 | `brain_v2/claims/claims.json` |

**master data + fact tab...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A10_address_chain_reconstruction` | reconstruct the chain from funding source to piece of work in an installat | -- | `brain_v2/chain_lineage.json` |

**configuration (sets) c...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A12_set_hierarchy_traversal` | walk a SAP set hierarchy to every leaf, then answer the three questions th | -- | `brain_v2/hierarchy_traversal.json` |

**source code crossed wi...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A13_custom_field_harvest` | harvest every customer-namespace field this installation added to the stan | -- | `brain_v2/custom_fields.json` |

**FM actuals crossed wit...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A14_budget_rate_impact` | compute the budget-rate impact the way the organisation defines it — FM at | -- | `brain_v2/br_impact.json` |

**the knowledge stores t...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A15_subject_graph` | relate the pieces of a subject as a graph of typed edges, where every node | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +12 | `brain_v2/claims/claims.json` |

**the payroll engine — c...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A16_payroll_end_to_end` | discover payroll end to end in six parts: the ENGINE (schemas), the LOGIC  | -- | `brain_v2/payroll_discovery.json` |

**the change log crossed...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A17_change_governance` | detect three governance conditions: a CHANNEL DIFFERENCE where an object i | -- | `brain_v2/change_governance.json` |

**any operational table ...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A18_reality_filter` | measures the distance between what the system RECORDS and what HAPPENED, i | -- | `brain_v2/reality_filter.json` |

**a master table's custo...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A19_wbs_model` | reads every custom field of a master table on THREE axes — type-aware fill | -- | `brain_v2/project_wbs_model.json` |

**repository + model**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `C7_brain_informed_code_interpretation` | read code THROUGH the brain and write back what it learned. Resolves every | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, HR-Workflows +10 | `brain_v2/code_interpretation.json` |

**el propio modelo de ba...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A44_model_gap_exploration` | recorrer un modelo ya construido preguntando que NO sabe: cuanto cae en cu | Treasury | `brain_v2/bank_model_findings.json` |

**el log de auditoria RF...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A27_interface_nature` | poner a cada interfaz DOS ejes: el dominio (donde pasa) y la NATURALEZA (q | BusinessPartner, FI_AA, Integration, Output +4 | `brain_v2/interface_inventory.json` |

**los demas algoritmos d...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A29_discovery_chain` | correr la cadena de descubrimiento entera -- realidad, columna vertebral d | -- | `process_mining/discovery_delta.json` |

**las conclusiones de lo...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A30_mining_bus` | dar a los mineros un sitio comun donde publicar lo que concluyen y consult | Treasury | `process_mining/mining_findings.json` |

**apqi -- la cola de bat...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A31_bdc_channel_mining` | descubrir quien genera sesiones de batch input, de donde vienen y a que do | Travel | `brain_v2/bdc_channel.json` |

**el repositorio entero ...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A32_mining_capability_census` | encontrar scripts que leen datos de EVENTO y sacan patrones de ellos sin e | PY-Finance | `brain_v2/methods/mining_candidates.json` |

**vari/varid -- el CONTE...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A33_variant_content_mining` | leer los VALORES de las variantes para saber lo que un programa HACE de ve | Output | `brain_v2/variant_content.json` |

**FAGL_011ZC (intervalos...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A34_account_behaviour_classes` | decir de que TIPO es cada cuenta de mayor por TRES EJES en orden de autori | -- | `brain_v2/account_classes.json` |

**la memoria de metodo, ...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A37_method_memory_applied` | dar a cualquier minero, ANTES de correr, lo que este proyecto ya aprendio  | Integration | `brain_v2/methods/algorithm_memory.json` |

**los claims ABIERTOS cr...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A38_claim_resolution` | cerrar el circulo de vuelta: encontrar los claims abiertos para los que un | Treasury | `brain_v2/claim_resolution_proposals.json` |

**E070 (TRKORR/TRFUNCTIO...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A40_config_transport_prerelease_check` | Antes de liberar una orden de customizing, dice QUE VA A CAMBIAR DE VERDAD | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +12 | `brain_v2/claims/claims.json` |

**P01 en vivo por RFC: F...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A39_fx_revaluation_scope_by_nature` | Descubre QUE CUENTAS DEBERIAN REVALUARSE Y NO SE REVALUAN, entrando por la | -- | `brain_v2/fx_revaluation_scope.json` |

**rsau_audit_history (P0...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A42_fm_executed_census` | Contrasta el catalogo estatico de PSM-FM contra la evidencia de EJECUCION  | -- | `brain_v2/fm_executed_census.json` |

**los 48 SKILL.md x brai...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A51_skill_registry` | convertir cada SKILL en un NODO con sus aristas: que tablas SAP documenta, | Integration, Output, Procurement | `brain_v2/skills/skill_registry.json` |

**skills x agentes x alg...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A52_toolgraph` | EL BRAIN DEL BRAIN: un grafo de mis PROPIOS instrumentos con quien usa a q | Closing_Activities, Integration, Master_Data_Governance, Output +2 | `brain_v2/toolgraph.json` |

**el foro de mineros x e...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A54_collaboration_mechanism` | hacer que los mineros COLABOREN, no que se mida si colaboran. Tres piezas: | Treasury | `process_mining/mining_findings.json` |

**rsau_audit_history (15...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A56_audit_slot_aggregate` | colapsar UNA sola vez los dos flujos de evento en un agregado EXTERNO E IN | -- | `brain_v2/change_attribution.json` |

**cualquier objeto SAP c...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A57_extraction_method_resolver` ⚠️ | responder 'como leo X y como lo analizo' sin volver a descubrirlo cada ses | -- | `brain_v2/method_registry.json` |

**los companions (HTML d...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A58_companion_knowledge_graph` | convertir el catalogo PLANO de companions en un GRAFO: dos companions que  | -- | `companions/companion_graph.json` |

**BNK_BATCH_HEADER del G...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A59_bcm_dual_control_mining` ⚠️ | encontrar los lotes de pago donde el que crea es el que aprueba (CRUSR=CHU | -- | `Zagentexecution/mcp-backend-server-python/bcm_dual_control_audit.json` |

**tfdir_all (modulos de ...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A62_lazy_generated_object_as_usage_proof` | distinguir LO INSTALADO de LO VIVO usando la generacion PEREZOSA como prue | BusinessPartner, Closing_Activities, Cost_Recovery_CRP, FI_AA +12 | `brain_v2/claims/claims.json` |

**un descubrimiento ya a...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A63_discovery_raises_questions` | CONVERTIR UN HALLAZGO EN PREGUNTAS PARA QUIEN NO SABIA QUE LE AFECTABA. Un | Treasury | `['process_mining/mining_findings.json` |

**el Gold DB p01_gold_ma...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A68_payment_lifecycle_e2e` | construir el log de eventos del ciclo de vida del PAGO -- factura contabil | Treasury | `process_mining/mining_findings.json` |

**lo que un minero ya ca...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A70_mining_output_contract` | EL CONTRATO DE SALIDA de un minero: datos NO bastan. Da tres clases -- OPO | Treasury | `process_mining/mining_findings.json` |

**T012K + T028B + T035D ...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A72_house_bank_ebs_wiring` | comprobar que cada cuenta de banco casa sigue CABLEADA al extracto electro | Treasury | `process_mining/mining_findings.json` |

**FEBKO.EFART + T012K + ...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A73_bank_statement_channel_census` | censar POR QUE CANAL entra el extracto de cada cuenta -- electronico, manu | Treasury | `process_mining/mining_findings.json` |

**T012T (texto) + SETLEA...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A74_bank_account_nature_model` | derivar la NATURALEZA de cada cuenta (operativa / transferencia / a la vis | Treasury | `process_mining/mining_findings.json` |

**T028B + T035D + TIBAN ...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A75_bank_config_profile_by_nature` | medir que configuracion lleva DE HECHO cada naturaleza de cuenta, para pod | Treasury | `process_mining/mining_findings.json` |

**REGUH + FEBKO + GLT0 (...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A76_bank_account_behaviour_signature` | clasificar cada cuenta por lo que HACE y no por como se llama: paga (REGUH | Treasury | `process_mining/mining_findings.json` |

**T028B.VGTYP + T028G (j...**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A77_ebs_format_consolidation` | contar cuantos MODELOS de extracto se sostienen, cuantos bancos y cuentas  | Treasury | `process_mining/mining_findings.json` |

**otros**

| algoritmo | qué contesta | dominios que cubre | aterriza en |
|---|---|---|---|
| `A78_bank_statement_sod_check` | buscar y publicar la SEGREGACION DE FUNCIONES en el extracto bancario tecl | Treasury | `process_mining/mining_findings.json` |

**INSTRUMENTOS — contestan en PANTALLA, no dejan fichero**

| instrumento | qué contesta | se corre con |
|---|---|---|
| `A11_shared_algorithm_memory` | hold what each algorithm LEARNED about the substrate — which log is a filtered subset, which con | `brain_v2/methods/algorithm_memory.py` |
| `A1_chunked_temporal_read` | read a purging log in bounded time windows (<=6h) because a wide call hangs and the connection d | `Zagentexecution/sap_data_extraction/scripts/accumulate_logs.py` |
| `A25_artifact_reachability` | comprobar que cada artefacto que un algoritmo promete en lands_in exista, lo lea alguien, y se l | `Zagentexecution/quality_checks/artifact_reachability_check.py` |
| `A26_knowledge_connectivity` | comprobar que el conocimiento guardado se pueda ENCONTRAR: que este en el campo que su store lee | `Zagentexecution/quality_checks/knowledge_connectivity_check.py` |
| `A28_graph_landing` | comprobar que lo generado llegue al GRAFO -- no a un JSON al lado --, que cada algoritmo tenga q | `Zagentexecution/quality_checks/graph_landing_check.py` |
| `A2_rolling_window_accumulation` ⚠️ | capture a window the source purges (7-120 days) into *_history tables, turning a window into a h | `Zagentexecution/sap_data_extraction/scripts/accumulate_logs.py` |
| `A35_mining_artifact_detector` | avisar EN EL MOMENTO de que acabas de construir un artefacto que mina y no lo has registrado: un | `Zagentexecution/quality_checks/mining_artifact_detector.py` |
| `A36_mining_capability_router` | convertir cada minero en una CAPACIDAD INVOCABLE: se pregunta por tema, en el idioma de quien lo | `process_mining/ask.py` |
| `A41_extract_fund_center_hierarchy` | Descubre BAJO QUÉ SETCLASS vive de verdad la jerarquía estándar de centros gestores (el rollup o | `Zagentexecution/sap_data_extraction/scripts/extract_fund_center_hierarchy.py` |
| `A43_fsv_alignment_check` | Mide, clave a clave, cuanto se ha ido la VERSION DE BALANCE (FSV) de produccion respecto de D01/ | `Zagentexecution/quality_checks/fsv_alignment_check.py` |
| `A46_mine_domain` | Descubre, por DOMINIO, quien mueve de verdad cada objeto ejecutado y por que canal: separa el tr | `process_mining/mine_domain.py` |
| `A47_ob09_vs_variant_check` | Encuentra la cuenta que esta PERFECTAMENTE configurada para revaluacion FX y NO SE VALORA NUNCA  | `Zagentexecution/quality_checks/ob09_vs_variant_check.py` |
| `A48_run_progress_from_its_own_log` | contestar POR DONDE VA un proceso largo leyendo la ultima marca de paso de su log y si el log se | `brain_v2/rebuild_progress.py` |
| `A48_semantic_activity_map` | Convierte un log crudo de arranques de transaccion en un log de PROCESO etiquetado: cada tcode - | `process_mining/semantic_activity_map.py` |
| `A50_transport_content_extraction` | traer al Gold QUE OBJETO viaja en QUE transporte. Sin esto se sabe que hubo un transporte y no q | `scripts/extraction/extract_fsv_structure.py` |
| `A53_skill_binding_gate` | parar cuando alguien opera sobre un tema que YA tiene skill y no lo nombra. Es el control que co | `Zagentexecution/quality_checks/skill_binding_check.py` |
| `A55_query_discipline_lint` ⚠️ | comprobar lo real (nuestro codigo) contra la norma (tres reglas de consulta que eran solo prosa) | `Zagentexecution/quality_checks/query_discipline_check.py` |
| `A60_outbound_channel_availability` | contestar la pregunta que ningun inventario nuestro contestaba: DE LOS 239 DESTINOS SALIENTES, ¿ | `Zagentexecution/quality_checks/outbound_channel_availability_check.py` |
| `A61_capability_footprint_in_log` | contestar SI UNA CAPACIDAD DEJA HUELLA ANTES DE CONCLUIR NADA DE SU SILENCIO. Se le da el conjun | `Zagentexecution/tasks/2026_08_26_inc16471_ads_log_mining/ads_outage_window_check.py` |
| `A61_event_dating_without_a_trace` | FECHAR UN EVENTO QUE EL SISTEMA NO REGISTRA. Seis pasos: (1) comprobar si el hecho deja traza -- | `.claude/skills/sap_log_forensics/SKILL.md` |
| `A64_authority_vs_request_delta` | SEPARAR LO QUE UN DOCUMENTO AUTORIZA DE LO QUE UN CORREO PIDE, y aplicar los cinco gates: (1) DE | `process_mining/authority_delta.py` |
| `A65_authorised_panel_reconciliation` | RECONCILIAR QUIEN PUEDE FIRMAR CONTRA QUIEN ESTA AUTORIZADO A FIRMAR, y separar las cuatro salid | `Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py` |
| `A66_master_data_replication_by_standard_api` | MEDIR EL HUECO REAL LEYENDO LOS DOS SISTEMAS EN VIVO Y REPLICAR POR LA API DEL OBJETO, con readb | `Zagentexecution/tasks/2026_08_20_mmf_gl_sync/gl_master_sync.py` |
| `A67_variant_write_safety` | COPIAR UNA VARIANTE SIN ROMPERLA, sabiendo que las dos formas de romperla NO DAN ERROR. (1) La l | `Zagentexecution/tasks/2026_08_21_variant_alignment/variant_align.py` |
| `A69_agent_roster_enumeration` | enumerar que agentes existen y cuales se OFRECIERON esta sesion, separandolos por PROCEDENCIA (p | `brain_v2/record_agent_roster.py` |
| `A6_frontier_with_substrate_tier` | coverage % + explicit worklist, with a third tier for technical substrate (connectivity, session | `process_mining/executed_objects_domain_map.py` |
| `A71_toolgraph_retrieval_check` | bateria de regresion para la puerta de entrada del toolgraph: cada caso es una PREGUNTA REAL de  | `Zagentexecution/quality_checks/toolgraph_retrieval_check.py` |
| `C1_component_resolution_chain` | object -> TADIR (package) -> TDEVC (component id) -> DF14L (application component) | `brain_v2/system_profile/probes/extract_component_hierarchy.py` |
| `C3_static_edge_extraction` | parse ABAP source for reads_tables / writes_tables / calls_fms and merge the edges into the grap | `brain_v2/parse_abap_edges.py` |
| `C4_object_role_derivation` | derive what each object is FOR — posting engine, report, interface, worklist, master-data mainte | `process_mining/derive_object_roles.py` |
| `D1_D3_delta_strategies` | PK-delta for master, value-compare for totals, high-water-mark for transactional | `scripts/extraction/gold_refresh.py` |
| `D4_field_splitting` | split a wide table read into column groups against the 512-byte line buffer, re-join locally | `Zagentexecution/mcp-backend-server-python/rfc_helpers.py` |
| `D5_bounded_probe_with_cap_reporting` | read with an explicit cap and date filter; report a hit cap as '>=cap', NEVER as a count | `brain_v2/system_profile/probes/probe_footprint.py` |
| `D6_aggregate_before_resolve` | push the row reduction into SQL (GROUP BY), then resolve the expensive enrichment ONCE per disti | `process_mining/detect_drift.py` |
| `E4_canonicalisation` | resolve any spelling to a canonical key through a declared alias contract, in exactly one place | `brain_v2/canonical.py` |

- 📐 **Cómo encajan entre sí:** `knowledge/exploration_architecture.md` — la cadena completa,
  las 4 superficies, las 5 vías, los 4 grados y las trampas que costó llegar ahí.
- **Ninguno de estos ficheros se lee entero.** Se abren con
  `python brain_v2/graph_queries.py search <termino>` o directamente cuando la tabla de arriba
  dice que contestan tu pregunta.
- **Comprobar que siguen siendo alcanzables:**
  `python Zagentexecution/quality_checks/artifact_reachability_check.py`

## OPEN WORK - incidents awaiting action (14 live, deadline first)
- `INC-EGYPT-PPC` - CLOSED_NOT_REQUIRED - **DUE 2026-09-05** - Add Egypt to the mandatory purpose-of-payment country list (Citi CBE requirement, effective 2026
  - NEXT: CERRADO como NOT_REQUIRED el 2026-08-20: SG confirma que no hay codigo para Egipto y el canal Citi no lleva este flujo (76,2% SocGen vs 1,9% Citi; la cuenta Citi Egipto emite el 100% en cheque prenumerado). QUEDA UNA SOLA ACCION, y es de higiene, no del incide
  - drill: `python brain_v2/graph_queries.py incident INC-EGYPT-PPC`
- `INC-PSTLADR-NOV2026` - OPEN - **DUE 2026-11-14** - Direccion estructurada 14-11-2026: el alcance real son los PROVEEDORES (8.149 sin CtrySubDvsn en
  - NEXT: Registro completo en knowledge/domains/Payment/dmee_map/REGISTRO_ERRORES_Y_ACCIONES.md. Por orden: B1 cargar los 399 proveedores US/CA (fichero listo) · F1 meter el validador en el ciclo antes del envio · A3 REACT_LEV nivel 1 · y tres decisiones que necesitan 
  - drill: `python brain_v2/graph_queries.py incident INC-PSTLADR-NOV2026`
- `INC-000005240` - ROOT_CAUSE_CONFIRMED - F-53 manual payment writes XREF1/XREF2='HQ' instead of 'JAK' for Jakarta user
  - drill: `python brain_v2/graph_queries.py incident INC-000005240`
- `INC-000005638` - ROOT_CAUSE_CONFIRMED - SES posting blocked + invoice payment blocked on Gabon donor fund 196EAR4042 (FIPEX-level AVC de
  - drill: `python brain_v2/graph_queries.py incident INC-000005638`
- `INC-000006073` - ROOT_CAUSE_CONFIRMED - PRRW Travel posting RW609 + ZFI020 for IIEP traveler on UNES-funded trip
  - drill: `python brain_v2/graph_queries.py incident INC-000006073`
- `INC-000006906` - RESOLVED_FIX_PROPOSED - Maputo field-office accountant cannot complete monthly MZN bank reconciliation 'download' — like
  - NEXT: 1) sap_adt_api RPY_PROGRAM_READ on YTBAE002 (+ includes + dynp) into extracted_code/CUSTOM/YTBAE002/ to anchor mechanism at TIER_1. 2) Live RFC VARI WHERE REPORT=YTBAE002 AND UNAME=J_DAVANE for her selection variant. 3) Tactical: give J_DAVANE background execu
  - drill: `python brain_v2/graph_queries.py incident INC-000006906`
- `INC-000011781` - EXECUTED_PARTIAL_OPEN_ITEMS - Add Renata Da Silva Freire RITTER to UBO BCM signatory panel (+ Martin/Ba/De Sousa delimitation,
  - drill: `python brain_v2/graph_queries.py incident INC-000011781`
- `INC-000013624` - SAP_SIDE_COMPLETE_ESCALATED_UPSTREAM - El extracto bancario electronico de NTB02/EUR01 (Northern Trust ASHI EUR) dejo de entrar al camb
  - drill: `python brain_v2/graph_queries.py incident INC-000013624`

_6 more open, drill by id:_ `INC-000016338` (EXECUTED_VERIFIED_ROLE_PENDING)  `INC-000016471` (TRIAGED_ROOT_CAUSE_CLASS_IDENTIFIED)  `INC-180995` (ROOT_CAUSE_CONFIRMED)  `INC-BUDGETRATE-EQG` (ROOT_CAUSE_CONFIRMED)  `INC-FXREVAL-OB09` (ROOT_CAUSE_CONFIRMED)  `INC-MMF-BNPPB-2026` (ANALYZED_EXECUTION_PENDING)


## AGENTES - lo que sabemos HACER (14 disponibles)
- **`authority-doc-reader`** - LECTURA. Extrae hechos ESTRUCTURADOS del documento que AUTORIZA un cambio — la carta, el formulario, el carton, el aviso del banco — que casi sie
- **`bank-process-discovery`** - model: sonnet # skills: PRECARGA, no recomendacion. La documentacion de Claude Code dice que # el contexto inicial de un subagente incluye el con
- **`batch-input-explorer`** - model: sonnet # skills: PRECARGA, no recomendacion. La documentacion de Claude Code dice que # el contexto inicial de un subagente incluye el con
- **`bcm-signatory-panel`** - 
- **`brain-steward`** - Promotes knowledge that surfaced in a working conversation into the CENTRAL brain before it is lost. This is the missing "transcript-pattern-extr
- **`document-output-discovery`** - model: sonnet # skills: PRECARGA, no recomendacion. La documentacion de Claude Code dice que # el contexto inicial de un subagente incluye el con
- **`fx-revaluation-scope`** - Audita QUE CUENTAS ENTRAN Y CUALES SE QUEDAN FUERA de la revaluacion FX (F.05 / SAPF100), entrando por la NATURALEZA de la cuenta — banco, deposi
- **`incident-analyst`** - Processes UNESCO SAP support incidents end-to-end. Use this agent whenever the user passes an incident — whether as an .eml file, pasted email te
- **`log-process-discovery`** - model: sonnet # skills: PRECARGA, no recomendacion. La documentacion de Claude Code dice que # el contexto inicial de un subagente incluye el con
- **`master-data-sync`** - Alinea MASTER DATA de P01 (fuente, read-only) hacia D01 / V01: cuentas GL, centros de coste, fondos, centros gestores, proyectos/WBS. Mide primer
- **`miner-onboarding`** - Convierte un script que MINA en una CAPACIDAD registrada — con su proceso completo, no con un esqueleto. Recibe un candidato (de `mining_capabili
- **`mining-arbiter`** - El JUICIO del foro de mineros. Resuelve lo que la jerarquía de evidencia no puede: dos medidas del mismo peso que dicen cosas distintas del mismo
- **`process-guardian`** - model: sonnet ---
- **`variant-intelligence`** - Lee el CONTENIDO REAL de las variantes de ejecucion de programas ABAP y lo convierte en conocimiento de proceso. El programa dice lo que se PUEDE

**Modelo de ejecutores de alineamiento P01 -> D01/V01**: `knowledge/alignment_executors_model.md` - la escalera de canales (API estandar / BC-Set / escritura directa bajo excepcion), los medidores, los actuadores por objeto y el metodo comun. Excepciones autorizadas, lista cerrada: `.claude/skills/sap_master_data_sync/SKILL.md`.

## BANCA - el explorador del modelo encontro 6 cosa(s) que pedir accion
> `python brain_v2/bank_model_explorer.py` (paso 2i del rebuild). El CRITERIO lo pone el
> agente `bank-process-discovery`; el modelo vive en
> `knowledge/domains/Treasury/house_bank_operating_roles.md`.
- `NEW` - El 43% de los bancos vivos cae en un cubo de 'no supe clasificarlo'
- `NEW` - 16 cuenta(s) con extracto y CERO pagos: no pagan, COBRAN
- `BLIND` - El extracto de FEBKO es PARCIAL: faltan 5 sociedad(es)
- `RISK` - 10 banco(s) casa sin actividad desde 2024 o antes
- `NEW` - 35 banco(s) ejecutan UN SOLO metodo de pago
- `RISK` - 4 sociedad(es) no francesas: su pais no alcanza la clase que despacha PPC

## WHAT WE KNOW DEEPLY - 50 companions; the 10 densest, and what each covers
> Do NOT re-derive these. Search any term across every store AND the companions: `python brain_v2/graph_queries.py search <term>`.

- `how_unesco_works.html` - Como trabaja UNESCO — vista general - basis, busarea, business area, carry forward, conformance, connectivity, derivation, donor, epi-use
- `bank_statement_ebs_companion.html` - Bank Statement & Reconciliation - basis, basu, bseg, bsik, business area, compliance, connectivity, derivation, donor
- `payment_bcm_companion.html` - Payment & BCM Intelligence - basu, biennium, bseg, bsik, compliance, donor, dual control, fbzp, fipex
- `transport_companion_D01K9B0CBF_v2.html` - Company Code STEM Creation - basis, bseg, business area, carry forward, derivation, fbzp, fmderive, fmifiit, ggb0
- `cts_dashboard.html` - CTS Dashboard (2017-2026) - basis, basu, biennium, bseg, business area, derivation, epi-use, ggb0, ggb1
- `treasury_operations_companion_v1.html` - Treasury Operations v1 - basu, biennium, bsik, business area, compliance, donor, fbzp, fipex, fm-avc
- `BCM_StructuredAddressChange.html` - BCM Structured Address Change - basis, bseg, bsik, compliance, derivation, dual control, fbzp, ggb0, ggb1
- `fi_substitutions_custom_code_companion_v1.html` - Substitutions & Custom Code Registry - basu, bseg, bsik, business area, derivation, fmderive, fmifiit, ggb0, ggb1
- `sap_knowledge_graph.html` - UNESCO SAP Living Knowledge Brain - basis, basu, connectivity, derivation, dual control, fmifiit, hcm, idoc, interface
- `fi_maintenance.html` - Finance Operations Reference - basu, biennium, bsik, business area, donor, fipex, fm-avc, fmifiit, monitoring

## ⛔ THE OPERATING MODEL EXISTS — do not re-invent
`brain_v2/capability_model/capability_model.json` = **Layer 15** of brain_state. Domain × 11
capabilities; AS-DESIGNED (standard SAP) + AS-RUN (ours); G = delta = the product. Model maturity:
**30.3%**. Do NOT propose a new framework or redesign the schema — EXTEND it.

## Brain at a glance (4724 objects · 258 rules · 642 claims · 19 incidents · 10 closed researches)
16 layers (L0–L15): core_principles · objects · indexes · rules · claims · known_unknowns · falsification ·
superseded · user_questions · data_quality · incidents · blind_spots(0) · interactions · domains_layer(3-axis) ·
**capability_model(L15)**.

## Capability model — 11 dimensions, systemic empty columns: R_S4_READINESS
- **A_PROCESS** (VERIFIED) — how does it actually run (discovered from data) — AS-RUN?
- **B_CODE** (VERIFIED) — which programs/classes/exits/BDC implement it?
- **C_CONFIG** (OWN) — which customizing parameterizes it?
- **D_DATA** (VERIFIED) — which tables + real keys hold it?
- **E_AUTH** (VERIFIED) — who can/does execute it (roles, users, SoD)?
- **F_INTERFACE_FILE** (OWN) — how does it cross the boundary (RFC/IDoc/file)?
- **G_CONFORMANCE** (VERIFIED) — does it deviate from / extend STANDARD SAP?
- **H_IMPROVE** (OWN) — where is the opportunity; what-if before building?
- **R_S4_READINESS** (VERIFIED) — how ready is this domain's custom code/config/process for the S/4HANA migration?
- **S_STANDARD_REF** (GAP) — do we have the STANDARD SAP as-designed baseline for this domain (precondition f
- **U_USAGE** (VERIFIED) — WHAT objects actually execute, WHO runs them, by which CHANNEL (dialog / batch /

## Where we are (execution sequence s079)
wwrqcozf1 CLOSED. A,B,C DONE. B2 scheduling = SessionStart daily curation (native hook, no schtasks). D SKIPPED by user (s079) - stays deferred. E maturity current. F commit = pending user OK (focused, not blanket - git status has ~100 unrelated changes).
Pending after gate: A · B · C · D · E · F

## DRILL — load on demand (don't read the whole brain)
- `python brain_v2/load_domain.py <topic>` — **THE DOMAIN LOAD. Run this FIRST when a topic is named**
  (everything the topic knows, ordered + chunked). The drills below are for follow-up questions, not
  for getting up to speed.
- `python brain_v2/graph_queries.py capability_gaps` — the ranked plan (generated, not written)
- `python brain_v2/graph_queries.py capability <domain>` — a domain's capability coverage
- `python brain_v2/graph_queries.py domain <name>` — domain registry entry
- `python brain_v2/graph_queries.py incident <id>` — incident trace
- `python brain_v2/graph_queries.py what_reads <table>` / `what_depends_on <obj>` — code dependency
- `python brain_v2/graph_queries.py stats` — freshness check
- Research base: `brain_v2/research/` — dedupe new research vs `sources_index.json` (175 urls); never re-assert `findings_registry.json` refuted.
- Full model: `brain_v2/capability_model/` (capability_model · s4_readiness_model · execution_backlog · applied_models · maturity).

## Rules to load first (behavioral DNA — 258 total)
Read `brain_v2/agent_rules/feedback_rules.json` for all. CRITICAL ones added s079: research_quality_gate (#148),
capability_model_is_the_operating_model (#149), archive_and_dedupe_deep_research (#150),
ask_strategy_before_scoping (#151), model_exists_do_not_reinvent (#152).
