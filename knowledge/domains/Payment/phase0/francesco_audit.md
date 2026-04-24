# Francesco Audit — FP_SPEZZANO DMEE transport history

**Phase 0 deliverable** · Session #62 · 2026-04-24 · Evidence tier: TIER_1 (parsed from `Zagentexecution/mcp-backend-server-python/cts_batch_*.json`)

## Context

User statement: *"Francesco no sabía del proceso"* (structured address change). Audit goal: verify what FP_SPEZZANO touched historically in DMEE and classify each transport as BLOCK / ASSIST / IRRELEVANT for this project.

## Verified facts

**FP_SPEZZANO = Francesco Spezzano**. Confirmed from CTS `summary.top_20_owners` field in `cts_batch_2024.json` + parsing all 10 year files.

| Metric | Value |
|---|---|
| Total transports by FP_SPEZZANO, 2017-2026 | **70** |
| DMEE-touching transports | **5** (all 2025 Q1) |
| Non-DMEE transports | 65 |
| Target trees touched | `/CGI_XML_CT_UNESCO`, `/CGI_XML_CT_UNESCO_1` |
| SEPA / CITI tree touches | **0** |
| All DMEE transports status | Released (`R`) |
| All DMEE transports type | Workbench |

## The 5 DMEE transports — detail

All have **empty description** field. Classification pending node-level inspection (requires pyrfc or manual DMEE tree version diff).

| Date | TRKORR | Target Tree | Obj count | Preliminary classification |
|---|---|---|---|---|
| 2025-03-20 | D01K9B0CZ0 | `/CGI_XML_CT_UNESCO` | 3 | PENDING — need node diff |
| 2025-03-07 | D01K9B0CWS | `/CGI_XML_CT_UNESCO_1` | 2 | PENDING |
| 2025-02-21 | D01K9B0CUS | `/CGI_XML_CT_UNESCO_1` | 1 | PENDING |
| 2025-02-21 | D01K9B0CUT | `/CGI_XML_CT_UNESCO_1` | 2 | PENDING |
| 2025-02-20 | D01K9B0CTP | `/CGI_XML_CT_UNESCO_1` | 3 | PENDING |

## Interpretation [INFERRED — needs validation]

- Francesco's 5 transports are on the **CGI trees only**, never touched SEPA or CITI
- Marlies reported CGI Dbtr is **already structured** (per her Excel analysis). If Francesco's transports are Dbtr-related, they may have contributed to that structured state.
- Small obj_count (1-3 per transport) = narrow changes, not full-tree rework
- Clustered in 4 weeks (Feb 20 → Mar 20) = likely a focused mini-project
- **User directive**: "Francesco no sabía del proceso" — we must not assume his work covers structured address broadly. It's likely tactical/reactive.

## BLOCK/ASSIST/IRRELEVANT classification — procedure (to execute in Phase 0 continued)

For each of the 5 transports, need to:
1. Fetch the transport's E071 object keys (pyrfc `RFC_READ_TABLE E071 WHERE TRKORR=X`)
2. Fetch the DMEE tree node IDs in the transport (if any are PAYM tree entries)
3. Compare node IDs against the `PstlAdr` subtree node IDs in `/CGI_XML_CT_UNESCO` and `/CGI_XML_CT_UNESCO_1`
4. Classify:
   - **BLOCK**: touches any PstlAdr node in Dbtr/Cdtr/CdtrAgt/UltmtCdtr hierarchy
   - **ASSIST**: touches structure supporting address work (FPAYHX mapping, char filter nodes on address, condition suppressing AdrLine)
   - **IRRELEVANT**: touches unrelated parts of the tree (Purp, payment amount tags, reference tags)

## What to do about Francesco

Per user directive (2026-04-24): audit as context, don't assume pattern.

- **Before any CGI tree edit in Phase 2**: alignment call with Francesco to disclose the 5 transports' scope — written agreement that our structured-address changes don't overwrite his WIP
- If BLOCK: coordinate merge path; schedule a joint review
- If ASSIST: treat as prerequisite; evaluate if his changes help or hinder
- If IRRELEVANT: no coordination needed; log in the audit

## Data source

- `Zagentexecution/mcp-backend-server-python/cts_batch_2017.json` through `cts_batch_2026.json`
- Field names: `trkorr`, `owner`, `date`, `status`, `type`, `description`, `objects[{pgmid,obj_type,obj_name}]`
- Parser: see Phase 0 implementation commit

## Corrections to prior agent output

- Earlier Explore agent reported 5 transports (correct count, correct author ID)
- Earlier Explore agent reported D01K9B0CZ0 2025-03-20 as most recent (correct)
- Earlier Explore agent missed the 4 other dates and the 2025-02-21 duplicate-date pair
- Prior user statement "Francesco no sabía" and Explore agent "Francesco authored" both need evidence-based reconciliation. This audit shows Francesco DID touch CGI DMEE trees but we don't know WHAT yet. Not inconsistent with "didn't know about the CBPR+ structured-address initiative specifically" — his changes may have been something else entirely.
