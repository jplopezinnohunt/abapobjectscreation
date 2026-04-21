# UNESCO SAP Knowledge: Bank Statement & EBS Architecture

**Source**: BFM/TRS Handover Documentation (11 Word docs + 3 Excels) + Gold DB analysis + P01 config extraction
**Session**: #029 (2026-03-31)
**Companion**: payment_bcm_companion.html (Bank Recon tab)
**Related**: payment_full_landscape.md, basu_mod_technical_autopsy.md, sap_custom_enhancement_registry.md

---

## PART A — Configuration (How It SHOULD Work)

### 1. E2E Bank Statement Lifecycle

```
INBOUND (Bank → SAP):
┌──────────┐    ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐
│ Bank     │    │ SWIFT / SIL  │    │ SAP EBS Import   │    │ FI Posting   │
│ MT940    │───>│ File Transfer│───>│ FF_5 (JOBBATCH)  │───>│ Z1 doc →     │
│ Statement│    │ 3 min poll   │    │ Auto-import 91%  │    │ BKPF + BSIS  │
└──────────┘    └──────────────┘    └──────────────────┘    └──────┬───────┘
                                                                   │
    EBS PROCESSING CHAIN:                                          │
    MT940 Tag 86 ─→ External Transaction Code ─→ Algorithm ─→     │
    Search String Match ─→ Posting Rule ─→ Account Symbol ─→      │
    GL Account + Business Area ─→ Z1 Document                     │
                                                                   │
RECONCILIATION:                                                    ▼
┌──────────────────┐    ┌──────────────┐    ┌───────────┐    ┌──────────┐
│ Automatic Clear  │    │ FEBAN/FB05   │    │ BSAS      │    │ Matched  │
│ (search strings  │───>│ Z7 clearing  │───>│ cleared   │───>│ Recon OK │
│  match payment)  │    │ doc created  │    │ items     │    │          │
└──────────────────┘    └──────────────┘    └───────────┘    └──────────┘
         │                                                         ▲
         │ no match                                                │
         ▼                                                         │
┌──────────────────┐    ┌──────────────┐                          │
│ Post to 11xxxxx  │    │ Manual FEBAN │                          │
│ Sub-bank account │───>│ post-process │──────────────────────────┘
│ (open item)      │    │ (T_ENG etc.) │
└──────────────────┘    └──────────────┘
```

### 2. MT940 Import Architecture

| Component | Detail |
|-----------|--------|
| **Format** | MT940 (SWIFT standard) text file |
| **Transport** | SWIFT Alliance Lite2 (Java 7.51-55) via SIL |
| **Polling** | HQ: 3 minutes / UIL, UBO: 15 minutes |
| **Directory** | Bank files: `\\hq-sapitf\SWIFTS\output\*` |
| **FEBV_FILEPATH** | `Z_EBS_PRO` (process), `Z_EBS_ARC` (archive), `Z_EBS_ERR` (error), `Z_EBS_TRA` (transfer) |
| **File naming** | `OSOGEFRPPXXX_<CCODE>_<BANK_ID>_<ACCOUNT_ID>_<STMT_DATE>` |
| **Import TCode** | FF_5 / FF.5 (Electronic Bank Statement upload) |
| **Automation** | 91.2% by JOBBATCH (automated background job) |
| **Volume** | ~100+ statements daily (per documentation) |
| **Document type** | Z1 (bank statement posting) |

### 3. GL Account Structure

The GL account ranges define the bank statement posting architecture:

| Range | Symbol | Purpose | Status |
|-------|--------|---------|--------|
| **10xxxxx** | `BANK` | Main bank account (from T012K.HKONT) | Active |
| **11xxxxx** | `BANK_SUB` | Sub-bank clearing/offsetting account | Active |
| **12xxxxx** | `BANK_TECH` | Technical bank account (legacy) | **Phasing out** |
| **13xxxxx** | `OFFSET_TECH_SUB` | Technical sub-bank offset (legacy) | **Phasing out** |

**Symbol-to-Account Mapping Logic:**
- `+` = same digit as reference account (from T012K)
- Specific digit = fixed, doesn't depend on reference

Example: Bank account CIT04-USD04 with reference GL 1043011:
- Symbol `BANK` with `++++++++++` → posts to `0001043011`
- Symbol `BANK_SUB` with `+++11+++++` → posts to `0001143011` (11 replaces 04 in positions 4-5)

### 4. EBS Posting Rules

| Posting Rule | Posting Area | Debit PK | Debit Symbol | Credit PK | Credit Symbol | Doc Type | Post Type | Description |
|-------------|-------------|----------|-------------|-----------|--------------|----------|-----------|-------------|
| **101I** | 1 | 40 | BANK | 50 | BANK_SUB | Z1 | 1 | Incoming GL sub bank posting |
| **101O** | 1 | 40 | BANK_SUB | 50 | BANK | Z1 | 1 | Outgoing GL sub bank posting |
| **102I** | 1 | 40 | BANK | — | BANK_SUB | Z1 | 5 | Incoming GL sub bank clearing |
| **102O** | 1 | — | BANK_SUB | 50 | BANK | Z1 | 4 | Outgoing GL sub bank clearing |
| **110I** | 1 | 40 | BANK | 50 | CHARGES | Z1 | 1 | Bank charges incoming |
| **110O** | 1 | 40 | CHARGES | 50 | BANK | Z1 | 1 | Bank charges outgoing |
| **111I** | 1 | 40 | BANK | 50 | INTEREST | Z1 | 1 | Interest incoming |
| **111O** | 1 | 40 | INTEREST | 50 | BANK | Z1 | 1 | Interest outgoing |
| **201I** | 1 | 40 | BANK | — | CUSTOMER | Z1 | 1 | Customer posting incoming |
| **201O** | 1 | — | CUSTOMER | 50 | BANK | Z1 | 1 | Customer posting outgoing |
| **202I** | 1 | 40 | BANK | — | CUSTOMER | Z1 | 8 | Customer clearing incoming |
| **202O** | 1 | — | CUSTOMER | 50 | BANK | Z1 | 4 | Customer clearing outgoing |
| **999I** | 1 | 40 | BANK | 50 | UNALLOCATED | Z1 | 1 | Unallocated incoming |
| **999O** | 1 | 40 | UNALLOCATED | 50 | BANK | Z1 | 1 | Unallocated outgoing |

