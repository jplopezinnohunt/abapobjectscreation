---
name: OCEL Extraction Methodology (the substance the deep research actually taught)
description: The actionable methodology mined from the 4M-token deep research transcripts (van der Aalst/RWTH sap-extractor + OCEL 2.0) — NOT the thin table list. How to build object-centric event logs from SAP correctly, the flattening problem we are committing, the object-type/key/field-activity recipes, GoRs, delta loading. Persisted s079 after the first synthesis under-mined the research.
type: project
---

# OCEL extraction methodology — what the deep research actually taught

Honest note: the first pass collapsed a 4M-token / 102-agent research into "tables you're missing".
The substance is the METHODOLOGY below — it changes HOW we build, not just WHAT to extract.

## 1. We are committing the FLATTENING problem (all THREE, not two)
Forcing a single case notion (our case = AUGBL / OBJECTID) causes — verbatim from the literature:
- **Deficiency** — unintentional REMOVAL of events.
- **Convergence** — unintentional DUPLICATION of events (one event shared by N cases).
- **Divergence** — inability to separate events within a case (false ordering).
"In enterprise systems one-to-one relationships are the EXCEPTION; most are one-to-many/many-to-many,
so data must be transformed to a single case — leading to these problems." And: "changing the
viewpoint implies changing the case notion and going back to the source to re-extract." → Our
single-case engine is the anti-pattern; build OCEL ONCE and analyze from any object angle.

