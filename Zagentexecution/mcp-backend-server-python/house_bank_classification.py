"""
house_bank_classification.py
=============================
Classify ALL 211 house banks using Gold DB tables.
Determine bank type + which config steps are needed/present.
"""
import sqlite3, os, sys, io, json
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB = os.path.join(os.path.dirname(__file__), "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
conn = sqlite3.connect(DB)

def q(sql):
    try:
        return conn.execute(sql).fetchall()
    except Exception as e:
        return []

def cols(table):
    return [r[1] for r in q(f"PRAGMA table_info({table})")]

# ── 1. Build bank master ──
print("="*70)
print("  Building House Bank Master from Gold DB")
print("="*70)

banks = {}
for r in q("SELECT HBKID, BANKS, BANKL FROM T012 WHERE BUKRS='UNES' ORDER BY HBKID"):
    banks[r[0]] = {"country": r[1], "bankl": r[2], "accounts": [], "config": {}}

# T012K accounts
for r in q("SELECT HBKID, HKTID, WAERS, HKONT, BANKN FROM T012K WHERE BUKRS='UNES'"):
    hbkid = r[0]
    if hbkid in banks:
        banks[hbkid]["accounts"].append({
            "hktid": r[1], "waers": r[2], "hkont": r[3], "bankn": r[4]
        })

print(f"  {len(banks)} house banks loaded")

# ── 2. Check each config table ──

# P01_SKA1 — account group
ska1_cols = cols("P01_SKA1")
print(f"\n  P01_SKA1 cols: {ska1_cols}")
ska1_map = {}
for r in q("SELECT SAKNR, KTOKS, XBILK FROM P01_SKA1 WHERE KTOPL='UNES'"):
    ska1_map[r[0].strip()] = {"KTOKS": r[1].strip() if r[1] else "", "XBILK": r[2].strip() if r[2] else ""}

# P01_SKB1 — company code level
skb1_cols = cols("P01_SKB1")
print(f"  P01_SKB1 cols: {skb1_cols}")
skb1_map = {}
needed_skb1 = ["SAKNR","FDLEV","ZUAWA","XKRES","XGKON","FIPOS","FSTAG","XOPVW","HBKID","HKTID","WAERS","XINTB"]
avail_skb1 = [f for f in needed_skb1 if f in skb1_cols]
print(f"  Available SKB1 fields: {avail_skb1}")

for r in q(f"SELECT {','.join(avail_skb1)} FROM P01_SKB1 WHERE BUKRS='UNES'"):
    row = dict(zip(avail_skb1, [str(v).strip() if v else "" for v in r]))
    skb1_map[row["SAKNR"]] = row

# P01_SKAT — texts (detect CLOSED)
skat_closed = set()
for r in q("SELECT SAKNR, TXT50 FROM P01_SKAT WHERE KTOPL='UNES' AND SPRAS='E'"):
    saknr = r[0].strip() if r[0] else ""
    txt = r[1].strip().upper() if r[1] else ""
    if "CLOSED" in txt or "DELETED" in txt:
        skat_closed.add(saknr)

# T028B — EBS posting rules (keyed by BANKL)
t028b_by_bankl = {}
for r in q("SELECT BANKL, KTONR, VGTYP, BNKKO FROM T028B"):
    bankl = r[0].strip() if r[0] else ""
    if bankl not in t028b_by_bankl:
        t028b_by_bankl[bankl] = []
    t028b_by_bankl[bankl].append({"ktonr": r[1], "vgtyp": r[2], "bnkko": r[3]})

# T042I — payment bank determination
t042i_by_hbkid = {}
for r in q("SELECT HBKID, HKTID, ZLSCH, WAERS, UKONT FROM T042I WHERE ZBUKR='UNES'"):
    hbkid = r[0].strip() if r[0] else ""
    if hbkid not in t042i_by_hbkid:
        t042i_by_hbkid[hbkid] = []
    t042i_by_hbkid[hbkid].append({"hktid": r[1], "zlsch": r[2], "waers": r[3], "ukont": r[4]})

# T042A — bank routing (DMEE)
t042a_by_hbkid = {}
for r in q("SELECT HBKID, HKTID, DMESSION FROM T042A WHERE ZBUKR='UNES'"):
    hbkid = r[0].strip() if r[0] else ""
    if hbkid not in t042a_by_hbkid:
        t042a_by_hbkid[hbkid] = []
    t042a_by_hbkid[hbkid].append({"hktid": r[1], "dmee": r[2]})

# FEBEP — actual bank statement items (which banks have EBS activity)
febep_banks = set()
febep_cols = cols("FEBEP_2024_2026")
if "HBKID" in febep_cols:
    for r in q("SELECT DISTINCT HBKID FROM FEBEP_2024_2026"):
        febep_banks.add(r[0].strip() if r[0] else "")

# BNK_BATCH — BCM batches (which banks have payment activity)
bcm_banks = set()
bnk_cols = cols("BNK_BATCH_HEADER")
if "HBKID" in bnk_cols:
    for r in q("SELECT DISTINCT HBKID FROM BNK_BATCH_HEADER"):
        bcm_banks.add(r[0].strip() if r[0] else "")

# REGUH — payment documents (which banks received payments)
reguh_banks = set()
reguh_cols = cols("REGUH")
if "UBNKS" in reguh_cols:
    # REGUH uses UBHBK for house bank
    for r in q("SELECT DISTINCT UBHBK FROM REGUH WHERE ZBUKR='UNES'"):
        reguh_banks.add(r[0].strip() if r[0] else "")

# PAYR — payment checks
payr_banks = set()
payr_cols = cols("PAYR")
if "HBKID" in payr_cols:
    for r in q("SELECT DISTINCT HBKID FROM PAYR"):
        payr_banks.add(r[0].strip() if r[0] else "")

# ── 3. Classify each bank ──
print(f"\n{'='*70}")
print("  BANK CLASSIFICATION")
print("="*70)

categories = {
    "PAYING_HQ": [],      # Has T042I entries — runs F110
    "EBS_ACTIVE": [],     # Has T028B + FEBEP activity
    "EBS_CONFIG": [],     # Has T028B but no FEBEP activity
    "REGULAR_FO": [],     # T012K only, no EBS, no payment
    "CLOSED": [],         # SKAT text contains CLOSED
    "LEGACY": [],         # No activity, possibly obsolete
}

detail = []

for hbkid, bank in sorted(banks.items()):
    accts = bank["accounts"]
    bankl = bank["bankl"]
    country = bank["country"]
    currencies = list(set(a["waers"] for a in accts))

    # Gather all GLs
    all_gls = []
    for a in accts:
        gl = a["hkont"]
        if gl:
            all_gls.append(gl)
            # Derive clearing
            sig = gl.lstrip('0')
            if sig.startswith('10'):
                all_gls.append(('11' + sig[2:]).zfill(len(gl)))

    # Check if closed
    is_closed = any(gl in skat_closed for gl in all_gls)

    # Check configs
    has_t028b = bankl in t028b_by_bankl
    has_t042i = hbkid in t042i_by_hbkid
    has_febep = hbkid in febep_banks
    has_bcm = hbkid in bcm_banks
    has_reguh = hbkid in reguh_banks
    has_payr = hbkid in payr_banks
    has_t042a = hbkid in t042a_by_hbkid

    # SKB1 field check
    skb1_issues = []
    for gl in all_gls:
        s = skb1_map.get(gl)
        if not s:
            continue
        sig = gl.lstrip('0')
        is_bank = sig.startswith('10')
        is_clearing = sig.startswith('11')

        ka = ska1_map.get(gl, {})
        if ka.get("KTOKS") and ka["KTOKS"] != "BANK":
            skb1_issues.append(f"{gl}:KTOKS={ka['KTOKS']}")
        if "HBKID" in s and s["HBKID"] and s["HBKID"] != hbkid:
            skb1_issues.append(f"{gl}:HBKID={s['HBKID']}!={hbkid}")
        if is_clearing and "XOPVW" in s and s["XOPVW"] != "X":
            skb1_issues.append(f"{gl}:XOPVW={s.get('XOPVW','')}")

    # Classify
    if is_closed:
        cat = "CLOSED"
    elif has_t042i:
        cat = "PAYING_HQ"
    elif has_febep:
        cat = "EBS_ACTIVE"
    elif has_t028b:
        cat = "EBS_CONFIG"
    elif len(accts) > 0:
        cat = "REGULAR_FO"
    else:
        cat = "LEGACY"

    categories[cat].append(hbkid)

    # Steps needed
    steps_needed = ["1_FS00", "2_FI12"]
    if not is_closed:
        steps_needed.extend(["3_FTE_BSM", "4_OBA1", "5_CM_NAME", "6_T035D_T028B", "7_BASU", "8_T018V", "10_GS02", "13_TIBAN"])
    if has_t042i or has_reguh:
        steps_needed.extend(["9.1_T042I", "9.2_INT_TRANSFER"])
    if has_t042i:
        steps_needed.append("9.3_OBPM4")

    detail.append({
        "hbkid": hbkid, "country": country, "currencies": currencies,
        "num_accounts": len(accts), "category": cat,
        "has_t028b": has_t028b, "has_t042i": has_t042i,
        "has_febep": has_febep, "has_bcm": has_bcm,
        "has_reguh": has_reguh, "has_payr": has_payr, "has_t042a": has_t042a,
        "skb1_issues": skb1_issues,
        "steps_needed": steps_needed,
    })

# ── 4. Print results ──
for cat, bank_list in categories.items():
    print(f"\n  {cat}: {len(bank_list)} banks")
    if bank_list:
        for hbkid in bank_list:
            d = next(x for x in detail if x["hbkid"] == hbkid)
            flags = []
            if d["has_t028b"]: flags.append("EBS")
            if d["has_t042i"]: flags.append("PAY")
            if d["has_febep"]: flags.append("FEBEP")
            if d["has_bcm"]: flags.append("BCM")
            if d["has_reguh"]: flags.append("REGUH")
            if d["has_t042a"]: flags.append("DMEE")
            if d["skb1_issues"]: flags.append(f"ISSUES:{len(d['skb1_issues'])}")
            flag_str = " [" + ",".join(flags) + "]" if flags else ""
            print(f"    {hbkid:8s} {d['country']:3s} {d['num_accounts']:2d}accts {','.join(d['currencies']):<15s}{flag_str}")

# ── 5. SKB1 pattern analysis ──
print(f"\n{'='*70}")
print("  SKB1 FIELD PATTERNS (across all bank G/Ls)")
print("="*70)

# Collect all bank GLs with their SKB1 data
all_bank_gls = []
for hbkid, bank in banks.items():
    for a in bank["accounts"]:
        gl = a["hkont"]
        if gl:
            sig = gl.lstrip('0')
            is_bank = sig.startswith('10')
            clearing = ('11' + sig[2:]).zfill(len(gl)) if is_bank else None
            s_bank = skb1_map.get(gl, {})
            s_clear = skb1_map.get(clearing, {}) if clearing else {}
            all_bank_gls.append({
                "hbkid": hbkid, "gl": gl, "clearing": clearing,
                "bank_skb1": s_bank, "clear_skb1": s_clear,
            })

# FDLEV distribution
print(f"\n  FDLEV on bank accounts (10*):")
fdlev_bank = {}
for g in all_bank_gls:
    v = g["bank_skb1"].get("FDLEV", "?")
    fdlev_bank[v] = fdlev_bank.get(v, 0) + 1
for k, v in sorted(fdlev_bank.items(), key=lambda x: -x[1]):
    print(f"    {k or '(empty)':10s}: {v}")

print(f"\n  FDLEV on clearing accounts (11*):")
fdlev_clear = {}
for g in all_bank_gls:
    if g["clearing"]:
        v = g["clear_skb1"].get("FDLEV", "?")
        fdlev_clear[v] = fdlev_clear.get(v, 0) + 1
for k, v in sorted(fdlev_clear.items(), key=lambda x: -x[1]):
    print(f"    {k or '(empty)':10s}: {v}")

# XOPVW on clearing
print(f"\n  XOPVW on clearing accounts (11*) — should be X:")
xopvw = {}
for g in all_bank_gls:
    if g["clearing"]:
        v = g["clear_skb1"].get("XOPVW", "?")
        xopvw[v] = xopvw.get(v, 0) + 1
for k, v in sorted(xopvw.items(), key=lambda x: -x[1]):
    pct = v / sum(xopvw.values()) * 100
    print(f"    {k or '(empty)':10s}: {v} ({pct:.0f}%)")

# XINTB
print(f"\n  XINTB (Post Auto Only) on bank accounts:")
xintb = {}
for g in all_bank_gls:
    v = g["bank_skb1"].get("XINTB", "?")
    xintb[v] = xintb.get(v, 0) + 1
for k, v in sorted(xintb.items(), key=lambda x: -x[1]):
    print(f"    {k or '(empty)':10s}: {v}")

# KTOKS
print(f"\n  KTOKS (Account Group) on all bank-related G/Ls:")
ktoks = {}
for g in all_bank_gls:
    gl = g["gl"]
    ka = ska1_map.get(gl, {})
    v = ka.get("KTOKS", "?")
    ktoks[v] = ktoks.get(v, 0) + 1
for k, v in sorted(ktoks.items(), key=lambda x: -x[1]):
    print(f"    {k or '(empty)':10s}: {v}")

# Wrong HBKID
print(f"\n  HBKID mismatches (SKB1.HBKID != T012K.HBKID):")
mismatches = []
for d in detail:
    if d["skb1_issues"]:
        hbkid_issues = [i for i in d["skb1_issues"] if "HBKID" in i]
        if hbkid_issues:
            mismatches.append((d["hbkid"], hbkid_issues))
print(f"    {len(mismatches)} banks with HBKID mismatches")
for hbkid, issues in mismatches[:20]:
    print(f"    {hbkid}: {issues}")

# ── 6. Summary ──
print(f"\n{'='*70}")
print("  CLASSIFICATION SUMMARY")
print("="*70)
print(f"  Total banks: {len(banks)}")
for cat, bank_list in categories.items():
    print(f"  {cat:15s}: {len(bank_list):4d}")

print(f"\n  Steps required by category:")
print(f"  {'Category':15s} 1  2  3  4  5  6  7  8  9.1 9.2 9.3 10 13")
for cat in ["PAYING_HQ", "EBS_ACTIVE", "EBS_CONFIG", "REGULAR_FO", "CLOSED"]:
    steps = {
        "PAYING_HQ":  "X  X  X  X  X  X  X  X  X   X   X   X  X",
        "EBS_ACTIVE": "X  X  X  X  X  X  X  X  -   -   -   X  X",
        "EBS_CONFIG": "X  X  X  X  X  X  X  X  -   -   -   X  X",
        "REGULAR_FO": "X  X  X  X  X  X  X  X  -   -   -   X  X",
        "CLOSED":     "-  M  R  R  R  R  -  R  R   -   -   R  -",
    }
    print(f"  {cat:15s} {steps[cat]}")
print(f"  Legend: X=required, -=not needed, M=modify, R=remove")

# Save detail
out = os.path.join(os.path.dirname(__file__), "house_bank_classification.json")
with open(out, "w") as f:
    json.dump(detail, f, indent=2, default=str)
print(f"\nDetail saved to: {out}")

conn.close()