**Posting Types:**
- Type 1 = Post on G/L account (no clearing)
- Type 4 = Clear Debit G/L account
- Type 5 = Clear (mixed — debit or credit)
- Type 8 = Clear Credit sub-ledger account

### 5. External Transaction Codes by Bank

#### Société Générale France (SOG01/SOG03)
| Ext Code | Meaning | Typical Rule | Algorithm |
|----------|---------|-------------|-----------|
| NCHG | Charges | 101I/101O | 000 |
| NCHK | Check | 101I/102O | 013 |
| NCLR | Clearing | 101I/102O | 015 |
| NCOL | Collection | 101I/101O | 000 |
| NMSC | Miscellaneous | 101I/101O | 000 |
| NRTI | Return interest | 101I/101O | 000 |
| NTRF | Transfer | 101I/102O | 015 |

#### Citibank (CIT04/CIT21)
| Ext Code | Meaning | Typical Rule | Algorithm |
|----------|---------|-------------|-----------|
| FCHG | Charges | 101I/101O | 000 |
| FCLR | Clearing | 101I/102O | 015 |
| FDDT | Direct debit | 101O | 000 |
| FINT | Interest | 111I/111O | 000 |
| FRTI | Return interest | 101I/101O | 000 |
| FTRF | Transfer | 101I/102O | 015 |
| S202 | Worldlink payment | 102O | 019 |

#### CPS Format (DECOMMISSIONED)
Codes N195, N495, N275, N469, N575, N475, N175, NCOL, NCLR — no longer used.

### 6. Interpretation Algorithms

| Algorithm | Name | Logic |
|-----------|------|-------|
| **000** | No interpretation | Post directly, no matching attempted |
| **001** | Standard | Standard algorithm |
| **013** | Check number match | Outgoing check: check number = or <> payment doc number |
| **015** | Clearing by assignment | Selection using assignment field (ZUONR) — matches payment docs |
| **019** | DME file matching | Matches by DME file reference number — for bulk payments |

### 7. Search String Matching (Automatic Clearing Engine)

The search strings parse MT940 Tag 86 (note-to-payee) to extract payment references for auto-clearing.

| Search String ID | Pattern | Purpose | Banks |
|-----------------|---------|---------|-------|
| **FO_PAYM_DOC** | `31########` | Field office payment doc number (OP docs from online banking) | Field offices |
| **FO_PAYM_POST_RULE** | `(31########)` | Same + replace posting rule with SUBF | Field offices |
| **SOG03_PAYM_DOC** | `(/2######/)`, `(/2 ######/)` | F110 generated payment doc numbers | SOG01/SOG03 |
| **SOG03_STAFF_10XXXXXX** | `(/0(0\|1)#####/)` | Staff number in payroll payment | SOG01/SOG03 |
| **CIT_PAYM_DOC** | `REF 0002######` | Citibank payment document reference | CIT04/CIT21 |
| **CIT_STAFF_0XXXXXX** | `REF 0######` | Citibank staff number | CIT04/CIT21 |
| **SOG_DME** | `PREF/01####` | DME file number (vendor bulk) | SOG01 |
| **SOG_DME_ALG_019** | `PREF/01#####` | DME file number (algorithm 019) | SOG01 |
| **CIT_DME** | `EF/01########-` | DME file number (Citibank) | CIT04 |

**Special characters:** `#` = single digit/character (wildcard), `|` = OR operator

**Search string evaluation order:**
1. More specific criteria given preference
2. Document number matches prioritized over generic number matches
3. If both matches exist, both document number and customer number rules checked
4. Default posting rule from OT83 used if no search string hit

### 8. Business Area Determination

#### Evolution
| Period | Mechanism | Table | Approach |
|--------|-----------|-------|----------|
| Pre-2022 | Hardcoded in user exit | `YBASUBST` | 1:1 GL → BA mapping. BA=X as default for unknowns |
| Post 10/2022 | Range-based substitution | `YTFI_BA_SUBST` | BUKRS + BLART + HKONT ranges → GSBER |

#### Calling Chain
```
FI Document Posting
  → GGB1 Substitution Engine (OBBH)
    → YRGGBS00 (formpool)
      → FORM U910 (Business Area Substitution)
        → YCL_FI_ACCOUNT_SUBST_READ.READ(iv_bukrs, iv_blart, iv_hkont)
          → Lookup 1: BUKRS + BLART + HKONT range → GSBER
          → Lookup 2 (fallback): BUKRS + SPACE (global) + HKONT range → GSBER
```