## 2. The OCEL extraction PIPELINE (4 steps — the actual HOW)
1. **Pre-processing** — select the relevant tables.
2. **Defining the activity concept** — how each row becomes an activity (transaction tables: "Executed
   <tcode>"; change tables: field/old-vs-new; record tables: "Created").
3. **Defining object types** — RULES: "the values of all columns except dates and numbers become OBJECTS
   of the object type given by the column's name"; master-table entries become EVENTS with columns as
   attributes. Per-object-type KEY: PurchaseOrder = EKKO.EBELN, PurchaseRequisition = EBAN.BANFN, etc.
4. **Connecting entries** — DETAIL tables (EKPO/BSEG) are used to ENRICH events / link objects.

## 3. Graph of Relationships (GoR) — table selection per process (WE CAN DO THIS NATIVELY)
The method uses a "Graph of Relationships" — graph the tables and object types related to a process to
SELECT what to extract (e.g. the subgraph for object type EINKBELEG = purchase orders). **Our brain IS a
GoR engine** (the data model + DD08L foreign keys + the connective layer). This is a differentiator: we
can generate the GoR per process from the brain, not hand-pick tables.

## 4. Object types & movement/flow tables (concrete)
- O2C object types: Inquiry, Quotation, Order, Delivery, Goods Movement, Shipment, WMS TO, Invoice.
- **EKBE / MSEG = "movement tables"**: EKBE yields the "Goods Receipt" activity for POs (via movement
  type code). VBFA = O2C flow. Document-flow/movement tables are dedicated event sources.
- Production-order process table set (one worked example): JCDS, TJ02T, AFKO, RESB, CDPOS, CDHDR, EKPO,
  EBAN, EKBE, MSEG.

## 5. Change-data nuances (important, missed first pass)
- **There is NO universal change table.** Whether/how changes are logged is CONFIG-DEPENDENT per object:
  JCDS holds STATUS history; CDPOS holds FIELD changes; different objects logged differently. Don't
  assume CDHDR/CDPOS covers everything (e.g. production-order status is in JCDS, not CDHDR/CDPOS).
- **3 ways to gather change data**: dedicated change tables (CDHDR/CDPOS, JCDS), redo logs, or snapshot
  diffing.
- **Append-only → DELTA-loadable**: CDHDR/CDPOS rows are never updated/deleted → safe for incremental
  delta loads. **~1 BILLION rows** in enterprise systems → filtering by OBJECTCLAS is MANDATORY
  (validates our by-object CDPOS extractor design, with the scale number we lacked).

## 6. Concrete field → activity mappings (the AP template, reusable)
- `BSEG-ZLSPR` (payment block) change → **"Payment Block Applied/Removed"**.
- `BSEG-ZTERM` (payment terms) change → **"Payment Term Changed"**.
- PREREQUISITE: change-document logging must be ACTIVE for the field (ZLSPR) or it isn't captured — a
  config check before mining the activity. (Build a library of field→activity mappings per process.)

## 7. Conformance (the use we don't do)
"Using conformance checking, the discovered model can be compared with other event logs to analyze
discrepancies" — the as-is vs reference comparison. Pairs with our code-level conformance angle.

## What changes in our build (actionable)
- A. STOP flattening: implement real OCEL (pm4py discover_ocdfg on a multi-object log) — fixes
  deficiency/convergence/divergence.
- B. Use the BRAIN as the GoR generator (per-process table/object selection) — our edge.
- C. Apply the object-type derivation rules + per-object-type keys; detail tables enrich.
- D. Delta/append-only loading for change docs; OBJECTCLAS filtering for CDPOS (~1B scale).
- E. Build a field→activity mapping library (ZLSPR/ZTERM/...) + the change-doc-logging prerequisite check.
- F. Conformance as-is-vs-reference.

## 8. ALGORITHMS & TOOLS (3rd-pass mining — the pieces that matter most, missed twice)
- **Object-Centric Petri Net (OCPN) discovery** (van der Aalst 2020, "Discovering object-centric Petri
  nets") — the actual OCPM discovery ALGORITHM, beyond the DFG/OCDFG. This is what discovers a real
  object-centric model. We were only doing DFG.
- **ocpa** — the object-centric process analysis Python library (OCPN discovery, conformance, performance
  over OCEL). pm4py has OCEL/OCDFG; ocpa is the deeper OCPM toolkit. Adopt alongside pm4py.
- **OCEL 2.0 STANDARD + formats**: three exchange formats — **SQLite (relational DB)**, XML, JSON
  (`*.jsonocel`). We already use SQLite → store our event log AS the standard OCEL 2.0 SQLite → instantly
  interoperable with pm4py/ocpa/ProM, no custom format. Reference OCELs: ocpm.info/o2c.jsonocel, p2p.jsonocel.
- **OCEL 2.0 dynamic object attributes (`oaval`, indexed by time)** — THE mechanism to model
  STATUS-LIFECYCLE: JEST/JCDS status changes = an object attribute whose value changes over time. So
  status isn't a separate event stream — it's the object's attribute history. Concrete model for JCDS.
- **OCEL 2.0 O2O (object-to-object) relationships + qualifiers** — model PO→PR→Invoice→Payment links
  with roles (E2O qualifier = actor/resource). Richer than flat.
- **OpenSLEX meta-model** — a generic relational→event-log meta-model, built from redo logs OR SAP change
  tables. An alternative extraction framework reference.
- **GoR is a 2-PHASE method with SQL recipes**: (1) build the Graph of Relations from a MASTER table of
  the process (then add joint/related tables; colors = the 5 table classes), (2) extract OCEL by SQL per
  GoR node category. The paper gives the SQL queries (Table 2). Our brain generates phase (1) natively.
- **Activity-from-change-context RECIPE (exact)**: default activity name = object-class name + the
  attribute description; Figure 4.9 maps (OBJECTCLAS, FNAME, VALUE_OLD, VALUE_NEW) → activity. Precise
  CDPOS→activity rule.
- **`jcds_tracking_activated`** — Celonis/UiPath pattern: a flag to build models from the JCDS table.
- Commercial landscape named: Celonis, SAP Signavio, **LANA, UiPath, ProcessGold**.

## What changes (added)
G. Adopt **OCEL 2.0 SQLite format** as our event-log store (we already use SQLite) — standard + interoperable.
H. Use **OCPN discovery (ocpa)**, not just DFG — the real object-centric model.
I. Model **status (JEST/JCDS) as OCEL dynamic object attributes (oaval)**, not a separate flat log.
J. Model **O2O relationships** (PO→PR→Invoice→Payment) with qualifiers (actor = resource).

## 9. CONCRETE TECHNIQUES (4th-pass — the Küsters/RWTH thesis + OCEL papers)
- **SQL-TRACE field discovery (we already have the ST01 skill!).** To find WHICH fields are
  activity-relevant: run the transaction (e.g. 2nd release of a PR), TRACE the SQL, observe the UPDATE
  (e.g. EBAN.FRGZU='XX' = release), which is mirrored in CDPOS/CDHDR. Then **filter the trace to INSERT
  statements only** (INSERTs are the change trail; UPDATEs often overwrite without a trail). This is the
  systematic way to build the field→activity library — and ties directly to our `sap_st01_trace_reader`.
- **Movement-type (BWART) → activity** (movement tables EKBE/MSEG): BWART code maps to the activity —
  101 = "Goods receipt for a PO", 261 = "materials issued to production". EKBE = GR for POs; MSEG = goods
  movements for production orders. Filter on BWART.
- **Production/QM process tables**: AFKO (production order header) + RESB (reservations) — merge to
  connect orders↔reservations; QMEL (quality notifications). Production-order STATUS lives in **JCDS**
  (NOT CDHDR/CDPOS) decoded via TJ02T — "status determines which transactions can execute next" (the
  status IS the process). Full production set: JCDS, TJ02T, AFKO, RESB, CDPOS, CDHDR, EKPO, EBAN, EKBE, MSEG.
- **CHNGIND='I' = creation event** (confirmed: "Created Purchase Order" = CDPOS.CHNGIND='I').
- **SAP Meta-Explorer** — tool to visualize/retrieve table connections (uses DD03L/DD03M meta-tables —
  same DDIC we extract for the data model). Reference impl is pandas + the sap-extractor DB connectors (like ours).

## 10. PAPERS / METHODOLOGY / ALGORITHMS still unsurfaced (4th-pass)
- **OCPM² (arXiv:2503.10735)** — "Extending the PROCESS MINING METHODOLOGY for Object-Centric Event Data
  Extraction" — a structured methodology (PM²-style) for OCED. A framework to follow, not just techniques.
- **"Filtering and Sampling Object-Centric Event Logs" (arXiv:2205.01428)** — the EVENT-LOG QUALITY
  methods we flagged as a gap: object-centric filtering/sampling. There IS a method; adopt it.
- **"Preserving complex object-centric graph structures to improve machine learning" (vdaalst p1427)** —
  ML/PREDICTION over object-centric data by PRESERVING the graph (GNN-style) instead of flattening.
  OCPM's three first-class uses: discover models, conformance, **PREDICTIONS** (van der Aalst).
- **OC-PM (Springer s10009-022-00668-w)** — analyzing OCELs + object-centric process models.
- **OCEL 2.0 spec**: ocel-standard.org/2.0 (the official standard site).
- Metaphor we share: "object-centric process mining = ERP's x-ray becomes an MRI" (erp.today).

## What changes (added)
K. Use our **ST01 trace skill** to discover activity-relevant fields per transaction (SQL-trace → INSERTs).
L. Build a **movement-type (BWART) activity library** (101/261/...) for EKBE/MSEG.
M. Add **production/QM** (AFKO/RESB/QMEL + JCDS) to the process catalogue.
N. Adopt **OCPM² methodology** + the **filtering/sampling** method (event-log quality) + **graph-preserving
   ML** for prediction.

## Meta-lesson
Mine research deeply, and DON'T STOP at the first pass — it took THREE passes to surface the algorithms
(OCPN, ocpa) and the standard (OCEL 2.0 formats, oaval, O2O) that are the actual core. Do not collapse a
4M-token study into a summary; grep the transcripts for tools/algorithms/formats explicitly, not just the
conclusions. See feedback_audit_what_youre_not_doing.
