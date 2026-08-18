"""ALGORITHM A16 — PAYROLL END-TO-END DISCOVERY.

WHAT IT ANSWERS
    How is payroll actually configured and run here, end to end: which schemas fire, which
    of the logic is custom, which master data drives it, HOW that master data is
    maintained — by hand, by interface, or by configuration — and how the result posts.

WHY IT EXISTS
    Payroll computes staff cost, which is the largest spend category in most public-sector
    installations, and it does so in a layer that is neither ABAP nor data: schemas, rules,
    wage types and features. A code search does not reach it. A table search does not
    recognise it. It was invisible in this brain until a budget-rate question forced the
    door, and what came out immediately was a mechanism — 72 'Constant Dollar' wage types —
    that is named after its OUTPUT and therefore appears nowhere in the schema or rule text.

    That is the general lesson this algorithm is built on: PAYROLL LOGIC IS NAMED AFTER
    WHAT IT PRODUCES. So the discovery runs from the output backwards as well as from the
    driver forwards, and reports both.

WHAT IT PRODUCES, in seven parts
    1. THE ENGINE      which schemas exist, which are custom, and the driver's shape.
    2. THE LOGIC       rules, how many are custom, and where the custom mass sits.
    3. THE OUTPUT      wage types, the custom ones, and families that share a naming stem
                       — the stem is usually the mechanism's real name.
    4. THE GATES       features, which are custom, and what structure each decides on.
                       A feature is a perimeter that no code or table search will find.
    5. THE MASTER DATA which infotypes carry the driving fields, and — crossed with the
                       change log — whether they are maintained BY HAND or by a channel.
    6. THE POSTING     the programs that move payroll into accounting, and the enhancements
                       sitting on that seam — where the custom mass concentrates.
    7. THE RESOLVED    what the posting actually resolved to, read from the documents rather
       POSTING         than the configuration. The configuration search fails for a
                       structural reason: a payroll symbolic account is CHAR(4) and the FI
                       account determination key is CHAR(3).

THE PART THAT IS NOT AN INVENTORY
    Anyone can list schemas. The question worth answering is which master data a human
    edits and which arrives from somewhere, because that is where the operating risk and
    the automation opportunity both sit. That comes from the change log, and where the
    change log is blind it says so rather than guessing.

USAGE
    python process_mining/payroll_discovery.py [--molga UN] [--out report.json]
"""

import collections
import io
import sqlite3
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "Zagentexecution", "mcp-backend-server-python"))
sys.path.insert(0, os.path.join(ROOT, "brain_v2", "methods"))
from rfc_helpers import get_connection  # noqa: E402
from algorithm_memory import remember  # noqa: E402

GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")
# A custom object is one in the customer namespace. Everything else is SAP's.
CUSTOM = ("Y", "Z")

# Tables whose golden copy holds ONLY runs that produced an accounting document. Reading one
# of these without the filter puts the simulations back — see purge_simulation_runs.py.
PURGED_TO_POSTED_RUNS = {
    "ppdix": "RUNID in (select RUNID from payroll_runs_posted)",
    "ppoix": "RUNID in (select RUNID from payroll_runs_posted)",
    "ppdit": ("DOCNUM in (select DOCNUM from ppdhd "
              "where RUNID in (select RUNID from payroll_runs_posted))"),
}


