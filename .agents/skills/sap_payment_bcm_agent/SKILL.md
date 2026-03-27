# SAP Payment & BCM Domain Agent

## Metadata
- **Name**: sap_payment_bcm_agent
- **Type**: Domain Agent (specialized)
- **Maturity**: Production
- **Origin**: Session #020 — Full payment configuration extraction + process mining
- **Triggers**: Questions about payments, F110, BCM, FBZP, house banks, payment methods, bank communication, advance payments, payment runs, vendor clearing

## Purpose

Specialized agent for all SAP payment and BCM (Bank Communication Management) questions at UNESCO. This agent has complete knowledge of:
- Payment configuration across all 9 company codes
- F110 automatic payment program setup (FBZP chain)
- BCM batch routing, approval workflows, and status lifecycle
- House bank network (211 banks across 50+ countries)
- Payment method definitions and currency routing
- Process mining results (1.4M events, 550K cases)

## When to Route Here

The **coordinator** should route to this agent when the user asks about:
- Payment configuration (FBZP, T042, T012)
- F110 payment runs (proposals, execution, house bank selection)
- BCM batches (BNK_MONI, approval, bank file transmission)
- House banks and bank accounts
- Payment methods and currency routing
- Vendor payment status (open items, clearing)
- Advance/down payments (FBA6, KA document type)
- Payment medium programs (DMEE, RFFOUS_T)
- Bank statements and reconciliation
- Payment process mining results
- Company code payment capability assessment

## NEVER Do This

1. **Never confuse T042A with T042C** — T042A has the payment method→bank routing (76 rows). T042C is client-level only (0 rows).
2. **Never assume FCLM_BAM_* tables exist** — UNESCO uses `BNK_BATCH_HEADER/ITEM`, NOT the FSCM BAM tables.
3. **Never assume central payment** — All 9 company codes pay for themselves (T042 BUKRS=ZBUKR).
4. **Never tell users IBE/MGIE/ICBA can run F110** — They pay OUTSIDE SAP (manual transfer/check in local banking system). [VERIFIED from handover docs]
5. **Never assume FEBEP has data** — 0 rows. BCM handles bank reconciliation, not classic electronic bank statements.
6. **Never skip BCM when analyzing payments** — BCM sits between F110 and bank. 374K items routed through BCM batches.
7. **Never assign Y_XXXX_FI_AP_PAYMENTS + YS:FI:M:BCM_MON_APP together** — This allows bypassing BCM validation entirely. 2023 INCIDENT: payment went to Coupa→bank without BCM approval. [VERIFIED from handover docs]
8. **Never use F110 run ID starting with B* for non-BCM payments** — B* prefix triggers BCM routing. Use any other ID for direct processing.

## UNESCO Payment Architecture

### The 4 Payment Processes [VERIFIED from BFM Handover Documentation]

**Source**: "Payment process and authorizations 1.2 TRS" (BFM/TRS handover)

**Process 1 — Payments managed OUTSIDE SAP** (IBE, MGIE, ICBA, field offices)
- AO posts outgoing payment in SAP (clearing vendor, debiting sub-bank account)
- Creates transfer in LOCAL banking system or writes a check
- No F110, no BCM, no DMEE
- Role: `YS:FI:D:DISPLAY__________:ALL` (display only)

**Process 2 — F110 + Manual File Download** (ICTP, UBO/Banco do Brazil, UNES checks phasing out, UIL migrating)
- F110 payment run in SAP, payment file created and downloaded manually to local directory
- User uploads file to bank portal manually
- Role: `Y_XXXX_FI_AP_PAYMENTS`
- BCM signatory: NOT relevant

**Process 3 — F110 + BCM + 2 Validations → Coupa → Bank** (UIS, IIEP, UIL/new SG bank, UBO/Citibank)
- F110 creates payment, BCM groups into batches
- **2 BCM signatories** must validate before file is generated
- File auto-downloaded to Coupa server → sent to bank
- Role: `Y_XXXX_FI_AP_PAYMENTS` OR `YS:FI:M:BCM_MON_APP______:XXXX` (**NEVER BOTH**)
- BCM signatory: REQUIRED

**Process 4 — F110 + BCM + 1 Validation → Coupa (2nd validation) → Bank** (UNES HQ)
- F110 creates payment, BCM groups into batches
- **1 BCM signatory** validates, file auto-downloaded to Coupa
- **Coupa provides 2nd validation** before sending to bank
- Role: `Y_XXXX_FI_AP_PAYMENTS` AND `YS:FI:M:BCM_MON_APP______:XXXX`
- **SECURITY RISK**: Both roles on same user = bypass BCM entirely (2023 incident)

### BCM Activation Rule
- F110 run ID starting with **`B*`** → routed to BCM
- Any other run ID → direct processing (no BCM)
- This is configured in SAP payment program customizing

### The 3 Payment Tiers (Data-Derived)

**Tier 1 — Full Automation (6 codes: UNES, UBO, ICTP, IIEP, UIL, UIS)**
- F110 automatic payment → BCM batch grouping → bank file transmission
- Complete FBZP chain: T042 → T042A → T042E → T042I → T012 → T012K
- BCM approval workflow (BNK_INI/BNK_COM roles)

**Tier 2 — Partial (ICTP)**
- F110 + physical checks (PAYR Method K = 898 checks via UNI01)
- 24 payment methods configured (most of any company code)
- No BCM — payments go directly to bank

**Tier 3 — Unconfigured (3 codes: IBE, MGIE, ICBA)**
- NO T042A entries (payment methods not linked to house banks)
- Have T012K bank accounts but no F110 routing
- Payments likely manual (F-53) or handled by HQ

### Company Code Profiles

| Code | City | Country | Ccy | Banks | Methods | BCM | F110 Runs | REGUH Items |
|------|------|---------|-----|-------|---------|-----|-----------|-------------|
| UNES | Paris | FR | USD | 154 | 16 | Yes (21.8K batches) | 8,639 | 818,739 |
| UBO | Brasilia | BR | BRL | 5 | 11 | Yes (1.7K) | 2,616 | 74,836 |
| ICTP | Trieste | IT | EUR | 3 | 24 | No | 1,952 | 24,078 |
| IIEP | Paris | FR | USD | 8 | 10 | Yes (2.1K) | 1,090 | 10,218 |
| UIL | Hamburg | DE | EUR | 3 | 3 | Yes (435) | 926 | 11,676 |
| UIS | Montreal | CA | USD | 4 | 7 | Yes (1.4K) | 509 | 2,464 |
| IBE | Geneva | CH | USD | 3 | 0 | No | 0 | 0 |
| MGIE | New Delhi | IN | USD | 2 | 0 | No | 0 | 0 |
| ICBA | Addis Ababa | ET | USD | 3 | 0 | No | 0 | 0 |

