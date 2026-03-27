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
7. **Never assign Y_XXXX_FI_AP_PAYMENTS + YS:FI:M:BCM_MON_APP together ON THE SAME USER** — This allows bypassing BCM validation entirely. 2023 INCIDENT: payment went to Coupa→bank without BCM approval. [VERIFIED from handover docs] Note: UNES Process 4 legitimately uses BOTH roles — but on DIFFERENT users (initiator ≠ approver). The risk is one person holding both.
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
- **FABS**: F110 run ID starting with **`BCM*`** → routed to BCM (literal prefix, not just B)
- **STEPS**: All payroll runs → BCM (wildcard `*` configured — every run goes through BCM)
- Any other prefix (0, T, M, etc.) → direct processing, no BCM batch created
- Configured in: SFW5 business function `FIN_FSCM_BNK` + payment program BCM identifier field

### The 3 Payment Tiers (Data-Derived)

**Tier 1 — Full Automation + BCM (5 codes: UNES, UBO, IIEP, UIL, UIS)**
- F110 automatic payment → BCM batch grouping → bank file transmission
- Complete FBZP chain: T042 → T042A → T042E → T042I → T012 → T012K
- BCM approval workflow (BNK_INI/BNK_COM roles)

**Tier 2 — F110 Autonomous / No BCM (ICTP)**
- F110 + physical checks (PAYR Method K = 898 checks via UNI01)
- 24 payment methods configured (most of any company code)
- No BCM — T-prefix run IDs, payments go directly to bank

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

**15 BCM Rules:**
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
| UNES_AP_X | UNES | **Exception: Exotic currencies (method X)**. Catches MGA payments WITHOUT IBAN → must be rejected. All other method X payments = normal flow. | Small |

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
| X | Exotic currency payment (method X → SOG01-USDD1, 1,069 currencies) | UNES only |
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

### Named Validators by Release Group [VERIFIED from FS v2.0 Appendix]

| Release Group | Doc Types | Named Users |
|--------------|-----------|-------------|
| BFM/PAY | AS, P3, SN | Terrer Ana, Bertoldini Simona, Perriot Dominique, Sall Amadou, Tahanout Kamel, Ollivier-Hutchings Beryl |
| BFM/FRA + BFM/TRS/AR | MR | Sarr Ebrima, Kassim Yasmina, La Jeanette, Montrose Michelle, Bidault Isabelle, Nastase Claudia, Notari Dominique, Yli-Hietanen Anssi, Dinh Manh-Khang, Dagher Antoine, Gonod Caroline |
| BSP/CFS | CO | Retnasingam Shantha, Dragan Silviu, Jayasinghe Harshinie |
| HRM/SPI | MF | Ong Poun, Djamali Ibrahime |
| HRM/SPI | IN | Charvet Riitta, Djamali Ibrahime |
| HRM/SPI | AP | Charvet Riitta, Ong Poun |
| BFM/TRS/CM | RF | Notari Dominique, Yli-Hietanen Anssi, Gazi Baizid, Marquand Isabelle, Krautheim Elisabeht |
| BFM/FNS | PS, PN | Von Michael Martin, Moumpala Octave, Ba Assane |

**Fallback table** `ZFI_PAYREL_EMAIL` known entries:
- `D_CROUZET` → `D.CROUZET@UNESCO.ORG`
- `M_SPRONK_WF` → `m.spronk@unesco.org`

### Workflow Notification Email Content
When a work item is assigned, email contains: SAP FI Document Number, Vendor Number, Vendor Name, Document Type, Business Area, Amount in Document Currency (incl. Tax), Tax amount, Amount without tax, Document Created by.

### Workflow Notifications
- Program: `RSWUWFML2` variant `ZWKFLOW_FI_EMA`
- ABAP FM `Z_WF_FI_EXCLUDE_NOTIF_EMAIL` checks user parameter `Z_WKF_EMAIL_NOTIF` in SU01
- If parameter = 'X' → user gets email notifications for workflow items

### Active/Passive Substitution for WF Absence [VERIFIED from handover doc]

| Type | When Used | Behavior | Setup |
|------|-----------|----------|-------|
| **Active** | Planned absence (e.g., 10-day leave) | Work items automatically appear in substitute's inbox too | Settings → Workflow Settings → Activate substitute |
| **Passive** | Unplanned absence (long-term fallback) | Substitute must manually "Adopt Substitution" to see items | Settings → Workflow Settings → Adopt Substitution |

**Key rules:**
- Substitute does NOT need original user's password or ID
- Substitute cannot access other data beyond WF items (authorization limited to WF scope)
- Work items completed by either user disappear from both inboxes automatically
- Active substitution: items appear in BOTH inboxes simultaneously
- Substitute can receive email notifications for new work items
- Passive: substitute can cover multiple approvers, selects which approver's inbox to view

**Configuration via SU3** → Maintain substitute (OOCU_RESP for org unit level)

### Workflow Routing Failure Diagnostic [VERIFIED — 3-Step Process]

When WF item goes to wrong person or nobody:
1. **FB03** — check "Entered by" field on the FI document header (who posted it)
2. **SU3** → Address tab → check E-Mail Address for that posting user
3. **UNESdir / role.hq.int.unesco.org** → check what email is in the Role Management system

**Root cause**: If SU3 email ≠ UNESdir email → workflow cannot find certifying officer → goes to fallback (ZFI_PAYREL_EMAIL). User must correct SU3 email. **All future items route correctly after fix. Past items remain unchanged.**

### Workflow Troubleshooting Transactions
| Transaction | Purpose |
|-------------|---------|
| SWI2_DIAG | Diagnosis of workflows with errors (restart stuck items). Handles document locking errors — select item + "Restart workflow" |
| SWI2_ADM1 | Work items without agents (forward to correct validator) |
| SWIA | Work Item Administration Report (lookup + forward). Filter by Status=Ready + work item text "Payment release for Invoice..." |
| SWU3 | Workflow runtime environment check |
| SWU_OBUF | Synchronize workflow buffers |
| PFTS | Task agent assignment maintenance |

