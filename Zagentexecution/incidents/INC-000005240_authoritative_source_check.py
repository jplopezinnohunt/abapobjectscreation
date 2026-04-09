"""
INC-000005240 — authoritative source check
=============================================
Asks the question: "Where, besides USR05.Y_USERFO, is the user's office stored
in SAP?" and tests the two strongest candidates for AL_JONATHAN:

  1. ADRP (Personal Address Master) via USR21 bridge
       → USR21 WHERE BNAME='AL_JONATHAN' → PERSNUMBER / ADDRNUMBER
       → ADRP WHERE PERSNUMBER+ADDRNUMBER match → DEPARTMENT / FUNCTION

  2. PA0001 (HR Org Assignment) via PA0105 bridge
       → PA0105 WHERE SUBTY='0001' AND USRID='AL_JONATHAN' → PERNR
       → PA0001 WHERE PERNR matches AND ENDDA='99991231' → PERSA, ORGEH, BTRTL, BUKRS

Also pulls the same info for the 3 "known field" users (JJ_YAKI-PAHI, O_RASHIDI,
DA_ENGONGA) as controls, and for I_WETTIE (the ambiguous one from the XBLNR scan).
"""
import sys
import os
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "Zagentexecution" / "mcp-backend-server-python"))
from rfc_helpers import get_connection, rfc_read_paginated  # noqa: E402

OUT = Path(__file__).with_suffix(".json")

USERS = [
    "AL_JONATHAN",     # subject — claims Jakarta
    "I_WETTIE",        # ambiguous — FX postings for Central Asia / East Africa
    "JJ_YAKI-PAHI",    # control — Y_USERFO='YAO'
    "O_RASHIDI",       # control — Y_USERFO='KAB'
    "DA_ENGONGA",      # control — Y_USERFO='DAK'
    "T_ENG",           # control — Y_USERFO='HQ' with HQ-looking XBLNRs
    "L_HANGI",         # control — Y_USERFO='HQ' central processor
]


def rfc(guard, table, fields, where):
    try:
        return rfc_read_paginated(
            guard, table=table, fields=fields, where=where, batch_size=500
        )
    except Exception as e:
        print(f"    {table} read failed ({where[:60]}): {e}")
        return []


def resolve_user(guard, bname):
    """For a given SAP BNAME, pull every authoritative source we can reach."""
    print(f"\n[{bname}]")
    out = {"BNAME": bname}

    # --- 1. USR21 → PERSNUMBER + ADDRNUMBER --------------------------------
    usr21 = rfc(guard, "USR21", ["BNAME", "PERSNUMBER", "ADDRNUMBER"], f"BNAME = '{bname}'")
    print(f"  USR21 rows: {len(usr21)}")
    for r in usr21:
        print(f"    PERSNUMBER={r['PERSNUMBER']} ADDRNUMBER={r['ADDRNUMBER']}")
    out["usr21"] = usr21

    # --- 2. ADRP via PERSNUMBER --------------------------------------------
    adrp = []
    for r in usr21:
        pn = r["PERSNUMBER"]
        if pn and pn != "0000000000":
            rows = rfc(
                guard, "ADRP",
                ["PERSNUMBER", "NAME_FIRST", "NAME_LAST", "DEPARTMENT", "FUNCTION", "TITLE"],
                f"PERSNUMBER = '{pn}'",
            )
            adrp.extend(rows)
    print(f"  ADRP rows: {len(adrp)}")
    for r in adrp:
        print(
            f"    {r['NAME_FIRST']} {r['NAME_LAST']}"
            f"  DEPARTMENT={r['DEPARTMENT']!r}  FUNCTION={r['FUNCTION']!r}"
        )
    out["adrp"] = adrp

    # --- 3. PA0105 subtype 0001 → PERNR ------------------------------------
    pa0105 = rfc(
        guard, "PA0105",
        ["PERNR", "SUBTY", "USRID"],
        f"USRID = '{bname}' AND SUBTY = '0001'",
    )
    print(f"  PA0105 rows: {len(pa0105)}")
    for r in pa0105:
        print(f"    PERNR={r['PERNR']} SUBTY={r['SUBTY']} USRID={r['USRID']}")
    out["pa0105"] = pa0105

    # --- 4. PA0001 current record via PERNR --------------------------------
    pa0001 = []
    for r in pa0105:
        pernr = r["PERNR"]
        rows = rfc(
            guard, "PA0001",
            ["PERNR", "BUKRS", "WERKS", "BTRTL", "PERSG", "PERSK", "ORGEH", "PLANS", "ENDDA", "BEGDA"],
            f"PERNR = '{pernr}' AND ENDDA = '99991231'",
        )
        pa0001.extend(rows)
    print(f"  PA0001 rows: {len(pa0001)}")
    for r in pa0001:
        print(
            f"    PERNR={r['PERNR']} BUKRS={r['BUKRS']} WERKS={r['WERKS']}"
            f" BTRTL={r['BTRTL']} ORGEH={r['ORGEH']} PLANS={r['PLANS']}"
            f" PERSG={r['PERSG']} PERSK={r['PERSK']}"
        )
    out["pa0001"] = pa0001

    return out


def main():
    print("Connecting to P01...")
    guard = get_connection("P01")
    print("Connected.")

    results = []
    for u in USERS:
        try:
            results.append(resolve_user(guard, u))
        except Exception as e:
            print(f"  FAILED: {e}")

    OUT.write_text(json.dumps(results, indent=2, default=str, ensure_ascii=False), encoding="utf-8")

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY — authoritative office per user")
    print("=" * 100)
    for r in results:
        bname = r["BNAME"]
        dept = r["adrp"][0].get("DEPARTMENT", "") if r["adrp"] else ""
        funct = r["adrp"][0].get("FUNCTION", "") if r["adrp"] else ""
        werks = r["pa0001"][0].get("WERKS", "") if r["pa0001"] else ""
        btrtl = r["pa0001"][0].get("BTRTL", "") if r["pa0001"] else ""
        bukrs = r["pa0001"][0].get("BUKRS", "") if r["pa0001"] else ""
        orgeh = r["pa0001"][0].get("ORGEH", "") if r["pa0001"] else ""
        print(
            f"  {bname:14s}  ADRP.DEPARTMENT={dept!r:20s} "
            f"WERKS={werks:5s} BTRTL={btrtl:5s} BUKRS={bukrs:5s} ORGEH={orgeh}"
        )
    print(f"\nOutput: {OUT}")


if __name__ == "__main__":
    main()
