"""ALGORITHM A15 — BUDGET-RATE SUBJECT GRAPH.

WHAT IT ANSWERS
    "How do the pieces of this mechanism relate?" — as a graph the model can traverse,
    rather than as paragraphs a reader has to hold in their head.

WHY IT EXISTS
    The budget rate was learned in fragments across a session: a rate type, a perimeter, a
    set of moments, two mechanisms, a control report, an impact figure, several
    corrections. Each landed correctly in its own store — the enhancement registry, claims,
    the backlog. What did not exist was the RELATION between them: that the perimeter is
    applied AT the moments, that the moments are WHERE the rate type is used, that the
    control report DEFINES the impact the algorithm measures, that the personnel side is a
    SIBLING mechanism sharing only the rate.

    A conclusion with no edges is prose with a JSON wrapper. The edges are what let a later
    question — "what does the availability check depend on?" — be answered mechanically.

WHAT IT DOES NOT DO
    It does not restate the knowledge. Every node points at where the content lives, and
    the graph carries only the RELATION and the evidence for it. One source of truth per
    fact; this is the index over them.

USAGE
    python brain_v2/build_br_graph.py
"""

import collections
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, "methods"))
from algorithm_memory import remember  # noqa: E402

ART = os.path.join(HERE, "budget_rate_enhancements.json")
CLAIMS = os.path.join(HERE, "claims", "claims.json")
OUT = os.path.join(HERE, "budget_rate_graph.json")

