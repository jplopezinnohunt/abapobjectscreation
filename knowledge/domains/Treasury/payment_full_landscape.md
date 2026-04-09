# UNESCO SAP Payment Full Landscape

**Source**: BFM/TRS Handover Documentation (PDFs) + Gold DB analysis + CTS mining
**Session**: #021 (2026-03-27) — 100% PDF coverage achieved
**Companion**: `Zagentexecution/mcp-backend-server-python/payment_bcm_companion.html` (v4, 775KB, 12 tabs)

---

## The 4 UNESCO Payment Processes

| # | Name | Company Codes | F110 | BCM | Role |
|---|------|--------------|------|-----|------|
| 1 | Outside SAP | IBE, MGIE, ICBA, Field Offices | No | No | `YS:FI:D:DISPLAY__________:ALL` |
| 2 | F110 + Manual File Download | ICTP, UBO/Banco do Brazil, UIL (migrating), UNES checks (phasing out) | Yes | No | `Y_XXXX_FI_AP_PAYMENTS` |
| 3 | F110 + BCM (2 validations) + Coupa | UIS, IIEP, UIL/new SG bank, UBO/Citibank | Yes | Yes | `Y_XXXX_FI_AP_PAYMENTS` **OR** `YS:FI:M:BCM_MON_APP______:XXXX` (**NEVER BOTH**) |
| 4 | F110 + BCM (1 validation) + Coupa (2nd validation) | UNES HQ | Yes | Yes | Both roles (UNES-specific — see security risk) |

**Process 1 detail**: AO posts outgoing payment in SAP (clears vendor, debits sub-bank account). Creates transfer in local banking system OR writes cheque. No SAP payment file.

**Process 2 detail**: F110 creates payment file. User downloads to local directory. Manually uploads to bank portal (internet banking).

**Process 3 detail**: 2 BCM signatories must approve before file is auto-generated and sent to Coupa server → bank. Y_XXXX_FI_AP_PAYMENTS and YS:FI:M:BCM_MON_APP MUST NEVER be on same user.

**Process 4 detail**: 1 BCM signatory validates. File auto-downloaded to Coupa. Coupa provides 2nd validation before sending to bank. ⚠ UNES-only — both roles required but creates bypass risk.

---

## 2023 Security Incident — BCM Bypass

**What happened**: A new BCM user had BOTH `Y_XXXX_FI_AP_PAYMENTS` AND `YS:FI:M:BCM_MON_APP______:XXXX` roles simultaneously. This combination allowed the user to:
1. Generate the payment file in F110 (AP_PAYMENTS role)
2. Download it directly to Coupa (BCM_MON_APP role)
3. **Bypass BCM approval entirely** — payment went to bank without any BCM validation

**Remediation**: New role `YO:FI:COUPA_PAYMENT_FILE_:` created to separate "download to Coupa" from "BCM monitor". Testing in V01, ready for P01 production deployment.

**Rule**: Y_XXXX_FI_AP_PAYMENTS + YS:FI:M:BCM_MON_APP on same user = FORBIDDEN (except UNES Process 4 scenario, which is tightly controlled).

---

## BCM Architecture

### Activation
- F110 run ID starting with `B*` → routed to BCM (FABS system)
- All payroll runs → BCM regardless of ID (STEPS system)
- Custom table `ZFI_BCM_ACTIVE` controls per-company-code activation
- Business function `FIN_FSCM_BNK` activated via SFW5

### BCM Grouping Rules (5 FABS + 1 STEPS)
| Rule | Priority | Origin | Criteria | Volume | Dual Control |
|------|----------|--------|----------|--------|-------------|
| UNES_AP_IK | 0 (highest) | FI-AP/FI-AR | Method L + InstrKey B1 | Low | Yes |
| UNES_AR_BP | 1 | FI-AR | Customer 600000-699999 | 6,471 | Yes |
| UNES_TR_TR | 1 | TR-CM-BT | Treasury transfers | 8,955 | **No (1 validation)** |
| UNES_AP_EX | 2 | FI-AP/FI-AR-PR | Embargo country list | Low | Yes |
| UNES_AP_ST | 3 | FI-AP/FI-AR | Catch-all standard | 186,248 | Yes |
| PAYROLL | 1 (STEPS) | HR-PY | All payroll runs | 268,902 | Yes (PAY+TRS) |