### UNES House Bank Network (45+ active banks)

**Primary banks (T042A configured):**
- SOG01 (Societe Generale, Paris) — EUR/USD, main HQ bank: 381K EUR + 107K USD payments
- CIT04 (Citibank, USD) — USD operations: 61K payments
- SOG03 (Societe Generale, multi-currency) — AUD/CHF/DKK/GBP/JPY
- CIT21 (Citibank, CAD) — Canadian dollar
- BNP01 (BNP Paribas) — Method Z (STEPS only)

**Field office banks (PAYR Method 3 = manual checks):**
- 35+ banks in local currencies across Africa, Asia, Latin America, Middle East
- Each serves 1-3 field offices with local currency + USD accounts
- Examples: AIB01 (Afghanistan/AFN), CBE01 (Ethiopia/ETB), BKC01 (China/CNY), SCB12 (Kenya/KES)

**Treasury transfer banks (BCM single-vendor batches):**
- WEL01 (729 items), CHA01 (706), SOG05 (333), DNB01 (196)
- Used for inter-company/treasury movements, not vendor payments

### BCM Configuration

**14 BCM Rules:**
| Rule | Company | Purpose | Volume |
|------|---------|---------|--------|
| PAYROLL | UNES | Payroll payments | 268,902 items |
| UNES_AP_ST | UNES | Standard AP | 186,248 |
| UNES_AP_10 | UNES | AP batch >=10 items | 72,221 |
| UBO_AP_MAX | UBO | Brazil AP max batch | 25,095 |
| IIEP_AP_ST | IIEP | IIEP standard AP | 14,274 |
| UNES_TR_TR | UNES | Treasury transfers | 8,955 |
| UNES_AR_BP | UNES | AR business partner | 6,471 |
| UIL_AP_ST | UIL | Hamburg AP | 2,648 |
| UNES_AP_EX | UNES | AP exceptions | 2,459 |
| UIS_AP_MAX | UIS | Montreal AP max | 2,431 |
| UBO_AP_ST | UBO | Brazil AP standard | 900 |
| UNES_AP_IK | UNES | AP inter-company | 775 |
| UIS_AP_ST | UIS | Montreal AP standard | 522 |
| UNES_AP_11 | UNES | AP batch >=11 | 163 |

**BCM Status Lifecycle:**
| Code | Meaning | Count | Avg Items | Avg Amount |
|------|---------|-------|-----------|------------|
| IBC15 | Completed | 7,016 | 24.4 | 358,140 |
| IBC17 | Failed | 2,056 | 26.5 | 1,213,033 |
| IBC05 | Sent to Bank | 1,650 | 11.0 | 1,072,233 |
| IBC11 | Approved | 1,291 | 45.0 | 514,235 |
| IBC06 | Rejected | 161 | 22.4 | 102,917 |
| IBC20 | Reversed | 69 | 0.0 | 0 |

**BCM Approval Flow:**
1. F110 creates payment documents (BKPF BLART=ZP)
2. BCM groups into batches by RULE_ID (company code + bank + amount threshold)
3. Batch status: IBC01 (New) → IBC11 (Approved) → IBC05 (Sent to Bank) → IBC15 (Completed)
4. Alternative: IBC01 → IBC17 (Failed) or IBC06 (Rejected) → manual intervention
5. User roles: BNK_INI (first-level edit), BNK_COM (approval levels)

**Key BCM Users:**
| User | Batches | Inferred Role |
|------|---------|---------------|
| C_LOPEZ | 7,043 | Primary AP processor |
| I_MARQUAND | 6,938 | Primary AP processor |
| I_WETTIE | 3,634 | AP processor |
| F_DERAKHSHAN | 3,048 | AP processor |
| S_COURONNAUD | 2,035 | AP processor |
| E_AMARAL | 1,525 | UBO AP processor |

### Payment Methods

| Letter | Description | Used By |
|--------|-------------|---------|
| N | Citibank XML Cross Border Transfer | UNES, IIEP, UIL, UIS |
| S | Scheck (EUR check) | UNES, IIEP, ICTP, UIL |
| M | Bankscheck (bank check) | ALL except UBO |
| J | Payment order | UNES, IIEP, ICTP, UBO |
| 3 | Manual cheque | IBE, IIEP, UIS, UNES (field offices) |
| C | Cheque | UBO, UIS, UNES |
| K | Auslandsscheck (foreign check) | IBE, ICTP, IIEP, UIS, UNES |
| 5 | Manual cheque USD | ICTP, UNES |
| L | Auslandsüberweisung (foreign transfer) | IBE, ICTP, UNES |
| X | Cheque diferido (deferred check) | UNES only |
| Z | Dummy payment method — STEPS only | UNES only (BNP01) |

### Process Mining Results

- **1,435,376 events** / **550,993 cases** / **12 activities** / **207 variants**
- Invoice → Payment: mean 4.1 days, median 2 days
- Invoice → Clearing (E2E): mean 5.6 days, median 2 days
- Due Date → Payment: mean 26.8 days late, median 14 days late
- On-Time Payment: **1.1%** [NEEDS INVESTIGATION]

### Payment Release Workflow (Pre-F110) [VERIFIED from handover docs]

**Source**: "FS Payment release workflow 2.0" + "Technical documentation of Workflow Financial Payment Release"

### Architecture
- **Workflow 90000003** — `ZBSEG_FRAME1` (Release for payment frame)
- **Sub-workflow 90000002** — `UN BSEG_SUBW` (Release for payment single-stage)
- **Business Object**: Custom subtype `YBSEG` of standard BSEG (package `YWFI`)
- **Trigger Event**: `BSEG-CREATED` (Posting Item Created with Payment Block)

### Scope
- **Company Code**: UNES only (other codes out of scope)
- **14 Document Types**: KR, KA, ER, KT, IT, CO, AS, P3, SN, MF, IN, AP, RF, MR
- **Excluded**: Payment Method O (field office) or U → not subject to workflow

