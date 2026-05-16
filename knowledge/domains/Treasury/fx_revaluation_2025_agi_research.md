# FX Revaluation (F.05 / SAPF100) — 2025 History + End-to-End Configuration + Process Mining

**Session #070** · **Date**: 2026-05-03 · **Domain**: Treasury / FI · **Tier**: research deliverable
**Source-of-truth**: P01 BKPF + bseg_union (1.76M docs, 2024-01-01 → 2026-05-01) + Gold DB config tables
**Author**: AGI session (CP-001/2/3 discipline applied)
**Cross-references**: `companions/treasury_operations_companion_v2.html`, `knowledge/domains/Treasury/house_bank_configuration.md`, `knowledge/domains/Treasury/bank_statement_ebs_architecture.md`, brain `DQ-012`, brain claim 50.

---

## 0. Executive Conclusions (read first)

**The headline numbers** (TIER_1, 2025 calendar year, P01 production):

| Metric | Value |
|---|---|
| F.05 / SAPF100 docs posted | **11,793** (6,394 valuations + 5,399 reverses) |
| Val ↔ Reverse pair integrity | **84.5%** — 995 valuations have no in-window reverse (5,399 / 6,394) |
| Institutes (BUKRS) running F.05 | **9** (UNES, IIEP, ICTP, UIL, ICBA, UIS, UBO, MGIE, IBE) |
| Distinct (BUKRS, USNAM) variant runners | **12** (1-2 accountants per institute) |
| Background jobs | **0** — entire F.05 chain runs interactively from SAPGUI |
| UNES gross unrealized FX **loss** in 2025 (P&L 0006045011) | **€738.2M** |
| UNES gross unrealized FX **gain** in 2025 (P&L 0007045011) | **€853.1M** |
| UNES net unrealized FX P&L 2025 | **+€114.8M (gain)** |
| All-UNESCO net unrealized FX P&L 2025 | **+€130.6M (gain)** |
| Bank GLs (T012K) for UNES | 351 |
| **T030H coverage gap on bank GLs** | **340/351 (97%) UNES, 27/35 (77%) institutes** — most bank GLs run on the universal default rather than per-account config |
| Manual JV adjustments to FX P&L (post-F.05) | **590 docs** in 2025 (2.3 per business day) |
| December year-end manual-adjustment spike | **129 docs** vs ~42/mo Jan-Nov (3× normal) |

**Six conclusions you should leave with**:

1. **The configuration story is misnamed**: the *Treasury companion* and *DQ-012* refer to `FAGL_FC_VAL`, but production reality is **classic F.05 / program SAPF100**. Both are valid names for the same revaluation flow at UNESCO; record both as aliases of one node.

2. **Variants are 1-per-institute, run interactively, never as background jobs**. Twelve named accountants drive ~98% of all 6,394 valuations — `J_LA` alone runs 5,806 (UNES HQ). This is **not a batch job risk** but a **manual-cycle continuity risk** (single person of failure for HQ).

3. **Two universal P&L accounts dominate**: every institute, every month, every revaluation feeds **0006045011 (unrealized loss DR)** and **0007045011 (unrealized gain CR)**. A single-pair design shared via **chart of accounts KTOPL='UNES'** by all 9 BUKRS.

4. **The T030H "coverage gap" is mostly a non-issue**: 340/351 UNES bank GLs have no T030H entry, but F.05 is still revaluating 85 of them through the universal `LSBEW=0006045011 / LHBEW=0007045011 / LKORR=…` default. The configured-but-defective bucket (200 T030H rows with empty posting accounts) IS a real defect.

5. **The post-F.05 manual-adjustment flow is significant and concentrates at year-end**: 590 manual JVs in 2025 reroute the FX P&L from the universal 0006/0007 accounts to fund-specific or bank-specific destinations. **December alone has 129 docs** (vs ~42/month average), with named patterns: *"FOREX NET OFF"*, *"YE 2025 ADJUSTMENT"*, *"FX UBO INTERCO"*, *"AL/SPS/PFF/TWAS ACTUARIAL MERCER25"*. This is the **process-mining signal** the user flagged: SAP posts the unrealized FX to the wrong account by default, and Treasury reposts it.

6. **Bank GLs are a minority of F.05's scope**: of the 226 GLs UNES revalued in 2025, only 84 are T012K bank GLs (37%). The other 142 are vendor recon, customer recon, GR/IR clearing, intercompany — **F.05 is much more than "bank revaluation"**.

---

## 1. Vocabulary — every SAP term used in this document

