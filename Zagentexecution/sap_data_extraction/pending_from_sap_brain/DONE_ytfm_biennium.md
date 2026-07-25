---
# Bus header — contract C-4 v1.1 (sole owner: C0). Derived from the prose below; nothing invented.
msg_type: DONE
request_id: ytfm_biennium
from_project: abapobjectscreation
owner: abapobjectscreation            # not stated verbatim; message is emitted by the golden-DB owner (this repo)
date: 2026-06-09
consumers: [unesco-sap-brain]
system_role: P01                      # "live P01 (client 350) via RFC_READ_TABLE"
closes: ["REQUEST.md"]                # the bare 2026-06-05 REQUEST; that filename carries no topic slug
tables_landed: [ytfm_fund_c5, ytfm_c5, ytfm_output, ytfm_output_t]
row_counts: {ytfm_fund_c5: 16549, ytfm_c5: 3, ytfm_output: 259, ytfm_output_t: 259}   # "~" / drift by a few between live reads
how_to_consume: "Regenerate ysfm_fund_c5 FROM the golden DB with the join in section 'Regeneration query'. Honor the raw zero-padded NUMC convention (FM_OUTPUT='0000000068') and SPRSL='E'. ODESC is intentionally absent (STRG, unreadable by RFC_READ_TABLE) - do not backfill it from the XLSX."
---

# DONE — 4 YTFM biennium (C/5) tables landed in the golden DB — SAP P01 source only

> **Status:** ✅ COMPLETE · **Date:** 2026-06-09 · **For:** `unesco-sap-brain`
> **Golden DB:** `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`
> **Extractor (re-runnable):** `scripts/extraction/p01_ytfm_biennium_sync.py`
> **Source:** **live P01** (client 350) via `RFC_READ_TABLE` — same mechanism as `ytfm_fund_cpl`.
> **Excel is NOT a source.** The reference XLSX in this folder were used only to confirm
> structure; **no data was taken from them.** Every stored value comes from SAP P01.

## Domain
**FM / Budget (Funds Management, PSM-FM)** — UNESCO's custom public-sector C/5 (Programme &
Budget biennium) classifier. NOT BCM. Evidence: the maintaining custom solution is function
group `Y_FM_BAPI` / `Y_FM_FUND_MANAGEMENT`, `tfdir_custom.APP_DOMAIN='FM/Budget'`
(`Y_BAPI_FUND_C5_ASSIGNMENT`, `Y_FM_UPDATE_FUND_C5`, `Y_BAPI_OUTPUT_*`).

## What landed (lowercase, raw P01 mirror)

| golden table | rows (P01, live) | columns (PK in **bold**) |
|---|---|---|
| `ytfm_fund_c5` | ~16,549 | **FIKRS**, **FINCODE**, **C5_ID**, C5_SEL, FM_OUTPUT |
| `ytfm_c5` | 3 | **C5_ID**, YEAR_FROM, YEAR_TO, YCHK_OUTPUT |
| `ytfm_output` | 259 | **FM_OUTPUT**, ZZSECT, ORANK, OTYPE |
| `ytfm_output_t` | 259 | **SPRSL**, **FM_OUTPUT**, ONAME, OTEXT |

`ytfm_c5`: `41`=2022-2023, `42`=2024-2025 (YCHK_OUTPUT=X), `43`=2026-2027 (YCHK_OUTPUT=X).
(Row counts are from a live prod system and drift by a few between reads — re-run the extractor for exact current counts.)

## ⚠️ Conventions to honor when regenerating `ysfm_fund_c5` from the golden DB

1. **NUMC columns are ZERO-PADDED, raw** (golden-DB convention, e.g. `ytfm_wrttp_gr.SEQNR='00'`):
   - `FM_OUTPUT` = `'0000000068'`, **not** `'68'`. Joins as-is across the three tables.
   - Display short form with `CAST(FM_OUTPUT AS INTEGER)`. `YEAR_FROM/YEAR_TO/ORANK` likewise raw NUMC.
2. **`SPRSL` is SAP-internal `'E'`** (not ISO `'EN'`). Filter `WHERE SPRSL='E'` for English. (P01 has only `E`.)
3. **Full table, no FM-area filter** — `ytfm_fund_c5` holds all FM areas in P01
   (IBE, ICBA, ICTP, IIEP, MGIE, UBO, UIL, UIS, UNES). Filter to your scope yourself.
4. **Derived/joined columns were dropped** — the XLSX `Name`, `Output name`, `Output text`,
   `FM Output description` are NOT raw SAP columns; reconstruct them via the join below.

## ‼️ ODESC is intentionally NOT in the golden DB (and not in Excel either)

`YTFM_OUTPUT_T.ODESC` (the long description) is DDIC type **`STRG` (string)**, which
**`RFC_READ_TABLE` cannot read**. Every SAP-native channel that could read it was checked and is
unavailable for this user on P01:
- `RFC_ABAP_INSTALL_AND_RUN` on P01 → **no authorization** (prod is locked, SNC/SSO).
- ADT-HTTP on P01 → **no password** (SNC/SSO only; port-8000 ICF not usable without SSO-over-HTTP).
- **D01 is not a valid substitute** — D01 `YTFM_OUTPUT_T` diverges from P01 (253 vs 259 rows; the 6
  new `43 C/5` FLD staff outputs `0000003129`–`0000003134` exist only in P01, and 5 common rows have
  different ONAME/OTEXT). The table is maintained directly in P01, not transported.
- No custom RFC-enabled **read** FM exists (only write/assignment BAPIs in `Y_FM_BAPI`).

**Therefore `ODESC` is omitted.** The SAP-readable text is stored instead: `ONAME` (CHAR20) and
`OTEXT` (CHAR40). For most outputs OTEXT == the full text; it is truncated only for descriptions
> 40 chars. To obtain ODESC you would need P01 `S_DEVELOP`/ADT authorization, or a new custom
RFC-enabled read FM on the `YTFM_*` solution. **Do not backfill ODESC from the XLSX.**

## Known, documented data fact (not an error)
- **`FM_OUTPUT='0000000000'` on ~134 `ytfm_fund_c5` rows** = fund×biennium with **no C/5 Output
  assigned yet** (unclassified). No match in `ytfm_output` by design; ~99.2% carry a real output.

## Regeneration query (golden DB → your `ysfm_fund_c5`)

```sql
SELECT f.FIKRS, f.FINCODE, f.C5_ID,
       c.YEAR_FROM, c.YEAR_TO,
       f.C5_SEL, f.FM_OUTPUT,
       o.ZZSECT  AS functional_area,
       t.ONAME, t.OTEXT
FROM ytfm_fund_c5 f
JOIN ytfm_c5  c ON c.C5_ID = f.C5_ID
LEFT JOIN ytfm_output   o ON o.FM_OUTPUT = f.FM_OUTPUT
LEFT JOIN ytfm_output_t t ON t.FM_OUTPUT = f.FM_OUTPUT AND t.SPRSL = 'E';
```

The 4 reference XLSX in this folder are now obsolete (golden DB = single source). They were left in
place because they belong to `unesco-sap-brain`; that project should remove its own copies.
