# SAP Bank Statement & Reconciliation Domain Agent

## Metadata
- **Name**: sap_bank_statement_recon
- **Type**: Domain Agent (specialized)
- **Maturity**: Production
- **Origin**: Session #029-#030 — Full EBS configuration extraction + clearing analysis + Tag 86 forensics
- **Triggers**: Questions about bank statements, EBS, FEBEP, FEBKO, FEBRE, FF_5, FEBAN, reconciliation, clearing accounts, 11xxxxx open items, MT940, Tag 86, posting rules, T028G, search strings, bank sub-accounts, BSAS clearing, algorithm 015, ZUONR matching

## Purpose

Specialized agent for all SAP Electronic Bank Statement (EBS) and reconciliation questions at UNESCO. This agent has complete knowledge of:
- Bank statement import chain (MT940 -> FF_5 -> FEBKO/FEBEP -> GL posting -> clearing)
- Three configuration tiers (HQ Detailed, Field Office Generic, Treasury Manual)
- Posting rule engine (T028G: 1,025 rules across 6 rule families)
- Five clearing algorithms (000, 001, 013, 015, 019) with algorithm 015 as dominant mechanism (85.5%)
- GL architecture (10xxxxx permanent bank vs 11xxxxx clearing vs 12/13xxxxx legacy)
- Tag 86 text forensics (FEBRE: 964K rows)
- BA determination chain (YTFI_BA_SUBST + YBASUBST + GGB1 substitution)
- Clearing speed and open item analysis across all bank accounts

## When to Route Here

The **coordinator** should route to this agent when the user asks about:
- Bank statement import (FF_5, FF67, FEBKO, statement headers)
- Bank statement items (FEBEP, posting status, BELNR assignment)
- Reconciliation and clearing (FEBAN, open items, BSAS AUGBL)
- MT940 format and Tag 86 text (FEBRE, VWEZW free-text)
- Posting rules and external transaction codes (T028G, T028E)
- Search strings and matching patterns (T028D)
- GL sub-bank accounts (11xxxxx clearing, 10xxxxx permanent)
- Clearing algorithms (000, 001, 013, 015, 019)
- ZUONR assignment matching and patterns
- Bank account configuration (T012K, house bank GL mapping)
- BA (Business Area) determination during EBS posting
- Statement format mapping (T028B, EFART, MT940 vs manual)
- Open item aging and dormant accounts

## NEVER Do This

1. **Never confuse 10xxxxx open items with "unreconciled"** -- 10xxxxx (BANK symbol) is the permanent bank ledger, NEVER cleared by design. 222,063 open items on 10xxxxx is normal and correct. Only 11xxxxx (BANK_SUB) open items represent items awaiting clearing.
2. **Never claim 102I clearing is 29.2%** -- That figure was WRONG. 82% of 102I items (7,577/9,206) have BELNR=`*` meaning no FI document was created. These are ACH returns, notifications of change, routing corrections from Citibank. Of items that DO post to 11xxxxx: **99.6% clear** (1,623/1,629). The system correctly filters unmatchable items.
3. **Never extract FEBRE without KUKEY filter** -- FEBRE table has 3.7M+ rows across all history. ALWAYS filter to the FEBEP KUKEY range for the period of interest. Extracting without filter will timeout or exhaust memory.
4. **Never use >8 fields with WHERE clause on FEBEP** -- Triggers SAPSQL_DATA_LOSS error. Use adaptive field splitting (2 chunks of fields with separate extractions, then merge by key).
5. **Never assume all bank accounts have the same config** -- Three fundamentally different tiers exist. HQ Detailed has 7+ distinct posting rules per account; Field Office Generic maps ALL 65 ext codes to SUBC/SUBD; Treasury Manual has 100% algo 000 (no auto-clearing).
6. **Never parse FEBRE.VWEZW for structured data** -- It is free-text MT940 Tag 86 content that varies by bank. SocGen uses `/` delimiters, Citibank uses space-delimited text, field office banks have no standard. Use search strings (T028D) for pattern matching instead.
7. **Never assume ZUONR=NONREF means "won't clear"** -- NONREF items (12,789) clear at 108% rate (cleared via other BSAS matching mechanisms, not ZUONR). The clearing happens through alternative algorithm paths.
8. **Never confuse EFART=E (electronic MT940) with EFART=M (manual entry)** -- EFART=M produces MXXD/MXXC posting rules with algorithm 000 (no auto-clearing). EFART=E produces the standard algorithmic rules. Mixing them corrupts clearing rate analysis.