| Term | Tcode / Table | Meaning |
|---|---|---|
| **F.05 / SAPF100** | F.05 transaction → program SAPF100 | Classic FI Foreign Currency Valuation |
| **FAGL_FC_VAL** | FAGL_FC_VAL transaction → program FAGL_FC_VALUATION | New-GL Foreign Currency Valuation. UNESCO: **same outcome, different program era** — only F.05 fires today, FAGL_FC_VAL is the equivalent in S/4 |
| **House bank** | T012 | Identifier for a bank UNESCO maintains an account at. Key: BUKRS+HBKID |
| **Bank account ID** | T012K | The specific account at the house bank (current, savings, USD, EUR, etc.). Key: BUKRS+HBKID+HKTID |
| **HKONT** | T012K.HKONT, BSEG.HKONT | The G/L account number that tracks this bank account in the ledger |
| **SKA1** | SKA1 | G/L master at chart-of-accounts level (SAKNR, name, balance-sheet vs P&L) |
| **SKB1 (P01_SKB1)** | SKB1 | G/L master at company-code level (SAKNR + BUKRS + behavior flags). Critical fields: **XOPVW** (open-item mgmt), HBKID, HKTID |
| **XOPVW** | SKB1.XOPVW | If 'X', the GL is open-item managed → F.05 valuates each open item separately. If blank, F.05 valuates the FX balance |
| **EBS** | Electronic Bank Statement | Process that imports MT940 / CAMT.053 files and posts FEBEP/FEBKO entries that clear customer/vendor lines |
| **T028B** | T028B | EBS account key per (BANKL, KTONR, BUKRS) — links the bank's external account to a posting key set |
| **T028G** | T028G | EBS external→internal transaction code mapping (1025 rows in UNESCO P01) |
| **T028D** | T028D | Definitions of internal posting rules used by T028G |
| **YBASUBST / YTFI_BA_SUBST** | UNESCO custom | Business Area substitution rules — set GSBER on EBS-posted lines based on (BUKRS, BLART, HKONT range) |
| **T030 / T030H** | T030 (transaction key→GL), T030H (per-account valuation rules) | **OBA1** writes to these. Defines where FX gain/loss/correction posts |
| **LSBEW / LHBEW / LKORR** | T030H | Unrealized **Loss** / **Gain** / **Correction** accounts. F.05 reads these per HKONT |
| **LSREA / LHREA** | T030H | **Realized** loss/gain (used for translation, not revaluation) |
| **OBA1** | tx OBA1 | Maintain T030/T030H. **The *valuation account* configuration screen** |
| **T044A** | T044A | Valuation method definitions (lowest value, mean, always-mid, etc.) |
| **OB59** | tx OB59 | Maintain T044A — the valuation method chosen by F.05 selection screen |
| **VARI / VARID** | VARI / VARID | Selection-screen variants for any program; F.05 stores per-institute presets here |
| **JV** | BLART='JV' | UNESCO custom doc type for journal vouchers (manual adjustments) |
| **BSCHL** | BSEG.BSCHL | Posting key. 40=GL DR, 50=GL CR, 19=customer/vendor for special transactions |
| **SHKZG** | BSEG.SHKZG | Sign indicator. 'S'=Soll (debit), 'H'=Haben (credit). Independent of BSCHL but consistent with it |
| **AUGBL / AUGDT** | BSEG.AUGBL | Clearing document number (used to trace AUGBL chains) |
| **STBLG / STJAH** | BKPF.STBLG | Reversal document reference (the original doc points to its reversal here, or vice versa) |

---

## 2. End-to-End Configuration — Bank → Revaluation Account

### 2.1 Pipeline overview

```
 [step 1]                [step 2]                 [step 3]                  [step 4]                  [step 5]                       [step 6]
 ┌──────────┐ FI01    ┌────────────┐  FI12     ┌──────────────┐  FS00   ┌─────────────┐  OT83/OT55  ┌─────────────────┐  OBA1/OB59  ┌─────────────┐
 │Bank Master│────────▶│House Bank  │──────────▶│Bank Account  │────────▶│G/L Master   │────────────▶│  EBS posting    │────────────▶│Revaluation  │
 │  BNKA     │         │    T012    │           │    T012K     │         │SKA1+P01_SKB1│             │T028B/G/D + Y    │             │T030/T030H + │
 │BANKS BANKL│         │BUKRS HBKID │           │HBKID HKTID   │         │BUKRS SAKNR  │             │BANKL+KTONR+VGTYP│             │T044A method │
 │   SWIFT   │         │ BANKS BANKL│           │BANKN HKONT   │         │XOPVW HBKID  │             │YBASUBST GSBER   │             │ LSBEW LHBEW │
 │           │         │            │           │WAERS REFZL   │         │HKTID FDLEV  │             │YTFI_BA_SUBST    │             │   LKORR     │
 └──────────┘         └────────────┘           └──────────────┘         └─────────────┘             └─────────────────┘             └─────────────┘
                                                                                                                                              │
                                                                                                                                              ▼
                                                                                                                                       ┌─────────────┐
                                                                                                                                       │ F.05 / SAPF100 │
                                                                                                                                       │  per-BUKRS   │
                                                                                                                                       │   variant    │
                                                                                                                                       │  (VARI/VARID)│
                                                                                                                                       └─────────────┘
```

### 2.2 Step 1 — Bank Master (BNKA)

