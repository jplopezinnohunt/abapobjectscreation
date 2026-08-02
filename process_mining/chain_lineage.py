"""ALGORITHM A10 — ADDRESS CHAIN RECONSTRUCTION.

WHAT IT ANSWERS
    "Which funding source paid for which piece of work?" — in an installation where no
    foreign key answers it.

WHY IT EXISTS
    SAP designs a chain: work (WBS) -> Funded Program -> FM line -> availability control.
    At UNESCO that chain is measurably absent from the schema: the FM ledger posts on
    exactly two legs (Fund x Fund Center), and Funded Program, Functional Area, Grant and
    Profit Center are populated in 0.0% of 2,308,814 actual lines. Yet the organisation
    plans, executes and reports on projects every day. So the chain exists somewhere else.

    It exists in the IDENTIFIER STRINGS. A WBS element is `123BKF0401.1.2`: the fund code
    is its root and the dot depth is its level. A project id IS a fund code. Two custom
    Y-tables carry the programmatic link the standard dimensions were meant to carry.

    A10 measures that: it reconstructs each hop of the chain, reports how much of it
    resolves, how much RESOLUTION IS LOST at each hop, and — the part that makes it a
    governance instrument rather than a join — whether anyone can OBSERVE the hop at all.

WHAT MAKES IT PORTABLE
    Everything installation-specific is declared in chain_spec.json: which columns carry
    which grammar, which hops to walk, which change-log classes should cover them. The
    algorithm asserts nothing about UNESCO. Point it at another spec and it profiles
    another installation.

THE VERDICTS, and why each is a different problem
    LIVE          the hop resolves through the carrier that was designed to carry it.
    SUBSTITUTED   the designed carrier is unused and something else carries it — a string
                  convention, a custom table. It WORKS, and it is invisible to anyone
                  reading the data model. This is the most important verdict A10 emits.
    COLLAPSED     the hop resolves, but many left values map to one right value, so
                  resolution is destroyed in transit. Control still happens; attribution
                  does not.
    PARTIAL       the carrier exists and covers only part of the population.
    BROKEN        the hop does not resolve. If it is a designed hop, the design is not
                  running.

USAGE
    python process_mining/chain_lineage.py [spec.json] [--out report.json]
"""

import collections
import io
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "brain_v2", "methods"))
from algorithm_memory import recall, remember  # noqa: E402  what the other algorithms learned
DEFAULT_SPEC = os.path.join(HERE, "chain_spec.json")

# A hop that resolves this well is doing its job.
LIVE = 99.0
# Below this it is not a hop, it is a coincidence.
BROKEN = 50.0
# Below this, essentially nothing arrives: the hop is not a hop.
DEAD = 5.0
# A discovered change-document class must look strongly like the table it claims. Lower
# than this and shared prefixes start producing confident wrong ownership.
AFFINITY = 0.75
# Share of addresses where many detail values arrive at a single bucket. Above this, the
# hop is a funnel: it resolves, and the finer dimension does not come out the other side.
SHARED_POOL = 50.0
# Report at most this many orphans — they are for diagnosis, not for the record.
ORPHAN_SAMPLE = 8


def shape(s):
    """The grammar of an identifier: digits -> D, letters -> A, everything else kept.

    `123BKF0401.1.2` -> `DDDAAADDDD_D_D`. Two identifiers share a shape when they were
    minted by the same rule, which is what lets us find the rules nobody wrote down.
    """
    s = (s or "").strip()
    s = re.sub("[^0-9A-Za-z]", "_", s)
    return re.sub("[0-9]", "D", re.sub("[A-Za-z]", "A", s))


def key_sql(expr, sep="."):
    """The little DSL the spec uses to name a join key.

    Kept in SQL rather than resolved per-row in Python: the fact tables run to millions of
    rows, and aggregating before resolving is the difference between seconds and an hour.
    """
    kind, _, col = expr.partition(":")
    if kind == "col":
        return 'trim("%s")' % col
    if kind == "root":
        # everything before the first separator — the fund code inside a WBS id
        return ("CASE WHEN instr(\"{c}\",'{s}')>0 THEN trim(substr(\"{c}\",1,instr(\"{c}\",'{s}')-1))"
                ' ELSE trim("{c}") END').format(c=col, s=sep)
    if kind == "concat":
        return " || '|' || ".join('trim("%s")' % c for c in col.split("|"))
    raise ValueError("unknown key expression: %r" % expr)


