---
name: S/4HANA BP/CVI Migration Readiness — scoreable from our master data (verified)
description: The Business Partner / Customer-Vendor Integration (CVI) migration is the mandatory central pillar of S/4HANA readiness. This documents the VERIFIED method (research wh5gw9exu, s079) and — critically — that we can SCORE BP-readiness NOW from already-extracted master data (LFA1/KNA1/BUT000/CVI_CUST_LINK) with no new extraction, by replicating the CVI_MIGRATION_PRECHK business checks. Feeds the R_S4_READINESS sub-scorecard (brain_v2/capability_model/s4_readiness_model.json).
type: project
---

# S/4HANA BP/CVI Migration Readiness (verified, scoreable now)

Why this matters: in S/4HANA the **Business Partner is the mandatory leading object** that fully
replaces the ECC customer/vendor transactions (XD01/XK01) — "you can no longer create a customer or a
vendor without first creating a Business Partner" (SAP Note 2265093 *S4TWL Business Partner Approach*; CVI
Cookbook KBA 2713963, VERIFIED 3-0). Every customer and vendor must be synchronized to a BP. **No BP/CVI
readiness = no S/4HANA conversion.** It is the single highest-value readiness factor and the one we can
score *today* from our own data.

## How SAP checks it (the method we replicate)
- **Pre-conversion check:** report **CVI_MIGRATION_PRECHK** via transaction **CVI_PRECHK** (CVI_PRECHK
  RUNS the check — it is NOT just a result viewer; that framing was refuted). Runs in the Preparation
  phase, BEFORE synchronization. Delivered down to ECC 6.0 via SAP Note 2743494 / EhP8 SP12.
- **Mass synchronization** (the actual conversion): transaction **MDS_LOAD_COCKPIT**. Creates BP roles
  **FLVN00/FLVN01** (vendor) and **FLCU00/FLCU01** (customer) — the *01 roles only when purchasing-org /
  sales-area data exists in the source record.
- **Links:** **CVI_CUST_LINK** (PARTNER_GUID↔KUNNR) and **CVI_VEND_LINK** (PARTNER_GUID↔LIFNR); common key
  to **BUT000** is **PARTNER_GUID**.

## The 9 business checks (= the BP-readiness scoring dimensions, VERIFIED)
Tax Code · Postal Code · Email · Transportation Zones · Tax Jurisdiction · Number Range · Industry ·
Bank Data · Address. The CVI pre-check scopes by customer/vendor, number range and account group, and runs
any subset of these — so these nine are exactly the dimensions a readiness score must cover.

**Concrete scoreable defect class:** missing **Tax Number Categories** → error *"Tax Type XXX is not
maintained for country YY"* (fix in view V_TFKTAXNUMTYPE via SM30; BP tax numbers stored in DFKKBPTAXNUM).
Detectable per customer/vendor country directly from master data.

## CRITICAL scoring rule (must encode)
A CVI_MIGRATION_PRECHK result of **"All applied Checks (0/0)" means NO check ran** (zero records selected),
**NOT a clean pass** (SAP KBA 3478108, VERIFIED). Our scorer MUST distinguish `0/0` (no denominator) from
`0 errors of N`. Reporting 0/0 as "ready" is exactly the kind of false-clean the methodology forbids.

## Why we can score it NOW (no new extraction — Bucket A)
We already hold in the Gold DB: **LFA1, LFB1, LFBK, KNA1, KNB1, BUT000, CVI_CUST_LINK, BP001, ADRC.**
That is enough to replicate the high-value checks (Tax Number Category per country, Bank Data, Address,
Number Range) over our real customer/vendor master and produce the **first real S/4 readiness score**
(BusinessPartner domain → moves the R_S4_READINESS cell off NONE legitimately, with evidence).
Minor extraction to complete the picture: BUT020, BUT0ID, BUT100, CVI_VEND_LINK, KNBK.

## Where it sits in the model
BP_CVI_READINESS is one factor of the **R_S4_READINESS composite** (fractal sub-scorecard,
`s4_readiness_model.json`). The other verified factors — Simplification-Item (SI-Check
/SDF/RC_START_CHECK, hard gate), Custom-Code (ATC S4HANA_READINESS + CCM), Technical (Maintenance Planner →
stack.xml), Readiness Check 2.0 (Notes 2913617/3059197) — all need a SYSTEM run; **BP/CVI is the only one
scoreable purely from extracted data.** That makes it the natural first build.

## Open (not verified here — do not assert)
Exact source→target BP field mapping (…→BUT000/BUT020/BUT0ID/BUT100) + mandatory BP fields; the Finance
pillars beyond Asset Accounting/ACDOCA (Material Ledger, new G/L, FIN-FSCM-CR, BAM, FINS_MIG_*); greenfield
Migration Cockpit mechanics; the composite weighting of factors into one score.
