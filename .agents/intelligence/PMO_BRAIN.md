# UNESCO SAP — Project Brain + PMO Brain

<!-- PMO-IDS: mismo-item = H137, H67, H68, H41, H50 -->
<!-- PMO-IDS: colision-historica = H91, H92, H93, H104, H105, H106, H107, H108, H109, H110, H111, H112, H113, H114 -->
<!--
  H135/H136, s107. Las repeticiones de numero son de DOS clases y confundirlas esconde la
  que importa, asi que se declaran aqui y `pmo_id_integrity_check.py` las vigila:

  mismo-item          un item VIVO con varias secciones (enunciado, hallazgos, cierre).
                      Es correcto y util. H137 tiene cuatro; H67/H68/H41/H50, dos.
  colision-historica  DOS items distintos con el mismo numero. Son 14, y salen de dos
                      sesiones repartiendo numeros sin mirar las del otro -- el fallo de
                      un-solo-escritor (ADR-008) aplicado al contador del PMO. Ejemplo:
                      H113 es a la vez 'reubicacion de reglas' y 'variantes de F.05'.

  NO SE RENUMERAN A CIEGAS. Un ID citado en un retro, un claim o un mensaje de commit se
  queda apuntando a nada, y el historial de git no se reescribe. Renumerar es una migracion
  con barrido de citas, y se hace cuando se decida hacerla entera.
  Cualquier repeticion NUEVA que no este en estas dos listas hace fallar la puerta: la deuda
  vieja queda visible sin poner el gate en rojo permanente (leccion de H131).
-->


> ## PENDIENTE AL ABRIR - S106 (2026-08-27). EMPIEZA POR H137.
>
> Decision del dueno al cerrar s106: registrar todo y reabrir sesion, porque los hooks
> nuevos SOLO CARGAN AL ARRANCAR -- el guardia de escritura sobre stores (PreToolUse) y la
> peticion del roster de agentes no estaban activos en la sesion que los escribio.
>
> ### DEL DUENO -- decision o produccion, el agente NO las hace
> 1. **EL FLAG DE UN BIT.** `YTBC_TRACE.ACTIVE='X'` para `WF_PAYMENT` en P01. Hoy la traza
>    esta APAGADA (sus dos hermanas estan a `X` con 594 y 197 filas), y por eso la liveness
>    del proxy a RoleManagement es INVERIFICABLE. Un flag la convierte en numero medido.
>    Es configuracion en PRODUCCION. Claim 626.
> 2. **EL DOBLE CONTROL DE BCM.** 3.359 de 5.757 lotes con `CHUSR = CRUSR` -- **58,4%**
>    creados y aprobados por la misma persona -- y el evento `BCM Batch Approved` solo se
>    emite cuando difieren, asi que el hueco sale DIBUJADO COMO VARIANTE NORMAL del proceso.
>    Es el hallazgo de NEGOCIO mas serio de s106, no una tarea tecnica. Claim 625.
> 3. **EL BACKUP.** Diferido explicitamente por el dueno ("luego hacemos backup"). Golden DB
>    **21,25 GB** + `~/.claude` **1,95 GB**, ninguno en git, sin copia mientras `D:` no este
>    montado. `python scripts/backup_golden.py --dest D:\claude_backups`
>
> ### ⬛ CERRADO EN s107 (2026-08-27) -- los cinco de la lista
> - **H137 CERRADO el tramo principal.** El companion existe (`payment_bcm_companion.html`,
>   828 KB) y las 11 etapas estan cubiertas: no habia nada perdido, faltaba el ORDEN. La
>   similitud de vocabulario no puede expresar secuencia, asi que el circuito se DECLARA
>   (`domains.json -> process_map.P2P.stages`) y el grafo gana una segunda clase de arista,
>   `SIGUE_A` (20). Gate `process_circuit_check.py`. **Barrido de los 44 hecho:** 4 de 50
>   companions son de facto un skill sin declarar -- `budget_rate`, `closing_activities`,
>   `treasury_operations`, `project_wbs`, los cuatro dominios sin skill. Claims 627/628.
>   **Sigue abierto:** escribir el skill `presupuesto-al-pago` y el veredicto del minero e2e.
> - **H138 CERRADO.** `braintoolbox.yaml` parsea (5 cambios quirurgicos, cero contenido
>   perdido) y su puerta comprueba el PARSEO antes de mirar ninguna cifra. Verificado
>   rompiendolo a proposito.
> - **H139 CERRADO.** `contestar()` casa por (sujeto, para): contesta la unica, la de `para=`,
>   TODAS con `a_todas=True`, o SE NIEGA. Nunca la primera en silencio. 4 casos probados.
> - **H136 CERRADO.** 788 secuencias mojibake reparadas, 0 restantes, vigilado por gate.
> - **H135 CERRADO como DECLARACION, no como renumeracion.** 5 repeticiones son un item vivo
>   con varias secciones (correcto); 14 son colisiones reales. **No se renumeran: medido,
>   H113 y H112 se citan en 5 ficheros cada uno, H110 en 4, y el historial de git no se
>   reescribe.** Declaradas en el bloque `PMO-IDS` de arriba; la puerta falla solo ante una
>   repeticion NUEVA sin clasificar.
> - **H140 CERRADO.** El agent-finder ya tiene minero: **A69_agent_roster_enumeration**
>   (`record_agent_roster.py`), con `UNOBSERVABLE` en su salida y en su `lo_que_NO_puede` para
>   la mitad del harness, que no es enumerable desde disco POR CONSTRUCCION.
> - **H143 NUEVO** (mio, medido violandolo): el guardia de escritura sobre stores solo casa
>   `Write|Edit|MultiEdit` — una escritura por Bash no lo dispara, y esta sesion trabaja por
>   Bash por instruccion del harness. Ver H143 abajo.
>
> ### DEL AGENTE -- en este orden, empezando por H137
> - **H137 -- PRIMERO.** El circuito presupuesto-a-pago existe REPARTIDO EN 4 PIEZAS con una
>   junta seca (nadie cose PO->factura con factura->WF), y el grafo de companions NO CONOCE
>   LA CADENA: no hay arista entre `p2p_purpose_of_payment` y `payment_bcm_companion`. Es lo
>   que originó s106 y sigue abierto. La cadena correcta, corregida por el dueño, esta en el
>   propio H137.
> - H138 `braintoolbox.yaml` no parsea como YAML y su puerta lee con regex, asi que no puede
>   verlo. Se intento reparar guiado por el parser, paro en la linea 210, se REVIRTIO entero.
> - H139 `colaborar.contestar()` casa por SUJETO y cierra solo la primera: `CLAIM 616` tiene
>   15 preguntas iguales, asi que una respuesta deja 14 abiertas para siempre.
> - H135 / H136 los IDs del PMO colisionan (18 repetidos) y el fichero esta DOBLE-CODIFICADO
>   en disco (el guion de H111 son tres caracteres, no U+2014).
> - H140 el *agent-finder*: falta el MINERO que enumere, con `UNOBSERVABLE` declarado para la
>   mitad del harness, que no es enumerable desde disco.
> - H141 `document-output-discovery` aislado (0 aristas DELEGA de entrada y salida).
> - H142 los HELPERS no son nodo del toolgraph, por eso nadie mide que se ignoren.
>
> ### Deuda medida que se dejo VISIBLE a proposito, no olvidada
> - 4 ficheros leen tablas de alias sin importar `canonical` (`canonical_usage_lint.py`).
>   No se tocaron a ciegas: hay que mirar si resuelven alias o solo nombran claves.
> - Invocacion de agentes al 38% de los medibles (`agent_invocation_check.py`), con su
>   ventana declarada: 9 lanzamientos en 8 dias NO permite concluir abandono.
>
> ### Instrumentos nuevos de s106 que la proxima sesion DEBE usar
> `record_agent_roster.py` (el arranque lo pide) · `whose_commits.py` (antes de creerse una
> alarma de escritor paralelo) · `canonical.same()` (SIEMPRE, antes de comparar nombres) ·
> `process_axis_consistency_check.py` · `agent_invocation_check.py` · `canonical_usage_lint.py`
>
> Two brains, one project. Updated every session. Read alongside `PROJECT_MEMORY.md`.
> **Last reconciled**: Session #082 (2026-06-15) — **ABAP CHANGE DISCIPLINE, end-to-end.** Born from INC-CLASS-LOSS (2026-06-12, ADT in-place write corrupted N_MENARD classes). Audited our write surface (2 kill-switched ADT clients + `adt_deploy` MCP + ~78 ad-hoc `deploy_*` scripts, ~81% with no transport) vs CRP's proven pipeline. The disciplined rule existed **only inside CRP** (never distributed) → **promoted to ecosystem universal standard**: `ecosystem-coordinator/.knowledge/way-of-working/sap-abap-change-discipline.md` + **BROADCAST-007** (abapobjectscreation + FINCLOSSING + offboardning_clone adopt; CRP exempt as origin) + CLAUDE.md pointer. **#0 landscape probe DONE** (live read-only RFC): **D01 (DEV) → V01 (QAS) → P01 (PROD)**, basis 7.50, 29,408 released transports — liberating IS the norm; the incident was the agent bypassing it. **Point A DONE — ported CRP gate stack**: `Zagentexecution/abap_deploy/` (objects_manifest.yaml own-objects-only + deploy_object.py 9-gate path + verify_mirror.py) + `process-guardian` agent. VERIFIED read-only: the real N_MENARD victim `YCL_FI_ACCOUNT_SUBST_BL` is HALTED at gate-0 → the incident would not recur. Closed `task_43451c89`. **Point B (transport RELEASE + ATC-REST) deferred by JP → H59.** Commits: fe9e0d6 (coordinator); 3896bb4/34bb9f7/b11722b (project). CRP untouched (read-only). New: H59-H62.
> **Prior**: Session #079 (2026-06-08) — **Capability Model (Layer 15) = the operating spine; this session folds into the master plan.** A domain is now modeled as AS-DESIGNED (standard SAP) + AS-RUN (ours); G = the delta = the product. 10 capability dimensions incl. **R_S4_READINESS** (composite/fractal sub-scorecard) and BP/CVI migration readiness (scoreable from our master data). **4 deep-researches CLOSED** under the new research quality-gate (process mining w3t7ufrbg · code mining w3os0wwlx · competitive landscape wgrqpmt9f · S/4-readiness/BP-CVI wh5gw9exu). 2 CRITICAL rules: **#148** research_quality_gate_before_conclusions, **#149** capability_model_is_the_operating_model. **Maturity baseline 22.7%** (54.5% of gap reachable without extraction) — dashboard `companions/model_maturity_dashboard.html`. Execution DEFERRED + fully specified: `brain_v2/capability_model/execution_backlog.json` (9 extraction + 9 analysis + 4 research). The plan is now GENERATED from the matrix (`graph_queries.py capability_gaps`). See `knowledge/capability_model.md`, `capability_model_execution_plan.md`, `adoption_backlog_synthesis_phaseB.md`.
> **Prior**: Session #058 (2026-04-20) — **INC-000006906 closure + bank reconciliation family inventory.** 5 new H-items (H54-H58): transport YTBAE002 fix to P01, STAD trace YTR1/YTR2/YTR2_HR, extract YCL_FI_BANK_RECONCILIATION_BL, YTBAI001 SMARTLINK status, YTBAM002_HR_UBO TADIR-delete. Dormant MODE 'E' landmines preserved on YTBAE001 + YTBAE001_HR (user declined speculative fix). New claims 52/53/54. +~30 new objects (YTR3 family, SAPDBSDF, PUT_BSIS, SKB1, FB08, F-04, FBRA, YBANK_ACCOUNTS_FO_OTH). 3 new feedback rules (mode_e_bdc + d01_adt_fallback + time_out_stack_blames_ldb). Retro: `Zagentexecution/retros/session_058_retro.md`.
> **Prior**: Session #054 (2026-04-14) — **Formalization audit + Core Principles bootstrap.** User-driven audit revealed 13 of 16 session #053 commitments were never formalized in PMO. Response: 3 Core Principles established (CP-001 Knowledge over velocity, CP-002 Preserve first, CP-003 Precision evidence facts) as constitutional layer 0 of brain_state.json. 4 new operational rules (86 total: retro_to_pmo_bridge CRITICAL, never_drop_columns HIGH, sample_before_aggregating + explicit_aggregation_filter MEDIUM). H42 schema migration executed: claims.evidence_for/against str → list[typed]. 11 new H-items (H41-H51). H36 refreshed (20→71 blind_spots). See `brain_v2/core_principles/core_principles.json` + `knowledge/session_retros/session_054_retro.md`.
> **Session #050** prior: Brain v3 validation + incident methodology bootstrap. 12 deliverables. H35 closed. 7 new feedback rules (58 total). 2 new brain layers (incidents=11, blind_spots=12). Brain coverage metric introduced: 75.6%. Object count 102→136 via force-include. New skill `sap_incident_analyst` + subagent `incident-analyst`. New session-close Phase 4b (Capture SAP Learnings).
> Session #049 prior: Brain v3 hybrid rebuild + portability + AGI self-awareness. 16 deliverables.
> Session #048 prior: INC-000006073 RCA + Travel/BusinessPartner domain creation. 14 deliverables.
> Session #042 prior: Brain v2 Explorer + Bank consolidation. 10 deliverables.
> **Current count**: 0 Blocking | **41** High | **31** Backlog = **72 total** (2026-08-20: H101/H102 CERRADOS — Egipto no hacia falta; +H106 desarmar D01, +H107 modelo de rol de bancos casa, +H108 bancos casa muertos, +H109 el papel de la red de campo y la palanca real, +H110 FEBKO parcial: el modelo de bancos no ve los cobros, +H111 divs sin cerrar en treasury v2) (+5 H101-H105 s101: Egipto probado en D01, defecto vivo en T015L INA, el guardian del indice que no comprueba vigencia) (+4 H59-H62 ABAP discipline; +3 H63-H65 companion knowledge layer 2026-06-21; +H66-H83 logs/SoD/integration 2026-06-21/22; +H84 extractor-maturity domain curation 2026-06-22; +H85 U_USAGE deep-dive 2026-06-23; +H86-H87 AVC detector wiring + ICTP consolidation 2026-06-23; +H88-H90 executed-objects map / hidden HR extractions / integration+time axes 2026-06-23) + **Capability-Model backlog** (Layer 15, source of truth `brain_v2/capability_model/execution_backlog.json`): **10 DONE** (7 analysis builds: OCEL2/PM4PY/P2P/STDREF/G-P2P/DEPGRAPH/OPENDATASET + 3 research: AUTH-SOD/FINANCE-S4/COMPETITORS) · **12 PENDING** (9 extraction [P01/D01-gated] + AN-BPCVI-SCORE + AN-ABAPLINT + DSGN-S4-WEIGHTING) · 1 DROPPED (RES-S4-GREENFIELD — brownfield). **NEXT no-P01:** AN-BPCVI-SCORE, DSGN-S4-WEIGHTING, **+ a DOMAIN-ENRICHMENT pass (propagate s079 verified findings into companions + domain .md — NOT yet done).**
> **⮕ > **⮕ INCOMING (2026-08-26 — s103: el brain del brain, y el patron que aparecio en TRES capas).**
> Sesion de MEJORA DEL MODELO, no de negocio. Lo hecho: A34 aterrizado (clases de cuenta por lo que SAP DECLARA, no por regex sobre texto libre) · E071 al Gold (2.369.936 objetos, 14.939 transportes, indice unico) · 4 defectos vivos medidos y 3 arreglados en nuestros propios instrumentos · el **grafo de herramientas** (`brain_v2/toolgraph.json`, 226 nodos, 537 aristas) y su **coordinador** (`graph_queries.py tool para "<tarea>"`) · el **mecanismo de colaboracion** entre mineros (`process_mining/colaborar.py`) · el **flujo del caso** como conocimiento (`brain_v2/methods/incident_flow.json`) · el skill que faltaba (`sap_bcm_signatory_maintenance`, 53 KB, 121 citas) · y **un comando que junta lo pendiente de las SEIS fuentes**: `python brain_v2/methods/pending_inventory.py`. Claims 591-607. Reglas nuevas: `feedback_ask_the_toolgraph_before_building_anything` (CRITICAL), `feedback_a_gate_must_measure_the_effect_not_the_form` (CRITICAL), `feedback_a_workflow_that_returns_text_lands_nothing` (CRITICAL), `feedback_pair_pipeline_stages_by_order_not_by_text`.
> **EL PATRON QUE ATRAVIESA TODO, y por el que estos H existen:** medir la FORMA en vez del EFECTO. Aparecio en TRES capas del mismo gate — comprobar que la cadena esta en el fichero (5 mineros recibian `None`), que el import RESUELVE (arreglado), y que la funcion se LLAMA (27 de 48 no la llamaban). Y en el skill_binding_check, y en el cruce declaracion-vs-balance (935 falsos), y en el detector de contradicciones (2 falsos). **Al escribir la comprobacion de un defecto, aplicale el mismo criterio que al defecto.**
> - **H131 [🟡 DEUDA DE BRIEF — 10 incidentes que solo se alcanzan leyendolos enteros]** — `incident_record_coverage_check.py` ahora comprueba el TRIANGULO de artefactos (doc + registro + que se LLEGUE) y reporta **10 docs sin BRIEF**: INC-000005240, 000005638, 000006073, 000006313, 000006906, 180995, BUDGETRATE-EQG, CLASS-LOSS-2026-06, MMF-BNPPB-2026, PSTLADR-NOV2026. Van como **AVISO y no como fallo a proposito**: un gate rojo permanente por deuda historica es como se consigue que un check se ignore. **Se saldan al tocar cada incidente**, escribiendo una seccion 0 de 60 segundos — que pidan, que se hizo, que bloquea, que decide quien, fecha limite. Modelo: `INC-000016338`.
> - **H132 [🟠 EL TOOLGRAPH SOLO VE CINCO RAICES — lo de fuera es invisible PARA SIEMPRE]** — `build_toolgraph.py` escanea `skill_registry.json`, `algorithms.json`, `algorithm_memory.json`, `.claude/agents/` y `Zagentexecution/quality_checks/`. **Un `.py` util fuera de esas cinco y que no nombre ninguna no lo encuentra `graph_queries.py tool` jamas** — no por timing, por estructura. Medido s104 con `brain_v2/rebuild_progress.py`, resuelto registrandolo como algoritmo **A48**. **Que falta:** decidir si se anade `brain_v2/*.py` y `scripts/*.py` como sexta raiz, o si la via canonica es siempre una ficha en `algorithms.json`. Hoy hay **66 instrumentos invocables** en esos dos directorios y el nuevo detector de `artifact_wiring_check.py` dice que todos estan nombrados — pero eso puede cambiar con el proximo que alguien escriba.
> - **H133 [🟢 EL BUCLE DE MEJORA — tres pasos hechos, la triada abierta]** — **Los tres roles quedan fijados** (JP, s105): *si es para leer es SKILL; si decide, es AGENTE; si descubre, es MINERO*. Agentes y skills se especializan por **DOMINIO**; los mineros por **TIPO DE EXPLORACION** — ejes ortogonales, y por eso un minero sirve a cualquier dominio: no es que sea general, es que esta especializado en otro eje. **HECHO 1 — metodos cautivos:** `A64` sale de `authority-doc-reader` (leer el PDF necesita criterio y se queda dentro; comparar lo autorizado con lo pedido es determinista y sale fuera). Al abrir los otros tres agentes aparecio algo mejor: **seis mineros ya existian como script y ninguno estaba declarado** — dados de alta `A65` (reconciliacion del panel autorizado), `A66` (replicacion de maestro por API estandar) y `A67` (copia segura de variantes). **Agentes sin instrumento: de 5 a CERO; `INVOCA` de 34 a 42, sin tocar un solo prompt.** **HECHO 2 — propagacion:** `A63` publica 22 preguntas dirigidas en el bus, verificadas leyendo el bus y no la salida del script; 15 son sobre la ceguera del log a instrumentos que leen `rsau_audit_history` sin saberlo. **HECHO 3 — delegacion:** se cerro solo con el paso 1. **QUE FALTA:** la **triada sobre los trabajos previos** — `work_triad_check.py` da **14 de 15 incompletos**. Y lo que la reevaluacion destapo (**claim 618**): los **27 skills sin lector son DOS problemas** — DOCE con instrumentos que deberian leerlos y no lo hacen (`fi_domain_agent` con 15, `sap_company_code_copy` con 14), que es perdida real; y QUINCE que nadie deberia leer tampoco, que es tema dormido. Ademas `fi_domain_agent` y `hcm_domain_agent` son **SKILLS nombradas «agent»**: bien guardadas, mal nombradas. Termometro del bucle: **conectividad 19,7 por ciento** (`LEE` 72 / `DEBERIA_LEER` 293).
> - **H127 [🔴 BLOQUEA EL CIERRE DE INC-000016338 — rol `BNK_APP` de `B_REISS`]** — Bettina REISS (`10049633`) esta en los dos nodos de tramo de UIL (`50039526` validar, `50039525` firmar) desde el 2026-08-26 y **no puede firmar**: `AGR_USERS` le da 6 roles, **todos de HR**, ninguno de la familia `YS:FI:M:BCM_MON_APP______:*`. Hace falta `YS:FI:M:BCM_MON_APP______:UIL` por `PFCG` (Security, Patrick Ikouna) **mas primer logon** (`USR02.TRDAT = 00000000`, nunca ha entrado). Precedente: los otros cinco firmantes de UIL ya tienen ese rol derivado, no es diseno nuevo. **Es el MISMO bloqueo que deja `INC-000011781` (Renata Ritter, UBO) abierto desde junio** — dos incidentes parados por la misma causa = toca procedimiento, no ticket. Detectado solo por `bcm_role_gap_check.py`.
> - **H128 [🟠 DECISION DE TRS — ¿migrar UBO/UIS al patron de tramos de UIL, o aceptar la divergencia?]** — Conviven **dos patrones validos** de tramo de importe (claim **613**): **UBO** nodo bajo con TODOS y nodo alto DISJUNTO; **UIL** nodo bajo con SOLO los limitados y nodo alto SOLAPADO 0→max. Cada uno hace directa una pregunta distinta — UBO *¿quien PUEDE aprobar ≤10.000?*, UIL *¿quien esta LIMITADO?* — y se eligio el de UIL porque es la pregunta que hace el carton. **No es un defecto que haya que armonizar**: subir el suelo del nodo alto de UIL quitaria a los cuatro sin tope los pagos por debajo de 10.000. **Decide TRS**, no el agente. Coste de tocar UBO: funciona hoy y el cambio mueve firmas sobre pagos reales. **Dependencia a re-verificar tras cualquier upgrade**: el patron de UIL solo funciona porque la determinacion devuelve la UNION (claim 612) y la columna `Priority` de `OOCU_RESP` esta VACIA.
> - **H129 [🟠 HACER OBLIGATORIO `--carton` Y ARCHIVAR LOS CARTONES QUE FALTAN]** — El control **ya funciona**: `bcm_signatory_reconciliation_check.py` calcula las DOS direcciones (`extras` y `missing`) y el 2026-08-26, corrido con `--entity UIL --carton`, devolvio `MISSING (1): 10097358`, exit 1 — caza a Yli-Hietanen sin ayuda. **Los 31 meses que lleva invisible en DOS entidades no los causo una herramienta ciega: los causo que `--carton` sea OPCIONAL y que no hubiera cartones archivados** (el repo tenia UNO, el de UIS; los dos de UBO se leyeron en `INC-000011781` y nunca se guardaron — hueco 8 del skill). **Que hacer:** (a) recuperar los cartones de UBO del `.eml` de INC-000011781 y archivarlos; (b) pedir a TRS los de IIEP, UIL-restantes y UNES; (c) hacer que el health check trimestral corra `--carton` para CADA entidad y falle si falta el fichero, en vez de pasar en verde por no mirarlo.
> - **H130 [🟡 GATE DEL `BEGDA` — segunda ocurrencia, toca mecanizarlo]** — La spec dijo `BEGDA=20260811` (fecha de la carta, *as of immediate effect*) y DBS puso `20260826`, la de ejecucion: **15 dias** en los que Reiss estaba en el panel del banco y no en el enrutado de SAP. En `INC-000006313` fueron **7 dias**. Por `feedback_second_occurrence_earns_a_procedure` esto ya debe dejar un **check recurrente**, no otra viñeta: comparar el `BEGDA` de las filas nuevas de `HRP1001` contra la fecha de la carta archivada en el carton y fallar si no coinciden.
> - **H116 [🔴 EL AGUJERO MAS GRANDE DEL MODELO — 39 de 49 skills SIN NI UN LECTOR]** — Medido con `brain_v2/toolgraph.json`: **`LEE` 34 aristas frente a `DEBERIA_LEER` 283**. Por cada relacion que existe, faltan ocho. `sap_payment_bcm_agent` son **106 KB de metodo de banca con CERO lectores** y 16 artefactos trabajando sobre sus mismas tablas. **El caso que lo destapo:** `config_transport_prerelease_check` se escribio y se **ARREGLO DOS VECES** sin abrir `sap_transport_intelligence`, que documenta que `OBJFUNC=M` **borra la tabla ENTERA en destino** y que `E071K` vacio tambien significa **ROL** — las dos cosas cambian su veredicto. **Que falta:** correr `python Zagentexecution/quality_checks/skill_binding_check.py` (da candidatos, no veredicto — el de mayor solape NO siempre es el bueno) y, por cada uno, nombrar el skill en el agente (`.claude/agents/<x>.md`) o en la ficha del algoritmo. **La relacion va en el STORE, no en la prosa**: un nombre citado en un `.md` no se consulta ni se recorre. **58 algoritmos y 5 agentes** sin skill declarado.
> - **H117 [🟠 8 ALGORITMOS ARREGLADOS CUYA SALIDA NO SE PERSISTE]** — `lands_in: PENDIENTE` en **A39, A40, A42, A43, A46, A47, A48, A49**. Tres de ellos (A47, A48, A43) se **arreglaron hoy** y su codigo esta bien: lo que falta es el store. Sin el, cada analisis vuelve a derivar lo mismo — que es exactamente lo que costo A34 antes de aterrizarlo. **Que falta:** por cada uno, decidir si su salida merece store o si su sitio es un claim, y escribirlo. Medidor: `pending_inventory.py`.
> - **H118 [🟠 45 MINEROS QUE NUNCA PASAN POR EL FORO]** — De 52 registrados con `mining_kind`: **45 tienen script que corre y no han pasado nunca**; 7 no aplican (puerta, enrutador, bus). El mecanismo ya es automatico — `metodo.avisar()` marca la visita y pone delante las preguntas abiertas — asi que **se marcaran solos al correr**. **La pregunta real es la otra:** los que no corren NUNCA. Un minero registrado que no se ejecuta es documentacion. Medidor: `mining_collaboration_check.py`. Estado del foro al cierre: **5 respuestas, 0 preguntas sin destinatario, 0 ocasiones perdidas** (eran 1, 11 y 1).
> - **H119 [🟠 93 REGISTROS DIVERGENTES DEL ESQUEMA — es MIGRACION, no un umbral que relajar]** — `store_schema_check.py` (declarado hoy; era uno de los 11 que **no corrian nunca**): **76 claims sin `status` ni `resolved_session`**, **16 reglas sin `created_session`** (`feedback_structured_addr_*`, `feedback_dmee_*`, `feedback_ekkn_8_field_rfc_ceiling`...), **1 incidente sin `process`** (INC-CLASS-LOSS-2026-06), mas 274 avisos de claves usadas una sola vez. El fallo que lo origino tumbo un rebuild con `KeyError:'claim'` y dejo 15 claims fuera del estado agregado. **Que falta:** migrarlos. Ponerlo verde bajando el umbral seria certificar un store divergente.
> - **H120 [🟠 27 CHECKS NO SE CORRIERON, Y NO ESTAN LIMPIOS: ESTAN SIN MIRAR]** — La auditoria `--tier gate` **descubre 50 y corre 24**. Los otros 26-27 son `live`/`analysis`, e incluyen `fsv_coverage_check`, `ob09_vs_variant_check` y `fx_revaluation_scope_check` — **justo los que se arreglaron hoy**. **Que falta:** una corrida `--tier all` con VPN antes de dar nada por verde. **Y dos checks se comen 10 de los 17 minutos sin terminar** (`production_discipline_check`, `inc5638_fm_ps_avc_misalignment`, TIMEOUT a 300s): un TIMEOUT cada corrida es como una puerta se convierte en mueble. Arreglando esos dos la auditoria baja a ~7 min. Mediana actual: 2,6s.
> - **H121 [🟠 37 IDENTIFICADORES QUE EL CODIGO TOCA Y EL BRAIN NO EXPLICA — 8 gatean una rutina que puede BLOQUEAR]** — Familia `ZTHRFIORI_*`: `BREQ` (9 rutinas), `HREQ` (6), `REQSTA` (6), la vista `ZV_HRFIORI_REQ` (5), `ATTACH` (4), `DAPPRV` (4), mas `EG_MAI` (7) y `RS_MAI` (5); llamados desde `CREATE_REQUEST`, `CANCEL_REQUEST`, `DELETE_ATTACHMENT` y `HANDLE_INFOTYPE_0965`. Con `ZTHR_EG_ADVANCE` / `ZTHR_EG_CLAIM` colgando del mismo sitio. **Y el 'no lo sabemos' era 'no lo alcanzamos':** `hcm_domain_agent/SKILL.md:164-165` YA define `ZTHRFIORI_BREQ` (cabecera de peticion de prestacion, GUID/STATUS/PERNR) y `ZTHRFIORI_EG_MAI`; `sap_reverse_engineering/SKILL.md:61` añade sus codigos de estado 00-09. Claim 607. **Que falta:** que hacen HREQ, REQSTA, ATTACH, DAPPRV y la vista; **que transicion de estado BLOQUEA**; y si EG es Education Grant (lo sugiere `HRPADUNEDGR` y **no esta verificado**).
> - **H122 [🟡 DOS CLAIMS CON DEUDA DE MEDIDA DECLARADA Y SIN PAGAR]** — **216**: faltan los **recuentos de USUARIO por dominio** (`COUNT(DISTINCT SLGUSER)` agrupando por `TRIM(PARAM1)`, con un script VERSIONADO que guarde su salida — la corrida original no se conservo). Los recuentos de EVENTO ya estan re-medidos. **219**: falta `COUNT(*)` y `COUNT(DISTINCT SLGUSER)` `WHERE TRIM(PARAM1) IN ('SA38','SA39','SE38')` sin filtro sobre SLGTC. **Y claims 28, 107, 205 marcados `needs_review`** que no son de esta sesion y llevan ahi.
> - **H123 [🟡 E071 INCOMPLETO, DECLARADO — 5.941 cabeceras SAPK sin contenido]** — `e071` tiene 2.369.936 objetos en 14.939 de las 20.915 cabeceras de `E070`. De las que faltan, **5.941 son SAPK y esta VERIFICADO que SI tienen contenido** (leidas de una en una: 713, 205, 393 objetos) — no vinieron por un defecto de particion **ya arreglado** (se partia con alfabeto `0-9A-Z` y se llaman `SAPK-10001INIWPGW`, con GUION en la quinta posicion). Las ~35 restantes se leyeron una a una y estan **VACIAS DE VERDAD**. Claims 593-595. **Que falta:** correr `python scripts/extraction/extract_fsv_structure.py --solo transportes` con VPN; el completar ya es idempotente (indice unico + `INSERT OR IGNORE` + asercion que PARA si suben objetos y no suben transportes).
> - **H124 [🟡 A40 SIGUE PARCIAL — y su exit 0 NO significa nada en dos casos]** — Arreglado hoy: resuelve las TAREAS HIJAS por `E070.STRKORR` y analiza la UNION (la orden de Egipto pasaba de exit 0 a exit 1); el eje de entidad se BUSCA (primer campo clave que discrimina) en vez de fijarse al 1o tras `MANDT`; y lee `OBJFUNC` (`M` = borra la tabla entera en destino, `D` = borra el objeto). **Lo que NO cubre:** el alcance de un **ROL** (objeto logico, `E071K` vacio, claves resueltas por R3trans sobre `AGR_*`) — ahi sale **exit 2, no analizable**. Y una clave BORRADA sale `[NO-OP]`, indistinguible de un troceo fallido. **Ver H106 y H112**, que dependen de el y llevan la advertencia.
> - **H125 [🟢 EL COORDINADOR EXISTE Y NADIE LO LLAMA SOLO]** — `python brain_v2/graph_queries.py tool para "<tarea>"` contesta que SKILL leer primero, que algoritmo ya existe, que agente lo hace, que puerta lo vigila y **que sabemos ya** (claims, incidentes, dominios); y clasifica la forma de la tarea: `REPETIDA` / `COMPARAR_ESTADO` / `DESCUBRIR`. Esta en `BRAIN_INDEX.md` y en la regla CRITICAL. **Que falta:** que se llame SOLO al empezar una tarea, en vez de depender de que alguien se acuerde — que es el mismo fallo que el coordinador existe para cazar. Escrito en el `improve` de A52.
> - **H126 [🟢 EL REPARTIDOR DEL FORO CRUZA POR PALABRAS]** — `colaborar._capacidades()` paso de 11 a **99** capacidades (catalogo a mano + 79 algoritmos + 13 agentes) tras descubrir que **dos preguntas llevaban semanas sin destinatario teniendo la respuesta escrita**: A19 (`que HACE un objeto` -> la capa de codigo) y A30 (`arbitrar` -> el **agente** `mining-arbiter`, y el repartidor no sabia que existieran agentes). **Que falta:** el cruce sigue siendo por PALABRAS, asi que una pregunta con otro vocabulario se queda sin destinatario y el silencio se lee como 'nadie lo sabe'.
INCOMING (2026-08-19 — s101: Egipto pasa de especificacion a fichero probado, y la mecanizacion caza un defecto vivo).**
> Done-since: `INC-EGYPT-PPC` construido en D01 (ticket real **INC-000016101**) y **probado por las dos mitades** — bloquea sin codigo (`ZFI-036`, GB931 UNES paso 012) y renderiza con codigo (fichero `pain.001` con `<Ustrd>/Payment for goods or services received/INV/224938`, identico a la prediccion hecha simulando CM003/CM004 antes de generarlo). Cero ABAP confirmado por ejecucion. Cazado y reparado de paso un dano colateral a **Indonesia** dentro del transporte de Egipto. Claims 524-529, 4 reglas nuevas, 2 checks nuevos, los dos companions actualizados. Artefacto: `Zagentexecution/tasks/2026_08_19_egypt_ppc_d01_test/`.
> - **~~H101~~ ~~H102~~ [CERRADOS 2026-08-20 — Egipto NO hacia falta]** — SG confirmo que no existe codigo nuevo para Egipto y que el canal Citi no lleva ese flujo (**SocGen 93,1% del corredor vs Citi Egipto 0,9%, y en cheque prenumerado, que no es RTGS ni CBFT**). No se transporta nada. Claim 530. **Sustituidos por H106.**
> - **H112 [🔴 DURABILIDAD — lo unico con riesgo de PERDIDA, no de retraso]** — El disco de copias `D:\claude_backups` **esta desconectado**; ultima copia 2026-08-19 17:56. Mientras siga asi, el **Golden DB (15,2 GB, gitignored) existe solo en este disco**. Y hay trabajo que solo vive aqui: **sin remoto y sin commitear** en `FINCLOSSING` (15), `SCRP` (4), `unescore20-PPM-brain` (7); **sin subir a origin** en `unesco-sap-brain` (4) y `unescrp` (1). Este proyecto esta limpio y en origin. El medidor lo ve solo desde s102 (`meta_capability.assets_backed_up` paso de estimacion ciega a MEDIDO, y hoy marca 0.00 con la razon correcta: *sin destino accesible*). **Que falta:** reconectar el disco y correr `python scripts/backup_golden.py --dest D:\claude_backups`; y decidir si los tres proyectos sin remoto lo tendran, porque hoy no hay nada que los proteja.
> - **H113 [🟠 REUBICACION — quedan 50, ya no hay ninguna CRITICAL]** — Las **22 CRITICAL sin punto de uso se reubicaron a 0** en s102 (a checks, scripts, skills, docs de dominio y `CLAUDE.md`). Quedan **50 reglas sin cita**, todas HIGH o menores. **Que falta:** el mismo tratamiento — por cada una, contestar *donde esta alguien en el momento en que aplica* y citarla ahi. **No se retiran** (regla `feedback_never_retire_anything_without_evidence`, CRITICAL): 'no citada' es un proxy, no evidencia. Mecanizacion del corpus: 11% -> 16% (37 de 221). El indicador a subir es ese, no el numero de reglas a bajar.
> - **H114 [🟡 HUERFANOS — 8, destapados y no arreglados]** — `artifact_wiring_check.py` (nuevo en s102) encuentra **8 artefactos que nadie invoca**: 6 scripts sin llamador (`agent_trace_hook.py`, `backfill_closing_activities.py`, `backup_projects.py`, `brain_coverage_audit.py`, `build_closing_activities_pdf.py`, `ingest_fx_revaluation_structured.py`) y 2 JSON que ni su autor relee. La mayoria son anteriores a s102. **Que falta:** por cada uno, encadenarlo o dar la evidencia de que ya no aplica — nunca borrarlo por no estar citado.
> - **H115 [🟢 REUBICAR, NO MECANIZAR — dos reglas mal colocadas]** — `feedback_predict_the_output_before_you_generate_it` y `feedback_a_warning_in_a_document_is_not_a_measurement` son **epistemologia, no procedimiento**: describen como razonar, no un momento con una accion. Su sitio es **CP-003** como elaboracion, no las posiciones 219/220 de un fichero que nadie abre. **Que falta:** decidir si los Core Principles admiten elaboraciones — hoy son tres parrafos — y si no, aceptar que son prosa y dejar de contarlas como deuda de mecanizacion.
> - **H106 [🟠 HIGIENE — desarmar D01 — JP CONFIRMA 2026-08-21]** — Decidido borrar la configuracion COMPLETA de Egipto en D01 (no solo el interruptor) y el transporte. PRE-readback guardado en `Zagentexecution/tasks/2026_08_19_egypt_ppc_d01_test/PRE_DELETE_snapshot_D01.json`: 5 filas T015L + 10 YTFI_PPC_STRUC + 1 YTFI_PPC_TAG + las 17 claves del transporte + las 18 filas de Indonesia como control. Orden: `YTFI_PPC_STRUC` primero (apaga el bloqueo), luego las inertes, luego `SE10`. **Riesgo a vigilar:** borrar en SM30 puede capturar la clave de un pais vecino, y ahora la operacion es un BORRADO. ~~Verificar despues con `config_transport_prerelease_check.py` y el diff completo de las tres tablas.~~ **RETIRADO 2026-08-26** -- motivo: el instrumento no puede ser la puerta de un BORRADO sobre customizing (A40 `DEFECTO_VIVO`). **EN SU LUGAR:** verificar despues con el **diff completo de las tres tablas D01 vs P01** (el metodo manual que encontro Indonesia el 2026-08-19), contra el PRE-readback `PRE_DELETE_snapshot_D01.json`, incluidas las 18 filas de Indonesia como control. **NO USAR `config_transport_prerelease_check.py` como puerta de este borrado**: sobre `D01K9B0FXE` devuelve exit 0 sin analizar nada (medido 2026-08-25 -- imprime 'E071K vacio' porque las claves viven en E071K de la TAREA, no de la orden), y una clave BORRADA (inexistente en ambos sistemas) sale `[NO-OP]` con exit 0, indistinguible de un troceo fallido (`brain_v2/methods/algorithms.json:1301` modo C). Su exit 0 aqui NO SIGNIFICA NADA. — El interruptor sigue ARMADO en D01: cualquier `FB60` a uno de los 716 proveedores con banco egipcio se bloquea sin motivo, y el transporte `D01K9B0FXE`/`D01K9B0FXF` existe sin liberar — si alguien lo libera por error, el bloqueo arranca en P01. **Accion:** borrar las filas `EG` de `YTFI_PPC_STRUC` (es el interruptor, rollback = un delete) y borrar el transporte. `T015L` y `YTFI_PPC_TAG` pueden quedarse, son inertes. No se pierde nada: la configuracion exacta esta en el companion §11, en los claims 526/527 y en `Zagentexecution/tasks/2026_08_19_egypt_ppc_d01_test/`. Se preserva el CONOCIMIENTO, no el artefacto.
> - **H111 [🟡 DEFECTO PRE-EXISTENTE, menor]** — `companions/treasury_operations_companion_v2.html` tiene **3 `<div>` sin cerrar** (235 abren / 238 cierran). Verificado que es previo a los cambios de s102: la diferencia neta que introdujo esta sesion es 0. No se toco a ciegas. **Que falta:** localizar los tres y cerrarlos, y de paso mirar si el resto de companions estaticos tienen el mismo problema — hoy nadie lo comprueba, y un HTML mal balanceado renderiza distinto segun el navegador.
> - **H110 [🟠 EXTRACCION — sin esto el modelo de bancos esta cojo]** — **`FEBKO` es un extracto PARCIAL**: 31.416 filas, solo 38 bancos y **solo 3 sociedades** (UNES, ICBA, MGIE). **`SOG01`, con 1,9M de pagos, tiene CERO filas**; faltan UBO, ICTP, IIEP, UIL y UIS enteras. Sin ello no se puede responder que bancos reciben extracto electronico, y cruzarlo produce conclusiones invertidas — casi se publica que los hubs no reciben extractos. Claim 535. **Que falta:** extraer `FEBKO` completo (todas las sociedades) por `gold_refresh.py`, y entonces anadir al modelo de bancos la dimension **recibe extracto / es cuenta receptora** — hoy declarada MISSING_INPUT y no como columna de ceros. **Ya se ve algo aun con el extracto parcial:** `SCB04`, `CIT13`, `SCB18`, `SBN01` y `SCB19` tienen extracto y CERO pagos — son **cuentas RECEPTORAS**, un rol al que un modelo derivado solo de `REGUH` es ciego por construccion, porque `REGUH` solo ve dinero saliendo.
> - **H109 [🟢 OPORTUNIDAD MEDIDA — H_IMPROVE, y la palanca NO es la que parece]** — **36 de 37 bancos de oficina de campo pagan el 100% en cheque.** Brasil (7%) y Canada (0%) son las excepciones que prueban que se puede salir del papel. Pero de las ~10.400 lineas en papel local, **solo 647 (6%) son candidatas claras a centralizar** — Libano 288, Jordania 206, Etiopia 153, y en las tres el hub YA paga a ese pais. **5.766 lineas (55%) estan bloqueadas por DATOS BANCARIOS DE PROVEEDOR ausentes**, y 3.952 por jurisdiccion. Claim 534. **La convergencia que esto revela:** los 1.225 proveedores egipcios sin LFBK (claim 489), los 8.149 sin CtrySubDvsn de INC-PSTLADR-NOV2026 y estas 5.766 lineas **son la misma causa** — el maestro de proveedores incompleto. Tres frentes, una palanca. **Que falta:** (a) confirmar con Tesoreria la clasificacion de jurisdiccion, que hoy es conocimiento mio y no un dato del sistema; (b) rehacer el corte por IMPORTE y no por lineas; (c) decidir si la campana de datos bancarios de proveedor se ataca como UN proyecto en vez de tres.
> - **H108 [🟡 HIGIENE DE MAESTRO — bancos casa muertos]** — Tres cuentas de banco casa configuradas en UNES sin mover dinero desde hace anos: **CHA01** (JPMorgan Chase, ultima ejecucion **2020-01**), **DNB01** (Noruega, **2017-07**) y **WEL01** (Wells Fargo, **2023-01**, 4 lineas ese ano). Las tres son cuentas de TESORERIA entre cuentas propias (metodo A). **SCB14** (Standard Chartered) si esta vivo (2026-04). Ademas **DEU01** — hub de UIL con 109 destinos — no ejecuta un pago desde **2023-09**: no es una cuenta de tesoreria, es un hub que se quedo callado, y merece pregunta aparte. Claim 533. **Que falta:** confirmar con Tesoreria si se cierran o se mantienen abiertas a proposito. Una cuenta abierta y sin uso es superficie de riesgo, no un dato neutro.
> - **H107 [🟢 MODELO — hecho, queda extenderlo]** — **`brain_v2/house_bank_roles.py`** contesta ahora "quien sirve este corredor y con que rol" en un comando (paso 2d del rebuild, artefacto `house_bank_roles.json`). Nacio de que el dato de Egipto estaba medido desde el 17-ago y disperso en prosa. **Que falta:** llevarlo al capability_model como evidencia de `Payment_BCM / F_INTERFACE_FILE` y `A_PROCESS`, y decidir si el mismo patron — rol operativo derivado en vez de declarado — aplica a otros canales (RFC destinations, interfaces de fichero).
> - **H103 [🟠 DEFECTO VIVO EN P01]** — **`T015L INA` tiene dos espacios** entre codigo y narrativa: `'P1203  Maintenance of international institutions such as offices of IM'`. India separa con `;`, asi que emite `P1203; Maintenance of...;INV;<XBLNR>` con un blanco de mas hacia el banco. Unica fila rota de las 73. Arreglo = borrar un espacio por SM30, cero ABAP. **No medido**: cuantos pagos han usado `INA` (REGUP no esta en el Gold DB). Claim 529 — encontrado por el check E/F en su primera corrida, nadie lo buscaba.
> - **H104 [🟠 INSTRUMENTAL — el guardian tiene el defecto que vigila]** — **`knowledge_reachability_check.py` sale con exit 0 mientras el indice que vigila miente.** Comprueba que el `id` este en `BRAIN_INDEX.md`; nunca comprueba que lo que el indice DICE sea actual. Toda la sesion s101 el indice decia `SPEC_READY` y proponia un plan equivocado en tres puntos, y el check lo daba por bueno. Es el patron del claim 496 — *el control prueba presencia, no correccion* — reproducido en nuestro propio instrumental. **Que falta:** que el check compare el `status`/`next_action` del indice contra el store, no solo la presencia del id.
> **⮕ FRONTERA DE ALINEAMIENTO DE CUSTOMIZING (JP 2026-08-20, s102).** Alinear master data NO alinea el sistema: las cuentas GL de UNES quedaron al 100% en los tres sistemas y el customizing sigue derivado. **TRES frentes, y de cada uno falta DECIDIR EL METODO** — encontrar el canal o autorizar una excepcion de escritura directa (registro EXC-* en `.agents/skills/sap_master_data_sync/SKILL.md`). Escalera de canales: (1) API estandar · (2) BC-Set, que escribe por el framework y graba en orden pero exige crear el BC-Set a mano una vez por sistema · (3) escritura directa, prohibida salvo excepcion nominal con las diez puertas.
> - **H114 [🔴 ALINEAR OB09 / `T030H` — y hay un defecto vivo de 20 M EUR]** — **(1) DEFECTO REAL, no de alineamiento:** `4041011` tiene **4 partidas abiertas de 5.000.000 EUR** (20-05, 20-07 y **dos del 20-08-2026**) y **no la selecciona ninguna variante de F.05**, **una de ellas al HABER**, asi que la exposicion NETA son **10 M EUR** (11.569.086,65 USD) y **no se revaluan**. Esta en la posicion de balance `FS10 1.1.2.1 Short Term Deposits` -dentro del grupo de inversiones- con `XOPVW='X'`; y `4041013`, que SI esta en la variante, tiene la misma naturaleza y solo UNA partida EUR abierta. Medido en vivo con `BSIS` cuenta a cuenta. `4041012` (0 abiertas) y `4041014` (solo USD) son **inertes**, no defectos. **Preguntar a Tesoreria si 4041011 debe entrar en `UNES_DEPOSIT`.** **(2) ALINEAMIENTO:** `T030H` diverge entre sistemas — el check detecta ademas dos `[DERIVA]` (`0001122421`, `0001122424`) con fila en P01 y no en D01. **Metodo:** `T030H` **si es transportable** (probado con `D01K9B0FXP`: funcion Q = **tarea**, 2 claves en E071K; ~~0 intrusas~~ **RETIRADO 2026-08-26**: era **vacuo**, no medido -- en `T030H` el check deriva el eje de entidad como el 1er campo clave tras `MANDT` (= `KTOPL`) y en D01 solo existe `UNES`, asi que la rama INTRUSA no podia disparar jamas; el discriminador real, `HKONT`, no se mira. El alcance de ese transporte **NO ESTA VERIFICADO**, y la **ORDEN padre** (`E070 WHERE STRKORR='D01K9B0FXP'`), que es lo que se libera, no la ha mirado nadie), asi que el canal ortodoxo existe: configurar en D01 y transportar. **No necesita excepcion** -- pero **ATENCION**: esa conclusion se apoya en la **EXISTENCIA del canal**, que sigue en pie, **no** en la limpieza del alcance. Medidor: `ob09_vs_variant_check.py` (exige las TRES condiciones desde s102). Claims 549, 540-refutado.
> - **H113 [🟢 ALINEAR VARIANTES DE F.05 — CANAL RESUELTO 2026-08-21, queda ejecutar]** — **`RS_CREATE_VARIANT_RFC` escribe y `RS_VARIANT_DELETE_RFC` borra**, probado extremo a extremo en D01 con una variante desechable y verificado releyendo (claim 550). **No hace falta excepcion**: es peldaño 1, API estandar. `RS_VARIANT_CHANGE_RFC` NO vale (sin tabla de contenido, es de dialogo), asi que modificar una existente = **borrar y recrear** con el contenido completo — destructivo, exige snapshot PRE y readback POST. **Y el aviso que cuesta caro: lo que no se envia SAP lo rellena con defectos EN SILENCIO** (la prueba perdio 9 parametros de pantalla), asi que hay que mandar TODOS los parametros, no solo la seleccion de cuentas. Estado del problema: — `UNES_DEPOSIT` tiene **tres contenidos distintos** con el mismo nombre: P01 **17 valores sueltos EQ** (ya con 4041018), D01 rango `4041011-13` + 2 sueltas redundantes, V01 rangos `4041011-14` y `5091010-12` + 10 sueltas. **`VARID.TRANSPORT='F'`: no se transportan NUNCA.** Consecuencia: **D01 y V01 no reproducen F.05 de produccion** — 4041017, la unica cuenta con 198 partidas EUR abiertas y 12 documentos `FBB1`, **no esta seleccionada en ninguno de los dos**. **Metodo pendiente de decidir:** no hay API de escritura de variantes (`RS_VARIANT_CONTENTS_RFC` solo LEE); las opciones son teclear a mano en cada sistema, o investigar `RS_CREATE_VARIANT_RFC` / `RS_VARIANT_CHANGE_RFC`, que **si estan remote-enabled** y no se han probado. Se lee con el agente `variant-intelligence`. Claim 542.
> - **H112 [🟠 ALINEACION DE CUSTOMIZING — la FSV, y esta BLOQUEADA por un candado de cliente]** — **Alinear master data NO alinea el sistema.** Con las cuentas GL de UNES al 100% en los tres sistemas (s102: 2 creadas en D01, 33 en V01, readback OK), la **version de balance** sigue derivada. ~~`FAGL_011ZC` faltan **195** intervalos en D01 y **131** en V01; `FAGL_011PC` **287** y **278**; `FAGL_011QT` 179 y 96; `FAGL_011SC` 51/22 mas **229/213 que DIFIEREN**.~~ **REETIQUETADO COMO HISTORICO 2026-08-26** -- motivo: el `287`/`278` de `FAGL_011PC` se midio por **clave subrogada** y no cuenta nodos ausentes; y el estado ya no es el de entonces. **Medido 2026-08-20 (s102), estado de ENTONCES:** `FAGL_011ZC` faltan **195** D01 / **131** V01; `FAGL_011QT` 179/96; `FAGL_011SC` 51/22 mas **229/213 que difieren**; `FAGL_011PC`: **numero de nodos ausentes DESCONOCIDO** (medido por clave subrogada). **ESTADO ACTUAL EN CONFLICTO Y SIN RESOLVER:** `brain_v2/methods/algorithms.json` (2026-08-25) dice **0 faltan / 0 difieren / 0 extra** en las 8 tablas contra D01 y V01; `.agents/skills/sap_master_data_sync/SKILL.md:153` dice **V01 parcial, falta `FAGL_011QT`**. **Re-medir antes de dar H112 por cerrado.** `T011`/`T011T` identicas: el marco coincide y el contenido no. **El bloqueo:** SCU0/SCMP devuelven **`TB569`** — `T000.CCCOPYLOCK='L'` en P01 (nivel 2: sin disponibilidad externa). Es un candado DISTINTO del de modificabilidad y hay que leer los tres (`CCCORACTIV`, `CCNOCLIIND`, `CCCOPYLOCK`). **Dos salidas:** (A) Basis baja el candado a **`X`** en SCC4 —nivel 1, sigue protegiendo contra sobrescritura y **si** permite la lectura de comparacion—, ventana y vuelta atras; (B) sin SCU0: `RFC_READ_TABLE` **no** esta afectado, `fsv_alignment_check.py` ya lee P01 y emite la especificacion, y se teclea en **D01 por `OB58`** grabando en orden, con transporte **D01→V01**. **No hay API RFC para la FSV** (comprobado en `TFDIR`) y `FAGL_011*` son estandar, asi que el INSERT plano esta prohibido. **Decision previa que ahorra la mitad:** la deriva se parte casi por igual entre **FS10** (111 D01 / 65 V01) y **FS11** (84 / 66) — determinar si FS11 sigue viva antes de tocar nada. **RUTA AUTORIZADA (JP 2026-08-20): EXC-001** en `.agents/skills/sap_master_data_sync/SKILL.md` -> 'REGISTRO DE EXCEPCIONES AUTORIZADAS'. Unica excepcion vigente para escritura directa: FAGL_011PC/QT/ZC/SC, chart UNES, destinos D01 y V01, SOLO INSERT de filas ausentes, con las DIEZ PUERTAS y la G10 obligatoria (registrar las claves en una orden de customizing ~~y validar con `config_transport_prerelease_check.py`~~ -- **RETIRADO 2026-08-26**). **ATENCION: G10 esta hoy SIN VALIDADOR.** `config_transport_prerelease_check.py` esta en `DEFECTO_VIVO`: no analiza la ORDEN que se libera (las claves viven en E071K de la TAREA) y no lee `E071`, que es justo donde deja rastro el `R3TR TABU` que G10 prescribe. Registrar las claves igualmente y **dejar la validacion de alcance marcada como PENDIENTE**, verificada a mano por diff completo de las tablas; **no dar G10 por pasada con un exit 0**. Alternativa ortodoxa si se prefiere: `OB58` en D01 grabando en orden + transporte D01->V01. Hoja de lanzamiento: `knowledge/domains/FI/fsv_alignment_runsheet.md`. Medidores: `fsv_alignment_check.py` y `ob09_vs_variant_check.py` -- **ANTES de creer su exit 0, ASEVERAR EL SID**: ambos aceptan `--systems` sin validarlo, y un SID sin bloque `SAP_<SID>_` en el `.env` cae al bloque generico, **que ES D01 y lleva password**, asi que conectan con EXITO al sistema equivocado y lo certifican alineado (claim 597; A43 `DEFECTO_VIVO`). `ob09_vs_variant_check.py` arrastra ademas A47 (`DEFECTO_VIVO`, claim 599). Claims 546, 547, 548.
> - **H113 [🟠 LAS VARIANTES DE F.05 DIVERGEN Y NO SE TRANSPORTAN]** — `UNES_DEPOSIT` tiene **tres contenidos distintos** con el mismo nombre: P01 **16 valores sueltos EQ**, D01 rango `4041011-13` + 2 sueltas redundantes, V01 rangos `4041011-14` y `5091010-12` + 10 sueltas. `VARID.TRANSPORT='F'`: **no se transportan nunca**, cada sistema tiene la suya editada a mano. Consecuencia dura: **D01 y V01 no reproducen F.05 de P01** — la cuenta que de verdad se valora en produccion (`4041017`, 402,7 M EUR) **no esta seleccionada en ninguno de los dos**. Y el cruce OB09 x variante da cuentas ACTIVAS configuradas que ninguna variante selecciona: **P01 4041011, 4041012, 4041014**; D01 4041014 y 4041017; V01 4041017. **MEDIDO 2026-08-21 (claim 551):** la divergencia es HETEROGENEA -- D01 118 diferencias (76 seleccion + 20 modo + 22 residuo) en 11 variantes; V01 solo 15 (11 seleccion + 4 residuo) en 3. **PLAN POR FASES, nada ejecutado:** (1) V01 entero, bajo riesgo; (2) D01 solo seleccion limpia -- IBE_OI, ICTP_OI, IIEP_OI, UNES_DEPOSIT, UNES_OI_AR/AP; (3) **DECISION HUMANA** para ICBA_*, MGIE_*, UIS_OI y UIL_OI, porque alinearlas BORRARIA el nombre de sesion batch (PAR_BNAM, vacio en P01 y con valor en D01) y cambiaria la bandera de alcance (PA_WEREF en P01 frente a PA_WEREN en D01); UIL_OI ademas difiere en 36 entradas de seleccion. Herramienta: `Zagentexecution/tasks/2026_08_21_variant_alignment/variant_align.py` (dry-run por defecto, snapshot PRE, restauracion automatica, verificacion POST). **Que falta:** (a) preguntar a Tesoreria si 4041011/4041012 —con exposicion EUR real— se dejaron fuera a proposito; (b) decidir si se alinean las variantes de D01/V01 a mano. Claims 540/542. Se lee con `RS_VARIANT_CONTENTS_RFC`, ver agente `variant-intelligence`.
> - **H105 [🟡 COBERTURA]** — **`REGUP` no esta en el Gold DB**, y eso deja dos cosas sin medir: el check D de `ppc_country_consistency_check.py` (uso degenerado — si un codigo se come el 60% de los pagos, el control es cosmetico) y el impacto real de H103. Es una extraccion, no un analisis.

