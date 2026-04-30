# TRM logistics email · CGI member banks (Shinhan KR, Metro GB, GT NG, SCB14, CIC01, BRA01, etc.)

**Status**: DRAFT (1-page logistics, simplified Session #63 2026-04-30) · Brain anchor: claim 105 + claim 99. **Previous 9-question gating draft superseded.**

**Why this version is shorter**: V001 ships Fully-Structured for `<CdtrAgt>` (the bank's own address block) and `<Cdtr>` / `<Dbtr>` (already structured in V000 for CGI tree). CBPR+ Nov 2026 minimum is Hybrid; Fully-Structured strictly satisfies any bank strictness. Per-bank acceptance design questions retired.

**Attach**: 1 sample V001 CGI pain.001.001.03 XML per bank, plus the generic 5-sample pack from `simulator_output/`.

**Send-list** (one per HBKID — instantiate before send):
- BRA01 (UBO Brazil non-Citi local)
- CIC01 (Côte d'Ivoire)
- SCB14 (Standard Chartered, multiple countries)
- Shinhan Bank (Korea, KRW)
- Metro Bank (UK, GBP)
- Guaranty Trust Bank (Nigeria, NGN)
- Other minor CGI-routed banks per T012K

---

## Subject

UNESCO ISO 20022 CBPR+ pain.001.001.03 (CGI Common Global Implementation) V001 migration — sample file attached

## Body

Dear [TRM Name] / [Bank] Treasury Operations,

UNESCO transmits payments to your institution in [currency] using the CGI multi-bank pain.001.001.03 format (`/CGI_XML_CT_UNESCO`), approximately [N] payments per year.

Ahead of November 2026 CBPR+ deadline, we are migrating to **fully-structured `<PstlAdr>` blocks** (StrtNm / BldgNb / PstCd / TwnNm / Ctry) — including the previously unstructured `<CdtrAgt>/<FinInstnId>/<PstlAdr>` block (your bank's address) sourced from our SAP house-bank master + BNKA bank database.

Attached: **1 sample V001 file** for [Bank] in [currency], generated from a real April 2026 production payment. Validated against pain.001.001.03 (current) and pain.001.001.09 (CBPR+ future) schemas — 100% PASS.

Two items, no responses required to proceed:

1. **Acknowledgement of receipt** — please confirm the attached sample is accepted by your file-ingestion / screening systems. Specifically confirm the structured `<CdtrAgt>` PstlAdr renders correctly on your side.

2. **Currency-specific Payment Purpose Code (PPC) preservation FYI** — if your destination country is among AE / BH / CN / ID / IN / JO / MA / MY / PH, our V001 design preserves the existing PPC tag dispatch on `<InstrForCdtrAgt>/<InstrInf>` and `<RmtInf>/<Ustrd>` — no change to your PPC content. (Skip this point if not applicable to your country.)

Production cutover is planned for Aug-Nov 2026 staggered. CGI tree goes first in our rollout (least disruption). Please flag any blackout periods or preferred weeks.

Thank you,
**Marlies Spronk** · Treasury · UNESCO
**Pablo Lopez** · SAP Configuration · UNESCO

---

## Plan-side notes (NOT to send)

- This email is logistics + courtesy, NOT gating per claim 105.
- Per-bank instantiation requires: HBKID lookup in T012K (bank name + branch), process-mining annual volume (REGUH counts for that HBKID), currency for that route. Marlies + Treasury team fill the [Bank] / [currency] / [N] placeholders.
- Brain anchor: when responses arrive, log each as TIER_2 claim with bank name + verbatim quote + email file path.
