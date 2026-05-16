"""Profile the 3 UNES-staff alt-payee candidates in D01.

Source/target master data + bank + recent REGUH for each pair.
The winner is the one whose alt-payee target has a complete FR/EU IBAN
and a clean address (so we can validate the resolved-payee XML output).
"""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
params = dict(
    ashost=os.getenv("SAP_ASHOST"), sysnr=os.getenv("SAP_SYSNR"),
    client=os.getenv("SAP_CLIENT"), user=os.getenv("SAP_USER"),
    lang="EN", snc_mode="1",
    snc_partnername=os.getenv("SAP_SNC_PARTNERNAME"), snc_qop="9",
)
conn = Connection(**params)

def rd(t, opts, fields, n=200):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=t,
                  OPTIONS=[{"TEXT": x} for x in opts],
                  FIELDS=[{"FIELDNAME": x} for x in fields],
                  DELIMITER="|", ROWCOUNT=n)
    cols = [f["FIELDNAME"] for f in r.get("FIELDS",[])] or fields
    return [dict(zip(cols, d["WA"].split("|"))) for d in r.get("DATA", [])]

PAIRS = [
    ("0010006352", "0000405183", "BARTON Michel → Béatrice"),
    ("0010049266", "0010049267", "KOUROUMA Madigbe → Keita"),
    ("0010055981", "0010055984", "MBAMBA Alpo Maun → Sarah"),
]

for src, tgt, descr in PAIRS:
    print(f"\n{'='*80}")
    print(f"  {descr}")
    print(f"  Source LIFNR: {src}  →  Alt-payee LIFNR: {tgt}")
    print('='*80)

    for role, lifnr in (("SOURCE", src), ("ALT-PAYEE", tgt)):
        print(f"\n  [{role}] {lifnr}")

        # LFA1
        l = rd("LFA1", [f"LIFNR = '{lifnr}'"],
               ["LIFNR","NAME1","KTOKK","STRAS","ORT01","PSTLZ","LAND1","ADRNR","LNRZA","LOEVM"], n=1)
        if not l:
            print("    NOT in D01 LFA1")
            continue
        d = l[0]
        print(f"    NAME={d['NAME1'].strip()}  KTOKK={d['KTOKK']}  LAND={d['LAND1']}  LOEVM='{d['LOEVM']}'")
        print(f"    LFA1 STRAS='{d['STRAS'].strip()}'  ORT01='{d['ORT01'].strip()}'  PSTLZ={d['PSTLZ']}")
        print(f"    ADRNR={d['ADRNR']}  LNRZA='{d['LNRZA'].strip()}'")

        # ADRC
        adrnr = d['ADRNR'].strip()
        if adrnr:
            a = rd("ADRC", [f"ADDRNUMBER = '{adrnr}'"],
                   ["ADDRNUMBER","STREET","HOUSE_NUM1","POST_CODE1","CITY1","COUNTRY","REGION"], n=1)
            if a:
                ar = a[0]
                print(f"    ADRC STREET='{ar['STREET'].strip()}' HOUSE='{ar['HOUSE_NUM1'].strip()}' POST={ar['POST_CODE1'].strip()} CITY='{ar['CITY1'].strip()}' COUNTRY={ar['COUNTRY']}")

        # LFBK (vendor bank account)
        try:
            b = rd("LFBK", [f"LIFNR = '{lifnr}'"],
                   ["LIFNR","BANKS","BANKL","BANKN","BKONT","KOINH"], n=10)
            for br in b:
                print(f"    LFBK BANKS={br['BANKS']} BANKL={br['BANKL'].strip()} BANKN={br['BANKN'].strip()} BKONT={br['BKONT']} KOINH={br['KOINH'].strip()[:30]}")
        except Exception as e:
            print(f"    LFBK err: {e}")

        # TIBAN
        try:
            t = rd("TIBAN", [f"TABKEY LIKE '%{lifnr}%'"],
                   ["TABKEY","IBAN","VALID_FROM"], n=5)
            for tr in t:
                print(f"    TIBAN IBAN={tr['IBAN'].strip()}  VALID_FROM={tr['VALID_FROM']}")
        except Exception as e:
            print(f"    TIBAN err: {e}")

    # Check whether source has ANY recent REGUH at cocode UNES (so we know F110 has selected it before)
    print(f"\n  REGUH for source LIFNR {src} at UNES (any LAUFD, narrow fields):")
    try:
        h = rd("REGUH",
               [f"LIFNR = '{src}'", " AND ZBUKR = 'UNES'"],
               ["LAUFD","LAUFI","ZBUKR","VBLNR"], n=10)
        for row in h:
            print(f"    {row['LAUFD']}/{row['LAUFI']}/{row['ZBUKR']} VBLNR={row['VBLNR']}")
    except Exception as e:
        print(f"    REGUH err: {e}")
