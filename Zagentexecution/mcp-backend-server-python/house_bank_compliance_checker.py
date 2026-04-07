"""
house_bank_compliance_checker.py
================================
Validates ALL configuration steps for a SAP house bank against proven patterns.
READ-ONLY — no writes to SAP.

Usage:
    python house_bank_compliance_checker.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection, rfc_read_paginated

# ── INPUT PARAMETERS ──────────────────────────────────────────────
SYSTEM = "D01"
BUKRS  = "UNES"
KTOPL  = "UNES"
HBKID  = "UBA01"
# ──────────────────────────────────────────────────────────────────

# Counters
PASS_COUNT = 0
FAIL_COUNT = 0
WARN_COUNT = 0
FAIL_ITEMS = []


def status(check_id, msg, level="PASS"):
    global PASS_COUNT, FAIL_COUNT, WARN_COUNT
    tag = {"PASS": "PASS", "FAIL": "FAIL", "WARN": "WARN"}.get(level, level)
    print(f"  [{tag}] {msg}")
    if level == "PASS":
        PASS_COUNT += 1
    elif level == "FAIL":
        FAIL_COUNT += 1
        FAIL_ITEMS.append(f"CHECK {check_id}: {msg}")
    elif level == "WARN":
        WARN_COUNT += 1


def safe_read(conn, table, fields, where, label=""):
    """Read table with graceful handling of TABLE_NOT_AVAILABLE."""
    from pyrfc import RFCError
    try:
        return rfc_read_paginated(conn, table, fields, where,
                                  batch_size=5000, throttle=0.5)
    except RFCError as e:
        if "TABLE_NOT_AVAILABLE" in str(e) or "NOT_AUTHORIZED" in str(e):
            print(f"  [WARN] {table}: not available or not authorized")
            return None
        raise


def derive_clearing_gl(hkont):
    """Derive clearing G/L from bank G/L: 10xxxxx → 11xxxxx.

    SAP G/L accounts are 10-digit with leading zeros.
    The significant part is 7 digits: e.g., 0001065421 → significant=1065421.
    Replace first digit of significant part: 1→1 becomes 10→11.
    So 0001065421 → 0001165421.
    """
    full = hkont.strip()
    # Strip leading zeros to find the significant number
    sig = full.lstrip('0')
    if not sig:
        return full
    # The significant number starts with '10' for bank accounts
    # Replace '10' prefix with '11' to get clearing
    if sig.startswith('10'):
        new_sig = '11' + sig[2:]
        # Pad back with leading zeros to original length
        return new_sig.zfill(len(full))
    return full  # Can't derive — not a 10xxxxx pattern


def run():
    global PASS_COUNT, FAIL_COUNT, WARN_COUNT

    print("=" * 70)
    print(f"  HOUSE BANK COMPLIANCE CHECK — {HBKID} / {BUKRS} / {SYSTEM}")
    print("=" * 70)

    conn = get_connection(SYSTEM)

    # ── CHECK 1: T012 — House Bank exists ─────────────────────────
    print(f"\nCHECK 1: T012 House Bank Master")
    t012 = safe_read(conn, "T012",
                     ["BUKRS", "HBKID", "BANKS", "BANKL"],
                     f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if t012 is None:
        status(1, "T012 table not available", "FAIL")
        conn.close()
        return
    if not t012:
        status(1, f"House bank {HBKID} NOT FOUND in {BUKRS}", "FAIL")
        conn.close()
        return

    hb = t012[0]
    BANKS = hb.get("BANKS", "").strip()
    BANKL = hb.get("BANKL", "").strip()
    status(1, f"House bank {HBKID} exists in {BUKRS} — "
              f"Country: {BANKS}, Bank Key: {BANKL}")

    # ── CHECK 2: BNKA — Bank Directory ────────────────────────────
    print(f"\nCHECK 2: BNKA Bank Directory")
    bnka = safe_read(conn, "BNKA",
                     ["BANKS", "BANKL", "BANKA", "STRAS", "ORT01", "SWIFT"],
                     f"BANKS = '{BANKS}' AND BANKL = '{BANKL}'")
    if not bnka:
        status(2, f"Bank directory entry NOT FOUND for {BANKS}/{BANKL}", "FAIL")
    else:
        b = bnka[0]
        status(2, f"Bank: {b.get('BANKA','').strip()}")
        print(f"         Street: {b.get('STRAS','').strip()}")
        print(f"         City: {b.get('ORT01','').strip()}")
        print(f"         SWIFT: {b.get('SWIFT','').strip()}")

    # ── CHECK 3: T012K — Bank Accounts ────────────────────────────
    print(f"\nCHECK 3: T012K Bank Accounts")
    t012k = safe_read(conn, "T012K",
                      ["BUKRS", "HBKID", "HKTID", "BANKN",
                       "WAERS", "HKONT", "FDGRP"],
                      f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    # Retry with fewer fields if first attempt failed (field names may differ)
    if t012k is None or (isinstance(t012k, list) and len(t012k) == 0):
        t012k = safe_read(conn, "T012K",
                          ["BUKRS", "HBKID", "HKTID", "BANKN", "WAERS", "HKONT"],
                          f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t012k:
        status(3, f"No bank accounts found for {HBKID}", "FAIL")
        conn.close()
        return

    accounts = []  # list of dicts with hktid, bankn, waers, hkont, clearing_gl
    for row in t012k:
        hktid = row.get("HKTID", "").strip()
        bankn = row.get("BANKN", "").strip()
        waers = row.get("WAERS", "").strip()
        hkont = row.get("HKONT", "").strip()
        clearing = derive_clearing_gl(hkont)
        accounts.append({
            "hktid": hktid, "bankn": bankn, "waers": waers,
            "hkont": hkont, "clearing_gl": clearing,
        })
        status(3, f"Account {hktid}: Bank Acct={bankn}, "
                  f"Currency={waers}, G/L={hkont}, Clearing={clearing}")

    # Collect all G/L accounts for subsequent checks
    all_gls = []
    gl_type = {}  # gl -> "bank" or "clearing"
    gl_currency = {}  # gl -> currency
    for a in accounts:
        if a["hkont"] and a["hkont"] not in all_gls:
            all_gls.append(a["hkont"])
            gl_type[a["hkont"]] = "bank"
            gl_currency[a["hkont"]] = a["waers"]
        if a["clearing_gl"] and a["clearing_gl"] != a["hkont"] and a["clearing_gl"] not in all_gls:
            all_gls.append(a["clearing_gl"])
            gl_type[a["clearing_gl"]] = "clearing"
            gl_currency[a["clearing_gl"]] = a["waers"]

    print(f"\n  All G/L accounts to check: {all_gls}")

    # ── CHECK 4: T012T — Account Descriptions ────────────────────
    print(f"\nCHECK 4: T012T Account Descriptions")
    t012t = safe_read(conn, "T012T",
                      ["BUKRS", "HBKID", "HKTID", "TEXT1", "SPRAS"],
                      f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t012t:
        status(4, "No descriptions found in T012T", "WARN")
    else:
        for row in t012t:
            hktid = row.get("HKTID", "").strip()
            text1 = row.get("TEXT1", "").strip()
            spras = row.get("SPRAS", "").strip()
            status(4, f"Account {hktid} ({spras}): {text1}")

    # ── CHECK 5: SKA1 — Chart of Accounts level ──────────────────
    print(f"\nCHECK 5: SKA1 Chart of Accounts Level")
    for gl in all_gls:
        ska1 = safe_read(conn, "SKA1",
                         ["KTOPL", "SAKNR", "KTOKS", "XBILK", "GVTYP", "BILKT"],
                         f"KTOPL = '{KTOPL}' AND SAKNR = '{gl}'")
        if not ska1:
            status(5, f"G/L {gl}: NOT FOUND in SKA1", "FAIL")
            continue
        s = ska1[0]
        ktoks = s.get("KTOKS", "").strip()
        xbilk = s.get("XBILK", "").strip()
        ok = True
        issues = []
        if ktoks != "BANK":
            issues.append(f"KTOKS={ktoks} (expected BANK)")
            ok = False
        if xbilk != "X":
            issues.append(f"XBILK={xbilk} (expected X)")
            ok = False
        if ok:
            status(5, f"G/L {gl}: KTOKS=BANK, XBILK=X")
        else:
            status(5, f"G/L {gl}: {', '.join(issues)}", "FAIL")

    # ── CHECK 6: SKB1 — Company Code level ────────────────────────
    print(f"\nCHECK 6: SKB1 Company Code Level")
    for gl in all_gls:
        skb1 = safe_read(conn, "SKB1",
                         ["BUKRS", "SAKNR", "FDLEV", "ZUAWA", "XKRES",
                          "XGKON", "FIPOS", "FSTAG", "XOPVW", "HBKID",
                          "HKTID", "WAERS", "MWSKZ", "MITKZ"],
                         f"BUKRS = '{BUKRS}' AND SAKNR = '{gl}'")
        if not skb1:
            status(6, f"G/L {gl}: NOT FOUND in SKB1", "FAIL")
            continue
        s = skb1[0]
        gtype = gl_type.get(gl, "bank")
        issues = []

        # Expected values depend on bank vs clearing
        if gtype == "bank":
            exp = {"FDLEV": "B0", "ZUAWA": "027", "XKRES": "X",
                   "XGKON": "X", "FIPOS": "BANK", "FSTAG": "UN03"}
        else:
            exp = {"FDLEV": "B1", "ZUAWA": "Z01", "XKRES": "X",
                   "XGKON": "X", "XOPVW": "X", "FIPOS": "BANK", "FSTAG": "UN03"}

        for field, expected in exp.items():
            actual = s.get(field, "").strip()
            if actual != expected:
                issues.append(f"{field}={actual} (exp {expected})")

        # Check HBKID/HKTID assignment
        actual_hbkid = s.get("HBKID", "").strip()
        actual_hktid = s.get("HKTID", "").strip()
        if actual_hbkid and actual_hbkid != HBKID:
            issues.append(f"HBKID={actual_hbkid} (exp {HBKID})")
        if gtype == "bank":
            # Bank G/L should have HBKID assigned
            if not actual_hbkid:
                issues.append("HBKID not assigned")

        # Check currency
        exp_waers = gl_currency.get(gl, "")
        actual_waers = s.get("WAERS", "").strip()
        if exp_waers and actual_waers and actual_waers != exp_waers:
            issues.append(f"WAERS={actual_waers} (exp {exp_waers})")

        if issues:
            status(6, f"G/L {gl} ({gtype}): {', '.join(issues)}", "FAIL")
        else:
            status(6, f"G/L {gl} ({gtype}): all fields OK — "
                      f"FDLEV={s.get('FDLEV','').strip()}, "
                      f"ZUAWA={s.get('ZUAWA','').strip()}, "
                      f"HBKID={actual_hbkid}")

    # ── CHECK 7: SKAT — Texts ────────────────────────────────────
    print(f"\nCHECK 7: SKAT G/L Account Texts")
    for gl in all_gls:
        skat = safe_read(conn, "SKAT",
                         ["SPRAS", "KTOPL", "SAKNR", "TXT20", "TXT50"],
                         f"KTOPL = '{KTOPL}' AND SAKNR = '{gl}'")
        if not skat:
            status(7, f"G/L {gl}: NO texts in SKAT", "FAIL")
            continue
        langs = [r.get("SPRAS", "").strip() for r in skat]
        has_e = "E" in langs
        txt20 = ""
        txt50 = ""
        for r in skat:
            if r.get("SPRAS", "").strip() == "E":
                txt20 = r.get("TXT20", "").strip()
                txt50 = r.get("TXT50", "").strip()
        if has_e:
            status(7, f"G/L {gl}: langs={langs}, TXT20={txt20}")
            print(f"         TXT50={txt50}")
        else:
            status(7, f"G/L {gl}: missing English text (langs={langs})", "WARN")

    # ── CHECK 8: TIBAN — IBAN ─────────────────────────────────────
    print(f"\nCHECK 8: TIBAN IBAN Entries")
    tiban = safe_read(conn, "TIBAN",
                      ["BUKRS", "HBKID", "HKTID", "BANKL", "BANKN", "IBAN"],
                      f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not tiban:
        status(8, f"No IBAN entries found for {HBKID}", "WARN")
    else:
        checked_hktids = {a["hktid"] for a in accounts}
        found_hktids = set()
        for row in tiban:
            hktid = row.get("HKTID", "").strip()
            iban = row.get("IBAN", "").strip()
            found_hktids.add(hktid)
            status(8, f"Account {hktid}: IBAN={iban}")
        missing = checked_hktids - found_hktids
        for m in missing:
            status(8, f"Account {m}: NO IBAN entry", "WARN")

    # ── CHECK 9: T030H — OBA1 Exchange Rate Differences ──────────
    print(f"\nCHECK 9: T030H Exchange Rate Differences (OBA1)")
    for gl in all_gls:
        gtype = gl_type.get(gl, "bank")
        currency = gl_currency.get(gl, "USD")
        t030h = safe_read(conn, "T030H",
                          ["KTOPL", "HKONT", "CURTP", "LKORR", "LSREA", "LHREA", "LSBEW", "LHBEW"],
                          f"KTOPL = '{KTOPL}' AND HKONT = '{gl}'")
        # Rule: Only non-USD clearing accounts MUST have entries
        needs_entry = (gtype == "clearing" and currency != "USD")
        if not t030h:
            if needs_entry:
                status(9, f"G/L {gl} ({gtype}, {currency}): "
                          f"MISSING T030H entry (required for non-USD clearing)", "FAIL")
            else:
                status(9, f"G/L {gl} ({gtype}, {currency}): "
                          f"no T030H entry (optional)")
        else:
            row = t030h[0]
            lkorr = row.get("LKORR", "").strip()
            lsrea = row.get("LSREA", "").strip()
            lhrea = row.get("LHREA", "").strip()
            lsbew = row.get("LSBEW", "").strip()
            lhbew = row.get("LHBEW", "").strip()
            issues = []
            if lsrea and lsrea != "0006045011":
                issues.append(f"LSREA={lsrea} (exp 0006045011)")
            if lhrea and lhrea != "0007045011":
                issues.append(f"LHREA={lhrea} (exp 0007045011)")
            if not lkorr or lkorr == "0000000000":
                issues.append(f"LKORR missing (should be {gl})")
            if not lsbew or lsbew == "0000000000":
                issues.append(f"LSBEW missing (should be 0006045011)")
            if not lhbew or lhbew == "0000000000":
                issues.append(f"LHBEW missing (should be 0007045011)")
            if issues:
                status(9, f"G/L {gl} ({gtype}, {currency}): {', '.join(issues)}", "FAIL")
            else:
                status(9, f"G/L {gl} ({gtype}, {currency}): "
                          f"LSREA={lsrea}, LHREA={lhrea}")

    # ── CHECK 10: Cash Management Account Name ───────────────────
    print(f"\nCHECK 10: Cash Management Account Names")
    # Try FDSB table (bank account planning)
    fdsb = safe_read(conn, "FDSB",
                     ["BUKRS", "HBKID", "HKTID", "DSART", "FDTEXT"],
                     f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if fdsb is None:
        # Try with fewer fields
        fdsb = safe_read(conn, "FDSB",
                         ["BUKRS", "HBKID", "HKTID", "FDTEXT"],
                         f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not fdsb:
        # Try T035 (Cash mgmt positions)
        t035 = safe_read(conn, "T035",
                         ["FDLEV", "FDGRP"],
                         f"FDLEV = 'B0'")
        if t035:
            status(10, f"T035 cash mgmt levels found ({len(t035)} entries)", "WARN")
            for r in t035[:5]:
                print(f"         {r}")
        else:
            status(10, "Cash management tables not accessible (FDSB, T035)", "WARN")
    else:
        for row in fdsb:
            hktid = row.get("HKTID", "").strip()
            fdtext = row.get("FDTEXT", "").strip()
            status(10, f"Account {hktid}: {fdtext}")

    # ── CHECK 11: T035D — Electronic Bank Statement ──────────────
    print(f"\nCHECK 11: Electronic Bank Statement Config")
    t035d = safe_read(conn, "T035D",
                      ["BUKRS", "DISKB", "BNKKO"],
                      f"BUKRS = '{BUKRS}'")
    if t035d is None:
        status(11, "T035D table not accessible", "WARN")
    else:
        # Filter for our house bank by DISKB pattern (e.g., UBA01-USD1)
        matched = [r for r in t035d
                   if HBKID in r.get("DISKB", "")]
        if not matched:
            status(11, f"No EBS config for {HBKID} in T035D", "WARN")
        else:
            for row in matched:
                diskb = row.get("DISKB", "").strip()
                bnkko = row.get("BNKKO", "").strip()
                status(11, f"EBS: DISKB={diskb}, G/L={bnkko}")

    # ── CHECK 12: T028B — Bank Statement Posting Rules ───────────
    print(f"\nCHECK 12: T028B Bank Statement Posting Rules")
    t028b = safe_read(conn, "T028B",
                      ["BANKL", "KTONR", "VGTYP", "BNKKO", "ANZTG"],
                      f"BANKL = '{BANKL}'")
    if not t028b:
        status(12, f"No posting rules found for bank key {BANKL}", "WARN")
    else:
        for row in t028b:
            vgtyp = row.get("VGTYP", "").strip()
            ktonr = row.get("KTONR", "").strip()
            bnkko = row.get("BNKKO", "").strip()
            status(12, f"Bank Key={BANKL}, BankAcct={ktonr}, "
                      f"Format={vgtyp}, CM={bnkko}")

    # ── CHECK 13: T018V — Receiving Bank Clearing Accounts ───────
    print(f"\nCHECK 13: T018V Receiving Bank / Clearing Accounts")
    # Try direct filter first
    t018v = safe_read(conn, "T018V",
                      ["BUKRS", "HBKID", "HKTID", "GEHVK", "WAERS", "ZLSCH"],
                      f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t018v:
        # Read ALL for BUKRS and filter in Python
        t018v_all = safe_read(conn, "T018V",
                              ["BUKRS", "HBKID", "HKTID", "GEHVK", "WAERS", "ZLSCH"],
                              f"BUKRS = '{BUKRS}'")
        if t018v_all is None:
            status(13, "T018V table not accessible", "WARN")
        elif not t018v_all:
            status(13, f"No T018V entries for {BUKRS}", "WARN")
        else:
            # Filter for our HBKID
            matched = [r for r in t018v_all
                       if r.get("HBKID", "").strip() == HBKID]
            if matched:
                t018v = matched
            else:
                status(13, f"No T018V entries for {HBKID} "
                          f"(total {len(t018v_all)} entries for {BUKRS})", "WARN")
                # Show all house banks found
                hbs = set(r.get("HBKID", "").strip() for r in t018v_all)
                print(f"         House banks in T018V: {sorted(hbs)}")

    if t018v:
        for row in t018v:
            hktid = row.get("HKTID", "").strip()
            ukont = row.get("GEHVK", "").strip()
            waers = row.get("WAERS", "").strip()
            status(13, f"Account {hktid} ({waers}): Clearing G/L={ukont}")
            # Check 10→11 pattern
            for a in accounts:
                if a["hktid"] == hktid:
                    if ukont and a["clearing_gl"] and ukont != a["clearing_gl"]:
                        status(13, f"  Clearing G/L mismatch: T018V={ukont}, "
                                  f"derived={a['clearing_gl']}", "WARN")

    # ── CHECK 14: T042I — Payment Bank Determination ─────────────
    print(f"\nCHECK 14: T042I Payment Bank Determination")
    t042i = safe_read(conn, "T042I",
                      ["ZBUKR", "ZLSCH", "HBKID", "HKTID",
                       "UKONT", "WAERS"],
                      f"ZBUKR = '{BUKRS}' AND HBKID = '{HBKID}'")
    if t042i is None:
        t042i = safe_read(conn, "T042I",
                          ["ZBUKR", "ZLSCH", "HBKID", "HKTID", "UKONT", "WAERS"],
                          f"ZBUKR = '{BUKRS}' AND HBKID = '{HBKID}'")
    if not t042i:
        status(14, f"No payment bank determination for {HBKID}", "WARN")
    else:
        for row in t042i:
            zlsch = row.get("ZLSCH", "").strip()
            hktid = row.get("HKTID", "").strip()
            ukont = row.get("GEHVK", "").strip()
            waers = row.get("WAERS", "").strip()
            status(14, f"Pay method={zlsch}, AcctID={hktid}, "
                      f"Currency={waers}, Clearing={ukont}")

    # ── CHECK 15: SETLEAF — GS02 Account Sets (YBANK) ────────────
    print(f"\nCHECK 15: SETLEAF Account Sets (YBANK)")
    # SETLEAF requires SETCLASS filter to avoid TABLE_WITHOUT_DATA
    setleaf = safe_read(conn, "SETLEAF",
                        ["SETNAME", "VALOPTION", "VALFROM", "VALTO"],
                        "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")
    if not setleaf:
        status(15, "No YBANK account sets found in SETLEAF", "WARN")
    else:
        sets = {}
        for row in setleaf:
            sn = row.get("SETNAME", "").strip()
            vfrom = row.get("VALFROM", "").strip()
            vto = row.get("VALTO", "").strip()
            opt = row.get("VALOPTION", "").strip()
            if sn not in sets:
                sets[sn] = []
            sets[sn].append((opt, vfrom, vto))

        print(f"  Found {len(sets)} YBANK sets with {len(setleaf)} entries")
        bank_gls = [gl for gl in all_gls if gl_type.get(gl) == "bank"]
        for gl in bank_gls:
            gl_short = gl.lstrip("0")
            found_in = []
            for sn, entries in sets.items():
                for opt, vfrom, vto in entries:
                    vf = vfrom.lstrip("0")
                    vt = vto.lstrip("0") if vto else ""
                    if opt == "EQ" and vf == gl_short:
                        found_in.append(sn)
                        break
                    elif opt == "BT" and vf <= gl_short <= vt:
                        found_in.append(sn)
                        break
            if found_in:
                status(15, f"G/L {gl}: found in sets {found_in}")
            else:
                status(15, f"G/L {gl}: NOT in any YBANK set", "FAIL")

    # ── SUMMARY ───────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print(f"  SUMMARY: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL / {WARN_COUNT} WARN")
    print("=" * 70)
    if FAIL_ITEMS:
        print("\nFAIL items:")
        for item in FAIL_ITEMS:
            print(f"  - {item}")
    if FAIL_COUNT == 0:
        print(f"\n  House bank {HBKID} is FULLY COMPLIANT.")
    print()

    conn.close()


if __name__ == "__main__":
    run()