> **⮕ INCOMING (2026-08-18 — s099: los quality_checks empiezan a correr solos, y encuentran cosas).**
> - **H91 [🔴 DATA QUALITY — pendiente, sin dueño asignado]** — **191 proveedores con `AKONT` atípica**, misma clase de defecto que INC-000006073. Detectado por `Zagentexecution/quality_checks/vendor_master_integrity_check.py` en su primera corrida automatizada. 127 grupos `(KTOKK,BUKRS)` analizados; el patrón dominante es `GVNT/UNES` usando `0002021011` cuando el 97% del grupo (2.378 pares) usa `0002021032` — 2,82% de cuota, muy por debajo del umbral del 5%. Ninguno tiene `GGB1`, así que no hay sustitución que lo explique. Incluye entidades reales (IUCN, CNRS, delegaciones permanentes, comisiones nacionales). **Qué falta:** decidir si es error de maestro o una categoría legítima mal etiquetada; si es error, corregir `LFB1-AKONT` por el canal autorizado (nunca escritura directa a P01). El check ya está en el tier gate, así que la cifra se vigila sola a partir de ahora.
> - **H92 [🟠 MODELO]** — **40 de 43 algoritmos no declaran `lands_in`** (`brain_v2/methods/algorithms.json`). El campo se añadió en s099 para la regla de "descubrir sin aterrizar" y sólo se aplicó a 3. Un algoritmo sin `lands_in` puede descubrir y no tener dónde dejarlo: es la versión sistémica del hueco que JP señaló con Purpose of Payment.
> - **H93 [🟠 RECUPERABILIDAD]** — **los companions no eran buscables por tema.** El trabajo de DMEE vive en `BCM_StructuredAddressChange.html` (965 menciones) titulado "BCM Structured Address Change" y etiquetado "finance": nada en su nombre ni en el registro dice DMEE. Resuelto para la búsqueda (`graph_queries.py search` ya alcanza los 15 companions con DMEE), **pendiente**: los companions siguen sin aparecer en `BRAIN_INDEX.md`, así que el conocimiento profundo no se anuncia solo al arrancar una sesión.

