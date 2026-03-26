"""
decode_numeric_bdc.py — Decode the mystery numeric BDC sessions by GAMA-BERNA
==============================================================================

Target sessions: 63178940U101, 91136176U701, 10155259V901, 63177865U101

Hypothesis: The numeric part is a PERSONNEL NUMBER.
  63178940 → UNESCO employee personnel number
  U/V      → variant code (payroll result, infotype type)
  101/701  → client + processing run counter

Strategy:
  1. Check if 63178940 is a real PA number in PA0001 (org assignment)
  2. Read program from TADIR for full PROGID 'Y1' → source → TCODE
  3. Read APQI FORMID field → often contains the program that created session
  4. Check BTCH5000/TBTCS for background job steps (links job to BDC name)
  5. Check table PRCA_RUN or payroll result tables (RGDIR, PC26x) for these numbers
"""
import os, sys
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def env(*keys, default=""):
    for k in keys:
        v = os.getenv(k)
        if v: return v
    return default

import pyrfc

params = {
    "ashost": env("SAP_P01_ASHOST", default="172.16.4.100"),
    "sysnr":  env("SAP_P01_SYSNR",  default="00"),
    "client": env("SAP_P01_CLIENT", default="350"),
}
snc_mode = env("SAP_P01_SNC_MODE")
snc_pn   = env("SAP_P01_SNC_PARTNERNAME")
if snc_mode and snc_pn:
    params["snc_mode"]        = snc_mode
    params["snc_partnername"] = snc_pn
    params["snc_qop"]         = env("SAP_P01_SNC_QOP", default="9")
else:
    params["user"]   = env("SAP_P01_USER", "SAP_USER")
    params["passwd"] = env("SAP_P01_PASSWORD", "SAP_P01_PASSWD")

print("Connecting to P01...")
conn = pyrfc.Connection(**params)
print("Connected OK\n")

def parse_fixed(wa, fields):
    result = {}; p = 0
    for f in fields:
        w = int(f.get("LENGTH", 10))
        result[f["FIELDNAME"]] = wa[p:p+w].strip()
        p += w + 1
    return result

cutoff = (datetime.now() - timedelta(days=90)).strftime("%Y%m%d")

# ─────────────────────────────────────────────────────────────────────────────
# 1. Get ALL numeric sessions from APQI with their full FORMID and PROGID
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 65)
print("[1] ALL NUMERIC BDC SESSIONS — Full APQI Data (last 90d)")
print("=" * 65)

r = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="APQI",
    FIELDS=[
        {"FIELDNAME": "GROUPID"},
        {"FIELDNAME": "QID"},
        {"FIELDNAME": "CREATOR"},
        {"FIELDNAME": "QSTATE"},
        {"FIELDNAME": "PROGID"},
        {"FIELDNAME": "FORMID"},
        {"FIELDNAME": "CREDATE"},
        {"FIELDNAME": "CRETIME"},
        {"FIELDNAME": "TRANSCNT"},  # transaction count
    ],
    OPTIONS=[
        {"TEXT": f"CREDATE >= '{cutoff}'"},
        {"TEXT": " AND CREATOR LIKE 'GAMA-BERNA%'"},
    ],
    ROWCOUNT=200,
)
fields = r.get("FIELDS", [])
rows_gama = []
for row in r.get("DATA", []):
    d = parse_fixed(row["WA"], fields)
    rows_gama.append(d)

print(f"Found {len(rows_gama)} sessions by GAMA-BERNA users\n")
# Group by GROUPID
by_group = defaultdict(list)
for d in rows_gama:
    by_group[d.get("GROUPID", "?")].append(d)

for gid, members in sorted(by_group.items(), key=lambda x: -len(x[1])):
    sample = members[0]
    print(f"  {gid:<30}  ×{len(members):>3}  "
          f"PROGID={sample.get('PROGID','?'):6}  "
          f"FORMID={sample.get('FORMID','?'):8}  "
          f"QSTATE={sample.get('QSTATE','?')}  "
          f"CREATOR={sample.get('CREATOR','?')}")

# ─────────────────────────────────────────────────────────────────────────────
# 2. Also check COLLOCA numeric sessions
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("[2] COLLOCA Numeric Sessions")
print("=" * 65)

