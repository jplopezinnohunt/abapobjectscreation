"""
INC-000005240 — CDPOS detail for A_HIZKIA's 2 FBL3N changes
============================================================
A_HIZKIA modified 2 of AL_JONATHAN's F-53 docs via FBL3N on 2026-02-16:
  - 3100003438/2026  CHANGENR=0118205716
  - 3100003439/2026  CHANGENR=0118205748

This pulls CDPOS detail to answer: was XREF1/XREF2/XBLNR/ZUONR changed?
If NO → AL_JONATHAN's XREF='HQ' is as-posted on those docs too.
If YES → those 2 docs need a separate note in the report.
"""
import sys, os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

OUT = Path(__file__).with_suffix(".json")

CHANGES = [
    {"OBJECTID": "350UNES31000034382026", "CHANGENR": "0118205716",
     "DOC": "3100003438/2026", "USER": "A_HIZKIA", "TCODE": "FBL3N", "DATE": "20260216"},
    {"OBJECTID": "350UNES31000034392026", "CHANGENR": "0118205748",
     "DOC": "3100003439/2026", "USER": "A_HIZKIA", "TCODE": "FBL3N", "DATE": "20260216"},
]


def main():
    print("Connecting to P01...")
    guard = get_connection("P01")
    print("Connected.\n")

    results = []
    for chg in CHANGES:
        print(f"=" * 90)
        print(f"CDPOS for {chg['DOC']}  CHANGENR={chg['CHANGENR']} by {chg['USER']} via {chg['TCODE']}")
        print("=" * 90)
        # CDPOS blocks compound WHERE via RFC_READ_TABLE "suspicious" filter.
        # Retry using just OBJECTID (which is the most selective single key).
        where_list = [{"TEXT": f"OBJECTCLAS = 'BELEG' AND"},
                      {"TEXT": f"OBJECTID = '{chg['OBJECTID']}'"}]
        try:
            rows = rfc_read_paginated(
                guard, table="CDPOS",
                fields=["OBJECTCLAS", "OBJECTID", "CHANGENR", "TABNAME", "TABKEY",
                        "FNAME", "CHNGIND", "VALUE_OLD", "VALUE_NEW"],
                where=where_list,
                batch_size=500,
            )
            # Client-side filter to the specific CHANGENR
            rows = [r for r in rows if r.get("CHANGENR", "").strip() == chg["CHANGENR"]]
            print(f"  Total CDPOS rows: {len(rows)}")
            for r in rows:
                fname = r.get("FNAME", "").strip()
                tabname = r.get("TABNAME", "").strip()
                chngind = r.get("CHNGIND", "").strip()
                old = r.get("VALUE_OLD", "").strip()
                new = r.get("VALUE_NEW", "").strip()
                tabkey = r.get("TABKEY", "").strip()
                marker = " <-- XREF/XBLNR/ZUONR" if fname in ("XREF1","XREF2","XREF3","XBLNR","ZUONR") else ""
                print(f"    {tabname:8s} {fname:10s} [{chngind}] OLD={old!r:25s} NEW={new!r:25s}{marker}")
                print(f"         TABKEY={tabkey}")
            results.append({**chg, "cdpos_rows": rows})
        except Exception as e:
            print(f"  FAILED: {e}")
            results.append({**chg, "error": str(e)})

    # Summary
    print("\n" + "=" * 90)
    print("VERDICT")
    print("=" * 90)
    for r in results:
        if "cdpos_rows" in r:
            touched = [p for p in r["cdpos_rows"]
                       if p.get("FNAME", "").strip() in ("XREF1", "XREF2", "XREF3")]
            if touched:
                print(f"  {r['DOC']}: XREF fields WERE modified:")
                for p in touched:
                    print(f"    {p['FNAME'].strip()}: {p['VALUE_OLD']!r} -> {p['VALUE_NEW']!r}")
            else:
                fields_changed = sorted({p.get("FNAME", "").strip() for p in r["cdpos_rows"]})
                print(f"  {r['DOC']}: XREF NOT modified. Fields changed: {fields_changed}")

    OUT.write_text(json.dumps(results, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    print(f"\nFull data: {OUT}")


if __name__ == "__main__":
    main()
