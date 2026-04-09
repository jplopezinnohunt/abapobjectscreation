"""
t030h_deep_analysis.py
=======================
Deep analysis of ALL 891 T030H entries + 155 partial entries.
Cross-reference with T012K, SKAT (closed), FEBEP (activity), SKB1.
Discover patterns: which are active? which affect revaluation?
"""
import sqlite3, os, sys, io
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DB = os.path.join(os.path.dirname(__file__), "..", "sap_data_extraction", "sqlite", "p01_gold_master_data.db")
conn = sqlite3.connect(DB)

def q(sql):
    try:
        return conn.execute(sql).fetchall()
    except Exception as e:
        return []

# ── Load T030H ──
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

# ── Load SKAT for closed detection + names ──
skat = {}
skat_closed = set()
for r in q("SELECT SAKNR, TXT50 FROM P01_SKAT WHERE KTOPL='UNES' AND SPRAS='E'"):
    saknr = r[0].strip()
    txt = r[1].strip() if r[1] else ""
    skat[saknr] = txt
    if "CLOSED" in txt.upper():
        skat_closed.add(saknr)

# ── Load T012K for house bank mapping ──
gl_to_bank = {}  # GL -> {hbkid, hktid, waers}
for r in q("SELECT HBKID, HKTID, WAERS, HKONT FROM T012K WHERE BUKRS='UNES'"):
    hbkid = r[0].strip()
    hktid = r[1].strip()
    waers = r[2].strip()
    hkont = r[3].strip()
    gl_to_bank[hkont] = {"hbkid": hbkid, "hktid": hktid, "waers": waers}
    # Also map clearing GL
    sig = hkont.lstrip('0')
    if sig.startswith('10'):
        clearing = ('11' + sig[2:]).zfill(len(hkont))
        gl_to_bank[clearing] = {"hbkid": hbkid, "hktid": hktid, "waers": waers, "is_clearing": True}

# ── Load SKB1 for HBKID/currency ──
skb1 = {}
for r in q("SELECT SAKNR, HBKID, WAERS, FDLEV FROM P01_SKB1 WHERE BUKRS='UNES'"):
    skb1[r[0].strip()] = {
        "HBKID": r[1].strip() if r[1] else "",
        "WAERS": r[2].strip() if r[2] else "",
        "FDLEV": r[3].strip() if r[3] else "",
    }

# ── Load FEBEP for activity (which GLs have bank statement items) ──
febep_gls = set()
for r in q("SELECT DISTINCT HKONT FROM FEBEP_2024_2026"):
    febep_gls.add(r[0].strip() if r[0] else "")

# Also check by KUKEY prefix for bank activity
febep_banks = set()
for r in q("SELECT DISTINCT HBKID FROM FEBEP_2024_2026"):
    febep_banks.add(r[0].strip() if r[0] else "")

# ── BSIS/BSAS for posting activity on these GLs ──
# Check if the GL has had postings in 2024-2026
active_gls = set()
for table in ["bsis", "bsas"]:
    for r in q(f"SELECT DISTINCT HKONT FROM {table} WHERE BUKRS='UNES' AND GJAHR >= '2024'"):
        active_gls.add(r[0].strip() if r[0] else "")

# ── Classify every T030H entry ──
print("="*70)
print("  T030H DEEP ANALYSIS — 891 entries")
print("="*70)

complete = []
partial = []

for hkont, entry in sorted(t030h.items()):
    is_complete = all(
        entry[f] and entry[f] != "0000000000"
        for f in ["LKORR","LSREA","LHREA","LSBEW","LHBEW"]
    )
    missing_fields = [f for f in ["LKORR","LSBEW","LHBEW"]
                      if not entry[f] or entry[f] == "0000000000"]

    # Determine GL type
    sig = hkont.lstrip('0')
    if sig.startswith('10'):
        gl_type = "bank_10*"
    elif sig.startswith('11'):
        gl_type = "clearing_11*"
    elif sig.startswith('12'):
        gl_type = "sub_12*"
    elif sig.startswith('13'):
        gl_type = "sub_13*"
    elif sig.startswith('92') or sig.startswith('91'):
        gl_type = "special_9*"
    elif sig.startswith('20'):
        gl_type = "invest_20*"
    else:
        gl_type = f"other_{sig[:2]}*"

    # House bank from T012K
    bank_info = gl_to_bank.get(hkont, {})
    hbkid = bank_info.get("hbkid", "")

    # From SKB1
    skb1_info = skb1.get(hkont, {})
    skb1_hbkid = skb1_info.get("HBKID", "")
    skb1_waers = skb1_info.get("WAERS", "")

    # If not in T012K, try SKB1
    if not hbkid:
        hbkid = skb1_hbkid

    # Is closed?
    is_closed = hkont in skat_closed
    # Also check if the bank GL (10*) is closed
    if gl_type == "clearing_11*":
        bank_gl = ('10' + sig[2:]).zfill(len(hkont))
        if bank_gl in skat_closed:
            is_closed = True

    # Activity
    has_febep = hkont in febep_gls
    has_postings = hkont in active_gls
    bank_has_febep = hbkid in febep_banks if hbkid else False

    # SKAT name
    name = skat.get(hkont, "")

    record = {
        "hkont": hkont, "gl_type": gl_type, "hbkid": hbkid,
        "waers": skb1_waers, "name": name,
        "is_closed": is_closed, "is_complete": is_complete,
        "missing": missing_fields,
        "has_febep": has_febep, "has_postings": has_postings,
        "bank_has_febep": bank_has_febep,
        "fields": entry,
    }

    if is_complete:
        complete.append(record)
    else:
        partial.append(record)