All rules additionally group by **VALUT** (value date) — ensures one payment file per execution date.

### BCM Release Strategy (Dual Control)
- **BNK_INI** (1st release): Rule 90000005, WF 50100024, procedure 31000004. Run release WF = **Always**.
- **BNK_COM** (2nd validation): Conditional. Applies to: UNES_AP_EX (prio 1), UNES_AP_ST (prio 2), UNES_AR_BP (prio 3), UNES_AP_IK (prio 4).
- Treasury transfers (UNES_TR_TR): BNK_COM = **1 validation only** (lower risk, no dual control).

### Delegation of Authority — Named Validators (Annex III)
| BFM Post | Code | Name | System | Group | USD Limit |
|----------|------|------|--------|-------|-----------|
| Treasurer | BFM 076 | Anssi Yli-Hietanen | FABS | TRS | $50,000,000 |
| GM USLS | BFM 977 | Irma Adjanohoun | FABS | TRS | $50,000,000 |
| Chief Accountant | BFM 080 | Ebrima Sarr | FABS | TRS+AP | $50,000,000 |
| Asst Treasury Officer | BFM 073 | Baizid Gazi | FABS | TRS | $50,000,000 |
| Accountant FRA | BFM 834 | Yasmina Kassim | FABS | TRS | $50,000,000 |
| Accountant FRA | BFM 077 | Jeannette La | FABS | TRS | $50,000,000 |
| Chief AP | BFM 058 | Lionel Chabeau | FABS | AP | $5,000,000 |
| Chief AR | BFM 053 | Theptevy Sopraseuth | FABS | AP | $5,000,000 |
| Chief PAY | BFM 046 | Simona Bertoldini | FABS+STEPS | AP+PAY | $5M / $300K |
| Sr Finance Asst AP | BFM 383 | Isabelle Marquand | FABS | AP | $500,000 |
| Sr Finance Asst AP | BFM 049 | Christina Lopez | FABS | AP | $500,000 |
| Asst Officer PAY | BFM 037 | Farinaz Derakhshan | STEPS | PAY | $150,000 |

**Note**: Chief PAY (BFM 046) as AP member is NOT authorized for SN (supernumerary) document type.

### Validation Flow by Payment Type
| Flow | Run By | 1st BCM Validation | 2nd BCM Validation |
|------|--------|-------------------|-------------------|
| Vendor/Customer/Staff payments | FAS/AP | AP group | TRS group |
| Business Partner (Inv & FX) | FAS/AP | TRS group | TRS group |
| Bank-to-bank transfers | TRS/MO | TRS group | N/A (1 validation) |
| Payroll bank transfers | FAS/PAY | PAY group | TRS group |

---

## DMEE XML Payment Format Trees

### Two Banks, Two Formats
| Bank | DMEE Tree | Standard | Used For |
|------|-----------|----------|---------|
| Societe Generale | `/CGI_XML_CT_UNESCO` | CGI pain.001 adapted | EUR cross-border, CHF, GBP, AUD, JPY, DKK, USD cross-border |
| Citibank | `/CITI/XML/UNESCO/DC_V3_01` | CITI CGI XML v3 Phase R217 (8.0) | USD, CAD, BRL, MGA, TND, exotic currencies |

**Since 2022 (TMS/Coupa migration)**: ALL Citibank files must be XML v3. XML v2 phased out.

### XML Invalid Character Handling (3 Layers) — Critical for New Countries
Each DMEE tree node has per-field checkboxes — must be set **field-by-field**:

