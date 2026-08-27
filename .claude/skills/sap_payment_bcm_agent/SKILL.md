---
name: sap_payment_bcm_agent
description: Specialized domain agent for SAP payment & BCM (Bank Communication Management) at UNESCO — F110, FBZP, house banks, payment batches, dual-control workflow 90000003, signatory rules OTYPE='RY'.
domains:
  functional: [BCM, Payment, Treasury]
  module: [FI, PD]
  process: [T2R, P2P]
tier: project
maturity: production
origin_session: 20
last_updated_session: 55
triggers: [payments, F110, BCM, FBZP, house banks, payment methods, bank communication, advance payments, payment runs, vendor clearing, dual control, 90000003, 90000004, 90000005, CRUSR, CHUSR, bank signatory, signatory panel, signature panel, change in bank signatory, add signatory, OOCU_RESP, carton, carton des signatures, IT1218, BNK_APP, RY node, signatory change]
---

# SAP Payment & BCM Domain Agent

## Metadata
- **Name**: sap_payment_bcm_agent
- **Type**: Domain Agent (specialized)
- **Maturity**: Production
- **Origin**: Session #020 — Full payment configuration extraction + process mining
- **Triggers**: Questions about payments, F110, BCM, FBZP, house banks, payment methods, bank communication, advance payments, payment runs, vendor clearing

## Purpose