def has_table(cx, t):
    return bool(cx.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (t,)).fetchone())


def cols_of(cx, t):
    return [r[1] for r in cx.execute('PRAGMA table_info("%s")' % t)]


def keyed_counts(cx, table, expr, sep=".", scope=None):
    """{key: rows} for one side of a hop. One GROUP BY, no row-by-row work.

    `scope` narrows the population a hop is SUPPOSED to cover. Without it, a hop that
    correctly serves 20% of a master gets scored against the 80% it was never meant to
    touch — which reads as a broken chain and is really a mis-stated denominator.
    """
    sql = 'SELECT %s k, count(*) FROM "%s"%s GROUP BY 1' % (
        key_sql(expr, sep), table, (" WHERE " + scope) if scope else "")
    return {k: n for k, n in cx.execute(sql) if k}


def detail_counts(cx, table, expr, detail, sep=".", scope=None):
    """{address: how many distinct DETAIL values live at it}.

    This is the measurement that names a collapse. Coverage says a hop resolves; this says
    how much of the finer story survived it. An FM line carries a commitment item; the
    availability bucket it consumes carries a grouped one. Both are true, and only the
    comparison per address shows that attribution was destroyed.

    Kept per-address rather than as one average on purpose: an average hides the case that
    matters, where most addresses collapse to a single bucket and a few keep their detail.
    """
    sql = ('SELECT %s k, count(DISTINCT trim("%s")) FROM "%s"%s GROUP BY 1'
           % (key_sql(expr, sep), detail, table, (" WHERE " + scope) if scope else ""))
    return {k: n for k, n in cx.execute(sql) if k}


# ---------------------------------------------------------------- grammars

def infer_grammars(cx, spec):
    """Find the rules nobody wrote down, by looking at how identifiers are SHAPED."""
    out = []
    for g in spec.get("grammars", []):
        t, col = g["table"], g["column"]
        if not has_table(cx, t) or col not in cols_of(cx, t):
            out.append({"id": g["id"], "status": "ABSENT",
                        "note": "%s.%s is not in this golden" % (t, col)})
            continue

        where, args = "", []
        for k, v in (g.get("scope") or {}).items():
            where, args = " WHERE %s=?" % k, [v]
        rows = [r[0] for r in cx.execute('SELECT "%s" FROM "%s"%s' % (col, t, where), args) if r[0]]

        shapes = collections.Counter(shape(r) for r in rows)
        ex = {}
        for r in rows:
            ex.setdefault(shape(r), []).append(r)
        total = sum(shapes.values()) or 1

        sep = g.get("hierarchy_separator")
        depth = collections.Counter(len(r.split(sep)) for r in rows) if sep else None

        rec = {
            "id": g["id"], "status": "MEASURED", "source": "%s.%s" % (t, col), "n": total,
            "distinct_shapes": len(shapes),
            "shapes": [{"shape": s, "n": n, "pct": round(100.0 * n / total, 1),
                        "examples": ex[s][:3]} for s, n in shapes.most_common(8)],
            "_why_it_matters": g.get("why"),
        }
        if depth:
            rec["hierarchy_depth"] = {str(d): depth[d] for d in sorted(depth)}
            rec["max_depth"] = max(depth)

        # Does the shape PREDICT a master-data attribute? If it does, the string is not a
        # label — it is a classification the schema never declared.
        corr = g.get("correlate_to")
        if corr and corr in cols_of(cx, t):
            pair = cx.execute('SELECT "%s","%s" FROM "%s"%s' % (col, corr, t, where), args)
            by = collections.defaultdict(collections.Counter)
            for v, a in pair:
                if v:
                    by[shape(v)][a or "(empty)"] += 1
            pred = {}
            for s, c in by.items():
                tot = sum(c.values())
                if tot >= 25:
                    pred[s] = {"dominant": c.most_common(4),
                               "concentration_pct": round(100.0 * c.most_common(1)[0][1] / tot, 1)}
            rec["predicts_%s" % corr] = pred
            strong = [s for s, v in pred.items() if v["concentration_pct"] >= 50]
            rec["_grammar_is_a_classification"] = bool(strong)
        out.append(rec)
    return out


