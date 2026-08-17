# Purpose of Payment — the P2P end-to-end

**Domain**: Procurement_P2P (spine) · FI · Payment_BCM · Treasury
**Status**: VERIFIED from source + P01 config + Gold DB — Session #099 (2026-08-17)
**Supersedes**: claim 116 (which said no capture control existed). See claim 484.
**Companion**: [companions/p2p_purpose_of_payment.html](../../../companions/p2p_purpose_of_payment.html)

---

## 0. Why this document exists

The purpose code is one mechanism that spans the whole **purchase-to-payment** spine: it is
**configured** by Treasury, **captured** by an AP clerk on the invoice, and **rendered** into the
payment file that the bank validates. Until this session the knowledge lived in three
disconnected places — a skill file, a set of orphan claims, and one paragraph of an autopsy
filed under PSM — and none of them was reachable from the P2P process. A support request about
Egypt was answered wrong twice because of it.

**The single most important correction:** the list that decides whether a purpose code is
*mandatory* is **`YTFI_PPC_STRUC.LAND1` matched against the vendor's BANK country
(`LFBK-BANKS`)**. Not `T015L` — that is the catalogue of code *values*. Not the vendor's address
country (`LFA1-LAND1`).

---

## 1. The three stages

### Stage 1 — MAINTAIN (configuration)

| Table | Rows (P01) | What it holds | Keyed by |
|---|---|---|---|
| `T015L` | 73 | The **catalogue of code values** — `LZBKZ` + description `ZWCK1`. UNESCO-specific values (`AE0`…`AE8`, `IN0`…, `JO0`…), **not** ISO 20022 text codes | `LZBKZ` |
| `YTFI_PPC_STRUC` | 133 | **The list that decides obligatoriness** + how the tag string is assembled from positional blocks (`SEPARATOR`, `FIXED_VAL`, `PPC_VAR`, `PPC_DESCR`, `PAY_FIELD`) | `LAND1` + `TAG_ID` + `PAY_TYPE` + `CODE_ORD` |
| `YTFI_PPC_TAG` | 11 | Where in the XML the value goes | `LAND1` + `TAG_ID` + `DEB_CRE` |

Countries configured: **AE, BH, CN, ID, IN, JO, MA, MY, PH** — 9. **Egypt is absent from all three.**

XML destination per country (`YTFI_PPC_TAG`):
- `AE`, `CN` → `<PmtInf><CdtTrfTxInf><InstrForCdtrAgt><InstrInf>`
- `BH`, `ID`, `IN`, `JO`, `MA`, `MY`, `PH` → `<PmtInf><CdtTrfTxInf><RmtInf><Ustrd>`

Pay types (`PAY_TYPE`), derived from `fpayh-dorigin(2)`: `HR` → `P` payroll · `TR` → `R`
replenishment · everything else → `O` third party. Example, UAE third party: `/` + `REC` + `/` +
`<PPC_VAR>`; UAE payroll: `/REC/SAL`; UAE replenishment: `/REC/IGT`.

### Stage 2 — USE (at invoice entry) — this is where the control lives

The AP clerk types the code into the SCB-indicator field (`BSEG-LZBKZ`) on the vendor line.
It is **not optional**: `FORM u917` blocks the posting.

```
FORM u917 CHANGING b_result.                    " YRGGBS00 : 1547-1590
  b_result = b_true.
  CHECK bseg-lifnr IS NOT INITIAL.              " vendor lines only
  CHECK bseg-bschl NE '26'.                     " skip down-payment clearing
  CHECK bseg-bschl NE '39'.
  ... SELECT lfbk -> lv_banks                   " the vendor's BANK country
  CHECK lv_banks IS NOT INITIAL.                " no bank record -> passes silently
  IF bseg-lzbkz IS NOT INITIAL. ... ELSE.
    SELECT SINGLE * FROM ytfi_ppc_struc
      WHERE land1 = @lv_banks
        AND ( ppc_code = 'PPC_VAR' OR ppc_code = 'PPC_DESCR' ).
    IF sy-subrc = 0. b_result = b_false. ENDIF. " BLOCKED
  ENDIF.
ENDFORM.
```

**Registration**: `exits-name = 'U917'` (`YRGGBS00:224`), wired as `VALID='UNES'`
`BOOLCLASS=009` `VALSEQNR=012`, `CONDID` `1UNES###009`, `CHECKID` `2UNES###009`.

