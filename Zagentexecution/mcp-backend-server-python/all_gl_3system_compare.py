"""
all_gl_3system_compare.py
==========================
Compare SKA1, SKB1, SKAT for ALL bank-related G/L accounts across D01, V01, P01.
Extracts all accounts linked via T012K, plus their derived clearing GLs.
"""
import sys, os, io, json, time
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

BUKRS = "UNES"
KTOPL = "UNES"
SYSTEMS = ["D01", "V01", "P01"]


def safe_read(conn, table, fields, where):
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where,
                                  batch_size=5000, throttle=0.5)
    except RFCError as e:
        if "TABLE_NOT_AVAILABLE" in str(e) or "NOT_AUTHORIZED" in str(e):
            return []
        raise


def bulk_extract(conn, system):
    """Extract ALL bank-related GL master data from one system."""
    print(f"  {system}: extracting...")

    # SKA1 — all UNES chart of accounts
    ska1 = {}
    rows = safe_read(conn, "SKA1",
        ["SAKNR", "KTOKS", "XBILK", "XLOEV", "XSPEB"],
        f"KTOPL = '{KTOPL}'")
    for r in rows:
        saknr = r.get("SAKNR", "").strip()
        ska1[saknr] = {k: str(v).strip() if v else "" for k, v in r.items()}
    print(f"    SKA1: {len(ska1)} accounts")

    # SKB1 — all UNES company code level
    skb1 = {}
    rows = safe_read(conn, "SKB1",
        ["SAKNR", "WAERS", "FDLEV", "ZUAWA", "XKRES", "XGKON",
         "FIPOS", "FSTAG", "XOPVW", "HBKID", "HKTID", "XINTB"],
        f"BUKRS = '{BUKRS}'")
    for r in rows:
        saknr = r.get("SAKNR", "").strip()
        skb1[saknr] = {k: str(v).strip() if v else "" for k, v in r.items()}
    print(f"    SKB1: {len(skb1)} accounts")

    # SKAT — all UNES texts (E only for comparison — F/P add too much volume)
    skat = {}
    for lang in ["E", "F", "P"]:
        rows = safe_read(conn, "SKAT",
            ["SAKNR", "SPRAS", "TXT20", "TXT50"],
            f"KTOPL = '{KTOPL}' AND SPRAS = '{lang}'")
        for r in rows:
            saknr = r.get("SAKNR", "").strip()
            sp = r.get("SPRAS", "").strip()
            if saknr not in skat:
                skat[saknr] = {}
            skat[saknr][sp] = {
                "TXT20": str(r.get("TXT20", "")).strip(),
                "TXT50": str(r.get("TXT50", "")).strip(),
            }
        time.sleep(1)
    print(f"    SKAT: {len(skat)} accounts with texts")

    # T012K — get all bank GLs
    t012k = safe_read(conn, "T012K",
        ["HBKID", "HKTID", "HKONT", "WAERS"],
        f"BUKRS = '{BUKRS}'")
    bank_gls = set()
    for r in t012k:
        gl = r.get("HKONT", "").strip()
        if gl:
            bank_gls.add(gl)
            sig = gl.lstrip('0')
            if sig.startswith('10'):
                bank_gls.add(('11' + sig[2:]).zfill(len(gl)))
    print(f"    T012K: {len(t012k)} accounts, {len(bank_gls)} GLs (bank+clearing)")

    return {"ska1": ska1, "skb1": skb1, "skat": skat, "bank_gls": bank_gls}


