"""
INC-000005240 — F110 substitution behavior test + A_HIZKIA profile
====================================================================
Tests the user's hypothesis that XREF substitution does not fire on F110
payment runs.

At UNESCO only 2 HQ users run F110 (I_MARQUAND and C_LOPEZ). We cannot find
a non-HQ F110 poster to directly test, so we test via a different angle:

  - Pull the FULL BSEG of one F110 clearing doc (all 6 source tables)
  - Look at whether XREF1/XREF2 are populated on ALL lines, some lines, or
    none — and what the values are
  - If substitution fires: vendor lines should have XREF='HQ' (C_LOPEZ's
    Y_USERFO), bank GL lines should either also have 'HQ' or be blank
    depending on whether the substitution step has a KOART filter
  - If substitution does NOT fire: all lines should be blank, OR the
    vendor line should carry whatever was copied from the cleared invoice

Also: pull A_HIZKIA profile (USR05, PA0001) to confirm she is in Jakarta
(which would validate the manual-workaround narrative).
"""
import sys, os, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

OUT = Path(__file__).with_suffix(".json")

# F110 clearing docs from the Pattern B test
F110_DOCS = [
    ("0002003771", "C_LOPEZ", "2026-02-26"),
    ("0002003828", "C_LOPEZ", "2026-02-26"),
]


def pull_all_lines(guard, belnr):
    """Read BSEG lines from all 6 clearing/open tables with XREF fields."""
    all_lines = []
    tables = ["BSAK", "BSAS", "BSIK", "BSIS", "BSAD", "BSID"]
    for table in tables:
        fields = ["BUKRS", "GJAHR", "BELNR", "BUZEI",
                  "XREF1", "XREF2", "XREF3", "ZUONR",
                  "HKONT", "BSCHL", "DMBTR", "SHKZG"]
        if table in ("BSAK", "BSIK"):
            fields.append("LIFNR")
        elif table in ("BSAD", "BSID"):
            fields.append("KUNNR")
        try:
            rows = rfc_read_paginated(
                guard, table=table, fields=fields,
                where=f"BUKRS = 'UNES' AND BELNR = '{belnr}' AND GJAHR = '2026'",
                batch_size=500,
            )
            for r in rows:
                r["_src"] = table
            all_lines.extend(rows)
        except Exception as e:
            print(f"    {table} failed: {e}")
    return all_lines


def main():
    print("Connecting to P01...")
    guard = get_connection("P01")
    print("Connected.\n")

    out = {}

    # 1. A_HIZKIA profile
    print("=" * 90)
    print("1. A_HIZKIA profile (USR05 + PA0105 + PA0001)")
    print("=" * 90)
    try:
        usr05 = rfc_read_paginated(
            guard, table="USR05",
            fields=["BNAME", "PARID", "PARVA"],
            where="BNAME = 'A_HIZKIA'",
            batch_size=200,
        )
        print(f"  USR05: {len(usr05)} rows")
        y_userfo = None
        for r in usr05:
            pid = r["PARID"].strip()
            pv = r["PARVA"].strip()
            if pid in ("Y_USERFO", "BUK", "FIK", "MOL", "WRK"):
                print(f"    {pid:15s} = {pv!r}")
            if pid == "Y_USERFO":
                y_userfo = pv
        print(f"  → A_HIZKIA Y_USERFO = {y_userfo!r}")

        pa0105 = rfc_read_paginated(
            guard, table="PA0105",
            fields=["PERNR", "SUBTY", "USRID"],
            where="USRID = 'A_HIZKIA' AND SUBTY = '0001'",
            batch_size=10,
        )
        print(f"  PA0105: {len(pa0105)} rows")
        pernr = pa0105[0]["PERNR"] if pa0105 else None
        if pernr:
            pa0001 = rfc_read_paginated(
                guard, table="PA0001",
                fields=["PERNR", "BUKRS", "WERKS", "BTRTL", "ORGEH", "PLANS"],
                where=f"PERNR = '{pernr}' AND ENDDA = '99991231'",
                batch_size=10,
            )
            if pa0001:
                r = pa0001[0]
                print(f"  PA0001: PERNR={r['PERNR']} BUKRS={r['BUKRS']} "
                      f"WERKS={r['WERKS']} BTRTL={r['BTRTL']} ORGEH={r['ORGEH']}")
        out["a_hizkia"] = {"usr05": usr05, "y_userfo": y_userfo,
                           "pa0105": pa0105, "pa0001": pa0001 if pernr else None}
    except Exception as e:
        print(f"  FAILED: {e}")

    # 2. Full BSEG for F110 clearing docs
    for (belnr, user, budat) in F110_DOCS:
        print("\n" + "=" * 90)
        print(f"2. Full BSEG sweep for F110 clearing doc {belnr}/2026 (by {user} on {budat})")
        print("=" * 90)
        lines = pull_all_lines(guard, belnr)
        print(f"  Total lines: {len(lines)}")
        for r in sorted(lines, key=lambda x: (x.get("_src",""), x.get("BUZEI",""))):
            partner = (r.get("LIFNR") or r.get("KUNNR") or "").strip() or "-"
            xref1 = str(r.get("XREF1", "")).strip()
            xref2 = str(r.get("XREF2", "")).strip()
            xref3 = str(r.get("XREF3", "")).strip()
            print(f"    {r['_src']:4s} L{str(r.get('BUZEI','?')).strip():>3s} "
                  f"HKONT={str(r.get('HKONT','')).strip():10s} "
                  f"P={partner:<10} "
                  f"BSCHL={str(r.get('BSCHL','')).strip() or '-':3s} "
                  f"XREF1={xref1!r:10s} XREF2={xref2!r:10s} XREF3={xref3!r:10s} "
                  f"ZUONR={str(r.get('ZUONR','')).strip()!r}")
        out[f"f110_{belnr}"] = lines

    OUT.write_text(json.dumps(out, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults: {OUT}")


if __name__ == "__main__":
    main()
