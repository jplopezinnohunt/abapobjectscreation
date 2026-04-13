"""Idempotent extension to brain updates for INC-BUDGETRATE-EQG (Session #053).

Adds:
  - 4 additional CRITICAL/HIGH feedback rules to prevent the specific mistakes I made
  - Object-level annotations on each affected SAP object (15 enhancements + singleton class +
    KBLE/KBLEW/FMAVCT) so future agents see the gotchas inline when they query the brain
  - Cross-reference relationships (related_objects on every annotation)
"""
import json
import os
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
NOW = datetime.now().isoformat()


# 1. Additional preventive feedback rules (the meta-mistakes from Session #053)
new_rules = [
    {
        "id": "feedback_table_columns_never_drop",
        "rule": "When iterating on a wide table (markdown/excel/report), NEVER remove existing columns when adding new ones. Build the wider table by extending the previous column set in a single canonical script. If a column becomes irrelevant, mark it 'deprecated' but keep displaying it for one session before removing.",
        "why": "Session #053: I removed columns 'actual EUR cons USD-eq', 'actual nonEUR USD cons', 'non-EUR breakdown' when adding 'AVC budget USD' + 'AVC available USD'. User caught it twice (the 2nd time with 'PUTA MADRE / me haces perder el tiempo / me reago' — strong frustration signal). This is a costly mistake that breaks user trust.",
        "how_to_apply": "When updating a previously-shown table: (1) read the user's last shown column list, (2) the new table MUST contain >= those columns + the additions, (3) if you must restructure, show the column-mapping diff explicitly first and ask. Use a single source-of-truth script that builds incrementally so columns can never silently drop.",
        "severity": "HIGH",
        "created_session": 53,
        "source_file": "knowledge/session_retros/session_053_retro.md (§10)",
    },
    {
        "id": "feedback_aggregation_scope_explicit",
        "rule": "Every aggregation column in a report must explicitly state its filter scope in the header AND in any explanatory note. Allowed scopes: 'per-line' (REFBN+RFPOS), 'per-FONDS+FIPEX' (cover-group context), 'per-fund' (FONDS only), 'system-wide'. NEVER label an aggregation column 'total' without specifying 'total of WHAT'.",
        "why": "Session #053: I labeled fund+FIPEX consumption as 'pool EUR cons' and the user reasonably assumed it was per-FR consumption ($170K vs €4,400 line). Caused 3 round-trips of clarification. The right column name was 'fund+FIPEX EUR cons (USD-equiv, broader cover-group context)'.",
        "how_to_apply": "For any column derived from SUM/COUNT: name it with explicit scope marker. Examples: 'line cons EUR (this REFBN+RFPOS only)', 'pool USD cons (same FONDS+FIPEX, all FRs)'. Never use bare 'total' or 'cons' without scope qualifier.",
        "severity": "HIGH",
        "created_session": 53,
        "source_file": "knowledge/session_retros/session_053_retro.md (§10)",
    },
    {
        "id": "feedback_no_silent_except_pass",
        "rule": "In data-extraction scripts (RFC, SQL, file I/O) NEVER use 'except: pass' or 'except Exception: pass'. Silent failures cause downstream tables to show 0 / null without explanation, leading to wrong conclusions. ALWAYS at minimum: 'except Exception as e: print(f\"ERROR <context>: {e}\", file=sys.stderr)'. For RFC calls in particular, log the WHERE clause and parameters that failed.",
        "why": "Session #053: my background FMAVCT script used 'except: pass' to swallow per-fund RFC errors. Result: AVC budget column showed 0 for ALL 64 rows (the WHERE clause syntax differed from earlier successful runs). User caught it ('AVC budget 0 doesn't make sense'). I would have spotted it instantly if errors had been printed.",
        "how_to_apply": "grep -n 'except.*pass' on every extraction script before running. Replace with explicit error logging. For batch operations across N entities, log ERR + entity ID so you know which entity failed without re-running.",
        "severity": "CRITICAL",
        "created_session": 53,
        "source_file": "Zagentexecution/quality_checks/br_line_level_inconsistency_check.py",
    },
    {
        "id": "feedback_sample_raw_rows_before_aggregating",
        "rule": "Before computing any metric over a SAP table (FMIOI, FMIFIIT, FMAVCT, BSEG, etc.), sample 3-5 RAW rows for one specific key and inspect them. This catches: (a) sign convention surprises (FMIOI carryforward pairs), (b) duplicate-row patterns (FMAVCT RVERS), (c) rounding-plug rows ($0.01-0.02 ratio=1.0 in FMIOI), (d) trailing-minus number formats ('1234.56-'). Skipping this step caused 3 wrong interpretations in Session #053.",
        "why": "Session #053 mistakes: (1) interpreted $0.01 ratio=1.0 rows as cross-currency consumption (they were rounding plugs), (2) computed open balance as orig-consumed (sign convention wrong for carryforwards), (3) double-counted FMAVCT due to RVERS duplicates. All three would have been caught by 5 minutes of raw-row inspection upfront.",
        "how_to_apply": "First action when querying a new table or new key: SELECT * FROM <table> WHERE <key>=<sample> ORDER BY ... LIMIT 10. Print rows. Read them. THEN write the aggregation. Total cost: 30 seconds. Total savings: hours of wrong analysis.",
        "severity": "HIGH",
        "created_session": 53,
        "source_file": "knowledge/session_retros/session_053_retro.md (§10)",
    },
]

