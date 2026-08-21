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
- Systems: **P01** (production) · **D01** (development) · **V01** (validation)
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
- **B2R** — 7 domains: CO, Closing_Activities, Cost_Recovery_CRP, FI, PBC, PS, PSM · avg coverage 61%
- **T2R** — 5 domains: Closing_Activities, FI, Payment_BCM, TRM, Treasury · avg coverage 69%
- **P2P** — 5 domains: FI, PM, Payment_BCM, Procurement, Treasury · avg coverage 65%
- **H2R** — 5 domains: HCM, HR-Workflows, PBC, PY-Finance, Travel · avg coverage 56%
- **P2D** — 2 domains: BusinessPartner, Master_Data_Governance · avg coverage 48%
- **A2R** — 1 domains: FI_AA · none measured
- **O2C** — 1 domains: SD · none measured
- **Cross-cutting by construction** (serve NO single process because they touch all): Integration, Support, Transport_Intelligence
- **⚠️ Stranded** (no process AND not technical — neither in a flow nor across one): Output, RE-FX

## 🔌 INTEGRATION — the richest surface, and the one that explains the operating model
**SAP here is a system-of-record fed by satellites, not a dialog system.** Any answer about how
the system is used that assumes people in screens is wrong before it starts.
- **300 interface records** (derived, queryable — `brain_v2/interface_inventory.json`):
  RFC_DESTINATION 239 · FILE 20 · BATCH_INPUT 17 · IDOC 9 · WEB_SERVICE 8 · WEBSERVICE 4 · DBCON 2 · HTTP_SERVICE 1
- **The boundary is mostly dead:** 238 RFC destinations configured,
  **10 live**, **228 dead**,
  **176 undeclared** — traffic crossing with no configuration entry.
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
- Claims touching authorization: 19 · drill: `graph_queries.py capability E_AUTH`
- **Posture store** `brain_v2/security_posture.json` — 2 ready · 3 missing input · 2 findings already stored as RECORDS.
- **Cannot see yet:** identity_inventory, role_content, auth_defaults — MISSING_INPUT means WE CANNOT SEE, never 'there is nothing'.

## 📈 MATURITY OF THE METHOD — 65.4%, measured from artifacts
Not a self-assessment: each dimension is derived from what is on disk.
- **Weakest:** **DURABILITY** 0.10 · **VERIFY** 0.40 · **ANALYZE** 0.48
- **Strongest:** MODEL_FIDELITY 0.98 · CONSOLIDATE 0.95 · ESCALATE 0.93
- **Read this together with the capability grid.** Two independent instruments agree: strong at
  COLLECTING, weak at VERIFYING. We know precisely what the system DOES and little about what it
  SHOULD do — which is the same finding as the near-empty `S_STANDARD_REF` column.

## OPEN WORK - incidents awaiting action (11 live, deadline first)
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
- `INC-180995` - ROOT_CAUSE_CONFIRMED - Ticket 180995 — two sibling transports from one ticket reached P01 101 days apart (MZ payroll cu
  - drill: `python brain_v2/graph_queries.py incident INC-180995`

_3 more open, drill by id:_ `INC-BUDGETRATE-EQG` (ROOT_CAUSE_CONFIRMED)  `INC-FXREVAL-OB09` (ROOT_CAUSE_CONFIRMED)  `INC-MMF-BNPPB-2026` (ANALYZED_EXECUTION_PENDING)


## AGENTES - lo que sabemos HACER (7 disponibles)
- **`bank-process-discovery`** - model: sonnet ---
- **`brain-steward`** - Promotes knowledge that surfaced in a working conversation into the CENTRAL brain before it is lost. This is the missing "transcript-pattern-extr
- **`fx-revaluation-scope`** - Audita QUE CUENTAS ENTRAN Y CUALES SE QUEDAN FUERA de la revaluacion FX (F.05 / SAPF100), entrando por la NATURALEZA de la cuenta — banco, deposi
- **`incident-analyst`** - Processes UNESCO SAP support incidents end-to-end. Use this agent whenever the user passes an incident — whether as an .eml file, pasted email te
- **`master-data-sync`** - Alinea MASTER DATA de P01 (fuente, read-only) hacia D01 / V01: cuentas GL, centros de coste, fondos, centros gestores, proyectos/WBS. Mide primer
- **`process-guardian`** - model: sonnet ---
- **`variant-intelligence`** - Lee el CONTENIDO REAL de las variantes de ejecucion de programas ABAP y lo convierte en conocimiento de proceso. El programa dice lo que se PUEDE

**Modelo de ejecutores de alineamiento P01 -> D01/V01**: `knowledge/alignment_executors_model.md` - la escalera de canales (API estandar / BC-Set / escritura directa bajo excepcion), los medidores, los actuadores por objeto y el metodo comun. Excepciones autorizadas, lista cerrada: `.agents/skills/sap_master_data_sync/SKILL.md`.

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

## WHAT WE KNOW DEEPLY - 46 companions; the 10 densest, and what each covers
> Do NOT re-derive these. Search any term across every store AND the companions: `python brain_v2/graph_queries.py search <term>`.

- `bank_statement_ebs_companion.html` - Bank Statement & Reconciliation - basis, basu, bseg, bsik, business area, cash, compliance, connectivity, derivation
- `payment_bcm_companion.html` - Payment & BCM Intelligence - avc, basu, biennium, bseg, bsik, cash, compliance, donor, dual control
- `transport_companion_D01K9B0CBF_v2.html` - Company Code STEM Creation - avc, basis, bseg, business area, carry forward, cash, derivation, fbzp, fmderive
- `cts_dashboard.html` - CTS Dashboard (2017-2026) - avc, basis, basu, biennium, bseg, business area, cash, derivation, epi-use
- `treasury_operations_companion_v1.html` - Treasury Operations v1 - avc, basu, biennium, bsik, business area, cash, compliance, donor, fbzp
- `BCM_StructuredAddressChange.html` - BCM Structured Address Change - basis, bseg, bsik, cash, compliance, derivation, dual control, fbzp, ggb0
- `fi_substitutions_custom_code_companion_v1.html` - Substitutions & Custom Code Registry - basu, bseg, bsik, business area, cash, derivation, fmderive, fmifiit, ggb0
- `sap_knowledge_graph.html` - UNESCO SAP Living Knowledge Brain - avc, basis, basu, connectivity, derivation, dual control, fmifiit, hcm, idoc
- `fi_maintenance.html` - Finance Operations Reference - avc, basu, biennium, bsik, business area, donor, fipex, fm-avc, fmifiit
- `inc_egypt_ppc_configuration.html` - Egypt — configure the country for Purpose of Payment - business area, interface, p2p, procure, substitution, taxonomy, upgrade, yrggbs00

## ⛔ THE OPERATING MODEL EXISTS — do not re-invent
`brain_v2/capability_model/capability_model.json` = **Layer 15** of brain_state. Domain × 11
capabilities; AS-DESIGNED (standard SAP) + AS-RUN (ours); G = delta = the product. Model maturity:
**30.3%**. Do NOT propose a new framework or redesign the schema — EXTEND it.

## Brain at a glance (1955 objects · 228 rules · 564 claims · 16 incidents · 9 closed researches)
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

## Rules to load first (behavioral DNA — 228 total)
Read `brain_v2/agent_rules/feedback_rules.json` for all. CRITICAL ones added s079: research_quality_gate (#148),
capability_model_is_the_operating_model (#149), archive_and_dedupe_deep_research (#150),
ask_strategy_before_scoping (#151), model_exists_do_not_reinvent (#152).
