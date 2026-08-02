"""ALGORITHM A13 — CUSTOM FIELD HARVEST.

WHAT IT ANSWERS
    "Where has this installation already extended the standard data model, and what does
    each extension carry?" — including the fields that are empty today.

WHY THE EMPTY ONES MATTER MOST
    A custom field is an extension point that someone already fought for: it exists in the
    dictionary, it survived every upgrade, and it is already in the tables a future design
    would write to. An empty one is not dead weight — it is a slot with a name, a type and
    usually a half-finished intent still visible in the code that references it. Designing
    a new solution without knowing them means either rebuilding what is there or colliding
    with it.

WHERE IT LOOKS, AND WHY BOTH
    SOURCE tells you a field EXISTS and how it is USED — the assignment, the check, the
    extractor that fills it. The GOLDEN tells you whether anything is IN it. Neither alone
    is enough: a field can be referenced everywhere and be empty, or be full and referenced
    nowhere. The pairing is the finding.

    And the third state is the one that bites: a field present in the dictionary and ABSENT
    FROM OUR EXTRACT. That is not "empty" — it is unmeasured, and reporting it as empty
    would be a confident wrong answer. It is reported as NOT_EXTRACTED, with the table to
    re-pull.

USAGE
    python process_mining/harvest_custom_fields.py [--out custom_fields.json]
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
from algorithm_memory import remember  # noqa: E402

CORPORA = ["extracted_sap_p01", "extracted_code", "extracted_sap"]
GOLD = os.path.join(ROOT, "Zagentexecution", "sap_data_extraction", "sqlite",
                    "p01_gold_master_data.db")

# TABLE-FIELD or ALIAS~FIELD where the field carries a customer namespace prefix.
USE = re.compile(r"\b([A-Z][A-Z0-9_]{1,29})[-~]((?:YY|ZZ)[A-Z0-9_]+)\b", re.I)
# A custom field used in a WHERE clause or a SELECT list carries NO table prefix, so the
# pattern above misses it entirely. The self-test that caught this: ZZFIX_RATE is known to
# gate the whole budget-rate mechanism and did not appear in the first run. Anything with a
# customer namespace is harvested, even when its owner cannot be attributed.
BARE = re.compile(r"(?<![A-Z0-9_~-])((?:YY|ZZ)[A-Z0-9_]{2,})(?![A-Z0-9_])", re.I)
# A typed declaration tells us the data element, which is where the intent usually hides.
TYPED = re.compile(r"\b((?:EV_|IV_|CV_)?(?:YY|ZZ)[A-Z0-9_]+)\s+TYPE\s+([A-Z][A-Z0-9_/]+)", re.I)
# Working-area prefixes: LS_, LT_, W_, S_, I_ etc. name a STRUCTURE, not a table.
LOCAL = re.compile(r"^(LS_|LT_|LV_|L_|W_|WA_|S_|T_|IT_|ET_|ES_|GS_|GT_|MT_|MS_|XB)", re.I)


def scan():
    """Every (owner, field) pair the source mentions, with where it was seen."""
    uses = collections.defaultdict(list)
    types = {}
    for corpus in CORPORA:
        base = os.path.join(ROOT, corpus)
        if not os.path.isdir(base):
            continue
        for dirpath, _, files in os.walk(base):
            for fn in files:
                if not fn.lower().endswith((".abap", ".txt")):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    src = io.open(p, encoding="utf-8", errors="replace").read()
                except OSError:
                    continue
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                for i, line in enumerate(src.splitlines(), 1):
                    for owner, field in USE.findall(line):
                        uses[(owner.upper(), field.upper())].append(
                            {"where": "%s:%d" % (rel, i), "code": line.strip()[:150]})
                    attributed = {f.upper() for _, f in USE.findall(line)}
                    for field in BARE.findall(line):
                        fu = field.upper()
                        if fu in attributed:
                            continue
                        uses[("(UNATTRIBUTED)", fu)].append(
                            {"where": "%s:%d" % (rel, i), "code": line.strip()[:150]})
                    for field, dtel in TYPED.findall(line):
                        types.setdefault(field.upper().lstrip("EIC").lstrip("_"), dtel.upper())
    return uses, types


def population(cx, table, field):
    """Three states, and the third is the one that matters: NOT_EXTRACTED is not EMPTY."""
    if cx is None:
        return {"state": "NO_GOLDEN"}
    row = cx.execute("SELECT name FROM sqlite_master WHERE type='table' AND lower(name)=lower(?)",
                     (table,)).fetchone()
    if not row:
        return {"state": "TABLE_NOT_EXTRACTED",
                "_meaning": "the table is not in the golden, so the field is UNMEASURED — not empty"}
    real = row[0]
    cols = {c[1].upper(): c[1] for c in cx.execute('PRAGMA table_info("%s")' % real)}
    if field.upper() not in cols:
        return {"state": "FIELD_NOT_EXTRACTED", "table_in_golden": real,
                "_meaning": ("the table was extracted WITHOUT this column, so the field is "
                             "UNMEASURED. Re-pull the table with all fields to measure it")}
    col = cols[field.upper()]
    n = cx.execute('SELECT count(*) FROM "%s"' % real).fetchone()[0]
    if not n:
        return {"state": "TABLE_EMPTY", "rows": 0}
    f = cx.execute('SELECT count(*) FROM "%s" WHERE "%s" IS NOT NULL AND trim("%s")<>%s'
                   % (real, col, col, "''")).fetchone()[0]
    d = cx.execute('SELECT count(DISTINCT trim("%s")) FROM "%s"' % (col, real)).fetchone()[0]
    ex = [r[0] for r in cx.execute(
        'SELECT DISTINCT trim("%s") FROM "%s" WHERE trim("%s")<>%s LIMIT 4'
        % (col, real, col, "''"))]
    return {"state": "POPULATED" if f else "EMPTY_IN_DATA", "rows": n, "filled": f,
            "filled_pct": round(100.0 * f / n, 1), "distinct": d, "examples": ex}


def main(argv):
    out_path = os.path.join(ROOT, "brain_v2", "custom_fields.json")
    if "--out" in argv:
        out_path = argv[argv.index("--out") + 1]
    cx = sqlite3.connect("file:%s?mode=ro" % GOLD, uri=True) if os.path.exists(GOLD) else None

    uses, types = scan()
    recs = []
    for (owner, field), hits in sorted(uses.items()):
        bare = owner == "(UNATTRIBUTED)"
        is_local = bool(LOCAL.match(owner)) or bare
        rec = {
            "field": field, "owner": owner,
            "owner_kind": ("UNATTRIBUTED_SEEN_IN_SQL" if bare else
                           "WORK_AREA_OR_STRUCTURE" if is_local else "TABLE_OR_STRUCTURE"),
            "data_element": types.get(field),
            "references": len(hits),
            "seen_in": sorted({h["where"].rsplit(":", 1)[0] for h in hits})[:5],
            "evidence": hits[:3],
        }
        # Only a real table name is worth measuring; a work area is a copy of something else.
        rec["population"] = ({"state": "NOT_A_TABLE"} if is_local
                             else population(cx, owner, field))
        recs.append(rec)

    by_state = collections.Counter(r["population"]["state"] for r in recs)
    tables_to_repull = sorted({r["owner"] for r in recs
                               if r["population"]["state"] in ("FIELD_NOT_EXTRACTED",
                                                               "TABLE_NOT_EXTRACTED")})

    print("A13 CUSTOM FIELD HARVEST")
    print("=" * 74)
    print("  %d distinct (owner, field) pairs across %d corpora" % (len(recs), len(CORPORA)))
    print("  states: %s" % dict(by_state))
    print()
    print("  ON REAL TABLES — what is measurable:")
    for r in recs:
        st = r["population"]["state"]
        if r["owner_kind"] != "TABLE_OR_STRUCTURE" or st == "NOT_A_TABLE":
            continue
        extra = ""
        if st == "POPULATED":
            extra = "%.1f%% of %d rows, %d distinct" % (
                r["population"]["filled_pct"], r["population"]["rows"], r["population"]["distinct"])
        print("    %-14s %-22s %-22s %s" % (r["owner"], r["field"], st, extra))
    print()
    if tables_to_repull:
        print("  TABLES TO RE-PULL WITH ALL FIELDS (their custom columns are UNMEASURED):")
        for t in tables_to_repull:
            print("    %s" % t)

    report = {
        "_algorithm": "A13 harvest_custom_fields.py",
        "_what_it_is": ("every customer-namespace field this installation added to the standard "
                        "model, how it is used in code, and whether anything is in it"),
        "_why_empty_ones_matter": (
            "an empty custom field is an extension point that already exists in the dictionary "
            "and already survived every upgrade. A future design either uses it or collides "
            "with it, and either way needs to know it is there"),
        "_the_state_that_is_not_empty": (
            "FIELD_NOT_EXTRACTED and TABLE_NOT_EXTRACTED mean UNMEASURED, not empty. Reporting "
            "them as empty would be a confident wrong answer"),
        "counts": dict(by_state), "tables_to_repull": tables_to_repull,
        "fields": recs,
    }
    json.dump(report, io.open(out_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    remember(subject="custom fields", kind="CARRIER", learned_by="A13_custom_field_harvest",
             session=98,
             fact="%d custom (owner, field) pairs harvested from source; states %s"
                  % (len(recs), dict(by_state)),
             evidence=out_path.replace("\\", "/"),
             implication=("before designing anything that needs a new field, check this "
                          "inventory — the slot may already exist, typed and upgrade-proof. "
                          "And never read a NOT_EXTRACTED state as empty"))
    print("\nwritten: %s" % os.path.relpath(out_path, ROOT).replace("\\", "/"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