# The subjects. Each one names where its content lives — the graph never duplicates it.
NODES = [
 {"id": "MECHANISM_NON_PERSONNEL", "kind": "MECHANISM",
  "what": "the budget rate for non-personnel cost: enhancements plus the control report",
  "content_in": "budget_rate_enhancements.json"},
 {"id": "MECHANISM_PERSONNEL", "kind": "MECHANISM",
  "what": "the budget rate for staff cost, computed in the PAYROLL ENGINE — in the "
          "calculation schema, in its codifications",
  "content_in": "budget_rate_enhancements.json ._THE_TWO_MECHANISMS.personnel",
  "status": "MECHANISM CLOSED s098 — engine, carrier, gate and posting design are all described. The AMOUNT is the one thing still not measured"},
 {"id": "RATE_EURX", "kind": "CONFIGURATION",
  "what": "exchange rate type EURX, 60 entries; USD/EUR = 1.09529 from 2024-01-01",
  "content_in": "budget_rate_enhancements.json .the_rate_type"},
 {"id": "RATE_M_UNORE", "kind": "CONFIGURATION",
  "what": "rate type M — the UN operational rate, the moving baseline",
  "content_in": "budget_rate_enhancements.json .the_rate_type._what_1_09529_actually_is"},
 {"id": "PERIMETER_8_RANGES", "kind": "RULE",
  "what": "eight conditions in YCL_FM_BR_EXCHANGE_RATE_BL, each SKIPPED when its parameter "
          "arrives empty",
  "content_in": "budget_rate_enhancements.json .the_exact_perimeter"},
 {"id": "PERIMETER_FEATURE_YYCDR", "kind": "RULE",
  "what": "the personnel gate: HR feature YYCDR evaluated per employee against PA0001",
  "content_in": "budget_rate_enhancements.json ._THE_TWO_MECHANISMS.personnel.the_gate"},
 {"id": "TWELVE_MOMENTS", "kind": "BEHAVIOUR",
  "what": "the twelve points in the FM lifecycle where the rate is applied",
  "content_in": "budget_rate_enhancements.json .the_twelve_moments"},
 {"id": "MOMENT_AVAILABILITY_CHECK", "kind": "BEHAVIOUR",
  "what": "the rate is applied INSIDE FM_FUNDS_CHECK, before availability is decided",
  "content_in": "budget_rate_enhancements.json .the_twelve_moments.moments[1]"},
 {"id": "CONTROL_REPORT", "kind": "CONTROL",
  "what": "transaction YFM_FI_BR_COMP running YFM_FI_COMPARE_INCLUDING_BR; "
          "FINAL_DIFF = FKBTR - DMBTR - ZZAMOUNTBRDIFF",
  "content_in": "budget_rate_enhancements.json .the_control_report"},
 {"id": "FOUR_BASELINES", "kind": "RULE",
  "what": "the four routes GET_BR_IMPACT selects between to value the standard side",
  "content_in": "budget_rate_enhancements.json .the_control_report.the_four_baselines_in_GET_BR_IMPACT"},
 {"id": "IMPACT_FIGURE", "kind": "MEASUREMENT",
  "what": "-2,365,688.44 USD over 11,179 financial-posting lines",
  "content_in": "brain_v2/br_impact.json"},
 {"id": "ALGORITHM_A14", "kind": "ALGORITHM",
  "what": "br_impact.py — replicates the organisation's own baselines",
  "content_in": "process_mining/br_impact.py"},
 {"id": "COMMITMENTS_NOT_COMPARABLE", "kind": "CONSTRAINT",
  "what": "SAP recalculates commitments, so no impact can be differenced on that side",
  "content_in": "budget_rate_enhancements.json .the_impact._SCOPE_CORRECTION_s098"},
 {"id": "TRACE_TABLES", "kind": "DATA",
  "what": "YTFM_BR_* — the control tables; the actuals one holds 12,852 rows and the "
          "position one holds zero",
  "content_in": "budget_rate_enhancements.json .measured_effect"},
 {"id": "DEFECT_MR_WAERS", "kind": "DEFECT",
  "what": "the main gate accepts EUR only while the staff gate accepting USD is unreachable",
  "content_in": "claims 412 and the incident record"},
 {"id": "DEFECT_MR_HKONT", "kind": "DEFECT",
  "what": "MR_HKONT declared and never populated, so the staff gate fails whenever a GL "
          "account is passed",
  "content_in": "AN-BR-HKONT-EMPTY-RANGE"},
 {"id": "DEAD_CODE_PBC_CONVERSION", "kind": "DEFECT",
  "what": "the personnel two-step conversion is fully implemented behind IF 1 = 2",
  "content_in": "budget_rate_enhancements.json ._THE_TWO_MECHANISMS.personnel.the_conversion"},
 # --- the PAYROLL set. Added s098 so the staff mechanism stops standing alone: it is
 # --- computed by an engine, carried by wage types, and lands through an account
 # --- determination that is NOT the FI one. Each of those is a subject in its own right.
 {"id": "PAYROLL_ENGINE", "kind": "MECHANISM",
  "what": "the payroll engine as configured here: schemas, rules, wage types and features — "
          "a layer that is neither ABAP nor data, and that no code or table search reaches",
  "content_in": "brain_v2/payroll_discovery.json"},
 {"id": "ALGORITHM_A16", "kind": "ALGORITHM",
  "what": "payroll_discovery.py — the end-to-end payroll discovery, in seven parts, built on "
          "the premise that PAYROLL LOGIC IS NAMED AFTER WHAT IT PRODUCES",
  "content_in": "process_mining/payroll_discovery.py"},
 {"id": "WAGE_TYPES_CONSTANT_DOLLAR", "kind": "DATA",
  "what": "the 72 'Constant Dollar' wage types — the staff budget rate's carrier, identically "
          "configured in T512W, so one mechanism rather than seventy-two decisions",
  "content_in": "budget_rate_enhancements.json ._THE_TWO_MECHANISMS.personnel"},
 {"id": "TWIN_POSTING", "kind": "BEHAVIOUR",
  "what": "each Constant Dollar wage type posts to its base's OWN symbolic account with the "
          "opposite sign — 58 of 58 configured pairs — so the two net on the account",
  "content_in": "budget_rate_enhancements.json ._THE_TWO_MECHANISMS.personnel.the_real_mechanism.how_it_posts"},
 {"id": "SYMBOLIC_ACCOUNT", "kind": "CONFIGURATION",
  "what": "the payroll symbolic account, CHAR(4) — SPAL, BSAL, HOUS, PADJ. The thing a wage "
          "type posts to, and NOT the same key as the FI transaction key",
  "content_in": "budget_rate_enhancements.json ._THE_TWO_MECHANISMS.personnel.the_real_mechanism.the_account_determination"},
 {"id": "FIELD_WIDTH_TRAP", "kind": "CONSTRAINT",
  "what": "T030-KTOSL is CHAR(3) and a payroll symbolic account is CHAR(4). The FI account "
          "determination CANNOT hold one, so three extractions chasing it were impossible "
          "by construction",
  "content_in": "brain_v2/methods/algorithm_memory.json ._field_width"},
 {"id": "RESOLVED_POSTING", "kind": "MEASUREMENT",
  "what": "read from PPDIT rather than from configuration: a 3-character FI transaction key "
          "fans out to several GL accounts, while every GL account belongs to exactly one "
          "key — so the account is decided BEYOND the key, by the wage type",
  "content_in": "brain_v2/payroll_discovery.json .resolved_posting"},
 {"id": "PAYROLL_TO_FM_BRIDGE", "kind": "CONFIGURATION",
  "what": "T9POST — a CUSTOM table mapping symbolic account x employee grouping to fund "
          "centre and fund. Payroll reaches FM through a customer table, not a standard one",
  "content_in": "budget_rate_enhancements.json ._THE_TWO_MECHANISMS.personnel.the_real_mechanism.the_payroll_to_fm_bridge"},
 {"id": "ENHANCEMENT_POSTING_ACCOUNTS", "kind": "DEFECT",
  "what": "ZHR_POSTING_ACCOUNTS_RETRO — a custom enhancement named after the account "
          "determination itself, hooked on RPCIPE00_OLD, the retro posting program",
  "content_in": "brain_v2/payroll_discovery.json .posting.enhancements_on_the_posting_path"},
 {"id": "MASTER_DATA_BY_HAND", "kind": "BEHAVIOUR",
  "what": "which payroll master data a human edits and which arrives by a channel — the "
          "operating risk and the automation opportunity sit in the same place",
  "content_in": "brain_v2/payroll_discovery.json .master_data"},
 {"id": "ALGORITHM_A17", "kind": "ALGORITHM",
  "what": "change_governance.py — the route by which a change reaches production, judged "
          "against the population of maintainers rather than a policy document",
  "content_in": "process_mining/change_governance.py"},
]

