# Request: refresh the AVC control TOTALS (live availability balances) + put the AVC layer on the recurring pipeline

> **From:** `unesco-sap-brain` (S40, AVC grouping analysis) · **Date:** 2026-06-30
> **Why:** The brain just characterized **how UNESCO actually controls AVC** — it is a *grouped* control
> (commitment items → ~9 activation groups → a single `TC` pool per **Fund × Fund Center**; only ~9% of
> funds carry any control object; tolerance profiles incl. a deactivated `Z200`). To state the values
> "as of today's P01" we need the **live availability balances** refreshed. Single-source-of-truth: raw
> SAP rows live ONLY in the golden DB; the brain never keeps a second copy (ADR-007).

## What's stale vs current (measured on the golden, 2026-06-30)
| Layer | Golden tables | Last pull | Status |
|---|---|---|---|
| Master data | `funds` (67,526), `fund_centers` (787), `commitment_items` | **2026-06-29** (recurring `_gold_sync_log`) | ✅ current |
| FM actuals | `fmifiit_full` (→ period **006/2026**), `fmioi`, `fmbl` | 2026-06-22 (recurring) | ~1 wk |
| AVC **config** | `buavctolass`, `fmavcldgratt/act/gat`, `fmavcatgr_001/002`, `fmavcbudfilt*` | 2026-06-19 (one-off config-frontier) | config, rarely changes |
| **AVC totals** | **`fmavct_2024/2025/2026`** (the live `HSL01` available-budget balances) | **untracked** — in *neither* `_gold_sync_log` *nor* `_config_frontier_manifest` | ⚠️ **drifts daily; no refresh cadence** |

## What to extract / fix
1. **Re-extract `FMAVCT`** (FM AVC totals records) for FM area(s) `UNES` + the 8 institute areas (ICTP, UIS, IIEP, IBE, UIL, ICBA, MGIE, UBO), fiscal years **2024–2026**, AVC ledger **`9H`**. Land as `fmavct_2024/2025/2026` (current convention) in `p01_gold_master_data.db`. Key/measure columns already in use: `RFIKRS, RFUND, RFUNDSCTR, RCMMTITEM, RYEAR, ALLOCTYPE_9, HSL01` (extend with any consumption/commitment legs available — e.g. the `HSL*` value-type columns — so available = budget − consumed can be computed, not just the budget leg).
2. **Add the whole AVC layer to the recurring PSM_FM pipeline** (config + totals) with a `_gold_sync_log` row, so it stops going stale silently. Config tables change rarely (re-sync weekly is fine); `FMAVCT` totals should ride the same cadence as `fmifiit_full`.
3. Note the AVC extraction in `_config_frontier_manifest` (or `_gold_sync_log`) with the `extracted_at` timestamp so freshness is queryable.

## Consumers / impact in unesco-sap-brain
- New analysis `knowledge/45_avc_grouping_control_logic.md` (+ claims CLM-201…) — the live $ availability figures and the controlled-fund count depend on `fmavct_*` being current.
- Cross-refs the AVC config already extracted 2026-06-19 (`buavctolass` etc.) and the INC-005638 desync surface (`knowledge/21`).
- Reconciles with the existing `BPGE/BPJA` budget totals and `fmifiit_full` consumption — fresh `FMAVCT` lets us re-measure FM-AVC vs PS-AVC divergence on today's data.

Resolve through `unesco-sap-brain/refs_external.json` → query the golden tables directly (never copy raw).