### Payment Method O/U Exclusion Logic
- Field offices register invoices in UNES company code
- **Substitution rule** defaults Payment Method **O** based on user ID parameter
- Method O is not used in F110 → these invoices are paid by field offices outside SAP
- When field office invoice needs HQ payment: remove Method O → triggers workflow
- Workflow checks: if Method O → reset payment block, set to W (Workflow block), wait for "Payment Method removed" event

### 7 Release Groups (by Document Type → Organizational Unit)

| Doc Types | Release Group | Validation Type |
|-----------|---------------|-----------------|
| CO | BSP/CFS | Fixed (same group always) |
| AS, P3, SN | BFM/PAY | Fixed |
| MF, IN, AP | HRM/SPI | Fixed |
| RF | BFM/TRS/CM | Fixed |
| MR | BFM/FRA & BFM/TRS/AR | Fixed |
| PS, PN | BFM/FNS | Fixed |
| KR, KA, KT, ER, IT | Certifying Officer (by sector) | **Flexible** (via SharePoint/LDAP lookup) |

### Certifying Officer Resolution
- For KR/KA/KT/ER/IT: workflow calls **Rule 90000001** → ABAP FM `Z_GET_CERTIF_OFFICER_UNESDIR`
- FM gets posting user's email → calls `Z_WF_GET_CERTIFYING_OFFICER` → reads **UNESCO LDAP** (UNESdir)
- LDAP returns certifying officer for the user's sector/unit
- Fallback: if no officer found → reads custom table **`ZFI_PAYREL_EMAIL`** for default backup users
- **Role Management app**: `https://role.hq.int.unesco.org/organizational-unit-overview/adm`
- Certifying officers have **$150,000 limits** (some $10,000)

### Classic Validation (Non-KR/KA/KT/ER/IT)
- **Rule 90000002** → ABAP FM `Z_WF_FI_PR_WF_ACTOR1_DET`
- Reads users from payment release customizing (SPRO: Release for Payment)
- Fallback: `ZFI_PAYREL_EMAIL`

### Workflow Notifications
- Program: `RSWUWFML2` variant `ZWKFLOW_FI_EMA`
- ABAP FM `Z_WF_FI_EXCLUDE_NOTIF_EMAIL` checks user parameter `Z_WKF_EMAIL_NOTIF` in SU01
- If parameter = 'X' → user gets email notifications for workflow items

### Workflow Troubleshooting Transactions
| Transaction | Purpose |
|-------------|---------|
| SWI2_DIAG | Diagnosis of workflows with errors (restart stuck items) |
| SWI2_ADM1 | Work items without agents (forward to correct validator) |
| SWIA | Work Item Administration Report (lookup + forward) |
| SWU3 | Workflow runtime environment check |
| SWU_OBUF | Synchronize workflow buffers |
| PFTS | Task agent assignment maintenance |

## SAP Roles & Authorization Matrix [VERIFIED]

| Role | Description | F110 Activities | BCM | Compatible With |
|------|-------------|-----------------|-----|-----------------|
| `YS:FI:D:DISPLAY__________:ALL` | Display only | 03, 13, 23 (display) | No | All |
| `Y_XXXX_FI_AP_PAYMENTS` | Institute/UBO payment | 02, 11-15, 21, 25 (full) | No | NOT with BCM_MON_APP |
| `YS:FI:M:AP_PAYMENT_RUN___:UKDS` | HQ BFM/AP payment | 02, 11-15, 21, 25 (full) | No | Context-dependent |
| `YS:FI:M:BCM_MON_APP______:XXXX` | BCM monitor + validate | BCM only | Yes | NOT with AP_PAYMENTS |
| `YO:FI:COUPA_PAYMENT_FILE_:` | Coupa download only (NEW) | None | Download only | BCM validators only |

### 2023 Security Incident
- New BCM user had BOTH `Y_XXXX_FI_AP_PAYMENTS` + `YS:FI:M:BCM_MON_APP` roles
- Could generate payment file in F110 AND download to Coupa, bypassing BCM approval
- **Remediation**: New role `YO:FI:COUPA_PAYMENT_FILE_:` separates Coupa download from BCM viewing
- **Status**: Testing in V01, ready to move to P01

### BCM Signatory Management
- Transaction: `OOCU_RESP` (Organization → Responsibility)
- Rules: **90000004** (BNK_COM_01_01_03) and **90000005** (BNK_INI_01_01_04)
- HQ signatories: CFO delegation of authority → updated by DBS on BFM/TRS request
- Institute/UBO signatories: bank signatory letters → updated by DBS
- **Changes done directly in production** (HR org structure not up to date in dev)
- To remove: **delimit validity** (never delete)

### BCM Validation Tiers (from Rule 90000005)
| Validation Group | Code | Threshold |
|------------------|------|-----------|
| UIS AP Validation up to 10,000 USD | BNK_01_01_04 | $10,000 |
| UIS AP Validation up to 5,000,000 USD N/ | BNK_01_01_04 | $5,000,000 |
| UNES FAS/PAP/AP Validation to 500,000 | BNK_01_01_04 | $500,000 |
| UNES FAS/PAP/AP Validation to 5,000,000 | BNK_01_01_04 | $5,000,000 |
| UNES FAS/PAP/AP Validation to 50,000,000 | BNK_01_01_04 | $50,000,000 |
| UNES TRS Validation up to 50,000,000 | BNK_01_01_04 | $50,000,000 |
| UNESCO bank to bank transfers | BNK_01_01_04 | Unlimited |
| UNES AP Validation up to 10,000,000 USD | BNK_01_01_04 | $10,000,000 |

## Exotic Currency Payments [VERIFIED]

**Payment Method X** — "Payment in non-standard currencies"
- Currencies: BWP, TND, XOF, MGA, ZMB
- Bank: SOG01-USDD1 (Societe Generale USD account, Paris)
- Vendor must have SWIFT code + bank account number
- BCM rule: `UNES_AP_X` catches MGA without IBAN → **must be manually rejected**
- Bank reconciliation: manual process via GL 1175011 (local ccy) → YTR2 → F-04 clearing

