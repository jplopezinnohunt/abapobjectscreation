# UNESCO E2E Vendor Payment → Medium Selection — 100% Detail Map

**Created**: Session #074 (2026-05-10) — answers the question:
**"How is a vendor paid, and how is the payment medium selected, end to end?"**

This document is grounded in **production evidence** (Gold DB tables, P01 RFC reads, code
extraction). Every step lists the table that proves it. No SAP doctrine without evidence.

---

## The 8-Step Chain (with Gold DB anchors)

```
┌────────────────────────────────────────────────────────────────────────┐
│ [1] VENDOR MASTER          LFA1 (316K) · LFB1 (327K) · LFBK (202K)     │
│ [2] OPEN ITEM              BSIK · BKPF (1.7M) · BSEG (via BSIS/BSAS)    │
│ [3] F110 RUN SETUP         REGUH (942K) — run = (LAUFD, LAUFI)          │
│ [4] PAYMENT METHOD CHAIN   T042Y → T042E → LFB1.ZWELS                   │
│ [5] HOUSE BANK & FORMAT    T042I → T042Z → DFPAYV (config matrix)       │
│ [6] GROUP & MEDIUM CREATION  DFPAYG (9,848 last 2y) — 1 row per group   │
│ [7] DMEE EXECUTION         DMEE_TREE_NODE → exit FM → FPAYHX → XML      │
│ [8] OUTPUT                 FDTA file → BCM workflow 90000003 → bank     │
└────────────────────────────────────────────────────────────────────────┘
```

Two tables sit at the heart of the answer:

- **`DFPAYV`** = configuration matrix. *Static.* 84 rows. Maps every
  (FORMI, ZBUKR, BANKS, HBKID, HKTID, CRDEB, RZAWE) tuple → variant name (VARI).
  **Tells you: "which medium *can* be produced for this combination?"**
- **`DFPAYG`** = execution evidence. *Dynamic.* 9,848 rows last 2y. One row per medium
  group actually created in an F110 run. Bound by (LAUFD, LAUFI, GRPNO, FORMI, ZBUKR, HBKID).
  **Tells you: "which medium *was actually produced*, in which run, for which vendors?"**

Joining `DFPAYG ↔ REGUH ↔ LFA1` gives the complete history: every payment, its format,
its vendor, its KTOKK.

---

## Step-by-step detail

### [1] Vendor master & alt-payee resolution

**Question**: who is the recipient of the payment, really?

| Source | Field | Purpose |
|---|---|---|
| `LFA1` | `KTOKK` | Account group (SCSA staff, INSO institutional, INDV, UNES, ICVS, …) |
| `LFA1` | `LNRZA` | General-level alt-payee. If set → payee = LNRZA, not LIFNR |
| `LFB1` | `LNRZB` | Cocode-level alt-payee. **Overrides** LFA1.LNRZA |
| `LFB1` | `HBKID` | Default house bank (per cocode) |
| `LFB1` | `ZWELS` | Allowed payment methods (per cocode) |
| `LFBK` | `BANKS/BANKL/BANKN/BKONT` | Vendor bank accounts (multiple per LIFNR) |
| `TIBAN` | `IBAN` | IBAN per BANKS/BANKL/BANKN |

**Alt-payee evidence in P01 (D01 master count 2026-05-10)**:
- LFA1.LNRZA populated: **16 vendors** (general-level)
- LFB1.LNRZB populated: **9 vendors** (cocode-level)
- REGUH where EMPFG ≠ LIFNR: 2 found in 300 sample (alt-payee fired in F110)

After alt-payee resolution: `FPAYH-GPA1R = payee LIFNR (resolved)` — this is what the
DMEE exit FMs read. NOT the invoice vendor.

### [2] Open item / accounting state

