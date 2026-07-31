"""attach_object_text.py — give every executed object its human-readable TEXT (s097).

USER POINT: "a cada reporte / transacción le puedes agregar el texto, eso ayudará".

Correct, and cheap: the texts are already in the Gold DB. Today the frontier is 3,667
object NAMES. Nobody can look at `RKPDEMO2` and tell what it is, so:

  * the unclassified tail cannot be triaged by eye,
  * every argument about a classification becomes archaeology,
  * and a misclassification is invisible — `RKPDEMO2` sat under Controlling for months
    while being a Project System cost report, and the name gave nothing away.

With the text attached, the classifier's mistakes become obvious at a glance. That is the
whole value: it does not improve the classification, it makes the classification
REVIEWABLE.

Sources, in priority order per object:
    d01_tstct   transaction texts (99,566 rows, English)
    d01_tstc    transaction -> program, so a report inherits its transaction's text
    tadir_obj   at minimum, the development package and application component

Emits: brain_v2/executed_objects_text.json, and enriches the frontier worklist.
Run: python process_mining/attach_object_text.py
"""
import json
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "brain_v2"))
sys.path.insert(0, str(REPO / "Zagentexecution" / "mcp-backend-server-python"))
from component_map import component_of_package  # noqa: E402

GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"
EMAP = REPO / "brain_v2" / "executed_objects_domain_map.json"
OUT = REPO / "brain_v2" / "executed_objects_text.json"


def main():
    con = sqlite3.connect(f"file:{GOLD}?mode=ro", uri=True)
    have = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}

    tcode_text, prog_of_tcode, tcode_of_prog = {}, {}, {}
    if "d01_tstct" in have:
        for tc, tx in con.execute("SELECT TCODE, TTEXT FROM d01_tstct WHERE SPRSL='E'"):
            if tc and tx:
                tcode_text[tc.strip()] = tx.strip()
    if "d01_tstc" in have:
        for tc, pg in con.execute("SELECT TCODE, PGMNA FROM d01_tstc"):
            tc, pg = (tc or "").strip(), (pg or "").strip()
            if tc and pg:
                prog_of_tcode[tc] = pg
                tcode_of_prog.setdefault(pg, tc)

    pkg_of = {}
    for tbl in ("tadir_obj", "tadir_prog"):
        if tbl in have:
            q = ("SELECT OBJ_NAME, DEVCLASS FROM " + tbl)
            for o, dc in con.execute(q):
                o = (o or "").strip()
                if o and o not in pkg_of:
                    pkg_of[o] = (dc or "").strip()
    con.close()

    emap = json.load(open(EMAP, encoding="utf-8"))
    enriched, resolved, unresolved = {}, 0, 0

    for dom, objs in emap.get("top_objects_by_domain", {}).items():
        for o in objs:
            name = o["object"]
            if name in enriched:
                continue
            text = tcode_text.get(name)
            via = "transaction text" if text else None
            if not text:
                # a report inherits the text of the transaction that launches it
                tc = tcode_of_prog.get(name)
                if tc and tc in tcode_text:
                    text, via = tcode_text[tc], f"via transaction {tc}"
            pkg = pkg_of.get(name)
            comp = component_of_package(pkg) if pkg else None
            if not text and comp:
                text, via = f"(no text) component {comp}", "application component"
            enriched[name] = {
                "text": text, "text_source": via, "package": pkg,
                "component": comp, "domain": dom,
                "execs": o.get("execs"), "users": o.get("users"),
                "channel": o.get("channel"),
            }
            if text:
                resolved += 1
            else:
                unresolved += 1

    frontier = [dict(name=k, **v) for k, v in enriched.items()
                if v["domain"] == "Uncatalogued"]
    frontier.sort(key=lambda x: -(x.get("execs") or 0))

    out = {
        "_generated_by": "process_mining/attach_object_text.py",
        "_why": ("the frontier was 3,667 NAMES. A name cannot be triaged. With the text "
                 "attached the classifier's mistakes become visible at a glance — this does "
                 "not improve the classification, it makes it REVIEWABLE."),
        "coverage": {"objects": len(enriched), "with_text": resolved,
                     "without_text": unresolved,
                     "pct": round(100.0 * resolved / max(1, len(enriched)), 1)},
        "frontier_readable": frontier[:60],
        "objects": enriched,
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    c = out["coverage"]
    print(f"wrote {OUT}")
    print(f"  {c['with_text']}/{c['objects']} objects now carry a readable text ({c['pct']}%)")
    print("\n  THE FRONTIER, now readable — top unclassified by volume:")
    for f in frontier[:12]:
        t = (f.get("text") or "??? no text, no component — genuinely opaque")[:58]
        print(f"    {f['name']:34s} {(f.get('execs') or 0):>9,d}  {t}")


if __name__ == "__main__":
    main()