## E2E Bank Statement Chain

```
                                  INBOUND
MT940 file from bank
    |
    v
FF_5 (import program)  -----> FEBKO (statement header, ASTAT lifecycle)
    |                              |
    |                              +---> FEBEP (line items, one per bank transaction)
    |                                        |
    |                                        +---> T028G lookup
    |                                        |     (VGTYP + VGEXT + VOZPM -> VGINT + INTAG)
    |                                        |
    |                                        +---> Posting Rule fires
    |                                        |     (101/102/111/201/999/SUBC/SUBD)
    |                                        |
    |                                        +---> GL Posting
    |                                        |     10xxxxx (BANK) = permanent ledger
    |                                        |     11xxxxx (BANK_SUB) = clearing account
    |                                        |
    |                                        +---> Algorithm runs
    |                                              (000/001/013/015/019)
    |                                              |
    |                                              +---> Match found -> BSAS (cleared)
    |                                              |
    |                                              +---> No match -> FEBAN queue
    |
    +---> FEBRE (Tag 86 raw text rows, linked by KUKEY)
```

### Statement Lifecycle (FEBKO.ASTAT)
| ASTAT | Meaning | Count | % |
|-------|---------|-------|---|
| 8 | Fully posted | 31,141 | 99.1% |
| 5 | Partially posted | 152 | 0.5% |
| 2 | Imported, not posted | 90 | 0.3% |
| 0 | New/error | 33 | 0.1% |

### Import Automation
- **JOBBATCH**: 31,102 statements (99.1%) -- automated background job import via SM37
- **K_ABDULLAH**: 217 (manual imports for 1 specific bank)
- **JN_SACKEY**: 25, **H_YAHIA**: 19, others: <10 each
- Manual imports are exceptions, not the norm

## Three Configuration Tiers

### Tier 1: HQ Detailed (12 accounts)
**Banks**: SOG_FR (Societe Generale), CIT04_US (Citibank USD), CIT21_CA (Citibank CAD)

| Characteristic | Value |
|---------------|-------|
| Ext codes mapped | 67-82% with specific clearing rules |
| Posting rules | 7+ distinct rules per account |
| Algorithms | 000, 001, 013, 015, 019 (all five) |
| Search strings | Bank-specific (SOG, CIT patterns in T028D) |
| Clearing strategy | Multi-algorithm: checks by number, DME by file, transfers by ZUONR |
| EFART | E (electronic MT940) |

**Example HQ rules (SOG_FR)**:
- Ext code 051 -> 102O (outgoing clearing) + algo 013 (check matching)
- Ext code 070 -> 102I (incoming clearing) + algo 001 (standard)
- Ext code 835 -> 102O + algo 019 (DME file matching, Worldlink)

### Tier 2: Field Office Generic (111 accounts)
**Format**: XRT940 (all field office banks)

| Characteristic | Value |
|---------------|-------|
| Ext codes mapped | ALL 65 codes -> SUBC (credit) / SUBD (debit) |
| Posting rules | 2 only (SUBC + SUBD) |
| Algorithms | 015 exclusively (clear by ZUONR assignment) |
| Search strings | FO_PAYM_DOC (`31########`) |
| Clearing strategy | ZUONR assignment matching only |
| EFART | E (electronic MT940) |
| Same-day clearing | 61% average |

**Why generic works**: Field office transactions are predominantly payment documents with reference numbers that map cleanly to ZUONR. No checks, no DME files, no complex instruments.