| Layer | Setting | Characters | Effect |
|-------|---------|------------|--------|
| 1 | Suppress Predefined Special | Fixed SAP: `- + * / \ . : ; , _ ( ) [ ] # < >` | Removed entirely |
| 2 | Replace National Characters | SAP table: é→E, ö→O, ü→U, ç→C, etc. | ASCII replacement |
| 3 | Suppress Custom Defined | UNESCO custom: `^"$%&{[]}=\`*~#;_!?⁰` | Removed entirely |

### Country-Specific Requirements
| Country | Risk | Requirement |
|---------|------|-------------|
| US/CA | HIGH | 35-char limit. Unstructured OR structured — never both. |
| Poland (PL) | MEDIUM | IBAN required — exception removed. |
| Madagascar (MG) | HIGH | MGA without IBAN → BCM rule UNES_AP_X → manual reject. |
| Tunisia (TN) | MEDIUM | TND 3 decimal places — SAP Note for ControlSum. |
| Brazil (BR) | HIGH | STCD2 for natural persons. Bank account "-" stripped. TAXID="TXID" constant. |
| UAE/Bahrain | MEDIUM | Payment Purpose Code required. Read from SGTXT via exit. |
| Japan (JP) | LOW | JPY 0 decimal places. |
| COP/ARS/IRR/MMK/SDG | BLOCKER | Out of scope / embargo countries. |
| ARS | HIGH | PMT held 90 days by Citibank (Argentine regulations). |
| UAH (Ukraine) | BLOCKER | Not serviced — bank will not execute. |
| VEF (Venezuela) | BLOCKER | Not serviced — bank will not execute. |
| LYD (Libya) | HIGH | Compliance pre-approval required before each payment. |
| YER (Yemen) | HIGH | Compliance pre-approval required before each payment. |

---

## File Transfer Infrastructure

```
SAP iRIS (Payment Processing)
  → \\hq-sapitf\coupa$\P01\In\Data (SAP Network File Directory)
    → SFTP every 15 minutes → Coupa Treasury Management System
      → SWIFT Integration Layer (SIL)
        → SWIFT Alliance Lite2
          → Banks (SOGE, CITI, BNP, etc.)

Banks
  → SWIFT Alliance Lite2 (EBS + Payment Status Reports)
  → SIL → \\hq-sapitf\SWIFT$\output\*
  → SAP (Bank Statement Processing + Payment Status Updates)
```

**File naming**: `aaaa_bbbb_ccxxxxxxxxyyyy.in` (aaaa=UNES, bbbb=SOGE/CITI, cc=type code, .in required)
**SWIFT client**: Alliance Lite2 (Java 7.51-55, IE 8/9 32-bit)
**Dev/test prefix**: D (dev) or V (V01) instead of P (prod)

### SWIFT Directory Access Control
| Group | Rights | Who |
|-------|--------|-----|
| NT AUTHORITY\SYSTEM | Full control | SAP system administrators |
| SAPServiceP01 + p01adm | Modify | SAP technical operations |
| SA_SWIFT (Marlies Spronk/KMI) | Modify | SWIFT coordinator |
| SG-SAPITF-SWIFT-RO | Read/Execute | BFM/TRS + BFM/FAS staff (11 named users) |

**Rule**: No individual user has write access to SWIFT folders. Only program `SAPFPAYM` can write payment files. Access changes: contact Vincent Vaurette (SAP Admin).

### 3 Automatic Payment Programs at UNESCO
1. **F110** — All 3rd party vendor payments (BFM/FAS/AP + Institutes)
2. **F111** — Bank-to-bank treasury replenishments (BFM/TRS via FRFT_B)
3. **Payroll Program** — HR payroll (BFM/PAY via STEPS system)

**Payroll flow**: ZHRUN (prepare) → FBPM1 (merge into BCM batch) → BNK_APP (PAY then TRS validation) → BNK_MONI (monitor) → BNK_MERGE_RESET (reset if needed, P_BATNO parameter)

