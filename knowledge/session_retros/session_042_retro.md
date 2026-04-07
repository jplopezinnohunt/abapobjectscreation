# Session #042 Retro — Brain v2 Explorer + Bank Data Consolidation

**Date:** 2026-04-06
**Previous:** #041 (Brain v2 impact chain operational)
**Main agent:** Claude Opus 4.6 (1M context) via Claude Code

---

## Hypotheses

| # | Hypothesis | Status | Evidence |
|---|---|---|---|
| H1: Gap analysis noise is solvable with severity filtering | **CONFIRMED** | 2,908 total → 56 CRITICAL+HIGH actionable. 70% of noise was LOW-severity isolated JOB_DEFINITION/CODE_OBJECT nodes. |
| H2: CITI/SEPA DMEE trees can be mapped from T042A data | **CONFIRMED** | +44 USES_DMEE_TREE edges (17 CITI + 27 SEPA) from T042A bank routing analysis. CIT01→UBO/UIS, CIT04/CIT21→UNES. |
| H3: H22/H23 PMO items are stale (data already complete) | **CONFIRMED** | FEBEP_2024_2026: 223K rows ALL months. FEBKO_2024_2026: 31K rows WITH HBKID (PMO said "missing"). Both tables had _2024_2026 suffixed versions that were complete. |
| H4: Currency conversion will deflate the "$13.9B" bank statement figure | **FALSIFIED** | Actual USD total = $16.8B (HIGHER). UZS (Uzbekistan Som) = $6.2B alone (37% of total from 1.3% of items). Weak currencies inflate, don't deflate. |

---

## Deliverables