#### Valid Business Areas (UNES)
| BA | Meaning |
|----|---------|
| GEF | Global Education Fund |
| PFF | Programme Fund |
| OPF | Operations Fund |
| MBF | Medical Benefits Fund |
| X | **Technical/interim** (being phased out — only 54 open items remain) |

#### YBASUBST Entry Format
```
| BUKRS | BLART | HKONT    | GSBER |
|-------|-------|----------|-------|
| UNES  | Z1    | 1094971  | GEF   |  ← field office bank GL
| UNES  | Z1    | 1294971  | X     |  ← technical account (transitioning)
```

### 9. User Exit Chain (EBS-specific)

```
CMOD Project: YTFBE001
  └── EXIT_RFEBBU10_001 (EBS posting user exit)
       └── Include: ZXF01U01
            └── Include: YTBAM001
                 └── Business area assignment during EBS integration
```

**What the exit does:**
- During FF_5 import, the exit fires for each bank statement line item
- Checks `I_FEBKO.EFART` (statement format) and `I_FEBKO.BUKRS` (company code)
- For UNES/IIEP/UBO: looks up business area from YBASUBST (legacy) or YTFI_BA_SUBST (modern)
- If clearing match found on 11xxxxx: inherits BA from the cleared offsetting item
- If no match and not in YBASUBST: item posted without BA → goes to FEBAN post-processing

**Legacy code being replaced:**
```abap
elseif (i_febko-efart = 'E') and (i_febko-bukrs ne 'UBO') and (i_febko-bukrs ne 'IIEP')
  move-corresponding i_febep to e_febep
  e_febep-gsber = 'X'   " ← This is what's being phased out
```

### 10. Incoming Payment Classification (Tag 86 Rules)

Incoming payments on EUR01/USD04 accounts are classified by parsing MT940 Tag 86 content:

| # | Category | Keyword in Tag 86 | Business Area | Customer Logic | Banks |
|---|----------|--------------------|---------------|----------------|-------|
| 1 | Assessed Contributions (Regular Budget) | `CONT` after ISO country code | GEF | Customer = ODD 6-digit (200000-299999 series) | SOG01, CIT04 |
| 2 | Assessed Contributions (WHF) | `WHF` | PFF | Customer = EVEN 6-digit | SOG01, CIT04 |
| 3 | Assessed Contributions (ICH) | `ICH` or `INTANGIBLE` | PFF | Customer from 201000-201999 range | SOG01, CIT04 |
| 4 | Voluntary Contributions | `BC` + budget code | PFF (rare: OPF) | Customer = 6-digit after `C` | SOG01, CIT04 |
| 5 | Invoices SR/RB | 74xxxxxxxx or 67xxxxxxxx | From invoice doc | Customer = 6-digit | SOG01, CIT04 |
| 6 | Office expenses | `PARKING`, `LOYER`, `RENT`, `TELEPHONE`, `DEVIS` | OPF | Customer = 6-digit | SOG01, CIT04 |
| 7 | Banks for deposits | 6-digit 600000-699999 | GEF | Customer from 600001-699999 | SOG01, CIT04 |
| 8 | MBF | `MBF`, `CAM`, `PENSION` | MBF | Customer = 8-digit after `ID` | SOG01, CIT04 |
| 9 | UPO Sales | All credits on EUR04 | OPF | Default customer 500469 | SOG01/EUR04 |

**Future Tag 86 format:** `C<6-digit customer>F<sector/keyword>`
- Example: `C200293 FCONT` → Customer 200293, Sector CONT → BA=GEF
- Example: `C100040 BC180REV9000` → Customer 100040, Budget code 180REV9000 → BA=PFF

### 11. Bank-Specific Configuration (Detailed)

#### SOG01/EUR01 (Société Générale, Paris — EUR primary)
- GL: 1075012 (bank) / 1175012 (sub-bank)
- Auto-clearing: F110 payment docs (SOG_PAYM_DOC), payroll staff numbers (SOG_STAFF), DME files (SOG_DME)
- Manual FEBAN: incoming contributions, charges, miscellaneous

#### CIT04/USD04 (Citibank, New York — USD primary)
- GL: 1043011 (bank) / 1143011 (sub-bank)
- Auto-clearing: Payment docs (CIT_PAYM_DOC), DME files (CIT_DME)
- Special: S202 (Worldlink bulk debits) — no DME reference, needs manual matching
- Manual FEBAN: incoming contributions, charges, Worldlink fees

#### SOG01/USDD1 (Société Générale, Paris — USD secondary)
- GL: 1075011 (bank) / 1175011 (sub-bank)
- Highest volume: 10,921 transactions (Jul 2021-Jun 2022)
- Auto-clearing: payment docs, payroll staff numbers

#### SOG01/EUR04 (Société Générale, Paris — UPO/Shops)
- GL: 1075042 (bank) / 1175042 (sub-bank)
- Special: All credits → default customer 500469 with BA=OPF
- Includes: card payments (NCOL), cash deposits (NMSC), donations

#### CIT21/CAD01 (Citibank, Canada — CAD)
- Auto-clearing: payment docs, staff numbers
- Treasury transfers: all post-processed via FEBAN

#### Treasury Transfer Accounts
- SCB14/USD01, SOG05, BNP01, CRA01, WEL01, CIC01
- Posting template: TR_TRNF
- Total volume: 558 transactions (Jul 2021-Jun 2022) — low volume, manual processing

