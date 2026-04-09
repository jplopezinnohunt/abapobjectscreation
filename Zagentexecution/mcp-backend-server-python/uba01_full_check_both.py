"""
uba01_full_check_both.py
========================
Full 15-check compliance for UBA01 in BOTH D01 and P01, then cross-system comparison.
"""
import sys, os, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

BUKRS = "UNES"
KTOPL = "UNES"
HBKID = "UBA01"


def safe_read(conn, table, fields, where):
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where,
                                  batch_size=5000, throttle=0.5)
    except RFCError as e:
        if "TABLE_NOT_AVAILABLE" in str(e) or "NOT_AUTHORIZED" in str(e):
            return None
        raise


def derive_clearing_gl(hkont):
    full = hkont.strip()
    sig = full.lstrip('0')
    if sig.startswith('10'):
        return ('11' + sig[2:]).zfill(len(full))
    return full


def run_check(system):
    results = {"system": system, "checks": [], "pass": 0, "fail": 0, "warn": 0}

    def status(check_id, msg, level="PASS"):
        results["checks"].append({"id": check_id, "msg": msg, "level": level})
        results[level.lower()] = results.get(level.lower(), 0) + 1
        print(f"  [{level}] {msg}")

    print(f"\n{'='*70}")
    print(f"  HOUSE BANK COMPLIANCE CHECK -- {HBKID} / {BUKRS} / {system}")
    print(f"{'='*70}")

    try:
        conn = get_connection(system)
    except Exception as e:
        print(f"  [ERROR] Cannot connect to {system}: {e}")
        return results

    # CHECK 1: T012
    print(f"\nCHECK 1: T012 House Bank Master")
    t012 = safe_read(conn, "T012", ["BUKRS","HBKID","BANKS","BANKL"],
                     f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t012:
        status(1, f"House bank {HBKID} NOT FOUND", "FAIL")
        conn.close()
        return results
    hb = t012[0]
    BANKS = hb.get("BANKS","").strip()
    BANKL = hb.get("BANKL","").strip()
    status(1, f"House bank exists -- Country={BANKS}, BankKey={BANKL}")

    # CHECK 2: BNKA
    print(f"\nCHECK 2: BNKA Bank Directory")
    bnka = safe_read(conn, "BNKA", ["BANKS","BANKL","BANKA","STRAS","ORT01","SWIFT"],
                     f"BANKS = '{BANKS}' AND BANKL = '{BANKL}'")
    if not bnka:
        status(2, f"Bank directory NOT FOUND for {BANKS}/{BANKL}", "FAIL")
    else:
        b = bnka[0]
        status(2, f"Bank={b.get('BANKA','').strip()}, SWIFT={b.get('SWIFT','').strip()}, City={b.get('ORT01','').strip()}")

    # CHECK 3: T012K
    print(f"\nCHECK 3: T012K Bank Accounts")
    t012k = safe_read(conn, "T012K", ["BUKRS","HBKID","HKTID","BANKN","WAERS","HKONT"],
                      f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t012k:
        status(3, f"No accounts found", "FAIL")
        conn.close()
        return results

    accounts = []
    all_gls = []
    gl_type = {}
    gl_currency = {}
    for row in t012k:
        hktid = row.get("HKTID","").strip()
        bankn = row.get("BANKN","").strip()
        waers = row.get("WAERS","").strip()
        hkont = row.get("HKONT","").strip()
        clearing = derive_clearing_gl(hkont)
        accounts.append({"hktid": hktid, "bankn": bankn, "waers": waers,
                         "hkont": hkont, "clearing_gl": clearing})
        status(3, f"AcctID={hktid}: BankAcct={bankn}, {waers}, GL={hkont}, Clearing={clearing}")
        for gl, gtype in [(hkont, "bank"), (clearing, "clearing")]:
            if gl and gl not in all_gls:
                all_gls.append(gl)
                gl_type[gl] = gtype
                gl_currency[gl] = waers

    # CHECK 4: T012T
    print(f"\nCHECK 4: T012T Descriptions")
    t012t = safe_read(conn, "T012T", ["BUKRS","HBKID","HKTID","TEXT1","SPRAS"],
                      f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t012t:
        status(4, "No descriptions", "WARN")
    else:
        for row in t012t:
            status(4, f"{row.get('HKTID','').strip()} ({row.get('SPRAS','').strip()}): {row.get('TEXT1','').strip()}")

    # CHECK 5: SKA1
    print(f"\nCHECK 5: SKA1 Chart of Accounts")
    for gl in all_gls:
        ska1 = safe_read(conn, "SKA1", ["KTOPL","SAKNR","KTOKS","XBILK"],
                         f"KTOPL = '{KTOPL}' AND SAKNR = '{gl}'")
        if not ska1:
            status(5, f"GL {gl}: NOT FOUND", "FAIL")
            continue
        s = ska1[0]
        ktoks = s.get("KTOKS","").strip()
        xbilk = s.get("XBILK","").strip()
        issues = []
        if ktoks != "BANK": issues.append(f"KTOKS={ktoks}")
        if xbilk != "X": issues.append(f"XBILK={xbilk}")
        if issues:
            status(5, f"GL {gl}: {', '.join(issues)} (expected BANK/X)", "FAIL")
        else:
            status(5, f"GL {gl}: KTOKS=BANK, XBILK=X")

    # CHECK 6: SKB1
    print(f"\nCHECK 6: SKB1 Company Code Level")
    for gl in all_gls:
        skb1 = safe_read(conn, "SKB1",
                         ["BUKRS","SAKNR","FDLEV","ZUAWA","XKRES","XGKON",
                          "FIPOS","FSTAG","XOPVW","HBKID","HKTID","WAERS","XINTB"],
                         f"BUKRS = '{BUKRS}' AND SAKNR = '{gl}'")
        if not skb1:
            status(6, f"GL {gl}: NOT FOUND in SKB1", "FAIL")
            continue
        s = skb1[0]
        gtype = gl_type.get(gl, "bank")
        issues = []
        if gtype == "bank":
            exp = {"FDLEV":"B0","ZUAWA":"027","XKRES":"X","XGKON":"X","FIPOS":"BANK","FSTAG":"UN03","XINTB":"X"}
        else:
            exp = {"FDLEV":"B1","ZUAWA":"Z01","XKRES":"X","XGKON":"X","XOPVW":"X","FIPOS":"BANK","FSTAG":"UN03","XINTB":"X"}
        for field, expected in exp.items():
            actual = s.get(field,"").strip()
            if actual != expected:
                issues.append(f"{field}={actual}(exp {expected})")
        # HBKID check
        actual_hbkid = s.get("HBKID","").strip()
        if actual_hbkid and actual_hbkid != HBKID:
            issues.append(f"HBKID={actual_hbkid}(exp {HBKID})")
        elif not actual_hbkid:
            issues.append("HBKID=empty")
        if issues:
            status(6, f"GL {gl} ({gtype}): {', '.join(issues)}", "FAIL")
        else:
            status(6, f"GL {gl} ({gtype}): all fields OK, HBKID={actual_hbkid}")

    # CHECK 7: SKAT
    print(f"\nCHECK 7: SKAT Texts")
    for gl in all_gls:
        skat = safe_read(conn, "SKAT", ["SPRAS","KTOPL","SAKNR","TXT20","TXT50"],
                         f"KTOPL = '{KTOPL}' AND SAKNR = '{gl}'")
        if not skat:
            status(7, f"GL {gl}: NO texts", "FAIL")
            continue
        langs = [r.get("SPRAS","").strip() for r in skat]
        en = [r for r in skat if r.get("SPRAS","").strip() == "E"]
        txt = en[0].get("TXT50","").strip() if en else ""
        if "E" in langs:
            status(7, f"GL {gl}: langs={langs}, EN={txt}")
        else:
            status(7, f"GL {gl}: missing English (langs={langs})", "WARN")

    # CHECK 8: TIBAN
    print(f"\nCHECK 8: TIBAN")
    tiban = safe_read(conn, "TIBAN", ["BUKRS","HBKID","HKTID","IBAN"],
                      f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not tiban:
        status(8, "No IBAN entries", "WARN")
    else:
        found = set()
        for row in tiban:
            hktid = row.get("HKTID","").strip()
            iban = row.get("IBAN","").strip()
            found.add(hktid)
            status(8, f"{hktid}: IBAN={iban}")
        for a in accounts:
            if a["hktid"] not in found:
                status(8, f"{a['hktid']}: NO IBAN", "WARN")

    # CHECK 9: T030H (OBA1)
    print(f"\nCHECK 9: T030H OBA1")
    for gl in all_gls:
        gtype = gl_type.get(gl, "bank")
        currency = gl_currency.get(gl, "USD")
        t030h = safe_read(conn, "T030H",
                          ["KTOPL","HKONT","CURTP","LKORR","LSREA","LHREA","LSBEW","LHBEW"],
                          f"KTOPL = '{KTOPL}' AND HKONT = '{gl}'")
        needs_entry = (gtype == "clearing" and currency != "USD")
        if not t030h:
            if needs_entry:
                status(9, f"GL {gl} ({gtype}/{currency}): MISSING (required for non-USD clearing)", "FAIL")
            else:
                status(9, f"GL {gl} ({gtype}/{currency}): no entry (optional)")
        else:
            row = t030h[0]
            f = {k: row.get(k,"").strip() for k in ["CURTP","LKORR","LSREA","LHREA","LSBEW","LHBEW"]}
            issues = []
            if not f["LKORR"] or f["LKORR"] == "0000000000":
                issues.append(f"LKORR=empty(exp {gl})")
            if not f["LSBEW"] or f["LSBEW"] == "0000000000":
                issues.append("LSBEW=empty(exp 0006045011)")
            if not f["LHBEW"] or f["LHBEW"] == "0000000000":
                issues.append("LHBEW=empty(exp 0007045011)")
            if not f["LSREA"] or f["LSREA"] == "0000000000":
                issues.append("LSREA=empty")
            if not f["LHREA"] or f["LHREA"] == "0000000000":
                issues.append("LHREA=empty")
            if issues:
                status(9, f"GL {gl} ({gtype}/{currency}): {', '.join(issues)}", "FAIL")
            else:
                status(9, f"GL {gl} ({gtype}/{currency}): LKORR={f['LKORR']}, LSREA={f['LSREA']}, LHREA={f['LHREA']}, LSBEW={f['LSBEW']}, LHBEW={f['LHBEW']}")

    # CHECK 10: FDSB Cash Management
    print(f"\nCHECK 10: FDSB Cash Management")
    fdsb = safe_read(conn, "FDSB", ["BUKRS","HBKID","HKTID","FDTEXT"],
                     f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not fdsb:
        status(10, "No cash management entries", "WARN")
    else:
        for row in fdsb:
            status(10, f"{row.get('HKTID','').strip()}: {row.get('FDTEXT','').strip()}")

    # CHECK 11: T035D EBS
    print(f"\nCHECK 11: T035D Electronic Bank Statement")
    t035d = safe_read(conn, "T035D", ["BUKRS","DISKB","BNKKO"],
                      f"BUKRS = '{BUKRS}'")
    if t035d is None:
        status(11, "T035D not accessible", "WARN")
    else:
        matched = [r for r in t035d if HBKID in r.get("DISKB","")]
        if not matched:
            status(11, f"No EBS config for {HBKID}", "WARN")
        else:
            for row in matched:
                status(11, f"DISKB={row.get('DISKB','').strip()}, GL={row.get('BNKKO','').strip()}")

    # CHECK 12: T028B Posting Rules
    print(f"\nCHECK 12: T028B Bank Statement Posting Rules")
    t028b = safe_read(conn, "T028B", ["BANKL","KTONR","VGTYP","BNKKO"],
                      f"BANKL = '{BANKL}'")
    if not t028b:
        status(12, f"No posting rules for bank key {BANKL}", "WARN")
    else:
        for row in t028b:
            status(12, f"BankKey={BANKL}, BankAcct={row.get('KTONR','').strip()}, "
                       f"Format={row.get('VGTYP','').strip()}, CM={row.get('BNKKO','').strip()}")

    # CHECK 13: T018V
    print(f"\nCHECK 13: T018V Receiving Bank Clearing")
    t018v = safe_read(conn, "T018V", ["BUKRS","HBKID","HKTID","GEHVK","WAERS","ZLSCH"],
                      f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t018v:
        t018v_all = safe_read(conn, "T018V", ["BUKRS","HBKID","HKTID","GEHVK","WAERS","ZLSCH"],
                              f"BUKRS = '{BUKRS}'")
        if t018v_all:
            t018v = [r for r in t018v_all if r.get("HBKID","").strip() == HBKID]
    if not t018v:
        status(13, f"No T018V entries for {HBKID}", "WARN")
    else:
        for row in t018v:
            status(13, f"{row.get('HKTID','').strip()} ({row.get('WAERS','').strip()}): "
                       f"Clearing={row.get('GEHVK','').strip()}, PayMethod={row.get('ZLSCH','').strip()}")

    # CHECK 14: T042I
    print(f"\nCHECK 14: T042I Payment Bank Determination")
    t042i = safe_read(conn, "T042I", ["ZBUKR","ZLSCH","HBKID","HKTID","UKONT","WAERS"],
                      f"ZBUKR = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t042i:
        status(14, f"No payment bank determination for {HBKID}", "WARN")
    else:
        for row in t042i:
            status(14, f"PayMethod={row.get('ZLSCH','').strip()}, AcctID={row.get('HKTID','').strip()}, "
                       f"{row.get('WAERS','').strip()}, Clearing={row.get('UKONT','').strip()}")

    # CHECK 15: SETLEAF
    print(f"\nCHECK 15: SETLEAF YBANK Sets")
    setleaf = safe_read(conn, "SETLEAF", ["SETNAME","VALOPTION","VALFROM","VALTO"],
                        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")
    if not setleaf:
        status(15, "No YBANK sets found", "WARN")
    else:
        sets = {}
        for row in setleaf:
            sn = row.get("SETNAME","").strip()
            if sn not in sets:
                sets[sn] = []
            sets[sn].append({"opt": row.get("VALOPTION","").strip(),
                             "from": row.get("VALFROM","").strip(),
                             "to": row.get("VALTO","").strip()})
        bank_gls = [gl for gl in all_gls if gl_type.get(gl) == "bank"]
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
                        found_in.append(f"{sn}(range)")
                        break
            if found_in:
                status(15, f"GL {gl}: in {found_in}")
            else:
                status(15, f"GL {gl}: NOT in any YBANK set", "FAIL")

    # SUMMARY
    print(f"\n{'='*70}")
    print(f"  {system} SUMMARY: {results['pass']} PASS / {results['fail']} FAIL / {results['warn']} WARN")
    print(f"{'='*70}")

    conn.close()
    return results


def main():
    d01 = run_check("D01")
    p01 = run_check("P01")

    # Cross-system comparison
    print(f"\n{'='*70}")
    print(f"  CROSS-SYSTEM COMPARISON D01 vs P01")
    print(f"{'='*70}")

    d01_map = {(c["id"], c["msg"].split(":")[0] if ":" in c["msg"] else c["msg"]): c
               for c in d01["checks"]}
    p01_map = {(c["id"], c["msg"].split(":")[0] if ":" in c["msg"] else c["msg"]): c
               for c in p01["checks"]}

    diffs = []
    for key in sorted(set(list(d01_map.keys()) + list(p01_map.keys()))):
        d = d01_map.get(key)
        p = p01_map.get(key)
        if d and p and d["level"] != p["level"]:
            diffs.append(f"  Check {key[0]} [{key[1]}]: D01={d['level']} / P01={p['level']}")
            diffs.append(f"    D01: {d['msg']}")
            diffs.append(f"    P01: {p['msg']}")

    if diffs:
        print(f"\n  Differences in check results:")
        for d in diffs:
            print(d)
    else:
        print(f"\n  All checks returned same results in both systems.")

    print(f"\n  D01: {d01['pass']} PASS / {d01['fail']} FAIL / {d01['warn']} WARN")
    print(f"  P01: {p01['pass']} PASS / {p01['fail']} FAIL / {p01['warn']} WARN")


if __name__ == "__main__":
    main()
