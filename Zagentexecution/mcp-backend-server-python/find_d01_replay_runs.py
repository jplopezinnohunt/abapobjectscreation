"""Find D01 DFPAYG runs we can re-run via ZSAPFPAYM_REPLAY for:
  - TISSIER Alexandre (0000412217) — non-staff INDV test
  - AGU (0000800131)              — alt-payee ICTP test (LNRZA = 0000800157 Wiley)
  - BERTOLDINI Simona (0010008305) — staff baseline (for reference)

Use D01 SNC connection (password is locked).
Output: for each LIFNR, the available D01 DFPAYG runs with FORMI matching the test format,
plus the run header (LAUFD/LAUFI/XVORL/GRPNO/FORMI/ZBUKR/HBKID/HKTID).
"""
import os
import sys
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# D01 uses the unprefixed SAP_* vars in the .env. Force SNC-only (no password).
params = dict(
    ashost=os.getenv("SAP_ASHOST"),
    sysnr=os.getenv("SAP_SYSNR"),
    client=os.getenv("SAP_CLIENT"),
    user=os.getenv("SAP_USER"),
    lang=os.getenv("SAP_LANG", "EN"),
    snc_mode="1",
    snc_partnername=os.getenv("SAP_SNC_PARTNERNAME"),
    snc_qop=os.getenv("SAP_SNC_QOP", "9"),
)
print("Connecting D01 via SNC (no password)…", file=sys.stderr)
conn = Connection(**params)
print("Connected D01", file=sys.stderr)

VENDORS = [
    ("0000412217", "TISSIER Alexandre",  "/SEPA_CT_UNES",       "UNES"),
    ("0000800131", "AGU (alt-payee)",    "/SEPA_CT_ICTP_ISO",   "ICTP"),
    ("0010008305", "BERTOLDINI Simona",  "/SEPA_CT_UNES",       "UNES"),
]

def read_table(table, options, fields, rowcount=200):
    r = conn.call("RFC_READ_TABLE",
        QUERY_TABLE=table,
        OPTIONS=[{"TEXT": t} for t in options],
        FIELDS=[{"FIELDNAME": f} for f in fields],
        DELIMITER="|", ROWCOUNT=rowcount)
    return [d["WA"].split("|") for d in r.get("DATA", [])]

for lifnr, name, formi, zbukr in VENDORS:
    print()
    print(f"=== {lifnr}  {name}  expected FORMI={formi} ZBUKR={zbukr} ===")

    # Step 1: REGUH for that vendor in D01 (last 2y), grouped by run
    rows = read_table(
        "REGUH",
        [f"LIFNR = '{lifnr}'", " AND LAUFD >= '20240101'", " AND XVORL = ' '"],
        ["LAUFD", "LAUFI", "ZBUKR", "HBKID", "HKTID", "VBLNR", "XVORL"],
        rowcount=50
    )
    if not rows:
        print("  no REGUH rows for this vendor in D01 since 2024.")
        continue

    # Build distinct runs
    runs = {}
    for r in rows:
        key = (r[0].strip(), r[1].strip(), r[2].strip())
        runs.setdefault(key, {"hbkid": r[3].strip(), "hktid": r[4].strip(), "n_lines": 0, "sample_vblnr": r[5].strip()})
        runs[key]["n_lines"] += 1

    print(f"  {len(runs)} distinct REGUH runs found")
    for (laufd, laufi, zb), info in sorted(runs.items()):
        print(f"  REGUH: LAUFD={laufd} LAUFI={laufi} ZBUKR={zb} HBKID={info['hbkid']} HKTID={info['hktid']} lines={info['n_lines']} VBLNR={info['sample_vblnr']}")

    # Step 2: cross-check DFPAYG for those runs with the expected FORMI
    print(f"  Checking DFPAYG for FORMI={formi}…")
    formi_clean = formi.replace("'", "''")
    for (laufd, laufi, zb), info in sorted(runs.items()):
        try:
            gpg = read_table(
                "DFPAYG",
                [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'", f" AND FORMI = '{formi_clean}'"],
                ["LAUFD", "LAUFI", "GRPNO", "FORMI", "ZBUKR", "HBKID", "HKTID", "BANKS", "BANKL", "CRDEB", "RZAWE", "ANZ_ERZ", "ANZ_ERL"],
                rowcount=10
            )
            for g in gpg:
                print(f"    DFPAYG ★ LAUFD={g[0]} LAUFI={g[1]} GRPNO={g[2]} FORMI={g[3]} ZBUKR={g[4]} HBKID={g[5]} HKTID={g[6]} BANKS={g[7]} CRDEB={g[9]} RZAWE={g[10]} ANZ_ERZ={g[11]} ANZ_ERL={g[12]}")
        except Exception as e:
            print(f"    DFPAYG read failed for {laufd}/{laufi}: {e}")

print()
print("Done.")