### Exotic Currency Classification
| Tier | Requirements | Count | Currencies |
|------|-------------|-------|------------|
| Standard | Name/address/account/IBAN | 619 | BWP, TND, XOF, ZMB, UGX, DOP, etc. |
| + Branch location | + Beneficiary bank branch | 166 | PEN, RWF, MWK, MNT, etc. |
| + Branch + IBAN | + IBAN required | 284 | MGA, AOA, GEL, MRO |
| Out of scope | Tax ID, embargo, etc. | 213 | COP, IRR, MMK, SDG, ARS, etc. |

### Payment File Regeneration
- Transaction: **ZPAYM** (custom) — regeneration of payment files from BCM batches
- Shows batches by status (New, In Approval, Approved, Sent to Bank, Completed, Exceptions)
- Can reschedule payment medium creation from F110

## DMEE XML Payment File Formats [VERIFIED — Critical for adding new countries]

**Source**: "FS Modifications XML Payment file format v2.0" + "Explanation on how to suppress invalid characters XML payment file"

### Two Banks, Two Format Trees

| Bank | DMEE Format Tree | Standard | Used For |
|------|-----------------|----------|----------|
| **Citibank** | `/CITI/XML/UNESCO/DC_V3_01` | CITI CGI XML V3 Phase R217 (8.0) | USD (US), CAD (CA), BRL (BR), MGA, TND, exotic currencies |
| **Societe Generale** | `/CGI_XML_CT_UNESCO` | SAP CGI_XML_CT adapted | EUR cross-border, CHF, GBP, AUD, JPY, DKK, USD cross-border |

**NOTE**: Since 2022 (TMS/Coupa), all CITIBANK files must be XMLv3. XMLv2 phased out.

### Payment Method → Bank → Format Mapping [VERIFIED]

| CC | Country | Bank | Account | Method | Type | Format |
|----|---------|------|---------|--------|------|--------|
| UBO | BR | CIT01 | BRL01 | Q | Boleto Bar Code | /CITI/.../DC_V3_01 |
| UBO | BR | CIT01 | BRL01 | R | TED Online | /CITI/.../DC_V3_01 |
| UIS | CA | CIT01 | CAD01 | C | Domestic | /CITI/.../DC_V3_01 |
| UIS | CA | CIT01 | USD01 | N | Cross Border | /CITI/.../DC_V3_01 |
| UNES | CA | CIT21 | CAD01 | C | Domestic | /CITI/.../DC_V3_01 |
| UNES | US | CIT04 | USD04 | L | Domestic USD | /CITI/.../DC_V3_01 |
| UNES | US | CIT04 | USD04 | N | Cross Border USD | /CITI/.../DC_V3_01 |
| UNES | US | CIT04 | USD04 | X | Exotic Currencies | /CITI/.../DC_V3_01 |
| UNES | FR | SOG01 | EUR01 | S | SEPA EUR | /CGI_XML_CT_UNESCO |
| UNES | FR | SOG03 | various | N | Cross Border (CHF/GBP/AUD/JPY/DKK) | /CGI_XML_CT_UNESCO |
| UNES | FR | SOG01 | USDD1 | N | Cross Border USD | /CGI_XML_CT_UNESCO |

### Treasury Transfers (Method A) — All use /CGI_XML_CT_UNESCO or no format
- UNES → SOG01 (EUR), SOG03 (multi-ccy), CIT04 (USD), NTB01, CIC01, BNP01, CRA01, WEL01, SCB14, DNB01, etc.
- Most treasury banks have NO DMEE format assigned (file created directly or not via BCM)

### XML Invalid Character Handling (3 Layers)

When adding a new country, this is the **hardest part** — each bank has different character requirements per field:

| Layer | Setting | Characters | Effect |
|-------|---------|------------|--------|
| 1. Suppress Predefined Special | Fixed SAP set | `- + * / \ . : ; , _ ( ) [ ] # < >` | Characters removed entirely |
| 2. Replace National Characters | SAP conversion | `é→E, ö→O, ü→U, ç→C` etc. | Accented → ASCII equivalent |
| 3. Suppress Specific Defined | UNESCO custom | `^"$%&{[]}=\`*~#;_!?⁰` | Characters removed entirely |

**Per-field configuration**: Each DMEE tree node has checkboxes: "Replace national characters", "Remove special chars", "Exclude/allow defined characters". Must be set field-by-field.

**Common rejection reasons**: Bank rejects payment file because vendor name/address contains characters not in the allowed set. No exhaustive list from banks exists — it's learned by trial and error.

### Country-Specific Complexities (Why Adding a Country is Hard)

| Requirement | Countries | Issue |
|-------------|-----------|-------|
| US Travel Rule: 35 char limit on Name/Address/Payment Details | US, CA | Must use unstructured OR structured address, never both |
| IBAN required | Poland, MGA (Madagascar), TND (Tunisia) | Reject if missing |
| Tax ID in payment file | Colombia (COP), Guatemala (GTQ), Argentina (ARS) | Different field placement per country |
| Branch location required | Peru, Rwanda, Malawi, Mongolia | Additional DMEE field mapping needed |
| Embargo countries | Iran (IRR), Myanmar (MMK), Sudan (SDG) | Excluded from automatic payment entirely |
| Decimal settings vary by currency | TND (3 decimals), JPY (0 decimals) | ControlSum must match individual amounts — SAP Note for conversion function |

### Steps to Add a New Country to Payment

1. Verify bank requirements for the destination country (character sets, IBAN, tax ID, branch info)
2. Configure payment method in FBZP if new method needed
3. Update DMEE tree: add country-specific conditions on PstlAdr nodes (structured vs unstructured)
4. Set character replacement options per field for the new country
5. Test in V01 — create payment, verify XML file, send through SWIFT test system
6. Contact bank to confirm file was received and correctly processed
7. Update BCM rules if new grouping needed (e.g., UNES_AP_X for exotic currencies)
8. Create OBPM4 variant (NEVER transported — recreate manually per system)

### DMEE Exit Functions & Custom Classes [VERIFIED from FS XML v2.0]

