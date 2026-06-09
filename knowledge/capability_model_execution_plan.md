---
name: Capability Model — Execution Plan (divided: no-extraction vs needs-SAP-extraction)
description: The plan generated FROM the capability matrix (Layer 15). Divided per user (s079) into (A) work doable NOW with what we already have — no new SAP extraction — and (B) work that needs NEW extraction of SAP tables/code/programs. Grounded in a Gold DB inventory (207 objects): we already hold the full P2P table set except CDPOS, so the first custom-over-standard x-ray needs NO extraction; the entire AUTH layer + CDPOS + variant contents + file config need extraction.
type: project
---

# Execution Plan — from the capability matrix

Generated from `graph_queries.py capability_gaps`. Expansion order (ranked): S_STANDARD_REF (0) → E_AUTH
(1) → G_CONFORMANCE (2) → A_PROCESS for high-H/low-A → F file/variant. KEY INSIGHT from the Gold DB
inventory: the highest-value first deliverable — the **P2P custom-over-standard x-ray** — needs NO new
extraction (we already hold EKKO/EKPO/EBAN/EKBE/RBKP/RSEG/BKPF/bseg_union/LFA1/T001/CDHDR; only CDPOS is
missing, and it only ENRICHES, it is not required for a first as-is model). So we can ship the
differentiator before any extraction lands.

> **Canonical task list = `brain_v2/capability_model/execution_backlog.json`** (loaded in brain_state, IDs
> AN-* / EXT-* / RES-*). This doc is the human BUCKET VIEW of it. Updated s079 to fold in the S/4HANA
> readiness + BP/CVI work (research wh5gw9exu): a second NO-extraction quick-win appears in Bucket A
> (BP/CVI readiness scored from our master data), and two new extraction items in Bucket B.

