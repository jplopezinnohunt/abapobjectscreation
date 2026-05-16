"""Extract full ZSAPFPAYM_REPLAY input data for D01 non-staff CGI runs.

Known runs from the broader scan:
  0000300149 MIL.EDU.AND INFOR.SUPPLIES  → 20250325/T0001/UNES, 20250326/T0001/UNES
  0000307133 Ai Te Bo Travel Service     → 20240115/CN/UNES
Both formats: /CGI_XML_CT_UNESCO.
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

RUNS = [
    ("20250325","T0001","UNES","0000300149","MIL.EDU.AND INFOR.SUPPLIES","/CGI_XML_CT_UNESCO"),
    ("20250326","T0001","UNES","0000300149","MIL.EDU.AND INFOR.SUPPLIES","/CGI_XML_CT_UNESCO"),
    ("20240115","CN   ","UNES","0000307133","Ai Te Bo Travel Service",   "/CGI_XML_CT_UNESCO"),
]

for laufd, laufi, zbukr, lifnr, name, formi in RUNS:
    print(f"\n{'='*82}")
    print(f"  Run: {laufd}/{laufi.strip()}/{zbukr}    Vendor: {lifnr}  {name}")
    print(f"  Format: {formi}")
    print('='*82)

    # DFPAYG for this exact run
    g = rd("DFPAYG",
           [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi.strip()}'", f" AND ZBUKR = '{zbukr}'"],
           ["LAUFD","LAUFI","GRPNO","FORMI","ZBUKR","BANKS","BANKL","HBKID","HKTID","CRDEB","RZAWE","ANZ_ERZ","ANZ_ERL"],
           n=20)
    print(f"  DFPAYG rows for run: {len(g)}")
    for row in g:
        print(f"    GRPNO={row['GRPNO'].strip()} FORMI={row['FORMI'].strip()} HBKID={row['HBKID']} HKTID={row['HKTID']} BANKS={row['BANKS']} CRDEB={row['CRDEB']} RZAWE={row['RZAWE']} ANZ_ERZ={row['ANZ_ERZ']} ANZ_ERL={row['ANZ_ERL']}")

    # REGUH narrow
    # REGUH read — drop LIFNR filter (was breaking the query), filter in Python
    try:
        h = rd("REGUH",
               [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi.strip()}'", f" AND ZBUKR = '{zbukr}'"],
               ["LIFNR","VBLNR","HBKID","HKTID","XVORL","XEB1"],
               n=50)
        h_vendor = [r for r in h if r["LIFNR"].strip() == lifnr]
        print(f"  REGUH rows: {len(h)} total, {len(h_vendor)} for vendor {lifnr}")
        for row in h_vendor:
            print(f"    LIFNR={row['LIFNR']} VBLNR={row['VBLNR']} HBKID={row['HBKID']} HKTID={row['HKTID']} XVORL='{row['XVORL']}' XEB1='{row['XEB1']}'")
    except Exception as e:
        print(f"  REGUH read err: {e}")

    # Bank fields in a second pass
    try:
        h2 = rd("REGUH",
                [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi.strip()}'", f" AND ZBUKR = '{zbukr}'"],
                ["LIFNR","ZBNKS","ZBNKL","ZIBAN"],
                n=50)
        for row in [r for r in h2 if r["LIFNR"].strip() == lifnr]:
            print(f"    LIFNR={row['LIFNR']} ZBNKS={row['ZBNKS']} ZBNKL={row['ZBNKL']} ZIBAN={row['ZIBAN'].strip()}")
    except Exception as e:
        print(f"  REGUH bank-fields err: {e}")

# Vendor master + ADRC for the candidates
print(f"\n{'='*82}\n  D01 vendor master + ADRC\n{'='*82}")
for lifnr in ("0000300149","0000307133"):
    l = rd("LFA1", [f"LIFNR = '{lifnr}'"],
           ["LIFNR","NAME1","KTOKK","STRAS","ORT01","PSTLZ","LAND1","ADRNR","LNRZA"], n=1)
    if l:
        d = l[0]
        print(f"\n  {d['LIFNR']} {d['NAME1'].strip()}  KTOKK={d['KTOKK']} LAND={d['LAND1']}")
        print(f"    LFA1 STRAS='{d['STRAS'].strip()}' ORT01='{d['ORT01'].strip()}' PSTLZ={d['PSTLZ']}")
        print(f"    ADRNR={d['ADRNR']}  LNRZA='{d['LNRZA'].strip()}' (alt-payee)")
        adrnr = d['ADRNR'].strip()
        if adrnr:
            a = rd("ADRC", [f"ADDRNUMBER = '{adrnr}'"],
                   ["ADDRNUMBER","STREET","HOUSE_NUM1","POST_CODE1","CITY1","COUNTRY","REGION"], n=1)
            if a:
                ar = a[0]
                print(f"    ADRC STREET='{ar['STREET'].strip()}' HOUSE='{ar['HOUSE_NUM1'].strip()}' POST={ar['POST_CODE1'].strip()} CITY1='{ar['CITY1'].strip()}' COUNTRY={ar['COUNTRY']} REGION={ar['REGION']}")
