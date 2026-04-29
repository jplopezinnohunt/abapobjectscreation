# N_MENARD Alignment — Specific Questions for the 30-min Call

**Session #62 prep · 2026-04-25**
Agent's articulated doubts that require Nicolas Ménard's input before Phase 2.

## Background context for the call

You are the code owner of:
- `YCL_IDFI_CGI_DMEE_FR / FALLBACK / UTIL / DE / IT` (5 BAdI implementation classes)
- 9 DMEE-related transports during 2024 (most recent FALLBACK GET_CREDIT 2024-11-22)
- `Y_IDFI_CGI_DMEE_COUNTRIES_DE / FR / IT` (3 enhancement implementations)

We are migrating UNESCO's 3 DMEE payment trees to ISO 20022 CBPR+ structured address by Nov 2026. Strategy: 2-file + DMEE native versioning. **The only ABAP code change needed is a 3-line guard in your FALLBACK class** (everything else is customizing or new V001 DMEE nodes).

We've extracted all your code from P01 + the SAP-std country dispatcher chain + CITIPMW V3 Event 05 FM + the XSLT post-processor. Components map: 32 components total, 1 needs ABAP (Pattern A fix), 5 need DMEE config, 26 unchanged or out of scope.

## Q1 — Pattern A: remove or guard?

**Current `YCL_IDFI_CGI_DMEE_FALLBACK_CM001::GET_CREDIT` lines 13-31**:

```abap
WHEN '<PmtInf><CdtTrfTxInf><Cdtr><Nm>'.
  IF i_fpayp-origin = 'TR-CM-BT'.
    c_value = i_fpayp-sgtxt.
  ENDIF.
  mv_cdtr_name = c_value.
  IF c_value+35 IS NOT INITIAL.
    CLEAR c_value+35.
  ENDIF.
  mv_fpayh = i_fpayh.
WHEN '<PmtInf><CdtTrfTxInf><Cdtr><PstlAdr><StrtNm>'.
  IF i_fpayh = mv_fpayh AND mv_cdtr_name+35 IS NOT INITIAL.
    c_value = |{ mv_cdtr_name+35 } { c_value }|.   "← prepend name overflow to street
  ENDIF.
  IF c_value+70 IS NOT INITIAL.
    CLEAR c_value+70.
  ENDIF.
```

The name-overflow-into-StrtNm logic works in V000 (where StrtNm is empty/legacy AdrLine-only). In V001 (structured) it CORRUPTS the real street value.

**Two fix options**:

| Option | Code change | V000 behavior post-fix | V001 behavior post-fix |
|---|---|---|---|
| **A1 — Remove** | Delete the `c_value = ...` assignment entirely | Vendor name >35 chars: bank receives only first 35 chars in `<Nm>`. Overflow LOST. | Real street preserved. |
| **A2 — Guard** | Add `AND c_value IS INITIAL` to the IF | Same as today (V000 unchanged) — overflow fills empty StrtNm. | Real street preserved (overflow only fills empty). |

**My ask**: was the overflow-into-StrtNm intentional design (workaround for SEPA `<Nm>` 35-char limit) or legacy hack you'd remove if you could? **Choose A1 or A2**.

**My recommendation**: A2 (guard) — backward-compatible, preserves V000 behavior exactly, surgical 1-2 lines added. But I want your call.

## Q1bis — `YCL_IDFI_CGI_DMEE_FR` method-level swap between D01 and P01

**Discovery 2026-04-29 via byte-level extraction**: the FR class has DIFFERENT methods in each system:

| System | Methods present in FR class |
|---|---|
| **P01** (production) | CCDEF, CCIMP, CCMAC, CI, CO, CP, CT, CU, **CM002** (created 2024-09-06 by N_MENARD) |
| **D01** (dev) | CCDEF, CCIMP, CCMAC, CI, CO, CP, CT, CU, **CM001** (created 2024-03-22 by N_MENARD) |

P01 has `CM002` but NOT `CM001`. D01 has `CM001` but NOT `CM002`.

**My questions**:
1. Did you rename `CM001` → `CM002` at some point in P01? If yes, why didn't D01 get the rename?
2. Or are CM001 and CM002 different methods (not a rename)? What does each do?
3. **What's the canonical shape we should align D01 to**? Options:
   - (a) Bring P01's CM002 to D01 + delete D01's CM001 (= align to P01)
   - (b) Keep CM001 in D01 + add CM002 from P01 (= D01 has both)
   - (c) Other?

