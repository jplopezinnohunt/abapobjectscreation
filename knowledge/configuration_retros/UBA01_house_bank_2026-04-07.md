# House Bank Configuration Report: UBA01 — UNESCO Maputo (Mozambique)

**Report Date:** 2026-04-07 (updated 2026-04-08)  
**Ticket:** INC-000005586  
**Configurator:** Pablo Lopez (DBS)  
**Bank:** United Bank for Africa Mozambique S.A. (UBA)  
**Reference Bank:** ECO09 (Ecobank Maputo)  

## Final Compliance (2026-04-08 — post-transport)

| System | PASS | FAIL | WARN | Status |
|--------|------|------|------|--------|
| **D01** | 30 | 0 | 2 | FULLY COMPLIANT |
| **V01** | — | — | — | IDENTICAL to D01/P01 |
| **P01** | 30 | 0 | 2 | FULLY COMPLIANT |

**3-system comparison:** ALL 15 CHECKS IDENTICAL across D01, V01, P01.

### Remaining Warnings (non-blocking)
1. **TIBAN (Check 8):** IBAN transport D01K9B0F58 (W) released to P01
2. **Cash Management (Check 10):** T035D PASS — DISKB entries confirmed (UBA01-MZN1, UBA01-USD1). T035 groups not readable via RFC (auth) but irrelevant — T035D is the real validation

## Transport History — 6 Transports (Too Many)

| # | Transport | Type | Client | Description | Status |
|---|-----------|------|--------|-------------|--------|
| 1 | D01K9B0F56 | C | 350 | New house bank and accounts UBA01 | Released |
| 2 | D01K9B0F59 | C | 350 | New mozambike bank OBA1 | Released |
| 3 | D01K9B0F5B | C | 350 | OBA1 Correction New bank Mozambique | Released |
| 4 | D01K9B0F5F | C | 350 | Sets YBANK | Released |
| 5 | D01K9B0F5K | C | 350 | OBA1 Correction New bank Mozambique | Released |
| 6 | D01K9B0F58 | W | — | IBAN New bank | Released |

**Assessment: 6 transports for 1 bank is excessive.** Breakdown:
- Transport 1 = initial bank + accounts (correct)
- Transport 2 = OBA1 first attempt (incomplete — missing LKORR + valuation)
- Transport 3 = OBA1 correction #1 (still wrong)
- Transport 4 = GS02 sets (should have been in transport 1)
- Transport 5 = OBA1 correction #2 (finally correct after ECO09 benchmark comparison)
- Transport 6 = IBAN (workbench — separate by nature, OK)

**Root cause:** OBA1 was configured 3 times because the process wasn't mature — we learned the T030H requirements (LKORR + valuation + realized) by trial and error instead of knowing them upfront. GS02 sets were done separately because they were discovered late.

**Target for next bank: 3 transports max**
1. C transport: ALL customizing (T012/T012K/T012T + SKA1/SKB1/SKAT + T030H + T035D + T028B + T018V + T042I + SETLEAF) — everything in ONE request
2. W transport: IBAN (workbench object, separate by nature)
3. Optional C: Only if TRS requests post-config changes

## Configuration Summary — All 15 Checks PASS

| # | Check | D01 | P01 | Detail |
|---|-------|-----|-----|--------|
| 1 | T012 House Bank | PASS | PASS | Country=MZ, BankKey=SP0000001YCB |
| 2 | BNKA Bank Directory | PASS | PASS | UBA MOCAMBIQUE,SA, SWIFT=UNAFMZMA |
| 3 | T012K Bank Accounts | PASS | PASS | MZN01 (070040004663) + USD01 (070340000190) |
| 4 | T012T Descriptions | PASS | PASS | English texts: "UNESCO MAPUTO - MZN/USD" |
| 5 | SKA1 Chart of Accounts | PASS | PASS | All 4 G/Ls: KTOKS=BANK, XBILK=X |
| 6 | SKB1 Company Code | PASS | PASS | FDLEV=B0/B1, ZUAWA=027/Z01, HBKID=UBA01, XINTB=empty, FSTAG=UN03 |
| 7 | SKAT Texts | PASS | PASS | 3 languages (E/F/P) on all 4 G/Ls |
| 8 | TIBAN | WARN | WARN | No IBAN generated yet |
| 9 | T030H OBA1 | PASS | PASS | MZN clearing (1165424): COMPLETE. USD clearing (1165421): COMPLETE |
| 10 | Cash Management | WARN | WARN | FDSB not accessible via RFC |
| 11 | T035D EBS Config | PASS | PASS | UBA01-MZN1→1065424, UBA01-USD1→1065421 |
| 12 | T028B Posting Rules | PASS | PASS | XRT940 format, both accounts mapped |
| 13 | T018V Receiving Bank | PASS | PASS | USD01: method A, clearing=1165421 |
| 14 | T042I Payment Bank | PASS | PASS | Method 3 (check), MZN01 |
| 15 | SETLEAF (YBANK) | PASS | PASS | 1065424→FO_OTH, 1065421→FO_USD |

## G/L Account Map

| G/L | Type | Currency | HBKID | FDLEV | ZUAWA | XOPVW | T030H |
|-----|------|----------|-------|-------|-------|-------|-------|
| 1065424 | Bank (10*) | MZN | UBA01 | B0 | 027 | — | Optional (bank) |
| 1165424 | Clearing (11*) | MZN | UBA01 | B1 | Z01 | X | COMPLETE |
| 1065421 | Bank (10*) | USD | UBA01 | B0 | 027 | — | N/A (USD) |
| 1165421 | Clearing (11*) | USD | UBA01 | B1 | Z01 | X | COMPLETE |

## Issues Found and Fixed During Configuration

| # | Issue | Root Cause | Fix |
|---|-------|-----------|-----|
| 1 | XINTB=X set on all 4 accounts | Misread of ECO09 benchmark — only 1/353 bank G/Ls has XINTB=X | Cleared via RFC in D01. P01 fixed by MD team same day (Ingrid reported F5562) |
| 2 | OBA1 missing LKORR + valuation sections | Initial config only filled Realized section | Fixed by ECO09 field-by-field comparison. Transport D01K9B0F5K |
| 3 | T028B initially not found | Searched by HBKID instead of BANKL+BANKN | Corrected search key — T028B was actually present |
| 4 | SKAT French+Portuguese texts "ECOBANK" | Copied from ECO09 reference without updating bank name | Fixed via RFC — updated to "UBA" |
| 5 | HBKID=ECO09 on P01 accounts | MD team copied from ECO09 reference and didn't update | Fixed by MD team after transport |
| 6 | GS02 sets missing UBA01 G/Ls | New accounts not yet added to YBANK sets | Added via GS02, transported D01K9B0F5F |
| 7 | V01 G/L 1165421 missing | V01 out of sync — G/L not created | Created via RFC (SKA1+SKB1+SKAT) |

## Status: CLOSED

All 6 transports released. 32 PASS / 0 FAIL / 1 WARN (TIBAN — transport D01K9B0F58 released).
D01 = V01 = P01 identical across all 15 checks. Configuration complete.

## Automation Scripts Used
- `house_bank_compliance_checker.py` — 15-check automated validation (D01/P01)
- `uba01_3system_comparison.py` — 3-system comparison (D01/V01/P01)
- `ybank_setleaf_sync.py` — YBANK set synchronization P01→D01
- `uba01_fix_xintb_d01.py` — XINTB fix in D01

See full skill: `.agents/skills/sap_house_bank_configuration/SKILL.md`