# ---------------------------------------------------------------- carriers

def measure_carriers(cx, spec):
    """How full is each dimension the design relies on? A 0% column is a design not running."""
    out = []
    for c in spec.get("dimension_carriers", []):
        t = c["table"]
        if not has_table(cx, t):
            out.append({"table": t, "status": "ABSENT"})
            continue
        have = cols_of(cx, t)
        n = cx.execute('SELECT count(*) FROM "%s"' % t).fetchone()[0]
        pops = {}
        # The designed carrier is always measured, even when the spec forgot to list it —
        # otherwise "is the design running?" gets answered by an absence of evidence.
        want = list(c["columns"])
        dw0 = c.get("designed_to_carry_work")
        if dw0 and dw0 not in want:
            want.append(dw0)
        for col in want:
            if col not in have:
                pops[col] = {"status": "COLUMN_ABSENT"}
                continue
            f = cx.execute('SELECT count(*) FROM "%s" WHERE "%s" IS NOT NULL AND trim("%s")<>%s'
                           % (t, col, col, "''")).fetchone()[0]
            pops[col] = {"populated": f, "pct": round(100.0 * f / n, 1) if n else 0.0}
        dw = c.get("designed_to_carry_work")
        rec = {"table": t, "role": c.get("role"), "rows": n, "population": pops}
        if dw:
            p = pops.get(dw, {})
            rec["designed_work_carrier"] = dw
            rec["designed_work_carrier_status"] = (
                "UNUSED" if p.get("pct") == 0.0 or p.get("status") == "COLUMN_ABSENT" else "IN_USE")
        out.append(rec)
    return out


# ---------------------------------------------------------------- hops

