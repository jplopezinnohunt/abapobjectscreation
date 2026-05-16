"""Scan ALL D01 DFPAYG (not just /SEPA_CT_UNES) and find which runs contain non-staff vendors.
Goal: identify any vendor in D01 that we can replay TODAY without creating new test data.
"""
import os, sys
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
print("Connected D01", file=sys.stderr)

def rd(table, options, fields, n=1000):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=table,
                  OPTIONS=[{"TEXT": t} for t in options],
                  FIELDS=[{"FIELDNAME": f} for f in fields],
                  DELIMITER="|", ROWCOUNT=n)
    return [d["WA"].split("|") for d in r.get("DATA", [])]

# All DFPAYG rows in D01 since 2024
print("\n=== ALL D01 DFPAYG since 2024-01-01 ===")
gpg = rd("DFPAYG", ["LAUFD >= '20240101'"],
         ["LAUFD","LAUFI","ZBUKR","HBKID","HKTID","GRPNO","FORMI","CRDEB","RZAWE","ANZ_ERZ","ANZ_ERL"], n=2000)
print(f"{len(gpg)} DFPAYG rows total in D01")

# Group by FORMI to see what's there
formats = {}
for g in gpg:
    f = g[6].strip()
    formats[f] = formats.get(f, 0) + 1
print(f"\nFORMI distribution:")
for f, n in sorted(formats.items(), key=lambda x: -x[1]):
    print(f"  {f:40s} {n}")

# For each run, get the vendor list
print(f"\n=== Vendor scan across all DFPAYG runs ===")
all_lifnrs = {}  # lifnr -> list of (laufd, laufi, zbukr, formi)
for g in gpg:
    laufd, laufi, zb, formi = g[0].strip(), g[1].strip(), g[2].strip(), g[6].strip()
    rows = rd("REGUH",
              [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'", " AND XVORL = ' '"],
              ["LIFNR"], n=500)
    for r in rows:
        lifnr = r[0].strip()
        all_lifnrs.setdefault(lifnr, []).append((laufd, laufi, zb, formi))

print(f"  {len(all_lifnrs)} distinct LIFNRs across all D01 runs")

# Classify staff vs non-staff via LFA1
print(f"\n=== LFA1 classification + non-staff candidates ===")
candidates = []
for lifnr in sorted(all_lifnrs.keys()):
    rows = rd("LFA1", [f"LIFNR = '{lifnr}'"],
              ["LIFNR","NAME1","KTOKK","STRAS","ORT01","LAND1","LNRZA","LOEVM"], n=1)
    if not rows:
        continue
    r = rows[0]
    ktokk = r[2].strip()
    name = r[1].strip()
    flag = "STAFF" if ktokk in ("UNES","SCSA","HQSU","ICTP") else "NON-STAFF"
    print(f"  {lifnr} {ktokk:5s} {flag:9s} {name[:30]:30s} LAND={r[5].strip()} LNRZA={r[6].strip() or '(none)'}")
    if flag == "NON-STAFF":
        candidates.append((lifnr, ktokk, name, r[5].strip(), r[6].strip(), all_lifnrs[lifnr]))

print(f"\n=== NON-STAFF candidates already in D01 DFPAYG ===")
if not candidates:
    print("  None — no non-staff vendor has a DFPAYG run in D01.")
else:
    for lifnr, ktokk, name, land, lnrza, runs in candidates:
        print(f"\n  {lifnr} {ktokk} {name} (LAND={land}, LNRZA={lnrza or '(none)'})")
        for laufd, laufi, zb, formi in runs:
            print(f"    run {laufd}/{laufi}/{zb}  FORMI={formi}")