class Session(object):
    """P01 drops after roughly a dozen calls; a dropped call is not an answer."""

    def __init__(self, sid="P01"):
        self.sid = sid
        self.c = get_connection(sid)
        self.calls = 0
        self.from_gold, self.from_p01 = [], []
        try:
            self.gold = sqlite3.connect("file:%s?mode=ro" % GOLD.replace("\\", "/"), uri=True)
        except sqlite3.Error:
            self.gold = None

    def call(self, fm, **kw):
        for attempt in range(4):
            try:
                r = self.c.call(fm, **kw)
                self.calls += 1
                return r
            except Exception as e:
                m = str(e)
                if "COMMUNICATION_FAILURE" not in m and "not reached" not in m:
                    raise
                time.sleep(2 + attempt * 3)
                self.c = get_connection(self.sid)
        raise RuntimeError("system unreachable after retries")

    def read(self, table, fields, where=None, rows=0):
        """READ THE GOLDEN FIRST, and only fall back to P01 for what is not held.

        Two reasons, and the second one is a correctness bug rather than a preference.

        The cheap one: re-extracting a table the golden already holds is the exact waste the
        persistence rule exists to prevent — process mining is re-reading the base you have.

        The one that matters: PPDIT in the golden has been PURGED to runs that actually
        posted. A live read has no such filter, so it silently returns the simulations back
        — and summing those overstated this very mechanism ninefold. The filter must live
        where the read happens, not in whoever remembers to apply it.
        """
        if self.gold is not None:
            t = table.lower()
            try:
                cur = self.gold.execute('select 1 from sqlite_master '
                                        "where lower(name)=? and type in ('table','view')", (t,))
                if cur.fetchone():
                    sql = 'select %s from "%s"' % (",".join('"%s"' % f for f in fields), t)
                    # The WHERE must travel or the golden answers a DIFFERENT question than
                    # P01 would — silently, and wider. RFC_READ_TABLE's OPTIONS syntax is
                    # SQL-shaped for the simple predicates used here; if it is not valid
                    # SQLite the except below sends the read to P01 rather than guessing.
                    conds = [c for c in (where, PURGED_TO_POSTED_RUNS.get(t)) if c]
                    if conds:
                        sql += " where %s" % " and ".join("(%s)" % c for c in conds)
                    if rows:
                        sql += " limit %d" % rows
                    got = [dict(zip(fields, r)) for r in self.gold.execute(sql)]
                    self.from_gold.append(table)
                    return [{k: (v or "").strip() for k, v in r.items()} for r in got]
            except sqlite3.Error:
                pass  # a golden that cannot answer is not an error; P01 still can
        self.from_p01.append(table)
        try:
            r = self.call("RFC_READ_TABLE", QUERY_TABLE=table,
                          FIELDS=[{"FIELDNAME": f} for f in fields],
                          OPTIONS=([{"TEXT": where}] if where else []), ROWCOUNT=rows)
        except Exception as e:
            if "WITHOUT_DATA" in str(e):
                return []
            raise
        meta = r["FIELDS"]
        return [{f["FIELDNAME"]: row["WA"][int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
                 for f in meta} for row in r["DATA"]]


def is_custom(name):
    return bool(name) and name[0].upper() in CUSTOM


def stems(names, minimum=3):
    """Wage types that share a leading stem are usually one mechanism.

    The staff budget rate is 72 wage types beginning '9'. Nothing in the schema or the rule
    text names it; the stem does. Grouping by stem is how a mechanism surfaces when it is
    named after its output.
    """
    by = collections.Counter(n[:1] for n in names if n)
    return {k: v for k, v in by.items() if v >= minimum}


def discover_engine(s):
    steps = s.read("T52C1", ["SCHEM", "SEQNO", "FUNCO", "PARM1", "PARM2", "PARM3", "PARM4",
                             "DELET"])
    by_schema = collections.defaultdict(list)
    for x in steps:
        by_schema[x["SCHEM"]].append(x)
    out = {}
    for sc, rows in by_schema.items():
        active = [r for r in rows if r["DELET"] != "*"]
        out[sc] = {"steps": len(rows), "active": len(active), "custom": is_custom(sc),
                   "calls": sorted({r["PARM1"] for r in active
                                    if r["FUNCO"] in ("COPY", "PIT", "PRT") and r["PARM1"]})}
    return out


def discover_logic(s):
    lines = s.read("T52C5", ["CCYCL", "LGART", "SEQNO"])
    by_rule = collections.Counter(x["CCYCL"] for x in lines if x["CCYCL"])
    custom = {k: v for k, v in by_rule.items() if is_custom(k)}
    return {"rule_lines": len(lines), "rules": len(by_rule), "custom_rules": len(custom),
            "largest_custom": sorted(custom.items(), key=lambda x: -x[1])[:12]}


def discover_output(s, molga):
    wt = s.read("T512T", ["LGART", "LGTXT"], "SPRSL = 'E' AND MOLGA = '%s'" % molga)
    names = [x["LGART"] for x in wt]
    text = {x["LGART"]: x["LGTXT"] for x in wt}
    fam = collections.defaultdict(list)
    for w in names:
        fam[w[:1]].append(w)
    # A family whose members share a phrase in their TEXT is a mechanism with a name.
    named = {}
    for stem, members in fam.items():
        words = collections.Counter()
        for m in members:
            t = (text.get(m) or "").upper()
            for phrase in ("CONSTANT DOLLAR", "BUDGET", "PBC", "RESERVE", "PROVISION"):
                if phrase in t:
                    words[phrase] += 1
        if words:
            named[stem] = {"members": len(members), "phrases": dict(words)}
    return {"wage_types": len(names), "custom": sum(1 for w in names if is_custom(w)),
            "families_by_stem": stems(names), "families_with_a_named_mechanism": named,
            "_the_lesson": ("payroll logic is named after WHAT IT PRODUCES. A family sharing "
                            "a stem and a phrase in its text is a mechanism the schema layer "
                            "will not mention")}


def discover_gates(s):
    feats = s.read("T549D", ["NAMEN", "STRUC", "FUNCT"])
    custom = [f for f in feats if is_custom(f["NAMEN"])]
    by_struc = collections.Counter(f["STRUC"] for f in custom if f["STRUC"])
    return {"features": len(feats), "custom": len(custom),
            "custom_by_structure": by_struc.most_common(10),
            "custom_names": sorted(f["NAMEN"] for f in custom)[:40],
            "_how_to_read_one": ("each feature is COMPILED into a generated program named "
                                 "/1PAPA/FEAT<client><NAME>, readable through "
                                 "RPY_PROGRAM_READ. A decision tree maintained in PE03 is not "
                                 "invisible — it is just not where anyone looks")}


def discover_master_data(s, cx):
    """Which infotypes drive it, and — the part that matters — HOW they are maintained."""
    out = {"infotypes_driving_the_gates": ["PA0001 — org assignment: PERSG, GSBER, WERKS"],
           "in_the_golden": [], "maintenance": {}}
    if cx:
        for t in ("PA0001", "PA0008", "PA0014", "PA0015"):
            row = cx.execute("SELECT name FROM sqlite_master WHERE type='table' "
                             "AND lower(name)=lower(?)", (t,)).fetchone()
            if row:
                n = cx.execute('SELECT count(*) FROM "%s"' % row[0]).fetchone()[0]
                out["in_the_golden"].append({"table": t, "rows": n})
        # Manual versus channel: the change log names the transaction, and a BLANK
        # transaction code is the signature of a BAPI or an interface rather than a person.
        # cdhdr_history FIRST: cdhdr is SUPERSEDED and is a strict subset -- 7.8M rows
        # against 12.0M. Trying the stale one first meant this loop found it, used it, and
        # answered confidently about 4.2M changes it never saw. A stale copy does not fail.
        for log in ("cdhdr_history", "cdhdr"):
            has = cx.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table','view') "
                             "AND name=?", (log,)).fetchone()
            if not has:
                continue
            rows = cx.execute(
                'SELECT OBJECTCLAS, TCODE, count(*) FROM "%s" '
                "WHERE OBJECTCLAS LIKE 'HR%%' OR OBJECTCLAS LIKE 'PA%%' "
                "GROUP BY 1,2 ORDER BY 3 DESC" % log).fetchall()
            if not rows:
                continue
            per = collections.defaultdict(lambda: {"manual": 0, "no_tcode": 0, "by": {}})
            for oc, tc, k in rows:
                tc = (tc or "").strip()
                d = per[oc]
                if tc:
                    d["manual"] += k
                    d["by"][tc] = k
                else:
                    d["no_tcode"] += k
            out["maintenance"][log] = {
                oc: {"with_a_transaction": v["manual"], "with_NO_transaction": v["no_tcode"],
                     "pct_no_transaction": round(100.0 * v["no_tcode"] /
                                                 (v["manual"] + v["no_tcode"]), 1)
                     if (v["manual"] + v["no_tcode"]) else 0,
                     "top_transactions": sorted(v["by"].items(), key=lambda x: -x[1])[:5]}
                for oc, v in sorted(per.items(), key=lambda x: -(x[1]["manual"] + x[1]["no_tcode"]))[:8]}
    out["_how_to_read_maintenance"] = (
        "a change document carrying a TRANSACTION CODE was made by a person in a screen. A "
        "BLANK transaction code is the signature of a BAPI, an interface or a batch. The ratio "
        "is the answer to 'is this master data maintained by hand or fed'. Where the change "
        "log carries no class for an object at all, the question is UNANSWERABLE from here and "
        "A8 attribution against the execution log is the only instrument left.")
    return out


