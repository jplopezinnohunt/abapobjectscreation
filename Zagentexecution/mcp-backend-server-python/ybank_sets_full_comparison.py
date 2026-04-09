"""
ybank_sets_full_comparison.py
=============================
Full entry-by-entry comparison of ALL YBANK sets between D01 and P01.
Discovers every difference: entries in D01 not in P01 and vice versa.

READ-ONLY — no writes.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated


def safe_read(conn, table, fields, where):
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where,
                                  batch_size=5000, throttle=0.5)
    except RFCError as e:
        if "TABLE_NOT_AVAILABLE" in str(e) or "NOT_AUTHORIZED" in str(e):
            print(f"  [WARN] {table}: not available or not authorized")
            return None
        raise


def extract_sets(conn, system):
    """Extract all YBANK SETLEAF entries + SETHEADER for set descriptions."""
    print(f"\n  Extracting SETLEAF from {system}...")
    setleaf = safe_read(conn, "SETLEAF",
                        ["SETNAME", "VALOPTION", "VALFROM", "VALTO", "LINEID", "SEQNR"],
                        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")
    if not setleaf:
        print(f"  [ERROR] No YBANK sets found in {system}")
        return {}

    # Also get SETHEADER for descriptions
    setheader = safe_read(conn, "SETHEADERT",
                          ["SETNAME", "DESSION"],
                          "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%' AND LANESSION = 'E'")
    # Fallback: try without language filter
    if not setheader:
        setheader = safe_read(conn, "SETHEADERT",
                              ["SETNAME", "DESSION"],
                              "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")

    desc_map = {}
    if setheader:
        for row in setheader:
            sn = row.get("SETNAME", "").strip()
            desc = row.get("DESSION", "").strip()
            if sn and desc:
                desc_map[sn] = desc

    # Build structured data
    sets = {}
    for row in setleaf:
        sn = row.get("SETNAME", "").strip()
        opt = row.get("VALOPTION", "").strip()
        vfrom = row.get("VALFROM", "").strip()
        vto = row.get("VALTO", "").strip()
        lineid = row.get("LINEID", "").strip()
        seqnr = row.get("SEQNR", "").strip()

        if sn not in sets:
            sets[sn] = {"description": desc_map.get(sn, ""), "entries": []}

        sets[sn]["entries"].append({
            "opt": opt,
            "from": vfrom,
            "to": vto,
            "lineid": lineid,
            "seqnr": seqnr,
        })

    print(f"  {system}: {len(sets)} sets, {len(setleaf)} total entries")
    return sets


def entry_key(e):
    """Unique key for an entry: option + from + to."""
    return (e["opt"], e["from"], e["to"])


def format_entry(e):
    if e["opt"] == "EQ":
        val = e["from"].lstrip("0") or "0"
        return f"EQ {val}"
    elif e["opt"] == "BT":
        vf = e["from"].lstrip("0") or "0"
        vt = e["to"].lstrip("0") or "0"
        return f"BT {vf}–{vt}"
    else:
        return f"{e['opt']} {e['from']}–{e['to']}"


def run():
    results = {}

    # Extract from both systems
    for system in ["D01", "P01"]:
        print(f"\n{'='*70}")
        print(f"  SYSTEM: {system}")
        print(f"{'='*70}")
        try:
            conn = get_connection(system)
            results[system] = extract_sets(conn, system)
            conn.close()
        except Exception as e:
            print(f"  [ERROR] Cannot connect to {system}: {e}")
            results[system] = {}

    d01 = results.get("D01", {})
    p01 = results.get("P01", {})

    if not d01 or not p01:
        print("\nCannot compare — missing data from one system.")
        return

    # ── FULL COMPARISON ──
    print(f"\n{'='*70}")
    print(f"  FULL YBANK SETS COMPARISON: D01 vs P01")
    print(f"{'='*70}")

    all_set_names = sorted(set(list(d01.keys()) + list(p01.keys())))
    total_d01_only = 0
    total_p01_only = 0
    total_match = 0
    diff_details = []

    for sn in all_set_names:
        d_set = d01.get(sn, {"entries": [], "description": ""})
        p_set = p01.get(sn, {"entries": [], "description": ""})

        d_entries = {entry_key(e): e for e in d_set["entries"]}
        p_entries = {entry_key(e): e for e in p_set["entries"]}

        d_keys = set(d_entries.keys())
        p_keys = set(p_entries.keys())

        matched = d_keys & p_keys
        d_only = d_keys - p_keys
        p_only = p_keys - d_keys

        total_match += len(matched)
        total_d01_only += len(d_only)
        total_p01_only += len(p_only)

        desc = d_set["description"] or p_set["description"]
        header = f"\n  {sn}"
        if desc:
            header += f" — {desc}"
        header += f"  (D01={len(d_entries)} / P01={len(p_entries)})"

        if d_only or p_only:
            print(header)
            if d_only:
                sorted_d = sorted(d_only, key=lambda k: k[1])
                for k in sorted_d:
                    e = d_entries[k]
                    print(f"    [D01 ONLY] {format_entry(e)}")
                    diff_details.append({
                        "set": sn, "side": "D01_ONLY",
                        "entry": format_entry(e), "raw": e
                    })
            if p_only:
                sorted_p = sorted(p_only, key=lambda k: k[1])
                for k in sorted_p:
                    e = p_entries[k]
                    print(f"    [P01 ONLY] {format_entry(e)}")
                    diff_details.append({
                        "set": sn, "side": "P01_ONLY",
                        "entry": format_entry(e), "raw": e
                    })
        else:
            print(f"{header}  [OK] IDENTICAL")

    # ── SUMMARY ──
    print(f"\n{'='*70}")
    print(f"  SUMMARY")
    print(f"{'='*70}")
    print(f"  Sets compared: {len(all_set_names)}")
    print(f"  Entries matched: {total_match}")
    print(f"  D01 only (missing in P01): {total_d01_only}")
    print(f"  P01 only (missing in D01): {total_p01_only}")
    print(f"  Total differences: {total_d01_only + total_p01_only}")

    if diff_details:
        print(f"\n  --- ACTION ITEMS ---")
        d01_missing = [d for d in diff_details if d["side"] == "P01_ONLY"]
        p01_missing = [d for d in diff_details if d["side"] == "D01_ONLY"]
        if p01_missing:
            print(f"\n  Need to ADD to P01 ({len(p01_missing)} entries):")
            for d in p01_missing:
                print(f"    {d['set']}: {d['entry']}")
        if d01_missing:
            print(f"\n  Need to ADD to D01 ({len(d01_missing)} entries):")
            for d in d01_missing:
                print(f"    {d['set']}: {d['entry']}")

    # Also try to resolve G/L numbers to names via SKAT
    print(f"\n  --- RESOLVING G/L NAMES ---")
    all_diff_gls = set()
    for d in diff_details:
        raw = d["raw"]
        if raw["opt"] == "EQ":
            all_diff_gls.add(raw["from"])

    if all_diff_gls:
        try:
            conn = get_connection("P01")
            for gl in sorted(all_diff_gls):
                skat = safe_read(conn, "SKAT",
                                 ["SAKNR", "TXT20", "TXT50"],
                                 f"KTOPL = 'UNES' AND SAKNR = '{gl}' AND SPRAS = 'E'")
                if skat:
                    txt = skat[0].get("TXT50", "").strip() or skat[0].get("TXT20", "").strip()
                    print(f"    {gl.lstrip('0')}: {txt}")
                else:
                    print(f"    {gl.lstrip('0')}: (no SKAT text)")
            conn.close()
        except Exception as e:
            print(f"  Could not resolve names: {e}")

    # Save
    out_path = os.path.join(os.path.dirname(__file__), "ybank_sets_comparison.json")
    with open(out_path, "w") as f:
        json.dump({
            "d01_sets": {sn: len(s["entries"]) for sn, s in d01.items()},
            "p01_sets": {sn: len(s["entries"]) for sn, s in p01.items()},
            "differences": diff_details,
            "summary": {
                "matched": total_match,
                "d01_only": total_d01_only,
                "p01_only": total_p01_only,
            }
        }, f, indent=2, default=str)
    print(f"\nData saved to: {out_path}")


if __name__ == "__main__":
    run()
