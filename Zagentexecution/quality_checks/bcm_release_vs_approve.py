#!/usr/bin/env python3
"""
bcm_release_vs_approve.py

Side-by-side cross of WHO VALIDATES/RELEASES (Step 1, BNK_INI rule 90000005)
vs WHO SIGNS/COMMITS (Step 2, BNK_COM rule 90000004), broken down by
company (entity) and amount band.

Why: BCM batch release is a mandatory 2-step control (validate THEN sign, by
two different people). The two steps select people from SEPARATE responsibility
nodes whose amount bands do NOT always line up. This tool pairs them by entity
and overlapping amount range so you can see, for any (company, amount), who can
release on Step 1 and who can sign on Step 2 — and where a band has a validator
but no signer (or vice-versa, or a missing-role person).

Pure read of the Gold DB (no SAP call). Inputs already extracted live from P01:
  - bcm_node_selection_criteria  (node -> ZBUKR + MAXPAYAMT_RULECURR band + RULE_ID)
  - bcm_signatory_responsibility (node -> rule_number 90000004/05 + STEXT)
  - bcm_node_agent_role_check    (node x ACTIVE agent + has_bnk_app flag)

Output: rebuilds Gold DB table bcm_release_vs_approve (one row per
entity x band x (ini_node, com_node)) and prints the matrix.

Usage:
    python bcm_release_vs_approve.py                 # all entities
    python bcm_release_vs_approve.py --entity UBO    # one entity
    python bcm_release_vs_approve.py --golden <path>
"""

# --- self-declaration, read by quality_checks/run_all.py -------------------
# An undeclared script is reported as UNCLASSIFIED and fails the runner loudly:
# a central registry is a list someone forgets to update.
QUALITY_CHECK = {
    "tier": "analysis",      # gate | live | analysis | quarantined
    "needs": "gold_db",    # gold_db | rfc_p01 | files
    "what": "side-by-side cross, produces a report",
}
# --------------------------------------------------------------------------

import argparse
import io
import os
import sqlite3
import sys
from datetime import date

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.join(HERE, "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")

INI_RULE = "90000005"   # Step 1 — Approve / Validate / Release
COM_RULE = "90000004"   # Step 2 — Sign / Commit
ENTITIES = ("UBO", "UIS", "IIEP", "UIL", "UNES")


def fnum(x):
    try:
        return float(str(x).replace(",", "")) if str(x).strip() else None
    except ValueError:
        return None


def band_label(lo, hi):
    def h(v):
        if v is None:
            return "?"
        if v >= 1e9:
            return "∞"
        if v >= 1e6:
            return f"{v/1e6:.0f}M".replace(".0M", "M")
        if v >= 1e3:
            return f"{v/1e3:.0f}K".replace(".0K", "K")
        return f"{v:.0f}"
    return f"{h(lo)}–{h(hi)}"


def overlap(a, b):
    """Two [lo,hi) bands overlap (touching endpoints do NOT count as overlap)."""
    return a[0] < b[1] and b[0] < a[1]


