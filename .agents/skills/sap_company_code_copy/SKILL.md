---
name: SAP Company Code Copy
description: >
  Complete checklist and validation protocol for copying a company code in SAP (EC01/EC02).
  Covers: transport analysis, number range gap detection (OBH2), posting period setup (FI/FM/CO/PS/AA),
  FBZP payment chain validation, house bank verification, copy inconsistency detection (country vs bank mismatch),
  and 41-task post-copy manual checklist across 10 functional areas. Use this skill whenever a company code
  is being created by copying from an existing one.
maturity: production
origin: Session #019 — ad hoc analysis of D01K9B0CBF (STEM/China Institute copy)
---

# SAP Company Code Copy Skill

> **Source authority**: Session #019 live validation against D01 (2026-03-26). 36 customizing objects,
> 682 table entries, 12 number range objects, 6 automated checks, 41 manual tasks catalogued.
> Cross-referenced with Transport Intelligence 21-module knowledge base.
> Proven on: D01K9B0CBF (FI core, JP_LOPEZ) + D01K9B0F3V (FM, I_KONAKOV) for company code STEM (China Institute).

---

## NEVER Do This

> [!CAUTION]
> - **Never transport number ranges (NROB)** — always copy via OBH2 or create manually in each environment. Transporting overwrites counters.
> - **Never transport T001B (posting periods)** — open periods manually via OB52 per environment.
> - **Never assume a copy is complete** — EC01 copies customizing tables but NOT: number ranges, posting periods, user tolerance assignments, FBZP bank ranking (T042I), master data (vendors/customers/cost centers/fund centers).
> - **Never skip the country/currency consistency check** — copies inherit house banks from the source, which may be in a completely different country.
> - **Never release the transport without validating the FBZP chain** — T042 → T042B → T042E → T042C → T042I → T012K. If any level is missing, F110 fails silently.
> - **Never skip authorization role updates** — users get "no authorization for company code" until F_BKPF_BUK is updated in PFCG.

---

## When to Use This Skill

- A new company code is being created via EC01 (copy) or EC02
- A transport contains T001 + SKB1 + T012 + T042 entries for a new BUKRS
- Someone asks "what do I need to do after copying a company code?"
- Pre-import review of a company code creation transport

---

## The Copy Creates (automatically via EC01)