rp = "brain_v2/agent_rules/feedback_rules.json"
rules = json.load(open(rp))
existing_ids = {r["id"] for r in rules}
added = 0
for r in new_rules:
    if r["id"] not in existing_ids:
        rules.append(r)
        added += 1
with open(rp, "w", encoding="utf-8") as f:
    json.dump(rules, f, indent=2, ensure_ascii=False)
print(f"feedback_rules: +{added} new (now {len(rules)} total)")


# 2. Object-level annotations: drop critical findings INTO each affected object so
#    when someone queries brain_state.objects['<X>'].annotations they see the gotcha
ap = "brain_v2/annotations/annotations.json"
ann = json.load(open(ap))


def add_annotation(obj_name, tag, finding, impact=None, line=None, related=None):
    if obj_name not in ann:
        ann[obj_name] = {"annotations": []}
    if "annotations" not in ann[obj_name]:
        ann[obj_name]["annotations"] = []
    sig = (tag, finding[:50])
    if any((a.get("tag"), (a.get("finding") or "")[:50]) == sig for a in ann[obj_name]["annotations"]):
        return False
    record = {
        "tag": tag,
        "finding": finding,
        "timestamp": NOW,
        "session": "#053",
        "incident": "INC-BUDGETRATE-EQG",
    }
    if impact:
        record["impact"] = impact
    if line is not None:
        record["line"] = line
    if related:
        record["related"] = related
    ann[obj_name]["annotations"].append(record)
    return True


added_ann = 0

# Singleton class
added_ann += int(add_annotation(
    "YCL_FM_BR_EXCHANGE_RATE_BL",
    "CRITICAL",
    "Constructor (CM00A line 8) hardcodes mr_waers = ['EUR']. This is the gate that blocks cross-currency consumption from getting BR treatment in Camp B enhancements. mr_waers2 (Staff variant) includes both EUR + USD but is dead code (only called from IF 1=2 branches). The complete cross-currency method convert_to_currency_2 (CM002) exists, is production-transported, but never runs.",
    impact="Every USD consumption posting against an EUR-loaded BR fund silently bypasses BR conversion and persists at identity, drifting the AVC pool fund-by-fund until FMAVC005 fires.",
    line=8,
    related=["ZFIX_EXCHANGERATE_AVC", "ZFIX_EXCHANGERATE_FI", "ZFIX_EXCHANGERATE_NEW_ITEM", "ZFIX_EXCHANGERATE_KBLEW", "ZFIX_EXCHANGERATE_PAYCOMMIT"],
))

# Camp A enhancements (FR-currency anchored)
for obj in ["ZFIX_EXCHANGERATE_CHECK_CONS", "ZFIX_EF_FUND_RESERVATION", "ZFIX_EXCHANGERATE_FUNDBLOCK"]:
    added_ann += int(add_annotation(
        obj,
        "CAMP_A_FR_ANCHORED",
        f"{obj} is Camp A: gate input iv_waers reads the FR's own currency (kblk-waers/kbld-waers). Always passes for EUR FRs regardless of consumption posting currency. SAFE for the cross-currency bug — it does not contribute to drift. CHECK_CONS specifically uses SAVE/RESTORE pattern (Enh1 saves m_t_addref, recalcs at BR; Enh2 restores) — nothing persisted, only EF check sees BR.",
        impact="Reading these enhancements alone gives a misleading picture that BR works correctly. The bug is in Camp B (NEW_ITEM/AVC/KBLEW/FI/PAYCOMMIT) which use posting-currency for the gate.",
        related=["YCL_FM_BR_EXCHANGE_RATE_BL", "INC-BUDGETRATE-EQG"],
    ))