r2 = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="APQI",
    FIELDS=[
        {"FIELDNAME": "GROUPID"},
        {"FIELDNAME": "CREATOR"},
        {"FIELDNAME": "QSTATE"},
        {"FIELDNAME": "PROGID"},
        {"FIELDNAME": "FORMID"},
        {"FIELDNAME": "CREDATE"},
    ],
    OPTIONS=[
        {"TEXT": f"CREDATE >= '{cutoff}'"},
        {"TEXT": " AND CREATOR LIKE '%COLLOCA%'"},
    ],
    ROWCOUNT=200,
)
fields2  = r2.get("FIELDS", [])
by_group2 = defaultdict(list)
for row in r2.get("DATA", []):
    d = parse_fixed(row["WA"], fields2)
    by_group2[d.get("GROUPID", "?")].append(d)

for gid, members in sorted(by_group2.items(), key=lambda x: -len(x[1]))[:15]:
    sample = members[0]
    print(f"  {gid:<30}  ×{len(members):>3}  "
          f"PROGID={sample.get('PROGID','?'):6}  "
          f"FORMID={sample.get('FORMID','?'):8}  "
          f"{sample.get('CREDATE','?')}")

# ─────────────────────────────────────────────────────────────────────────────
# 3. Decode: is 63178940 a personnel number? → Check PA0001
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("[3] DECODE: Is the numeric prefix a Personnel Number in PA0001?")
print("=" * 65)

# Extract first 8 digits from numeric session names found
import re
numeric_pernrs = set()
for gid in by_group.keys():
    m = re.match(r'^(\d{8,10})', gid)
    if m:
        numeric_pernrs.add(m.group(1)[:8])  # PA pernr is 8 digits

print(f"  Potential PERNRs to check: {numeric_pernrs}")

for pernr in list(numeric_pernrs)[:5]:
    try:
        r3 = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="PA0001",
            FIELDS=[
                {"FIELDNAME": "PERNR"},
                {"FIELDNAME": "ENAME"},
                {"FIELDNAME": "PLANS"},
                {"FIELDNAME": "ORGEH"},
                {"FIELDNAME": "BEGDA"},
                {"FIELDNAME": "ENDDA"},
            ],
            OPTIONS=[
                {"TEXT": f"PERNR = '{pernr.zfill(8)}'"},
                {"TEXT": " AND ENDDA >= '20260101'"},
            ],
            ROWCOUNT=3,
        )
        rows3 = r3.get("DATA", [])
        fields3 = r3.get("FIELDS", [])
        if rows3:
            print(f"\n  PERNR {pernr} IS A REAL EMPLOYEE:")
            for row in rows3:
                d = parse_fixed(row["WA"], fields3)
                print(f"    Name: {d.get('ENAME','?'):30}  Position: {d.get('PLANS','?')}  Org: {d.get('ORGEH','?')}")
        else:
            print(f"  PERNR {pernr} → not in PA0001 (or wrong format)")
    except Exception as ex:
        print(f"  PA0001 check for {pernr}: {str(ex)[:80]}")

# ─────────────────────────────────────────────────────────────────────────────
# 4. Resolve PROGID 'Y1' and 'R0' → full program names via TADIR
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("[4] RESOLVE PROGID: 'Y1' and 'R0' → full ABAP program name")
print("=" * 65)

# The PROGID in APQI is not the full name — it's stored shortened
# The FORMID might tell us more. Let's look at what FORMID looks like.
# Also query TADIR for programs starting with Y (UNESCO standard prefix)
print("\n  TADIR: Programs starting with Y* (top 30 by name):")
r4 = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="TADIR",
    FIELDS=[{"FIELDNAME": "OBJ_NAME"}, {"FIELDNAME": "DEVCLASS"}, {"FIELDNAME": "AUTHOR"}],
    OPTIONS=[{"TEXT": "OBJECT = 'PROG' AND OBJ_NAME LIKE 'Y%'"}],
    ROWCOUNT=200,
)
fields4 = r4.get("FIELDS", [])
prog_rows = [parse_fixed(row["WA"], fields4) for row in r4.get("DATA", [])]
for p in sorted(prog_rows, key=lambda x: x.get("OBJ_NAME",""))[:30]:
    print(f"    {p.get('OBJ_NAME','?'):40}  {p.get('DEVCLASS','?'):15}  {p.get('AUTHOR','?')}")

# ─────────────────────────────────────────────────────────────────────────────
# 5. Check TBTCS (background job steps) for GAMA-BERNA related jobs
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("[5] BACKGROUND JOB STEPS (TBTCS) — Find ABAP prog from job")
print("=" * 65)

