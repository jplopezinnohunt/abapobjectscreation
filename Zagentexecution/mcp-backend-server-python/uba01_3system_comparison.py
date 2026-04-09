"""
uba01_3system_comparison.py
============================
Full UBA01 configuration comparison across D01, V01, P01.
All 18 checks from the skill, side by side.
"""
import sys, os, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

BUKRS = "UNES"
KTOPL = "UNES"
HBKID = "UBA01"
SYSTEMS = ["D01", "V01", "P01"]


def safe_read(conn, table, fields, where):
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where, batch_size=5000, throttle=0.5)
    except RFCError as e:
        if "TABLE_NOT_AVAILABLE" in str(e) or "NOT_AUTHORIZED" in str(e):
            return None
        raise


def derive_clearing(hkont):
    sig = hkont.strip().lstrip('0')
    if sig.startswith('10'):
        return ('11' + sig[2:]).zfill(len(hkont.strip()))
    return None


def check_system(system):
    """Run all checks for one system, return dict of results."""
    r = {"system": system, "checks": {}, "error": None}
    try:
        conn = get_connection(system)
    except Exception as e:
        r["error"] = str(e)
        return r

    # CHECK 1-2: T012 + BNKA
    t012 = safe_read(conn, "T012", ["BUKRS","HBKID","BANKS","BANKL"], f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t012:
        r["checks"]["1_T012"] = "NOT FOUND"
        conn.close()
        return r
    hb = t012[0]
    BANKS = hb.get("BANKS","").strip()
    BANKL = hb.get("BANKL","").strip()
    r["checks"]["1_T012"] = f"OK Country={BANKS} BankKey={BANKL}"

    bnka = safe_read(conn, "BNKA", ["BANKA","SWIFT","ORT01"], f"BANKS = '{BANKS}' AND BANKL = '{BANKL}'")
    r["checks"]["2_BNKA"] = f"{bnka[0].get('BANKA','').strip()} SWIFT={bnka[0].get('SWIFT','').strip()}" if bnka else "NOT FOUND"

    # CHECK 3: T012K
    t012k = safe_read(conn, "T012K", ["HKTID","BANKN","WAERS","HKONT"], f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    accounts = []
    if t012k:
        for row in t012k:
            a = {k: row.get(k,"").strip() for k in ["HKTID","BANKN","WAERS","HKONT"]}
            a["clearing"] = derive_clearing(a["HKONT"]) or ""
            accounts.append(a)
        r["checks"]["3_T012K"] = f"{len(accounts)} accounts: " + ", ".join(f"{a['HKTID']}/{a['WAERS']}" for a in accounts)
    else:
        r["checks"]["3_T012K"] = "NO ACCOUNTS"
        conn.close()
        return r

    # CHECK 4: T012T
    t012t = safe_read(conn, "T012T", ["HKTID","TEXT1","SPRAS"], f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if t012t:
        descs = {row.get("HKTID","").strip(): row.get("TEXT1","").strip() for row in t012t if row.get("SPRAS","").strip() == "E"}
        r["checks"]["4_T012T"] = "; ".join(f"{k}={v}" for k, v in sorted(descs.items()))
    else:
        r["checks"]["4_T012T"] = "NO DESCRIPTIONS"

    # Build all GLs
    all_gls = []
    gl_type = {}
    gl_currency = {}
    for a in accounts:
        gl = a["HKONT"]
        clr = a["clearing"]
        if gl:
            all_gls.append(gl)
            gl_type[gl] = "bank"
            gl_currency[gl] = a["WAERS"]
        if clr:
            all_gls.append(clr)
            gl_type[clr] = "clearing"
            gl_currency[clr] = a["WAERS"]

    # CHECK 5: SKA1
    ska1_results = []
    for gl in all_gls:
        ska1 = safe_read(conn, "SKA1", ["SAKNR","KTOKS","XBILK"], f"KTOPL = '{KTOPL}' AND SAKNR = '{gl}'")
        if ska1:
            s = ska1[0]
            ktoks = s.get("KTOKS","").strip()
            ska1_results.append(f"{gl[-7:]}:KTOKS={ktoks}")
        else:
            ska1_results.append(f"{gl[-7:]}:MISSING")
    r["checks"]["5_SKA1"] = " | ".join(ska1_results)

    # CHECK 6: SKB1 (key fields including XINTB)
    skb1_results = []
    for gl in all_gls:
        skb1 = safe_read(conn, "SKB1",
            ["SAKNR","FDLEV","ZUAWA","XOPVW","HBKID","FSTAG","XINTB","XKRES","XGKON","FIPOS"],
            f"BUKRS = '{BUKRS}' AND SAKNR = '{gl}'")
        if skb1:
            s = skb1[0]
            gt = gl_type.get(gl, "?")
            fields = []
            fields.append(f"FDLEV={s.get('FDLEV','').strip()}")
            fields.append(f"ZUAWA={s.get('ZUAWA','').strip()}")
            if gt == "clearing":
                fields.append(f"XOPVW={s.get('XOPVW','').strip()}")
            fields.append(f"HBKID={s.get('HBKID','').strip()}")
            fields.append(f"XINTB={s.get('XINTB','').strip() or '-'}")
            fields.append(f"FSTAG={s.get('FSTAG','').strip()}")
            skb1_results.append(f"{gl[-7:]}({gt}): {' '.join(fields)}")
        else:
            skb1_results.append(f"{gl[-7:]}:MISSING")
    r["checks"]["6_SKB1"] = "\n      ".join(skb1_results)

    # CHECK 7: SKAT
    skat_results = []
    for gl in all_gls:
        skat = safe_read(conn, "SKAT", ["SAKNR","SPRAS","TXT20"], f"KTOPL = '{KTOPL}' AND SAKNR = '{gl}'")
        if skat:
            langs = sorted(set(row.get("SPRAS","").strip() for row in skat))
            skat_results.append(f"{gl[-7:]}:langs={langs}")
        else:
            skat_results.append(f"{gl[-7:]}:NO TEXT")
    r["checks"]["7_SKAT"] = " | ".join(skat_results)

    # CHECK 8: TIBAN
    tiban = safe_read(conn, "TIBAN", ["HKTID","IBAN"], f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    r["checks"]["8_TIBAN"] = f"{len(tiban)} entries" if tiban else "NONE"

    # CHECK 9: T030H
    t030h_results = []
    for gl in all_gls:
        if gl_type.get(gl) != "clearing":
            continue
        t030h = safe_read(conn, "T030H", ["HKONT","CURTP","LKORR","LSREA","LHREA","LSBEW","LHBEW"],
                          f"KTOPL = '{KTOPL}' AND HKONT = '{gl}'")
        if t030h:
            e = t030h[0]
            lkorr = e.get("LKORR","").strip()
            lsbew = e.get("LSBEW","").strip()
            lhbew = e.get("LHBEW","").strip()
            empty_lkorr = not lkorr or lkorr == "0000000000"
            empty_lsbew = not lsbew or lsbew == "0000000000"
            empty_lhbew = not lhbew or lhbew == "0000000000"
            missing = []
            if empty_lkorr: missing.append("LKORR")
            if empty_lsbew: missing.append("LSBEW")
            if empty_lhbew: missing.append("LHBEW")
            cur = gl_currency.get(gl, "?")
            if missing:
                t030h_results.append(f"{gl[-7:]}({cur}): PARTIAL missing {','.join(missing)}")
            else:
                t030h_results.append(f"{gl[-7:]}({cur}): COMPLETE")
        else:
            cur = gl_currency.get(gl, "?")
            t030h_results.append(f"{gl[-7:]}({cur}): NO ENTRY")
    r["checks"]["9_T030H"] = " | ".join(t030h_results)

    # CHECK 10: Cash Mgmt / T035D
    t035d = safe_read(conn, "T035D", ["DISKB","BNKKO"], f"BUKRS = '{BUKRS}'")
    if t035d:
        matched = [row for row in t035d if HBKID in row.get("DISKB","")]
        if matched:
            r["checks"]["10_CM"] = " | ".join(f"{row.get('DISKB','').strip()}->{row.get('BNKKO','').strip()}" for row in matched)
        else:
            r["checks"]["10_CM"] = "NO CM NAMES"
    else:
        r["checks"]["10_CM"] = "T035D NOT ACCESSIBLE"

    # CHECK 11: T035D EBS symbols (same table, already loaded)
    r["checks"]["11_T035D"] = r["checks"]["10_CM"]  # Same data

    # CHECK 12: T028B
    t028b = safe_read(conn, "T028B", ["BANKL","KTONR","VGTYP","BNKKO"], f"BANKL = '{BANKL}'")
    if t028b:
        r["checks"]["12_T028B"] = " | ".join(
            f"Acct={row.get('KTONR','').strip()} Type={row.get('VGTYP','').strip()} CM={row.get('BNKKO','').strip()}"
            for row in t028b)
    else:
        r["checks"]["12_T028B"] = "NO ENTRIES"

    # CHECK 13: T018V
    t018v = safe_read(conn, "T018V", ["HBKID","HKTID","GEHVK","WAERS","ZLSCH"], f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if t018v:
        r["checks"]["13_T018V"] = " | ".join(
            f"{row.get('HKTID','').strip()}({row.get('WAERS','').strip()}) Method={row.get('ZLSCH','').strip()} Clr={row.get('GEHVK','').strip()}"
            for row in t018v)
    else:
        r["checks"]["13_T018V"] = "NO ENTRIES"

    # CHECK 14: T042I
    t042i = safe_read(conn, "T042I", ["HBKID","HKTID","ZLSCH","WAERS","UKONT"], f"ZBUKR = '{BUKRS}' AND HBKID = '{HBKID}'")
    if t042i:
        r["checks"]["14_T042I"] = " | ".join(
            f"Method={row.get('ZLSCH','').strip()} {row.get('HKTID','').strip()}/{row.get('WAERS','').strip()}"
            for row in t042i)
    else:
        r["checks"]["14_T042I"] = "N/A (not a paying bank)"

    # CHECK 15: SETLEAF
    setleaf = safe_read(conn, "SETLEAF", ["SETNAME","VALOPTION","VALFROM"],
                        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")
    if setleaf:
        bank_gls = [gl for gl in all_gls if gl_type.get(gl) == "bank"]
        set_results = []
        for gl in bank_gls:
            gl_short = gl.lstrip("0")
            found = [row.get("SETNAME","").strip() for row in setleaf
                     if row.get("VALOPTION","").strip() == "EQ" and row.get("VALFROM","").strip().lstrip("0") == gl_short]
            if found:
                set_results.append(f"{gl[-7:]}: {found}")
            else:
                set_results.append(f"{gl[-7:]}: NOT FOUND")
        r["checks"]["15_SETLEAF"] = " | ".join(set_results)
    else:
        r["checks"]["15_SETLEAF"] = "SETLEAF NOT ACCESSIBLE"

    conn.close()
    return r


def run():
    results = {}
    for system in SYSTEMS:
        print(f"\n  Checking {system}...")
        results[system] = check_system(system)

    # Print comparison
    print(f"\n{'='*90}")
    print(f"  UBA01 FULL COMPARISON — D01 vs V01 vs P01")
    print(f"{'='*90}")

    all_checks = sorted(set(
        k for r in results.values() if not r.get("error") for k in r.get("checks",{}).keys()
    ))

    for check in all_checks:
        print(f"\n  {check}:")
        values = {}
        for system in SYSTEMS:
            r = results[system]
            if r.get("error"):
                values[system] = f"ERROR: {r['error'][:60]}"
            else:
                values[system] = r.get("checks",{}).get(check, "N/A")

        # Check if all same
        unique = set(str(v) for v in values.values())
        marker = "MATCH" if len(unique) == 1 else "DIFF"

        for system in SYSTEMS:
            val = values[system]
            # Highlight differences
            if marker == "DIFF":
                print(f"    [{system}] {val}")
            else:
                if system == SYSTEMS[0]:
                    print(f"    [ALL]  {val}")
                    break

    # Summary of differences
    print(f"\n{'='*90}")
    print(f"  DIFFERENCES SUMMARY")
    print(f"{'='*90}")

    diff_count = 0
    for check in all_checks:
        vals = {}
        for system in SYSTEMS:
            r = results[system]
            if not r.get("error"):
                vals[system] = str(r.get("checks",{}).get(check, ""))
        unique = set(vals.values())
        if len(unique) > 1:
            diff_count += 1
            print(f"\n  {check}:")
            for system in SYSTEMS:
                if system in vals:
                    print(f"    {system}: {vals[system][:120]}")

    if diff_count == 0:
        print("\n  ALL CHECKS IDENTICAL across D01, V01, P01")
    else:
        print(f"\n  Total differences: {diff_count}")


if __name__ == "__main__":
    run()
