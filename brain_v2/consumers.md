# Consumers of this brain

*Reverse pointer — every project that depends on `abapobjectscreation/brain_v2/` must be listed here. Agents working in THIS project must check downstream impact before structural refactors.*

**Last updated**: 2026-05-23

---

## Tier 2 Application Projects

### FINCLOSSING (Financial Closing & Consolidation)
- **Path**: `c:\Users\jp_lopez\projects\FINCLOSSING\`
- **Created**: 2026-05-23 (Session #00)
- **Tier**: 2 — Application Project (greenfield ABAP module)
- **Consumes**:
  - Brain layers: `core_principles`, `objects`, `claims`, `incidents`, `rules`, `domains_layer`, `known_unknowns`, `data_quality`
  - Source files: `agent_rules/feedback_rules.json`, `core_principles/core_principles.json`, `annotations/annotations.json`, `claims/claims.json`, `incidents/incidents.json`
  - Gold DB (read-only): `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`
  - Knowledge docs: `knowledge/domains/{FI,PSM,Treasury,HCM}/`
  - Companion: `companions/carry_forward_2026.html`
  - Skills: `sap_class_deployment`, `sap_adt_api`, `sap_data_extraction`, `sap_segw`, `sap_webgui`, `fi_domain_agent`, `psm_domain_agent`, `sap_transport_intelligence`, `sap_transport_companion`, `sap_master_data_sync`
- **Parent domains it crosses**: FI, PSM, Treasury, HCM, CO
- **Canonical dependency manifest** (single source of truth): `FINCLOSSING/brain_v2/refs_external.json`
- **Governing rule**: `feedback_cross_project_brain_link`

---

## Refactor impact check (before structural changes)

If you are about to:
- Rename / restructure any of the consumed source files above
- Move a domain definition in `brain_state.json#/domains_layer`
- Rename a skill listed above
- Restructure `knowledge/domains/{FI,PSM,Treasury,HCM,CO}/`
- Move incidents out of `brain_v2/incidents/incidents.json`

→ Open each consumer's `refs_external.json`, find the affected pointer, propose an update in the same change, and notify via `ecosystem-coordinator/ecosystem/priority-actions.md`.

Silent breakage of a consumer = CP-001 violation (knowledge lost / traceability broken).