**Field office scope**: Payment release workflow (WF 90000003) runs at HQ only. Field offices (IBE, MGIE, ICBA) use Process 1 (outside SAP). Workflow triggers only when HQ executes a payment on a field office's behalf.

---

## Known Operational Issues

### Issue 1: BCM Batch Work Item Reservation
- **Symptom**: BCM batch visible in BNK_MONI but absent from other approvers' SAP inbox
- **Root Cause**: Clicking a WF work item "reserves" it for that user — disappears from all others
- **Affected**: IIEP batches 8544, 8545, 8546 — stuck with M_SARMENTO-G (Mariana Sarmento Godoi)
- **WF Task**: IS 50100025 "Release the Work Item" — BCM approvers pool
- **IIEP Approver Pool**: A_DE-GRAUWE, A_LOPEZ-REY, A_TERRER, E_MOYO, E_ZADRA, M_POISSON, M_SARMENTO-G, P_DIAS, S_GRANT-LEWI
- **Fix**: Transaction SWIA (Work Item Administration) to reassign/release the locked work item

### Issue 2: Wrong Certifying Officer
- **Symptom**: WF item sent to wrong person or nobody receives it
- **Root Cause**: Email mismatch between SAP SU01 profile and UNESdir LDAP
- **Fix**: Check `https://role.hq.int.unesco.org` → verify CO → check SU01 email → fallback: ZFI_PAYREL_EMAIL

---

## Audit Finding: BCM Dual Control Gap

**Finding**: BNK_BATCH_HEADER shows approved UNES batches where CRUSR=CHUSR (same user created AND approved the batch). This violates Segregation of Duties.

**Tables**: BNK_BATCH_HEADER, STATUS='A' (Approved), CRUSR=CHUSR

This is an open audit finding for the next audit cycle.

---

## UIL-Specific Configuration (Hamburg — new 2024)

| Bank | Account | Currency | GL | Payment Method |
|------|---------|---------|-----|---------------|
| SOG05 | EUR01 | EUR | 1175792 | S (SEPA EUR) |
| SOG05 | USD01 | USD | 1175791 | N (International) |

- BCM: 2 validations required, UIL AP Validation up to $5,000,000
- Payment run users: Britta Hoffman, Larissa Steppin
- BCM validators: Atchoarena David, Jahan Nusrat, Valdes Cotera Raul, Zholdoshalieva Rakhat, Gazi Baizid, Yli-Hietanen Anssi

---

## SAP Notes Implemented (21 BCM Notes)

See sap_payment_bcm_agent SKILL.md for full list. Key ones:
- 1698595: FTE_BSM error FAGL_LEDGER_CUST023
- 1595730: BNK_MONI Batch status incorrect
- 1566148: BCM Duplicate payment file from proposal run
- 2028671: BCM Rule description not saved after change
- 1997772/1999340: BCM Rule Maintenance currency/amounts

---

## Exotic Currency Note to Payee (SWIFT :70)

Payment method X generates SWIFT field `:70` with format:
```
EXO//Detailed reason for payment//FPAYP-XBLNR//
```
- `EXO//` = fixed prefix for all exotic currency payments
- Reason determined from document type (REGUP-BLART) via custom table
- Additional info = FPAYP-XBLNR (vendor invoice number)
- OBPM2 name: `Y_EXOTIC_CURRENCY` — function module `Y_FI_PAYMEDIUM_NOTE_TO_PAYEE`
- Madagascar (MGA): SWIFT :57D Option D (BIC + bank address in one field — :57A and :57D cannot coexist)

## Integration Points
- **sap_payment_bcm_agent** skill — full payment domain knowledge
- **sap_payment_e2e** skill — process mining and cycle time analysis
- **sap_company_code_copy** skill — FBZP chain for new company codes
- **fi_domain_agent** skill — GL posting rules, substitutions
- **Gold DB**: REGUH(942K), BNK_BATCH_HEADER(27K), BNK_BATCH_ITEM(600K), BKPF(1.67M), BSAK(739K)