**Fires on**: `FB01`, `FB41`, `FB60`, `FB65`, `FBA6`, `FBR2`, `MIR7`, `MIRO`, `FBV0`, `FBVB`,
`F-47` — with an invoice document type (`AP CO ER IN IT KA KR KT MF MR RE RF PS PN`) and a
vendor line (`KOART='K'`).

The value then rides `BSEG-LZBKZ` → open item (`BSIK`) → `REGUP-LZBKZ` at F110 → `FPAYP-LZBKZ`.

### Stage 3 — RENDER (at payment)

`F110` → `SAPFPAYM` → DMEE tree `/CGI_XML_CT_UNESCO` →
`YCL_IDFI_CGI_DMEE_FR===CM002` dispatches → `YCL_IDFI_CGI_DMEE_UTIL->GET_TAG_VALUE_FROM_CUSTO`
(`CM003`) reads `YTFI_PPC_TAG` + `YTFI_PPC_STRUC` and assembles the string.

`CM003` line 48 does `READ TABLE mt_t015l WITH KEY lzbkz = is_fpayp-lzbkz`. An empty `LZBKZ`
yields `sy-subrc <> 0` → empty tag → the receiving bank rejects. That is the failure mode
`U917` exists to prevent.

---

## 2. The separate note-to-payee mechanism (free text, SWIFT :70)

Distinct from PPC and **relevant whenever a bank asks for narrative purpose rather than a code**.

`Y_FI_PAYMEDIUM_NOTE_TO_PAYEE` (67 lines) reads custom table **`YVENDOR_PAYM_REF`** keyed
`(BUKRS, LIFNR, BLART)` and writes `FPAYP-ZREF01`. With no row it falls back to a format chosen
by `FPAYHX-PREFTYP`:

- `'SAMPLE 01'` → `No.<xblnr>/<bldat>`
- `'SAP SEPA'` → `/INV/<xblnr> <bldat>`

`Y_FI_PAYMEDIUM_06` and `Y_FI_PAYMEDIUM_DMEE_30` read the same table.

> ⚠️ The `sap_payment_bcm_agent` skill states this FM builds `EXO//reason//XBLNR//` from
> `REGUP-BLART`. **The string `EXO` does not appear in any of the ten recovered sources.** The
> claim came from a spec (`FS Note to Payee v1.1`), not from the code. Treat the skill text as
> unverified until someone finds where `EXO//` is actually produced (candidate: a DMEE tree
> constant, not ABAP).

---

## 3. Scope — SocGen only, by written specification

PPC functional spec v2.0 (M. Spronk), page 16:

> the development is only for the XML file of Société Générale

Citibank payments do **not** carry PPC. Any request to make a purpose code mandatory for a
Citi-routed country is a **new development**, not a configuration change. (claim 267)

---

## 4. Measured state (2026-08-17)

**Capture compliance** — Gold DB `REGUP_SCENARIOS` (188 payment runs, 2025-01-02 → 2026-04-29,
6 company codes) joined to `LFA1`. This is a curated subset, not full `REGUP`:

| Vendor country | Lines | Empty `LZBKZ` | Filled |
|---|---:|---:|---:|
| IN | 303 | **283** | 20 |
| JO | 13 | 0 | 13 |

**Resolved — and the answer is bigger than the question** (`KU-2026-099-PPC-COVERAGE`, claim 485):

1. **259 of the 283 were a measurement error.** `U917` keys on the vendor's **bank** country
   (`LFBK-BANKS`); the measurement above keys on the vendor's **address** country
   (`LFA1-LAND1`). That vendor banks in **Singapore** — the control correctly does not apply.
   No defect.
2. **The residual 24 lines are all company code `IIEP`** (vendor `0000492662` KAPUR Avani,
   Jan–Apr 2025). And that is the real finding.

### The control covers ONE company code out of NINE

`U917` is step `VALSEQNR=012` of validation `VALID='UNES'`. OB28 assigns validations per
company code, and at UNESCO that assignment is optional. Measured live in P01 (`GB931`):

