# Email drafts package — Phase 0 closure outreach

**Generated**: 2026-04-29 · **Session**: #62

3 emails ready to send + 1 attachment generator suggestion.

## Drafts

| # | File | To | Purpose | When to send |
|---|---|---|---|---|
| 1 | [01_email_to_NMENARD.md](01_email_to_NMENARD.md) | Nicolas Menard (DBS/SDI/TPI) | Phase 0 closure FYI + Phase 2 review heads-up | NOW |
| 2 | [02_email_to_MSPRONK.md](02_email_to_MSPRONK.md) | Marlies Spronk (FIN/TRS) | Phase 0 closure FYI + Phase 4 UAT pre-arrangement + bank TRM outreach request | NOW |
| 3 | [03_email_TRM_template.md](03_email_TRM_template.md) | Bank TRMs (SocGen, Citi, CGI banks) | Bank acceptance criteria pain.001 Nov 2026 | After Marlies forwards |

## Suggested attachments

For Nicolas:
- Sample V000 + V001 XML pair for `/CGI_XML_CT_UNESCO` (Worldlink Madagascar) — `simulator_output/CGI/sample_3_*.xml`
- Pattern A2 ABAP guard 3 lines (already in email body)
- Phase 2 sequencing 1-pager (TBD if needed)

For Marlies:
- Scope summary 1-pager (table from email body works)
- Sample V000 + V001 XML pair for SOG01 SEPA — `simulator_output/SEPA/sample_1_*.xml`
- Bank TRM outreach template (#3 above)

## Tone calibration

- **Nicolas (technical)**: docs decoded, here's what we did, courtesy 5-min review of 3 lines later. Not asking permission, informing.
- **Marlies (business)**: Phase 0 done, scope confirmed, 99% no input needed; one specific ask (TRM forwarding); UAT planning starts.
- **Bank TRM**: clear ask, bounded answer (a/b/c), 2-week window, professional.

## Decisions baked into these drafts

1. Pattern A = A2 (guard, not remove) — bank-mandated, decided.
2. FR/CM002 retrofit — confirmed, in Phase 2 Step 0.
3. Q3 UltmtCdtr unified into V001 (no V002 needed).
4. PPC system preserved — V001 changes don't touch InstrInf/Ustrd nodes.
5. Cutover order CGI → SEPA → CITI.
6. Test pyramid L0-L3 (proposal mode in D01 → V01 → bank pilot → prod).

If responses change any of these, log in brain claims + update plan.

## Tracking responses

| From | Response | Action | Logged |
|---|---|---|---|
| Nicolas | (pending) | | |
| Marlies | (pending) | | |
| SocGen TRM | (pending) | | |
| Citi TRM | (pending) | | |
| CGI banks TRMs | (pending) | | |

Update this table as responses arrive.
