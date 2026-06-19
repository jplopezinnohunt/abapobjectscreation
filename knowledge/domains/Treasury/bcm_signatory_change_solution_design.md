# BCM Signatory-Change — Solution & Routine Design (schema + flow + procedure)

**Status**: design, v1.2 — 2026-06-19 (added release-config chain `TBCA_REL_*`, grouping-rule conditions, reject BAdI; corrected: grouping is also bank-agnostic)
**Origin incident**: INC-000011781 (UBO / add Renata Ritter)
**Source of every fact below**: **live P01 reads via `RFC_READ_TABLE`** (`rfc_helpers.get_connection("P01")`). NOT screenshots — screenshots are not authoritative (period filters hide rows; OCR is unreliable). P01 is **read-only** for the agent; changes are executed by DBS in `OOCU_RESP`.
**Related**: [`bcm_signatory_rules.md`](bcm_signatory_rules.md) · skill `sap_payment_bcm_agent` (Reconciliation Protocol, Step 7 mandatory output)

---

## 1. Purpose
Standard, repeatable solution for "Change in Bank Signatory panel of <ENTITY>" incidents: validate the TRS letter/carton, read the **real** current SAP state from P01, reconcile, and produce a DBS change-spec + TRS reply — separating the **current ask** from **old issues**.

---

## 2. Data model — THREE levels (the schema)

```
LEVEL 1  ENTITY  (company code, e.g. UBO)  ── the scoping key for signatory nodes
            │
   ┌────────┴───────────────────────────────────────────────┐
   │                                                          │
LEVEL 2  BANKS (per entity)                       LEVEL 3  SIGNATORY NODES (per entity)
   from T012/T012K                                    PD objects OTYPE='RY'
   each house bank account                            key = (ENTITY × RULE × AMOUNT-TIER)
   has ITS OWN carton (legal authority)               bank-AGNOSTIC people-buckets
   BCM-routed banks = those in T042A                  members = HRP1001 RELAT='007' SCLAS='P'
```

- **Level 1 — Entity** = SAP company code (`ZBUKR`). This is what scopes the signatory nodes.
- **Level 2 — Banks** = `T012`/`T012K` house banks of the company code. Each **bank account** has its own *carton des signatures* (account-level legal authority). The banks that actually reach BCM are the ones in **`T042A`** (F110 payment path). Banks **not** in `T042A` (collection/manual) never produce a BCM batch.
- **Level 3 — Nodes** = `RY` responsibility objects, keyed by **entity + amount band** (selection logic in §3a). Their selection criteria live in **infotype 1218** (`HRP1218`/`HRT1218`) as expressions on the standard BCM structure `BNK_STR_BATCH_REL_APPR` — **NOT** in the generic PFAC `HRP1222` (which is empty here). Members live in `HRP1001` (`RELAT='007' SCLAS='P' SOBID=PERNR`, with `BEGDA/ENDDA`).

### Two "rules" — and NEITHER is bank-aware (corrected 2026-06-19)
| Concept | Keyed on | Bank-aware? | Where (verified live) |
|---|---|---|---|
| Batch-grouping rule (`RULE_ID`, e.g. `UBO_AP_MAX/ST`) | grouping origin + company code + amount + payment method | **NO** | `TBNK_RULE` / `TBNK_RULE_SELOP` — see §3b |
| Signatory rule `90000005` (BNK_INI / Validate) | entity + amount tier | **NO** | RY nodes, IT1218 (§3a) |
| Approval rule `90000004` (BNK_COM / Commit) | entity + amount tier | **NO** | RY nodes, IT1218 (§3a) |

> **Correction (was wrong in v1.1):** the grouping rule does **not** key on house bank. `UBO_AP_MAX`'s real conditions (`TBNK_RULE_SELOP`, read live 2026-06-19) are grouping origin + company code + amount + payment method — **no `HBKID`**. The bank is only **carried** on the batch (`BNK_BATCH_HEADER.HBKID`), never **tested** at any layer. Bank-agnostic therefore holds for **both** grouping and signatory selection.

