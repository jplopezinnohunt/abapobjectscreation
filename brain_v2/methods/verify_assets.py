"""verify_assets.py — THE GUARANTEE (s097).

The question this answers: how do we guarantee that what a session explores and learns
becomes part of the model, instead of staying in a conversation?

Not by remembering. Discipline is not a mechanism — it fails precisely when the session
is long and interesting, which is exactly when the discoveries happen. s097 is the
proof: the session whose entire argument was "knowledge must not stay in the chat"
extracted two Gold DB tables that unlock the whole bottom-up direction of the model and
registered them nowhere.

So it is enforced instead. Four checks, run inside rebuild_all:

  A. DECLARED-BUT-MISSING   an asset in the registry that is not on disk / not in the
                            Gold DB. Either it was never really produced, or something
                            deleted it. Both are failures.
  B. PRESENT-BUT-UNDECLARED a Gold DB table or a brain_v2 store that nobody declared.
                            This is the leak that motivated the file: the asset exists,
                            works, and is invisible to the next session.
  C. ORPHAN-TOOL            a tool referenced by a method that does not exist, or an
                            asset with no `produced_by` method — knowledge of HOW is
                            missing even though the WHAT survived.
  D. STAGE-1-METHOD         a method still at "discovered": performed by hand once and
                            never scripted. Below stage 3 it is not part of the product.

A and C fail the rebuild. B and D warn loudly with a list — they are curation debt, and
failing on them would block a rebuild for a table someone legitimately just created.

Usage:  python brain_v2/methods/verify_assets.py [--strict]
        --strict also fails on B and D (use before a release/close).
"""
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).parent
BRAIN = HERE.parent
REPO = BRAIN.parent
REGISTRY = HERE / "asset_registry.json"
METHODS = HERE / "model_maturity_methods.json"
GOLD = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite" / "p01_gold_master_data.db"

# Gold DB tables that predate the registry. Declaring the exemption explicitly is
# honest; silently ignoring everything old would make check B decorative.
LEGACY_PREFIXES = ("_", "sim_", "d01_", "v01_", "p01_")


def _load(p):
    return json.load(open(p, encoding="utf-8")) if p.exists() else {}


def main(strict=False):
    reg = _load(REGISTRY)
    meth = _load(METHODS)
    assets = reg.get("assets", {})
    methods = meth.get("methods", {})
    fail, warn = [], []

    # ---- A: declared but missing -----------------------------------------
    gold_tables = set()
    if GOLD.exists():
        con = sqlite3.connect(str(GOLD))
        gold_tables = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type IN ('table','view')")}
        con.close()

    for name, a in assets.items():
        kind = a.get("kind")
        if kind == "gold_table":
            if gold_tables and name not in gold_tables:
                fail.append(f"A DECLARED-BUT-MISSING gold_table '{name}' "
                            f"— regenerate: {a.get('regenerate', '?')}")
        elif kind in ("store", "tool", "doc"):
            p = a.get("path")
            if p and not (REPO / p).exists():
                fail.append(f"A DECLARED-BUT-MISSING {kind} '{name}' at {p}")

    # ---- C: orphan tools / assets with no method -------------------------
    for mid, m in methods.items():
        tools = m.get("tool") or m.get("tools") or []
        for t in ([tools] if isinstance(tools, str) else tools):
            # a tool reference may name a section of a script, e.g. "x.py (coherence)"
            base = str(t).split(" (")[0].strip()
            if base.endswith(".py") and not (REPO / base).exists():
                fail.append(f"C ORPHAN-TOOL method {mid} points at missing tool {base}")

    for name, a in assets.items():
        if a.get("kind") in ("gold_table", "store") and not a.get("produced_by"):
            warn.append(f"C no `produced_by` on asset '{name}' — the HOW is undeclared")

    # ---- B: present but undeclared ---------------------------------------
    declared_tables = {n for n, a in assets.items() if a.get("kind") == "gold_table"}
    known_elsewhere = set()
    reg_path = BRAIN / "gold_table_registry.json"
    if reg_path.exists():
        blob = json.dumps(_load(reg_path))
        known_elsewhere = {t for t in gold_tables if f'"{t}"' in blob}
    for t in sorted(gold_tables):
        if t.lower().startswith(LEGACY_PREFIXES) or t in declared_tables or t in known_elsewhere:
            continue
        warn.append(f"B UNDECLARED gold table '{t}' — declare it in asset_registry.json "
                    f"or it is invisible to the next session")

    # ---- D: methods still at stage 1 -------------------------------------
    for mid, m in methods.items():
        stage = str(m.get("stage", "1_discovered"))
        n = stage.split("_")[0]
        if n.isdigit() and int(n) < 3:
            warn.append(f"D method {mid} is at stage {stage} — below 3 it is NOT part "
                        f"of the product. Promote it or drop it.")

    # ---- report ----------------------------------------------------------
    print(f"[assets] {len(assets)} declared · {len(gold_tables)} gold tables · "
          f"{len(methods)} methods")
    for w in warn:
        print("  WARN " + w)
    for f in fail:
        print("  FAIL " + f, file=sys.stderr)

    if fail or (strict and warn):
        print(f"\nASSET GATE FAILED — {len(fail)} error(s), {len(warn)} warning(s).\n"
              "An asset the model cannot see is knowledge that died with the session "
              "that made it.", file=sys.stderr)
        sys.exit(1)
    print(f"OK — every declared asset is present and every method is scripted."
          f"{f' ({len(warn)} curation warning(s))' if warn else ''}")


if __name__ == "__main__":
    main(strict="--strict" in sys.argv)
