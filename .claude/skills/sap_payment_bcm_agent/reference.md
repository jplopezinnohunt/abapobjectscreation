# sap_payment_bcm_agent — referencia detallada

> Extraído de `SKILL.md` para que su cuerpo no ocupe contexto en cada turno.
> Lo carga quien lo necesite; el índice está en `SKILL.md`.

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

### BCM Signatory Management [VERIFIED 2026-04-09 — direct P01 extraction]

**Source of truth**: transaction `OOCU_RESP` (Organization → Responsibility).
**Storage**: SAP PD infotypes HRP1000 (object header) / HRP1001 (relationships). Responsibility groups are **OTYPE='RY'** objects; assignments to users are HRP1001 with **RELAT='007' SCLAS='P'** (RY → Person → PERNR).
**Extraction script**: `Zagentexecution/mcp-backend-server-python/extract_bcm_signatories.py` (runs on P01, joins PA0002 + PA0105 for name/user/email).
**Gold DB tables**: `bcm_signatory_responsibility`, `bcm_signatory_assignment`.
**Knowledge doc**: [`knowledge/domains/Treasury/bcm_signatory_rules.md`](../../../knowledge/domains/Treasury/bcm_signatory_rules.md).

#### The two rules
| Rule # | Rule class | Role | SHORT in HRP1000 |
|--------|------------|------|------------------|
| **90000004** | `BNK_COM_01_01_03` | **COMMIT** — final release ("2nd signature" that lets the file go to the bank) | `BNK_01_01_03` |
| **90000005** | `BNK_INI_01_01_04` | **INITIATE / VALIDATE** — 1st approval of the BCM batch | `BNK_01_01_04` |

Each rule is a PFAC rule (returns a list of agents to the workflow). The workflow is `90000003` — BNK_BATCH_HEADER approval. It calls 90000005 first to obtain validators, then 90000004 to obtain committers.

#### Rule 90000004 (COMMIT) — 7 responsibility groups, 62 distinct signatories over time
| Responsibility group (STEXT) | RY OBJID | Total rows | **Currently active (2026-04-09)** |
|------------------------------|----------|------------|-----------------------------------|
| UNES signatures for all transfers | 50010052 | 13 | **0** — all delimited 2023-01-20 |
| UIS signatures for all transfers | 50010054 | 20 | 8 |
| UIS signatures up to 10.000 | 50036326 | 15 | 0 — tier discontinued |
| IIEP signatures for all transfers | 50010088 | 16 | 6 |
| UBO signatures up to 10.000 | 50034894 | 11 | 8 |
| UBO signatures for transfers over 10.000 | 50036737 | 10 | 7 |
| UIL signatures for all transfers | 50037531 | 8 | 4 |

**CRITICAL finding**: UNES has **zero currently active committers under rule 90000004** — the entire group was delimited to 2023-01-20 when UNES migrated to **Process 4** (F110 + BCM 1 validation → Coupa 2nd validation → bank). For UNES, Coupa performs the commit step externally; SAP BCM only runs the INITIATE step via rule 90000005. UIS ≤10.000 tier is also fully delimited (2024-01-17).

#### Rule 90000005 (INITIATE / VALIDATE) — 15 responsibility groups, tiered by entity + amount
| Responsibility group | RY OBJID | Rows |
|----------------------|----------|------|
| UIS AP Validation up to 10.000 USD | 50010051 | 19 |
| UIS AP Validation up to 5.000.000 USD N/ | 50010053 | 12 |
| UIS Validation | 50036801 | 16 |
| UNES FAS/PAP/AP Validation to 500.000 | 50010075 | 12 |
| UNES FAS/PAP/AP Validation to 5.000.000 | 50010076 | 10 |
| UNES FAS/PAP/AP Validation to 50.000.000 | 50010077 | 5 |
| UNES FAS/PAP/AP Validation to 7.500.000 | 50038878 | 1 |
| UNES AP Validation up to 10.000.000 USD | 50036716 | 2 |
| UNES FAS/PAP/PAY Validation | 50032363 | 8 |
| UNES TRS Validation up to 50.000.000 | 50010078 | 15 |
| UNESCO bank to bank transfers | 50010079 | 13 |
| IIEP Validation | 50010087 | 16 |
| UBO Validation up to 10.000 USD | 50034892 | 11 |
| UBO Validation up up to 5.000.000 USD | 50034893 | 11 |
| UIL Validation | 50037530 | 9 |