### 12. BBP Bank Reconciliation Automation Project (2020-2022)

**Project Team:**
- Anssi Yli-Hietanen (Project Leader)
- Abhishek Gupta (BFM/MO — PM & Functional Coordinator)
- Thavry Eng (BFM/MO — Team Member)
- Ingrid Wettie (BFM/MO — Team Member)
- Baizid Gazi (BFM/TRS — Team Member)
- Marlies Spronk (KMI/FAM — Functional Specialist & Technical Coordinator)

**Project Phases:**
1. Decommission BA=X default → replace with YBASUBST table-driven lookup
2. Implement BA inheritance from offsetting accounts during EBS clearing
3. Implement automatic reconciliation via search strings
4. Deploy FEBAN for post-processing of unmatched items
5. Decommission YTR2/YTR2_HR legacy reconciliation programs

**Testing Results (D01):**
| Scenario | Result | Notes |
|----------|--------|-------|
| Clearing during upload (auto-match) | **PASS** | BA inherited from offsetting account correctly |
| FEBAN simple posting (no clearing) | **FAIL** | BA can't be determined — development bug |
| FEBAN with clearing (vendor match) | **FAIL** | BA not inherited from vendor item |
| Manual BA override in FEBAN | Partial | System doesn't adapt BA as expected |

**Known Issue:** FEBAN BA derivation requires development fix. System should take BA from offsetting account regardless of clearing status.

---

## PART B — Production Reality (From Gold DB 2024-2026)

### 13. Bank GL Activity by House Bank

**CRITICAL FINDING: BSAS has 0 cleared items on bank GLs (10xxxxx) — ALL clearing happens on sub-bank GLs (11xxxxx).**

This means the 10xxxxx accounts are the ACCUMULATION side — they grow with each bank statement import and are never directly cleared. The 11xxxxx sub-bank accounts are where actual payment matching happens.

**Top banks by open items on 10xxxxx (UNES):**

| # | House Bank | Acct ID | CCY | Open Items | Open Amount (Local) | GL |
|---|-----------|---------|-----|-----------|--------------------|----|
| 1 | ECO08 | USD01 | USD | 14,065 | 21,388,111 | 0001094311 |
| 2 | SCB04 | TZS01 | TZS | 11,936 | 9,847,082 | 0001081264 |
| 3 | ECO05 | XAF01 | XAF | 8,361 | 11,405,827 | 0001094204 |
| 4 | **CIT04** | **USD04** | **USD** | **6,877** | **7,138,241,833** | 0001043011 |
| 5 | **SOG01** | **EUR01** | **EUR** | **6,767** | **2,977,044,512** | 0001075012 |
| 6 | AIB01 | USD01 | USD | 5,392 | 53,890,520 | 0001090651 |
| 7 | CIT02 | KZT01 | KZT | 5,246 | 9,459,805 | 0001043124 |
| 8 | CIT23 | XOF01 | XOF | 5,246 | 93,300,214 | 0001043254 |
| 9 | SCB18 | ZMW01 | ZMW | 4,541 | 4,417,270 | 0001081844 |
| 10 | SOG06 | HTG01 | HTG | 4,249 | 3,047,004 | 0001075524 |
| 11 | SCB03 | XAF01 | XAF | 3,859 | 32,899,456 | 0001081644 |
| 12 | **SOG01** | **USDD1** | **USD** | **3,591** | **907,200,271** | 0001075011 |

**Key insight:** The top 3 by item count are field office banks (ECO08, SCB04, ECO05), NOT HQ banks. But the top by AMOUNT are CIT04/USD04 ($7.1B) and SOG01/EUR01 ($3.0B) — the HQ primary accounts.

### 13b. FEBEP/FEBKO — EBS IS FULLY ACTIVE (Critical Correction)

**Previous claim "FEBEP=0 rows" was WRONG.** Session #029 extraction reveals:

| Table | Rows (2024-2026) | Key Finding |
|-------|------------------|-------------|
| **FEBEP** | **223,710** line items | 99.9% have FI document number (BELNR). Only 147 unposted. |
| **FEBKO** | **84,972** statement headers | 99.0% fully posted (ASTAT=8). 745 partially posted. |

**FEBKO Status Distribution:**
| ASTAT | Count | Meaning |
|-------|-------|---------|
| 8 | 84,172 (99.0%) | Fully posted |
| 7 | 745 (0.9%) | Partially posted |
| 4 | 30 | Processing |
| Other | 25 | Various |

**Monthly FEBEP Volume (stable ~7-10K/month):**
- 2024: 93,371 items (avg 7,781/month)
- 2025: 109,120 items (avg 9,093/month)
- 2026 Q1: 21,219 items (avg 7,073/month)

**Average items per statement:** 2.6 (most are 2-line: bank debit + sub-bank credit)

### 13c. T028G — Production Posting Rules (Validated)

**23 transaction types configured in P01.** Key banks:

**SOG_FR (Société Générale — primary):** 18 rules
- NTRF outgoing → 102O algorithm 015 (clearing by assignment) [MATCHES documentation]
- NTRF incoming → 102I algorithm 001 (standard)
- NCHK outgoing → 102O algorithm 013 (check number match) [MATCHES]
- NMSC → 101I/102O (post to sub-bank, no clearing)
- NINT → 111I/111O (interest)