| Exit/Class | DMEE Tree | Purpose |
|------------|-----------|---------|
| `Z_DMEE_EXIT_TAX_NUMBER` | /CITI/.../DC_V3_01 | Brazil: select STCD2 (natural person tax ID) when STCD1 is empty |
| `FI_CGI_DMEE_EXIT_W_BADI` | /CGI_XML_CT_UNESCO | SG: beneficiary name >35 chars → spill Name2 into address. Also PPC handling |
| `CL_IDFI_CGI_DMEE_FALLBACK` | /CGI_XML_CT_UNESCO | SG: empty bank number when not available (method GET_CREDIT) |
| `/CITIPMW/FI_PAYMEDIUM_DMEE_05` | /CITI/.../DC_V3_01 | Brazil: BranchId fix `p_zbnky+3` → `p_zbnkl+3` (program `/CITIPMW/LPMWV3F01`) |
| `YCL_IDFI_CGI_DMEE_FALLBACK` | Custom (YENH_FI_DMEE) | UNESCO DMEE fallback: credit/debit value calculation |

### Country-Specific DMEE Adaptations [VERIFIED]

| Country | Adaptation | DMEE Node | Condition |
|---------|-----------|-----------|-----------|
| US/CA | Unstructured address only (AdrLine) | Dbtr>PstlAdr | FPAYHX.UBISO <> 'US','CA','FR' |
| US/CA | Structured address for beneficiary | Cdtr>PstlAdr | FPAYHX.UBISO = 'US','CA','FR' |
| Poland (PL) | IBAN node exception removed | CdtrAcct>Id>IBAN | FPAYHX.ZBISO <> 'PL' condition REMOVED |
| Brazil (BR) | Bank account "-" stripped | CdtrAcct>Id | Remove special chars flag |
| Brazil (BR) | TAXID = "TXID" constant | Cdtr>Id>OrgId>Othr>Cd | Condition: FPAYHX.UBISO = 'BR' |
| Brazil (BR) | Natural person STCD2 | Cdtr>Id>PrvtId | Condition: FPAYHX.STCD1 = '' |
| USD/CAD/MGA/TND/BRL | Phone/Fax removed | CdtDtls>PhneNb, FaxNb | FPAYHX.WAERS <> currencies |
| MGA/TND | Bank account removed (IBAN only) | CdtrAcct>Id | FPAYHX.SBISO <> 'TN','MG' |
| AE/CN | Payment Purpose Code required | InstrForCdtrAgt/InstrInf | Read from SGTXT via exit |

### SG (Societe Generale) Specific [VERIFIED]

- **CGI_XML_CT_UNESCO** format: InstrId max 16 chars (SG limit, standard = 29)
- **DOC1T atom**: payment origin (01 = vendor/customer, 03 = payroll)
- **DOC1R atom**: company code + payment doc (target offset 2, no space between DOC1T and DOC1R)
- **Beneficiary name**: if Name1 > 35 chars, overflow into StrtNm line of address (user exit FI_CGI_DMEE_EXIT_W_BADI)
- **Address rule**: NEVER mix structured and unstructured. SG rejects hybrid addresses.
- **Contract code**: CMi101 Tag:20 = FR14H819 (live SWIFT), FR08B176 (live FTP). Tag:23 = OTHR/WKST/FR14H819

### Payment File Infrastructure [VERIFIED from Blueprint]

**File Directories**:
- Payment files output: `\\hq-sapitf\SWIFT$\P01\input` (FABS), `P11` (STEPS)
- Bank statements input: `\\hq-sapitf\SWIFT$\output\*`
- Coupa directory: `\\hq-sapitf\coupa$\P01\In\Data`
- Dev/test files prefixed with D or V

**File Naming Convention**: `aaaa_bbbb_ccxxxxxxxxyyyy.in`
- aaaa = Sending entity (always UNES)
- bbbb = Receiving entity (SOGE or CITI)
- cc = File type (01=pain.001.001.02, 02=pain.fin.mt101, 03=pain.001.001.03)
- xxxxxxxx = Freely defined name by UNESCO
- yyyy = Unique identifier by SAP
- .in = Required extension for SWIFT
- Example: `UNES_SOGE_03SEPOPF.in`

**SWIFT Transfer**: Every 15 minutes, SFTP checks directory → SWIFT Integration Layer (SIL) → Alliance Lite2 → Banks

### BCM Release Rules — Full Detail [VERIFIED from Blueprint pages 21-25]

**FABS (all company codes except payroll)**:
- BNK_INI (1st release) → WF Release Step → Rule **90000005** (BNK_INI_01_01_04)
- BNK_COM (2nd validation) → WF Release Step → Rule **90000004** (BNK_COM_01_01_03)

**STEPS (payroll only)**:
- BNK_INI → Rule **90000001** → CHIEF OF UNIT (BFM 046) + ASSISTANT PAYROLL (BFM 037)
- BNK_COM → Rule **90000002** → TREASURER (BFM 076) + ASSISTANT TREASURER (BFM 073)

**V_TBCA_RTW_LINK assignments**:
| Rel.Object | Release Pr | Release Workflow | Release Procedure WF |
|------------|-----------|-----------------|---------------------|
| BNK_INI | 01 | 50100024 | 31000004 |
| BNK_COM | 01 | 50100024 | 50100021 |
| BNK_COM | 02 | 50100024 | 50100022 |
| BNK_COM | 03 | 50100024 | 50100023 |

### Delegation of Authority — Annex III [VERIFIED from Blueprint p.25]

**Validation Flow Types**:
| Flow | Run By | 1st BCM Validation | 2nd BCM Validation |
|------|--------|-------------------|-------------------|
| Vendor/Customer/Staff payments | FAS/AP | AP group | TRS group |
| Business Partner (Inv & FX) | FAS/AP | TRS group | TRS group |
| Bank-to-bank transfers | TRS/MO | TRS group | N/A (1 validation) |
| Payroll bank transfers | FAS/PAY | PAY group | TRS group |

