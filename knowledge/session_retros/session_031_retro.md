# Session #031 Retro — Company Code Copy Companion v2 + Blueprint
**Date:** 2026-04-01 to 2026-04-03
**Duration:** ~6 hours across 3 days
**Model:** Opus 4.6 (1M context)

## Accomplished
- **Companion v2** for STEM company code creation (3,684 lines):
  - Updated from 2 transports to 4: D01K9B0CBF (FI, 36/682), D01K9B0F3V (FM, 9/51), D01K9B0F4I (R_RIOS periods, 2/6), D01K9B0F40 (R_RIOS logistics, in progress)
  - 2 Critical Discoveries: missing commitment items (GL→CI gap), missing cost elements (CSKB=0)
  - R_RIOS posting period config analyzed: T001B (UNES+ variant), T010O, T010P (4 language variants)
- **Reverse-engineered 3 previous company code creations** from P01:
  - ICTP (2011, Italy, R_ORSARIA): 8,319 keys, 6 transports, 4 people. ONLY institute with F110 (29 T042I ranking entries)
  - MGIE (2013, India, M_SPRONK): 4,853 keys, 1 transport, 1 person. Manual payments only
  - ICBA (2016, Ethiopia, M_SPRONK): 5,330 keys, 5 transports, 3 people. Manual payments only
- **Full master data comparison via RFC**: CSKB (cost elements), CSKS (cost centers), AUFK (orders), ANLA (assets), KNB1 (customers), LFB1 (vendors), FMCI (commitment items), FMFCTR (fund centers), FMFINT (funds), CEPC (profit centers=0 for all)
- **Payment tier classification**: Tier 1 (ICTP, full F110), Tier 2 (UNES/IIEP partial), Tier 3 (MGIE/ICBA manual)
- **Key finding**: UNESCO does NOT use profit centers (CEPC=0 for all 9 company codes)
- **Key finding**: Cost elements are in CSKB not CSKA. All institutes have ~350-490 cost elements
- **Key finding**: All institutes have 22-26 commitment items — standardized pattern

## What Failed (4 serious errors)
1. **Destroyed correct transport data** — re-extracted E071K for released transports, got 0/0, replaced v1 correct data
2. **Misinterpreted TABKEY language codes** — D/E/F/P in T010P are SPRAS (language), not functional types
3. **False alarm on empty transports** — marked released and in-progress transports as "EMPTY" and "NEEDS VERIFICATION"
4. **Wrong FMIFIIT=0 conclusion for ICBA** — extraction script didn't include ICBA in filter, concluded ICBA shares UNES FM area

## Key Discoveries
- ICTP is the only institute using F110 automatic payments (11,050 F110 transactions 2024-2026)
- MGIE and ICBA use manual payments exclusively (FBZ2, FB60)
- Each institute has its own Controlling Area (KOKRS=BUKRS) and FM Area (FIKRS=BUKRS)
- Cost elements, commitment items, fund centers, funds — ALL created as master data post-transport, never transported
- FMIFIIT extraction script missing ICBA and UIL from filter

## Verification Check
- **Assumption challenged:** FMIFIIT=0 for ICBA means shared FM area → WRONG, extraction gap
- **Gap identified:** T010P TABKEY interpretation not verified against SAP documentation
- **Claim probed:** "D01K9B0CBF has 0 objects" → WRONG, transport was released, E071 cleared

## Pending → Next Session
1. Extract FMIFIIT for ICBA and UIL (add to filter in extract_fmifiit_full.py line 98)
2. Update sap_company_code_copy SKILL.md with blueprint findings
3. Update PMO_BRAIN.md with new items from this session
4. When R_RIOS completes D01K9B0F40, extract its content and update companion