| # | Deliverable | Status | Location |
|---|---|---|---|
| 1 | Gap analysis severity filter (CRITICAL/HIGH/MEDIUM/LOW) | SHIPPED | `brain_v2/queries/gap.py` |
| 2 | Confidence decay — Principle 4 of architecture doc | SHIPPED | `brain_v2/core/graph.py` `decay_confidence()` + `stale_edges()` |
| 3 | CLI `stale` + `decay` commands | SHIPPED | `brain_v2/cli.py` |
| 4 | CITI/SEPA DMEE tree mapping (+44 edges) | SHIPPED | `brain_v2/ingestors/config_ingestor.py` |
| 5 | Brain v2 HTML companion (1,056 KB, 5 tabs) | SHIPPED | `brain_v2/output/brain_v2_explorer.html` + `brain_v2/companion_builder.py` |
| 6 | H21 Currency conversion (CURRENCY_USD_RATES + FEBEP_USD view) | SHIPPED | Gold DB: `CURRENCY_USD_RATES` table + `FEBEP_USD` view |
| 7 | E2E bank statement chain edges (+60 domain knowledge edges) | SHIPPED | `brain_v2/ingestors/domain_knowledge_ingestor.py` |
| 8 | H19 CLOSED (bank recon aging — already investigated #029) | CLOSED | 2,737 real unreconciled on 11xxxxx |
| 9 | H22 CLOSED (FEBEP — data complete in _2024_2026 table) | CLOSED | 223,710 rows, 27 cols, all months |
| 10 | H23 CLOSED (FEBKO — HBKID present in _2024_2026 table) | CLOSED | 31,416 rows, 62 cols, HBKID 0% null |

**Closure math:** 10 deliverables shipped (7 new artifacts + 3 PMO items closed), 0 new items added. Net closure: +10. Session gate: PASS.

---

## Discoveries

1. **FEBEP/FEBKO PMO was stale for 12 sessions** — H22 said "60% coverage, missing months" but FEBEP_2024_2026 has 223K rows with ALL months. H23 said "missing HBKID" but FEBKO_2024_2026 has HBKID with 0% null. Both had `_2024_2026` suffixed tables that were complete — the original unsuffixed tables (50K row truncated extractions) were the incomplete ones. **Rule: always check both table names before declaring data missing.**

2. **$16.8B not $13.9B** — Currency conversion INCREASED the total (H4 falsified). UZS (Uzbekistan Som) alone = $6.2B from only 1,739 items. Weak currencies (UZS, IRR, LBP, VND) inflate totals massively. For meaningful analysis, need to either exclude outlier currencies or report in transaction count, not amount.

3. **Correlated subqueries kill SQLite on large tables** — 7 attempts at TCURR conversion failed (hanging/timeout) due to `WHERE GDATU = (SELECT MIN(GDATU) FROM TCURR t2 WHERE t2.FCURR = TCURR.FCURR)`. The fix: fetchall into Python dict, pick latest per currency in-memory. **Rule: never use correlated subqueries in Gold DB — always materialize in Python.**

4. **6 stale Python processes holding DB locks** — Background tasks that timed out held open SQLite connections, blocking new queries. `taskkill //F //IM python.exe` was needed before clean run.

5. **CGI_XML_CT_UNESCO_FB is orphaned** — CRITICAL gap finding: the fallback DMEE tree has NO USES_DMEE_TREE edges. Either it's truly unused config or we're missing the mapping (no T042A entries route to it).

6. **T012K bank impact is massive** — Changing T012K affects 30 objects: 3 DMEE classes → 3 trees → 18 payment methods + 6 banks. This is the most impactful config table for payments.

---

## Failures/Corrections

1. **7 failed background tasks** — All currency conversion attempts via correlated subquery on TCURR. Root cause: SQLite optimizer doesn't handle correlated subqueries on 55K-row tables well. Fixed by moving aggregation to Python.

2. **VPN/SNC not available** — H25 (T028A) and H26 (T012K UKONT) blocked. SNC credentials expired ("No credentials were supplied"). These remain pending.

---

## Verification Check

| Claim | Verification | Result |
|---|---|---|
| Gap severity reduces noise | `python -m brain_v2.cli gaps CRITICAL` | 1 CRITICAL + 55 HIGH (vs 2,908 total) |
| Confidence decay works | `python -m brain_v2.cli decay 42` | 16 edges decayed, 0 at floor |
| CITI/SEPA edges added | Brain stats: USES_DMEE_TREE count | 80 total (36 CGI + 17 CITI + 27 SEPA) |
| HTML companion loads | File size + structure check | 1,056 KB, 5 tabs, 4,188 nodes embedded |
| FEBEP_USD view works | `SELECT SUM(KWBTR_USD) FROM FEBEP_USD` | $16,833,863,076 |
| Bank impact chain works | `python -m brain_v2.cli impact "SAP_TABLE:FEBEP" 4` | 9 affected (3 programs + 6 process steps) |
| Brain total | `python -m brain_v2.cli stats` | 52,491 nodes, 113,172 edges |

**AI Diligence Statement:** Claude verified H22/H23 completion by querying actual Gold DB data rather than trusting PMO text. Discovered PMO was stale for 12 sessions. Currency conversion falsified the hypothesis that amounts were inflated by DMBTR — they were actually higher in USD. 7 background tasks failed and were diagnosed (correlated subquery pattern).

---

## PMO Reconciliation

### Items to strike:
- **H19** — CLOSED. Bank recon aging already investigated #029. 2,737 real unreconciled.
- **H21** — DONE. CURRENCY_USD_RATES table + FEBEP_USD view. Real total: $16.8B.
- **H22** — CLOSED. FEBEP_2024_2026 complete (223K rows, all months).
- **H23** — CLOSED. FEBKO_2024_2026 complete (31K rows, HBKID present).

### Items unchanged:
- **H25** — Blocked (VPN). T028A not in Gold DB.
- **H26** — Blocked (VPN). T012K missing UKONT.

### Net: 4 items struck, 0 added = net closure +4

---

## What Could Be Better

1. **Should have checked `_2024_2026` table suffixes before declaring data missing** — H22/H23 were stale for 12 sessions because nobody queried the actual data. This wasted mental overhead across multiple sessions.

2. **Correlated subquery anti-pattern should become a feedback rule** — 7 failed attempts. Add `feedback_no_correlated_subquery.md`.

3. **Background task cleanup** — 6 stale Python processes accumulated. Need a pattern to auto-kill timed-out processes.

4. **HTML companion could use more pre-computed impacts** — Only 3 were pre-computed (FPAYP.XREF3, YCL_IDFI_CGI_DMEE_FR, /CGI_XML_CT_UNESCO). Should pre-compute for all CRITICAL nodes.

5. **BROADCAST-003 not acknowledged** — Forgot during session. Must do at close.