---

## 3. The flow — bank → rule → node (how SAP picks the signatories)

```
Bank (CIT01 / BRA01 / …)  ── only decides which BATCH is built
        ▼
BCM batch  RULE_ID=UBO_AP_ST/MAX  carries  ZBUKR=UBO + HBKID + amount
        ▼
BCM release WF WS50100024 → WS50100021 (std BUSISB001)  →  approval procedure picks the AMOUNT tier
        ▼
scoped by ENTITY (ZBUKR=UBO), NOT by bank:
   90000005 INI  ≤10K (50034892)   ≤5M (50034893)
   90000004 COM  ≤10K (50034894)   >10K (50036737)
        =  people-buckets (members = HRP1001). Selection criteria in IT1218 — see §3a.
```

### 3a. Node selection — WHERE the logic lives (verified live in P01, infotype 1218)

It is **not** the generic PFAC criteria mechanism (`HRP1222` is empty). The selection criteria sit on each `RY` node in **infotype 1218**: `HRP1218` (header → `TABNR`) → `HRT1218` (expression rows), as **expressions evaluated against the standard BCM container structure `BNK_STR_BATCH_REL_APPR`**.

**Runtime selection — PROVEN by reading the code (2026-06-19), all STANDARD SAP, no custom code:**
`BNK_API_GET_REL_ACTORS` → `BCA_API_REL_GET_ACTORS` → `BCA_OBJ_REL_GET_ACTORS` (FG `BCA_OBJ_REL_WF_CUST`). The last one: (1) `BCA_DB_REL_RULE_SEL_SINGLE` reads `TBCA_REL_RULE` → the rule (90000004/05); (2) builds a workflow rule object `OTYPE='AC' OBJID=<rule>`; (3) reads `TBCA_REL_OBJ_CAT` → structure `BNK_STR_BATCH_REL_APPR`, fills it from the batch and maps it to a workflow **container**; (4) calls the standard agent FM **`RH_GET_ACTORS`** with the rule + container → returns the agents. `RH_GET_ACTORS` resolves the rule as a **Responsibilities** rule and evaluates each RY node's IT1218 criteria → the matching node's `HRP1001` people. **The reject BAdI plays no part in selection.** Evidence: `BADI_IMPL` for `BNK%` = 3 impls, only **1 custom** (the reject `Z_CL_BNK_BADI_PAYMT_CHG`), **none for agent selection**. FM sources saved under `code/` (`bnk_get_rel_actors.abap`, `bca_get_actors.abap`, `bca_obj_get_actors.abap`).

Exact criteria read live from `HRT1218`:

| Node | Rule | `ZBUKR` | `MAXPAYAMT_RULECURR` | `RULE_ID` |
|---|---|---|---|---|
| 50034892 | 90000005 INI | UBO | 0 – 10 000 | UBO_AP_MAX |
| 50034893 | 90000005 INI | UBO | 10 000 – 5 000 000 | UBO_AP_ST |
| 50034894 | 90000004 COM | UBO | 0 – 10 000 | — |
| 50036737 | 90000004 COM | UBO | 10 000 – 50 000 000 | — |

**Runtime selection key = `ZBUKR` (entity) + `MAXPAYAMT_RULECURR` (amount band)** (+ `RULE_ID` on the INI nodes). There is **no `HBKID`/bank field anywhere in the criteria** → confirms bank-agnostic node selection. It IS standard BCM (the *Approval Procedure* customizing generates the rule and writes these IT1218 expressions); it only *looked* non-standard because it bypasses the usual PFAC/`HRP1222` path. The amount thresholds (10 000 / 5 000 000 / 50 000 000) are the BCM approval-procedure amount levels.

