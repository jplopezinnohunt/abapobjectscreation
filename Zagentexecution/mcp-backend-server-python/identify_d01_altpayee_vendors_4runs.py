"""Identify source vendors + alt-payee targets for the 4 D01 test runs.

Per format:
  /CGI_XML_CT_UNESCO     — 20230623/00001R/UNES
  /CGI_XML_CT_UNESCO_1   — 20250307/00001R/UNES  (CGI_1)
  /CITI/XML/UNESCO/DC_V3_01 — 20220613/00001R/UNES
  /SEPA_CT_UNES          — 20210316/TST/UNES     (already documented but re-confirmed)

For each run:
  - List ALL REGUH.LIFNR with EMPFG populated
  - Parse EMPFG → resolved alt-payee LIFNR (>NNNNNNNNNN>Z format)
  - Pull LFA1 + ADRC for both source and alt-payee
  - Also pull IBAN from TIBAN for the alt-payee (the bank that actually receives)
"""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_ASHOST'), sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'), user=os.getenv('SAP_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected D01")

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

RUNS = [
    ("20210316", "TST",     "UNES", "/SEPA_CT_UNES"),
    ("20230623", "00001R",  "UNES", "/CGI_XML_CT_UNESCO"),
    ("20250307", "00001R",  "UNES", "/CGI_XML_CT_UNESCO_1"),
    ("20220613", "00001R",  "UNES", "/CITI/XML/UNESCO/DC_V3_01"),
]

def parse_alt(empfg):
    s = empfg.strip()
    if s.startswith('>') and '>Z' in s:
        return s[1:].split('>')[0]
    return s

def lookup_vendor(lifnr):
    info = {"lifnr": lifnr, "name": None, "ktokk": None, "land": None,
            "street": None, "house": None, "post": None, "city": None,
            "country": None, "iban": None}
    if not lifnr:
        return info
    l = rd("LFA1", [f"LIFNR = '{lifnr}'"],
           ["LIFNR","NAME1","KTOKK","LAND1","ADRNR"], n=1)
    if not l:
        info["name"] = "NOT IN D01 LFA1"
        return info
    d = l[0]
    info["name"] = d["NAME1"].strip()
    info["ktokk"] = d["KTOKK"].strip()
    info["land"] = d["LAND1"].strip()
    adrnr = d["ADRNR"].strip()
    if adrnr:
        try:
            a = rd("ADRC", [f"ADDRNUMBER = '{adrnr}'"],
                   ["STREET","HOUSE_NUM1","POST_CODE1","CITY1","COUNTRY"], n=1)
            if a:
                ar = a[0]
                info["street"] = ar["STREET"].strip()
                info["house"] = ar["HOUSE_NUM1"].strip()
                info["post"] = ar["POST_CODE1"].strip()
                info["city"] = ar["CITY1"].strip()
                info["country"] = ar["COUNTRY"].strip()
        except Exception:
            pass
    # IBAN
    try:
        t = rd("TIBAN", [f"TABKEY LIKE '%{lifnr}%'"],
               ["IBAN"], n=1)
        if t:
            info["iban"] = t[0]["IBAN"].strip()
    except Exception:
        pass
    return info

for laufd, laufi, zb, formi in RUNS:
    print(f"\n{'='*82}")
    print(f"  {formi}  |  run {laufd}/{laufi}/{zb}")
    print('='*82)
    try:
        reguh = rd("REGUH",
                   [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                   ["LIFNR","EMPFG","XVORL"], n=200)
        hits = [r for r in reguh if r['EMPFG'].strip()]
        print(f"  Total REGUH={len(reguh)}, with EMPFG={len(hits)}")
        # Deduplicate by (source, alt) pair
        seen = set()
        for h in hits:
            src = h['LIFNR'].strip()
            alt = parse_alt(h['EMPFG'])
            key = (src, alt)
            if key in seen:
                continue
            seen.add(key)
            xv = h['XVORL']
            print(f"\n  Pair (XVORL='{xv}'): SOURCE={src}  →  ALT-PAYEE={alt}  (raw EMPFG={h['EMPFG'].strip()})")
            for role, lifnr in (("SOURCE", src), ("ALT-PAYEE", alt)):
                info = lookup_vendor(lifnr)
                addr = ""
                if info["street"]:
                    addr = f"{info['street']}"
                    if info["house"]:
                        addr += f" {info['house']}"
                    addr += f", {info['post']} {info['city']}, {info['country']}"
                print(f"    [{role}] {info['lifnr']} {(info['name'] or '')[:32]:32s} KTOKK={info['ktokk']} LAND={info['land']}")
                if addr:
                    print(f"        addr: {addr}")
                if info["iban"]:
                    print(f"        IBAN: {info['iban']}")
    except Exception as e:
        print(f"  ERR: {e}")
