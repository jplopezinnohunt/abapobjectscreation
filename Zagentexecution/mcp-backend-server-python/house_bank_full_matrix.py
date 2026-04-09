"""
house_bank_full_matrix.py
==========================
Full 13-step compliance matrix for ALL house banks using Gold DB.
Now with T030H, T035D, T018V, T012T extracted.
Groups CLOSED banks separately. Discovers config patterns.
"""
import sqlite3, os, sys, io, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB = os.path.join(os.path.dirname(__file__), "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
conn = sqlite3.connect(DB)

def q(sql):
    try:
        return conn.execute(sql).fetchall()
    except:
        return []

def cols(table):
    return [r[1] for r in q(f"PRAGMA table_info({table})")]

# ── Load all reference data ──
# T012
t012 = {}
for r in q("SELECT HBKID, BANKS, BANKL FROM T012 WHERE BUKRS='UNES'"):
    t012[r[0].strip()] = {"country": r[1].strip(), "bankl": r[2].strip()}

# T012K
t012k = {}
for r in q("SELECT HBKID, HKTID, WAERS, HKONT, BANKN FROM T012K WHERE BUKRS='UNES'"):
    hbkid = r[0].strip()
    if hbkid not in t012k:
        t012k[hbkid] = []
    t012k[hbkid].append({
        "hktid": r[1].strip(), "waers": r[2].strip(),
        "hkont": r[3].strip(), "bankn": r[4].strip()
    })

# SKAT — detect closed
skat_closed = set()
for r in q("SELECT SAKNR, TXT50 FROM P01_SKAT WHERE KTOPL='UNES' AND SPRAS='E'"):
    if r[1] and "CLOSED" in r[1].upper():
        skat_closed.add(r[0].strip())

# T012T — descriptions
t012t = {}
for r in q("SELECT HBKID, HKTID, TEXT1, SPRAS FROM T012T"):
    key = f"{r[0].strip()}_{r[1].strip()}"
    t012t[key] = r[2].strip() if r[2] else ""

# T030H — OBA1
t030h = {}
for r in q("SELECT HKONT, CURTP, LKORR, LSREA, LHREA, LSBEW, LHBEW FROM T030H WHERE KTOPL='UNES'"):
    hkont = r[0].strip()
    t030h[hkont] = {
        "CURTP": r[1].strip() if r[1] else "",
        "LKORR": r[2].strip() if r[2] else "",
        "LSREA": r[3].strip() if r[3] else "",
        "LHREA": r[4].strip() if r[4] else "",
        "LSBEW": r[5].strip() if r[5] else "",
        "LHBEW": r[6].strip() if r[6] else "",
    }

# T035D — EBS account symbols
t035d = {}
for r in q("SELECT DISKB, BNKKO FROM T035D WHERE BUKRS='UNES'"):
    t035d[r[0].strip()] = r[1].strip() if r[1] else ""

# T028B — EBS posting rules (by BANKL)
t028b = {}
for r in q("SELECT BANKL, KTONR, VGTYP, BNKKO FROM T028B"):
    bankl = r[0].strip()
    if bankl not in t028b:
        t028b[bankl] = []
    t028b[bankl].append({"ktonr": r[1], "vgtyp": r[2], "bnkko": r[3]})

# T018V — receiving accounts
t018v = {}
for r in q("SELECT HBKID, HKTID, GEHVK, WAERS, ZLSCH FROM T018V WHERE BUKRS='UNES'"):
    hbkid = r[0].strip()
    if hbkid not in t018v:
        t018v[hbkid] = []
    t018v[hbkid].append({
        "hktid": r[1].strip(), "clearing": r[2].strip() if r[2] else "",
        "waers": r[3].strip(), "zlsch": r[4].strip()
    })

# T042I — payment determination
t042i = {}
for r in q("SELECT HBKID, HKTID, ZLSCH, WAERS, UKONT FROM T042I WHERE ZBUKR='UNES'"):
    hbkid = r[0].strip()
    if hbkid not in t042i:
        t042i[hbkid] = []
    t042i[hbkid].append({"hktid": r[1], "zlsch": r[2], "waers": r[3], "ukont": r[4]})

# P01_SKB1 — company code data
skb1 = {}
skb1_fields = ["SAKNR","FDLEV","ZUAWA","XKRES","XGKON","FIPOS","FSTAG","XOPVW","HBKID","HKTID","WAERS","XINTB"]
avail = [f for f in skb1_fields if f in cols("P01_SKB1")]
for r in q(f"SELECT {','.join(avail)} FROM P01_SKB1 WHERE BUKRS='UNES'"):
    row = dict(zip(avail, [str(v).strip() if v else "" for v in r]))
    skb1[row["SAKNR"]] = row

# P01_SKA1
ska1 = {}
for r in q("SELECT SAKNR, KTOKS FROM P01_SKA1 WHERE KTOPL='UNES'"):
    ska1[r[0].strip()] = r[1].strip() if r[1] else ""

# SETLEAF (from live data if available, otherwise skip)
# We checked this lives in live system, not Gold DB

# FEBEP — which banks have actual EBS activity
febep_banks = set()
febep_cols = cols("FEBEP_2024_2026")
if "HBKID" in febep_cols:
    for r in q("SELECT DISTINCT HBKID FROM FEBEP_2024_2026"):
        febep_banks.add(r[0].strip() if r[0] else "")

# REGUH — payment activity
reguh_banks = set()
if "UBHBK" in cols("REGUH"):
    for r in q("SELECT DISTINCT UBHBK FROM REGUH WHERE ZBUKR='UNES'"):
        reguh_banks.add(r[0].strip() if r[0] else "")

# ── Build full matrix ──
def derive_clearing(hkont):
    sig = hkont.lstrip('0')
    if sig.startswith('10'):
        return ('11' + sig[2:]).zfill(len(hkont))
    return None

print("="*70)
print("  FULL HOUSE BANK CONFIGURATION MATRIX (P01)")
print("="*70)

results = []
closed_banks = []
active_banks = []

for hbkid in sorted(t012.keys()):
    info = t012[hbkid]
    accounts = t012k.get(hbkid, [])
    if not accounts:
        continue

    # All GLs
    all_gls = []
    bank_gls = []
    clearing_gls = []
    for a in accounts:
        gl = a["hkont"]
        if gl:
            bank_gls.append(gl)
            all_gls.append(gl)
            clr = derive_clearing(gl)
            if clr:
                clearing_gls.append(clr)
                all_gls.append(clr)

    # Is closed?
    is_closed = any(gl in skat_closed for gl in all_gls)
    currencies = list(set(a["waers"] for a in accounts))
    has_non_usd = any(c != "USD" for c in currencies)

    # Step checks
    checks = {}

    # Step 1: FS00 — SKA1/SKB1
    ska1_ok = all(ska1.get(gl) == "BANK" for gl in bank_gls if gl in ska1)
    ska1_issues = [f"{gl}:KTOKS={ska1.get(gl,'?')}" for gl in bank_gls if gl in ska1 and ska1[gl] != "BANK"]
    checks["1_FS00"] = "OK" if ska1_ok and bank_gls else "MISS"

    # SKB1 field checks
    skb1_issues = []
    for gl in all_gls:
        s = skb1.get(gl)
        if not s:
            continue
        if s.get("HBKID") and s["HBKID"] != hbkid:
            skb1_issues.append(f"{gl}:HBKID={s['HBKID']}")
        clr = gl.lstrip('0')
        if clr.startswith('11') and s.get("XOPVW") != "X":
            skb1_issues.append(f"{gl}:XOPVW={s.get('XOPVW','')}")

    # Step 2: FI12
    checks["2_FI12"] = "OK"  # If we got here, T012K exists

    # Step 4: OBA1/T030H
    t030h_ok = True
    t030h_detail = []
    for clr in clearing_gls:
        entry = t030h.get(clr)
        if entry:
            missing = []
            if not entry["LKORR"] or entry["LKORR"] == "0000000000":
                missing.append("LKORR")
            if not entry["LSBEW"] or entry["LSBEW"] == "0000000000":
                missing.append("LSBEW")
            if not entry["LHBEW"] or entry["LHBEW"] == "0000000000":
                missing.append("LHBEW")
            if missing:
                t030h_detail.append(f"{clr}:missing {','.join(missing)}")
                t030h_ok = False
            else:
                t030h_detail.append(f"{clr}:OK")
        else:
            # Non-USD clearing needs entry
            gl_cur = None
            for a in accounts:
                if derive_clearing(a["hkont"]) == clr:
                    gl_cur = a["waers"]
            if gl_cur and gl_cur != "USD":
                t030h_detail.append(f"{clr}:MISSING(required,{gl_cur})")
                t030h_ok = False
            else:
                t030h_detail.append(f"{clr}:none(USD,optional)")
    checks["4_OBA1"] = "OK" if t030h_ok else "FAIL"

    # Step 6a: T035D
    t035d_matches = [k for k in t035d.keys() if hbkid in k]
    checks["6a_T035D"] = "OK" if t035d_matches else "MISS"

    # Step 6b: T028B
    bankl = info["bankl"]
    has_t028b = bankl in t028b
    checks["6b_T028B"] = "OK" if has_t028b else "MISS"

    # Step 8: T018V
    has_t018v = hbkid in t018v
    checks["8_T018V"] = "OK" if has_t018v else "MISS"

    # Step 9.1: T042I
    has_t042i = hbkid in t042i
    checks["9.1_T042I"] = "OK" if has_t042i else "N/A"

    # Activity
    has_febep = hbkid in febep_banks
    has_reguh = hbkid in reguh_banks

    # Classify
    if is_closed:
        cat = "CLOSED"
    elif has_t042i:
        cat = "PAYING"
    elif has_febep:
        cat = "EBS_ACTIVE"
    elif has_t028b or t035d_matches:
        cat = "EBS_CONFIG"
    elif has_t018v:
        cat = "RECEIVING"
    else:
        cat = "BASIC"

    entry = {
        "hbkid": hbkid, "country": info["country"], "currencies": currencies,
        "num_accounts": len(accounts), "category": cat,
        "checks": checks, "t030h_detail": t030h_detail,
        "skb1_issues": skb1_issues + ska1_issues,
        "has_febep": has_febep, "has_reguh": has_reguh,
    }
    results.append(entry)

    if is_closed:
        closed_banks.append(entry)
    else:
        active_banks.append(entry)

# ── Print active banks ──
print(f"\n  ACTIVE BANKS ({len(active_banks)}):")
print(f"  {'HBKID':8s} {'Cat':12s} {'CC':3s} {'#':2s} {'Cur':15s} {'FS00':5s} {'OBA1':5s} {'T035D':6s} {'T028B':6s} {'T018V':6s} {'T042I':6s} {'Issues'}")
print(f"  {'-'*8} {'-'*12} {'-'*3} {'-'*2} {'-'*15} {'-'*5} {'-'*5} {'-'*6} {'-'*6} {'-'*6} {'-'*6} {'-'*20}")

for b in sorted(active_banks, key=lambda x: x["category"]):
    c = b["checks"]
    issues = b["skb1_issues"][:2]
    issue_str = "; ".join(issues) if issues else ""
    print(f"  {b['hbkid']:8s} {b['category']:12s} {b['country']:3s} {b['num_accounts']:2d} {','.join(b['currencies']):<15s} "
          f"{c.get('1_FS00','?'):5s} {c.get('4_OBA1','?'):5s} {c.get('6a_T035D','?'):6s} {c.get('6b_T028B','?'):6s} "
          f"{c.get('8_T018V','?'):6s} {c.get('9.1_T042I','?'):6s} {issue_str}")

# ── OBA1 analysis ──
print(f"\n{'='*70}")
print("  OBA1 (T030H) PATTERN ANALYSIS")
print("="*70)
print(f"  Total T030H entries (UNES): {len(t030h)}")

# Completeness
complete = 0
partial = 0
for hkont, entry in t030h.items():
    has_all = all(entry[f] and entry[f] != "0000000000"
                  for f in ["LKORR","LSREA","LHREA","LSBEW","LHBEW"])
    if has_all:
        complete += 1
    else:
        partial += 1
print(f"  Complete (all 5 fields): {complete}")
print(f"  Partial (missing fields): {partial}")

# Show partial entries
if partial > 0:
    print(f"\n  Partial entries (missing LKORR/LSBEW/LHBEW):")
    for hkont, entry in sorted(t030h.items()):
        missing = []
        for f in ["LKORR","LSBEW","LHBEW"]:
            if not entry[f] or entry[f] == "0000000000":
                missing.append(f)
        if missing:
            print(f"    {hkont}: missing {','.join(missing)}")

# Active banks with OBA1 issues
print(f"\n  Active banks with OBA1 issues:")
for b in active_banks:
    if b["checks"].get("4_OBA1") == "FAIL":
        print(f"    {b['hbkid']}: {b['t030h_detail']}")

# ── T018V pattern ──
print(f"\n{'='*70}")
print("  T018V RECEIVING ACCOUNT PATTERNS")
print("="*70)
print(f"  Total T018V entries (UNES): {sum(len(v) for v in t018v.values())}")
print(f"  Banks with T018V: {len(t018v)}")

# Payment method distribution
zlsch_dist = {}
for hbkid, entries in t018v.items():
    for e in entries:
        z = e["zlsch"]
        zlsch_dist[z] = zlsch_dist.get(z, 0) + 1
print(f"\n  Payment method distribution:")
for z, cnt in sorted(zlsch_dist.items(), key=lambda x: -x[1]):
    print(f"    {z or '(empty)':5s}: {cnt}")

# Active banks WITHOUT T018V
missing_t018v = [b for b in active_banks if b["checks"].get("8_T018V") == "MISS"]
print(f"\n  Active banks WITHOUT T018V ({len(missing_t018v)}):")
for b in missing_t018v[:20]:
    print(f"    {b['hbkid']:8s} {b['category']:12s} {b['country']:3s} {','.join(b['currencies'])}")

# ── Summary ──
print(f"\n{'='*70}")
print("  FINAL SUMMARY")
print("="*70)

cats = {}
for b in results:
    cat = b["category"]
    cats[cat] = cats.get(cat, 0) + 1

print(f"  Total banks: {len(results)}")
for cat, cnt in sorted(cats.items(), key=lambda x: -x[1]):
    print(f"    {cat:15s}: {cnt}")

# Config quality for active banks
total_checks = 0
total_ok = 0
for b in active_banks:
    for k, v in b["checks"].items():
        if v != "N/A":
            total_checks += 1
            if v == "OK":
                total_ok += 1
if total_checks:
    print(f"\n  Active bank config quality: {total_ok}/{total_checks} ({total_ok/total_checks*100:.0f}%)")

conn.close()

# Save
out = os.path.join(os.path.dirname(__file__), "house_bank_full_matrix.json")
with open(out, "w") as f:
    json.dump(results, f, indent=2, default=str)
print(f"\nSaved to: {out}")
