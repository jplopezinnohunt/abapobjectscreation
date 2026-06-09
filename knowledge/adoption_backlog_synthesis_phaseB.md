---
name: Adoption Backlog — Phase B synthesis over 3 CLOSED researches (process mining + code mining + competitive landscape)
description: The consolidated "what we incorporate" backlog, built ONLY on three CLOSED deep-researches (s079, methodology rule #148). Every row carries an evidence tier — ✅ VERIFIED (survived 3-vote adversarial verification, with citation), 🔶 LEAD (raised but failed verification = not established), 🟦 OWN (our own analysis), ⏳ GAP (the research's own stated uncovered area), ❌ REFUTED (must not repeat). Tiers are load-bearing: only ✅ may drive a product commitment without further verification.
type: project
---

# Adoption Backlog — Phase B (over 3 closed researches)

Phase A closed: research #1 (object-centric process mining, run w3t7ufrbg — 4/102 verified), #3 (SAP code
mining, w3os0wwlx — 25/99 verified, 0 killed), #2 (competitive landscape, wgrqpmt9f — 23/79 verified, 2
killed). All three reached Synthesize with real adversarial votes. This synthesis admits ONLY closed
material; nothing from the degraded/failed earlier runs.

**Tier legend:** ✅ VERIFIED (3-vote, cited) · 🔶 LEAD (raised, failed verification — NOT a fact) ·
🟦 OWN (our own analysis/inventory) · ⏳ GAP (research stated it did NOT cover) · ❌ REFUTED (do not repeat).

---

## A. ALGORITHMS / METHODS
| Item | What it adds | Tier | Source |
|------|-------------|------|--------|
| **OCEL 2.0 data model** (O2O + E2O relations, qualifiers, time-varying object attrs, multi-typed events, no single case) | the object-centric substrate: one event links standard AND custom Z-objects without a forced case notion | ✅ VERIFIED | vdaalst p1435.pdf; arXiv 2403.01975; ocel-standard.org |
| **On-demand multi-perspective mining** from one OCEL store; structurally avoids convergence/divergence | extract SAP once, pivot standard↔custom perspectives without re-extraction | ✅ VERIFIED | vdaalst p1435; arXiv 2209.09725; RWTH PADS |
| **OPID — object-centric Petri nets with identifiers** (conformance alignments tracking object identity; tool oCoCoMoT, SMT-encoded) | THE method for "as-implemented vs as-delivered" — attribute a deviation to a specific (custom) object | ✅ VERIFIED | arXiv 2312.08537; Springer 978-3-031-61433-0 |
| Celonis **Perspectives / CREATE_EVENTLOG** (derive N event logs from one OCDM dataset, each anchored to one object) | commercial proof of the OCEL multi-perspective pattern | ✅ VERIFIED | docs.celonis.com/ocdm, /perspectives |
| Inductive / Heuristic Miner, token-replay, alignments | sound models + conformance beyond DFG | 🟦 OWN | capability_inventory §A,B |
| OCPN discovery (ocpa), HOEG/GNN predictive, OCPM², OLAP-on-OCEL, Graph-of-Relations seeding | raised in #1 but **0-0, did not survive** — leads only | 🔶 LEAD | arXiv 2503.10735, 2404.05316, 2412.00393 (unconfirmed) |
| Discrete-event simulation (SimPy) calibrated from the log | our capability #3 (SIMULATE) | 🟦 OWN | product_architecture doc |

