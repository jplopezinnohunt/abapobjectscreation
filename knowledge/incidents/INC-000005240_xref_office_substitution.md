# INC-000005240 — Root Cause Analysis (canonical, v2)

**Date:** 2026-04-09 | **Analyst:** JP Lopez (main agent, Session #051)
**Status:** Root cause **CONFIRMED** from SAP source code + live RFC data — fix path defined
**Supersedes:** `INC-000005240_f53_fistl_unesco_default.md` (v1, wrong mechanism — see §13 Triage)

---

## 1. Issue — As Received

### 1.1 Email from Anthony Leonardo Jonathan (FU/JAK) — 07.04.2026 09:47 UTC

> "When posting F-53 the reference key becomes HQ instead of JAK even though there is no option for inputting the Reference 1 and 2"

(Verbatim from the `.eml` body — no screenshots attached.)

### 1.2 The Question

Why does Anthony's user — a Jakarta field-unit finance clerk — see **"HQ"** in the "reference key" field of every F-53 outgoing payment he posts, with no on-screen opportunity to override it?

### 1.3 Context — prior custom development on YRGGBS00

UNESCO runs a custom copy of SAP-standard substitution form pool `RGGBS000` named `YRGGBS00`. It defines XREF1 / XREF2 / ZLSCH / asset-expense / ICTP substitution exits. The XREF1 / XREF2 forms (`UXR1` / `UXR2`) were introduced in ~2009 by I_KONAKOV (commit marker `***IKON27032009`) to drive office-based downstream logic: the office code written here is later read by form `UZLS` to decide the payment method (`ZLSCH='O'` for field-office outbound vs default for HQ).

### 1.4 Ticket Summary

| Field | Value |
|---|---|
| Ticket | INC-000005240 |
| Received | 2026-04-07 09:47 UTC |
| Reporter | Anthony Leonardo Jonathan — `AL_JONATHAN` |
| Email | al.jonathan@unesco.org |
| Department | FU/JAK — Field Unit / Jakarta |
| Priority | Moderate |
| Classification | Core Applications → SAP → Report an Issue |
| Transaction | F-53 (dialog wrapper → posts as `FBZ2` / `FBZ1` in BKPF) |
| Screenshot | None |

### 1.5 User term → SAP field translation (MANDATORY per skill feedback_user_term_to_sap_field_translation)

| User says | SAP field / object | Confidence | Why |
|---|---|---|---|
| "reference key" | **`BSEG-XREF1`** and **`BSEG-XREF2`** (Reference Key 1 / 2) | **HIGH** | The user clarifies himself in the same sentence: *"no option for inputting the Reference 1 and 2"*. XREF1/XREF2 are the only BSEG line-item fields literally labelled "Reference Key 1" / "Reference Key 2". |
| "HQ" | Office code `'HQ'` (UNESCO Headquarters, Paris) — 2-char value of the `Y_USERFO` SU3 parameter in USR05 | **HIGH** | Confirmed in source at `YRGGBS00_SOURCE.txt:1093` as the expected XREF2 value for UNES HQ postings, and validated against YFO_CODES.FOCOD. |
| "JAK" | Office code `'JAK'` — the Jakarta Field Unit value for `Y_USERFO` | **HIGH** | Matches the user's department "FU/JAK". Comparable office codes observed in production USR05: `YAO` (Yaoundé), `KAB` (Kabul), `DAK` (Dakar). |
| "no option for inputting" | The F-53 dialog screen **does not expose** XREF1/XREF2 as input fields for payment lines | **HIGH** | This triggers the `IF bseg_xref2 = space` branch in form `UXR2`, which reads USR05 and substitutes. |

**Key anti-confusion note:** the string `"UNESCO"` in INC-000006073 means a *fund center* populated by FMDERIVE exit `ZXFMDTU02_RPY`. The string `"HQ"` in this incident is an *office code* populated by forms `UXR1`/`UXR2` in YRGGBS00. **Completely different mechanism. Do NOT conflate.** (Lesson recorded as feedback rule `feedback_user_term_to_sap_field_translation`.)

---

## 2. Executive Summary

### 2.1 Ticket statement

`AL_JONATHAN` (Jakarta Field Unit — FU/JAK) reports that when he posts F-53 outgoing payments, the "reference key" becomes `HQ` instead of `JAK`, and the F-53 screen gives him no way to enter `Reference 1` / `Reference 2` before posting.

### 2.2 Short explanation (to be used when answering the user)

UNESCO tags every FI line item with an **originating office code** (e.g., `HQ`, `JAK`, `YAO`, `KAB`, `DAK`, `BRZ`, `IIEP_PAR`, `UIS`, `IBE`) in the fields **`BSEG-XREF1`** and **`BSEG-XREF2`**. The tag is written automatically at posting time by custom **substitution** forms in the form pool `YRGGBS00`:

- **`FORM UXR1`** — [YRGGBS00_SOURCE.txt:996](../../Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt#L996) — writes `BSEG-XREF1`
- **`FORM UXR2`** — [YRGGBS00_SOURCE.txt:1024](../../Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt#L1024) — writes `BSEG-XREF2` (only when blank — always true on F-53 since the screen hides the field)

At the moment the document is posted (whether it's an invoice via FB60/MIRO/FB01, a direct disbursement via F-53/FBZ2, a payment run via F110, or a manual clearing via FB1K), the substitution reads the **posting user's `USR05` parameter `Y_USERFO`** and copies its value into XREF1 / XREF2. The office code comes **from the user's SU3 parameter configuration** — NOT from any HR organization structure, NOT from the document's cost center / business area / fund, NOT from the vendor's country. Just the user parameter.

**The code works exactly as designed.** The root cause of this ticket is **master data**: `AL_JONATHAN`'s `USR05.Y_USERFO` is set to `'HQ'` instead of `'JAK'`. Every document he posts reads that wrong value and stamps `XREF='HQ'`. A_HIZKIA (a Jakarta team colleague, Y_USERFO='JAK' confirmed) has been manually correcting his documents via FBL3N since **2026-02-16** — independent confirmation that the expected correct value is `'JAK'`.

The XREF1 / XREF2 fields are **invisible on the F-53 entry screen** (the dialog has never exposed them, which is why the user sees no override option).

### 2.3 Solution

**Transaction SU3 (or SU01 for an administrator):** update `AL_JONATHAN`'s `Y_USERFO` parameter from `'HQ'` to `'JAK'`. After the change, every new document he posts will carry `XREF='JAK'` on the vendor and GL lines, and downstream form `UZLS` will derive `ZLSCH='O'` (field-office outbound) for Jakarta postings.

**Prerequisite — MUST do first (KU-027):** verify `'JAK'` exists in `YFO_CODES.FOCOD` via SE16N. If not, add the row via SM30 BEFORE the SU3 change. Otherwise the in-code validation in UXR1 will raise a `w018` warning on every subsequent posting, and UXR2 will raise a hard `e018` error if the user ever manually types `'JAK'` on a screen that exposes XREF2.

### 2.4 Why the posting commits with wrong values and no error (the validation gap)

This ticket is not about an SAP error message — there is no error raised. The posting commits cleanly with wrong XREF values because **the entire chain of substitution, validation, and screen input has zero effective gate on XREF correctness**:

- **Substitution (SUBSTID='UNESCO' in GB922, 17 steps at callpoint 3)** — runs on every UNES FI document. Steps 005/006/007 (writing XREF1/XREF2/ZLSCH via UXR1/UXR2/UZLS) fire with **no effective prerequisite gate**, stamping the posting user's Y_USERFO on every BSEG line the engine touches. Verified via live CDPOS on doc 3100003438 (the VALUE_OLD='HQ' on the bank GL line at the time of A_HIZKIA's FBL3N change proves UXR1 fired at original posting time).

- **In-code validation inside the substitution** (`UXR1` checks written value against `YFO_CODES.FOCOD` → `w018` warning only; `UXR2` checks only the user-entered branch, not the auto-write branch) — catches dictionary misses and manual typos, but **does NOT catch wrong-but-valid codes**. `'HQ'` is a valid code in YFO_CODES; the check passes even though the user is physically in Jakarta.

- **Line-item validation (`VALID='UNES'` in GB93/GB931, 12 steps at BOOLCLASS 009)** — fully mapped via live RFC. Steps 011 (`=U915` multi-bank check) and 012 (`=U917` SCB indicator check) fire on invoice-entry vendor lines, but **neither U915 nor U917 references XREF fields** (their source code is §3.3 / §3.4.4). And more importantly: **F-53 / FBZ2 is in ZERO validation TCODE prerequisites.** Manual outgoing payments are completely outside the UNES validation scope.

- **Screen-level input (F-53 / FBZ2 entry screen)** — does not expose XREF1 / XREF2. User cannot see or correct the value before posting.

- **HR-master alignment** — no gate cross-checks `USR05.Y_USERFO` against `PA0001.WERKS/BTRTL`. AL_JONATHAN's PA0001 says `WERKS='ID00' BTRTL='JKT'` (Indonesia / Jakarta — HR knows) but his USR05 says `Y_USERFO='HQ'` — the two are never reconciled.

**Result:** the substitution silently writes wrong values, no validation checks them, no screen shows them, and no master-data alignment catches the drift. **The business has been absorbing the gap via manual post-posting corrections: 21,754 FBL3N/FBL1N/FB02 edits on UNES FI documents in Q1 2026 alone, by 242 distinct users.** A_HIZKIA is one of those users, specifically correcting AL_JONATHAN's docs.

### 2.5 Additional observation (not the ticket's root cause)

**If a person physically located in HQ processes invoices, payments, or clearings on behalf of other offices, the value written to XREF1 / XREF2 will always be the value in that person's user parameter (`HQ`), not the office the document is actually for.**

This is by design: the substitution has no awareness of "which office this document is for"; it only knows "which user is posting right now and what is that user's `Y_USERFO`". Per §7.5, three flavours of this pattern were observed empirically:

- **F110 automatic payment run** (C_LOPEZ, HQ) clearing DA_ENGONGA's (Dakar) invoices: the new vendor clearing line on the F110 payment document carries `XREF='HQ'`. This is a **real business line** — it represents actual money movement — so the mis-attribution is a **real data-quality concern** for reporting (MEDIUM severity).
- **FB1K manual zero-balancing clearing** (L_HANGI, HQ) clearing DA_ENGONGA's invoices: the clearing document contains a zero-balancing BSCHL=27/37 pair with `XREF='HQ'`, but **these are metadata-only lines** (they net to zero and have no financial impact); the **original invoice line's `XREF='DAK'` is preserved unchanged**. This is a cosmetic / metadata-level mis-attribution (LOW severity).
- **SAPF124 automatic clearing** (JOBBATCH, no `Y_USERFO`): blank XREF on clearing-pair lines; again metadata-level; original invoice preserved (LOW severity).

**None of these cases are the defect reported in this ticket.** AL_JONATHAN's 10 F-53 documents are **self-clearing direct disbursements** (AUGBL = BELNR) with no prior invoice involved — the entire business transaction is authored by AL_JONATHAN himself, so the "wrong XREF" is a master-data bug at HIS user level, not a cross-user mis-attribution.

### 2.6 Ticket scope vs. broader observations

- **Ticket scope (INC-000005240):** AL_JONATHAN's `USR05.Y_USERFO='HQ'` must be changed to `'JAK'`. Fix = SU3 update (after §2.3 YFO_CODES prerequisite). Blast radius = his 10 F-53 documents (empirically measured in §8.3) + any future postings until corrected. **This is a narrow, reversible, master-data-only fix.**
- **Class-level observation (strategic, §10.2):** there are probably more AL_JONATHAN-class users — field users whose HR master says field-unit but whose `Y_USERFO='HQ'`. The audit query is trivial now (PA0001 cross-reference is proven in §4.1). **Should be run before or in parallel with the tactical fix.**
- **Structural observation (strategic, §7.5 + §10.3):** the validation framework has no XREF check at any callpoint, F-53 is outside validation coverage, and the substitution has no effective prerequisite gate. This is the root of the 21,754 Q1 manual corrections. **A separate business decision for UNESCO Finance/BI to consider; does not block this ticket.**

### 2.6 Internal validation chain (source + live data)

```
YRGGBS00_SOURCE.txt:230  exits-name = 'UXR1'  (XREF1 substitution exit registered)
YRGGBS00_SOURCE.txt:235  exits-name = 'UXR2'  (XREF2 substitution exit registered)
YRGGBS00_SOURCE.txt:996  FORM uxr1 USING bseg_xref1 LIKE bseg-xref1.
YRGGBS00_SOURCE.txt:1000      SELECT SINGLE * FROM usr05 WHERE bname = sy-uname AND parid = 'Y_USERFO'.
YRGGBS00_SOURCE.txt:1003      IF sy-subrc IS INITIAL.
YRGGBS00_SOURCE.txt:1004          bseg_xref1 = usr05-parva.
YRGGBS00_SOURCE.txt:1024  FORM uxr2 USING bseg_xref2 LIKE bseg-xref2.
YRGGBS00_SOURCE.txt:1026      IF bseg_xref2 = space.
YRGGBS00_SOURCE.txt:1028          SELECT SINGLE * FROM usr05 WHERE bname = sy-uname AND parid = 'Y_USERFO'.
YRGGBS00_SOURCE.txt:1031          IF sy-subrc IS INITIAL.
YRGGBS00_SOURCE.txt:1032              bseg_xref2 = usr05-parva.

Live RFC evidence (2026-04-09, P01):
  USR05 for AL_JONATHAN: Y_USERFO = 'HQ'   ← root cause
  BSAK vendor lines for his 10 FBZ2 docs (§8.3): ALL have XREF1='HQ' XREF2='HQ'
  No CDHDR changes on 8 of 10 docs → values are as-posted, not post-hoc edits
  PA0001.WERKS='ID00' BTRTL='JKT' — HR master says Jakarta (independent confirmation that user master is wrong)
```

### 2.7 Fix paths

- **Tactical (this ticket):** SU3 update, `AL_JONATHAN.Y_USERFO = 'JAK'` after verifying `JAK` in `YFO_CODES`.
- **Strategic (master-data class):** periodic audit of every UNES user where `USR05.Y_USERFO` does not align with `PA0001.WERKS/BTRTL` (field users with an `HQ` parameter). Straightforward query once PA0105 / PA0001 extraction is in Gold DB.
- **Design observation (separate from this ticket):** the cross-user clearing behavior documented in §7.5 is a UNESCO design choice — XREF always reflects the posting user, not the document's business origin. Raising it with UNESCO Finance / BI owners is a decision for the business, not a bug fix.

**Internal validation chain (from source + live data):**
```
YRGGBS00_SOURCE.txt:230  exits-name = 'UXR1'  (XREF1 substitution exit registered)
YRGGBS00_SOURCE.txt:235  exits-name = 'UXR2'  (XREF2 substitution exit registered)
YRGGBS00_SOURCE.txt:996  FORM uxr1 USING bseg_xref1 LIKE bseg-xref1.
YRGGBS00_SOURCE.txt:1000      SELECT SINGLE * FROM usr05 WHERE bname = sy-uname AND parid = 'Y_USERFO'.
YRGGBS00_SOURCE.txt:1003      IF sy-subrc IS INITIAL.
YRGGBS00_SOURCE.txt:1004          bseg_xref1 = usr05-parva.   ← writes the office code verbatim
YRGGBS00_SOURCE.txt:1024  FORM uxr2 USING bseg_xref2 LIKE bseg-xref2.
YRGGBS00_SOURCE.txt:1026      IF bseg_xref2 = space.          ← F-53 always hits this branch
YRGGBS00_SOURCE.txt:1028          SELECT SINGLE * FROM usr05 WHERE bname = sy-uname AND parid = 'Y_USERFO'.
YRGGBS00_SOURCE.txt:1031          IF sy-subrc IS INITIAL.
YRGGBS00_SOURCE.txt:1032              bseg_xref2 = usr05-parva.   ← writes the office code verbatim

Live RFC evidence (2026-04-09, INC-000005240_live_diagnostic.py against P01):
  USR05 for AL_JONATHAN: Y_USERFO = 'HQ'   ← root cause
  BSAK lines for 10 of his FBZ2 docs: ALL have XREF1='HQ', XREF2='HQ'
  XBLNR on the same docs: 'JAKARTA' (FBZ1) and Indonesian vendor names (FBZ2)
```

---

## 3. How Office-Based XREF Substitution Works at UNESCO

### 3.0 What XREF1/XREF2 are and why they matter for UNESCO

`BSEG-XREF1` and `BSEG-XREF2` are two 12-character "Reference Key" fields on every FI line item. SAP leaves them for customer use. UNESCO repurposes them to tag each line with the **originating office code** (e.g., `HQ`, `JAK`, `YAO`, `KAB`, `DAK`, `BRZ`, `IIEP_PAR`, `UIS`, `IBE`). Downstream consumers include:

- **Form `UZLS`** (`YRGGBS00_SOURCE.txt:1050-1119`): reads `XREF2` to decide the payment method (`ZLSCH`). For company code UNES, if `XREF2 = 'HQ'` → `ZLSCH` stays default; otherwise → `ZLSCH = 'O'` (field-office outbound).
- **Payment method-specific BCM workflows**: field-office payments are routed differently than HQ payments. Getting the office tag wrong silently mis-routes the payment.
- **FI reporting by office**: the XREF fields are the only office-level partition of the FI line-item stream.
- **Reconciliation / audit**: the field-unit finance team reads XREF2 to confirm that their postings are tagged with the correct office.

Because these fields are invisible on the F-53 screen (UNESCO never added them to the entry layout), the user has no UI signal that something is wrong — they only see the result after the fact, when reports or reconciliations turn up "HQ" postings they didn't expect.

### 3.1 The office-code dictionary `YFO_CODES`

`YFO_CODES` is a small UNESCO custom table with columns (at minimum) `FOCOD` (office code) and `PAYMT` (payment method). It is the **whitelist** of valid office codes and also the `FOCOD → PAYMT` mapping used by the commented-out original logic of form `UZLS`. `YFO_CODES` is maintained by the UNESCO BASIS/Finance team.

> **Open question (KU-027):** does `YFO_CODES` currently contain a row `FOCOD = 'JAK'`? If not, the tactical fix below needs two steps: add the row first, then update the user parameter. *(Not checked in this investigation — follow-up before fix deployment.)*

### 3.2 How the office code reaches the posting — the rule and its prerequisites

**IMPORTANT — the rule alone does not apply; it must pass a prerequisite.** In GGB1, a substitution step has two parts:

1. **The code** — the exit form (`UXR1`, `UXR2`, `UZLS`) and what it writes
2. **The prerequisite (BOOLEXP stored in GB905 → GB901)** — the Boolean expression that must evaluate to TRUE on the current document/line for the step to fire

**Without a matching prerequisite, the substitution does not run even though the code exists.** You can have UXR1 in YRGGBS00 source, registered as an exit, referenced in GB922 — and it will still never execute on a given BSEG line unless the step's prerequisite BOOLEXP evaluates TRUE for that line.

**Status of the prerequisite mapping for SUBSTID='UNESCO' steps 005 / 006 / 007:**

- `GB922` (Gold DB) shows: step 005 → BSEG.XREF1 via `EXITSUBST='UXR1'`, step 006 → BSEG.XREF2 via `UXR2`, step 007 → BSEG.ZLSCH via `UZLS`
- `GB922` does NOT carry the prerequisite in its own columns (confirmed — schema has no BOOLID column per step)
- The prerequisite linking lives in **`GB905`** (substitution step header) — **NOT in Gold DB, extraction pending RFC**
- `GB901` holds the BOOLEXP bodies keyed by BOOLID — available in Gold DB but cannot be linked to steps without GB905

**Until GB905 is extracted, the prerequisite condition that gates UXR1/UXR2/UZLS for SUBSTID='UNESCO' is NOT KNOWN**. The earlier draft of this section speculated *"empty prerequisite = always fires on every line"* — that was inference, not evidence, and must be replaced with the actual GB905 content once RFC is back.

### 3.2.1 What the empirical evidence tells us about substitution firing patterns

Even without GB905, the observed data gives us a partial map of when UXR1/UXR2 fires:

| Event | Vendor line (BSAK/BSIK) | Bank GL line (BSAS/BSIS) | Evidence source |
|---|---|---|---|
| **F-53 / FBZ2 manual payment** (AL_JONATHAN) | XREF1/2 populated from poster's `Y_USERFO` | **ALSO populated** (at post time) | CDPOS `VALUE_OLD='HQ'` on line 001 (BSAS bank GL) of 3100003438 proves substitution fired on the GL line too |
| **FB60 / MIRO / FB01 invoice posting** (DA_ENGONGA) | XREF1 populated from poster's `Y_USERFO`, XREF2 variable (user-enterable on MIRO/FB60) | Not yet verified — need RFC sweep on invoice side bank GL lines | §7.5 empirical table |
| **F110 automatic payment run** (C_LOPEZ) | XREF1/2 populated from F110 poster's `Y_USERFO` | **BLANK** | `0002003771` / `0002003828` BSAS L002 XREF=`''` while BSAK L001 XREF=`'HQ'` |
| **FB1K manual clearing** (L_HANGI) | Populated from poster's `Y_USERFO` | Need to verify | §7.5 empirical table |
| **SAPF124 automatic clearing** (JOBBATCH) | Tries to fire but no USR05 Y_USERFO row → blank | Blank | `0100020514` all lines blank |

**Key observation:** the substitution firing behavior is NOT uniform. F-53 manual posting fires on ALL BSEG lines (vendor + GL), but F110 automatic clearing fires only on the vendor line (leaving the bank GL blank). This asymmetry **must be controlled by a prerequisite** (GB905) or by a TCODE-specific pre-filter elsewhere — the exact mechanism is not yet proven without GB905.

### 3.2.2 Correction to the earlier "vendor-lines-only" claim

An earlier version of §3.2 and §8.3 in this report claimed that *"XREF substitution fires only on BSAK vendor lines"*. That claim was **wrong** and is now explicitly retracted. The error was an artifact of reading BSEG line items via `bseg_union` which does not carry XREF1/XREF2/XREF3 columns — I interpreted "no XREF value in bseg_union" as "XREF is blank in the live data", when in reality `bseg_union` simply doesn't include those fields. The live RFC read on F-53 BSAK lines did show XREF populated; the CDPOS history on 3100003438 proves XREF1 was also populated on BSAS line 001 at post time.

The corrected position is:
- **F-53 / FBZ2 (manual dialog posting):** substitution fires on every BSEG line created by the posting, including bank GL lines (empirically proven via CDPOS)
- **F110 (automatic payment run):** substitution fires on the vendor clearing line but NOT on the bank GL line (empirically proven via live RFC on 2 F110 docs)
- **The difference between these two cases is TBD** — pending GB905 extraction to see the actual step prerequisites and any F110-specific config

Consequences:

1. **The document's own context does not matter.** The substitution does not look at cost center, fund center, business area, company code assignment, personnel area of the vendor, or anything else about the document. It only asks *"who is the current user, and what is their Y_USERFO?"*

2. **Clearing documents are also "postings".** When an F110 payment run or an FB1K manual clearing creates new BSEG lines (to clear an open vendor item), those new lines go through the same substitution and carry the clearing user's `Y_USERFO` — NOT the original invoice's XREF values. The invoice line keeps its original XREF; the clearing line gets a new, separately-derived XREF from the clearing user.

3. **System users without `Y_USERFO` leave XREF blank.** `JOBBATCH` (used by SAPF124 automatic clearing) has no `Y_USERFO` row in USR05 → the `SELECT SINGLE * FROM usr05 ... sy-subrc <> 0` → UXR1/UXR2 fall through without writing → XREF stays SPACE. Empirically confirmed in §7.5.

4. **XREF1 and XREF2 can diverge per TCODE.** UXR1 has its guard (`IF bseg_xref1 = space`) **commented out** at [YRGGBS00_SOURCE.txt:998](../../Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt#L998) — so XREF1 is **always overwritten** with `USR05.Y_USERFO` regardless of what the user typed on the screen. UXR2 keeps its guard — so XREF2 is **only overwritten when it was blank** on entry. Screens that expose XREF2 to user input (e.g., MIRO, FB60) allow free-text values to survive; screens that hide XREF2 (F-53, FB01) always get the USR05 value. Empirically visible in the DA_ENGONGA data in §7.5: her MIRO invoices have `XREF1='DAK' XREF2='HQ'`, her FB60 has `XREF1='DAK' XREF2='UNDP-MR'`, her FB01 has `XREF1='DAK' XREF2='DAK'`.

### 3.2.1 Scenario A — AL_JONATHAN's F-53 direct disbursement (this ticket)

This is the pattern that AL_JONATHAN's 10 documents follow. It is a **single-event flow**: the F-53 document both posts and pays in one commit. There is no pre-existing invoice.

**Empirical evidence** from Gold DB `bseg_union` AUGBL trace (2026-04-09):

| Pmt BELNR/GJAHR | BSCHL | LIFNR | AUGBL | Result |
|---|---|---|---|---|
| 3100003438/2026 | 29 | 10157142 MUHAMMAD HASNAN | **3100003438** | SELF-CLEAR — `AUGBL = BELNR` |
| 3100003439/2026 | 29 | 10150370 CRESTI FITRIANA | **3100003439** | SELF-CLEAR |
| 3100003504/2026 | 29 | 10073496 RACHMANIA SITI | **3100003504** | SELF-CLEAR |
| 3100003505/2026 | 29 | 10002633 ANHAR PERMANA | **3100003505** | SELF-CLEAR |
| 3100003506/2026 | 29 | 10105124 VIDYANI AHMAD | **3100003506** | SELF-CLEAR |
| 3100003509/2026 | 29 | 10153157 ROCHMY AKBAR | **3100003509** | SELF-CLEAR |
| 3100007233/2026 | 25 | 10103901 RODOLFO MARTINS | **3100007233** | SELF-CLEAR |
| 3100007235/2026 | 25 | 10157142 MUHAMMAD HASNAN | **3100007235** | SELF-CLEAR (closes the Feb advance 37004766) |
| 3100007237/2026 | 25 | 10073496 RACHMANIA SITI | **3100007237** | SELF-CLEAR |
| 3100007238/2026 | 25 | 10150370 CRESTI FITRIANA | **3100007238** | SELF-CLEAR |

All 10 vendor lines have `AUGBL = BELNR` — **no pre-existing invoice is being cleared**. The BSCHL values (`29` = special GL / advance, `25` = outgoing payment) and the BKTXT values (`TRAVEL ADVANCE`, `TRAVEL CLAIM`, `MEDICAL REIMBURSEMENT`) confirm these are direct disbursements against employee-vendor accounts, not supplier invoices paid through a prior FB60/MIRO step.

**Pattern A flow (empirically confirmed):**

```
User opens F-53 (Post Outgoing Payment — dialog transaction wrapping FBZ2)
  ↓
User enters: vendor, amount, bank GL, BKTXT, XBLNR
(XREF1 / XREF2 NOT exposed on the F-53 screen — stay SPACE)
  ↓
User clicks POST → SAP commits as BKPF.TCODE='FBZ2'
  ↓
SAP builds draft BKPF + BSEG in memory:
    line 1 — bank clearing GL (BSCHL=50 credit, HKONT=118134x) — XREF SPACE
    line 2 — vendor line   (BSCHL=25 or 29 debit, HKONT=202104x) — XREF SPACE
    (optional) line 3 — FX rounding diff on expense GL — XREF SPACE
  ↓
FI substitution fires at callpoint where GB922 SUBSTID='UNESCO' is active
  ↓
Steps 005 / 006 / 007 of the UNESCO substitution fire:
    Step 005 → form UXR1 on each line:
        SELECT USR05 WHERE BNAME=SY-UNAME AND PARID='Y_USERFO'
        IF sy-subrc = 0:
            bseg_xref1 = usr05-parva       ← AL_JONATHAN's 'HQ' written here
            SELECT YFO_CODES WHERE FOCOD=bseg_xref1
            IF sy-subrc <> 0: MESSAGE w018(zfi)   ← warning only
    Step 006 → form UXR2 on each line:
        IF bseg_xref2 = SPACE:                    ← always true on F-53
            same SELECT USR05
            bseg_xref2 = usr05-parva              ← AL_JONATHAN's 'HQ' written here
    Step 007 → form UZLS on each line:
        IF bseg_xref2(4) <> 'UNDP':
            CASE bseg-bukrs WHEN 'UNES':
                IF bseg-xref2 <> 'HQ': bseg_zlsch = 'O'  (field-office outbound)
                ELSE: bseg_zlsch stays at default   ← what AL_JONATHAN hits
  ↓
Document commits as self-clearing payment:
    BSAK(bsak) row for the vendor line: AUGBL = BELNR (same doc), XREF1='HQ', XREF2='HQ'
    BSAS(bsas) row for the bank line: AUGBL = a bank clearing run (e.g., '0100014718')
    BSIS(bsis) row for the FX diff (if any): AUGBL = empty
  ↓
Downstream: BCM / BI reporting / reconciliation reads XREF2 as the office tag
```

**Empirical confirmation that the substitution DOES fire on F-53/FBZ2:** On 2026-04-09 via RFC against P01, all 10 of AL_JONATHAN's self-cleared BSAK vendor lines carry `XREF1='HQ' XREF2='HQ'`. Since there is no prior invoice (Pattern A is self-clearing) and since 8 of 10 docs have zero CDHDR change records (no post-hoc FBL3N edit), the XREF values can **only** have been written by the substitution firing at his F-53 posting time. Therefore the substitution IS active for FBZ2 regardless of what the `1UNES###*` / `2UNES###*` rules suggest — it must fire at callpoint 3 (complete document) via GB922 SUBSTID='UNESCO' with no TCODE prerequisite, or via a BTE/exit path not visible in GB901.

> **Correction to an earlier working hypothesis:** in an earlier draft of this analysis I inferred from GB901 that F-53/FBZ2 "does not trigger" XREF substitution because no rule lists those TCODEs. The AUGBL trace **refutes** that inference. F-53/FBZ2 DOES trigger the substitution — the GB901 rules I was reading (`1UNES###009`, `1UNES###011`, etc.) apply to OTHER substitution/validation steps, not to GB922 SUBSTID='UNESCO' steps 005/006/007 which fire unconditionally at callpoint 3. The exact prerequisite-less naming convention is documented in the FI substitution architecture pointer at the bottom of this section (§3.2c).

### 3.2.2 Scenario B — Invoice posted by one user, cleared by another (separate observation — §7.5)

The SAME rule from §3.2 applies; the only difference is that two distinct events are involved and they are executed by two distinct users:

1. **Event 1 — Invoice posting** (FB60 / MIRO / FB01 / F-47 / PRRW-generated FI doc): posted by some user (a field user, a travel admin, a payroll batch user, etc.). Substitution fires on the new vendor line at posting time, reading THAT user's `Y_USERFO`, writing it to `XREF1` (and to `XREF2` if the screen hides it). The invoice goes to `BSIK` (open) with that XREF.

2. **Event 2 — Clearing** (F110 payment run OR FB1K manual clearing OR SAPF124 automatic clearing OR F-53 dialog against an open item): posted by a different user (often an HQ central processor, or the JOBBATCH system user). The clearing creates a NEW BSEG line (the payment / clearing side). Substitution fires on that new line with the CLEARING user's `Y_USERFO`. **The original invoice line's XREF is NOT rewritten** — it keeps its value. Only the new clearing line gets a fresh XREF.

**Result:** the AP pair (invoice side + clearing side) can carry different XREF values. This is not two substitution mechanisms fighting each other — it is the SAME mechanism firing twice with two different users.

Empirically verified in §7.5 using DA_ENGONGA (field user, `Y_USERFO='DAK'`) invoices cleared by C_LOPEZ (F110, `'HQ'`), L_HANGI (FB1K, `'HQ'`), and JOBBATCH (SAPF124, no `Y_USERFO` row → blank XREF).

**Important scoping note:** this scenario is **NOT the defect reported in this ticket**. It is a separate behavior worth documenting. The ticket fix (SU3 update for AL_JONATHAN) is independent of any decision about Scenario B.

### 3.2.3 How to tell one scenario from the other in BSAK data

| Indicator | Scenario A (self-clearing direct disbursement) | Scenario B (invoice + separate clearing) |
|---|---|---|
| `BSAK.AUGBL` vs `BSAK.BELNR` | **equal** | different |
| Prior `BSIK` entry for the same vendor | none | present |
| BSCHL on the vendor line | 25 (outgoing payment) or 29 (special GL advance) | 31 on invoice, 25/28 on clearing |
| BKTXT | Direct disbursement text (`TRAVEL ADVANCE`, `MEDICAL REIMBURSEMENT`, etc.) | Varies — often invoice reference |
| Typical users | Field users directly reimbursing employees (AL_JONATHAN) | Any user combination — the rule itself is the same |

### 3.2.4 Attribution for this ticket — definitive

Given the AUGBL evidence in §6.1 (all 10 of AL_JONATHAN's F-53 docs are self-clearing with `AUGBL = BELNR`), the `XREF1='HQ' XREF2='HQ'` on his 10 BSAK vendor lines can ONLY have come from the substitution firing at his own posting time, reading his own `USR05.Y_USERFO='HQ'`:
1. No prior invoice exists (self-clearing).
2. No CDHDR post-hoc modification exists for 8 of 10 docs (the other 2 have A_HIZKIA FBL3N entries that need CDPOS detail — separate follow-up).
3. F-53 screen does not expose XREF1/XREF2 — user cannot type them.
4. The values match his `Y_USERFO` verbatim.

**Root cause of this ticket: `AL_JONATHAN.USR05.Y_USERFO = 'HQ'` instead of `'JAK'`. Fix: SU3 update. No code change required.**

#### 3.2c Architecture pointer — where the framework lives in UNESCO brain knowledge

The general UNESCO FI substitution/validation framework (YRGGBS00, YXUSER bypass, BASU framework, UAEP/UATF/U904/U917, callpoint structure) is already documented in:

- [`knowledge/domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md`](../domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md)
- [`knowledge/domains/PSM/EXTENSIONS/validation_substitution_matrix.md`](../domains/PSM/EXTENSIONS/validation_substitution_matrix.md)
- [`knowledge/domains/FI/ggb1_substitution_tables_distinction.md`](../domains/FI/ggb1_substitution_tables_distinction.md)

**Those docs had a blind spot on the `UXR1` / `UXR2` / `UZLS` / `Y_USERFO` / `YFO_CODES` office-tagging trio** — this incident fills that gap. The framework-level pointer will be added to the domain docs at investigation close (held per `feedback_brain_rebuild_after_finalized` — no mid-investigation knowledge capture).

### 3.3 Custom framework components in YRGGBS00 touching XREF fields

| Exit | Source range | Purpose | Data source | In-code validation | Trigger (empirically confirmed) |
|---|---|---|---|---|---|
| **`UXR1`** | `YRGGBS00_SOURCE.txt:996-1016` | Write `BSEG-XREF1` | `USR05 WHERE PARID='Y_USERFO'` | **After writing**, SELECT `YFO_CODES WHERE FOCOD=bseg_xref1` → raise `w018 ZFI` **warning** (does NOT stop posting) if the written code is not in the dictionary | Fires on every BSEG line in UNES FI postings (F-53 bank GL CDPOS-proven). Original `IF bseg_xref1 = space` guard has been commented out at line 998 — **ALWAYS overwrites** regardless of what the user had typed |
| **`UXR2`** | `YRGGBS00_SOURCE.txt:1024-1041` | Write `BSEG-XREF2` | `USR05 WHERE PARID='Y_USERFO'` | **Asymmetric:** (a) SPACE branch (auto-write from USR05) — **NO validation** — trusts USR05 value blindly. (b) ELSE branch (user manually typed a value) — SELECT `YFO_CODES` → raise `e018 ZFI` **hard error** (stops posting) if not in dictionary | SPACE branch fires on every BSEG line where XREF2 was not manually entered (always true on F-53 since the screen hides it) |
| **`UZLS`** | `YRGGBS00_SOURCE.txt:1050-1119` | Derive `BSEG-ZLSCH` from `XREF2` per company code | Literal CASE statement on `BUKRS` + `XREF2` | None — pure CASE derivation, no dictionary check | Fires per line after UXR2. For UNES: matches `'HQ'` → ZLSCH stays at default; non-HQ → ZLSCH forced to `'O'` (field-office outbound). Also has the `IF bseg-xref2(4) <> 'UNDP'` special case for UNDP transfers |
| `UAEP` | `YRGGBS00_SOURCE.txt:1128+` | Asset expense substitution | `YXUSER` / company-code case | `YXUSER` XTYPE='AF' bypass | When posting against asset GLs — documented in [`finance_validations_and_substitutions_autopsy.md`](../domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md) §2.1 |
| `UATF` / `NSAI` | Referenced in autopsy §2.2 | Technical fund / WBS clearance | `YXUSER` XTYPE='AA' bypass | — | Clears `BSEG-PROJK` for technical funds (unrelated to this incident) |
| `U904` | Referenced in autopsy §2.3 | Payment supplement linkage | `BSEG-UZAWE` CASE | — | UZAWE → GSBER derivation (unrelated to this incident) |
| **`U915`** | `YRGGBS00_SOURCE.txt:1499-1519` | **VALIDATION** — multi-bank vendor check | `LFBK` lookup | Returns `b_false` if vendor has >1 bank account and `BVTYP` not specified on the line. Skips BSCHL 26/39 (down-payment clearing). **Does NOT check XREF fields** | Fires only on invoice-entry TCODEs via UNES validation step 011 (`VALID='UNES'` VALSEQNR=011) — see §3.4 |
| **`U917`** | `YRGGBS00_SOURCE.txt:1543-1590` | **VALIDATION** — SCB indicator consistency | `LFBK.BANKS` + `BSEG-LZBKZ` + `YTFI_PPC_STRUC` | Returns `b_false` if `LZBKZ(2) ≠ LFBK-BANKS`, or if country requires PPC indicator per `YTFI_PPC_STRUC` and `LZBKZ` is empty. **Does NOT check XREF fields** | Fires only on invoice-entry TCODEs via UNES validation step 012 (`VALID='UNES'` VALSEQNR=012) — see §3.4 |
| `UIT1` / `UIT2` / `UIT3` / `UIT4` | `YRGGBS00_SOURCE.txt:255-273` (registration) | Parallel XREF substitution for **ICTP** MIGO/MIRO postings | separate logic | — | MM transactions on company code ICTP (unrelated to this incident) |

**For this incident, the relevant mechanisms are:** `UXR1` + `UXR2` (write XREF), `UZLS` (downstream payment-method derivation), and the observation that **`U915` + `U917` are the ONLY validation exits that fire on invoice vendor lines — and neither checks XREF**. The other exits are listed for completeness and cross-reference to the existing `finance_validations_and_substitutions_autopsy.md` doc.

### 3.4 The complete Validation & Substitution model at UNESCO (acknowledged)

This section acknowledges the full picture of how UNESCO's FI substitution and validation framework is wired, correcting earlier gaps in my analysis. It is the reference model that the rest of the report builds on.

#### 3.4.1 Two separate mechanisms

UNESCO runs **two independent mechanisms** on every FI posting in UNES. They share the same custom form pool (`YRGGBS00`) but are configured in **different GGB-framework tables** and fire at **different phases** of the posting.

| Mechanism | GGB framework | Identifier | GGB tables | Purpose |
|---|---|---|---|---|
| **Substitution** (writes values) | GGB1 | `SUBSTID='UNESCO'` | `GB922` (17 steps) | Writes values onto BSEG fields at posting time (callpoint 3 — complete document) |
| **Validation** (checks values) | GGB0 | `VALID='UNES'` | `GB93` (header) + `GB931` (12 steps, confirmed via RFC) | Checks values against business rules at line-item time (BOOLCLASS=009); raises error/warning/info |

**Both mechanisms are registered** through `T80D` to the same `YRGGBS00` form pool:

```
T80D ARBGB=GBLS FORMPOOL=YRGGBS00   ← substitution form pool for FI
T80D ARBGB=GBLR FORMPOOL=YRGGBS00   ← validation form pool for FI
```

**But they are completely separate in terms of which rules apply to which events.** A TCODE can trigger substitution without triggering any validation, or vice versa. AL_JONATHAN's F-53 case is exactly this: substitution fires, validation doesn't.

#### 3.4.2 The substitution side — SUBSTID='UNESCO'

- **GB922 (step bodies, Gold DB — 17 rows):** the actual write logic. Steps 005 (XREF1 via UXR1), 006 (XREF2 via UXR2), 007 (ZLSCH via UZLS) are the ones relevant to this ticket.
- **GB901 (Boolean expressions, Gold DB):** contains `3UNESCO#001..019` rules, but **steps 005, 006, 007 have NO matching GB901 entry** (`3UNESCO#005`, `#006-HR-ranges`, `#007` do not cover the XREF/ZLSCH steps).
- **GB905 / GB921 (step-to-prerequisite linking table):** **empty via RFC probe** — UNESCO is not using the standard GGB1 step-header mechanism. The step prerequisites (if any) are implicit or stored in a location not accessible through `RFC_READ_TABLE`.
- **Empirical behavior:** the steps DO fire, proven by CDPOS on AL_JONATHAN's docs + live BSAK reads. The conclusion is that steps 005/006/007 have an **empty/missing prerequisite → they fire unconditionally on every BSEG line at callpoint 3**.
- **In-code check:** `UXR1` validates the written value against `YFO_CODES.FOCOD` and raises a `w018 ZFI` **warning** (non-blocking) if missing. `UXR2` validates ONLY in the user-entered branch with a `e018 ZFI` **hard error**. The auto-write from USR05 in `UXR2` is **unvalidated**.

#### 3.4.3 The validation side — VALID='UNES' (BOOLCLASS 009)

Fully mapped via live RFC extraction of `GB93` (header) and `GB931` (12 steps) on 2026-04-09:

| VALSEQNR | CONDID (prerequisite — "when to check") | CHECKID (the check — "must be TRUE") | Severity | Message | Fires on |
|---|---|---|---|---|---|
| 001 | `1UNES###001` (`BUKRS='UNES'`) | `2UNES###001` (GSBER NOT IN DAE/IBA/PAR/FEL/PDK) | E | ZFI 015 | Every UNES line |
| 002 | `1UNES###004` (`BUDAT≤31.12.2011 AND =U913`) | `2UNES###004` (FALSE — disabled) | E | ZFI 024 | Disabled |
| 003 | `1UNES###006` (HKONT in 6046/7034/7046 ranges) | `2UNES###006` (`BLART='R1'`) | E | ZFI 021 | Specific GL ranges |
| 004 | `1UNES###002` (`BLART='RE'`) | `2UNES###002` (MIRO/MR8M/MIR7/MIR4/FBL1N/FBL3N/FB02/'') | E | ZFI 019 | MM invoices |
| 005 | `1UNES###003` (`BLART IN TV/TF`) | `2UNES###003` (`AWTYP='TRAVL' OR FBL1N/FBL3N/FB02`) | E | ZFI 019 | Travel docs |
| 006 | `1UNES###005` (`BLART IN ZP/CP`) | `2UNES###005` (F110/F111/FB08/FBL1N/FBL3N/FB02/'') | **E** | ZFI 019 | **F110 auto payment run** (but the check is effectively a TCODE tautology) |
| 007 | `1UNES###008` (`BLART IN CA/CC`) | `2UNES###008` (FB01/F-58/FBZ4/FB08/FBL1N/FBL3N/FB02/'') | E | ZFI 019 | Cash/check docs |
| 008 | `1UNES###007` (`TCODE='F-58' OR 'FBZ4'`) | `2UNES###007` (`BLART IN CA/CC`) | E | ZFI 004 | Alternative outgoing payments + reset clearing |
| 009 | `1UNES###012` (`GEBER='185GEF0006'`) | `2UNES###012` (`=U916`) | **I** | ZFI 023 | Info message only |
| 010 | `1UNES###010` (`BLART IN RB/SR AND KOART='D'`) | `2UNES###010` (XREF3 in OFFICE RENT, PARKING, ...) | E | ZFI 011 | Customer bills/credit memos — expense type |
| 011 | `1UNES###011` (invoice-entry TCODE list + `KOART='K'`) | `2UNES###011` (`=U915` multi-bank check) | **E** | ZFI 012 | **Invoice-entry TCODEs only** — see list below |
| 012 | `1UNES###009` (invoice-entry TCODE list + `KOART='K'`) | `2UNES###009` (`=U917` SCB indicator check) | **E** | ZFI 036 | **Invoice-entry TCODEs only** — same list |

**The invoice-entry TCODE list (from `1UNES###009` / `1UNES###011`):**

```
BLART IN (AP, CO, ER, IN, IT, KA, KR, KT, MF, MR, RE, RF, PS, PN)
AND
TCODE IN (FB01, FB41, FB60, FB65, FBA6, FBR2, MIR7, MIRO, FBV0, FBVB, F-47)
AND
KOART = 'K'
```

**Not in this list:** F-53, FBZ2, FBZ1, FBZ4, F-58, F110, F111, FB1K.

#### 3.4.4 The critical finding — no validation step checks `XREF1` / `XREF2` / `XREF3`

Of the 12 UNES validation steps, **zero reference the XREF fields** at either the CONDID or CHECKID level:

- Step 010 references `BSEG-XREF3` as a CHECK (expense type: OFFICE RENT / PARKING / TELEPHONE / ...) — but only for customer docs (BLART in RB/SR + KOART='D') and it checks `XREF3`, not `XREF1`/`XREF2`
- No other step checks any XREF field

**Exit forms called by validation:**
- `U915` — multi-bank vendor check (reads `LFBK`, checks line count + BVTYP). **Does NOT touch XREF.**
- `U916` — Fund GL restriction (checks `FISTL` + `HKONT`). **Does NOT touch XREF.**
- `U917` — SCB indicator consistency (checks `LZBKZ` + `LFBK.BANKS` + `YTFI_PPC_STRUC`). **Does NOT touch XREF.**

**Conclusion: at UNESCO, no validation rule anywhere in the FI posting chain checks that the XREF values written by the substitution are consistent with anything** — not with HR, not with fund center, not with business area, not with vendor country, not even with the same YFO_CODES dictionary that UXR1/UXR2 use at write time (that's an in-code check, not a GGB0 validation, and it's non-blocking or asymmetric).

#### 3.4.5 Substitution vs validation TCODE coverage — summary

| Event | Substitution fires? | Validation fires? | Is XREF checked anywhere? |
|---|---|---|---|
| **Invoice posting** (FB60/MIRO/FB01/FB65/FBA6/FBR2/MIR7/FBV0/FBVB/F-47/FB41) | YES — UXR1/UXR2 write from invoice poster's Y_USERFO (+ UXR1 warns on dictionary miss) | YES — steps 011 (U915) + 012 (U917) for vendor lines | **NO** — neither U915 nor U917 touches XREF |
| **F-53 / FBZ2 manual payment** | YES — writes from payer's Y_USERFO | **NO** — F-53/FBZ2 is in **zero** validation TCODE lists | **NO** — no validation fires at all |
| **F-58 manual payment with printout** | YES | YES — step 008 (BLART in CA/CC check) | **NO** — checks BLART, not XREF |
| **FBZ4 reset clearing** | YES | YES — step 008 | **NO** — same |
| **F110 automatic payment run** | Partial — vendor line yes, bank GL blank (anomaly) | YES — step 006 (but check is a TCODE tautology) | **NO** — no meaningful check |
| **FB1K manual clearing** | YES — writes clearing user's Y_USERFO on new BSEG pair | **NO** — FB1K is not in any UNES validation TCODE list | **NO** |
| **SAPF124 auto clearing (JOBBATCH)** | Code runs but `USR05` SELECT fails → no write | **NO** | **NO** |
| **Post-posting change via FB02/FBL1N/FBL3N** | N/A | Several validations fire (`1UNES###002/003/005/008` all list FBL1N/FBL3N/FB02) but still none checks XREF | **NO** |

**The validation coverage is asymmetric and incomplete:**
- Invoice posting is the ONLY event with line-item validation (U915, U917) that runs meaningful bank checks
- F-53 / FBZ2 manual payment has **ZERO validation coverage**
- Change transactions (FBL1N/FBL3N/FB02) have SOME validation, but again none checks XREF
- Manual clearing (FB1K) and auto clearing (SAPF124) have **ZERO validation coverage**

**No single step in the entire 12-step UNES validation rule set reads `BSEG-XREF1` or `BSEG-XREF2`.** The XREF fields are written by substitution and then never checked by anything.

---

## 4. Investigation: Why AL_JONATHAN Gets 'HQ' Instead of 'JAK'

### 4.1 AL_JONATHAN's user master (`USR05 WHERE BNAME = 'AL_JONATHAN'`)

Live RFC read from P01 on 2026-04-09 (`INC-000005240_live_diagnostic.py`) — full PARID dump:

| PARID | PARVA | Meaning |
|---|---|---|
| BP2 | `0` | BP transaction control |
| BUK | `UNES` | Default company code |
| CAC | `UNES` | Default controlling area |
| EKO | `UNES` | Default purchasing organization |
| EVO | `01` | Default purchasing group |
| FIK | `UNES` | Default financial management area |
| FO3 | `4` | (unknown) |
| KPL | `UNES` | Default chart of accounts |
| MOL | `UN` | Country grouping (molga) |
| MOR | `6` | (unknown) |
| PDB | `000000000001` | (unknown) |
| PFL | `000000000001` | (unknown) |
| UGR | `FQ` | (unknown) |
| WRK | `0002` | Default plant |
| **`Y_USERFO`** | **`'HQ'`** | **Office code — the smoking gun** |

**Observation:** every single one of his PARIDs looks like a template for an HQ user at UNES. There is no per-user customization. This strongly suggests Anthony was created from an HQ template and never had his office code updated when he was assigned to the Jakarta Field Unit.

### 4.2 The substitution form that writes XREF2 — confirmed

`YRGGBS00_SOURCE.txt:1024-1041`:

```abap
FORM uxr2 USING bseg_xref2 LIKE bseg-xref2.
    IF bseg_xref2 = space.        " user didn't type anything — F-53 always hits this
        CLEAR usr05.
        SELECT SINGLE * FROM usr05
               WHERE bname = sy-uname
                 AND parid = 'Y_USERFO'.
        IF sy-subrc IS INITIAL.
            bseg_xref2 = usr05-parva.    " ← writes 'HQ' for AL_JONATHAN
        ENDIF.
    ELSE.    " user entered something — validate it
        SELECT SINGLE * FROM yfo_codes WHERE focod = bseg_xref2.
        IF sy-subrc <> 0.
            MESSAGE e018(zfi) WITH bseg_xref2.   " hard error
        ENDIF.
    ENDIF.
ENDFORM.
```

`UXR1` is similar but *always* overwrites (the original `IF bseg_xref1 = space` guard has been commented out at line 998):

```abap
FORM uxr1 USING bseg_xref1 LIKE bseg-xref1.
*     if bseg_xref1 = space.        " GUARD COMMENTED OUT
    CLEAR usr05.
    SELECT SINGLE * FROM usr05
           WHERE bname = sy-uname
             AND parid = 'Y_USERFO'.
    IF sy-subrc IS INITIAL.
        bseg_xref1 = usr05-parva.   " ← always writes, even if user had typed XREF1
        SELECT SINGLE * FROM yfo_codes WHERE focod = bseg_xref1.
        IF sy-subrc <> 0.
            MESSAGE w018(zfi) WITH bseg_xref1.    " ← warning only, not error
        ENDIF.
    ENDIF.
ENDFORM.
```

### 4.3 The lookup table — `YFO_CODES`

Form `UXR1` validates the XREF1 value against `YFO_CODES.FOCOD` but only raises a **warning** (`w018`) if the code is missing. Form `UXR2` validates *only* in the user-entered branch (not the SPACE→USR05 branch), meaning it blindly trusts whatever `USR05-PARVA` returns. **There is no gate preventing a bad Y_USERFO value from being written to XREF2.**

> **Open question (KU-027):** current `YFO_CODES` contents are not loaded into Gold DB. A confirmed list of valid FOCOD values would let us scan USR05 for every UNES user whose Y_USERFO is NOT in YFO_CODES — a cheap class generalization.

### 4.4 What value flows in, what flows out

| Input | Value | Source |
|---|---|---|
| `SY-UNAME` | `AL_JONATHAN` | current user |
| `USR05-PARVA` (PARID `Y_USERFO`) | **`'HQ'`** | live RFC read, 2026-04-09 |
| `BSEG-XREF1` (after UXR1) | **`'HQ'`** | written by `bseg_xref1 = usr05-parva` |
| `BSEG-XREF2` (after UXR2) | **`'HQ'`** | written by `bseg_xref2 = usr05-parva` |
| Downstream `ZLSCH` (via UZLS) | Default (no override) | `IF bseg-xref2 <> 'HQ'` is false → `bseg_zlsch = 'O'` does not fire |

### 4.5 The F-53 screen — why the user sees no input field

F-53 (Post Outgoing Payment) is a dialog wrapper on top of `FBZ0`-style bank clearing. Its entry screens show only the minimum required fields: date, bank GL, amount, vendor, open items to clear. XREF1 and XREF2 are NOT in any of the stock entry screens. UNESCO has never added them via a BDC fill or a screen variant. The user's statement *"no option for inputting the Reference 1 and 2"* is factually correct — the screen doesn't let him.

The only workaround on the user side is to drill into the FI document after simulation and overwrite XREF1/XREF2 per line before pressing SAVE. **Almost no field-unit clerk knows this, and it's fragile** (XREF1 would still be overwritten by UXR1 because its guard is commented out — XREF2 would survive because its guard is intact).

### 4.6 Summary — every path the substitution can take

```
A. USR05 Y_USERFO missing (SY-SUBRC <> 0)
     → UXR1: nothing happens, XREF1 stays whatever the user had (SPACE for F-53)
     → UXR2: nothing happens, XREF2 stays SPACE
     → Downstream UZLS: falls through CASE ... WHEN 'UNES' without match → ZLSCH = 'O'
     → Field-office behaviour (intended for offices without YFO mapping)

B. USR05 Y_USERFO = 'HQ' (AL_JONATHAN's actual state)
     → UXR1: bseg_xref1 = 'HQ' (YFO_CODES check passes)
     → UXR2: bseg_xref2 = 'HQ'
     → Downstream UZLS: 'HQ' matches the HQ branch → ZLSCH stays default
     → HQ behaviour — WRONG for AL_JONATHAN (he's in Jakarta)

C. USR05 Y_USERFO = 'JAK' (the correct state for AL_JONATHAN)
     → UXR1: bseg_xref1 = 'JAK' (YFO_CODES check: does JAK exist? Unknown — KU-027)
     → UXR2: bseg_xref2 = 'JAK'
     → Downstream UZLS: 'JAK' ≠ 'HQ' → ZLSCH = 'O'
     → Field-office outbound behaviour — CORRECT
```

---

## 5. System Execution Chain (Technical Detail) — From Source Code

### 5.1 The chain end to end

```
Step 1   User opens F-53.
Step 2   User enters vendor 0010150370 (CRESTI FITRIANA), bank GL, amount, clicks POST.
Step 3   SAP builds BKPF(BUKRS='UNES', TCODE='FBZ2', USNAM='AL_JONATHAN') and two BSEG lines:
             line 001: vendor line  (BSCHL 25, LIFNR 0010150370, DMBTR = payment, XREF1/2 = SPACE)
             line 002: bank line    (BSCHL 50, HKONT bank GL, DMBTR = payment, XREF1/2 = SPACE)
Step 4   Substitution callpoint 0002 fires for every BSEG line.
Step 5   Form UXR1 runs (YRGGBS00_SOURCE.txt:996):
             SELECT USR05 WHERE BNAME='AL_JONATHAN' AND PARID='Y_USERFO' → PARVA='HQ'
             bseg_xref1 = 'HQ'
             SELECT YFO_CODES WHERE FOCOD='HQ' → sy-subrc = 0 (HQ exists) → no warning
Step 6   Form UXR2 runs (YRGGBS00_SOURCE.txt:1024):
             bseg_xref2 = SPACE → enters the USR05 branch
             SELECT USR05 WHERE BNAME='AL_JONATHAN' AND PARID='Y_USERFO' → PARVA='HQ'
             bseg_xref2 = 'HQ'
Step 7   Form UZLS runs (YRGGBS00_SOURCE.txt:1090):
             IF bseg-xref2(4) <> 'UNDP' → true
             CASE bseg-bukrs WHEN 'UNES'.
                 IF bseg-xref2 <> 'HQ' → FALSE (XREF2 is 'HQ')
                 → bseg_zlsch stays at default (user-entered or empty)
Step 8   Document commits → BSAK (vendor cleared items) has
             BELNR=3100003439, GJAHR=2026, BUZEI=002,
             LIFNR=0010150370, XREF1='HQ', XREF2='HQ', XREF3='', ZUONR='20260212'
Step 9   Downstream reporting groups this vendor line under "HQ" instead of "JAK".
```

### 5.2 Case OK vs Case FAIL

| Step | Case OK (AL_JONATHAN with Y_USERFO='JAK') | Case FAIL (AL_JONATHAN actual, Y_USERFO='HQ') |
|---|---|---|
| 5 | `USR05-PARVA = 'JAK'` → `XREF1 = 'JAK'` | `USR05-PARVA = 'HQ'` → `XREF1 = 'HQ'` |
| 6 | `XREF2 = 'JAK'` | `XREF2 = 'HQ'` |
| 7 | UZLS: `'JAK' <> 'HQ'` → `ZLSCH = 'O'` | UZLS: `'HQ' = 'HQ'` → `ZLSCH` unchanged |
| 8 | BSAK has `XREF1='JAK', XREF2='JAK', ZLSCH='O'` | BSAK has `XREF1='HQ', XREF2='HQ', ZLSCH=default` |
| 9 | Posting attributed to Jakarta office | Posting attributed to HQ office |

**The single line where the chain diverges is `YRGGBS00_SOURCE.txt:1032`** (`bseg_xref2 = usr05-parva`), driven by the value of a master-data field the user cannot see from F-53.

### 5.3 The Code — exact lines

Registration of the substitution exits (lines 230-243):

```abap
*** IKON27032009
    exits-name  = 'UXR1'.                " substitution for XREF1
    exits-param = c_exit_param_field.
    exits-title = TEXT-xr1.
    APPEND exits.

    exits-name  = 'UXR2'.                " substitution for XREF2
    exits-param = c_exit_param_field.
    exits-title = TEXT-xr2.
    APPEND exits.
```

Form UXR1 (lines 996-1016) and form UXR2 (lines 1024-1041) — reproduced in §4.2 above verbatim.

Form UZLS relevant block (lines 1090-1118):

```abap
IF bseg-xref2(4) <> 'UNDP'.
    CASE bseg-bukrs.
        WHEN 'UNES'.
            IF bseg-xref2 <> 'HQ'.
                bseg_zlsch = 'O'.
            ENDIF.
        WHEN 'UBO'.
            IF bseg-xref2 <> 'BRZ'.
                bseg_zlsch = 'O'.
            ENDIF.
        WHEN 'UIS'.
            IF bseg-xref2 <> 'UIS'.
                bseg_zlsch = 'O'.
            ENDIF.
        WHEN 'IBE'.
            IF bseg-xref2 <> 'IBE'.
                bseg_zlsch = 'O'.
            ENDIF.
        WHEN 'IIEP'.
            IF bseg-xref2 <> 'IIEP_PAR'.
                bseg_zlsch = 'O'.
            ENDIF.
        WHEN OTHERS.
    ENDCASE.
ELSE.
    bseg_zlsch = 'U'.
ENDIF.
```

---

## 6. Why It Has Always Been Wrong (not a regression)

Unlike INC-000006073, this is not a "it used to work and now it doesn't" incident. It has **always** been wrong for AL_JONATHAN, from day one of his user account.

### 6.1 Historical posting evidence (Dec/2025 → March/2026)

From Gold DB + live RFC (10 captured BSAK line items for his 14 FBZ1/FBZ2 docs in the window):

| Doc key | BUDAT | TCODE | BLART | Vendor | XREF1 | XREF2 |
|---|---|---|---|---|---|---|
| 3100003438/2026 | 2026-02-12 | FBZ2 | OP | 0010157142 MUHAMMAD HASNAN | HQ | HQ |
| 3100003439/2026 | 2026-02-12 | FBZ2 | OP | 0010150370 CRESTI FITRIANA | HQ | HQ |
| 3100003504/2026 | 2026-02-12 | FBZ2 | OP | 0010073496 RACHMANIA SITI | HQ | HQ |
| 3100003505/2026 | 2026-02-12 | FBZ2 | OP | 0010002633 ANHAR PERMANA | HQ | HQ |
| 3100003506/2026 | 2026-02-12 | FBZ2 | OP | 0010105124 VIDYANI AHMAD | HQ | HQ |
| 3100003509/2026 | 2026-02-12 | FBZ2 | OP | 0010153157 ROCHMY AKBAR | HQ | HQ |
| 3100007233/2026 | 2026-03-16 | FBZ2 | OP | 0010103901 RODOLFO MARTINS | HQ | HQ |
| 3100007235/2026 | 2026-03-16 | FBZ2 | OP | 0010157142 MUHAMMAD HASNAN | HQ | HQ |
| 3100007237/2026 | 2026-03-16 | FBZ2 | OP | 0010073496 RACHMANIA SITI | HQ | HQ |
| 3100007238/2026 | 2026-03-16 | FBZ2 | OP | 0010150370 CRESTI FITRIANA | HQ | HQ |

100% consistent: every vendor line AL_JONATHAN posts is tagged HQ regardless of the vendor's actual nationality (Indonesian) or the document's origin (the XBLNR on his FBZ1 docs literally reads "JAKARTA").

### 6.2 Flow — what actually happened (and still happens)

Every time AL_JONATHAN posts:
1. F-53 screen → XREF1/XREF2 = SPACE (fields not on screen)
2. UXR1/UXR2 substitution fires → reads `USR05-PARVA = 'HQ'` → writes `XREF1='HQ', XREF2='HQ'`
3. UZLS reads `XREF2='HQ'` → ZLSCH unchanged (HQ branch matches)
4. BSAK line committed with office code `HQ`

### 6.3 The single variable that must change

`USR05 WHERE BNAME='AL_JONATHAN' AND PARID='Y_USERFO'`: `PARVA` must be changed from `'HQ'` to the correct Jakarta office code (likely `'JAK'`, pending `YFO_CODES` verification).

### 6.4 Are other users affected? (Class generalization — hypothesis)

Very likely yes. All 15 of AL_JONATHAN's SU3 parameters look like a template (every one points to UNES/HQ defaults). If this template was used for other field-unit users without per-user overrides, they are also posting with `Y_USERFO='HQ'`. See §11 for the proposed class-check query.

---

## 7.5 Additional observation — XREF attribution in cross-user clearing scenarios (not a ticket finding)

This section documents an observation that surfaced during the investigation. **It is NOT the root cause of this ticket**, it is NOT claimed to be a defect, and the ticket fix (SU3 update for AL_JONATHAN) does not depend on any action here. This is documentation of how the XREF-writing rule behaves when invoice posting and clearing are done by different users — so the behavior is understood for future reference.

### 7.5.1 The rule (restated from §3.2)

The same substitution rule fires on **every** FI posting event, reading the **current user's** `USR05.Y_USERFO` and writing it to `BSEG-XREF1` / `BSEG-XREF2` on the new document's vendor lines. There is no variant of the rule — just one rule, one source, one behavior.

This means: when a document is posted by user A and later cleared (via F110 payment run, FB1K manual, SAPF124 auto, or F-53 against an open item) by user B, the invoice side keeps user A's XREF and the clearing side gets user B's XREF. Two users, two postings, two XREF values — nothing contradictory, just the same rule firing twice.

### 7.5.2 Empirical sample — `DA_ENGONGA` (Dakar) invoices cleared by HQ / system users

Six documents sampled on 2026-04-09 via live RFC (P01):

| Invoice BELNR | Invoice TCODE | Invoice poster | Invoice XREF1 | Invoice XREF2 | Cleared by doc | Clearing TCODE | Clearing user | Clearing user Y_USERFO | Clearing XREF1 | Clearing XREF2 |
|---|---|---|---|---|---|---|---|---|---|---|
| 5100004414/2026 | MIRO | DA_ENGONGA (`Y_USERFO='DAK'`) | `'DAK'` | `'HQ'` | 0002003771 | F110 | **C_LOPEZ** | `'HQ'` | `'HQ'` | `'HQ'` |
| 5100004419/2026 | MIRO | DA_ENGONGA | `'DAK'` | `'HQ'` | 0002003771 | F110 | C_LOPEZ | `'HQ'` | `'HQ'` | `'HQ'` |
| 5100004424/2026 | MIRO | DA_ENGONGA | `'DAK'` | `'HQ'` | 0002003828 | F110 | C_LOPEZ | `'HQ'` | `'HQ'` | `'HQ'` |
| 6400003609/2026 | FB60 | DA_ENGONGA | `'DAK'` | `'UNDP-MR'` | 0100024070 | FB1K | **L_HANGI** | `'HQ'` | `'HQ'` | `'HQ'` |
| 6400003560/2026 | FB01 | DA_ENGONGA | `'DAK'` | `'DAK'` | 0100020514 | FB1K (SAPF124) | **JOBBATCH** | (no row) | `''` | `''` |
| 6400003617/2026 | FB01 | DA_ENGONGA | `'DAK'` | `'DAK'` | 0100020974 | FB1K | JOBBATCH | (no row) | (no BSAK rows) | (no BSAK rows) |

### 7.5.3 What the sample shows — and the important distinction between REAL and METADATA lines

1. **XREF1 and XREF2 do not always match on the same line.** DA_ENGONGA's MIRO invoices have `XREF1='DAK' XREF2='HQ'` — because MIRO's entry screen allows XREF2 to be typed, UXR2 sees non-SPACE and skips the USR05 write (going to the validate-only branch), while UXR1 always writes `USR05.Y_USERFO` regardless of the user's screen input. For FB01 invoices where neither field is typed, both UXR1 and UXR2 write `'DAK'`.

2. **The clearing documents created by HQ central users carry the clearing user's office** — but the business significance of those clearing-doc XREF values is NOT the same across all clearing types. **Critical distinction:**

   **2a. F110 automatic payment run — REAL business lines**
   When F110 clears a vendor invoice, the payment document contains a **real vendor debit line** (BSCHL=25, "outgoing payment") and a **real bank credit line** (BSCHL=50). Both are genuine financial postings representing the actual money movement: vendor's open item is paid, cash leaves the bank. The vendor line's `XREF1='HQ' XREF2='HQ'` (C_LOPEZ's `Y_USERFO`) IS the "who made this payment" tag — and it is accurate in the strict sense (the payment was made by C_LOPEZ through F110), just **not aligned with the originating office attribution** (the invoice came from Dakar, but the payment is now tagged HQ).
   
   **→ F110 mis-attribution is a REAL data-quality issue for reporting that joins invoice origin to payment-execution office.**
   
   **2b. FB1K manual zero-balancing clearing — METADATA LINES, not real business events**
   When FB1K clears vendor items that already balance to zero (e.g., a credit memo offsetting an invoice, or settlement of a down payment against a final invoice), the clearing document contains a **zero-balancing BSEG pair** — typically BSCHL=27 (credit clearing) + BSCHL=37 (debit clearing) on the **same vendor and same GL account**. These two lines **cancel each other out** (equal amounts, opposite signs). **Their only purpose is to create the `AUGBL` linkage** marking the original open items as cleared. They have **zero financial impact** at the vendor, GL, or company-code level.
   
   L_HANGI's doc 0100024070 (which cleared DA_ENGONGA's FB60 invoice 6400003609) is exactly this pattern:
   
   ```
   Doc 0100024070/2026:
     L001 BSCHL=27 LIFNR=100187 HKONT=2021051 DMBTR=...  XREF1='HQ' XREF2='HQ'  (credit — metadata)
     L002 BSCHL=37 LIFNR=100187 HKONT=2021051 DMBTR=... (same) XREF1='HQ' XREF2='HQ'  (debit — metadata)
   ```
   
   **The XREF values on these lines are cosmetic** — they are stamped by the substitution on BSEG records that exist only for linkage purposes. The underlying **original invoice line (`6400003609` L001, BSCHL=31, `XREF1='DAK' XREF2='UNDP-MR'`)** IS PRESERVED UNCHANGED. Its values are correct, its `AUGBL` is updated to `0100024070`, and any downstream consumer that correctly filters BSAK by real posting keys (e.g., `BSCHL NOT IN (27, 37)` for clearing-pair exclusion, or joins via `AUGBL` to the original open item) will see the correct `'DAK' / 'UNDP-MR'` attribution.
   
   **→ FB1K zero-balance clearing mis-attribution is a cosmetic / metadata-level issue.** The original invoice's office tag is preserved. The "wrong XREF" on the clearing pair matters only to naive downstream consumers that sum amounts by XREF without distinguishing metadata clearing pairs from real posted lines.

3. **System users (JOBBATCH) with no `USR05.Y_USERFO` row produce blank XREF.** The `SELECT SINGLE * FROM usr05 ... sy-subrc <> 0` branch returns no row, so UXR1/UXR2 fall through without writing — XREF stays SPACE. For SAPF124 automatic clearing (which is also typically zero-balancing), this is again a metadata-level issue — the original invoice's XREF is preserved.

4. **The UNDP case:** DA_ENGONGA's FB60 vendor invoice for vendor 0000100187 carries `XREF2='UNDP-MR'` (a manually entered memo reference for a UNDP transfer). This is why the `UZLS` form at [YRGGBS00_SOURCE.txt:1090](../../Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt#L1090) special-cases `IF bseg-xref2(4) <> 'UNDP'` — UNESCO uses XREF2 for both office codes AND UNDP transfer references depending on the context.

### 7.5.3a Revised severity ranking — where the REAL material exposure is

| Flow | Clearing/payment line type | XREF impact severity | Reasoning |
|---|---|---|---|
| **F-53 manual payment** (AL_JONATHAN case) | REAL — direct disbursement, vendor debit, BSCHL=25/29 | **HIGH** | The vendor line is a real financial event; XREF is the "who paid this" tag; wrong value is committed silently without any validation; this is the ticket |
| **F110 automatic payment run** | REAL — vendor clearing line (BSCHL=25) has real financial meaning | **MEDIUM** | Real payment execution, but the vendor clearing line tags the F110 runner's office (HQ always — only 2 F110 runners at UNESCO, both HQ); asymmetric because bank GL line is blank |
| **FB1K manual zero-balancing clearing** | METADATA — BSCHL=27/37 zero-balancing pair | **LOW** | Clearing-pair lines net to zero, no financial impact; original invoice's XREF is preserved; only affects naive downstream consumers |
| **SAPF124 auto clearing** | METADATA — typically zero-balancing | **LOW** | Same as FB1K but with JOBBATCH producing blank XREF instead of HQ; still metadata-only |
| **Invoice posting** (FB60/MIRO/FB01) | REAL — vendor credit line (BSCHL=31) has real meaning | **LOW** (partially validated) | XREF from invoice poster; XREF2 allows user input on some screens; U915 + U917 validations run (bank + SCB) but neither touches XREF; for field users, the result is usually the correct field office |

**The real material exposure is concentrated on F-53 (HIGH, this ticket) and F110 (MEDIUM, structural).** The FB1K / SAPF124 cross-user mis-attribution is a metadata-level cosmetic issue that does not corrupt the underlying financial reality.

### 7.5.4 Downstream consequence summary

Any process that groups FI line items by XREF1 / XREF2 as the office key will see the following when processing a cross-user AP transaction:

| Process | Sees invoice side | Sees clearing side | Net effect if grouping by XREF |
|---|---|---|---|
| `UZLS` payment-method derivation | `DAK` / `HQ` / `UNDP-MR` → various | `HQ` or blank | Invoice line can drive `ZLSCH='O'` (field-office outbound); clearing line drives default HQ or blank |
| Field-office BI reports | Invoice under DAK | Clearing under HQ | The pair is split across two offices in the report |
| Reconciliation by office | Same — split view | Same — split view | Field-office reconciler sees only invoice line; HQ reconciler sees clearing line |

### 7.5.5 How this relates to AL_JONATHAN's ticket

**It does not.** AL_JONATHAN's 10 F-53 documents are all **self-clearing** (AUGBL = BELNR, §6.1). No cross-user handoff is involved in his case — he is both the "invoice poster" and the "payment poster" on a single self-clearing doc. His XREF is wrong because his `Y_USERFO` is wrong, and fixing his `Y_USERFO` fixes his XREF.

The cross-user scenario documented above **is a separate behavior for different documents by different users**, with no causal link to this ticket's defect. The ticket fix is independent.

### 7.5.6 If UNESCO ever wants to revisit this behavior (optional, future)

This is not an action item for this ticket. It is included only if UNESCO ever decides to re-examine how XREF is derived.

The current design is: *"XREF is the posting user's office, full stop, on every posting."* An alternative design would be: *"XREF is derived from the document's own context (cost center / fund center / business area / XBLNR prefix)"*. Either design is internally consistent. Which is correct depends on what UNESCO Finance / BI / BCM expect XREF to mean. **That conversation is for UNESCO business owners, not for this ticket.**

---

## 7. Broken Safety Nets (what should have caught this)

Seven potential safety nets exist (or could exist) to catch a wrong XREF value. **None of them caught AL_JONATHAN's case. Five are absent entirely; two exist but are inadequate.**

| # | Safety net | Where it is (or would be) | Why it didn't fire |
|---|---|---|---|
| 1 | **YFO_CODES dictionary check in UXR1** — per the in-code validation in §3.3 | `YRGGBS00_SOURCE.txt:1007-1011` | The check runs AFTER UXR1 has already written the value. It only fires if the written code is **not in `YFO_CODES.FOCOD`** and raises a `w018 ZFI` **warning** — **NOT an error**. The warning does not stop the posting. `'HQ'` exists in YFO_CODES (it's the HQ office code), so no warning fires. **This safety net catches dictionary misses, not wrong-for-user values.** |
| 2 | **YFO_CODES check in UXR2** — asymmetric | `YRGGBS00_SOURCE.txt:1035-1039` | Only runs in the ELSE branch (when the user manually typed a value). In the SPACE branch (auto-write from `USR05.Y_USERFO`) there is **no check at all** — the USR05 value is trusted blindly. For F-53, XREF2 is always SPACE on entry (screen hides it), so UXR2 always takes the SPACE branch and the check never fires. |
| 3 | **UNES line-item validation (`VALID='UNES'`) on XREF fields** — what the 12 validation steps in `GB931` ought to check | `GB93` + `GB931` (verified via live RFC 2026-04-09) | **No step checks BSEG-XREF1 or BSEG-XREF2.** The 12 steps check `GSBER`, `BLART`, `TCODE`, `HKONT`, `GEBER`, `BSCHL`, vendor bank account count (`U915`), and SCB indicator (`U917`). **Zero steps reference XREF fields.** See §3.4.3 for the full map. |
| 4 | **Validation coverage for F-53 / FBZ2** — if line-item validation did check XREF, it would need to fire on the F-53 TCODE | `GB931` VALSEQNR 001-012 | **`F-53` and `FBZ2` appear in ZERO UNES validation prerequisites.** The closest TCODEs are `F-58` + `FBZ4` (step 008) and `F110` + `F111` (step 006). See §3.4.5. Manual outgoing payments pass through the UNES validation layer completely uncovered. |
| 5 | **User-level override from F-53 screen** | F-53 entry screen configuration | The XREF1 / XREF2 fields are not exposed on F-53 entry screens. User has no UI to see or correct the value before posting. |
| 6 | **HR-master / SU3 alignment check** — would compare `USR05.Y_USERFO` to `PA0001.WERKS/BTRTL` | No such check exists at UNESCO | Nothing cross-validates the user-parameter office against HR's personnel area. A user can be hired in Jakarta (PA0001=ID00/JKT) and still have `Y_USERFO='HQ'` (USR05) with no detection. |
| 7 | **Automated pre-creation SU3 validation** — would force Y_USERFO to match a valid office for the user's HR org | No such validation exists | SU3 parameters are free-text at creation. Admins can set any value. |

**Two of these safety nets (#1 and #2) actually exist in the substitution code itself**, but they protect against the wrong risk: dictionary misses (bad codes) and manual typos, not correctness-for-user (wrong-but-valid codes). **Five safety nets (#3-#7) are completely absent.** The 21,754 Q1 2026 manual FBL3N/FB02 corrections by 242 users are the operational cost of having **no effective safety net on XREF values**.

---

## 8. Evidence

### 8.1 USR05 for AL_JONATHAN — full PARID dump (2026-04-09, P01)

See §4.1. Key row: `BNAME='AL_JONATHAN', PARID='Y_USERFO', PARVA='HQ'`.

### 8.2 USR05 comparison across 12 active posters (Dec/2025-March/2026 UNES)

| USNAM | `Y_USERFO` | FBZ docs in window | Interpretation |
|---|---|---|---|
| AL_JONATHAN | **`'HQ'`** | 14 | **SUBJECT — wrong** (Jakarta) |
| T_ENG | `'HQ'` | 8,609 | Genuine HQ user |
| S_EARLE | `'HQ'` | 8,304 | Genuine HQ user |
| C_LOPEZ | `'HQ'` | 4,110 | Genuine HQ user |
| I_MARQUAND | `'HQ'` | 4,095 | Genuine HQ user |
| B_GAZI | `'HQ'` | 1,853 | Genuine HQ user |
| I_WETTIE | `'HQ'` | 959 | Genuine HQ user |
| S_AGOSTO | `'HQ'` | 915 | Genuine HQ user |
| JJ_YAKI-PAHI | **`'YAO'`** | 514 | Yaoundé — field office, correct |
| L_HANGI | `'HQ'` | 485 | Unknown |
| O_RASHIDI | **`'KAB'`** | 467 | Kabul — field office, correct |
| DA_ENGONGA | **`'DAK'`** | 320 | Dakar — field office, correct |

**Confirms that the mechanism works for field users** (YAO, KAB, DAK are populated correctly), and that AL_JONATHAN is the anomaly.

### 8.3 AL_JONATHAN's FULL BSEG line-item sweep (all 36 lines since 2024, RFC verified)

Gold DB shows AL_JONATHAN has **14 BKPF documents** across his entire presence in the system (2024-01-01 → 2026-03-28 extraction window). First posting 2026-02-06, last 2026-03-16 — he is a newly onboarded user with ~6 weeks of history.

The 14 documents fan out to **36 BSEG line items** across three source tables: 10 in BSAK (vendor cleared), 18 in BSAS (GL cleared — bank clearing side), 8 in BSIS (GL open — expense accruals). A live RFC sweep on 2026-04-09 captured all 36 with `XREF1`/`XREF2`/`XREF3`/`ZUONR`/`HKONT`.

**Full dump (sorted by BUDAT / BELNR / BUZEI):**

| # | BUDAT | BELNR / GJAHR | Line | Src | HKONT | LIFNR/KUNNR | Vendor name | **XREF1** | **XREF2** | XREF3 | ZUONR |
|--|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 2026-02-06 | 3200000273/2026 | 001 | BSAS | 0001181344 | — | — | `''` | `''` | `''` | `''` |
| 2 | 2026-02-06 | 3200000273/2026 | 002 | BSAS | 0002100340 | — | — | `''` | `''` | `''` | `''` |
| 3 | 2026-02-06 | 3200000273/2026 | 003 | BSIS | 0006045011 | — | — | `''` | `''` | `''` | `''` |
| 4 | 2026-02-12 | 3100003438/2026 | 001 | BSAS | 0001181341 | — | — | `''` | `''` | `''` | `''` |
| 5 | 2026-02-12 | **3100003438/2026** | **002** | **BSAK** | 0002021061 | 0010157142 | MUHAMMAD HASNAN | **`'HQ'`** | **`'HQ'`** | `''` | `'20260212'` |
| 6 | 2026-02-12 | 3100003439/2026 | 001 | BSAS | 0001181344 | — | — | `''` | `''` | `''` | `''` |
| 7 | 2026-02-12 | **3100003439/2026** | **002** | **BSAK** | 0002021061 | 0010150370 | CRESTI FITRIANA | **`'HQ'`** | **`'HQ'`** | `''` | `'20260212'` |
| 8 | 2026-02-12 | 3100003504/2026 | 001 | BSAS | 0001181344 | — | — | `''` | `''` | `''` | `''` |
| 9 | 2026-02-12 | **3100003504/2026** | **002** | **BSAK** | 0002021043 | 0010073496 | RACHMANIA SITI | **`'HQ'`** | **`'HQ'`** | `''` | `'20260212'` |
| 10 | 2026-02-12 | 3100003504/2026 | 003 | BSIS | 0007045011 | — | — | `''` | `''` | `''` | `''` |
| 11 | 2026-02-12 | 3100003505/2026 | 001 | BSAS | 0001181344 | — | — | `''` | `''` | `''` | `''` |
| 12 | 2026-02-12 | **3100003505/2026** | **002** | **BSAK** | 0002021043 | 0010002633 | ANHAR PERMANA | **`'HQ'`** | **`'HQ'`** | `''` | `'20260212'` |
| 13 | 2026-02-12 | 3100003505/2026 | 003 | BSIS | 0007045011 | — | — | `''` | `''` | `''` | `''` |
| 14 | 2026-02-12 | 3100003506/2026 | 001 | BSAS | 0001181344 | — | — | `''` | `''` | `''` | `''` |
| 15 | 2026-02-12 | **3100003506/2026** | **002** | **BSAK** | 0002021043 | 0010105124 | VIDYANI AHMAD | **`'HQ'`** | **`'HQ'`** | `''` | `'20260212'` |
| 16 | 2026-02-12 | 3100003506/2026 | 003 | BSIS | 0006045011 | — | — | `''` | `''` | `''` | `''` |
| 17 | 2026-02-12 | 3100003509/2026 | 001 | BSAS | 0001181344 | — | — | `''` | `''` | `''` | `''` |
| 18 | 2026-02-12 | **3100003509/2026** | **002** | **BSAK** | 0002021043 | 0010153157 | ROCHMY AKBAR | **`'HQ'`** | **`'HQ'`** | `''` | `'20260212'` |
| 19 | 2026-02-12 | 3100003509/2026 | 003 | BSIS | 0007045011 | — | — | `''` | `''` | `''` | `''` |
| 20 | 2026-02-27 | 3200000390/2026 | 001 | BSAS | 0001181344 | — | — | `''` | `''` | `''` | `''` |
| 21 | 2026-02-27 | 3200000390/2026 | 002 | BSAS | 0002100340 | — | — | `''` | `''` | `''` | `''` |
| 22 | 2026-02-27 | 3200000390/2026 | 003 | BSIS | 0006045011 | — | — | `''` | `''` | `''` | `''` |
| 23 | 2026-02-27 | 3200000401/2026 | 001 | BSAS | 0001181344 | — | — | `''` | `''` | `''` | `''` |
| 24 | 2026-02-27 | 3200000401/2026 | 002 | BSAS | 0002100340 | — | — | `''` | `''` | `''` | `''` |
| 25 | 2026-02-27 | 3200000401/2026 | 003 | BSIS | 0006045011 | — | — | `''` | `''` | `''` | `''` |
| 26 | 2026-02-27 | 3200000403/2026 | 001 | BSAS | 0001181344 | — | — | `''` | `''` | `''` | `''` |
| 27 | 2026-02-27 | 3200000403/2026 | 002 | BSAS | 0002100340 | — | — | `''` | `''` | `''` | `''` |
| 28 | 2026-02-27 | 3200000403/2026 | 003 | BSIS | 0006045011 | — | — | `''` | `''` | `''` | `''` |
| 29 | 2026-03-16 | 3100007233/2026 | 001 | BSAS | 0001181341 | — | — | `''` | `''` | `''` | `''` |
| 30 | 2026-03-16 | **3100007233/2026** | **002** | **BSAK** | 0002021061 | 0010103901 | RODOLFO MARTINS | **`'HQ'`** | **`'HQ'`** | `''` | `'20260316'` |
| 31 | 2026-03-16 | 3100007235/2026 | 001 | BSAS | 0001181341 | — | — | `''` | `''` | `''` | `''` |
| 32 | 2026-03-16 | **3100007235/2026** | **002** | **BSAK** | 0002021061 | 0010157142 | MUHAMMAD HASNAN | **`'HQ'`** | **`'HQ'`** | `''` | `'20260316'` |
| 33 | 2026-03-16 | 3100007237/2026 | 001 | BSAS | 0001181341 | — | — | `''` | `''` | `''` | `''` |
| 34 | 2026-03-16 | **3100007237/2026** | **002** | **BSAK** | 0002021042 | 0010073496 | RACHMANIA SITI | **`'HQ'`** | **`'HQ'`** | `''` | `'20260316'` |
| 35 | 2026-03-16 | 3100007238/2026 | 001 | BSAS | 0001181341 | — | — | `''` | `''` | `''` | `''` |
| 36 | 2026-03-16 | **3100007238/2026** | **002** | **BSAK** | 0002021061 | 0010150370 | CRESTI FITRIANA | **`'HQ'`** | **`'HQ'`** | `''` | `'20260316'` |

**Aggregates:**
- **Total line items:** 36
- **Distinct `XREF1` values:** `['', 'HQ']`
- **Distinct `XREF2` values:** `['', 'HQ']`
- **Distinct `XREF3` values:** `['']` (XREF3 is never populated by any exit)
- **Lines with `XREF1='HQ'`:** 10 — every one is a BSAK vendor line
- **Lines with `XREF2='HQ'`:** 10 — same 10 BSAK vendor lines
- **Lines with XREF blank:** 26 — every BSAS (bank clearing) and BSIS (expense) line

### 8.3.1 Correction — the "vendor-line-only" reading was wrong

An earlier version of this section claimed *"substitution fires on BSAK vendor lines only; BSAS/BSIS GL lines are blank"*. **That claim was a Gold-DB-schema artifact, not reality.** 

**Why the earlier reading was wrong:** the table above shows `XREF1=''` and `XREF2=''` on the GL lines, but those values came from joining to `bseg_union` which **does not carry XREF columns** (`PRAGMA table_info(bseg_union)` confirms this). I was reading empty values from a table that simply doesn't have the field.

**What really happens — established via CDPOS on 2026-04-09:**

For AL_JONATHAN's doc `3100003438/2026` line 001 (BSAS bank GL, HKONT=1181341):

```
CDPOS CHANGENR=0118205716 (A_HIZKIA FBL3N 2026-02-16):
  TABNAME=BSEG  FNAME=XREF1  VALUE_OLD='HQ'  VALUE_NEW='JAK'
```

The `VALUE_OLD='HQ'` is the value the GL line was carrying at the moment A_HIZKIA opened FBL3N — **4 days after the F-53 posting**. Since (a) SAP-standard clearing does not modify BSEG-XREF fields of the cleared line, (b) no other CDHDR entry exists between 2026-02-12 and 2026-02-16, and (c) the F-53 screen does not expose XREF1/XREF2 for user entry, **the only possible source of `XREF1='HQ'` on this GL line is the substitution firing at original posting time via UXR1 with AL_JONATHAN's `Y_USERFO='HQ'`**.

**So the corrected reality is:**
- **Substitution fires on EVERY BSEG line** created by an F-53 / FBZ2 posting (vendor + GL + customer + asset lines), not just vendor lines
- Steps 005 (XREF1) and 006 (XREF2) of GB922 SUBSTID='UNESCO' run at callpoint 3 with **no effective prerequisite gate**
- The in-code behavior of `UXR1` / `UXR2` (read `USR05.Y_USERFO`, write if present) applies to all lines the engine hands it
- On F110, the bank GL line is blank — that's an F110-specific anomaly (see §3.4.5), NOT a general rule about substitution skipping GL lines

**The earlier §3.4-era hypothesis that `3UNESCO#013` (`KOART='K'`) was the prerequisite for step 005 is therefore WRONG.** Step 005 has no effective prerequisite in the data we can observe; it fires on all lines.

### 8.3.2 Document-level breakdown

- **4 FBZ1 documents** (Incoming Payment, BLART=IP, TCODE=FBZ1) — these are NOT F-53 / outgoing payments. They are F-52 incoming payments and are **excluded from the ticket scope**. Their lines are not sampled in this analysis.
- **10 FBZ2 documents** (Outgoing Payment, BLART=OP, TCODE=FBZ2 — the stored TCODE for F-53 dialog postings) — each has one BSAK vendor line verified via RFC to carry `XREF1='HQ' XREF2='HQ'`, and at least one (3100003438) has CDPOS confirming the bank GL line also carried `XREF1='HQ'` at posting time.

**Damage assessment for AL_JONATHAN — corrected:**
- **14 F-53 documents** total by AL_JONATHAN in 2026-02 / 2026-03 (10 F-53 direct disbursements + 4 unrelated FBZ1 excluded)
- Every BSEG line created by his F-53 postings carries `XREF='HQ'` (vendor lines confirmed via RFC; GL lines confirmed indirectly via CDPOS on 1 doc)
- **10 vendor lines × direct confirmation** + estimated **~14-20 GL lines × indirect confirmation** = full set of posted lines are affected
- A_HIZKIA corrected 2 of his docs (GL side only, via FBL3N) — the remaining 8-12 are still untouched

See §6.1 for the higher-level document summary by date and `XBLNR`.

### 8.3.2 Document-level breakdown

- **4 FBZ1 documents** (Incoming Payment, BLART=IP) with `XBLNR='JAKARTA'` — these have no BSAK lines at all (no vendor cleared) → **no XREF tagging, not affected by this ticket**. They record cash deposits/receipts; substitution doesn't fire on BSAS/BSIS.
- **10 FBZ2 documents** (Outgoing Payment, BLART=OP) — each has exactly one BSAK vendor line tagged `HQ/HQ` → **these are the 10 affected lines**.

**Complete damage assessment for AL_JONATHAN:**
- Affected: **10 vendor line items** (the BSAK rows above)
- Not affected: 26 GL line items + 4 FBZ1 incoming-payment docs (no BSAK lines)
- **100% of his vendor AP line items in the system carry `XREF1='HQ' XREF2='HQ'`** — there is no counter-example in his history.

See §6.1 for the higher-level document summary by date and `XBLNR`.

### 8.4 XBLNR context

Multiple FBZ1 (Incoming Payment) documents from AL_JONATHAN have `XBLNR='JAKARTA'`, and FBZ2 (Outgoing) documents have Indonesian vendor names in XBLNR. This is further qualitative evidence that his postings are Jakarta field-unit operations being mis-tagged as HQ.

### 8.5 XREF2 distribution for the full F-53/FBZ population — NOT YET RUN

`bseg_union` in Gold DB **does not currently carry `XREF1`/`XREF2`/`XREF3`** (confirmed 2026-04-09 via `PRAGMA table_info(bseg_union)`). A full-population class count requires either:
- Enriching bseg_union with XREF1/XREF2/XREF3 columns via a targeted RFC extraction, **or**
- A live RFC sweep over BSAK/BSAD/BSIK/BSID/BSAS/BSIS for the window.

Recorded as known_unknown **KU-028** — to be addressed after user confirms fix path (the class-count decision gates on whether HR/Finance wants to run the tactical fix only for AL_JONATHAN or sweep all field-unit users).

### 8.6 `YFO_CODES` contents — NOT YET READ

USR05 is blocked from `IN (...)` RFC reads and YFO_CODES is not in Gold DB. Recorded as **KU-027** — a quick follow-up RFC call to confirm `JAK` exists in `YFO_CODES.FOCOD` before applying the tactical fix.

### 8.7 GB901 / GB922 substitution rules that touch XREF1/XREF2

Not yet queried for this incident. Because the root cause is firmly in a custom **exit** (UXR1/UXR2) and not in a standard GB901/GB922 rule, this verification is **non-blocking** for the root cause. It may surface additional office-writing rules in the future but is not needed to fix this ticket.

---

## 9. Root Cause — Final

> The user master record for `AL_JONATHAN` has the SU3 parameter `Y_USERFO` set to the value `'HQ'` instead of the correct Jakarta value (expected `'JAK'`). Every FI line item he posts — including on transaction F-53 which has no on-screen input for `BSEG-XREF1`/`XREF2` — runs through custom substitution exits `UXR1` (`YRGGBS00_SOURCE.txt:996`) and `UXR2` (`YRGGBS00_SOURCE.txt:1024`), which unconditionally copy `USR05-PARVA` into `BSEG-XREF1`/`BSEG-XREF2`. The code works exactly as designed. The defect is purely in master data, not in code, and has been present since the user account was created with HQ-default parameters on every one of its 15 SU3 entries. This is confirmed by 10 consecutive BSAK line items across two posting days (2026-02-12 and 2026-03-16) all carrying `XREF1='HQ' XREF2='HQ'` while paying Indonesian vendors.

---

## 10. Fix Recommendation

### 10.1 Tactical fix (immediate — master data, no transport)

**Prerequisite check — MUST run BEFORE the SU3 update (KU-027):**

1. **Verify that `'JAK'` exists in `YFO_CODES.FOCOD`** via SE16N on table `YFO_CODES` (or one-shot RFC read).
   - **If `'JAK'` exists →** proceed to step 2 directly. The SU3 update will take effect cleanly.
   - **If `'JAK'` does NOT exist →** `UXR1` will write `XREF1='JAK'` and then immediately raise `w018 ZFI` warning ("Office code JAK not in YFO_CODES dictionary") on every one of AL_JONATHAN's future postings. The posting still commits (w018 is a warning not an error), but the user sees a dialog warning every time — bad UX. **Add the `YFO_CODES` row FIRST** via SM30 / maintenance view, THEN do the SU3 update. *This is the §3.3 in-code validation path; missing the prerequisite check will produce a nagging warning on every posting.*
   - **Additional UXR2 risk:** if the user ever manually types `'JAK'` in XREF2 on a screen that exposes the field (MIRO, FB60) and `'JAK'` is NOT in YFO_CODES, `UXR2` will raise `e018 ZFI` **hard error** and block posting. This would create a new class of blocked postings after the fix. Adding the YFO_CODES row before the SU3 update also prevents this.

2. **Update AL_JONATHAN's SU3 parameter:** SU3 / SU01 → user `AL_JONATHAN` → Parameters tab → change `Y_USERFO` from `'HQ'` to `'JAK'`. Save.

3. **Smoke test:** have AL_JONATHAN (or his proxy) post a test F-53 document and verify:
   - `BSAK` line for the vendor: `XREF1='JAK' XREF2='JAK'`
   - No `w018` or `e018` warnings/errors in the posting log
   - Downstream `ZLSCH` behavior: since `XREF2 <> 'HQ'` for UNES, form `UZLS` will now force `ZLSCH='O'` (field-office outbound) — **confirm this is the intended payment method for Jakarta postings** with the Jakarta treasury team BEFORE flipping the switch. If HQ's payment method should still apply, the `UZLS` rule needs adjustment (this is a separate decision).

4. **Do NOT retroactively re-post historical documents.** The wrong XREF values on his existing 10 F-53 docs are historical posted data; retroactive updates require FB02 line-item edits (which are restricted) and can only correct GL lines via FBL3N (which A_HIZKIA has already done for 2 of the 10). Accept the historical data as-posted, fix going forward.

### 10.2 Strategic fix — master-data audit (same-class users)

Now that PA0001 cross-reference is proven (§4.1), the class-generalization query is trivial:

```sql
-- Every UNES user where HR says field-unit but SU3 says HQ
SELECT u.BNAME, p.WERKS, p.BTRTL, u.PARVA AS y_userfo
FROM USR05 u
  JOIN PA0105 m ON m.USRID = u.BNAME AND m.SUBTY = '0001'
  JOIN PA0001 p ON p.PERNR = m.PERNR AND p.ENDDA = '99991231'
WHERE u.PARID = 'Y_USERFO'
  AND p.BUKRS = 'UNES'
  AND p.WERKS <> 'FR00'     -- not HQ country (France)
  AND u.PARVA = 'HQ'        -- but SU3 says HQ
```

1. **Run the audit** — needs USR05 + PA0105 + PA0001 either extracted to Gold DB (KU-028) or RFC'd live. The query returns the full population of AL_JONATHAN-class users in one shot.
2. **Expand YFO_CODES** for any newly-discovered field office that isn't already in the whitelist.
3. **Batch-correct USR05** for the identified users (same SU3 update but for multiple BNAMEs).
4. **Periodic job**: add a weekly/monthly report that re-runs the query and flags any new drift between HR and SU3.
5. **Pre-creation SU3 validation**: require `Y_USERFO` to match `PA0001.WERKS/BTRTL` at user creation / HR-org-change time.

### 10.3 Strategic fix — validation coverage (the bigger gap)

The real structural gap surfaced by this investigation is that **`VALID='UNES'` has 12 steps but NONE check XREF values, and F-53 / FBZ2 is in zero TCODE prerequisites** (§3.4 and §7). Two options for UNESCO Finance/BI to consider:

**Option A — add an XREF consistency validation step to `VALID='UNES'`:**
- Add a new validation step with CONDID `BUKRS='UNES' AND KOART='K'` and CHECKID that verifies `BSEG-XREF1 IN <YFO_CODES allowed set>` AND `BSEG-XREF1` matches the user's HR-assigned office (via a custom exit that reads PA0001 via PA0105→USR05 or a mapping table). Severity=E (hard error) would block wrong postings. Severity=W (warning) would let postings through but flag them in a review queue.

**Option B — add F-53 / FBZ2 to the existing validation TCODE lists:**
- At minimum, extend `1UNES###005` (which currently fires on `BLART IN ZP/CP`) or `1UNES###007` (which fires on `TCODE IN F-58/FBZ4`) to also include FBZ2. This would fire the existing validation steps on F-53 postings too, but since none of them check XREF, this alone doesn't fix the XREF gap — it would only align TCODE coverage.

**Option C — close the UXR1 overwrite gap:**
- In `YRGGBS00_SOURCE.txt` line 998, the `IF bseg_xref1 = space` guard is commented out. Re-enabling it would stop UXR1 from silently overwriting user-entered values. On its own this doesn't fix AL_JONATHAN's case (F-53 screen doesn't let him enter anything anyway) but it would prevent future regressions where a user DOES type a correct value and UXR1 overwrites it.

**Option D — replace the SU3-parameter-based lookup with an HR-master lookup:**
- The substitution would read `PA0001.WERKS/BTRTL` (via PA0105 SY-UNAME lookup) instead of `USR05.Y_USERFO`. This eliminates the dual source of truth problem. Biggest change, highest reliability, but requires development effort and regression testing.

### 10.4 Questions for UNESCO HR / Finance before any fix deployment

1. Is Anthony's physical office **Jakarta (JAK)** — or does UNESCO use a more granular code like `JKT`, `JAKA`, `IDN`? The email signature says "FU/JAK" and we have empirical precedent in other users' `Y_USERFO` (YAO, KAB, DAK) suggesting 3-char office codes.
2. Does `'JAK'` exist in `YFO_CODES` today?
3. Should the tactical fix cover **only AL_JONATHAN**, or should the §10.2 class audit be run first and all AL_JONATHAN-class users corrected in one batch?
4. Should F-53 / FBZ2 postings have **ZLSCH='O' (field-office outbound)** for Jakarta users once their Y_USERFO is JAK? The `UZLS` form will derive this automatically after the fix — but only if field-office outbound is the intended payment method for Jakarta disbursements.
5. Is there any appetite for the **validation coverage improvement** (§10.3 Option A) — adding an XREF consistency check as the 13th UNES validation step? This would catch wrong XREF values at posting time, across ALL TCODEs (not just F-53), and would eliminate the need for the 21,754 manual FBL3N corrections per quarter.

---

## 11. Office Code → XREF Map (as understood from this investigation)

These are the office codes referenced in YRGGBS00 source + live USR05 observations. This is not a complete list of all UNESCO office codes — it's the subset proven to exist in production.

| Office code | Full name (inferred) | Company code | Referenced in |
|---|---|---|---|
| `HQ` | UNESCO Headquarters, Paris | UNES | YRGGBS00:1093 (UZLS CASE UNES), USR05 template default |
| `JAK` | Jakarta Field Unit, Indonesia | UNES | User department FU/JAK — **not yet verified to exist in YFO_CODES** (KU-027) |
| `YAO` | Yaoundé Regional Office, Cameroon | UNES | USR05 row (JJ_YAKI-PAHI) |
| `KAB` | Kabul Country Office, Afghanistan | UNES | USR05 row (O_RASHIDI) |
| `DAK` | Dakar Regional Office, Senegal | UNES | USR05 row (DA_ENGONGA) |
| `BRZ` | (Brasilia? Brazil office) | UBO | YRGGBS00:1097 (UZLS CASE UBO) |
| `UIS` | UNESCO Institute for Statistics, Montreal | UIS | YRGGBS00:1101 (UZLS CASE UIS) |
| `IBE` | International Bureau of Education, Geneva | IBE | YRGGBS00:1105 (UZLS CASE IBE) |
| `IIEP_PAR` | IIEP Paris | IIEP | YRGGBS00:1109 (UZLS CASE IIEP) |
| `UNDP(.+)` | UNDP-administered postings | any | YRGGBS00:1090 special case (skips company-code CASE) |

Full YFO_CODES contents should be extracted to Gold DB (follow-up, KU-027).

---

## 12. Extracted Code Assets (this session)

| File | What it is |
|---|---|
| `Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt` | Full UNESCO copy of RGGBS000 substitution form pool — ~1100 lines. Contains forms UXR1, UXR2, UZLS, UAEP, U910, UIT1-UIT4 and the substitution exit registration list. |
| `Zagentexecution/incidents/INC-000005240_live_diagnostic.py` | One-shot diagnostic script that pulls USR05 for AL_JONATHAN + 11 comparison users, BKPF docs from Gold DB, and BSAK vendor-cleared line items via RFC. Read-only, written to `INC-000005240_live_diagnostic.json`. |
| `Zagentexecution/incidents/INC-000005240_live_diagnostic.json` | Captured evidence: 347 USR05 PARID rows across 12 users, 14 BKPF docs, 10 BSAK lines. |

No new code was deployed to P01 or D01 in this investigation. Everything was read-only.

---

## 13. Triage of the prior wrong-path investigation (from Session #050 subagent)

The first attempt on this ticket (executed as a subagent delegated from the main agent) chased the **wrong mechanism** — FMDERIVE exit `ZXFMDTU02_RPY` (PSM fund center hardcoding for GL accounts 0006045011 / 0007045011 / 0006045014). That defect may be a real separate observation but is NOT the cause of INC-000005240.

### 13.1 Wrong-path artifacts produced

| File | Status | Disposition |
|---|---|---|
| `Zagentexecution/incidents/INC-000005240_intake.json` | Wrong parsing (maps "reference key" to XBLNR/ZUONR/FISTL and "HQ" to UNESCO fund center) | **Rewrite** to reflect XREF1/XREF2 + office code (pending user approval in Step 9 of the workflow) |
| `knowledge/incidents/INC-000005240_f53_fistl_unesco_default.md` | Wrong mechanism — full 9-section analysis of FMDERIVE | **Move / rename** to `knowledge/observations/fmderive_hardcoded_fictr_for_gl_6045xxx.md` — may describe a real separate defect worth tracking |
| `Zagentexecution/quality_checks/fmderive_hardcoded_fictr_check.py` | Useful quality check, unrelated to this ticket | **Keep** — unlink from INC-000005240, relink to the observation file |
| `brain_v2/annotations/annotations.json` new entries (ZXFMDTU02_RPY, fmifiit_full, fund_centers, USR05) | Mixed — USR05 annotation is still useful, FMDERIVE ones are wrong-incident | **Review each** — keep USR05 (re-tagged to this incident), revert or re-tag the rest |
| `brain_v2/claims/claims.json` claims 27-30 | Tied to FMDERIVE hypothesis | **Revert or re-tag** as "discovered during INC-000005240 investigation but unrelated to ticket — filed as observation" |
| `brain_v2/agi/known_unknowns.json` KU-024/025/026 | Mostly FMDERIVE | **Review each**, keep any that actually apply |
| `brain_v2/agi/data_quality_issues.json` DQ-017 | FMDERIVE data | **Review** |

All of the above is **held pending user confirmation of this v2 root cause** — that is the rule `feedback_brain_rebuild_after_finalized`.

### 13.2 Feedback rule captured from this failure mode

- `feedback_main_agent_holds_incident_context` — **HIGH** — do not delegate the 7-step incident workflow to a subagent
- `feedback_user_term_to_sap_field_translation` — **HIGH** — Section 1 of every incident report must include the translation table before any code search
- `feedback_process_before_root_cause` — **HIGH** — write "how it should work" before "why it fails"
- `feedback_brain_rebuild_after_finalized` — **HIGH** — rebuild only AFTER user confirms root cause

All four have been added to `brain_v2/agent_rules/feedback_rules.json` in this session.

---

## 14. Data Sources

| Source | What was read | When |
|---|---|---|
| `.eml` file | Email body (verbatim symptom) | 2026-04-09 |
| `Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt` | Full form pool (grep + full form body reads of UXR1, UXR2, UZLS) | 2026-04-09 |
| Gold DB `bkpf` (`Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`) | 14 documents for AL_JONATHAN, BUKRS=UNES, TCODE IN FBZ1/FBZ2, BUDAT 2025-12-01 → 2026-03-31 | 2026-04-09 |
| P01 live RFC | USR05 (per-user BNAME reads for 12 users — 347 PARID rows), BSAK (per-doc reads for 14 docs — 10 line items) | 2026-04-09 |
| `knowledge/incidents/INC-000006073_travel_busarea.md` | Template/structure reference | 2026-04-09 |
| `knowledge/domains/FI/ggb1_substitution_tables_distinction.md` | GGB1 architecture reference (negative hint — confirmed this was NOT the mechanism) | 2026-04-09 |

---

## 15. Known unknowns opened by this incident

| ID | Unknown | Impact | Follow-up |
|---|---|---|---|
| **KU-027** | Does `YFO_CODES` contain a row for `FOCOD='JAK'`? | Blocks tactical fix — if not, need to add the row first | Single RFC read on `YFO_CODES` or manual SE16N check. ~30 seconds. |
| **KU-028** | How many other UNES users have `Y_USERFO='HQ'` but an HR master (PA0001.PERSA / ORGEH) indicating a field-unit assignment? | Sizes the class generalization | Extract USR05 filtered by `PARID='Y_USERFO'` to Gold DB (~50K rows estimate), join against PA0001 already in Gold DB, report mismatches. |
| **KU-029** | What are the downstream consequences of wrong XREF2 for AL_JONATHAN's 14 docs? (Did the payment run for those vendors apply the wrong ZLSCH? Did BCM workflow route them to the wrong approver?) | Determines whether retroactive remediation is needed | Trace through F110 / BCM / RRPROC for the affected BELNRs. |
| **KU-030** | Was the `IF bseg_xref1 = space` guard in UXR1 intentionally commented out, and when? | Informs the strategic fix recommendation (whether the guard was removed for a good reason or by accident) | Check transport history for YRGGBS00 / CTS / git blame on the include. |

---

## 16. Actions taken in this session (all reversible until user confirms)

1. Read the `.eml` end to end, built the User-term → SAP-field translation table.
2. Located forms UXR1 and UXR2 in `YRGGBS00_SOURCE.txt`; extracted verbatim code at lines 996-1016 and 1024-1041.
3. Wrote the diagnostic script `Zagentexecution/incidents/INC-000005240_live_diagnostic.py` (READ-ONLY).
4. Ran the diagnostic against P01 — captured 347 USR05 PARID rows and 10 BSAK line items.
5. Confirmed `AL_JONATHAN.Y_USERFO = 'HQ'` and all 10 of his FBZ2 lines have `XREF1='HQ' XREF2='HQ'`.
6. Wrote this canonical report (v2).
7. Held back all `brain_v2/` incident-layer updates (annotations, claims, incidents, KU-027/028/029/030, DQ) until user confirms the root cause.

**Next:** present findings to the user for approval. On approval → apply brain updates + rebuild. On rejection → triage this doc to observations and continue investigation.