### SPRO Customizing Path (Payment Release)
```
Financial Accounting → Accounts Receivable and Accounts Payable
  → Business Transactions → Release for Payment
    → Create/Assign Workflow Variant
    → Define Release Approval Groups / Paths / Procedures
    → Define Relevant Document Types
    → Define Users with Authorization to Payment Release
    → Define Payment Block Reason for Payment Release
```

### SWU3 Go-Live Setup (run in each client — QA + P01)
1. Run "Perform Automatic Workflow Customizing" (covers RFC dest WORKFLOW_LOCAL_xxx, WF-BATCH user, plan version)
2. Assign agent for tasks via `PFTS`: enter TS90000002, TS90000007, TS90000008 → Extras → Agent Assignments → General Task → Update Index
3. Run `SWU_OBUF` to synchronize buffers
4. Verify via "Start Verification Workflow" button in SWU3 → check SAP Business Workplace inbox

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

### BCM Authorization Objects [VERIFIED from Blueprint pp.41-60 + SAP Note 1076337]

**F_STAT_MON** — Controls BNK_MONI (Batch Monitor) and BNK_APP (Approve Payments)

| Field | Values | Description |
|-------|--------|-------------|
| BNK_RULE | Rule ID | Which BCM rule the user can process |
| BNK_ACT | READ, EDIT, R, F, B | READ=display, EDIT=edit batch, R=reject, F=release, B=return |
| BNK_ITMDFT | X / blank | X=display items, blank=no items displayed |

**F_STAT_USR** — Signature User (4-eye principle for BNK_APP)
- Assigns a "signature user" to each logon user for approval confirmation
- One person maintains the relation, another person confirms it (hard-coded 4-eye)
- Activities: 01=Create, 31=Confirm
- Configured via: Accounting → FSCM → BCM → Environment → Current Settings → Maintain/Confirm Signature User

**SAP Note 1076337** — BCM: Additional recommendations for customizing (BCM authorizations)

**Authorization Changes Required When Implementing BCM:**
1. Remove direct file generation from F110/F111 (payment files must go via BCM only)
2. Restrict SWIFT directory access: `\\hq-sapift\SWIFTS\*` — only SAPFPAYM can write (no other SAP program, no individual Windows users)
3. Add BCM transactions to AP role: FBPM1 (merge), BNK_MERGE_RESET (reset), FBPM2 (unmerged)
4. Add to validator roles: BNK_APP (approve), BNK_MONI (monitor), BNK_MONIA (alt monitor)
5. Add to TRS role: FTE_BSM (bank statement monitor), payment file creation
6. Add to AR role: FTE_BSM (bank statement monitor)

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

### Special Currency Restrictions [VERIFIED from FS Exotic Currency Requirements]

| Currency | Country | Status | Restriction |
|----------|---------|--------|-------------|
| UAH | Ukraine | **Not serviced** | Cannot process — bank will not execute |
| VEF | Venezuela | **Not serviced** | Cannot process — bank will not execute |
| LYD | Libya | **Compliance pre-approval required** | Must get compliance clearance before each payment |
| YER | Yemen | **Compliance pre-approval required** | Must get compliance clearance before each payment |
| ARS | Argentina | **PMT held 90 days** | Payment held by Citibank for 90 days due to Argentine regulations |
| COP | Colombia | **Tax ID required** | STCD field needed in vendor master — out of scope for standard method |
| IRR | Iran | **Embargo** | Cannot process — OFAC/UN sanctions |
| MMK | Myanmar | **Embargo** | Cannot process — OFAC/UN sanctions |
| SDG | Sudan | **Embargo** | Cannot process — OFAC/UN sanctions |

**For UAH/VEF/LYD/YER**: AO must arrange alternative payment mechanism outside SAP (local banking, manual wire). Document as Process 1 (Outside SAP).

### Exotic Currency Note to Payee — SWIFT Field :70 [VERIFIED from FS Note to Payee v1.1]

**Payment method X** generates SWIFT field :70 (Note to Payee) with this structure:
```
EXO//Detailed reason for payment//additional information//
```
- Fixed prefix: `EXO//` — mandatory for ALL exotic currency payments (identifies file as exotic)
- One entry per paid document (1 payment can cover multiple invoices — each gets its own entry)
- "Detailed reason for payment" → determined from **REGUP-BLART** (document type) via custom table
- "Additional information" → **FPAYP-XBLNR** (external document number / vendor invoice ref)

**OBPM2 Note to Payee name:** `Y_EXOTIC_CURRENCY` — linked to payment method X and format `/Cmi101`

**Function modules:** `Y_FI_PAYMEDIUM_NOTE_TO_PAYEE` (logic), `Y_FI_PAYMEDIUM_41` (may need changes)

**Document Type → Payment Reason mapping** (custom table, REGUP-BLART as key):

| Doc Type | Description | Reason in :70 field |
|----------|-------------|---------------------|
| AP | Annuities & Oth Ben | RENTS |
| AS | Advances Salaries | STAFF MEMBER SALARY |
| CO | Coupons | INVOICE |
| ER | Expense Reimbursement | STAFF MEMBER REIMBURSEMENT |
| IN | Insurance Transfers | INSURANCE |
| IT | Invoice IC Transfer | INVOICE |
| KA | Supplier Advances | SUPPLIER INVOICES |
| KR | Supplier Invoices FI | SUPPLIER INVOICES |
| KT | Temp Supp. Payments | STAFF MEMBER SALARY |
| MF | MBF Postings | MEDICAL CLAIM |
| MR | Customer Reimbursement | CUSTOMER REIMBURSEMENT |
| P3 | Payroll Adjustments | STAFF MEMBER SALARY |
| PN | Participation Program | CONTRIBUTION FROM UNESCO |
| PS | Prosper Requests | PAYMENT TO THIRD PARTY |
| RE | Invoice-Gross (MM) | INVOICE |
| RF | Return of Funds ROF | INVOICE |
| TF | Travel Req Field Off | STAFF TRAVEL |
| TV | Travel Request FI TV | STAFF TRAVEL |