# Camp B enhancements (posting-currency anchored — the bug surface)
for obj in ["ZFIX_EXCHANGERATE_AVC", "ZFIX_EXCHANGERATE_FI", "ZFIX_EXCHANGERATE_NEW_ITEM", "ZFIX_EXCHANGERATE_KBLEW", "ZFIX_EXCHANGERATE_PAYCOMMIT"]:
    added_ann += int(add_annotation(
        obj,
        "CAMP_B_POSTING_ANCHORED",
        f"{obj} is Camp B: gate input iv_waers reads the per-row posting currency (twaer/<*>-waers). FAILS silently when consumption is non-EUR. Standard SAP then persists the row at identity (FKBTR=TRBTR for USD) or at standard M-rate. This is the silent drift-injector.",
        impact="Each non-EUR consumption posting that hits this enhancement contributes drift to the AVC pool. Across 458 funds in P01, lifetime drift volume is ~$375M with ~$35.7M estimated drift exposure.",
        related=["YCL_FM_BR_EXCHANGE_RATE_BL", "INC-BUDGETRATE-EQG", "FMAVCT", "FMIOI", "FMIFIIT"],
    ))

# Camp C — filters (only BR_REVALUATION on the active path, BR_AVC_EXCLUSIONS dead code)
added_ann += int(add_annotation(
    "ZFIX_BR_REVALUATION",
    "CAMP_C_FILTER",
    "Camp C: filter-only enhancement, no BR conversion. Fires only on FMN4N (PO commitment recalc). DELETES rows from t_fmoi/u_t_fmioi_buf where fikrs<>'UNES' OR twaer<>'EUR' OR bus_area<>'GEF' OR ftype not in mr_fund_type. Effect: revaluation excludes USD rows on EUR-loaded funds → drift cleanup tools cannot fix the cross-currency gap.",
    impact="If you try to run FMN4N to clean up drift, this enhancement removes the very rows that need cleaning. Need to either temporarily deactivate this enhancement or extend H39 to handle USD rows on EUR-loaded funds.",
    related=["INC-BUDGETRATE-EQG"],
))

added_ann += int(add_annotation(
    "ZFIX_BR_REVAL_RESFUND",
    "CAMP_C_FILTER",
    "Camp C: filter-only. Fires on FMZZ (Reservation Fund Revaluation report). Sets testlauf='X' (TEST RUN ONLY — never persists). Filters non-EUR rows out. Inert in production except for reporting purposes.",
    related=["INC-BUDGETRATE-EQG"],
))

# Dead-code BAdI
added_ann += int(add_annotation(
    "ZFIX_BR_AVC_EXCLUSIONS",
    "DEAD_CODE_IN_PROD",
    "BAdI implementation of FMAVC_ENTRY_FILTER. Created 2025-05-14 in D01 (transports D01K9B0D4Z + D01K9B0D50). Deactivated next day 2025-05-15 (transports D01K9B0D54 + D01K9B0D55). Exists only in D01 + V01 — absent from TS1, TS3, P01. Logic only in BUDGET_FILTER (wrong method — should be POSTING_FILTER for consumption); whitelist hardcoded to MIRO + F110. POSTING_FILTER is empty stub. NEVER affected production AVC behavior. PMO H38 to delete from D01+V01.",
    impact="Do NOT cite this BAdI as evidence that 'MIRO/F110 are silenced in production'. They are not. AVC fires equally for all tcodes in P01.",
    related=["FMAVC_ENTRY_FILTER", "IF_EX_FMAVC_ENTRY_FILTER", "INC-BUDGETRATE-EQG", "PMO_H38"],
))

# Auxiliary
for obj in ["ZFIX_FM_BR_POST_FROM_PY_AUTO", "ZFIX_BR_BAPI_EMPLOYEE_POST"]:
    added_ann += int(add_annotation(
        obj,
        "CAMP_D_AUXILIARY",
        f"{obj} is Camp D: payroll/BAPI bridge. Out of scope for the cross-currency bug. Handles HRPAY runid bookkeeping and BAPI account data setting respectively.",
        related=["YCL_FM_BR_EXCHANGE_RATE_BL"],
    ))