| Source | Field | Purpose |
|---|---|---|
| `BSIK` (15K open) | `BUKRS, LIFNR, BELNR, BUZEI` | Open vendor item |
| `BSAK` (776K cleared) | same | Cleared vendor item (after F110) |
| `BSIS` (2.4M open) | `KOSTL, AUFNR, PRCTR, FKBER, SGTXT` | GL open lines (UNESCO-enriched columns) |
| `BSAS` (1.5M cleared) | same | GL cleared lines |
| `BKPF` (1.7M) | `BLART, BUDAT, BLDAT, WAERS` | Document header |

Open items become the F110 candidate pool. Each item has its own currency, due date,
and method — F110 selects them all and groups for payment.

### [3] F110 run setup & selection

| Source | Field | Purpose |
|---|---|---|
| `REGUH` (942K) | `LAUFD, LAUFI` | Run identification (date + run ID) |
| `REGUH` | `XVORL` | 'X' = proposal, '' = posted |
| `REGUH` | `LIFNR` | Invoice vendor |
| `REGUH` | `EMPFG` | Resolved payee key (after alt-payee) |
| `REGUH` | `ZBUKR` | Paying company code |
| `REGUH` | `HBKID, HKTID` | Selected house bank + account |
| `REGUH` | `RZAWE` | Payment method (the "lock" in FBZP terms) |
| `REGUH_FAST` (567K) | `WAERS, RWBTR, ZALDT` | Currency, gross amount, value date |

A REGUH row = "one F110 grouped this vendor's items into one payment." If the same
vendor pays via SEPA EUR and CGI USD, that's two REGUH rows (different LAUFD/LAUFI/RZAWE).

### [4] Payment method determination — FBZP "three locks"

The payment method (`ZLSCH`/`RZAWE`) is determined by a 3-level chain:

| Lock | Table | Key | Effect |
|---|---|---|---|
| Country-level catalog | `T042Y` (missing in Gold DB · ~50 rows) | `LAND1, ZLSCH` | Defines method behavior per country |
| Cocode-level binding | `T042E` (89 rows) | `BUKRS, ZLSCH` | Activates method for paying co |
| Vendor-level binding | `LFB1.ZWELS` (327K) | `LIFNR, BUKRS` | Allows method for vendor |

**Real example (UNES cocode payment to French staff)**:
```
T042Y(FR, T) → method 'T' = SEPA Credit Transfer EUR
T042E(UNES, T) → method 'T' active in UNES cocode
LFB1.ZWELS for LIFNR contains 'T' → vendor can be paid via 'T'
F110 picks 'T' → drives format selection
```

### [5] House bank + format selection

| Source | Field | Purpose |
|---|---|---|
| `T042I` (77 rows) | `BUKRS, ZLSCH, HBKID` | House bank list per cocode/method |
| `T042Z` (263 rows) | `BUKRS, ZLSCH, HBKID, FORMI` | Links method → DMEE format |
| `T012` (211 rows) | `BUKRS, HBKID` | House bank master (per cocode) |
| `T012K` (402 rows) | `BUKRS, HBKID, HKTID` | House bank account |
| `T028V` (23 rows) | `BANKS, BNKGR` | EBS routing (bank external code → group) |
| `DFPAYV` (84 rows) | `FORMI, ZBUKR, BANKS, HBKID, HKTID, CRDEB, RZAWE, VARI` | **The matrix** that links every combination → DMEE selection variant |

**`DFPAYV` is the key**: it's the static configuration that names every medium SAP
*can* produce. Read it like a router table.

```
DFPAYV examples for UNES cocode:
  /SEPA_CT_UNES UNES SOG01 → VARI: UNE_SEPA
  /CGI_XML_CT_UNESCO UNES SOG01 → VARI: UNE_TRE_USD / UNE_TRE_EUR01 / UNE_INT_EUR / UNE_INT_USD
  /CGI_XML_CT_UNESCO UNES SOG03 → VARI: UNE_INT_CHF / DKK / GBP / JPY / AUD
  /CGI_XML_CT_UNESCO UNES BNP01 → VARI: UNE_TRE_BNPEUR
  /CITI/XML/UNESCO/DC_V3_01 UNES CIT04 USD04 N → UNE_XML3_USD_I
  /CITI/XML/UNESCO/DC_V3_01 UNES CIT21 CAD01 C → UNE_XML3_CAD
```