**My recommendation**: option (a) — D01 mirrors P01 exactly. Production behavior anchored on P01.

## Q2 — D01 retrofit: why are 5 objects P01-only?

Phase 0 inventory (`knowledge/domains/Payment/phase0/d01_vs_p01_inventory.csv`) shows 5 objects exist in P01 TADIR but NOT in D01:

```
CLAS  YCL_IDFI_CGI_DMEE_DE                  author=N_MENARD devclass=YA
CLAS  YCL_IDFI_CGI_DMEE_IT                  author=N_MENARD devclass=YA
ENHO  Y_IDFI_CGI_DMEE_COUNTRIES_DE          author=N_MENARD devclass=YA
ENHO  Y_IDFI_CGI_DMEE_COUNTRIES_FR          author=N_MENARD devclass=YA
ENHO  Y_IDFI_CGI_DMEE_COUNTRIES_IT          author=N_MENARD devclass=YA
```

**My questions**:
1. Do you remember why these are missing in D01? (D01 refresh? Manual delete? Transport reverted?)
2. Are there potentially **older versions of the same classes still in D01 under a different name** that we'd accidentally overwrite?
3. Is there any in-flight WIP in D01 on the BAdI ecosystem that retrofit would clobber?

**My ask**: confirm D01 has no in-flight WIP that retrofit would damage, or list anything we should preserve.

## Q3 — Retrofit method preference

We need to bring those 5 objects from P01 back to D01 before we can edit FALLBACK in D01 (your Pattern A fix transport). Three methods:

| Method | How |
|---|---|
| **A — Reverse transport** (P01 transport history → re-import into D01) | If the original transports are still archived in CTS history |
| **B — Recreate from extracted source** (we have the .abap files) — SE24/SE38 paste | New transport author = whoever pastes |
| **C — SAPLink XML import** | If SAPLink installed in D01 |

**My ask**: what's UNESCO BASIS team's preferred method for "P01-only object retrofit to D01"? Have you done this before?

## Q4 — Phase 2 code-review scope

Phase 2 (May 2026) involves 4 transport types:
1. **D01-BADI-FIX-01**: Pattern A 3-line change to FALLBACK_CM001 — **your code, you must review**
2. **D01-RETROFIT-01**: bring 5 P01-only objects back to D01 — **your code, you must approve method**
3. **D01-DMEE-V001-{SEPA,CITI,CGI}**: 3-4 transports adding V001 versions of trees + new structured nodes — **customizing, not your code, but on objects you've authored**
4. **D01-OBPM4-SEPA-EVENT05**: 1 row added to TFPM042FB — **customizing, not your code**

**My ask**: do you want to review:
- (a) Only #1 + #2 (your code/objects)?
- (b) #1 + #2 + #3 (everything in the BAdI ecosystem you authored)?
- (c) #1 + #2 + #3 + #4 (all transports in the change)?

Your time scope. (a) is minimum, (c) is maximum.

## Q5 — Vendor edge cases you want tested

The 32-component map specifies test cases (Marlies's 10 production cases + standard edge cases). But you have institutional memory of edge cases nobody else knows:
- Vendors with name > 35 chars (so Pattern A fix gets exercised)
- Vendors with special characters in address (char filter Layer 3)
- Alt-payee (LFB1.LNRZB) scenarios for Worldlink CITI
- One-time vendors (FPAYH-GPA1T='14') with BSEC-only address
- French SEPA vs SEPA-extended (CY/CH/NO/MC/IS — included in CITIPMW SEPA list)

**My ask**: 3-5 specific vendor scenarios you want to see in V000+V001 parallel test before cutover. Vendor IDs if you remember any.

## Q6 — Anything else you'd flag

Open question: is there any UNESCO-specific gotcha in DMEE we should know about that isn't in the documentation or code comments? (e.g., "we tried X in 2019 and it broke because Y").

## Format of the call

- **30 min** — focused on Q1-Q6, decisions binary where possible
- **Output**: written notes confirming Pattern A choice + retrofit method + review scope. Pablo takes notes, sends Nicolas a 1-pager confirming after the call.
- **Attendees**: Pablo + Nicolas (+ optional Marlies if free)
- **When**: Tue 29 Apr 16:00 / Wed 30 Apr 10:00 / Thu 1 May 14:00 (Paris time)
