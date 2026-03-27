# Session #025 Retro — T015L Live Validation: PPC Tables Corrected

**Date:** 2026-03-27
**Duration:** ~2h
**Type:** Live Data Validation
**Session focus:** P01 live query of T015L to validate PPC documentation. PDF tables were completely wrong.

---

## What Was Accomplished

| Area | Achievement |
|------|------------|
| **T015L P01 query** | 73 rows extracted. 8 PPC countries confirmed. Code format completely different from PDF. |
| **8 country tables replaced** | All LZBKZ values from T015L: AE(9), BH(6), CN(3), ID(9), IN(11), JO(10), MA(10), MY(10), PH(5) |
| **2 new NEVER rules** | #9: Never use ISO 20022 codes for T015L/PPC. #10: Never assume AE/BH BAdIs live in P01. |
| **Known failures corrected** | China: slash-notation (/CSTRDR/ etc.), not numeric 001/002/003. |
| **Source docs warning** | 20240321 PDF entry: "ISO codes in PDF are WRONG." |
| **Companion v5→v6** | 8-country tables replaced. Doc vs Reality: T015L CONFIRMED. BAdI table updated. Warning banner. |
| **AE/BH BAdI confirmed absent** | P01 TADIR: Y_IDFI_CGI_DMEE_COUNTRY_AE and _BH do NOT exist in P01. CTS D01 only. |

---

## Key Intelligence

| Finding | Significance |
|---------|-------------|
| T015L LZBKZ = UNESCO-specific codes | NOT ISO 20022. AE0-AE8, BH0-BH5, CN0/1/2 (slash), etc. |
| China = slash-notation | /CSTRDR/, /CCDNDR/, /COCADR/ — PDF 001/002/003 was wrong. |
| AE+BH BAdIs NOT in P01 | Running UTIL fallback in production today. |
| YOPAYMENT_TYPE not in P01 | TABLE_NOT_AVAILABLE. Exists D01 only. |
| T015L key = MANDT+LZBKZ+BLART | No BUKRS column. 73 rows globally. |

---

## PMO Reconciliation
- No new items. **Total: 9 Blocking | 11 High | 40 Backlog = 60 items**

---

## Pending → Next Session
1. Full critical review — validate all process mining findings against live data
2. BCM dual control count re-verification
