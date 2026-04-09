# Business Partner / Vendor Domain — UNESCO SAP Intelligence

**Created:** 2026-04-08 (Session #048)
**Trigger:** INC-000006073 revealed vendor master data gap (KTOKK→AKONT chain)

## Domain Scope

SAP Vendor Master Data (classic model) + Business Partner (S/4 path): vendor general data, company code data, bank details, payment methods, reconciliation accounts, withholding tax, dunning, and the relationship chain that connects vendor account groups to GL accounts to posting behavior.

## UNESCO Vendor Landscape

### Company Codes with Vendors
UNES, IIEP, UBO, MGIE, ICBA, UIL, UIS, IBE, ICTP (9 company codes)

### Vendor Account Groups (KTOKK) — Key to Reconciliation GL

| KTOKK | Description | AKONT (typical in IIEP) | Usage |
|---|---|---|---|
| **UNES** | UNESCO employees (International Staff) | 2021042 | Standard personnel vendor |
| **SCSA** | Service Contract / SSA / Non-reimbursable | 2021011 | Consultants, SSA holders |
| **STAF** | Local staff | varies | National officers |
| **EMPL** | General employees | varies | Other employee types |

### The KTOKK→AKONT→GGB1 Chain (discovered via INC-000006073)

```
LFA1.KTOKK (vendor account group)
  → determines → LFB1.AKONT (reconciliation GL account per company code)
    → determines → BSEG.HKONT (GL on posting line)
      → matches or misses → GGB1 substitution rules (GL-based conditions)
        → if missed → GSBER stays empty → posting fails
```

This chain is invisible in normal operations because same-company postings fill GSBER from the employee master before GGB1 needs to run. It only surfaces in intercompany scenarios.

## SAP Tables — Vendor Model

### Tier 1: Core Master Data (extract to Gold DB)

| Table | Content | Key Fields | Priority |
|---|---|---|---|
| **LFA1** | Vendor General Data | LIFNR, NAME1, KTOKK, LAND1, STCD1 | **HIGH** |
| **LFB1** | Vendor Company Code Data | LIFNR, BUKRS, AKONT, ZTERM, ZWELS, FDGRV | **HIGH** |
| **LFBK** | Vendor Bank Details | LIFNR, BANKS, BANKL, BANKN, KOINH, BVTYP, IBAN | **HIGH** |
| **LFBW** | Vendor Withholding Tax | LIFNR, BUKRS, WITHT, WT_WITHCD | MEDIUM |
| **LFB5** | Vendor Dunning Data | LIFNR, BUKRS, MABER, MAHNS | LOW |
| **LFC1** | Vendor Transaction Figures | LIFNR, BUKRS, GJAHR, UMSAV | LOW |

### Tier 2: Customer Model (mirror for intercompany)

| Table | Content | Key Fields | Priority |
|---|---|---|---|
| **KNA1** | Customer General Data | KUNNR, NAME1, KTOKD, LAND1 | MEDIUM |
| **KNB1** | Customer Company Code Data | KUNNR, BUKRS, AKONT, ZTERM | MEDIUM |

### Tier 3: Business Partner (S/4 convergence)

| Table | Content | Key Fields | Priority |
|---|---|---|---|
| **BUT000** | BP General Data | PARTNER, NAME_ORG1, BU_GROUP | LOW (if exists) |
| **BUT0BK** | BP Bank Details | PARTNER, BANKL, BANKN | LOW (if exists) |

### Tier 4: Configuration

| Table | Content | Key Fields | Already in Gold DB? |
|---|---|---|---|
| **T077K** | Vendor Account Groups (KTOKK definition) | KTOKK, TXT30 | No |
| **T077S** | Customer Account Groups | KTOKD, TXT30 | No |
| **TIBAN** | IBAN directory | BANKS, BANKL, IBAN, BKREF | No |
| **BNKA** | Bank master data | BANKS, BANKL, BANKA, SWIFT | No (check T012K) |

## Relationships to Other Domains

### Travel Domain
```
LFA1.KTOKK → LFB1.AKONT → BSEG.HKONT → GGB1 rule coverage
                                        → GSBER derivation chain
ZCL_IM_TRIP_POST_FI (BAdI) reads PA0027 for vendor GSBER fallback
ZXTRVU05 exit processes vendor lines per BUKRS
YFI_LFBK_TRAVEL_UPDATE reads LFA1.KTOKK + LFBK for travel flag
```

### Payment Domain
```
LFB1.ZWELS (payment methods) → F110 payment run selection
LFB1.AKONT → REGUH clearing account
LFBK.BVTYP → partner bank type → DMEE tree selection
LFBK.IBAN → SWIFT routing → bank statement matching (FEBEP)
T012K (house banks) → LFBK (vendor banks) → payment matching
```

### Treasury Domain
```
LFBK.BANKS+BANKL → BNKA/T012K → house bank identification
TIBAN → IBAN validation → SWIFT (MT940/MT103) matching
LFB1.FDGRV → cash management group → liquidity forecast
```

### FI Domain
```
LFB1.AKONT → SKA1/SKB1 (GL master) → chart of accounts
LFB1.ZTERM → payment terms → aging analysis
LFB1.FDGRV → cash discount group
BSIK/BSAK (open/cleared vendor items) → uses LFB1.AKONT as recon
```

## Brain Edges

```
LFA1 --HAS_COMPANY_DATA--> LFB1 [1:N by BUKRS]
LFA1 --HAS_BANK_DATA--> LFBK [1:N by BANKS+BANKL+BANKN]
LFA1.KTOKK --DETERMINES--> LFB1.AKONT [account group → recon GL]
LFA1.KTOKK --CONFIGURED_BY--> T077K [account group definition]
LFB1.AKONT --POSTS_TO--> SKA1/SKB1 [GL master]
LFB1.AKONT --MATCHES--> GGB1.3IIEP###002 [substitution rule GL condition]
LFB1.ZWELS --SELECTS--> F110 [payment method → payment run]
LFB1 --LINKS_TO--> BSIK [open items] / BSAK [cleared items]
LFBK.BVTYP --ROUTES--> DMEE [payment format tree]
LFBK.IBAN --MATCHES--> FEBEP [bank statement items]
LFBK --HAS_IBAN--> TIBAN [IBAN directory]
KNA1 --MIRROR_OF--> LFA1 [customer side of intercompany]
KNB1 --MIRROR_OF--> LFB1 [customer company code data]
```

## Extraction Strategy

**Script:** `Zagentexecution/sap_data_extraction/scripts/extract_vendor_model.py`

All tables use field splitting (wide tables exceed RFC 512-byte buffer).
Filter: Company codes IN (IIEP, UNES, UBO, MGIE, ICBA, UIL, UIS, IBE, ICTP).
No date filter needed — master data tables are full extracts.

## Incidents

| Ticket | Date | Vendor Impact | Root Cause |
|---|---|---|---|
| INC-000006073 | 2026-04-08 | KTOKK=SCSA → AKONT=2021011 → GGB1 miss | Wrong vendor account group since 2016 |