**Named Validators with Limits**:
| BFM Post | Code | Name | System | Group | USD Limit |
|----------|------|------|--------|-------|-----------|
| Treasurer | BFM 076 | Anssi Yli-Hietanen | FABS | TRS | 50,000,000 |
| General Manager USLS | BFM 977 | Irma Adjanohoun | FABS | TRS | 50,000,000 |
| Chief Accountant | BFM 080 | Ebrima Sarr | FABS | TRS | 50,000,000 |
| Assistant Treasury Officer | BFM 073 | Baizid Gazi | FABS | TRS | 50,000,000 |
| Accountant FRA | BFM 834 | Yasmina Kassim | FABS | TRS | 50,000,000 |
| Accountant FRA | BFM 077 | Jeannette La | FABS | TRS | 50,000,000 |
| Chief Accountant | BFM 080 | Ebrima Sarr | FABS | AP | 50,000,000 |
| Chief AP | BFM 058 | Lionel Chabeau | FABS | AP | 5,000,000 |
| Sr Finance Asst AP | BFM 383 | Isabelle Marquand | FABS | AP | 500,000 |
| Sr Finance Asst AP | BFM 049 | Christina Lopez | FABS | AP | 500,000 |
| Chief AR | BFM 053 | Theptevy Sopraseuth | FABS | AP | 5,000,000 |
| Chief PAY | BFM 046 | Simona Bertoldini | FABS | AP | 5,000,000 |
| Chief Accountant | BFM 080 | Ebrima Sarr | STEPS | PAY | 300,000 |
| Chief PAY | BFM 046 | Simona Bertoldini | STEPS | PAY | 300,000 |
| Assistant Officer PAY | BFM 037 | Farinaz Derakhshan | STEPS | PAY | 150,000 |

**Note**: Chief PAY (BFM 046) as AP group member is NOT authorized for SN (supernumerary) document types.

### SAP Notes Implemented for BCM [VERIFIED from Blueprint p.30-31]

| # | Note | Description | System |
|---|------|-------------|--------|
| 1 | 1698595 | FTE_BSM error FAGL_LEDGER_CUST023 | FABS+STEPS |
| 2 | 1595730 | BNK_MONI Batch status set to incorrect | FABS+STEPS |
| 3 | 1654923 | BNK_MONI Status displays error even when file created | FABS+STEPS |
| 4 | 1698455 | BCM no alert during/after file creation problems | FABS+STEPS |
| 5 | 1704078 | BCM Alert table BNK_BTCH_TIMEOUT too large | FABS+STEPS |
| 6 | 1836541 | BNK_MONI Check on existence of payment file | FABS+STEPS |
| 7 | 1978287 | BNK_MONI message file not yet created is incorrect | FABS+STEPS |
| 8 | 1681517 | RBNK_MERGE_RESET restriction to batch number | FABS+STEPS |
| 9 | 1892712 | RBNK_MERGE_RESET P_BATNO field name not label | FABS+STEPS |
| 10 | 1566148 | BCM Duplicate payment file from proposal run | FABS+STEPS |
| 11 | 2028671 | BCM Rule description not saved after change | FABS+STEPS |
| 12 | 1598633 | Process improvement returned batches | STEPS |
| 13 | 1488375 | Attachment for returned batches (not valid) | FABS+STEPS |
| 14 | 1876093 | SBWP correction on attachment for returned | FABS+STEPS |
| 15 | 1879033 | Process change for returned batches | STEPS |
| 16 | 1997772 | BCM Rule Maintenance on currency and amounts | FABS+STEPS |
| 17 | 1999340 | BCM Rule Maintenance correction on 1997772 | FABS+STEPS |
| 18 | 1391319 | Batch Creation HR Payroll BCM activation error | STEPS |
| 19 | 1416652 | Termination of SAPFPAYM_MERGE | STEPS |
| 20 | 1718468 | BNK_MONI Authorization check | STEPS |
| 21 | 1697428 | Message FZ116 HR Payments | STEPS |

### Key DMEE Transactions

| Transaction | Purpose |
|-------------|---------|
| DMEE | Display/Change Format Tree (the XML template) |
| OBPM1 | Assign DMEE format to payment method |
| OBPM4 | Create selection variants for payment medium (**NEVER transported**) |
| OBPM5 | Set indicator for merging cross-payment media |
| FBPM1 | Merge payments in BCM |
| BNK_APP | Approve payments in BCM |
| BNK_MONI | Monitor payment batch status |
| BNK_BNK_INI_REL01 | Assign release procedure to BNK_INI |
| BNK_BNK_COM_REL01 | Assign release procedure to BNK_COM |

## BCM Infrastructure [VERIFIED from Blueprint + Solution Docs]

### File Transfer Architecture
```
SAP iRIS (Payment Processing)
  → SAP Network File Directory (\\hq-sapitf\coupa$\P01\In\Data)
    → SFTP every 15 minutes → Coupa Treasury Management System
      → SWIFT Integration Layer (SIL)
        → SWIFT Alliance Lite2
          → Banks

Banks
  → SWIFT Alliance Lite2 (EBS + Payment Status Reports)
    → SIL → \\hq-sapitf\SWIFT$\output\*
      → SAP (Bank Statement Processing + Payment Status Updates)
```

### BCM Activation (from Blueprint)
- Business function: `FIN_FSCM_BNK` activated via `SFW5`
- FABS: BCM identifier = `BCM*` (F110 run IDs starting with BCM* go through BCM)
- STEPS: All payroll runs = `*` (all go through BCM)
- OBPM5: Cross-payment media merging indicator set

### BCM Release Strategy (Dual Control)
- **BNK_INI** (1st release): Release procedure 01, WF release step → Rule 90000005. Run release workflow = **Always**
- **BNK_COM** (2nd validation): Release procedure 01, **Conditional**. Dual control for: UNES_AP_EX (prio 1), UNES_AP_ST (prio 2), UNES_AR_BP (prio 3), UNES_AP_IK (prio 4)
- Treasury transfers (UNES_TR_TR): BNK_COM = **1 validation only** (no dual control — bank-to-bank transfers are lower risk)

### BCM Payment Grouping Rules (5 FABS rules + 1 STEPS rule)

| Rule | Priority | Description | Criteria |
|------|----------|-------------|----------|
| UNES_AP_IK | 0 | US InstrucKey B1 payments | Origin=FI-AP OR FI-AR, CoCode=UNES, Method=L, InstrKey=B1 |
| UNES_AR_BP | 1 | Business Partner (Inv & FX) | Origin=FI-AR, CoCode=UNES, Customer 600000-699999 |
| UNES_TR_TR | 1 | Treasury bank-to-bank | Origin=TR-CM-BT, CoCode=UNES |
| UNES_AP_EX | 2 | Exception list (embargo countries) | Origin=FI-AP/FI-AR-PR, CoCode=UNES, Country in (MM,IR,IQ,SD,SS,SY,CU,KP,AE,MX,JO) |
| UNES_AP_ST | 3 | Standard 3rd party | Origin=FI-AP OR FI-AR, CoCode=UNES (catch-all) |
| PAYROLL | 1 | Payroll (STEPS only) | Origin=HR-PY |

