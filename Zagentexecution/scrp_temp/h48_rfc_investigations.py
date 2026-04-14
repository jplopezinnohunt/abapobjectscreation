"""H48 RFC investigations:
- KU-027: YFO_CODES.JAK verification (P01 via SNC/SSO)
- KU-030 complement: REPOSRC/VRSD version history for YRGGBS00 (D01 or P01)
- KU-031 bonus: check if GGB1 / GGB1T / GCLASS etc exist
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-backend-server-python"))

from rfc_helpers import ConnectionGuard


def try_systems(fn_name, *args, **kwargs):
    """Try P01 first (prod data), fallback to D01 (dev)."""
    for sys_id in ("P01", "D01"):
        try:
            guard = ConnectionGuard(sys_id)
            guard.connect()
            print(f"\n=== {fn_name} on {sys_id} ===")
            result = fn_name(guard, *args, **kwargs)
            guard.close()
            return result, sys_id
        except Exception as e:
            print(f"  {sys_id} failed: {e}")
            try:
                guard.close()
            except Exception:
                pass
    return None, None


def check_yfo_codes(guard):
    """KU-027: Does YFO_CODES contain FOCOD='JAK'?"""
    try:
        r = guard.call("RFC_READ_TABLE",
                       QUERY_TABLE="YFO_CODES",
                       OPTIONS=[{"TEXT": "FOCOD = 'JAK'"}],
                       FIELDS=[],
                       ROWCOUNT=5)
        rows = r.get("DATA", [])
        fields = r.get("FIELDS", [])
        print(f"  YFO_CODES WHERE FOCOD='JAK': {len(rows)} rows")
        if fields:
            print(f"  Columns: {[f['FIELDNAME'] for f in fields]}")
        for row in rows:
            print(f"    DATA: {row.get('WA','')}")
        # Also list distinct FOCOD values
        r2 = guard.call("RFC_READ_TABLE",
                        QUERY_TABLE="YFO_CODES",
                        FIELDS=[{"FIELDNAME": "FOCOD"}],
                        ROWCOUNT=100)
        all_focod = [row["WA"].strip() for row in r2.get("DATA", [])]
        print(f"  All FOCOD values ({len(all_focod)}): {sorted(set(all_focod))}")
        return rows, all_focod
    except Exception as e:
        print(f"  YFO_CODES query failed: {e}")
        return None, None


def check_yrggbs00_versions(guard):
    """KU-030 complement: find version history of YRGGBS00 via VRSD."""
    try:
        r = guard.call("RFC_READ_TABLE",
                       QUERY_TABLE="VRSD",
                       OPTIONS=[{"TEXT": "OBJNAME = 'YRGGBS00' AND OBJTYPE = 'REPS'"}],
                       FIELDS=[{"FIELDNAME": "VERSNO"},
                               {"FIELDNAME": "VERSDATE"},
                               {"FIELDNAME": "VERSTIME"},
                               {"FIELDNAME": "AUTHOR"},
                               {"FIELDNAME": "KORRNUM"}],
                       ROWCOUNT=50)
        rows = r.get("DATA", [])
        print(f"  VRSD YRGGBS00 versions: {len(rows)}")
        for row in rows[:20]:
            print(f"    {row['WA']}")
        return rows
    except Exception as e:
        print(f"  VRSD YRGGBS00 failed: {e}")
        # Try REPOSRCV (inactive version table)
        try:
            r2 = guard.call("RFC_READ_TABLE",
                            QUERY_TABLE="VRSX",
                            OPTIONS=[{"TEXT": "OBJNAME = 'YRGGBS00'"}],
                            FIELDS=[],
                            ROWCOUNT=10)
            print(f"  VRSX YRGGBS00: {len(r2.get('DATA',[]))} rows")
            return r2.get("DATA", [])
        except Exception as e2:
            print(f"  VRSX fallback failed: {e2}")
            return None


def check_ggb1_tables(guard):
    """KU-031 bonus: check alternative prerequisite-storage tables."""
    candidates = ["GGB1", "GGB1T", "GCTAB", "GCTAB2", "GCLASS", "GCSTR", "GB921", "GB905", "GB931"]
    found = {}
    for t in candidates:
        try:
            r = guard.call("RFC_READ_TABLE",
                           QUERY_TABLE=t,
                           FIELDS=[],
                           ROWCOUNT=3)
            rows = r.get("DATA", [])
            fields = r.get("FIELDS", [])
            found[t] = {
                "rows_sampled": len(rows),
                "columns": [f["FIELDNAME"] for f in fields][:10],
            }
            print(f"  {t}: {len(rows)} rows sampled, cols={found[t]['columns']}")
        except Exception as e:
            msg = str(e)
            if "TABLE_NOT_AVAILABLE" in msg or "NOT FOUND" in msg.upper():
                found[t] = {"status": "NOT_EXISTS"}
                print(f"  {t}: NOT_EXISTS")
            else:
                found[t] = {"status": f"ERROR: {msg[:80]}"}
                print(f"  {t}: ERROR {msg[:80]}")
    return found


if __name__ == "__main__":
    print("=" * 60)
    print("H48 RFC investigations — KU-027, KU-030, KU-031")
    print("=" * 60)

    print("\n--- KU-027: YFO_CODES.JAK verification ---")
    try_systems(check_yfo_codes)

    print("\n--- KU-030 complement: YRGGBS00 version history ---")
    try_systems(check_yrggbs00_versions)

    print("\n--- KU-031 bonus: substitution-prerequisite table landscape ---")
    try_systems(check_ggb1_tables)

    print("\nDone.")
