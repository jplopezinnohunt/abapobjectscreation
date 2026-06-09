# BRAIN INDEX (L1 lean bootstrap — read THIS first, drill the rest)

> Tiered loading (s079). This ~4KB index replaces reading the full ~400K-token brain_state.json at
> bootstrap. Load this, then DRILL on demand via `python brain_v2/graph_queries.py <cmd>`. Read the full
> brain_state.json ONLY when you need depth this index doesn't give.

## ⛔ THE OPERATING MODEL EXISTS — do not re-invent
`brain_v2/capability_model/capability_model.json` = **Layer 15** of brain_state. Domain × 10
capabilities; AS-DESIGNED (standard SAP) + AS-RUN (ours); G = delta = the product. Model maturity:
**23.3%**. Do NOT propose a new framework or redesign the schema — EXTEND it.

## Brain at a glance (742 objects · 155 rules · 209 claims · 10 incidents · 8 closed researches)
16 layers (L0–L15): core_principles · objects · indexes · rules · claims · known_unknowns · falsification ·
superseded · user_questions · data_quality · incidents · blind_spots(0) · interactions · domains_layer(3-axis) ·
**capability_model(L15)**.

## Capability model — 10 dimensions, systemic empty columns: E_AUTH, R_S4_READINESS
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

## Rules to load first (behavioral DNA — 155 total)
Read `brain_v2/agent_rules/feedback_rules.json` for all. CRITICAL ones added s079: research_quality_gate (#148),
capability_model_is_the_operating_model (#149), archive_and_dedupe_deep_research (#150),
ask_strategy_before_scoping (#151), model_exists_do_not_reinvent (#152).
