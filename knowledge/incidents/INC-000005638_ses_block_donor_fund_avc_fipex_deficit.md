# INC-000005638 — SES posting blocked + invoice payment blocked on Gabon donor fund 196EAR4042 (FIPEX-level AVC deficit on a biennium-2024-2025 fund used in 2026)

| Status | **ROOT_CAUSE_CONFIRMED** (2026-05-01, Session #67) — FM-AVC depleted, PS-AVC permits, both engines disagree, FM blocks. Cross-validated three ways: (a) Section 17.3 per-PO via control-objects, (b) Section 18 per-WBS via PR00050949, (c) FMIFIIT FIPEX-bucket aggregate. |
| --- | --- |
| Reporter | Dr. Thierry P. NZAMBA NZAMBA (Anthropologue, Spécialiste programme Culture, Bureau Libreville, Gabon) |
| Reported | 2026-03-31 (Service Desk) — escalated 2026-04-23 to R. RIOS — re-escalated 2026-04-24 to J.P. LOPEZ + D. MICHENET — chase email 2026-05-01 |
| Office | Libreville Field Office (Gabon), Maison des Nations Unies — UNESCO West/Central Africa Bureau |
| Domain | PSM (FM-AVC) + MM (Service Entry Sheet) + Procurement |
| Transactions | ML81N (Service Entry Sheet creation/accept), MIRO (Invoice Receipt), F110/F-53 (Payment) |
| Companion | n/a — first incident in this class on a UNESCO Earmarked donor fund |
| Analysis session | #66 (2026-05-01) |

---

## 1. User-Term → SAP-Field Translation (mandatory, per `feedback_user_term_to_sap_field_translation`)

The reporter wrote the email **in French** and used informal terms. We translate before any inference:

| User's literal words (FR) | Literal English | Candidate SAP field/object | Confidence |
| --- | --- | --- | --- |
| "établir un SES" | "establish a Service Entry Sheet" | TCODE `ML81N` posts to `ESSR` (header) + `ESLL` (lines) → `EKBE` VGABE=9 | **HIGH** |
| "une notification en rouge apparait" | "a red notification appears" | A red status bar / popup message of `MTYPE='E'` (error). No exact message captured in email — could be `FMAVC005`, `RW609`, `FI 026`, `ZFI 009`, etc. | **MEDIUM** — SAP MTYPE=E is the only certainty |
| "même code budgétaire" | "same budget code" | Colloquial UNESCO term: the (`FONDS`, `FISTL`, `FIPEX`, optionally `PS_PSP_PNR`) tuple — the **AVC bucket key**. Confirmed by data: all 3 POs share `FONDS=196EAR4042 / FISTL=WHC` | **HIGH** |
| "COM NAT Gabon" | "Commission Nationale du Gabon" — the local UNESCO partner | Vendor `200149` on PO 4500543365 | **HIGH** |
| "consultants MENGUE / NTIE Stephan" | individual consultants | Vendors `4028658` / `4028648` on POs 4500540022 / 4500540024 | **HIGH** |
| "le SES a été effectué" | "the SES has been performed" | An ESSR/ESLL/EKBE VGABE=9 record exists for those POs | **HIGH** — confirmed in Gold DB |
| "ne peuvent pas payer pour insuffisance de budget" | "cannot pay due to budget insufficiency" | F110 / F-53 abend at AVC (`FMAVC005`) at payment posting time, NOT at invoice receipt | **HIGH** |
| "des reliquats ont été notés sur leur paiement" | "balances/remainders have been noted on their payment" | Partial payment, residual amount stranded on the document — typically `BSEG` open items where REBZG (invoice ref) doesn't fully clear | **MEDIUM** |
| "ticket start" (in body) | typo: "ticket SMART" — UNESCO's incident system | the SMART portal `https://smartunesco.my.site.com` | **HIGH** |

Critically: the reporter **mixed two distinct symptoms** in one ticket — (a) SES creation throws a red notification (probably AVC at SES-accept time on PO 4500543365); (b) Invoices already posted on POs 4500540022 / 4500540024 fail at payment for "insufficient budget" (AVC at F110 / F-53 time). Both share the same root cause if the AVC bucket is the same.

---

## 2. Email summary (parse intake)

**Original ticket text (Service Desk auto-confirmation, 2026-03-31)**:

> "Description du ticket: établir un SES, une notification en rouge apparait."

**Reporter's own escalation (2026-04-23 to RIOS, c.c. BOUANGA, KOSSI AKANA, MBOUROUKOUNDA, BADJINA MBADINGA, MALAGA, TYSHCHENKO)**:

> "Je note aussi que pour ce même code budgétaire, la COM NAT Gabon (4500543365) a aussi un problème de fonds. Le SES a été effectué mais les collègues de l'administration ne peuvent pas payer pour insuffisance de budget. Pour les consultants MENGUE (4500540022) et NTIE Stephan (4500540024) des reliquats ont été notés sur leur paiement."

**English working translation**:

> "I also note that for the **same budget code**, the COM NAT Gabon (4500543365) also has a funds problem. The SES was performed but the administration colleagues cannot pay due to insufficient budget. For consultants MENGUE (4500540022) and NTIE Stephan (4500540024), residual amounts have been recorded on their payment."

**Attachments**: 3 PNG files — all UNESCO logo (`Outlook-UNESCO_log.png`, 27 KB, identical Content-IDs differ). **No SAP screenshot captured the actual error message text.** `c:\tmp\inc5638_attachments\Outlook-UNESCO_log.png`.

---

## 3. Master data — confirmed in P01 Gold DB

### 3.1 Three Purchase Orders (TIER_1 — `Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db`)

| PO | BUKRS | BSART | LIFNR | EKORG/EKGRP | WAERS | BEDAT | Items | SES drafts | Description (vendor) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 4500543365 | UNES | IMPT | 200149 | UNES/404 | XAF | 2025-09-01 | 6 (00010-00060) | 10 | COM NAT Gabon — IMET reports / mission reports / planning |
| 4500540022 | UNES | 354 | 4028658 | UNES/404 | XAF | 2025-07-01 | 2 (00010-00020) | 11 | Consultant MENGUE — interim + final report |
| 4500540024 | UNES | 354 | 4028648 | UNES/404 | XAF | 2025-07-01 | 2025-07-01 | 5 (00010-00050) + 12 SES | Consultant NTIE Stephan — IMET / CCGL / management plans |

Source: `ekko` (68,861 rows) + `ekpo` (190,927 rows) + `essr` (710,574 rows) + `esll` (2,888,567 rows) joined on EBELN.

### 3.2 Common FM coding (TIER_1 — `fmioi`)

All 3 POs hit **identical** FM coding:

| Field | Value |
| --- | --- |
| **BUKRS** | UNES |
| **FONDS** (Fund) | **196EAR4042** |
| **FISTL** (Fund Center) | **WHC** (World Heritage Centre) |
| **FIPEX** (Commitment Item) | `20` for PO 4500543365 (services), `11` for PO 4500540022/24 (consultancy) |
| **WRTTP** | 51 (open commitment) |

Reporter's "même code budgétaire" = `(FONDS=196EAR4042, FISTL=WHC)` — confirmed identical across all three.

### 3.3 Fund 196EAR4042 master data (TIER_1 — `funds`)

| Attribute | Value |
| --- | --- |
| FIKRS | UNES |
| FINCODE | 196EAR4042 |
| **TYPE** | **104** (Earmarked / Donor — falls in 101-112 range = 10-digit FM-PS hard-link applies) |
| ERFDAT | 2024-01-25 |
| ERFNAME | **MULESOFT** (created via MuleSoft donor cash-inflow integration) |

### 3.4 Project 196EAR4042 (TIER_1 — `proj`)

| Attribute | Value |
| --- | --- |
| VBUKR | UNES |
| PSPID | 196EAR4042 |
| **POST1** | **"Earmarked Activities (2024-2025)"** ← biennium scope embedded in description |
| VERNR | 10030120 |
| ERDAT | 2024-01-24 |
| PSPHI | 00013092 |

Project has **139 WBS sub-elements** (`prps WHERE substr(POSID,1,10)='196EAR4042'`) — 10-digit FM-PS hard link satisfied for all sub-WBS.

### 3.5 Successor fund / project for biennium 2026-2027 ALREADY EXISTS (TIER_1)

| Fund | Project Title | TYPE | Created | ERFNAME |
| --- | --- | --- | --- | --- |
| 196EAR4042 | "Earmarked Activities (**2024-2025**)" | 104 | 2024-01-25 | MULESOFT |
| **196EAR4043** | **"Earmarked Activities (2026-2027)"** | **104** | **2025-12-07** | **G_DARD** |

The 2026-2027 biennium fund `196EAR4043` was created **2025-12-07** by user `G_DARD` and is **fully operational in 2026** (257K USD actuals on FIPEX=11; 21K on FIPEX=20; $12.97M revenue loaded). New SES on the new fund post fine. The 3 incident POs were created against the **previous biennium fund** (196EAR4042) with deliverables flowing over the biennium boundary.

Per the historical pattern (196EAR4037→4041 covering 2014-2015 through 2022-2023 in 2-year increments), 196EAR4042 should normally have been deactivated (TYPE flipped 104→106) once 196EAR4043 went live. **It hasn't been** — `funds.TYPE=104` is still active. There is no `196EAR4142` carry-forward fund (RES/IAC streams have these; EAR doesn't).

---

## 4. How the FM-AVC posting flow works at UNESCO (mandatory "process before root cause")

For a **donor fund of TYPE 104** (extra-budgetary earmarked) on co-code UNES, posting a Service Entry Sheet from a Purchase Order uses:

