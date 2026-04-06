# Session Learning: Payment Process Mining — 4-Stream Architecture & REGUH Validation
**Date:** 2026-03-27
**Project:** abapobjectscreation (UNESCO SAP Intelligence)
**Session focus:** Critical review of payment process mining model. Validate live data vs documentation. Fix companion and skill files.

---

## ❌ Error 1: OP documents incorrectly framed as "BCM bypass"
**What I did:** Initial companion text said "267K manual OP docs bypass F110, BCM, DMEE, and SWIFT entirely."
**Why it failed:** OP documents were assumed to be ad-hoc F-53 manual payments by users. No GL analysis was performed.
**Fix:** Joined BSAK (BLART=OP) to BKPF and extracted HKONT. All OP docs credit GL 2021xxx — field office sub-bank clearing accounts not in T012K. Confirmed REGUH→OP = 0 rows. This is a structural architecture, not bypass behavior.
**Lesson:** Never characterize document types by assumption. Always check GL account range and REGUH coverage before labeling a payment stream.
**Cost:** ~1 session of incorrect framing in companion v5/v6.

---

## ❌ Error 2: REGUH→Invoice link documented as "incomplete"
**What I did:** sap_payment_e2e SKILL.md Known Gap #2 stated "REGUH.VBLNR format doesn't match BSAK.AUGBL directly."
**Why it failed:** The assumption was written before running the actual join. When the join was executed: REGUH.VBLNR = BSAK.AUGBL returned **1,380,108 matched rows**.
**Fix:** Updated Known Gap #2 to reflect the validated link. OP docs return 0 rows because they are outside REGUH scope by design — not a data quality issue.
**Lesson:** Document links as INFERRED until a live query confirms them. Run the join before writing the gap note.
**Cost:** Incorrect gap note persisted from Session #020 to #027 (7 sessions).

---

## ❌ Error 3: BCM same-user count understated (1,557 → 3,394)
**What I did:** PMO H13 listed "1,557 same-user batches" as the dual-control gap count.
**Why it failed:** The original query only counted CRUSR=CHUSR for the IBC15 status. The correct scope is IBC15 + IBC05 (completed AND sent-to-bank) — both are post-approval states where dual control matters.
**Fix:** Re-queried BNK_BATCH_HEADER: CRUSR=CHUSR WHERE CUR_STS IN ('IBC15','IBC05') = 3,394 rows. Named breakdown added: UNES_AP_10=1,754, UNES_AP_EX=317 (exception countries), PAYROLL=276.
**Lesson:** When querying audit control gaps, define the exact status scope explicitly. Don't assume one status captures all relevant states.
**Cost:** Understated audit finding in PMO for ~1 session.

---

## ✅ Pattern 1: 4-Stream clearing architecture via GL range analysis
**What worked:** Extracting HKONT from BKPF for OP-cleared documents → 2021xxx GL range identifies field office sub-bank accounts. Cross-referencing with T012K confirms these accounts are NOT in house bank table.
**Why it works:** GL account ranges are stable structural metadata. 2021xxx = sub-bank clearing is UNESCO design — not arbitrary.
**Reuse:** Any time a BLART distribution shows unexpected volumes, always check GL account range before assuming intent. Pattern: `SELECT HKONT, COUNT(*) FROM BKPF WHERE BLART='OP' GROUP BY HKONT`.

---

## ✅ Pattern 2: REGUH link validation via direct join
**What worked:** `SELECT COUNT(*) FROM REGUH r JOIN bsak b ON r.VBLNR = b.AUGBL` as the definitive link test.
**Why it works:** REGUH.VBLNR stores the payment document number in the same format as BSAK.AUGBL. Direct equi-join works.
**Reuse:** Always validate cross-table links with a COUNT join before documenting as "incomplete." Run: VBLNR=AUGBL, LAUFD+LAUFI+BUKRS as secondary keys.

---

## ✅ Pattern 3: Named individual finding from CRUSR=CHUSR analysis
**What worked:** Adding `GROUP BY CRUSR` to the same-user batch query reveals individual operators who run BCM start-to-finish alone. F_DERAKHSHAN=259 PAYROLL batches.
**Why it works:** Segregation-of-duties gaps are most actionable when named — audit teams need individual user evidence, not just aggregate counts.
**Reuse:** In any BCM dual-control audit query, always add `GROUP BY CRUSR ORDER BY COUNT(*) DESC` to surface named risk.

---

## Promote to Central?
- [ ] Error 1 (GL range check before labeling payment stream) — qualifies for sap-intelligence skill note
- [ ] Pattern 3 (named individual in SoD queries) — reusable across any BCM/workflow dual-control analysis
- [x] Proposed in priority-actions.md: "Process Mining: GL range analysis before payment stream classification"
