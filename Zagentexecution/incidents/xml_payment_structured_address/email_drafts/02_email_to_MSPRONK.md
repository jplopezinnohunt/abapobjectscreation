**To**: Spronk, Marlies <m.spronk@unesco.org>
**From**: Lopez, Julio Pablo Francisco <jp.lopez@unesco.org>
**Subject**: BCM Structured Address Nov 2026 — Phase 0 closed, summary + Phase 4 UAT pre-arrangement

---

Hi Marlies,

Following up on your email from 14 April about the bank-driven CBPR+ Nov 2026 structured address change. Phase 0 (discovery + design) is complete. Sharing the conclusions and what's ahead — the heads-up for Phase 4 UAT (July 2026) is the only thing that needs you at this stage.

## Phase 0 closure — what's been done

The 3 trees in scope and the per-tree V001 changes are now confirmed end-to-end:

| Tree | V000 (today) | V001 (target Nov 2026) | Bank requirement |
|---|---|---|---|
| `/SEPA_CT_UNES` | Hybrid (`<Ctry>` + `<AdrLine>`) | Add full structured (StrtNm/PstCd/TwnNm/Ctry) | SocGen mandate |
| `/CITI/XML/UNESCO/DC_V3_01` | Dbtr unstructured (no `<Ctry>`!) | Fix Dbtr + add structured | Citi CBPR+ |
| `/CGI_XML_CT_UNESCO` (+`_1`) | Dbtr+Cdtr OK ✅, CdtrAgt unstructured | Fix CdtrAgt structured | CGI-MP banks |

Plus:
- **CITI tree UltmtCdtr** (Worldlink) — also resolved within V001 (no separate V002 needed). The data sources are FPAYH-Z + FPAYP-NAME1, currently emitting AdrLine, V001 will emit StrtNm.

## Validation evidence (technical, optional reading)

We built a Python simulator that reads real production data (REGUH/REGUP/LFA1/ADRC) and renders V000 + V001 pain.001 XML for each scenario.

Result: **794 production scenarios × 3 schema validations = 2,382 PASS / 0 fail** against pain.001.001.03 (current) + pain.001.001.09 (CBPR+ Nov 2026).

Sample XMLs available if you want to inspect — happy to send 5 V000+V001 pairs per tree.

## What we know without needing TRM input

| Bank requirement source | Where we got it |
|---|---|
| SocGen Pattern A overflow logic | Nicolas's TS DMEE doc 29/02/2024 (you discussed with bank, confirmed) |
| Citi CBPR+ structured address | CITIPMW V3 product source code (17 FMs we've extracted) |
| CGI-MP banks (multi-bank) | T042Z routing config + production XML emission patterns |
| pain.001.001.03 + .09 schema | Public ISO 20022 XSDs |

## What WOULD help from you (not blocking, but useful)

If easy/quick:
- **3-5 vendor edge cases** you'd specifically want tested in Phase 3 (vendors > 35-char names, special chars, alt-payee, one-time vendors with BSEC-only address). Process mining gave us 81 statistical scenarios but your tribal knowledge from 31 DMEE transports 2017-2024 might pick edge cases we'd miss.
- **3-5 specific vendor IDs** for live UAT in V01 if you remember any.

No urgency — when convenient.

## Phase 4 UAT (July 2026) — pre-arrangement

This is what I'd like you to be aware of in advance so we can plan together:

- We'll send **pilot files** to SocGen + Citi + CGI-routed banks via their test gateways (separate from prod path)
- Need their **written acceptance** that V001 structured format is accepted at their gateway
- Then UNESCO entity finance leads (FIN/TRS + UBO + UIS + IIEP + UIL) sign UAT close-out
- Cutover Aug → Nov 2026, staggered: CGI first → SEPA → CITI

We'll prepare the pilot file packages + email templates for TRM outreach in Phase 1 (April-May). I'll loop you in on the bank acceptance process.

## What's still open (Phase 1 — your input requested)

- **Bank specs from TRMs** — would you be able to forward our request to SocGen + Citi + CGI banks for their written CBPR+ Nov 2026 acceptance criteria? I can draft the request email; you'd need to forward to the right TRM contacts. **5 minutes of your time.**
- **Vendor master DQ remediation** — 5 active vendors are missing CITY1+COUNTRY in ADRC. Can be batch-fixed by Master Data team. We have the list.

## Detailed evidence (if you want to dig deeper)

- 99 evidence claims (TIER_1) in our internal brain
- 81 production scenarios mapped (HBKID × tree × pay type × currency)
- 30 sample V000+V001 XMLs ready for inspection
- BCM workflow + signatory rules already analyzed (no impact on H13 dual-control work)
- Process mining: SOG01 carries 490K of 942K total UNESCO payments — it's the king test target

Happy to send any specific artifact or schedule 30 min if you'd prefer to walk through. Otherwise the next ask is during Phase 1 (TRM outreach kickoff, ~last week of April).

Best regards,
Pablo

---

**Suggested attachments** (only if useful):
- 1-pager: scope + V001 changes per tree (this email's table 1)
- Sample V000 + V001 XML pair for SOG01 SEPA scenario
- Bank TRM outreach email draft template