## B. TOOLS / LIBRARIES / STANDARDS
| Item | Aporta | Tier | Source |
|------|--------|------|--------|
| **OCEL 2.0 SQLite/XML/JSON** exchange formats + metamodel + libs | canonical event store; SQLite is drop-in for our Gold DB | ✅ VERIFIED | vdaalst p1435; ocel-standard.org |
| **pm4py** (PIS / Fraunhofer FIT spinoff) — leading OSS; HAS a SAP path | full discovery/conformance engine; we use only DFG today | ✅ VERIFIED | github PIS/pm4py |
| **abaplint** (OSS MIT, TS, on abapGit-serialized code, 183 rules, dead-code/unused detection) | repo-graph linting + dead-code, CI-friendly, graph-compatible | ✅ VERIFIED | github.com/abaplint; rules.abaplint.org |
| **ATC + Code Inspector (SCI)** static engine; variant `S4HANA_READINESS_<ver>`; central remote-check hub (SAP_BASIS 7.51/7.52 central → satellites 7.00+ via RFC); ATC transport-release gate (block on findings) | scan the whole landscape from one hub; wire code-quality to the change lifecycle | ✅ VERIFIED | SAP Help Remote Code Analysis; sapinsider; KBA 3296069/3392481 |
| **Custom Code Migration Fiori app** (3 project types: S/4HANA Migration / BTP Analysis / Custom Code Analysis; usage-based scoping → deletion transports in SUM) | central tool for used-vs-unused scoping | ✅ VERIFIED | SAP CustomCodeMigration_EndtoEnd.pdf; SAP-samples ccm-workshops |
| **SolMan 7.2 CCLM + Decommissioning Cockpit** (4-phase: non-usage, clone/similarity, never-active, obsolete) | landscape-wide custom-code lifecycle (note: SAP Cloud ALM is successor) | ✅ VERIFIED | SAP blog CCLM; KBA 2825777 |
| **Celonis** RFC ABAP module (transport, /CELONIS/BUFFTAB) + Continuous (CDC-delta via /CELONIS/EX_CL_NEW) / one-time / local modes; **"Replacing SAP cluster tables (BSEG)"** best practice | reference for the extractor/CDC pattern + cluster-table handling | ✅ VERIFIED | docs.celonis.com (rfc-module, pipeline, ocpm cluster) |
| **UiPath PM** native SAP = S_RFC + std RFC_READ_TABLE/RFCPING/RFC_GET_FUNCTION_INTERFACE + custom **Z_XTRACT_IS_TABLE** (Theobald alt: Z_THEO_READ_TABLE) | on-stack custom-extractor pattern | ✅ VERIFIED | docs.uipath.com native-sap-extraction |
| **SAP Signavio Process Intelligence** native = std **RFC_READ_TABLE** via JCo, Basis 7.40+ (512-char limit, Note 2246160); newer Datasphere Replication via CDS Views; two models (Standardized vs Custom SQL pipelines / "event collectors") | the vanilla-RFC + SQL-transform pattern (same primitive we use) | ✅ VERIFIED | help.sap.com signavio-PI feature-scope; signavio etl docs |
| **SAP Signavio Process Insights** = ST-PI (+ST-A/PI) on-stack plug-in, PUSH over outbound HTTPS to BTP (Cloud ALM framework); setup `/n/SDF/PINS_SETUP`; Cloud Connector not used | the on-stack push paradigm (no external extractor) | ✅ VERIFIED | community.sap.com 14289914; help.sap.com ST-PI |
| **SAP PaPM "Sample Content for Process Mining on S/4HANA – P2P"** — runs in-HANA (Model Table fns), reads ACDOCA/COSP/COSS via HANA views (zero data movement), derives activities + START/END + variant ranking = SAP-delivered **normative baseline** | a delivered reference P2P model to conform against | ✅ VERIFIED | help.sap.com PaPM P2P sample content PDF |
| ocpa (object-centric toolkit), OCPM² methodology | candidate; **failed verification in #1** | 🔶 LEAD | unconfirmed |
| Competitors with NO verified claim: MS Power Automate (Minit), IBM (myInvenio), ARIS, Apromore, mindzie, Lana/Appian, QPR, Skan, **Mehrwerk MPM (on HANA/SAC)**, Disco, ABBYY | their SAP-connector strategy | ⏳ GAP | #2 openQuestions — dedicated pass |
| Panaya, SmartShift, SNP CrystalBridge, Tricentis LiveCompare, Basis Technologies, Theobald, LeanIX | static-side vendors beyond SAP-native | ⏳ GAP | #3 openQuestions |

## C. TABLES / EVENT SOURCES
| Item | Qué aporta | Tier | Source |
|------|-----------|------|--------|
| **P2P table set: BKPF, BSEG, CDHDR, CDPOS, EKKO, EKPO, EBAN, LFA1, T001, USR02** | SAP-OFFICIAL tables→event-log mapping for P2P (PaPM) — our extraction target list, validated | ✅ VERIFIED | PaPM P2P sample content PDF |
| **Academic table map**: P2P = EKKO/RBKP/EKBE; O2C = VBAK/BKPF; detail = EKPO/EKPA/EKET/BSEG/RSEG/RESB | peer-reviewed table classification for OCEL extraction | ✅ VERIFIED | arXiv 2110.03467 (Berti/van der Aalst) |
| **BSEG is a CLUSTER table** (non-key cols in RFBLG VARDATA) → needs replacement/declustering strategy | avoid naive BSEG extraction (we already learned this; now externally confirmed) | ✅ VERIFIED | docs.celonis.com cluster-table best practice; KBA 2769310 |
| **CDPOS** field-level changes (+ CDHDR) | richest change event source — we have CDHDR headers, not CDPOS | 🟦 OWN | event_sources_catalog; DQ-S079 (pending P01). NB: CDHDR/CDPOS *recipe* details were 🔶 LEAD in #1 |
| JCDS, VBFA, SWW*, NAST, BAL*, APQ*, STAD/SWNC, SNAP, AFKO/RESB/QMEL | status/flow/workflow/output/log/BDC/dump event sources | 🟦 OWN | event_sources_catalog |
| **Auth tables: AGR_1251, AGR_USERS, AGR_TCODES, USOBT/USOBX (SU24)** | roles/users/SoD — the "down to roles and users" layer | ⏳ GAP | #3 openQuestion (largest gap) |
| FM (public sector): FMRESERV, FMIOI, FMIFIIT, FMIT, FMAVCT, FMBH/FMBL/FMBDT | budget→commitment→actual→AVC | 🟦 OWN | fund_management doc |
| **Job VARIANT** (TBTCP.VARIANT + VARI/VARIS) → job INTENT | turns a job step into a parameterized business action | 🟦 OWN | event_sources_catalog §addition (skill sap_variant_analysis) |
| **FILE SYSTEM** (AL11, logical paths PATH/FILENAMECI/FILENAME, OPEN DATASET, file ports, COUPA/MT940/DMEE) | File as OCEL object = the JOIN between external systems and SAP | 🟦 OWN | event_sources_catalog §addition (unmodeled gap) |