**CIT04_US (Citibank NY):** 11 rules
- NTRF outgoing → 102O algorithm **019** (DME matching) [MATCHES documentation]
- S202 outgoing → 102O algorithm 019 (Worldlink bulk)
- All incoming → 102I algorithm 001

**Field offices (XRT940/XRT940X):** 130 + 128 = 258 rules
- Covers ALL field office banks
- Simplified posting (mostly 101I/101O)

### 13d. YBASUBST — Legacy BA Substitution (Validated)

**752 entries total.** Distribution by company code:
- UNES: 282 Z1-specific entries + general entries (mostly BA=GEF)
- Institutes (IBE, ICBA, ICTP, IIEP, UBO, etc.): remaining entries

**BA=X still in YBASUBST:** Only **9 entries** (IIEP=6, UBO=3) — all on technical 12/13 accounts being phased out.

**YTFI_BA_SUBST (modern):** 129 range-based entries.
- UNES Z1: Single range `0001000000 - 0001199999 → GEF` (covers ALL bank GLs with GEF default)
- Institutes have specific GL ranges

### 14. Business Area Distribution on Bank Items

**BSIS open items (bank GLs, HKONT LIKE '0001%', BUKRS='UNES'):**

| Business Area | Open Items | % of Total | Status |
|--------------|-----------|-----------|--------|
| GEF | 199,599 | 84.0% | Normal — Global Education Fund is largest |
| PFF | 33,570 | 14.1% | Normal — Programme Fund |
| OPF | 2,256 | 0.9% | Normal — Operations |
| IBA | 1,753 | 0.7% | IIEP Business Area |
| PDK | 1,274 | 0.5% | Dakar regional |
| PAR | 861 | 0.4% | Paris |
| **X** | **54** | **0.02%** | **BBP project nearly complete — only 54 items remain with legacy BA=X** |
| FEL | 25 | 0.01% | Fellowships |

**Key Finding:** BA=X phase-out SUCCESS — from thousands of items pre-2022 to just 54 remaining.

### 15. Clearing Methods in Practice

**Z1 creation (bank statement import):**
| TCode | Count | Users | Purpose |
|-------|-------|-------|---------|
| FB01 | 170,216 | JOBBATCH, I_BIDAULT | Auto-import (91.2%) + manual |
| FB05 | 38,012 | T_ENG, EG_STREIDWOL, I_BIDAULT, AB_GUPTA | Posting with clearing |
| FBR2 | 1 | S_COURONNAUD | Post with reference |

**Z7 creation (clearing documents):**
| TCode | Count | Users | Purpose |
|-------|-------|-------|---------|
| FB05 | 3,474 | L_NEVES (1,653), F_CADIO (967), JC_CUBA (696) | Manual clearing |
| FB08 | 10 | JC_CUBA, B_LOPES, L_NEVES | Reversal |
| FB01 | 2 | S_COURONNAUD | Manual posting |

**CRITICAL: Z7 clearing is 100% MANUAL.** Zero JOBBATCH Z7 documents = no automatic clearing in production. All 3,486 clearing documents were created by named users.

### 16. Automation Rate

| Metric | Value | Note |
|--------|-------|------|
| Auto-import (Z1 creation) | **91.2%** (189,993 of 208,229) | JOBBATCH = automated |
| Manual import | 8.8% (18,236) | Named users (FF_5 manual upload) |
| Auto-clearing (Z7 creation) | **0%** | Zero JOBBATCH Z7 docs |
| Manual clearing (FB05) | **100%** (3,486 Z7 docs) | L_NEVES=1,653, F_CADIO=967, JC_CUBA=696 |

**CRITICAL DISTINCTION:** 91.2% auto-IMPORT ≠ auto-RECONCILED.
- **Import** is 91.2% automated (JOBBATCH creates Z1 docs)
- **Reconciliation** is **0% automated** in production (all Z7 clearing is manual FB05)
- The search string configuration exists but appears to clear DURING import (posting type 4/5 in Z1), NOT as separate Z7 documents
- This means auto-clearing happens as part of the Z1 posting itself (102O posting rules), not as a separate step

### 17. Open Item Aging by Bank

**Top 10 banks by total open items (UNES), with aging breakdown:**

| Bank | AcctID | 0-30d | 1-3m | 3-9m | 9-15m | 15m+ | Total |
|------|--------|-------|------|------|-------|------|-------|
| ECO08 | USD01 | 119 | 1,013 | 3,752 | 3,467 | 5,714 | 14,065 |
| SCB04 | TZS01 | 58 | 330 | 2,466 | 2,554 | 6,528 | 11,936 |
| ECO05 | XAF01 | 62 | 168 | 1,278 | 5,086 | 1,767 | 8,361 |
| CIT04 | USD04 | 117 | 546 | 1,513 | 1,608 | 3,093 | 6,877 |
| SOG01 | EUR01 | 90 | 514 | 1,469 | 1,574 | 3,120 | 6,767 |
| AIB01 | USD01 | 48 | 374 | 1,369 | 1,094 | 2,507 | 5,392 |
| CIT02 | KZT01 | 36 | 249 | 1,543 | 1,186 | 2,232 | 5,246 |
| CIT23 | XOF01 | 47 | 360 | 1,266 | 1,199 | 2,374 | 5,246 |
| SCB18 | ZMW01 | 4 | 242 | 1,782 | 564 | 1,949 | 4,541 |
| SOG06 | HTG01 | 0 | 338 | 1,781 | 2,130 | 0 | 4,249 |

