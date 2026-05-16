"""Find P01 production alt-payee cases via BSEC (one-time vendor / doc-level alt-payee).

BSEC holds the address-of-record per document. Populated when:
  (a) Vendor is CPD/one-time (KTOKK in CPD-type set; LFA1 has no address)
  (b) Document explicitly overrides the master address (entered at FB60/FB70 time)

For every BSEC row since 2024:
  - get LIFNR + address-on-doc (NAME1, STRAS, ORT01, LAND1)
  - cross-ref to REGUP → REGUH → DFPAYG to find which FORMI paid that doc

Goal: identify which SEPA-family formats actually emitted alt-payee/CPD data
       to the bank, in production.
"""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
params = dict(
    ashost=os.getenv("SAP_P01_ASHOST"), sysnr=os.getenv("SAP_P01_SYSNR"),
    client=os.getenv("SAP_P01_CLIENT"), user=os.getenv("SAP_P01_USER"),
    lang="EN", snc_mode="1",
    snc_partnername=os.getenv("SAP_P01_SNC_PARTNERNAME"), snc_qop="9",
)
conn = Connection(**params)
print("Connected P01")

def rd(t, opts, fields, n=2000):
    r = conn.call("RFC_READ_TABLE", QUERY_TABLE=t,
                  OPTIONS=[{"TEXT": x} for x in opts],
                  FIELDS=[{"FIELDNAME": x} for x in fields],
                  DELIMITER="|", ROWCOUNT=n)
    cols = [f["FIELDNAME"] for f in r.get("FIELDS",[])] or fields
    return [dict(zip(cols, d["WA"].split("|"))) for d in r.get("DATA", [])]

# === 1. Full BSEC scan since 2024 (cap at 5000) ===
print("\n=== BSEC rows since 2024 ===")
bsec = rd("BSEC",
          ["GJAHR >= '2024'"],
          ["BUKRS","BELNR","GJAHR","BUZEI","NAME1","LAND1"],
          n=5000)
print(f"  Total BSEC rows: {len(bsec)}")

# distribution by BUKRS
from collections import Counter
bk = Counter(r['BUKRS'].strip() for r in bsec)
print(f"  BUKRS distribution: {dict(bk.most_common())}")

# distribution by LAND1
ld = Counter(r['LAND1'].strip() for r in bsec)
print(f"  LAND1 distribution (top 15): {dict(ld.most_common(15))}")

# === 2. Cross-reference with REGUP → REGUH → DFPAYG to learn paying FORMI ===
# REGUP key: LAUFD, LAUFI, ZBUKR, LIFNR + invoice doc (BUKRS, BELNR, GJAHR)
# Strategy: take a sample of BSEC rows that look most likely to have been paid,
# then check whether they appear in REGUP. Sample by BUKRS + recent year.

# Pick a sample of representative BSEC rows from different BUKRS
sample_keys = []
seen_bukrs = set()
for r in bsec:
    b = r['BUKRS'].strip()
    if b not in seen_bukrs:
        seen_bukrs.add(b)
    sample_keys.append((b, r['BELNR'].strip(), r['GJAHR'].strip(), r['BUZEI'].strip(), r['NAME1'].strip(), r['LAND1'].strip()))

print(f"\n=== Cross-ref sample (up to 50): BSEC → REGUP → REGUH → DFPAYG ===")
hits_by_formi = Counter()
hits_examples = {}
for i, (bukrs, belnr, gjahr, buzei, name, land) in enumerate(sample_keys[:50]):
    # REGUP lookup
    try:
        regup_rows = rd("REGUP",
                        [f"BUKRS = '{bukrs}'", f" AND BELNR = '{belnr}'", f" AND GJAHR = '{gjahr}'"],
                        ["LAUFD","LAUFI","ZBUKR","LIFNR","BUKRS","BELNR","GJAHR","BUZEI"],
                        n=10)
        if not regup_rows:
            continue
        for rp in regup_rows:
            laufd = rp['LAUFD'].strip(); laufi = rp['LAUFI'].strip(); zb = rp['ZBUKR'].strip()
            # DFPAYG for the run
            try:
                gpg = rd("DFPAYG",
                         [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
                         ["FORMI"], n=5)
                for g in gpg:
                    formi = g['FORMI'].strip()
                    hits_by_formi[formi] += 1
                    if formi not in hits_examples:
                        hits_examples[formi] = f"  example: {bukrs}/{belnr}/{gjahr} {name[:25]} ({land}) → run {laufd}/{laufi}/{zb}"
            except Exception:
                pass
    except Exception:
        continue

print(f"\n=== Format distribution for BSEC docs that were actually paid ===")
for formi, n in hits_by_formi.most_common():
    print(f"  {formi:40s} {n}")
    print(hits_examples[formi])

print(f"\n=== Untraced BSEC ===")
print(f"  Of {len(sample_keys[:50])} BSEC docs sampled, {sum(hits_by_formi.values())} produced REGUP→DFPAYG hits")
