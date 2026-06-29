---
name: Cost Recovery Analysis 2025
description: Personal cost recovery posting analysis for UNESCO — 4,211 docs, 3 company codes (IIEP/UNES), 3 streams, complete posting schema documented.
type: project
---

## Cost Recovery 2025 — Summary

**4,211 documents / 8,490 GL lines** across 2 company codes.

### Three Streams by BKTXT
| Stream | BUKRS | BLART | Docs | Revenue GL |
|--------|-------|-------|-----:|-----------|
| STAFF COST RECOVERY 2025 | IIEP | JV | 1,447 | 7034011 |
| ITF/COST RECOVERY 2025 | IIEP | R1 | 794 | 7022020 |
| Cost Recovery (field) | UNES | R1 | 1,964 | 7046013 |

### Posting Pattern (every doc)
Line 1: PK=40 DEBIT GL 6046013 (staff) or 6046014 (consultants) → charges project fund
Line 2: PK=50 CREDIT GL 70xxxxx (revenue) → recovers to receiving pool

### Key Dimensions
- **FISTL** routing differs: UNES field = same office both sides; IIEP = TEC/KMM/TRA→ADM receives
- **GSBER**: UNES always PFF(debit)/OPF(credit); IIEP = PDK/PAR/IBA
- **633CRP9003** is the shared CRP pool for all UNESCO (87 offices book to it)
- **Staff vs Consultants**: IIEP 94%/6%, UNES Field 72%/28%

### Scripts
- `cost_recovery_analysis.py` — Full analysis by segment
- `enrich_bsis_bsas_fields.py` — KOSTL enrichment for BSIS/BSAS
- `enrich_fmifiit_objnrz.py` — OBJNRZ (WBS) enrichment for FMIFIIT

---

## FI Document Number-Range Bands (RF_BELEG, P01 — claim #281)

Verified across 1,826,719 BKPF rows. High 9x bands in use:

| Band | Range | BLART | Use |
|------|-------|-------|-----|
| 90 | 9000000000-9199999999 | R1 | Cost recovery (ITF/field) — 2026 max ~9000007720 UNES |
| 92 | 9200000000-9299999999 | JV | Staff cost recovery — 2026 max ~9200020727 UNES |
| 93 | — | IO | — |
| 94 | — | OF | — |
| 95 | — | IT | — |
| 98 | — | R8 | — |

**FREE bands: 91, 96, 97, 99.**

**Recommendation for a new cost-recovery doc type:** use band **96** (9600000000-9699999999) — isolated from R1 (band 90) and JV (band 92).

**Transport note:** NRIV/FBN1 intervals are NOT transported (NROB transports the object definition only). Intervals must be created manually per client. Only T003 (doc-type definition) transports.

---

## R1 Account Validation (GB901, company code UNES — claim #282)

The FI validation controlling cost-recovery R1 postings (GGB0/OB28, line-item callup point) is stored in GB901:

- **Prerequisite** `2UNES###006`: `BKPF-BLART = 'R1'` (fires only for R1 literally)
- **Account check** `1UNES###006`: `BSEG-HKONT IN`:
  - `6046012–6046020` (staff/consultant cost debit)
  - `7034011–7034013` (IIEP revenue credit)
  - `7046012–7046014` (UNES field revenue credit)

**Design implication:** any new BLART (e.g. a JV-copy for cost recovery) bypasses this validation unless step `2UNES###006` is extended in GGB0 to include the new BLART. The account ranges align with the posting pattern: debit 6046013/6046014, credit 7034011/7046013.

Evidence: `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db` tables GB901 + GB903, session s-2026-06-29.