| Company code | Validation | Steps | Has U917? |
|---|---|---:|---|
| UNES | `UNES` | **12** | ✅ step 012 |
| ICTP | `ICTP` + `ICTP_HE` | 4 + 4 | ❌ |
| IIEP | `IIEP` | 2 | ❌ |
| UBO | `UBO` | 3 | ❌ |
| UIL | `UIL` | 1 | ❌ |
| UIS | `UIS` | — | ❌ |
| IBE · ICBA · MGIE | none assigned | 0 | ❌ |

**Adding a country to `YTFI_PPC_STRUC` turns the capture control on for `UNES` and for nobody
else.** Whether the other institutes should get an equivalent step is a functional decision,
now tracked as `KU-2026-099-PPC-INSTITUTE-COVERAGE`.

> **Why a table search can never settle this.** `GB931` stores `CHECKID` as a boolean-expression
> id (`2UNES###009`), never the literal `=U917`; the exit call lives inside the `GB901`
> expression body. A table-level search for `LZBKZ` returns nothing and *cannot* disprove the
> control — the structural reason claim 116 went wrong.

**Egypt** — `REGUH` 2016-2026: 17,778 lines to Egypt-domiciled payees, 744 vendors, and
**2,762 vendors** in `LFA1` (which would make it the 5th-largest of the group). Of the payments
that actually settle at an Egyptian bank (`UBNKS='EG'`): **387 lines, 100% through house bank
`CIT19`, method 3** (`USD01` 269 + `EGP01` 118, EGP 20.8M).

**Egypt exposure by company code** — which half of the population the control could reach:

| Population | Lines | Covered by U917 |
|---|---:|---|
| Settle at an Egyptian bank (`UBNKS='EG'`) | 387 | **100% — all UNES** |
| Egypt-domiciled payees (`LAND1='EG'`) | 17,778 | UNES 16,058 ✅ · ICTP 1,242 ❌ · UIL 348 ❌ · IIEP 117 ❌ · UIS 9 ❌ · UBO 4 ❌ |

So for the population Citi's notice actually binds, capture *would* be enforced once `EG` rows
exist. **1,720 lines (9.7%)** to Egypt-domiciled payees sit in institutes with no capture
control at all.

---

## 5. Known holes in the control

Read from the same source, not inferred:

1. **No bank record → no check.** `CHECK lv_banks IS NOT INITIAL` — a vendor with no `LFBK` row
   passes silently.
2. **Invoice entry only.** `F-53` / `FBZ2` manual payments, `FB1K` clearings and `SAPF124` auto
   clearing are not covered.
3. **Down-payment clearing skipped** (`BSCHL` 26 / 39).
4. **Multi-bank ambiguity.** With no `BVTYP` on the line the `SELECT SINGLE` on `LFBK` takes an
   arbitrary row — `U915` forces disambiguation on the same TCODEs, which mitigates but does not
   eliminate it.
5. **Interfaces.** Claim 39 records that the F110 BAPI bypasses substitution callpoint 3 and may
   bypass validation callpoint 2 — unverified for `U917`.

---

## 5a. CORRECTED SCOPE — `REGUH-UBNKS` is OUR bank, not the payee's (claim 489)

Everything I first wrote about the Egypt population rested on reading `UBNKS` as the
beneficiary's bank country. It is **our house bank's country**. Proof: each `HBKID` maps to
exactly one `UBNKS` across the whole table — `SOG01` → FR across **1,943,748 lines as a single
distinct value**, `CIT19` → EG, `CIT04` → US, `BRA01` → BR, `UNI01` → IT, `DEU01` → DE. A
payee-bank field cannot behave that way. `UBNKS/UBNKL/UBKNT/UBHKT` are the house-bank block.
The beneficiary's bank country is `LFBK-BANKS` — exactly what `u917` reads.

Citi binds payments *"destined for **or** originating within"* Egypt. Two populations:

| Population | How to find it | Lines | `u917` would block |
|---|---|---:|---|
| **Originating in Egypt** — paid from our Citibank Egypt account | `HBKID='CIT19'` | 392 | **65 (17%)** |
| **Destined for Egypt** — beneficiary banks in Egypt, method N | `LFBK-BANKS='EG'` | 9,095 | **8,103 (89%)** ≈ USD 41.5M |

**The configuration is worth far more than first assessed.** The control is well designed for
the destined-for half — 89% coverage, and those payments *do* produce a payment file, so both
capture and rendering apply. It is weak only on the originating-in half: 254 of those 392 lines
go to payees with **no `LFBK` row**, so `CHECK lv_banks IS NOT INITIAL` exits and the control
never fires. Those are the cheques.