**Madagascar (MGA) special rule for SWIFT field :57**:
- Trigger: method X + currency MGA + beneficiary bank country MG (ALL three conditions)
- Standard: cannot use :57A and :57D simultaneously in SWIFT format
- Rule: use **:57D only** (Option D) — contains BIC + full bank name + address in one field
- Fields: Sub-field 1 = `/34x` → `fpayh-zbnka` (bank name); Sub-field 2 = `4*35x` (address + city + branch + BIC)
- Function module to modify: `Y_FI_PAYMEDIUM_101_30`

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

**Legacy format (retired)**: `/CITI/XML/UNESCO/DIRECT_CREDIT` — Citi PMW Template Master V2. Used for standard ACH/WIRE before 2022. Replaced by DC_V3_01 for all company codes. Do not create new payment methods pointing to this format.

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
| `Y_FI_PAYMEDIUM_NOTE_TO_PAYEE` | /Cmi101 (method X) | Exotic currencies: builds SWIFT :70 field with `EXO//reason//XBLNR//` |
| `Y_FI_PAYMEDIUM_101_20` | /Cmi101 | HR payroll: CMI101 tags :21R (header ref) and :21 (item ref = PERNR last 7) |
| `Y_FI_PAYMEDIUM_101_30` | /Cmi101 | Madagascar MGA: SWIFT :57D Option D (BIC + bank name/address in one field) |
| `DMEE_EXIT_SEPA_21` | /SEPA_CT_UNES | HR payroll: populates `<PmtInfId>` XML node with laufi+identifier+month formula |

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

### SWIFT Directory Access Control [VERIFIED from Solution Description Payment Process]

**Path**: `\\hq-sapitf\SWIFTS\Input\*` (payment files to bank) and `\\hq-sapitf\SWIFTS\output\*` (EBS + PSR from bank)

| Access Group | Rights | Who |
|---|---|---|
| NT AUTHORITY\SYSTEM | Full control | System administrators |
| SAPServiceP01 + p01adm | Modify | SAP technical operations |
| SA_SWIFT (Marlies Spronk/KMI/FAM) | Modify | SWIFT coordinator |
| SG-SAPITF-SWIFT-RO | Read/Execute | Functional staff (list below) |

**SG-SAPITF-SWIFT-RO members** (as of 2021-10-20, maintained by Vincent Vaurette/SAP Admin):

| BFM/TRS | BFM/FAS | KMI |
|---------|---------|-----|
| Adjanohoun, Irma | Bertoldini, Simona | Spronk, Marlies |
| Streidwolf, Engelhard | Derakhshan, Farinaz | |
| Eng, Thavry | La, Jeanette | |
| Gazi, Baizid | Lopez-Chemouny, Christina | |
| Gupta, Abhishek | Marquand, Isabelle | |
| Sopraseuth, Thepthevy | Mathewos, Mehari | |
| Wettie, Ingrid | | |
| Yli-Hietanen, Anssi | | |

**Security rule**: No individual user has write access to SWIFT folders. Only `SAPFPAYM` program can write to `\\hq-sapitf\coupa$\P01\In\Data`. Access changes requested to Vincent Vaurette.

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
| OBPM2 | Configure fixed payment reference (SEPA remittance) |
| OBPM4 | Create selection variants for payment medium (**NEVER transported**) |
| OBPM5 | Set indicator for merging cross-payment media |
| FBPM1 | Merge payments in BCM |
| BNK_APP | Approve payments in BCM |
| BNK_MONI | Monitor payment batch status |
| BNK_BNK_INI_REL01 | Assign release procedure to BNK_INI |
| BNK_BNK_COM_REL01 | Assign release procedure to BNK_COM |

## Payment Purpose Code (PPC) [VERIFIED from FS XML v2.0 + 20240321 Presentation]

**Scope**: SG format only (`/CGI_XML_CT_UNESCO`). Citibank payments do NOT use PPC. SG transmits to local banks that require a purpose code per regulatory mandate.

### Architecture: BAdI per Country [VERIFIED from Gold DB CTS + SQL analysis]

The DMEE exit `FI_CGI_DMEE_EXIT_W_BADI` dispatches to per-country BAdI classes. Gold DB CTS confirms the following taxonomy:

**Naming convention** (important — two separate patterns):
- `Y_IDFI_CGI_DMEE_COUNTRIES_XX` (ENHO only) = character/address handling for country XX (DE, FR, IT, AE)
- `Y_IDFI_CGI_DMEE_COUNTRY_XX` (ENHO + **ENBC**) = PPC-specific BAdI for country XX

**PPC-enabled ENBC implementations confirmed in CTS:**
| BAdI Object | Class | Country |
|------------|-------|---------|
| `Y_IDFI_CGI_DMEE_COUNTRY_AE` | `YCL_IDFI_CGI_DMEE_AE` | UAE [CONFIRMED] |
| `Y_IDFI_CGI_DMEE_COUNTRY_BH` | `YCL_IDFI_CGI_DMEE_BH` | Bahrain [CONFIRMED] |

**Address/formatting ENBC only (NOT PPC):**
- `Y_IDFI_CGI_DMEE_COUNTRIES_DE` → Germany (address)
- `Y_IDFI_CGI_DMEE_COUNTRIES_FR` → France (address)
- `Y_IDFI_CGI_DMEE_COUNTRIES_IT` → Italy (address)

**Utility class (fallback mechanism):**
- `YCL_IDFI_CGI_DMEE_UTIL` — method `GET_TAG_VALUE_FROM_CUSTO` — reads tag values from customizing tables. Countries without dedicated BAdI (CN, ID, IN, JO, MA, MY, PH) likely route through this class using T015L-LZBKZ as the configured value. [INFERRED — source code not read]