**Worked example — THIS is the selection point (raw `HRT1218`, live P01).** A UBO payment of USD 7,500 (batch `ZBUKR=UBO`, amount 7 500, `RULE_ID=UBO_AP_MAX`): `RH_GET_ACTORS` evaluates each node's IT1218 condition against the batch container and keeps the ones where ALL match → **50034892** (INI, `ZBUKR=UBO` ∧ 0–10000 ∧ UBO_AP_MAX) for validate, **50034894** (COM, `ZBUKR=UBO` ∧ 0–10000) for sign; the >10K / ≤5M nodes are excluded by the amount band. The selected node's people = its `HRP1001` `A007→P` agents (node 50034892 = 11 persons). So "the node" is the RY row whose IT1218 carries `ZBUKR='UBO'` + the amount band the payment falls in. Raw per-node criteria persisted to Golden DB `bcm_node_selection_criteria` (67 rows / 24 nodes).

**Consequence (the invariant):** because the node is chosen by **company code + amount** and never by bank, **all of an entity's BCM banks share the same node set (N banks : 1 node set)**. Therefore **every BCM-routed bank's carton for that entity MUST list the same people** — otherwise the single node would over-authorize the stricter bank. SAP on ECC cannot model per-bank signatories. → If two cartons of the same entity diverge, HALT and escalate to TRS (rule not representable).

---

### 3b. WHERE the node is configured — release chain + custom code (verified live P01/D01, 2026-06-19)

The signatory node is not configured on one screen; it is the end of a chain across the BCM **release framework** (`TBCA_REL_*`), plus the grouping process upstream and a custom reject BAdI.

**(i) Upstream grouping process — `TBNK_RULE` / `TBNK_RULE_SELOP`** (general BCM, a *separate* process from signing). `UBO_AP_MAX` (the ≤10K bucket) real conditions, read live:

| Seq | Field | Attribute | RelOp | Low … High |
|---|---|---|---|---|
| 1 | `DORIGIN` | Grouping Origin | BT | FI-AP … FI-AR-PR |
| 1 | `ZBUKR` | Paying Company Code | EQ | UBO |
| 1 | `AMT_RULECU` | Payment amount (rule ccy) | GT | `10000.00-` |
| 1 | `RZAWE` | Payment Method | EQ | R |

`AMT_RULECU GT 10000.00-` = amount > −10,000 (AP outgoing amounts are negative) → matches abs value **< 10,000** = the ≤10K bucket. **No `HBKID`** → grouping is bank-agnostic. **Dev→prod drift:** P01 has **13** grouping rules; D01 has **14** (extra `UNES_AX_EX` Exotic Currency, not transported). The IMG screenshots were D01 ("Change View"). Authoritative prod list = the 13 in Golden DB `bcm_grouping_rule`.

**(ii) Release configuration chain** (full, every row read live — table → value):