## D. SYSTEM ARTIFACTS (monitors / objects / usage logs)
| Item | Qué mide | Tier | Source |
|------|----------|------|--------|
| **SCMON (ABAP Call Monitor) + SUSG** (aggregate; SCMON ~7-day local) | which programs/FMs/methods actually execute | ✅ VERIFIED | SAP CCM guide; KBA 2569292 (SCMON = UPL successor) |
| **UPL** (Usage Procedure Logging; SolMan BW) | predecessor usage source | ✅ VERIFIED | SAP CCM guide; community UPL |
| **ST03N / SWNC workload** | transaction last-used dates SCMON/UPL can't give; collect ~13 months | ✅ VERIFIED | SAP CCM guide; smartShift |
| **Simplification Database** (object→SAP Note; tcode SYCM; load into central ATC) | the as-delivered change catalog for readiness | ✅ VERIFIED | SAP CustomCodeMigration PDF; KBA 3693326 |
| **40-60% of custom code is dead** (some say 60-75%) | the size of the used-vs-unused prize | ✅ VERIFIED (medium) | smartShift; SAP-PRESS (vendor estimates) |
| SE84 where-used / cross-reference (program→table→class→service graph) | dependency graph (our brain already is a partial GoR) | 🟦 OWN / ⏳ GAP | #3 touched only indirectly |
| /IWFND/ OData usage, RFC/BAPI call inventory (RFCDES) | service usage mining | ⏳ GAP | #3 openQuestion |
| SCDO change-doc objects / DBTABLOG (SCU3) for Z-table logging | how to log changes on custom tables | 🔶 LEAD | #1 (failed verification) |

## ❌ REFUTED — do NOT repeat as fact
- The arXiv 2110.03467 OCEL method is **NOT primarily CDHDR/CDPOS-based** (event derivation is broader). (0-3)
- **pm4py does NOT lack a SAP path** — do not claim it ships no SAP connector. (0-3)

## Split-vote cautions (2-1 — wording matters)
- Celonis "Continuous" = **change-log delta sync, NOT streaming real-time CDC**.
- Signavio PI now ALSO has a Datasphere/CDS-View replication path beside RFC_READ_TABLE.

## Time-sensitivity (re-verify before commitment)
- Celonis on-premise extractors deprecate ~end-2026 (→ On-Premise Client).
- SolMan 7.2 CCLM is on a sunset path (→ SAP Cloud ALM); mainstream maintenance to end-2027.
- ATC readiness variant suffix changes per release (S4HANA_READINESS_2022/2023/...).

## What this means for us (conclusions — each traces to a tier above)
1. **Adopt now, low-risk (all ✅):** OCEL 2.0 SQLite as the event substrate; pm4py full engine (beyond DFG);
   abaplint on our extracted_code; treat the PaPM P2P table list as our validated extraction target.
2. **The conformance moat (✅ OPID + ⏳ normative baseline):** OPID/oCoCoMoT is the verified method for
   custom-vs-standard; the as-delivered baseline can be the SAP PaPM reference content (✅ it exists) —
   but whether SAP ships a machine-consumable normative model for OTHER processes is an open question (#1).
3. **Code-mining is our strongest, most-verified ground (25/25):** ATC central hub + SCMON/UPL/ST03N usage
   + CCLM decommissioning + Simplification DB are all confirmed and we are largely NOT overlaying them.
4. **Biggest UNVERIFIED gaps to close next (serial, one at a time):** (a) authorization/SoD layer
   (AGR_*/SU24/SUIM/GRC) — the "down to roles and users"; (b) services/OData-RFC usage mining;
   (c) code→process linking method; (d) the unmapped competitors (Mehrwerk MPM, MS, IBM, ARIS, QPR…).
5. **Our additions (🟦):** job-variant→intent and file-system-as-object are real, unmodeled, and not
   covered by any tool we surveyed — candidate differentiators, to be built and then verified on our data.
