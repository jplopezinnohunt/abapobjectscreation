# Session Learning: Company Code Copy Companion v2
**Date:** 2026-04-01 to 2026-04-03
**Project:** SAP Intelligence Platform (abapobjectscreation)
**Session focus:** Transport companion for STEM company code creation + reverse engineering of 3 previous company codes (ICTP, MGIE, ICBA)

## ❌ Error 1: Destroyed correct data with re-extraction of released transports
**What I did:** Re-ran RFC extraction on E071/E071K for D01K9B0CBF and D01K9B0F3V, got 0/0, and REPLACED the original correct data (36/682 and 9/51) with the wrong 0/0.
**Why it failed:** SAP clears E071/E071K after transport release. The v1 companion had the data extracted when transports were still modifiable. Re-extracting released transports returns empty.
**Fix:** Restored v1 data. Added note explaining released transport behavior.
**Lesson:** NEVER re-extract transport contents that were already captured. Released transports clear E071/E071K. Previous extraction = source of truth.
**Cost:** ~2h debugging, multiple companion rewrites, user frustration

## ❌ Error 2: Misinterpreted SAP TABKEY language codes as functional types
**What I did:** Interpreted T010P TABKEYs 350DSTEM/350ESTEM/350FSTEM/350PSTEM as D=standard posting period, E=special period, F=fiscal year change, P=posting period.
**Why it failed:** D/E/F/P are SAP language keys (Deutsch/English/French/Portuguese). These are posting period variant DESCRIPTIONS in 4 languages, not 4 different period types.
**Fix:** Corrected to language key interpretation.
**Lesson:** In SAP TABKEYs, single-letter prefixes before MANDT+BUKRS are almost always SPRAS (language keys). Common: D=German, E=English, F=French, P=Portuguese, S=Spanish.
**Cost:** Wrong analysis in companion, had to correct

## ❌ Error 3: Created false alarms for transports in progress
**What I did:** Marked D01K9B0F40 (logistics) as "EMPTY — logistics not yet configured" with red WARNING styling. Marked D01K9B0F3V as "NEEDS VERIFICATION".
**Why it failed:** D01K9B0F40 is a new transport R_RIOS is actively working on — "0 objects" just means it's in progress, not failed. D01K9B0F3V was already released (0/0 is normal).
**Fix:** Changed to neutral "in progress" language. Removed false alarms.
**Lesson:** A transport with 0 objects can mean: (a) released (E071 cleared), (b) in progress (not yet configured), or (c) actually empty. Don't alarm without knowing which.
**Cost:** ~1h, user frustration

## ❌ Error 4: FMIFIIT=0 for ICBA claimed as "shares FM with UNES"
**What I did:** Saw FMIFIIT=0 for ICBA in Gold DB and concluded ICBA shares UNES FM area for postings. Built an elaborate "Discovery #10" around this.
**Why it failed:** The extraction script `extract_fmifiit_full.py` line 98 filters by 7 FM areas — ICBA and UIL were not in the filter. The 0 was an extraction gap, not a real finding.
**Fix:** FM consultant confirmed all institutes have their own FM area. Corrected the companion.
**Lesson:** ALWAYS check extraction script filters before claiming "0 rows = no data exists". This is the same mistake as FEBEP=0 in Session #029.
**Cost:** Wrong conclusion shared with team, credibility hit

## ✅ Pattern 1: Reverse-engineering company code creation from E071K
**What worked:** Querying E071K WHERE OBJNAME='T001' to find all transports that created company codes, then parsing TABKEY[3:7] to extract BUKRS.
**Why it works:** E071K TABKEYs for T001 contain MANDT(3)+BUKRS(4). Cross-referencing with E070 dates gives creation timeline.
**Reuse:** For any "when was this object created?" question, E071K TABKEY parsing + E070 date = creation history.

## ✅ Pattern 2: Gold DB + RFC hybrid approach
**What worked:** Using Gold DB for master data counts (BKPF, BSAK, EKKO, T012K, T042I) and RFC only for tables not in Gold DB (CSKS, CSKB, AUFK, ANLA, KNB1, LFB1, FMCI, FMFCTR).
**Why it works:** Gold DB already has 52 tables extracted. Only go to RFC for what's missing.
**Reuse:** Always check Gold DB first. RFC = last resort for missing data.

## ✅ Pattern 3: 3-company blueprint comparison reveals patterns
**What worked:** Comparing ICTP (2011), MGIE (2013), ICBA (2016) revealed: F110 is not universal (only ICTP), cost elements/commitment items are ALWAYS master data (never transported), profit centers not used, payment tiers exist.
**Why it works:** Real production data from 3 different creations over 5 years gives statistical weight to conclusions.
**Reuse:** When evaluating any new SAP configuration, compare against 2-3 existing similar objects in production.

## ✅ Pattern 4: CSKB not CSKA for cost elements
**What worked:** CSKA returned 0 for all controlling areas. CSKB (time-dependent master data) returned the real cost elements: UNES=493, ICTP=368, MGIE=362, ICBA=357.
**Why it works:** CSKA is the header table, CSKB is the time-dependent detail. RFC_READ_TABLE on CSKA may return 0 if the table structure is complex. CSKB always works.
**Reuse:** For cost elements, always query CSKB not CSKA.

## Promote to Central?
- [x] Qualifies — Released transport re-extraction rule is critical for any SAP transport analysis
- [x] Qualifies — TABKEY language code interpretation prevents recurring misinterpretation
- [ ] Proposed in priority-actions.md
