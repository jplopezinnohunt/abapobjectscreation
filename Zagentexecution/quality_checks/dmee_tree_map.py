#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dmee_tree_map.py -- the map of EVERY live DMEE tree: structure + mapping + EXITS.

WHY THIS EXISTS
---------------
Session 2026-08-18/19: I handed over a change spec for the CGI CdtrAgt address
built on the node MAPPING alone, and the user stopped me twice on the same
thing -- "estan los codigos de las extensiones para cada elemento, y eso
deberias conocerlo para todos". Both times he was right, and the second time
the miss was bigger than the first:

  1. I read ONE exit column. Six things decide a node's content -- MP_IF_TP,
     MP_SC_TAB/FLD, MP_CONST, MP_EXIT_FUNC, CK_EXIT_FUNC, CV_RULE. A node can
     carry a mapping AND an exit (screenshot: CdtrAgt/BIC has FPAYH-ZSWIF *and*
     FI_CGI_DMEE_EXIT_W_BADI). The exit wins. Reading the mapping alone tells
     you what SAP would do if nobody had overridden it. In /CGI_XML_CT_UNESCO
     that is 392 of 628 nodes -- 62% of the tree was invisible to me.
  2. I analysed 3 trees. REGUT says SIX formats are live in 2026. The Italian
     ICTP family -- including /SEPA_CT_ICTP_ISO_EXTRASEPA, the cross-border one
     and therefore the one Nov-2026 hits hardest -- was never looked at.

The lesson is not "check the exits". It is that a per-question hand probe
re-derives a partial picture every time and silently omits whatever the
question did not ask about. So this is a MAP, not an answer: it walks every
live tree end to end and prints what is there, whether or not anyone asked.

WHAT IT REPORTS
---------------
  * which formats are actually live      (REGUT.DTFOR, measured -- not assumed)
  * every PstlAdr subtree in each        (child order = XML order)
  * per node: mapping, constant, MP exit, CK exit, conversion rule, conditions
  * every exit function the tree uses, and where -- ours vs delivered
  * three defect classes, flagged:
      ORDER   children violate the ISO 20022 PostalAddress6 xs:sequence
      HYBRID  structured tag and AdrLine in the same PstlAdr
      NOV26   no structured TwnNm/Ctry -- legal today, rejected from Nov-2026

USAGE
    python dmee_tree_map.py                  # D01 trees, live formats from P01
    python dmee_tree_map.py --sys P01
    python dmee_tree_map.py --tree /SEPA_CT_ICTP_ISO_EXTRASEPA
    python dmee_tree_map.py --all-trees      # do not filter to live formats
    python dmee_tree_map.py --json out.json

Read-only. Two RFC_READ_TABLE reads per system, no ROWSKIPS (P01 rejects it).
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "mcp-backend-server-python"))

# ISO 20022 PostalAddress6 is an xs:sequence -- this order IS the contract.
# Ctry is second-to-last. Emitting it first is the 2026-07-21 bank rejection.
ISO_ORDER = ["AdrTp", "Dept", "SubDept", "StrtNm", "BldgNb", "PstCd",
             "TwnNm", "CtrySubDvsn", "Ctry", "AdrLine"]
STRUCTURED = {"Dept", "SubDept", "StrtNm", "BldgNb", "PstCd", "TwnNm",
              "CtrySubDvsn"}

NODE_F = ["TREE_ID", "VERSION", "NODE_ID", "TECH_NAME", "REF_NAME", "PARENT_ID",
          "FIRSTCHILD_ID", "BROTHER_ID", "NODE_TYPE", "MP_IF_TP", "MP_SC_TAB",
          "MP_SC_FLD", "MP_SC_NODE", "MP_CONST", "CV_RULE", "MP_EXIT_FUNC",
          "CK_EXIT_FUNC", "MP_SELECTION", "LEV"]
COND_F = ["TREE_ID", "VERSION", "NODE_ID", "COND_NUMBER", "ARG1_TAB", "ARG1_FLD",
          "ARG1_CONST", "ARG2_TAB", "ARG2_FLD", "ARG2_CONST", "OPERATOR",
          "LINK_OPERATOR"]
REGUT_F = ["LAUFD", "DTFOR", "ZBUKR", "BANKS"]


def exit_owner(fn):
    """An exit is OURS if we can change it. SAP- and Citi-delivered we cannot."""
    if fn.startswith(("Z", "Y")):
        return "CUSTOM"          # ours -- source belongs in extracted_code/
    if fn.startswith("/CITIPMW/"):
        return "CITI"            # bank add-on, delivered
    return "SAP"                 # standard (FI_CGI_DMEE_EXIT_W_BADI, DMEE_EXIT_*)


