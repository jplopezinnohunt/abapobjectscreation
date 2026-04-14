# Session #052 Retro — BCM Signatory Intelligence + INC-000006313 (Part 1 + Part 2)

**Date**: 2026-04-09 (Part 1) + 2026-04-13 (Part 2)
**Duration**: 2 working segments
**Operator**: Pablo Lopez
**Primary driver**: User question *"do we have signature modification process in the payment domain?"* escalated into a full BCM signatory intelligence build after OOCU_RESP screenshots were provided, then into an end-to-end operational change (INC-000006313) when TRS forwarded the signatory change letter. Part 2 (2026-04-13) cleaned up the 3 pre-existing defects discovered during Part 1 after business confirmation.

> **Note on session number**: Session #051 was closed in parallel by another stream. This retro documents the BCM signatory work stream and is numbered #052.

---

## 1. What the session delivered

### Code artifacts
| File | Kind | Purpose |
|------|------|---------|
| `Zagentexecution/mcp-backend-server-python/extract_bcm_signatories.py` | Extractor | Pulls all BCM signatory responsibility groups + user assignments from P01 HRP1000/HRP1001/PA0002/PA0105 into Gold DB tables `bcm_signatory_responsibility` and `bcm_signatory_assignment`. Reusable. |
| `Zagentexecution/quality_checks/bcm_signatory_reconciliation_check.py` | Recurring DQ check | Detects ghost PERNRs, role-split inconsistency, and (with `--carton`) drift between SAP and a bank's carton des signatures. Exit code 1 on any defect. |
| `Zagentexecution/quality_checks/cartons/uis_citibank_canada_20260402.txt` | Canonical carton | 8 PERNRs authorized on UIS Citibank Canada panel per TRS letter FIN.8/MOD/10.0000003625. |
| `Zagentexecution/update_brain_inc6313.py` | One-shot brain updater | Idempotent script that appended 3 rules, 2 claims, 1 DQ, 2 known unknowns, 1 incident to the brain. |

### Knowledge artifacts
| File | Kind | Content |
|------|------|---------|
| `knowledge/incidents/INC-000006313_uis_bcm_add_voffal.md` | Canonical incident | Full end-to-end narrative: request, pre-verify, spec, execution, post-verify, side findings, 9 learnings, closure checklist. |
| `knowledge/domains/Treasury/bcm_signatory_rules.md` | Domain doc | Already existed from earlier in the session; extended with "Reconciliation protocol", "Known defects (open)", and "Change history" sections. |
| `knowledge/session_retros/session_052_retro.md` | Retro | This file. |