## BUCKET A — DO NOW, NO EXTRACTION (uses Gold DB + extracted_code + closed researches)
| ID | Task | Capability cell it fills | Uses (already have) |
|----|------|--------------------------|---------------------|
| AN-OCEL2 | **OCEL 2.0 SQLite substrate** — reformat existing events (bkpf, cdhdr, tbtcp, jest, edidc) into an OCEL 2.0 store | A_PROCESS foundation | Gold DB; OCEL 2.0 spec ✅ |
| AN-PM4PY | **pm4py full engine** — finish the drafted upgrade: inductive/heuristic miner + token-replay conformance | A_PROCESS | sap_process_discovery.py; pm4py ✅ |
| AN-P2P | **P2P as-is discovery** — build the P2P event log + variants/performance from the tables we hold | A_PROCESS (Procurement) ◐→● | EKKO/EKPO/EBAN/EKBE/RBKP/RSEG/BKPF |
| AN-STDREF | **Capture S_STANDARD_REF baselines** (rank-0) — DOCUMENT the standard SAP as-designed model per domain from SAP Best Practices / verified PaPM P2P content. Start P2P, then Payment, then FM/BCS | S_STANDARD_REF ○→◐ | PaPM P2P table+flow ✅; SAP docs |
| AN-G-P2P | **First G conformance delta on P2P** — align as-is (AN-P2P) vs standard baseline (AN-STDREF) via OPID/token-replay → the FIRST custom-over-standard x-ray | **G_CONFORMANCE (Procurement) ○→◐** | AN-P2P+AN-STDREF; OPID ✅ |
| **AN-BPCVI-SCORE** | **🆕 BP/CVI readiness scorer** — replicate the 9 CVI business checks over LFA1/KNA1/BUT000/CVI_CUST_LINK; encode `0/0 ≠ clean` (KBA 3478108); flag missing Tax Number Category per country, bank data, address → **FIRST real S/4 readiness score** | **R_S4_READINESS / BP_CVI (BusinessPartner) ○→◐** | LFA1/KNA1/BUT000/CVI_CUST_LINK ✅ (research wh5gw9exu) |
| AN-ABAPLINT | **abaplint on extracted_code/** — dead-code/unused on the 812 files | B_CODE | extracted_code/; abaplint ✅ |
| AN-DEPGRAPH | **Code dependency graph view** — surface the 52K-node brain as program→table→class where-used | B_CODE | brain graph (already parsed) |
| AN-OPENDATASET | **OPEN DATASET scan** + job→variant linkage half (TBTCP.VARIANT) | F (file/job intent, design) | extracted_code/; tbtcp |

## BUCKET B — NEEDS NEW SAP EXTRACTION / SYSTEM RUN (gated; P01 not currently active)
Provenance rule: system-invariant CODE/structure can come from D01; production DATA must come from P01.
| ID | Extract / Run | Capability cell | System | Caveat |
|----|---------------|-----------------|--------|--------|
| EXT-AUTH | **AUTH layer**: AGR_1251, AGR_USERS, AGR_TCODES, AGR_DEFINE, USOBT/USOBX (SU24), USR02 | **E_AUTH ○→ (closes the column — highest leverage)** | role↔auth = P01; SU24 = D01 | biggest model gap; do RES-AUTH-SOD research first |
| EXT-CDPOS | **CDPOS** (field-level changes) | A_PROCESS (enrich) | P01 | CLUSTER (CDCLS) — ABAP FOR ALL ENTRIES path |
| EXT-VARIANT | **VARI / VARIS** (variant contents) | F (job intent, completes AN-OPENDATASET) | P01 | pool table — key via RFC + RS_VARIANT_CONTENTS |
| EXT-FILES | **File config**: PATH, FILENAMECI, FILENAME, FILEPATH, OPSYSTEM + AL11 | F (file system) | config D01-ok; AL11 per-system | tcode FILE |
| EXT-SERVICES | **Service/interface usage**: /IWFND/ OData, RFC inventory, EDIDS | E/F + B_CODE | P01 | |
| EXT-USAGE | **Usage data**: SCMON/SUSG + UPL + ST03N (used-vs-dead) | B_CODE + R_S4 custom-code factor | P01 | requires SCMON ACTIVE — PROBE first |
| EXT-EVENTSOURCES | **Missing sources**: JCDS, VBFA, SWW*, NAST, BAL*, APQ*, SNAP | A_PROCESS breadth | P01 | per event_sources_catalog |
| **EXT-BPCVI** | **🆕 BP/CVI vendor side**: BUT020, BUT0ID, BUT100, CVI_VEND_LINK, KNBK | R_S4 / BP_CVI (completes AN-BPCVI-SCORE) | P01 | we already hold the customer side |
| **EXT-S4CHECKS** | **🆕 S/4 system checks (RUNS, not tables)**: ATC S4HANA_READINESS, SI-Check /SDF/RC_START_CHECK, Maintenance Planner, Readiness Check 2.0, Simplification DB import | R_S4 (SI / custom-code / technical / readiness-check factors) | D01 (mostly) | system runs, not Gold-DB pulls |

## RESEARCH follow-ups (gaps the closed researches named) — `RES-*`
RES-AUTH-SOD (auth/SoD method → lift E_AUTH GAP→VERIFIED) · RES-FINANCE-S4 (Finance pillars beyond Asset
Accounting) · RES-COMPETITORS (Mehrwerk/MS/IBM/ARIS/QPR…) · RES-S4-GREENFIELD (Migration Cockpit + factor weighting).

## Sequencing (what the division means)
1. **Two NO-extraction quick-wins, either first:**
   - **AN-P2P→AN-STDREF→AN-G-P2P** = the P2P custom-over-standard x-ray (the product's core demo), preceded by AN-OCEL2/AN-PM4PY.
   - **AN-BPCVI-SCORE** = the first real S/4 readiness score from our own master data (self-contained, the migration hook).
   Both move the matrix without P01.
2. **In parallel, no extraction:** AN-ABAPLINT/AN-DEPGRAPH (code), AN-OPENDATASET (file/variant halves).
3. **Then extraction/runs, when P01 active:** EXT-AUTH (closes column E, lifts every domain) first — preceded
   by RES-AUTH-SOD; then EXT-CDPOS/EXT-USAGE (deepen) + EXT-S4CHECKS (S/4 system runs, D01); then
   EXT-BPCVI/EXT-VARIANT/EXT-FILES (complete BP+variant+file); then EXT-SERVICES/EXT-EVENTSOURCES.
4. **Cross-project:** AN-STDREF standard baselines are system-invariant → reusable by unesco-sap-brain and any
   other SAP project verbatim (the portability principle).

## Definition of done (per the operating rule)
A domain cell goes ●HAVE only with evidence; a G cell requires BOTH the AS-DESIGNED baseline AND the AS-RUN
process AND the computed delta. Nothing is presented as conformance without the standard baseline.