def read_table(conn, table, fields, where=""):
    kw = dict(QUERY_TABLE=table, DELIMITER="|",
              FIELDS=[{"FIELDNAME": f} for f in fields], ROWCOUNT=0)
    if where:
        kw["OPTIONS"] = [{"TEXT": where}]
    r = conn.call("RFC_READ_TABLE", **kw)
    return [dict(zip(fields, [c.strip() for c in d["WA"].split("|")]))
            for d in r["DATA"]]


def live_formats(since="20240101"):
    """What is ACTUALLY used, from the media table -- never from assumption."""
    from rfc_helpers import get_connection
    c = get_connection("P01")
    try:
        rows = read_table(c, "REGUT", REGUT_F, "LAUFD >= '%s'" % since)
    finally:
        c.close()
    out = {}
    for x in rows:
        f = x["DTFOR"]
        if not f:
            continue
        d = out.setdefault(f, {"total": 0, "by_year": collections.Counter(),
                               "countries": set()})
        d["total"] += 1
        d["by_year"][x["LAUFD"][:4]] += 1
        if x["BANKS"]:
            d["countries"].add(x["BANKS"])
    return out


def load_trees(system):
    from rfc_helpers import get_connection
    c = get_connection(system)
    try:
        nodes = read_table(c, "DMEE_TREE_NODE", NODE_F)
        conds = read_table(c, "DMEE_TREE_COND", COND_F)
    finally:
        c.close()
    return nodes, conds


def pick_version(versions):
    """V001 = maintenance (what you edit). V000 = active. V002+ = backup."""
    return "001" if "001" in versions else sorted(versions)[0]


def children(src, parent):
    """Walk FIRSTCHILD then the BROTHER chain. Sibling order IS the XML order."""
    out, cur, seen = [], src.get(parent["FIRSTCHILD_ID"]), set()
    while cur and cur["NODE_ID"] not in seen:
        seen.add(cur["NODE_ID"])
        out.append(cur)
        cur = src.get(cur["BROTHER_ID"])
    return out


def node_path(src, nid):
    o, cur, k = [], src.get(nid), 0
    while cur and k < 40:
        o.append(cur["TECH_NAME"])
        cur = src.get(cur["PARENT_ID"])
        k += 1
    p = " > ".join(reversed(o))
    return p.replace("Document > CstmrCdtTrfInitn > PmtInf > ", "")


def source_of(n):
    """Everything that can decide this node's value. The exit outranks the map."""
    bits = []
    if n["MP_CONST"]:
        bits.append("const %r" % n["MP_CONST"])
    if n["MP_SC_TAB"]:
        bits.append("%s-%s" % (n["MP_SC_TAB"], n["MP_SC_FLD"]))
    if n["MP_SC_NODE"]:
        bits.append("node %s" % n["MP_SC_NODE"])
    if n["MP_EXIT_FUNC"]:
        bits.append("EXIT %s [%s]" % (n["MP_EXIT_FUNC"],
                                      exit_owner(n["MP_EXIT_FUNC"])))
    if n["CK_EXIT_FUNC"]:
        bits.append("CHECK %s [%s]" % (n["CK_EXIT_FUNC"],
                                       exit_owner(n["CK_EXIT_FUNC"])))
    if n["CV_RULE"]:
        bits.append("cv %r" % n["CV_RULE"])
    return bits or ["(vacio)"]


def audit_pstladr(src, parent):
    """The three defect classes. Returns list of (CLASS, message)."""
    kids = children(src, parent)
    names = [k["TECH_NAME"] for k in kids]
    seq = [n for n in names if n in ISO_ORDER]
    idx = [ISO_ORDER.index(n) for n in seq]
    out = []
    if idx != sorted(idx):
        want = [n for n in ISO_ORDER if n in set(seq)]
        out.append(("ORDER", "orden ISO roto: %s -> debe ser %s"
                    % (" ".join(seq), " ".join(want))))
    present = set(names)
    if (present & STRUCTURED) and "AdrLine" in present:
        out.append(("HYBRID", "estructurado + AdrLine en el mismo PstlAdr"))
    for need in ("TwnNm", "Ctry"):
        if need not in present:
            out.append(("NOV26", "sin <%s> estructurado" % need))
    return out


def render_conditions(rows):
    if not rows:
        return ""
    parts = []
    for x in sorted(rows, key=lambda z: int(z["COND_NUMBER"] or 0)):
        a1 = x["ARG1_CONST"] or ("%s-%s" % (x["ARG1_TAB"], x["ARG1_FLD"])).strip("-")
        a2 = x["ARG2_CONST"] or ("%s-%s" % (x["ARG2_TAB"], x["ARG2_FLD"])).strip("-")
        parts.append(("%s %s %s %s" % (x["LINK_OPERATOR"], a1, x["OPERATOR"], a2)).strip())
    return "  IF " + " ".join(parts)


