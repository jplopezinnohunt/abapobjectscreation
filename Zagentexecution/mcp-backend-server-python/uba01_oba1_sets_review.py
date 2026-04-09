"""
uba01_oba1_sets_review.py
=========================
D01 vs P01 comparison for UBA01:
  - OBA1 (T030H) — Exchange rate difference config for ALL G/L accounts
  - SETLEAF (YBANK) — Account set membership for ALL bank G/Ls
  - ECO09 benchmark: show what a fully configured house bank looks like

READ-ONLY — no writes.
"""

import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

BUKRS = "UNES"
KTOPL = "UNES"
HBKID = "UBA01"
REFERENCE_HBKID = "ECO09"  # benchmark


def safe_read(conn, table, fields, where, label=""):
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where,
                                  batch_size=5000, throttle=0.5)
    except RFCError as e:
        if "TABLE_NOT_AVAILABLE" in str(e) or "NOT_AUTHORIZED" in str(e):
            print(f"  [WARN] {table}: not available or not authorized")
            return None
        raise


def get_accounts(conn, hbkid):
    """Get T012K accounts for a house bank, return list of dicts."""
    t012k = safe_read(conn, "T012K",
                      ["BUKRS", "HBKID", "HKTID", "BANKN", "WAERS", "HKONT"],
                      f"BUKRS = '{BUKRS}' AND HBKID = '{hbkid}'")
    if not t012k:
        return []
    accounts = []
    for row in t012k:
        hkont = row.get("HKONT", "").strip()
        sig = hkont.lstrip('0')
        if sig.startswith('10'):
            clearing = ('11' + sig[2:]).zfill(len(hkont))
        else:
            clearing = hkont
        accounts.append({
            "hktid": row.get("HKTID", "").strip(),
            "bankn": row.get("BANKN", "").strip(),
            "waers": row.get("WAERS", "").strip(),
            "hkont": hkont,
            "clearing_gl": clearing,
        })
    return accounts


def check_t030h(conn, system, all_gls, gl_type, gl_currency):
    """Check OBA1 (T030H) for all G/L accounts."""
    results = {}
    for gl in all_gls:
        t030h = safe_read(conn, "T030H",
                          ["KTOPL", "HKONT", "CURTP", "LKORR", "LSREA",
                           "LHREA", "LSBEW", "LHBEW"],
                          f"KTOPL = '{KTOPL}' AND HKONT = '{gl}'")
        gtype = gl_type.get(gl, "?")
        currency = gl_currency.get(gl, "?")

        if not t030h:
            results[gl] = {
                "system": system, "type": gtype, "currency": currency,
                "exists": False, "fields": {}
            }
        else:
            row = t030h[0]
            fields = {}
            for f in ["CURTP", "LKORR", "LSREA", "LHREA", "LSBEW", "LHBEW"]:
                fields[f] = row.get(f, "").strip()
            results[gl] = {
                "system": system, "type": gtype, "currency": currency,
                "exists": True, "fields": fields,
            }
    return results


