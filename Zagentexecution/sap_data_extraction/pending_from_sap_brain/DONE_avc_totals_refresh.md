# DONE — AVC totals refresh + AVC layer onto the recurring PSM_FM pipeline

> **Resolved:** 2026-06-30 · **For:** `unesco-sap-brain` S40 (AVC grouping analysis)
> **By:** `abapobjectscreation` (SAP source of truth) · Request: [REQUEST_avc_totals_refresh.md](REQUEST_avc_totals_refresh.md)
> Golden DB is single-source-of-truth (ADR-007); query the tables directly via `refs_external.json`. No raw copy was sent.

## 1. FMAVCT re-extracted WIDE (live P01, ledger 9H, FY 2024-2026, all 9 FM areas)
Re-pulled `FMAVCT` for **UNES + ICTP UIS IIEP IBE UIL ICBA MGIE UBO** → rebuilt `fmavct_2024/2025/2026`.

| table | rows (was) | rows (now) | cols (was→now) |
|---|---|---|---|
| `fmavct_2024` | 15,890 (UNES only) | **18,838** (9 areas) | 7 → **38** |
| `fmavct_2025` | 13,288 | **16,112** | 7 → **38** |
| `fmavct_2026` |  9,531 | **13,593** | 7 → **38** |

**Schema is a strict superset** — the legacy 7 columns (`RFIKRS, RFUND, RFUNDSCTR, RCMMTITEM, RYEAR, ALLOCTYPE_9, HSL01`) are all retained, so existing consumers don't break. Added the columns needed to compute **`available = budget − consumed`**:
- **Full natural key** `RLDNR, RRCTY, RVERS, RYEAR, RTCUR, DRCRK, RPMAX, ROBJNR, COBJNR, SOBJNR` → every row now uniquely identified (the legacy pull collided ~36% of rows on the readable dims, which is why budget vs consumed was previously unresolvable).
- **All period buckets** `HSLVT, HSL01..HSL16` (FM-area/local currency) → annual figure = `HSLVT + Σ HSL01..HSL16`, not just period 1.
- Extra dims `RFUNCAREA, RGRANT_NBR, RMEASURE, RCVRGRP_9, BUDGET_PD_9, WFSTATE_9`.

### How to compute available = budget − consumed (verified example)
The budget address and its consumption are **separate rows sharing the consuming object `COBJNR`, distinguished by `ROBJNR`** (the responsible/budget object), and grouped by cover group `RCVRGRP_9`. Verified on `9H/2026/UNES/3110111021/PAX/TC`:
- `ROBJNR=…3870146` (budget) annual **4,500.00** USD
- `ROBJNR=…3870148` (consumption) annual **547.65** USD → **available = 3,952.35**.

Value type is `ALLOCTYPE_9` (data element `BUAVC_ALLOCTYPE`; for UNES only `KBFC` = "Hard commitments / allocated budget" is in use; the SEEC/SENC/REEC… cover-element legs exist in the domain but carry no UNES rows). `RRCTY` ∈ {0,1} is also retained.

## 2. AVC layer is now on the recurring PSM_FM pipeline
New owner script: **`scripts/extraction/psm_avc_refresh.py`** (`config` | `totals` | `all`). Field-split RFC reads (the 38-col set exceeds the 512-byte WA buffer). Registered as **`source: "curated"`** in `brain_v2/gold_table_registry.json` (`delta: "external"` → `gold_refresh.py` skips them; this script owns them) with `refresh_script` + `cadence`:
- **config** (BUAVCTOLASS, FMAVCATGR_001/002, FMAVCBUDFILTB/H, FMAVCLDGRACT/ATT/GAT) — weekly. *(BUAVCTOLASS had already drifted 34→36 rows since the 2026-06-19 one-off, confirming the staleness risk.)*
- **totals** (FMAVCT) — same cadence as `fmifiit_full` (balances drift daily).

## 3. Freshness is queryable
Every AVC table now has a `_gold_sync_log` row and a `_config_frontier_manifest` row with `extracted_at = 2026-06-30`. Query examples:
```sql
SELECT gold, ts, n_total FROM _gold_sync_log WHERE gold LIKE '%avc%' ORDER BY ts DESC;
SELECT sqlite_table, extracted_at, n_rows FROM _config_frontier_manifest
  WHERE grp LIKE '%recurring%';
```