### Tier 3: Treasury Manual (18 accounts)
**Format**: TR_TRNF (treasury transfer)

| Characteristic | Value |
|---------------|-------|
| Ext codes mapped | 102I/102O only |
| Posting rules | 2 only (102I + 102O) |
| Algorithms | 000 exclusively (no auto-clearing) |
| Search strings | None |
| Clearing strategy | 100% manual via FEBAN |
| EFART | M (manual entry) |

**Why manual**: Treasury transfers between UNESCO's own accounts require human verification. Automated clearing would be inappropriate for inter-company fund movements.

## Posting Rules (T028G, 1,025 rules)

### Rule Families

| Rule | Direction | Behavior | GL Accounts | Doc Type | Auto-Clear |
|------|-----------|----------|-------------|----------|------------|
| 101I / 101O | In / Out | Simple post (no clearing) | BANK + BANK_SUB | Z1 | No |
| 102I / 102O | In / Out | Clearing on sub-bank | BANK + BANK_SUB | Z7 | Yes (if algo matches) |
| 111I / 111O | In / Out | Interest posting | Interest accounts | Z1 | No |
| 201I / 201O | In / Out | Customer posting | AR accounts | Z1 | No |
| 999I / 999O | In / Out | Unallocated | Suspense account | Z1 | No (FEBAN required) |
| SUBC / SUBD | Credit / Debit | Field office generic | BANK + BANK_SUB | Z7 | Yes (algo 015) |

### Posting Rule Selection Logic (T028G)
```
Input:  VGTYP (format group) + VGEXT (external transaction code) + VOZPM (payment indicator)
Output: VGINT (posting rule) + INTAG (algorithm)
```

- T028G has 1,025 entries mapping ext codes to internal posting rules
- Each bank format (T028B) defines which VGTYP to use
- VGEXT comes from MT940 field :61: subfield (transaction type code)
- VOZPM distinguishes credit vs debit when ext code is ambiguous

### Post Type (T028G.BUODO)
| Post Type | Meaning |
|-----------|---------|
| 1 | Debit bank, credit offset |
| 2 | Credit bank, debit offset |
| 4 | Debit bank, clear on sub-bank (outgoing clearing) |
| 5 | Credit bank, clear on sub-bank (incoming clearing) |

## Clearing Algorithms

### Algorithm 000 -- No Interpretation
- Posts to GL only, no automatic clearing attempt
- Items land in FEBAN queue for manual processing
- Used by: Treasury Manual tier, interest postings, unallocated items
- Volume: ~14.5% of items

### Algorithm 001 -- Standard Matching
- Matches by document number and amount
- Used for: incoming payments at HQ (SocGen, Citibank)
- Requires: BELNR or reference number in bank statement

### Algorithm 013 -- Check Number Matching
- Matches by check number from MT940 against PAYR table
- Used for: physical check clearing (ICTP mainly)
- Requires: check number in Tag 86 text, PAYR entry exists

### Algorithm 015 -- Clear by Assignment (ZUONR)
- **THE dominant mechanism: 85.5% of all cleared items**
- Matches bank statement reference to ZUONR field on open FI items
- Used by: ALL field office accounts (SUBC/SUBD), plus HQ for transfers
- Matching chain: MT940 reference -> search string extracts value -> compared to BSID/BSIK ZUONR
- Speed: 61% same-day clearing (XRT940 format)

