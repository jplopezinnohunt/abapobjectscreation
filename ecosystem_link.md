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
| Add 4 YTFM biennium tables to the SAP golden (FM domain) — `YTFM_FUND_C5/C5/OUTPUT/OUTPUT_T` | `unesco-sap-brain` | ✅ **DONE (Session #080)** — all 4 landed in golden; verified 2026-06-09 (`ytfm_fund_c5`, `ytfm_c5`, `ytfm_output`, `ytfm_output_t` present in `p01_gold_master_data.db`). chip `task_64603104` dismissed · spec was in `Zagentexecution/sap_data_extraction/pending_from_sap_brain/REQUEST.md` |

## 3b. Data-ready handoffs (produced FOR a consumer to continue analysis)
| Handoff | To | Status |
|---|---|---|
| **SAP config-frontier** — 61 FI/FM/GM customizing tables (GMDERIVE/`GMDT`, doc-splitting `T8G*`/`FAGL_SPLIT`, new-GL `T881/T882`, FMDERIVE `TABADR*`/`FMDERIVE*`, AVC `FMUP*`/`BUAVCTOLASS`/`FMAVCLDGR*`) → golden DB (+`_config_frontier_manifest`) | `unesco-sap-brain` | ✅ **READY (2026-06-19)** — closes the "still needs extraction" rows in their `knowledge/35_recreated_conclusions.md` (HYP-003/008/012/018, CLM-012/024/036, OI-FI-01, F3). Response note: `Zagentexecution/sap_data_extraction/pending_from_sap_brain/DONE_config_frontier.md` · evidence: `knowledge/config_frontier_extraction_2026-06-19.md` · task chip dropped into their queue. They consume read-only via their `refs_external.json` and recompute the verdicts. |

## 4. Produces-back / promotion
This project IS the promotion target: peers (e.g. `FINCLOSSING`) push stabilized SAP skills, TIER_1 claims, and universal incidents back here via `ecosystem-coordinator/priority-actions.md`.