print(f"\n  Complete entries: {len(complete)}")
print(f"  Partial entries: {len(partial)}")

# ── Analyze partial entries ──
print(f"\n{'='*70}")
print("  PARTIAL T030H ENTRIES (missing LKORR/LSBEW/LHBEW)")
print("="*70)

# Group by GL type
by_type = {}
for r in partial:
    t = r["gl_type"]
    if t not in by_type:
        by_type[t] = []
    by_type[t].append(r)

print(f"\n  By G/L type:")
for t in sorted(by_type.keys()):
    entries = by_type[t]
    closed = sum(1 for e in entries if e["is_closed"])
    active_post = sum(1 for e in entries if e["has_postings"])
    active_febep = sum(1 for e in entries if e["has_febep"])
    print(f"    {t:15s}: {len(entries):3d} total, {closed:3d} closed, {active_post:3d} with postings 2024+, {active_febep:3d} with FEBEP")

# ── Critical: Partial entries on ACTIVE accounts ──
print(f"\n{'='*70}")
print("  CRITICAL: Partial T030H on ACTIVE (non-closed) accounts with postings")
print("="*70)

critical = [r for r in partial if not r["is_closed"] and r["has_postings"]]
risk_revaluation = [r for r in partial if not r["is_closed"] and r["has_postings"] and r["waers"] != "USD"]

print(f"\n  Active + has postings: {len(critical)}")
print(f"  Active + has postings + non-USD (REVALUATION RISK): {len(risk_revaluation)}")

if critical:
    print(f"\n  {'GL':12s} {'Type':12s} {'HBKID':8s} {'Cur':5s} {'FEBEP':6s} {'Missing':20s} {'Name'}")
    print(f"  {'-'*12} {'-'*12} {'-'*8} {'-'*5} {'-'*6} {'-'*20} {'-'*40}")
    for r in sorted(critical, key=lambda x: (x["waers"]=="USD", x["hkont"])):
        febep = "YES" if r["has_febep"] else "no"
        risk = " ** REVAL RISK" if r["waers"] != "USD" else ""
        print(f"  {r['hkont']:12s} {r['gl_type']:12s} {r['hbkid']:8s} {r['waers']:5s} {febep:6s} {','.join(r['missing']):20s} {r['name'][:40]}{risk}")

# ── Closed partial — just count ──
closed_partial = [r for r in partial if r["is_closed"]]
print(f"\n  Closed banks with partial T030H: {len(closed_partial)} (no action needed)")

# ── Inactive partial (no postings since 2024) ──
inactive_partial = [r for r in partial if not r["is_closed"] and not r["has_postings"]]
print(f"  Non-closed but no postings since 2024: {len(inactive_partial)}")
if inactive_partial:
    # Group by GL type
    by_t = {}
    for r in inactive_partial:
        t = r["gl_type"]
        by_t[t] = by_t.get(t, 0) + 1
    for t, cnt in sorted(by_t.items(), key=lambda x: -x[1]):
        print(f"    {t}: {cnt}")

# ── Pattern analysis on COMPLETE entries ──
print(f"\n{'='*70}")
print("  COMPLETE T030H PATTERNS")
print("="*70)

# LSREA/LHREA values
loss_gain = {}
for r in complete:
    key = (r["fields"]["LSREA"], r["fields"]["LHREA"])
    loss_gain[key] = loss_gain.get(key, 0) + 1

print(f"\n  Loss/Gain account pairs:")
for (loss, gain), cnt in sorted(loss_gain.items(), key=lambda x: -x[1]):
    print(f"    Loss={loss} Gain={gain}: {cnt} entries")

