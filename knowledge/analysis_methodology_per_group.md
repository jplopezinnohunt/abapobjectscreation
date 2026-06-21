---
name: Analysis Methodology per Group — best-practice + commercial-grounded + AI-native
description: The per-group analysis methodology (Phase 2 "build the solution on our reality"). For each event-source group: goal, best-practice technique, which commercial product does it + how, the data we hold, and the AI-NATIVE new angle that goes beyond traditional PM tools. Grounded in our verified research base (w3t7ufrbg OCPM, wgrqpmt9f competitive landscape, wwyujjqyk SoD). 2026-06-21.
type: project
---

# Analysis Methodology per Group

> User directive (2026-06-21): each group needs its OWN methodology (they differ); lean on best practices and
> the commercial products that already do it; we already researched the sources; **with AI, much is new.**
> Grounded in the verified research base — not re-derived. Companions: `process_mining_table_analysis.md`,
> `process_mining_maturity.md`, `process_mining_capability_inventory.md`, `sap_event_sources_catalog.md`.

## 0. The unifying substrate (what the research settled)
- **OCEL 2.0 is the foundation** (research w3t7ufrbg, van der Aalst/RWTH PADS): one unchanging object-centric
  dataset → on-demand multi-perspective mining (no re-extraction when the question changes). E2O + O2O relations,
  qualifiers, time-varying attributes. We use SQLite already → adopting the OCEL 2.0 SQLite format is trivial.
- **Conformance is the product** (research w3t7ufrbg): object-centric conformance via **OPID** (object-centric
  Petri nets with identifiers) = the "as-implemented vs as-delivered / custom-over-standard" x-ray.
- **How the commercial products do it** (research wgrqpmt9f): **Celonis** = deployed RFC ABAP module + Continuous
  (CDC delta) Extraction + Process Intelligence Graph (object-centric OCDM); documents BSEG cluster handling.
  **SAP Signavio Process Intelligence** = RFC_READ_TABLE via JCo (Basis 7.40+); **Process Insights** = ST-PI
  on-stack plug-in. **UiPath PM** = RFC (RFCPING/RFC_GET_FUNCTION_INTERFACE). → We already extract via
  RFC_READ_TABLE (Signavio-class); our gap is the ANALYSIS layer, not the connector.

## 1. The methodology template (tailored per group)
Every group runs the same 6 steps, but the content of each differs by group:
1. **OCEL objects + events** — declare the object types and event types for this group.
2. **case/activity/timestamp/resource** mapping (per `sap_event_sources_catalog.md`).
3. **Discover** — model from the log (DFG → Inductive/Heuristic → OCPN).
4. **Conform** — vs a reference process (the differentiator; see §3 AI-native for where the reference comes from).
5. **Enrich** — performance, decision rules, resource/SoD, root-cause.
6. **Act** — anomaly alerts, narrative, recommendation.

## 2. Per-group methodology
| Group (data we hold) | Analysis goal | Best-practice technique | Commercial reference | AI-native NEW |
|---|---|---|---|---|
| **P2P** (EKKO/EKPO/EKBE/ESSR/RBKP) | maverick buying, 3-way-match deviations, rework | OCPN discovery + conformance vs P2P reference | Celonis P2P app (object-centric) | LLM derives the reference P2P from SAP best-practice docs → conformance with no hand-built model |
| **Payment E2E** (REGUH/REGUP/FEBEP/FEBKO) | dual-control, cycle time, exceptions | variant + SoD + performance spectrum | Celonis AP/AR apps | agent narrates each $-exposed deviation in business terms |
| **FI/GL** (BKPF/bseg_union) | posting patterns, manual-JE risk, period-end | transaction mining + anomaly | Signavio Financial close | LLM anomaly + decision mining ("why this manual JE") |
| **PSM/FM budget** (FMIFIIT/FMIOI/FMBH/FMAVC) | commitment→consumption lifecycle, AVC breaches | object-centric (Fund/FundCenter objects) + temporal | (none native — public-sector gap) | **our differentiator**: public-sector budget OCPM, no commercial equivalent |
| **Audit / SoD** (rsau_audit_history + CDHDR + AGR_*) | SoD violations, handover, resource behavior, security | **function→action→permission ruleset** (research wwyujjqyk, GRC GRACFUNC model) over AGR_* + runtime evidence from RSAU/ST01 | SAP GRC Access Control; Celonis Execution Mgmt | **agentic SoD**: LLM proposes the ruleset from role names + reconciles *declared* auth (AGR_*) vs *actual* behavior (RSAU) — catches "has the right but never uses it" and "uses without the clean role" |
| **Master data** (LFA1/KNA1/ADRC/BNKA + CDHDR) | duplicate/governance, change control | object quality + change mining | Celonis MDM app | LLM dedup/semantic match + change-intent classification |
| **Interface** (EDIDC/RFC) | failed IDocs, integration bottlenecks | interface event mining | — | agent triages the 9,242 status-29 PROJECT IDocs (known) with root-cause |
| **Jobs/batch** (TBTCO/TBTCP) | automation map, job INTENT via variant | batch mining + variant decode (skill `sap_variant_analysis`) | — | LLM reads VARI/VARIS contents → "parameterized business action" semantics |

## 3. The AI-native layer (the user's point — "con AI muchas cosas son nuevas")
Traditional PM (Celonis/Signavio) is query + visualization over a fixed model. What AI changes — our edge:
1. **Reference process WITHOUT manual modeling** — an LLM derives the as-designed reference from SAP standard
   docs / OSS notes / our domain docs, so conformance needs no hand-built BPMN. (Kills the costliest step.)
2. **Semantic activity labeling** — tcode/report/OBJECTCLAS → business activity by LLM, not a maintained map.
3. **NL → analysis** — the user asks in words; the brain (networkx GoR + OCEL) answers. Replaces PQL/Celonis-LLM.
4. **Agentic conformance + narrative** — an agent explains *why* a case deviated in business terms, using the
   document + Z-code context (we have both in the brain) — root-cause that commercial tools can't (no code context).
5. **Declared-vs-actual reconciliation** — pair static auth (AGR_*) with actual behavior (RSAU) — an AI-native
   SoD that goes past GRC's rule-matching to "right unused" / "done without the role."
6. **Custom-over-standard x-ray** — our brain already holds the Z-code graph; the AI overlays discovered behavior
   on the custom code map. **No commercial product has the customer's own code in the loop.** This is the moat.

## 4. Sequencing (ties to maturity roadmap)
Build the methodology group-by-group, each on the OCEL 2.0 substrate, starting where data is richest + value
highest: **Audit/SoD** (data ready, AI-native edge, business value) and **PSM/FM budget** (no commercial
equivalent — public-sector differentiator). Each group built = a measurable step on `process_mining_maturity.md`.
Grounding sources: research `w3t7ufrbg`, `wgrqpmt9f`, `wc36ii0um`, `wwyujjqyk` (+ `sources_index.json`, 175 urls).
