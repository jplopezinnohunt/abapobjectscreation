"""
Probe: does ICBA have a Fund Management area?
Try multiple tables and naming conventions.
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rfc_helpers import get_connection  # type: ignore


def safe_call(guard, table, fields, where, label, rowcount=200):
    try:
        res = guard.call(
            "RFC_READ_TABLE",
            QUERY_TABLE=table,
            FIELDS=[{"FIELDNAME": f} for f in fields] if fields else [],
            OPTIONS=[{"TEXT": where}] if where else [],
            DELIMITER="|",
            ROWCOUNT=rowcount,
        )
        rows = []
        for d in res.get("DATA", []):
            wa = d["WA"].split("|")
            cols = fields if fields else [str(i) for i in range(len(wa))]
            rows.append({c: wa[i].strip() if i < len(wa) else "" for i, c in enumerate(cols)})
        print(f"  [{label}] OK rows={len(rows)}")
        if rows:
            for r in rows[:5]:
                print(f"      {r}")
        return rows
    except Exception as e:
        print(f"  [{label}] ERR: {str(e)[:120]}")
        return []


def describe(guard, table):
    """Get all field names of a table via DDIF_FIELDINFO_GET if possible."""
    try:
        r = guard.call("DDIF_FIELDINFO_GET", TABNAME=table, LANGU="E")
        fields = [f["FIELDNAME"] for f in r.get("DFIES_TAB", [])]
        print(f"  [{table}] {len(fields)} fields: {fields[:30]}")
        return fields
    except Exception as e:
        print(f"  [{table}] DESCRIBE ERR: {str(e)[:120]}")
        return []


def main():
    g = get_connection("P01")
    print("=== STEP 1 — does T001K have data at all? ===")
    safe_call(g, "T001K", ["BUKRS", "FIKRS"], "", "T001K (no filter)")

    print("\n=== STEP 2 — describe T001 to see if it has FIKRS or FM-area field ===")
    fields = describe(g, "T001")

    print("\n=== STEP 3 — pull T001 BUKRS+FIKRS for the 3 institutes ===")
    if "FIKRS" in fields:
        safe_call(g, "T001", ["BUKRS", "FIKRS", "BUTXT"],
                  "BUKRS = 'ICBA' OR BUKRS = 'MGIE' OR BUKRS = 'IBE'",
                  "T001 BUKRS+FIKRS", rowcount=20)

    print("\n=== STEP 4 — describe FM01 master table ===")
    describe(g, "FM01")
    print("\n=== STEP 5 — pull all FM01 (no filter) ===")
    safe_call(g, "FM01", ["FIKRS", "BUKRS", "WAERS"], "", "FM01 ALL")

    print("\n=== STEP 6 — try FMFINCODE for ICBA directly (not FIKRS=ICBA) ===")
    safe_call(g, "FMFINCODE", ["FIKRS", "FINCODE", "FONDSART"],
              "FINCODE LIKE 'ICBA%'", "FMFINCODE FINCODE LIKE ICBA%", rowcount=20)
    safe_call(g, "FMFINCODE", ["FIKRS", "FINCODE", "FONDSART"],
              "FIKRS = 'ICBA'", "FMFINCODE FIKRS=ICBA", rowcount=20)

    print("\n=== STEP 7 — try TFKBVZ + FM_USE_AREA (alt FM master) ===")
    describe(g, "TFKBVZ")
    safe_call(g, "TFKBVZ", None, "", "TFKBVZ", rowcount=10)

    print("\n=== STEP 8 — check fund types tables exist ===")
    # T036F (without 'T' suffix), FMFGTRT (texts), V_FMFUNDTYPE underlying
    for t in ["T036F", "T036FT", "T036FTT", "FMFG_T", "FMFGSCHEME"]:
        describe(g, t)

    print("\n=== STEP 9 — look at TKA02 (CO area to BUKRS link) for ICBA ===")
    safe_call(g, "TKA02", ["KOKRS", "BUKRS"],
              "BUKRS = 'ICBA' OR BUKRS = 'MGIE' OR BUKRS = 'IBE'",
              "TKA02 CO->BUKRS", rowcount=20)

    g.close()


if __name__ == "__main__":
    main()