def check_setleaf(conn, system, bank_gls):
    """Check YBANK set membership for bank G/Ls."""
    setleaf = safe_read(conn, "SETLEAF",
                        ["SETNAME", "VALOPTION", "VALFROM", "VALTO", "LINEID"],
                        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")
    if not setleaf:
        return {"error": "No YBANK sets found"}

    # Build set index
    sets = {}
    for row in setleaf:
        sn = row.get("SETNAME", "").strip()
        if sn not in sets:
            sets[sn] = []
        sets[sn].append({
            "opt": row.get("VALOPTION", "").strip(),
            "from": row.get("VALFROM", "").strip(),
            "to": row.get("VALTO", "").strip(),
            "lineid": row.get("LINEID", "").strip(),
        })

    result = {
        "system": system,
        "total_sets": len(sets),
        "total_entries": len(setleaf),
        "sets_detail": {},
        "gl_membership": {},
    }

    # Show all sets and entry counts
    for sn in sorted(sets.keys()):
        result["sets_detail"][sn] = len(sets[sn])

    # Check each bank G/L
    for gl in bank_gls:
        gl_short = gl.lstrip("0")
        found_in = []
        for sn, entries in sets.items():
            for e in entries:
                vf = e["from"].lstrip("0")
                vt = e["to"].lstrip("0") if e["to"] else ""
                if e["opt"] == "EQ" and vf == gl_short:
                    found_in.append(sn)
                    break
                elif e["opt"] == "BT" and vf <= gl_short <= vt:
                    found_in.append(f"{sn} (range {e['from']}-{e['to']})")
                    break
        result["gl_membership"][gl] = found_in if found_in else ["NOT FOUND"]

    return result


def run():
    results = {"UBA01": {}, "ECO09_benchmark": {}}

    for system in ["D01", "P01"]:
        print(f"\n{'='*70}")
        print(f"  SYSTEM: {system}")
        print(f"{'='*70}")

        try:
            conn = get_connection(system)
        except Exception as e:
            print(f"  [ERROR] Cannot connect to {system}: {e}")
            results["UBA01"][system] = {"error": str(e)}
            continue

        # ── UBA01 accounts ──
        print(f"\n--- UBA01 Accounts ---")
        uba_accounts = get_accounts(conn, HBKID)
        if not uba_accounts:
            print(f"  UBA01 not found in {system}")
            results["UBA01"][system] = {"accounts": [], "t030h": {}, "sets": {}}
        else:
            for a in uba_accounts:
                print(f"  {a['hktid']}: {a['waers']} | bank={a['hkont']} | clearing={a['clearing_gl']}")

            # Build GL maps
            all_gls = []
            gl_type = {}
            gl_currency = {}
            for a in uba_accounts:
                if a["hkont"] not in all_gls:
                    all_gls.append(a["hkont"])
                    gl_type[a["hkont"]] = "bank"
                    gl_currency[a["hkont"]] = a["waers"]
                if a["clearing_gl"] != a["hkont"] and a["clearing_gl"] not in all_gls:
                    all_gls.append(a["clearing_gl"])
                    gl_type[a["clearing_gl"]] = "clearing"
                    gl_currency[a["clearing_gl"]] = a["waers"]

            # T030H check
            print(f"\n--- OBA1 / T030H ---")
            t030h = check_t030h(conn, system, all_gls, gl_type, gl_currency)
            for gl, info in t030h.items():
                if info["exists"]:
                    f = info["fields"]
                    print(f"  {gl} ({info['type']}/{info['currency']}): "
                          f"CURTP={f['CURTP']} LKORR={f['LKORR']} "
                          f"LSREA={f['LSREA']} LHREA={f['LHREA']} "
                          f"LSBEW={f['LSBEW']} LHBEW={f['LHBEW']}")
                else:
                    print(f"  {gl} ({info['type']}/{info['currency']}): NO ENTRY")

            # SETLEAF check
            print(f"\n--- YBANK Sets (SETLEAF) ---")
            bank_gls = [gl for gl in all_gls if gl_type.get(gl) == "bank"]
            sets_result = check_setleaf(conn, system, bank_gls)
            if "error" in sets_result:
                print(f"  {sets_result['error']}")
            else:
                print(f"  Total sets: {sets_result['total_sets']}, "
                      f"total entries: {sets_result['total_entries']}")
                print(f"  Set sizes:")
                for sn, cnt in sets_result["sets_detail"].items():
                    print(f"    {sn}: {cnt} entries")
                print(f"  UBA01 bank G/L membership:")
                for gl, membership in sets_result["gl_membership"].items():
                    marker = "PASS" if membership[0] != "NOT FOUND" else "FAIL"
                    print(f"    [{marker}] {gl}: {membership}")

            results["UBA01"][system] = {
                "accounts": uba_accounts,
                "t030h": t030h,
                "sets": sets_result,
            }

        # ── ECO09 benchmark ──
        print(f"\n--- ECO09 Benchmark ({system}) ---")
        eco_accounts = get_accounts(conn, REFERENCE_HBKID)
        if not eco_accounts:
            print(f"  ECO09 not found in {system}")
            results["ECO09_benchmark"][system] = {"accounts": []}
        else:
            eco_all_gls = []
            eco_gl_type = {}
            eco_gl_currency = {}
            for a in eco_accounts:
                print(f"  {a['hktid']}: {a['waers']} | bank={a['hkont']} | clearing={a['clearing_gl']}")
                if a["hkont"] not in eco_all_gls:
                    eco_all_gls.append(a["hkont"])
                    eco_gl_type[a["hkont"]] = "bank"
                    eco_gl_currency[a["hkont"]] = a["waers"]
                if a["clearing_gl"] != a["hkont"] and a["clearing_gl"] not in eco_all_gls:
                    eco_all_gls.append(a["clearing_gl"])
                    eco_gl_type[a["clearing_gl"]] = "clearing"
                    eco_gl_currency[a["clearing_gl"]] = a["waers"]

            # T030H for ECO09
            print(f"\n  ECO09 OBA1 / T030H:")
            eco_t030h = check_t030h(conn, system, eco_all_gls, eco_gl_type, eco_gl_currency)
            for gl, info in eco_t030h.items():
                if info["exists"]:
                    f = info["fields"]
                    print(f"    {gl} ({info['type']}/{info['currency']}): "
                          f"CURTP={f['CURTP']} LKORR={f['LKORR']} "
                          f"LSREA={f['LSREA']} LHREA={f['LHREA']} "
                          f"LSBEW={f['LSBEW']} LHBEW={f['LHBEW']}")
                else:
                    print(f"    {gl} ({info['type']}/{info['currency']}): NO ENTRY")

            # SETLEAF for ECO09
            print(f"\n  ECO09 YBANK Sets:")
            eco_bank_gls = [gl for gl in eco_all_gls if eco_gl_type.get(gl) == "bank"]
            eco_sets = check_setleaf(conn, system, eco_bank_gls)
            if "error" not in eco_sets:
                for gl, membership in eco_sets["gl_membership"].items():
                    marker = "PASS" if membership[0] != "NOT FOUND" else "FAIL"
                    print(f"    [{marker}] {gl}: {membership}")

            results["ECO09_benchmark"][system] = {
                "accounts": eco_accounts,
                "t030h": eco_t030h,
                "sets": eco_sets,
            }

        conn.close()

    # ── CROSS-SYSTEM COMPARISON ──
    print(f"\n{'='*70}")
    print(f"  CROSS-SYSTEM COMPARISON: D01 vs P01")
    print(f"{'='*70}")

    for bank_id in ["UBA01"]:
        d01 = results.get(bank_id, {}).get("D01", {})
        p01 = results.get(bank_id, {}).get("P01", {})

        if "error" in d01 or "error" in p01:
            print(f"\n  Cannot compare — connection error in one system")
            continue

        # T030H comparison
        print(f"\n--- T030H (OBA1) D01 vs P01 ---")
        d_t030h = d01.get("t030h", {})
        p_t030h = p01.get("t030h", {})
        all_gls_union = sorted(set(list(d_t030h.keys()) + list(p_t030h.keys())))

        for gl in all_gls_union:
            d = d_t030h.get(gl, {})
            p = p_t030h.get(gl, {})
            d_exists = d.get("exists", False)
            p_exists = p.get("exists", False)
            gtype = d.get("type", p.get("type", "?"))
            currency = d.get("currency", p.get("currency", "?"))

            if d_exists and p_exists:
                diffs = []
                for f in ["CURTP", "LKORR", "LSREA", "LHREA", "LSBEW", "LHBEW"]:
                    dv = d["fields"].get(f, "")
                    pv = p["fields"].get(f, "")
                    if dv != pv:
                        diffs.append(f"{f}: D01={dv} / P01={pv}")
                if diffs:
                    print(f"  [DIFF] {gl} ({gtype}/{currency}): {'; '.join(diffs)}")
                else:
                    print(f"  [MATCH] {gl} ({gtype}/{currency}): identical")
            elif d_exists and not p_exists:
                print(f"  [D01 ONLY] {gl} ({gtype}/{currency}): exists in D01 but NOT P01")
            elif not d_exists and p_exists:
                print(f"  [P01 ONLY] {gl} ({gtype}/{currency}): exists in P01 but NOT D01")
            else:
                print(f"  [NONE] {gl} ({gtype}/{currency}): no entry in either system")

        # SETLEAF comparison
        print(f"\n--- YBANK Sets D01 vs P01 ---")
        d_sets = d01.get("sets", {})
        p_sets = p01.get("sets", {})

        if "error" not in d_sets and "error" not in p_sets:
            # Compare set sizes
            d_detail = d_sets.get("sets_detail", {})
            p_detail = p_sets.get("sets_detail", {})
            all_set_names = sorted(set(list(d_detail.keys()) + list(p_detail.keys())))
            print(f"  Set entry counts:")
            for sn in all_set_names:
                dc = d_detail.get(sn, 0)
                pc = p_detail.get(sn, 0)
                marker = "MATCH" if dc == pc else "DIFF"
                print(f"    [{marker}] {sn}: D01={dc} / P01={pc}")

            # Compare GL membership
            d_mem = d_sets.get("gl_membership", {})
            p_mem = p_sets.get("gl_membership", {})
            all_mem_gls = sorted(set(list(d_mem.keys()) + list(p_mem.keys())))
            print(f"\n  G/L membership comparison:")
            for gl in all_mem_gls:
                dm = d_mem.get(gl, ["N/A"])
                pm = p_mem.get(gl, ["N/A"])
                if dm == pm:
                    print(f"    [MATCH] {gl}: {dm}")
                else:
                    print(f"    [DIFF] {gl}: D01={dm} / P01={pm}")

    # Save raw data
    out_path = os.path.join(os.path.dirname(__file__), "uba01_oba1_sets_data.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nRaw data saved to: {out_path}")


if __name__ == "__main__":
    run()
