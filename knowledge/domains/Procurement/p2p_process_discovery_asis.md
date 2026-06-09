---
name: P2P (Purchase-to-Pay) — AS-RUN process discovered from data (s079)
description: The first real custom-over-standard x-ray for Procurement, discovered from OUR Gold DB (no extraction). pm4py inductive miner + token-replay conformance + an OCEL 2.0 object-centric store, over 77,629 POs / 437,002 events. The standard 3-way-match happy path vs the real deviations (open POs, invoice-before-goods, multi-cycle). Applied models: OCEL2 + inductive_conformance + dependency_graph (see applied_models.json). Moves Procurement S_STANDARD_REF→PARTIAL, G_CONFORMANCE→PARTIAL.
type: project
---

# P2P AS-RUN — discovered process (the x-ray)

Built from tables we already hold (EKKO/EKPO/EBAN/EKBE/RBKP/RSEG/BKPF) — **no extraction**. Engine:
`Zagentexecution/sap_data_extraction/scripts/sap_process_discovery.py p2p_po_lifecycle` + OCEL 2.0 store
`ocel_build_p2p.py`. This is the AS-RUN half of the domain (the AS-DESIGNED standard = SAP 3-way match /
PaPM P2P reference; G = the delta below).

## What ran
- **77,629 POs · 437,002 events · 5 activities · 5,014 distinct variants.**
- Inductive miner: Petri net 11 places / 14 transitions (on a 4,000-case sample — inductive untractable on
  the full log, the documented scalability ceiling).
- **Conformance (token replay): fitness 0.891 · precision 0.693.**
- OCEL 2.0 object-centric store: 404,675 events / 100,359 objects / **3 object types**
  (PurchaseOrder 72,891 · Vendor 26,912 · PurchasingGroup 556) — one event links multiple objects, no flat
  single-case. File: `process_discovery/p2p.ocel2.sqlite`.

## AS-DESIGNED (standard) vs AS-RUN (ours) — the deltas
| Pattern | Cases | Reading |
|---------|------:|---------|
| **PO Created → Goods Receipt → Invoice Receipt** | 20,987 | the STANDARD 3-way match (the happy path) |
| **PO Created (only)** | 12,622 | POs created, never received/invoiced — **open / abandoned POs** |
| **PO → Invoice Receipt → Goods Receipt** (IR before GR) | 4,487 (+1,375 more) | **control deviation**: invoice posted before goods confirmed (GR/IR mismatch risk) |
| GR→IR→GR→IR, GR→GR→IR→IR | 4,668 + 3,015 | partial deliveries / multiple invoices |
| starts WITHOUT "PO Created" (IR→GR→…) | 1,472 + 854 IR-starts | probable **incomplete cases** (PO created before the data window) |

## Honest caveats (do not over-read)
- **No intra-day time** (`dtime=000000`) → same-day event order is **arbitrary**; part of "IR before GR"
  may be that, not a real deviation. **EXT-CDPOS (real field-level timestamps) would disambiguate.**
- Inductive/conformance numbers are on a **4,000-case sample**, not the full 77,629.
- **VGABE=9** (119,123 EKBE rows) left **unclassified by design** (not SAP-confirmed; never-infer rule).

## Capability impact (Procurement_P2P)
- **A_PROCESS = HAVE** (deepened to object-centric + inductive + conformance, beyond DFG).
- **S_STANDARD_REF → PARTIAL** (standard 3-way captured as the baseline).
- **G_CONFORMANCE → PARTIAL** (as-is vs standard delta computed; the open-PO + IR-before-GR deviations are
  the first real custom-over-standard findings). To reach HAVE: align vs a formal PaPM/OPID reference net.

## Next to deepen (from the backlog)
EXT-CDPOS (field-level timestamps → disambiguate same-day order + add field-change events) · classify
VGABE=9 · formal OPID conformance vs the PaPM P2P reference baseline.