Totals: **24 responsibility groups, 253 assignments (all periods), 76 unique signatories across both rules**.

#### Signatory change process
- **HQ (UNES) signatories**: CFO delegation of authority letter → DBS updates directly in P01 on BFM/TRS request. HR org structure is NOT maintained in D01.
- **Institute / UBO signatories**: bank signatory letters from the institute → DBS updates directly in P01.
- **Removal**: always **delimit validity** (`ENDDA`). Never delete the HRP1001 row — history must survive for audit.
- **Adding a new signatory**: DBS uses OOCU_RESP in P01, selects the right RY object, adds a P (Person) row with BEGDA = today and ENDDA = 99991231.

#### How to read the current active list from the Gold DB
```sql
SELECT stext, pernr, firstname || ' ' || lastname AS name, uname, email, begda, endda
FROM bcm_signatory_assignment
WHERE rule_number = '90000004'          -- or '90000005'
  AND endda >= strftime('%Y%m%d','now')
ORDER BY stext, lastname;
```

#### Never do this
- **Never assume HRP1000 `OTYPE='AC'`** — BCM responsibility groups are OTYPE='RY' (not the generic PFAC 'AC' object). Our SNC user cannot read 'AC' objects but CAN read 'RY' via RFC_READ_TABLE.
- **Never query HRP1001 with `IN (...)`** — SAP security rejects multi-value WHERE clauses on HR tables. Loop one OBJID per call.
- **Never chain more than ~3 `AND` clauses** in RFC_READ_TABLE WHERE against HR tables — the parser errors out with `DB_Error on HRP1001: "AN" is not valid`. Split the filter or apply the rest in Python.
- **Never use PA0001 for name resolution from this SNC user** — blocked by structural authorization. Use **PA0002** (VORNA/NACHN) + **PA0105 SUBTY=0001** (USRID → SAP user) + **PA0105 SUBTY=0010** (USRID_LONG → email) instead.
- **Never trust the screenshot begin date as the first-ever assignment** — OOCU_RESP consolidates overlapping periods. The HRP1001 rows are the authoritative per-period truth.
- **Never write to P01** — the AI agent is strictly read-only on P01. OOCU_RESP changes are executed by DBS. Agent scope = analysis + spec + post-change verification via RFC_READ_TABLE only. Even if the user asks "update it", the answer is "spec for DBS + verify after".

#### BCM Signatory Reconciliation Protocol [ADDED Session #052 — INC-000006313]

When the user brings a signatory change request (add/remove/update to a BCM panel), **follow this 7-step path in order**. It takes ~3 minutes and catches the 3 known classes of defect (ghost PERNR, panel drift, role split).

**Step 1 — Parse the request**
Identify: entity (UNES/UIS/IIEP/UBO/UIL), bank (optional — implies a carton), person name, action (add/remove). If the request came with a TRS instruction letter PDF, extract attachments and **read the `Carton des signatures` page** (last page, HEPATUS V10.x). That page has the authoritative PERNRs, not the cover letter which uses names only.

**Step 2 — Brain lookup**
Read `brain_state.incidents` for any prior incident involving the same person/entity. Read `brain_state.data_quality` for any open ghost-PERNR warnings for that entity. Read the relevant RY OBJIDs from [bcm_signatory_rules.md](../../../knowledge/domains/Treasury/bcm_signatory_rules.md).

**Step 3 — Identify target RY groups by name semantics**
The responsibility group STEXT carries the tier: `"for all transfers"` = no amount limit (the live group). `"up to X"` = amount-tier sibling — **check Gold DB to see if it still has active members** before acting; most tier-limited groups are retired with zero active members. When in doubt, the `"for all transfers"` group is the one TRS means.

