# TRM logistics email · Citibank (CITI tree + Worldlink)

**Status**: DRAFT (1-page logistics, simplified Session #63 2026-04-30) · Brain anchor: claim 105 (V001 Fully-Structured eliminates per-bank strictness gating) + claim 99 (Q3 RESOLVED system-driven). **Previous 9-question gating draft superseded.**

**Why this version is shorter**: V001 ships Fully-Structured for Cdtr / Dbtr / UltmtCdtr / CdtrAgt blocks. CITI tree's existing XSLT post-processor (`CGI_XML_CT_XSLT`) auto-removes empty leaf nodes — vendors missing some structured fields render cleanly without us asking Citi for tolerance. Q3 (Worldlink UltmtCdtr data source) was answered Session #62 from system data — no Citi clarification needed.

**Attach**: 5 sample V001 CITI pain.001.001.03 XMLs (from `simulator_output/`) — covering: 1× UNES Citi US USD, 1× UBO Citi BR BRL Worldlink, 1× UNES Canada CAD, 2× UltmtCdtr-populated Worldlink edge cases.

---

## Subject

UNESCO `/CITI/XML/UNESCO/DC_V3_01` V001 migration — sample files attached + cutover coordination

## Body

Dear [TRM Name],

UNESCO is migrating the Citi pain.001.001.03 file format (`/CITI/XML/UNESCO/DC_V3_01`) to **fully-structured** ISO 20022 address blocks ahead of November 2026 CBPR+:

- ~85K payments/year · UNES HQ Citi US (CIT04) + UBO Brazil branch (CIT01) + UIS + UNES Canada (CIT21)
- V001 adds structured `<Dbtr>/<PstlAdr>` (5 tags) + structured `<UltmtCdtr>/<PstlAdr>/<StrtNm>` (Worldlink) + completes `<CdtrAgt>/<PstlAdr>` (PstCd + BldgNb)

Attached: **5 sample V001 files** generated from real April 2026 production payments. All validated against pain.001.001.03 + pain.001.001.09 schemas — 100% PASS. Citi's existing `CGI_XML_CT_XSLT` post-processor will continue to auto-remove empty structured leaf nodes (no behavior change there).

Two items, no responses required to proceed:

1. **Acknowledgement of receipt** — please confirm the 5 attached samples are accepted by your screening / DC_V3_01 ingestion. The UltmtCdtr Worldlink samples are the most relevant to confirm (since V001 adds `<StrtNm>` populated from FPAYH-ZSTRA — same field already used in `<AdrLine1>` today).

2. **Cutover-window preference** — UNESCO plans CITI as the **last** tree in our staggered Aug-Nov 2026 rollout. Do you have a preferred week / blackout periods on Citi side?

Thank you,
**Marlies Spronk** · Treasury · UNESCO
**Pablo Lopez** · SAP Configuration · UNESCO

---

## Plan-side notes (NOT to send)

- This email is logistics + courtesy, NOT gating per claim 105. Phase 2 proceeds without responses.
- The /CITIPMW/V3_PAYMEDIUM_DMEE_05 FM (your industry-solution Event 05) is unchanged in V001 — no upgrade needed.
- Brain anchor: when response arrives, log as TIER_2 claim with verbatim quote + email file path.
