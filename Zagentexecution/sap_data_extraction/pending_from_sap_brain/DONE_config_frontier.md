---
# Bus header — contract C-4 v1.1 (sole owner: C0). Derived from the prose below; nothing invented.
msg_type: DONE
request_id: config_frontier
from_project: abapobjectscreation
owner: abapobjectscreation
date: 2026-06-19
consumers: [unesco-sap-brain]
system_role: P01                      # "MEASURED on P01 client 350"
closes:
  - "unesco-sap-brain/knowledge/35_recreated_conclusions.md lines 75-80"   # closes a knowledge doc, not a REQUEST_ file
tables_landed: UNKNOWN                # 61 tables, NOT enumerated in-message; full inventory lives in manifest_ref
row_counts: {_total_approx: 13794}    # "~13,794 rows"; golden table count 225 -> 286
manifest_ref: _config_frontier_manifest
verdicts:
  - "HYP-008 / OI-FI-01 doc splitting: OFF - FAGL_ACTIVEC/FAGL_SPLIT_ACTC empty, GLT0 populated -> classic G/L; method Z000000012 does not exist"
  - "F3 new-GL ledger: t881 defines leading 0L -> FAGLFLEXT but 0 postings; real parallel ledgers = classic FI-SL"
  - "HYP-018 / CLM-012/024 GMDERIVE: strategy GMDT registered but GMGR/GMIA = 0 grants -> GM not productively used"
  - "CLM-036 / HYP-003 FMDERIVE: config = generic TABADR*, not FMDT_*; strategy FMOA = 14 steps / 5 custom DRULE -> '5 of 26' half-confirmed (5 matches, 26 does not)"
  - "HYP-012 AVC tolerance: BCS AVC active (ledger 9H, 9 FM areas, FY2001+); limits 100% Error default, ICTP 80% Warning; no 50% threshold"
how_to_consume: "Resolve through unesco-sap-brain/refs_external.json -> query the golden tables read-only (never copy raw). Start from _config_frontier_manifest."
---

# DONE — SAP config-frontier extraction (response to unesco-sap-brain)

**Owner:** abapobjectscreation (SAP source of truth) · **Date:** 2026-06-19 · **For:** unesco-sap-brain
**Closes the "still needs extraction" rows in** `unesco-sap-brain/knowledge/35_recreated_conclusions.md` (lines 75-80).

The last SAP-internal config frontier is now in the golden DB
(`Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`, read-only).
**61 new tables (~13,794 rows); golden 225 → 286.** Full inventory + row counts (incl. empty/absent) in golden table **`_config_frontier_manifest`**. Evidence writeup: `abapobjectscreation/knowledge/config_frontier_extraction_2026-06-19.md`.

## Verdicts (MEASURED on P01 client 350)

| Brain item | Verdict | Key golden tables |
|---|---|---|
| **HYP-008 / OI-FI-01** doc splitting | **OFF** — `FAGL_ACTIVEC`+`FAGL_SPLIT_ACTC` empty, `FAGLFLEXT`/`FMGLFLEXT` empty, `GLT0` populated → **classic G/L**. Method **`Z000000012` does NOT exist** (only std `0000000001`/`0000000012`). No doc-split impact. | `t8g12/20/21/21a/30a`, `fagl_split_fld_s`, manifest empties |
| **F3** new-GL ledger | `t881` defines leading `0L`→FAGLFLEXT but **0 postings**; real parallel ledgers = classic FI-SL (COFIT/GLPCT/FILCT/ECMCT). | `t881`, `t882`, `t882c` |
| **HYP-018 / CLM-012/024** GMDERIVE | Strategy `GMDT` **registered** (`fmderivefuncid`) but `GMGR`/`GMIA` = **0 grants** → GM not productively used. No `GMDT_FIELD`/`GMDT_STEP` tables exist. | `fmderivefuncid`, manifest GM rows |
| **CLM-036 / HYP-003** FMDERIVE 26-step | Config = generic **`TABADR*`** tables, **NOT `FMDT_*`**. Strategy **FMOA** (ICTP+UBO) = **14 steps, 5 custom DRULE**. → "**5** of 26" half-confirmed: **5 matches**, **26 does not** (FMOA=14; largest is `FMYC` env `UNESCO2025-26`=22). Recompute "26" against `tabadrs`. | `tabadrs/sf/st`, `tabadr/h/t`, `fmderive002/003/007`, `fmfmoa*` rule-values |
| **HYP-012** AVC tolerance | BCS AVC **active** (ledger `9H`, 9 FM areas, FY2001+). Limits `buavctolass`: **100% Error** default, **ICTP 80% Warning→100% E**, ZIT3→130% ceiling. **No 50% threshold** — that framing was imprecise. | `buavctolass`, `fmavcldgract/att/gat`, `fmup00/01/02` |

## How to consume
Resolve through `unesco-sap-brain/refs_external.json` → query the golden tables directly (never copy raw). Start from `_config_frontier_manifest`. Update the frontier table in `knowledge/35_recreated_conclusions.md` and close HYP-003/008/012/018 + CLM-012/024/036 + OI-FI-01 with the verdicts above.

> Note: these golden tables + the extraction scripts live under the gitignored `sap_data_extraction/` tree (local-only, regenerable from P01 via the documented scripts). Durability of the data = the golden DB file backup, not git.