**Additional grouping criteria**: All rules group by **VALUT** (value date) — ensures one payment file per execution date.

### 3 Automatic Payment Programs at UNESCO

1. **F111** — Payment Request program for bank-to-bank transfers (replenishments). Treasury manages via FRFT_B.
2. **F110** — Automatic Payment program for all 3rd party payments.
3. **Payroll payment program** — Run by BFM/PAY.

### Complete Document Type Payment Validation Matrix [VERIFIED]

| Doc Type | Description | Number Range | Payment Check |
|----------|-------------|-------------|---------------|
| KR | Supplier Invoices FI | 64 | Payment Validation Workflow |
| KA | Supplier Advances | 62 | Payment Validation Workflow |
| ER | Expense Reimbursement | 69 | Payment Validation Workflow |
| KT | Temp Supplier Payments | 70 | Payment Validation Workflow |
| IT | Invoice IC Transfer | 95 | Payment Validation Workflow |
| CO | Coupons | 91 | Payment Validation Workflow |
| AS | Advances Salaries | 63 | Payment Validation Workflow |
| P3 | Payroll Adjustments | 85 | Payment Validation Workflow |
| SN | Surnum Postings | 65 | NO (gap identified) |
| MF | MBF Postings | 81 | Payment Validation Workflow |
| IN | Insurance Transfers | 18 | Payment Validation Workflow |
| AP | Annuities & Oth Ben | 69 | Payment Validation Workflow |
| RF | Return of Funds ROF | 21 | Payment Validation Workflow |
| MR | Customer Reimburse | 72 | Payment Validation Workflow |
| PS | Prosper Requests | 44 | Payment Validation Workflow |
| PN | Participation Progr | 43 | Payment Validation Workflow |
| TD | Treasury Transaction | 41 | Payment Validation Workflow |
| TO | Other Treasury Opera | 42 | Payment Validation Workflow |
| AB | Accounting Document | 01 | Automatic Payment Block |
| RE | Invoice-Gross (MM) | 51 | Rule: post only through MM |
| ZP | Payment Posting | 20 | Rule: post only through F110/F111 |
| CP | Payments Cheque | 34 | Rule: post only through payment program |

### UIL-Specific Configuration [VERIFIED from UIL Solution Doc]
- 2 new bank accounts at Societe Generale: SOG05-EUR01 (EUR), SOG05-USD01 (USD)
- GL sub-bank accounts: 1175792 (EUR), 1175791 (USD)
- Payment methods: S (SEPA EUR), N (International EUR+USD)
- BCM: 2 validations required. UIL AP Validation up to 5,000,000 USD
- BCM Roles: `YS:FI:M:BCM_MERGE_________:`, `YS:FI:M:BCM_MON_APP______:`, `YS:FI:M:BCM_REV_REJ_PAY__:`
- Payment run users: Britta Hoffman, Larissa Steppin
- BCM validators: Atchoarena David, Jahan Nusrat, Valdes Cotera Raul, Zholdoshalieva Rakhat, Gazi Baizid, Yli-Hietanen Anssi

## Custom Payment Programs

| Program | Purpose | Package/Author |
|---------|---------|----------------|
| ZFI_SWIFT_UPLOAD_BCM | BCM SWIFT payment file upload (2.8K lines) | Z001 / P_KLEIN |
| YBSEG_REL | Payment release report | YWFI / D_CROUZET |
| ZNOTREJECT | Non-rejection handler | YWFI / D_CROUZET |
| YENH_FI_DMEE | DMEE format enhancement (credit/debit calc) | — |
| YCEI_FI_SUPPLIERS_PAYMENT | Supplier payment enhancement | — |
| Y_F110_AVIS_IBE | Payment advice form (IBE) | — |
| ZF140_CHEQUE_DOC | Cheque document form (ICTP) | — |
| RSWUWFML2 (variant ZWKFLOW_FI_EMA) | WF email notification sender | SAP standard |
| SAPFPAYM_SCHEDULE (tcode ZPAYM) | Payment medium regeneration | SAP standard |

## Data Sources

| Table | Rows | Key Fields |
|-------|------|-----------|
| T001 | 9 | BUKRS, BUTXT, LAND1, WAERS |
| T042/T042A/T042B | 9/76/9 | Payment routing + settings |
| T042E/T042I/T042Z | 89/76/263 | Methods per country + bank ranking |
| T012/T012K | 211/402 | House banks + accounts + GL |
| BNK_BATCH_HEADER | 27,443 | BCM batch headers |
| BNK_BATCH_ITEM | 600,042 | BCM batch items (VBLNR linkage) |
| REGUH | 942,011 | F110 payment run headers |
| PAYR | 4,431 | Payment register (checks) |
| BKPF | 1,677,531 | Document headers |
| BSAK/BSIK | 747,925 | Vendor cleared/open items |

## Companion & Dashboards

| Asset | Path | Size |
|-------|------|------|
| Payment Process Mining Dashboard | `Zagentexecution/mcp-backend-server-python/payment_process_mining.html` | 694KB |
| Payment & BCM Companion | `Zagentexecution/mcp-backend-server-python/payment_bcm_companion.html` | 664KB |
| Event Log (CSV) | `Zagentexecution/mcp-backend-server-python/payment_event_log.csv` | ~50MB |
| Config Extraction Script | `Zagentexecution/mcp-backend-server-python/extract_payment_config.py` | |
| Process Mining Script | `Zagentexecution/mcp-backend-server-python/payment_process_mining.py` | |
| Companion Builder | `Zagentexecution/mcp-backend-server-python/build_payment_companion.py` | |
| **Extracted ABAP Code** | `Zagentexecution/extracted_code/payment_workflow/` | 5 files, 14KB |

## Source Documentation (BFM Handover PDFs)