| What | Tables | Typical Volume |
|------|--------|---------------|
| Company code definition | T001, T001Q, T001A | 1-4 entries |
| Company code address | ADRC, ADR2-ADR13, ~40 sub-tables | ~38 entries (SAP artifacts) |
| GL account assignment (co code segment) | SKB1 | 200-600 accounts. **Sync P01→D01 via `sap_master_data_sync` skill** |
| GL master (chart of accounts) | SKA1, SKAT | ~2,500 accounts. Sync P01→D01 first (69 accounts were missing #034) |
| Cost elements | CSKA, CSKU, CSKB | ~535 master + ~3,800 CO area. Sync P01→D01 (26+92+174 were missing #034) |
| Account assignment objects (FM) | AAACC_OBJ | 5-10 entries |
| House banks + accounts | T012, T012D, T012K, T012T | 5-20 entries |
| Cash planning groups | T035D, T035U | 3-12 entries |
| Payment program (partial) | T042, T042B, T042E, T042T | 5-10 entries |
| Tolerance groups | T043G, T043S, T043T, T043GT, T043ST | 15-25 entries |
| Invoice verification tolerances | T169G, T169P, T169V | 10-15 entries |
| Dunning assignment | T047 | 1 entry |
| Asset accounting | T093B, T093C, T093D, T093U, T093V | 5-10 entries |
| Controlling area | TKA00, TKA01, TKA02, TKA07, TKA09, TKT09 | 5-10 entries |
| Consolidation unit | T882 | 1-2 entries |
| MM valuation | MARV, ATPRA | 2 entries |
| View/template data | V_T001 (VDAT), ADDRESS (TDAT), CAREAMAINT (CDAT) | SAP artifacts |

**Total typical:** 30-40 objects, 400-800 table entries (keys).

---

## The Copy Does NOT Create (must be done manually)

### Number Ranges — OBH2

Run `OBH2` (Copy Company Code Number Ranges) from a reference company code in **each target environment**.

| NR Object | Description | TCode | Module | Impact If Missing |
|-----------|-------------|-------|--------|-------------------|
| RF_BELEG | FI Document Numbers | FBN1 | FI | ALL FI postings fail — no document number |
| ANLAGENNR | Asset Number Ranges | AS08 | AA | Cannot create assets (AS01) |
| FIAA-BELNR | Asset Accounting Documents | SNUM | AA | Depreciation runs (AFAB) fail |
| RK_BELEG | CO Document Numbers | KANK | CO | CO postings/allocations fail |
| BUED_DOCNR | FM Entry Document Number | SNUM | PSM-FM | Budget entries (FMBB) fail |
| BUED_DOFAM | Budgeting Document Family | SNUM | PSM-FM | Budget document families fail |
| BULI_DOCNR | FM Budget Line Item Number | SNUM | PSM-FM | FM line items fail |
| FM_POSIT1 | FM Commitment Item Position | SNUM | PSM-FM | Commitment item numbering fails |
| FM_BELEG2 | FM Budget Monitoring Docs | SNUM | PSM-FM | Budget monitoring docs fail |
| CF_DOC | Fiscal Year Change Document | SNUM | PSM-FM | Year-end carry-forward fails |
| CAJO_DOC2 | Cash Journal Documents | FBCJC0 | FI | Cash journal (FBCJ) fails |
| RP_REINR | Trip Number Ranges | SNUM | Travel | Travel expense creation fails |

**Validation query:** `SELECT OBJECT, COUNT(*) FROM NRIV WHERE SUBOBJECT = '{new_bukrs}' GROUP BY OBJECT`
Compare against a reference company code. Missing objects = gaps.

### Posting Periods (per module, per environment)

| Module | TCode | Table | Order | Impact If Skipped |
|--------|-------|-------|-------|-------------------|
| FI | OB52 | T001B | 1st (do first) | ALL FI postings blocked |
| PSM-FM | FMBS | BPBKFM | 2nd | No budget postings, no commitments |
| CO | OKP1 | COKP | 3rd | CO postings blocked (FI still creates CO docs but they queue) |
| PS | OKP1 | COKP | 3rd (same as CO) | WBS postings blocked (only if PS used) |
| AA | OAAQ | T093D | 4th | Depreciation runs (AFAB) fail |

**Order matters:** FI must be open before FM/CO/AA can post, since all modules generate FI documents.

### FBZP Payment Chain (6 levels)

```
T042 (Paying CoCode) → T042B (Pmt Methods/CoCode) → T042E (Pmt Methods/Country)
    → T042C (Pmt/CoCode/Country) → T042I (Bank Ranking) → T012K (Bank Accounts)
```

**EC01 copies:** T042, T042B, T042E (levels 1-3)
**EC01 does NOT copy:** T042C, T042I (levels 4-5) — **must be configured manually via FBZP**

Without T042C + T042I, F110 payment runs produce **empty proposals with no error message**.

### Multi-Transport Import Order

Company code creation often spans **multiple transports** by different team members (e.g., FI team + FM team). Critical rules:

1. **FI core transport FIRST** — creates T001 (company code), SKB1 (GL accounts), banking, tolerances
2. **FM transport SECOND** — adds FM Area assignment to T001, creates FM01, hierarchy variants
3. **CO/AA/other transports AFTER** — depend on company code + GL accounts existing

**Conflict detection:** If multiple transports modify the same table (e.g., T001, T882), the last import wins for overlapping fields. Always import FI first so FM can add FM-specific fields on top.

**T001A (Group Currency):** Added separately from T001. Contains GWAE2/GWAE3 for parallel valuation in consolidated reporting. Often added after initial copy when group currency is decided.

---

## Copy Inconsistency Detection

When a company code is copied from a source in a different country, these mismatches occur:

| Check | How to Detect | Example |
|-------|--------------|---------|
| Country vs house bank | T001.LAND1 ≠ T012 bank country | Source=ET (Ethiopia), Target=CN (China) but bank=CBE (Ethiopian) |
| Currency vs bank accounts | T001.WAERS ≠ T012K account currencies | CoCode currency=USD but bank accounts in ETB |
| Payment method country | T042E.LAND1 ≠ T001.LAND1 | Payment methods defined for ET, not CN |
| Bank account numbers empty | T012K.BANKN = blank | Copy creates structure but not real account numbers |
| Planning group labels | T035U texts reference source currencies | "ETB Account 1" instead of "CNY Account 1" |

**Automated validation script:** `transport_bank_validate.py` in `Zagentexecution/mcp-backend-server-python/`

---

## Complete Post-Copy Checklist (41 Tasks)

### FI — Financial Accounting (8 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 1 | Assign users to tolerance groups | OB57 | CRITICAL |
| 2 | Verify doc type → number range mapping | OBA7 | HIGH |
| 3 | Verify automatic account determination (GR/IR, FX, cash discount, tax) | OBYC | HIGH |
| 4 | Verify tax codes for target country | FTXP / OBBG | HIGH |
| 5 | Set up withholding tax types/codes | OBWP / OBWQ | MEDIUM |
| 6 | Check substitution / validation rules include new BUKRS | GGB1 / GGB0 | MEDIUM |
| 7 | Verify exchange rate types and maintain rates | OB07 / OB08 | MEDIUM |
| 8 | Verify correspondence forms and programs | OB77 / OB78 | LOW |

### Bank / Payments (7 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 9 | Replace/update house bank for target country | FI12 | CRITICAL |
| 10 | Configure T042C — payment methods per co code per country | FBZP | CRITICAL |
| 11 | Configure T042I — bank ranking order | FBZP | CRITICAL |
| 12 | Verify DMEE payment format tree | DMEE / OBPM1 | HIGH |
| 13 | Recreate OBPM4 selection variants (never transported) | OBPM4 | HIGH |
| 14 | Configure electronic bank statement mapping | OT83 / FF.5 | MEDIUM |
| 15 | Update planning group descriptions for correct currencies | OT42 | LOW |

### PSM-FM — Funds Management (7 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 16 | Verify FM area assignment | OF01 | HIGH |
| 17 | Verify/create FM derivation rules for new BUKRS | FMDERIVE | CRITICAL |
| 18 | Create fund centers | FMSA | HIGH |
| 19 | Create funds (GEBER) | FM5I | HIGH |
| 20 | Create/verify commitment items | FMCI | MEDIUM |
| 21 | Verify AVC (budget availability control) | FMBB / FM5T | MEDIUM |
| 22 | Configure budget carry-forward settings | FMBN / 2KEC | LOW |

### CO — Controlling (4 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 23 | Create cost centers + hierarchy | KS01 | HIGH |
| 24 | Set default cost center / profit center for GL accounts | OKB9 | HIGH |
| 25 | Create profit centers + hierarchy | KE51 | MEDIUM |
| 26 | Add to CO allocation cycles (if applicable) | KSV5 / KSU5 | LOW |

### AA — Asset Accounting (3 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 27 | Verify asset class → GL account determination | AO90 | HIGH |
| 28 | Verify depreciation keys/useful lives for target country tax rules | AFAMS | MEDIUM |
| 29 | Create asset classes if needed | OAOA | LOW |

### MM — Materials Management / Invoice Verification (3 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 30 | Review invoice tolerance values for target country | OMR6 | HIGH |
| 31 | Verify purchasing organization assignment | OX17 | HIGH |
| 32 | Verify GR/IR clearing account | OBYC (WRX) | MEDIUM |

### FI-AR — Accounts Receivable / Dunning (2 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 33 | Verify dunning procedure assignment | FBMP | LOW |
| 34 | Verify dunning form assignment | OB96 | LOW |

### Master Data (3 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 35 | Extend vendors to new company code | FK01 / XK01 | CRITICAL |
| 36 | Extend customers to new company code | FD01 / XD01 | MEDIUM |
| 37 | Create bank directory entries for target country | FI01 | MEDIUM |

### Security (2 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 38 | Add new BUKRS to authorization roles (F_BKPF_BUK etc.) | PFCG | CRITICAL |
| 39 | Assign updated roles to users | SU01 | CRITICAL |

### Consolidation / Reporting (2 tasks)

| # | Task | TCode | Priority |
|---|------|-------|----------|
| 40 | Verify consolidation group assignment | OC13 | LOW |
| 41 | Add to reporting hierarchies / BI extractors | SE16 / custom | LOW |

---

## Automation Assets

| Asset | Location | Purpose |
|-------|----------|---------|
| `transport_adhoc_read.py` | `Zagentexecution/mcp-backend-server-python/` | Extract E071 + E071K objects for any transport |
| `transport_bank_validate.py` | `Zagentexecution/mcp-backend-server-python/` | 6-check automated validation (GL recon, FBZP chain, country match, bank accounts) |
| `transport_companion_*.html` | `Zagentexecution/` | Generated HTML companion page with full analysis |
| Transport Object Taxonomy | `knowledge/domains/Transport_Intelligence/transport_object_taxonomy.md` | Object classification reference |

---

## Companion Page Generation

When analyzing a company code copy transport, generate an HTML companion page with:

1. **Executive summary** — what company code, what it does, source identification
2. **Functional area breakdown** — every object explained user-friendly
3. **Pre-import safety checklist** — XPRA, NROB, OBJFUNC, ALARM checks
4. **Automated validation results** — GL reconciliation, FBZP chain, country match, bank accounts
5. **Copy inconsistency analysis** — country vs bank, currency mismatches
6. **Number range gap table** — compare against reference company code
7. **Open posting periods checklist** — FI, FM, CO, PS, AA with transactions
8. **Complete 41-task manual checklist** — grouped by module with priority
9. **Mitigation plan** — prioritized fix list for identified issues
10. **FBZP chain diagram** — visual showing which levels are OK/MISSING

Template: `Zagentexecution/transport_companion_D01K9B0CBF.html`

---

## Summary Statistics

- **7 CRITICAL** tasks (blocks basic operations)
- **12 HIGH** tasks (blocks specific modules)
- **11 MEDIUM** tasks (degraded functionality)
- **11 LOW** tasks (cosmetic / edge cases)
- **12 number range objects** to verify
- **5 posting period types** to open
- **6 FBZP chain levels** to validate
- **5 copy inconsistency checks** to run