**A master-data ceiling no configuration can lift:** 1,225 of 2,762 Egypt-domiciled vendors
(44%) have no `LFBK` row. For every one of them `u917` is inert whatever is entered in
`YTFI_PPC_STRUC`.

## 5b. HOW YOU MAKE A COUNTRY MANDATORY — the change spec

This is the actual question behind the Egypt request: *how does a country get onto the list
that forces a reason for payment?*

**One row type is the switch.** `u917` blocks the posting when the vendor's bank country has
**any** `YTFI_PPC_STRUC` row with `PPC_CODE = 'PPC_VAR'` or `'PPC_DESCR'`. Everything else
makes the code *usable* and *renderable*; that row makes it **mandatory**.

### The model: Jordan, the cleanest country (13 of 13 lines carry a code)

| Table | Rows | Content |
|---|---:|---|
| `YTFI_PPC_TAG` | 1 | `JO · USTRD · C · <PmtInf><CdtTrfTxInf><RmtInf><Ustrd>` |
| `YTFI_PPC_STRUC` | 18 | 6 building blocks × 3 pay types (`O` third-party, `P` payroll, `R` replenishment) |
| `T015L` | 10 | `JO0`…`JO9` — the codes the clerk picks from |

The 6 blocks per pay type, in `CODE_ORD` order:

```
O (third party)     /  + PURP + /  + PPC_VAR          + / + PAY_FIELD FPAYP-XBLNR
P (payroll)         /  + PURP + /  + FIXED_VAL '206'  + / + PAY_FIELD FPAYP-SGTXT
R (replenishment)   /  + PURP + /  + FIXED_VAL '704'  + / + PAY_FIELD FPAYP-SGTXT
```

Only `O` uses `PPC_VAR` — the clerk's code. Payroll and replenishment are fixed, because the
purpose is known in advance. **`PPC_VAR` on the `O` rows is what makes the country mandatory.**

### The spec for Egypt

### The reason list — verified against ISO 20022 (claims 490 · 495, research `wegppc001`)

An earlier version of this document proposed four codes that **do not exist** — `TRVL`, `RDEV`,
`ITSV`, `TRAI` were invented. Every code below was checked against the published ISO 20022
External Purpose Codes list (125 codes) and confirmed independently against LHV's
`ExternalPurpose1Code` reference.

| `LZBKZ` | `ZWCK1` | Covers — measured across the nine configured countries |
|---|---|---|
| `EG0` | `SUPP Payment for goods or services received` | generic supplier — PH0 **76%** |
| `EG1` | `SCVE Service fees for consulting work` | consulting **and** IT/telecom — AE4 37% · JO6 43% · IN6 21% · MA5 26% · AE3 18% |
| `EG2` | `SALA Salary payment` | payroll — IN9 9% · PH1 3% |
| `EG3` | `BEXP Travel and business expenses` | travel — AE7 13% · PH3 18% · ID0 21% |
| `EG4` | `GDDS Purchase of goods` | goods |
| `EG5` | `CHAR Charitable contribution` | charity — AE1 · PH4 |
| `EG6` | `RENT Rent` | rent — JO9 · AE6 |
| `EG7` | `STDY Training and education services` | training — MA6 11% |
| `EG8` | `GOVT Payment to a government or international organisation` | international organisations — MY3 23% |
| `EG9` | `OTHR Other business services` | **the catch-all, most used of all** — IN7 63% · ID7 34% · MY9 33% · MA9 32%; also absorbs R&D, which has no ISO code |

**Three judgement calls:** ISO has no code for research and development (3rd most-used category)
→ `OTHR`. ISO has no code for financial services (50% of Jordan) → `SCVE`. `OTLC` (Other Telecom
Related Bill) exists but describes a telecom *bill*, not the purchase of IT services → folded
into `SCVE`, keeping the list at ten.

**To be confirmed by the bank.** The codes are valid ISO 20022 values and Egypt adopted ISO 20022
on 2026-06-21, so the family is right. That Citibank Egypt accepts *this selection and wording*
is not verified — confirm with CitiService Egypt before transport. No CBE purpose-code list could
be found in any published source, consistent with the notice asking for a description.

