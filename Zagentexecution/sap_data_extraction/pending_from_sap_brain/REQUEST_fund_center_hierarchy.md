---
# Bus header — contract C-4 v1.1 (sole owner: C0). Derived from the prose below; nothing invented.
msg_type: REQUEST
request_id: fund_center_hierarchy
from_project: unesco-sap-brain        # "(S39)"
date: 2026-06-30
status: OPEN                          # no DONE_fund_center_hierarchy.md on disk as of 2026-07-25
why: "The golden DB has the leaf fund_centers (787) but not the standard hierarchy - the office -> sub-region -> region -> sector -> HQ rollup cannot be reconstructed. The extracted SET tables contain only set class 0000."
resource_requested: "Add the FM fund-center standard-hierarchy SET rows (parent-child tree + leaves + group texts) to p01_gold_master_data.db and note the set class used in a manifest row"
extract_spec:
  - source_table: SETNODE
    keys: [SETCLASS, SUBCLASS, SETNAME, SUBSETNAME]
    set_class: "0306"
    fm_area: [UNES, ICTP, UIS, IIEP, IBE, UIL, ICBA, MGIE, UBO]
  - source_table: SETLEAF
    keys: [SETCLASS, SETNAME, VALFROM, VALTO]
    set_class: "0306"
    fm_area: [UNES, ICTP, UIS, IIEP, IBE, UIL, ICBA, MGIE, UBO]
  - source_table: SETHEADER
    keys: [SETNAME, DESCRIPT]
    set_class: "0306"
  - source_table: SETHEADERT
    keys: [SETNAME, DESCRIPT]
    set_class: "0306"                 # "if UNESCO keeps it under a different set class, extract whichever resolves fund_centers.FICTR into a tree"
consumers:
  - "unesco-sap-brain/knowledge/44_fund_center_structure_organizational_axis.md sections 1 and 4 (closes claim CLM-196)"
  - "unesco-sap-brain entity fund-center-structure + /tools/fund-center-structure.html"
resolve_via: "unesco-sap-brain/refs_external.json -> query the golden tables directly (never copy raw)"
---

# Request: extract the Fund Center STANDARD HIERARCHY (FM responsibility-axis rollup)

> **From:** `unesco-sap-brain` (S39) · **Date:** 2026-06-30
> **Why:** Single-source-of-truth — raw SAP structure lives ONLY in the golden DB. The brain just
> characterized the **Fund Center as the organizational/responsibility axis** of the model
> (`knowledge/44`, claims CLM-190…200). The one missing piece is the **standard hierarchy** — the
> office → sub-region → region → sector → HQ **rollup**. It is **NOT in the golden DB**, so the
> parent-child tree (and any region/sector budget roll-up reporting) cannot be reconstructed.

## What's there vs. missing (measured on the golden, 2026-06-30)
- `p01_gold_master_data.db` HAS the **leaf** master: `fund_centers` (787, key `FICTR`/`FIKRS`) + `fund_centers_text`. Leaf fund centers and their spend (`fmifiit_full.FISTL`) are visible.
- It does **NOT** have the **hierarchy**: there is no `FMFCTR`-hierarchy table, and the extracted SAP **SET** tables (`SETLEAF`/`SETNODE`/`SETHEADER`) contain **only set class `0000`** (15 basis sets) — none of the FM fund-center groups. So the rollup is unverified.

## What to extract (the FM fund-center standard hierarchy)
SAP stores the FM fund-center hierarchy as a **set** (group structure). Please add, for FM area(s) `UNES` (+ the 8 institute FM areas: ICTP, UIS, IIEP, IBE, UIL, ICBA, MGIE, UBO):

| Source | Key | What it is |
|---|---|---|
| **`SETNODE`** (set class **`0306`**) | `SETCLASS='0306', SUBCLASS=<FM area>, SETNAME, SUBSETNAME` | the parent→child **node tree** of fund-center groups |
| **`SETLEAF`** (set class `0306`) | `SETCLASS='0306', SETNAME, VALFROM/VALTO` | the **leaf** fund centers under each group |
| **`SETHEADER` / `SETHEADERT`** (set class `0306`) | `SETNAME, DESCRIPT` | group names/descriptions |

*(If UNESCO keeps the FM fund-center hierarchy under a different set class/standard-hierarchy name, please extract whichever class resolves the `fund_centers.FICTR` values into a tree — e.g. the FM "standard hierarchy" maintained via `FMSA`/`FM_SETS`. The discriminator: the set whose leaves match `fund_centers.FICTR`.)*

## Suggested action
1. Add the `0306` (or the UNESCO fund-center standard-hierarchy) `SETNODE`/`SETLEAF`/`SETHEADER(T)` rows to the RFC extraction — same mechanism as the existing config-frontier SET pull.
2. Land them in `p01_gold_master_data.db` (lowercase names to match convention), and note the set class/name used in `_config_frontier_manifest` or an equivalent manifest row.

## Consumers / impact in unesco-sap-brain
- `knowledge/44_fund_center_structure_organizational_axis.md` §1 + §4 (the functional class is currently a TEXT heuristic — the hierarchy makes it authoritative) and claim **CLM-196** (the data-gap claim, to be closed).
- entity `fund-center-structure` (TOPIC) + `funds-center`, companion `/tools/fund-center-structure.html`.
- Enables office→region→sector budget roll-up for the TO-BE responsibility tree (the redesign).

Resolve through `unesco-sap-brain/refs_external.json` → query the golden tables directly (never copy raw).