**Step 4 — Gold DB pre-check (the person's current state)**
```sql
SELECT rule_number, stext, begda, endda
FROM bcm_signatory_assignment
WHERE pernr = '<PERNR>'
ORDER BY rule_number, begda;
```
Identify expired vs active rows. Never re-insert a currently active assignment.

**Step 5 — P01 person validation**
Read-only via RFC_READ_TABLE:
- `PA0002 PERNR=<P>` → confirm VORNA/NACHN match the request
- `PA0105 PERNR=<P>` → confirm SUBTY='0001' has a non-empty USRID (if empty, the PERNR is a **ghost** and you must find the correct one)
- `USR02 BNAME=<USRID>` → UFLAG=0 (not locked), GLTGV/GLTGB covers the requested period

**Step 6 — Run the reconciliation check**
```bash
python Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py \
    --entity UIS \
    --carton Zagentexecution/quality_checks/cartons/uis_citibank_canada_YYYYMMDD.txt
```
This script detects:
1. **Ghost PERNRs** (active SAP row with empty PA0105/0001 SAP user)
2. **Role-split inconsistency** (user on only one of INI/COM rules)
3. **Carton diff** (extras in SAP, missing from SAP) when a `--carton` file is provided
4. Exit code 1 if any defect, 0 if clean — suitable for CI

Save each carton file under `Zagentexecution/quality_checks/cartons/<entity>_<bank>_<yyyymmdd>.txt` with one PERNR per line (`#` for comments). One file per bank account carton, not per entity.

**Step 6b — Access-control check (MANDATORY, INC-000011781) — does every assigned signatory hold the BNK_APP role?**
```bash
python Zagentexecution/quality_checks/bcm_role_gap_check.py            # all entities & nodes
python Zagentexecution/quality_checks/bcm_role_gap_check.py --entity UBO
```
Being in a node (HRP1001) is **NOT** enough to sign — the user also needs a role granting transaction `BNK_APP` (e.g. `YS:FI:M:BCM_MON_APP______:<entity>`). This check reads live P01 (`AGR_1251` S_TCODE='BNK_APP' ∪ `AGR_TCODES` ∪ BCM derived roles; active holders from `AGR_USERS`), flags every assigned signatory whose user holds no such role, and rebuilds Gold DB `bcm_node_agent_role_check` (node × agent) + `bcm_signatory_role_gap` (per user). **Run it for every signatory request** and feed the result into the **Access** column of the Step-7 table:
- a ❌ on an **ADD** ⇒ the node change MUST be paired with a Security/PFCG ticket for the entity role (this was Renata's original "not authorized to use transaction BNK_APP" error);
- a ❌ on someone being **removed** reinforces the removal (they can't sign anyway).
Baseline 2026-06-19: 39 active signatories, 6 with no BNK_APP role (UBO: I_BA, VM_MARTIN · IIEP: B_PONT · UNES node 50010078: 3 of 6).

**Step 7 — Produce the spec for DBS (no execution)**

##### MANDATORY OUTPUT STRUCTURE (locked 2026-06-17, INC-000011781 — user directive)

Every BCM signatory-change incident MUST be presented as **ONE single table** covering **every ACTIVE member of every affected node PLUS every addition** — never just the deltas. Expired/red OOCU_RESP rows are **not** in the table (active panel only); an expired row that carries an action — a re-add, or a person still active on another node — goes in the net-operations **Old issues** block instead. This makes the live panel, the requested change, and pre-existing drift visible in one place and auditable. Columns, in this exact order:

`Rule | Node (OBJID) | Node name (STEXT) | PERNR | Person | Live status | Carton | Access (BNK_APP role) | Action`

- One row per (node × person), for **all four** (or all relevant) tier/phase nodes of the entity — list `keep` rows too, not only changes.
- **Access (BNK_APP role)** column (from Step 6b, live): ✅ has a BNK_APP-granting role / ❌ no role. A ❌ means the change MUST be paired with a Security/PFCG ticket — being in the node alone does not let the person sign. Every signatory change is therefore **two actions**: the node (OOCU_RESP/DBS) **and** the role (PFCG/Security).
- **Action legend (mandatory):** ✅ keep (on carton, correct) · ➕ ADD (current ask) · ➖ DELIMIT (current ask) · ⚠️ TRS = old issue, needs separate TRS sign-off (over-auth removal or on-carton-but-absent add).
- The Rule + Node OBJID + Node name are all mandatory on every row (lookalike-group trap — see below).
- Follow the table with a **net-operations summary** split into two blocks:
  1. **Current ask** (authorized by the TRS letter/REF) — the discrete ADD/DELIMIT ops: `Op | PERNR | Rule | Node`. BEGDA = TRS letter effective date, ENDDA = 99991231.
  2. **Old issues — hold for TRS sign-off** — drift not covered by this letter (over-authorized removals, on-carton-but-absent adds), listed but NOT executed without per-item TRS authorization.
- Membership data must come from a **live P01 read** (RFC_READ_TABLE on HRP1001, **all periods**) — not a stale Gold DB snapshot, not screenshots. Read all periods to (a) determine who is *currently active* and (b) catch a person who looks expired on one node but is **still active on another** (the Martin case). But the **table shows ACTIVE members only**; expired rows that need an action go in *Old issues*, not the main table.

This structure supersedes the old "5-column deltas-only spec". Hand to DBS; wait for execution confirmation.

#### Lookalike-group trap (INC-000006313 Part 2, Session #052)
In OOCU_RESP rule 90000005, several groups sit adjacent in the tree and end with the word `Validation`:
- `IIEP Validation` — RY **50010087** — entity IIEP Paris
- `UIS Validation` — RY **50036801** — entity UIS Montreal
- `UNES TRS Validation up to 50.000.000` — RY 50010078 — entity UNES HQ
- `UBO Validation up to 10.000 USD` — RY 50034892 — entity UBO Brazil

During INC-000006313 Part 2, DBS first added Svein OESTTVEIT to `IIEP Validation` by mistake because the agent's spec used the word "UIS Validation" without the RY OBJID. Had this gone undetected, Svein would have been able to approve **IIEP payments** (wrong entity, wrong carton, compliance breach). The reconciliation check caught it the same day via the role-split warning, and DBS corrected.

**Mitigation in every spec**:
1. Present RY OBJID prominently — not as a footnote. Bold it.
2. Name the specific adjacent trap explicitly: "do NOT pick `IIEP Validation` (RY 50010087)".
3. After DBS confirms execution, re-run `bcm_signatory_reconciliation_check.py` AND directly verify via RFC that:
   - the target RY has the expected new members
   - the adjacent-entity RYs (same rule, different entity prefix) are unchanged vs the previous snapshot

#### Validation-against-bank protocol
When the incident explicitly asks SAP to mirror a specific bank carton (as opposed to just adding one person):
1. Save the carton to `Zagentexecution/quality_checks/cartons/<entity>_<bank>_<yyyymmdd>.txt` (one PERNR per line, `#` comments). Use the letter date as the filename date, not the execution date.
2. Run the reconciliation check with `--carton <path>` and capture exit code.
3. Apply the full spec (delimits + adds, always BEGDA = letter date, ENDDA = 99991231) via DBS.
4. After DBS executes, **run the check TWICE**:
   - Once with the carton file → expect MATCH=full-carton-size, EXTRAS=0, MISSING=0, exit 0
   - Once without `--entity` (global) → ghost check + role-split scan across all entities, to confirm no adjacent-group collateral damage
5. Mirror the spec into `knowledge/incidents/<INC>.md` with the carton filename, pre-state table, post-state table, reconciliation exit codes. Use this artifact as evidence for the audit.

**Do not mark the incident as CLOSED until both reconciliation runs return exit 0.**

**After DBS executes**
- Re-run `extract_bcm_signatories.py` to refresh the Gold DB
- Re-run the reconciliation check — the specific items you requested should now be resolved, pre-existing defects will still show
- Verify the new HRP1001 rows match the spec (BEGDA might have drifted from letter date to execution date — flag any gap)
- Close the incident in the brain with before/after diff

#### Known data quality defects [status as of 2026-04-13]
- ~~**Ghost PERNR 10567156 (Svein OESTTVEIT) on UIS rules**~~ — **RESOLVED 2026-04-13**. DBS delimited ghost and inserted real PERNR 10067156 (user `S_OESTTVEIT`) on both RY 50010054 and RY 50036801. Verified via reconciliation check exit=0.
- ~~**Role-split inconsistency on UIS**~~ — **ANSWERED/CLOSED 2026-04-13**. Was maintenance drift, not intentional. All 8 Citibank Canada carton signatories now on both rules. Confirmed: the carton's "sign jointly two by two" has NO role semantics — any two signatories can sign together.
- **SAP↔carton drift on UIS — other banks (still open)**: Stephenson-Odle and Zhang were removed from SAP UIS rules on 2026-04-13 as part of the full cleanup. If UIS has other bank accounts at other banks where they are still signatories, that would need separate TRS cartons. Parked as `uq_uis_non_citibank_signatories`.

#### Verified UIS Citibank Canada panel (live, 2026-04-13)
Both rule 90000004 (RY 50010054) and rule 90000005 (RY 50036801) now hold exactly these 8 PERNRs, matching the 02/04/2026 carton:
```
10050037  O_LABE        Olivier LABE
10067156  S_OESTTVEIT   Svein OESTTVEIT
10069500  J_PESSOA      Jose PESSOA
10092400  S_VOFFAL      Said OULD AHMEDOU VOFFAL
10097358  A_YLI-HIETAN  Anssi YLI-HIETANEN
10105832  N_REUGE       Nicolas REUGE
10107946  AG_IMHOF      Adolfo Gustavo IMHOF
10150918  L_SANNEH      Lamin SANNEH
```
Canonical carton file: `Zagentexecution/quality_checks/cartons/uis_citibank_canada_20260402.txt`.

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
| AE/CN/ID/IN/JO/MA/MY/PH | Payment Purpose Code required | `Purp/Cd` or `InstrInf` | Read from `REGUP-LZBKZ` (T015L SCB indicator repurposed as PPC). Payroll detected via LAUF1 last-char 'P' → SALA. NOT from SGTXT. [VERIFIED architecture; XML value confirmation needs BAdI source read] |

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

> **FULL EBS REFERENCE**: See `knowledge/domains/FI/bank_statement_ebs_architecture.md` (Session #029)
> 22 sections covering: posting rules (T028G: 1,025 rules, 23 transaction types), search strings (6 patterns),
> account symbols (BANK/BANK_SUB/BANK_TECH/OFFSET_TECH_SUB), BA determination (YBASUBST→YTFI_BA_SUBST),
> user exit chain (CMOD YTFBE001), incoming payment classification (CONT/WHF/ICH/BC/MBF rules),
> and production reality: FEBEP=223K items, FEBKO=85K statements, 11xxxxx clearing rate=99.4%.
>
> **Key Session #029 corrections**: FEBEP≠0 (EBS fully active), 10xxxxx items are permanent ledger (not unreconciled),
> real gap = 2,737 items on 11xxxxx, Z7 clearing = 100% manual (0 automated).

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
| 20240321 Payment Purpose Code (presentation) | `Payment Purpose Code/` | PPC tables for 8 countries. **WARNING: country code values in this PDF do NOT match T015L P01 data.** PDF lists ISO 20022 text codes (BEXP/CORT/SALA...) for AE/BH. T015L reality: AE=9 UNESCO codes (AE0-AE8), BH=6 codes (BH0-BH5), CN=slash-notation (NOT 001/002/003). Use T015L query as authoritative source. |

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
7. **(Session #037)** Agent surfaces the H13 dual-control finding and reframes it as **automation debt, not fraud** — see "Dual-Control Audit" section below.

---

## Dual-Control Audit (H13, routed Session #037 via skill_coordinator)

**The single largest dual-control gap in UNESCO payments is not fraud — it is automation debt at HQ treasury.** This section captures the complete H13 finding for any future `sap_payment_bcm_agent` invocation.

### Detection query (Gold DB)

```sql
-- Same-user batches (CRUSR = CHUSR) 2024-2026
SELECT CRUSR,
       SUM(CASE WHEN CRUSR=CHUSR THEN 1 ELSE 0 END) AS same_user_batches,
       SUM(CASE WHEN CRUSR!=CHUSR THEN 1 ELSE 0 END) AS diff_user_batches,
       ROUND(100.0 * SUM(CASE WHEN CRUSR=CHUSR THEN 1 ELSE 0 END) / COUNT(*), 1) AS self_approval_pct,
       ROUND(SUM(CASE WHEN CRUSR=CHUSR THEN BATCH_SUM ELSE 0 END), 0) AS same_user_sum
FROM BNK_BATCH_HEADER
WHERE CRUSR != '' AND CRDATE >= '20240101'
GROUP BY CRUSR ORDER BY same_user_batches DESC;
```

### Reproducible findings (Session #037, 2026-04-05)

- **3,359 same-user batches** in scope 2024-2026, **~$655.9M** local-currency exposure
- **70.3% on Wednesday** — weekly manual AP cycle signature
- **Top 2 users (C_LOPEZ, I_MARQUAND) = 2,705 batches / 81% of volume / ~$475M**. Both HQ Paris treasury.
- **Self-approval rates:** C_LOPEZ 94.7% · I_MARQUAND 92.9% · E_AMARAL 49.2% · F_DERAKHSHAN 25.9%
- **F_DERAKHSHAN reclassified:** prior hypothesis doc (#036) flagged him as top risk — **wrong**. 74% of his PAYROLL batches DO have a second approver. The 161 solo are vacation backup exceptions.
- **None own background jobs** in `tbtco` → dialog humans, not service accounts.

### Status field guidance

- `STATUS` column = GUID reference to SAP state object — **opaque in Gold DB**, do not parse.
- `CUR_STS` column = **semantic short code** — always use this:
  - `IBC15` ~78% — primary active state
  - `IBC11` ~21%
  - `IBC17` — Failed (BCM outage Jul 2021 – Dec 2022, outside 2024-26 scope)
  - `IBC20`, `IBC09` — rare
- Rule: filters like `STATUS IN ('COMPLETED','SENT')` from prior docs were written against RFC live, **not Gold DB**. Do not copy-paste to Gold DB queries.

### Why it is automation debt, not fraud

C_LOPEZ and I_MARQUAND are the **only two HQ Paris treasury operators** running the weekly AP cycle manually every Wednesday. Each approves their own batches because there is no third operator to provide dual control. They cover each other during vacation. The fix is **staffing or automation**, not a workflow policy. Payroll dual-control works correctly (74% second-approved). Brazil (E_AMARAL) has healthy 50/50 coverage with a local colleague.

### User pattern signatures

- **HQ weekly AP operator**: >90% self-approval, UNES only, SOG01/CIT04/SOG03/CIT21, 83% Wednesday, 10-12 CET, UNES_AP_10/EX/IK
- **Field office batch** (E_AMARAL): ~50% self-approval, single co code (UBO), BRL, UBO_AP_MAX
- **Payroll backup** (F_DERAKHSHAN): ~26% self-approval, PAYROLL rule, solo = vacation backup only
- **Occasional** (S_COURONNAUD, A_ALMEIDA): <5% self-approval, normal

### Highest-risk subset

`UNES_AP_EX` (AE/JO/embargo exception list): **331 same-user batches / ~$1.9M**. Small $, high sanctions exposure. Ship carve-out first.

### Remediation paths (ranked by shippability)

1. **Detective nightly report** via `Zagentexecution/bcm_dual_control_monitor.py` — zero blockers, ships this week
2. **UNES_AP_EX carve-out** — BCM/FBZP config, low effort, needs director signoff
3. **HQ role split** — blocked on HR adding a 3rd operator (staffing lever)
4. **Workflow 90000003 mod** — enforce `CHUSR ≠ CRUSR`, blocked on YWFI source (H14, D01 password)
5. **Automate Wednesday AP cycle** — strategic, multi-month

### Historical drift (cost of 15-session inaction)

- #027 reported 3,394 same-user batches
- #037 measures 4,760 all-time / 3,359 in scope
- Delta: **+1,366 batches (+40%)** accumulated during 15 sessions of PMO inaction
- This drift is why the session open/close symmetry control was added in #037 (`.agents/workflows/session_start.md` v2 + `scripts/session_preflight.py` S1/S2/S3/SYM checks).

### Artifacts

| File | Purpose |
|---|---|
| `Zagentexecution/bcm_dual_control_monitor.py` | Daily-runnable monitor |
| `Zagentexecution/mcp-backend-server-python/bcm_dual_control_audit.csv` | 3,359-row detail |
| `Zagentexecution/mcp-backend-server-python/bcm_dual_control_audit.html` | Interactive companion |
| `Zagentexecution/mcp-backend-server-python/bcm_dual_control_audit.json` | API-friendly summary |
| `knowledge/domains/BCM/h13_executive_summary.md` | CFO one-pager |
| `knowledge/domains/BCM/h13_remediation_hypothesis.md` | Original hypothesis (partially superseded) |

### Invocation triggers for this section

- User asks about BCM dual-control, F110 approval, or workflow 90000003
- User mentions C_LOPEZ, I_MARQUAND, F_DERAKHSHAN, E_AMARAL
- User asks "who runs the weekly AP cycle"
- User asks about UNES_AP_EX / exception-list batches
- Someone asks for the H13 numbers

### If this section grows past ~300 lines

Per `skill_coordinator/SKILL.md` rule 3, split into a dedicated skill `sap_payment_bcm_forensics` inheriting content verbatim. Do not consolidate or compress.