| # | Table | Rows to add | Status |
|---|---|---|---|
| 1 | `T015L` | the 10 rows above | ✅ derived + verified; business approves the wording |
| 2 | `YTFI_PPC_TAG` | 1 row: `EG · USTRD · C · <PmtInf><CdtTrfTxInf><RmtInf><Ustrd>` | ready, copy Jordan |
| 3 | `YTFI_PPC_STRUC` | 18 rows in the Jordan shape; `O` carries `PPC_VAR`, `P`/`R` carry the fixed CBE codes for salary and inter-company transfer | ready once §1 exists |

**Zero ABAP.** All three are maintained tables (SM30 / the customizing view), transported like
any config.

### Two caveats that decide the value of doing it

1. **Capture is enforced for company code `UNES` only** (claim 485). The 387 Egypt-bank-settling
   lines are all UNES, so for the population Citi binds this works — but the 1,720 lines to
   Egypt-domiciled payees in ICTP/UIL/IIEP/UIS/UBO stay uncontrolled.
2. **The rendering half is moot for this path** (claim 488): the Egypt payments leave as
   pre-numbered cheques with no SAP payment file. Adding the rows still buys the *capture* —
   the clerk is forced to state a purpose at invoice entry, and the value is on the document
   for whoever fills the bank portal. That is worth having; it is just not the whole answer.

## 6. Egypt — what the request actually needs

Citi's notice (12 Jul 2026, effective **5 Sep 2026**) requires Purpose of Payment on all RTGS and
Cross-Border Funds Transfers to/from Egypt, in *Transaction Details / Payment Details* or **SWIFT
Field 70**, as narrative text ("Payment for goods received under Invoice 12345").

The request as forwarded — *"add Egypt to the list of mandatory purpose code countries"* —
maps onto two different levers, and only one of them reaches Citi:

| | Effect | Reaches the Citi file? |
|---|---|---|
| Add `EG` rows to `YTFI_PPC_STRUC` with `PPC_CODE='PPC_VAR'/'PPC_DESCR'` | Turns the **capture** control on at invoice entry, zero ABAP | ❌ — renders only on the SocGen CGI tree |
| Add `EG` rows to `T015L` | Gives the codes something to choose from | ❌ on its own |
| `YVENDOR_PAYM_REF` / note-to-payee | Free text into `FPAYP-ZREF01` → `:70` | **The candidate** — needs verification on the CITI medium |

### RESOLVED — there is no SAP payment file to fix (claim 488)

Measured live in P01:

| Evidence | Result |
|---|---|
| `T042E` (UNES, method 3) | `ZFORN='Y110_PRENUM_CHCK'`, `XEIPO` empty → form-based cheque print, **not** the Payment Medium Workbench |
| `T042Z` (FR, method 3) | *"Manual cheque (Pre-Numbered)"*, `PROGN='RFFOUS_C'`, **`XSCHK='X'`** — identical for CA, CH, MZ |
| `REGUT` for the 5 most recent Egypt runs | **no row** — no payment medium file created |
| `PAYR` for the same runs | **no row** — not even the cheque register is written |

**Citi's notice binds RTGS and Cross-Border Funds Transfers submitted through Citi channels.
A pre-numbered cheque is neither, and there is no SAP-generated instruction to add a purpose
field to.** Adding `EG` rows to `YTFI_PPC_STRUC` would switch the *capture* control on at
invoice entry (claim 484), but there is no outbound file for it to render into.

**The remaining fix is procedural**, not a development: whoever issues the actual instruction —
the Cairo office, in the bank's own portal — must populate the Purpose of Payment there. Owner
and channel tracked as `KU-2026-099-EGYPT-INSTRUCTION-CHANNEL`, deadline 5 September 2026.

*Limit of the evidence:* absence of a `REGUT`/`PAYR` row was read per run for the 5 most recent
Egypt runs. It was not verified that `REGUT` holds rows for other runs in the same window, so
the claim is "no row for these runs", not "REGUT is empty".

---

## 7. How to re-derive any of this

```bash
python brain_v2/graph_queries.py search "purpose of payment"   # the claims
python brain_v2/graph_queries.py section U917                  # the control, with line range
python brain_v2/graph_queries.py blocking_code Payment_BCM     # every routine that can block
python brain_v2/graph_queries.py code YRGGBS00                 # where the real source lives
```