# The edges. This is the part that did not exist before.
EDGES = [
 ("MECHANISM_NON_PERSONNEL", "USES", "RATE_EURX",
  "CONVERT_TO_CURRENCY reads rate type EURX"),
 ("MECHANISM_PERSONNEL", "USES", "RATE_EURX",
  "the designed two-step conversion ends on EURX — the one thing the two mechanisms share"),
 ("MECHANISM_NON_PERSONNEL", "GATED_BY", "PERIMETER_8_RANGES", "CHECK_CONDITIONS"),
 ("MECHANISM_PERSONNEL", "GATED_BY", "PERIMETER_FEATURE_YYCDR",
  "CL_HRPA_FEATURE=>GET_VALUE, per employee, per date"),
 ("PERIMETER_8_RANGES", "APPLIED_AT", "TWELVE_MOMENTS",
  "each moment supplies its own subset, and an unsupplied condition is skipped"),
 ("TWELVE_MOMENTS", "INCLUDES", "MOMENT_AVAILABILITY_CHECK", "moment 2 of 12"),
 ("MOMENT_AVAILABILITY_CHECK", "CHANGES_WHAT_IS_ALLOWED", "MECHANISM_NON_PERSONNEL",
  "the rate is applied before availability is decided, so it is not a reporting adjustment"),
 ("RATE_EURX", "IS_A_FROZEN_SNAPSHOT_OF", "RATE_M_UNORE",
  "1.09529 is the operational rate in force at the start of the biennium"),
 ("RATE_EURX", "COINCIDES_WITH", "RATE_M_UNORE",
  "twice in 2024 — 15 January and 15 August — which is why the 2024 impact is exactly zero"),
 ("CONTROL_REPORT", "DEFINES", "IMPACT_FIGURE",
  "FINAL_DIFF nets the budget-rate part out; the residual is the real break"),
 ("CONTROL_REPORT", "SPECIFIES", "FOUR_BASELINES", "GET_BR_IMPACT chooses by value type"),
 ("ALGORITHM_A14", "REPLICATES", "FOUR_BASELINES",
  "rather than reconstructing a definition the organisation already has"),
 ("ALGORITHM_A14", "PRODUCES", "IMPACT_FIGURE", "brain_v2/br_impact.json"),
 ("COMMITMENTS_NOT_COMPARABLE", "BOUNDS", "IMPACT_FIGURE",
  "the figure covers financial postings only; the commitment side has no stable counterpart"),
 ("MECHANISM_NON_PERSONNEL", "WRITES", "TRACE_TABLES", "the YTFM_BR_* control tables"),
 ("TRACE_TABLES", "EVIDENCES", "DEAD_CODE_PBC_CONVERSION",
  "YTFM_BR_FM_POS holds zero rows, consistent with the guarded branch not running"),
 ("DEFECT_MR_WAERS", "LIMITS", "MECHANISM_NON_PERSONNEL",
  "EUR is 20.7% of the ledger; USD, at 52.7%, is outside the main path"),
 ("DEFECT_MR_HKONT", "BLOCKS", "MECHANISM_PERSONNEL",
  "the staff gate is the only one accepting USD and it fails on an empty range"),
 ("DEAD_CODE_PBC_CONVERSION", "BLOCKS", "MECHANISM_PERSONNEL",
  "both call sites sit inside IF 1 = 2"),
 ("MECHANISM_PERSONNEL", "COMPUTED_IN", "MECHANISM_PERSONNEL",
  "the payroll engine's calculation schema, in its codifications — not in ABAP"),
 # --- the payroll edges. These are what make the staff side a mechanism with a path rather
 # --- than a claim: engine -> carrier -> symbolic account -> resolved GL account.
 ("MECHANISM_PERSONNEL", "COMPUTED_BY", "PAYROLL_ENGINE",
  "the calculation schema and its codifications — the reason a code search never found it"),
 ("ALGORITHM_A16", "DISCOVERS", "PAYROLL_ENGINE",
  "seven parts: engine, logic, output, gates, master data, posting, resolved posting"),
 ("MECHANISM_PERSONNEL", "CARRIED_BY", "WAGE_TYPES_CONSTANT_DOLLAR",
  "72 wage types, identical in T512W — named after their output, which is why the schema "
  "text does not mention them"),
 ("WAGE_TYPES_CONSTANT_DOLLAR", "POSTS_AS", "TWIN_POSTING",
  "58 of 58 configured pairs go to the base's symbolic account with the opposite sign"),
 ("TWIN_POSTING", "RESOLVES_THROUGH", "SYMBOLIC_ACCOUNT",
  "the twin inherits the base's account assignment because it uses the base's account"),
 ("FIELD_WIDTH_TRAP", "EXPLAINS_WHY_WE_COULD_NOT_FIND", "SYMBOLIC_ACCOUNT",
  "a CHAR(4) key cannot sit in a CHAR(3) field; measuring the widths ended the search in "
  "one call after three extractions had not"),
 ("RESOLVED_POSTING", "ANSWERS", "SYMBOLIC_ACCOUNT",
  "the documents carry the key and the resolved account on one row, so the assignment is "
  "read from what happened rather than from what was configured"),
 ("SYMBOLIC_ACCOUNT", "REACHES_FM_THROUGH", "PAYROLL_TO_FM_BRIDGE",
  "T9POST — and none of the 24 Constant Dollar symbolic accounts appears in it, consistent "
  "with the twin inheriting its base's assignment"),
 ("ENHANCEMENT_POSTING_ACCOUNTS", "SITS_ON", "RESOLVED_POSTING",
  "a custom enhancement named after account determination, on the retro posting program"),
 ("PAYROLL_ENGINE", "DRIVEN_BY", "MASTER_DATA_BY_HAND",
  "the infotypes that carry the driving fields, crossed with the change log"),
 ("ALGORITHM_A17", "JUDGES", "MASTER_DATA_BY_HAND",
  "by which route each change reached production, and whether that route is the norm"),
 ("PERIMETER_FEATURE_YYCDR", "SELECTS_FROM", "PAYROLL_ENGINE",
  "2,086 employees of 23,700 — a perimeter held in a feature, which no code or table "
  "search would find"),
 ("ALGORITHM_A16", "SHARES_WITH", "ALGORITHM_A14",
  "both write to the shared algorithm memory, so a trap found by one is available to the "
  "other — the field-width trap came out of the payroll hunt and applies to any join"),
]


