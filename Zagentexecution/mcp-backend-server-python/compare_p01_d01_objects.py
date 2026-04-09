"""
Compare actual table values between P01 and D01 for all objects
in the 7 open P01 customizing requests.

View names map to underlying tables:
  V_T77HRFPM_CLSNG  -> T77HRFPM_CLSNG (HCM Fiori closing)
  V_T163K            -> T163K (MM tolerance)
  V_T100C            -> T100C (message control)
  V_VBWF15           -> VBWF15 (workflow task assignment)
  VC_T012N           -> T012N (house bank names) -- try T012 too
  V_001_B            -> T001 (company code basic)
  TABADRH            -> TABADRH (FM address hierarchy)
  VV_FMTABADRH_REASSIGNMENT -> FMTABADRH (FM reassignment)
  V_FMYC_CFC1_A     -> FMYC_CFC1_A (CF control)
  VV_FMABP_CNTRL_BFC -> FMABP_CNTRL (ABP control)
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
os.environ["PYTHONIOENCODING"] = "utf-8"
from rfc_helpers import get_connection


def read_table(conn, table, fields=None, options=None, max_rows=200):
    """Read table, return (field_names, rows) or (None, error)."""
    try:
        params = {
            "QUERY_TABLE": table,
            "DELIMITER": "|",
            "ROWCOUNT": max_rows,
        }
        if fields:
            params["FIELDS"] = [{"FIELDNAME": f} for f in fields]
        if options:
            params["OPTIONS"] = [{"TEXT": o} for o in options]
        result = conn.call("RFC_READ_TABLE", **params)
        fnames = [f["FIELDNAME"].strip() for f in result.get("FIELDS", [])]
        rows = []
        for row in result.get("DATA", []):
            parts = row["WA"].split("|")
            rows.append({h: parts[i].strip() for i, h in enumerate(fnames)})
        return fnames, rows
    except Exception as e:
        return None, str(e)


def compare_tables(p01_rows, d01_rows, key_fields):
    """Compare two sets of rows by key fields. Returns diff summary."""
    def make_key(row):
        return tuple(row.get(k, "") for k in key_fields)

    p01_map = {make_key(r): r for r in p01_rows}
    d01_map = {make_key(r): r for r in d01_rows}

    only_p01 = set(p01_map.keys()) - set(d01_map.keys())
    only_d01 = set(d01_map.keys()) - set(p01_map.keys())
    common = set(p01_map.keys()) & set(d01_map.keys())

    diffs = []
    for key in common:
        p_row = p01_map[key]
        d_row = d01_map[key]
        field_diffs = {}
        for f in p_row:
            pv = p_row.get(f, "")
            dv = d_row.get(f, "")
            if pv != dv:
                field_diffs[f] = {"P01": pv, "D01": dv}
        if field_diffs:
            diffs.append({"key": dict(zip(key_fields, key)), "differences": field_diffs})

    return {
        "only_in_P01": [dict(zip(key_fields, k)) for k in only_p01],
        "only_in_D01": [dict(zip(key_fields, k)) for k in only_d01],
        "value_differences": diffs,
        "identical_count": len(common) - len(diffs),
        "p01_total": len(p01_rows),
        "d01_total": len(d01_rows),
    }


def main():
    print("Connecting to both systems...")
    p01 = get_connection(system_id="P01")
    print("[OK] P01 connected")
    d01 = get_connection(system_id="D01")
    print("[OK] D01 connected")

    # Tables to compare with their key fields
    comparisons = [
        {
            "name": "T77HRFPM_CLSNG",
            "view": "V_T77HRFPM_CLSNG",
            "transport": "P01K950265 + P01K950267",
            "keys": None,  # Will use all fields if no key known
        },
        {
            "name": "T163K",
            "view": "V_T163K",
            "transport": "P01K950269 + P01K950271",
            "keys": ["BUKRS", "EKORG", "BSART", "KNTTP", "KTOPL"],
        },
        {
            "name": "T100C",
            "view": "V_T100C",
            "transport": "P01K950269 + P01K950271",
            "keys": ["ARBGB", "MSGNR"],
        },
        {
            "name": "VBWF15",
            "view": "V_VBWF15",
            "transport": "P01K950275",
            "keys": None,
        },
        {
            "name": "T012N",
            "view": "VC_T012N",
            "transport": "P01K950277",
            "keys": ["BUKRS", "HBKID", "HKTID", "SPRAS"],
        },
        {
            "name": "T001",
            "view": "V_001_B",
            "transport": "P01K950279",
            "keys": ["BUKRS"],
        },
        {
            "name": "TABADRH",
            "view": "TABADRH",
            "transport": "P01K950269",
            "keys": None,
        },
    ]

    results = {}

    for comp in comparisons:
        tbl = comp["name"]
        print(f"\n{'='*60}")
        print(f"Comparing: {tbl} (from {comp['view']}, transport {comp['transport']})")
        print(f"{'='*60}")

        # Read from both systems
        p01_fnames, p01_result = read_table(p01, tbl)
        d01_fnames, d01_result = read_table(d01, tbl)

        if p01_fnames is None:
            print(f"  P01 ERROR: {str(p01_result)[:150]}")
            results[tbl] = {"status": "P01_ERROR", "error": str(p01_result)[:200]}
            continue
        if d01_fnames is None:
            print(f"  D01 ERROR: {str(d01_result)[:150]}")
            results[tbl] = {"status": "D01_ERROR", "error": str(d01_result)[:200]}
            continue

        p01_rows = p01_result
        d01_rows = d01_result

        print(f"  P01: {len(p01_rows)} rows, D01: {len(d01_rows)} rows")
        print(f"  Fields: {', '.join(p01_fnames[:10])}{'...' if len(p01_fnames) > 10 else ''}")

        # Determine key fields
        key_fields = comp["keys"]
        if key_fields is None:
            # Use first 3 fields as key (heuristic)
            key_fields = p01_fnames[:3] if len(p01_fnames) >= 3 else p01_fnames
            print(f"  Using heuristic keys: {key_fields}")

        # Filter key fields to those that exist
        key_fields = [k for k in key_fields if k in p01_fnames]
        if not key_fields:
            print(f"  WARNING: No valid key fields found, using first field")
            key_fields = [p01_fnames[0]]

        diff = compare_tables(p01_rows, d01_rows, key_fields)
        results[tbl] = diff

        # Print results
        if diff["only_in_P01"]:
            print(f"  ONLY IN P01 ({len(diff['only_in_P01'])} rows):")
            for r in diff["only_in_P01"][:5]:
                print(f"    {r}")
            if len(diff["only_in_P01"]) > 5:
                print(f"    ... and {len(diff['only_in_P01'])-5} more")

        if diff["only_in_D01"]:
            print(f"  ONLY IN D01 ({len(diff['only_in_D01'])} rows):")
            for r in diff["only_in_D01"][:5]:
                print(f"    {r}")
            if len(diff["only_in_D01"]) > 5:
                print(f"    ... and {len(diff['only_in_D01'])-5} more")

        if diff["value_differences"]:
            print(f"  VALUE DIFFERENCES ({len(diff['value_differences'])} rows differ):")
            for d in diff["value_differences"][:10]:
                print(f"    Key: {d['key']}")
                for field, vals in d["differences"].items():
                    print(f"      {field}: P01='{vals['P01']}' vs D01='{vals['D01']}'")

        if not diff["only_in_P01"] and not diff["only_in_D01"] and not diff["value_differences"]:
            print(f"  IDENTICAL - no differences found ({diff['identical_count']} matching rows)")

        # Verdict
        has_drift = bool(diff["only_in_P01"] or diff["only_in_D01"] or diff["value_differences"])
        verdict = "DRIFT DETECTED" if has_drift else "NO DRIFT"
        print(f"\n  >>> VERDICT: {verdict}")

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for tbl, diff in results.items():
        if isinstance(diff, dict) and "status" in diff:
            print(f"  {tbl:25s} ERROR: {diff.get('error','')[:80]}")
        else:
            has_drift = bool(diff.get("only_in_P01") or diff.get("only_in_D01") or diff.get("value_differences"))
            drift_details = []
            if diff.get("only_in_P01"):
                drift_details.append(f"+{len(diff['only_in_P01'])} P01-only")
            if diff.get("only_in_D01"):
                drift_details.append(f"+{len(diff['only_in_D01'])} D01-only")
            if diff.get("value_differences"):
                drift_details.append(f"{len(diff['value_differences'])} value diffs")
            status = f"DRIFT [{', '.join(drift_details)}]" if has_drift else "IDENTICAL"
            print(f"  {tbl:25s} {status}")

    # Save full results
    out_path = os.path.join(os.path.dirname(__file__), "p01_d01_comparison_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    print(f"\nFull results saved to {out_path}")


if __name__ == "__main__":
    main()