**H19 Key Insight:** The 15m+ aging is NOT concentrated on HQ banks — field office banks (ECO08=5,714, SCB04=6,528) have MORE stale items than CIT04 (3,093) or SOG01 (3,120). This suggests field office reconciliation is structurally weaker than HQ.

**Root cause hypothesis [INFERRED]:**
- Field office banks use simplified posting (101I to 11xxxxx) → all go to manual FEBAN
- HQ banks have search strings configured for auto-clearing → better clearing rate
- But on 10xxxxx accounts, items are NEVER cleared (by design) — they represent the bank's view. Reconciliation happens on 11xxxxx.

### 18. Sub-Bank Account (11xxxxx) Activity

**Sub-bank accounts are WHERE actual reconciliation happens:**

| Metric | Value |
|--------|-------|
| Open on 11xxxxx | 2,737 items (10.6M local ccy) |
| Cleared on 11xxxxx | 443,666 items (11.3B local ccy) |
| **Clearing rate** | **99.4%** |

Sub-bank (11xxxxx) clearing rate = 99.4% — excellent. Only 2,737 items remain open.

**Top sub-bank GLs with open items:**
| GL | Open Items | Amount | BA | Likely Bank |
|----|-----------|--------|-----|------------|
| 0001181104 | 690 | 691,086 | GEF | SCB field office |
| 0001190654 | 524 | 18,426 | GEF | Field office |
| 0001194311 | 143 | 218,468 | GEF | ECO08/USD01 |
| 0001194694 | 132 | 16,016 | GEF | ECO02/XOF01 |
| 0001175012 | 96 | 118,679 | GEF | SOG01/EUR01 |

**ARCHITECTURAL INSIGHT:**
- 10xxxxx = bank's view (never cleared, items accumulate → the 199K "open items")
- 11xxxxx = SAP's clearing view (99.4% cleared → actual reconciliation works well)
- The 199K open items on 10xxxxx are **NOT unreconciled** — they are the permanent record. The REAL unreconciled count is the 2,737 open items on 11xxxxx.

---

## PART C — The Bridge (Configuration vs Reality)

### 19. Configuration-vs-Reality Matrix

**The Big Picture — What Production Data Reveals:**

| Metric | Documentation Says | Production Reality | Assessment |
|--------|-------------------|-------------------|------------|
| FEBEP data | — (SKILL.md said "0 rows") | **223,710 items** (2024-2026), 99.9% posted | **[CORRECTED]** EBS is FULLY active |
| FEBKO data | ~100+ statements/day | **84,972 statements**, 99.0% fully posted | [VERIFIED] matches documented volume |
| Auto-import rate | ~100+ statements/day | 91.2% auto (189K JOBBATCH) | [VERIFIED] matches |
| Auto-clearing rate | Search strings auto-clear payments | **0% Z7 auto-clearing** | [VERIFIED] clearing during Z1 import only, not as separate Z7 |
| Posting rules | SOG_FR/CIT04_US documented | **T028G: 23 types, 1,025 rules** — matches documentation | [VERIFIED] config matches |
| BA=X phase-out | Replace with YBASUBST | YBASUBST has 9 BA=X entries. BSIS has 54 BA=X items | [VERIFIED] **BBP project SUCCESS** |
| YBASUBST | 1:1 GL→BA mapping | **752 entries** (282 UNES Z1-specific) | [VERIFIED] active in P01 |
| YTFI_BA_SUBST | Range-based (post 10/2022) | **129 entries** including UNES 10xxx→GEF global range | [VERIFIED] active |
| 10xxxxx open items | Normal (bank view) | 199K items | [VERIFIED] by design — not unreconciled |
| 11xxxxx clearing rate | Target: high automation | **99.4%** cleared (443K of 446K) | [VERIFIED] **excellent** |
| Real unreconciled | — | **2,737 items on 11xxxxx** | [VERIFIED] actual gap |
| FEBAN BA bug | Fails in D01 testing | **Unknown in P01** | [NOT VERIFIED] |
| BSAS AUGBL | Should link clearing docs | **EMPTY on all 449K rows** | [VERIFIED] extraction gap — re-enrichment needed |

**Per-Bank Configuration Match (documented vs actual):**

| Bank | Account | Documented Config | Production Volume | Aging 15m+ | Assessment |
|------|---------|------------------|------------------|-----------|------------|
| SOG01 | EUR01 | NTRF→102O/015 auto-clear | 6,767 open (10xxx) | 3,120 | HQ bank — search strings configured |
| CIT04 | USD04 | NTRF→102O/019 DME + S202 Worldlink | 6,877 open (10xxx) | 3,093 | S202 Worldlink gap confirmed in docs |
| SOG01 | USDD1 | NTRF→102O/015 + staff match | 3,591 open (10xxx) | *within SOG01* | Highest volume account |
| ECO08 | USD01 | Simplified (101I to 11xxx) | **14,065** open | **5,714** | **Worst performer — field office** |
| SCB04 | TZS01 | Simplified (101I to 11xxx) | 11,936 open | 6,528 | Field office — no auto-clearing |
| ECO05 | XAF01 | Simplified (101I to 11xxx) | 8,361 open | 1,767 | Field office |

### 20. Where Configuration Fails (Root Cause Analysis)

