---
name: PM — Plant Maintenance / Equipment
description: 19,313 equipment records with six EAM business functions switched on. Probably the SAP back-end of the "Mouv" equipment satellite — that link is unverified and is the first thing to check.
type: project
module: PM-EQM-EQ
capability_domain: PM
status: PRODUCTIVE
claims: [356]
---

# PM — Plant Maintenance / Equipment

**Technical component:** `PM-EQM-EQ` · **Capability row:** `capability_model.domains.PM`

## What is measured

| Signal | Measurement |
|---|---|
| Equipment master records (`EQUI`) | **19,313** |
| Plants (`T001W`) | 84 |
| Warehouses (`T300`) | 2 |
| EAM business functions | `EAM_SFWS_SC1`, `EAM_SFWS_UI1_MP`, `EAM_SFWS_UI1_WOREL`, `EAM_SFWS_UI1_WOCAL`, `EAM_SFWS_UI1_SHOPP`, `EAM_SFWS_UI1_DSIGN` — **all ON** |

19,313 equipment records is a substantial installed base, and six activated EAM UI business
functions mean somebody deliberately switched on enhanced maintenance functionality — a project
decision, not a default.

## The hypothesis to test first

The integration map documents a satellite called **"Mouv"** — *asset/equipment management*, 12
custom RFC function modules, classified low volume. PM is very probably its SAP back-end.

**This is UNVERIFIED and it matters:** if Mouv is the front-end, equipment is maintained *outside*
SAP and PM is a system of record being written to by an external application — which places it
squarely inside the 80.6%-external operating model and changes how it must be governed.

How to test: resolve the 12 Mouv function modules and check whether they touch `EQUI` / `IFLOT` /
maintenance orders.

## Open questions

1. **Mouv ↔ PM** — the link above. First priority.
2. **Are there maintenance orders at all**, or is this equipment master data only? No order volume
   has been measured. An equipment register without orders is an inventory, not a maintenance
   process.
3. **The FI-AA overlap.** ≥20,000 assets and 19,313 equipment records. One population, two, or a
   partial link via `ANLA`?
4. **84 plants** against 9 company codes — plants here likely represent field offices/sites. Worth
   confirming: it defines the geographic granularity of logistics.

## Relations

- **Capability:** `PM` (D_DATA HAVE · U_USAGE PARTIAL · rest NONE)
- **Module axis:** PM · **Process axis:** P2P
- **Adjacent:** [[FI_AA]] (asset/equipment overlap) · [[Procurement]] (spares, services) ·
  [[Integration]] (the Mouv satellite)
- **Claim:** #356 (TIER_1, measured)