def walk_hop(cx, hop, sep="."):
    r = {"id": hop["id"], "semantic": hop.get("semantic"),
         "designed_carrier": hop.get("designed_carrier"),
         "actual_carrier": hop.get("actual_carrier"), "expected": hop.get("expect")}
    lt, rt = hop["left"]["table"], hop["right"]["table"]
    if not has_table(cx, lt) or not has_table(cx, rt):
        r["verdict"] = "UNMEASURABLE"
        r["why"] = "table absent from this golden: %s" % (lt if not has_table(cx, lt) else rt)
        return r

    lk = hop["left"]["key"].partition(":")[2].split("|")[0]
    rk = hop["right"]["key"].partition(":")[2].split("|")[0]
    if lk not in cols_of(cx, lt) or rk not in cols_of(cx, rt):
        r["verdict"] = "UNMEASURABLE"
        r["why"] = "key column absent (%s.%s or %s.%s)" % (lt, lk, rt, rk)
        return r

    lscope, rscope = hop["left"].get("scope"), hop["right"].get("scope")
    if lscope:
        r["left_scope"] = lscope
        r["_scope_reason"] = hop.get("scope_reason")
    left = keyed_counts(cx, lt, hop["left"]["key"], sep, lscope)
    right = keyed_counts(cx, rt, hop["right"]["key"], sep, rscope)
    lrows = sum(left.values())
    if not lrows:
        # Not "empty" — the designed carrier exists as a column and is blank in every row.
        # That is the strongest possible statement that a design is not running.
        r["verdict"] = "BROKEN"
        r["why"] = ("the left key resolves to nothing in any row — the carrier this hop "
                    "depends on is declared and never populated")
        r["left_rows"] = cx.execute('SELECT count(*) FROM "%s"' % lt).fetchone()[0]
        return r

    matched = set(left) & set(right)
    hit = sum(left[k] for k in matched)
    cov = 100.0 * hit / lrows

    # Resolution loss. Only measurable when the spec names the finer dimension that the
    # hop is suspected of flattening.
    collapse, fan, shared = None, {}, None
    if hop["left"].get("detail") and hop["right"].get("detail"):
        ld = detail_counts(cx, lt, hop["left"]["key"], hop["left"]["detail"], sep, lscope)
        rd = detail_counts(cx, rt, hop["right"]["key"], hop["right"]["detail"], sep, rscope)
        both = [(ld[k], rd[k]) for k in (set(ld) & set(rd))]
        if both:
            fan = {
                "left_detail": hop["left"]["detail"], "right_detail": hop["right"]["detail"],
                "addresses_compared": len(both),
                "avg_left_detail_per_address": round(sum(a for a, _ in both) / float(len(both)), 2),
                "avg_right_detail_per_address": round(sum(b for _, b in both) / float(len(both)), 2),
            }
            # The statement that matters is not an average. It is: at how many addresses do
            # SEVERAL distinct cost categories arrive and only ONE bucket exist to hold them?
            # That is a shared pool, and at those addresses attribution is gone entirely.
            single = [1 for a, b in both if b == 1 and a > 1]
            shared = round(100.0 * len(single) / len(both), 1)
            fan["addresses_where_many_share_one_bucket_pct"] = shared
            fan["_reading"] = (
                "at %.1f%% of addresses, %s distinct %s values on average arrive at a SINGLE %s "
                "— every cost category there draws on one shared pool"
                % (shared, fan["avg_left_detail_per_address"], fan["left_detail"], fan["right_detail"]))
            collapse = (round(fan["avg_left_detail_per_address"]
                              / fan["avg_right_detail_per_address"], 2)
                        if fan["avg_right_detail_per_address"] else None)
            r["resolution"] = fan

    r.update({
        "left": "%s [%s]" % (lt, hop["left"]["key"]), "right": "%s [%s]" % (rt, hop["right"]["key"]),
        "left_rows": lrows, "left_distinct_keys": len(left), "right_distinct_keys": len(right),
        "resolved_rows": hit, "coverage_pct": round(cov, 1),
        "resolved_distinct_keys": len(matched),
        "orphan_keys": len(set(left) - set(right)),
        "orphan_examples": sorted(set(left) - set(right))[:ORPHAN_SAMPLE],
        "collapse_ratio": collapse,
    })

    # One coverage number over a mixed population is an average of things that have
    # nothing to do with each other. Split it by the grammar of the key: if some families
    # resolve completely and others not at all, that is the finding, and the average hides it.
    uneven = False
    if hop.get("breakdown_by") == "grammar":
        by = collections.defaultdict(lambda: [0, 0])
        for k, n in left.items():
            s = shape(k)
            by[s][0] += n
            if k in matched:
                by[s][1] += n
        bd = [{"shape": s, "rows": t, "resolved": m, "coverage_pct": round(100.0 * m / t, 1)}
              for s, (t, m) in sorted(by.items(), key=lambda x: -x[1][0]) if t >= 50]
        r["coverage_by_grammar"] = bd[:10]
        if len(bd) >= 3:
            spread = max(x["coverage_pct"] for x in bd) - min(x["coverage_pct"] for x in bd)
            uneven = spread > 60

    if uneven and cov >= 5.0:
        r["verdict"] = "UNEVEN"
        zero = [x["shape"] for x in r["coverage_by_grammar"] if x["coverage_pct"] < 1.0]
        r["why"] = ("%.1f%% overall, but that average is meaningless: coverage runs from %.1f%% "
                    "to %.1f%% across identifier families%s. Some populations are fully carried "
                    "and others not at all, and nothing declares which — so the rule for who "
                    "gets a link is undocumented."
                    % (cov, min(x["coverage_pct"] for x in r["coverage_by_grammar"]),
                       max(x["coverage_pct"] for x in r["coverage_by_grammar"]),
                       (", including %s with no coverage at all" % ", ".join(zero[:3])) if zero else ""))
    elif cov < DEAD:
        r["verdict"] = "BROKEN"
        r["why"] = "only %.1f%% of rows resolve — nothing meaningful arrives" % cov
    elif shared is not None and shared >= SHARED_POOL:
        r["verdict"] = "COLLAPSED"
        r["why"] = ("%.1f%% resolves, and then the detail is destroyed: at %.1f%% of addresses "
                    "several distinct %s arrive at a SINGLE %s. Control still happens on the "
                    "pooled bucket; attribution to a cost category does not survive it."
                    % (cov, shared, fan.get("left_detail"), fan.get("right_detail")))
    elif cov < BROKEN:
        r["verdict"] = "SPARSE"
        r["why"] = ("the carrier exists and serves only %.1f%% of the population — real for those "
                    "rows, absent for the rest" % cov)
    elif cov >= LIVE:
        r["verdict"] = "LIVE"
    else:
        r["verdict"] = "PARTIAL"
        r["why"] = "%.1f%% resolves; %s keys have no counterpart" % (cov, r["orphan_keys"])

    # The verdict that matters most: it works, and not through what was designed.
    designed = (hop.get("designed_carrier") or "").lower()
    actual = (hop.get("actual_carrier") or "").lower()
    if r["verdict"] in ("LIVE", "PARTIAL") and actual and actual != "none" and designed not in (
            "", "none", actual) and ("string" in actual or "custom" in actual):
        r["verdict"] = "SUBSTITUTED" + ("" if r["verdict"] == "LIVE" else "_PARTIAL")
        r["why"] = ("resolves at %.1f%% — but through %s, not through the designed %s. It works "
                    "and it is invisible to anyone reading the data model."
                    % (cov, hop.get("actual_carrier"), hop.get("designed_carrier")))
    return r


