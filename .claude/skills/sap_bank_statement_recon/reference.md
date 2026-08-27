# sap_bank_statement_recon — referencia detallada

> Extraído de `SKILL.md` para que su cuerpo no ocupe contexto en cada turno.
> Lo carga quien lo necesite; el índice está en `SKILL.md`.

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

## When Implementing Custom Recon Programs (anti-patterns to avoid)

These rules were distilled from INC-000006906 (Session #057–058) and the frozen YTBAE002 codebase. Any new or modified custom recon program must comply.

### Rule R1 — No MODE 'E' CALL TRANSACTION inside any loop

```abap
" DO NOT WRITE:
CALL TRANSACTION 'FB08' USING bdc_tab MODE 'E'
                              MESSAGES INTO messtab.
```

MODE 'E' opens SAPGUI on BDC error. On slow-WAN paths (UNESCO field offices) the cumulative GUI handshake breaches `rdisp/max_wprun_time` and the caller's LDB fetch TIME_OUTs with a stack pointing at the LDB, not at the CALL TRANSACTION. See Claim 54 / INC-000006906. Use MODE 'N' + `MESSAGES INTO` + post-loop error reporting:

```abap
" DO WRITE:
CALL TRANSACTION 'FB08' USING bdc_tab MODE 'N'
                              MESSAGES INTO messtab.
" ... collect messtab throughout the loop, surface in final list.
```

### Rule R2 — Guard every RANGE before feeding it to an LDB / SELECT

```abap
" DO NOT WRITE:
LOOP AT lt_source INTO wa_source.
  APPEND <range_entry> TO lr_hkont.
ENDLOOP.
CALL FUNCTION 'LDB_PROCESS' LDBNAME='SDF' ... .

" DO WRITE:
LOOP AT lt_source INTO wa_source.
  APPEND <range_entry> TO lr_hkont.
ENDLOOP.
IF lr_hkont IS INITIAL.
  MESSAGE 'No open-item GL found — aborting to avoid full BSIS scan.' TYPE 'I'.
  RETURN.
ENDIF.
```

SAP's contract for empty IN-lists is "no filter" — which is the opposite of the developer's intent. See Claim 53 (latent, YTBAE002.abap:1366).

### Rule R3 — Do NOT resolve bank scope via YBANK_* sets if you don't need the Report-Painter hierarchy

If the program only needs the GLs of one house bank account, use `SELECT ... FROM SKB1 WHERE BUKRS+HBKID+HKTID` (what YTBAE002 does at `:1098`). Do not call `RS_SET_VALUES_READ` / `G_SET_GET_ALL_VALUES` on `YBANK_*` — those sets have 61% coverage gap (Claim 52) and you'll silently exclude active bank GLs.

If the program DOES need the hierarchy (cash-position by currency, etc.), the Report-Painter set API is correct — just understand Claim 52's preventive audit applies and run `ybank_set_coverage_check.py` after any config change.

### Rule R4 — Respect SKB1.XOPVW='X' as the canonical "open-item managed" flag

Bank sub-bank GLs (11xxxxx / 13xxxxx / 15xxxxx) MUST have `XOPVW='X'` on `SKB1` to participate in any open-item reconciliation. A missing `XOPVW` flag is a master-data bug that surfaces either as (a) the program silently produces no output, or (b) if the program has the R2 bug, as a TIME_OUT via an unbounded LDB scan. When diagnosing "why didn't this item clear?" check `SKB1.XOPVW` first.

### Rule R5 — Test every new recon program from a field-office VPN, not from HQ

A program that passes HQ testing (LAN RTT ~ microseconds) can still TIME_OUT from Maputo / IIEP / UIS if it has MODE 'E' BDC or any other network-coupled step. HQ reproduction is necessary but not sufficient. Always test with at least one slow-WAN user before release.

### Rule R6 — Surface BDC errors in the list, never via dialog

The pattern established by YTBAE002's `PROC_RECONCIL_MESS_ADD` (lines 754, 795, 840, 874) is correct: after each CALL TRANSACTION, copy `Y_MESSTAB` into an accumulator table (`GT_RECONCIL_MESS`), and at end of loop render the accumulator in the list output. This gives the user a complete view of all errors at once without any GUI interaction. Re-use this pattern.

---

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