r5 = conn.call("RFC_READ_TABLE",
    QUERY_TABLE="TBTCS",
    FIELDS=[
        {"FIELDNAME": "JOBNAME"},
        {"FIELDNAME": "JOBCOUNT"},
        {"FIELDNAME": "STEPCOUNT"},
        {"FIELDNAME": "PROGNAME"},
        {"FIELDNAME": "VARIANT"},
        {"FIELDNAME": "AUTHCKNAM"},
    ],
    OPTIONS=[{"TEXT": "AUTHCKNAM LIKE '%GAMA%' OR AUTHCKNAM LIKE '%COLLOCA%'"}],
    ROWCOUNT=50,
)
fields5 = r5.get("FIELDS", [])
job_steps = [parse_fixed(row["WA"], fields5) for row in r5.get("DATA", [])]
if job_steps:
    print(f"  Found {len(job_steps)} job steps:")
    for js in job_steps[:20]:
        print(f"    Job: {js.get('JOBNAME','?'):35}  Prog: {js.get('PROGNAME','?'):30}  User: {js.get('AUTHCKNAM','?')}")
else:
    print("  No job steps found via AUTHCKNAM filter")
    # Try without filter — look for jobs with numeric names matching our sessions
    print("\n  Searching TBTCO for jobs containing numeric patterns...")
    for pattern in ["63178940", "91136176", "10155259"]:
        try:
            r5b = conn.call("RFC_READ_TABLE",
                QUERY_TABLE="TBTCO",
                FIELDS=[{"FIELDNAME": "JOBNAME"}, {"FIELDNAME": "AUTHCKNAM"}, {"FIELDNAME": "STATUS"}],
                OPTIONS=[{"TEXT": f"JOBNAME LIKE '%{pattern}%'"}],
                ROWCOUNT=5,
            )
            rows5b = r5b.get("DATA", [])
            if rows5b:
                f5b = r5b.get("FIELDS", [])
                for row in rows5b:
                    d = parse_fixed(row["WA"], f5b)
                    print(f"    {pattern} → Job: {d}")
            else:
                print(f"    Pattern {pattern}: no TBTCO match")
        except Exception as ex:
            print(f"    TBTCO {pattern}: {str(ex)[:60]}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Read payroll control record + try to link to payroll run type
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("[6] Try to read ABAP program Y1 source directly (RFC_READ_REPORT)")
print("=" * 65)

for prog_attempt in ["Y1", "Y100", "YALLOS", "YRPALLOS", "YHRPALLOS"]:
    try:
        r6 = conn.call("RFC_READ_REPORT", PROGRAM=prog_attempt)
        lines = [l.get("LINE", "") for l in r6.get("QTAB", [])]
        if lines:
            print(f"\n  Program '{prog_attempt}' EXISTS — {len(lines)} lines")
            # Show first 30 + search for CALL TRANSACTION
            for line in lines[:20]:
                print(f"    {line}")
            print(f"  ...")
            tcodes = []
            for line in lines:
                lu = line.upper()
                if "CALL TRANSACTION" in lu or "BDC_OPEN_GROUP" in lu:
                    print(f"  *** KEY LINE: {line.strip()}")
            break
        else:
            print(f"  '{prog_attempt}': empty")
    except Exception as ex:
        print(f"  '{prog_attempt}': {str(ex)[:60]}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Payroll results tables — check if these are payroll batch session names
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("[7] RGDIR — Payroll Result Directory (are these payroll runs?)")
print("=" * 65)

# Sample numeric pernr from our sessions
for pernr in list(numeric_pernrs)[:3]:
    try:
        r7 = conn.call("RFC_READ_TABLE",
            QUERY_TABLE="RGDIR",
            FIELDS=[{"FIELDNAME": "PERNR"}, {"FIELDNAME": "SRTZA"},
                    {"FIELDNAME": "FPPER"}, {"FIELDNAME": "INPER"}],
            OPTIONS=[{"TEXT": f"PERNR = '{pernr.zfill(8)}'"}],
            ROWCOUNT=3,
        )
        rows7 = r7.get("DATA", [])
        if rows7:
            f7 = r7.get("FIELDS", [])
            print(f"  PERNR {pernr} has RGDIR entries — THIS IS A PAYROLL PERNR:")
            for row in rows7:
                print(f"    {parse_fixed(row['WA'], f7)}")
        else:
            print(f"  PERNR {pernr}: no RGDIR entry")
    except Exception as ex:
        print(f"  RGDIR {pernr}: {str(ex)[:60]}")

conn.close()
print("\nProbe complete.")
