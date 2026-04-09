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