# ---------------------------------------------------------------- instruments

def check_consistency(cx, spec):
    """Where TWO carriers claim the same fact, measure where they DISAGREE.

    A convention is only load-bearing if it agrees with the structure it stands in for.
    An identifier whose shape says "level 4" while the real parent-child tree puts the node
    at level 3 is worse than a missing link: everyone reads the code, because the code IS
    the convention, and for those rows everyone is wrong.

    The first check kind is depth-vs-tree. Others belong here as they are found — the
    pattern is the point, not this one instance.
    """
    out = []
    for chk in spec.get("consistency_checks", []):
        if chk.get("kind") != "depth_vs_tree":
            out.append({"id": chk.get("id"), "status": "UNKNOWN_KIND"})
            continue
        a, b = chk["carrier_a"], chk["carrier_b"]
        if not (has_table(cx, a["table"]) and has_table(cx, b["table"])):
            out.append({"id": chk["id"], "status": "UNMEASURABLE"})
            continue

        sep = chk.get("separator", ".")
        ident = {k: v for k, v in cx.execute(
            'SELECT "%s","%s" FROM "%s"' % (a["key"], a["value"], a["table"]))}
        parent = {k: v for k, v in cx.execute(
            'SELECT "%s","%s" FROM "%s"' % (b["key"], b["parent"], b["table"]))}

        def tree_depth(node):
            d, cur, guard = 1, node, 0
            while guard < 40:
                p = parent.get(cur)
                guard += 1
                if not p or not str(p).strip().strip("0"):
                    break
                d += 1
                cur = p
            return d

        agree, dis, ex = 0, 0, []
        for node in parent:
            code = ident.get(node)
            if not code:
                continue
            said = len(str(code).split(sep))
            real = tree_depth(node)
            if said == real:
                agree += 1
            else:
                dis += 1
                if len(ex) < 10:
                    ex.append({"identifier": code, "claimed_level": said, "actual_level": real})
        tot = agree + dis
        rec = {"id": chk["id"], "fact": chk.get("fact"), "status": "MEASURED",
               "compared": tot, "agree": agree, "disagree": dis,
               "agreement_pct": round(100.0 * agree / tot, 1) if tot else 0.0,
               "examples": ex}
        if tot and 100.0 * agree / tot >= 99.0:
            rec["verdict"] = "CONVENTION_HOLDS"
            rec["why"] = ("the identifier and the structure agree at %.1f%% — the convention is "
                          "load-bearing AND consistent, so reading the level off the code is "
                          "safe for all but %d rows" % (100.0 * agree / tot, dis))
        else:
            rec["verdict"] = "CONVENTION_DRIFTS"
            rec["why"] = ("the identifier and the structure disagree on %d of %d rows — reading "
                          "the level off the code is not safe" % (dis, tot))
        rec["_the_exceptions_are_the_point"] = (
            "every disagreeing row is a node whose identifier claims a position the tree does "
            "not give it. Everyone reads the code, so for these everyone is wrong.")
        out.append(rec)
    return out


def _norm(s):
    return re.sub("[^A-Z0-9]", "", (s or "").upper())


def _affinity(table, klass):
    """How strongly a change-document class looks like it belongs to a table.

    Longest common run of characters, scaled by the class name. `ytfm_fund_c5` and
    `YFMFUNDC5` score high; `funds` and `FMFINCODE` do not. Deliberately crude: this
    proposes candidates for a human to confirm, it does not decide.
    """
    a, b = _norm(table), _norm(klass)
    if not a or not b:
        return 0.0
    best = 0
    for i in range(len(b)):
        for j in range(i + best + 1, len(b) + 1):
            if b[i:j] in a:
                best = max(best, j - i)
            else:
                break
    return round(best / float(len(b)), 2)