def discover_posting(s):
    """The last leg: how the result reaches FI and FM, and who enhanced that path.

    This is where the custom logic concentrates in practice. A posting program is the seam
    between two modules, and a seam is where an organisation reaches for an enhancement —
    so the enhancement inventory on the posting objects is usually the shortest description
    of what an installation actually changed about payroll.
    """
    out = {}
    # The symbolic-account configuration: wage type -> symbolic account -> GL.
    for tab, fields in (("T52EL", ["MOLGA", "LGART", "KOMOK", "SYMKO"]),
                        ("T52EK", ["KOMOK", "SYMKO", "KTOSL"]),
                        ("T030", ["KTOPL", "KTOSL", "BWMOD", "KONTS", "KONTH"])):
        try:
            rows = s.read(tab, fields, rows=0)
            out[tab] = {"rows": len(rows)}
            if tab == "T52EL" and rows:
                out[tab]["by_molga"] = collections.Counter(r["MOLGA"] for r in rows).most_common(8)
        except Exception as e:
            out[tab] = {"error": str(e)[:70]}

    # The posting programs, and the enhancements sitting on them. ENHOBJ names the hooked
    # object; a custom enhancement on a posting program is a deliberate intervention in the
    # seam between payroll and accounting.
    progs = ["RPCIPE00", "RPCIPE00_OLD", "RPCIPE01", "RPCIPP00", "SAPLHRFPM_POSTING",
             "RPCALCU0", "RPCALCX0", "SAPLHRPAY99_POST"]
    enh = []
    for p in progs:
        try:
            rows = s.read("ENHOBJ", ["ENHNAME", "OBJ_TYPE", "OBJ_NAME"],
                          "OBJ_NAME = '%s'" % p)
            for r in rows:
                enh.append({"hooked_object": p, "enhancement": r["ENHNAME"],
                            "type": r["OBJ_TYPE"], "custom": is_custom(r["ENHNAME"])})
        except Exception:
            continue
    # Anything custom hooked onto an HR function group is the same signal, found the other way.
    try:
        for r in s.read("ENHOBJ", ["ENHNAME", "OBJ_TYPE", "OBJ_NAME"], "ENHNAME LIKE 'Y%'"):
            if (r["OBJ_NAME"] or "").upper().startswith(("RPC", "HRFPM", "SAPLHR", "PC2", "HR")):
                enh.append({"hooked_object": r["OBJ_NAME"], "enhancement": r["ENHNAME"],
                            "type": r["OBJ_TYPE"], "custom": True})
    except Exception:
        pass
    seen, uniq = set(), []
    for e in enh:
        k = (e["enhancement"], e["hooked_object"], e["type"])
        if k not in seen:
            seen.add(k)
            uniq.append(e)
    out["enhancements_on_the_posting_path"] = uniq
    out["custom_enhancements"] = [e for e in uniq if e["custom"]]
    out["_why_this_leg_matters"] = (
        "a posting program is the seam between payroll and accounting, and a seam is where an "
        "organisation reaches for an enhancement. The custom enhancements on this path are "
        "usually the shortest description of what an installation actually changed")
    return out