| Document | Path | Key Content |
|----------|------|-------------|
| FS Payment Release Workflow 2.0 | `UNESCO/DBS Team - FAM/.../Payment Release Workflow/` | 4 payment processes, 14 doc types, 7 release groups, workflow diagram |
| Technical documentation WF | Same folder | WF 90000003, sub-WF 90000002, YBSEG, SWU3 setup, agent assignments |
| Active/passive substitution | Same folder | WF substitution rules for planned/unplanned absence |
| Why wrong validators | Same folder | Email mismatch troubleshooting (SU3 vs UNESdir) |
| Workflow troubleshooting | Same folder | SWI2_DIAG, SWI2_ADM1, SWIA — restart stuck items |
| Payment process & auth 1.1 | `UNESCO/DBS Team - FAM/.../Payments/` | 4 processes, BCM B* prefix, role matrix, security incident |
| Payment process & auth 1.2 | Same folder | Extended: BCM signatory rules 90000004/90000005, OOCU_RESP, validation tiers |
| Payment exotic currencies | Same folder | Method X, SOG01-USDD1, 3 currency tiers, BCM rule UNES_AP_X |
| Regeneration payment files | Same folder | ZPAYM transaction, BCM batch status tabs |

## Integration Points

- **coordinator** — Routes payment questions here
- **fi_domain_agent** — GL posting rules, substitutions, FM-FI bridge
- **sap_transport_intelligence** — BCM post-transport checklist (SWU3, SWE2, OBPM4)
- **sap_company_code_copy** — FBZP chain gaps, 41-task post-copy checklist
- **sap_data_extraction** — Gold DB queries for payment analysis
- **psm_domain_agent** — FM commitment/actual linkage to payments

## Custom SAP Objects — YWFI Package (34 objects) [EXTRACTED]

### Extracted Source Code (`extracted_code/payment_workflow/`)

| File | Lines | Function | Architecture |
|------|-------|----------|--------------|
| `Z_GET_CERTIF_OFFICER_UNESDIR.abap` | 70 | Certifying officer lookup | **SOAP proxy** `ZROLE_MGTCO_FACADE` on logical port `LP_ROLE_MGT` → UNESCO Role Management web service. Input: posting agent email. Output: certifying officer emails. Originally RFC dest `BOC_INVOICE_WF` (migrated to web service 2019 by FGU). |
| `Z_WF_GET_CERTIFYING_OFFICER.abap` | 128 | Workflow Rule 90000001 resolver | **Orchestrator**: (1) Get posting agent from WF container → (2) Read email from USR21+ADR6 → (3) Call `Z_GET_CERTIF_OFFICER_UNESDIR` → (4) If nobody: fallback to `ZFI_PAYREL_EMAIL`. Uses `YCL_BC_TRACE_TABLE` for trace. |
| `Z_WF_FI_PR_WF_ACTOR1_DET.abap` | 238 | Workflow Rule 90000002 resolver | **Classic validation**: Reads VBWF15 (payment release customizing by FRWEG/approval path + document type). Determines actors from FI release groups. Fallback: `ZFI_PAYREL_EMAIL`. |
| `Z_WF_FI_BSEG_EVENT_PAYM_METHOD.abap` | 23 | Change document event handler | Template for BSEG change document events. Fills event container before raising. Minimal (placeholder `SKIP`). |
| `Z_WF_FI_EXCLUDE_NOTIF_EMAIL.abap` | 24 | Notification filter | Checks USR05 parameter `Z_WKF_EMAIL_NOTIF` for user. If NOT 'X' → clears email (suppresses WF notification). Called by `RSWUWFML2`. |

### Confirmed from SAP (not source-extracted)

| Object | Type | Status | Detail |
|--------|------|--------|--------|
| `YBSEG` | Business Object Subtype | CONFIRMED in TADIR | Custom BSEG subtype for workflow, package YWFI |
| `ZFI_PAYREL_EMAIL` | Custom Table | **EXTRACTED** (2 rows) | Fallback validators: A_KHISTY, E_MOYO |
| `ZAD_SMTPADR` | Custom Structure | CONFIRMED | Email address structure for certifying officers |
| `ZPAYM` | Transaction | CONFIRMED | → `SAPFPAYM_SCHEDULE` (payment medium regeneration) |
| `ZFIWFLIST` | Transaction | CONFIRMED | Workflow list display |
| `ZFI_PAYREL_EMAIL` | Transaction | CONFIRMED | Maintain fallback email table |
| `YCL_IM_MMIV_WF_FI` | Class | CONFIRMED | MM Invoice Verification workflow enhancement |
| `YINVOICE_UPDATE` | Enhancement | CONFIRMED | Invoice update enhancement |
| `YMMIV_WF_FI` | BAdI Implementation | CONFIRMED | MM Invoice WF for FI |
| `ZFIWF` | Screen variant | CONFIRMED | Workflow display screen |
| `Z_WKF_EMAIL_NOTIF` | User Parameter | CONFIRMED | Controls WF email notifications in SU01 |
| Package `YWFI` | Dev Package | **34 objects** | Complete payment workflow development. Author: D_CROUZET (2016-11-09) |

### Key Code Architecture Findings

1. **LDAP→SOAP migration (2019)**: `Z_GET_CERTIF_OFFICER_UNESDIR` was refactored from RFC destination `BOC_INVOICE_WF` to SOAP web service proxy `ZROLE_MGTCO_FACADE`. The old RFC code is commented out — confirms the Role Management system moved to a web service architecture.

2. **Dual fallback pattern**: Both rule resolvers (90000001 certifying + 90000002 classic) fall back to `ZFI_PAYREL_EMAIL` if no validator found. Currently only 2 fallback users configured (A_KHISTY, E_MOYO).

3. **Trace logging**: `Z_WF_GET_CERTIFYING_OFFICER` uses `YCL_BC_TRACE_TABLE` with structure `YSBC_TRACE_PAYMENT` — payment workflow has built-in audit trail.

4. **VBWF15 is the config table**: `Z_WF_FI_PR_WF_ACTOR1_DET` reads from VBWF15 (FI payment release customizing) — this is where the 7 release groups are configured in SPRO.

5. **Notification opt-in**: Email notifications are opt-in via USR05 parameter `Z_WKF_EMAIL_NOTIF = 'X'`. Users without this parameter get NO email notifications for workflow items.

## You Know It Worked When

1. Agent correctly identifies company code payment tier (Full/Partial/Unconfigured)
2. Agent knows UNES has 45+ house banks and can explain the field office network
3. Agent can trace Invoice → F110 → BCM → Bank for any company code
4. Agent knows BCM rules and can explain PAYROLL vs AP_ST vs TR_TR
5. Agent correctly states T042A (not T042C) is the payment method routing table
6. Agent warns about IBE/MGIE/ICBA having no F110 capability
