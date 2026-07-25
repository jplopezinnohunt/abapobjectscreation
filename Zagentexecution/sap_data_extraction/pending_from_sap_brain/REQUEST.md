---
# Bus header — contract C-4 v1.1 (sole owner: C0). Derived from the prose below; nothing invented.
msg_type: REQUEST
request_id: ytfm_biennium             # filename carries NO topic slug; id taken from the answering DONE_ytfm_biennium.md
from_project: unesco-sap-brain
date: 2026-06-05
status: RESOLVED                      # answered by DONE_ytfm_biennium.md (2026-06-09); this file was NOT renamed
why: "Single-source-of-truth rule - raw SAP table data must live ONLY in the golden DB, not duplicated in the brain. These 4 tables exist only in unesco-sap-brain and are missing from p01_gold_master_data.db."
resource_requested: "Add the 4 YTFM C/5 (biennium) tables to the FM extraction pipeline and land them in p01_gold_master_data.db"
extract_spec:
  - source_table: YTFM_FUND_C5
    keys: [FIKRS, FINCODE, C5_ID, C5_SEL, FM_OUTPUT]
  - source_table: YTFM_C5
  - source_table: YTFM_OUTPUT
  - source_table: YTFM_OUTPUT_T
consumers:
  - "unesco-sap-brain/artifacts/build-biennium-conversion.js"
  - "unesco-sap-brain/knowledge/24"
  - "unesco-sap-brain/knowledge/25"
  - "unesco-sap-brain/knowledge/27"
  - "unesco-sap-brain /tools/biennium.html"
resolve_via: UNKNOWN                  # this message states no resolve_via line (every later REQUEST does)
---

# Request: add 4 YTFM (biennium) tables to the golden DB — FM / Fund Management domain

> **From:** `unesco-sap-brain` project · **Date:** 2026-06-05
> **Why:** Single-source-of-truth rule — raw SAP table data must live ONLY here (the golden DB),
> not duplicated in the brain. These 4 tables are currently **only** in `unesco-sap-brain` and are
> **missing** from `p01_gold_master_data.db`. Please incorporate them into the extraction pipeline
> (FM / Fund Management domain) so the golden DB becomes the complete single source.

## What the golden DB already has vs. what's missing
`p01_gold_master_data.db` HAS `ytfm_fund_cpl` (cols FIKRS, FINCODE, ALINE, NONIBF) — but it does **NOT**
have the **biennium classification** tables below. They are a different YTFM family (C/5 = biennium).

## The 4 tables to add (XLSX provided in this folder as reference data)
| Table | Cols (key) | Rows (≈) | What it is |
|---|---|---|---|
| **YTFM_FUND_C5** | `FIKRS, FINCODE, C5_ID, C5_SEL, FM_OUTPUT` | ~15,685 | The **fund × biennium** classifier — which C/5 biennium (C5_ID 41/42/43) each FINCODE belongs to, + its C/5 Output (Functional Area). The backbone of the brain's biennium analysis. |
| **YTFM_C5** | biennium dimension | 3 | The C/5 biennium master (41=2022-23, 42=2024-25, 43=2026-27). |
| **YTFM_OUTPUT** | C/5 Output code | ~ | C/5 Expected Result / Output codes (→ Functional Area). |
| **YTFM_OUTPUT_T** | C/5 Output text | ~ | Text/descriptions for the C/5 Outputs. |

## Suggested action
1. Add `YTFM_FUND_C5`, `YTFM_C5`, `YTFM_OUTPUT`, `YTFM_OUTPUT_T` to the RFC extraction (FM domain)
   — same mechanism as the existing `ytfm_fund_cpl` / `ytfm_wrttp_gr`.
2. Land them in `p01_gold_master_data.db` (lowercase table names to match convention).
3. Once present in the golden DB, `unesco-sap-brain` will regenerate its derived `ysfm_fund_c5`
   table FROM the golden DB instead of from the now-removed XLSX.

## Consumers in unesco-sap-brain (so you know the impact)
- `artifacts/build-biennium-conversion.js` (the biennium conversion tool data)
- `knowledge/24`, `knowledge/25` (migration plan), `knowledge/27` (fund simplification)
- the deployed `/tools/biennium.html`

The 7 other raw tables the brain had (csks, FMAVCT, FMFINCODE→funds, FMFCTR→fund_centers, proj, PRPS,
YTFM_FUND_CPL) already exist in the golden DB, so those XLSX are being **removed** from the brain
(no action needed here for them).
