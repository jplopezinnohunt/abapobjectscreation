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