def check_instruments(cx, spec, hops):
    """Can anyone SEE this object change? An object nobody observes is one nobody governs.

    Two things are measured that a declaration alone would miss. First, every change log
    is checked, not one: an installation may keep a filtered current log and a fuller
    history, and a class present only in the second is invisible to anyone querying the
    first. Second, classes are DISCOVERED by name affinity, because custom tables get
    custom change-document objects that no standard list will ever mention.
    """
    ins = spec.get("instruments", {})
    cl = ins.get("change_log", {})
    oc = cl.get("object_column", "OBJECTCLAS")
    logs = list(cl.get("tables") or ([cl["table"]] if cl.get("table") else []))

    # Ask what the other algorithms already learned about change instruments before
    # trusting this spec. A8 found that one of these logs is a filtered subset; that is
    # not something A10 should have to rediscover, or worse, fail to.
    learned = []
    for m in recall(kind="INSTRUMENT"):
        learned.append({"subject": m["subject"], "fact": m["fact"],
                        "learned_by": m["learned_by"], "implication": m["implication"]})
        if has_table(cx, m["subject"]) and m["subject"] not in logs:
            logs.append(m["subject"])

    per_log = {}
    for t in logs:
        if has_table(cx, t) and oc in cols_of(cx, t):
            per_log[t] = {k: n for k, n in cx.execute(
                'SELECT "%s",count(*) FROM "%s" GROUP BY 1' % (oc, t)) if k}

    tables = list((cl.get("expected_classes") or {}).keys())
    declared = set(v for v in (cl.get("expected_classes") or {}).values() if v)

    # Discovery, assigned ONE-TO-ONE. Scoring each table independently let `ytfm_fund_cpl`
    # claim `YFMFUNDC5` on a shared prefix — a confident wrong answer, which is exactly the
    # failure this whole algorithm exists to catch. A class belongs to its BEST match and
    # to nothing else.
    pairs = []
    for lg, classes in per_log.items():
        for k in classes:
            if k in declared:
                continue
            for tbl in tables:
                a = _affinity(tbl, k)
                if a >= AFFINITY:
                    pairs.append((a, classes[k], tbl, k, lg))
    pairs.sort(reverse=True)
    assigned, taken_class, taken_tbl = {}, set(), set()
    for a, n, tbl, k, lg in pairs:
        if k in taken_class or tbl in taken_tbl:
            continue
        taken_class.add(k)
        taken_tbl.add(tbl)
        assigned[tbl] = {"class": k, "log": lg, "records": n, "affinity": a}

    out = []
    for tbl, klass in (cl.get("expected_classes") or {}).items():
        rec = {"object": tbl, "declared_class": klass, "seen_in": {}}
        if tbl in assigned:
            rec["discovered_candidate"] = assigned[tbl]

        use = klass or (assigned[tbl]["class"] if tbl in assigned else None)
        rec["change_log_class"] = use
        for lg, classes in per_log.items():
            if use and use in classes:
                rec["seen_in"][lg] = classes[use]

        if not use:
            rec["visibility"] = "BLIND"
            rec["why"] = ("no change-document object is declared for this table and none was "
                          "discovered — who changed it cannot be answered from the change log")
            rec["fallback"] = ins.get("execution_log", {}).get("algorithm")
        elif not rec["seen_in"]:
            rec["visibility"] = "DECLARED_BUT_EMPTY"
            rec["why"] = ("the change-document object is part of the design and carries no "
                          "records in any log here — changes to this object leave no trace")
            rec["fallback"] = ins.get("execution_log", {}).get("algorithm")
        elif len(rec["seen_in"]) < len(per_log):
            missing = [l for l in per_log if l not in rec["seen_in"]]
            rec["visibility"] = "OBSERVABLE_IN_ONE_LOG_ONLY"
            rec["why"] = ("present in %s and absent from %s — anyone querying the wrong log "
                          "concludes this object never changes"
                          % (", ".join(rec["seen_in"]), ", ".join(missing)))
        else:
            rec["visibility"] = "OBSERVABLE"
        if not klass and use:
            rec["_note"] = ("this class was DISCOVERED, not declared — a custom change-document "
                            "object for a custom table")
        out.append(rec)

    # Which classes does each log carry that the others do not? A log that is a filtered
    # subset of another is a trap: it answers "no changes" for objects it simply omits.
    if len(per_log) > 1:
        allsets = {t: set(v) for t, v in per_log.items()}
        for t, s in allsets.items():
            others = set().union(*[v for k, v in allsets.items() if k != t])
            if others - s:
                out.append({"object": "_LOG_COVERAGE_%s" % t, "visibility": "PARTIAL_LOG",
                            "classes_missing_here": sorted(others - s),
                            "why": ("this log does not carry %d change-document classes that "
                                    "another log does — it is a filtered subset, and querying "
                                    "it alone silently under-reports"
                                    % len(others - s))})
    if learned:
        out.append({"object": "_RECALLED_FROM_ALGORITHM_MEMORY", "visibility": "PRIOR_KNOWLEDGE",
                    "memories": learned,
                    "why": ("these instrument facts were learned by other algorithms and applied "
                            "here without rediscovery — the logs they name were added to the "
                            "set this run measured")})
    return out