**REVISED UNDERSTANDING:** The 199K "open items" on 10xxxxx are NOT failures — they are the bank's permanent ledger. The REAL reconciliation gap is the 2,737 open items on 11xxxxx sub-bank accounts.

However, the 10xxxxx accumulation DOES matter for:
- GL balance confirmation (bank vs books reconciliation)
- Aging analysis for dormant accounts
- Currency exposure tracking

**Actual root causes for remaining gaps:**

1. **Field office simplified posting** [VERIFIED] — ECO08 (14K), SCB04 (12K), ECO05 (8K) use 101I posting (no clearing during import). All items go to FEBAN manual processing → explains field office dominance in aging.

2. **Search strings work for HQ, not field offices** [INFERRED] — FO_PAYM_DOC pattern `31########` is configured, but field office banks have different external codes and reference formats. CPS format was decommissioned, potentially leaving gaps.

3. **S202 Worldlink gap** [REPORTED in docs] — CIT04 S202 transactions have no DME reference → cannot auto-match. Documented as known limitation.

4. **FEBAN BA derivation bug** [REPORTED in D01 testing] — FEBAN fails to determine business area for simple postings and clearing. If this persists in P01, it blocks post-processing of unmatched items on 11xxxxx.

5. **BSAS AUGBL not extracted** [VERIFIED] — Cannot trace clearing chain (Z1→clearing doc) because AUGBL field is empty on all 449K BSAS bank rows. This is an extraction gap, not a system gap. Re-enrichment needed.

6. **Currency inflation** [VERIFIED] — XOF, TZS, KZT, IDR inflate local currency amounts. The "$13.9B" figure is meaningless without USD conversion. H21 remains open.

### 20b. Custom Programs in Use

**YTR3 / YTBAE002 — UNESCO's custom bank-reconciliation reversal/clearing program** (added 2026-04-20 after INC-000006906).

