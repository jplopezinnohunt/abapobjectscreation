# INC-000006313 — Add Said OULD AHMEDOU VOFFAL to UIS BCM signatory panel + full UIS panel cleanup

**Status**: CLOSED_WITH_CLEANUP
**Type**: Operational change + pre-existing defect cleanup
**Date opened**: 2026-04-09
**Date closed**: 2026-04-09 (Part 1 Said add) / **2026-04-13 (Part 2 full panel alignment)**
**Requester**: Ingrid Wettie (TRS, Middle Office)
**Executed by**: DBS (in P01 directly via OOCU_RESP)
**Verified by**: AI agent (read-only via RFC_READ_TABLE on HRP1001)
**System**: P01
**Related domain**: Treasury / BCM Signatory Management
**Related rule**: [knowledge/domains/Treasury/bcm_signatory_rules.md](../domains/Treasury/bcm_signatory_rules.md)

---

## 1. Request

### Email chain
- **Role Management Mailer Service → Sawsan Nehme (UIS AO)** — 2026-04-08 16:44 — "IMPORTANT: Change in Bank Signatory panel of UIS". Notification that TRS validated a UIS signatory panel change and an instruction letter has been sent to the bank via courier. AO has **two weeks** (→ 2026-04-22) to confirm the bank registered the change.
- **Ingrid Wettie → Pablo (me)** — 2026-04-09 09:03 — "Can you please add Ould Ahmedou Voffal, Said for UIS in BCM?"

### Attached PDF (the authoritative TRS letter)
File: `20260408 UIS.pdf` (5 pages)
- **Page 1** — Cover letter to Citi Europe PLC (Warsaw onboarding contact Nirmal Murugan), dated 7 April 2026, introducing Said's email `s.voffal@unesco.org`.
- **Page 2** — TRS letter to **Citibank, N.A. Canada Branch** (Toronto), REF `FIN.8/MOD/10.0000003625`, dated **02/04/2026** ("as of immediate effect"), signed by **Anssi Yli-Hietanen, Treasurer**. Accounts affected: **UIS USD 2017588014** and **CAD 2017588006**. Modification: **add Mr Said OULD AHMEDOU VOFFAL**. Final panel = **8 signatories authorized to sign jointly two by two**, unlimited amount between UIS bank accounts. Clause: *"This list replaces all previous signatory lists."*
- **Page 3** — Financial Regulations clause: only the Treasurer (Anssi Yli-Hietanen) can open/transfer/close bank accounts, designate staff, and agree electronic banking conditions.
- **Page 4** — *Carton des signatures* (HEPATUS signature specimen card) with the 8 PERNRs and specimen signatures. **This is the authoritative list of PERNRs.**
- **Page 5** — Copy of Said's UN Laissez-Passer (Index No UNESCO10092400, DOB 01-JAN-1964, issued 14-NOV-2023, expires 14-NOV-2028).

### The 8 authorized UIS signatories (Citibank Canada, 02/04/2026)
| # | PERNR | Name | Duty Station |
|---|-------|------|--------------|
| 1 | 10107946 | IMHOF Adolfo Gustavo | Montreal |
| 2 | 10050037 | LABE Olivier | Montreal |
| 3 | **10067156** | OESTTVEIT Svein | Montreal |
| 4 | 10092400 | OULD AHMEDOU VOFFAL Said | Montreal |
| 5 | 10069500 | PESSOA Jose | Montreal |
| 6 | 10105832 | REUGE Nicolas | Montreal |
| 7 | 10150918 | SANNEH Lamin | Montreal |
| 8 | 10097358 | YLI-HIETANEN Anssi | Headquarters |

---

## 2. Pre-change verification (read-only, 2026-04-09)