### Skill updates
- `.agents/skills/sap_payment_bcm_agent/SKILL.md` — replaced the stub "BCM Signatory Management" section with:
  - Verified RY/HRP1001 schema
  - 7-group breakdown of rule 90000004 with current-active counts
  - 15-group breakdown of rule 90000005
  - Signatory change process
  - Gold DB query recipes
  - "Never do this" list
  - **Full 7-step BCM Signatory Reconciliation Protocol** (added Session #052)
  - "Known data quality defects" section

### Brain updates (Session #052 delta)
| Layer | Added | Notes |
|-------|-------|-------|
| `feedback_rules.json` | +3 → **72** | `feedback_p01_readonly_absolute` (CRITICAL), `feedback_bcm_signatory_ry_otype` (HIGH), `feedback_bcm_ghost_pernr_check` (HIGH) |
| `claims.json` | +2 → **43** | `claim_bcm_ry_otype` (VERIFIED), `claim_ghost_pernr_oesttveit` (VERIFIED) |
| `data_quality_issues.json` | +1 → **21** | `dq_ghost_pernr_bcm_oesttveit` (HIGH, OPEN, promoted to recurring check) |
| `known_unknowns.json` | +2 → **34** | `uq_uis_non_citibank_signatories`, `uq_uis_bcm_role_split_consistency` |
| `incidents.json` | +1 → **3** | `INC-000006313` CLOSED, type=operational_change, full code_validation_chain |

> **Note**: all brain entries were written with `created_session=51` initially and must be patched to `52`. See action item in §7.

### Gold DB delta
- `bcm_signatory_assignment`: 253 → **255** rows (+2 for Said)
- `bcm_signatory_responsibility`: 24 rows (unchanged)

---

## 2. Timeline

| Time | Event |
|------|-------|
| T0 | User asks *"do we have signature modification process in the payment domain?"* |
| T1 | Brain/grep search reveals BCM workflow 90000004 + 90000005 exist in payment_full_landscape.md but without extracted data |
| T2 | User pastes 4 OOCU_RESP screenshots for rule 90000004 with ~93 assignments visible |
| T3 | I attempt HRP1000 OTYPE='AC' — zero rows (authorization wall) |
| T4 | Discover OTYPE='RY' works via `HRP1000 SHORT LIKE 'BNK%'` |
| T5 | Build `extract_bcm_signatories.py`, hit `IN ()` rejection, hit PA0001 authorization block, pivot to PA0002 + PA0105 |
| T6 | Extraction completes: 24 RY groups, 253 assignments, 76 unique signatories. 100% match with user's screenshots |
| T7 | User asks for the signature modification process — I document the flow: F110 → FBPM1 → workflow 90000003 → rule 90000005 (validators) → rule 90000004 (committers) → DMEE → bank |
| T8 | User forwards `INC-000006313` email (Ingrid Wettie) + PDF (TRS letter to Citibank Canada) |
| T9 | I parse the PDF carton des signatures (HEPATUS V10.x): 8 PERNRs, Said is #4, BEGDA 02/04/2026 |
| T10 | I propose 11 changes (add Said + delimit drift + fix ghost PERNR) |
| T11 | **User corrects me**: *"the email is to add 1 and not delimited any. but the signatures for UIS are not aligned with the reality?"* |
| T12 | I narrow scope to 2 adds, confirm drift is a separate finding |
| T13 | **User corrects me again**: *"you cannot do any insert!!!"* — clarifies P01 read-only boundary |
| T14 | I produce the 2-row spec for DBS |
| T15 | User (or DBS on user's behalf) executes the 2 adds in P01 OOCU_RESP: *"i added"* |
| T16 | I re-extract P01 via RFC_READ_TABLE — both new HRP1001 rows present, BEGDA=20260409 (DBS used execution date, not letter date) |
| T17 | User asks *"show me the issues against the PDF"* |
| T18 | Full side-by-side reveals: 1 ghost PERNR (10567156 vs 10067156), 2 extras (STEPHENSON, ZHANG), 2 missing (SANNEH on commit, YLI-HIETANEN on validation) |
| T19 | User informs TRS about the inconsistencies |
| T20 | User triggers session close protocol with *"acknowledge how the signature process works... add to Payment Domain and update rebuild"* |
| T21 | This retro + brain update |

---

## 3. What went well

1. **Brain-first traversal worked** — following the `feedback_brain_first_then_grep` rule, I started with `brain_state.json` and the grep found the `payment_full_landscape.md` pre-existing documentation of rules 90000004/90000005. That saved ~10 minutes of blind exploration.
2. **Iterative discovery of the RY schema** — when OTYPE='AC' returned 0 rows I didn't give up; I broadened to `SHORT LIKE 'BNK%'` and the RY schema revealed itself. Extraction then matched the user's screenshots 100%.
3. **PDF parsing caught the ghost PERNR** — reading the `carton des signatures` page and comparing PERNR-by-PERNR against HRP1001 revealed the 10567156 vs 10067156 discrepancy that had been silently present in production since 2025-10-04. This was the biggest latent defect this session uncovered.
4. **Tight scope control after user pushback** — when the user said "add 1, don't delimit" and "you cannot do any insert", I reverted cleanly from my 11-change proposal to the 2-row spec and stopped trying to propose writes. Later, when the user triggered session close, I captured the dropped scope as separate parked items (`known_unknowns` + `data_quality_issues`) instead of losing them.
5. **The reconciliation check script is reusable** — it runs in seconds against the Gold DB, can be pointed at any entity, and supports carton diffs. It promoted the ghost-PERNR class of defect into a recurring automated detector.

---

## 4. What went wrong

1. **Overreach before user instruction** — my first "spec for DBS" proposed **11 changes** (add Said + fix ghost + fix drift) when the user had only asked for 1 change. The user had to correct me twice: first to narrow scope, then to forbid P01 writes entirely. I should have defaulted to the minimum-ask interpretation and asked before expanding.
2. **Almost attempted a P01 write** — before the user's explicit "you cannot do any insert" correction, I had mentally queued a Python `apply_bcm_signatory_change.py --execute` script. The P01 read-only rule existed implicitly from prior sessions but wasn't in `feedback_rules.json` yet. Now it is (CRITICAL severity).
3. **Missed the "when" in the email on first read** — the user had to prompt me *"and the email said something about when"* before I re-read and saw the 2-week deadline (2026-04-22) and the "as of immediate effect" effective date (2026-04-02). My first pass only extracted the sender/recipient/basic body.
4. **DBS used execution date instead of letter date for BEGDA** — the HRP1001 rows were inserted with BEGDA=20260409 (execution day) instead of 20260402 (TRS letter "as of immediate effect"). This creates a 7-day audit gap where Said was authorized at the bank but not in SAP workflow routing. Low material risk but I didn't flag this as a pre-execution instruction to DBS; next time the spec must include "use letter date as BEGDA".
5. **PA0001 blocked detected late** — I started with PA0001 as name source and had to pivot to PA0002/PA0105 after every query returned `TABLE_WITHOUT_DATA`. The extraction script now documents this trap.
6. **Session number drift** — I wrote this retro as #051 initially, not knowing another stream had closed 051 in parallel. User caught it and I renamed to #052. Brain entries written with `created_session=51` need a patch to `52` (see §7).

---

## 5. Phase 4b — What did we learn about SAP itself?

**This section is MANDATORY per session close protocol.** Answering: "what did we learn about SAP that the next agent needs to know, separate from our extraction tooling?"

### 5.1 BCM workflow responsibility storage
- **BCM rules 90000004 / 90000005 are NOT stored as standard PFAC AC objects** visible to a low-privilege SNC user. They live as PD objects of **OTYPE='RY'** with `SHORT` = rule class (`BNK_01_01_03`, `BNK_01_01_04`) and `STEXT` = responsibility group name. Our user has zero read on OTYPE='AC' but full read on OTYPE='RY'. This is a structural-authorization nuance that is not documented anywhere in SAP Help or the BCM cookbook.
- **User assignments inside an RY group are HRP1001 rows** with `RELAT='007' SCLAS='P' SOBID=<8-char PERNR>`. The PERNR is resolved to name via PA0002 (VORNA/NACHN), to SAP logon user via PA0105 SUBTY='0001' (USRID), and to email via PA0105 SUBTY='0010' (USRID_LONG). **PA0001 is fully blocked** for our SNC user and returns `TABLE_WITHOUT_DATA` for every PERNR.
- **PA0105 USRID vs USRID_LONG is subtype-dependent**: SUBTY='0001' populates the legacy 12-char `USRID` field; SUBTY='0010' populates `USRID_LONG`. They are mutually exclusive per row.

### 5.2 RFC_READ_TABLE quirks on HR tables
- **`IN (...)` clauses are rejected** with `OPTION_NOT_VALID / SAIS 000 / suspicious WHERE condition`. Loop one equality per call.
- **More than ~3 `AND` clauses crash the parser** with `DB_Error on HRP1001: The parser produced the error: "AN" is not valid h`. Keep the WHERE simple and filter the rest in Python.
- **HRP1000 `OTYPE='P'` is also blocked** — cannot read the person PD object header directly. Go via PA0002/PA0105 via PERNR.

### 5.3 The BCM signature workflow end-to-end
```
F110 payment run
 └─ FBPM1 creates BCM batches in BNK_BATCH_HEADER (status=New)
     └─ Workflow 90000003 starts
         ├─ Resolves rule 90000005 (BNK_INI) for entity + amount tier
         │    → returns P objects from matching RY group
         │    → 1 or 2 validators approve in BNK_APP
         │    → System Signature = SAP user + password (F_STAT_USR 4-eye)
         └─ Resolves rule 90000004 (BNK_COM) for entity
              → returns P objects from matching COM group
              → committer clicks "Commit" in BNK_APP
              → batch status=Approved
                  └─ DMEE file generated
                      └─ SWIFT or Coupa → Bank
```
**UNES exception**: rule 90000004 has zero active committers for UNES — all delimited 2023-01-20. UNES uses Process 4 (1 BCM validation → Coupa as 2nd signature → bank). SAP BCM runs only the INI step for UNES.

### 5.4 Responsibility group naming semantics
- **`"X signatures for all transfers"`** (rule 90000004) = no amount tier = the one live commit group for entity X.
- **`"X Validation"`** or **`"X FAS/PAP/AP Validation to N"`** (rule 90000005) = initiate/validation, tiered by amount.
- **`"X signatures up to N"`** (rule 90000004) and **`"X AP Validation up to N"`** (rule 90000005) = historical amount-tier sibling groups, mostly **retired** (zero active members). Never add to one without first checking active count in Gold DB.

### 5.5 Entity-level vs bank-account-level reconciliation
- **SAP BCM responsibility groups are entity-level**: one "UIS signatures for all transfers" covers all UIS bank accounts at all banks.
- **A bank's carton des signatures is bank-account-level**: one carton per (entity, bank, account).
- **Therefore**: you cannot strictly reconcile a SAP group against a single carton unless the entity has only one bank account, OR you combine cartons from all the entity's bank accounts. This is a structural mismatch between SAP's data model and the bank's. For UIS we currently only have the Citibank Canada carton, so STEPHENSON/ZHANG drift cannot be classified as a defect until we get cartons for any other UIS accounts.

### 5.6 Ghost PERNR — a class of defect
- A BCM HRP1001 row can reference a PERNR that exists in PA0002 (so OOCU_RESP shows a name and the row looks healthy) but has **no PA0105 SUBTY='0001' SAP user**. Workflow 90000003 silently cannot route a BNK_APP work item → the signatory is disabled in SAP even though they appear on the bank's panel.
- Promoted to recurring check: `bcm_signatory_reconciliation_check.py` check #1.
- First known instance: PERNR 10567156 (Svein OESTTVEIT), added 2025-10-04 — 6 months of silent production breakage before discovery.

### 5.7 Where signatory change authority lives
- Only the **Treasurer** (currently Anssi Yli-Hietanen) can open/transfer/close bank accounts, designate signatories, and agree e-banking conditions. Per UNESCO Financial Regulations, Director-General-delegated.
- **CFO delegation of authority** drives HQ (UNES) signatory changes via BFM/TRS request.
- **Bank signatory letters from the entity** drive Institute/UBO/UIS/IIEP/UIL changes.
- **DBS executes all changes directly in P01** via OOCU_RESP. D01 cannot be used because HR org structure is not maintained in dev.
- **HEPATUS V10.x** generates the cryptographically-rendered carton des signatures with the authoritative PERNRs.

---

## 6. Process improvements for next session

1. **P01 read-only is now a CRITICAL rule in `feedback_rules.json`** — the next agent will have this at session start and will not attempt to script a P01 write.
2. **BCM signatory reconciliation is now a reusable protocol in the skill** — the next agent facing a similar request can follow the 7-step path (Parse → Brain lookup → Identify RY by name → Gold DB pre-check → P01 person validation → Run reconciliation check → Spec for DBS).
3. **The check script is runnable without context** — `python bcm_signatory_reconciliation_check.py --entity UIS --carton cartons/uis_citibank_canada_YYYYMMDD.txt` works as a one-liner and returns exit code 1 on any defect.
4. **Cartons directory is canonical and versioned** — future cartons go to `Zagentexecution/quality_checks/cartons/` with `<entity>_<bank>_<yyyymmdd>.txt` naming. Never overwrite — keep historical diffs.
5. **Parked questions for TRS** — `uq_uis_non_citibank_signatories` and `uq_uis_bcm_role_split_consistency` are now in `known_unknowns.json` with `addressed_to` and `blocks_action` fields. Next session can read these and know what's waiting on whom.
6. **Check session number early** — when running a session close, confirm the next session number from `ls knowledge/session_retros/` BEFORE writing brain entries with `created_session=N`, to avoid parallel-stream collisions.

---

## 7. Open items for follow-up

| Item | Owner | Status | Blocker |
|------|-------|--------|---------|
| Patch brain entries `created_session=51` → `52` (3 rules, 2 claims, 1 DQ, 2 known_unknowns, 1 incident) | Agent | Pending in this session | — |
| Reply to Ingrid Wettie confirming SAP update + reminder of 2026-04-22 bank confirmation deadline | User (Pablo) | Pending | None — draft text available in incident doc |
| Ghost PERNR 10567156 cleanup (delimit + insert 10067156) | DBS | Waiting on TRS authorization | TRS must issue a letter or authorize the correction |
| UIS panel drift: confirm whether STEPHENSON/ZHANG are legitimate at other UIS banks | TRS | Waiting on TRS | User already informed business |
| UIS role-split: confirm whether YLI-HIETANEN commit-only and SANNEH validate-only is intentional | TRS | Waiting on TRS | User already informed business |
| Run reconciliation check for UNES/IIEP/UBO/UIL against their respective cartons (we only have UIS) | Agent | Waiting for cartons | TRS must provide PDFs |

---

## 8. Stats

- Rules: 69 → **72** (+3)
- Claims: 41 → **43** (+2)
- Data quality: 20 → **21** (+1)
- Known unknowns: 32 → **34** (+2)
- Incidents: 2 → **3** (+1)
- BCM signatory assignments in Gold DB: 253 → **255** (+2)
- New code files: 3 (`extract_bcm_signatories.py`, `bcm_signatory_reconciliation_check.py`, `update_brain_inc6313.py`)
- New knowledge files: 2 (`INC-000006313_uis_bcm_add_voffal.md`, this retro)
- Skill updates: 1 (`sap_payment_bcm_agent/SKILL.md` BCM Signatory Management section + 7-step protocol)
- Session duration: ~1 session
- P01 writes performed: **0** (read-only boundary held)

---

# PART 2 — Full UIS panel cleanup (2026-04-13)

## 9. Part 2 summary

After business confirmation (2026-04-13), the 3 pre-existing defects identified during Part 1 side-findings were authorized for cleanup. 9 HRP1001 operations delivered as spec, executed by DBS. One IIEP/UIS mis-target was caught and corrected the same day. Final reconciliation: exit 0, both UIS rules 8/8 matching the Citibank Canada carton.

## 10. Operations executed (9 rows across 2 rules)

**Rule 90000004 / RY 50010054 `UIS signatures for all transfers`**:
1. DELIMIT ghost 10567156 Svein OESTTVEIT
2. ADD real 10067156 Svein OESTTVEIT (user S_OESTTVEIT)
3. DELIMIT 10136066 STEPHENSON-ODLE (not on carton)
4. DELIMIT 10098989 ZHANG (not on carton)
5. ADD 10150918 SANNEH (was validator-only)

**Rule 90000005 / RY 50036801 `UIS Validation`**:
6. DELIMIT ghost 10567156 Svein OESTTVEIT
7. DELIMIT 10098989 ZHANG
8. ADD real 10067156 Svein OESTTVEIT
9. ADD 10097358 YLI-HIETANEN (was committer-only)

## 11. The IIEP / UIS near-miss (biggest learning of Part 2)

DBS first added Svein (PERNR 10067156) to `IIEP Validation` (RY 50010087) by mistake instead of `UIS Validation` (RY 50036801). Both groups sit adjacent in the OOCU_RESP tree under rule 90000005 and both end with the word "Validation".

**Caught by**: `bcm_signatory_reconciliation_check.py` role-split warning — Svein appeared on UIS Commit but not on UIS Validation. Direct P01 RFC read then exposed his row sitting on IIEP instead.

**Had it gone undetected**: Svein would have been able to approve IIEP payments (wrong entity, no authorization letter, compliance breach).

**Fix**: DBS reversed the IIEP add (delimited the wrong row on 2026-04-12) and re-added Svein on UIS Validation correctly. Less than one day of exposure.

**Promoted to feedback rule**: `feedback_bcm_spec_must_include_rule_ry_stext` (HIGH severity). Every change spec row must include all three identifiers: Rule number, RY OBJID, STEXT. The RY OBJID is the only unambiguous identifier.

## 12. Part 2 final state — verified 2026-04-13

Reconciliation check output:
```
Ghost PERNR check            : 0 ghosts
Role-split check for UIS     : 0 inconsistencies
Carton diff                  : MATCH=8, EXTRAS=0, MISSING=0
Exit code                    : 0
```

Both rules now mirror the carton exactly: 8 PERNRs, all on both Commit and Validation.

---

# SESSION CLOSE — addressing the 5 questions

## Q1. What did we learn about SAP?

**Already captured in Phase 4b (§5) above** — but Part 2 added three operationally critical items:

1. **Lookalike-group trap in OOCU_RESP rule 90000005 tree.** Groups named `IIEP Validation`, `UIS Validation`, `UNES TRS Validation up to 50.000.000`, `UBO Validation up to 10.000 USD`, `UIL Validation` all sit adjacent, all end with "Validation", all share the rule code `BNK_01_01_04`. The only unambiguous discriminator is the **RY OBJID** (8 digits). Name-only references can silently land a signatory on the wrong entity and cause compliance breaches.
2. **DBS uses execution date, not letter date, for BEGDA by default.** Every add in Parts 1 and 2 was inserted with BEGDA = day-of-execution rather than 2026-04-02 (letter "as of immediate effect"). Low material risk, but this means SAP BCM BEGDA ≠ bank authorization date by default. Change specs must explicitly instruct DBS to use the letter date if strict alignment matters.
3. **Ghost PERNRs are not a one-off.** The 10567156 ghost for Svein OESTTVEIT existed for 6 months silently. Before this session, we had no automated way to detect one. Now we do (`bcm_signatory_reconciliation_check.py` Check #1). Recommend running this check quarterly across ALL entities, not just UIS, to find any other ghosts lurking in UNES/IIEP/UBO/UIL panels.

## Q2. What new objects did we add to the brain?

Before Session #052 the brain had essentially no classified BCM objects. Post-rebuild, it has **167 objects** (was 145 at Session #052 start — +22). The new BCM-relevant nodes:

| Object | Type | Role |
|--------|------|------|
| `HRP1000` | SAP_TABLE | PD object header — where RY responsibility groups live |
| `HRP1001` | SAP_TABLE | PD relationships — where signatory assignments live |
| `PA0002` | SAP_TABLE | Personal data infotype — name resolution |
| `PA0105` | SAP_TABLE | Communication infotype — SAP user + email resolution |
| `OOCU_RESP` | SAP_TRANSACTION | The OOCU maintenance transaction |
| `BNK_COM_01_01_03` | WORKFLOW_RULE | Rule 90000004 (COMMIT) |
| `BNK_INI_01_01_04` | WORKFLOW_RULE | Rule 90000005 (INITIATE / VALIDATION) |
| `50010054` | RY_GROUP | UIS signatures for all transfers |
| `50036801` | RY_GROUP | UIS Validation |
| `50010087` | RY_GROUP | IIEP Validation (now a known-trap lookalike) |
| 14 other `500xxxxx` | RY_GROUP | Other entity panels (UNES, UBO, UIL, tier-limited historical groups) |
| `bcm_signatory_responsibility` | GOLD_DB_TABLE | Materialized snapshot of RY groups |
| `bcm_signatory_assignment` | GOLD_DB_TABLE | Materialized snapshot of PERNR assignments |
| `bcm_signatory_reconciliation_check.py` | QUALITY_CHECK_SCRIPT | Recurring DQ detector |

**Plus**: 1 new incident (INC-000006313), 4 new feedback rules (P01 read-only, RY schema, ghost-PERNR check, spec-must-include-RY), 3 new claims (RY storage, ghost PERNR, lookalike trap), 1 RESOLVED DQ (ghost), 1 ANSWERED known unknown (role split), 1 still-open known unknown (UIS non-Citibank accounts).

## Q3. What relationships do we need to maintain going forward?

Four maintenance edges that must survive across sessions:

1. **Carton ↔ SAP mirror** — every bank carton TRS issues for any entity creates an expected state in `bcm_signatory_assignment`. The canonical carton files live in `Zagentexecution/quality_checks/cartons/<entity>_<bank>_<yyyymmdd>.txt` and must be updated whenever TRS issues a new letter. Old cartons are never overwritten, so we can reproduce reconciliation as of any past date.

2. **HRP1001 → PA0105/0001 integrity** — every HRP1001 row with SCLAS='P' SOBID=X must resolve to a non-empty PA0105 SUBTY='0001' USRID for PERNR X, otherwise it's a ghost. The reconciliation check enforces this.

3. **Rule-symmetry invariant** — for any entity's bank panel where the carton says "sign jointly two by two", the set of active PERNRs on rule 90000004 (Commit) must equal the set on rule 90000005 (Validation). Any asymmetry is either (a) maintenance drift or (b) intentional role split — must be documented per entity.

4. **Entity-level vs bank-account-level** — SAP BCM groups are entity-level. If an entity holds accounts at multiple banks, there is ONE SAP group covering all of them, but potentially several bank cartons. Reconciliation must use the **union of all the entity's cartons**, not a single carton, before concluding drift exists.

## Q4. Do we need to reconstruct the brain?

**No.** The brain was rebuilt once in this session (`python brain_v2/rebuild_all.py`) and is FRESH (0.0 hours old, 0 stale sources). The rebuild was a normal regenerate-from-source, not a reconstruction.

**Reasons not to reconstruct**:
- `brain_v2/brain_state.json` is mechanically derived from the source JSONs (rules, claims, DQ, known_unknowns, incidents, annotations). All 7 source files are current and consistent.
- The NetworkX graph has 53,912 nodes and 114,029 edges — intact.
- SQLite Active DB is rebuilt from sources every rebuild; no orphan state.
- Coverage is 56.2% (down from 71.4% at start because we added many new referenced PERNR names in the incident record that aren't yet classified as first-class objects). This is NOT a reconstruction trigger — it's a "next-session add ~20 PERNRs to `objects[]`" task to bring coverage back above 70%.

**When a reconstruction would be warranted** (none of these apply now):
- Source JSON corruption or schema mismatch
- Multiple sessions' claims/rules contradicting each other without resolution
- Graph becoming unrebuilable from sources

## Q5. What can we do better?

Five concrete improvements for future similar work:

1. **Always emit specs with RY OBJID as primary key** — not entity name, not STEXT. The IIEP/UIS near-miss proved that name-based references are not safe when adjacent groups share wording. This is now enforced by `feedback_bcm_spec_must_include_rule_ry_stext`.

2. **Instruct DBS explicitly on BEGDA** — "use 2026-04-02 (TRS letter date) as BEGDA, not today" needs to be a line in every spec. Otherwise DBS defaults to execution date and SAP drifts from the letter by 1–7 days. Add a pre-execution checklist item.

3. **Run the check BEFORE the spec, not only after** — in Part 2, if I had run `bcm_signatory_reconciliation_check.py` on all entities at session start, I'd have seen the ghost defect immediately without needing the carton PDF comparison. The check is cheap (seconds) — run it at every BCM session start.

4. **Proactively collect cartons for all entities** — we only have the UIS Citibank Canada carton. UNES, IIEP, UBO, UIL all have bank accounts with authorized panels we haven't fingerprinted. A one-time ask to TRS for the latest cartons of all 5 entities would let the reconciliation check cover every panel.

5. **Session-number check at session close** — before writing brain entries with `created_session=N`, always `ls knowledge/session_retros/session_05*.md` to confirm N hasn't been claimed by a parallel stream. Part 1 of this session lost an hour patching `created_session=51` → `52` because another stream closed 051 earlier the same day. Trivial to avoid with a pre-write check.

---

## 13. Final stats (Session #052 total — Part 1 + Part 2)

- Rules: 69 → **82** (+13 across project streams, 4 from this session)
- Claims: 41 → **46** (+5 across project streams, 3 from this session)
- Data quality open: 21 → **7** (one resolved this session: ghost PERNR; others handled by parallel streams)
- Known unknowns: 32 → **34** (+2 from this session; 1 answered this session)
- Incidents: 2 → **6** (+4 across project streams, 1 from this session)
- BCM signatory assignments in Gold DB: 253 → **259** (+6: Said ×2, real Svein ×2, Sanneh, Yli-Hietanen)
- BCM ghost PERNRs in production: 1 → **0** ✅
- Brain state: 299,845 → **354,606 bytes** (8.9% of 1M context, still well within budget)
- New code files: 3
- New knowledge files: 2
- Skill updates: 1 (now with full reconciliation protocol + validation-against-bank + lookalike trap)
- **P01 writes performed by agent: 0** (read-only boundary held across all 21 timeline events)
- Incident INC-000006313: **CLOSED_WITH_CLEANUP** — SAP mirrors Citibank Canada carton perfectly, reconciliation exit 0