def run():
    print("="*90)
    print("  ALL G/L ACCOUNTS — SKA1/SKB1/SKAT — D01 vs V01 vs P01")
    print("="*90)

    data = {}
    conns = {}
    for system in SYSTEMS:
        try:
            conns[system] = get_connection(system)
            data[system] = bulk_extract(conns[system], system)
            conns[system].close()
        except Exception as e:
            print(f"  {system} ERROR: {e}")
            data[system] = {"ska1": {}, "skb1": {}, "skat": {}, "bank_gls": set()}

    # Union of all bank GLs across systems
    all_bank_gls = set()
    for system in SYSTEMS:
        all_bank_gls.update(data[system]["bank_gls"])
    all_bank_gls = sorted(all_bank_gls)

    print(f"\n  Total unique bank GLs to compare: {len(all_bank_gls)}")

    # Compare
    ska1_diffs = []
    skb1_diffs = []
    skat_diffs = []
    missing_gls = []  # GL exists in one system but not another

    SKA1_COMPARE = ["KTOKS", "XBILK", "XLOEV", "XSPEB"]
    SKB1_COMPARE = ["WAERS", "FDLEV", "ZUAWA", "XKRES", "XGKON",
                    "FIPOS", "FSTAG", "XOPVW", "HBKID", "HKTID", "XINTB"]

    for gl in all_bank_gls:
        # Check existence
        exists = {s: gl in data[s]["ska1"] or gl in data[s]["skb1"] for s in SYSTEMS}
        if not all(exists.values()) and any(exists.values()):
            present = [s for s in SYSTEMS if exists[s]]
            absent = [s for s in SYSTEMS if not exists[s]]
            missing_gls.append({"gl": gl, "present": present, "absent": absent})

        # SKA1 comparison
        for field in SKA1_COMPARE:
            vals = {}
            for s in SYSTEMS:
                d = data[s]["ska1"].get(gl)
                vals[s] = d.get(field, "") if d else "(MISSING)"
            if len(set(vals.values())) > 1:
                ska1_diffs.append({"gl": gl, "field": field, "values": vals})

        # SKB1 comparison
        for field in SKB1_COMPARE:
            vals = {}
            for s in SYSTEMS:
                d = data[s]["skb1"].get(gl)
                vals[s] = d.get(field, "") if d else "(MISSING)"
            if len(set(vals.values())) > 1:
                skb1_diffs.append({"gl": gl, "field": field, "values": vals})

        # SKAT comparison (E/F/P)
        for lang in ["E", "F", "P"]:
            for tf in ["TXT20", "TXT50"]:
                vals = {}
                for s in SYSTEMS:
                    d = data[s]["skat"].get(gl)
                    if d and lang in d:
                        vals[s] = d[lang].get(tf, "")
                    else:
                        vals[s] = "(MISSING)"
                if len(set(vals.values())) > 1:
                    skat_diffs.append({"gl": gl, "lang": lang, "field": tf, "values": vals})

    # ── Report ──
    print(f"\n{'='*90}")
    print(f"  RESULTS")
    print(f"{'='*90}")

    # Missing GLs
    print(f"\n  GLs MISSING in one or more systems: {len(missing_gls)}")
    if missing_gls:
        for m in missing_gls[:50]:
            print(f"    {m['gl']}: present in {m['present']}, MISSING in {m['absent']}")
        if len(missing_gls) > 50:
            print(f"    ... and {len(missing_gls)-50} more")

    # SKA1 diffs
    print(f"\n  SKA1 differences: {len(ska1_diffs)}")
    if ska1_diffs:
        # Group by field
        by_field = {}
        for d in ska1_diffs:
            f = d["field"]
            if f not in by_field:
                by_field[f] = []
            by_field[f].append(d)
        for field, diffs in sorted(by_field.items()):
            print(f"    {field}: {len(diffs)} GLs differ")
            for d in diffs[:10]:
                vals_str = " | ".join(f"{s}={d['values'][s]}" for s in SYSTEMS)
                print(f"      {d['gl']}: {vals_str}")
            if len(diffs) > 10:
                print(f"      ... and {len(diffs)-10} more")

    # SKB1 diffs
    print(f"\n  SKB1 differences: {len(skb1_diffs)}")
    if skb1_diffs:
        by_field = {}
        for d in skb1_diffs:
            f = d["field"]
            if f not in by_field:
                by_field[f] = []
            by_field[f].append(d)
        for field, diffs in sorted(by_field.items()):
            print(f"    {field}: {len(diffs)} GLs differ")
            for d in diffs[:10]:
                vals_str = " | ".join(f"{s}={d['values'][s]}" for s in SYSTEMS)
                print(f"      {d['gl']}: {vals_str}")
            if len(diffs) > 10:
                print(f"      ... and {len(diffs)-10} more")

    # SKAT diffs
    print(f"\n  SKAT differences: {len(skat_diffs)}")
    if skat_diffs:
        # Group by type of diff
        by_pattern = {"MISSING_TEXT": [], "ECOBANK": [], "TRUNCATION": [], "OTHER": []}
        for d in skat_diffs:
            vals = d["values"]
            if any(v == "(MISSING)" for v in vals.values()):
                by_pattern["MISSING_TEXT"].append(d)
            elif any("ECOBANK" in v.upper() for v in vals.values() if v != "(MISSING)"):
                by_pattern["ECOBANK"].append(d)
            else:
                # Check if it's just truncation (TXT50 matches, TXT20 differs)
                by_pattern["OTHER"].append(d)

        for pattern, diffs in by_pattern.items():
            if not diffs:
                continue
            print(f"\n    {pattern}: {len(diffs)} differences")
            for d in diffs[:15]:
                label = f"{d['gl']} {d['lang']}/{d['field']}"
                vals_str = " | ".join(f"{s}={d['values'][s][:35]}" for s in SYSTEMS)
                print(f"      {label:25s}: {vals_str}")
            if len(diffs) > 15:
                print(f"      ... and {len(diffs)-15} more")

    # Final summary
    print(f"\n{'='*90}")
    print(f"  SUMMARY")
    print(f"{'='*90}")
    print(f"  Bank GLs compared: {len(all_bank_gls)}")
    print(f"  GLs missing in 1+ system: {len(missing_gls)}")
    print(f"  SKA1 field diffs: {len(ska1_diffs)}")
    print(f"  SKB1 field diffs: {len(skb1_diffs)}")
    print(f"  SKAT text diffs: {len(skat_diffs)}")
    print(f"  Total differences: {len(missing_gls) + len(ska1_diffs) + len(skb1_diffs) + len(skat_diffs)}")


if __name__ == "__main__":
    run()