# Tables
added_ann += int(add_annotation(
    "FMAVCT",
    "QUERY_PATTERN",
    "Wide table (>512 bytes/row). RFC_READ_TABLE FIELDS=[] returns DATA_BUFFER_EXCEEDED. Workaround: pass narrow FIELDS list (max 12 cols) AND split WHERE conditions into multiple OPTIONS entries (single complex WHERE rejected with OPTION_NOT_VALID). Dedup result rows by full-row signature (RVERS/RPMAX duplicates double-count if summed naively). For UNESCO ledger 9H 2026 carryforward allotment: ALLOCTYPE_9='KBFC'. HSL01-HSL16 = per-period local USD; HSLVT = yearly total. Available = SUM(HSL*) - SUM(open FMIOI commitments + FMIFIIT actuals on same FONDS+FUNDSCTR+CMMTITEM).",
    impact="If you don't dedup or you sum HSLVT alongside HSL01-16, you double-count budget. Vonthron's case: $12,897.80 was the correct dedup'd value; without dedup it became $25,795.60 (2x). That misled my analysis briefly.",
    related=["FMIOI", "FMIFIIT", "INC-BUDGETRATE-EQG"],
))

added_ann += int(add_annotation(
    "FMIOI",
    "WRTTP_81_CARRYFORWARD_PATTERN",
    "Earmarked-fund commitment rows: original creation (positive), period-specific consumption reductions (negative), period-016 year-end reversal (positive equal to remaining), period-000 carryforward-IN to next year. Naive sign-sum across all years does NOT equal 'open balance'. For 'open' filter by current GJAHR + signed sum. For 'lifetime consumed' use KBLE/KBLEW NOT FMIOI. Rows with ratio=1.0 + amount $0.01-0.02 are SAP rounding plugs, NOT cross-currency consumption signatures.",
    impact="3 wrong interpretations in Session #053 came from skipping raw-row inspection on FMIOI. Always sample 3 raw WRTTP=81 rows for any FR before computing per-line metrics.",
    related=["KBLE", "KBLEW", "INC-BUDGETRATE-EQG"],
))

added_ann += int(add_annotation(
    "KBLE",
    "CLUSTER_TABLE_RFC_PATTERN",
    "Cluster table — RFC_READ_TABLE returns TABLE_WITHOUT_DATA. Use RFC-enabled wrapper FM '/SAPPSPRO/PD_GM_FMR2_READ_KBLE' with parameter I_BELNR=<FR doc number>. Returns T_KBLE (consumption events with RBELNR/RBUZEI = consumer FI doc/line — the canonical FR↔FI traceability link without needing BSEG.KBLNR access) AND T_KBLEW (per-currency split CURTP=00 transaction currency, CURTP=10 local USD).",
    impact="Without this wrapper FM, FR consumption history is unreachable via standard RFC. Use it whenever you need to know which FI documents consumed a specific FR line.",
    related=["KBLEW", "/SAPPSPRO/PD_GM_FMR2_READ_KBLE", "INC-BUDGETRATE-EQG"],
))

added_ann += int(add_annotation(
    "KBLEW",
    "CLUSTER_TABLE_RFC_PATTERN",
    "Cluster table. Same access pattern as KBLE — use /SAPPSPRO/PD_GM_FMR2_READ_KBLE wrapper which returns T_KBLEW alongside T_KBLE. Each KBLE consumption event produces 2 KBLEW rows: POSNR=01 CURTP=00 (transaction currency, EUR for EUR FR), POSNR=02 CURTP=10 (local currency = USD = FM-area). The CURTP=10 USD value is the BR-applied USD-equivalent of the consumption (if BR fired correctly).",
    impact="To find the per-line BR-applied consumption USD value, sum WRBTR where CURTP=10 grouped by REFBN+RFPOS.",
    related=["KBLE", "/SAPPSPRO/PD_GM_FMR2_READ_KBLE", "INC-BUDGETRATE-EQG"],
))

# CL_FM_EF_POSITION — the recommended fix location
added_ann += int(add_annotation(
    "CL_FM_EF_POSITION",
    "FIX_LOCATION_H39",
    "Standard SAP class. Method CHECK_CONSUMPTION is the natural hook for the preventive validation (PMO H39): block any consumption posting where FR header WAERS=EUR + GSBER=GEF + fund_type ∈ mr_fund_type AND consumption_doc-WAERS ≠ EUR with MESSAGE 'Z_BR_001' TYPE 'E'. ZFIX_EXCHANGERATE_CHECK_CONS already enhances this method — H39 adds a sibling enhancement that runs BEFORE the recalc and rejects cross-currency upfront.",
    related=["ZFIX_EXCHANGERATE_CHECK_CONS", "INC-BUDGETRATE-EQG", "PMO_H39"],
))

with open(ap, "w", encoding="utf-8") as f:
    json.dump(ann, f, indent=2, ensure_ascii=False)
print(f"annotations: +{added_ann} new annotations across {len({k for k in ann if any(a.get('session')=='#053' for a in ann[k]['annotations'])})} objects")

print("\nDone. Now rebuild brain_state.json with: python brain_v2/rebuild_all.py")