def main():
    art = json.load(io.open(ART, encoding="utf-8")) if os.path.exists(ART) else {}
    c = json.load(io.open(CLAIMS, encoding="utf-8"))
    cl = c["claims"] if isinstance(c, dict) and "claims" in c else c

    # Every node must point at content that EXISTS. A node whose content_in is a dead path
    # is the same failure as prose in a path field — it looks structured and answers nothing.
    def resolve(ref):
        # The reference is "<path> [.json.path.inside]". Take the PATH — the first token —
        # whole. Splitting it on '.' truncates any real filename at its extension, which is
        # how a working reference gets reported as broken.
        base = ref.split()[0]
        for cand in (os.path.join(HERE, base), os.path.join(ROOT, base), base):
            if os.path.exists(cand):
                return True
        # Some references name a record rather than a file — a claim, a backlog task.
        return base.startswith("claims") or base.startswith("AN-") or base.startswith("EXT-")

    nodes = []
    for nd in NODES:
        rec = dict(nd)
        rec["content_resolves"] = resolve(nd["content_in"])
        rec["degree"] = sum(1 for a, _, b, _ in EDGES if nd["id"] in (a, b))
        nodes.append(rec)

    ids = {n["id"] for n in nodes}
    edges, dangling = [], []
    for a, rel, b, why in EDGES:
        if a in ids and b in ids:
            edges.append({"from": a, "rel": rel, "to": b, "why": why})
        else:
            dangling.append([a, rel, b])

    br_claims = sorted({int(x["id"]) for x in cl
                        if any(k in json.dumps(x.get("related_objects") or []).upper()
                               for k in ("EURX", "BR_", "BUDGET", "ZZFIX", "YTFM_BR"))
                        or "BUDGET RATE" in (x.get("claim") or "").upper()[:200]})

    by_kind = collections.Counter(n["kind"] for n in nodes)
    orphan_nodes = [n["id"] for n in nodes if n["degree"] == 0]
    unresolved = [n["id"] for n in nodes if not n["content_resolves"]]

    out = {
        "_algorithm": "A15 build_br_graph.py",
        "_what_it_is": ("the RELATION between the pieces of the budget rate. Every node points "
                        "at where its content lives; the graph carries only the edges and the "
                        "evidence for them"),
        "_why_edges": ("a conclusion with no edges is prose with a JSON wrapper. The edges are "
                       "what let 'what does the availability check depend on' be answered "
                       "mechanically"),
        "nodes": nodes, "edges": edges,
        "summary": {
            "nodes": len(nodes), "edges": len(edges), "by_kind": dict(by_kind),
            "orphan_nodes": orphan_nodes, "dangling_edges": dangling,
            "nodes_with_unresolved_content": unresolved,
            "claims_on_this_subject": br_claims,
            "most_connected": sorted([(n["degree"], n["id"]) for n in nodes], reverse=True)[:5]},
        "_the_shape_it_reveals": (
            "two sibling mechanisms sharing exactly one thing — the rate type. Everything else "
            "differs: the gate is eight ranges on one side and an HR feature on the other, the "
            "moments are twelve on one side and a payroll schema on the other, and only one of "
            "the two has a measurable impact. Three of the four DEFECT nodes point at the "
            "personnel side, and it is the side that has never been measured."),
    }
    json.dump(out, io.open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    print("A15 BUDGET-RATE SUBJECT GRAPH")
    print("=" * 66)
    print("  %d nodes, %d edges" % (len(nodes), len(edges)))
    print("  by kind: %s" % dict(by_kind))
    print("  claims on this subject: %s" % br_claims)
    if orphan_nodes:
        print("  ORPHAN NODES (no edge — the relation is missing): %s" % orphan_nodes)
    if dangling:
        print("  DANGLING EDGES: %s" % dangling)
    if unresolved:
        print("  CONTENT NOT RESOLVED: %s" % unresolved)
    print("\n  most connected:")
    for deg, i in sorted([(n["degree"], n["id"]) for n in nodes], reverse=True)[:5]:
        print("    %-32s %d edges" % (i, deg))
    remember(subject="budget rate graph", kind="CARRIER", learned_by="A15_br_graph", session=98,
             fact="%d subjects related by %d typed edges; %d claims on the subject"
                  % (len(nodes), len(edges), len(br_claims)),
             evidence="brain_v2/budget_rate_graph.json",
             implication=("ask the graph before re-deriving: the relation between perimeter, "
                          "moments, rate type and control is recorded, not remembered"))
    print("\nwritten: brain_v2/budget_rate_graph.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