def discover_resolved_posting(s, cx):
    """Part 7: what the posting ACTUALLY resolved to, from the documents rather than config.

    The account determination for payroll defeated a search through the configuration for a
    structural reason worth recording: T030-KTOSL is CHAR(3) and a payroll symbolic account
    is CHAR(4), so the FI account determination cannot hold one. They are two different
    keys that share a field name.

    The posting documents settle it. PPDIT carries, on one row, the FI TRANSACTION KEY
    (3 characters — HRA, HRC, HRF here) and the RESOLVED GL account. So the assignment is
    read from what happened rather than from what was configured, which is both easier and
    more truthful.
    """
    out = {"_why_config_search_fails": (
        "T030-KTOSL is CHAR(3); a payroll symbolic account is CHAR(4). They are different "
        "keys wearing the same field name, and joining them is impossible by construction"),
        "_where_the_answer_is": "PPDIT — the posting document items carry the key and the "
                                "resolved GL account on the same row"}
    try:
        rows = s.read("PPDIT", ["DOCNUM", "DOCLIN", "ITTYP", "BUKRS", "KTOSL", "HKONT"])
    except Exception as e:
        out["error"] = str(e)[:90]
        return out
    fwd, rev = collections.defaultdict(set), collections.defaultdict(set)
    for r in rows:
        fwd[r["KTOSL"]].add(r["HKONT"])
        rev[r["HKONT"]].add(r["KTOSL"])
    out["rows"] = len(rows)
    out["_source"] = ("the PURGED golden — runs that actually posted only. Read live from P01 "
                      "this returns the simulations too, and they are 89% of the table")
    out["transaction_keys"] = {k: sorted(v)[:8] for k, v in sorted(fwd.items())}
    out["keys_with_one_account"] = sum(1 for v in fwd.values() if len(v) == 1)
    out["keys_with_several"] = sum(1 for v in fwd.values() if len(v) > 1)
    out["accounts_with_one_key"] = sum(1 for v in rev.values() if len(v) == 1)
    out["accounts_total"] = len(rev)
    out["_reading"] = (
        "a transaction key fans out to several GL accounts while every GL account belongs to "
        "exactly one key. So the account is decided BEYOND the key — by the wage type, which "
        "is what the wage-type tables are for. The key is the FI bucket; the wage type picks "
        "the account inside it")
    return out


