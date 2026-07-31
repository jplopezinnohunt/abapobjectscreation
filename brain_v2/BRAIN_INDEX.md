# BRAIN INDEX (L1 lean bootstrap — read THIS first, drill the rest)

> Tiered loading (s079). This ~4KB index replaces reading the full ~400K-token brain_state.json at
> bootstrap. Load this, then DRILL on demand via `python brain_v2/graph_queries.py <cmd>`. Read the full
> brain_state.json ONLY when you need depth this index doesn't give.

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

## ⛔ THE OPERATING MODEL EXISTS — do not re-invent
`brain_v2/capability_model/capability_model.json` = **Layer 15** of brain_state. Domain × 11
capabilities; AS-DESIGNED (standard SAP) + AS-RUN (ours); G = delta = the product. Model maturity:
**32.1%**. Do NOT propose a new framework or redesign the schema — EXTEND it.

## Brain at a glance (1212 objects · 171 rules · 359 claims · 10 incidents · 8 closed researches)
16 layers (L0–L15): core_principles · objects · indexes · rules · claims · known_unknowns · falsification ·
superseded · user_questions · data_quality · incidents · blind_spots(0) · interactions · domains_layer(3-axis) ·
**capability_model(L15)**.

## Capability model — 11 dimensions, systemic empty columns: R_S4_READINESS
- **S_STANDARD_REF** (GAP) — do we have the STANDARD SAP as-designed baseline for this domain (precondition f
- **A_PROCESS** (VERIFIED) — how does it actually run (discovered from data) — AS-RUN?
- **B_CODE** (VERIFIED) — which programs/classes/exits/BDC implement it?
- **C_CONFIG** (OWN) — which customizing parameterizes it?
- **D_DATA** (VERIFIED) — which tables + real keys hold it?
- **E_AUTH** (VERIFIED) — who can/does execute it (roles, users, SoD)?
- **F_INTERFACE_FILE** (OWN) — how does it cross the boundary (RFC/IDoc/file)?
- **G_CONFORMANCE** (VERIFIED) — does it deviate from / extend STANDARD SAP?
- **H_IMPROVE** (OWN) — where is the opportunity; what-if before building?
- **R_S4_READINESS** (VERIFIED) — how ready is this domain's custom code/config/process for the S/4HANA migration?
- **U_USAGE** (VERIFIED) — WHAT objects actually execute, WHO runs them, by which CHANNEL (dialog / batch /

## Where we are (execution sequence s079)
wwrqcozf1 CLOSED. A,B,C DONE. B2 scheduling = SessionStart daily curation (native hook, no schtasks). D SKIPPED by user (s079) - stays deferred. E maturity current. F commit = pending user OK (focused, not blanket - git status has ~100 unrelated changes).
Pending after gate: A · B · C · D · E · F

## DRILL — load on demand (don't read the whole brain)
- `python brain_v2/graph_queries.py capability_gaps` — the ranked plan (generated, not written)
- `python brain_v2/graph_queries.py capability <domain>` — a domain's capability coverage
- `python brain_v2/graph_queries.py domain <name>` — domain registry entry
- `python brain_v2/graph_queries.py incident <id>` — incident trace
- `python brain_v2/graph_queries.py what_reads <table>` / `what_depends_on <obj>` — code dependency
- `python brain_v2/graph_queries.py stats` — freshness check
- Research base: `brain_v2/research/` — dedupe new research vs `sources_index.json` (175 urls); never re-assert `findings_registry.json` refuted.
- Full model: `brain_v2/capability_model/` (capability_model · s4_readiness_model · execution_backlog · applied_models · maturity).

## Rules to load first (behavioral DNA — 171 total)
Read `brain_v2/agent_rules/feedback_rules.json` for all. CRITICAL ones added s079: research_quality_gate (#148),
capability_model_is_the_operating_model (#149), archive_and_dedupe_deep_research (#150),
ask_strategy_before_scoping (#151), model_exists_do_not_reinvent (#152).
