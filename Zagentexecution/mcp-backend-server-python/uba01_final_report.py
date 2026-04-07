"""
uba01_final_report.py — Cross-system compliance report for UBA01
Compares D01 vs P01 for ALL configuration steps.
"""
import sys, os, json
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))
from rfc_helpers import get_connection

BUKRS = "UNES"
KTOPL = "UNES"
HBKID = "UBA01"
ACCTS = ["0001065421", "0001165421", "0001065424", "0001165424"]

def safe_call(conn, table, fields, where):
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
            FIELDS=[{"FIELDNAME": f} for f in fields],
            OPTIONS=[{"TEXT": where}])
        return r.get("DATA", [])
    except Exception:
        return None

def extract_system(sid):
    data = {}
    conn = get_connection(sid)

    # T012
    r = safe_call(conn, "T012", ["BUKRS","HBKID","BANKS","BANKL"],
                  f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    data["T012"] = [d.get("WA","") for d in (r or [])]

    # T012K
    r = safe_call(conn, "T012K", ["HKTID","BANKN","WAERS","HKONT"],
                  f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    data["T012K"] = [d.get("WA","") for d in (r or [])]

    # SKB1 per account
    for acct in ACCTS:
        r = safe_call(conn, "SKB1",
                      ["SAKNR","WAERS","HBKID","HKTID","FDLEV","XINTB","XOPVW","ZUAWA","FSTAG","XKRES","XGKON","FIPOS"],
                      f"BUKRS = '{BUKRS}' AND SAKNR = '{acct}'")
        data[f"SKB1_{acct}"] = [d.get("WA","") for d in (r or [])]

    # SKA1 per account
    for acct in ACCTS:
        r = safe_call(conn, "SKA1", ["SAKNR","KTOKS","XBILK"],
                      f"KTOPL = '{KTOPL}' AND SAKNR = '{acct}'")
        data[f"SKA1_{acct}"] = [d.get("WA","") for d in (r or [])]

    # SKAT per account (English)
    for acct in ACCTS:
        r = safe_call(conn, "SKAT", ["SAKNR","TXT20","TXT50"],
                      f"SPRAS = 'E' AND KTOPL = '{KTOPL}' AND SAKNR = '{acct}'")
        data[f"SKAT_{acct}"] = [d.get("WA","") for d in (r or [])]

    # T030H per account
    for acct in ACCTS:
        r = safe_call(conn, "T030H", ["HKONT","CURTP","LSREA","LHREA"],
                      f"KTOPL = '{KTOPL}' AND HKONT = '{acct}'")
        data[f"T030H_{acct}"] = [d.get("WA","") for d in (r or [])]

    # T035D
    r = safe_call(conn, "T035D", ["DISKB","BNKKO"], f"BUKRS = '{BUKRS}'")
    matched = [d.get("WA","") for d in (r or []) if HBKID in d.get("WA","")]
    data["T035D"] = matched

    # T018V (read all, filter in Python)
    r = safe_call(conn, "T018V", ["HBKID","ZLSCH","WAERS","HKTID","GEHVK"],
                  f"BUKRS = '{BUKRS}'")
    matched = [d.get("WA","") for d in (r or []) if HBKID in d.get("WA","")]
    data["T018V"] = matched

    # T042I
    r = safe_call(conn, "T042I", ["HBKID","ZLSCH","WAERS","HKTID","UKONT"],
                  f"ZBUKR = '{BUKRS}' AND HBKID = '{HBKID}'")
    data["T042I"] = [d.get("WA","") for d in (r or [])]

    # TIBAN
    r = safe_call(conn, "TIBAN", ["BANKL","BANKN","IBAN"],
                  f"BUKRS = '{BUKRS}' AND HBKID = '{HBKID}'")
    data["TIBAN"] = [d.get("WA","") for d in (r or [])]

    # SETLEAF
    r = safe_call(conn, "SETLEAF", ["SETNAME","VALOPTION","VALFROM"],
                  "SETCLASS = '0000' AND SETNAME LIKE 'YBANK%'")
    for acct in ACCTS:
        short = acct.lstrip("0")
        found = []
        for d in (r or []):
            wa = d.get("WA","")
            parts = wa.split("|")
            if len(parts) >= 3 and parts[2].strip().lstrip("0") == short:
                found.append(parts[0].strip())
        data[f"SETLEAF_{acct}"] = found

    conn.close()
    return data


def parse_pipe(wa, fields):
    parts = wa.split("|")
    result = {}
    for i, f in enumerate(fields):
        result[f] = parts[i].strip() if i < len(parts) else ""
    return result


def pf(ok):
    return "PASS" if ok else "FAIL"


def main():
    print("Extracting D01...")
    d01 = extract_system("D01")
    print("Extracting P01...")
    p01 = extract_system("P01")

    # Save raw
    with open("uba01_final_report_data.json", "w") as f:
        json.dump({"D01": d01, "P01": p01}, f, indent=2, default=str)

    CRIT = []

    print()
    print("=" * 80)
    print(f"  HOUSE BANK CONFIGURATION REPORT: {HBKID} / {BUKRS}")
    print(f"  Cross-system comparison: D01 (Development) vs P01 (Production)")
    print("=" * 80)

    # --- STEP 1: House Bank Master ---
    print("\n--- STEP 1: House Bank Master (T012) ---")
    for sid, data in [("D01", d01), ("P01", p01)]:
        exists = len(data["T012"]) > 0
        print(f"  {sid}: {'EXISTS' if exists else 'MISSING'}")
        if not exists and sid == "P01":
            CRIT.append(f"House bank {HBKID} does not exist in P01 (not yet transported)")

    # --- STEP 2: Bank Accounts ---
    print("\n--- STEP 2: Bank Accounts (T012K) ---")
    for sid, data in [("D01", d01), ("P01", p01)]:
        entries = data["T012K"]
        print(f"  {sid}: {len(entries)} accounts")
        for e in entries:
            p = parse_pipe(e, ["HKTID","BANKN","WAERS","HKONT"])
            print(f"    {p['HKTID']}: BankAcct={p['BANKN']}, Curr={p['WAERS']}, G/L={p['HKONT']}")
        if not entries and sid == "P01":
            CRIT.append(f"No bank accounts for {HBKID} in P01")

    # --- STEP 3: G/L Accounts ---
    print("\n--- STEP 3: G/L Account Master Data (SKA1 + SKB1 + SKAT) ---")
    skb1_fields = ["SAKNR","WAERS","HBKID","HKTID","FDLEV","XINTB","XOPVW","ZUAWA","FSTAG","XKRES","XGKON","FIPOS"]
    for acct in ACCTS:
        short = acct.lstrip("0")
        is_clr = short.startswith("11")
        print(f"\n  Account {short} ({'clearing/sub-bank' if is_clr else 'bank'}):")
        print(f"  {'Field':<20} {'D01':<25} {'P01':<25} {'Match':<8}")
        print(f"  {'-'*20} {'-'*25} {'-'*25} {'-'*8}")

        # SKA1
        for sid, data in [("D01", d01), ("P01", p01)]:
            ska1 = data.get(f"SKA1_{acct}", [])
            if not ska1:
                print(f"  {'SKA1':<20} {'MISSING' if sid=='D01' else '':<25} {'MISSING' if sid=='P01' else '':<25}")
                if sid == "P01":
                    CRIT.append(f"Account {short}: MISSING from SKA1 in P01")

        d_ska1 = parse_pipe(d01.get(f"SKA1_{acct}", [""])[0], ["SAKNR","KTOKS","XBILK"]) if d01.get(f"SKA1_{acct}") else {}
        p_ska1 = parse_pipe(p01.get(f"SKA1_{acct}", [""])[0], ["SAKNR","KTOKS","XBILK"]) if p01.get(f"SKA1_{acct}") else {}
        if d_ska1 and p_ska1:
            for fld in ["KTOKS", "XBILK"]:
                dv = d_ska1.get(fld, "")
                pv = p_ska1.get(fld, "")
                match = dv == pv
                print(f"  {'SKA1.'+fld:<20} {dv:<25} {pv:<25} {pf(match):<8}")
                if not match:
                    CRIT.append(f"Account {short}: SKA1.{fld} differs D01={dv} vs P01={pv}")

        # SKB1
        d_skb1 = parse_pipe(d01.get(f"SKB1_{acct}", [""])[0], skb1_fields) if d01.get(f"SKB1_{acct}") else {}
        p_skb1 = parse_pipe(p01.get(f"SKB1_{acct}", [""])[0], skb1_fields) if p01.get(f"SKB1_{acct}") else {}

        if not d_skb1:
            print(f"  {'SKB1':<20} {'MISSING':<25}")
            CRIT.append(f"Account {short}: MISSING from SKB1 in D01")
        if not p_skb1:
            print(f"  {'SKB1':<20} {'':<25} {'MISSING':<25}")
            CRIT.append(f"Account {short}: MISSING from SKB1 in P01")

        if d_skb1 and p_skb1:
            for fld in ["WAERS","HBKID","HKTID","FDLEV","XINTB","XOPVW","ZUAWA","FSTAG","XKRES","XGKON","FIPOS"]:
                dv = d_skb1.get(fld, "")
                pv = p_skb1.get(fld, "")
                match = dv == pv
                flag = ""
                if fld == "HBKID" and pv != HBKID and pv:
                    flag = " *** WRONG BANK ASSIGNMENT ***"
                    CRIT.append(f"Account {short}: P01 has HBKID={pv} instead of {HBKID} -- WRONG BANK ASSIGNMENT")
                print(f"  {'SKB1.'+fld:<20} {dv:<25} {pv:<25} {pf(match):<8}{flag}")
        elif d_skb1:
            for fld in skb1_fields[1:]:
                dv = d_skb1.get(fld, "")
                print(f"  {'SKB1.'+fld:<20} {dv:<25} {'---':<25}")

        # SKAT
        d_skat = parse_pipe(d01.get(f"SKAT_{acct}", [""])[0], ["SAKNR","TXT20","TXT50"]) if d01.get(f"SKAT_{acct}") else {}
        p_skat = parse_pipe(p01.get(f"SKAT_{acct}", [""])[0], ["SAKNR","TXT20","TXT50"]) if p01.get(f"SKAT_{acct}") else {}
        if d_skat or p_skat:
            for fld in ["TXT20", "TXT50"]:
                dv = d_skat.get(fld, "---") if d_skat else "---"
                pv = p_skat.get(fld, "---") if p_skat else "---"
                match = dv == pv
                print(f"  {'SKAT.'+fld:<20} {dv:<25} {pv:<25} {pf(match):<8}")

    # --- STEP 4: OBA1 ---
    print("\n--- STEP 4: OBA1 Exchange Rate Differences (T030H) ---")
    print(f"  {'Account':<15} {'D01':<35} {'P01':<35}")
    print(f"  {'-'*15} {'-'*35} {'-'*35}")
    for acct in ACCTS:
        short = acct.lstrip("0")
        d_val = d01.get(f"T030H_{acct}", [])
        p_val = p01.get(f"T030H_{acct}", [])
        d_str = d_val[0] if d_val else "MISSING"
        p_str = p_val[0] if p_val else "MISSING"
        print(f"  {short:<15} {d_str:<35} {p_str:<35}")

    # --- STEP 5: T035D EBS ---
    print("\n--- STEP 5: Electronic Bank Statement (T035D) ---")
    for sid, data in [("D01", d01), ("P01", p01)]:
        entries = data.get("T035D", [])
        print(f"  {sid}: {entries if entries else 'MISSING'}")

    # --- STEP 6: T018V Clearing ---
    print("\n--- STEP 6: Receiving Bank Clearing (T018V) ---")
    for sid, data in [("D01", d01), ("P01", p01)]:
        entries = data.get("T018V", [])
        print(f"  {sid}: {entries if entries else 'MISSING'}")

    # --- STEP 7: T042I Payment ---
    print("\n--- STEP 7: Payment Bank Determination (T042I) ---")
    for sid, data in [("D01", d01), ("P01", p01)]:
        entries = data.get("T042I", [])
        print(f"  {sid}: {entries if entries else 'MISSING'}")

    # --- STEP 8: TIBAN ---
    print("\n--- STEP 8: IBAN (TIBAN) ---")
    for sid, data in [("D01", d01), ("P01", p01)]:
        entries = data.get("TIBAN", [])
        print(f"  {sid}: {entries if entries else 'MISSING'}")

    # --- STEP 9: SETLEAF ---
    print("\n--- STEP 9: Account Sets YBANK (GS02) ---")
    for acct in ACCTS:
        short = acct.lstrip("0")
        if short.startswith("11"):
            continue
        d_val = d01.get(f"SETLEAF_{acct}", [])
        p_val = p01.get(f"SETLEAF_{acct}", [])
        print(f"  {short}: D01={d_val if d_val else 'MISSING'}, P01={p_val if p_val else 'MISSING'}")
        if not d_val:
            CRIT.append(f"Account {short}: NOT in any YBANK set in D01")

    # --- CRITICAL FINDINGS ---
    print()
    print("=" * 80)
    print(f"  CRITICAL FINDINGS: {len(CRIT)} issues")
    print("=" * 80)
    for i, c in enumerate(CRIT, 1):
        print(f"  {i}. {c}")

    if not CRIT:
        print("  No critical issues found.")

    print()
    print("=" * 80)
    print("  END OF REPORT")
    print("=" * 80)


if __name__ == "__main__":
    main()