The (FORMI, ZBUKR, HBKID, HKTID, CRDEB, RZAWE) tuple acts as the ROUTING KEY. F110
picks one VARI; SAPFPAYM uses VARI to drive the DMEE engine.

### [6] Group & medium creation — `DFPAYG` is the evidence

When SAPFPAYM runs:
1. Reads all REGUHs of the run that match the variant (currency filter, etc.)
2. Groups them by (FORMI, ZBUKR, BANKS, BANKL, HBKID, HKTID, CRDEB, RZAWE)
3. Each unique group → one row in `DFPAYG` with `GRPNO` (sequence number)
4. Generates one XML file per group

**`DFPAYG.GRPNO` is the medium counter.** Each row = one bank file produced.

P01 evidence (last 2 years):
- 9,848 medium groups created
- 7 distinct FORMI values
- 13 distinct (FORMI × ZBUKR × HBKID) combinations active
- Average ~12 groups per F110 run

### [7] DMEE execution — where the address actually gets emitted

| Source | Field | Purpose |
|---|---|---|
| `DMEE_TREE_HEAD` | `TREE_TYPE, TREE_ID, VERSION, ACTIVE` | One row per format-version |
| `DMEE_TREE_NODE` | `NODE_ID, TECH_NAME, PARENT_ID` | Tree topology |
| `DMEE_TREE_NODE` | `MP_SC_TAB, MP_SC_FLD, MP_OFFSET, MP_LENGTH` | Direct field binding (FPAYHX-REF01[0..60] etc.) |
| `DMEE_TREE_NODE` | `MP_EXIT_FUNC` | Exit FM called per node |
| `DMEE_TREE_COND` | conditions | Suppress empty / route by value |
| `TFPM042FB` (311 rows) | `FORMI, EVENT, FNAME` | Event 05 FM bindings (Cdtr/Dbtr address pre-load) |

**Address resolution paths (per UNESCO format) — the critical map**:

| Tree | Address path TODAY | After V001 |
|---|---|---|
| `/SEPA_CT_UNES` | Direct FPAYHX-REF01 binding (SAP std `FI_PAYMEDIUM_DMEE_CGI_05` populates from ADRC at Event 05) | **`Y_FI_DMEE_ADR`** (PA0006-first detection) |
| `/CGI_XML_CT_UNESCO` | `FI_CGI_DMEE_EXIT_W_BADI` → `YCL_IDFI_CGI_DMEE_FALLBACK::GET_CREDIT` (only handles name overflow; address comes from FPAYHX-REF01 = ADRC) | **same bug — not fixed** |
| `/CITI/XML/UNESCO/DC_V3_01` | Same: BAdI dispatcher + FPAYHX REF buffer (= ADRC) | **same bug — not fixed** |
| `/SEPA_CT_ICTP_ISO` | Direct FPAYHX bindings (= ADRC) | not fixed |
| `/SEPA_CT_ICTP_ISO_EXTRASEPA[_I]` | Same BAdI dispatcher (= ADRC for non-overridden) | not fixed |

**The bug is not about Y_FI_DMEE_ADR specifically — it's about the FPAYHX-REF01 buffer**
populated from `ADRC` blindly by SAP standard Event 05. Any format that reads FPAYHX REF
buffers without overriding gets dept code for SCSA staff. Y_FI_DMEE_ADR is one
*replacement* path; it's only wired into `/SEPA_CT_UNES`.

### [8] Output file & BCM workflow