### Said's identity, active state
- `PA0002` PERNR=10092400: VORNA=Said, NACHN=OULD AHMEDOU VOFFAL, latest record 2026-03-22 → 9999-12-31 (returning employee)
- `PA0105/0001`: USRID = `S_VOFFAL`
- `PA0105/0010`: USRID_LONG = `S.VOFFAL@UNESCO.ORG`
- `USR02` BNAME=`S_VOFFAL`: UFLAG=0 (unlocked), GLTGV=2026-04-02, GLTGB=2028-03-19, USTYP=A (Dialog)
- Passport: UNESCO10092400 matches PERNR ✓
- **All prior BCM assignments expired** (between 2021-10-18 and 2024-01-17)

### Which groups to add him to
Derived from the phrase **"for all transfers"** in the responsibility group name (= no amount tier = the only live UIS panel). The retired tier-limited sibling groups (`UIS signatures up to 10.000`, `UIS AP Validation up to 10.000 USD`, `UIS AP Validation up to 5.000.000 USD N/`) all have **zero currently active members** and are not maintained anymore.

| Rule | RY OBJID | Group (STEXT) | Why |
|------|----------|---------------|-----|
| 90000005 (INI) | 50036801 | UIS Validation | Only live UIS initiate group |
| 90000004 (COM) | 50010054 | UIS signatures for all transfers | Only live UIS commit group ("for all transfers" = unlimited amount) |

---

## 3. Change spec handed to DBS

```
PLVAR=01  OTYPE=RY  RELAT=007  ISTAT=1  SCLAS=P  SOBID=10092400
BEGDA=20260409  ENDDA=99991231

Row 1: OBJID=50036801  (UIS Validation — rule 90000005 INI)
Row 2: OBJID=50010054  (UIS signatures for all transfers — rule 90000004 COM)
```

**No delimits requested.** Scope was strictly additive per Ingrid's email.

---

## 4. Execution

DBS executed the change in P01 via OOCU_RESP on 2026-04-09. Confirmation arrived verbally ("i added").

---

## 5. Post-change verification (read-only)

### Direct HRP1001 read
```
RY 50010054 (UIS signatures for all transfers):
  SOBID=10092400  ISTAT=1  BEGDA=20260409  ENDDA=99991231  ✅
RY 50036801 (UIS Validation):
  SOBID=10092400  ISTAT=1  BEGDA=20260409  ENDDA=99991231  ✅
```

Historical expired rows (BEGDA=20160303/20211018, ENDDA=20231004) are preserved as audit history. Nothing was overwritten.

### Gold DB refresh
`extract_bcm_signatories.py` re-run after the change:
- `bcm_signatory_assignment` row count: 253 → **255** (+2 for Said)
- Two new rows confirmed with `SELECT * FROM bcm_signatory_assignment WHERE pernr='10092400' AND endda >= '20260409'`.

### Deviation from the letter
The TRS letter says *"as of immediate effect"* (dated 2026-04-02). DBS used **BEGDA = 2026-04-09** (execution date) instead of 2026-04-02 (letter date). This creates a **7-day audit gap** where Said was on the Citibank Canada panel but not in the SAP workflow routing. Low material risk because no UIS batches required his signature in that window, but flagged for future process improvement.

---

## 6. Side findings (NOT part of this incident — logged separately)

While verifying the post-change state against the PDF carton, three pre-existing discrepancies were discovered between SAP BCM and the Citibank Canada carton. **None were acted on** (user instruction: "the email is to add 1 and not delimited any"). All are logged for future follow-up:

### 6.1 Ghost PERNR — **unambiguous defect**
- HRP1001 row for both UIS groups contains `SOBID=10567156` for Svein OESTTVEIT.
- The carton des signatures says **PERNR 10067156**.
- `PA0002` confirms both PERNRs exist with name "Svein OESTTVEIT", but:
  - **10067156** (real) — continuous PA0002 history 1955 → 9999, `PA0105/0001 = S_OESTTVEIT`, `PA0105/0010 = S.OESTTVEIT@UNESCO.ORG`.
  - **10567156** (ghost) — single flat PA0002 row, no `PA0105/0001`, no work email (only private `svein.osttveit@orange.fr`).
