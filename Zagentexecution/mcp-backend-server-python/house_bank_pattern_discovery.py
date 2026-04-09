"""
house_bank_pattern_discovery.py
================================
Define configuration patterns from REAL data across all 67 active banks.
For each of the 13 steps: what's the actual pattern? what's missing?
Cross-reference ALL config tables to build the definitive bank profile.
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

# ══════════════════════════════════════════════════════════════
# LOAD ALL CONFIG TABLES
# ══════════════════════════════════════════════════════════════

# T012 + T012K
t012 = {}
for r in q("SELECT HBKID, BANKS, BANKL FROM T012 WHERE BUKRS='UNES'"):
    t012[r[0].strip()] = {"country": r[1].strip(), "bankl": r[2].strip()}

t012k = {}
for r in q("SELECT HBKID, HKTID, WAERS, HKONT, BANKN FROM T012K WHERE BUKRS='UNES'"):
    hbkid = r[0].strip()
    if hbkid not in t012k:
        t012k[hbkid] = []
    t012k[hbkid].append({"hktid": r[1].strip(), "waers": r[2].strip(),
                          "hkont": r[3].strip(), "bankn": r[4].strip()})

# T012T
t012t = {}
for r in q("SELECT HBKID, HKTID, TEXT1, SPRAS FROM T012T"):
    key = f"{r[0].strip()}_{r[1].strip()}_{r[2].strip() if r[3] else ''}"
    hbkid = r[0].strip()
    hktid = r[1].strip()
    if hbkid not in t012t:
        t012t[hbkid] = {}
    if hktid not in t012t[hbkid]:
        t012t[hbkid][hktid] = []
    t012t[hbkid][hktid].append(r[3].strip() if r[3] else "")

# SKAT closed
skat = {}
skat_closed = set()
for r in q("SELECT SAKNR, TXT50 FROM P01_SKAT WHERE KTOPL='UNES' AND SPRAS='E'"):
    saknr = r[0].strip()
    txt = r[1].strip() if r[1] else ""
    skat[saknr] = txt
    if "CLOSED" in txt.upper():
        skat_closed.add(saknr)

# SKA1
ska1 = {}
for r in q("SELECT SAKNR, KTOKS, XBILK FROM P01_SKA1 WHERE KTOPL='UNES'"):
    ska1[r[0].strip()] = {"KTOKS": r[1].strip() if r[1] else "", "XBILK": r[2].strip() if r[2] else ""}

# SKB1
skb1 = {}
for r in q("SELECT SAKNR, FDLEV, ZUAWA, XKRES, XGKON, FIPOS, FSTAG, XOPVW, HBKID, HKTID, WAERS, XINTB FROM P01_SKB1 WHERE BUKRS='UNES'"):
    fields = ["SAKNR","FDLEV","ZUAWA","XKRES","XGKON","FIPOS","FSTAG","XOPVW","HBKID","HKTID","WAERS","XINTB"]
    row = {f: (str(v).strip() if v else "") for f, v in zip(fields, r)}
    skb1[row["SAKNR"]] = row

# T030H
t030h = {}
for r in q("SELECT HKONT, CURTP, LKORR, LSREA, LHREA, LSBEW, LHBEW FROM T030H WHERE KTOPL='UNES'"):
    t030h[r[0].strip()] = {f: (r[i+1].strip() if r[i+1] else "") for i, f in enumerate(["CURTP","LKORR","LSREA","LHREA","LSBEW","LHBEW"])}

# T035D
t035d = {}
for r in q("SELECT DISKB, BNKKO FROM T035D WHERE BUKRS='UNES'"):
    t035d[r[0].strip()] = r[1].strip() if r[1] else ""

# T028B
t028b = {}
for r in q("SELECT BANKL, KTONR, VGTYP, BNKKO FROM T028B"):
    bankl = r[0].strip()
    if bankl not in t028b:
        t028b[bankl] = []
    t028b[bankl].append({"ktonr": (r[1].strip() if r[1] else ""), "vgtyp": (r[2].strip() if r[2] else ""), "bnkko": (r[3].strip() if r[3] else "")})

# T018V
t018v = {}
for r in q("SELECT HBKID, HKTID, GEHVK, WAERS, ZLSCH FROM T018V WHERE BUKRS='UNES'"):
    hbkid = r[0].strip()
    if hbkid not in t018v:
        t018v[hbkid] = []
    t018v[hbkid].append({"hktid": r[1].strip(), "clearing": r[2].strip() if r[2] else "",
                          "waers": r[3].strip(), "zlsch": r[4].strip()})

# T042I
t042i = {}
for r in q("SELECT HBKID, HKTID, ZLSCH, WAERS, UKONT FROM T042I WHERE ZBUKR='UNES'"):
    hbkid = r[0].strip()
    if hbkid not in t042i:
        t042i[hbkid] = []
    t042i[hbkid].append({"hktid": r[1].strip(), "zlsch": r[2].strip(), "waers": r[3].strip(), "ukont": r[4].strip() if r[4] else ""})

# T042A (DMEE routing)
t042a = {}
for r in q("SELECT HBKID, HKTID FROM T042A WHERE ZBUKR='UNES'"):
    hbkid = r[0].strip()
    t042a[hbkid] = t042a.get(hbkid, 0) + 1

# FEBEP activity
febep_banks = set()
for r in q("SELECT DISTINCT HBKID FROM FEBEP_2024_2026"):
    febep_banks.add(r[0].strip() if r[0] else "")

# REGUH activity
reguh_banks = set()
for r in q("SELECT DISTINCT UBHBK FROM REGUH WHERE ZBUKR='UNES'"):
    reguh_banks.add(r[0].strip() if r[0] else "")

# BNK_BATCH (BCM)
bcm_banks = set()
for r in q("SELECT DISTINCT HBKID FROM BNK_BATCH_HEADER"):
    bcm_banks.add(r[0].strip() if r[0] else "")

# ══════════════════════════════════════════════════════════════
# HELPER
# ══════════════════════════════════════════════════════════════

def derive_clearing(hkont):
    sig = hkont.lstrip('0')
    if sig.startswith('10'):
        return ('11' + sig[2:]).zfill(len(hkont))
    return None

def is_bank_closed(hbkid):
    accts = t012k.get(hbkid, [])
    for a in accts:
        if a["hkont"] in skat_closed:
            return True
        clr = derive_clearing(a["hkont"])
        if clr and clr in skat_closed:
            return True
    return False

# ══════════════════════════════════════════════════════════════
# BUILD FULL PROFILE PER ACTIVE BANK
# ══════════════════════════════════════════════════════════════

print("="*70)
print("  CONFIGURATION PATTERN DISCOVERY — ALL ACTIVE BANKS")
print("="*70)

profiles = []

for hbkid in sorted(t012.keys()):
    if is_bank_closed(hbkid):
        continue
    if hbkid not in t012k:
        continue

    info = t012[hbkid]
    accts = t012k[hbkid]
    bankl = info["bankl"]
    country = info["country"]
    currencies = sorted(set(a["waers"] for a in accts))
    has_non_usd = any(c != "USD" for c in currencies)

    profile = {
        "hbkid": hbkid, "country": country, "bankl": bankl,
        "num_accounts": len(accts), "currencies": currencies,
        "steps": {},
    }

    # ── STEP 1: FS00 (SKA1 + SKB1) ──
    step1 = {"status": "OK", "issues": []}
    for a in accts:
        gl = a["hkont"]
        clr = derive_clearing(gl)
        for check_gl, gl_label in [(gl, "bank"), (clr, "clearing")]:
            if not check_gl:
                continue
            ka = ska1.get(check_gl, {})
            sb = skb1.get(check_gl, {})
            if not ka:
                step1["issues"].append(f"{check_gl}({gl_label}):NOT_IN_SKA1")
                step1["status"] = "FAIL"
                continue
            if ka.get("KTOKS") != "BANK":
                step1["issues"].append(f"{check_gl}:KTOKS={ka.get('KTOKS','?')}")
                step1["status"] = "FAIL"
            if not sb:
                step1["issues"].append(f"{check_gl}({gl_label}):NOT_IN_SKB1")
                step1["status"] = "FAIL"
                continue
            # Bank vs clearing field expectations
            if gl_label == "bank":
                if sb.get("FDLEV") != "B0": step1["issues"].append(f"{check_gl}:FDLEV={sb.get('FDLEV','')}")
                if sb.get("ZUAWA") != "027": step1["issues"].append(f"{check_gl}:ZUAWA={sb.get('ZUAWA','')}")
            else:
                if sb.get("FDLEV") != "B1": step1["issues"].append(f"{check_gl}:FDLEV={sb.get('FDLEV','')}")
                if sb.get("ZUAWA") != "Z01": step1["issues"].append(f"{check_gl}:ZUAWA={sb.get('ZUAWA','')}")
                if sb.get("XOPVW") != "X": step1["issues"].append(f"{check_gl}:XOPVW={sb.get('XOPVW','')}")
            # Common checks
            if sb.get("HBKID") and sb["HBKID"] != hbkid:
                step1["issues"].append(f"{check_gl}:HBKID={sb['HBKID']}!={hbkid}")
                step1["status"] = "FAIL"
            if sb.get("FSTAG") != "UN03": step1["issues"].append(f"{check_gl}:FSTAG={sb.get('FSTAG','')}")
    if step1["issues"]:
        step1["status"] = "ISSUE"
    profile["steps"]["1_FS00"] = step1

    # ── STEP 2: FI12 (T012 + T012K + T012T) ──
    step2 = {"status": "OK", "issues": []}
    descs = t012t.get(hbkid, {})
    for a in accts:
        if a["hktid"] not in descs:
            step2["issues"].append(f"{a['hktid']}:NO_T012T")
    if step2["issues"]:
        step2["status"] = "WARN"
    profile["steps"]["2_FI12"] = step2

    # ── STEP 4: OBA1 (T030H) ──
    step4 = {"status": "OK", "issues": []}
    for a in accts:
        clr = derive_clearing(a["hkont"])
        if not clr:
            continue
        entry = t030h.get(clr)
        if entry:
            missing = [f for f in ["LKORR","LSREA","LHREA","LSBEW","LHBEW"]
                        if not entry[f] or entry[f] == "0000000000"]
            if missing:
                step4["issues"].append(f"{clr}({a['waers']}):missing {','.join(missing)}")
                step4["status"] = "FAIL"
        else:
            if a["waers"] != "USD":
                step4["issues"].append(f"{clr}({a['waers']}):MISSING_REQUIRED")
                step4["status"] = "FAIL"
    profile["steps"]["4_OBA1"] = step4

    # ── STEP 5: Cash Mgmt Account Name (T035D view) ──
    # T035D contains both CM account names and EBS symbols
    # CM names follow pattern: HBKID-CUR{N}
    step5 = {"status": "OK", "issues": []}
    cm_names = [k for k in t035d.keys() if hbkid in k]
    if not cm_names:
        step5["status"] = "MISS"
        step5["issues"].append("No CM account names")
    else:
        # Check each account has a CM name
        for a in accts:
            found = any(hbkid in k and a["waers"][:3].upper() in k.upper() for k in cm_names)
            if not found:
                step5["issues"].append(f"{a['hktid']}({a['waers']}):no CM name")
    if step5["issues"] and step5["status"] == "OK":
        step5["status"] = "WARN"
    profile["steps"]["5_CM_NAME"] = step5

    # ── STEP 6a: T035D (EBS account symbols) ──
    step6a = {"status": "OK", "issues": []}
    if not cm_names:
        step6a["status"] = "MISS"
    profile["steps"]["6a_T035D"] = step6a

    # ── STEP 6b: T028B ──
    step6b = {"status": "OK", "issues": []}
    bankl_entries = t028b.get(bankl, [])
    if not bankl_entries:
        step6b["status"] = "MISS"
        step6b["issues"].append(f"No T028B for bankl={bankl}")
    else:
        # Check each account's bank number is mapped
        for a in accts:
            found = any(e["ktonr"].strip() == a["bankn"].strip() for e in bankl_entries)
            if not found and a["bankn"]:
                step6b["issues"].append(f"{a['hktid']}:bankn={a['bankn']} not in T028B")
        # Check transaction type
        vgtyps = set(e["vgtyp"] for e in bankl_entries)
        step6b["vgtyp"] = sorted(vgtyps)
    if step6b["issues"] and step6b["status"] == "OK":
        step6b["status"] = "WARN"
    profile["steps"]["6b_T028B"] = step6b

    # ── STEP 8: T018V ──
    step8 = {"status": "OK", "issues": []}
    t018v_entries = t018v.get(hbkid, [])
    if not t018v_entries:
        step8["status"] = "MISS"
    else:
        # Verify clearing GL matches derived
        for e in t018v_entries:
            for a in accts:
                if a["hktid"] == e["hktid"]:
                    expected_clr = derive_clearing(a["hkont"])
                    if expected_clr and e["clearing"] and e["clearing"] != expected_clr:
                        step8["issues"].append(f"{e['hktid']}:T018V clr={e['clearing']} != derived {expected_clr}")
        # Check all accounts have T018V
        t018v_hktids = set(e["hktid"] for e in t018v_entries)
        for a in accts:
            if a["hktid"] not in t018v_hktids:
                step8["issues"].append(f"{a['hktid']}:no T018V entry")
    if step8["issues"] and step8["status"] == "OK":
        step8["status"] = "WARN"
    profile["steps"]["8_T018V"] = step8

    # ── STEP 9.1: T042I ──
    step91 = {"status": "N/A", "issues": []}
    t042i_entries = t042i.get(hbkid, [])
    if t042i_entries:
        step91["status"] = "OK"
        step91["methods"] = sorted(set(e["zlsch"] for e in t042i_entries))
    profile["steps"]["9.1_T042I"] = step91

    # ── Activity flags ──
    profile["has_febep"] = hbkid in febep_banks
    profile["has_reguh"] = hbkid in reguh_banks
    profile["has_bcm"] = hbkid in bcm_banks
    profile["has_t042a"] = hbkid in t042a

    # ── Classify ──
    if hbkid in t042i:
        profile["category"] = "PAYING"
    elif hbkid in febep_banks:
        profile["category"] = "EBS_ACTIVE"
    elif bankl in t028b or cm_names:
        profile["category"] = "EBS_CONFIG"
    elif t018v_entries:
        profile["category"] = "RECEIVING"
    else:
        profile["category"] = "BASIC"

    profiles.append(profile)

# ══════════════════════════════════════════════════════════════
# PATTERN ANALYSIS
# ══════════════════════════════════════════════════════════════

print(f"\n  Active banks analyzed: {len(profiles)}")

# ── By category ──
cats = {}
for p in profiles:
    c = p["category"]
    if c not in cats:
        cats[c] = []
    cats[c].append(p)

for cat in ["PAYING","EBS_ACTIVE","EBS_CONFIG","RECEIVING","BASIC"]:
    banks = cats.get(cat, [])
    if not banks:
        continue
    print(f"\n{'='*70}")
    print(f"  {cat} ({len(banks)} banks)")
    print(f"{'='*70}")

    # Step-by-step compliance
    steps = ["1_FS00","2_FI12","4_OBA1","5_CM_NAME","6a_T035D","6b_T028B","8_T018V","9.1_T042I"]
    step_stats = {s: {"OK":0,"FAIL":0,"MISS":0,"WARN":0,"ISSUE":0,"N/A":0} for s in steps}

    for p in banks:
        for s in steps:
            status = p["steps"].get(s, {}).get("status", "?")
            if status in step_stats[s]:
                step_stats[s][status] += 1

    print(f"\n  Step compliance:")
    print(f"  {'Step':12s} {'OK':>4s} {'FAIL':>5s} {'MISS':>5s} {'WARN':>5s} {'ISSUE':>6s} {'N/A':>4s}")
    for s in steps:
        st = step_stats[s]
        print(f"  {s:12s} {st['OK']:4d} {st['FAIL']:5d} {st['MISS']:5d} {st['WARN']:5d} {st['ISSUE']:6d} {st['N/A']:4d}")

    # List banks with issues per step
    for s in steps:
        issues_banks = [p for p in banks if p["steps"].get(s, {}).get("status", "OK") not in ("OK","N/A")]
        if issues_banks:
            print(f"\n  {s} issues:")
            for p in issues_banks:
                step_info = p["steps"][s]
                print(f"    {p['hbkid']:8s} [{step_info['status']}] {'; '.join(step_info.get('issues',[])[:3])}")

# ── T028B transaction type patterns ──
print(f"\n{'='*70}")
print("  T028B TRANSACTION TYPE PATTERNS")
print("="*70)

vgtyp_banks = {}
for p in profiles:
    vgtyps = p["steps"].get("6b_T028B", {}).get("vgtyp", [])
    key = ",".join(vgtyps) if vgtyps else "(none)"
    if key not in vgtyp_banks:
        vgtyp_banks[key] = []
    vgtyp_banks[key].append(p["hbkid"])

for vgtyp, banks in sorted(vgtyp_banks.items(), key=lambda x: -len(x[1])):
    print(f"  {vgtyp:20s}: {len(banks):3d} banks — {', '.join(banks[:10])}")

# ── T018V payment method patterns ──
print(f"\n{'='*70}")
print("  T018V PAYMENT METHOD PATTERNS")
print("="*70)

t018v_patterns = {}
for p in profiles:
    entries = t018v.get(p["hbkid"], [])
    methods = sorted(set(e["zlsch"] for e in entries)) if entries else ["(none)"]
    key = ",".join(methods)
    if key not in t018v_patterns:
        t018v_patterns[key] = []
    t018v_patterns[key].append(p["hbkid"])

for pattern, banks in sorted(t018v_patterns.items(), key=lambda x: -len(x[1])):
    print(f"  {pattern:10s}: {len(banks):3d} banks")

# ── T042I paying bank patterns ──
print(f"\n{'='*70}")
print("  T042I PAYING BANK PATTERNS")
print("="*70)

for p in [p for p in profiles if p["category"] == "PAYING"]:
    print(f"\n  {p['hbkid']} ({p['country']}, {','.join(p['currencies'])}):")
    for e in t042i.get(p["hbkid"], []):
        print(f"    Method={e['zlsch']:3s} Currency={e['waers']:5s} AcctID={e['hktid']:8s} Clearing={e['ukont']}")
    if p["has_t042a"]:
        print(f"    T042A DMEE routing: {t042a[p['hbkid']]} entries")
    if p["has_bcm"]:
        print(f"    BCM: active")

# ── Currency coverage ──
print(f"\n{'='*70}")
print("  CURRENCY COVERAGE")
print("="*70)

cur_count = {}
for p in profiles:
    for c in p["currencies"]:
        cur_count[c] = cur_count.get(c, 0) + 1

print(f"  {len(cur_count)} currencies across {len(profiles)} active banks:")
for c, cnt in sorted(cur_count.items(), key=lambda x: -x[1]):
    print(f"    {c:5s}: {cnt:3d} banks")

# ── DEFINITIVE PATTERN TABLE ──
print(f"\n{'='*70}")
print("  DEFINITIVE CONFIGURATION PATTERNS")
print("="*70)

# Count patterns
all_ok = sum(1 for p in profiles
             if all(p["steps"][s]["status"] in ("OK","N/A")
                    for s in ["1_FS00","2_FI12","4_OBA1","5_CM_NAME","6a_T035D","6b_T028B","8_T018V"]))
some_issue = len(profiles) - all_ok

print(f"\n  Fully compliant banks (all checked steps OK): {all_ok} / {len(profiles)} ({all_ok/len(profiles)*100:.0f}%)")
print(f"  Banks with at least 1 issue: {some_issue}")

# Banks with issues — sorted by severity
issue_banks = []
for p in profiles:
    issues = []
    for s in ["1_FS00","2_FI12","4_OBA1","5_CM_NAME","6a_T035D","6b_T028B","8_T018V"]:
        st = p["steps"][s]
        if st["status"] not in ("OK","N/A"):
            issues.extend([f"{s}:{i}" for i in st.get("issues",[])])
    if issues:
        issue_banks.append({"hbkid": p["hbkid"], "cat": p["category"], "issues": issues})

if issue_banks:
    print(f"\n  All banks with issues:")
    for b in sorted(issue_banks, key=lambda x: -len(x["issues"])):
        print(f"    {b['hbkid']:8s} [{b['cat']:12s}] {len(b['issues'])} issues: {'; '.join(b['issues'][:5])}")

# ── Step requirement by category ──
print(f"\n  Configuration steps required per bank type:")
print(f"  {'Step':12s} {'PAYING':8s} {'EBS_CFG':8s} {'BASIC':8s} {'Notes'}")
print(f"  {'-'*12} {'-'*8} {'-'*8} {'-'*8} {'-'*30}")
step_defs = [
    ("1_FS00",     "REQ","REQ","REQ","SKA1+SKB1: KTOKS=BANK, FDLEV B0/B1, ZUAWA 027/Z01"),
    ("2_FI12",     "REQ","REQ","REQ","T012+T012K+T012T"),
    ("3_FTE_BSM",  "REQ","REQ","REQ","Not in Gold DB (FCLM_BSM_CUST)"),
    ("4_OBA1",     "REQ","REQ","REQ","T030H: non-USD clearing must have all 5 fields"),
    ("5_CM_NAME",  "REQ","REQ","OPT","T035D CM account names: {HBKID}-{CUR}{N}"),
    ("6a_T035D",   "REQ","REQ","OPT","T035D EBS symbols"),
    ("6b_T028B",   "REQ","REQ","OPT","T028B: bankl+bankn -> vgtyp. 93% XRT940"),
    ("7_BASU",     "N/A","N/A","N/A","Range 1000000-1199999 covered by Z1"),
    ("8_T018V",    "REQ","REQ","OPT","T018V: 100% method A"),
    ("9.1_T042I",  "REQ","N/A","N/A","Only 2 paying banks: CIT21, ECO09"),
    ("9.2_INTXFR", "REQ","N/A","N/A","Account determination for G/L payments"),
    ("9.3_OBPM4",  "REQ","N/A","N/A","SAPFPAYM variant + OBPM4 link (V01+P01)"),
    ("10_GS02",    "REQ","REQ","OPT","SETLEAF: bank GL in YBANK_ACCOUNTS_*"),
    ("11_TRM5",    "N/A","N/A","N/A","No longer required (2026-04-07)"),
    ("12_T038",    "N/A","N/A","N/A","Grouping is symbol-based"),
    ("13_TIBAN",   "OPT","OPT","OPT","IBAN generation"),
]
for s, pay, ebs, basic, notes in step_defs:
    print(f"  {s:12s} {pay:8s} {ebs:8s} {basic:8s} {notes}")

conn.close()

# Save
out = os.path.join(os.path.dirname(__file__), "house_bank_patterns.json")
with open(out, "w") as f:
    json.dump(profiles, f, indent=2, default=str)
print(f"\nSaved to: {out}")