| Attribute | Value |
|---|---|
| TCODE | `YTR3` (live TSTC: `PGMNA=YTBAE002 DYPNO=1000 CINFO=9`) |
| Program | `YTBAE002` (package `YA`, 3,422 lines, monolithic, no INCLUDEs, no Y/Z deps) |
| Author history | 10 transports by N_MENARD, 2023-04-14 → 2023-06-29. Frozen since. |
| Source | `extracted_code/CUSTOM/YTBAE002/YTBAE002.abap` (Session #057 extraction) |
| Output | Classical list report (`WRITE` + `CALL SCREEN 9000`). No ALV. |

**What it does (NOT a read-only report):**
It decides, from BSIS row content + PAYR/BKPF correlation, whether each
open bank sub-bank line needs to be reversed, cleared, or reset-cleared.
It then drives three standard FI clearing TCODEs via BDC:

| TCODE | Call site | Purpose |
|---|---|---|
| `FB08` | `YTBAE002.abap:723, :853` | Reverse document |
| `F-04` | `YTBAE002.abap:771` | Post with clearing |
| `FBRA` | `YTBAE002.abap:819` | Reset cleared items |

All four CALL TRANSACTIONs pass `USING BDCDTAB MODE GC_MOD MESSAGES INTO
Y_MESSTAB`, and each is followed by `PROC_RECONCIL_MESS_ADD` (:754, :795,
:840, :874) which persists the message table into `GT_RECONCIL_MESS` for
the list output.

**Selection screen (YTBAE002.abap:297-310):**

| Param | Default | Obligatory |
|---|---|---|
| `GP_BUKRS` | `UNES` | YES |
| `GP_HBKID` | — | YES |
| `GP_HKTID` | — | YES |
| `GP_BUDAT` | `SY-DATUM` | YES |

No SELECT-OPTIONS, no date ranges. One fiscal year per run
(`GJAHR = GP_BUDAT(4)` at :369).

**Scope resolution (YTBAE002.abap:1098-1127):**
- `SELECT SAKNR XOPVW FROM SKB1 WHERE BUKRS+HBKID+HKTID`
- Route to `GR_SAKNR` (balance range) if `SAKNR+3(2) IN ('10','12','14')`
- Route to `GR_SAKNR_OI` (open-items range) if `SAKNR+3(2) IN ('11','13','15')`
  **AND** `SKB1.XOPVW = 'X'` (open-item managed)
- **Dependency:** bank sub-bank GLs MUST have `XOPVW='X'` on `SKB1`, else
  the OI range is empty and the LDB scan degrades.
- Does NOT use YBANK_* Report-Painter sets (grep-confirmed over the full
  corpus).

**Known defects:**

| Defect | Location | Severity | Status |
|---|---|---|---|
| **MODE 'E' BDC network coupling** | `YTBAE002.abap:27` (`GC_MOD='E'`) | HIGH | INC-000006906 — TIME_OUT on slow WAN (Maputo). Fix at `Zagentexecution/fixes/INC-000006906/YTBAE002_fix.abap` ('E'→'N'). See anti-pattern below. |
| **Empty-range unbounded LDB scan** | `YTBAE002.abap:1366-1370` | MED (latent) | LOOP AT LR_SAKNR without `IS NOT INITIAL` guard. If SKB1 returns no `XOPVW='X'` rows, LDB scans BSIS with only `BUKRS+GJAHR`. Not triggered by INC-000006906's input but real. Optional fix `FIX_C` in the same fix file. |

**TCODEs called (via BDC from this program):** `FB08`, `F-04`, `FBRA` —
standard FI clearing transactions. Authorization on those TCODEs is
required for the user running `YTR3`.

---

### 20c. Anti-Pattern — MODE 'E' CALL TRANSACTION in Reconciliation Loops

**Pattern:** any custom ABAP program that issues
`CALL TRANSACTION '<t>' USING <bdc> MODE 'E'` inside a `GET <table>` /
`LDB_PROCESS` / large-LOOP path will open SAPGUI on every BDC error. MODE
`'E'` is documented as *"Only display if error — opens SAPGUI so the user
can correct interactively"*. On slow WAN paths (field offices) the
cumulative GUI round-trip adds hundreds of milliseconds per error and can
exceed `rdisp/max_wprun_time`. The work-process aborts with `TIME_OUT` in
whatever `SELECT` is currently waiting — typically the caller's logical
database (e.g., `SAPDBSDF:1983 PUT_BSIS`), which obfuscates the real cause.

**Canonical instance:** INC-000006906 — YTBAE002 at `line 27` plus four
CALL TRANSACTION sites (`:723 FB08`, `:771 F-04`, `:819 FBRA`, `:853
FB08`). User reproduced from HQ (fast LAN) in ~2 s; from Maputo (slow
WAN) TIME_OUTs.

**Why it's lethal (and silent at HQ):** the code "works" at HQ forever
because the GUI handshake round-trips in microseconds on LAN. It
degrades in direct proportion to WAN RTT, which is why field offices
suffer while HQ does not.

**The correct pattern:**

```abap
" WRONG — network-coupled
CALL TRANSACTION 'FB08' USING bdc_tab MODE 'E'
                              MESSAGES INTO messtab.

" RIGHT — silent, errors captured for post-loop reporting
CALL TRANSACTION 'FB08' USING bdc_tab MODE 'N'
                              MESSAGES INTO messtab.
" ... then at end of loop, surface messtab in the list / ALV.
```

MODE `'N'` runs the BDC with no GUI interaction. `MESSAGES INTO` captures
every message silently. Errors become visible in the list output after
the loop finishes.

**Falsification:** if a program with MODE `'E'` BDC inside an LDB loop
runs from HQ without dumping, that is NOT evidence the program is safe —
it is evidence that the WAN handshake has not yet been triggered. Test
from a field-office VPN.

**Detection (systemic):** see Claim 54 (`claim-006906-mode-e-bdc-
network-coupling`). Proposed recurring check
`Zagentexecution/quality_checks/mode_e_bdc_in_loop_check.py` to scan
Y*/Z* REPOSRC for the pattern once TSTC/TRDIR/REPOSRC are in Gold DB
(KU-new-10).

---

### 21. Known Issues & Data Gaps

| Issue | Status | Impact |
|-------|--------|--------|
| FEBAN BA derivation bug | [REPORTED in testing docs] — P01 status unknown | Blocks manual post-processing |
| BA=X residual: 54 items | [VERIFIED] — confirmed in Gold DB | Minor — near-complete phase-out |
| BSAS AUGBL gap (H20) | **[VERIFIED]** — AUGBL is EMPTY on ALL 449,675 bank BSAS rows | AUGBL was NOT extracted for bank GLs. Re-enrichment needed to build clearing chain. |
| ~~FEBEP = 0 rows~~ | **[CORRECTED]** FEBEP has **223,710 items** (2024-2026), 99.9% posted. FEBKO has 84,972 statements. **EBS IS FULLY ACTIVE.** Previous claim was wrong — likely queried wrong client or never extracted. | Critical correction to SKILL.md needed |
| T028B/T028G/T028R | **[EXTRACTED]** T028B=169, T028G=1,025, T028D=331 rows. T028R=empty. | Config tables now in Gold DB |
| YBASUBST/YTFI_BA_SUBST | **[EXTRACTED]** YBASUBST=752, YTFI_BA_SUBST=129 rows. | BA substitution rules validated |

---

## Source Documents

| Document | Key Content |
|----------|-------------|
| FS Automatic Bank integration and reconciliation Customizing.docx | Complete EBS customizing: account symbols, posting rules, search strings per bank |
| FS Automatic Bank reconciliation Development.docx | User exit chain (CMOD YTFBE001), BA inheritance logic, ABAP code |
| BBP Bank Reconciliation Automation 2.0.docx | Full project scope, phases, account list, authorization changes |
| BBP Bank Reconciliation Automation.docx | Original v1.0 project plan (Sep 2020) |
| Bank statement integration and reconciliation 2022.docx | Options analysis for YTR2 replacement |
| Automatic reconciliation in SAP.docx | Technical vs main account posting comparison |
| Concerning the specific topic 2 related to FEBAN access.docx | FEBAN access control, field office vs HQ processing |
| EBS Different posting rules for 1 Ext Transaction code.docx | Search string priority logic, SUBD/SUBF rule interaction |
| SAP Help Configuration EBS.docx | Search string configuration guide (art vs science), BDC field mapping |
| Testing EBS development.docx | Test cases: BA from YBASUBST, BA inheritance, FEBAN failures |
| Example error.docx | FEBAN BA determination error screenshots (D01/V01) |
| Analysis EBS 2022 Incoming amount.xlsx | Posting rule analysis per bank account with Tag 86 examples |
| IP_information from bank statements_220427.xlsx | Incoming payment Tag 86 classification rules |
| Analysis EBS 2021 2022 buss area X.xlsx | BA=X phase-out analysis (permission denied — locked) |
