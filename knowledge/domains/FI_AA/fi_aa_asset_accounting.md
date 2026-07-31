---
name: FI-AA — Asset Accounting
description: Asset Accounting is live in all 9 company codes with 20,000+ asset masters and 10,680 postings in 2024+. Reported as "not evidenced" until s097 — it was never examined, not absent.
type: project
module: FI-AA-AA
capability_domain: FI_AA
status: PRODUCTIVE
claims: [356]
---

# FI-AA — Asset Accounting

**Technical component:** `FI-AA-AA` · **Capability row:** `capability_model.domains.FI_AA`

## What is measured

| Signal | Measurement |
|---|---|
| Asset master records (`ANLA`) | **≥ 20,000** (probe cap reached — the true figure is higher) |
| Asset company codes (`T093C`) | **9 — i.e. all of them** |
| Asset postings (`ANEP`) 2024+ | 10,680 |
| Switch framework | `FI_AA_TRANSFER` **ON** |

Active in **every** company code. That, plus an activated transfer business function, makes this a
fully deployed module — not a residual configuration.

## Why it was missed

It was reported as *"not evidenced"* in a scope answer because neither the Gold DB nor the
execution map carried an Asset Accounting bucket. Absence in a derived index was read as absence in
the system. One bounded probe settled it.

**The floor-is-not-an-inventory rule (profile invariant I2) exists because of this case.**

## The PM overlap — ANSWERED (s097)

The "PM overlap" question below is closed. The **Mouv** satellite calls both sides:
`Y_AM_CREATE_ASSET`, `Y_AM_ASSET_CHANGE`, `Z_AM_ASSET_DELETE`, `ZINV_CONFASSET_FIORI`
(Asset Accounting) **and** `ZPM_MYEQUIPMENT`, `ZPM_READ_EQUI_DATA`, `Y_BAPI_COMPLETE_EQUI`
(Plant Maintenance). Equipment and assets are linked **by an external application**, not
by an SAP standard link — so asset custody is governed outside SAP. Claim #379.

## Open questions

1. **Depreciation areas and the chart of depreciation** — not yet read. Determines whether this is
   IPSAS-compliant reporting or a book-only implementation.
2. **Asset classes and number ranges** — what a UN agency actually capitalises (buildings? vehicles?
   IT equipment?) is unknown.
3. **The PM overlap.** 19,313 equipment records exist in Plant Maintenance. Are equipment and assets
   linked, duplicated, or unrelated? Highest-value question here.
4. **Field offices.** With assets in all 9 company codes, how is physical custody tracked across
   locations?

## Relations

- **Capability:** `FI_AA` (D_DATA HAVE · C_CONFIG/U_USAGE PARTIAL · rest NONE)
- **Parent domain:** `FI` · **Module axis:** FI · **Process axis:** A2R
- **Adjacent:** [[FI]] · [[PM]] (the equipment/asset overlap) · [[RE-FX]] (buildings & leases)
- **Claim:** #356 (TIER_1, measured)