def learn(report, session=None):
    """Write back what this run established, so the next algorithm starts from it."""
    wrote = []
    for h in report["hops"]:
        if h["verdict"].startswith("SUBSTITUTED"):
            wrote.append(remember(
                subject=h["left"].split(" ")[0] + " -> " + h["right"].split(" ")[0],
                kind="CARRIER", learned_by="A10_chain_lineage", session=session,
                fact=("this link resolves at %.1f%% through %s, NOT through the designed %s"
                      % (h["coverage_pct"], h["actual_carrier"], h["designed_carrier"])),
                evidence="%d of %d rows" % (h["resolved_rows"], h["left_rows"]),
                implication=("join through the actual carrier and say so. Anyone reading the "
                             "data model will look for the designed one and find nothing.")))
    for i in report["instruments"]:
        if i.get("visibility") in ("BLIND", "DECLARED_BUT_EMPTY", "OBSERVABLE_IN_ONE_LOG_ONLY"):
            wrote.append(remember(
                subject=i["object"], kind="INSTRUMENT", learned_by="A10_chain_lineage",
                session=session,
                fact="change visibility for this object is %s (%s)" % (
                    i["visibility"], i.get("change_log_class") or "no class"),
                evidence=json.dumps(i.get("seen_in") or {}),
                implication=i.get("why") or "confirm before answering who-changed-this here"))
    return wrote


# ---------------------------------------------------------------- run

