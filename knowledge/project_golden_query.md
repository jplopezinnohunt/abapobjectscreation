---
name: Golden Query - BKPF + bseg_union + FMIFIIT + PRPS
description: The canonical JOIN for FI document analysis combining GL lines, FM assignment, and WBS element. Validated at 100% match rate.
type: project
---

## The Golden Query

Combines all FI document data into one view: header + GL line + FM assignment + WBS element.

```sql
SELECT
  -- Header (BKPF)
  b.BUKRS, b.BELNR, b.GJAHR, b.BLART, b.BKTXT, b.XBLNR, b.BUDAT, b.MONAT, b.USNAM, b.TCODE,
  -- GL Line (bseg_union = BSIS ∪ BSAS ∪ BSIK ∪ BSAK ∪ BSID ∪ BSAD)
  u.BUZEI, u.BSCHL, u.HKONT, u.SHKZG, u.DMBTR, u.WRBTR, u.WAERS, u.GSBER, u.KOSTL, u.AUFNR,
  u.source_table,
  -- FM (FMIFIIT)
  f.FISTL, f.FONDS, f.FIPEX, f.FKBTR, f.WRTTP, f.VRGNG, f.GRANT_NBR, f.OBJNRZ, f.SGTXT,
  -- WBS Element (PRPS via OBJNRZ)
  p.POSID AS WBS_ELEMENT, p.POST1 AS WBS_DESCRIPTION
FROM bseg_union u
  JOIN bkpf b     ON u.BUKRS = b.BUKRS AND u.BELNR = b.BELNR AND u.GJAHR = b.GJAHR
  LEFT JOIN fmifiit_full f ON u.BUKRS = f.BUKRS AND u.BELNR = f.KNBELNR
                           AND u.GJAHR = f.KNGJAHR AND u.BUZEI = f.KNBUZEI
  LEFT JOIN prps p ON f.OBJNRZ = p.OBJNR
```

## JOIN Keys
- `bseg_union → bkpf`: BUKRS + BELNR + GJAHR
- `bseg_union → fmifiit_full`: BUKRS + BELNR=KNBELNR + GJAHR=KNGJAHR + BUZEI=KNBUZEI
- `fmifiit_full → prps`: OBJNRZ = OBJNR

## Field Coverage (cost recovery 2025, 8,490 lines)
| Field | Coverage | Source |
|-------|----------|--------|
| BSCHL (Posting Key) | 100% | bseg_union |
| GSBER (Business Area) | 99.9% | bseg_union |
| FISTL (Fund Center) | 90.5% | FMIFIIT |
| FONDS (Fund) | 90.5% | FMIFIIT |
| WBS_ELEMENT | 85.9% | PRPS via OBJNRZ |
| KOSTL (Cost Center) | 4.6% | bseg_union |

The 9.5% gap = BSAS clearing lines (intercompany GL 5098030/5098011) — no FM assignment by design.

## LEFT JOIN is mandatory
BSAS/BSAK clearing lines have no FM data. Use LEFT JOIN for FMIFIIT and PRPS, never INNER JOIN.

## Why:**
Built during Session #016. Previously we were joining only BKPF+FMIFIIT and missing BSCHL, GSBER, KOSTL from the GL side. The full union of all 6 secondary index tables + FMIFIIT + PRPS gives the complete picture.
