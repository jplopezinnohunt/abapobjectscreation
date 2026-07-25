---
# Bus header — contract C-4 v1.1 (sole owner: C0). Derived from the prose below; nothing invented.
msg_type: REQUEST
request_id: fmit_bcs_totals
from_project: unesco-sap-brain        # "(S40 AVC refinement)"
date: 2026-06-30
status: OPEN                          # no DONE_fmit_bcs_totals.md on disk as of 2026-07-25
why: "The authoritative UNESCO negative-funds check (YFM1 -> YFM1_BCS_V3 -> variant ZNEGATIVECHECK) reads FMIT, which the golden DB does not have - so the official RB budget-allocation figures cannot be reproduced."
resource_requested: "Land FMIT (FM/BCS totals) in p01_gold_master_data.db and add it to the recurring pipeline alongside fmavct/fmifiit"
extract_spec:
  - source_table: FMIT
    keys: [FIKRS, RFONDS, RFISTL, RFIPEX, RYEAR, RWRTTP, VERSN]   # + period buckets HSL01..HSL16 and HSLVT
    fm_area: [UNES]                   # "(+ the 8 institutes if cheap)"
    years: [2024, 2025, 2026, 2027]   # "covers biennia 42 + 43"
    ledger: 9H
    filters: {VERSN: "0"}             # "ledger 9H / version 0"
consumers:
  - "unesco-sap-brain/knowledge/45 section 8 (YFM1/ZNEGATIVECHECK reproduction)"
resolve_via: "unesco-sap-brain/refs_external.json -> query the golden read-only (never copy raw)"
---

# Request: extract FMIT (BCS budget totals) — basis of the official negative-funds check (YFM1)

> **From:** `unesco-sap-brain` (S40 AVC refinement) · **Date:** 2026-06-30
> **Why:** The authoritative UNESCO negative-funds check is **YFM1 → YFM1_BCS_V3 → variant ZNEGATIVECHECK**, which (per your own `knowledge/domains/PSM/REPORTS/yfm1_technical_analysis.md`) reads **`FMIT`** (FM/BCS totals). The golden DB has `FMAVCT` (AVC ledger), `BPGE`/`BPJA` (budget overall/annual) and `fmifiit_full`, **but NOT `FMIT`** — so we cannot reproduce the official RB budget-allocation figures (e.g. the 5 RP Output Pool negatives totalling −$1.94M for biennium 2026-27).

## What to extract
- **`FMIT`** (FM Totals) for FM area(s) **UNES** (+ the 8 institutes if cheap), ledger 9H / version 0, fiscal years **2024–2027** (covers biennia 42 + 43). Land as `fmit` (or `fmit_<year>`), lowercase, in `p01_gold_master_data.db`.
- Keep the native structure: keys `FIKRS, RFONDS, RFISTL, RFIPEX, RYEAR, RWRTTP, VERSN` + period buckets `HSL01…HSL16` + `HSLVT` (same wide shape as the FMAVCT rebuild). The value-type `RWRTTP` is essential (it drives Budget vs Actual vs Commitment via `YTFM_WRTTP_GR`).
- Add a `_gold_sync_log` row so it rides the recurring pipeline alongside `fmavct`/`fmifiit`.

## Why it matters here
- Lets the brain **reproduce YFM1/ZNEGATIVECHECK** (RB-only, type 001-099, ex-`*GEF*`, ex-CI `GAINS`, version 0, year-2 allocation) instead of reading screenshots — closes the data gap noted in `unesco-sap-brain/knowledge/45` §8.
- Enables the correct split: RB budget-allocation negatives (FMIT, what UNESCO monitors) vs FMAVCT availability incl. XB.

Reference: `abapobjectscreation/knowledge/domains/PSM/REPORTS/yfm1_technical_analysis.md`. Resolve through `unesco-sap-brain/refs_external.json`; query the golden read-only (never copy raw).