| # | Step | Where (verified table) | Actual value in P01 |
|---|---|---|---|
| 1 | Batch carries the inputs | struct `BNK_STR_BATCH_REL_APPR` | `RULE_ID` + `ZBUKR` + amount + payment method |
| 2 | Release object → type + procedure | `TBCA_RELPROC_CUS` | `BNK_COM` → REL_TYPE **3**, proc **01** · `BNK_INI` → REL_TYPE **1**, proc **01** |
| 3 | **Which procedure fires (determination)** | **`TBCA_RELPROC_EXP`** | proc 01 fires when batch `RULE_ID` ∈ { IIEP_AP_ST, UBO_AP_MAX, UBO_AP_ST, UIS_AP_ST, UIS_AP_MAX, UIL_AP_ST… } — OR-expression on `BNK_STR_BATCH_REL_APPR` (maint. M_SPRONK 2022-23) |
| 4 | Procedure name | `TBCA_REL_PROC`(T) | 01 = **"Dual Ctrl"** (00 No release · 02 3x · 03 4x) |
| 5 | **Step → rule (the wiring)** | `TBCA_REL_RULE` | BNK_INI/01/01 → **90000005** · BNK_COM/01/01 → **90000004** |
| 6 | **Rule → its RY nodes** | `RY.rule_number` (HRP1000 / `bcm_signatory_responsibility`) | **90000004** → 50034894, 50036737 (+ all entities' commit nodes) · **90000005** → 50034892, 50034893 (+ …). All entities hang under just these 2 rules |
| 7 | Pick ONE node among the rule's siblings | `IT1218` (`HRP1218`/`HRT1218`) | `ZBUKR` + amount band [+ `RULE_ID` on INI] → the matching node |
| 8 | People of that node | `HRP1001` (RELAT 007, SCLAS P) | the PERNRs — **what DBS edits in `OOCU_RESP`** |
| 9 | Activity → function module | `TBCA_REL_FM` | all **standard** `BNK_API_BATCH_*` (reject = activity `06` → `BNK_API_BATCH_REJECT`) — no custom FM |
| 10 | Workflow per step | `TBCA_RTW_LINKAGE` | BNK_INI → WF `31000004` · BNK_COM → WF `50100021`; master WF `50100024` |
| 11 | **On REJECT — only custom code** | BAdI `BNK_BADI_ORIG_PAYMT_CHG` → `Z_CL_BNK_BADI_PAYMT_CHG` | `ON_REJECT`: auto-reverse the F110 payment (FBRA reset + FB08, reason 01); log SLG1/FBPM |

**Plain reading:** the grouping `RULE_ID` does double duty — it groups the batch **and** (via `TBCA_RELPROC_EXP`, step 3) selects the **Dual-Control** procedure. The step maps to a **rule** (90000004 commit / 90000005 validate); each rule owns a set of **RY nodes** (step 6, via `rule_number`); the node's **IT1218** criteria (entity+amount) pick the one that matches; its **HRP1001** people sign. **"Configuring a node" = `OOCU_RESP` Change** (people + IT1218). Determination FMs are standard; the **only** custom code is the reject BAdI.

> **Correction vs the first §3b draft:** the procedure is assigned/determined by `TBCA_RELPROC_CUS` + `TBCA_RELPROC_EXP` (NOT `TBCA_REL_PROC`, which is only the name catalogue), and the rule→node link is the `rule_number` carried on each RY. All read live via `RFC_READ_TABLE` 2026-06-19, persisted to Golden DB (`bcm_release_proc_assign`, `bcm_release_proc_determination`, `bcm_release_activity_fm`, `bcm_release_rule`, `bcm_release_*`).

**(iii) Custom code** — the only method implemented in `Z_CL_BNK_BADI_PAYMT_CHG` is `IF_EX_BNK_ORIG_PAYMT_CHG~ON_REJECT` (SAP note 1333640): on batch/payment **reject**, reverse the F110 payment (`J_1B_FBRA_POSTING_AUFRUFEN`, reversal reason `01`) and log to SLG1/FBPM. Full source: [`code/Z_CL_BNK_BADI_PAYMT_CHG.abap`](code/Z_CL_BNK_BADI_PAYMT_CHG.abap) (read from D01 via ADT). It does **not** affect agent/node selection — it is the reject handler only.

**(iv) Custom logic lives in a SEPARATE gate — FI "Release for Payment" (`WS90000003`), NOT the BCM batch release.** Two distinct approval gates exist: **(1) FI Release for Payment** = `WS90000003` (tasks "Determine subworkflow release for payt", "Release for payment single-stage" = std `WS00400011`, "Reset payment block") — a **document/invoice-level** gate run **before** F110, and **where UNESCO's custom code is**; **(2) BCM batch signatory release** = `WS50100024`→`WS50100021` (std `BUSISB001`, tasks RELEASE/GETRELEASESUBWORKFLOW) — run **after** F110 on the payment file, agent selection **standard** (`RH_GET_ACTORS`, §3a). The migrated-session note that called `90000003` "the BCM workflow" conflated the two. Gate (1) runs **4 custom tasks (D_CROUZET, 2010)**, persisted in Golden DB `bcm_workflow_custom_task`:

| Task | BOR method | Name | What it does |
|---|---|---|---|
| TS90000008 | `BSEG.CHANGE` | Change Document Line | change a doc line item |
| TS90000010 | `SYSTEM.GENERICINSTANTIATE` | ZGETGOSNOTE | get a GOS note/attachment |
| TS90000011 | `SYSTEM.GENERICINSTANTIATE` | Create instance ZBSEG | instantiate custom BOR `YBSEG` |
| TS90000012 | **`BSEG.ZCREATEPAYMENTBLOCKWF`** | Set Block Payment to W | **set payment block `ZLSPR='W'`** |

The methods live on the **custom BOR subtype `YBSEG`** (PARENT `BSEG`, program `YBSEG_REL`, by A_AHOUNOU). `ZCREATEPAYMENTBLOCKWF` does a **direct SQL `UPDATE bseg`/`UPDATE bsik SET zlspr = 'W'`** for the document line (companycode/documentno/fiscalyear/lineitem). Full source: [`code/YBSEG_REL.abap`](code/YBSEG_REL.abap). **So the workflow DOES contain custom logic (payment blocking by direct table update), but it acts on the document — not on who-signs.** Node/agent selection remains standard `RH_GET_ACTORS` (§3a). ⚠️ Note for later: direct `UPDATE` of FI documents bypasses standard APIs — flag for review.

---

### 3c. End-to-end flow — TWO gates, with the config behind each step (verified 2026-06-19)

```
GATE 1 · FI RELEASE FOR PAYMENT (document-level, BEFORE F110) · WF WS90000003
  invoice posted (BKPF/BSEG)
   └─ CUSTOM block:  TS90000012 YBSEG.ZCREATEPAYMENTBLOCKWF → UPDATE bseg/bsik SET zlspr='W'  (W=Workflow block, T008T)  [prog YBSEG_REL]
   └─ CUSTOM:        TS90000011 instantiate BOR YBSEG (subtype of BSEG)
   └─ STANDARD:      TS00407859 determine subwf → WS00400011 "Release for payment single-stage" (approver releases)
        ├─ ✗ reject → CUSTOM YBSEG.rejectionreason → SGOS_NOTE_CREATE_DIALOG on BKPF (GOS note) + COMMIT; stays blocked
        └─ ✓ approve → STANDARD TS00407868 "Reset payment block" → ZLSPR cleared → payable
F110 PAYMENT RUN → GROUPING (Process ①)
   F110 selects free docs; banks from T042A (UBO: CIT01, BRA01); FBZP house-bank determination
   └─ GROUP: TBNK_RULE / TBNK_RULE_SELOP → RULE_ID by DORIGIN+ZBUKR+AMT_RULECU+RZAWE (no bank). ≤10K=UBO_AP_MAX, >10K=UBO_AP_ST; +GROUP_FIELD1=VALUT
   └─ batch: BNK_BATCH_HEADER (ZBUKR+HBKID+RULE_ID+amount) on BNK_STR_BATCH_REL_APPR
GATE 2 · BCM BATCH SIGNATORY RELEASE (file-level, AFTER F110) · WF WS50100024→WS50100021 (std BUSISB001)
   └─ procedure determ.: TBCA_RELPROC_CUS (BNK_COM type3/proc01, BNK_INI type1/proc01) + TBCA_RELPROC_EXP (RULE_ID∈{…} → proc 01 "Dual Ctrl")
   └─ STEP 1 validate: TBCA_REL_RULE BNK_INI/01/01 → rule 90000005
        └─ STANDARD select: BNK_API_GET_REL_ACTORS → BCA_OBJ_REL_GET_ACTORS → RH_GET_ACTORS(rule AC, container=BNK_STR_BATCH_REL_APPR)
             → eval RY IT1218 (ZBUKR+amount): rule 90000005 → RY 50034892 ≤10K / 50034893 ≤5M → people HRP1001
   └─ STEP 2 sign (different person, 4-eyes): TBCA_REL_RULE BNK_COM/01/01 → rule 90000004 → RY 50034894 ≤10K / 50036737 >10K; auth role BNK_APP
        ├─ ✗ reject → CUSTOM BAdI Z_CL_BNK_BADI_PAYMT_CHG~ON_REJECT → J_1B_FBRA_POSTING_AUFRUFEN (FBRA+FB08 reason 01) + SLG1/FBPM
        └─ ✓ commit
OUTPUT: DMEE → SWIFT/Coupa → bank
```
**One line:** Gate 1 (custom) blocks the *document* until released; F110 pays freed docs and groups by RULE_ID; Gate 2 (standard selection) gets two different people to validate then sign the *batch*. Custom code is only at the document gate (block/reject); signatory selection is 100% standard `RH_GET_ACTORS`.

---

## 4. Complete node inventory (live P01, 2026-06-17)

Structure is **not** uniformly "2 per company": 1..N nodes per (entity × rule), tiered by amount only where needed.

| Entity | COMMIT nodes (90000004) | INI nodes (90000005) | Pattern |
|---|---|---|---|
| **UBO** | 50034894 ≤10K · 50036737 >10K | 50034892 ≤10K · 50034893 ≤5M | **clean 2×2, amount-tiered** |
| UIS | 50010054 all · 50036326 ≤10K(0) | 50010051(0) · 50010053(0) · 50036801 | mixed; old tiers retired |
| IIEP | 50010088 all | 50010087 | single node |
| UIL | 50037531 all | 50037530 | single node |
| UNES | 50010052 (0 — Coupa) | 50010075/76/77/78/79 · 50032363 · 50036716(0) · 50038878 | many INI tiers; COMMIT→Coupa |
| (stubs) | — | 50038588 / 50038589 (empty "Generated Rule") | ignore |

`(0)` = zero active members today (delimited/retired). Full per-node active counts: see `full_inventory.py` output / `bcm_signatory_responsibility` + live `HRP1001`.

---

## 5. Reconciliation logic + completeness gate

```
BCM banks of entity  := banks of the company code present in T042A     (NOT all T012K)
require: a current carton for EACH BCM bank        ── completeness gate
assert : all those cartons are IDENTICAL           ── alignment gate (else HALT → TRS)
target := that single agreed panel, split by tier  (≤10K-only vs unlimited)
current:= live HRP1001 membership of the entity's RY nodes (all periods)
reconcile per (node × person):
   on carton & active in SAP            → keep
   on carton & absent/expired in SAP    → ADD  (current ask if in letter; else TRS gap)
   in letter "delete" & active in SAP   → DELIMIT (current ask)
   active in SAP & not on any carton     → over-auth → DELIMIT (TRS, old issue)
GATE: if any BCM bank lacks a current carton → DO NOT flag "SAP-extra" as drift;
      emit "INCOMPLETE: missing cartons for <HBKID…>".
```
Tier mapping (validated by Amaral): **"≤10K only"** → ≤10K nodes only; **"unlimited"** → all tier nodes of both rules.

---

## 6. MANDATORY output structure (locked 2026-06-17)

ONE table, mirroring `OOCU_RESP` **1:1** — every `HRP1001` row the screen shows (active **and** expired/red-X) **plus** the additions. Columns:

`Rule | Node (OBJID) | Node name (STEXT) | PERNR | Person | Live status (HRP1001) | Action`

- **Live status** = `Active` / `Expired <ENDDA>` / `New`. Include expired rows (action `—`, no action) so the table matches the SAP screen and never looks like a mismatch.
- Membership = live `HRP1001` read, **all periods** (resolve multi-period people — e.g. an expired + an active row in the same node).
- Legend: ✅ keep · ➕ ADD (current ask) · ➖ DELIMIT (current ask) · ⚠️ TRS (old issue, needs sign-off) · — no action.
- Follow with **net-operations summary**, split: **Current ask** (authorized by REF) vs **Old issues — hold for TRS**.
- Rule + OBJID + Node name on every row (lookalike-group safeguard).

---

## 7. The routine (phases) — read-only; DBS executes

| Phase | What | How (read-only) |
|---|---|---|
| 0 Ingest | extract PDFs + body from the .eml; detect entity + bank list | `parse_eml`/`extract_attach` |
| 1 Validate request | read each carton/letter → {ref, account, effective_date, deletes[], adds[], panel[tier]}; cross-check carton PERNR = passport = email-id; assert all cartons identical | agent + PDF read |
| 2 Live state | read RY nodes of the entity + `HRP1001` all periods; never a stale snapshot/screenshot | `RFC_READ_TABLE` |
| 3 Employee validity | `PA0000` STAT2=3, `USR02` UFLAG/GLTGB, `PA0002`/`PA0105` for adds (esp. new) | `RFC_READ_TABLE` |
| 4 Reconcile | §5 logic + completeness/alignment gates | deterministic |
| 5 Output | §6 mandatory table + net-ops spec + TRS reply + `INC-xxxx.md` | templated |
| — Execute | **DBS** in `OOCU_RESP` (P01). Agent never writes P01. | DBS |
| 6 Verify | re-read `HRP1001`; refresh `extract_bcm_signatories.py`; `bcm_signatory_reconciliation_check.py` | `RFC_READ_TABLE` |

---

## 8. Worked example — INC-000011781 (UBO / Renata Ritter)
- BCM banks (T042A): **CIT01 + BRA01**; both cartons received and **identical** (8 signatories) → rule representable.
- Renata `10021811` confirmed on carton; live: `PA0000` STAT2=3 active, `USR02 R_RITTER` unlocked (⚠️ validity ends 2026-09-30), `PA0105` user/email match. Still lacks `BNK_APP` role (Security).
- **Current ask:** ADD `10021811` to all 4 UBO nodes; DELIMIT `10108464` Martin in **50034893** (his only active period — verified via all-periods read; screenshot hid it).
- **Old issues (TRS):** Ba `10005016` + De Sousa Carvalho `10016038` (active, not on carton → over-auth); Yli-Hietanen `10097358` (on carton, expired 2024 in SAP → gap); Gazi `10105030` (expired, no action).

---

## 9. Data sources used (all live P01)
`HRP1000`, `HRP1001` (all periods), **`HRP1218`/`HRT1218` (node-selection criteria = expressions on `BNK_STR_BATCH_REL_APPR`: `ZBUKR` + `MAXPAYAMT_RULECURR` + `RULE_ID`)**, `HRP1222`/`HRP1230` (empty — confirms selection is NOT via the PFAC path), `BNK_BATCH_HEADER`, `T012`/`T012K`, `T042A`, `PA0000`, `PA0002`, `PA0105`, `USR02`, `DD02L`/`DD03L`.

**Added 2026-06-19 (release chain + grouping):** grouping rules `TBNK_RULE` / `TBNK_RULE_T` / `TBNK_RULE_SELOP`; release framework `TBCA_REL_RULE` / `TBCA_REL_PROC`(T) / `TBCA_REL_OBJ_CAT` / `TBCA_RTW_LINKAGE`; reject BAdI `Z_CL_BNK_BADI_PAYMT_CHG` (read from **D01** via ADT — code is system-invariant Z*).

**Golden DB tables (derived snapshots — local-only, NOT in git):** `bcm_signatory_responsibility`/`bcm_signatory_assignment` (signing); `bcm_grouping_rule`/`bcm_grouping_rule_selop` (grouping); `bcm_release_rule`/`bcm_release_procedure`(`_t`)/`bcm_release_object`/`bcm_release_wf_linkage` (release chain). Refresh before relying on counts.
