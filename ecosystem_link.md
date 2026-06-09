# Ecosystem Link — abapobjectscreation (SAP Intelligence) ↔ peer projects

*Canonical map of what this project OWNS/PRODUCES and (minimally) CONSUMES. This is the SAP **source of truth** for the ecosystem — most edges point INTO this project.*
*Standard: `ecosystem-coordinator/.knowledge/way-of-working/ecosystem-link-manifest.md` · Registry: `ecosystem/data-capability-registry.md` · Rule: ADR-007 / BROADCAST-005.*

**Last reviewed:** 2026-06-09 · **Active ecosystem: 4 projects** — `abapobjectscreation`, `unesco-sap-brain`, `FINCLOSSING`, `unescore20-PPM-brain`.

---

## 1. What abapobjectscreation OWNS (the SAP source of truth)

| Asset | Path (read-only for consumers) | Consumers |
|---|---|---|
| **SAP golden DB** | `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db` (6.4 GB, 205 tables, P01 PROD) | `unesco-sap-brain`, `FINCLOSSING`, `unescore20-PPM-brain` (monitoring scope) |
| **SAP Intelligence brain** | `brain_v2/brain_state.json` (objects/claims/incidents/rules/domains; `brain_v2_index.db` 86 MB) | `FINCLOSSING` (and `unesco-sap-brain` for cross-validation), `unescore20-PPM-brain` (monitor — brain metrics) |
| **Domain knowledge** (FI / PSM / Treasury / HCM) | `knowledge/domains/{FI,PSM,Treasury,HCM}/` | `FINCLOSSING`, `unescore20-PPM-brain` (monitor scope) |
| **28 skills, 7 layers** (RFC extraction, ADT REST, ABAP class/SEGW deploy, transport intelligence, domain agents) | `.agents/skills/` | `FINCLOSSING` (10 skills), any SAP-touching project |
| **Extracted code** | `extracted_code/` | `FINCLOSSING` |

**Read-only contract for consumers:** peers never write here. Cross-project reads must resolve through the consumer's own `refs_external.json` (see `FINCLOSSING/brain_v2/refs_external.json`, `unesco-sap-brain/refs_external.json`, `unescore20-PPM-brain/refs_external.json`).

## 2. What abapobjectscreation CONSUMES

- **Ecosystem governance** (`ecosystem-coordinator/.knowledge/way-of-working/*`, `ecosystem/priority-actions.md`) — read-only, like every project.
- **No SAP data dependency on peers** — this project is the root extractor (RFC ← SAP P01).

## 3. Incoming suggestions (from peers, to evaluate)
| Suggestion | From | Status |
|---|---|---|
| Add 4 YTFM biennium tables to the SAP golden (FM domain) — `YTFM_FUND_C5/C5/OUTPUT/OUTPUT_T` | `unesco-sap-brain` | chip `task_64603104` · ref XLSX + spec in `Zagentexecution/sap_data_extraction/pending_from_sap_brain/REQUEST.md` |

## 4. Produces-back / promotion
This project IS the promotion target: peers (e.g. `FINCLOSSING`) push stabilized SAP skills, TIER_1 claims, and universal incidents back here via `ecosystem-coordinator/priority-actions.md`.
