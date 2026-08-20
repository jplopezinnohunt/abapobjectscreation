# Deep-Research Archive (persisted s079)

Durable, git-tracked archive of the deep-research runs. **Purpose: never re-read or re-run what was
already analyzed; enrich incrementally instead.** (CP-002 preserve.)

## Files
- `<id>_<slug>.json` — full result of each CLOSED research (question, verified findings, refuted claims,
  caveats, open questions, all sources, stats). The 4 closed runs:
  - `w3t7ufrbg_process_mining_objectcentric.json` — OCEL 2.0, OPID conformance, object-centric algorithms
  - `w3os0wwlx_code_mining_static.json` — ATC/SCI, CCLM, SCMON/UPL, abaplint, Custom Code Migration
  - `wgrqpmt9f_competitive_landscape.json` — Celonis/UiPath/Signavio/PaPM connectors, pm4py, table maps
  - `wh5gw9exu_s4hana_readiness_bpcvi.json` — BP/CVI migration, SI-Check, Maintenance Planner, Readiness Check
- `sources_index.json` — **every web URL already consulted** (91 unique), with which research/angle/quality/
  claimCount. **Dedupe new research against this** — do not re-fetch a url here unless ENRICHING it.
- `findings_registry.json` — **every verified finding (37) + refuted claim (26)** across all 4 researches,
  so no tool/method/model is lost and refuted claims are never re-asserted.
- `_run_log.json` — run provenance. 2 runs FAILED (degraded by concurrency) and were superseded by solo
  reruns — do NOT re-run those queries; use the CLOSED rerun.

## How to use (before launching ANY new deep-research)
1. Check `sources_index.json` — is the url/source already analyzed? If yes, READ the archived finding,
   don't re-fetch.
2. Check `findings_registry.json` — is the claim already verified or refuted? Don't re-litigate.
3. Scope the new research to ENRICH the open questions (in each `<id>.json`.openQuestions) — the named gaps:
   auth/SoD method, Finance pillars beyond Asset Accounting, greenfield Migration Cockpit, unmapped
   competitors (Mehrwerk/MS/IBM/ARIS/QPR), exact BP field mapping.
4. Append new runs here; never overwrite.

## Lesson encoded
Run deep-researches **SERIALLY** (one at a time). Concurrent heavy runs degrade the Verify stage
(StructuredOutput failures → 0-0 votes → false "all refuted"). See `_run_log.json`.

> **Reglas que aplican en este punto** — citadas aquí para que existan donde se usan, no sólo en `feedback_rules.json`:
> - `feedback_research_quality_gate_before_conclusions` — el momento es ir a USAR el resultado de una investigación: ninguna produce conclusiones hasta estar CLOSED con sus 8 garantías.