**`YOPAYMENT_TYPE`** (CUS0 + CUS1 confirmed in CTS) — custom table storing payment type codes. Data element `YE_HRMBF_PAYMENT_TYPE`. Likely used for P/R payment type detection. [CONFIRMED table exists; CONTENT unread — needs RFC or SM30]

**T042Z finding**: AE, BH, JO, MA are NOT in T042Z (no per-country payment method descriptions). This confirms these destinations are served by cross-border methods (N, X) without country-level method restriction. CN, ID, MY, PH ARE in T042Z with local methods (B/C/T/W).

### Design: SCB Indicator as PPC Carrier

**Key insight**: UNESCO uses the **SCB indicator field** (`T015L-LZBKZ`) — normally the "State Central Bank indicator" in German banking — as the carrier for Payment Purpose Codes. This field is per payment method/currency in table T015L, and is readable in DMEE via `REGUP-LZBKZ`.

**Country resolution gap**: T015L is keyed by (BUKRS + payment method + currency), NOT by destination country. If the same method/currency combination serves multiple PPC countries (e.g., method N/USD for both UAE and India), the BAdI class must also read the beneficiary country (`REGUP-UBISO` or `FPAYHX.ZBISO`) and perform a per-country lookup or branch. The T015L LZBKZ value likely acts as a flag or default; the actual per-country PPC logic is inside `YCL_IDFI_CGI_DMEE_AE`/`_BH` etc. [INFERRED — needs source code read to confirm]

| SAP Field | Table | Usage |
|-----------|-------|-------|
| LZBKZ | T015L | SCB indicator — repurposed as PPC container |
| LZBKZ | REGUP | Read at payment run time → passed to DMEE exit |
| LAUF1 suffix | REGUP | Payment type detection: 'P' = payroll, 'R' = replenishment, other = vendor |

**Payment type detection via REGUP-LAUF1**:
- Last character = `P` → Payroll payment → purpose code = `SALA` (ISO 20022 — Salary)
- Last character = `R` → Replenishment → purpose code = `IFT` (Intracompany funds transfer)
- Otherwise → Vendor/supplier payment → use country-specific PPC from T015L/LZBKZ

**XML placement**: DMEE exit `FI_CGI_DMEE_EXIT_W_BADI` (already handling beneficiary name overflow) also handles PPC injection into:
- `InstrForCdtrAgt/InstrInf` — Instruction for creditor agent
- `Purp/Cd` — Purpose code element (ISO 20022 standard)

### 8-Country Purpose Code Tables [VERIFIED from 20240321 Presentation]

#### UAE (AE) — 20 codes
| PPC | Description |
|-----|-------------|
| BEXP | Business Expenses |
| CORT | Trade Settlement |
| DIVI | Dividends |
| GOVT | Government Payment |
| HEDG | Hedging |
| ICCP | Irrevocable Credit Card Payment |
| IHRP | Instalment Hire Purchase |
| INTC | Intracompany Payment |
| INTP | Interest Payment |
| LOAN | Loan |
| MGSC | Mortgage |
| OTHR | Other |
| PENS | Pension |
| RINP | Regular Instalment Payment |
| SALA | Salary / Staff Payment |
| SECU | Securities |
| SSBE | Social Security Benefit |
| SUPP | Supplier Payment |
| TAXS | Tax Payment |
| TREA | Treasury Payment |

#### Bahrain (BH)
| PPC | Description |
|-----|-------------|
| SALA | Salary |
| SUPP | Supplier Payment |
| GOVT | Government Payment |
| TREA | Treasury |
| OTHR | Other |

#### China (CN)
| PPC | Description |
|-----|-------------|
| 001 | Goods import/export |
| 002 | Service |
| 003 | Current transfer income |
| 101 | Direct investment |
| 102 | Securities investment |
| 999 | Other capital items |

**Note**: China uses numeric codes, not ISO 20022 text codes. Injected into `InstrInf` field.

#### Indonesia (ID)
| PPC | Description |
|-----|-------------|
| SALA | Salary |
| SUPP | Goods/Services Purchase |
| TREA | Capital / Treasury |
| CORT | Trade Settlement |
| OTHR | Other |

#### India (IN)
| PPC | Description |
|-----|-------------|
| P0001 | Advance payment against imports |
| P0002 | Payment towards imports |
| P0005 | Payments for services (non-software) |
| P0006 | Payments for software services |
| P0008 | Salary remittance |
| P0010 | Remittance towards consultancy |
| P1006 | Dividend remittance |
| P0009 | Other current account payments |

**Note**: India uses 5-character alphanumeric codes (RBI purpose codes). Must be transmitted in `Purp/Cd`.

#### Jordan (JO)
| PPC | Description |
|-----|-------------|
| SALA | Salary |
| SUPP | Supplier/Vendor |
| GOVT | Government / Institutional |
| TREA | Treasury |
| OTHR | Other |

#### Morocco (MA)
| PPC | Description |
|-----|-------------|
| SALA | Salary |
| SUPP | Supplier |
| TREA | Treasury Transfer |
| OTHR | Other |

#### Malaysia (MY) and Philippines (PH) [INFERRED — same codes assumed; no dedicated BAdI confirmed in CTS]
| PPC | Description |
|-----|-------------|
| SALA | Salary |
| SUPP | Trade / Vendor |
| TREA | Intra-group / Treasury |
| OTHR | Other |

### Configuration Points

| Step | Where | What |
|------|-------|------|
| 1 | T015L (transaction OBAT or SM30) | Enter PPC value in LZBKZ field per payment method + currency |
| 2 | DMEE: `/CGI_XML_CT_UNESCO` | Node `Purp/Cd` or `InstrInf`: source = REGUP-LZBKZ with exit logic |
| 3 | Exit `FI_CGI_DMEE_EXIT_W_BADI` | Intercepts LZBKZ + detects payroll (LAUF1 suffix 'P') / replenishment ('R') |
| 4 | Test in V01 | Verify XML contains correct `<Purp><Cd>` element for country |
| 5 | Bank confirmation | Each local SG bank confirms receipt with correct PPC |

