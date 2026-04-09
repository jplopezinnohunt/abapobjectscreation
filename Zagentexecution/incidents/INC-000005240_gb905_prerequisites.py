"""
INC-000005240 — Extract GB905 + GB921 (substitution step prerequisites + headers)
===================================================================================
Without GB905, we cannot know WHICH GB901 BOOLEXP (prerequisite) is the gate
for GB922 SUBSTID='UNESCO' step 005 (XREF1 via UXR1). This script pulls the
linking tables via RFC so we can definitively answer:

  - For SUBSTID='UNESCO', step 005 (XREF1), what is the prerequisite BOOLID?
  - What is that BOOLEXP's content in GB901?
  - Under what conditions does UXR1 actually fire?

Same for step 006 (XREF2/UXR2) and step 007 (ZLSCH/UZLS).
"""
import sys, os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

OUT = Path(__file__).with_suffix(".json")


def try_read(guard, table, fields, where):
    try:
        return rfc_read_paginated(guard, table=table, fields=fields,
                                  where=where, batch_size=500)
    except Exception as e:
        print(f"    {table} read failed: {e}")
        return None


def main():
    print("Connecting to P01...")
    guard = get_connection("P01")
    print("Connected.\n")

    out = {}

    # 1. GB905 — substitution step prerequisites
    print("=" * 90)
    print("A. GB905 — substitution step prerequisites for SUBSTID='UNESCO'")
    print("=" * 90)
    gb905 = try_read(
        guard, "GB905",
        fields=["SUBSTID", "SUBSEQNR", "CONSEQNR", "BOOLID"],
        where="SUBSTID = 'UNESCO'",
    )
    if gb905 is not None:
        print(f"  GB905 returned {len(gb905)} rows for SUBSTID='UNESCO'")
        for r in gb905:
            print(f"    step {r['SUBSEQNR']}/{r['CONSEQNR']}  BOOLID={r['BOOLID']!r}")
        out["gb905_unesco"] = gb905
    else:
        # Maybe the schema is different
        print("  GB905 failed — trying GB931 (validation steps) as backup")
        gb931 = try_read(
            guard, "GB931",
            fields=["VALIDID", "SEQNR", "BOOLID"],
            where="VALIDID = 'UNESCO'",
        )
        if gb931 is not None:
            print(f"  GB931 returned {len(gb931)} rows for VALIDID='UNESCO'")
            for r in gb931:
                print(f"    step {r['SEQNR']}  BOOLID={r['BOOLID']!r}")
            out["gb931_unesco"] = gb931

    # 2. GB921 — substitution rule header
    print("\n" + "=" * 90)
    print("B. GB921 — substitution rule header (name, description, callpoint, bukrs)")
    print("=" * 90)
    gb921 = try_read(
        guard, "GB921",
        fields=["SUBSTID", "EVENT", "CALLP", "BOOLCLAS", "ACTIVE"],
        where="SUBSTID = 'UNESCO'",
    )
    if gb921 is not None:
        print(f"  GB921 returned {len(gb921)} rows")
        for r in gb921:
            print(f"    {r}")
        out["gb921_unesco"] = gb921

    # Try the generic substitution name table
    print("\n" + "=" * 90)
    print("C. GB921 — any row mentioning UNESCO / UNES")
    print("=" * 90)
    for sub in ["UNESCO", "UNES"]:
        try:
            r = rfc_read_paginated(
                guard, "GB921",
                fields=["SUBSTID", "EVENT", "CALLP"],
                where=f"SUBSTID = '{sub}'",
                batch_size=50,
            )
            print(f"  SUBSTID={sub!r}: {r}")
        except Exception as e:
            print(f"  SUBSTID={sub!r}: {e}")

    # 3. List all UNESCO substitution-related tables via RFC — try common names
    print("\n" + "=" * 90)
    print("D. Probing other candidate tables (TB_GB*, GB91x, TVARC)")
    print("=" * 90)
    for tab in ["GB91", "GB92", "GB90", "GB905", "GB906", "GB907", "GB921",
                "GB922", "GB931", "GB932", "T80D", "T80M", "TVARC"]:
        try:
            r = rfc_read_paginated(
                guard, tab, fields=["*"] if False else [], where="",
                batch_size=1,
            )
        except Exception:
            pass

    # 4. Practical fallback — try GB905 without WHERE (get all, then filter)
    print("\n" + "=" * 90)
    print("E. GB905 — ALL rows, filter client-side for UNESCO")
    print("=" * 90)
    try:
        all_gb905 = rfc_read_paginated(
            guard, "GB905",
            fields=["SUBSTID", "SUBSEQNR", "CONSEQNR", "BOOLID"],
            where="",
            batch_size=5000,
        )
        print(f"  GB905 total rows: {len(all_gb905)}")
        unesco = [r for r in all_gb905 if r["SUBSTID"].strip() == "UNESCO"]
        print(f"  UNESCO subset   : {len(unesco)}")
        for r in sorted(unesco, key=lambda x: (x["SUBSEQNR"], x["CONSEQNR"])):
            print(f"    step {r['SUBSEQNR']}/{r['CONSEQNR']}  BOOLID={r['BOOLID']!r}")
        out["gb905_all_unesco"] = unesco
    except Exception as e:
        print(f"  GB905 read failed: {e}")

    OUT.write_text(json.dumps(out, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults: {OUT}")


if __name__ == "__main__":
    main()