> **INCOMING (2026-08-18 cont. - s099: verificacion del backup).**
> - **H95 [CODIGO FALTANTE - pendiente]** - **la app Fiori `ZHROFFBOARDING` nunca se descargo.** 26 marcadores `.ERROR` en `extracted_sap/HCM/Fiori_Apps/Offboarding/bsp/BSP_ZHROFFBOARDING/`, todos `HTTP 404 - Resource /sap/bc/adt/bsp/applications/ZHROFFBOARDING/pages/ does not exist` contra D01. Su hermana `BSP_YHR_OFFBOARDEMP` si esta (65 ficheros en git). **Encaja con los 37 descubrimientos sin aterrizar, que son todos `ZTHRFIORI_*`**: HR-Fiori es justo la zona donde el cerebro no puede explicar lo que el codigo toca, y es la misma zona donde fallo la extraccion. No es casualidad, pero tampoco esta probado que sea la misma causa. **Que falta:** reintentar por otra ruta ADT (la de `pages/` no existe para esta app - probar `/sap/bc/adt/filestore/ui5-bsp/objects/`), o confirmar que la app fue borrada de D01 y el 404 es correcto.
> - **H96 [LIMPIEZA]** - **16 GB duplicados en `C:\Users\jp_lopez\projects\_golden_backups`**, de una ejecucion accidental de `backup_golden.py` sin `--dest`: ese script no tiene argparse, asi que `--help` LO EJECUTA. Quedo en el mismo volumen que el original, de modo que protege de un script defectuoso pero no de un fallo de disco, que es de lo que va el backup. Borrable - el bueno esta en `D:\claude_backups`, verificado (369 tablas, 5 vistas, bpja 135.794 identico, `quick_check=ok`). **ARREGLADO (s099):** `--help` imprime uso y sale 0, y una flag desconocida PARA con exit 2 en vez de caer al backup por defecto. `--help` era solo el caso que mordio: un `--dst` mal escrito hacia lo mismo. Verificado que ninguno de los dos escribe nada.
> - **H97 [DURABILIDAD - otros repos del ecosistema]** - el integrity gate detecta **repos hermanos sin remoto y con cambios sin commitear**: FINCLOSSING (15), SCRP (4), unescore20-PPM-brain (7); y **unesco-sap-brain con 4 commits sin subir**. Solo existen en este disco. No es este proyecto, pero es el mismo riesgo de durabilidad y nadie lo esta mirando.
>
> - **H98 [MODELO]** - **4 datasets de descubrimiento VARADOS**: corrieron, produjeron hallazgos, y ningun claim los cita. `E3_trigger_evaluation` (27 hallazgos, `brain_v2/methods/trigger_state.json`), `A3_two_axis_classification` y `A4_ordered_classifier_ladder` (18, `job_classification.json`), `B4_declarative_conformance` (5, `p2p_conformance.json`). Detectado por `Zagentexecution/quality_checks/finding_promotion_check.py`, con trinquete en 4. **Que falta:** promover lo que importe a claims, o declarar en `lands_in` por que ese dataset es entrada de otro paso y no fuente de conocimiento.
> - **H99 [MODELO - recuperabilidad]** - **el indice por entidad no tiene capa de alias ni de familia.** `entity DMEE` devuelve 15 companions y CERO claims, porque los claims que hablan de DMEE listan `FI_CGI_DMEE_EXIT_W_BADI` o `YCL_IDFI_CGI_DMEE_FR` en `related_objects`, no la palabra DMEE. Preguntar por el CONCEPTO no encuentra el analisis; solo preguntar por el nombre exacto del objeto. **Que falta:** una capa que agrupe una familia bajo su concepto (DMEE -> sus clases, exits y tablas), derivada del prefijo de nombre y de la co-ocurrencia, no escrita a mano.
>
> - **H100 [RIESGO -> PODA, pendiente]** - **78 escritores de SAP MUERTOS, listos para borrar.** Medido s099 (`brain_v2/sap_write_tool_reachability.json`): de los 88 sin kill-switch, **78 no los importa nadie y no los nombra ningun fichero vivo**; 9 estan nombrados por algo vivo y 1 lo importa su propio test. Casi todos en `Zagentexecution/mcp-backend-server-python/`: deploy_yfi_v2..v6, direct_insert_seoclass, complete_reconstruction, final_rpy_write, reposrc_insert, write_via_bridge, abap_bridge_*. **Que falta:** decidir la forma de borrado. Propuesta: mover a `Zagentexecution/_obsolete/` en un commit propio (reversible por git) en vez de `rm`, revisar antes los 9 nombrados uno a uno, y NO tocar los dos falsos positivos que el hook `stop_integrity_hook.py` usa de verdad (`process_mining/accumulate_problems.py`, `method_registry.py`). Dos de los 78 pueden ser el registro de la recuperacion de INC-CLASS-LOSS: comprobarlo antes.
>
> **Reward function**: items_shipped - items_added > 0 per session. Net-zero is failure.
> **Growth paradigm**: Skills grow, never consolidate. Memory grows, no line limit. Knowledge is routed via `skill_coordinator`, never compressed.
> **⮕ INCOMING (2026-06-21 — log accumulator + RSAU audit + process-mining Tier 0/1/2; facts promoted by steward S-083, claims #212–216).** Pending backlog (H66–H70):
> - **H66 [BLOCKING for schedule]** — BASIS **keytab/headless SNC** so the 14-day `accumulate_logs.py` runs unattended (interactive Kerberos ticket dies ~10h, fails overnight — claim #215). JP raises the ticket.
> - **H67** — complete volatile-log capture: **SM21 syslog** `SALC_MSC_READ_SYSLOG` returned 0 lines (verify ONLY_LOCAL/window/per-server); **ST22 dumps (SNAP)** need the dump FM (not RFC_READ_TABLE); rerun **9 failed RSAU chunks** (idempotent); decide+apply the **RSAU type-retention filter** (keep Dialog Logon+Transaction Start+User Master Changes+High; drop RFC machine noise ~80%).
> - **H68** — process-mining next tiers: **formal alignments conformance + temporal bottlenecks**; **label custom cockpits** YFM1/ZICTP_COCKPIT/YKBLP_N via the brain (comprehension gap = real master/budget maintenance, the moat); **SoD permission-level (AGR_*)** + declared-vs-actual reconciliation; **roll methodology** to Payment/FI/Treasury/PSM; LLM-native labeling. Scripts in `process_mining/` (committed 2a2b94f/c4926f0/9b4fb1a/62b5a9e). Maturity 12.5%→~25%.
> - **H69** — Gold DB catalog: extend beyond ~26/306 tables; **rename upgrade tables to real SAP names** (`tpalog_upgrades`→`tpalog`, `tbtco_upgrade2026_jobs`→`tbtco` subset). See `knowledge/gold_db_table_catalog.md`.
> - **H70** — decisions: move `accumulate_logs.py` to git-tracked `scripts/` (currently gitignored local-only); Golden DB (~6.4GB) + `~/.claude` memory remain LOCAL-ONLY → need disk/offsite backup.
>
> **⮕ INCOMING (2026-06-21 cont. — OPERATING-MODEL discovery + PROBLEMS + SoD; steward S-085, claims #220–231).** Done-since: **H67 ✅** (problems accumulator `process_mining/accumulate_problems.py` captures ST22 dumps + SM21 syslog in one P01-safe call `/USE/BL_GET_SHORTDUMPS`; RSAU signal view `rsau_audit_signal` = 36% signal; SM21 syslog retains only ~7d). **H68 partial** (cockpits labeled; AGR_* still open). New actionables (H71–H80), redefined from the full session so findings escalate as TASKS, not notes:
> - **H71 [🔴 CONTROL — ✅ ANALYZED 2026-06-22 (a+b+c); escalate remediation to controls/treasury]** — **Write-channel SoD.** CONFIRMED at behavioral AND declared (AGR role) levels — full writeup `knowledge/domains/Security/h71_write_channel_sod_remediation.md`, claims #237–240. **Conflict 1** = Brasília AP (E_SILVA/L_NEVES/**+C_SOUZA/+B_LOPES**, identical `Y_UBO_*` bundle) post GR+invoice+PO (ACTVT 01/02; vendor-bank role is display-only) = self-approve 3-way-match → **R$ 264.7M (~US$49M), 9,411 POs, 100% with GR**. **Conflict 2** = HQ ICTP (MP_ANCUTA `Y_ICTP_SIS` vendor+PR+PO change; S_STANTIC) control 5,084 vendors + 77K PR changes → **~EUR 11.8M** cleared AP to controlled vendors. **ROOT:** `S_RFC=*` (Y_ICTP_COMMON, Y_UBO_ADMINISTRATION) + custom `ZBAPI_VENDOR_CHANGE` does NO `F_LFA1` check (S_STANTIC changed 6,972 vendors with no F_LFA1 grant) → role-split alone is cosmetic; control must move to call/data layer + SAP-native approval (T055F dual-control vendor bank, MRBR invoice release, PR/PO release creator≠releaser). **Remaining:** execute remediation (BASIS/Security + Controls); pull MSEG.USNAM for same-PO self-match. Evidence: `knowledge/system_operating_model_rfc.md` §items-5-9.
>   - **⚠ï¸ SPECIAL HANDLING (not an autonomous fix — human escalation required):**
>     1. **Controls/fraud-risk escalation, not a tech ticket.** Owners: **Controls/Treasury** (business SoD owners) decide remediation acceptance; **BASIS/Security** change roles (kill `S_RFC=*`) + activate SAP config (T055F sensitive-field dual control, MRBR, release strategy); **Dev** adds `AUTHORITY-CHECK` to `ZBAPI_VENDOR_CHANGE`. We do NOT change prod authorizations/config ourselves.
>     2. **Custom-BAPI fix follows BROADCAST-007:** own Z-objects only → D01 dev → **released transport** → ATC-REST gate → **JP 4-eyes**. No ADT write; no change in P01.
>     3. **🔴 NO QAS** = the structural test risk for these role/config changes — flag it explicitly; there is no QA tier to validate before prod (escalate as the gating risk).
>     4. **Sensitive** — names real users with a self-dealing *capability* (capability ≠ proven fraud). Route through the controls channel; do NOT broadcast names widely.
>     5. **Ecosystem (ADR-007):** candidate **BROADCAST to `unesco-sap-brain`** — the S_RFC=* + integration-write-channel weakness is architecturally relevant to the S/4 redesign (the write-side control model). Decide with JP before sending.
> - **H72 [🔴 AUDIT]** — **P2P 3-way-match violations:** 70 IR-before-GR ($713,341, claim #214) + ~~32 invoice+payment SoD (T_ENG/I_MARQUAND, #213)~~ **RETIRADO 2026-08-26** -- motivo: el `32` se conto agrupando por `SLGTC`, el tcode **LANZADOR**, cuando el arrancado vive en `PARAM1` (coinciden en 8 de 1.235.225 filas); claim #213 **SUPERSEDIDO**. **En su lugar:** solapamiento SoD factura+pago en `T_ENG` e `I_MARQUAND` (corroborado por el doble control de BCM, claim #6, y por `AGR_1251`, claims #237-240); **el RECUENTO de usuarios en conflicto se retiro y se DESCONOCE** -- hay que re-derivarlo con `PARAM1`. + 17% PO-no-receipt (open commitments). Remediation + recurring detector. **ACCION PREVIA: re-correr `tier2_sod.py` arreglado ANTES de llevar H72 a ningun comite.** Las otras dos patas **SOBREVIVEN INTACTAS**: los 70 IR-before-GR ($713.341) y el 17% PO-sin-recepcion salen de `p2p_conformance.py` sobre `EKKO`/`EKBE` -- tablas de negocio, no el audit-log -- y no pasan por `SLGTC`.
> - **H73 [🔴 SECURITY]** — **Arbitrary-program-exec auth review** (claim #219): `SE38`/`SA38`/`SA39` by end users → review `S_DEVELOP` ACTVT=16.
> - **H74 [✅ ANALYZED 2026-06-22 — hypothesis REFUTED]** — ~~Satellite TCP connectivity~~. Deepened (`knowledge/h74_syslog_10054_connectivity_analysis.md`, `process_mining/parse_syslog.py`, claim #236, supersedes #232's satellite part): **the 272 `10054` are NOT satellite drops.** 269/272 = end-user **SAP GUI frontend resets** (WP=DP dispatcher; `dpTermin` names workstations; 86% business-hours, weekday, Sat=1/Sun=8 = human curve). Only 3/272 = SAP↔SQL Server, all at **Sun 02:53 maintenance window**. **Zero gateway/RFC-server resets** → MuleSoft/ORION RFC links not TCP-dropping. Remaining actions (→ fold into H78/monitoring): make SQL-Server alerting maintenance-window-aware; investigate `RFFMAVC_OVERALL_VIEW` batch SQL error; reclassify frontend churn as non-failures; keepalive-to-satellites NOT indicated.
> - **H75 [🟡 INTEGRATION — live break, re-flag of H52]** — **9,242 status-29 PROJECT IDocs** to MULE_PROD (CJ20N Core Manager integration broken). Escalate to the integration team.
> - **H76 [✅ DONE 2026-06-22]** — **AGR pull from P01** done via `Zagentexecution/tasks/2026_06_22_h71_sod_write_channel/pull_agr_sod.py` → Gold DB `agr_users` + `agr_1251_sod` + `agr_sod_map.json`. Unblocked H71. Method note: P01 secured `RFC_READ_TABLE` (SAIS) rejects `IN(...)` ("suspicious WHERE") → read per-value equality. Declared-vs-actual finding surfaced: S_STANTIC does vendor change with NO F_LFA1 grant (custom-BAPI bypass). Remaining: USR02 (last-logon / right-unused) not yet pulled; broaden AGR scan beyond the 7 SoD users for H73 S_DEVELOP review.
> - **H77** — **OCEL with `origin=resource` per event** → integration-first conformance (P2P process attributed to satellites). EKBE conformance is already channel-agnostic so findings hold; this adds the channel/resource axis.
> - **H78 [🟡 PARTIAL 2026-06-22]** — **operationalize the PROBLEMS accumulator**. ✅ CENTDATA parse DONE: `process_mining/parse_syslog.py` decodes the fixed format + classifies each row by channel (frontend_DIAG_reset / db_connection_reset / rfc_cpic_error / http_idle_logout / orion_app_error / batch_sql_error) → `syslog_parsed_summary.json`. Remaining: wire BOTH `accumulate_problems.py` (weekly, SM21 ~7d retention) AND `parse_syslog.py` into the schedule so a >7d baseline accumulates AND the noise filter reclassifies frontend churn as non-failures (drop it from the "network error" signal — see H74).
> - **H79 [🟢 ECOSYSTEM]** — **align our 17 MuleSoft flows ↔ PPM `INT-01..06`** with `unescore20-PPM-brain` (the other bridge end; `BROADCAST-ASRUN-MODEL` sent).
> - **H80** — **channel-mix unified** complete (proper IDoc/Jobs by-month, honest multi-unit view).
> - **H81 [🟢 ARCHITECTURE — the culmination]** — **Reconstruct the complete integration architecture** (the authoritative integration model). Fuse THIS session's audit-log-derived operating model (satellites named by host: MuleSoft synctrigger 17-flow PPM↔SAP sync, BRIDGE-RFC=ORION EAI portal, named-user write channel, WF-BATCH, PBC; read/write per satellite; 80% external) WITH the existing integration-element audit (H52: COUPA/GEODIS/SISTER/SuccessFactors/TULIP/UNESDIR/MuleSoft partner profiles + EDIDC/RFCDES/DBCON) INTO one per-integration model — for each integration: external system, channel (RFC/BAPI/IDoc/file/DBCON), FMs/BAPIs, direction (read/write), volume, **and failures** (9,242 status-29 IDocs H75, ~~the 10054 connectivity resets H74~~ → CORRECTED: H74 shows the 10054 are frontend churn, NOT satellite failures; the real integration-failure tail is small — see H82/H83). Output: an **integration companion** (`companions/`) + domain doc (`knowledge/domains/Integration/`), aligned to PPM `INT-01..06` (H79). Sources: `system_operating_model_rfc.md`, `process_mining/rfc_process_classifier.py` (origin axis), `memory/project_integration_elements_gap.md` (H52). This is the end-to-end integration x-ray UNESCO actually runs on.
> - **H82 [🟡 OPS — from H74]** — **SAP↔SQL Server link: maintenance-window-aware monitoring.** The ONLY genuine backend TCP reset is the SQL-Server `dbsh` link (3× `10054` + the lone `DBIF_REPO_SQL_ERROR` dump on `MDS_CTRL_STRATEGY`), all clustered at **Sun 2026-06-21 02:53** = one maintenance window, episodic not chronic. Activity: confirm the backup/maintenance window with BASIS/DBA; make any DB-connection alerting window-aware (suppress Sun 02:00–06:00) so it doesn't page on the known blip. Evidence: claim #236, `knowledge/h74_syslog_10054_connectivity_analysis.md`. (Needs: BASIS/DBA input — outside our read-only P01 reach.)
> - **H83 [🟡 OPS — from H74]** — **Investigate `RFFMAVC_OVERALL_VIEW` batch SQL errors.** The one *recurring* integration-adjacent fault: 3× `DBSQL_*_ERROR` inside the FM Availability-Control overall-view rebuild batch job (00:00 / 05:00 / 07:30 windows). Not the network — check the job's SQL / locking / data volume. Evidence: claim #236, `knowledge/h74_syslog_10054_connectivity_analysis.md`. (Investigable from our side: trace the program + SM37 run history once VPN/P01 is up.)

> **⮕ INCOMING (2026-06-22 — Gold-DB refresher industrialized + extractor maturity model; steward S-089).** Done-since: **PSM_FM + PS fully refreshed & at L4** (master/text/totals/transaction, P01→canonical Gold DB, delta-aware). New machinery: `brain_v2/gold_table_registry.json` (all 317 tables classified by **domain × table_type**; builder `build_gold_table_registry.py`; human map `knowledge/gold_table_domain_map.md`) · `scripts/extraction/gold_refresh.py` (registry-driven, delta-aware: master=pk-upsert, totals=value-compare, txn=partitioned full-row, `_gold_sync_log` audit) · `brain_v2/gold_extractor_maturity.py` (per domain × per table ladder L0→L4, wired into meta-capability EXTRACT). **Extractor maturity baseline = 29.1%** (PSM_FM 0.42 / PS 0.81; everything else L1). Caught+fixed a data-loss bug (fmioi key-collapse 1.81M→1.03M → restored 2.19M, verified == P01 raw). Commits ec62194→8190f3c.
> - **H85 [🟢 MODEL — U_USAGE per domain + deep-dive]** — **Build the U_USAGE (Execution & Usage Footprint) census for the other 14 domains.** New capability dimension #11 (2026-06-23, `knowledge/capability_U_USAGE_execution_footprint.md`): per domain WHAT executes / WHO / HOW (dialog/batch/RFC-BAPI/BDC) / WHEN / VOLUME, from `rsau_audit_history` + `tbtcp` + apqi. Only **PSM_FM=HAVE** (`brain_v2/fm_executed_census.json`: 322/1,331 tcodes live=13.2%; RFC channel = MULESOFT/BRIDGE-RFC + named-user writes E_SILVA/A_BARONE → H71). All others=NONE → U_USAGE theme=6.7%, model maturity 30.3→28.2%. Method = `process_mining/fm_executed_census.py` (swap the name filter per domain, or drive from B_CODE object set). Then **deep-dive per object** (purpose/owner/dead-vs-used/S4-disposition), volume-ranked. Commit 258a4d3.
> - **H84 [🟢 DATA — extractor maturity lever]** — **Curate the remaining domains into the extractor registry** (climb extractor maturity 29.1%→higher). All non-PSM_FM/PS domains sit at **L1 (classified only, no refresh contract)**: **Payment 68 · Config 50 · FI 38 · Logs 16 · Master_BP 14 · Procurement 12 · Controlling 7 · Transport 4 · Integration 4 · Travel 2 · Security 2 · Cross_Domain 1** tables. Per domain: add curated specs to `CURATED` in `build_gold_table_registry.py` (gold↔SAP, key, delta strategy, partition, value_fields/amounts), then `gold_refresh.py <domain>` to sync → L4. **Rule (data-loss trap, learned this session): a line-item table whose stored columns lack the full unique key must NOT be key-deduped — store all rows; ALWAYS verify golden==P01 raw count after a bulk txn refresh.** Method per table: `process_mining/method_registry.py <TABLE>`. Provenance (`d01_/v01_`, 24) is excluded (not a P01-refresh domain).

> **⮕ INCOMING (2026-06-23 — PSM-FM U_USAGE deep-dive; steward S-090).** Done-since: PSM_FM `brain_v2/fm_usage_deepdive.json` (15 object cards + synthesis) committed. Claims #249–#252 promoted. New actionables H86–H87:
> - **H86 [🔴 PSM — CORRECTED 2026-06-23: read AVC from the STANDARD, retire the hand-rolled detector]** — ⚠ï¸ **`committed_vs_available_detector.py` is REFUTED — do NOT wire it.** It re-derives AVC with an invented formula (fmifiit WRTTP 66−54 + bpja−coep−cooi) and produces nonsense pools (fund **196EAR4042**: detector pool **−$12,940,635** vs the **standard AVC ledger FMAVCT net +$1,565,164** — wrong by $14.5M AND sign; total UNES 2026 net = **+$375.7M**, AVC holds). Same error class as GL-from-BSIS instead of GLT0. **The REAL AVC is computed by the system:** control object=(Fund,FundsCtr,CmmtItem), ledger **9H** active all 9 institutes (tolprof 9HZ00001; ICTP=ZIT1/UBO=Z002/UIL=Z001/rest=Z000), activity groups `fmavcatgr` map consumption WRTTP→amount type (50→20/51→30/54→40/60-61→40), available=consumable−consumption, blocks at posting. **DO:** read real AVC via the STANDARD — report **FMAVCR / RFFMAVC*** or the standard **FMAVC read FM** on P01, OR re-extract **FMAVCT fully** (our slice has only ALLOCTYPE_9=KBFC). The real blind-spot test = compare YPS8/YFM1 output vs the STANDARD FMAVCR, not vs the broken detector. Claim #249 quantification SUPERSEDED; YPS8/YFM1 reuse-the-filter (code, #153/#159) still stands but needs re-validation against the standard. See [[feedback_avc_real_from_standard_not_handrolled]].
> - **H87 [🟡 PSM / S4 — ICTP monolith consolidation scoping]** — **Scope and plan ICTP custom suite decommission / consolidation onto standard tcodes.** `ZICTP_COCKPIT` (5,014 / 8 users, 42% on D_CRESEVICH+B_RAZZINI) fronts 70+ ZICTP_* objects re-implementing ME28/ME2L/MIRO/FBL1N/cash/VAT for one Cat-1 institute (Trieste). Largest single S/4 re-platform/decommission scope in PSM_FM + clearest bus-factor risk (claim #250). Step 1: inventory ZICTP_* package via TADIR + extract all program sources. Step 2: map each ZICTP_* to its standard-SAP equivalent (ME28→standard ME28, ZICTP_REP_BCS→RFFMEPGAX/FMRP_RFFMEP1AX). Step 3: gap assessment with ICTP local team. Cross-links: claim #218 (cockpit code), claim #251 (fork duplication), R_S4_READINESS PSM_FM.

> **⮕ INCOMING (2026-06-23 — "how UNESCO works": map every executed object; discovery PATTERNS).** Goal restated by user: explain **100% of transactions/reports/RFC-BAPIs/jobs that run** — what they are, who/what calls them, where from, and which are integrations. Done-since: built `process_mining/executed_objects_domain_map.py` + `brain_v2/executed_objects_domain_map.json` (object→domain map, 4 channels), cached **`tadir_prog`(388K)+`tdevc`(28K)** in the Gold DB (durable), wrote `knowledge/operating_model_discovery_methods.md` (the 4 mapping methods + hidden-extraction + time-factoring patterns). New actionables H88–H90:
> - **H88 [🟢 MODEL/DISCOVERY — complete the executed-objects→domain map]** — The map currently reaches **60% by execution volume / 39% by object** via the PACKAGE method (TADIR.DEVCLASS). Raise it by triangulating the other 3 methods (`operating_model_discovery_methods.md`): (a) **objects-read** — resolve generated programs by their embedded object (`/1BCDWB/DB<table>`→table→domain, SAP-Query `AQ*/!Q*`→workspace/table); (b) **caller→domain** — map service-accounts + dialog users to domains + actor-type (human/integration/batch); (c) extend DEVCLASS/name rules for the ~670 custom Z/Y + ~1,051 std missed. **Honest scope:** the tail is ad-hoc queries + generated + technical substrate (SAPMSSY1/RS*) — the technical substrate is a legitimate non-business tier, not "lost knowledge". This is the **U_USAGE** method at scale (folds into H84/H85). Artifacts committed this session.
> - **H89 [🔴 GOVERNANCE/SECURITY — ungoverned ad-hoc HR data extraction (hidden extractions)]** — VERIFIED 2026-06-23: **6,060 ad-hoc SAP-Query executions · 1,798 distinct queries · 153 users; 60% are HR (3,658 execs, 39 users)** = sensitive personnel data extracted outside governed reports. Top runner **JOBBATCH (1,890) = queries SCHEDULED AS JOBS → automated extraction → almost certainly file output = a parallel integration nobody catalogued.** Active & growing (2026-03→06, ~1,500/mo). **DO:** (1) trace which HR infotypes/tables the top HR queries read (what data leaves) + who; (2) trace whether the JOBBATCH-scheduled queries write to file system (OPEN DATASET) — confirms shadow integration; (3) route as a data-governance finding. Cross-links: H73 (arbitrary-extraction auth), H71 (write-channel SoD). Pattern doc: `operating_model_discovery_methods.md`.
> - **H90 [🟡 MODEL — integration layer + TIME axis on U_USAGE]** — Add the BEHAVIOR axis (read / DB-write / **file** OPEN-DATASET / RFC-out) + ACTOR axis (human / integration MULESOFT·BRIDGE·UBO-RFC·SISTER / batch) to every executed object, so "internal process" vs "integration" is separable system-wide (integration = technical caller OR file OR write/call-out). Add the **TIME** axis (when used, monthly) to detect active-vs-dead + seasonality. First probe = the H89 query→job→file trace. Feeds F_INTERFACE_FILE + R_S4_READINESS (dead-code).

> **⮕ INCOMING (2026-06-18, worked via the unesco-sap-brain harness — session migrated here, NOT yet reconciled):** BCM signatory **node-selection mechanism FOUND = infotype 1218** (`HRP1218`/`HRT1218` expressions on `BNK_STR_BATCH_REL_APPR`: ZBUKR + amount band, bank-agnostic; `HRP1222` empty) + **INC-000011781** (UBO / Renata Ritter, SPEC_READY: ADD 10021811 ×4 nodes, DELIMIT Martin 10108464 from 50034893; Ba/Carvalho/Yli-Hietanen parked for TRS). Landed: `knowledge/domains/Treasury/bcm_signatory_change_solution_design.md`, `companions/bcm_signatory_companion.html`, `knowledge/incidents/INC-000011781_ubo_bcm_add_ritter.md`, Treasury/README "BCM Signatory Panel Management (hub)", IT1218 section + change-history in `bcm_signatory_rules.md`, extended `feedback_bcm_signatory_intelligence.md`, skill triggers. ~~**TODO: `python brain_v2/rebuild_all.py`** to fold IT1218 + INC-000011781 into `brain_state.json`~~ — **DONE s099 (2026-08-17), but the TODO itself is the lesson.** It sat unexecuted from 2026-06-18 to 2026-08-17: INC-000011781 (our richest BCM precedent — IT1218 node selection, the drift sweep, the role gap) had a doc on disk and **no first-class record**, so `BRAIN LOOKUP` could not reach it. Same for INC-180995 and INC-CLASS-LOSS-2026-06 — **11 docs vs 7 records**. All 3 backfilled; `incidents.json` 7→10, brain 1634→1667 objects, coverage held at 100.0%, blind_spots 0. **A TODO is not a control** → the control now exists: `Zagentexecution/quality_checks/incident_record_coverage_check.py` (exit 0 = clean) + rule `feedback_incident_doc_without_record_is_invisible`.

---

## 🔴 INC-PSTLADR-NOV2026 — GRAVE, deadline duro 14-11-2026

**804 empleados a los que seguimos pagando en 2026 no tienen ciudad en ningun sitio.** Desde el
14-11-2026 `<TwnNm>` es obligatorio cuando se emite `<PstlAdr>` en ISO 20022, y sus pagos de nomina
no tendran de donde sacarlo. **NO son los proveedores** — FI-AP esta al 100% con ciudad; la averia
es HR-PY: 1.016 de 5.128 empleados sin ciudad (19%), 2.354 sin codigo postal (45%), concentrado en
oficinas de terreno (CM, BR, SN, IN, AF, ZW, TH, KE, ML, IQ).

Se nos escapaba porque en REGUH el receptor de nomina es un **PERNR que no existe en LFA1**: la
direccion viene del infotipo HR y viaja en el propio REGUH (`ZSTRA/ZORT1/ZPSTL/ZLAND`).

**Registro completo de errores y acciones:** `knowledge/domains/Payment/dmee_map/REGISTRO_ERRORES_Y_ACCIONES.md` — 17 riesgos medidos, con los
descartados y la medida que los descarto, para que no se reabran.

**Por orden:** B1 cargar los 399 proveedores US/CA (fichero listo, `FIXB_1_CARGAR_region.csv`) ·
F1 meter `pain001_address_validator.py` en el ciclo ANTES del envio · A3 encender `REACT_LEV`
nivel 1. Y tres decisiones que necesitan respuesta, no codigo: los 68 proveedores con codigo
postal comodin, el codigo postal de 1.127 empleados, y los 898 pagos de CITI sin BIC.

**Corregido 2026-08-19:** la nomina NO esta en alcance — los 818 sin ciudad cobran por cheque.
El alcance real son los proveedores: 8.149 sin `CtrySubDvsn` en TODOS los rails.

Doc: `knowledge/incidents/INC-PSTLADR-NOV2026_direccion_estructurada_nomina.md` · claims 504-509
Drill: `python brain_v2/load_domain.py dmee`

## PROJECT BRAIN — What We Built

### The System (as of 2026-03-26)

```
UNESCO SAP Intelligence Toolkit — 10 Capability Layers, 38 Skills
├── L1: SAP Connectivity      → pyrfc + SNC/SSO (D01 dev / P01 prod)
├── L2: Data Extraction       → ~2.5GB gold SQLite DB, 24M+ rows, 68 tables
├── L3: Validation/Domain     → sap_brain.py (73.9K nodes, 3-level access), 4 domain agents + coordinator
├── L4: Code Extraction       → ADT API, BSP/OData/Enhancement extraction
├── L5: Transport Intel       → CTS dashboard, 7,745 transports analyzed
├── L6: Fiori Development     → Offboarding clone (React+UI5 Web Components)
├── L7: Process Intelligence  → process-intelligence.html + pm4py (848K P2P events)
├── L8: System Monitoring     → sap_system_monitor.py (SM04/SM35/SM37/ST22)
├── L9: Class Deployment      → 16 scripts (create, deploy, verify ABAP classes)
├── L10: BDC Intelligence     → bdc_full_inventory.py (Allos/Y1 payroll forensics)
└── L11: Integration Intel    → 38 systems, 334 RFC FMs, 7 UNESCO .NET apps mapped

Governance: .agents/GOVERNANCE.md + SKILL_MATURITY.md (38 skills scored)
Companions: 15 HTML (landing page + 14 domain companions)

Each layer FEEDS the others:
  L2→L3 (data validates domain), L5→L4 (transports→code targets),
  L3→L6 (domain rules→app logic), L4→L6 (code→rebuild),
  L2→L7 (event logs), L5→L7 (CTS data)
```

### Key Intelligence Discovered

| Finding | Impact |
|---------|--------|
| P01 SSO works, no password needed | All prod monitoring is passwordless |
| `PRAAUNESC_SC` BDC — 89 sessions by `_COLLOCA` | #1 Allos replacement target |
| `OBBATCH` — 109 automated sessions | Background automation via BDC |
| 0 Fiori apps in P01 (13 in D01) | None have reached production yet |
| 826 programs in P01 vs 1000 in D01 | 174 dev objects not promoted |
| 33 tables discovered via code analysis | Auto brain edge `READS_TABLE` |
| PBC generates ~90% of CDHDR volume | Filter OBJECTCLAS='FMRESERV' for non-FM analysis |
| BSEG declustered in P01 | Can read PROJK directly via RFC_READ_TABLE (no MANDT in WHERE) |
| FMIFIIT.KNBUZEI = BSIS.BUZEI | Perfect 1:1 line-level FM↔FI join |
| FMIFIIT.OBJNRZ = PRPS.OBJNR | Proper WBS element recovery (85.9% coverage for 2025) |

### What the Brain Knows (73,877 nodes — Session #014)
- **64,766 FUNDs** + 710 FUND_CENTERs + 7 FUND_AREAs (with aggregate metadata)
- **7,745 TRANSPORTs** (full CTS inventory)
- **59 Code objects**: 2 BSP Apps, 13 Classes, 44 Tables, App Areas, Domains
- **45 KNOWLEDGE_DOC nodes**: cross-referenced to classes and tables
- **23 SKILL nodes**: L1-L7 + Meta layer + sap_data_extraction
- **10 DOCUMENT nodes**: expert seeds (YRGGBS00, doc_reference, FI substitution sources)
- **5 PROCESS nodes**: B2R, H2R, P2P, T2R, P2D — UNESCO core processes
- **8 JOINS_VIA edges**: table-to-table foreign keys
- **3-level access**: L1 BRAIN_SUMMARY.md, L2 `--focus`, L3 full JSON

### Multi-Agent Architecture (Session #006)
- **Coordinator**: `.agents/skills/coordinator/SKILL.md` — routes by process type
- **PSM Domain Agent**: `.agents/skills/psm_domain_agent/SKILL.md` — FM/budget
- **HCM Domain Agent**: `.agents/skills/hcm_domain_agent/SKILL.md` — HR/employee lifecycle
- **FI Domain Agent**: `.agents/skills/fi_domain_agent/SKILL.md` — GL/validation/substitution

---

## PMO BRAIN — Single Source of Truth for ALL Pending Work

> **RULE**: Every pending item lives HERE. SESSION_LOG entries point here, not the reverse.
> **RECONCILIATION**: At session close, EVERY new pending item must be added here.
> Items completed mid-session get ~~struck through~~ with session # and date.

### 🔴 BLOCKING — Cannot progress without these

| # | Task | First raised | Blocks | Notes |
|---|------|-------------|--------|-------|
| ~~B1~~ | ~~FMIFIIT OBJNRZ enrichment 2024+2026~~ | ~~#016~~ | ~~Golden Query WBS coverage~~ | ~~Done #028: 2024 (16 periods, 27 min) + 2026 (3 periods, 4 min). All years now enriched.~~ |
| ~~B2~~ | ~~BSEG PROJK extraction~~ | ~~#016~~ | ~~WBS for ~9.5% non-FM docs~~ | ~~Closed #035: BSEG is not a table — it's a JOIN (bseg_union VIEW). Golden Query covers 85.9% WBS via FMIFIIT.OBJNRZ→PRPS. Remaining 9.5% = clearing lines without FM match, marginal value. Resolved by design.~~ |
| ~~B3~~ | ~~CO tables: COOI, COEP, RPSCO~~ | ~~#005~~ | ~~Entire CO cost layer missing~~ | ~~Done #035: 3,451,708 rows (COOI 773K + COEP 2.55M + RPSCO 127K). DD03L-verified fields. Period-by-period extraction for VPN resilience. Gold DB loaded. Anchor estimate was 1.6M — actual 2x larger.~~ |
| ~~B4~~ | ~~B2R tables: FMIOI+FMBH+FMBL verification~~ | ~~#009~~ | ~~B2R lifecycle mining~~ | ~~Done — verified #028: FMIOI=1.8M, FMBH=287K, FMBL=319K rows~~ |
| ~~B5~~ | ~~SES gap: ESSR↔ESLL PACKNO mismatch~~ | ~~#011~~ | ~~P2P service receipts~~ | ~~Done — verified #028: 707K PACKNO matched (99.99% of ESSR)~~ |
| ~~B6~~ | ~~EKBE BUDAT enrichment~~ | ~~#018~~ | ~~P2P temporal precision~~ | ~~Done #028: 363K rows enriched (BUDAT+BLDAT+BEWTP+MENGE+DMBTR+WRBTR+WAERS). 2024=161K, 2025=175K, 2026=27K. MEINS auth-restricted. GJAHR=0000 (119K delivery notes) skipped.~~ |
| ~~B7~~ | ~~CDHDR process mining~~ | ~~#011~~ | ~~Audit trail analysis~~ | ~~Done — verified #028: cdhdr_activity_mapping.py exists with pm4py integration~~ |
| ~~B8~~ | ~~P2P bottleneck/temporal analysis~~ | ~~#009~~ | ~~P2P insights~~ | ~~Done — verified #028: p2p_process_mining.py + HTML dashboard built~~ |
| ~~B9~~ | ~~Fix STEM FBZP chain~~ | ~~#019~~ | ~~N/A~~ | ~~Closed #028: STEM not in T001. 9 real co codes (IBE,ICBA,ICTP,IIEP,MGIE,UBO,UIL,UIS,UNES) all configured~~ |
| ~~B10~~ | ~~Update remaining stale skills~~ | ~~#017~~ | ~~Agents using outdated instructions~~ | ~~KILLED #036: subsumed by `SKILLS_CONSOLIDATION_PLAN.md` (38→6 archetypes). The 3 stale skills (sap_native_desktop, sap_automated_testing, sap_enhancement_extraction) will be absorbed or deleted during consolidation, not individually "updated". Item was ceremonial maintenance, not strategic work.~~ |

### 🟡 HIGH — Next available session

**H141 -- EL AGENTE document-output-discovery ESTA AISLADO EN SU PROPIO GRAFO: 0 ARISTAS
DELEGA DE ENTRADA Y 0 DE SALIDA (medido 2026-08-27 sobre brain_v2/toolgraph.json).** Tiene
5 aristas INVOCA hacia instrumentos (A60, A30, A52 x2) -- no esta ocioso -- pero en la
capa de COLABORACION ENTRE AGENTES (26 aristas DELEGA en todo el toolgraph) nadie lo nombra
y el no nombra a nadie.

Y es ironico de la forma mas literal posible: `.claude/agents/document-output-discovery.md`
declara su propio origen en su primera linea -- "Nace de INC-000016471 (2026-08-26), donde
el canal por el que sale TODO PDF de la casa estuvo caido tres dias laborables sin que nadie
lo supiera, PORQUE NADIE ERA SU DUENO." El agente que existe para que un canal huerfano nunca
mas quede sin dueno es el, hoy, un nodo huerfano del grafo que mide colaboracion.

No es un caso aislado: `otras_senales.agentes_que_no_delegan_en_nadie` en
brain_v2/braintoolbox.yaml ya contaba 5 -- pero el agregado no dice CUALES, y sin el nombre
el hallazgo no se puede accionar. Es el mismo modo de fallo que "EL HUERFANO PROPIO"
(braintoolbox.yaml, seccion 6): "se crea un instrumento y no se declara... es el mismo
defecto que le achacamos a UNES_DEPOSIT -- lo que se mantiene a mano se degrada -- aplicado
a nuestro propio trabajo."

**Accion:** decidir un DUENO declarado para document-output-discovery en el toolgraph (quien
lo invoca cuando se rompe una salida de documentos -- hoy nadie lo hace desde otro agente,
solo bajo demanda directa del usuario) y para los otros 4 agentes huerfanos del mismo
`otras_senales`, nombrandolos. No mecanizar la deteccion otra vez: ya existe (`A52_toolgraph`
+ braintoolbox `salud`); falta la DECISION, que es trabajo de agente, no de minero.

**H143 [🟠 EL GUARDIA DE ESCRITURA SOBRE STORES TIENE UN AGUJERO POR HERRAMIENTA, NO POR
INTENCION -- medido violandolo yo mismo, s107].** `store_write_guard_hook.py` esta enganchado
a `PreToolUse` con `matcher: "Write|Edit|MultiEdit|NotebookEdit"`. **Un `python - <<EOF` que
escribe el mismo fichero por Bash no dispara nada**: escribi `brain_v2/domains/domains.json`
y `brain_v2/claims/claims.json` por Bash y el guardia ni se entero. No hubo dano -- comprobe
el lock a mano (`FREE`) y las dos escrituras fueron atomicas (`os.replace`) -- pero eso fue
DISCIPLINA, que es exactamente lo que el guardia existe para no depender de. Y en este proyecto
la sesion trabaja por Bash por instruccion del harness, asi que **la via mas usada es la unica
sin vigilar**. Es la misma forma que el defecto que el propio guardia documenta: `rebuild_lock`
protegia rebuild-contra-rebuild y el candado estaba en la otra puerta. **Que falta:** decidir
entre (a) anadir `Bash` al matcher y que el hook mire el `command` buscando rutas de store --
detecta el caso comun y NO el general, hay que declararlo; o (b) mover la guarda DENTRO del
unico escritor legitimo, un helper `escribir_store(path, obj)` que compruebe el lock y haga el
`os.replace`, y prohibir el `json.dump` suelto con un lint. **(b) mide el efecto; (a) mide la
forma** -- y este proyecto ya sabe cual de las dos envejece mal.

**H142 -- EL TOOLGRAPH MIDE SI SE LEEN LOS SKILLS, NO SI SE USAN LOS HELPERS -- y por ese
hueco se cuelan HALLAZGOS FALSOS (medido 2026-08-27).**

`brain_v2/canonical.py` existe y expone `canonical()`, `aliases_of()` y **`same(a, b)`**. Lo
importan CINCO modulos. En s106 resolvi alias **a mano tres veces** y falle **dos**: publique
"5 referencias rotas en process_map" -- eran alias declarados -- y estuve a punto de
"corregir" `parent: Treasury_EBS`, que es la clave canonica correcta. `same(a,b)` era
literalmente la funcion que lo impedia.

**Y lo peor es que el modulo se escribio para impedir exactamente esto.** Su propio docstring:

> *"THE most repeated defect in this codebase. In session 097 alone the same bug appeared
> THREE times, in three different files, and was fixed three times separately... Fixing a
> recurring defect three times is not fixing it... the failure was never missing data, it was
> that every consumer re-implemented the lookup. **This module is the lookup. Import it; do
> not re-derive it.**"*

Tres veces en s097. Tres mas en s106, por el agente que ese mismo dia predicaba no reinventar
lo que existe. **La solucion se escribio, se documento, se dejo lista para importar -- y el
defecto siguio.** Escribir el helper no fue suficiente; nada obliga a usarlo.

**Por que la defensa declarada no protege:** el modo REINVENTAR LO QUE EXISTE dice "consultar
toolgraph.json antes de proponer nada". Pero el toolgraph **no tiene nodos de HELPER**: sus
aristas LEE / DEBERIA_LEER van de instrumento a SKILL. Un helper no aparece, luego no puede
tener lector, luego nadie mide que se ignora.

**La distincion que hay que registrar:** un skill no leido es conocimiento que no se aplica;
un helper no usado es **una funcion que YA resuelve el problema y que se reescribe peor**. El
segundo produce hallazgos FALSOS, no solo pobres -- y dos de los mios llegaron al dueno antes
de que los retirara.

**Dos salidas, a decidir con el criterio de A69 (mirar si ya existe antes de escribir):**
(a) helpers como nodo del toolgraph, con arista DEBERIA_USAR derivada de quien opera sobre su
mismo problema y no lo importa; (b) mas barato y quiza suficiente: un lint que marque toda
comparacion de conjuntos de nombres que no pase por `canonical.same()`.

**H140 -- HAY AGENTES QUE EL MODELO NO VE, Y EL HUECO ES BIDIRECCIONAL (medido 2026-08-27,
peticion del dueno: "hay mas agentes que no ves... seria un nuevo agente, agent finder").**

    en disco (.claude/agents)      14
    ofrecidos por el harness       18
    EN EL MODELO (toolgraph)       14        universo real de este proyecto: 20 -> ve el 70%

    ofrecidos y NO en disco : Explore · Plan · general-purpose · claude ·
                              claude-code-guide · statusline-setup
    en disco y NO ofrecidos : log-process-discovery · process-guardian

Y en `unescrp` hay 17 definiciones mas que no vemos. La ilustracion que lo cierra: **Explore
hizo hoy dos de los tres mejores trabajos de la sesion** -- encontro la fractura en 4 piezas del
circuito P2P, midio el punto ciego del grafo de companions, y corrigio texto que yo habia
escrito esa misma manana. **Y no existe en nuestro modelo.** El instrumento que mide nuestra
colaboracion es ciego al agente que mas colaboro.

**LA FORMA DEL INSTRUMENTO, por el criterio de corte de la propia caja** (si es para leer es
skill; si decide es agente; si descubre es minero):
- **enumerar** definiciones de agente por el ecosistema = DETERMINISTA -> **MINERO**
- **decidir** si uno hallado es nuestro, si duplica a otro, si se adopta o solo se registra =
  CRITERIO -> **AGENTE**. Precedente exacto: `miner-onboarding` hace esto para mineros.

**LA FRONTERA QUE NO SE PUEDE SALTAR, y es la parte importante:** los 6 del harness **no son
enumerables desde disco por ningun script**. Un minero encontraria 31 ficheros y seguiria
estructuralmente ciego a Explore y companyia. Si reporta "hay 14" comete exactamente el defecto
de H134. **Tiene que emitir UNOBSERVABLE para esa mitad**, no una cifra confiada -- claim 616:
una frontera del instrumento invalida TODA conclusion sacada de su silencio. La unica via de
observarla es que una SESION declare el roster que recibio, porque el harness se lo da a la
sesion y no al disco.

**Alcance:** empezar por este proyecto (20) y unescrp (17); el registro debe distinguir
PROPIO / DE OTRO PROYECTO / DEL HARNESS, porque adoptar no es lo mismo que conocer.

**H138 -- `braintoolbox.yaml` NO SE PUEDE PARSEAR COMO YAML, Y SU PUERTA NO SE ENTERA
(medido 2026-08-27, defecto PRE-EXISTENTE -- comprobado contra HEAD antes de tocarlo).**
`yaml.safe_load` falla: escalares PLANOS que contienen `: ` sin comillas. Dos confirmados y
al menos uno mas detras:

```
piezas: - objeto: ... "Un objeto puede ser varias cosas a la vez: Solution Manager es..."
defensa: fallback al crudo. Un alias mal resuelto NO DA ERROR: da un cero, que es peor
```

**Por que importa mas de lo que parece.** El fichero se presenta como el modelo canonico de
como trabajamos y dice de si mismo *"NO es prosa: cada afirmacion de aqui se mide en un
fichero real"*. Pero **ningun consumidor puede leerlo como datos**: es prosa con aspecto de
YAML. Y `braintoolbox_check.py`, que lo vigila, pasa en verde porque lee con **regex**, no con
un parser -- o sea la puerta comprueba las 16 CIFRAS y es estructuralmente incapaz de detectar
que el documento esta roto. Es el mismo patron que H134: un instrumento que afirma dentro de
una frontera que no declara.

**Intento y marcha atras (s106).** Se escribio un reparador guiado por el PARSER (no por un
patron mio), que entrecomilla el valor solo en la linea que el parser senala y **PARA si no
sabe arreglarla sin inventar**. Paro en la linea 210. Se REVIRTIO entero en vez de dejar el
fichero a medio entrecomillar: dos lineas con comillas y el documento igual de irreparseable
es peor que no haberlo tocado -- cambia la prosa sin ganar nada.

**Que falta:** terminar la pasada (probablemente < 10 lineas) y **anadir al gate un
`yaml.safe_load` que falle**, que es el arreglo de fondo: hoy el guardian no puede ver la
clase de rotura que mas le importa.

**H139 -- UNA RESPUESTA EN EL BUS CIERRA UNA PREGUNTA Y DEJA ABIERTAS LAS OTRAS 14
(medido 2026-08-27).** `colaborar.contestar(minero, sujeto, ...)` busca por **`sujeto`** y
hace `return` en la PRIMERA coincidencia. Pero el propagador abre una pregunta **por cada
minero destinatario** con el MISMO sujeto:

```
CLAIM 616                             15 preguntas, 15 abiertas
ADS                                    4 preguntas,  4 abiertas
A65_AUTHORISED_PANEL_RECONCILIATION    4 preguntas,  3 abiertas tras contestar una
A67_VARIANT_WRITE_SAFETY               3 preguntas,  3 abiertas
```

Contestar `CLAIM 616` cierra UNA de quince; las otras catorce quedan abiertas para siempre y
`mining_collaboration_check` las cuenta como ocasion perdida. **La cifra de "preguntas sin
contestar" esta inflada por construccion**, igual que lo estaba `DEBERIA_LEER` (claim 622):
otro denominador que no se deriva.

**Arreglo:** que `contestar()` acepte `para=` (o el indice) para desambiguar, y que sin `para`
conteste a TODAS las del mismo sujeto o se NIEGUE, en vez de elegir la primera en silencio.
Decidir cual de las dos: una respuesta puede ser valida para los 15 destinatarios (el caso de
CLAIM 616) o especifica de uno.

**H137 -- EL COMPANION DE PRESUPUESTO-A-PAGO: ENCONTRARLO, Y DECIDIR SI UN COMPANION ES
UN SKILL DE DOMINIO SIN DECLARAR (pedido del dueno, 2026-08-27).**

**Lo que el dueno recuerda, en sus palabras:** este proyecto tenia un companion que recorria
el **circuito completo de pagos** y era *"muy bueno y detallado"*. La cadena que describe:

```
PO  ->  factura  ->  si es de cierto TIPO la factura debe llevar PPC
    ->  aprobacion por WORKFLOW  ->  y ESE workflow llama a Role Management
    ->  pago  ->  proceso BCM, distinto SEGUN LA SOCIEDAD
```

No recuerda como estaba identificado ni donde esta. **Eso es el sintoma, no un detalle**: es
el mismo defecto que ya medimos en s099 -- si no se llega desde los dos puntos de entrada, no
existe. Un artefacto que el propio dueno no sabe localizar esta perdido aunque el fichero
este en disco.

**La tesis a evaluar, que es lo de fondo:** *los companions contienen IMPLICITAMENTE skills
que se generaron para el dominio*. Si es cierto, tenemos 44 companions y solo 50 skills, y una
parte del conocimiento de dominio esta atrapada en HTML que nadie declara como skill -- no lo
lee ningun instrumento, no aparece en el toolgraph, y no puede tener lectores porque no es un
nodo. Concretamente este seria el skill **presupuesto-al-pago (B2R + P2P + Payment_BCM)**,
que hoy no existe: tenemos los dominios sueltos, no el CIRCUITO que los atraviesa.

**Pista fuerte y fresca (s106):** el paso *"el workflow llama a Role Management"* CONECTA con
el claim 619. RM lo consume CRP para resolver actores (CERTIFYING / OFFICER_IN_CHARGE /
APPROVING / BUDGET_OFFICER); si ademas lo llama un workflow de aprobacion de facturas,
**RM tiene un segundo consumidor que no teniamos mapeado**, y deja de ser "una cosa de CRP"
para ser infraestructura de resolucion de actores de toda la casa. Verificarlo es parte de
esta tarea.

**Como atacarlo (orden, para no repetir el fallo del alias que da cero):**
1. Buscar por CONTENIDO, no por nombre de fichero -- el companion de RM en unescrp se llamaba
   `unesdir-role-management.html` y un grep por nombre no lo encontraba (S-208). Terminos:
   PPC, BCM, workflow de aprobacion, factura, PO, y las combinaciones. Empezar por
   `companions/` (44) y por `companions/companion_graph.json`, que los indexa.
2. Si aparece: leerlo entero antes de opinar, y decidir que parte es SKILL (conocimiento
   curado, se LEE), que parte es PROCESO (doc de dominio) y si falta el METODO. La triada.
3. Si NO aparece: es una perdida real y hay que decir eso, no reconstruirlo de memoria.
4. Cerrar la pregunta general: barrer los 44 companions y marcar cuales son de facto un skill
   de dominio sin declarar. Eso es una respuesta MEDIDA a la tesis del dueno, no una opinion.

**LA CADENA COMPLETA, CORREGIDA POR EL DUENO (2026-08-27) -- la de arriba estaba corta:**

```
PO -> GOODS RECEIPT -> SERVICE ENTRY SHEET (en algunos casos) -> INVOICE
   -> PPC si aplica -> aprobacion WF (llama a RM) -> F110
   -> BCM (lote + panel + liberacion)  <- EN MEDIO, con parada posible
   -> fichero al banco -> acuse -> extracto
```

Faltaban **recepcion de mercancia** y **hoja de entrada de servicios**, que no es un detalle:
la hoja de servicios es un objeto propio con su ciclo, y en una casa que compra sobre todo
SERVICIOS es el tramo normal, no la excepcion.

**Y ya esta minado:** `companions/p2p_process_mining.html` recorre exactamente
`EBAN -> EKKO/EKPO -> ESSR/ESLL -> RBKP/RSEG -> EKBE` (848.135 eventos, 193.296 casos), y
`ESSR/ESLL` ES la hoja de entrada de servicios. O sea el tramo que el dueno anadio NO es un
hueco de mineria: esta cubierto y termina en `Invoice Posted`. Lo que falta sigue siendo la
COSTURA con el tramo de workflow, no el tramo en si.

**TRES REQUISITOS DEL DUENO (2026-08-27), que acotan como se resuelve esto:**
1. **NO PERDER NADA.** Ni skills ni companions. Lo que se reorganice se PRESERVA (CP-002);
   lo obsoleto se SUPERSEDE, no se borra. Si un companion resulta ser un skill de dominio,
   el companion NO desaparece: gana una declaracion, no pierde su fichero.
2. **SKILLS *Y* COMPANIONS**, los dos ejes. La tesis es que el companion contiene el skill
   implicito; el entregable no es elegir uno, es declarar la relacion entre ambos.
3. **SI HAY OPORTUNIDAD, UN MINERO DEL END-TO-END.** El circuito completo no lo mina hoy
   nadie: hay mineros por tramo (A21 caso, B1_B2_B3 flujo, B4 conformidad P2P,
   A24 ciclo de vida) y cada uno declara que NO puede solo. Puede que lo que falte sea la
   COMPOSICION y no un minero nuevo -- decidirlo con evidencia, no por gusto.
4. **QUE COLABOREN LOS AGENTES.** Enfasis explicito del dueno tras un fallo mio: conteste
   yo las preguntas del bus como agente principal, y eso NO es que los agentes colaboren.
   Se lanzaron 3 en paralelo (Explore para localizar por CONTENIDO, bank-process-discovery
   para el criterio de dominio, miner-onboarding para el veredicto del minero), con el bus
   como canal entre ellos.

**No confundir con H135/H136**, que son defectos del propio PMO. Esto es conocimiento de
negocio potencialmente perdido, y vale mas.

**H137 -- HALLAZGOS DE bank-process-discovery (s107), tramo pago->BCM y verificacion RM.**
Corrida `python brain_v2/bank_model_explorer.py` primero (no recalculado a mano). Veredictos:
RISK 2, NEW 3, BLIND 1, STABLE 5 -- ninguno requiere accion nueva de este agente: RISK
"4 sociedades no francesas sin clase PPC" ya es el modelo conocido (claims 494/531, doc
`house_bank_roles.py`); NEW "16 cuentas RECEPTORA" ya esta en claim 535, pendiente
programar el tipo en el clasificador (no hecho esta pasada, queda para la proxima); BLIND
FEBKO parcial ya es claim 535/536.

1. **CORRECCION DEL DUENO EN CALIENTE, verificada: BCM va DENTRO del tramo de pago, no
   despues.** F110 crea BKPF BLART=ZP -> BCM agrupa en LOTE por RULE_ID (BNK_BATCH_HEADER
   27.443 filas, BNK_BATCH_ITEM 600.042 filas via VBLNR) -> panel firma via BNK_APP
   (workflow 90000003) -> SOLO ENTONCES se genera y transmite el fichero (BNK_MONI:
   "Approved" = file creation scheduled; "Sent to Bank" = file created and transferred).
   IBC17 Fallido / IBC06 Rechazado son PARADAS reales -- el circuito puede detenerse ahi.
   Lo que cambia por SOCIEDAD es DOBLE: (a) si BCM existe siquiera (Tier1 UNES/UBO/IIEP/
   UIL/UIS con BCM; Tier2 ICTP F110 sin BCM; Tier3 IBE/MGIE/ICBA sin F110); (b) cuantos
   firmantes y si hay 2a validacion en Coupa, dentro de las que si tienen BCM. Aterrizado
   en claim 623.

2. **PPC: no re-derivado, ya esta medido.** Aplica a pagos CROSS-BORDER de proveedor/
   beneficiario en 9 paises (T015L), solo cuando la sociedad es FRANCESA (unica clase BAdI
   que despacha, claim 494/531) y el metodo/moneda cae en un T042Z de la familia SG. La
   distincion de "TIPO de factura" real medida es proveedor vs NOMINA (LAUF1 sufijo 'P' ->
   codigo SALA), no un campo de la factura. Ver `sap_payment_bcm_agent/SKILL.md` seccion
   PPC y `Zagentexecution/quality_checks/ppc_country_consistency_check.py`.

3. **RM: claim 619 se quedaba corto -- hay un TERCER consumidor, y es el que H137 pedia.**
   CRP (claim 619) NO es el workflow de facturas: es un Fiori app distinto (certificados de
   personal/consultoria, JV directo, sin LIFNR, sin evidencia de que entre en F110/BCM). El
   que SI es "workflow de aprobacion de facturas -> Role Management" es el workflow SAP
   90000003/90000001 (doc types KR/KA/KT/ER/IT, sociedad UNES) via
   `Z_GET_CERTIF_OFFICER_UNESDIR` -> proxy tipado `ZROLE_MGTCO_FACADE`/`LP_ROLE_MGT` ->
   RoleManagement. **MEDIDO, con una contradiccion abierta y declarada, no oculta**: el
   skill `crp/unesdir-role-management` (unescrp, S-118) dice que ese MISMO proxy tipado es
   runtime-DEAD (0 oficiales para un email valido) y que por eso CRP lo abandono. Si esa
   muerte es del proxy y no del caso de uso de CRP, el workflow de facturas podria estar
   cayendo SIEMPRE al fallback `ZFI_PAYREL_EMAIL` sin que nadie lo note -- un defecto vivo,
   no verificado. Aterrizado en claim 624 (OPEN_QUESTION) y publicado como pregunta en el
   bus de mineria (`process_mining/mining_findings.json`, sujeto
   `ZROLE_MGTCO_FACADE_LP_ROLE_MGT_liveness`) porque cerrarlo exige leer ABAP o probar en
   vivo -- fuera del alcance de este instrumento (solo Gold DB + prosa).

4. **Tramos NO modelados -- nombrados, no rellenados con suposicion:**
   - **PO -> recepcion -> factura**: no hay medicion de este agente sobre MM (pedido,
     entrada de mercancias, MIRO). Dominio de `sap_payment_e2e`/mineria P2P (A21/B1-B4), no
     de banca.
   - **El propio ABAP de `Z_GET_CERTIF_OFFICER_UNESDIR`**: no leido (punto 3).
   - **Si un certificado CRP alguna vez desemboca en pago via F110/BCM**: no encontrado en
     el esquema OData revisado; no descartado del todo (requeriria leer el codigo de
     posteo de la extension DPC de `Z_CRP_SRV`).
   - **El companion de presupuesto-a-pago que el dueno recuerda**: no es tarea de este
     agente localizarlo (ver Explore/miner-onboarding en paralelo); este agente no lo
     busco por nombre ni contenido.

**H137 -- CERRADO EL TRAMO PRINCIPAL (s107, 2026-08-27). NO HABIA NADA PERDIDO: FALTABA EL
ORDEN.**

**1. El companion existe y se llama `payment_bcm_companion.html` (828 KB).** Localizado por
CONTENIDO, no por nombre (barrido de los 142 HTML del repo por la combinacion Role Management
+ PPC + BCM). Contiene lo que el dueno recordaba, literalmente: *UNESCO Payment End-to-End
Flow*, *Workflow Identity*, *Actor Resolution Rules*, *WF Call Chain (step by step)* con
`Z_GET_CERTIF_OFFICER_UNESDIR -> role.hq.int.unesco.org`, *BCM Release Rules*, DMEE y los
tiers por sociedad. **Lo que no tiene es el principio**: arranca en *FI document posted*, no
en el pedido. Por eso no se reconocia como "el circuito completo".

**2. El circuito esta en CINCO piezas, y las once etapas estan CUBIERTAS.** Barrido de los 52
HTML de `companions/` contra los tokens de cada etapa: ninguna etapa se quedo sin companion.
`p2p_process_mining.html` cubre pedido -> recepcion -> hoja de servicios -> factura MM;
`payment_bcm_companion.html` cubre documento FI -> PPC -> WF/RM -> F110 -> BCM -> fichero;
`p2p_purpose_of_payment.html` + `inc_egypt_ppc_configuration.html` el PPC;
`bcm_signatory_companion.html` el panel; `bank_statement_ebs_companion.html` el extracto.
**No hay perdida de conocimiento** -- que era lo unico que H137 temia de verdad.

**3. POR QUE EL GRAFO NO CONOCIA LA CADENA, y por que no era un umbral mal puesto.**
`companion_graph.json` tenia **UN SOLO tipo de arista**: coseno IDF sobre vocabulario
compartido, que mide **PARECIDO**. Dos etapas **contiguas** comparten poco vocabulario
*precisamente porque son etapas distintas* -- `EBAN`/`EKPO` no se parece a
`BNK_BATCH_HEADER`. **La similitud no puede expresar secuencia, por construccion.** Medido
antes de tocar nada: de los 10 pares entre las 5 piezas, **6 sin arista**, y
`p2p_purpose_of_payment.html` **sin ninguna** con las otras cuatro. Bajar el umbral no habria
cosido el circuito: habria metido ruido. Es el mismo defecto que el driver OCEL 2.0 de
`braintoolbox.yaml` nombra -- tratar el proceso como un CONTENEDOR plano (`process_map` da un
conjunto de dominios) en vez de como una PERSPECTIVA con orden.

**4. LO HECHO -- la secuencia como segunda clase de arista, declarada y vigilada:**
- `brain_v2/domains/domains.json -> process_map.P2P.stages`: **11 etapas** con sus objetos,
  sus `evidence_tokens`, sus companions, cuales son **CONDICIONALES** (hoja de servicios,
  PPC, BCM por tier de sociedad) y cuales pueden **PARAR el circuito** (metodo O/U termina el
  WF; IBC17/IBC06 paran BCM). `domains` sigue diciendo QUIEN participa; `stages` dice EN QUE
  ORDEN. Son campos distintos a proposito.
- `scripts/build_companion_graph.py`: emite **`sequence_edges` (SIGUE_A)** -- **20 aristas, 9
  companions dentro de la cadena** -- proyectadas de esa declaracion, separadas de las 130 de
  parecido, y dibujadas con flecha (discontinua donde la etapa anterior puede parar). **La
  arista que el PMO daba por ausente, `p2p_purpose_of_payment <-> payment_bcm_companion`, ya
  existe como SIGUE_A -- y sigue sin existir como parecido, que es exactamente el punto.**
- `Zagentexecution/quality_checks/process_circuit_check.py` (**gate nuevo**): comprueba que
  cada etapa siga cubierta, que el companion declarado la contenga **de verdad**, que el orden
  sea consecutivo, y dibuja las juntas.

**5. EL FALSO POSITIVO QUE SE CAZO A SI MISMO, y es el aprendizaje que vale.** La primera
version del gate declaro el circuito **entero cosido**... acreditando la junta factura->FI a
`transport_companion_D01K9B0CBF_v2.html` y la de servicios->factura a
`fm_ps_avc_temporal_forecast_v1.html`: **un companion de TRANSPORTES y uno de AVC**, que citan
`MIRO`/`BKPF` de pasada. Su propio docstring ya advertia de esto y aun asi lo hizo. **Una cita
no es una narracion** -- el mismo limite que el `LEE` del toolgraph, tercera capa del patron
"medir la FORMA en vez del EFECTO". Regla que quedo en el codigo: una junta esta cosida cuando
un fichero **DECLARADO** para una etapa (alguien lo abrio y lo juzgo) **MIDE** cobertura de la
contigua -- **juicio Y medida, ninguno de los dos solo**. Segunda version: la junta 40->45 baja
de COSIDA a **ARISTA** (parecido 0,297, senal debil), que es la verdad.

**QUE QUEDA ABIERTO de H137** (no se toco, y se dice en vez de darlo por hecho):
- **El barrido de los 44 companions** para contestar MEDIDA la tesis del dueno -- *cuales son
  de facto un skill de dominio sin declarar*. Es el punto 4 de "como atacarlo" y sigue entero.
- **El skill `presupuesto-al-pago`**: no creado. Ahora hay de que sacarlo -- las 11 etapas son
  su indice -- pero crearlo es trabajo aparte.
- **El minero end-to-end**: sin veredicto. La evidencia nueva empuja a COMPOSICION y no a
  minero nuevo (cada tramo ya esta minado), pero eso lo decide `miner-onboarding` con la
  cadena delante, no yo por gusto.
- **Las etapas 1-3 no producen arista SIGUE_A** porque las tres viven en el mismo fichero:
  son bucles, y un bucle no es travesia (`braintoolbox` seccion 6). Correcto, pero significa
  que el grafo no muestra el tramo de compras como cadena.

 -- EL BOUNDARY LLAMA DEAD A 38 DESTINOS QUE SU EVIDENCIA NO PUEDE VER (medido 2026-08-27,
claim 620).** `process_mining/interface_boundary.py` correlaciona `RFCDES` contra
`rsau_audit_history.PARAMX`, que registra llamadas **RFC**. Un `cl_http_client=>create_by_destination`
no es RFC y no deja fila ahi. De los 227 destinos DEAD, **38 son `HTTP external` (tipo G)**: para
esos, `observed_calls: 0` mide *sin trafico RFC*, no *sin uso*.

El script declara en su comentario que "DEAD is now a fact rather than an artefact" tras quitar el
muestreo de 400.000 filas. Cierto para tipo 3; **sobreextendido para tipo G** -- quitar el muestreo
arregla la COBERTURA de la fuente, no su APLICABILIDAD. Es DENOMINADOR INCOMPLETO
(`braintoolbox.yaml`) sobre nuestro propio instrumento, y contradice la consigna del `BRAIN_INDEX`:
*MISSING_INPUT significa NO PODEMOS VER, nunca NO HAY NADA*.

**Arreglo (pequeno y determinista):** tercer cubo `UNOBSERVABLE` para los tipo G (y revisar `driver`
e `internal`, que tampoco esta claro que emitan PARAMX). Que el `findings` diga por que no se puede
concluir, en vez de concluir. Mientras no se haga, **no citar la cifra "227 dead" sin partirla por
tipo** -- hoy el `BRAIN_INDEX` publica "238 configuradas, 11 vivas, 227 muertas" sin ese corte.

**Caso que lo destapo:** `svc-prod-role.hq.int.unesco.org` (host de RoleManagement, claim 619) figura
DEAD con 0 llamadas. **No se afirma que este vivo** -- ese destino esta en P01 y quien llama a RM
corre en D01, asi que no hay contradiccion de dato. Lo que falla es la licencia para pronunciarse.

**H135 -- LOS IDs DEL PMO COLISIONAN: 18 NUMEROS REPETIDOS, Y YA HAY REFERENCIAS AMBIGUAS
(medido 2026-08-27).** 121 marcas `**H<n>`, solo **102 distintas**. Repetidos: H41, H50, H67, H68,
H91, H92, H93 y **el bloque entero H104-H114**. Son dos flujos de numeracion que no se ven entre si:
los items de seccion (`^**H<n>`) y la lista citada de pendientes de sesion (`> - **H<n>`), cada uno
contando por su cuenta.

**No es cosmetico: ya rompio una referencia.** La linea de H124 dice *"Ver H106 y H112, que dependen
de el"* -- y H106 y H112 existen **dos veces cada uno**, con contenidos sin relacion (H112 es a la vez
*el disco de copias desconectado* y *la alineacion de la FSV*). Un lector no puede resolver a cual
apunta, y un agente tampoco.

**Como se cazo:** al insertar H134 la guarda del script fallo (`H112 ya existe`) en vez de escribir
encima. El defecto llevaba ahi desde antes; lo que faltaba era que alguien asertara antes de tocar --
regla #180, *un replace silencioso es un defecto silencioso*.

**Arreglo:** asignar el siguiente id desde el **maximo global** (hoy 133), no desde el maximo de una
seccion; y una puerta que cuente marcas frente a distintas y falle. Sin eso, cada sesion que numere
mirando su propia lista vuelve a colisionar. Renumerar lo viejo es aparte y puede no compensar -- lo
urgente es dejar de crear colisiones nuevas.

**H136 -- EL PMO ESTA DOBLE-CODIFICADO: EL FICHERO CONTIENE MOJIBAKE, NO SOLO SE VE MAL
(medido 2026-08-27).** El guion largo de `**H111 -- EL BRAIN_STATE` no es U+2014: son **tres
caracteres**, `U+00E2 U+20AC U+201D`. Es decir, los bytes UTF-8 del guion (E2 80 94) fueron
**decodificados como cp1252 y regrabados como UTF-8**. Lo mismo les pasa a los emoji de las
cabeceras de seccion. **Esta en el disco**, no es un artefacto del terminal: se comprobo imprimiendo
los codepoints.

**Por que importa:** cualquier busqueda o edicion por texto que use el caracter correcto **no
encuentra nada y falla en silencio** si no hay asercion -- que es exactamente lo que paso dos veces
al intentar insertar H134. Y afecta al fichero que declaramos *single source of truth* de todo el
trabajo pendiente.

**Arreglo:** una pasada de reparacion (`s.encode('cp1252','ignore').decode('utf-8')` sobre los tramos
afectados) **con diff revisado antes de grabar**, no a ciegas -- hay texto legitimamente acentuado y
un arreglo mal aplicado lo destroza. **Decision del dueno**, porque toca el fichero entero. Mientras
no se haga: los bloques nuevos se escriben en **ASCII puro** (H134/H135/H136 lo estan) para no anadir
mas corrupcion.

**H111 — EL BRAIN_STATE YA NO CABE EN CONTEXTO: 1.396.967 TOKENS, EL 139,7% DE UN MILLON
(medido por el propio rebuild, 2026-08-24).** 5.587.869 bytes. La progresion es **4 MB el
20-ago, 5 el 21, 5,5 el 24**: medio mega al dia.

Hoy no rompe nada porque la carga es escalonada y nadie lo lee entero. Pero **un fichero que no
cabe en contexto ha dejado de ser un fallback**: el `BRAIN_INDEX` dice "lee el brain_state
completo cuando necesites profundidad que el indice no da", y eso ya no se puede hacer.

**No se toca a lo bruto.** Encogerlo por compresion va contra CP-002, y la respuesta correcta
es estructura, no perdida. Las opciones reales son tres y son una DECISION, no una tarea:
particionarlo por dominio · dejar de materializar en el las capas que ya viven en su store ·
o aceptar que el fallback desaparece y quitar esa frase del indice.

Lo que NO se puede seguir haciendo es mirarlo crecer: nada vigila ese numero, y solo aparecio
porque `add_knowledge_links` lo imprime de paso.

**H110 — EL ACUMULADOR PIDE SIEMPRE 16 DIAS, PASE LO QUE PASE: 45 DIAS DE SM20 AUSENTES (s102, medido 2026-08-22).**
`accumulate_logs.py` corrio hoy tras **62 dias** sin ejecutarse. TBTCO (lookback 180d) y CDHDR (120d)
cubrieron el hueco entero. **RSAU/SM20 no**: `RSAU_DEFAULT_DAYS = 16` es una CONSTANTE, asi que pidio
2026-08-06..2026-08-22 y dejo fuera **2026-06-22 .. 2026-08-05 = 45 dias**. Medido en la Gold DB:
**julio entero = 0 filas** (`202602` 299K · `202603` 3,49M · `202604` 4,94M · `202605` 4,30M ·
`202606` 2,58M · **`202607` 0** · `202608` 2,22M).

**No estaban perdidos — sonda a P01 el 2026-08-22, ventana 08:00-10:00h:**
20260622 → 23.076 filas · 20260701 → 21.793 · 20260715 → 21.117 · 20260731 → 20.865 ·
20260805 → 22.113 (control: 20260810 → 22.987, 20260820 → 19.689). O sea **la retencion real de SM20
en P01 es ≥ 62 dias**, no los ~14d que el script asume ni el ≥61d del claim #212. El hueco era
recuperable y el propio acumulador no lo pidio.

**El arreglo NO es correr mas a menudo.** Es que la ventana se DERIVE del estado: `dias desde el
ultimo run` (que ya esta en `accumulate_logs_state.json`) **+ margen**, acotado por la retencion
medida — nunca una constante. El `freshness_guard()` ya DETECTA el gap y lo imprime como WARN; luego
pide 16 dias igual. **Detectar no es actuar** (misma forma que la regla #179).

**RESUELTO el mismo dia.** (a) Rescate ejecutado: julio paso de **0 a 4.507.421 filas**, los 45 dias
del hueco estan **45 de 45** cubiertos. (b) La ventana ya no es constante: `derive_rsau_days()` la
saca del **hueco mas antiguo que la historia REALMENTE tiene** dentro del techo de retencion medido
(70d), no de "dias desde la ultima corrida" — porque una corrida que muere a medias sella el estado
igual, y en cuanto una corrida posterior rellena los dias recientes un hueco en MEDIO se vuelve
invisible a cualquier aritmetica sobre la fecha de corrida. Probado en 6 escenarios; el del hueco
real deriva **63d**, la misma ventana que hoy hubo que elegir a mano. (c) El WARN ya no miente:
decia "lost forever" y era falso. (d) **RSAU no salia en el informe de cobertura** — por eso el
agujero de julio nunca se vio; ahora sale y cuenta dias AUSENTES, no solo el span MIN..MAX que los
oculta por construccion.

**Lo que destapo nada mas anadirlo, y esto si queda abierto:** `14 de 183 dias sin filas`, la peor
racha **12 dias (2026-02-24..2026-03-07)**. Estan fuera del techo de 70d: **irrecuperables**. No es
accion, es el coste ya pagado de haber tenido este defecto abierto — y la medida de por que la
cobertura tiene que mirarse por dias y no por span.

**H109 — UN REBUILD SOBREVIVE AL SUSPEND Y COLISIONA CON EL SIGUIENTE (s102, medido 2026-08-22).**
Un `rebuild_all.py` lanzado el 21/08 a las 23:17 seguia VIVO a las 08:36 del dia siguiente: el PC se
suspendio, no se apago, y el proceso sobrevivio. Al volver se lanzo otro (via `curate.py`, que
invoca `rebuild_all.py` en su linea 84). Resultado: **dos escritores concurrentes sobre
`brain_state.json`** durante horas, y el fichero en disco quedo en 5.337.221 bytes cuando la version
verificada y commiteada la noche anterior tenia 5.639.898.

**Por que la regla de un solo escritor no lo evito**: la regla dice "no lances dos rebuilds", y nadie
lanzo dos a sabiendas — uno resucito. Una regla que depende de que el operador recuerde no cubre el
caso en que el sistema recuerda por el.

**Mecanizado el 2026-08-22 — `brain_v2/rebuild_lock.py`, cableado en `rebuild_all.py`:**
1. ✅ **Lock con PID y heartbeat**. HELD se niega y dice quien manda · ORPHAN (PID muerto) lo
   reclama solo · HUNG (vivo pero sin latir >15 min) se niega y **no mata**. Probado en los tres.
2. ✅ **Tope de duracion** — >45 min cuenta como HUNG.
3. ⬜ **Guard al commitear** — la funcion existe (`is_rebuild_running()`), **falta llamarla desde el
   hook de cierre**. Es lo unico que queda de H109.

*Resuelto hoy a mano: matado el proceso zombi (PID 10680 + hijo), dejado correr el nuevo.*

**H108 — 11 DE 13 INCIDENTES NO DEJARON PROCESO, SOLO CASO (s102, medido).** Lo detecto JP:
*"la creacion de cuentas no tenia conocimiento a dominio, solo incidente"*. Barrido de los 13
incidentes: **solo 2 tienen documento de PROCESO en su dominio**, y son los dos que se tocaron ese
dia. Mecanizado en `Zagentexecution/quality_checks/incident_domain_knowledge_check.py` (tier gate).

**Tres pares — dos incidentes del mismo dominio y tipo — donde el proceso YA se puede escribir:**

| Dominio | Tipo | Incidentes | Proceso que falta |
|---|---|---|---|
| **BANCOS** (hoy tagueado `Treasury`, canonico `Treasury_EBS`) · eje **P2P** | MASTER_DATA | `INC-000006313` + `INC-000011781` | **panel de firmantes BCM**: alta y baja de personas, la carta como autoridad de registro, el barrido de la poblacion. Correccion de JP: BCM vive en el dominio de los BANCOS y su eje es purchase-to-pay, no T2R — autorizar un pago es P2P. El canonico `Treasury_EBS` induce a error: ese dominio es banco casa **y** extractos |
| `Payment_BCM` | REGULATORY | `INC-EGYPT-PPC` + `INC-PSTLADR-NOV2026` | **requisito regulatorio de un banco**: como se decide si aplica (rol del banco casa, corredor), como se prueba, como se despliega |
| `PSM_FM` — **Fund Management** | ERROR | `INC-000005638` + `INC-BUDGETRATE-EQG` | **tipo de cambio presupuestario y deriva del pool de AVC** |

Y **`INC-CLASS-LOSS-2026-06` apunta a `BASIS`**, que es una clave transversal y no un dominio con
registro: el mismo defecto que tuvo `Closing_Activities` cinco sesiones.

**La regla ya existia y llevamos tres pares incumpliendola** (`sap_incident_analyst`: *por la 2a
ocurrencia debes un procedimiento*). Lo que faltaba no era la regla: era el check que la mide.

*Siguiente accion: escribir el proceso de autorizacion bancaria BCM — es el par mas maduro, con
dos casos ya documentados en detalle.*

**H107 — 50 CUENTAS CON OB09 Y SIN VARIANTE DE F.05 (s102, medido). Escala muy superior a
INC-000016262.** `4041011` no era un caso aislado. Barrido de toda la sociedad UNES: **69 cuentas
activas con partidas abiertas en divisa y fuera de toda variante, 50 de ellas con `T030H`
configurado** — alguien quiso revaluarlas y nunca entraron en el calculo.

| Familia | Cuentas | Lo mas grueso |
|---|---|---|
| Travel Agency Clearing de oficinas de campo (`920x`/`923x`) | **31** | UZS 136,5 M · IRR 222 M · NGN 14,2 M |
| Clearing de institutos (`509x`) | **7** | `5098012` UIS en **13 monedas** · `5091011` EUR −12,89 M |
| Inversiones y depositos (`404x`) | 2 | `4041011` EUR 10 M · `4044015` EUR −3,97 M |
| Otras | 10 | `2111000` VAT HQ EUR 1,44 M · `4060000` Fixed Assets Clearing en 4 monedas |

**Metodo que hay que usar para revisarlo** (esta en el agente `fx-revaluation-scope`): la
incoherencia no es "no estar en una variante" — hay 497 cuentas de balance fuera y la mayoria con
razon — sino **no estar cuando tus iguales de la misma posicion de balance si estan**. Filtrado
asi: 208 cuentas.

**Causa estructural, no descuido:** la cobertura por RANGO (`UNES_UNBA`, `UNES_OI_G/L`) da 94-100 %
porque la FSV y la variante leen la misma estructura de numeracion; la cobertura por LISTA
(`UNES_DEPOSIT`, 18 sueltas) da 30-50 %. **La recomendacion no es "anade la cuenta X" sino "por que
`404xxxx` y los clearing `509x`/`920x` se mantienen a mano cuando bancos va por rango".**

*Pendiente de decidir con FRA/Tesoreria antes de tocar nada.* Claims 558-563.

**H106 — PREGUNTA A TESORERIA: 3 cuentas con OB09 y en ninguna variante de F.05 (s102, medido).**
No es una cuenta suelta, es un patron en la familia de depositos e inversiones. Con `T030H` puesto
y **fuera de toda variante**: `4041011` Term Deposits Principal (**defecto VIVO**, 10 M EUR netos
abiertos), `4041012` Term Accounts Principal Current y `4041014` MMF USD JPMorgan (latentes: misma
configuracion incompleta, sin exposicion hoy). Alguien configuro donde postear y nunca las metio
en el calculo.

Segundo grupo, sin `T030H` **y** sin variante, que nadie ha preguntado: `4041015`, `4041016`,
`4043021`, `4043022`, `4043024`, `4043027`, `4043028` y los mandatos `4043030/31/32`
(PIMCO · JP Morgan · RAMP). `4041019` NO entra: cerrada en INC-000016262 (USD sobre sociedad USD).

**Hipotesis descartada en la misma sesion.** Se penso que el criterio de `UNES_DEPOSIT` fuera
"cuentas en moneda distinta de USD". Falso: dentro hay cuentas en USD que llevan euros y estan bien
incluidas — `4043011` (USD, EUR 20,5 M), `4043025` (USD, EUR 7,3 M), `4043026` (USD, EUR 6,2 M).
**El dato que cierra la cuestion:** de las 25 cuentas de la familia, **8 tienen exposicion abierta
en divisa y SIETE estan dentro de la variante**. La unica fuera es `4041011` — 571,6 M USD de saldo
y 10 M EUR abiertos. Es una **omision suelta**, no un criterio mal planteado. La pregunta a
Tesoreria es directa: ¿por que esta fuera, y se anade?

Instrumento: `python Zagentexecution/quality_checks/fx_revaluation_scope_check.py` · agente
`fx-revaluation-scope` · claims 558-561.

**H105 — REVALUACION FX (F.05 / SAPF100): el dominio NO existe, la materia SI (s102, medido).**
Mismo patron que master data: hay conocimiento de sobra y ningun registro que lo reuna.
**Medido 2026-08-21:** 36 claims, 5 incidentes y 6 documentos hablan de revaluacion FX, repartidos
entre **10 etiquetas de dominio**. El dueno natural, `Closing_Activities`, tiene el registro
**VACIO** — 0 docs, 0 companions, 0 objetos, 0 incidentes, sin `coverage_pct` — mientras 4 docs de
revaluacion viven fisicamente en `knowledge/domains/Closing_Activities/`
(`fx_revaluation_process.md`, `fx_revaluation_closing_calendar_2025.md`, `README.md`,
`sap_variant_forensic_methodology.md`).

**Defecto de datos a arreglar primero (barato y silencioso):** conviven **dos grafias** —
`Closing_Activities` (10 claims) y `Closing Activities` con espacio (6 claims, entre ellos el
incidente `INC-FXREVAL-OB09`). Cualquier consulta por una pierde la otra sin avisar. Normalizar en
el store y anadir un gate al validador de ontologia para que no vuelva a pasar.

*Lo que ya esta medido y no hay que re-derivar:* los **2 tipos de valoracion** (A reversible /
B a balance) y la mecanica `T030H`/OB09; que **OB09 y la variante de F.05 son un solo gate** y
cada mitad falla en silencio por separado; que `4041011` tiene **10 M EUR netos abiertos, OB09
puesto y esta en ninguna variante**; y `INC-FXREVAL-OB09` (la sub-cuenta bloqueada 1109574 usada
como LKORR de 1010574/1110574).

*Alcance propuesto:* poblar el registro de `Closing_Activities` con sus objetos (`T030H`, `TCURR`,
`SAPF100`, `VARID`/variantes de F.05, `BSIS`/`BSAS`), reclamar los 36 claims dispersos, colgar los
5 incidentes, y declarar la matriz **que cuenta se valora, con que metodo, por que variante** —
que hoy solo se puede reconstruir a mano. Instrumento existente:
`Zagentexecution/quality_checks/ob09_vs_variant_check.py` (**A47 `DEFECTO_VIVO`** -- `main()` resuelve con `covered()`, su funcion LEGADO, teniendo la correcta en el mismo fichero: **34 falsos positivos sobre 780 cuentas**. **Arreglar `main()` antes de apoyarse en su salida**; claim 599). **ATENCION: la matriz 'que cuenta se valora, con que metodo, por que variante' NO se puede construir con el camino actual**, porque no clasifica las cuentas asociadas -- arreglar el instrumento es PARTE de la tarea, no un prerrequisito aparte.

**H104 — MASTER DATA GOVERNANCE: explorar y expandir el dominio (s102, JP).** El dominio existe
y esta cableado (`brain_v2/master_data_registry.json`, companion generado, alias por nombre de
objeto en `load_domain.py`), pero **solo 1 de 10 tipos esta mecanizado punta a punta**. Queda
abierto a proposito: lo que falta no es codigo, es CONOCIMIENTO DE PROCESO que hoy no tenemos.

*Lo que YA esta medido y no hay que re-derivar:* el canal RFC de cada tipo (`TFDIR` de D01,
`FMODE='R'`, 2026-08-21); que las clases de coste SI tienen canal; que los `BAPI_BANKDETAIL*`
son de interlocutor y NO del banco casa; que los centros de beneficio no se usan; y que el alta
nace en P01 y solo se notifica si hay revaluacion (2 cuentas de retraso en D01, **33 en V01**).

*Lo que falta, por orden de valor:*
1. **La cadena de tareas POSTERIORES de cada tipo.** Solo esta medida la de la cuenta de mayor
   (7 pasos). Para un centro de coste, un fondo o un PEP no sabemos que dispara un alta — y ese
   es el valor del dominio, no el alta en si.
2. **La autoridad de registro de cada tipo.** Para la cuenta de mayor es el formulario `AM 3-11`
   validado por FRA. Para los otros 9: DESCONOCIDA. Sin autoridad no hay Track B posible.
3. **Quien es el dueno de las tareas posteriores.** Hoy llegan por correo a quien las reciba.
   Es la causa raiz del dominio entero, y es una pregunta de organizacion, no de SAP.
4. **Ejecutores para los 7 tipos con canal medido y sin ejecutor** — centro de coste primero
   (`BAPI_COSTCENTER_CHECKMULTIPLE` permite validar sin escribir, asi que el dry-run es real).
5. **El paso 0 programado.** Hoy `gl_alignment_check.py` existe pero nadie lo dispara: mientras
   sea bajo demanda, el proceso sigue arrancando con un correo. Candidato a tarea de Windows
   junto a las 3 ya registradas.
6. **Extender el barrido a los otros tipos**: cuanta deriva P01 vs D01/V01 hay en centros de
   coste, fondos y PEP. Nunca se ha medido; el numero de las cuentas (33) sugiere que no sera 0.

*Instrumentos que ya existen:* `gl_alignment_check.py` · `ob09_vs_variant_check.py` (**A47 `DEFECTO_VIVO`** -- arreglar `main()` antes de apoyarse en su salida; claim 599) ·
`fsv_coverage_check.py` · `config_transport_prerelease_check.py` · agente `master-data-sync`.
*Doc:* `knowledge/domains/Master_Data_Governance/gl_account_creation_process.md`.
*Reglas:* `feedback_a_master_data_domain_is_a_registry_of_object_types` ·
`feedback_a_config_object_applies_to_a_population_prove_it_before_measuring`.


**H91 — SECURITY: open it as a DOMAIN (s097, JP).** It has never been one, and that is exactly
why searching for it returns nothing: today it exists only as capability column `E_AUTH`, empty
in 16 of 21 domains, and as the single MISSING component of the installation profile — nothing
in the repository derives a security posture. Scope: **users, logs, profiles and roles**
(`USR02` last logon and lock state, `AGR_*` role assignment, `USOBT`/`USOBX` authorisation
defaults, `SU53`/RSAU failures), plus the **attribution question below**, which is a security
question and not a usage one.
Two things are already known and must not be re-derived: the control surface here is the CALL
and DATA layer, not the role layer (`S_RFC=*` plus a custom write FM that skips the object
check); and a clean PFCG picture therefore does not mean segregation holds.

**H92 — ATTRIBUTION: 5.3M calls that no person can be tied to (s097, measured).** The
"80% external" headline hides a sharper fact. Behind each technical account, `PARAMX` carries
the calling `user=` — and the accounts split cleanly in two:
- **TRANSPARENT** — `WF-BATCH` 660,588 calls with **542 distinct real users** behind it (only
  14% is the account itself), `SMTMSBP` with 4 technical users.
- **OPAQUE** — `MULESOFT` 3,230,958 calls, ONE identity, 100% itself. `BRIDGE-RFC` 2,106,347
  and `UBO-RFC` 324,390 carry **no `PARAMX` at all** — not even a caller field.
So it is NOT that a generic user is masking people, which would still leave a trail. For 5.3M
calls **there is no trail**. And people DO log in: **1,848 distinct users by dialog** (902,758
events) and 1,882 by RFC/CPIC. The finding is not "nobody uses SAP" — it is that **the write
traffic enters through channels where attribution is lost**.
Task: decide whether attribution is recoverable (MuleSoft-side correlation id, an ORION log, a
header we do not read) or structurally absent. If absent, that is the finding for governance,
because every SoD and every change-approval control assumes an actor.

**H93 — SUPPORT has no coverage metric (s099).** The Support domain registry now carries its
docs, incidents, two tracks, procedures and 4 recurring checks — but `coverage_pct` is still
`null`, and deliberately so: no metric was invented for it. Support is not a SAP business domain,
so the 11-capability grid does not apply (`S_STANDARD_REF` for Support is a category error), and
it is not one of the 8 meta-capability dimensions either. Decide where it belongs and what it
measures. The candidate levers are already instrumentable: **% of incident docs with a first-class
record** (now gated at 100% by `incident_record_coverage_check.py`), **% of repeated scenarios that
have a procedure doc**, and **% of Track-B tickets whose drift sweep produced a standing check**.
Until then Support reports no coverage, which is honest and useless.

**H94 — PERNRs are synthesized into the brain typed `GL_ACCOUNT` (s099, measured).** Drilling
`graph_queries.py incident INC-000011781` returns the signatories 10021811 / 10016038 / 10005016 /
10097358 as `"type": "GL_ACCOUNT"`. The synthesizer types any 8-digit numeric name as a GL account.
Harmless for retrieval today, wrong for anything that reasons over object type, and it inflates the
GL population. This is the same defect family as **H41** (promote PERNRs to first-class PERSON
objects) — H41 lists 11 PERNRs from blind_spots; Track B keeps adding more with every signatory
ticket. Fix the type inference at the same time as H41, not separately.



| # | Task | First raised | Category | Notes |
|---|------|-------------|----------|-------|
| ~~H1~~ | ~~Create `sap_payment_e2e` skill~~ | ~~#019~~ | ~~Skill~~ | ~~Done #021~~ |
| ~~H2~~ | ~~Create `sap_process_mining` skill~~ | ~~#017~~ | ~~Skill~~ | ~~Done — SKILL.md exists, Functional (3). OCEL pending as G1~~ |
| ~~H3~~ | ~~Create `sap_change_audit` skill~~ | ~~#017~~ | ~~Skill~~ | ~~Done — SKILL.md exists, Functional (3). Compliance template → added #023~~ |
| ~~H4~~ | ~~BSEG UNION view in SQLite~~ | ~~#011~~ | ~~Data~~ | ~~Done — bseg_union VIEW exists, 4.7M rows (BSIS+BSAS+BSIK+BSAK+BSID+BSAD). Verified #023~~ |
| ~~H5~~ | ~~Merge sap_segw + segw_automation~~ | ~~#018~~ | ~~Skill~~ | ~~Done #023 — sap_segw now comprehensive (5 workflows, element IDs, full troubleshooting). segw_automation redirects.~~ |
| ~~H6~~ | ~~Brain integration of P2P~~ | ~~#009~~ | ~~Brain~~ | ~~KILLED #036: brain is write-only. 73K nodes built, zero decisions routed through it. Adding PROCESS_VARIANT nodes is more write, not more value. Resurrect only if a decision needs graph traversal that SQL can't do.~~ |
| ~~H7~~ | ~~Design Fiori replacement for PRAA*~~ | ~~#005~~ | ~~App~~ | ~~Moved to backlog #036 as G54 (was deprioritized #028 but never actually moved)~~ |
| ~~H8~~ | ~~P01 transaction usage report~~ | ~~#005b~~ | ~~Monitoring~~ | ~~Done — verified #028: sap_system_monitor.py --report transactions works~~ |
| ~~H9~~ | ~~P01 runtime dumps report~~ | ~~#005b~~ | ~~Monitoring~~ | ~~Done — verified #028: sap_system_monitor.py --report dumps works~~ |
| ~~H10~~ | ~~Document Coupa integration~~ | ~~#002~~ | ~~Analysis~~ | ~~KILLED #036: SUPERSEDED. `integration_map_complete.md` (#035) documented COUPA dual-channel (file + BDC). `project_coupa_file_integration.md` memory exists. This item was already done but never closed.~~ |
| ~~H11~~ | ~~**Extract Benefits BSP + HCM Z-reports (merged H11+H12)**~~ | ~~#005b (merged #036)~~ | ~~Code~~ | ~~**Done #038** via RFC (not ADT — avoided the .env password dependency). 4 HCMFAB MYFAMILY classes extracted: `ZCL_ZHCMFAB_MYFAMILYME_DPC` + `_DPC_EXT` + `_MPC` + `_MPC_EXT`. 7 BSP apps discovered in ZFIORI package: YHR_BEN_ENRL (Benefits Enrollment), YHR_EDURENT_APV, YHR_OFFBOARDEMP, YHR_OFFBRD, ZHRBENEFREQ, ZHREDURENTALADM, Z_HCMPROCES_EXT. 222 HCM namespace Z-reports discovered, 12 extracted as sample (including ZZHRPAF02 186KB, ZHRAUTOSTEP, ZNHR_LOAD_PAYSCALE_GROUPS). Channel: `READ REPORT` via `RFC_ABAP_INSTALL_AND_RUN` over SNC/SSO — same channel as H29.~~ |
| ~~H12~~ | ~~Populate HCM/Reports folder~~ | ~~#005b~~ | ~~Code~~ | ~~MERGED into H11 #036.~~ |
| ~~H13~~ | ~~**BCM dual-control gap remediation**~~ | ~~#021/#027~~ | ~~Audit~~ | ~~**Done #037 — Deliverable 1 shipped.** Monitor script `Zagentexecution/bcm_dual_control_monitor.py`, HTML companion `bcm_dual_control_audit.html`, executive summary `knowledge/domains/BCM/h13_executive_summary.md`. Reframe: automation debt, not fraud. 3,359 same-user batches in scope / $656M exposure. Top 2 = C_LOPEZ + I_MARQUAND (94.7% / 92.9% self-approval) — HQ treasury manual Wednesday cycle, no 3rd operator. F_DERAKHSHAN reclassified (74% dual-controlled). +1,366 drift since #027 (15 sessions of inaction cost). Paths 2–5 (carve-out, role split, workflow mod, automation) spawn as H13a/b/c/d in next review.~~ |
| ~~H14~~ | ~~**Extract YWFI package source from D01**~~ | ~~#021~~ | ~~Code~~ | ~~**Done #038** via RFC (TADIR query DEVCLASS='YWFI' → 37 objects). Full extraction: classes, programs, FUGRs with method includes. Key find: `ZWF_GET_CERTIFYING_OFFICER` (NOT `Z_WF_GET_CERTIFYING_OFFICER` as PMO said — wrong underscore) is a FUGR with 5 includes (TOP+UXX+U01+U02+U03, 7KB of logic). Other extracted FUGRs: `ZFI_PAYREL_EMAIL`, `Z_WF_FI_EVENT_PAYMENT_METH`, `Z_WF_FI_EXCLUDE_NOTIF`, `Z_WF_FI_GET_CLASSIC_VALID`. Programs: `YBSEG_REL`, `ZNOTREJECT`. Output: `extracted_code/YWFI/`.~~ |
| ~~H16~~ | ~~Investigate 229 PAYROLL IBC17 (Failed) BCM batches~~ | ~~#026~~ | ~~Audit~~ | ~~Closed #028: ALL 2,056 IBC17 failures are 2021-2022 (BCM activation outage Jul21-Dec22). Zero failures in 2024-2026. Root cause: BCM activated mid-2021, misconfigured for 15 months, fixed Oct-Dec 2022. Out of data scope.~~ |
| ~~H17~~ | ~~Rebuild payment event log: model all 4 clearing streams~~ | ~~#026/#027~~ | ~~Analytics~~ | ~~Done #028: 4-stream model implemented. 1,848,699 events / 550,993 cases. Stream 2 (OP field office): 274,863 events. Stream 3 (AB netting): 138,378 events. Stream 4 (Tier 3 OP): 82 events. Dashboard + CSV rebuilt. Brain rebuilt (73,922 nodes).~~ |
| ~~H18~~ | ~~**SEPA `<Purp><Cd>` PurposeCode source identification**~~ | ~~#026~~ | ~~Code~~ | ~~**Done #039 (CONFIRMED from P01).** The PurposeCode comes from **`FPAYP-XREF3`**, read by DMEE tree `/CGI_XML_CT_UNESCO` node `Purp > Cd` (N_9662041050), post-processed by BAdI `FI_CGI_DMEE_EXIT_W_BADI`. Proprietary fallback from `FPAYP-STRFR`. Not a static literal — runtime field mapping. 13 UNESCO DMEE trees analyzed (8,308 nodes in P01). D01 vs P01 comparison: 12/13 trees identical, only `/CGI_XML_CT_UNESCO_1` diverges (9 address nodes differ — minor). ABAP classes `YCL_IDFI_CGI_DMEE_FR/FALLBACK/UTIL` are BAdI implementations receiving tree values, not containing them. PMO class names `_AE`/`_BH` never existed. Findings: `knowledge/domains/Payment/h18_dmee_tree_findings.md`. Comparison CSV: `h18_dmee_d01_vs_p01_comparison.csv`. Probe script: `h18_dmee_tree_probe.py`.~~ |
| ~~H19~~ | ~~**Bank recon aging investigation**~~ | ~~#028~~ | ~~Audit~~ | ~~**Closed #042.** Already fully investigated #029: 199K items on 10xxxxx = permanent ledger (by design). Real unreconciled = 2,737 on 11xxxxx (0.6% gap). No further action needed — finding documented in `bank_statement_ebs_architecture.md`.~~ |
| ~~H20~~ | ~~BSAS AUGBL re-enrichment for bank statements~~ | ~~#028~~ | ~~Data~~ | ~~Done #030: 553,781 items enriched with AUGBL+AUGDT (100% fill rate). Year 2024=247K, 2025=267K, 2026=49K. Clearing chain now fully traceable.~~ |
| ~~H21~~ | ~~**Bank recon amounts: currency conversion**~~ | ~~#028~~ | ~~Analytics~~ | ~~**Done #042.** CURRENCY_USD_RATES table (203 currencies from TCURR type M) + FEBEP_USD view created in Gold DB. Real USD total: **$16.8B** (not $13.9B — conversion increased total). UZS=$6.2B (37% from 1.3% items), USD=$5.8B, EUR=$2.7B. Weak currencies (UZS/IRR/LBP) inflate, don't deflate. Falsified hypothesis that DMBTR was inflated.~~ |
| ~~H22~~ | ~~**FEBEP full fields extraction**~~ | ~~#029~~ | ~~Data~~ | ~~**Closed #042 — DATA WAS ALREADY COMPLETE.** PMO was stale 12 sessions. `FEBEP_2024_2026` table has 223,710 rows with 27 fields, ALL months present (2024-01 through 2026-03). The unsuffixed `FEBEP` (50K rows, 104 cols) was the truncated first attempt — the real data lives in the `_2024_2026` table. "Missing months" claim was wrong.~~ |
| ~~H23~~ | ~~**FEBKO full fields extraction**~~ | ~~#029~~ | ~~Data~~ | ~~**Closed #042 — DATA WAS ALREADY COMPLETE.** PMO said "Missing HBKID" but `FEBKO_2024_2026` has 31,416 rows with 62 fields INCLUDING HBKID (0% null). The unsuffixed `FEBKO` (50K rows, 8 cols) was the truncated first attempt. Same pattern as H22 — always check `_2024_2026` suffix.~~ |
| ~~H24~~ | ~~FEBRE extraction (Note-to-payee / Tag 86 text)~~ | ~~#029~~ | ~~Data~~ | ~~Done #030: 964,055 rows (KUKEY-filtered 2024-2026). 211K match FEBEP. Tag 86 analysis completed: 102I root cause = ACH returns (BELNR=*). Search string effectiveness validated.~~ |
| ~~**H34**~~ | ~~**Code Brain v2: SAP cross-reference extraction + annotation framework + incident linking**~~ | ~~**#048**~~ | ~~**Brain**~~ | ~~**Done #049 — pivoted from extraction to architecture rewrite.** D010TAB/WBCROSS = 200M+ rows, never bulk extract. Built Brain v3 hybrid instead: object-centric `brain_v2/brain_state.json` (4.2% of context, 10 AGI layers, 1 Read = full intelligence). 50 feedback rules migrated from `~/.claude/memory/` (portable). 26 claims (15 superseded for anti-regression). 19 known_unknowns + 16 data quality issues mined from 48 retros. Single-command rebuild via `rebuild_all.py`. SessionStart hook in `.claude/settings.json`. AGI score 41/100→90/100. See `Brain_Architecture/brain_design_specification_v3.md` and `session_049_retro.md`.~~ |
| ~~**H35**~~ | ~~**Validate Brain v3 in real session work**~~ | ~~#049~~ | ~~Brain~~ | ~~**Done #050.** Brain v3 used for the entire session including a self-evaluation that produced 12 deliverables. FALS-003 falsified (I globbed before reading the brain link) — fix shipped: `feedback_brain_first_then_grep` rule + Layer 11 (incidents) + Layer 12 (blind_spots) + `_coverage` metric + force-include. Object count 102→136. AGI score 90→101 (added Failure-mode visibility criterion).~~ |
| **H36** | **Triage brain blind_spots — superseded by H50** | #050 | Brain | Original scope #050: 20 blind_spots. Session #054 audit: count grew to **71** (all MISSING flavor). Coverage dropped 75.6% → 64.3%. H36 is preserved as history anchor; **H50 supersedes with updated scope**. H36 action list remains valid for the first 20: extract PA0027, ZCL_IDFI_CGI_DMEE_FR, ZCL_IM_TRIP_POST_FI_CM006; model GB901/GB922 from Gold DB; drop pseudo-refs (LHRTSF01:852, inst_fund_ba_wbs_cc, GB901:2IIEP###001). |
| **H37** | **Process next incident with new infrastructure** | #050 | Workflow | User will pass next incident in Session #051. Invoke `incident-analyst` subagent (`.claude/agents/incident-analyst.md`) and follow the 7-step `sap_incident_analyst` skill protocol. Output: `knowledge/incidents/INC-<id>_<slug>.md` + first-class record in `brain_v2/incidents/incidents.json`. Resolves FALS-005 (does the workflow reproduce INC-000006073-quality output on a fresh case?). |
| **H38** | **Cleanup `ZFIX_BR_AVC_EXCLUSIONS` landscape inconsistency** | #053 | Code/Cleanup | Discovered Session #053 during INC-BUDGETRATE-EQG analysis. BAdI implementation of `FMAVC_ENTRY_FILTER` exists in **D01 + V01 only**; absent in TS1, TS3, P01. Created 2025-05-14 by JP_LOPEZ (transports D01K9B0D4Z + D50, "BR - AVC Exlclusion MIRO F110"), **deactivated next day 2025-05-15** (transports D01K9B0D54 + D55, "BR Deactivate AVC exclusion"). Never promoted beyond V01. Class `ZFIX_BR_AVC_EXCLUSIONS` (CCDEF/CCIMP/CM001/CM002/CO/CU/CI/CP/CT) is dead code. **Action**: delete from D01+V01 (release transport through chain). **Lesson**: tcode-blacklist mute on AVC was the wrong direction; cross-currency drift must be fixed at the persistence layer or via preventive validation (H39), not the AVC filter. |
| **H39** | **Build preventive validation for cross-currency consumption against EUR BR FRs** | #053 | Code | Per business agreement (Session #053 close). Implementation: new BAdI implementation on `CL_FM_EF_POSITION->CHECK_CONSUMPTION`. Logic: IF `check_br_is_active() = abap_true` AND `m_r_doc->m_f_kblk-waers='EUR'` AND `m_f_kblp-gsber='GEF'` AND `fund_type IN mr_fund_type` AND `consumption_doc-waers <> 'EUR'` THEN MESSAGE 'Z_BR_001' TYPE 'E' "Cannot consume in &1 against EUR Budget Rate Fund Reservation &2/&3. Please post in EUR." Test coverage: FB60/FB65/FB70/MIRO/F110 in TS3 with all 64 listed at-risk FR lines from `Zagentexecution/incidents/INC_budget_rate_eq_guinea/br_lines_FINAL.xlsx`. Coordinate with H38 (delete dead BAdI first). |
| **H40** | **One-time FMAVCREINIT cleanup of 26 affected funds for 2026 / ledger 9H** | #053 | Operations | After H39 deploys to production. Run `RFFMAVC_REINIT` for FIKRS=UNES, GJAHR=2026, ALDNR=9H, FUND IN (26-fund list from incident INC-BUDGETRATE-EQG.scope). Clears accumulated AVC pool drift. Verify each fund's Available USD post-reinit. List of funds: 3110111021, 3110111061, 3210151021, 3210621061, 3210631031, 3230311021, 3230311031, 3230321041, 3230411011, 3230411081, 3230511011, 3230711051, 3230833081, 3230836011, 3230851011, 3240211011, 3310511011, 3310611021, 3310611041, 3310611051, 3310611071, 3310714011, 3320111011, A110111041, A230211011, A230542041. Add a recurring schedule? TBD with treasury — reinit is heavy. |
| **H41** | **Promote 11 PERNRs from blind_spots to first-class person objects** | #054 | Brain/Meta | Discovered session #054 audit of retro #053 formalization gap. Brain carries 11 PERNR-shaped blind_spots (all numeric 8-digit): 10050037, 10067156, 10069500, 10092400, 10097358, 10098989, 10105832, 10107946, 10136066, 10150918, 10567156. These are referenced by BCM workflow annotations + INC-000006313 (VOFFAL add) + ghost PERNR 10567156 (dq_ghost_pernr_bcm_oesttveit RESOLVED). Promotion: for each PERNR, create a first-class object in `brain_state.objects[]` with type=PERSON, fields={pernr, name (from PA0001), BCM_roles, active_rules, related_incidents, HR_status}. Data source: Gold DB PA0001 + OOCU_RESP extraction. Supersedes the "low priority next session" deferred item from #053 retro. |
| **H42** | **Migrate claims.evidence_for/against from str to structured list (DONE session #054)** | #054 | Brain/Schema | **Done session #054.** Schema `evidence_for` and `evidence_against` migrated from `str` to `list[{type, ref, cite, added_session, migrated_from_legacy}]`. 46 claims migrated. Legacy text preserved verbatim in new fields `evidence_legacy_text_for` + `evidence_legacy_text_against` (CP-001). Types inferred automatically: 24 empirical, 11 production_data, 8 source_code, 3 config. `build_active_db.py` patched to json.dumps() the list and add `evidence_count_for/against` columns (CP-003: claims with count<2 are suspect). Backup: `brain_v2/claims/claims.json.pre_session054_backup`. Enables queries: "claims with only empirical evidence", "claims missing source-code anchors", etc. |
| **H43** | **Register 4 missing objects from session #053 (FMAVCT, KBLEW, CL_FM_EF_POSITION, /SAPPSPRO/PD_GM_FMR2_READ_KBLE)** | #054 | PSM/Brain | Session #053 retro §11 committed to registering these as first-class brain objects — never done. All 4 confirmed in `brain_state.blind_spots`. Required fields: type (TABLE/CLASS/FUNCTION_MODULE), domain (PSM), annotations with Session #053 findings (FMAVCT wide-table query pattern, KBLEW cluster wrapper, CL_FM_EF_POSITION→CHECK_CONSUMPTION as H39 fix target). Source data: retro §6 "Tables/data sources discovered" + §7 "Custom code/class architecture". |
| **H44** | **Build `sap_fm_avc_intelligence` skill (AVC = core PSM)** | #054 | PSM/Skill | Availability Control is the foundation of PSM at UNESCO. Skill must encapsulate: FMAVCT wide-table extraction pattern (narrow FIELDS, split OPTIONS), cluster-table access via `/SAPPSPRO/PD_GM_FMR2_READ_KBLE`, fund-level vs FR-line-level metric distinction, Camp A/B/C enhancement asymmetry classification for BR composites, EURX rate type handling, FMIOI WRTTP=81 carryforward pair interpretation (CP-003: sample before aggregating), FMAVCT dedup by RVERS/RPMAX. Source references: retro #053 + `knowledge/domains/PSM/EXTENSIONS/budget_rate_custom_solution.md` + `Zagentexecution/quality_checks/budget_rate_consumption_audit.py`. Deliverable: `.agents/skills/sap_fm_avc_intelligence/SKILL.md` + MATURITY entry. Upgraded from "consider" (retro §13) to HIGH based on domain criticality. |
| **H45** | **Deploy AL_JONATHAN SU3 Y_USERFO fix (DQ-018)** | #054 | FI/Config | Single-user fix for INC-000005240 class. User Anthony Jonathan (Jakarta Field Unit) has USR05 parameter Y_USERFO='HQ', should be 'JAK'. Every F-53/FBZ2 posting carries wrong XREF office tag. Blocked by **KU-027** (verify YFO_CODES contains FOCOD='JAK' before SU3 update). Action: (1) extract YFO_CODES table from P01; (2) confirm JAK entry; (3) update USR05 for AL_JONATHAN via SU3; (4) verify next F-53 posting carries XREF1/XREF2='JAK'. Dependency on H48 (understand substitution mechanics before deploying). |
| **H46** | **Systemic XREF drift strategic fix (DQ-019)** | #054 | FI/Strategy | 21,754 manual post-posting XREF edits in Q1 2026 (FBL3N/FBL1N/FB02/FBL5N on UNES documents). Strategic options documented in `knowledge/domains/Treasury/xref_office_tagging_model.md §7.3`. Decision needed between: (a) preventive substitution fix (code in YRGGBS00), (b) opt-in SU3-based user param model, (c) periodic reconciliation + auto-correction job, (d) tolerate as known manual tax. Must select one, write implementation plan, coordinate with Treasury. Scope: production-wide, affects all 9 company codes. Blocked by H48 (understand WHY substitution fires asymmetrically). |
| **H47** | **HR/BASIS alignment process for USR05.Y_USERFO ↔ PA0001.WERKS/BTRTL (DQ-020)** | #054 | HCM×BASIS | Organizational process gap: USR05 (finance office code, SU3) and PA0001 (HR personnel area/subarea) use different code systems at UNESCO with no enforced sync. A user's finance office can drift silently from their HR assignment. Not a technical bug — a missing process. Action: propose HR→BASIS alert mechanism when PA0001.WERKS/BTRTL changes; periodic diff report (SAP job); policy for mandatory SU3 update on HR transfer. Owner: HR + BASIS collab. Cross-domain item. |
| **H48** | **Investigate KU-030/031/032: YRGGBS00 substitution mechanics (session #055 update: DOUBLE ASYMMETRY confirmed)** | #054 | FI/Investigation | **KU-027 ANSWERED #055**: YFO_CODES.JAK exists as 'JAKARTA'. H45 unblocked. **KU-030 MOSTLY_ANSWERED #055**: 57 transports modified YRGGBS00 (E071+E070 extracted). Primary maintainer I_KONAKOV (~20 transports 2008-2023). Guard comment-out narrow-scoped to KONAKOV 2009-08-27 cluster (D01K951407/442/618) or 2010-04-26 (D01K960319). Definitive closure needs SE38 version diff via GUI. **KU-031 ANSWERED_CORRECTED #055**: prior claim that prereqs were procedural was WRONG. Prereqs ARE declarative via 3-table chain GB922->GB921->GB901. 16 UNESCO steps in GB921. 56 UNESCO boolean rows in GB901. Key finding: step 005 (UXR1/XREF1) has NO prereq — fires unconditionally. Step 006 (UXR2/XREF2) prereq HKONT IN (6 bank GLs). **KU-032 ENRICHED_NOT_CLOSED #055**: asymmetry F110 vs F-53 must come from callpoint iteration or downstream filter — still needs ST05 trace. **DOUBLE ASYMMETRY** confirmed: UXR1 broken at CONFIG (no prereq) AND CODE (guard commented). UXR2 intact at both levels. Claims #47 updated, #48 + #49 added. 2 new YRGGBS00 annotations. |
| **H49** | **Test FALS-001 to FALS-006 predictions** | #054 | Brain/Meta | 6 falsification predictions pending test (layer 7 brain_state). Split by testability: **Testable now** (session #054): FALS-001 (brain_state.json size < growth threshold), FALS-002 (one-Read faster than multi-file), FALS-003 (knowledge_docs links reduce grep), FALS-005 (incident-analyst subagent matches INC-000006073 quality — test on INC-BUDGETRATE-EQG + INC-000006313 + INC-000005240). **Longer horizon**: FALS-004 (50 rules enough? — need 10 sessions of delta), FALS-006 (DQ-001 recurring check finds 5+ more vendor drift — need full fmifiit scan). Action: write `brain_v2/agi/falsification_test_session054.py` that evaluates each against current state + updates `falsification_log.json` with verdict PASSED/FALSIFIED/DEFERRED. |
| **H50** | **Triage 71 brain_spots (supersedes H36)** | #054 | Brain/Meta | Coverage 64.3% (71 MISSING, 0 GHOST, 0 PSEUDO). Classification target per CP-001: every blind_spot must have flavor + disposition (PROMOTE, MODEL_FROM_DATA, PSEUDO_REF_DROP, DEFER). Breakdown: 11 PERNRs (→ H41 PROMOTE as PERSON), 4 session #053 objects (→ H43 PROMOTE), ~56 remaining (SAP table refs like BSEG.XREF1, CL_* classes, DMEE trees, FM FMs). Target: coverage ≥ 80% post-triage. Script: `brain_v2/triage_blind_spots.py` classifies each via pattern matching + annotations lookup. Output: add `disposition` + `rationale` fields to each blind_spot. |
| ~~**H51**~~ | ~~**Audit + backfill traceability gaps in existing brain (6/6 DONE session #054)**~~ | ~~#054~~ | ~~Brain/Meta~~ | ~~**Closed #054.** All 6 sub-steps done: (1) 15/15 superseded claims linked, (2) 4/4 incidents annotated with chain_anchor_type (all 100% coverage), (3) annotation finding audit — 88 annotations, only 3 <80 chars, all 3 complete-concise (not truncated), 0 expansion needed, (4) 21/21 data_quality enriched, (5) 34/34 known_unknowns enriched, (6) 86/86 feedback rules tagged with derives_from_core_principle. Audit methodology validated CP-003 precision principle: empirical verification replaced assumption of truncation. Nothing further to do.~~ |
| **H53** | **D01K9B0F72 / I_KONAKOV (W) — HR COBL BAPI enhancement + 2 new Fund types impact audit** | #055 | HCM×PSM×FI / Investigation | **Raised by user 2026-04-16.** Transport `D01K9B0F72` (task type W = customizing), owner I_KONAKOV, labelled "HR COBL BAPI enhancement"; per user, 2 new Fund types were added. **Not yet in our CTS snapshot** (cts_transports latest ≪ F72). **Ambiguity to resolve first (CP-003)**: "Fund type" can mean (a) FINTYP master-config in T035C / `funds.TYPE` classifier — scope bounded to master data + reporting; or (b) new custom fields appended to `CI_COBL` / HR posting BAPI (`BAPI_ACC_HR_PAYROLL_POST`, `HR_POSTING_DOCUMENT_CREATE`) — scope extends into BSEG/BSIS enrichment, .NET callers, payroll posting docs. W-type (customizing) skews toward (a); "COBL BAPI enhancement" wording skews toward (b). **Action plan**: (1) pyrfc E071 pull on D01K9B0F72 to enumerate actual objects (R3TR TABU T035C entries vs R3TR CLAS/TABD CI_COBL append); (2) read T035C from P01 (currently NOT in Gold DB — gap) and diff vs our `funds.TYPE` distinct values; (3) if CI_COBL touched, extract the append structure + any BAdI `FI_POSTING_DERIVATION` / `HRPAY00_EXPORT_CE_RESULTS` impls; (4) assess impact on bseg_union view, BSIS enrichment (13-field set from #028), SISTER .NET reports, HR Workflow .NET, FM carry-forward, FMIOI/FMIFIIT keys. **Impact hypothesis (TIER_3, to falsify)**: IF only T035C, impact is reporting-only (new classifier values); IF CI_COBL fields, impact reaches BSEG and requires a new BSIS enrichment pass. **Owner of the change**: I_KONAKOV (also primary YRGGBS00 maintainer per H48 findings). **Connects to**: H42+H43 (new brain objects for T035C, CI_COBL append), data quality gap (T035C missing from Gold DB). |
| **H54** | **INC-000006906 follow-up: transport YTBAE002 MODE 'E' → 'N' fix to P01** | #058 | Treasury/Fix | Fix file drafted at `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap`. One-char change at `YTBAE002.abap:27`. Rollout: D01 apply + activate + transport of copies (pkg `YA`) → release to P01 → ask J_DAVANE (FU/MAP, Maputo) to retry → monitor ST22 on `SAPDBSDF:1983` for one week. Blast radius: zero behavioral change on happy path; errors remain visible via existing `GT_RECONCIL_MESS` → list output at `:2600-2616`. |
| **H55** | **STAD trace YTR1 / YTR2 / YTR2_HR usage (KU-2026-057-02)** | #058 | Treasury/Investigation | TBTCO shows YTBAE001 has 1 dormant job (STATUS=NULL), YTBAE001_HR zero. Before proposing decommission, confirm zero interactive usage via STAD for TCODEs YTR1 + YTR2 + YTR2_HR over at least the last 90 days. If zero: propose TCODE + program decommission. If non-zero: apply same MODE 'E' → 'N' fix at `YTBAE001.abap:118` + `YTBAE001_HR.abap:122` in a separate transport. **Dormant MODE 'E' landmine** — user decision Session #058 was NOT to fix speculatively; confirm usage first. |
| **H56** | **Extract YCL_FI_BANK_RECONCILIATION_BL (KU-2026-057-03)** | #058 | Treasury/Code | The 2023 OOP class that backs YFI_BANK1 / YFI_BANK_RECONCILIATION. Drives both `P_DETAIL` (detail ALV) and `P_DASH` (dashboard ALV) modes. Not yet extracted — shell program is only 34 LOC; all selection + rendering logic lives in this class. Extract via `RPY_CLASS_READ` over P01 SNC/SSO. Add annotation + edges to brain. Needed to answer whether this class eventually replaces YTR3 (YTBAE002) usage or supplements it. |
| **H57** | **YTBAI001 (SMARTLINK CMI940 → MT940) production status (KU-2026-057-01)** | #058 | Treasury/Investigation | Bank-statement file converter (197 LOC, A.ELMOUCH 2002). Hardcoded `/usr/sap/D01/conversion/input/TITRBK03/sg2707.txt` paths → deployed on D01, filesystem paths never updated for P01. Zero TBTCO runs. Check if SMARTLINK CMI940 still feeds SAP, or if EBS MT940 pipeline has fully replaced it. If dead: propose TCODE YTR0 + program decommission + TADIR cleanup. |
| **H58** | **YTBAM002_HR_UBO housekeeping TADIR-delete (KU-2026-057-04)** | #058 | Treasury/Cleanup | Include not pulled in by any executable today. Second-order fork (D_SIQUEIRA 2008) of YTBAM002_HR that hardcodes `BDCDTAB-FVAL = 'UBO'` vs `'UNES'`. Unreachable-code trap for future incident analysts. Confirm zero P01 usage via cross-project grep; if zero, TADIR-remove in a housekeeping transport. Low-priority cleanup. |
| **H59** | **ABAP discipline POINT B — native rails: transport RELEASE + ATC-via-REST, then retire kill-switch** | #082 | ABAP/Discipline | Deferred by JP 2026-06-15. Wire into `Zagentexecution/abap_deploy/deploy_object.py`: (1) create/RELEASE the workbench transport (primitives already exist: `SAPADTClient.create_transport` / `transport_release`) → durable version + enables import to **V01 (QAS)**; (2) **ATC via REST** (`atc_run` / `atc_worklist` exist) as the pre-release gate, replacing any home-made syntax check; (3) once #1+gate-stack are the path, **retire the `ALLOW_D01_WRITES` kill-switch** (replace blunt block with the disciplined process). Neither this project NOR CRP does this yet. Governing rule: `ecosystem-coordinator/.knowledge/way-of-working/sap-abap-change-discipline.md` steps #1/#3. |
| **H60** | **Define OUR smoke invariants + functionality fingerprints (deliberately NOT ported)** | #082 | ABAP/Discipline | CRP's `smoke_d01.py` + `quality_check.py` fingerprints are CRP-app-specific (zcrp_aprvl_hist pairing, currency render-safety, write-site counts). Porting them empty = cargo-cult (the rule warns against it). When ABAP dev resumes: define the invariants/fingerprints for OUR owned objects and chain them into `deploy_object.py` (post-write). Until then the gated readback path is the discipline. |
| **H61** | **Seed the git mirror + populate objects_manifest.yaml with full owned-Z set** | #082 | ABAP/Discipline | `Zagentexecution/abap_deploy/objects_manifest.yaml` is seeded with 2 objects (ZCL_CRP_PROCESS_REQ, ZCL_CRP_CERT_READER). Enumerate ALL Z*/Y* objects we actually own (TADIR AUTHOR/DEVCLASS=ours), add them as tier=custom, then run `python verify_mirror.py --adopt-missing` to pull live D01 source into `sap/classes/*.clas.abap` (read-only against D01). That makes deploy_object.py's diff-gate operational for the full set. |
| **H62** | **Quarantine/archive the ~78 legacy ad-hoc write scripts** | #082 | ABAP/Cleanup | The `deploy_*`/`reconstruct_*`/`force_*`/`smart_ccimp_*`/`direct_insert_*` scripts in `Zagentexecution/mcp-backend-server-python/` are the historical direct-write surface (~81% transport-blind). The `process-guardian` agent + CLAUDE.md pointer now steer to the single gated path; move the legacy scripts to an `archive/` (don't delete history) so they can't be invoked by mistake. Low-priority, do after H61. |
| **H63** | **Build a `Transport_Intelligence` companion (domain exists only as Word)** | #083 (2026-06-21) | Companion/Viz | The repo-wide 100% file census surfaced a knowledge domain with **no HTML companion** — it lives only as 5 `.docx` under `knowledge/domains/Transport_Intelligence/` (`SAP_Transport_Intelligence_Reference.docx`, `_Modules_Supplement.docx`, `_REFX_Dunning.docx`, `_Workflow.docx`, `_FlexWF_InvUnblock_BCM.docx`). Action: synthesize an HTML companion from those docs (artifact-hierarchy: Word is the snapshot, the companion is the living layer), register in `companions/companions.json` (domain `transport`), let `build_companion_graph.py` relate it. NOTE: `transport_companion_D01K9B0CBF_v2.html` already exists but is a single-transport (STEM) companion, NOT the domain reference. |
| **H64** | **Classify/register `my_monitors_dashboard.html`** | #083 (2026-06-21) | Companion/Decision | Census found the only genuinely-unregistered dashboard: title "My Monitors — JP Lopez Personal Dashboard" (`Zagentexecution/my_monitors/my_monitors_dashboard.html`, git-tracked, 8KB). Decide: (a) promote → copy to `companions/`, register in `companions.json` under a new `monitoring` domain (the landing `domains_map` catch-all already renders unmapped domains, so it'll appear); or (b) keep as a personal/local tool, out of the registry. The two `golden_*_rows.html` viewers are raw Golden-DB row dumps (no title) → leave as data viewers, NOT companions. |
| **H65** | **Clean up ~20 stale git-tracked duplicate companion HTML** | #083 (2026-06-21) | Companion/Cleanup | `companion_graph.json → html_inventory_repo_wide` lists deterministically: 3 `duplicate_copies` (identical) + 17 `diverged_stale` (OLDER generations) of the canonical `companions/*.html`, in build dirs (`Zagentexecution/mcp-backend-server-python/`, `Zagentexecution/dashboards/`, `Zagentexecution/sap_data_extraction/reports/`, repo-root `py_finance_wage_type_companion_v1.html`). `companions/` is the current copy (verified by mtime). These tracked stale copies create the "more companions" illusion and risk opening an old version. Action (needs user OK — `git rm` of tracked files): remove stale copies, point build scripts to emit directly into `companions/`, re-run `build_companion_graph.py` to confirm 0 duplicates. Regenerate the list anytime: `python scripts/build_companion_graph.py`. |
| **H52** | **Integration-element audit — per-integration SAP elements (FM / IDoc / program+variant / endpoint)** | #055 | Integration/Brain | **MAJOR PROGRESS session #055**. Live probes on BOTH D01 and P01 via pyrfc + probe script `probe_p01_integration.py`. **5 program sources extracted** (COUPA → `YCL_FI_COUPA_ACCOUNTING_LOAD` + RFBIBL00; GEODIS = SFI CSV; SF_ORGANIZATION = SFI org; TULIP = DBCON pull; UNESDIR = AD→PA0105 subtype 0010). **MuleSoft partner profile on P01** (EDP13 outbound: PROJECT/PROJECT02, FUNDSCENTER/FUNDSCTR, SYNCH; EDP21 inbound: ADRMAS/ADR2MAS/ADR3MAS/DEBMAS). **P01 live EDIDC**: **9,242 PROJECT IDocs to MULE_PROD, ALL failing at status 29 (ALE service error)** — recent example DOCNUM 4143503 created 2025-11-12 by user M_SARMENTO-G via CJ20N. FUNDSCENTER + SYNCH profile entries have zero traffic. **DBCON P01 = 2 entries only** (TULIP + UNESDIR); SISTER DBCON exists only on D01 → SISTER production is RFC-only. **Corrections vs prior memory**: (a) SuccessFactors IS LIVE; (b) GEODIS = SFI not logistics; (c) SISTER = RFC-only in P01 (not 2-channel); (d) UNESDIR = SQL-direct not HTTP; (e) P01 ≠ D01 partner profiles (drift). **New ops finding (flag to team)**: 9,242 accumulated status-29 PROJECT IDocs → CJ20N Core Manager integration is broken. **Remaining unknowns**: Salesforce BOR mechanism (no P01 evidence); .NET Web.config → FM mapping; COUPA file path (inside class); UNJSPF SOAP payload. Full inventory: `memory/project_integration_elements_gap.md`. |
| H25 | **T028A + T028E extraction (account symbol definitions)** | #029 | Config | T028A = symbol-to-GL mapping (BANK→10xxxxx, BANK_SUB→11xxxxx). T028E = posting key definitions. Validates the account symbol configuration. **Zombie age 19. Kill if not done by #055.** |
| H26 | **T012K UKONT re-extraction** | #029 | Config | T012K missing UKONT field (sub-bank GL paired with bank GL). Need to re-extract with all fields to validate 10xxx↔11xxx pairing. **Zombie age 19. Kill if not done by #055.** |
| ~~**H33**~~ | ~~**Brain v2: Absorb ALL text into graph — zero dead text**~~ | ~~**#040**~~ | ~~**Brain**~~ | ~~**Done #040.** `knowledge_ingestor.py` shipped: 113 KNOWLEDGE_DOC nodes + 40 SKILL nodes + 19 COMPANION nodes + 1,177 reference edges (DOCUMENTED_IN/SKILLED_IN/DISCOVERED_IN). Covers knowledge/domains/ (44 docs), .agents/skills/ (40 skills), session retros (34), intelligence docs, HTML companions (19). Enforced by preflight check S5 (no static artifacts when brain exists). Principle: if it has relationships, it's a node.~~ |
| ~~**H30**~~ | ~~**Brain v2 Phase 1: Behavioral edges from code**~~ | ~~**#039**~~ | ~~**Brain**~~ | ~~**Done #040.** 1,251 code nodes + 671 behavioral edges from 1,142 ABAP files. Parser: 6 regex patterns (SELECT, CALL FUNCTION, INSERT/MODIFY, INHERITING FROM, INTERFACES, BAdI naming). Multi-class flat directory grouping (DMEE pattern). Recursive scanner handles 5-level nesting after project reorganization.~~ |
| ~~**H31**~~ | ~~**Brain v2 Phase 2: Config + Integration + Transport edges**~~ | ~~**#039**~~ | ~~**Brain**~~ | ~~**Done #040.** 50,798 nodes + 111,048 edges from 7 ingestors. Config (T042A, DMEE trees, BCM, house banks), Transports (7,745 + 46K objects → 108K edges), Integration (239 RFC dests, 3,073 RFC-enabled FMs, 7 .NET apps, IDocs), SQLite schema (83 tables + 18 proven joins), Jobs (227 programs), Processes (5 E2E, 30 steps). Build time: 45s.~~ |
| ~~**H32**~~ | ~~**Brain v2 Phase 3: Process overlay + Query engine + CLI**~~ | ~~**#039**~~ | ~~**Brain**~~ | ~~**Done #040.** 4 query types operational: impact analysis (BFS with risk decay), dependency tracing (reverse BFS), structural similarity (Jaccard), gap analysis (2,931 findings on first run). CLI: `python -m brain_v2 build\|stats\|impact\|depends\|similar\|gaps\|search\|critical\|path`. Validated: HR_READ_INFOTYPE impact → 9 affected objects, ZCL_HR_FIORI_EDUCATION_GRANT depends → 26 dependencies.~~ |
| ~~H29~~ | ~~**Update 510 SKAT text differences P01→D01**~~ | ~~#034~~ | ~~Data Sync~~ | ~~**Done #038**: real scope was **1,690 rows multi-language** (not 510 English-only from #034 note). 1,511 UPDATEs (518 E + 500 F + 493 P) + 179 INSERTs (87 F + 92 P). Pattern: SELECT SINGLE + UPDATE FROM ls (avoids 72-char ABAP truncation bug). 141 batches, ok=1690 ko=0, gap=0 verified. Log: `knowledge/domains/FI/h29_skat_sync_log.md`. Side-fix: `rfc_helpers.py` RECONNECTABLE_ERRORS extended with RFC_CLOSED/broken/WSAE* patterns after mid-flight crash at batch 31.~~ |
| ~~H27~~ | ~~TCURR/TCURF extraction (exchange rates)~~ | ~~#029~~ | ~~Analytics~~ | ~~Done #030: TCURR 54,993 rates + TCURF 2,614 factors loaded. Ready for H21 currency conversion.~~ |
| ~~H28~~ | ~~Bank Statement EBS Companion HTML~~ | ~~#029~~ | ~~Viz~~ | ~~Done #030: `bank_statement_ebs_companion.html` — 10 tabs (Overview, E2E Chain, Config Tiers, Posting Rules, Algorithms, GL Structure, BA Determination, Production Reality, Interactive Map, Glossary). Includes production analysis: 97% outgoing clearing, 46.5% incoming, 85.7% algo 015. SVG network diagram.~~ |
| ~~H15~~ | ~~Read Blueprint BCM pages 21-47~~ | ~~#021~~ | ~~Knowledge~~ | ~~Done #022 — Full 21 SAP Notes, Delegation of Authority table, grouping rules, XML char handling all extracted~~ |

### 🟡 DESVIACIONES DE ESQUEMA EN LOS STORES — detectadas 2026-08-19, sin tratar

Las detecta `python Zagentexecution/quality_checks/store_schema_check.py` (enganchado al hook Stop,
sale 1). **Ninguna es de la sesión 101**: vienen de las sesiones 51, 62, 66, 69, 71, 79, 97 y 98.
Hasta ahora nadie las veía; ahora salen en cada cierre.

**No se arreglaron a propósito.** Rellenar `created_session` en 13 claims donde el dato no existe
sería inventarlo, y es exactamente lo que la regla `feedback_label_inferred_vs_measured` prohíbe.

#### claims.json — ~~104~~ ~~76~~ **41** de 520, por combinación de lo que falta

| # | Cuántos | Falta | Tratamiento |
|---|---:|---|---|
| ~~S1~~ | ~~28~~ 0 | ~~`domain_axes`~~ | **HECHO 2026-08-19.** Y NO era derivable del `domain` como escribí: el mismo dominio produce hasta 36 `domain_axes` distintos. Lo resolvió el generador que ya existía, `brain_v2/scripts/backfill_domain_axes.py`, que infiere por palabra clave sobre el texto del claim. 44 claims + 49 reglas + 1 incidente al 100% |
| ~~S2~~ | ~~23~~ 0 | ~~`resolution_notes` + `resolved_session`~~ | **HECHO 2026-08-19** |
| ~~S3~~ | ~~11~~ 0 | ~~`resolved_session` + `status`~~ | **HECHO**: los 11 tenían `status='VERIFIED'`, que describe verificación y no ciclo de vida — y eso ya lo dicen `claim_type=verified_fact` + `confidence=TIER_1` en los 11 sin excepción. Normalizado a `active` |
| ~~S4~~ | ~~9~~ 0 | ~~`resolution_notes`~~ | **HECHO 2026-08-19** |
| S5 | 8 | `created_session` + `resolved_session` + `status` | **NO automatizable**: la sesión de origen no se puede deducir |
| S6 | 25 | combinaciones de los anteriores | Mismo criterio por campo |

#### claims.json — inconsistencia de TIPO, además de ausencia

~~`created_session` convive en cuatro formatos~~ — **HECHO 2026-08-19**: normalizados **91**
referencias de sesión a entero (`'#51'`, `'#051'`, `'s079'`, `'S-098'` → `51`, `79`, `98`) en los tres
stores. `int` pasa de 379 a 421 en claims.

**Lo que queda sin tocar y no debe tocarse**: 115 valores tipo `'s-2026-06-29'`. Son **fechas**, no
números de sesión, y convertirlas inventaría el dato. Y 13 ausentes, que tampoco se pueden deducir.

`status` tiene 7 valores para 520 claims: `active` (448) · `superseded` (37) · ausente (21) ·
`VERIFIED` (11) · y tres con un solo uso. **`VERIFIED` parece un `claim_type` colado en `status`** —
verificar antes de tocar.

#### incidents.json — ~~3~~ 0 · **HECHO 2026-08-19**

| Incidente | Faltaba | Cómo se resolvió |
|---|---|---|
| `INC-BUDGETRATE-EQG` | `primary_object_id` | **Derivado del propio registro**: su `root_cause_summary` habla del *"15-member `ZFIX_EXCHANGERATE` composite"* y es el 2º de `related_objects` |
| `INC-000006906` | `root_cause_summary` | **Resumido de su doc §2** y citando la fuente: `MODE 'E'` en los BDC + WAN lento (`YTBAE002.abap:27`) |
| `INC-000005638` | `chain_anchor_coverage_pct`, `chain_audited_session` | **`null` a propósito.** La auditoría de cadena ocurrió o no; los demás tienen valor porque se auditaron en las sesiones 54/56/78/99. Éste nunca. Poner un porcentaje sin haberla hecho sería inventarlo — queda anotado en `chain_anchor_note` |

De paso, `INC-PSTLADR-NOV2026` llevaba `chain_audited_session: 's101'` donde los demás son entero.
Era mío, de esta misma sesión. Normalizado a `101`.

#### feedback_rules.json — ~~42~~ **16** de 214

> Ganaron `domain_axes` (49) en la misma pasada, pero sus desviaciones son de OTROS campos: `derives_from_core_principle` y `created_session`. Siguen en 42.


| Falta | Cuántos | Tratamiento |
|---|---:|---|
| ~~`derives_from_core_principle`~~ | ~~38~~ 0 | **HECHO 2026-08-19.** Leídas una a una y asignadas. Reparto final del corpus: CP-003 114 · CP-001 70 · CP-002 30 |
| `created_session` | 16 | **No deducible.** Dejar como está |
| `rule` | ~~2~~ 0 | **HECHO 2026-08-19.** No estaban vacías: el texto vivía bajo `statement` y bajo `title` — la misma divergencia que se cometió hoy con los claims. Renombrada la clave, sin perder nada |

#### Por dónde empezar

1. ~~Las 2 reglas sin `rule`~~ — **hecho**. No estaban vacías, el texto estaba bajo otra clave.
2. ~~S1 (28) y la normalización `'#51'` → `51`~~ — **hechas**.
3. ~~S2 + S4 (32)~~ — **hechas**. Y los 6 `superseded` que parecían necesitar decisión no la
   necesitaban: llevaban el dato bajo otra clave (`superseded_session`, o la sesión dentro de
   `superseded_reason`). Recuperado, no inventado.
4. ~~Decidir S3~~ — **resuelto sin convención**: no había que asumir nada.
5. **Lo que QUEDA (41)**: 27 sin `created_session`+`resolved_session`+`status` y 14 sueltos.
   Todos necesitan la sesión de origen, que no se puede deducir. **Dejar como están** — inventar la
   procedencia es peor que no tenerla.

Re-medir: `python Zagentexecution/quality_checks/store_schema_check.py`

### 🟢 BACKLOG — When blocking/high are clear

> **Session #036 Purge**: 31 zombie items (>10 sessions old, no movement) killed with explicit reason.
> Kill criteria: (a) speculative, (b) ceremony not decision-enabling, (c) superseded, (d) nice-to-have masquerading as work.
> Pre-purge: 52 items. Post-purge: 21 items. Survivors have a deadline or a hard business tie-in.

#### Process Mining & Analytics
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G1~~ | ~~OCEL 2.0 multi-object~~ | ~~#009~~ | ~~KILLED #036: speculative. Current pm4py mining is not queried by any decision. Adding OCEL = adding ceremony.~~ |
| ~~G2~~ | ~~CTS conformance deep dive~~ | ~~#009~~ | ~~KILLED #036: found 100% conformant. No value in deeper analysis.~~ |
| ~~G3~~ | ~~Pattern Brain (Algorithms)~~ | ~~#005b~~ | ~~KILLED #036: speculative "anomaly detection" with no target metric.~~ |
| ~~G4~~ | ~~process-intelligence.html filter RELE~~ | ~~#003~~ | ~~KILLED #036: minor cosmetic on a dashboard nobody uses.~~ |
| ~~G5~~ | ~~process-intelligence.html browser verify~~ | ~~#003~~ | ~~KILLED #036: same dashboard, same lack of demand.~~ |

#### Skills & Governance
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G6~~ | ~~Build T2R skill~~ | ~~#018~~ | ~~KILLED #036: YAGNI. No Travel-to-Claim work in session backlog. Build when demanded.~~ |
| ~~G7~~ | ~~Build P2D skill~~ | ~~#018~~ | ~~KILLED #036: YAGNI. Same as G6.~~ |
| ~~G8~~ | ~~Create crp_fiori_app skill~~ | ~~#017~~ | ~~KILLED #036: speculative. CRP has 19 items but none active.~~ |
| G9 | **Publish `sap-intelligence` SKILL.md** to ecosystem | ecosystem | Survives — governance obligation to ecosystem coordinator |
| G10 | **Promote Transport Companion pattern** | ecosystem | Survives — ecosystem obligation |
| G11 | **Promote Company Code Copy checklist** | ecosystem | Survives — ecosystem obligation |
| ~~G12~~ | ~~Cross-reference maturity vs SESSION_LOG~~ | ~~#018~~ | ~~KILLED #036: audit ceremony. `session_preflight.py` Check 8 now enforces skill count automatically.~~ |

#### Data Extraction (non-blocking)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G13~~ | ~~Job source code extraction~~ | ~~#018~~ | ~~KILLED #036: 228 programs already catalogued. Source extraction is speculative until a specific program needs it.~~ |
| ~~G14~~ | ~~BP Conversion extraction~~ | ~~#005b~~ | ~~KILLED #036: S/4HANA readiness is not a 2026 goal. Resurrect when migration is actually planned.~~ |
| ~~G15~~ | ~~PSM domain code extraction~~ | ~~#005b~~ | ~~KILLED #036: extracted_sap/PSM/ empty = no concrete need, only completionism.~~ |
| ~~G16~~ | ~~Real Estate domain extraction~~ | ~~#005b~~ | ~~KILLED #036: new domain discovery ≠ requirement. No RE work in pipeline.~~ |

#### CTS Dashboard Fixes
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G17~~ | ~~Improve module classification~~ | ~~#004~~ | ~~KILLED #036: 3,329/4,168 in "General IMG" — cosmetic. Dashboard works.~~ |
| ~~G18~~ | ~~total_mods verification~~ | ~~#004~~ | ~~KILLED #036: trivial QA on a working dashboard.~~ |
| ~~G19~~ | ~~topbar KPI sync~~ | ~~#004~~ | ~~KILLED #036: hardcoded value vs data mismatch — 5 min fix if ever demanded, not a PMO item.~~ |
| ~~G20~~ | ~~TADIR cache enrichment~~ | ~~#004~~ | ~~KILLED #036: SOTR/VARX skipped — no user-facing impact.~~ |

#### Infrastructure
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G21~~ | ~~Vector Brain (ChromaDB)~~ | ~~#005b~~ | ~~KILLED #036: speculative. 30 sessions without a use case. Current keyword grep works.~~ |
| ~~G22~~ | ~~**SAP MCP Server build**~~ | ~~#005b~~ | ~~**KILLED #037**: MCP server already exists and is operational at `Zagentexecution/mcp-backend-server-python/sap_mcp_server.py`. Done-but-never-closed pattern (same as H10 in #036). Zombie for 30 sessions because no one struck it. Verified via file existence.~~ |
| ~~G23~~ | ~~Duplicate script cleanup~~ | ~~#005b~~ | ~~KILLED #036: hygiene, not strategic. Do during a refactor, not as a PMO item.~~ |
| ~~G24~~ | ~~Index YRGGBS00 + YPS8~~ | ~~#005b~~ | ~~KILLED #036: indexing ceremony. Nobody queries this index.~~ |
| ~~G25~~ | ~~Archive legacy root docs~~ | ~~#005b~~ | ~~Done #023~~ |
| ~~G26~~ | ~~Brain auto-refresh workflow~~ | ~~#006~~ | ~~KILLED #036: see G1/H6 — brain is write-only. Auto-refresh = more writes, not more value.~~ |
| ~~G27~~ | ~~Notion PMO sync~~ | ~~#006~~ | ~~KILLED #036: nice-to-have integration. PMO_BRAIN.md is the source of truth; duplication adds sync cost.~~ |

#### Integration & Connectivity (Session #032)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G37 | **Build Basis Monitoring HTML companion** | #032 | Script `sap_system_monitor.py` ready, needs companion. SM04/SM37/SM35/ST22. |
| G38 | **Update system_inventory.html with .NET apps** | #032 | 7 UNESCO .NET apps discovered but only in connectivity diagram, not inventory page |
| G39 | **Add RFC API Surface tab to rfc_analysis.html** | #032 | 334 RFC-enabled FMs by domain. Data in tfdir_custom table. |
| G40 | **Investigate TULIP + UNESDIR 93% job failures** | #032 | YHR_MANAGER_FROM_TULIP_UPDATE (14/15 failed), YHR_CREATE_MAIL_FROM_UNESDIR (28/30 failed) |
| ~~G41~~ | ~~Verify SuccessFactors EC migration status~~ | ~~#032~~ | ~~Closed #035: SF EC IS ACTIVE. ECPAO_OM_OBJECT_EXTRACTION (43 parallel jobs, 1,290 runs) + ECPAO_EMPL_EXTRACTION (3 jobs, 51 runs). Massive OM+Employee extraction to EC Payroll. Not "planned" — live in production.~~ |
| G42 | **Build FI Support Agent skill** | #032 | Orchestrates fi_maintenance + payment_bcm + bank_statement + brain + Gold DB to resolve tickets |
| G43 | **Confirm SAPBC/us0033 is decommissioned** | #032 | Legacy Business Connector. No jobs/code/IDocs. Check SM59 connection test. |
| G44 | **Extend `sap_master_data_sync` to CC/PC/FA** | #034 | Cost centers (CSKS/CSKT), profit centers (CEPC/CEPCT), functional areas (TFKB/TFKBT), fund centers (FMFCTR/FMFCTRT). Same 4-step pattern. |
| G45 | **Update connectivity diagram with file-based integration tier** | #035 | 5 tiers: SWIFT/banks (7K runs), COUPA (348), SuccessFactors EC (1,340), TULIP/UNESDIR (45), Data Hub/BW (30+). New integration vector. |
| G46 | **Update `sap_interface_intelligence` skill with file-based vector** | #035 | Add TBTCO/TBTCP job analysis as integration discovery method. Current skill only covers RFC destinations + IDocs. |
| G47 | **Investigate Data Hub target system** | #035 | YFM_OUTPUT_INDIRECT_COSTS_DH + YHR_ORG_UNIT_COUNT_DH + YFM_STAFF_COST_DISTRIBUT_DH — "DH" suffix = Data Hub. What system is this? |

#### Future Ideas
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G28 | **Fiori PA Mass Update App** | #002 | Survives — consolidates PRAA* BDC (135/quarter) + absorbs G54. Real business op value. **Rejustified #037**: age 33 sessions but real consolidation value confirmed. Deadline: ship scoping doc (not app) in 5 sessions or KILL. Needs coupling with HR roadmap, not H13. |
| ~~G29~~ | ~~Coupa → SAP API Interface~~ | ~~#002~~ | ~~KILLED #036: speculative. COUPA file + BDC integration is working (integration_map_complete.md). No business push to replace.~~ |
| ~~G30~~ | ~~BDC Trigger Analysis (RISK)~~ | ~~#002~~ | ~~KILLED #036: "risk analysis for a hypothetical replacement". No replacement in flight.~~ |
| ~~G31~~ | ~~P01 user activity map~~ | ~~#006~~ | ~~KILLED #036: nice-to-have. Not tied to any decision.~~ |
| ~~G32~~ | ~~Service node enrichment~~ | ~~#006~~ | ~~KILLED #036: brain ceremony.~~ |
| ~~G33~~ | ~~Transport Living Knowledge~~ | ~~#005b~~ | ~~KILLED #036: speculative "evolving seeds" concept.~~ |
| ~~G34~~ | ~~abapGit integration~~ | ~~#006~~ | ~~KILLED #036: 29 sessions dormant. No abapGit workflow in use.~~ |
| ~~G35~~ | ~~Catch live BDC field data~~ | ~~#002~~ | ~~KILLED #036: requires live SAP + SM35 access + a failing session — too many preconditions for nonzero value.~~ |
| ~~G36~~ | ~~sap_bp_conversion SKILL.md~~ | ~~#005b~~ | ~~KILLED #036: future skill for future migration. YAGNI.~~ |
| G55 | **BP Conversion Readiness: research SAP vendor→BP migration strategies** | #048 | **RESURRECTED from G14+G36 — now justified by INC-000006073.** Wrong KTOKK caused production failure. 21 BP tables now in Gold DB (2.5M rows). Research SAP help (help.sap.com/docs/SAP_S4HANA_ON-PREMISE vendor-customer-integration), SAP blogs, conversion strategies. Analyze UNESCO data: KTOKK distribution, CVI_VEND_LINK gaps (0 rows = no BP↔vendor mapping yet), BUT000 vs LFA1 coverage (559 BP vs 316K vendors = <1% converted). Output: `knowledge/domains/BusinessPartner/bp_conversion_readiness.md` |
| G56 | **Travel domain discovery: KTOKK anomalies + GGB1 coverage gaps across all company codes** | #048 | Cross LFB1.AKONT with GB901/GB922 to find every GL with vendors but no substitution rule — systematic INC-000006073 prevention. Also: KTOKK vs PERSG cross-check to find more wrong vendor account groups. |
| G57 | **Ingest Travel + BP domain into Brain v2 (48 + BP edges)** | #048 | 69 ABAP files + 21 Gold DB tables + relationship definitions in `travel_brain_edges.md`. Run `sap_brain.py --ingest-domain Travel` and `--ingest-domain BusinessPartner`. |
| G58 | **Extract PTRV_SCOS + PTRV_SHDR with ALL fields** | #048 | Current extraction has 8/35 and 11/25 fields. Re-extract with DDIF pattern for full trip cost assignment data. |
| G59 | **Build automated annotation prompts mid-session** | #049 | AGI layers (known_unknowns, falsification, data_quality) decay without enforcement. Need a hook or workflow that prompts agent to populate them when discoveries happen. Currently relies on agent discipline. |
| G60 | **Validate `/hooks` reload + SessionStart hook fires** | #049 | Created `.claude/settings.json` SessionStart hook in #049. Watcher wasn't watching `.claude/` at session start, so hook needs `/hooks` open or restart to activate. Verify it actually fires next session. |

#### Ecosystem-Level
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G48 | **Rescue Vendor MDM** | ecosystem | 98 days stalled |
| G49 | **ADR-004: Testing as Skill or Project?** | ecosystem | Architecture decision pending |
| G50 | **Promote BSP React patterns** | ecosystem | To `.knowledge/skills/sap-fiori-react/SKILL.md` |
| G51 | **Score UNESCO SAP Brain on 10 dimensions** | ecosystem | Gap analysis |

#### Added Session #036 (2026-04-05)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G52 | **Integration map companion HTML** | #035 retro | Build interactive visual from integration_map_complete.md (37 flows, 8 channels, 18+ systems) |
| G53 | **Investigate 10 integration open questions** | #035 retro | Exchange rate source (Q1), Data Hub identity (Q2), LSMW origin (Q3), Core Mgr bidirectional (Q4), COUPA/SWIFT file paths (Q5), BOC purpose (Q6), AWS security (Q7), Vendor export target (Q8), UNJSPF payload (Q9), TULIP/UNESDIR 93% failure (Q10) |
| ~~G54~~ | ~~Design Fiori replacement for PRAA*~~ | ~~#005 (moved from H7 #036)~~ | ~~MERGED into G28 #036: PRAA replacement is the same concept as "Fiori PA Mass Update App". Two items, one idea.~~ |

#### Added Session #036 (2026-04-05) — Infrastructure for AGI-discipline
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G55~~ | ~~Skills Consolidation Execution (38→6 archetypes)~~ | ~~#036~~ | ~~KILLED #036 by user: knowledge loss unacceptable. Skills are memory, merging is lossy compression. See `.agents/SKILLS_CONSOLIDATION_PLAN.md` (REJECTED). Alternative: individual deletion of truly-dormant skills only if they've been dormant 30+ sessions AND contain no unique knowledge.~~ |
| G56 | **Nightly SAP health check (`sap_health_check.py`)** | #036 | Auto-generated invariant queries over Gold DB (FM-FI balance, BCM dual-control delta, open item aging). Converts platform from archive to monitor. |
| ~~G57~~ | ~~Convert 10 more feedback rules to executable checks~~ | ~~#036~~ | ~~KILLED #036 (user decision): same growth paradigm as skills and memory. Feedback files are part of memory — they GROW, never consolidate. Converting to executable checks is optional for high-frequency rules, not a reduction target. `session_preflight.py` Check 9 updated to track health, not count.~~ |
| ~~G58~~ | ~~**Route H13 BCM finding into `sap_payment_bcm_agent` SKILL.md**~~ | ~~#036~~ | ~~Done #037 via skill_coordinator — new "Dual-Control Audit" section at `sap_payment_bcm_agent/SKILL.md` with SQL query, reproducible findings, CUR_STS vs STATUS guidance, user pattern signatures, remediation paths, invocation triggers. ~90 lines substantive content. First real invocation of skill_coordinator's routing protocol.~~ |
| ~~G59~~ | ~~**Route file-based integration vector into `sap_interface_intelligence`**~~ | ~~#036~~ | ~~Done #037 via skill_coordinator — new "File-Based Integration Vector" section at `sap_interface_intelligence/SKILL.md` with pattern signature, detection method, channel matrix (RFC/IDoc/HTTP/DB/Transport/File), COUPA reference, invocation triggers. ~60 lines. 9 systems identified, full per-system enumeration deferred to #038+.~~ |

#### Added Session #039 (2026-04-06)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G61~~ | ~~**Brain v2: fix impact query direction + v1 migration (73K fund nodes)**~~ | ~~#039~~ | ~~**Done #041.** Impact direction model corrected: ROUTES_TO_BANK→bidirectional, forward/backward traversal working. FPAYP.XREF3→32 objects. v1 migration deferred (fund nodes are taxonomic, low value for impact analysis). Domain knowledge ingestor covers BAdI param tables.~~ |
| ~~G62~~ | ~~**Brain v2: ingest DMEE→FPAYP.XREF3 edge from h18_dmee_tree_nodes.csv**~~ | ~~#039~~ | ~~**Done #041.** Domain knowledge ingestor creates DMEE class→FPAYP/REGUH/T042Z edges (88 edges). USES_DMEE_TREE edges (36) from T042A bank routing (SOG*→/CGI_XML_CT_UNESCO). Full chain: FPAYP.XREF3→class→DMEE→paymethod→bank verified.~~ |
| G63 | **Formalize Discovery Patterns as ecosystem skill** | #039 | Independent of Brain v2. 6 proven patterns (Payment E2E, P2P, Integration, Bank Recon, Code+BAdI tracing, Transport Impact). Create `.agents/skills/discovery_patterns/SKILL.md` + promote to ecosystem-coordinator as `enterprise-discovery` skill. |
| G64 | **Brain v2: self-improvement research track** | #039 | **Phase 4 (after H32).** Investigate real self-improving KG models (Graphiti temporal, Agentic-KGR co-evolution, ARC Prize refinement). Spec: Section A.7 (3 validated loops) + A.8 (platform absorption). |

#### Added Session #038 (2026-04-05)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| ~~G60~~ | ~~**User-operated monitor bundle: BCM dual-control + Basis (SM04/SM37/SM35/ST22)**~~ | ~~#038~~ | ~~**Done #038 (added + shipped same session).** Location: `Zagentexecution/my_monitors/run_my_monitors.py` + `my_monitors_dashboard.html` (8.9 KB, 2 tabs: BCM + Basis) + `README.md`. On-demand launcher over Gold DB (no cron, no SMTP, no infra). Tab 1 surfaces H13 finding (3,359 same-user batches, Wednesday cycle, top-2 ops). Tab 2 surfaces TBTCO job health + TFDIR_CUSTOM FM inventory + ICFSERVICE count. User's "el monitor puede ser mío junto a Basis" idea from Block 4.~~ |

#### Added Session #050 (2026-04-09)
| # | Task | First raised | Notes |
|---|------|-------------|-------|
| G65 | **Run vendor_master_integrity_check.py against full master + remediation report** | #050 | Resolves FALS-006 + KU-020. Run the script with default threshold + a looser rank-based pass. Produce a per-(KTOKK,BUKRS) outlier list. Cross-check with GGB1 coverage. Estimate full exposure across the 316K vendor master. Promote findings to BusinessPartner README and PMO if scope is >10 vendors. |
| G66 | **PA0027 subtype 02 expiration scan across employee master** | #050 | INC-000006073 root cause included a BAdI safety net that silently fails when PA0027-02 record is expired (Katja's expired 2021-01-31). Build a recurring check that lists all employees whose latest PA0027-02 record's ENDDA is in the past. The BAdI then never fires for them — they are exposed to the same intercompany trip failure. Promote to `Zagentexecution/quality_checks/pa0027_subtype_02_expiration_check.py`. |
| G67 | **TADIR-wide brain coverage metric** | #050 | Resolves KU-023. The current `_coverage.pct_classified = 75.6%` only measures the closed loop (objects the brain has TALKED about). The open loop is unmeasured: how many `Y*/Z*` objects exist in TADIR vs how many are in `brain_state.objects`? Build a one-shot script that queries TADIR via RFC, joins with `brain_state.objects` keys, and reports per-domain coverage. |

---

## COMPLETED (Archive)

Items completed across all 19 sessions — kept for audit trail.

| # | Task | Completed | Session |
|---|------|-----------|---------|
| ~~1~~ | Extract FMIFIIT full | 2026-03-15 | #005 |
| ~~2~~ | Brain redesign — Living Knowledge Engine | 2026-03-15 | #006 |
| ~~3~~ | Create `sap_data_extraction` SKILL.md | 2026-03-15 | #007 |
| ~~4~~ | Consolidate 3 SQLite DB copies | 2026-03-15 | #007 |
| ~~5~~ | Run overnight FI/MM extraction | 2026-03-16 | #010 |
| ~~6~~ | CDHDR extraction (7.8M rows) | 2026-03-16 | #011 |
| ~~7~~ | P2P complement: EBAN+RBKP+RSEG | 2026-03-16 | #011 |
| ~~8~~ | ESLL extraction (2.9M rows) | 2026-03-19 | #013 |
| ~~9~~ | FMIOI extraction (1.8M rows) | 2026-03-19 | #013 |
| ~~10~~ | Jobs intelligence (228 programs) | 2026-03-19 | #014 |
| ~~11~~ | Interface intelligence (239 RFC dests) | 2026-03-19 | #014 |
| ~~12~~ | P2P event log (848K events) | 2026-03-19 | #014 |
| ~~13~~ | Connectivity diagram | 2026-03-19 | #014 |
| ~~14~~ | Brain 73.9K nodes (8 sources) | 2026-03-19 | #014 |
| ~~15~~ | Cost recovery analysis | 2026-03-26 | #016 |
| ~~16~~ | Golden Query built | 2026-03-26 | #016 |
| ~~17~~ | BSIS/BSAS 13-field enrichment | 2026-03-26 | #016 |
| ~~18~~ | FMIFIIT OBJNRZ 2025 only | 2026-03-26 | #016 |
| ~~19~~ | GOVERNANCE.md + SKILL_MATURITY.md | 2026-03-26 | #018 |
| ~~20~~ | 1,002-file commit | 2026-03-26 | #018 |
| ~~21~~ | Transport companion D01K9B0CBF | 2026-03-26 | #019 |
| ~~22~~ | sap_transport_companion skill | 2026-03-26 | #019 |
| ~~23~~ | sap_company_code_copy skill | 2026-03-26 | #019 |
| ~~24~~ | sap_payment_bcm_agent skill (728 lines, 13 PDFs) | 2026-03-27 | #021 |
| ~~25~~ | sap_payment_e2e skill (process mining results) | 2026-03-27 | #021 |
| ~~26~~ | Payment BCM companion HTML (664KB) | 2026-03-27 | #021 |
| ~~27~~ | Payment process mining HTML (694KB, 1.4M events) | 2026-03-27 | #021 |
| ~~28~~ | Gold DB +9 tables (BNK_BATCH_HEADER/ITEM, REGUH, PAYR, T042*, T012*, T001) | 2026-03-27 | #021 |
| ~~29~~ | PMO audit: 11 items closed (B1,B4-B9,H8,H9,H16,H17) | 2026-03-31 | #028 |
| ~~30~~ | FMIFIIT OBJNRZ enrichment 2024+2026 (all years complete) | 2026-03-31 | #028 |
| ~~31~~ | EKBE BUDAT+6 fields enrichment (363K rows, 2-pass) | 2026-03-31 | #028 |
| ~~32~~ | 4-stream payment event log (1.85M events, 550K cases) | 2026-03-31 | #028 |
| ~~33~~ | Bank recon process discovery (239K docs, 91.2% auto) | 2026-03-31 | #028 |
| ~~34~~ | Companion v8 (14 tabs: +Deep Analysis, +Bank Recon, 794KB) | 2026-03-31 | #028 |
| ~~35~~ | Brain 73,935 nodes (+10 Source 9: streams, findings, bank recon) | 2026-03-31 | #028 |
| ~~36~~ | BSAS AUGBL enrichment (553K items, 100% fill) | 2026-03-31 | #030 |
| ~~37~~ | TCURR (55K) + TCURF (2.6K) exchange rates extracted | 2026-03-31 | #030 |
| ~~38~~ | Bank Statement EBS Companion v1 (10 tabs, production analysis) | 2026-03-31 | #030 |
| ~~39~~ | FEBEP re-extracted 27 fields (133K rows, E2E chain analysis) | 2026-03-31 | #030 |
| ~~40~~ | GL + Cost Element P01→D01 sync (880 records, 6 tables, gap=0) | 2026-04-03 | #034 |
| ~~41~~ | `sap_master_data_sync` skill created (#38) | 2026-04-03 | #034 |
| ~~42~~ | CO tables extracted: COOI 773K + COEP 2.55M + RPSCO 127K = 3.45M rows | 2026-04-04 | #035 |

---

## SESSION CLOSE PROTOCOL — Mandatory Reconciliation

> **This is the #1 rule that prevents pending items from getting lost.**

At the END of every session, the agent MUST:

1. **List all new pending items** discovered during the session
2. **Add each one** to the appropriate section above (B/H/G) with session # in "First raised"
3. **Strike through** any items completed during the session
4. **Verify count**: `pending_before + new_pending - completed = pending_after`
5. **Update SESSION_LOG.md** with: "PMO reconciled: +N new, -N completed, N total pending"
6. **Update MEMORY.md** pending count (just the number, not the list — list lives HERE)

**If you skip this, items get lost. This happened between sessions #009 and #020 (11 sessions without reconciliation).**

---

## Operating Rules

1. **Every session**: Read this PMO Brain FIRST — it's the single source of truth
2. **Every session**: Pick 1 🔴 Blocking + 1-2 🟡 High Priority tasks
3. **Every session end**: MANDATORY reconciliation (see protocol above)
4. **Brain rule**: After any extraction → run `sap_brain.py --build --html`
5. **Skill rule**: After discovering a new pattern 3x → create a skill for it
6. **P01 rule**: All monitoring data from P01 only. Never use D01 data for decision-making


## s097 — PENDIENTES (recuperar en la próxima sesión)

> Fuente de verdad: `brain_v2/capability_model/execution_backlog.json`. Esto es el índice.
> Estado del modelo: `graph_queries.py profile` · `methods` · `coherence`.

### Bloqueado por el usuario (no por el modelo)
- **BACKUP** — `DURABILITY 0.10`. Golden DB 13,28 GB + `~/.claude`, sin respaldo confirmado.
  Contiene ahora `df14l`, `tadir_obj`, `tfdir_all` y la base de D01. Git no los protege.
- **EXT-HCM-TABLES** — 188.636 ejecuciones, cero tablas. Es dato de personal: falta confirmar
  alcance y restricciones de privacidad.
- **AN-FLOW-B2C2A** — falta la explicación de la relación PROJ2FUND ↔ B2C2A (¿los fondos se
  ejecutan por proyectos? Si sí, los dos flujos se fusionan y el event log se construye distinto).

### Prioridad 1
`AN-PS-DOC` (1,6M ejecuciones, sin documento) · `AN-PBC-DEEP` (68 usuarios, 4/11 celdas) ·
`AN-CLAIM-VERIFY` (desde 24,5%) · `AN-ALGO-GOLDEN` (un fix sin caso no es un fix)

### Prioridad 2
`AN-GM-CAPABILITY` (Grants, antes del cliente #2) · `AN-CRP-CELLS` · `AN-FLOW-POST2BUDGET` ·
`AN-FLOW-PROJ2FUND` · `AN-INTEGRATION-VERIFY` (794.261 ejecuciones movidas, sin verificar) ·
`AN-EVENTLOG-DEFS` · `AN-ALGO-CROSSCHECK` (ascenso vs clasificador: el desacuerdo es un defecto
en uno de los dos — la validación más barata que tenemos, sin usar) · `AN-ALGO-ADAPTIVE-FEED`

### Prioridad 3
`AN-LEGACY-ARCHIVE` (8 extractores superados) · `AN-FAILMODE-VIEW`

### Defectos declarados de algoritmos nuevos (arreglar antes de citar sus cifras)
- **F1** trunca nombres de destino y escanea una muestra → `230 DEAD` lleva error de parseo.
- **F2** por la misma truncación puede partir una flota en dos: las de 17 y 21 endpoints
  comparten prefijo GUID y podrían ser el mismo satélite. **No citar 40 como cifra cerrada.**
- **improve_algorithms** no pondera por PROFUNDIDAD en el DAG, y debería: mejorar una capa baja
  levanta todo lo de arriba.


---

## Capacidad de mineria — pendientes abiertos (sesion 103, 2026-08-25)

El patron que los une: **producimos conocimiento de CLASIFICACION dentro de un analisis y no lo
sacamos de ahi**. Un dato perdido se nota manana; un clasificador perdido no se nota nunca,
porque el siguiente analisis vuelve a derivarlo sin saber que ya lo sabiamos. Regla
`feedback_a_classifier_born_inside_an_analysis_must_be_promoted` (CRITICAL).

### Prioridad 1 — capacidad que existe y no se puede reusar
- **MIN-VARIANT-CORPUS** — extraer VARI/VARID de las **127 variantes DISENADAS** (35 programas;
  el resto de los 29.190 pares son instancias de un solo uso, como los 14.585 de RBDAPP01). De
  sus valores salen las **rutas de fichero** = el mapa de integraciones por job, que hoy no
  existe. Algoritmo A33, `lands_in` PENDIENTE. Empezar por `ZFI_SWIFT_UPLOAD_BCM` (2 variantes,
  2.780 pasos, codigo propio) y `YFI_COUPA_POSTING_FILE`.
- **MIN-ACCOUNT-CLASSES** — extraer `FAGL_011ZC` al Gold DB y materializar
  cuenta -> nodo de balance -> **clase de cuenta**. Hoy se deriva EN VIVO dentro de
  `fsv_coverage_check.py` y no se guarda, asi que la revaluacion FX, el analisis de bancos y el
  alta de maestros lo re-derivan cada uno por su cuenta. Algoritmo A34. Cuidado medido: la
  version se elige por la VARIANTE de RFBILA00 (`BILAVERS`), nunca por T011 — usar la
  equivocada invento un hueco de 144 M EUR.
- **MIN-TRANSPORT** — 20.915 transportes en E070, **15 scripts** que los analizan y **UN** solo
  algoritmo registrado (`A17_change_governance`). Registrar al menos
  `brain_v2/ingestors/transport_ingestor.py` y
  `Zagentexecution/quality_checks/config_transport_prerelease_check.py`.

### Prioridad 2 — cobertura del censo
- **MIN-REGISTER-23** — 23 mineros vivos sin registrar, borradores ya emitidos en
  `brain_v2/methods/mining_candidates.json` (11 CANAL_Y_ACTOR, 6 FLUJO_DE_CONTROL, 2 REALIDAD,
  1 DERIVA). El `failure_mode` de cada uno hay que **averiguarlo corriendolo**: inventarlo es
  peor que dejarlo vacio.
- **MIN-OTROS-REPOS** — el censo solo mira este repo. Los mineros de `FINCLOSSING`,
  `unesco-sap-brain` y `unescore20-PPM-brain` no los ve nadie desde aqui.
- **MIN-TRANSCRIPT** — parte del metodo se genera en la CONVERSACION y no llega a tocar disco.
  A35 mira ficheros; deberia mirar tambien el transcript de la sesion.

### Prioridad 3 — la capa de juicio
- **MIN-ARBITRO** — los choques entre mineros se SACAN a la luz (`mining_bus.py choques`) y no
  los arbitra nadie. Los de hoy se resuelven solos por autoridad de evidencia; el dia que
  choquen **dos medidas del mismo peso** hace falta juicio, y eso es un agente, no una regla.
- **MIN-PRECONDICIONES** — los cinco modos de fallo de la familia B dicen lo mismo — *si la
  precondicion esta mal, la salida es verosimil y falsa* — y **ninguno la comprueba**: solo la
  documentan. Convertir cada `failure_mode` en una precondicion que se NIEGUE a publicar, como
  hizo `fsv_coverage_check` al negarse a llamar hueco a lo que no se ejecuta.

### Stores que siguen fuera del grafo (3)
`drift_signals.json` · `p2p_ocel2_summary.json` · `reality_filter.json` — son agregados sin
nombre de objeto: o se les da una clave por objeto, o se declaran agregados **con motivo** en
`graph_landing_check.FUERA`. Dejarlo en silencio es lo que dejo 19 stores fuera durante meses.


### Aparcado por JP durante la reparacion (sesion 103) — decidir despues
- **MIN-COMO-SKILL** — el INDICE DE CAPACIDADES (`process_mining/ask.py`: que se puede preguntar
  y que minero lo contesta, con la llamada exacta, lo que NO puede y su trampa) es *parte
  fundamental del brain*. Queda por decidir **si debe ser un SKILL** en vez de un script, para
  que se cargue solo cuando alguien necesita minar algo.
- **MIN-LLAMABLE** — cada minero es una CAPACIDAD invocable desde otro descubrimiento o desde el
  analisis de una incidencia: si un minero sabe leer variantes, eso vale para el alcance de una
  revaluacion, para el formato DMEE de una corrida y para saber si una cuenta se procesa alguna
  vez. `ask.py` da el enrutado y el `como_se_importa`; falta que los AGENTES lo usen por defecto
  en vez de re-derivar.


### ⛔ Capacidad de mineria — los TRES que quedan abiertos (sesion 103, 2026-08-25)

Marcados por JP explicitamente para que el verde de las puertas no se lea como la capacidad
entera. Las puertas estan todas en verde y **eso no significa que esto este hecho**.

- **MIN-OBEDECER** — *que la memoria se LEA no es que se OBEDEZCA.* Los 32 mineros importan
  `metodo` e imprimen las memorias que les aplican, y la puerta
  (`method_memory_applied_check.py`) los da por buenos. Pero **solo A31 condiciona su
  comportamiento** con `mem.prohibe(...)`; los otros 31 la leen y la muestran. Es una medida de
  FORMA disfrazada de medida de efecto — el defecto que esta sesion cazo cuatro veces, cometido
  por la puerta que existe para cazarlo. Queda escrito en el `failure_mode` de A37.
  **Como se cierra:** que la `implication` sea EJECUTABLE, no solo texto — una comprobacion
  asociada que BLOQUEE publicar una cifra que la contradice, en vez de un aviso que se lee y se
  ignora.

- **MIN-REGISTRAR-45** — 45 mineros vivos detectados por el censo y sin registrar, con
  borrador emitido en `brain_v2/methods/mining_candidates.json`. El `failure_mode` de cada uno
  **hay que averiguarlo CORRIENDOLO**: inventarlo es peor que dejarlo vacio porque parece
  pensado. Lo completa el agente `miner-onboarding`, que exige las cuatro capas (leer,
  INTERPRETAR, agrupar, donde se uso) — registrar solo la parte contable mata el criterio, que
  es lo unico que no se puede volver a derivar.

- **MIN-MIRAR-LOS-NUEVOS** — ~418 nombres que el delta destapo y **nadie ha mirado**. No
  son ruido: son lo que el grafo NO tenia. Los mayores bloques son 80 programas estandar y ~77
  propios que el modelo no sabe explicar (`log_reality.delta_vs_model`, unexplained=1.298 con
  6,5% de cobertura), 38 jobs de frontera, 33 destinos RFC no declarados y 22 programas con
  variante. **Cada uno es un candidato a claim o un objeto que falta.**
  Se leen en `process_mining/discovery_delta.json`.

**Y el aviso que los une:** las tres puertas verdes miden que el conocimiento se puede
ENCONTRAR, no que se haya MIRADO. Un delta con 420 hallazgos y cero lecturas humanas es
exactamente el estado que esta sesion vino a arreglar, un nivel mas arriba.


---

## Mineria agentica — REVISION CONSOLIDADA (sesion 103, 2026-08-25)

Los comentarios de JP durante la sesion, lo que quedo abierto, y lo que encontraron las TRES
auditorias de fidelidad. Aqui y no en el chat, porque el chat se pierde con la ventana.

### A. Comentarios de JP — estado real

| lo que pidio | estado |
|---|---|
| Foto de base antes de la cadena | HECHO |
| ¿BI/RFC desde logs es mining? | SI — A31 |
| Buscar que otros procesos minan sin registrar | HECHO — A32, **45** candidatos |
| Mecanizar el alta al grupo de mining | HECHO — `--proponer` + agente `miner-onboarding` |
| Leer variantes: valores, paths, grupos por similitud | HECHO — A33 |
| Que detecte que YO genere un minero | HECHO — A35 |
| ¿Los mineros colaboran dejando comentarios? | PARCIAL — ver seccion C |
| Verdadera colaboracion agentica / best practices | HECHO — blackboard + contract net + reflexion + arbitro |
| Foro donde todos preguntan | HECHO — y estrenado con 2 preguntas |
| Que aprendan de la forma de explorar | HECHO a medias — leen, **solo A31 obedece** |
| Cada minero invocable desde otro discovery | HECHO — `ask.py` (A36) |
| **El circulo que CREA y RESUELVE claims** | **HECHO tarde** — `claim_resolution.py`; se me habia pasado el camino de vuelta |
| **La ORQUESTACION como conocimiento replicable** | **ABIERTO** — el orden vive en el codigo, no como conocimiento consultable |
| Cuentas -> estructura de balance -> clases | ABIERTO — A34 registrado, **store sin materializar** |
| Transport analyzer | ABIERTO — 15 scripts, **1 registrado** |
| Buscar en otros repos y conversaciones | ABIERTO — **solo este repo** |
| ¿El indice de capacidades debe ser un SKILL? | ABIERTO — sin decidir |
| Que los agentes revisen lo suyo y minen EN CONJUNTO | ABIERTO — **no se ha hecho la corrida conjunta** |

### B. Lo que encontraron las auditorias

**1a vuelta — 65 perdidas, 27 graves, PIERDE_MUCHO en los 4.** Al mecanizar un metodo se
conserva la parte contable y se tira la interpretativa. Reparadas.

**2a vuelta — la reparacion introdujo ~10 defectos nuevos por minero.** El peor: el bloque que
existe para no repetir el error de dominio lo repitio EN ESPEJO (mezclar poblaciones en vez de
tablas). Y se escribio una medida FALSA en la memoria de metodo -- un "100%" que era 39%.
Reparadas.

**3a vuelta — 12 defectos nuevos en A31 y 14 en A33, y con un patron que ya no es casualidad:**

> **LAS REPARACIONES APLICAN EL ARREGLO DONDE SE VE, NO DONDE TIENE CONSECUENCIA.**

- el corte de 4.000 SIGUE ahi y ahora la salida publica `_sin_muestreo: true` — antes el
  muestreo era invisible, ahora esta **desmentido por un campo**
- la memoria se corrigio a mano a 1.728/32,4% y el instrumento mide 1.445/38,8%: **ninguna
  corrida futura reproduce esa memoria**
- `SAPMSSY1 es un report` se arreglo en el JSON y en el print, **no en la cadena que va al bus**
  — que es lo que leen los demas mineros
- `if otros: pass` se listo como corregido en un commit **y no lo estaba**
- `prohibe()` pone un global que **nadie lee**: aparece una sola vez en todo el repo
- la mezcla de poblaciones no se elimino, **se renombro**: FMRESERV 966.671 ahora sale bajo
  la etiqueta TRAVEL
- **hallazgo FALSO celebrado**: el "herramienta sin nombrar que mueve mucho" de SIN_GRAMATICA es
  **WF-BATCH**, el usuario batch del motor de workflow, 3 sesiones; sus 198.850 cambios son su
  trabajo normal. Y su tipo estaba en el mismo fichero.
- la segmentacion por herramienta **solapa y no lo dice**: 407+40+1=448 para 446 distintos; dos
  personas estan en TRAVEL y en HCM_ALLOS a la vez y aportan casi todo lo no-HR
- `--desde` ya no alimenta ninguna consulta: **solo cambia la etiqueta publicada**
- el `61%` hardcodeado se republica sobre otra poblacion (real: 20,4% para los 446, 71,2% para
  los 40 de ALLOS)
- `_es_un_fosil` (A33) sale `false` sin evidencia: 27 de 115 tienen `ultima: null` y los 27
  dicen que no son fosiles

### C. ¿Colaboran los mineros? — MEDIDO, no afirmado

| senal | estado |
|---|---|
| PUBLICAR | 235 hallazgos de 9 mineros |
| CONSULTAR | 1 de 9 lo hacia, y **tiraba el resultado**. Corregido en A31 |
| PREGUNTAR | **0 preguntas** hasta hoy. Estrenado: 2, las dos diciendo *por que no puedo yo* |
| CHOCAR | 5 sujetos con dos mineros distintos |
| ARBITRAR | 5 resueltos por regla · **0 por el arbitro**, que nunca se ha invocado |

**Era un tablon con una discusion, no una colaboracion.** Falta que los 7 mineros restantes
consulten antes de concluir y que alguien conteste las preguntas abiertas.

### D. Los tres de siempre, que siguen

- **MIN-OBEDECER** — leer no es obedecer. La puerta mide la forma.
- **MIN-REGISTRAR-45** — con borrador; el `failure_mode` hay que averiguarlo CORRIENDOLO.
- **MIN-MIRAR-LOS-NUEVOS** — 418 nombres que el delta destapo y nadie ha mirado.

---

## Canal ADS (Adobe Document Services) — ARBITRADO 2026-08-26 (s105), lo que queda ABIERTO

Origen: INC-000016471 (vivo). Arbitraje publicado en `process_mining/mining_findings.json`
(sujetos `ADS`, `DESTINO_SALIENTE_TIPO_G`, `ADSUSER`, `F1_INTERFACE_BOUNDARY`) y promovido a los
claims **614 / 615 / 616**; claims **372 y 585** quedan `partially_superseded` con su texto intacto.

**Lo establecido, para no re-discutirlo:** `DEAD` sobre un destino RFC de tipo G o H **no es una
medida** — `rsau_audit_history` registra llamadas RFC y no ve una llamada HTTP saliente (40 de 40
destinos G/H con `observed_calls=0`; las 5 rutas al SLD DEAD mientras el job `RSLDAGDS` que las usa
terminaba OK 126 veces en la misma ventana). Y `NO_MEDIBLE` son **dos** preguntas: el TRAFICO no se
mide desde aqui, la DISPONIBILIDAD si.

| id | pendiente | quien | por que no se cerro |
|---|---|---|---|
| **ADS-1 POBLACION** | Censar que objetos renderizan por ADS. Dos vias: (a) extraer `TNAPR` / `NAST` / `FPCONTEXT` / `FPLAYOUT` / `FPINTERFACE` — **ninguna esta en el Gold DB** (384 tablas); (b) censo por EJECUCION: contar los grupos de funciones GENERADOS `/1BCDWB/*` en el log, que es a lo que compila un formulario Adobe. | este proyecto (A19 + A33; preguntas abiertas en el bus, sujeto `ADS`) | el corpus de codigo extraido da **1** objeto (`RFFORI00`) y es un SUELO, no un censo. Sin poblacion no hay radio de alcance: no sabemos a cuanta gente afecta que ADS caiga |
| **ADS-2 DISPONIBILIDAD** | Dar dueno y monitor al canal: `medibilidad_disponibilidad` en `brain_v2/build_interface_inventory.py` para los 239 destinos salientes + un test de conexion periodico | este proyecto + Basis (el test se ejecuta en SAP) | hoy los 239 dicen `evidence_it_runs: 'see interface_boundary.json for LIVE/DEAD'`, que para los 40 de tipo G/H remite a una fuente que no los ve |
| **ADS-3 F1 SIN FICHA** | Dar de alta `process_mining/interface_boundary.py` (F1) en `process_mining/ask.py` con su `lo_que_NO_puede` ("no ve trafico que no sea una llamada RFC: los destinos G/H le son invisibles") y hacer que emita `NO_OBSERVABLE` en vez de `DEAD` para esos tipos | `miner-onboarding` | **es la causa raiz del choque, no un empate**: un minero que emite veredictos sobre 238 destinos y no esta en el registro no puede recibir preguntas ni sembrar su limite en el foro. `ask.py` tiene 11 algoritmos; F1 no es ninguno |
| **ADS-4 GATE** | Check recurrente que falle si un clasificador publica un veredicto de AUSENCIA con tasa 0% o 100% sobre una clase entera de la poblacion (mecaniza la regla nueva `feedback_a_verdict_of_absence_must_name_the_instrument_that_could_have_seen_it`) | este proyecto | es la 2a vez que la misma forma de defecto sale en los stores de interfaces (`DEAD` 40/40 y `NO_MEDIBLE` 239/239): por la regla #172, al 2o avistamiento toca GATE, no correccion |
| **ADS-5 FRONTERA (escalado, NO nuestro)** | Estado de `ADSUSER` en el **UME del AS Java** de `hq-sap-sbp` (bloqueo / caducidad) | Basis + dueno del AS Java | **estructuralmente invisible para nosotros**, no es un hueco de datos: `ADSUSER` no existe en `USR02` de P01, luego ninguna tabla ABAP nuestra puede contenerlo jamas. Lo que SI esta de nuestro lado y separa las 4 causas en un clic: `SM59` -> destino `ADS` -> Connection Test (401 = ADSUSER · timeout/rechazo = host o red · 200 = ADS vivo) y `SFP` -> Test ADS Connection (`FP_PDF_TEST_00`). Los dos de SOLO LECTURA |
| **ADS-6 DEUDA** | `s=N` en el destino `ADS`: basic auth de un usuario de servicio viajando sobre **HTTP plano** en cada render de PDF. Y `T=N`: traza apagada | Basis | destapado por el incidente, no es su causa |

**Lo que el arbitraje SI cerro y no hace falta volver a medir (claim 617):** el host `hq-sap-sbp`
llama a P01 como un metronomo desde su pila **ABAP** de Solution Manager (`SMTMSBP` ->
`SM_P01CLNT350_*`), ~2.100-2.300 eventos al dia sin huecos. **El 2026-08-25, el dia que el usuario no
podia sacar su PDF, marco 2.138 eventos de 00:00:17 a 23:58:22 — indistinguible de un dia normal.**

- **El diagnostico baja de CUATRO causas a DOS.** Caen la #3 (red / DNS / host movido) y la #4 en su
  version de saturacion de la maquina: una caja asi de tocada habria mellado el metronomo ABAP y no
  lo mello. Quedan la **#1** (la aplicacion `AdobeDocumentServices` parada o colgada) y la **#2**
  (`ADSUSER` en el UME), las dos dentro de la pila **Java** (instancia 03, puerto 50300).
- **Las dos las separa el MISMO clic, y es de solo lectura:** `SM59` -> destino `ADS` ->
  *Connection Test*. **401 = #2** · **rechazo o timeout contra 50300 = #1**. Es decir: **no hace
  falta pedir acceso al AS Java para avanzar**; hace falta un test que Basis ya puede dar, y solo si
  sale 401 se entra en NWA. Eso es lo que hay que decirle hoy a quien lleve el ticket.
- **Y la leccion de instrumento, que dura mas que el incidente:** ese latido es un sensor de la
  **MAQUINA**, no del canal. Solo produce senal **negativa** (maquina caida => no hay PDF) y nunca
  positiva. Un monitor de ADS montado sobre el latido de la instancia ABAP vecina **habria dado
  VERDE durante toda esta incidencia**. El monitor de ADS-2 tiene que atacar el puerto 50300.

**Dominio `Output`:** sigue STRANDED y es el caso de estudio. `capability_model` lo tiene con
`D_DATA=PARTIAL`, `F_INTERFACE_FILE=PARTIAL` y **las otras nueve dimensiones en NONE**. Antes de hoy
tenia 0 claims, 0 reglas, 0 incidentes y 0 anotaciones sobre Adobe. Asi se ve un dominio stranded
**el dia que se rompe**: nadie sabe que cuelga de el, nadie mira si responde, y el ticket llega
clasificado en el equipo equivocado.