- **Production impact**: when workflow 90000003 resolves either rule, it returns PERNR 10567156 → empty SAP user → **Svein cannot be routed a work item in BNK_APP**. He appears on the Citibank panel but is silently unable to sign in SAP.
- **Added**: 2025-10-04 — pre-dates this incident by 6 months.
- **Logged as**: `brain_v2/agi/data_quality_issues.json` open item `dq_ghost_pernr_bcm_oesttveit`.

### 6.2 Extras in SAP not on Citibank Canada carton
- **10136066 STEPHENSON-ODLE Ophelia** — active in RY 50010054 (Commit) since 2019-05-03, `ENDDA=99991231`.
- **10098989 ZHANG Yanhong** — active in RY 50010054 (Commit) and RY 50036801 (Validation) since 2024-08-07, `ENDDA=99991231`.
- **May or may not be a defect**: SAP responsibility groups are **entity-level**, not bank-account-level. One group covers ALL UIS bank accounts. If UIS has other accounts at other banks where Stephenson/Zhang are still signatories, they are legitimate. Needs TRS to provide all UIS bank account cartons for full reconciliation.
- **Logged as**: `brain_v2/agi/known_unknowns.json` entry `uq_uis_non_citibank_signatories` (parked question for TRS).

### 6.3 Missing from SAP but on Citibank Canada carton
- **10150918 SANNEH Lamin** — on Citibank panel, active in Validation only, **missing from Commit**.
- **10097358 YLI-HIETANEN Anssi** — on Citibank panel, active in Commit only, **missing from Validation**.
- The carton says "sign jointly two by two" without role distinction. SAP's split between INI/COM is not maintained consistently.
- **Logged as**: `brain_v2/agi/known_unknowns.json` entry `uq_uis_bcm_role_split_consistency`.

### 6.4 Communication to business
Business (TRS) was informed by the user about the inconsistencies between the bank and the system state. A separate cleanup request is expected from TRS. The agent must not act on items 6.1–6.3 without a specific, per-item TRS authorization.

---

## 7. Learnings (feed into Phase 4b of session retro)

1. **SAP BCM signatory rules are stored under OTYPE='RY', not 'AC'.** HRP1000.SHORT holds the rule class (`BNK_01_01_03` / `BNK_01_01_04`), HRP1000.STEXT holds the group description. HRP1001 with RELAT='007' SCLAS='P' links the group to a Person (PERNR).
2. **PA0001 is fully blocked** for the SNC user. Use PA0002 (VORNA/NACHN) + PA0105 SUBTY='0001' (USRID = SAP user) + PA0105 SUBTY='0010' (USRID_LONG = email).
3. **RFC_READ_TABLE rejects complex WHERE clauses**: `IN (...)` fails with `OPTION_NOT_VALID / SAIS 000 / suspicious WHERE condition`. Also, more than ~3 `AND` clauses fails with `DB_Error on <table>: The parser produced the error: "AN" is not valid h`. Loop one condition per call.
4. **"for all transfers" naming convention** = no amount tier. Retired tier-limited sibling groups have zero active members. If a TRS letter says "add to UIS in BCM" without specifying a tier, the target is the `for all transfers` group(s).
5. **SAP BCM responsibility groups are entity-level, not bank-account-level.** One group ("UIS signatures for all transfers") covers all UIS accounts at all banks. A bank-specific *carton des signatures* is NOT a 1:1 source of truth for that SAP group — it is the authoritative list for ONE bank only.
6. **Ghost PERNR is a class of defect**: a BCM row points to a PERNR that exists in PA0002 but has no `PA0105/0001` SAP user. Silent production breakage. Must be detected by a recurring data-quality check.
7. **Authoritative source for signatory changes**: the HEPATUS-generated *carton des signatures* (page 4 of the TRS letter) holds the correct PERNRs. The bank-side cover letter (page 2) uses names only. Always cross-check the PERNR from the carton against HRP1001.SOBID.
8. **Workflow chain**: F110 → FBPM1 (BCM batch) → Workflow 90000003 → Rule 90000005 resolves validators → BNK_APP validation → Rule 90000004 resolves committers → BNK_APP commit → DMEE file → SWIFT/Coupa → bank.
9. **Change execution boundary**: P01 is read-only for the AI agent. Signatory changes are executed by DBS directly in P01 via OOCU_RESP. AI agent scope = analysis + spec + post-change verification via RFC_READ_TABLE only.