Specialized agent for all SAP payment and BCM (Bank Communication Management) questions at UNESCO. This agent has complete knowledge of:
- Payment configuration across 9 operational company codes (+ STEM = 10th, FBZP chain broken)
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
- Bank statements and reconciliation → **REDIRECT to `sap_bank_statement_recon`** (dedicated agent since Session #030)
- Payment process mining results
- Company code payment capability assessment
- **Bank signatory panel changes** ("Change in Bank Signatory panel of &lt;ENTITY&gt;", add/remove a signatory in BCM) → see the **Signatory-change hub** below

> **Signatory-change hub (entry point — read in order):** (1) [`knowledge/domains/Treasury/bcm_signatory_change_solution_design.md`](../../../knowledge/domains/Treasury/bcm_signatory_change_solution_design.md) — 3-level model + **node selection in IT1218** + reconciliation; (2) [`bcm_signatory_rules.md`](../../../knowledge/domains/Treasury/bcm_signatory_rules.md) — RY nodes + change process; (3) companion `companions/bcm_signatory_companion.html`; (4) precedents `INC-000006313` (UIS) / `INC-000011781` (UBO). Mandatory output format = Reconciliation Protocol **Step 7** below. Node selection lives in **infotype 1218** (`HRP1218`/`HRT1218`, expressions on `BNK_STR_BATCH_REL_APPR`) — NOT the empty PFAC `HRP1222`.

## NEVER Do This

1. **Never confuse T042A with T042C** — T042A has the payment method→bank routing (76 rows). T042C is client-level only (0 rows).
2. **Never assume FCLM_BAM_* tables exist** — UNESCO uses `BNK_BATCH_HEADER/ITEM`, NOT the FSCM BAM tables.
3. **Never assume central payment** — All 9 company codes pay for themselves (T042 BUKRS=ZBUKR).
4. **Never tell users IBE/MGIE/ICBA can run F110** — They pay OUTSIDE SAP (manual transfer/check in local banking system). [VERIFIED from handover docs]
5. **~~Never assume FEBEP has data~~** — **CORRECTED Session #029**: FEBEP has **223,710 items** (2024-2026), 99.9% posted. FEBKO has 84,972 statement headers. EBS is FULLY active in P01. BCM handles outbound payments; EBS handles inbound bank statement import/reconciliation. They are complementary, not alternatives. See `knowledge/domains/FI/bank_statement_ebs_architecture.md` for full EBS architecture.
6. **Never skip BCM when analyzing payments** — BCM sits between F110 and bank. 374K items routed through BCM batches.
7. **Never assign Y_XXXX_FI_AP_PAYMENTS + YS:FI:M:BCM_MON_APP together ON THE SAME USER** — This allows bypassing BCM validation entirely. 2023 INCIDENT: payment went to Coupa→bank without BCM approval. [VERIFIED from handover docs] Note: UNES Process 4 legitimately uses BOTH roles — but on DIFFERENT users (initiator ≠ approver). The risk is one person holding both.
8. **Never use F110 run ID starting with B* for non-BCM payments** — B* prefix triggers BCM routing. Use any other ID for direct processing.
9. **Never use ISO 20022 text codes for T015L/PPC** — UNESCO's T015L uses custom UNESCO-specific LZBKZ values (AE0-AE8, BH0-BH5, CN0-CN2, etc.), NOT ISO 20022 codes (BEXP/CORT/SALA...). The PDF documentation is wrong on this. Always query `SELECT LZBKZ, ZWCK1 FROM T015L WHERE MANDT=350` to get the actual values in use.
10. **Never assume AE/BH PPC BAdIs are live in P01** — As of 2026-03-27, `Y_IDFI_CGI_DMEE_COUNTRY_AE` and `Y_IDFI_CGI_DMEE_COUNTRY_BH` exist only in D01 CTS transports. P01 TADIR has no record of them. UTIL fallback may still be active for these countries.

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

**Tier 3 — Manual Payment via F-53 (3 codes: IBE, MGIE, ICBA)** [VERIFIED from BSAK 2024-2026]
- NO T042A entries — F110 cannot run for these codes
- Payments ARE posted in SAP via **F-53 (BLART=OP)** — outgoing payment document created manually
- Bank transfer executed in LOCAL banking system; SAP receives the OP clearing doc
- Cleared items confirmed in BSAK: IBE=5,364 OP docs, MGIE=3,211 OP docs, ICBA=1,227 OP docs (2024-2026)
- Also see BLART=AB (reversals) and BLART=KR (direct credit memo clearing)
- "Outside SAP" means the bank instruction — the accounting document IS in SAP

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
| A | Treasury bank-to-bank transfer (F111 / FRFT_B replenishments) | UNES only |
| Q | Boleto Bar Code — Brazil domestic | UBO (CIT01/BRL01) |
| R | TED Online — Brazil electronic transfer | UBO (CIT01/BRL01) |
| W | Local country-specific (T042Z configured) | Subset of countries in T042Z |

### Process Mining Results

- **1,435,376 events** / **550,993 cases** / **12 activities** / **207 variants**
- Invoice → Payment: mean 4.1 days, median 2 days
- Invoice → Clearing (E2E): mean 5.6 days, median 2 days
- Due Date → Payment: mean 26.8 days, median 14 days [⚠ see below]
- On-Time Payment: **1.1%** [⚠ MISLEADING — see below]

**⚠ On-Time KPI is a measurement artifact [VERIFIED Session #026]**
73% of UNES invoices have `ZTERM=0001` (Net immediate) with `ZFBDT = BUDAT`. The "due date" is the posting date itself — so "26.8 days late" actually means "26.8 days from posting to payment," not lateness against payment terms. For invoices WITH actual payment terms (`ZFBDT ≠ BUDAT`):
- On-time/early: **4.6%** (9,090)
- 1–7 days late: 18% (35,558)
- 8–30 days late: 14% (28,279)
- 31–100 days late: 20% (38,863)
- 100+ days late: **43%** (85,666) ← genuine finding

**Second gap**: UNES clearing documents show `BLART=OP` (F-53 manual) = **267K** vs `BLART=ZP` (F110) = **138K**. The event log only captured ZP. Manual payments via F-53 are not modeled. The 550K case count and "Payment Executed" activity both undercount actual payments.

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
- FM gets posting user's email → calls `Z_WF_GET_CERTIFYING_OFFICER` → **calls the RoleManagement
  (RM) SOAP service** — CORRECTED s106. This line said "reads UNESCO LDAP (UNESdir)" and was
  **wrong**: it is a typed SOAP consumer proxy `zrole_mgtco_facade` with
  `logical_port_name = 'LP_ROLE_MGT'`, operation `get_certifying_officers_by_emp`. UNESDIR is a
  DIFFERENT service reached by DBCON/SQL. The FM's own name (`…_UNESDIR`) and its trace field
  (`unesdir_subrc`) carry the same mislabel — the name lies, so believing it hides the real
  dependency. Full entry: `.claude/skills/sap_interface_intelligence/SKILL.md` (RM section).
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

## Payment Purpose Code (PPC) [VERIFIED from FS XML v2.0 + 20240321 Presentation]

> ⚠ **VERIFICATION STATUS**: T015L configuration (73 rows, 8 countries) VERIFIED from P01 live query. BAdI architecture (AE+BH) VERIFIED from Gold DB CTS. **UNVERIFIED**: what exact value goes into `<Purp><Cd>` XML — is it the LZBKZ key (AE5), the abbreviation in ZWCK1 (SAL), or something else? Needs BAdI source code read (D01 ADT). AE+BH BAdIs are in D01 only — not yet live in P01. UTIL fallback for 6 other countries is INFERRED.

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

#### UAE (AE) — 9 codes [VERIFIED from T015L P01 live query]
| LZBKZ | Description (T015L.ZWCK1) |
|-------|---------------------------|
| AE0 | FIS Financial services |
| AE1 | CHC Charitable Contributions (Charity and Aid) |
| AE2 | IFS International Financial Services |
| AE3 | ITS International Trade Services |
| AE4 | PMS Project Management Services |
| AE5 | SAL Salary (Compensation of employees) |
| AE6 | RNT Rent (real estate) |
| AE7 | STR Staff Travel |
| AE8 | TCS Technical/Consultancy Services |

**Note**: UNESCO-specific codes, NOT ISO 20022 text codes. Format: `[LZBKZ] [abbrev] [description]`. BAdI `Y_IDFI_CGI_DMEE_COUNTRY_AE` confirmed in CTS (D01 only — NOT yet in P01 TADIR as of 2026-03-27). AE payments via UNES_AP_EX exception batch.

#### Bahrain (BH) — 6 codes [VERIFIED from T015L P01 live query]
| LZBKZ | Description (T015L.ZWCK1) |
|-------|---------------------------|
| BH0 | STR Staff Travel |
| BH1 | FIS Financial services |
| BH2 | IFS International Financial Services |
| BH3 | CHC Charitable Contributions (Charity and Aid) |
| BH4 | PMS Project Management Services |
| BH5 | SAL Salary (Compensation of employees) |

**Note**: BAdI `Y_IDFI_CGI_DMEE_COUNTRY_BH` confirmed in CTS (D01 only — NOT yet in P01 TADIR as of 2026-03-27).

#### China (CN) — 3 codes [VERIFIED from T015L P01 live query]
| LZBKZ | Description (T015L.ZWCK1) |
|-------|---------------------------|
| CN0 | /CSTRDR/ Reglement d'un service |
| CN1 | /CCDNDR/ (description from T015L) |
| CN2 | /COCADR/ (description from T015L) |

**Note**: China uses slash-notation codes (NOT numeric 001/002/003 as in original PDF documentation). Descriptions are in French. Uses UTIL fallback `YCL_IDFI_CGI_DMEE_UTIL.GET_TAG_VALUE_FROM_CUSTO` — no dedicated BAdI in CTS.

#### Indonesia (ID) — 9 codes [VERIFIED from T015L P01 live query]
| LZBKZ | Description (T015L.ZWCK1) |
|-------|---------------------------|
| ID0 | 2461 Business Trip |
| ID1 | 2468 (description from T015L) |
| ID2 | 2490 (description from T015L) |
| ID3 | 2495 (description from T015L) |
| ID4 | 2550 (description from T015L) |
| ID5 | 2570 (description from T015L) |
| ID6 | 2580 (description from T015L) |
| ID7 | 2640 (description from T015L) |
| ID8 | 2670 (description from T015L) |

**Note**: Indonesia uses 4-digit numeric codes. Uses UTIL fallback — no dedicated BAdI in CTS.

#### India (IN) — 11 codes [VERIFIED from T015L P01 live query]
| LZBKZ | Description (T015L.ZWCK1) |
|-------|---------------------------|
| IN0 | P0301 Purchases towards travel |
| IN1 | P0403 (description from T015L) |
| IN2 | P0802 (description from T015L) |
| IN3 | P0804 (description from T015L) |
| IN4 | P1004 (description from T015L) |
| IN5 | P1005 (description from T015L) |
| IN6 | P1006 (description from T015L) |
| IN7 | P1019 (description from T015L) |
| IN8 | P1304 (description from T015L) |
| IN9 | P1401 (description from T015L) |
| INA | P1203 Maintenance of international institutions |

**Note**: India uses RBI purpose codes (5-char alphanumeric). Uses UTIL fallback — no dedicated BAdI in CTS. RBI codes change periodically — verify against current RBI Annex-I.

#### Jordan (JO) — 10 codes [VERIFIED from T015L P01 live query]
| LZBKZ | Description (T015L.ZWCK1) |
|-------|---------------------------|
| JO0 | 206 Overseas Incoming Salaries |
| JO1 | 404 (description from T015L) |
| JO2 | 705 (description from T015L) |
| JO3 | 801 (description from T015L) |
| JO4 | 802 (description from T015L) |
| JO5 | 803 (description from T015L) |
| JO6 | 804 (description from T015L) |
| JO7 | 807 (description from T015L) |
| JO8 | 809 (description from T015L) |
| JO9 | 811 (description from T015L) |

**Note**: Jordan uses 3-digit numeric codes. Uses UTIL fallback — no dedicated BAdI in CTS. AE+JO both require PPC AND BCM exception batch (UNES_AP_EX).

#### Morocco (MA) — 10 codes [VERIFIED from T015L P01 live query]
| LZBKZ | Description (T015L.ZWCK1) |
|-------|---------------------------|
| MA0 | 250 Transport aérien de passagers |
| MA1 | 442 (description from T015L) |
| MA2 | 510 (description from T015L) |
| MA3 | 570 (description from T015L) |
| MA4 | 585 (description from T015L) |
| MA5 | 595 (description from T015L) |
| MA6 | 720 (description from T015L) |
| MA7 | 725 (description from T015L) |
| MA8 | 800 (description from T015L) |
| MA9 | 1280 (description from T015L) |

**Note**: Morocco uses numeric codes with French descriptions. Uses UTIL fallback — no dedicated BAdI in CTS.

#### Malaysia (MY) — 10 codes [VERIFIED from T015L P01 live query]
| LZBKZ | Description (T015L.ZWCK1) |
|-------|---------------------------|
| MY0 | 11210 Passenger by air |
| MY1 | 12140 (description from T015L) |
| MY2 | 14310 (description from T015L) |
| MY3 | 15200 (description from T015L) |
| MY4 | 16510 (description from T015L) |
| MY5 | 16520 (description from T015L) |
| MY6 | 16730 (description from T015L) |
| MY7 | 16760 (description from T015L) |
| MY8 | 16780 (description from T015L) |
| MY9 | 16793 (description from T015L) |

**Note**: Malaysia uses 5-digit numeric codes. Uses UTIL fallback — no dedicated BAdI confirmed in CTS. [INFERRED fallback applies]

#### Philippines (PH) — 5 codes [VERIFIED from T015L P01 live query]
| LZBKZ | Description (T015L.ZWCK1) |
|-------|---------------------------|
| PH0 | SUPP Supplier/Vendor payment |
| PH1 | SALA Payroll/Salaries |
| PH2 | BEXP Business Expenses |
| PH3 | TRVL Travel |
| PH4 | CHAR Charitable Contributions |

**Note**: Philippines uses ISO-like 4-char codes. Uses UTIL fallback — no dedicated BAdI confirmed in CTS. [INFERRED fallback applies]

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
| China code rejected | Sending wrong code format | Verify T015L has CN0-CN2 with slash-notation codes (/CSTRDR/ etc.), NOT numeric 001/002/003. Do NOT use ISO text codes for CN. |
| India code invalid | RBI codes change periodically (last verified 2024) | Verify against current RBI Annex-I list |
| MY/PH PPC wrong | Codes assumed identical to shared ISO set — not BAdI-confirmed | Read actual YCL_IDFI_CGI_DMEE class for MY/PH if it exists |

---


## Referencia detallada

Lo que sigue vive en **[reference.md](reference.md)** y se carga sólo si hace
falta — una skill cargada se queda en contexto todo el turno, así que aquí
queda lo que se lee ANTES de actuar y allí el detalle:

- **SAP Roles & Authorization Matrix [VERIFIED]**
- **DMEE XML Payment File Formats [VERIFIED — Critical for adding new countries]**
- **BCM Infrastructure [VERIFIED from Blueprint + Solution Docs]**
- **Field Office Cash & Manual Cheque Handling [VERIFIED from CR 126/127 BBP]**
- **EBS & SWIFT Infrastructure Architecture [VERIFIED from Solution Description EBS]**
- **Custom Payment Programs**
- **Data Sources**
- **Companion & Dashboards**
- **Source Documentation (BFM Handover PDFs)**
- **Integration Points**
- **Custom SAP Objects — YWFI Package (34 objects) [EXTRACTED]**
- **You Know It Worked When**
- **Dual-Control Audit (H13, routed Session #037 via skill_coordinator)**
