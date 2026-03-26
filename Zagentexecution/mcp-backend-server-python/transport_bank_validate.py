"""
transport_bank_validate.py — Validate Bank+Payment config for copied company code STEM
Checks: GL reconciliation, FBZP chain completeness, source identification, country match
Output: JSON with pass/fail per check
"""
import os, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

def env(*keys, default=""):
    for k in keys:
        v = os.getenv(k)
        if v: return v
    return default

def rfc_connect():
    import pyrfc
    params = {
        "ashost": env("SAP_ASHOST", default="172.16.4.66"),
        "sysnr": env("SAP_SYSNR", default="00"),
        "client": env("SAP_CLIENT", default="350"),
    }
    snc_mode = env("SAP_SNC_MODE")
    snc_pn = env("SAP_SNC_PARTNERNAME")
    if snc_mode and snc_pn:
        params["snc_mode"] = snc_mode
        params["snc_partnername"] = snc_pn
        params["snc_qop"] = env("SAP_SNC_QOP", default="9")
    else:
        params["user"] = env("SAP_USER")
        params["passwd"] = env("SAP_PASSWORD")
    print(f"[RFC] Connecting to {params['ashost']}...")
    return pyrfc.Connection(**params)

def read_table(conn, table, fields, where, max_rows=5000):
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE=table,
            FIELDS=[{"FIELDNAME": f} for f in fields],
            OPTIONS=[{"TEXT": t} for t in where],
            ROWCOUNT=max_rows, ROWSKIPS=0, DELIMITER="|")
        rows = []
        for row in r.get("DATA", []):
            parts = row.get("WA", "").split("|")
            if len(parts) == len(fields):
                rows.append({fields[i]: parts[i].strip() for i in range(len(fields))})
        return rows
    except Exception as e:
        print(f"  [WARN] Failed to read {table}: {e}")
        return []

conn = rfc_connect()
results = {}

# ─── CHECK 1: T012K GL Reconciliation accounts exist in SKB1 ───
print("\n[CHECK 1] GL Reconciliation — T012K.HKONT exists in SKB1 for STEM")
t012k = read_table(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "HKONT", "WAESSION"], ["BUKRS = 'STEM'"])
# Field WAESSION might not exist, retry without it
if not t012k:
    t012k = read_table(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "BANKN", "HKONT"], ["BUKRS = 'STEM'"])

skb1_accounts = set()
skb1_rows = read_table(conn, "SKB1", ["BUKRS", "SAKNR"], ["BUKRS = 'STEM'"], max_rows=1000)
for r in skb1_rows:
    skb1_accounts.add(r["SAKNR"].lstrip("0"))

gl_check = []
for r in t012k:
    hkont = r.get("HKONT", "").lstrip("0")
    exists = hkont in skb1_accounts or r.get("HKONT", "") in [s["SAKNR"] for s in skb1_rows]
    gl_check.append({
        "bank": r.get("HBKID", ""),
        "account_id": r.get("HKTID", ""),
        "bank_account_nr": r.get("BANKN", ""),
        "gl_recon_account": r.get("HKONT", ""),
        "exists_in_skb1": exists
    })
    status = "PASS" if exists else "FAIL"
    print(f"  {r.get('HKTID',''):6} HKONT={r.get('HKONT',''):10} in SKB1? {status}")

all_gl_ok = all(g["exists_in_skb1"] for g in gl_check)
results["check1_gl_reconciliation"] = {
    "status": "PASS" if all_gl_ok else "FAIL",
    "detail": gl_check,
    "skb1_count": len(skb1_accounts)
}

# ─── CHECK 2: T042I Ranking Order exists ───
print("\n[CHECK 2] Ranking Order — T042I for STEM")
t042i = read_table(conn, "T042I", ["ZBUKR", "HBKID", "HKTID", "ZLSCH"], ["ZBUKR = 'STEM'"])
has_ranking = len(t042i) > 0
results["check2_ranking_order"] = {
    "status": "PASS" if has_ranking else "FAIL",
    "rows": len(t042i),
    "detail": t042i[:10]
}
print(f"  T042I rows for STEM: {len(t042i)} → {'PASS' if has_ranking else 'FAIL — F110 cannot select bank'}")
for r in t042i:
    print(f"    Bank={r.get('HBKID','')}/{r.get('HKTID','')} Method={r.get('ZLSCH','')}")

# ─── CHECK 3: T042C Payment method per co code per country ───
print("\n[CHECK 3] Payment Methods/CoCode/Country — T042C for STEM")
t042c = read_table(conn, "T042C", ["BUKRS", "LAND1", "ZLSCH", "HBKID", "HKTID"], ["BUKRS = 'STEM'"])
has_t042c = len(t042c) > 0
results["check3_payment_method_cocode_country"] = {
    "status": "PASS" if has_t042c else "FAIL",
    "rows": len(t042c),
    "detail": t042c[:10]
}
print(f"  T042C rows for STEM: {len(t042c)} → {'PASS' if has_t042c else 'FAIL — FBZP chain incomplete'}")
for r in t042c:
    print(f"    Country={r.get('LAND1','')} Method={r.get('ZLSCH','')} Bank={r.get('HBKID','')}/{r.get('HKTID','')}")

