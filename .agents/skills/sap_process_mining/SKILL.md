---
name: SAP Process Mining (pm4py Engine)
description: >
  Process discovery and conformance checking on UNESCO SAP event data using pm4py.
  8 CLI commands covering CTS transport mining, FM budget lifecycle, P2P procurement,
  and CDHDR change audit. Generates DFG, variants, conformance, bottleneck, and
  temporal analysis. JSON-first output for brain integration, HTML for visual exploration.
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