def main(argv):
    molga = argv[argv.index("--molga") + 1] if "--molga" in argv else "UN"
    out_path = os.path.join(ROOT, "brain_v2", "payroll_discovery.json")
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]

    import sqlite3
    cx = sqlite3.connect("file:%s?mode=ro" % GOLD, uri=True) if os.path.exists(GOLD) else None
    s = Session()

    print("A16 PAYROLL END-TO-END DISCOVERY   country grouping = %s" % molga)
    print("=" * 74)

    engine = discover_engine(s)
    custom_sc = {k: v for k, v in engine.items() if v["custom"]}
    print("\n1. THE ENGINE")
    print("   %d schemas, %d custom" % (len(engine), len(custom_sc)))
    for sc, v in sorted(custom_sc.items(), key=lambda x: -x[1]["active"])[:8]:
        print("      %-6s %3d steps (%d active) -> calls %s"
              % (sc, v["steps"], v["active"], ", ".join(v["calls"][:6])))

    logic = discover_logic(s)
    print("\n2. THE LOGIC")
    print("   %d rule lines over %d rules, %d custom"
          % (logic["rule_lines"], logic["rules"], logic["custom_rules"]))
    print("      largest custom: %s" % ", ".join("%s(%d)" % t for t in logic["largest_custom"][:8]))

    output = discover_output(s, molga)
    print("\n3. THE OUTPUT")
    print("   %d wage types, %d custom" % (output["wage_types"], output["custom"]))
    for stem, v in sorted(output["families_with_a_named_mechanism"].items()):
        print("      stem '%s': %d members, phrases %s" % (stem, v["members"], v["phrases"]))

    gates = discover_gates(s)
    print("\n4. THE GATES")
    print("   %d features, %d custom" % (gates["features"], gates["custom"]))
    print("      by structure: %s" % gates["custom_by_structure"][:6])

    md = discover_master_data(s, cx)
    print("\n5. THE MASTER DATA — maintained by hand, or fed?")
    if md["in_the_golden"]:
        print("   in the golden: %s" % ", ".join("%s (%d)" % (x["table"], x["rows"])
                                                 for x in md["in_the_golden"]))
    else:
        print("   NOT ONE payroll master-data table is in the golden")
    for log, per in md["maintenance"].items():
        for oc, v in list(per.items())[:4]:
            print("      %-8s %-14s manual %7d | no transaction %7d (%.1f%%)"
                  % (log, oc, v["with_a_transaction"], v["with_NO_transaction"],
                     v["pct_no_transaction"]))

    post = discover_posting(s)
    print("\n6. THE POSTING — how it reaches FI/FM, and who enhanced that path")
    for t in ("T52EL", "T52EK", "T030"):
        v = post.get(t) or {}
        print("      %-7s %s" % (t, v.get("rows", v.get("error"))))
    ce = post["custom_enhancements"]
    print("      enhancements on the posting path: %d, of which CUSTOM %d"
          % (len(post["enhancements_on_the_posting_path"]), len(ce)))
    for e in ce[:12]:
        print("         %-30s -> %-8s %s" % (e["enhancement"], e["type"], e["hooked_object"]))

    resolved = discover_resolved_posting(s, cx)
    print("\n7. THE RESOLVED POSTING — read from the documents, not the configuration")
    if "error" in resolved:
        print("      %s" % resolved["error"])
    else:
        print("      %d posiciones REALES | %d claves, %d abren a varias cuentas"
              % (resolved["rows"], len(resolved["transaction_keys"]),
                 resolved["keys_with_several"]))
        print("      %d of %d GL accounts belong to exactly ONE key"
              % (resolved["accounts_with_one_key"], resolved["accounts_total"]))
        for k, v in list(resolved["transaction_keys"].items())[:5]:
            print("         %-5s -> %s" % (k, ", ".join(v[:4])))

    rep = {"_algorithm": "A16 payroll_discovery.py", "posting": post,
           "resolved_posting": resolved, "country_grouping": molga,
           "engine": engine, "logic": logic, "output": output, "gates": gates,
           "master_data": md,
           "_the_premise": ("payroll logic is named after WHAT IT PRODUCES, so the discovery "
                            "runs from the output backwards as well as from the driver "
                            "forwards"),
           "summary": {"schemas": len(engine), "custom_schemas": len(custom_sc),
                       "rules": logic["rules"], "custom_rules": logic["custom_rules"],
                       "wage_types": output["wage_types"], "features": gates["features"],
                       "custom_features": gates["custom"],
                       "custom_enhancements_on_posting": len(post["custom_enhancements"]),
                       "rfc_calls": s.calls}}
    json.dump(rep, io.open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    remember(subject="payroll end to end", kind="INSTRUMENT", learned_by="A16_payroll_discovery",
             session=98,
             fact="%d schemas (%d custom), %d rules (%d custom), %d wage types, %d features (%d custom)"
                  % (len(engine), len(custom_sc), logic["rules"], logic["custom_rules"],
                     output["wage_types"], gates["features"], gates["custom"]),
             evidence=os.path.relpath(out_path, ROOT).replace("\\", "/"),
             implication=("the payroll engine is configuration and reads like data. Run this "
                          "before assuming any staff-cost calculation is unreachable"))
    print("\nwritten: %s  (%d RFC calls)"
          % (os.path.relpath(out_path, ROOT).replace("\\", "/"), s.calls))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