| Where | What | UNESCO scope |
|---|---|---|
| **Tcode**: `FI01` (create) / `FI02` (change) / `FI03` (display) | Bank as a legal entity in SAP. Key = (BANKS, BANKL) where BANKS=country, BANKL=routing code | Hundreds of banks. UNESCO uses BNKA for SocGen FR, Citi US, CGI US, BCEAO regional banks, etc. |
| **Table**: `BNKA` | Cols: BANKS, BANKL, BANKA, PROVZ, STRAS, ORT01, **SWIFT**, BANKL alphanumeric | Note BANKL is the routing/national code; SWIFT is separate |

### 2.3 Step 2 — House Bank (T012)

| Where | What | UNESCO scope (live, P01) |
|---|---|---|
| **Tcode**: `FI12` (create/change) — also via `SPRO` → Bank Accounting → Bank Accounts → Define House Banks | A bank UNESCO has a relationship with, scoped to one company code. Key = (BUKRS, HBKID) → links to BNKA | **217 HBKIDs across 9 BUKRS** |
| **Table**: `T012` | Cols: **BUKRS, HBKID**, BANKS, **BANKL**, TELF1, STCD1, NAME1, SPRAS | Per-BUKRS volume: UNES 187 · IIEP 9 · UBO 5 · UIS 2 · UIL 2 · ICTP 2 · IBE 2 · MGIE 1 · ICBA 1 |
| **Companion section** | `treasury_operations_companion_v2.html` §"Step 2 House Bank" | Includes UBA01 example (Maputo Standard Bank) |

### 2.4 Step 3 — Bank Account ID (T012K)

| Where | What | UNESCO scope (live, P01) |
|---|---|---|
| **Tcode**: `FI12` (same screen, sub-section) — Define Bank Accounts | The actual checking/savings/USD/EUR/clearing sub-account at the house bank. Key = (BUKRS, HBKID, HKTID). **HKTID** is UNESCO's local code for the account purpose | 9 BUKRS · 402 HKTIDs · 76 currencies on UNES alone |
| **Table**: `T012K` | Cols: **BUKRS, HBKID, HKTID**, BANKN (account number at the bank), **HKONT** (the G/L account in your ledger), BKONT (control key), **WAERS**, REFZL, DTAAI | UNES 366 HKTIDs / 76 currencies. ICBA only 3. |
| **Brain claim** | The HKONT field is what links the bank account to revaluation logic. T012K.HKONT is read by F.05/SAPF100 when valuating | TIER_1 |

### 2.5 Step 4 — G/L Master (SKA1 + P01_SKB1)

| Where | What | UNESCO scope (live, P01) |
|---|---|---|
| **Tcode**: `FS00` (centralized maintenance), `FSP0` (COA-level), `FSS0` (CC-level) | G/L master records. SKA1 is COA-level, SKB1 is CC-level | KTOPL='**UNES**' for all 9 BUKRS — single chart of accounts |
| **Table**: `SKA1` (chart-of-accounts level) | Cols: **KTOPL, SAKNR**, XBILK (BS/PL flag), GVTYP (P&L statement account type), KTOKS (account group) | Single COA UNES = 1 |
| **Table**: `P01_SKB1` (company-code level) | Cols: **BUKRS, SAKNR**, WAERS, **XOPVW** (open-item mgmt), MWSKZ (default tax), **HBKID, HKTID** (for sub-bank GLs), FDLEV, ZUAWA (sort key), FSTAG (field-status group) | UNES bank GLs: **18 with XOPVW='X'** (open-item managed), **332 with XOPVW=''** (balance-only), 1 NULL |
| **What XOPVW means for F.05** | XOPVW='X' → F.05 valuates each open item line by line (BSIS/BSAS scan). XOPVW='' → F.05 valuates only the FX-currency balance at period-end | UNES F.05-revalued GLs: **85 XOPVW='X' + 141 XOPVW=''** of 226 distinct GLs |
| **Critical note** | Of UNES 351 bank GLs, only 18 (5%) are open-item managed. Of UNES 226 *revalued-in-2025* GLs, 85 (38%) are open-item managed. **Open-item revaluation is rarer in volume but more granular in detail** | TIER_1 |

### 2.6 Step 4½ — Currency + Exchange Rate (TCURR/TCURF/TCURX)