def main():
    ap = argparse.ArgumentParser(description="BCM Step1(validate) vs Step2(sign) side-by-side, by company x amount")
    ap.add_argument("--entity", help="filter to one entity (UBO/UIS/IIEP/UIL/UNES)")
    ap.add_argument("--golden", default=GOLDEN, help="path to the Gold DB")
    ap.add_argument("--system", default="P01")
    args = ap.parse_args()

    ts = date.today().strftime("%Y-%m-%dT00:00:00")
    db = sqlite3.connect(args.golden)
    c = db.cursor()

    # 1) criteria pivot: node -> {zbukr, lo, hi, rule_id}
    crit = {}
    for node, field, lo, hi in c.execute(
            "SELECT node_objid,field,expr_low,expr_high FROM bcm_node_selection_criteria"):
        d = crit.setdefault(node, {})
        if field == "ZBUKR":
            d["zbukr"] = (lo or hi or "").strip()
        elif field.startswith("MAXPAYAMT"):
            d["lo"], d["hi"] = fnum(lo), fnum(hi)
        elif field == "RULE_ID":
            d["rule_id"] = (lo or hi or "").strip()

    # 2) responsibility: node -> rule + stext
    resp = {objid: (rule, stext) for objid, rule, stext
            in c.execute("SELECT objid,rule_number,stext FROM bcm_signatory_responsibility")}

    # 3) active people per node (+ role flag)
    people = {}
    for oid, person, un, has in c.execute(
            "SELECT ry_objid,person,uname,has_bnk_app FROM bcm_node_agent_role_check ORDER BY person"):
        people.setdefault(oid, []).append((person.strip(), un, has))

    def node_info(oid):
        rule, stext = resp.get(oid, ("", ""))
        d = crit.get(oid, {})
        ppl = people.get(oid, [])
        return {
            "objid": oid, "rule": rule, "stext": stext,
            "zbukr": d.get("zbukr", ""), "lo": d.get("lo"), "hi": d.get("hi"),
            "rule_id": d.get("rule_id", ""),
            "n": len(ppl), "miss": sum(1 for _, _, h in ppl if h != "Y"),
            "people": ppl,
        }

    def ppl_csv(node):
        return ", ".join(
            (p.split()[0] if p else "?") + ("" if h == "Y" else " ✗")
            for p, _, h in node["people"]) or "(none active)"

    # rebuild output table
    c.execute("DROP TABLE IF EXISTS bcm_release_vs_approve")
    c.execute("""CREATE TABLE bcm_release_vs_approve(
        entity TEXT, band_low REAL, band_high REAL, band_label TEXT,
        ini_node TEXT, ini_stext TEXT, ini_n INT, ini_miss INT, ini_people TEXT,
        com_node TEXT, com_stext TEXT, com_n INT, com_miss INT, com_people TEXT,
        note TEXT, source_system TEXT, generated_at TEXT)""")

    out_rows = []
    targets = [args.entity.upper()] if args.entity else ENTITIES
    for ent in targets:
        ini = [node_info(o) for o, (r, _) in resp.items() if r == INI_RULE and crit.get(o, {}).get("zbukr") == ent]
        com = [node_info(o) for o, (r, _) in resp.items() if r == COM_RULE and crit.get(o, {}).get("zbukr") == ent]
        ini_active = sorted([n for n in ini if n["n"] > 0], key=lambda n: (n["lo"] or 0))
        com_active = sorted([n for n in com if n["n"] > 0], key=lambda n: (n["lo"] or 0))

        rows = []
        if not com_active:
            # Step 2 is done outside SAP (UNES → Coupa, Process 4) — list validators only
            for inn in ini_active:
                rows.append((inn, None, "Step-2 sign done in Coupa (Process 4) — no SAP signer in 90000004"))
        else:
            paired_ini = set()
            for cn in com_active:
                matched = [inn for inn in ini_active if overlap((inn["lo"], inn["hi"]), (cn["lo"], cn["hi"]))]
                if not matched:
                    rows.append((None, cn, "signer band has NO active SAP validator (Step 1 gap)"))
                    continue
                for inn in matched:
                    paired_ini.add(inn["objid"])
                    note = ""
                    if inn["hi"] is not None and cn["hi"] is not None and inn["hi"] < cn["hi"]:
                        note = f"⚠ validator tops at {band_label(0, inn['hi']).split('–')[1]}, signer at {band_label(0, cn['hi']).split('–')[1]} → no SAP validator above that"
                    if inn["people"] == cn["people"]:
                        note = (note + " · " if note else "") + "same people validate & sign (SoD relies on 2 distinct users at run time)"
                    rows.append((inn, cn, note))
            for inn in ini_active:
                if inn["objid"] not in paired_ini:
                    rows.append((inn, None, "validates but no overlapping signer band"))

        # emit
        for inn, cn, note in rows:
            lo = (inn or cn)["lo"]
            hi = (inn or cn)["hi"]
            out_rows.append((
                ent, lo, hi, band_label(lo, hi),
                inn["objid"] if inn else "", inn["stext"] if inn else "", inn["n"] if inn else 0,
                inn["miss"] if inn else 0, ppl_csv(inn) if inn else "—",
                cn["objid"] if cn else "COUPA", cn["stext"] if cn else "(Coupa / no SAP signer)",
                cn["n"] if cn else 0, cn["miss"] if cn else 0, ppl_csv(cn) if cn else "—",
                note, args.system, ts,
            ))

    c.executemany("INSERT INTO bcm_release_vs_approve VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", out_rows)
    db.commit()

    # print
    print(f"BCM Step1 (validate/release, {INI_RULE}) vs Step2 (sign/commit, {COM_RULE}) — {args.system} — {ts[:10]}")
    print("=" * 110)
    cur_ent = None
    for r in out_rows:
        (ent, lo, hi, lbl, ino, ist, inn_, imiss, ipl, cno, cst, cn_, cmiss, cpl, note, *_) = r
        if ent != cur_ent:
            print(f"\n### {ent}")
            cur_ent = ent
        print(f"  [{lbl:>9}]  Step1 {ino or '—':<8} ({inn_}p{('/'+str(imiss)+'✗') if imiss else ''}): {ipl}")
        print(f"  {'':>11}  Step2 {cno:<8} ({cn_}p{('/'+str(cmiss)+'✗') if cmiss else ''}): {cpl}")
        if note:
            print(f"  {'':>11}  ↳ {note}")
    print(f"\npersisted {len(out_rows)} rows -> bcm_release_vs_approve (Gold DB)")
    db.close()


if __name__ == "__main__":
    main()