---

## 8. Closure checklist

- [x] Requested change executed in P01
- [x] Read-only verification against HRP1001 — both rows present
- [x] Gold DB refreshed — `bcm_signatory_assignment` reflects post-change state
- [x] Side findings logged (ghost PERNR, extras, missing)
- [x] Business informed by user about side findings
- [x] Knowledge doc updated (`bcm_signatory_rules.md`)
- [x] Skill updated (`sap_payment_bcm_agent/SKILL.md`)
- [x] Reconciliation script created (`Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py`)
- [x] Brain layers updated (rules, claims, data_quality, known_unknowns, incidents)
- [x] Reply to Ingrid Wettie drafted (pending user send) — confirming SAP update + reminder that bank confirmation deadline is 2026-04-22

---

# PART 2 — Full UIS panel alignment (2026-04-13)

## 9. Part 2 trigger

Business (via Pablo) confirmed that SAP BCM UIS should be a strict mirror of the Citibank Canada carton of 02/04/2026. The 3 pre-existing defects identified during Part 1 side-findings (ghost PERNR, entity drift, role split) were authorized for cleanup.

## 10. Pre-state (before Part 2) vs target (the 8-PERNR carton)

Current SAP active rows were 9 on Commit and 8 on Validation, with 3 defects.

## 11. Change spec delivered to DBS (9 operations)

| # | Rule | RY OBJID | STEXT | Action | PERNR | BEGDA | ENDDA |
|---|------|----------|-------|--------|-------|-------|-------|
| 1 | 90000004 | 50010054 | UIS signatures for all transfers | DELIMIT | 10567156 (ghost Svein) | — | 20260412 |
| 2 | 90000004 | 50010054 | UIS signatures for all transfers | ADD | 10067156 (real Svein, S_OESTTVEIT) | 20260413 | 99991231 |
| 3 | 90000004 | 50010054 | UIS signatures for all transfers | DELIMIT | 10136066 STEPHENSON-ODLE | — | 20260412 |
| 4 | 90000004 | 50010054 | UIS signatures for all transfers | DELIMIT | 10098989 ZHANG | — | 20260412 |
| 5 | 90000004 | 50010054 | UIS signatures for all transfers | ADD | 10150918 SANNEH | 20260413 | 99991231 |
| 6 | 90000005 | 50036801 | UIS Validation | DELIMIT | 10567156 (ghost Svein) | — | 20260412 |
| 7 | 90000005 | 50036801 | UIS Validation | DELIMIT | 10098989 ZHANG | — | 20260412 |
| 8 | 90000005 | 50036801 | UIS Validation | ADD | 10067156 (real Svein) | 20260413 | 99991231 |
| 9 | 90000005 | 50036801 | UIS Validation | ADD | 10097358 YLI-HIETANEN | 20260413 | 99991231 |

## 12. Execution — and the IIEP near-miss (important learning)

DBS started executing the spec. On the first Rule 90000005 add for Svein, the operator opened **`IIEP Validation` (RY 50010087)** by mistake instead of **`UIS Validation` (RY 50036801)** — both groups sit adjacent in the OOCU_RESP tree under rule 90000005 and both end in the word "Validation". Svein's 10067156 row was added to IIEP Validation with BEGDA=20260413.