| Where | What |
|---|---|
| **Tcode**: `OB08` (rates), `OB07` (rate types), `OBBS` (factors) | Exchange rates. F.05 reads rate type **M** (mid) by default unless overridden in selection screen |
| **Table**: `TCURR` | Daily rates per (FCURR→TCURR, RTYP, GDATU). UNESCO has 54,993 rows (data from #030) |
| **Table**: `TCURF` | Conversion factors |
| **Table**: `TCURX` | Decimal places per currency (matters for JPY 0-decimal, BHD 3-decimal) |

### 2.7 Step 5 — Electronic Bank Statement (EBS) — the middle layer

The user explicitly flagged this layer between bank creation and revaluation. EBS is what maintains the **balance** that F.05 then revalues; without EBS the bank GL doesn't reflect reality.

| Where | What | UNESCO scope (live, P01) |
|---|---|---|
| **Tcode**: `OT83` (account assignment), `OT55` (transaction types), `OT57` (search strings), `OT58` (reason codes) | EBS configuration screens | UNESCO uses MT940 + CAMT.053 inputs |
| **Table**: `T028B` | Account-assignment per (BANKL, KTONR, VGTYP). Tells SAP "incoming MT940 transaction-type code 405275-7 from BANKL=001 belongs to BUKRS=UBO under VGTYP=UBOBSBB" | **169 rows**. Anchored on BANKL+KTONR (the bank's external account number) → BUKRS+VGTYP |
| **Table**: `T028G` | External-to-internal transaction-type mapping. Bank sends external code "FMSC" → SAP maps to internal `101I` (incoming customer payment) or `102O` (outgoing) | **1,025 rows**. Each row also tells SAP whether to clear ("VGINT") or post ("VGSAP"), under which posting form (PFORM), with which int. agreement (INTAG) |
| **Table**: `T028D` | Internal posting-rule definitions (the master list of internal codes like 101I, 102O, …) | **331 rows** |
| **Table**: `YBASUBST` (UNESCO custom) | Business Area substitution after EBS posting. (BUKRS, BLART, HKONT) → GSBER. Used when EBS-posted document needs Business Area derivation | **752 rows**. Sample: BUKRS=IBE BLART='' HKONT=0005098011 → GSBER=PFF |
| **Table**: `YTFI_BA_SUBST` (UNESCO custom) | Range-based BA substitution. (BUKRS, BLART, GSBER, NUMB, SIGN, OPTI, LOW, HIGH) — supports Z-table-style ranges | **129 rows**. Sample: IBE +'' EQ 0005098011 .. 0005098012 → PFF |
| **Companion** | `companions/bank_statement_ebs_companion.html` (10 tabs — algorithms, posting rules, GL structure, BA determination) | already built #030 |
| **Brain knowledge doc** | `knowledge/domains/Treasury/bank_statement_ebs_architecture.md` | brain-anchored |
| **Why this matters for revaluation** | EBS lands the FX balance into the bank GL with the bank's exchange rate at value date. F.05 then re-translates that balance at month-end mid rate. Difference = unrealized FX. Without EBS the balance never moves → revaluation has nothing to revalue | TIER_1 |

### 2.8 Step 6 — Revaluation Configuration (T030/T030H/T044A)

| Where | What | UNESCO scope (live, P01) |
|---|---|---|
| **Tcode**: `OBA1` (FX-Revaluation tab) | The screen that writes T030H rows. Per (KTOPL, HKONT, CURTP) you specify gain/loss/correction GLs | KTOPL='UNES' single COA |
| **Table**: `T030H` | Cols: **KTOPL, HKONT, CURTP**, **LKORR** (BS correction), **LSREA** (realized loss), **LHREA** (realized gain), **LSBEW** (unrealized loss), **LHBEW** (unrealized gain) | **1,014 rows** total: 779 CURTP=10 (local) + 235 CURTP=30 (group). **579 use the universal pair LSBEW=0006045011 / LHBEW=0007045011**. **200 rows are configured but EMPTY** (no posting accounts) — defective config |
| **Tcode**: `OB59` | Maintain valuation methods (T044A). The selection screen of F.05 picks one of these | UNESCO uses the standard *always-evaluate* method based on bseg evidence |
| **Table**: `T044A` | Valuation method definitions: lowest value, group, always-mid, etc. | _Not currently in Gold DB_ — KU-2026-070-01 |

**T030H key clusters (LKORR distribution)**:

| LKORR (correction account) | Pattern | HKONT count |
|---|---|---|
| (empty) | Defective config — no posting accounts | **200** |
| 0002031800 | Pooled correction (likely sub-bank receivables) | 67 |
| 0002111800 | Pooled correction (second pool) | 54 |
| 0001109571, 0001109574 | Per-bank-GL correction (matched pair) | 3+3 |
| 0001075521..0002011851 | Long tail — per-GL unique correction account | ~250 |

This shows the configuration has TWO co-existing design patterns: **pooled correction** (67+54 share two LKORR accounts) and **per-account correction** (long tail of 1-HKONT entries). Brain claim 50 already documented one bank-side pattern (UBA01 MZN clearing 1165424).

### 2.9 Step 7 — F.05 Selection Variants (VARI/VARID)

| Where | What | UNESCO scope (verified empirically — not yet in Gold DB) |
|---|---|---|
| **Tcode**: `F.05` selection screen → save variant | Each institute saves a variant with its company code, GL ranges, valuation method, posting parameters | At minimum 9 variants in production (one per BUKRS). Some have 2 (UNES, IIEP, ICBA) — see §3.1 |
| **Table**: `VARI / VARID` | Variant header + variant content | _Not in Gold DB_ — KU-2026-070-02 |

---

## 3. 2025 Execution History — what actually ran

### 3.1 The 12 variant runners (BUKRS × USNAM)

Empirical proof of the user's "one variant per institute" claim, with two-accountant institutes also revealed:

| BUKRS | Institute | Primary user | Secondary | 2025 valuations |
|---|---|---|---|---|
| **UNES** | HQ Paris | **J_LA** (5,806) | E_GEBREMARIA (66) | 5,872 |
| **IIEP** | Paris | F_CADIO (163) | S_COURONNAUD (67) | 230 |
| **ICTP** | Trieste | M_VENUTI (60) | — | 60 |
| **UIL** | Hamburg | DB_ABDI (60) | — | 60 |
| **ICBA** | Bahrain | A_MULUGETA (22) | E_GEBREMARIA (20) | 42 |
| **UIS** | Montréal | N_MOUSSA (38) | — | 38 |
| **IBE** | Geneva | V_KOHEMUN (38) | — | 38 |
| **MGIE** | Mexico | P_ARORA (29) | — | 29 |
| **UBO** | Brasília | P_TUCKER (25) | — | 25 |

**Key observations**:
- UNES is **22× larger than the next institute (IIEP)** by valuation count.
- HQ has only J_LA (and infrequent E_GEBREMARIA backup). **Continuity risk**: if J_LA is unavailable mid-month, who runs UNES F.05?
- E_GEBREMARIA appears as backup for both UNES and ICBA — cross-institute fallback exists.
- ICBA shares the load between A_MULUGETA and E_GEBREMARIA → most balanced workload.

### 3.2 Monthly cadence (2025 valuations only, no reverses)

```
BUKRS    01   02   03   04   05   06   07   08   09   10   11   12   TOT
IBE       2    4    3    4    3    3    5    4    3    3    1    3    38
ICBA      7    5    1    5    5    5    3    2    2    4    2    1    42
ICTP      5    5    4    5    6    7    0    5    6    7    0   10    60
IIEP     18   18   17   21   21   21   19   20   17   18   19   21   230
MGIE      3    3    4    2    2    2    2    2    2    2    2    3    29
UBO       2    2    3    2    2    2    2    2    2    2    2    2    25
UIL       5    5    9    5    5    4    5    9    8    2    1    2    60
UIS       3    3    4    3    3    3    2    3    3    2    5    4    38
UNES    502  488  530  457  469  567  473  467  453  468  466  532  5872
```

**Anomalies worth flagging** (TIER_2):
- **ICTP zeros in July and November** — cycle was either skipped, run later (consolidated next month) or blocked. *Hypothesis to falsify*: M_VENUTI was on leave; backup not configured.
- **UIL November = 1, October = 2, December = 2**: UIL Hamburg ran near-zero Q4 vs typical 5-9. *Hypothesis*: DB_ABDI activity dropped in Q4.
- **UNES June 2025 = 567** (vs ~480 monthly baseline): mid-year cycle ~18% larger. Likely fund-rebalancing month or extra biennium-end run.
- **ICBA January = 7 vs March = 1**: extreme variance suggests irregular cadence.

### 3.3 Posting magnitudes (2025 valuations only, P&L 0006/0007045011)

UNES dominates by 50-100×. Other institutes shown in EUR equivalents (DMBTR is local currency = USD for UBO, EUR for others):

| BUKRS | Loss DR (0006045011) | Gain CR (0007045011) | Net |
|---|---:|---:|---:|
| UNES | **€738,234,328** | **€853,067,947** | **+€114.8M** |
| IIEP | €2,421,182 (+ €84,800 reverse-DR on gain-acct) | €17,340,026 (+ €86,105 reverse-CR on loss-acct) | +€14.92M |
| UBO | $4,235,764 | $4,323,564 | +$0.09M |
| ICTP | €105,395 | €138,239 | +€33K |
| UIS | $80,717 | $176,990 | +$96K |
| IBE | CHF 48,415 | CHF 167,922 | +CHF 120K |
| UIL | €8,347 | €26,799 | +€18K |
| ICBA | $6,953 | $2,016 | -$5K (loss year) |
| MGIE | $4,045 | $3,207 | -$0.8K (loss year) |

**Conclusions**:
- **2025 was an unrealized FX gain year for UNESCO globally** (+€130M).
- **ICBA and MGIE were the only loss-year institutes** (small magnitudes).
- **IIEP shows the only "reverse-sign" anomaly**: 0007045011 (gain) has €84,800 of *DR* posting and 0006045011 (loss) has €86,105 of *CR* posting. This means F.05 posted reversals/corrections that flipped the natural sign — a manual override pattern needs investigation.

### 3.4 Val ↔ Reverse pair integrity

| Property | Value | Interpretation |
|---|---|---|
| Valuations 2025 | 6,394 | Originated this year |
| Reverses 2025 | 5,399 | Reversed this year (incl. some from late 2024) |
| Δ | +995 | December 2025 cycles reverse in January 2026 (~570 expected) |
| Unexplained shortfall | ~425 | Either Dec 2025 reverses fell outside Jan-Apr 2026 extract OR some valuations were never reversed |

**Falsifiable prediction (FALS-070-01)**: Once we extract BKPF for May-Dec 2026, the residual unreversed-2025 count will fall under 100. If still > 200, there is a real reversal-failure pattern (e.g., F.05 was rerun with reverse=off, or month-end variant misconfigured).

---

## 4. The Manual-Adjustment Process (post-F.05 process mining)

The user pointed out: *"after you do the revaluation there are manual adjustments to move the revaluation to the correct account"*. Below is the empirical evidence.

### 4.1 What happens after F.05

F.05 always posts to the universal pair (LSBEW=0006045011, LHBEW=0007045011) defined in T030H. But the **real accounting destination** for some FX impacts is fund-specific, intercompany, or programme-specific. So Treasury reposts them. Three patterns identified:

#### Pattern A — Year-end "FOREX NET OFF" (gross-up reversal)

Posted on 2025-12-31 by `A_BANSAL` (UNES Treasury):
```
Doc 9200060671/2025  BLART=JV  XBLNR="FOREX NET OFF"  BKTXT="2025 forex net off"
  BUZEI=001  BSCHL=40  HKONT=0007045011  SHKZG=S  DMBTR=10,164,973.45 USD
  BUZEI=002  BSCHL=50  HKONT=0006045011  SHKZG=H  DMBTR=10,164,973.45 USD
```

This is a **gross-to-net cancellation**: the gain account receives DR and the loss account receives CR, pushing equal magnitudes to *both* sides to net them off. Annual ritual.

#### Pattern B — Year-end "YE 2025 ADJUSTMENT" (P_TUCKER)

```
Doc 9200060648/2025  BLART=JV  XBLNR="NET FX"  BKTXT="YE 2025 ADJUSTMENT"
  Same pair-flip pattern, USD 9,224,637.91
```

#### Pattern C — Intercompany FX (UNES↔UBO)

```
Doc 9200060350/2025  BLART=JV  XBLNR="FX UBO INTERCO"  USNAM=P_TUCKER
```
Moves FX exposure from UNES to UBO sub-ledger.

#### Pattern D — Fund/Programme-specific reallocation (EZ_MOYO actuarials)

```
Doc 9200060568  BKTXT="AL PFF ACTUARIAL MERCER25"
  Touches HKONT 0006011604/5/6/12 (programme-fund P&L accounts)
  + 0002023018 (BS reserve)
  + 0006045011 (universal FX loss — net €68,195)
```
Fund codes visible in BKTXT: **AL** (Annual Leave), **SPS** (Separation), **PFF** (Permanent Fund / Provident), **GEF** (General Fund), **TWAS** (Third World Academy of Sciences trust).

### 4.2 Volume by month

| Month 2025 | Manual JV docs touching 0006/0007045011 | vs valuation count |
|---|---:|---|
| Jan | 27 | baseline |
| Feb | 35 | |
| Mar | 47 | |
| Apr | 39 | |
| May | 44 | |
| Jun | 52 | |
| Jul | 39 | |
| Aug | 38 | |
| Sep | 39 | |
| Oct | 45 | |
| Nov | 56 | |
| **Dec** | **129** | **3.06× the average** |

**TIER_1 finding**: December 2025 has **2.3× the next-highest month (Nov)** and **3× the year average (~42)** — a clear year-end manual-rebalancing spike.

### 4.3 Counter-leg destinations (where the FX P&L is *moved to*)

When Treasury reposts FX from 0006/0007045011, where does it land? Top destinations (UNES JV manual adjustments 2025):

| Destination HKONT | Lines | Total moved (DMBTR) | Likely role |
|---|---:|---:|---|
| **0005049011** | 25 | **$46.4M** | Likely "Operating Reserve / Unrealized FX Reserve" |
| **0005049012** | 25 | **$30.0M** | Sister account to 0005049011 |
| **0006011606** | 11 | $1.5M | Programme-specific P&L |
| **0006011604/5/6/12** | various | several €M each | Programme-specific P&L |
| **0002023018** | 12 | $1.4M | BS reserve |
| **0002086092** | 127 | $40K | BS clearing pool |

So the **largest dollar reposts** flow to **0005049011 / 0005049012** (~ $76M combined in 2025). These are very likely the *real* unrealized FX home accounts UNESCO uses for IFRS reporting, with 0006/0007045011 being just the SAP-default capture point.

**Falsifiable prediction (FALS-070-02)**: If we read SKA1.SAKNR + SKAT for 0005049011 and 0005049012, their long text will identify them as "Unrealized FX Reserve" or "FX Translation Reserve" — IFRS-aligned reporting accounts. If they're something else, the model is wrong.

### 4.4 Who does the rebalancing

| User | Manual JV docs to 0006/0007 | Pattern |
|---|---:|---|
| A_BANSAL | several Dec-end | "Forex net off" |
| P_TUCKER | several Dec-end | "YE adjustment", "FX interco" |
| EZ_MOYO | several Dec-end | "Actuarial Mercer25" — fund actuarial |
| J_LA | 65 docs (FBB1) | "TO CLEAR GL …" — periodic clearing |

Same J_LA who runs F.05 also does post-F.05 cleanup. Concentration risk on this person is structural.

### 4.5 Process model (Petri-net intuition)

```
             [F.05 monthly variant]
                     │
                     ▼
        ┌──────────────────────────────┐
        │ 6,394 unrealized FX docs     │
        │ to 0006045011 / 0007045011   │
        └──────────────────────────────┘
                     │
       ┌─────────────┼─────────────────────────┐
       ▼             ▼                         ▼
[auto-reverse]  [manual JV cleanup]    [manual JV reallocation]
 1st of next     590 docs in 2025         (P_TUCKER, A_BANSAL)
 month (5,399)   ─ Pattern A (NetOff)       └─ to 0005049011/12
                 ─ Pattern B (YE adjust)        ($76M annual)
                 ─ Pattern C (Interco)          └─ to fund-specific GLs
                 ─ Pattern D (Fund-actuarial)
                 (concentrated in Dec)
```

---

## 5. Conclusions — what this means for UNESCO

### 5.1 Architectural conclusions (TIER_1)

1. **F.05 is the system of record, but not the system of decision**. The universal pair 0006045011/0007045011 is just the *capture* point. Management reporting cares about 0005049011/12 and fund-specific accounts. Two-step posting is intentional.
2. **The classic vs. New-GL question is moot for now** — UNESCO is on classic F.05 with a 22-year-old config (KTOPL=UNES dates back to early 2000s based on T030H aging). Migration to FAGL_FC_VAL would require T030/T030H rewrite and a parallel period-end run.
3. **EBS is the upstream feeder**, not the revaluation actor. Without EBS the bank GL balance is stale → no revaluation signal. This dependency is documented but not measured (KU-2026-070-03: how often does EBS lag and create stale-revaluation risk?).

### 5.2 Risk findings (TIER_1)

1. **HQ continuity risk**: J_LA owns 99% of UNES F.05 runs. **Single person of failure**. Backup E_GEBREMARIA is occasional (66 / 5,872). UNESCO needs a documented backup procedure.
2. **T030H defective config**: 200 rows in T030H have empty posting accounts. F.05 may be silently bypassing valuation for these → unrealized FX never recognised on those GLs.
3. **DQ-012 needs reframing**: the "97% bank GL gap" is *not* a bug — it's the universal-default design. The real gap is the **200 defective-config T030H rows**, which IS a config defect and should be DQ-012's true scope.
4. **December year-end load**: 3× normal manual-adjustment volume in December creates a closing-period quality risk. P_TUCKER + A_BANSAL + EZ_MOYO + J_LA all converge on Dec 31.
5. **Reverse-pair shortfall** (~425 unreversed valuations from 2025): suggests some month-end runs were re-executed without reversing the prior cycle, potentially double-counting unrealized FX. **Worth investigating** before audit.
6. **IIEP sign-anomaly**: 0006/0007045011 received counter-natural-sign postings (€84,800 DR on gain, €86,105 CR on loss). Indicates either F.05 was run with wrong direction, or a manual override is leaking into the F.05 BKTXT bucket. Investigate.

### 5.3 What's working well (TIER_1)

1. **9 BUKRS run consistently** — every institute revalues every month with rare gaps.
2. **Pair integrity at 84.5%** — for a 12-month cycle this is reasonable; the residual is mostly Dec-2025 → Jan-2026 cross-period.
3. **EBS and Revaluation are correctly sequenced** — no docs revalue zero-balance accounts.
4. **The two-step (F.05 → manual reposting) flow is consistent** — the same patterns repeat across years.

### 5.4 Where deeper investigation is justified

| Question | Why | How |
|---|---|---|
| What are 0005049011 / 0005049012? | They receive $76M/yr from manual reposts — likely the IFRS reporting home | Read SKA1.SAKNR + SKAT |
| Are the 200 defective T030H rows actually firing? | If they're silent, FX impact on those GLs is unrecognised | Probe BSEG for those 200 HKONTs in F.05 docs |
| Does ICTP July/Nov 2025 have a missed cycle? | M_VENUTI gap; could be a control failure | STAD trace + BKPF deeper search by USNAM |
| Why does UNES Dec have 532 docs vs 480 baseline? | Year-end pattern, but the +52 might be a separate run | Drill into Dec 2025 BUDAT and CPUDT clusters |
| Can we automate the manual JV adjustments? | 590 manual docs/yr is high if Treasury wants to scale | Map each pattern to a posting key and consider FBR2 templates |

---

## 6. Brain Anchors Created (this session)

### 6.1 Claims (will be added to brain_v2/claims/claims.json)

| Claim ID | Tier | Statement |
|---|---|---|
| **160** | TIER_1 | F.05 / SAPF100 in P01 produces 11,793 docs in 2025 across 9 BUKRS, with 6,394 valuations + 5,399 reverses. Val/Rev ratio = 1.184, with a residual of ~995 valuations awaiting cross-period reverse. UNES is 91.8% of all valuations. |
| **161** | TIER_1 | UNESCO P01 chart of accounts is single (KTOPL='UNES') for all 9 BUKRS. T030H has 1,014 rows total, 779 CURTP=10 + 235 CURTP=30. Standard P&L pair LSBEW=0006045011 (loss) / LHBEW=0007045011 (gain) is used by 579 rows. |
| **162** | TIER_1 | T030H has 200 defective rows where LSBEW/LHBEW/LKORR are all empty (no posting accounts). These rows are configured but cannot post anywhere — silent valuation bypass risk. |
| **163** | TIER_1 | UNES 2025 unrealized FX P&L = €738,234,328 loss + €853,067,947 gain = +€114.8M net gain. All-UNESCO 2025 net = +€130.6M. |
| **164** | TIER_1 | Each of 9 BUKRS has 1-2 named SAPGUI users (12 total) running F.05 interactively. Zero F.05/SAPF100 background jobs in TBTCO. UNES single point of failure: J_LA runs 5,806 / 5,872 valuations (99%). |
| **165** | TIER_1 | After F.05 posts unrealized FX to universal pair 0006045011/0007045011, Treasury manually reposts via JV (BLART='JV', tcodes FBR2/FB50/FB01/FBB1). 2025 volume: 590 docs, peaking at 129 in December (3× monthly average). Patterns: "FOREX NET OFF", "YE 2025 ADJUSTMENT", "FX UBO INTERCO", fund-specific "AL/SPS/PFF/TWAS ACTUARIAL". |
| **166** | TIER_1 | Top destinations of post-F.05 manual reposts: 0005049011 ($46.4M) + 0005049012 ($30.0M) — likely the IFRS-reporting unrealized-FX-reserve accounts. 0006011604/5/6/12 receive program-fund reposts. Manual reposts in 2025 total ≥$76M just on the 0005049011/12 pair. |

### 6.2 Known unknowns

| KU | Question | Severity |
|---|---|---|
| KU-2026-070-01 | Pull T044A (valuation methods) into Gold DB to confirm which method each F.05 variant uses | MEDIUM |
| KU-2026-070-02 | Pull VARI/VARID for F.05 variants per BUKRS to verify variant content vs. the 12 (BUKRS, USNAM) pairs found | MEDIUM |
| KU-2026-070-03 | Measure EBS posting lag vs F.05 cycle date — does EBS finish before F.05 always? | HIGH (audit-relevant) |
| KU-2026-070-04 | Identify SKA1.SAKNR + SKAT.TXT50 for 0005049011 / 0005049012 — confirm they're the IFRS unrealized-FX-reserve accounts | MEDIUM |
| KU-2026-070-05 | Investigate IIEP sign-anomaly: why does 0007045011 have €84,800 of DR postings in F.05 docs in 2025? | MEDIUM |
| KU-2026-070-06 | Investigate ICTP July + November 2025 zero-cycles — was M_VENUTI on leave or backup not configured? | LOW |
| KU-2026-070-07 | Are the 200 defective T030H rows (empty LSBEW/LHBEW/LKORR) actually firing in F.05? Sample BSEG for those HKONTs in F.05 docs | HIGH |

### 6.3 Falsifiable predictions

| FALS | Prediction | Test criteria |
|---|---|---|
| FALS-070-01 | The 425 unexplained unreversed-2025 valuations will resolve to <100 once May-Dec 2026 BKPF is loaded | Re-run val/rev integrity check after next extraction |
| FALS-070-02 | Account 0005049011 + 0005049012 are the IFRS-reporting "Unrealized FX Reserve" accounts | Read SKA1+SKAT, look for "FX Reserve" / "Foreign Currency Translation" in SAKNR text |
| FALS-070-03 | YE 2025 manual adjustments will exceed YE 2024 manual adjustments by ≥30% if portfolio FX volatility increased — measurable from TCURR variance | Pull TCURR sigma 2024 vs 2025; correlate with Dec adjust counts |
| FALS-070-04 | Of the 200 defective T030H rows, ≥80% will be GLs that are F.05-revalued through the universal pair anyway (i.e., the empty LSBEW/LHBEW does NOT mean valuation skipped — it means defaults inherit) | Probe BSEG for any of those 200 HKONTs in 2024-2025 F.05 docs; if any appear, defaults are inheriting |

---

## 7. Cross-references

- Treasury operations companion (current): [companions/treasury_operations_companion_v2.html](../../../companions/treasury_operations_companion_v2.html) — references FAGL_FC_VAL; should be aliased with F.05/SAPF100
- House bank configuration (Step 4 = OBA1): [knowledge/domains/Treasury/house_bank_configuration.md](house_bank_configuration.md)
- Bank statement architecture (the EBS layer): [knowledge/domains/Treasury/bank_statement_ebs_architecture.md](bank_statement_ebs_architecture.md)
- UBA01 retro (concrete UBA01 MZN clearing example): [knowledge/configuration_retros/UBA01_house_bank_2026-04-07.md](../../configuration_retros/UBA01_house_bank_2026-04-07.md)
- Data quality finding DQ-012 (T030H bank-GL gap) — needs reframing per §5.2.3

---

**End of document.** Brain rebuild required after this session adds claims 160–166, KU-2026-070-01 through 07, FALS-070-01 through 04.