# ─── CHECK 4: Identify source company code ───
print("\n[CHECK 4] Source Company Code identification — other BUKRs with CBE01")
all_cbe01 = read_table(conn, "T012", ["BUKRS", "HBKID", "BANKS", "BANKL", "SWIFT"], ["HBKID = 'CBE01'"])
other_codes = [r for r in all_cbe01 if r["BUKRS"] != "STEM"]
results["check4_source_identification"] = {
    "status": "INFO",
    "stem_bank": [r for r in all_cbe01 if r["BUKRS"] == "STEM"],
    "other_cocodes_same_bank": other_codes
}
print(f"  Company codes with house bank CBE01:")
for r in all_cbe01:
    marker = " ← THIS" if r["BUKRS"] == "STEM" else " ← POTENTIAL SOURCE"
    print(f"    {r['BUKRS']:6} SWIFT={r.get('SWIFT','')} BANKL={r.get('BANKL','')}{marker}")

# Compare GL reconciliation accounts between STEM and potential sources
if other_codes:
    print("\n  Comparing GL reconciliation accounts (T012K):")
    for src in other_codes[:3]:  # top 3
        src_t012k = read_table(conn, "T012K", ["BUKRS", "HBKID", "HKTID", "HKONT"], [f"BUKRS = '{src['BUKRS']}'", "AND HBKID = 'CBE01'"])
        stem_hkonts = {g["gl_recon_account"] for g in gl_check}
        src_hkonts = {r.get("HKONT", "") for r in src_t012k}
        overlap = stem_hkonts & src_hkonts
        match_pct = len(overlap) / max(len(stem_hkonts), 1) * 100
        print(f"    {src['BUKRS']}: {len(src_t012k)} accounts, GL overlap with STEM = {match_pct:.0f}% {'← LIKELY SOURCE' if match_pct > 80 else ''}")
        results["check4_source_identification"][f"gl_comparison_{src['BUKRS']}"] = {
            "source_accounts": src_t012k,
            "overlap_pct": match_pct
        }

# ─── CHECK 5: Country match ───
print("\n[CHECK 5] Country match — T001.LAND1 for STEM vs payment methods")
t001_stem = read_table(conn, "T001", ["BUKRS", "BUTXT", "LAND1", "WAERS"], ["BUKRS = 'STEM'"])
t042e = read_table(conn, "T042E", ["BUKRS", "LAND1", "ZLSCH"], ["BUKRS = 'STEM'"])

stem_country = t001_stem[0].get("LAND1", "") if t001_stem else "UNKNOWN"
stem_currency = t001_stem[0].get("WAERS", "") if t001_stem else "UNKNOWN"
stem_name = t001_stem[0].get("BUTXT", "") if t001_stem else "UNKNOWN"
t042e_countries = set(r.get("LAND1", "") for r in t042e)

country_match = stem_country in t042e_countries if t042e_countries else False
results["check5_country_match"] = {
    "status": "PASS" if country_match else "FAIL",
    "stem_country": stem_country,
    "stem_currency": stem_currency,
    "stem_name": stem_name,
    "payment_method_countries": list(t042e_countries),
    "t042e_detail": t042e
}
print(f"  STEM: {stem_name}, Country={stem_country}, Currency={stem_currency}")
print(f"  T042E payment methods defined for countries: {t042e_countries}")
print(f"  Country in T042E? {'PASS' if country_match else 'FAIL — payment methods not defined for STEM country'}")

# ─── CHECK 6: Bank account numbers ───
print("\n[CHECK 6] Bank Account Numbers — real or dummy?")
for r in t012k:
    bankn = r.get("BANKN", "")
    is_dummy = bankn in ("", "0", "0000000000", "XXXXXXXXXX", "1234567890")
    status = "WARN — looks like placeholder" if is_dummy else "OK"
    print(f"  {r.get('HKTID',''):6} BANKN={bankn:20} {status}")
    r["is_dummy"] = is_dummy

results["check6_bank_accounts"] = {
    "status": "PASS" if not any(r.get("is_dummy") for r in t012k) else "WARN",
    "detail": [{k: v for k, v in r.items() if k != "is_dummy"} for r in t012k]
}

# ─── SUMMARY ───
print("\n" + "="*60)
print("VALIDATION SUMMARY")
print("="*60)
total_pass = sum(1 for c in results.values() if isinstance(c, dict) and c.get("status") == "PASS")
total_fail = sum(1 for c in results.values() if isinstance(c, dict) and c.get("status") == "FAIL")
total_warn = sum(1 for c in results.values() if isinstance(c, dict) and c.get("status") == "WARN")

for key, val in results.items():
    if isinstance(val, dict) and "status" in val:
        icon = {"PASS": "✓", "FAIL": "✗", "WARN": "⚠", "INFO": "ℹ"}.get(val["status"], "?")
        print(f"  {icon} {key}: {val['status']}")

print(f"\nTotal: {total_pass} PASS, {total_fail} FAIL, {total_warn} WARN")

# Save results
out_path = os.path.join(os.path.dirname(__file__), "transport_bank_validation.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\nSaved to {out_path}")
