"""Find all D01 DFPAYG entries for /SEPA_CT_UNES (recent), enrich with REGUH vendor + LFA1.
Filter by KTOKK so we can identify staff vs non-staff in D01's existing test universe.
Also check whether TISSIER + AGU LIFNRs exist in D01 LFA1 at all.
"""
import os
import sys
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

# Step 1: all DFPAYG rows for /SEPA_CT_UNES recently
print("\n=== D01 DFPAYG /SEPA_CT_UNES (since 2024) ===")
gpg = rd("DFPAYG",
         ["FORMI = '/SEPA_CT_UNES'", " AND LAUFD >= '20240101'"],
         ["LAUFD","LAUFI","ZBUKR","HBKID","HKTID","GRPNO","CRDEB","RZAWE","ANZ_ERZ","ANZ_ERL"], n=500)
print(f"{len(gpg)} DFPAYG rows")
for g in gpg[:20]:
    print(" ", "|".join(x.strip() for x in g))

# Step 2: for each (LAUFD,LAUFI,ZBUKR), pull REGUH vendor list
print("\n=== LIFNR universe per run ===")
seen_lifnrs = set()
run_to_lifnrs = {}
for g in gpg:
    laufd, laufi, zb = g[0].strip(), g[1].strip(), g[2].strip()
    rows = rd("REGUH",
              [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'", " AND XVORL = ' '"],
              ["LIFNR","VBLNR","HBKID","HKTID"], n=200)
    lifnrs = sorted(set(r[0].strip() for r in rows))
    run_to_lifnrs[(laufd, laufi, zb)] = lifnrs
    seen_lifnrs.update(lifnrs)
    print(f"  {laufd}/{laufi}/{zb}: {len(lifnrs)} LIFNRs")

# Step 3: LFA1 lookup for those LIFNRs
print(f"\n=== LFA1 lookup for {len(seen_lifnrs)} distinct LIFNRs ===")
lifnr_info = {}
for lifnr in sorted(seen_lifnrs):
    rows = rd("LFA1",
              [f"LIFNR = '{lifnr}'"],
              ["LIFNR","NAME1","KTOKK","STRAS","ORT01","LAND1","LNRZA","LOEVM"], n=2)
    if rows:
        lifnr_info[lifnr] = rows[0]
        r = rows[0]
        print(f"  {r[0].strip():12s} {r[2].strip():5s} {r[1].strip()[:30]:30s} STRAS={r[3].strip()[:25]} CITY={r[4].strip()[:18]} LAND={r[5].strip()} LNRZA={r[6].strip()}")

# Step 4: identify non-staff candidates already in D01 test data
print("\n=== Non-staff candidates already replay-ready in D01 ===")
for lifnr, r in lifnr_info.items():
    ktokk = r[2].strip()
    if ktokk not in ("UNES","SCSA","HQSU","ICTP"):
        for (laufd, laufi, zb), lifnrs in run_to_lifnrs.items():
            if lifnr in lifnrs:
                print(f"  {lifnr} {ktokk} {r[1].strip()[:30]:30s} → run {laufd}/{laufi}/{zb}  LNRZA={r[6].strip() or '(none)'}")

# Step 5: also check whether TISSIER + AGU exist at all in D01 LFA1
print("\n=== Existence check in D01 LFA1 ===")
for lifnr in ("0000412217","0004014974","0000800131","0000301769","0000306841"):
    rows = rd("LFA1", [f"LIFNR = '{lifnr}'"], ["LIFNR","NAME1","KTOKK","LAND1"], n=1)
    if rows:
        print(f"  {lifnr}: EXISTS — {rows[0]}")
    else:
        print(f"  {lifnr}: NOT in D01 LFA1")