### Algorithm 019 -- DME File Matching
- Matches bank statement to original DME payment file sent to bank
- Used for: Citibank Worldlink payments (HQ), SocGen bulk payments
- Requires: DME file reference in statement (PREF/01#### or EF/01########-)
- Search strings: SOG_DME, CIT_DME patterns in T028D

## GL Account Architecture

### Account Ranges and Symbols

| Range | Symbol | Purpose | Cleared? | Open Items (2024-2026) |
|-------|--------|---------|----------|----------------------|
| 10xxxxx | BANK | Permanent bank ledger | **NEVER** | 222,063 (normal) |
| 11xxxxx | BANK_SUB | Clearing (sub-bank) account | Yes | 2,996 (99.4% cleared) |
| 12xxxxx | BANK_TECH | Legacy technical | Phasing out | 28 |
| 13xxxxx | OFFSET_TECH | Legacy offset | Phasing out | 26 |

### Why 10xxxxx Is Never Cleared
- 10xxxxx represents the actual bank balance in SAP
- Every bank statement line creates a posting here (debit or credit)
- The balance of 10xxxxx should match the bank's own ledger
- Clearing would destroy the audit trail of bank movements
- "Open items" on 10xxxxx = every individual bank transaction ever posted (cumulative)

### 11xxxxx Clearing Health
- Total items posted to 11xxxxx: 536,541
- Cleared items: 533,545 (99.4%)
- Open items: 2,996
- Of open items: **87.8% are <30 days old** = current processing queue, NOT backlog
- True aged items (>90 days): <3% of open = genuinely stuck or timing differences

### 12xxxxx / 13xxxxx Legacy
- Being phased out
- 28 + 26 = 54 open items remaining
- No new postings expected
- Candidates for cleanup/write-off review

## Clearing Chain (from BSAS Analysis)

### AUGBL Prefix Distribution
| AUGBL Prefix | % of Clearings | Source |
|-------------|---------------|--------|
| 01xxxxxxxx | 64.5% | F110 payment documents (automatic payments that clear the sub-bank) |
| 35xxxxxxxx | 31.8% | Z7 clearing documents created during EBS import (algorithm-matched) |
| 20xxxxxxxx | 2.1% | Manual clearing (FEBAN / F-03) |
| Other | 1.6% | Reversals, corrections |

### Clearing Speed
| Timeframe | Cumulative % |
|-----------|-------------|
| Same day | 55.3% |
| Within 3 days | 76.4% |
| Within 7 days | 88.1% |
| Within 30 days | 99.3% |
| >30 days | 0.7% |

### Clearing Document Statistics
- Average items per clearing doc: 5.1
- Maximum items per clearing doc: 1,882 (batch clearing)
- Median items per clearing doc: 2

## Clearing Rates by Posting Rule (Verified)

| Rule | Total Items | Cleared | Rate | Notes |
|------|-------------|---------|------|-------|
| SUBD | 87,581 | 83,057 | 94.8% | FO debit, algo 015 |
| 102O | 16,589 | 15,994 | 96.4% | HQ outgoing clearing |
| SUBC | 6,354 | 6,028 | 94.9% | FO credit, algo 015 |
| TECD | 1,196 | 1,153 | 96.4% | Treasury debit |
| MXXD | 4,617 | 4,563 | 98.8% | Manual format, cleared via FEBAN post-processing |
| 102I | 9,206 total | 1,623/1,629 on 11xxx | 99.6%* | *Of items that post. 82% have BELNR=`*` (no FI doc) |

### 102I Root Cause (CRITICAL CORRECTION)

The initial analysis showed "29.2% clearing" for 102I which was **wrong**. The breakdown:
- 9,206 total 102I items
- 7,577 (82%) have BELNR=`*` = **no FI document created by design**
- These are ACH returns, notifications of change, incorrect routing numbers
- Tag 86 text confirms: "ACH CREDIT NOTIF. OF CHG.", "INCORRECT TRANSIT/ROUTING NO."
- Only 1,629 items actually post to 11xxxxx accounts
- Of those: **1,623 cleared = 99.6%**
- The system correctly identifies and filters unmatchable items

## Search Strings (T028D, 331 entries)

### Key Patterns

| Search String ID | Pattern | Purpose | Used By |
|-----------------|---------|---------|---------|
| FO_PAYM_DOC | `31########` | Field office payment document numbers | All XRT940 accounts |
| SOG03_PAYM_DOC | `(/2######/)` | F110 payment docs (SocGen format) | SOG_FR accounts |
| CIT_PAYM_DOC | `REF 0002######` | Citibank payment document reference | CIT04_US, CIT21_CA |
| SOG_DME | `PREF/01####` | DME file reference (SocGen bulk) | SOG_FR (algo 019) |
| CIT_DME | `EF/01########-` | DME file reference (Citibank Worldlink) | CIT04_US (algo 019) |
| SOG_CHK | `CHK######` | Check number (SocGen) | SOG_FR (algo 013) |

### How Search Strings Work
1. Algorithm receives Tag 86 text from MT940
2. Searches for pattern defined in T028D
3. Extracts the matched portion (e.g., payment doc number)
4. Uses extracted value to search against open items (BSID/BSIK ZUONR, BELNR, or PAYR check number)
5. If match found + amount matches -> clearing document created

## ZUONR Patterns (Assignment Field)

| ZUONR Pattern | Items | Clearing Rate | Description |
|--------------|-------|--------------|-------------|
| 3100x... | 9,338 | High | Field office payment docs |
| 2xxx... | 51,740 | 95% | Payment document numbers |
| NONREF | 12,789 | 108%* | No reference found |
| BANK CHARG | 4,658 | 32% | Bank charges (often no matching item) |
| CHECK##### | 2,341 | 89% | Check numbers |

*NONREF items clear at >100% because some get cleared by multiple mechanisms (BSAS matching finds them through alternative paths even without ZUONR).

## BA (Business Area) Determination

### Calling Chain
```
EBS posting triggers -> GGB1 (substitution framework)
    -> YRGGBS00 (substitution program)
        -> FORM U910 (substitution rule)
            -> YCL_FI_ACCOUNT_SUBST_READ (ABAP class)

EBS user exit:
    YTFBE001 (enhancement)
        -> EXIT_RFEBBU10_001
            -> ZXF01U01
                -> YTBAM001 (BA mapping table)
```

### BA Determination Tables

**YTFI_BA_SUBST** (129 entries) -- Modern range-based rules (post Oct-2022)
- Maps account ranges + cost center ranges to Business Area
- Takes priority over legacy YBASUBST
- Example: GL 5xxxxx + cost center 3xxx* -> BA = GEF

**YBASUBST** (752 entries) -- Legacy table
- Direct account -> BA mapping
- 9 entries still have BA=X (for IIEP/UBO special cases)
- Being gradually replaced by YTFI_BA_SUBST ranges

### BA Distribution (from FEBEP postings)
| Business Area | % |
|--------------|---|
| GEF | 82.3% |
| PFF | 13.0% |
| X (special) | 1.6% |
| OPF | 1.3% |
| Other | 1.8% |

## System Health Dashboard

### FEBEP (Bank Statement Items)
| Metric | Value |
|--------|-------|
| Total items (2024-2026) | 223,710 |
| Posted (BSTAT != blank) | 99.9% |
| With FI document (BELNR != `*`) | ~82% |
| BELNR=`*` (no posting by design) | ~18% |

### FEBKO (Statement Headers)
| Metric | Value |
|--------|-------|
| Total statements (2024-2026) | 31,416 |
| Fully posted (ASTAT=8) | 31,141 (99.1%) |
| Partially posted (ASTAT=5) | 152 (0.5%) |
| Not posted (ASTAT=2) | 90 (0.3%) |
| Error (ASTAT=0) | 33 (0.1%) |

### FEBRE (Tag 86 Text)
| Metric | Value |
|--------|-------|
| Total rows (2024-2026, KUKEY-filtered) | 964,055 |
| Fields | 4 (KUKEY, SESSION, SEESSION_ITEM, VWEZW) |
| Avg rows per FEBEP item | ~4.3 |

### 11xxxxx Clearing Account
| Metric | Value |
|--------|-------|
| Total items posted | 536,541 |
| Cleared | 533,545 (99.4%) |
| Open | 2,996 |
| Open <30 days | 87.8% (current queue) |
| Avg clearing time | 2.3 days |
| Same-day clearing (XRT940) | 61% |

## Tables in Gold DB

### EBS Core Tables
| Table | Rows | Fields | Description |
|-------|------|--------|-------------|
| FEBEP_2024_2026 | 223,710 | 27 base + 7 enriched | Bank statement line items |
| FEBKO_2024_2026 | 31,416 | 62 | Statement headers (all DD03L fields) |
| FEBRE | 964,055 | 4 | Tag 86 raw text (KUKEY-filtered) |

### Clearing & GL Tables
| Table | Rows | Fields | Description |
|-------|------|--------|-------------|
| BSAS | 553,786 | bank items | Cleared bank items with AUGBL+AUGDT enriched (100%) |

### Configuration Tables
| Table | Rows | Description |
|-------|------|-------------|
| T028B | 169 | Bank -> format mapping (EFART, statement format) |
| T028G | 1,025 | Ext code -> posting rule transformation |
| T028D | 331 | Search string definitions for algorithms |
| T028E | 1,316 | Posting key definitions |
| T012K | 402 | Bank GL account mapping |
| YBASUBST | 752 | Legacy BA substitution |
| YTFI_BA_SUBST | 129 | Modern range-based BA substitution |
| TCURR | 54,993 | Exchange rates |
| TCURF | 2,614 | Exchange rate factors |

### Gold DB Path
```
Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db
```

### Query Patterns
```sql
-- Statement health check
SELECT ASTAT, COUNT(*) FROM FEBKO_2024_2026 GROUP BY ASTAT;

-- Clearing rate by posting rule
SELECT VGINT, COUNT(*) as total,
       SUM(CASE WHEN AUGBL IS NOT NULL THEN 1 ELSE 0 END) as cleared
FROM FEBEP_2024_2026
WHERE KOESSION LIKE '11%'
GROUP BY VGINT;

-- Open items aging on 11xxxxx
SELECT
  CASE WHEN julianday('now') - julianday(BUDAT) < 30 THEN '<30d'
       WHEN julianday('now') - julianday(BUDAT) < 90 THEN '30-90d'
       ELSE '>90d' END as age_bucket,
  COUNT(*)
FROM BSAS WHERE HKONT LIKE '11%' AND AUGBL IS NULL
GROUP BY age_bucket;

-- Tag 86 text for specific statement item
SELECT f.VWEZW FROM FEBRE f
WHERE f.KUKEY = (SELECT KUKEY FROM FEBEP_2024_2026 WHERE BELNR = '<docnum>' LIMIT 1);
```

**CRITICAL**: Always `PRAGMA table_info(<table>)` before querying. Field names vary.

## Companion & Knowledge Assets

### Interactive Companion
- **File**: `bank_statement_ebs_companion.html`
- **Location**: `Zagentexecution/mcp-backend-server-python/`
- **Tabs**: 13 tabs, v2.0+
- **Content**: System health, clearing rates, tier comparison, algorithm analysis, GL architecture, Tag 86 samples, search string catalog, ZUONR patterns, BA determination, open item aging

### Knowledge Documentation
- **File**: `bank_statement_ebs_architecture.md`
- **Location**: `knowledge/domains/FI/`
- **Content**: 22 sections across 3 parts (Configuration, Processing, Analysis)

## Key Transactions

| Transaction | Purpose |
|-------------|---------|
| FF_5 | Import bank statement (MT940 file) |
| FF67 | Memo record and bank statement entry |
| FEBAN | Manual bank statement post-processing (clearing queue) |
| FEBA | Display bank statement |
| FEBP | Post bank statement |
| FF.5 | Import electronic bank statement (variant of FF_5) |
| FI12 | House bank master data |
| OT83 | Bank statement format configuration |
| BNK_MONI | BCM batch monitor (outbound payment files) |

## Relationship to Payment Domain

Bank statements and payments are **complementary, not alternatives**:

```
OUTBOUND (Payment -> Bank):
  F110 -> REGUH -> BCM -> DMEE -> Bank File -> Bank
  [Covered by sap_payment_bcm_agent]

INBOUND (Bank -> Reconciliation):
  Bank -> MT940 -> FF_5 -> FEBKO/FEBEP -> Posting -> Clearing
  [Covered by THIS agent]
```

The two domains meet at the clearing point:
- Payment creates an open item on 11xxxxx (debit for outgoing payment)
- Bank statement import creates the matching entry on 11xxxxx (credit from bank confirmation)
- Algorithm matches them -> clearing document (Z7 or AUGBL) -> both items closed

### Cross-Domain Queries
When analyzing end-to-end payment lifecycle:
1. Use `sap_payment_bcm_agent` for: F110 run analysis, BCM batch status, REGUH items, payment methods
2. Use `sap_bank_statement_recon` (this agent) for: statement import status, clearing success, open items, algorithm performance
3. Join point: BSAS.AUGBL links payment documents to clearing documents

## Diagnostic Playbook

### "Why didn't this item clear?"
1. Check FEBEP.VGINT -- what posting rule was assigned?
2. Check T028G -- what algorithm (INTAG) does that rule use?
3. If algo 015: check if ZUONR was populated on the original payment FI doc
4. If algo 019: check if DME file reference exists in Tag 86 (FEBRE.VWEZW)
5. If algo 013: check PAYR for matching check number
6. If algo 000: item is by design manual -- check FEBAN queue

### "Are we behind on reconciliation?"
1. Query 11xxxxx open items: `SELECT COUNT(*) FROM BSIS WHERE HKONT LIKE '11%'`
2. Check aging: 87.8% <30 days is NORMAL (current processing queue)
3. Only items >90 days are genuinely stuck
4. Check FEBKO ASTAT: any statements not fully posted (ASTAT != 8)?
5. Check FEBAN: items pending manual clearing

### "Statement import failed"
1. Check FEBKO for the statement: ASTAT=0 indicates error
2. Verify format mapping in T028B for the bank
3. Check if ext code exists in T028G for the format group
4. Missing ext code -> posting rule 999 (unallocated) -> needs FEBAN
5. Check SM37 for JOBBATCH job status

### "What bank format does account X use?"
1. Look up T012K for the house bank + account ID
2. T028B maps house bank to EFART (E=electronic, M=manual) and format group
3. Format group determines which T028G rules apply
4. XRT940 = field office generic, SOG_FR/CIT04_US = HQ detailed, TR_TRNF = treasury manual

## Statement Format Mapping (T028B, 169 entries)

### Key Formats
| Format | Banks | EFART | Tier | Accounts |
|--------|-------|-------|------|----------|
| SOG_FR | Societe Generale (France) | E | HQ Detailed | 12 |
| CIT04_US | Citibank (USD) | E | HQ Detailed | ~5 |
| CIT21_CA | Citibank (CAD) | E | HQ Detailed | ~3 |
| XRT940 | All field office banks | E | FO Generic | 111 |
| TR_TRNF | Treasury transfers | M | Treasury Manual | 18 |

## Extraction Rules

### FEBEP Extraction
- **Date scope**: 2024-2026 only (per project rules)
- **Field splitting**: Max 8 fields per WHERE clause chunk. Split into 2 extractions, merge by KUKEY
- **Key fields first chunk**: KUKEY, ESESSION, ESNUM, VGINT, BELNR, BUDAT, KWBTR, WBTRG
- **Key fields second chunk**: KUKEY, AUGBL, AUGDT, ZUESSION, HESSION, KOESSION, VGEXT, VOZPM

### FEBRE Extraction
- **MUST filter by KUKEY range** matching FEBEP's KUKEY range
- Without filter: 3.7M+ rows, will timeout
- Fields: KUKEY, SESSION, SEESSION_ITEM, VWEZW (only 4 fields needed)

### FEBKO Extraction
- Full DD03L field list (62 fields) -- small table, extract all
- Filter by AESSION (statement date) for date range

### BSAS Enrichment
- Filter: HKONT LIKE '1%' (bank accounts only)
- Must include: AUGBL, AUGDT (clearing document and date)
- Join with FEBEP via: BSAS.BELNR = FEBEP.BELNR or BSAS.AUGBL = FEBEP.BELNR