⚠️ `YRGGBS00`'s canonical corpus path holds a **29-line stub**; the real 1,593-line body is
UTF-16 at `Zagentexecution/mcp-backend-server-python/YRGGBS00_SOURCE.txt`. `code` returns the
real one and flags `STUB_AT_CANONICAL`. Grepping the corpus for `LZBKZ` returns nothing — that
false negative is what produced claim 116. See rule
`feedback_a_zero_match_grep_is_a_claim_about_your_grep`.

---

## 8. Provenance

| Fact | Source |
|---|---|
| `u917` body, guards, registration | `YRGGBS00_SOURCE.txt:1547-1590` and `:224` (UTF-16) |
| GB931 registration, TCODE/BLART firing list | [`finance_validations_and_substitutions_autopsy.md` §2.4](../PSM/EXTENSIONS/finance_validations_and_substitutions_autopsy.md) |
| PPC tables, DDIC inventory, dispatcher | claims 97, 98, 179 |
| SocGen-only scope | claim 267 — PPC functional spec v2.0 p.16 |
| `Purp>Cd` ← `FPAYP-XREF3` | claim 5 (H18, P01 DMEE tree, 631 nodes) |
| Note-to-payee real behaviour | `extracted_code/FI/YFPAYM_full/Y_FI_PAYMEDIUM_NOTE_TO_PAYEE.abap` (recovered s099) |
| Egypt volumes, T015L/PPC row counts | Gold DB `REGUH`, `LFA1`, `T015L`, `YTFI_PPC_STRUC`, `YTFI_PPC_TAG` |
| Capture compliance | Gold DB `REGUP_SCENARIOS` ⋈ `LFA1` |

## The configuration procedure, and what is wrong with it (claim 496)

**The switch is `YTFI_PPC_STRUC`, not `T015L`.** All nine configured countries carry a `PPC_VAR`
or `PPC_DESCR` row, and that row is what makes `u917` block the posting. `T015L` and
`YTFI_PPC_TAG` do nothing on their own. So a new country goes in **two transports**:

| Transport | Tables | Effect on import |
|---|---|---|
| 1 | `T015L` (10 rows) + `YTFI_PPC_TAG` (1 row) | none — the codes simply become selectable |
| 2 | `YTFI_PPC_STRUC` (11 rows) | **the block and the rendering both start here** |

Put them in one transport and every posting to a vendor banking in that country is blocked the
second the import finishes, with no training done. Rollback is deleting the `YTFI_PPC_STRUC` rows.

**Exact content constants**, measured across the 73 existing `T015L` rows: `BLART='2'`,
`LVAWV='000'`, `ZWCK2` empty (72 of 73), `EDIBL` empty. `ZWCK1` is `CHAR(70)` holding
`code + space + narrative`. `TAG_ID` is `USTRD` for 7 of 9 countries; only AE and CN use
`INSTRINF`.

**Prove the rendering separately from the block.** They are different layers driven by two
different countries — our house bank picks the DMEE class, the vendor's bank picks the config
rows. A passing block is not evidence that anything reaches the file; only reading `<Ustrd>` in a
generated CGI XML is.

### The seven weaknesses

1. **The control tests presence, not correctness.** `T015L` has **no country field** — its key is
   `LZBKZ` alone. The country prefix is a convention. `u917` only checks the field is non-empty,
   so `JO6` on an Egyptian payment passes every layer. Fix: one condition, `lzbkz(2) = lv_banks`.
2. **Three tables, maintained independently, nothing ties them.** Switch without tag = users
   forced to fill a field never written to the file. Silent. Now checked by
   `Zagentexecution/quality_checks/ppc_country_consistency_check.py`.
3. **Vendors with no `LFBK` row are invisible** — `CHECK lv_banks IS NOT INITIAL` exits first.
   254 lines.
4. **No emergency bypass.** `YXUSER` gates five routines; `u917` is not one of them.
5. **A dominant catch-all makes the control cosmetic** — IN7 63%, ID7 34%, MY9 33%, MA9 32%.
6. **Only the FR house-bank class dispatches PPC** — `_DE`, `_IT` and `_FALLBACK` never call the
   lookup. Latent silent failure for any non-FR paying bank.
7. **The control stops at company code `UNES`** — 1,720 lines in the other five institutes.