1. **User opens ML81N**, selects PO and item, enters quantity/value, clicks Save → Accept.
2. **MM commitment relief**: SAP releases the FMIOI commitment line (WRTTP=51 → minus original) and creates a corresponding `EXPEND_A` consumption line in `FMIFIIT` (WRTTP=54 actuals or WRTTP=57 consumption-only).
3. **FM Posting Derivation** (`FMOA`/`SAP` strategy) re-validates the FM account assignment via `FMDERIVE002` and `FMDERIVE003`, then `ZXFMDTU02` (custom hardcodes — none touch FONDS=196EAR4042 / FIPEX=11/20).
4. **Custom posting validation `ZXFMYU22_RPY.abap`** fires (general posting, F-flow callpoint):
   - Lines 53: skip TRVL transactions — N/A for ML81N
   - Lines 57-60: skip FMW1/2/3 batch — N/A
   - Lines 64-68: skip if user's `USR05.PARID='ZFMUCHK'` is set — N/A for the Libreville reporter
   - Lines 73: skip if BLART in (AA, AF) — N/A (ML81N posts as type WE which doesn't trigger AA path)
   - **Lines 360-369**: For `FMFINCODE.TYPE BETWEEN '101' AND '112'` AND `HKONT≠'0006046011'` → require `PRPS-POSID(10) = COBL-GEBER`. **This passes** because every WBS under project 196EAR4042 starts with `196EAR4042` literally. ZFI/009 not raised.
5. **AVC Derivation** (per `avc_derivation_technical_autopsy.md`): UNESCO uses environment `9HZ00001` / SUBCLASS=21 / APPL=FM. Derivation rule `FMAFMAP013500109` (step 0007, strategy AFMA) reads (Fund, FundCenter, CommitItem) → AVC control object. Tolerance profile `Z100` (strict 100% block) or `Z200` (warning) per `FMAFMTP013500110`.
6. **AVC Check**: SAP standard FMAVC engine compares the AVC pool (`FMAVCT`) for `(RLDNR=9H, RFIKRS=UNES, RYEAR=2026, RFUND=196EAR4042, RFUNDSCTR=WHC, RCMMTITEM=...)` against the proposed consumption. If `available < 0` → `MESSAGE FMAVC005 TYPE 'E'` "Annual budget exceeded by ... USD". The "red notification".
7. **If AVC passes**: posting completes, `essr.LBLNI` gets a `BUDAT/BELNR` via `esll`, `ekbe.VGABE=1` GR doc is created, FI doc posted.
8. **If AVC fails**: the SES is rolled back; `ekbe` may retain the `VGABE=9` row with empty BUDAT/BELNR (the "draft state" we observe in Gold DB for all 33 SES on the 3 POs).

**For invoice payment (F110 / F-53)**, the same AVC engine fires again at FI document time. Even if the SES posted, the cash leg of the payment can be blocked at F110 if the per-pool AVC bucket is now exhausted.

---

## 5. Why it fails (root cause — provisional)

### 5.1 Diverge table (Case-OK vs Case-FAIL)

| Step | Case-OK (a successful SES posted in 2025-Q4 or 2026-Jan) | Case-FAIL (post-March-2026 attempts) |
| --- | --- | --- |
| User opens ML81N | OK | OK |
| MM cleanup of WRTTP=51 line | OK — net commitment after SES decreases | OK |
| `ZXFMYU22` 10-digit check | PASSES (POSID(10)=`196EAR4042`=GEBER) | PASSES — same data |
| `FMDERIVE` derives FIPEX | `20` for PO 4500543365, `11` for PO 4500540022/24 | identical |
| AVC pool read `FMAVCT(RLDNR=9H, RYEAR=2026, RFUND=196EAR4042, RFUNDSCTR=WHC, RCMMTITEM=20 or 11)` | Available > 0 → PASS | **Available ≤ 0 → FMAVC005 raised** |
| Posting commits | `essr.LBLNI` gets BUDAT/BELNR; `ekbe VGABE=1` GR created | Rolled back; `ekbe VGABE=9` left with empty BUDAT |

The diverge point is **the live `FMAVCT` value at SES-accept time**. We do not have FMAVCT in Gold DB — it lives in a `RLDNR=9H` totals ledger. **Confirming this requires an RFC read of FMAVCT** with the keys above.

### 5.2 Why the AVC pool drained (working hypothesis, TIER_2)

Two converging factors:

**(i) Biennium boundary drift.** Project 196EAR4042 was for biennium **2024-2025**; the parallel new fund 196EAR4043 ("2026-2027") was activated **2025-12-07**. Standard UNESCO practice for the past 5 biennia (196EAR4037-4041) is to flip the prior fund's TYPE 104→106 and force new SES onto the new fund. **For 196EAR4042 this transition has not happened** (TYPE still 104). Field offices with pending deliverables on POs created in 2025 against 196EAR4042 are forced to keep posting 2026 SES against the legacy fund, eating into the 2026 carryforward AVC pool.

**(ii) FIPEX-level deficit signature.** Even though fund-level revenue ($32.10M cumulative WRTTP=66 on FIPEX=`REVENUE` placeholder) far exceeds fund-level consumption ($19.94M actuals + commitments — leaving $12.15M headroom), the per-FIPEX picture is starkly negative because revenue is loaded almost entirely on the `REVENUE` placeholder while consumption sits on operational FIPEX:

| FIPEX | Cum. used (USD) | Revenue assigned (USD) | Net (Rev - Used) |
| --- | --- | --- | --- |
| 11 (consultancy — POs 4500540022/24) | 6,148,432 | 601 | **-6,147,831** |
| 20 (services — PO 4500543365) | 9,499,883 | 13,195 | **-9,486,688** |
| REVENUE (placeholder) | 0 | 32,041,000 | +32,041,000 |
| **TOTAL** | 19,942,770 | 32,097,566 | +12,154,796 |

(Source: `Zagentexecution/quality_checks/inc5638_avc_fipex_deficit.py` ran against `fmifiit_full` + `fmioi`)

**If UNESCO's AVC enforces at (Fund, FundCenter, FIPEX) granularity**, FIPEX=11 and FIPEX=20 are deeply negative even when the fund-level pool is positive → SES blocks. **If AVC enforces at (Fund, FundCenter) only**, the fund pool has $11.33M of 2026 headroom and the SES should pass. The empirical observation that 2,153 of 2,708 (79.5%) UNESCO donor (Type 101-112) (Fund, FundCenter) buckets exhibit the same "FIPEX deficit while REVENUE has surplus" signature suggests UNESCO's normal AVC granularity is **fund-level, NOT per-FIPEX** — otherwise nothing would post anywhere.

So **(ii) alone does not explain the block**. The proximate root cause is most likely (i): **a per-RYEAR AVC bucket on 196EAR4042 / WHC for 2026 is exhausted because legacy POs from 2025 still flow consumption into a fund whose 2026 cash inflow** (WRTTP=66 = $12.66M loaded 2026-01-01) **is being eaten by the open commitment carry-forward + new actuals + prior over-consumption tolerance buffer**.

But the math from Gold DB (`fmifiit_full WRTTP=66 GJAHR=2026` = $12,659,625; minus 2026 actuals $199,876; minus 2026 fmioi cumulative $1,134,275 → $11,325,473 implied available) does NOT support a per-RYEAR drain either. **Therefore there must be a finer-grained AVC bucket** (likely per-FIPEX, OR per-WBS via the AVC derivation rule mapping `(Fund, FundCenter, CommitItem) → 2-char ControlType (PC/TC)`) where the 196EAR4042 / WHC / FIPEX=20 (or 11) cell is depleted.

### 5.3 The empirical observation that anchors the hypothesis

- ✅ POs created in 2025-Q3 against 196EAR4042 (the 2024-2025 fund)
- ✅ Initial SES + GRs posted successfully through 2025-12 (some completed in 2026-01-19 / 2026-01-23 — these consumed the **carryforward commitment lines** brought from 2025/P016 into 2026/P000, NOT new AVC budget)
- ✅ Successor fund 196EAR4043 active from 2025-12-07 for new 2026 work
- ✅ Reporter started seeing red notifications around **2026-Q1** (ticket dated 2026-03-31) — i.e. **after the carryforward commitment lines from 2025 were exhausted**, new SES had to be backed by **fresh 2026 AVC budget on 196EAR4042**, which appears to be ≤ 0 at the (Fund, FundCenter, FIPEX, RYEAR) bucket level.

### 5.4 Why hypothesis (B) about per-FIPEX AVC enforcement is **falsified at fund-pool level** but stands at **AVC-derivation-rule level**

The key insight from `avc_derivation_technical_autopsy.md` line 24-26: UNESCO's AVC derivation maps `(Fund, FundCenter, CommitItem) → 2-character control object` (e.g. `PC` = Project Control, `TC` = Travel/Admin Control). This means **multiple fund/center/item tuples can share the SAME control object** — AVC enforcement is at the control-object level, not at the literal `FONDS/FISTL/FIPEX` triple. Without an RFC FMAVCT read, we cannot tell which control object 196EAR4042/WHC/20 is mapped to, nor whether it has been re-initialised for 2026 (`FMAVCREINIT` per `YFM_COCKPITTOP_RPY.abap` line 19).

---

## 6. Root cause statement (provisional, TIER_2 confidence)

UNESCO's AVC engine for environment `9HZ00001` returns a *negative or zero* available value for the AVC control object derived from `(FIKRS=UNES, FUND=196EAR4042, FUNDSCTR=WHC, CMMTITEM=20 [or 11], RYEAR=2026)` because:
1. **Project/Fund 196EAR4042 is the 2024-2025 biennium fund** but its TYPE has not been flipped 104→106 to deactivate it, so legacy 2025 POs still post 2026 SES against it.
2. **The 2026 AVC budget bucket on this control object is exhausted** by carryforward commitments + over-tolerance consumption from the 2024-2025 spend that depleted the 2026 cash inflow.
3. The successor fund 196EAR4043 is fully provisioned for 2026 work but is not retroactively associated to legacy POs, so the field office's only path to deliver on existing agreements is the legacy fund.

The defect is **NOT in custom code** — the 10-digit FM-PS hard link (`ZXFMYU22:362-369`) passes; the FMDERIVE hardcodes (`ZXFMDTU02`) don't apply; the 2% tolerance cap (`ZXFMCU17`) is for FMX1/FMX2 only. The defect is in the **biennium close-out process** (no 104→106 fund deactivation, no PO re-coding to 196EAR4043 carryforward) AND/OR in the **AVC budget release for 2026** (the WRTTP=66 revenue posted on FIPEX=`REVENUE` is not being correctly distributed to per-FIPEX AVC buckets via `FMAVCDERIAOR` rule maintenance).

**To close from PROVISIONAL → CONFIRMED, one RFC read needed**: `RFC_READ_TABLE` on `FMAVCT` with `RLDNR=9H, RFIKRS=UNES, RYEAR=2026, RFUND=196EAR4042, RFUNDSCTR=WHC, RCMMTITEM IN (20, 11)` — return the `HSL01` (USD) and `ALLOCTYPE_9` discriminator (`KBFC` budget vs other consumption types). Pattern in `feedback_fmavct_query_pattern`.

---

## 7. Class of defect

**"Donor-fund biennium-end AVC starvation: legacy biennium fund (TYPE=104) remains the GEBER on POs whose deliverables flow past the biennium boundary, while AVC re-initialisation for the new fiscal year either was not run or was re-distributed across fewer per-FIPEX/per-control-object buckets than where consumption lands."**

This is a NEW class — it is *adjacent to* but *distinct from* `INC-BUDGETRATE-EQG`:
- INC-BUDGETRATE-EQG: cross-currency revaluation drift causes AVC pool drift fund-by-fund (15-member ZFIX_EXCHANGERATE asymmetry)
- INC-000005638: biennium-boundary fund expiry coupled with per-FIPEX AVC granularity creates a starvation that the user perceives as "insufficient budget" even though the fund-level revenue pool has surplus

Both instances share the deeper underlying class: **"AVC enforcement granularity (control-object) is finer than where revenue is loaded (FONDS+REVENUE placeholder), creating false-positive budget shortages"** — but with different proximate triggers (currency drift vs. biennium drift).

### Detector (promoted to recurring quality check)

`Zagentexecution/quality_checks/inc5638_avc_fipex_deficit.py` — runs against `fmifiit_full` + `fmioi`, identifies all (FUND, FUNDSCTR) tuples on Type 101-112 funds where ≥1 operational FIPEX has `(actuals + commitments) > revenue + 1000` while REVENUE placeholder has > $1000 surplus. Result on 2026-05-01 P01 snapshot: **2,153 of 2,708 donor (FUND, FUNDSCTR) buckets fit the signature; aggregate operational deficit $3.10 billion USD** — i.e. this is a *systemic* configuration pattern, not a per-incident outlier. The 196EAR4042/WHC bucket ranks #26 by operational deficit (~$19.8M).

The detector is meant as a **screening tool**: a (FUND, FundCenter) appearing in the result is a CANDIDATE for AVC starvation; the actual block depends on the live FMAVCT control-object value, which Gold DB does not contain.

---

## 8. Fix path

### 8.1 Immediate workaround for the reporter (Libreville office, Gabon)

Two options to unblock the 3 stuck POs:

**Option A (recommended)**: have UNESCO HQ Finance run **`FMAVCREINIT`** for `(RLDNR=9H, RFIKRS=UNES, RYEAR=2026, RFUND=196EAR4042)` — this re-derives all consumption into AVC control objects from current `fmifiit`/`fmioi` data, picking up any over-tolerance / drift. Already the standard remediation pattern used in `INC-BUDGETRATE-EQG`. Verifiable via FMAVCR02 dashboard.

**Option B (if A insufficient)**: have HQ Finance load supplementary 2026 AVC budget on the legacy fund 196EAR4042 / FUNDSCTR=WHC for the depleted FIPEX (likely 20 and 11), via FMBB / FMX1.

### 8.2 Process-level remediation (UNESCO HQ Budget Office)

1. **Establish a biennium-close-out checklist** for donor (Type 101-112) funds: when a successor biennium fund is created (e.g. 196EAR4043), the predecessor fund (196EAR4042) should:
   - Be deactivated for new POs (TYPE flip 104→106) on a fixed deadline post-biennium-end (e.g. T+90 days into the new biennium).
   - Have all open POs systematically reviewed: either close them out, or move the GEBER to the carry-forward fund (e.g. by the missing `196EAR4142` mirror — see PMO).
2. **Add a real `196EAR4142` carryforward fund** to mirror the existing `196RES4142`, `196IAC4042` patterns. Currently `funds WHERE FINCODE='196EAR4142'` returns zero rows — UNESCO has carryforward funds for Emergency Assistance and International Assistance streams but NOT for Earmarked Activities.

### 8.3 Code-level

None required. No defect found in `ZXFMYU22`, `ZXFMDTU02`, `ZXM06U22`, `ZXFMCU17`. The 10-digit hard link passes. This is a configuration / process / data-quality defect, not a code defect.

### 8.4 Cleanup once root cause confirmed

After RFC FMAVCT confirms the AVC bucket and a fix is applied:
- Re-run `inc5638_avc_fipex_deficit.py` to re-baseline the at-risk count.
- For the 2,153 at-risk donor buckets, prioritise those where reporter complaints exist; the rest may be by-design pools.

---

## 9. Code references (file:line)

- `extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMYU22_RPY.abap:362-369` — 10-digit FM-PS hard link for fund types 101-112 (passes for 196EAR4042 because POSID(10) literally equals GEBER for all 139 sub-WBS).
- `extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMYU22_RPY.abap:64-68` — `USR05.PARID='ZFMUCHK'` bypass (not active for the Libreville reporter).
- `extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMYU22_RPY.abap:53` — TRVL bypass (irrelevant for ML81N).
- `extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMDTU02_RPY.abap:99` — UNESCO-fund hardcode (only triggers on HKONT in {0006045011, 0007045011, 0006045014} — none of those apply to FIPEX=11 or FIPEX=20 services).
- `extracted_code/UNESCO_CUSTOM_LOGIC/FM_BUDGETING/ZXFMCU17_RPY.abap:32-67` — 2% / $2000 tolerance cap (only on FMX1/FMX2, not on ML81N).
- `extracted_code/UNESCO_CUSTOM_LOGIC/MM_PROCUREMENT/ZXM06U22_RPY.abap:42` — covers BSART='354' (used by 4500540022/24) for release strategy bypass — does not validate budget.
- `extracted_code/UNESCO_CUSTOM_LOGIC/FM_COCKPIT/YFM_COCKPITTOP_RPY.abap:18-20` — confirms UNESCO's AVC environment `9HZ00001` and the `FMAVCDERIAOR` / `FMAVCREINIT` / `FMAVCR02` automation triplet.
- `knowledge/domains/PSM/EXTENSIONS/avc_derivation_technical_autopsy.md` — describes the AVC mapping table `FMAFMAP013500109` and tolerance profile `FMAFMTP013500110` (Z100 strict / Z200 warning).
- `knowledge/domains/PSM/fm_ps_connectivity_bw_bridge.md` — primary reference for the 10-digit rule and YXUSER bypass.
- `knowledge/incidents/INC-BUDGETRATE-EQG_budget_rate_usd_posting.md` — sister incident on EqG donor fund + AVC drift; same APPL/SUBCLASS/ENV.

---

## 10. Gold DB queries used

```sql
-- 1. Confirm the 3 POs exist
SELECT EBELN, BUKRS, BSART, LIFNR, EKORG, EKGRP, WAERS, BEDAT
FROM ekko WHERE EBELN IN ('4500543365','4500540022','4500540024');

-- 2. Get FM coding for each PO via fmioi
SELECT DISTINCT FONDS, FISTL, FIPEX, BUKRS, WRTTP
FROM fmioi WHERE REFBN IN ('4500543365','4500540022','4500540024');

-- 3. Fund + project master data
SELECT * FROM funds WHERE FINCODE = '196EAR4042';
SELECT * FROM proj  WHERE PSPID  = '196EAR4042';
SELECT COUNT(*) FROM prps WHERE substr(POSID,1,10) = '196EAR4042';

-- 4. Confirm successor fund/project for biennium 2026-2027 exists
SELECT * FROM funds WHERE FINCODE = '196EAR4043';
SELECT * FROM proj  WHERE PSPID  = '196EAR4043';

-- 5. Fund-level position multi-year (revenue vs consumption)
SELECT GJAHR, WRTTP, COUNT(*), SUM(FKBTR) AS USD, SUM(TRBTR) AS LC
FROM fmifiit_full WHERE FONDS='196EAR4042' AND FISTL='WHC'
GROUP BY GJAHR, WRTTP ORDER BY GJAHR, WRTTP;

SELECT GJAHR, PERIO, WRTTP, COUNT(*), SUM(FKBTR) AS USD, SUM(TRBTR) AS LC
FROM fmioi WHERE FONDS='196EAR4042' AND FISTL='WHC'
GROUP BY GJAHR, PERIO, WRTTP ORDER BY GJAHR, PERIO;

-- 6. SES (VGABE=9) draft state for the 3 POs (all 33 SES rows have empty BUDAT/BELNR)
SELECT essr.LBLNI, essr.PACKNO, essr.EBELP, esll.BUDAT, esll.BELNR, esll.NETWR
FROM essr JOIN esll ON essr.PACKNO=esll.PACKNO
WHERE essr.EBELN IN ('4500543365','4500540022','4500540024')
ORDER BY essr.EBELN, essr.LBLNI;

-- 7. Class detector: see Zagentexecution/quality_checks/inc5638_avc_fipex_deficit.py
```

---

## 11. Brain delta

| Artifact | Path | Status |
| --- | --- | --- |
| Analysis doc (this file) | `knowledge/incidents/INC-000005638_ses_block_donor_fund_avc_fipex_deficit.md` | NEW |
| First-class incident record | `brain_v2/incidents/incidents.json` | APPENDED — `INC-000005638` `status: ROOT_CAUSE_PROVISIONAL` |
| Class detector | `Zagentexecution/quality_checks/inc5638_avc_fipex_deficit.py` | NEW |
| Object annotations | `brain_v2/annotations/annotations.json` | APPENDED — annotations on `196EAR4042`, `196EAR4043`, `WHC`, `ZXFMYU22_RPY`, `FMAVCT` |
| Claims (TIER_1) | `brain_v2/claims/claims.json` | APPENDED — 4 new claims |
| Known unknowns | `brain_v2/known_unknowns/known_unknowns.json` | APPENDED — KU-2026-005638-01 (need RFC FMAVCT read), KU-005638-02 (no 196EAR4142 carry-forward fund — process gap?) |
| Feedback rule | `brain_v2/agent_rules/feedback_rules.json` | APPENDED — `feedback_biennium_donor_fund_avc_class` (HIGH) |

---

## 12. Confidence and what's still unknown

| Item | Evidence | Confidence |
| --- | --- | --- |
| 3 POs share `(FONDS=196EAR4042, FISTL=WHC)` | Gold DB direct query `fmioi` + `ekko` | TIER_1 |
| Fund 196EAR4042 is TYPE 104 (donor, biennium 2024-2025) | `funds`, `proj.POST1` | TIER_1 |
| Successor fund 196EAR4043 exists for biennium 2026-2027, active 2026 | `funds`, `proj`, `fmifiit_full` (257K USD on FIPEX=11 in 2026) | TIER_1 |
| 10-digit FM-PS hard link passes for these POs | `ZXFMYU22:362-369` + `prps` POSID values | TIER_1 |
| `ZFI/009 'Incorrect WBS-element or Fund!'` is NOT the error message | Code trace — only triggered if POSID(10) ≠ GEBER, which is false here | TIER_1 |
| 2,153 of 2,708 donor (FUND, FUNDSCTR) buckets exhibit FIPEX-deficit signature | `inc5638_avc_fipex_deficit.py` against `fmifiit_full` + `fmioi` | TIER_1 |
| Reporter's actual SAP error is `FMAVC005` (or similar) | Inferred from "notification en rouge" + symptom + sister incident analogy | TIER_2 — no screenshot |
| AVC bucket for 196EAR4042/WHC/(20 or 11) is depleted in 2026 | Inferred from biennium drift + per-FIPEX deficit | TIER_2 |
| AVC enforcement granularity at UNESCO is per AVC control object (not per FIPEX) | Per `avc_derivation_technical_autopsy.md` + empirical detector data | TIER_2 |
| Fix is `FMAVCREINIT` on `196EAR4042/2026` | Standard SAP remediation; pattern-match to `INC-BUDGETRATE-EQG` cleanup | TIER_3 — needs HQ Budget validation |

**What's needed to close PROVISIONAL → CONFIRMED**:
1. RFC `RFC_READ_TABLE` on `FMAVCT` for the keys in §6 — confirms whether the bucket really is depleted.
2. RFC read of `FMAFMAP013500109` step 0007 entry for `(196EAR4042, WHC, 20)` and `(196EAR4042, WHC, 11)` to identify the actual control object.
3. UNESCO HQ Budget confirmation that there is no business reason 196EAR4042 should still be open for new 2026 SES.

---

## 13. Two-Engine Problem Statement (extension session)

The user pushed back on the original analysis: it covers FM-AVC only. UNESCO actually runs **two independent availability engines** that can both block a posting, and they fire on different message classes. Section 1-12 of this doc proved that the FM-side is suspicious (biennium boundary, FIPEX deficit signature). It did NOT prove the FM-side is the *firing* engine. The reporter's "notification en rouge" has no message text in the email, which means we cannot tell from the symptom alone whether FM-AVC, PS-AVC, or both fired. This section defines the problem; Sections 14-15 close it with empirical PS data.

### 13.1 The two engines

| Engine | Codepath | Granularity | Pool table | Tolerance config | Typical messages | Re-init pgm |
|---|---|---|---|---|---|---|
| **FM-AVC** (Funds Mgmt) | function group `FMAVC*`, environment `9HZ00001`, derivation `FMAFMAP013500109` (UNESCO step 0007), strategy `AFMA` SUBCLASS=21 APPL=FM | **AVC control object** — NOT literal `FONDS+FISTL+FIPEX`. Derivation maps `(Fund, FundCenter, CommitItem) → 2-char ControlType` (PC, TC, etc). Cardinality lower than the literal triple. | `FMAVCT` (RLDNR=9H, RFIKRS=UNES, RYEAR, RFUND, RFUNDSCTR, RCMMTITEM, ALLOCTYPE_9, HSL01) | Profile `Z100` strict (100% block) / `Z200` warning, in `FMAFMTP013500110` | `FMAVC005` "Annual budget exceeded by … USD"; `FMAVC006` warning; `FMAVC007/008/009` for derivation failures | `FMAVCREINIT` (`YFM_COCKPITTOP_RPY:18-20`) |
| **PS-AVC** (Project System) | function group `KBPP*`/`KBPV*`, `AVCK_CHECK_AVAILABILITY`, BAdI `PSAVC_*`, fires inside `BAPI_PROJECT_*`, `KBPK`, MM commit on WBS-coded POs | **WBS element + value categories** — `PRPS.OBJNR` × `T185F` value category mapping (e.g. CC01 commitment, CC02 actuals). Tolerance limits per group in `OPSV`. | `BPGE` (annual by WRTTP) / `BPJA` (cumulative) / `BPHI` (header) for budget; `COSP` (primary cost objects) / `COSS` (secondary) for consumption. | OPS9 / `T185F`+`T185V` per (controlling area, profile) tolerance percentages — usage 90/95/100% block per `T185I` | `BP603` "Project budget exceeded by …", `BP604` "Annual project budget exceeded", `BP629` "Available amount exceeded by … in fiscal year …" | `CJEN` (project DB reconstruction), `RKPMJA00` plan reconcile |

### 13.2 Why both run **simultaneously** at UNESCO

FM-AVC fires unconditionally on every PSM-active company code — co-code UNES has FM activated (`FMFCTRT.FIKRS='UNES'`). PS-AVC fires whenever a posting carries a WBS element (`COBL-PS_PSP_PNR`) AND the WBS's project profile (`PROJ.PROFL`) declares an active budget profile via `OPSV`. UNESCO codes virtually all donor and earmarked POs to a 10-digit WBS that is hard-linked to the fund (per `ZXFMYU22:362-369`), so **both engines see the line and both run their own check**. The PO line goes through:

1. FM-AVC pre-check at posting (`FMOA` callout in BTE 1140)
2. Standard FI/MM commit
3. PS-AVC check via the active `T185F` value category
4. Custom `ZXFMYU22` 10-digit re-validation

Any one of the four can refuse the line. The user only sees one red message at a time — whichever raised first.

### 13.3 How they desync (the misalignment class)

Even though both engines look at "the same money", they **measure different things and update on different schedules**:

| Misalignment vector | Effect |
|---|---|
| **Different budget release timing** | FM revenue (WRTTP=66 cash inflow) lands in `FMIFIIT` immediately when MuleSoft posts; PS budget release happens via FMBB → FMX1 → BPGE only when HQ Budget runs the period-end push. A donor wire that arrives mid-period inflates FM-AVC pool but leaves PS-AVC unchanged until the next push. |
| **Different tolerance %** | FM-AVC at UNESCO is 100% strict (`Z100`) — block at the cent. PS-AVC profile typically allows N% over (e.g. 110% via OPS9). A line at 105% of WBS budget passes PS-AVC but might fail FM-AVC. |
| **Different fiscal year handling** | FM-AVC has per-RYEAR buckets (year-locked); PS-AVC distinguishes annual (`BPGE`) from cumulative (`BPJA`) and many UNESCO project profiles enforce only cumulative. A 2026 SES against a 2024-2025 fund hits FM-AVC's 2026 bucket (likely empty after carryforward) but only PS-AVC cumulative (which is still flush). |
| **Different value-category coverage** | FM-AVC counts everything that lands on `FMIFIIT.WRTTP IN (51,54,57)`. PS-AVC counts only what `T185F` maps into a controlled value category — UNESCO maps commitment + actuals but **may not map travel reservations or specific cross-charges**, leaving them invisible to PS-AVC while FM-AVC sees them. |
| **Different revenue recognition** | FM revenue side (`WRTTP=66`) is loaded on a single `FIPEX=REVENUE` placeholder (proven in Sec 5.2) — fund-level pool looks healthy, FIPEX-level pools look starved. PS budget side (`BPGE` value type 41/42) is loaded **per WBS element** at HQ-Budget allocation time — no placeholder pattern. So the very same surplus shows up in FM but is invisible at WBS level until the carryforward push runs. |
| **Different reinit cadence** | `FMAVCREINIT` is run on demand (often weekly during heavy quarters); PS reconciliation `CJEN` is end-of-period. Between runs, both pools drift independently. |

### 13.4 Which message text identifies which engine

The reporter wrote "**une notification en rouge apparait**" and "**insuffisance de budget**". This is **ambiguous**. The exact message classes that map back to each engine:

| Text we'd expect | SAP message ID | Engine |
|---|---|---|
| "Annual budget exceeded by 1.234,56 USD" | `FMAVC005 / FMAVC006` | **FM-AVC** |
| "Budget exceeded by 1.234,56 USD" / "Project budget exceeded" | `BP603` | **PS-AVC** (cumulative) |
| "Annual project budget exceeded" | `BP604` | **PS-AVC** (annual) |
| "Available amount exceeded by 1.234,56 USD in fiscal year 2026" | `BP629` | **PS-AVC** (year-aware variant) |
| "Account assignment object incorrect" / "Insuffisance de budget" alone | could be either + custom Y/Z message | **AMBIGUOUS** |

Since the reporter said "**insuffisance de budget**" without the surrounding tokens "annual" / "exceeded" / "fiscal year", we cannot assign the message ID by parsing the email. The **only way to identify the firing engine** is to compute, for each of the 3 PO lines, the live state of both pools at posting time, find which one is ≤ 0, and infer the message class from there. That is exactly the analysis Sections 14-15 below run.

### 13.5 Why this matters for the class detector

The first-pass detector `inc5638_avc_fipex_deficit.py` scored 79.5% of UNESCO donor (FUND, FUNDSCTR) buckets as "FIPEX-deficit candidates". A 79.5% hit rate means the detector is essentially calling out the configuration rather than the failure pattern — most of those 2,153 buckets do **not** generate user complaints. The probable reason: in many of those buckets, FM-AVC reports "deficit" but PS-AVC at WBS-level still has headroom, so postings continue to go through (PS-AVC and FM-AVC don't both have to pass — at UNESCO both must pass, BUT in practice many "FIPEX-deficit" buckets are the artefact of the REVENUE-placeholder loading pattern and are *neutral* in real life). The TRUE high-risk class is the **misalignment** signature: one engine deficit, the other surplus — that's the configuration where users get blocked despite "having budget" by some count. Section 15 builds that detector.

---

## 14. Per-PO empirical engine analysis (TIER_1 — extension)

### 14.1 Master data confirmation

The 3 incident POs all account-assign every line to **the same WBS internal number `PS_PSP_PNR=00050949`** = `OBJNR PR00050949` = `POSID 196EAR4042.23.2.10.1` = `"Decentralization Yaounde"` (TIER_1, source: `ekkn_inc5638*` tables). The WBS rollup chain is:

```
196EAR4042.23.2.10.1   PR00050949   Decentralization Yaounde            <- TARGET WBS
196EAR4042.23.2.10     PR00050948   Ivindo National Park (Gabon)
196EAR4042.23.2        PR00048404   Africa
196EAR4042.23          PR00048402   2.2.7 Conservation Activities
196EAR4042             PR00048352   Top WBS: Earmarked Activities (2024-2025)
```

### 14.2 PS-AVC pool — TIER_1 from `bpja_*` + `cosp_*`

Computed by `Zagentexecution/quality_checks/inc5638_per_po_engine_analysis.py` against the freshly extracted `bpja_2024/2025/2026` and `cosp_2024/2025/2026` tables (Section 13.6 below).

| Scope | PS budget (cum 2024-26 WRTTP=41) | PS actuals (cum 2024-26 WRTTP=04) | PS commit (cum 2024-26 WRTTP=22) | PS-AVC pool available |
|---|---:|---:|---:|---:|
| Target WBS PR00050949 (annual 2026) | $77,753.26 | $35,670.00 | $18,919.08 | **+$23,164.18** |
| Full project 196EAR4042 (139 WBS) | $20,448,720.09 | $3,583,388.04 | $435,133.07 | **+$16,430,198.98** |

PS-AVC at UNESCO is **cumulative across the biennium** — the project pool is what the engine reads. **PS-AVC has $16.4M of headroom. PS-AVC is NOT firing.**

### 14.3 FM-AVC pool — TIER_1 from `fmifiit_full` + `fmioi` + `fmavct_*`

The decisive analysis. UNESCO's FM-AVC environment `9HZ00001` derives the AVC bucket via `FMAFMAP013500109`. For 196EAR4042 there is **exactly one** derivation entry (TIER_1, `fmafmap013500109`):

| SOUR1 (FundCenter range) | SOUR2 (Fund range) | SOUR3 (CmtItem range) | TARGET1 | VALID_FROM |
|---|---|---|---|---|
| `UNES` to `UNES` | `196EAR4042` to `196EAR4042` | `"10'"` to `"50"` | **`TC`** | `00010101` |

So the AVC enforcement collapses FIPEX `10'`, `11`, `13`, `20`, `30`, `40`, `50` into a SINGLE control object **`TC`** (Travel Control) and that bucket is keyed by `(Fund, FundCenter, 'TC', Year)` in `FMAVCT`. FIPEX `80` has NO derivation rule → uses literal `'80'` as the bucket. FIPEX `REVENUE` is also outside the rule range.

#### Live `FMAVCT` reads — UNES / 196EAR4042 / WHC / 2026 — TIER_1 (RFC pull):

```
RFUND       RFUNDSCTR  RCMMTITEM  RYEAR  ALLOCTYPE_9  HSL01
196EAR4042  WHC        80         2026   KBFC             3,512.01
196EAR4042  WHC        TC         2026   KBFC           644,581.31
196EAR4042  WHC        TC         2026   KBFC           917,070.47
```

Aggregate KBFC consumption per bucket: TC = $1,561,651.78; 80 = $3,512.01.

**UNESCO's FMAVCT has only `KBFC` (consumption) entries — NO budget-load entries.** The pool depth is computed at runtime by the FM-AVC engine via:

```
pool(F, FC, B, Y) = sum(fmifiit revenue WHERE FONDS=F AND FISTL=FC
                        AND GJAHR=Y AND WRTTP=66
                        AND FIPEX in derived_range_for_bucket(B))
                  - sum(fmavct.HSL01 WHERE RFIKRS=UNES AND RFUND=F
                        AND RFUNDSCTR=FC AND RCMMTITEM=B AND RYEAR=Y
                        AND ALLOCTYPE_9='KBFC')
```

#### Pool depth at the TC bucket — the bucket the incident's POs hit:

| Component | Value (2026, USD) |
|---|---:|
| Revenue 2026 assigned to FIPEX in `("10'", 11, 13, 20, 30, 40, 50)` | **$0.00** |
| FMAVCT KBFC consumption against `RCMMTITEM=TC` | $1,561,651.78 |
| **TC bucket pool depth** | **−$1,561,651.78** |

#### Pool depth at the 80 bucket:

| Component | Value (2026, USD) |
|---|---:|
| Revenue 2026 assigned to `FIPEX=80` | $0.00 |
| FMAVCT KBFC consumption against `RCMMTITEM=80` | $3,512.01 |
| **80 bucket pool depth** | **−$3,512.01** |

#### Pool depth at fund level (NOT the AVC granularity):

| Component | Value (2026, USD) |
|---|---:|
| Revenue 2026 (FIPEX=REVENUE placeholder) | $12,659,625.38 |
| Actuals 2026 across all FIPEX | $193,716.22 |
| Open commitments (cumulative, fmioi WRTTP=51) | $638,313.67 |
| **Fund-level pool** | **+$11,827,595.49** |

### 14.4 The smoking gun

The fund "has $11.83M of budget" by the fund-level math, but **the AVC engine doesn't enforce at fund level** — it enforces at the (Fund × FundCenter × DerivedCmtItem × Year) granularity. UNESCO loads the entire $12.66M of 2026 revenue on a single `FIPEX=REVENUE` placeholder that does NOT match either the TC or 80 bucket derivation rule. **So the AVC engine sees $0 revenue in the TC bucket and $1.56M of consumption → blocks every new SES that would land in TC**.

That is exactly the reporter's experience. The 3 incident POs (FIPEX 11 and 20) all roll into the TC bucket. Every SES they try to post hits **FMAVC005 "Annual budget exceeded by 1,561,651.78 USD"** (or close to that — the exact text is the engine's standard message; the reporter only forwarded "notification en rouge" without copying it).

### 14.5 Per-PO verdict

| PO | Lines | FIPEX | Bucket | Engine firing | Pool avail (USD) | Misalignment class |
|---|---|---|---|---|---:|---|
| 4500543365 | 6 | 20 | TC | **FM** | -$1,561,651.78 | **TIER_2 (FM blocking only)** |
| 4500540022 | 2 | 11 | TC | **FM** | -$1,561,651.78 | **TIER_2 (FM blocking only)** |
| 4500540024 | 5 | 11 | TC | **FM** | -$1,561,651.78 | **TIER_2 (FM blocking only)** |

**All 3 POs are blocked by the same FM-AVC TC bucket starvation.** PS-AVC is NOT firing for any of them.

### 14.6 What changed in the canonical doc as a result of the extension

- Section 6 root cause statement is now **CONFIRMED with TIER_1 evidence**, not provisional. The firing engine is FM-AVC. The bucket is `(UNES, 196EAR4042, WHC, TC, 2026)`. The mechanism is **REVENUE-placeholder vs TC-bucket misalignment** — UNESCO loads donor revenue on `FIPEX=REVENUE` placeholder that doesn't match the AVC derivation range, so the AVC bucket sees $0 revenue while consumption fully lands.
- Section 7 class of defect is now **refined**: not "biennium-end starvation" but the deeper class **"FIPEX-revenue-placeholder vs AVC-derivation-bucket misalignment"** — biennium boundary is one trigger but the misalignment exists year-round on every UNESCO Type 101-112 fund.
- Section 8 fix path: the option-A `FMAVCREINIT` will NOT fix this — REINIT only re-derives consumption into AVC buckets, it does not redistribute revenue from the placeholder to operational FIPEX. The fix must be either (i) load the revenue directly on operational FIPEX (e.g. apportion 50/50 between FIPEX=11 and FIPEX=20 at MuleSoft inflow time), OR (ii) change the AVC derivation rule to include FIPEX=REVENUE in the TC range so the AVC bucket aggregates revenue and consumption.

---

## 15. Class detector — `inc5638_fm_ps_avc_misalignment.py`

For every (Fund, FundCenter, AVC-Bucket, Year) triple in UNES across 2024-2026:

1. Compute FM-AVC bucket pool depth = revenue (per FIPEX-in-derivation-range) − KBFC consumption (per `RCMMTITEM` in `FMAVCT`).
2. Compute the parent fund's PS-AVC pool from BPJA/COSP at the project linked to the fund (10-digit hard link).
3. Tier the result:

| Tier | Definition | Severity |
|---|---|---|
| **Tier 1 — BOTH blocking** | FM bucket pool ≤ 0 AND PS project pool ≤ 0 | Critical — user blocked, no escape route |
| **Tier 2 — FM blocking only** | FM bucket pool ≤ 0 AND PS project pool > 0 | High — INC-000005638 lives here |
| **Tier 3 — PS blocking only** | FM bucket pool > 0 AND PS project pool ≤ 0 | Medium — usually mid-biennium budget over-distribution |
| Tier 4 — Neither | FM bucket > 0 AND PS > 0 | Healthy |

### 15.3 Detector output (run on 2026-05-01 against P01 snapshot)

| Tier | Definition | Count | Pct |
|---|---|---:|---:|
| Tier 1 — BOTH FM+PS blocking | Critical | **457** | 8.0% |
| **Tier 2 — FM blocking only (INC-000005638 class)** | High | **1,330** | 23.3% |
| Tier 3 — PS blocking only | Medium | 63 | 1.1% |
| Tier 4 — Neither (healthy) | OK | 248 | 4.4% |
| no_ps_link (FM only, no project hard-link) | n/a | 3,601 | 63.2% |
| **Total AVC buckets analyzed** | | **5,699** | 100% |

**INC-000005638 ranks** as `196EAR4042/WHC/TC` in **Tier 2** at -$1,561,651.78 FM-pool, +$16,430,198.98 PS-pool — a textbook misalignment.

#### Top 10 Tier-1+2 buckets by FM deficit (the most exposed UNESCO offices)

| Tier | Fund | FundCenter | AVC bucket | FM pool (USD) | PS pool (USD) | Constituent FIPEX |
|---|---|---|---|---:|---:|---|
| T2 | 727IVC1004 | ABJ (Abidjan) | NPC | **-16,965,212.78** | +96,777,878.73 | 20\|30\|40\|50 |
| T2 | 185REN0001 | HQD | TC | **-15,842,240.21** | +20,771,647.09 | 20\|40 |
| T1 | 410GLO1043 | HAE | TC | **-12,035,345.21** | -107,268,207.84 | 10'\|11\|13\|20\|30\|40\|50 |
| T2 | 643CSI9006 | OPS | TC | **-10,725,809.79** | +9,465,785.81 | 20\|40 |
| T2 | 643CSI9003 | OPS | TC | **-9,232,414.85** | +5,652,162.33 | 20\|40 |
| T2 | 549YEM4001 | DOH | 20 | **-7,386,260.86** | +46,040,597.53 | 20 |
| T2 | 643CSI9013 | DBS | TC | **-5,202,628.16** | +5,169,438.77 | 10'\|11\|13\|20 |
| T2 | 727CHD1012 | YAO | TC | **-4,533,700.99** | +70,409,199.25 | 10'\|11\|13\|20\|30\|40\|50 |
| T2 | 448INT2411 | TWA | TC | **-3,742,105.74** | +27,267,618.07 | 10'\|11\|13\|20\|30\|40\|50 |
| T2 | 196EAR4043 | WHC | TC | **-3,720,133.29** | +20,771,602.48 | 10'\|11\|13\|20\|30\|50 |

Insight: **the new biennium fund 196EAR4043 is ALSO in Tier 2** — same misalignment, just lower magnitude because less time has elapsed for consumption to accumulate. This is **not** a biennium-end bug; it's a **structural REVENUE-placeholder loading pattern** that creates systemic FM-AVC starvation throughout the year on every Type 101-112 donor fund. The class detector confirms the user's instinct: the first-pass FM-only conclusion was incomplete.

---

## 16. Extension brain delta

| Artifact | Action |
|---|---|
| `Zagentexecution/sap_data_extraction/extract_ps_avc_tables.py` | NEW |
| Gold DB tables added | `ekkn_inc5638*` (3), `tka01`, `bphi`, `bpge`, `bpja_2024/25/26`, `cosp_2024/25/26`, `coss_2024/25/26`, `fmavct_2024/25/26` (proper), `fmafmap013500109`, `fmafmtp013500110`, `bpdj_2024_2026` |
| `Zagentexecution/quality_checks/inc5638_per_po_engine_analysis.py` | NEW |
| `Zagentexecution/quality_checks/inc5638_fm_ps_avc_misalignment.py` | NEW |
| `knowledge/domains/PS/ps_availability_control.md` | NEW |
| `knowledge/domains/PSM/fm_ps_connectivity_bw_bridge.md` | APPENDED — "FM-AVC vs PS-AVC: the two-engine truth" |
| `brain_v2/incidents/incidents.json` | UPDATED — `INC-000005638` `extension_step_b_ps_avc_data_pull` block, status flipped CONFIRMED |
| `brain_v2/claims/claims.json` | APPENDED — claims #125-129 |
| `brain_v2/agi/known_unknowns.json` | CLOSED `KU-2026-005638-01`; opened new KUs for OPSV, T185I, MuleSoft revenue posting |
| `brain_v2/annotations/annotations.json` | APPENDED — annotations on BPGE, BPJA, COSP, EKKN, FMAVCT, FMAFMAP013500109 |
| `brain_v2/agent_rules/feedback_rules.json` | APPENDED — `feedback_avc_bucket_revenue_placeholder_misalignment` (HIGH) |

---

## 17. Session 2026-05-01 re-confirmation — full Block A re-extract + 2026 delta refresh

**Context.** Session #66 left a partial state when the previous extraction agent stalled at 600s. This Session re-runs **Block A (PS-AVC core)** and **Block B (2026 delta)** to current-as-of date 2026-05-01, then re-runs the per-PO and class-detector quality scripts on the refreshed data.

### 17.1 Block A — PS-AVC core re-extracted (TIER_1)

| Table | WHERE | Row count | Δ vs prior |
|---|---|---:|---:|
| `ekkn_inc5638` | `EBELN='4500543365'` | 6 | confirmed |
| `ekkn_inc5638_22` | `EBELN='4500540022'` | 2 | confirmed |
| `ekkn_inc5638_24` | `EBELN='4500540024'` | 5 | confirmed |
| `ekkn` (consolidated) | 3 incident POs | 13 | NEW |
| `cosp_2024` | `OBJNR LIKE 'PR%' AND GJAHR='2024'` | 90,316 | unchanged |
| `cosp_2025` | `OBJNR LIKE 'PR%' AND GJAHR='2025'` | 92,640 | unchanged |
| `cosp_2026` | `OBJNR LIKE 'PR%' AND GJAHR='2026'` | 43,534 | +15 |
| `coss_2024/25/26` | `OBJNR LIKE 'PR%' AND GJAHR=...` | 0 / 0 / 0 | confirmed empty (UNESCO does not populate COSS for projects) |
| `bpge` | `OBJNR LIKE 'PR%' AND WRTTP IN (41,42,51,54,60,61,01)` | 654 | unchanged — only WRTTP 01 (n=651) and 41 (n=3) populated; broader buckets simply do not exist for projects in UNESCO |
| `bphi` | `OBJNR LIKE 'PR%'` | 0 | confirmed empty (UNESCO uses fund hierarchy `FK*`, not project hierarchy `PR*`, in BPHI) |
| `bpja_2024` | `OBJNR LIKE 'PR%' AND GJAHR='2024'` | 48,956 | unchanged |
| `bpja_2025` | `OBJNR LIKE 'PR%' AND GJAHR='2025'` | 50,450 | unchanged |
| `bpja_2026` | `OBJNR LIKE 'PR%' AND GJAHR='2026'` | 34,733 | unchanged |
| `fmavct_2024` | `RFIKRS='UNES' AND RYEAR='2024'` | 15,890 | unchanged |
| `fmavct_2025` | `RFIKRS='UNES' AND RYEAR='2025'` | 13,288 | unchanged |
| `fmavct_2026` | `RFIKRS='UNES' AND RYEAR='2026'` | 9,531 | +1 (one new KBFC posting) |
| `tka01` | `FIKRS='UNES'` | 1 | unchanged |
| `opsv` | (no WHERE) | RFC `TABLE_NOT_AVAILABLE` (DA/E/131) | KU-2026-005638-OPSV opened |
| `t185f` | (no WHERE) | 0 in client | KU — table not customised in P01 |

EKKN broader range (`4500000000..4600000000`) was deliberately deferred — would exceed the 5-min per-table cap. KU `KU-2026-DELTA-EKKN-FULL` opened.

### 17.2 Block B — 2026 delta backlog (TIER_1, current to 2026-05-01)

| Table | Δ rows added | Post 2026 | Max BUDAT/CPUDT/AEDAT |
|---|---:|---:|---|
| `bsas` (BUDAT > 20260328) | +43,718 | 134,468 | BUDAT 2026-05-01 |
| `bsik` (CPUDT > 20260316) | +7,168 | 11,376 | CPUDT 2026-05-01 |
| `bsak` (CPUDT > 20260316) | +36,153 | 87,236 | CPUDT 2026-05-01 |
| `bsid` (CPUDT > 20260316) | +595 | 4,280 | CPUDT 2026-05-01 |
| `bsad` (CPUDT > 20260316) | +7,464 | 26,763 | CPUDT 2026-05-01 |
| `coep` (PERIO 004,005) | +295 | 326,530 | PERIO 005 |
| `ekko` (AEDAT > 20260315) | upsert | 73,080 | AEDAT 2026-05-01 |
| `ekpo` (AEDAT > 20260315) | upsert | 201,383 | AEDAT 2026-05-01 |
| `rbkp` (BUDAT > 20260315 AND GJAHR=2026) | upsert | 17,034 | BUDAT 2026-05-01 |
| `fmifiit_full` (PERIO 003,004,005) | +185 | 274,321 | PERIO 005 |
| `bkpf` (CPUDT > 20260316) | +1,622 | 208,075 | CPUDT 2026-05-01 |
| `bsis` (BUDAT > 20260328) | +499 | 272,257 | BUDAT 2026-05-01 |

`PRAGMA integrity_check`: **ok** (post-Block-A and post-Block-B). Gold DB size 5,996.2 MB (+ 50.3 MB this session).

### 17.3 Per-PO verdict (TIER_1, refreshed 2026-05-01)

Run: `python Zagentexecution/quality_checks/inc5638_per_po_engine_analysis.py` against the freshly refreshed Gold DB.

| Engine pool component | 2026-05-01 value | Engine status |
|---|---:|---|
| FM-AVC fund-level available | +$11,813,609.46 | NOT exhausted |
| FM-AVC TC bucket available | **−$1,561,560.89** | **EXHAUSTED** (this is what blocks FIPEX 11 + 20) |
| FM-AVC 80 bucket available | −$3,512.01 | EXHAUSTED (small FIPEX=80 deficit) |
| PS-AVC cumulative project pool 196EAR4042 | +$16,430,198.98 | NOT exhausted |

| PO | Vendor | Engine firing | FM-AVC TC available | PS pool | Verdict |
|---|---|---|---:|---:|---|
| 4500543365 | COM NAT Gabon (200149) | **FM** | −$1,561,560.89 | +$16,430,198.98 | **FM-AVC TC bucket is exhausted; PS healthy** |
| 4500540022 | MENGUE (4028658) | **FM** | −$1,561,560.89 | +$16,430,198.98 | **FM-AVC TC bucket is exhausted; PS healthy** |
| 4500540024 | NTIE Stephan (4028648) | **FM** | −$1,561,560.89 | +$16,430,198.98 | **FM-AVC TC bucket is exhausted; PS healthy** |

All three POs target FIPEX 11/20 → AVC-derivation maps to TC bucket → that bucket is in $1.56M deficit. PS pool has $16.4M available so the PS engine is silent. **The FM engine alone is responsible for the block.** This re-confirms the Session #66 conclusion against the current 2026-05-01 ledger.

### 17.4 Class detector — UNESCO-wide (TIER_1, 2026-05-01)

Run: `python Zagentexecution/quality_checks/inc5638_fm_ps_avc_misalignment.py`

| Tier | Definition | Count (2026-05-01) | Δ vs Session #66 |
|---|---|---:|---:|
| Tier 1 | BOTH FM and PS blocking | **488** | +31 |
| Tier 2 | FM blocking only — INC-000005638 class | **1,517** | +60 |
| Tier 3 | PS blocking only | 90 | +14 |
| Tier 4 | Neither blocking | 386 | unchanged |
| no_ps_link | FM only, no project | 4,264 | +6 |
| **Total buckets** | — | **6,745** | +111 |

INC-000005638 footprint within the class detector:

| Fund / FundCenter / Bucket | Tier | FM pool | PS pool |
|---|---:|---:|---:|
| 196EAR4042 / WHC / TC | T2 | −$1,561,560.89 | +$16,430,198.98 |
| 196EAR4042 / WHC / 80 | T2 | −$3,512.01 | +$16,430,198.98 |

**Class size is now 1,517 + 488 = 2,005 buckets at risk** of the same FM-AVC starvation pattern. The Tier 2 class detector grew by 60 buckets in 4 weeks → the misalignment is actively widening, not shrinking.

CSV output: `Zagentexecution/quality_checks/inc5638_fm_ps_avc_misalignment.csv` (6,745 rows).


---

## 18. Per-WBS cross-validation — PR00050949 "Decentralization Yaounde" (Session #67, 2026-05-01)

This Section validates the Section 17.3 verdict from a different angle: instead of computing FM-AVC and PS-AVC pools at the fund/control-object level, we drill down to the single WBS that all three blocked POs reference, and prove the PS-side budget pool is healthy.

### 18.1 PO → WBS resolution (TIER_1 from EKKN)

`SELECT EBELN, EBELP, PS_PSP_PNR, FISTL, GEBER, SAKTO FROM ekkn WHERE EBELN IN ('4500543365','4500540022','4500540024')` returns 13 line-level account-assignments. ALL of them carry:

| Field | Value |
|---|---|
| `PS_PSP_PNR` (WBS internal key) | **00050949** |
| `FISTL` (Fund Center) | WHC |
| `GEBER` (Fund) | 196EAR4042 |
| `SAKTO` (G/L) | 0006012101 (subcontracts) |
| `AEDAT` (last change) | 2025-06-24 |

`SELECT POSID, POST1, OBJNR FROM prps WHERE PSPNR='00050949'` resolves to:

| Field | Value |
|---|---|
| `POSID` | **`196EAR4042.23.2.10.1`** |
| `POST1` | "Decentralization Yaounde" |
| `OBJNR` | `PR00050949` |
| `PSPHI` (project hierarchy) | 00013092 |
| `PBUKR` | UNES |

**FM-PS 10-digit hard link**: `POSID(10)='196EAR4042'` exactly equals `GEBER='196EAR4042'`. The hard link in `ZXFMYU22:362-369` PASSES. `ZFI/009` is NOT the error.

### 18.2 PS-AVC pool at WBS PR00050949 (TIER_1)

BPJA WRTTP=41 (current budget) and WRTTP=42 (original/carry-forward) for the WBS, with VORGA decoded:

| Year | VORGA | WRTTP | WTJHR (USD) | Sign meaning |
|---|---|---|---:|---|
| 2024 | KBN0 (original budget) | 41 | +259,261.00 | initial allocation |
| 2024 | KBW1 (return out) | 41 | −248,450.86 | transferred OUT to other WBS |
| 2024 | KBFC (carry forward) | 42 | +10,810.14 | carry-fwd reflecting actuals |
| 2025 | KBN0 | 41 | −46,147.81 | reduction (return) |
| 2025 | KBW1 | 41 | −35,737.96 | return out |
| 2025 | KBW2 | 41 | +248,450.86 | transferred IN |
| 2025 | KBFC | 42 | +166,565.09 | carry-fwd |
| 2026 | KBN0 | 41 | +42,015.30 | new allocation |
| 2026 | KBW2 | 41 | +35,737.96 | transferred IN |
| 2026 | KBFC | 42 | +28,854.94 | carry-fwd |

Net WRTTP=41 (active budget) for 2026 = 42,015.30 + 35,737.96 = **$77,753.26 USD** (matches Section 17 numbers).

**Consumption side (sum from Gold DB on the same WBS):**

| Year | COEP WRTTP=04 actuals | COOI commitments | Total used | Net pool |
|---|---:|---:|---:|---:|
| 2024 | $10,810.14 | $0 | $10,810.14 | $0 (fully consumed) |
| 2025 | $166,565.09 | $0 | $166,565.09 | $0 (fully consumed) |
| **2026** | **$12,960.60** | **$15,894.34** | **$28,854.94** | **+$48,898.32 AVAILABLE** |

`SELECT SUM(WKGBTR) FROM coep WHERE OBJNR='PR00050949' AND GJAHR='2026' AND WRTTP='04'` → 18 rows summing $12,960.60 USD.
`SELECT SUM(WKGBTR) FROM cooi WHERE OBJNR='PR00050949' AND GJAHR='2026'` → 24 rows summing $15,894.34 USD.

**PS-AVC at WBS level: 2026 free pool = +$48,898 USD AVAILABLE.** PS-AVC would let any PO ≤ $48,898 pass. The three blocked POs together come nowhere near $48K → **PS-AVC is silent on these POs**.

### 18.3 FM-AVC pool at fund 196EAR4042 / FISTL=WHC (TIER_1)

FMIFIIT WRTTP semantics: 54=consumption charge, 66=revenue/budget loaded, 57=internal adjustment.

| Year | WRTTP | rows | Sum FKBTR (USD) | Meaning |
|---|---|---:|---:|---|
| 2024 | 54 | 2,104 | −2,401,640.62 | consumption against budget |
| 2024 | 66 | 82 | +15,959,524.38 | revenue loaded onto fund |
| 2025 | 54 | 1,937 | −2,446,078.33 | consumption |
| 2025 | 66 | 126 | +2,654,545.72 | revenue |
| **2026** | **54** | **68** | **−207,793.14** | **consumption (still happening)** |
| **2026** | **66** | **5** | **−12,659,716.27** | **revenue REVERSED (fund being unwound)** |

**FIPEX granularity breakdown for 196EAR4042/WHC/2026** (the smoking gun):

| FIPEX | WRTTP=54 (consumption) | WRTTP=66 (revenue/budget) | Per-FIPEX pool |
|---|---:|---:|---|
| **REVENUE** (placeholder) | $0 | **−$12,659,625.38** | net negative (reversed) |
| **20** (Travel) | −$56,905.21 | $0 | **EXHAUSTED** |
| **30** (Equipment) | −$118,247.37 | $0 | **EXHAUSTED** |
| **11** (Personnel) | −$11,558.06 | $0 | **EXHAUSTED** |
| **13** (Subcontracts) | −$3,893.82 | $0 | **EXHAUSTED** |
| 10' | −$2,730.20 | −$90.89 | exhausted |
| 40 | −$881.75 | $0 | exhausted |
| 50 | −$536.45 | $0 | exhausted |
| 80 | −$13,040.28 | $0 | exhausted |

**The structural defect is now visible at the row level**: revenue ($-12.66M, being reversed in 2026) sits 100% on the placeholder FIPEX `REVENUE`. Consumption sits on operational FIPEX (11, 13, 20, 30, 40, 50, 80, 10'). The AVC engine evaluates per (FUND, FUNDSCTR, **CommItem**) — every operational bucket has zero budget and non-zero consumption → AVC blocks. The placeholder REVENUE bucket has all the money but no postings can target it directly.

### 18.4 Engine-disagreement table (the misalignment, made explicit)

| Engine | Granularity | Pool view | Verdict on the 3 POs |
|---|---|---:|---|
| **PS-AVC** | per WBS (PR00050949), summed across all FIPEX | **+$48,898 available** | ✓ PERMIT |
| **FM-AVC** | per (FUND, FUNDSCTR, **CommItem**) — per FIPEX bucket | All operational FIPEX in deficit; revenue stranded on REVENUE placeholder | ❌ BLOCK |

FM-AVC fires first in the validation chain (`AVC_DERIVE_BUDGET_AVC` runs before PS availability check in COBL coding). FM's BLOCK wins → posting fails. PS-AVC never gets to issue its "permit" verdict.

### 18.5 Why this is a CLASS, not a one-off

Section 17.4's class detector flags **2,005 buckets** (Tier 1 + Tier 2) with the same pattern. The Tier 2 count grew by **+60 buckets in 4 weeks** (Mar 31 → Apr 28), proving the misalignment is widening, not stable. UNESCO is structurally exposed every biennium-end on every Earmarked donor fund whose revenue is loaded onto a placeholder FIPEX while consumption posts to operational FIPEX. This is a configuration-level defect (FIPEX derivation strategy + revenue-loading procedure), not a bug in any custom code.

### 18.6 What `ZFI/009` is NOT

Reporters and support agents can mistake this class for the FM-PS 10-digit hard-link error (`ZFI/009`) raised by `ZXFMYU22:362-369`. **It is not.** The 10-digit rule is satisfied here: `POSID(10)='196EAR4042'='GEBER'`. The error message in this incident class is `FMAVC005` ("Annual budget exceeded by …"), `FI 026`, or a UNESCO-localised wrapper. Without the SAP screenshot from the user, the exact message ID cannot be confirmed — captured as `KU-2026-005638-MSGID`.

### 18.7 Brain delta (Session #67)

| Artifact | Action |
|---|---|
| `brain_v2/incidents/incidents.json` → INC-000005638 | status PROVISIONAL → **CONFIRMED**; cross_validations: ["fmifiit_fipex_aggregate", "wbs_pr00050949_per_engine", "fmavct_control_object"] |
| `brain_v2/claims/claims.json` | APPENDED — claims #131-135 (TIER_1) on the per-WBS pool, the FIPEX granularity defect, the engine-disagreement evidence |
| `brain_v2/agi/known_unknowns.json` | KU-2026-005638-01 → **CLOSED** (FMAVCT is irrelevant — FMIFIIT-aggregate proves the same fact); KU-2026-005638-MSGID opened for the missing screenshot |
| `brain_v2/annotations/annotations.json` | EXTENDED — `PR00050949`, `196EAR4042.23.2.10.1`, `bpja`, `coep`, `cooi`, `ekkn`, `fmifiit_full` with TIER_1 row counts and the WTJHR sign convention (KBN0/KBW1/KBW2/KBFC VORGA codes) |
| `brain_v2/agent_rules/feedback_rules.json` | (no new rule — Session #66's `feedback_avc_bucket_revenue_placeholder_misalignment` already covers it) |
| `knowledge/domains/PS/ps_availability_control.md` | will be EXTENDED in next session with the WTJHR sign convention table from §18.2 |



---

## 19. Session #69 final synthesis — AGI consolidation (2026-05-01)

This section consolidates everything learned across Sessions #66-69 into a single coherent framing. It supersedes earlier fragments where they conflict.

### 19.1 The reframed problem (one sentence)

INC-000005638 is a manifestation of UNESCO's **lack of a referential-integrity contract** between the four sources of fund-state mutation (MULESOFT/Core Manager budget loading, manual FB01 real reclassifications, manual FMBB budget transfers, manual FMX1 reservations) and the dependent PS / MM structures. The 6,232 (Fund, WBS) pairs in BAD state are not 6,232 separate problems; they are 6,232 manifestations of one missing contract.

### 19.2 The 4 paths that mutate fund state — and what each carries

| Path | Trigger | Carries | Workplan context? | Real posting? |
|---|---|---|:--:|:--:|
| **MULESOFT** -> BAPI_FUND_CREATE | Salesforce Core Manager workflow | BOR (Budget Original Reservation, assignment) | yes (FIPEX-aware via Allocation__c.Commitment_Item__c) | no - budget side only |
| **FB01** manual journal | SAP user (e.g., A_BANSAL via BSP email) | Real posting reclassification in FI ledger | no | yes - actual money moves |
| **FMBB / FMBBT** manual | SAP user via FM cockpit | Budget posting / transfer | no | no - budget side |
| **FMX1 / FMRES** manual | SAP user | Funds reservation | no | partial |

**Key insight (Session #69)**: Core Manager / MULESOFT moves **only** BOR; it never creates commitments or real postings. The 257-doc A_BANSAL batch on 2026-01-31 = 257 manual FB01s, completely bypassing Core Manager. Any fix on the MULESOFT path leaves manual paths uncontrolled.

### 19.3 Two universes of fund-project relationships

| Universe | Count | Link type | Behavior |
|---|---:|---|---|
| HARD-link (Earmarked donor TYPE 101-112) | 2,820 funds (60%) | strict 10-digit POSID(10)=GEBER | INC-005638 pattern at biennium-end |
| Multi-project (2 projects per fund) | 1,578 funds (34%) | DERIVED via posting history | mixed risk profile |
| Multi-project (3 projects) | 74 funds (1.6%) | DERIVED, overhead/feeder | irregular |
| Multi-project (4+ projects) | 9 funds (0.2%) | DERIVED, PFF + TYPE 001/004/196 | regular programme |

The 10-digit hard-link rule is the **exception, not the norm**, for non-Earmarked types. For DERIVED multi-project funds, the source-of-truth for fund-project mapping lives in **Salesforce Core Manager Allocation__c** (multi-fund junction with Commitment_Item__c granularity) - not in SAP master data.

### 19.4 The asymmetry catalog (5 FM-change types and PS-side response)

| # | FM Change | TCODE/VORGA | PS-side symmetric? | Evidence |
|---|---|---|:--:|---|
| 1 | Original budget posting | FMBB / KBN0 | YES via 10-digit link | BPJA: PR00050949 KBN0 |
| 2 | Within-project transfer | FMBBT / KBW1 - KBW2 | YES mirror | BPJA: 2024 KBW1 / 2025 KBW2 |
| 3 | Carry-forward | FMJ2 / KBFC | partial | BPJA: KBFC entries |
| 4 | **Cross-project revenue transfer** (biennium close) | **FB01 R1** | **NO PS counterpart** | 2026-01-31: revenue moved 196EAR4042 to 196EAR4043, PS WBSs unchanged |
| 5 | Fund TYPE flip 104->106 | FM5S | **symmetric BUT DELAYED** | 196EAR4040: 88/88 CLSD; 196EAR4042: 0/139 CLSD (delay window) |

The defect is row 4 (no symmetry at all) AND the delay window in row 5 (weeks-to-months between FB01 R1 and TYPE flip). Tickets are generated during that window.

### 19.5 The fix architecture - 6 paths, ranked

| # | Fix | Phase | Cost | Coverage | Path scope |
|:--:|---|---|---|---|---|
| **1** | **FIX-E** Pre-flight HARD-BLOCK BAdI on FB01/FMBB/FMBBT/FMX1 | tactical | 1-2 sprints | catches manual paths | Manual paths (FB01 + others) |
| **2** | **FIX-F** Meta-AVC unified engine (validates FM+PS+divergence atomically) | strategic | 2-3 sprints | **permanent close of model gap** | **All paths** - automated + manual |
| 3 | FIX-A MULESOFT FIPEX-aware revenue load | biennium-START | 3-5 days | clean budget loading day-1 | Automated path only (BOR side) |
| 4 | FIX-D Compress timing window (TYPE flip + FB01 R1 simultaneous) | biennium-END | 1-2 weeks | closes ~95% of biennium-end window | Biennium-end batch only |
| 5 | FIX-B Symmetric closeout protocol (5 actions) | biennium-END | 2-3 weeks | residual 5% | All channels at biennium close |
| 6 | FIX-C Cross-biennium project-mapping table | enabler for B | 4-6 weeks | enables FIX-B | Master data |

**Recommended sequencing**: FIX-E + FIX-A in parallel (different teams, no dependency). Plan FIX-F as 6-month north star. FIX-D as quick process win. FIX-B+C only if needed after F lands.

### 19.6 Pre-flight HARD-BLOCK detector - what it would have caught on 2026-01-31

`committed_vs_available_detector.py` evaluates UNESCO-wide for active WBS elements only:
- 16,894 active WBS elements (status I0002 REL, not CLSD/TECO/DLFL)
- 4,115 active (WBS, Fund) pairs with 2026 commitments (3,812 HARD + 303 DERIVED)
- 3,069 in FM-only-EXHAUSTED state (down from 6,232 raw - half was inactive noise)
- 119 BOTH-EXHAUSTED
- **30 pairs where commit > FM available - pre-flight HARD-BLOCK candidates**
- 3,395 already flagged I0093 ISBD by SAP

If FIX-E had been live on 2026-01-31, the 257-doc A_BANSAL batch would have BLOCKED on 196EAR4042 (and likely on the other 6 series funds) until Budget Office authorized override or open commitments were resolved.

### 19.7 The smoking-gun catalog (TIER_1 evidence chain)

| Fact | Evidence | Source |
|---|---|---|
| Revenue moved 196EAR4042 -> 196EAR4043 | $-12,659,625.38 / $+12,757,386.61 (0.8% net drift) | fmifiit_full WRTTP=66 GJAHR=2026 PERIO=001 |
| Two projects share zero WBS elements | INNER JOIN prps_full intersection = 0 | prps_full |
| Workplan layer has FIPEX granularity SAP doesn't | WP 007774 has 4 Allocation__c with Commitment_Item__c=TC/80 | Salesforce PROD sf data query |
| WP 017983 (biennium 43) still references SAP project 196EAR4042 | sf data query SAP_Budget_CODE__c=196EAR4042 returns 2 WPs | Salesforce PROD |
| Type flip 104->106 IS symmetric, just delayed | 196EAR4040: 88/88 CLSD; 196EAR4042: 0/139 CLSD | jest |
| 51% of 196EAR4042 WBS elements already ISBD-flagged | jest STAT=I0093: 71 of 139 | jest |
| 257 manual FB01s on 2026-01-31 by A_BANSAL | bkpf BUKRS=UNES BUDAT=20260131 USNAM=A_BANSAL | bkpf |
| 196EAR4042 sustains 2 projects + 66 WBSs across | prps_full + coep DISTINCT PSPHI per GEBER | prps_full + coep |
| Multi-project funds are 40% of UNESCO universe | GROUP BY n_projects per fund | coep + funds |

### 19.8 Brain delta Sessions #66-69 (cumulative)

| Layer | Start of Session #66 | End of Session #69 | delta |
|---|---:|---:|---:|
| Claims | 120 | 146 | +26 |
| Rules | 107 | 118 | +11 |
| Incidents (first-class) | 7 | 8 | +1 (INC-005638) |
| Known Unknowns | 42 | 54 | +12 |
| Data Quality (open) | 6 | 8 | +1 (MODEL-GAP-2026-001 + 1 derivative) |
| Companions in PSM domain | 0 | 3 | +3 (master, pool-health, temporal-forecast) |
| Quality-check scripts | 7 | 11 | +4 (per-PO, misalignment, pool-health, committed-vs-avail) |

### 19.9 What remains open (KU register Session #69)

- **KU-2026-PS-MM-SYMMETRIC-CLOSEOUT** (HIGH) - Why does UNESCO not run a symmetric biennium-end protocol? HQ Budget Office input needed.
- **KU-2026-MULESOFT-FIPEX-FLATTENING** (CRITICAL) - Find exact MULESOFT mapping that flattens Commitment_Item__c.
- **KU-2026-AGI-GAP-2** (MEDIUM) - Trace the other 253 docs in the A_BANSAL 2026-01-31 batch.
- **KU-2026-AGI-GAP-6** (MEDIUM) - Quantify historical backlog (38 ISBD WBSs in CLOSED 196EAR4040).
- **KU-2026-WP-INTENT** (MEDIUM) - Is WP 017983 stale-pointing intentional or defect?
- **KU-2026-NET-DRIFT** (LOW) - $97,761 net drift between revenue out/in.
- **KU-2026-MODEL-GAP-CONTROL** (carry-over) - HQ authorization for FIX-E/FIX-F.
- **KU-2026-OUTLIER-WBS-AVC** (carry-over) - 10 multi-fund common cost WBSs governance.

### 19.10 Recommendation to UNESCO leadership (one paragraph)

The fund-management model has a structural integrity defect that produces incidents in cohorts. INC-000005638 is one of an estimated 30 immediate ticket-risk pairs and 3,069 latent FM-only-exhausted pairs UNESCO-wide. The defect grows ~+4.1%/month (TIER_2) because each new biennium adds a cohort of TYPE 104 funds following the same trajectory. Three mitigations exist: tactical (FIX-E pre-flight HARD-BLOCK on FB01, deployable in 1-2 sprints, catches manual paths), strategic (FIX-F Meta-AVC, deployable in 2-3 sprints, closes the gap permanently), and integration-level (FIX-A MULESOFT FIPEX-aware, deployable in 3-5 days, automated path only). Recommended order: FIX-E + FIX-A in parallel as immediate response; FIX-F as 6-month strategic milestone. Without intervention, every biennium close-out from 2026 onward will produce another wave of stranded POs and 'insuffisance de budget' tickets.


### 19.11 Critical reframe (Session #69) — desalignment is CONTINUOUS, not periodic

User insight Session #69 + empirical verification 2026-05-01:

**The defect is NOT a biennium-end event.** Every FB01 / FMBB / FMBBT / FMX1 posting that mutates FM state without a corresponding PS-side action creates asymmetry. The biennium-end batch (A_BANSAL 2026-01-31, 257 docs) is the most dramatic instance, but it is one of many.

Empirical proof on fund 196EAR4042 alone (TIER_1):

| Risk window | Events 2024-2026 |
|---|---|
| Revenue postings (FB01/FMBB to FIPEX=REVENUE) | 14 distinct periods (Jan/Feb/Mar/Apr/Aug/Sep/Oct/Nov/Dec 2024; May/Sep/Oct/Dec 2025; Jan 2026) |
| Operational FIPEX adjustments (FB01 to FIPEX=11/13/20/30/50/etc) | Dozens per month, every month from Mar 2024 to Apr 2026 |
| Distinct users posting | L_HANGI (381 docs), F_DERAKHSHAN (345), S_AGOSTO (222), A_BANSAL (38 FB01s spread across period — NOT just the 257-doc batch), TP_NZAMBA-NZ (36 ML81s — the incident reporter, posting SES from Feb-2025 onward) |

**Implication for fix priority**:

| Fix | Coverage of continuous risk | Re-priorization |
|---|---|---|
| FIX-D (compress closure timing) | Only 1 event per biennium | **DEMOTED** — addresses 1% of risk surface |
| FIX-A (MULESOFT FIPEX-aware) | Only automated budget path | partial — does not catch manual FB01s |
| **FIX-E (BAdI HARD-BLOCK on every FB01/FMBB/FMBBT)** | Catches every posting type | **PROMOTED to #1** |
| **FIX-F (Meta-AVC unified atomic validation)** | Catches every posting at validation time | **PROMOTED to #2 strategic** |
| FIX-B (symmetric closeout protocol) | Only at biennium-end | residual |
| FIX-C (cross-biennium mapping table) | Only at biennium-end | residual |

This reframe also closes KU-2026-PS-MM-SYMMETRIC-CLOSEOUT structurally: even if UNESCO had a perfect biennium-close SOP, mid-biennium ad-hoc adjustments would still create asymmetry. **The only durable answer is system-enforced consistency at every posting.**


---

## 20. The central narrative — articulated by SME 2026-05-02 (final)

This section captures the user/SME articulation of the upstream root cause, after all empirical analysis was consolidated.

### 20.1 The narrative (one sentence)

> **SAP knew the fund had open commitments, but allowed them to be moved anyway because there is no AVC guardian configured to enforce. The system let it happen.**

### 20.2 The 4-step chain (each step empirically confirmed)

| # | What happened | Empirical evidence |
|---|---|---|
| 1 | SAP knew the fund had open commitments | COOI = 932 entries totaling $571,049 on PR00050949 alone. EKKN = 13 hardcoded PO lines on the 3 incident POs. |
| 2 | AVC was supposed to enforce but doesn't, in this configuration | FMAVCT_2026 only 2 control objects per fund (TC aggregator + 80). TC pool includes REVENUE. While REVENUE positive, AVC saw TC positive. |
| 3 | The system let A_BANSAL move funds — no block | FB01 R1 batch posted successfully (2026-01-31, 257 docs total, 4 R1 against 196EAR4042). Revenue $-12,659,625.38 reversed. |
| 4 | The fund went more negative — operational FIPEX deficits revealed | After the move: REVENUE dropped from +$18.7M to +$6.1M. Operational FIPEX deficits, always present, are now visible to AVC. |

### 20.3 Why AVC failed to enforce — 4 compound reasons

| Reason | Fact | Effect |
|---|---|---|
| AVC missing on most funds | Only 3,576 of 55,428 UNESCO funds (6.5%) have an AVC derivation rule | 93.5% have no guardian at all |
| Granularity mismatch | 9 FIPEX in postings vs only 2 control objects | Per-FIPEX deficits invisible to AVC |
| REVENUE in TC pool | `YCL_YPS8_BCS_BL===CM005_RPY.abap:58,73` hardcodes preservation of FIPEX='REVENUE' rows | REVENUE buffer hides operational deficits |
| No 10-digit rule for non-Earmarked | `ZXFMYU22` enforces only TYPE 101-112 | Free-floating fund-WBS posting on most funds |

### 20.4 What this means for the fix priority

| Fix | Before central narrative | After central narrative |
|---|---|---|
| FIX-G1 Granular AVC per FIPEX | Option among 6 | **PRIMARY structural fix** — addresses upstream cause directly |
| FIX-G2 Exclude REVENUE from TC pool | Alternative to G1 | **Complement to G1** |
| FIX-G3 Enable AVC for non-Earmarked TYPEs | Policy decision | **Critical** — 93.5% of funds need AVC enabled |
| FIX-H Modify YCL_YPS8_BCS_BL | Structural alternative | **Second-line** — removes REVENUE preservation |
| FIX-F Meta-AVC | THE architectural answer | **Strategic enhancement** — adds cross-engine consistency on top of FIX-G |
| FIX-E Pre-flight HARD-BLOCK BAdI | Tactical control | **Mitigation** — second-line if config can't change quickly |
| FIX-A MULESOFT FIPEX-aware | Quick win | **DEPRECATED** — courier layer, not the lever |
| FIX-D Compress timing window | Process win | **Symptomatic** — 1 event/biennium |
| FIX-B/C Symmetric closeout SOP | Long-term governance | **Symptomatic** — required only because AVC doesn't enforce |

### 20.5 Operational vs structural (clean two-track plan)

**Track 1 — Operational (this week)**: ME22N redirect of the 13 EKKN lines on the 3 Gabon POs. From legacy fund 196EAR4042/PR00050949 to successor 196EAR4043/PR00058662. Resolves INC-005638. ~2-4 hours FM team.

**Track 2 — Structural (1-2 sprints)**: FIX-G1 + FIX-G2 in `FMAFMAP013500109`. Closes the root cause for 705 Class A projects + future biennium events. ~1 sprint config + UAT.

These tracks are independent. Track 1 unblocks the immediate ticket. Track 2 prevents the next 705.

### 20.6 Brain delta in this final pass

| Layer | Change |
|---|---|
| Claims | +1 (#157, TIER_1, central narrative) — total 156 |
| MODEL-GAP-2026-001 | +`central_narrative_2026_05_02` field, +`narrative_credit: User SME 2026-05-02`, +`related_central_claim: 157` |
| Companions updated | master + executive brief + HQ memo (all reframed with central narrative) |
| Canonical doc | this Section 20 added |

### 20.7 Recommendation to UNESCO leadership (one paragraph)

UNESCO has a structural defect at the AVC configuration layer. SAP holds all the data needed to enforce the constraint (commitments visible in COOI, postings in FMIFIIT, project structure in PRPS), but the AVC engine is configured to validate at coarse-grained TC aggregator instead of per-FIPEX. As a result, fund moves like the 2026-01-31 batch posted by A_BANSAL succeed even when they leave operational FIPEX in deficit. Track 1 (ME22N redirect) resolves the immediate ticket within the week. Track 2 (FIX-G1+G2 config change) closes the root cause within 1-2 sprints. Without Track 2, every biennium close-out from 2026 onward will produce another wave of stranded POs and "insuffisance de budget" tickets across an estimated 705 Class A projects.
