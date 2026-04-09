# Treasury — XREF Office Tagging Model (End-to-End)

**Scope:** how `BSEG-XREF1` and `BSEG-XREF2` carry office codes across the UNESCO AP/Payment lifecycle, which TCODEs activate which mechanisms, and where the validation gaps are.

**Source of truth for mechanism:** [`knowledge/domains/PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md`](../PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md) §2.7 (new — the XREF office-tagging trio)

**Root evidence:** [INC-000005240 report](../../incidents/INC-000005240_xref_office_substitution.md)

**Created:** 2026-04-09 (Session #051 finalization) — fills the gap noted in the existing autopsy.

---

## 1. What XREF1 / XREF2 are at UNESCO

`BSEG-XREF1` and `BSEG-XREF2` are two 12-character "Reference Key" fields that SAP leaves for customer use. **UNESCO repurposes them as the originating office tag** on every FI line item. Observed office codes in production:

| Code | Meaning | Company code | Example user |
|---|---|---|---|
| `HQ` | UNESCO Headquarters, Paris | UNES | C_LOPEZ, T_ENG, S_EARLE, L_HANGI, I_MARQUAND |
| `JAK` | Jakarta Field Unit, Indonesia | UNES | A_HIZKIA (correctly set); AL_JONATHAN (incorrectly set to 'HQ') |
| `YAO` | Yaoundé Regional Office, Cameroon | UNES | JJ_YAKI-PAHI |
| `KAB` | Kabul Country Office, Afghanistan | UNES | O_RASHIDI (USR05 says KAB; PA0001.BTRTL says KBL — note the mapping discrepancy) |
| `DAK` | Dakar Regional Office, Senegal | UNES | DA_ENGONGA (USR05 says DAK; PA0001.BTRTL says DKR) |
| `BRZ` | Brasilia Office (Brazil) | UBO | — |
| `UIS` | UNESCO Institute for Statistics, Montreal | UIS | — |
| `IBE` | International Bureau of Education, Geneva | IBE | — |
| `IIEP_PAR` | IIEP Paris | IIEP | — |
| `UNDP-*` | UNDP-administered postings (special prefix) | any | Free-text memo references, not an office code |

**Key observation:** `USR05.Y_USERFO` codes are NOT the same as `PA0001.BTRTL` codes. An implicit mapping exists (`PAR→HQ`, `JKT→JAK`, `KBL→KAB`, `DKR→DAK`, `YAO→YAO`) but it is tribal knowledge — no table enforces it.

---

## 2. The end-to-end mechanism

### 2.1 Write path (substitution)

```
FI posting event (any TCODE in UNES)
  ↓
GB922 SUBSTID='UNESCO' at callpoint 3 (complete document)
  ↓
Step 005: form UXR1 → writes BSEG-XREF1 = USR05.Y_USERFO for SY-UNAME (always — guard commented out)
Step 006: form UXR2 → writes BSEG-XREF2 = USR05.Y_USERFO for SY-UNAME (only when XREF2 was blank on entry)
Step 007: form UZLS → reads BSEG-XREF2 to derive BSEG-ZLSCH per company code
  ↓
Document committed with office tag on every BSEG line
```

### 2.2 Read path (downstream consumers)

1. **`UZLS` payment-method derivation** — For UNES, `XREF2='HQ'` keeps `ZLSCH` at default; anything else forces `ZLSCH='O'` (field-office outbound). For UBO, the trigger value is `'BRZ'`; for UIS, `'UIS'`; for IBE, `'IBE'`; for IIEP, `'IIEP_PAR'`.
2. **Field-office P&L reporting** — any BI cube that groups vendor AP by XREF attributes
3. **Reconciliation / audit** — auditors who compare office-level activity
4. **Payment approval workflow (YWFI package, workflow 90000003)** — if approver routing uses XREF as the office key
5. **BCM (Bank Communication Management)** — payment file routing via `ZLSCH` → `DMEE` format → house bank selection

**Every one of these consumers trusts the XREF tag blindly.** None of them re-validate it against HR, cost center, or any independent source.

### 2.3 Validation path (mostly absent)

- **In-code dictionary check** (partial) — `UXR1` raises `w018 ZFI` warning (non-blocking) if the written value is not in `YFO_CODES.FOCOD`; `UXR2` raises `e018 ZFI` hard error ONLY in the user-typed branch (not in the auto-write branch)
- **GGB0 validation `VALID='UNES'`** (12 steps in GB931) — **none check XREF fields**. The validation exits U915 (multi-bank vendor) and U917 (SCB indicator) fire on invoice vendor lines but ignore XREF content entirely
- **HR-master alignment** — no mechanism cross-checks `USR05.Y_USERFO` against `PA0001.WERKS/BTRTL`
- **SU3 maintenance-time validation** — no enforcement; the parameter is free-text

**The net effect: XREF values can be wrong in virtually any direction and no automated check fires.** The business absorbs the gap via post-posting manual correction (§5).

---

## 3. TCODE × Event coverage matrix

| Stage | TCODE / Event | Substitution fires? | Validation fires? | XREF tagged as |
|---|---|---|---|---|
| **Invoice posting — vendor invoice** | `FB60`, `MIRO`, `FB01`, `FB65`, `FBA6`, `FBR2`, `MIR7`, `FBV0`, `FBVB`, `F-47`, `FB41` | YES on vendor line + GL line; UXR1 warning if YFO_CODES miss | YES — U915 (multi-bank) + U917 (SCB); neither checks XREF | Invoice poster's `Y_USERFO` |
| **Invoice posting — customer invoice / billing** | `FB70`, `FB75`, etc. | TBD — not verified in this investigation | TBD | TBD |
| **Direct disbursement — F-53 manual** | `F-53` → commits as `BKPF.TCODE='FBZ2'` | YES on all lines (vendor + bank GL; CDPOS-proven) | **NO — F-53/FBZ2 is in ZERO `VALID='UNES'` prerequisites** | Payer's `Y_USERFO` (self-clearing, AUGBL=BELNR) |
| **Manual payment with print — F-58** | `F-58` | YES (inferred from the rule set) | YES — step 008 fires on F-58; BLART check only, not XREF | Payer's `Y_USERFO` |
| **Automatic payment run — F110** | `F110` | Asymmetric: YES on vendor clearing line, **NO on bank GL line** (empirical anomaly) | YES — step 006 fires on F110; but check is a TCODE tautology | F110 runner's `Y_USERFO` (empirically only HQ users run F110 at UNESCO: C_LOPEZ, I_MARQUAND) |
| **Reset clearing — FBZ4** | `FBZ4` | YES | YES — step 008 fires on FBZ4 | Reset user's `Y_USERFO` |
| **Incoming payment — F-52** | `F-52` → `FBZ1` | TBD — not fully verified | TBD | TBD |
| **Manual clearing — FB1K** | `FB1K` | YES on new BSEG lines (zero-balancing pair BSCHL=27/37) | **NO — FB1K is in ZERO `VALID='UNES'` prerequisites** | Clearing user's `Y_USERFO` — **BUT** these are metadata lines (§4), not real business events |
| **Auto-clearing — SAPF124** | `FB1K` program `SAPF124` (typically by `JOBBATCH`) | Code runs but USR05 SELECT fails (JOBBATCH has no Y_USERFO) → XREF stays blank | NO | Blank |
| **Post-posting change — FB02 / FBL1N / FBL3N** | `FB02`, `FBL1N`, `FBL3N` | N/A — not a posting event | YES — steps 002/003/005/008 fire (various) | User can manually edit XREF1 via FBL3N (GL view) or XREF2 via FB02 (doc edit) — this is how workarounds happen |

---

## 4. Real business lines vs metadata lines — CRITICAL distinction

Not every BSEG record with an XREF value represents a real financial event. Some are **metadata linkage lines** that exist only to create the `AUGBL` clearing relationship.

| BSEG line pattern | BSCHL | Is it a real business line? | XREF interpretation |
|---|---|---|---|
| **Vendor invoice credit** | 31 | **REAL** — creates open AP liability | Invoice poster's office; attributable |
| **Vendor invoice debit** (credit memo, reversal) | 21 | REAL | Poster's office |
| **Vendor outgoing payment** | 25 | **REAL** — actual payment | Payer's office |
| **Special GL advance** | 29 | REAL — advance payment | Payer's office |
| **Vendor clearing credit** (FB1K zero-balance pair) | 27 | **METADATA** — zero-balancing pair | Cosmetic — clearing user's office on a line that has no financial impact |
| **Vendor clearing debit** (FB1K zero-balance pair) | 37 | **METADATA** — zero-balancing pair | Cosmetic |
| **Bank GL debit** (payment side) | 40 | REAL — outflow | Typically blank on F110; populated on F-53 |
| **Bank GL credit** (receipt side) | 50 | REAL — inflow/clearing | Typically blank on F110; populated on F-53 |
| **Customer invoice** | 01-19 | REAL | Poster's office |

**When counting affected documents or measuring blast radius, filter out metadata clearing pairs.** The underlying invoice line's XREF is the business-meaningful value. See [INC-000005240 §7.5.3](../../incidents/INC-000005240_xref_office_substitution.md) for the full analysis.

---

## 5. The manual workaround layer — scale metrics (Q1 2026, UNES)

Because no automated validation catches wrong XREF values, UNESCO users perform post-posting correction via `FBL3N` / `FBL1N` / `FB02`. Measured scale:

| Metric | Value |
|---|---|
| Total manual edit events on UNES BELEG | **21,754** |
| Distinct UNES BELEG documents touched | **24,597** |
| Distinct users performing manual edits | **242** |
| FBL3N (GL line-item change) events | 11,575 by 124 users on 10,620 docs |
| FBL1N (vendor line-item change) events | 7,909 by 210 users on 6,558 docs |
| FB02 (doc change) events | 1,362 by 14 users on 1,278 docs |
| FBL5N (customer line-item change) events | 908 by 6 users on 627 docs |

**Top manual editors:** C_VINCENZI (2,075 FBL1N), R_MUSAKWA (1,422 FBL3N+FB02), I_BIDAULT (631 FB02), M_AHMADI (550 FBL3N), L_HANGI (499 FBL1N), A_HIZKIA (932 FBL3N full-year, 134 FBL1N — Jakarta user correcting XREF=HQ→JAK on field-unit postings).

**Jakarta cluster (users with `A_*` prefix and field-unit PA0001):** A_DELGADO 1,732 + A_CARVE 1,288 + A_HIZKIA 932 + A_YEGIAZARIA 839 + A_DEGA 614 = ~5,400 FBL3N edits over 2 years on UNES FI documents.

**This is the operational cost of having zero runtime validation on XREF values.** It's not just a technical gap — it's a standing budget line on human time.

---

## 6. Known gaps and follow-ups (KU references)

| KU ID | Question | Priority |
|---|---|---|
| **KU-027** | Does `YFO_CODES` currently contain `FOCOD='JAK'`? Critical before deploying the SU3 fix on AL_JONATHAN (otherwise `w018 ZFI` warning fires on every posting, and `e018` hard error if he ever manually types 'JAK'). | **HIGH** — blocking for AL_JONATHAN fix |
| **KU-028** | How many other UNES users have `Y_USERFO='HQ'` but `PA0001.WERKS/BTRTL` indicates a field-unit assignment? Query is trivial once PA0105/PA0001 extraction is proven. | MEDIUM — sizes the class generalization |
| **KU-029** | What is the downstream impact of wrong XREF on the 21,754 Q1 manually-corrected documents? Did payment method (ZLSCH) differ? Did field-office reports miss them? | LOW — historical |
| **KU-030** | Why is the `IF bseg_xref1 = space` guard commented out in UXR1 (line 998)? When was it removed, by whom, and why? | LOW — informational |
| **KU-031** | The substitution step linkage table at UNESCO is not in standard GB905/GB921 (both empty). Where is the prerequisite linkage stored? | LOW — framework curiosity |
| **KU-032** | Why does F110 substitution fire on the vendor clearing line but NOT on the bank GL line, while F-53 fires on both? Is there a BAPI vs dialog difference, a GGB1 step filter not visible in our data, or an F110-specific payment-program override? | MEDIUM — explains the F-53 vs F110 asymmetry |

---

## 7. Fix design patterns (if UNESCO ever decides to close the gap)

### 7.1 Minimal master-data fix (per-user, reactive)

SU3 update `USR05.Y_USERFO` for any drifted user. Reactive — doesn't prevent new drift.

### 7.2 Audit + batch correction (class-level, reactive)

Periodic `PA0001 × PA0105 × USR05` query flags drifted users. Batch-correct. Still reactive.

### 7.3 Add XREF validation step to `VALID='UNES'` (systemic, preventive)

Add a 13th step with CONDID `BUKRS='UNES' AND KOART='K'` and CHECKID = new custom exit `UXRF` that:
- Reads `PA0105` for `SY-UNAME → PERNR`
- Reads `PA0001.BTRTL` for that PERNR
- Maps BTRTL → expected YFO code via a new mapping table (or extends YFO_CODES with a BTRTL column)
- Compares `BSEG-XREF1` against the expected value
- Returns `b_false` (hard error) or raises a warning based on severity configuration

**Blocks wrong postings at posting time, across ALL TCODEs.** Biggest prevention value but requires a transport.

### 7.4 Close the UXR1 overwrite gap (defensive, low-effort)

Uncomment line 998's `IF bseg_xref1 = space` guard so UXR1 no longer silently overwrites user-typed XREF1 values. On its own this doesn't fix the auto-write path but prevents regression on screens that DO expose XREF1.

### 7.5 Replace USR05-based lookup with HR-master lookup (structural, highest effort)

Rewrite UXR1/UXR2 to read `PA0001.BTRTL` via PA0105→SY-UNAME→PERNR lookup, then translate to YFO code. Eliminates the dual source of truth. Requires development + regression test + transport.

---

## 8. Cross-references

- **Incident:** [INC-000005240](../../incidents/INC-000005240_xref_office_substitution.md) — the AL_JONATHAN ticket that surfaced this model
- **Framework autopsy:** [PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md](../PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md) §2.5-2.8 — full UXR1/UXR2/UZLS/U915/U916/U917 source and logic
- **FI GGB1 tables:** [FI/ggb1_substitution_tables_distinction.md](../FI/ggb1_substitution_tables_distinction.md) — GB922/GB931/GB901/GB93 naming conventions
- **Payment landscape:** [Treasury/payment_full_landscape.md](payment_full_landscape.md) — downstream BCM / F110 / DMEE context
- **Feedback rules added during this investigation:** `feedback_psm_extensions_is_fi_substitution_home`, `feedback_bseg_union_has_no_xref`, `feedback_empirical_over_theoretical_substitution`, `feedback_metadata_vs_real_bseg_lines`, `feedback_extract_ggb_tables_for_substitution_incidents`