The reconciliation check caught it immediately:
- Role-split warning flagged Svein as "on Commit but not on UIS Validation"
- Direct RFC read on RY 50010087 exposed his 10067156 row there
- Had this gone undetected, Svein could have approved IIEP payments (wrong entity, no authorization letter, compliance breach)

DBS reversed the IIEP add (delimited the wrong row) and re-added Svein on UIS Validation correctly.

**Lesson promoted to feedback rule `feedback_bcm_spec_must_include_rule_ry_stext` (HIGH severity)**:
Every change spec row must always carry all three identifiers: Rule number, RY OBJID, STEXT. The RY OBJID is the only unambiguous identifier — adjacent groups can share both the rule number and similar STEXT wording.

## 13. Final state — verified 2026-04-13

Both rules now hold **exactly the 8 carton PERNRs**:

| PERNR | Name | SAP User | On Commit? | On Validation? |
|-------|------|----------|-----------|-----------------|
| 10050037 | Olivier LABE | O_LABE | ✅ | ✅ |
| 10067156 | Svein OESTTVEIT | S_OESTTVEIT | ✅ (new, 13.04.2026) | ✅ (new, 13.04.2026) |
| 10069500 | Jose PESSOA | J_PESSOA | ✅ | ✅ |
| 10092400 | Said OULD AHMEDOU VOFFAL | S_VOFFAL | ✅ | ✅ |
| 10097358 | Anssi YLI-HIETANEN | A_YLI-HIETAN | ✅ | ✅ (new, 13.04.2026) |
| 10105832 | Nicolas REUGE | N_REUGE | ✅ | ✅ |
| 10107946 | Adolfo Gustavo IMHOF | AG_IMHOF | ✅ | ✅ |
| 10150918 | Lamin SANNEH | L_SANNEH | ✅ (new, 13.04.2026) | ✅ |

Reconciliation check output (exit code 0):
```
GHOST PERNR CHECK     : 0 ghosts
ROLE-SPLIT CHECK (UIS): 0 inconsistencies
CARTON DIFF           : MATCH=8, EXTRAS=0, MISSING=0
```

## 14. Brain updates (Session #052 closure)

- `dq_ghost_pernr_bcm_oesttveit` → **RESOLVED** (DBS delimited 10567156 + inserted 10067156)
- `uq_uis_bcm_role_split_consistency` → **ANSWERED** (was maintenance drift, not intentional — carton's "sign jointly two by two" has no role semantics)
- `uq_uis_non_citibank_signatories` → still open (TRS must confirm if UIS has other bank accounts where STEPHENSON/ZHANG were still signatories — the cleanup removed them on the assumption the Citibank Canada carton is the only UIS panel)
- New feedback rule `feedback_bcm_spec_must_include_rule_ry_stext` (HIGH, Session #052) — prevents lookalike-group mis-add
- Skill `sap_payment_bcm_agent` updated with: Lookalike-group trap, Validation-against-bank protocol, Verified UIS Citibank Canada panel snapshot

## 15. Brief summary of the full incident life cycle

**What happened:** Treasury needed Said OULD AHMEDOU VOFFAL added to the UIS BCM signatory panel as part of a Citibank Canada signatory change. During analysis, we discovered the SAP UIS panel had drifted from the bank's carton over time: one ghost PERNR (silent defect since 2025-10-04), two signatories in SAP no longer on the carton, two on the carton missing one of the two SAP rules.

**What we fixed:** 9 operations across 2 rules, delivered as a spec, executed by DBS. One mis-targeted add (IIEP instead of UIS) was caught by the reconciliation check and corrected the same day.

**Result:** SAP BCM UIS panel is now a perfect mirror of the 02/04/2026 Citibank Canada carton. Both rules have exactly 8 authorized signatories, same on Commit and on Validation. Ghost PERNR defect resolved, role-split drift resolved. Reconciliation check exit 0.

**What remains outside scope:** Confirming whether UIS has other bank accounts at other banks where the delimited people (Stephenson, Zhang) were still authorized — parked for TRS.