# LKORR pattern (should be the account itself)
lkorr_self = sum(1 for r in complete if r["fields"]["LKORR"] == r["hkont"])
lkorr_other = sum(1 for r in complete if r["fields"]["LKORR"] != r["hkont"])
print(f"\n  LKORR (Bal.sheet adj.):")
print(f"    LKORR = account itself: {lkorr_self}")
print(f"    LKORR = different account: {lkorr_other}")
if lkorr_other:
    print(f"    Examples of LKORR != self:")
    others = [r for r in complete if r["fields"]["LKORR"] != r["hkont"]][:10]
    for r in others:
        print(f"      {r['hkont']}: LKORR={r['fields']['LKORR']} ({r['name'][:30]})")

# ── By GL type (complete) ──
print(f"\n  Complete entries by GL type:")
comp_by_type = {}
for r in complete:
    t = r["gl_type"]
    comp_by_type[t] = comp_by_type.get(t, 0) + 1
for t, cnt in sorted(comp_by_type.items(), key=lambda x: -x[1]):
    print(f"    {t}: {cnt}")

# ── Active banks: which have complete OBA1 for ALL their clearing accounts? ──
print(f"\n{'='*70}")
print("  PER-BANK OBA1 COMPLETENESS (active banks only)")
print("="*70)

# Get active bank list from T012K
banks = {}
for r in q("SELECT HBKID, HKTID, WAERS, HKONT FROM T012K WHERE BUKRS='UNES'"):
    hbkid = r[0].strip()
    if hbkid not in banks:
        banks[hbkid] = []
    banks[hbkid].append({"hktid": r[1].strip(), "waers": r[2].strip(), "hkont": r[3].strip()})

bank_oba1 = {}
for hbkid, accts in sorted(banks.items()):
    # Skip closed banks
    all_gls = [a["hkont"] for a in accts]
    any_closed = any(gl in skat_closed for gl in all_gls)
    for a in accts:
        gl = a["hkont"]
        sig = gl.lstrip('0')
        if sig.startswith('10'):
            clr = ('11' + sig[2:]).zfill(len(gl))
            if clr in skat_closed:
                any_closed = True

    if any_closed:
        continue

    clearing_status = []
    for a in accts:
        gl = a["hkont"]
        sig = gl.lstrip('0')
        if sig.startswith('10'):
            clr = ('11' + sig[2:]).zfill(len(gl))
            entry = t030h.get(clr)
            if entry:
                is_comp = all(entry[f] and entry[f] != "0000000000"
                              for f in ["LKORR","LSREA","LHREA","LSBEW","LHBEW"])
                clearing_status.append({"gl": clr, "waers": a["waers"],
                                        "exists": True, "complete": is_comp})
            else:
                clearing_status.append({"gl": clr, "waers": a["waers"],
                                        "exists": False, "complete": False})

    if clearing_status:
        all_ok = all(s["complete"] or (not s["exists"] and s["waers"] == "USD")
                     for s in clearing_status)
        bank_oba1[hbkid] = {"status": clearing_status, "all_ok": all_ok}

banks_ok = sum(1 for v in bank_oba1.values() if v["all_ok"])
banks_issue = sum(1 for v in bank_oba1.values() if not v["all_ok"])

print(f"\n  Active banks with OBA1 checked: {len(bank_oba1)}")
print(f"  All clearing GLs OK: {banks_ok}")
print(f"  Issues: {banks_issue}")

if banks_issue:
    print(f"\n  Banks with OBA1 issues:")
    for hbkid, data in sorted(bank_oba1.items()):
        if not data["all_ok"]:
            issues = [s for s in data["status"] if not s["complete"] and not (not s["exists"] and s["waers"] == "USD")]
            for s in issues:
                state = "PARTIAL" if s["exists"] else "MISSING"
                print(f"    {hbkid:8s} {s['gl']} ({s['waers']}): {state}")

# ── Final summary ──
print(f"\n{'='*70}")
print("  FINAL SUMMARY")
print("="*70)
print(f"  T030H total entries: {len(t030h)}")
print(f"  Complete (5/5 fields): {len(complete)} ({len(complete)/len(t030h)*100:.0f}%)")
print(f"  Partial (missing fields): {len(partial)} ({len(partial)/len(t030h)*100:.0f}%)")
print(f"    - On closed accounts: {len(closed_partial)}")
print(f"    - On inactive (no postings 2024+): {len(inactive_partial)}")
print(f"    - On ACTIVE with postings: {len(critical)}")
print(f"      - Non-USD (REVALUATION RISK): {len(risk_revaluation)}")
print(f"      - USD only (lower risk): {len(critical) - len(risk_revaluation)}")

conn.close()