### Cross-Domain Warning: AE + JO Are Dual-Flagged

UAE (AE) and Jordan (JO) appear in TWO separate control lists:
1. **BCM UNES_AP_EX exception rule** — payments to AE/JO are routed to the exception batch (manual oversight)
2. **PPC requirement** — payments to AE/JO require a purpose code in the XML

When paying to UAE or Jordan: the payment gets exceptional BCM handling AND needs a valid PPC in the DMEE output. Both controls must be satisfied.

**India compliance note**: RBI purpose codes (P0001-P1006) change periodically. Verify against current [RBI Annex-I](https://www.rbi.org.in) before adding new India payment types. Stale codes will cause bank rejection.

### Known Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| Bank rejects file | Missing PPC — country requires it but T015L-LZBKZ not set | Add PPC in T015L for payment method + currency |
| SALA sent as SAL | Incorrect 3-char code — ISO 20022 requires 4-char SALA | Verify exit uses `SALA` not `SAL` for payroll |
| Wrong PPC on payroll | LAUF1 suffix detection logic not triggered | Check payment run ID format; verify YOPAYMENT_TYPE table content |
| China code rejected | Sending ISO text code instead of numeric | Verify DMEE condition: `LZBKZ` populated with 3-digit numeric for LAND1=CN |
| India code invalid | RBI codes change periodically (last verified 2024) | Verify against current RBI Annex-I list |
| MY/PH PPC wrong | Codes assumed identical to shared ISO set — not BAdI-confirmed | Read actual YCL_IDFI_CGI_DMEE class for MY/PH if it exists |

---

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

### Payroll BCM Payment Flow [VERIFIED from Helpcard Payroll Payments BCM]

Full end-to-end flow for payroll bank payments:

| Step | Transaction | Action | Notes |
|------|-------------|--------|-------|
| 1 | **ZHRUN** | Prepare payroll payment | Test mode first (simulate). STEPS payroll system. |
| 2 | **FBPM1** | Merge payments into BCM batch | Creates BCM batches from payroll payment documents. |
| 3 | **BNK_APP** | BCM validation (PAY group → TRS group) | 2-step approval: Chief PAY (BFM 046) then Treasurer (BFM 076/073). |
| 4 | **BNK_MONI** | Monitor batch status | Confirms batch sent to bank. |
| 5 | **BNK_MERGE_RESET** | Reset batch if needed | Use only when payment must be re-run (e.g., wrong value date). |

**BNK_MERGE_RESET parameters**:
- `P_BATNO` = Batch number to reset (required — SAP Note 1892712 fixes field label)
- Test mode: Run first to check what will be reset
- Strict check: If errors exist, reset is blocked until resolved
- SAP Note 1681517: Adds restriction to reset by batch number only (prevents mass reset)

### HR Payroll Payment References [VERIFIED from FS HR Payroll Payment References v2.1]

**Context**: Payroll runs generate payment files in STEPS (now iRIS). Payment file and bank statement are in different systems — SAP standard references don't match. A custom reference is built for automated reconciliation.

**SAP Objects**: Package `ZHR_HR_POSTING`, Class `ZCL_PAYMENT_REF`, Author: Claude-Henri Berger

**Scope restriction**: These modifications are ONLY valid for payroll (REGUH-DORIGIN = 'HR-PY'). Must NOT be applied to FABS.

#### BSEG-ZUONR Assignment (bulk payments — house bank SOG01, account EUR01)

**Payment method S** (SEPA zone, from Feb 2014 — replaces H and I):

| Business Area | Identifier | Formula |
|---------------|-----------|---------|
| GEF | `6` | `CONCATENATE reguh-laufi(4) '6' reguh-LAUFD+4(2)` |
| OPF | `7` | `CONCATENATE reguh-laufi(4) '7' reguh-LAUFD+4(2)` |
| Other | `8` | `CONCATENATE reguh-laufi(4) '8' reguh-LAUFD+4(2)` |

**Payment method H** (legacy, France domestic — deactivatable as no longer in use):

| Business Area | Identifier | Formula |
|---------------|-----------|---------|
| GEF | `1` | `CONCATENATE reguh-laufi(4) '1' reguh-LAUFD+4(2)` |
| OPF | `2` | `CONCATENATE reguh-laufi(4) '2' reguh-LAUFD+4(2)` |
| Other | `3` | `CONCATENATE reguh-laufi(4) '3' reguh-LAUFD+4(2)` |

**Decoding the formula**: `laufi(4)` = first 4 chars of run ID + identifier digit + `LAUFD+4(2)` = 2-digit month from run date

#### Individual payments (non-bulk):
- BSEG-ZUONR = **last 7 positions of REGUH-PERNR** (personnel number, including leading zeros)
- Example: PERNR=`10000050` → ZUONR=`0000050`

#### CITI Bank rule (added v2.1, January 2019):
- For all payroll postings via CITI bank: BSEG-ZUONR = **REGUH-VBLNR** (individual payment doc number)
- Replaces personnel number logic for Citibank payroll payments
- SAP Notes: **2007174** + **505698** (payment document number on HR payroll)

#### DMEE — SEPA XML File Reference (/SEPA_CT_UNES)
- Format tree: `/SEPA_CT_UNES`, tree type PAYM, edit via DMEE transaction
- Field modified: `<PmtInfId>` (Payment Information ID XML node)
- User exit: **`DMEE_EXIT_SEPA_21`** — applies same bulk formula (identifiers 6/7/8) to XML node

#### CMI101 File — HR Payroll Tags
- Function module (unchanged): **`Y_FI_PAYMEDIUM_101_20`**
- Tag `:21R` (Header Reference): same formula as ZUONR (bulk = laufi+identifier+month; other = REGUT-RENUM last 7)
- Tag `:21` (Item Reference): last 7 positions of REGUH-PERNR (individual beneficiary reference on bank statement)

### BNK_APP — Digital Signature & 5 Key Actions [VERIFIED from Helpcard BCM Validation]

**Digital signature process**:
- Type: **System Signature** (not PKI certificate)
- Authentication: SAP User ID + Password entered at approval time
- Purpose: Non-repudiation — signatory confirms approval with credentials
- BCM checks: signature user linked via F_STAT_USR authorization object

**5 Primary Actions in BNK_APP**:
1. **Validate batch** — Approve the payment batch (triggers WF to next signatory or file creation)
2. **Reject batch** — Send back to originator with reason (triggers returned-batch WF)
3. **Change line layout** — Adjust display columns (cosmetic only, no payment impact)
4. **Change value date** — Modify the payment execution date (must be within allowed range)
5. **Log / History** — View full audit trail: who validated/rejected and when

**BNK_MONI Status Tabs**:
| Tab | Meaning |
|-----|---------|
| New | Batch created, not yet submitted for approval |
| In Approval | BCM validation in progress (1 or 2 signatories pending) |
| Approved | All signatures complete, file creation scheduled |
| Sent to Bank | File created and transferred via SWIFT |
| Completed | Bank confirmed receipt and processing |
| Exceptions | Error during file creation or SWIFT transfer |

### Fixed Payment Reference (SEPA) [VERIFIED from FS Fixed Payment Reference]

**Purpose**: Ensures a consistent, traceable payment reference in SEPA credit transfers. Replaces auto-generated references for specific vendor/document type combinations.

**Configuration**: Transaction **OBPM2** — Payment Reference

**Reference Table** (custom, per UNESCO):
- Key: BUKRS + LIFNR + BLART + BELNR
- Value: 75-character payment reference string

**Formula when no table entry**:
```
/INV/&FPAYP-XBLNR& &FPAYP-BLDAT(Z)&
```
- `XBLNR` = External document number (vendor invoice number)
- `BLDAT(Z)` = Document date formatted as YYYYMMDD

**DMEE Trees using fixed reference**:
- `SEPA_CT_UNES` — UNESCO SEPA Credit Transfer format
- `CMI101` — CMI payment format (tag 20/23 contract reference)

**Why this matters**: Without fixed references, remittance information in the bank file uses SAP-generated IDs that vendors cannot match to their invoices. Fixed references use the vendor's invoice number → zero reconciliation effort.

### Complete Document Type Payment Validation Matrix [VERIFIED — 37 types]

**Workflow types** (blocked on posting, released by workflow):

| Doc Type | Description | Number Range | Payment Check |
|----------|-------------|-------------|---------------|
| AP | Annuities & Oth Ben | 69 | Payment Validation Workflow |
| AS | Advances Salaries | 63 | Payment Validation Workflow |
| CO | Coupons | 91 | Payment Validation Workflow |
| ER | Expense Reimbursement | 69 | Payment Validation Workflow |
| IN | Insurance Transfers | 18 | Payment Validation Workflow |
| IT | Invoice IC Transfer | 95 | Payment Validation Workflow |
| KA | Supplier Advances | 62 | Payment Validation Workflow |
| KR | Supplier Invoices FI | 64 | Payment Validation Workflow |
| KT | Temp Supplier Payments | 70 | Payment Validation Workflow |
| MF | MBF Postings | 81 | Payment Validation Workflow |
| MR | Customer Reimburse | 72 | Payment Validation Workflow |
| P3 | Payroll Adjustments | 85 | Payment Validation Workflow |
| PN | Participation Progr | 43 | Payment Validation Workflow |
| PS | Prosper Requests | 44 | Payment Validation Workflow |
| RF | Return of Funds ROF | 21 | Payment Validation Workflow |
| SN | Surnum Postings | 65 | NO (gap — not in workflow) |
| TD | Treasury Transaction | 41 | Payment Validation Workflow |
| TO | Other Treasury Opera | 42 | Payment Validation Workflow |

**Automatic payment block** (substitution rule sets block N on posting — cannot be removed):

| Doc Type | Description | Range |
|----------|-------------|-------|
| AB | Accounting Document | 01 |
| AC | Assessed Contributions | 73 |
| FO | Field Office Posting | 40 |
| IM | Imprests | 33 |
| IO | IOVs Postings | 93 |
| IP | Incoming Payments | 32 |
| JV | Adjustment Postings | 92 |
| KG | Vendor Credit Memo | 17 |
| KX | Visits and Missions | 15 |
| KZ | Vendor Payment | 14 |
| OP | Outgoing Payments Oth | 31 |
| PF | Payroll FOPAG | 87 |
| PP | Payroll Posting | 86 |
| PX | Payroll Posting | 88 |
| R8 | Migration for FO | R8 |
| RB | Rebilling | 67 |
| RV | Billing Doc Transfer | 19 |
| SR | Sales & Renting Post | 74 |
| SX | Surnum Postings | 68 |
| VC | Voluntary Contrib | 75 |
| Z5 | Petty Cash Postings | 39 |

**Special rules** (posted only through specific programs):

| Doc Type | Description | Rule |
|----------|-------------|------|
| CA | Crossed Payee Cheque | Only via F-58, FB01, FB02, FB08, FBL1N, FBL3N |
| CC | Cashable Cheque | Same as CA |
| CP | Payments Cheque | Only via payment program |
| RE | Invoice-Gross (MM) | Only via MM (pre-validations in MM process) |
| TF | Travel Req Field Off | Only via TV module |
| TV | Travel Request FI TV | Only via TV module |
| ZP | Payment Posting | Only via F110/F111 or FB08 reversal |

### UIL-Specific Configuration [VERIFIED from UIL Solution Doc]
- 2 new bank accounts at Societe Generale: SOG05-EUR01 (EUR), SOG05-USD01 (USD)
- GL sub-bank accounts: 1175792 (EUR), 1175791 (USD)
- Payment methods: S (SEPA EUR), N (International EUR+USD)
- BCM: 2 validations required. UIL AP Validation up to 5,000,000 USD
- BCM Roles: `YS:FI:M:BCM_MERGE_________:`, `YS:FI:M:BCM_MON_APP______:`, `YS:FI:M:BCM_REV_REJ_PAY__:`
- Payment run users: Britta Hoffman, Larissa Steppin
- BCM validators: Atchoarena David, Jahan Nusrat, Valdes Cotera Raul, Zholdoshalieva Rakhat, Gazi Baizid, Yli-Hietanen Anssi

---

## Field Office Cash & Manual Cheque Handling [VERIFIED from CR 126/127 BBP]

**Background**: CR 126 (Cash Journal), CR 127 (Manual Cheque), CR 15 (Bank Reconciliation) — implemented 2019–2020 for field offices under company code UNES.

### Cash Journal — FBCJ (CR 126)
- **Transaction**: FBCJ
- **Document type**: Z5 — Petty Cash Postings (number range 39)
- **G/L must be "Post automatically only"** in FS00 — prevents direct manual postings
- **Number range**: Must be 01 (SAP requirement). Incoming: 1900000000–1999999999, Outgoing: 2900000000–2999999999
- **Created manually before go-live in P01**

**Pilot cash journals (UNES company code):**

| Office | Cash Journal | G/L Account | Currency |
|--------|-------------|------------|---------|
| Dakar | DAK1 | 1900254 | XOF |
| Mexico | MXC1 | 1900434 | MXN |
| Santiago | STG1 | 1900574 | CLP |
| Tashkent | TAS1 | varies | UZS |

**18 Business Transactions defined** including: Customer/Vendor/G/L postings, FUEL PURCHASES (6022020), OFFICE SUPPLIES (6022023), POSTAGE COURIER (6024011), TAXI (6025011), MAINT & REPAIR (6032011/13/14), COURTESY EXPENSES (6035011).

**Key G/L accounts:**
| Account | Description |
|---------|-------------|
| 2021011 | Cash journal vendor clearing |
| 2022011 | UNDP advance G/L |
| 2029091 | Advance payment (Special G/L F) |
| 9112034 | UNDP bank clearing account |

### Manual Cheque — F-58 (CR 127)
- **Transaction**: F-58 (Payment with Printout)
- **Two new document types**: CA (Crossed/Payee Cheque), CC (Cashable Cheque)
- Default for F-58 = CA; user can change to CC; can be bank-account-specific
- CA and CC **only allowed in**: F-58, FB01, FB02, FB08, FBL1N, FBL3N

**Pilot house banks for manual cheques:**

| Office | House Bank | Account | Currency | Sub Bank Acct |
|--------|-----------|---------|----------|--------------|
| Santiago | BAE01 | CLP01 | CLP | 1109574 |
| Mexico | CIT14 | MXN01 | MXN | 1143434 |

### Cash Replenishment — 4 Methods

| Method | When Used | Key Transaction | Notes |
|--------|-----------|----------------|-------|
| 1 — Cheque to staff member | Standard FO with bank account | F-47 (advance) → F-58 (CC cheque) → FBCJ | ZP+Z5 assignments aligned for BFM/AP clearing |
| 2 — Bank transfer to staff member | Antenna office (no local bank account, HQ sends local ccy) | F-47 (advance) → payment via F110 → FBCJ | Instruction Key change to HQ |
| 3 — Via UNDP | No local bank, HQ cannot send local ccy | F-48 (vendor DP) + Prosper request → UNDP pays → FBCJ | G/L 9112034 (UNDP clearing), Business Area GEF |
| 4 — Cash facilitator | Remote location (e.g., Baghdad → Amman/Erbil) | FBCJ vendor posting → MIRO or FB60 for fee/invoice | Vendor 333061 = FLIGHT CENTRE (Mexico example) |

### Bank Reconciliation (CR 15) — Cheque Clearing via EBS
- Check number registered in F-58 → printed on physical cheque
- When cashed: bank statement provides check number via code **NCHK**
- EBS auto-matches NCHK → clears vendor payment document
- **FEBAN**: manual processing for non-auto-cleared items
- **EBS posting rules**: SUBE (Income MT940 clearing), SUBF (Payment MT940 clearing)
- **Posting Type 4** = Clear debit G/L, **Type 8** = Clear credit sub-ledger (vendor)
- Transaction types: **BAE01_CL** (Bank of Chile / Santiago), **CIT23_SN** (Citibank / Dakar)

---

## EBS & SWIFT Infrastructure Architecture [VERIFIED from Solution Description EBS]

### SWIFT Integration Layer Architecture
```
SAP iRIS (F110/SAPFPAYM) → SAP Network File Directory → SWIFT Integration Layer (SIL) → SWIFT Alliance Lite 2 → Banks
```
- **SIL polling interval**: **3 minutes** (HQ general); **15 minutes** (UIL/UBO — different configuration)
- 3 directory types on SWIFT server: Payment Files, Payment Status Reports (PSR), Bank Statement Files (EBS)

### EBS File Paths — Table FEBV_FILEPATH (configured via transaction FILE)

| Path Key | Usage | Physical Directory | File Name Pattern |
|---------|-------|-------------------|------------------|
| Z_EBS_PRO | Process (new EBS files) | `\\hq-sapitf\SWIFT$\<SYSID>\output\ebs\` | `OSOGEFRPPXXX*` |
| Z_EBS_ARC | Archive (processed) | `\\hq-sapitf\SWIFT$\<SYSID>\output\ebs\archive` | — |
| Z_EBS_ERR | Error (failed) | `\\hq-sapitf\SWIFT$\<SYSID>\output\ebs\error` | `OSOGEFRPPXXX_<CCODE>_<BANK_ID>_<ACCOUNT_ID>_<STATEMENT_DATE>` |
| Z_EBS_TRA | Transfer (in transit) | `\\hq-sapitf\SWIFT$\<SYSID>\output\ebs\transfer` | — |

**EBS file naming convention**: `OSOGEFRPPXXX_<CCODE>_<BANK_ID>_<ACCOUNT_ID>_<STATEMENT_DATE>`

### SWIFT Directory Access Control
- **No individual Windows user** can write to `\\hq-sapitf\SWIFT$\*` directly
- **Only SAPFPAYM** program can write payment files (enforced via SAP authorization profile)
- **SA_SWIFT** (Marlies Spronk, KMI/FAM): Modification rights — manages SWIFT server, Autoclient, SIL
- **SG-SAPITF-SWIFT-RO**: Read and execute — BFM and KMI users for functional review

| BFM/TRS | BFM/FAS | KMI |
|---------|---------|-----|
| Adjanohoun Irma | Bertoldini Simona | Spronk Marlies |
| Streidwolf Engelhard | Derakhshan Farinaz | — |
| Eng Thavry | La Jeanette | — |
| Gazi Baizid | Lopez-Chemouny Christina | — |
| Gupta Abhishek | Marquand Isabelle | — |
| Sopraseuth Theptthevy | Mathewos Mehari | — |
| Wettie Ingrid | — | — |
| Yli-Hietanen Anssi | — | — |

**Group update managed by**: Vincent Vaurette (SAP administrator)

## Custom Payment Programs

| Program | Purpose | Package/Author |
|---------|---------|----------------|
| ZFI_SWIFT_UPLOAD_BCM | BCM SWIFT payment file upload (2.8K lines) | Z001 / P_KLEIN |
| YBSEG_REL | Payment release report | YWFI / D_CROUZET |
| ZCL_PAYMENT_REF | HR payroll payment reference class — bulk ZUONR formula + CITI VBLNR rule | ZHR_HR_POSTING / C-H Berger |
| Y_FI_PAYMEDIUM_NOTE_TO_PAYEE | Note to payee for payment method X (exotic currency SWIFT :70) | — |
| Y_FI_PAYMEDIUM_101_20 | CMI101 generation: HR payroll tags :21R + :21 (PERNR last 7) | — |
| Y_FI_PAYMEDIUM_101_30 | CMI101 :57D adjustment for Madagascar (BIC + bank name in Option D) | — |
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

**Field Office Scope**: Payment release workflow (WF 90000003) is active at UNESCO HQ only. Field offices (IBE, MGIE, ICBA) use Process 1 (outside SAP) — they post the outgoing payment directly and execute via local banking system. The workflow runs only when HQ executes a payment on behalf of a field office.

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
| FS Exotic Currency Requirements | Same folder | Full 40+ currency table, UAH/VEF not serviced, LYD/YER compliance, ARS 90-day hold |
| FS Note to Payee payment exotic currencies v1.1 | Same folder | SWIFT :70 EXO// format, Y_EXOTIC_CURRENCY in OBPM2, doc type→reason mapping, MGA :57D rule |
| FS HR Payroll payment references v2.1 | `1 Functional Specifications/` | BSEG-ZUONR bulk formula (GEF/OPF/other), CITI VBLNR rule, ZCL_PAYMENT_REF, DMEE_EXIT_SEPA_21 |
| Improvement Project to Brazil Payments | `UBO/BCM/` | 2014-2015 project (5% complete). 6 scope items: FI doc number in batch, utilities, salary transfer, auto-reconciliation, block rejected items, email to suppliers |
| Regeneration payment files | Same folder | ZPAYM transaction, BCM batch status tabs |
| FS Fixed Payment Reference | Same folder | OBPM2, SEPA reference table BUKRS/LIFNR/BLART/BELNR, formula /INV/XBLNR BLDAT |
| Helpcard BCM Validation | Same folder | BNK_APP 5 actions, digital signature (Signatory ID+password), BNK_MONI status tabs |
| Helpcard Payroll Payments BCM | Same folder | ZHRUN→FBPM1→BNK_APP→BNK_MONI→BNK_MERGE_RESET, P_BATNO parameter, SAP Notes 1681517/1892712 |
| Solution Document UIL Payment Process | `0 Solution Description/` | SOG05 EUR01/USD01, UIL BCM validators (6 persons), roles YS:FI:M:BCM_*, SFTP every 15 min |
| BBP Cash Cheque Bank Reconciliation v2 | Same folder | CR 126 (FBCJ/Z5), CR 127 (F-58/CA/CC), CR 15 (EBS/FEBAN). Project: Yli-Hietanen+Spronk |
| Solution Description Cash Cheque (Final) | Same folder | Final version: Mexico replaces Dakar as 2nd pilot, HQ 12xxxxx/13xxxxx EBS architecture |
| Cash Replenishment Solution Proposals | Same folder | 4 replenishment methods (cheque/bank transfer/UNDP/cash facilitator), G/L 2029091/9112034 |
| Solution Description Payment EBS Process | Same folder | Complete doc type registry (37 types), F111, 3 payment programs, FEBV_FILEPATH paths, SIL 3-min polling |
| Payment in exotic currencies | `Payments/` | Method X pilot 5 currencies, BCM rule UNES_AP_X, G/L 1175011/1275011/1375011, YTR2, currency scope tables (1,069 in scope, 213 out of scope), embargo list |
| Payment Release Workflow PDFs (5 docs) | `Payment Release Workflow/` | FS v2.0 (3 trigger filters, 7 groups, named validators), Technical Doc (SWU3 steps, PFTS), Wrong validators (email mismatch fix), Troubleshooting (SWI2_DIAG/SWIA), Active/passive substitution |
| FS Payment Purpose Code XML 2.0 | `Payment Purpose Code/` | Custom dev for /CGI_XML_CT_UNESCO (SG only). SCB indicator (T015L-LZBKZ) as PPC carrier. LAUF1 suffix detection (P=payroll, R=replenishment). FI_CGI_DMEE_EXIT_W_BADI handles injection |
| 20240321 Payment Purpose Code (presentation) | `Payment Purpose Code/` | Full PPC tables for 8 countries: AE (20 codes), BH, CN (numeric 001/002/003/101/102/999), ID, IN (RBI 5-char codes), JO, MA, MY/PH. XML tags: Purp/Cd + InstrInf |

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
