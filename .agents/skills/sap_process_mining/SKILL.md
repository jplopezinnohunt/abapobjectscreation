---
name: SAP Process Mining (pm4py Engine)
description: >
  Process & usage mining on UNESCO SAP data, two complementary tiers.
  TIER 1 (event-log, pm4py): process discovery / variants / conformance / bottleneck /
  temporal for CTS, FM lifecycle, P2P, CDHDR — "how does ONE process flow?".
  TIER 2 (object-usage, U_USAGE by domain): inventory EVERY executed object
  (tcode/report/RFC-BAPI/job) and map each to domain + actor + behavior + time via 4
  triangulated methods (TADIR.DEVCLASS / logs / objects-read / caller→domain), detect
  hidden/ungoverned extractions (ad-hoc SAP Queries) — "how does UNESCO work overall?".
  JSON-first for brain integration, HTML for visual exploration.
domains:
  functional: [*]
  module: [*]
  process: [*]
---

# SAP Process Mining — pm4py Engine

## Purpose

Discover **how UNESCO SAP processes actually work** (vs. how they're documented):
1. **Process Discovery** — DFG (Directly-Follows Graph) from event logs
2. **Variant Analysis** — How many paths exist? Which is most common?
3. **Conformance Checking** — Does actual behavior match expected model?
4. **Bottleneck Detection** — Where do cases stall?
5. **Temporal Profiling** — Seasonal patterns, period-end spikes

---

## NEVER Do This

> [!CAUTION]
> - **NEVER use pm4py low-level API** — v2.7+ requires high-level functions: `pm4py.discover_dfg(df)` not `dfg_discovery.apply(log)`. The DataFrame-first API is mandatory.
> - **NEVER load full FMIFIIT without WRTTP filter** — internal value types inflate event counts
> - **NEVER accumulate >2M events in RAM without chunking** — use batch processing for large tables
> - **NEVER skip the activity mapping step** — raw WRTTP/VRGNG codes are meaningless without human labels
> - **NEVER use graphviz for visualization** — pm4py HTML output works without graphviz installed

---

## Script Location

```
Zagentexecution/mcp-backend-server-python/
  sap_process_discovery.py          <- Core engine (8 CLI commands)
  cdhdr_activity_mapping.py         <- TCODE→activity rules (100+)
  p2p_process_mining.py             <- P2P-specific mining (848K events)
  process_discovery_output/         <- JSON results directory
    cts_dfg.json                    <- CTS transport DFG
    cts_variants.json               <- CTS variant analysis
    cts_conformance.json            <- CTS conformance (100% fitness)
    cts_bottleneck.json             <- CTS bottleneck analysis
    cts_temporal.json               <- CTS temporal profile
    fm_process_patterns.json        <- FMIFIIT mining (2M events)
```

---

## CLI Commands

```bash
cd Zagentexecution/mcp-backend-server-python

# CTS Transport Mining
python sap_process_discovery.py --cts-dfg          # Directly-Follows Graph
python sap_process_discovery.py --cts-variants      # Variant analysis
python sap_process_discovery.py --cts-conformance   # Conformance checking
python sap_process_discovery.py --cts-bottleneck    # Bottleneck detection
python sap_process_discovery.py --cts-temporal      # Temporal profiling

# FM Budget Lifecycle
python sap_process_discovery.py --fm-lifecycle      # FMIFIIT event mining

# P2P Procurement
python p2p_process_mining.py                        # Full P2P event log mining

# CDHDR Change Audit (via activity mapping)
python cdhdr_activity_mapping.py --mine             # Change doc mining
```

---

## Operating-Model / Object-Usage Discovery — the U_USAGE method (BY DOMAIN)

> A **second tier** of process mining, complementary to the event-log mining above. Event-log mining
> answers *"how does ONE process flow?"* (P2P, CTS, FM lifecycle — case-centric). This answers
> **"how does UNESCO work overall?"**: inventory EVERY executed object (tcode / report / RFC-BAPI / job)
> and map each to **domain + actor + behavior + time** = the AS-RUN operating model (capability dimension
> **U_USAGE**). Method-of-record (read these): `knowledge/operating_model_discovery_methods.md` +
> `knowledge/capability_U_USAGE_execution_footprint.md`.

### The 5-step replicable protocol (works for ANY domain)
1. **INVENTORY** — pull the AS-RUN object set from `rsau_audit_history` (Transaction Start→`PARAM1`,
   Report Start→`SLGREPNA`, RFC Function Call→`PARAM3`) + `tbtcp` (jobs→`PROGNAME`), carrying volume +
   actor (`SLGUSER`) + time (`SAL_DATE`).
2. **MAP to domain — TRIANGULATE 4 methods** (no single one is complete):
   - **by PACKAGE `TADIR.DEVCLASS`** — authoritative, module-coded (FMRP→PSM_FM, FBAS→FI, ME→Procurement,
     PC10→HCM). Cache `tadir_prog`(388K)+`tdevc`(28K) in the Gold DB. **Floor ≈60% by execution volume.**
   - **by LOGS** (execution context / channel).
   - **by OBJECTS-READ** — resolve generated programs via their embedded object (`/1BCDWB/DB<table>`→table→domain;
     SAP-Query `AQ*/!Q*`→workspace/table).
   - **by CALLER→DOMAIN** — map service-account/user→domain + actor-type (human / integration / batch).
3. **ENRICH** per object — actor-type (human / integration MULESOFT·BRIDGE·UBO-RFC·SISTER / batch) + behavior
   (read / DB-write / **file** OPEN-DATASET·AL11 / RFC-out → **integration = technical caller OR file OR write/call-out**)
   + time profile (active vs dead, seasonality).
4. **DETECT hidden extractions** — ad-hoc SAP Queries (`AQ*/!Q*`/SAPQUERY) + caller + time = ungoverned parallel
   data extraction; **query→job→file = shadow integration**. (Verified 2026-06-23: 6,060 execs · 1,798 queries ·
   153 users · 60% HR · JOBBATCH=1,890 scheduled.)
5. **DEEP-DIVE per domain** — top objects by volume → purpose / owner / dead-vs-used / S4-disposition.

### THE command — run this, do NOT re-derive (executable, parameterized by domain)
```bash
cd process_mining
python mine_domain.py                # ALL domains  → brain_v2/domain_footprints/<DOMAIN>.json + _index.json
python mine_domain.py PSM_FM         # one domain
python mine_domain.py HCM PSM_FM     # several
```
**Output per domain (DATA, not prose):** `totals` · `by_channel` · **`by_actor` (human / integration / batch)** ·
`time_monthly` · `dead_objects` · `top_objects` (each with actor_mix, first/last month, dead flag) ·
`hidden_extractions` · `integration_objects`. Uses the SHARED classifier
`executed_objects_domain_map.make_classifier` — **one source of truth, so the next session RUNS this, it does not
re-invent the rules.** Supporting tools: `executed_objects_domain_map.py` (the object→domain map + the
`tadir_prog`/`tdevc` cache), `fm_executed_census.py` (legacy PSM template), `method_registry.py <TABLE>`.

**Verified real output (2026-06-23, all 16 domains):** PS = 1.6M execs but only **6,264 human** vs 1.44M
integration + 165K batch (**PS is machine-driven, near-zero dialog**) · BusinessPartner **88% integration**
(BP master data = MULESOFT/RFC, not people) · PSM_FM **93% human** (real budget work) · HCM **28 hidden ad-hoc
extractions** · FI 239 / PSM_FM 197 dead objects (S/4 dead-code candidates).

**Honest scope:** the unmapped tail (Uncatalogued domain) = ad-hoc queries + generated programs + technical
substrate (SAPMSSY1/RS*) — the substrate is a legitimate **NON-business tier**, NOT lost knowledge. Coverage
today: **60% volume / 39% object**. Raise it via the objects-read + caller methods (PMO H88).

---

## Data Sources & Event Log Construction

### CTS Events (Transport Lifecycle)
```python
# case_id = TRKORR (transport number)
# activity = status transition (Created → Released → Imported)
# timestamp = AS4DATE + AS4TIME
df = pd.DataFrame({
    'case:concept:name': transport_ids,
    'concept:name': activities,     # Created, Released, Imported, etc.
    'time:timestamp': timestamps,
    'org:resource': users
})
```
**Results**: 7,745 cases, 400 unique cases, 198 variants, 96 DFG edges, 100% conformance

### FM Budget Lifecycle (FMIFIIT)
```python
# case_id = FONDS (fund code)
# activity = WRTTP description (via mapping)
# timestamp = GJAHR + PERIO (period-level granularity)
WRTTP_ACTIVITY = {
    '50': 'Funds Reservation',
    '54': 'Actual (Down Payment)',
    '57': 'Actual (Invoice)',
    '58': 'Commitment',
    '61': 'Funds Pre-commitment',
    '66': 'Actual (Transfer)',
}
```
**Results**: 2,070,523 events, 616,427 cases, 1,019 variants (92 seconds)

### P2P Procurement (Multi-Table)
```python
# case_id = EBELN (PO number) or BANFN (PR number)
# activity = stage in P2P flow
# Events from: EBAN → EKKO → EKPO → EKBE → RBKP → RSEG → BKPF
P2P_ACTIVITIES = [
    'PR Created',           # EBAN.ERDAT
    'PO Created',           # EKKO.BEDAT
    'GR Posted',            # EKBE.BUDAT (VGABE=1)
    'SES Created',          # ESSR.ERDAT
    'Invoice Received',     # RBKP.BLDAT
    'Invoice Posted',       # RBKP.BUDAT
    'Payment Cleared',      # BSAK.AUGDT
]
```
**Results**: 848K events, 193K cases (Session #014)

---

## pm4py API Reference (v2.7+)

```python
import pm4py

# Discovery
dfg, start, end = pm4py.discover_dfg(df)
net, im, fm = pm4py.discover_petri_net_alpha(df)
tree = pm4py.discover_process_tree_inductive(df)

# Variant analysis
variants = pm4py.get_variants(df)

# Conformance
fitness = pm4py.fitness_token_based_replay(df, net, im, fm)

# Statistics
stats = pm4py.get_service_time(df)

# Visualization (HTML — no graphviz needed)
pm4py.save_vis_dfg(dfg, start, end, 'output.html')
pm4py.save_vis_petri_net(net, im, fm, 'output.html')
```

> [!IMPORTANT]
> Always use `pm4py.discover_dfg(df)` (high-level), never `dfg_discovery.apply(log)` (deprecated low-level).
> DataFrame columns MUST be: `case:concept:name`, `concept:name`, `time:timestamp`

---

## Process Flows Discovered

### B2R (Budget-to-Report) — Full Lifecycle
```
Budget Entry (FMBH) → Commitment (FMIOI) → Funds Reservation (FMIOI)
  → Actual Posting (FMIFIIT) → FI Document (BKPF) → Carryforward
```
**Status**: FMIFIIT mining done (2M events). FMIOI/FMBH loaded. Full B2R mining pending (needs B2R event log construction).

### P2P (Procure-to-Pay) — Full Lifecycle
```
PR (EBAN) → PO (EKKO) → GR (EKBE) → Invoice (RBKP/RSEG) → Payment (BKPF/BSEG)
```
**Status**: ✅ Done (848K events, 193K cases). Dashboard: `p2p_process_mining.html`

### CTS (Transport Lifecycle)
```
Created → Released → Imported (DEV→QA→PRD)
```
**Status**: ✅ Done (7,745 cases). 100% conformance.

---

## OCEL 2.0 (Pending — Object-Centric)

pm4py supports OCEL 2.0 for multi-object process mining:
```python
# Instead of one case per PO, track multiple objects simultaneously:
# Object types: PO, Invoice, Vendor, Material, WBS Element
ocel = pm4py.read_ocel2('p2p_events.sqlite')
ocdfg = pm4py.discover_oc_petri_net(ocel)
```
**Status**: 🟡 Pending. Requires constructing OCEL event log from P2P + B2R tables.

---

## Integration Points

- **Change Audit**: CDHDR events → `sap_change_audit` skill → activity mapping → pm4py
- **Brain**: DFG edges → PROCESS_VARIANT/BOTTLENECK nodes in `sap_brain.py`
- **Dashboard**: `process-intelligence.html` (297KB) + `p2p_process_mining.html` (663KB)
- **FI Domain**: Payment events from BKPF/BSEG feed P2P completion step
- **PSM Domain**: FMIFIIT WRTTP mapping feeds B2R lifecycle events

---

## Known Failures

| Error | Cause | Fix |
|-------|-------|-----|
| `AttributeError: module 'pm4py' has no attribute 'discover_dfg'` | Wrong pm4py version | `pip install pm4py>=2.7.20` |
| `KeyError: 'case:concept:name'` | DataFrame columns wrong | Rename cols to XES standard names |
| Mining takes >5 minutes | Too many events without filtering | Pre-filter by date/WRTTP/fund before mining |
| DFG has too many edges (unreadable) | Low-frequency noise | Filter DFG edges: `pm4py.filter_dfg(dfg, threshold=0.05)` |
| `graphviz not found` | Not installed | Use HTML output: `pm4py.save_vis_dfg()` — no graphviz needed |

---

## You Know It Worked When

1. DFG visualization shows clear process flow with edge frequencies
2. Variant analysis identifies top 5 most common paths
3. Conformance fitness > 0.8 for known processes
4. Bottleneck analysis identifies stages with highest wait times
5. JSON output loadable into brain for PROCESS_VARIANT node creation