def report(system, only_tree=None, all_trees=False, dump=None):
    nodes, conds = load_trees(system)
    by_tree = collections.defaultdict(list)
    for n in nodes:
        by_tree[n["TREE_ID"]].append(n)
    cond_ix = collections.defaultdict(list)
    for c in conds:
        cond_ix[(c["TREE_ID"], c["VERSION"], c["NODE_ID"])].append(c)

    usage = {}
    if only_tree:
        targets = [only_tree]
    elif all_trees:
        targets = sorted(by_tree)
    else:
        usage = live_formats()
        targets = sorted(usage, key=lambda f: -usage[f]["total"])

    print("=" * 100)
    print("MAPA DMEE -- sistema %s -- %d arboles en total, %d bajo analisis"
          % (system, len(by_tree), len(targets)))
    print("=" * 100)
    if usage:
        print("\nFORMATOS VIVOS (medido en REGUT P01, 2024+, campo DTFOR):")
        print("  %-38s %7s %7s %7s %7s   %s"
              % ("FORMATO (= TREE_ID)", "total", "2024", "2025", "2026", "paises"))
        for f in targets:
            d = usage[f]
            print("  %-38s %7d %7d %7d %7d   %s"
                  % (f, d["total"], d["by_year"]["2024"], d["by_year"]["2025"],
                     d["by_year"]["2026"], ",".join(sorted(d["countries"]))))

    result, totals = {}, collections.Counter()
    for tid in targets:
        rows = by_tree.get(tid)
        if not rows:
            print("\n\n%s\n!! %s -- NO EXISTE en %s" % ("#" * 100, tid, system))
            continue
        versions = sorted({r["VERSION"] for r in rows})
        v = pick_version(versions)
        # index PER VERSION: NODE_IDs repeat across versions, and one dict for
        # all of them silently builds a cross-version chimera (burned 2026-08-18)
        src = {r["NODE_ID"]: r for r in rows if r["VERSION"] == v}

        exits = collections.Counter()
        for n in src.values():
            for fld in ("MP_EXIT_FUNC", "CK_EXIT_FUNC"):
                if n[fld]:
                    exits[n[fld]] += 1

        print("\n\n%s\n# %s   V%s   %d nodos   versiones=%s"
              % ("#" * 100, tid, v, len(src), ",".join(versions)))
        print("#   exits: %d nodos, %d funciones distintas"
              % (sum(exits.values()), len(exits)))
        for fn, k in exits.most_common():
            print("#     %4dx  %-38s %s" % (k, fn, exit_owner(fn)))

        tre = {"version": v, "versions": versions, "nodes": len(src),
               "exits": dict(exits), "pstladr": []}
        pstl = [n for n in src.values() if n["TECH_NAME"] == "PstlAdr"]
        print("#   PstlAdr: %d" % len(pstl))
        for p in sorted(pstl, key=lambda z: node_path(src, z["NODE_ID"])):
            flags = audit_pstladr(src, p)
            for cls, _ in flags:
                totals[cls] += 1
            tag = "  ".join("[%s]" % c for c, _ in flags) or "[OK]"
            print("\n  %s   %s" % (node_path(src, p["NODE_ID"]), tag))
            print("     padre %s%s" % (p["NODE_ID"],
                  render_conditions(cond_ix.get((tid, v, p["NODE_ID"]), []))))
            for cls, msg in flags:
                print("     !! %-7s %s" % (cls, msg))
            for i, k in enumerate(children(src, p), 1):
                print("     %2d. %-26s %-14s %s%s"
                      % (i, k["TECH_NAME"], k["NODE_ID"], " | ".join(source_of(k)),
                         render_conditions(cond_ix.get((tid, v, k["NODE_ID"]), []))))
            tre["pstladr"].append({
                "path": node_path(src, p["NODE_ID"]), "node_id": p["NODE_ID"],
                "flags": [{"class": c, "msg": m} for c, m in flags],
                "children": [{"pos": i, "tag": k["TECH_NAME"],
                              "node_id": k["NODE_ID"], "source": source_of(k),
                              "mp_exit": k["MP_EXIT_FUNC"],
                              "ck_exit": k["CK_EXIT_FUNC"],
                              "cv_rule": k["CV_RULE"]}
                             for i, k in enumerate(children(src, p), 1)]})
        result[tid] = tre

    print("\n\n%s\nRESUMEN: %s" % ("=" * 100,
          "  ".join("%s=%d" % (k, n) for k, n in sorted(totals.items()))
          or "sin hallazgos"))
    if dump:
        json.dump({"system": system,
                   "usage": {k: {"total": v["total"],
                                 "countries": sorted(v["countries"])}
                             for k, v in usage.items()},
                   "trees": result}, open(dump, "w"), indent=1)
        print("JSON -> %s" % dump)
    return totals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sys", default="D01")
    ap.add_argument("--tree")
    ap.add_argument("--all-trees", action="store_true")
    ap.add_argument("--json")
    a = ap.parse_args()
    report(a.sys, a.tree, a.all_trees, a.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