def main(argv):
    spec_path = DEFAULT_SPEC
    out_path = os.path.join(ROOT, "brain_v2", "chain_lineage.json")
    rest = [a for a in argv if not a.startswith("--")]
    if rest:
        spec_path = rest[0] if os.path.isabs(rest[0]) else os.path.join(ROOT, rest[0])
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]

    spec = json.load(io.open(spec_path, encoding="utf-8"))
    db = spec["golden_db"]
    db = db if os.path.isabs(db) else os.path.join(ROOT, db)
    if not os.path.exists(db):
        print("golden not found: %s" % db)
        return 2
    cx = sqlite3.connect(db)

    sep = "."
    for g in spec.get("grammars", []):
        if g.get("hierarchy_separator"):
            sep = g["hierarchy_separator"]

    print("A10 ADDRESS CHAIN RECONSTRUCTION  instance=%s" % spec.get("instance"))
    print("=" * 78)

    grammars = infer_grammars(cx, spec)
    print("\nGRAMMARS — the classifications nobody declared")
    for g in grammars:
        if g["status"] != "MEASURED":
            print("  %-12s %s" % (g["id"], g["status"]))
            continue
        tag = " [IS A CLASSIFICATION]" if g.get("_grammar_is_a_classification") else ""
        print("  %-12s n=%-7d %d shapes%s" % (g["id"], g["n"], g["distinct_shapes"], tag))
        for s in g["shapes"][:3]:
            print("        %-20s %5.1f%%  %s" % (s["shape"], s["pct"], ", ".join(s["examples"][:2])))
        if g.get("max_depth"):
            print("        depth 1..%d  %s" % (g["max_depth"], g["hierarchy_depth"]))

    carriers = measure_carriers(cx, spec)
    print("\nDIMENSION CARRIERS — is the designed chain populated?")
    for c in carriers:
        if c.get("status") == "ABSENT":
            print("  %-16s ABSENT" % c["table"])
            continue
        print("  %-16s %d rows" % (c["table"], c["rows"]))
        for col, p in c["population"].items():
            print("      %-11s %s" % (col, p.get("status") or ("%.1f%%" % p["pct"])))
        if c.get("designed_work_carrier"):
            print("      -> designed work carrier %s is %s"
                  % (c["designed_work_carrier"], c["designed_work_carrier_status"]))

    hops = [walk_hop(cx, h, sep) for h in spec.get("hops", [])]
    # A BROKEN verdict without a mechanism is a symptom. Attach the declared, measured
    # reason so the report says WHY the carrier is empty, not merely that it is.
    dm = spec.get("derivation_mechanisms") or {}
    for con in dm.get("consequences", []):
        for h in hops:
            if h["id"] == con.get("affects_hop") and h["verdict"] == "BROKEN":
                h["root_cause"] = con
                h["why"] = "%s %s" % (h.get("why", ""), con["reason"])
    print("\nHOPS — the address chain, walked")
    for h in hops:
        print("  %-26s %-18s %s" % (h["id"], h["verdict"],
                                    ("%.1f%% of %s rows" % (h["coverage_pct"], h["left_rows"]))
                                    if "coverage_pct" in h else (h.get("why") or "")))
        if h.get("why") and "coverage_pct" in h:
            print("        %s" % h["why"])

    cons = check_consistency(cx, spec)
    if cons:
        print("\nCONSISTENCY — where two carriers claim the same fact")
        for k in cons:
            if k.get("status") != "MEASURED":
                print("  %-16s %s" % (k["id"], k.get("status")))
                continue
            print("  %-16s %-20s %.1f%% agree, %d disagree"
                  % (k["id"], k["verdict"], k["agreement_pct"], k["disagree"]))
            for e in k["examples"][:3]:
                print("        %-24s code says %d, tree says %d"
                      % (e["identifier"], e["claimed_level"], e["actual_level"]))

    instruments = check_instruments(cx, spec, hops)
    print("\nINSTRUMENTS — who can see these objects change?")
    for i in instruments:
        print("  %-16s %-20s %s" % (i["object"], i["visibility"],
                                    i.get("change_log_class") or "(no class declared)"))

    verdicts = collections.Counter(h["verdict"] for h in hops)
    report = {
        "_algorithm": "A10 chain_lineage.py — address chain reconstruction",
        "_what_it_measures": (
            "whether the chain from funding source to piece of work resolves, through WHICH "
            "carrier, how much resolution survives each hop, and whether anyone can observe "
            "the hop change"),
        "_spec": os.path.relpath(spec_path, ROOT).replace("\\", "/"),
        "instance": spec.get("instance"),
        "grammars": grammars, "dimension_carriers": carriers, "hops": hops,
        "consistency_checks": cons,
        "instruments": instruments,
        "summary": {
            "hops_walked": len(hops), "verdicts": dict(verdicts),
            "substituted": [h["id"] for h in hops if h["verdict"].startswith("SUBSTITUTED")],
            "broken": [h["id"] for h in hops if h["verdict"] == "BROKEN"],
            "collapsed": [h["id"] for h in hops if h["verdict"] == "COLLAPSED"],
            # Only objects genuinely unwatchable. Meta rows (log coverage, recalled
            # memory) are not objects and must not inflate a governance count.
            "convention_exceptions": sum(k.get("disagree", 0) for k in cons),
            "blind_objects": [i["object"] for i in instruments
                              if i.get("visibility") in ("BLIND", "DECLARED_BUT_EMPTY")],
            "observable_in_one_log_only": [i["object"] for i in instruments
                                           if i.get("visibility") == "OBSERVABLE_IN_ONE_LOG_ONLY"],
        },
    }
    wrote = learn(report, session=spec.get("session"))
    report["_learned_back_into_algorithm_memory"] = len(wrote)
    json.dump(report, io.open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n%s" % ("-" * 78))
    print("verdicts: %s" % dict(verdicts))
    print("written: %s" % os.path.relpath(out_path, ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