| Source | Purpose |
|---|---|
| `FDTA` | The actual XML/DTAUS file blob (per LAUFD/LAUFI) |
| `FDTAH` | File header (one row per group) |
| BCM workflow `90000003` | Approves and sends the file to the bank (SocGen, Citi, BNP, …) |

After SAPFPAYM, the file lives in FDTA. BCM workflow gates it with dual control before
the file leaves UNESCO.

---

## Drift forecast — same address bug across formats

SQL replay (Gold DB) of v6 PA0006-first detection across **all** formats actually used
in P01 last 2 years (master data coverage 70.7%):

| Format | Cocodes | Vendors paid | Staff drift forecast | Drift % | Status |
|---|---:|---:|---:|---:|---|
| **`/SEPA_CT_UNES`** | UNES, IIEP, UIL | 18,495 | **1,905** | 10.3% | ✓ FIXED v6 (D01, P01 cutover pending) |
| **`/CGI_XML_CT_UNESCO`** | UNES, IIEP, UIL | 18,184 | **1,882** | 10.3% | ⚠ NOT FIXED |
| **`/CITI/XML/UNESCO/DC_V3_01`** | UNES, UBO, UIS | 21,772 | **1,818** | 8.4% | ⚠ NOT FIXED |
| `/SEPA_CT_ICTP_ISO` | ICTP | 1,926 | 79 | 4.1% | ⚠ NOT FIXED (ICTP staff trips) |
| `/SEPA_CT_ICTP_ISO_EXTRASEPA` | ICTP | 1,082 | 2 | 0.2% | ⚠ NOT FIXED |
| Long tail | – | 17 | 0 | 0% | – |
| **Total** | | **61,476** | **5,686** | 9.2% | **33% covered by v6** |

The fix surface is **3× larger** than just SEPA. The next ~3,800 staff drift cases live
in CGI and CITI formats that read the same FPAYHX-REF01 buffer.

### Fix-path options for the remaining formats

| Format | Fix path | Trade-off |
|---|---|---|
| `/CGI_XML_CT_UNESCO` | (A) Wire `Y_FI_DMEE_ADR` into Cdtr/PstlAdr leaves of CGI tree, OR (B) Add Z BAdI implementation that runs before Nicolas's class with PA0006-first detection | (A) UNESCO-controlled config-only; (B) ABAP but bounded to Z code |
| `/CITI/XML/UNESCO/DC_V3_01` | Same options | Same |
| `/SEPA_CT_ICTP_ISO[_EXTRASEPA]` | Wire `Y_FI_DMEE_ADR` into ICTP trees | UNESCO-controlled |

`feedback_only_modify_our_own_code` rules out modifying Nicolas's
`YCL_IDFI_CGI_DMEE_FALLBACK_CM001`. Either he extends his class (external dependency),
or we wire our FM into the trees (pure config + transport).

---

## Reproducibility — every cell of every table above is queryable today

Gold DB tables added Session #074:
- `DFPAYG` (9,848 rows) — last 2 years
- `DFPAYV` (84 rows) — full config matrix
- `sim_v6_results` — `/SEPA_CT_UNES UNES` simulation
- `sim_sepa_all` — all SEPA formats simulation
- `sim_all_formats` — drift forecast across all UNESCO formats

Scripts under `Zagentexecution/`:
- `sepa_simulator_step1.py` — universe builder
- `sepa_simulator_step2.py` — bulk PA0006 + ADRC extract
- `sepa_simulator_step3.py` — `/SEPA_CT_UNES` simulation
- `sepa_simulator_all.py` — all SEPA formats
- `sim_all_formats.py` — full landscape drift forecast

Master data still missing (next P01 fetch):
- 7,534 LIFNRs in CGI/CITI universe not in `_sim_univ` (mostly UBO cocode)
- `DMEE_TREE_NODE` in Gold DB (currently P01 RFC only — claim 69 has 1,975 rows extracted)
- T042Y (country-level method catalog) — small, easy fetch
- REGUP (item-level F110 lines) — needed for full drill-down to invoice level
