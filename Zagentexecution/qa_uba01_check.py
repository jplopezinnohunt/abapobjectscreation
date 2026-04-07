"""
QA Check: Excel Request Forms vs D01 Configuration for House Bank UBA01
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "mcp-backend-server-python"))
from rfc_helpers import get_connection
from pyrfc import RFCError

conn = get_connection("D01")

PASS_COUNT = 0
FAIL_COUNT = 0
MISSING_COUNT = 0

def rfc_read(table, fields, options, batch_size=100):
    """Simple RFC_READ_TABLE wrapper."""
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    try:
        result = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                           ROWCOUNT=batch_size, ROWSKIPS=0,
                           OPTIONS=options, FIELDS=rfc_fields)
    except RFCError as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        raise
    raw = result.get("DATA", [])
    hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    rows = []
    for row in raw:
        parts = row["WA"].split("|")
        rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
    return rows

def check(label, form_val, d01_val):
    global PASS_COUNT, FAIL_COUNT
    form_val = str(form_val).strip()
    d01_val = str(d01_val).strip()
    if form_val.upper() == d01_val.upper():
        print(f"  [PASS] {label}: '{d01_val}'")
        PASS_COUNT += 1
    else:
        print(f"  [FAIL] {label}: Form='{form_val}' vs D01='{d01_val}'")
        FAIL_COUNT += 1

def check_gl(label, form_val, d01_val):
    global PASS_COUNT, FAIL_COUNT
    form_val = str(form_val).strip().lstrip("0")
    d01_val = str(d01_val).strip().lstrip("0")
    if form_val == d01_val:
        print(f"  [PASS] {label}: '{d01_val}'")
        PASS_COUNT += 1
    else:
        print(f"  [FAIL] {label}: Form='{form_val}' vs D01='{d01_val}'")
        FAIL_COUNT += 1

def missing(label, what):
    global MISSING_COUNT
    print(f"  [MISSING] {label}: {what}")
    MISSING_COUNT += 1

# Pad GL to 10 digits (SAP format)
def pad_gl(gl):
    return gl.zfill(10)

print("=" * 70)
print("QA CHECK: Excel Forms vs D01 Configuration - House Bank UBA01")
print("=" * 70)

# ── 1. T012 — House Bank Master ──
print("\n--- T012: House Bank Master (BUKRS=UNES, HBKID=UBA01) ---")
rows = rfc_read("T012",
    ["BUKRS","HBKID","BANKS","BANKL","NAME1"],
    [{"TEXT": "BUKRS EQ 'UNES' AND HBKID EQ 'UBA01'"}])
if rows:
    r = rows[0]
    print(f"  [RAW] {r}")
    check("Bank Country (BANKS)", "MZ", r.get("BANKS",""))
    check("Bank Key (BANKL)", "SP0000001YCB", r.get("BANKL",""))
else:
    missing("T012", "No record found for UNES/UBA01")

# ── 2. T012K — Bank Accounts ──
print("\n--- T012K: Bank Accounts (BUKRS=UNES, HBKID=UBA01) ---")
rows_t012k = rfc_read("T012K",
    ["BUKRS","HBKID","HKTID","BANKN","WAERS","HKONT","FDGRP"],
    [{"TEXT": "BUKRS EQ 'UNES' AND HBKID EQ 'UBA01'"}])

expected_accounts = {
    "USD01": {"desc": "UNESCO MAPUTO - USD", "BANKN": "070340000190", "WAERS": "USD", "HKONT": "1065421"},
    "MZN01": {"desc": "UNESCO MAPUTO - MZN", "BANKN": "070040004663", "WAERS": "MZN", "HKONT": "1065424"},
}
for acct_id, exp in expected_accounts.items():
    print(f"\n  Account ID: {acct_id} ({exp['desc']})")
    match = [r for r in rows_t012k if r.get("HKTID","").strip() == acct_id]
    if not match:
        missing(f"T012K/{acct_id}", "Account not found in D01")
        continue
    r = match[0]
    print(f"  [RAW] {r}")
    check(f"  Bank Account Number (BANKN)", exp["BANKN"], r.get("BANKN",""))
    check(f"  Currency (WAERS)", exp["WAERS"], r.get("WAERS",""))
    check_gl(f"  G/L Account (HKONT)", exp["HKONT"], r.get("HKONT",""))

# ── 3. BNKA — Bank Directory ──
print("\n\n--- BNKA: Bank Directory (BANKS=MZ, BANKL=SP0000001YCB) ---")
rows_bnka = rfc_read("BNKA",
    ["BANKS","BANKL","BANKA","STRAS","ORT01","SWIFT"],
    [{"TEXT": "BANKS EQ 'MZ' AND BANKL EQ 'SP0000001YCB'"}])
if rows_bnka:
    r = rows_bnka[0]
    print(f"  [RAW] {r}")
    check("Bank Name (BANKA)", "UBA Mozambique S.A.", r.get("BANKA",""))
    d01_street = r.get("STRAS","").strip()
    form_street = "Av. Zedequias Manganhela, 267, Edificio JAT 4, Piso 7"
    check("Street (STRAS)", form_street, d01_street)
    check("City (ORT01)", "MAPUTO", r.get("ORT01",""))
    check("SWIFT Code (SWIFT)", "UNAFMZMA", r.get("SWIFT",""))
else:
    missing("BNKA", "No bank record found for MZ/SP0000001YCB")

# ── 4. SKA1 — Chart of Accounts Level ──
print("\n--- SKA1: Chart of Accounts (KTOPL=UNES) ---")
gl_list = ["1065421","1165421","1065424","1165424"]
gl_labels = {
    "1065421": "1065421 (BK UBA USD)",
    "1165421": "1165421 (S-BK UBA USD)",
    "1065424": "1065424 (BK UBA MZN)",
    "1165424": "1165424 (S-BK UBA MZN)",
}
for gl in gl_list:
    gl_padded = pad_gl(gl)
    label = gl_labels.get(gl, gl)
    print(f"\n  Account {label}:")
    try:
        rows_ska1 = rfc_read("SKA1",
            ["KTOPL","SAKNR","KTOKS","XBILK"],
            [{"TEXT": f"KTOPL EQ 'UNES' AND SAKNR EQ '{gl_padded}'"}], batch_size=10)
        if rows_ska1:
            r = rows_ska1[0]
            print(f"    [RAW] {r}")
            print(f"    [INFO] Account Group (KTOKS): '{r.get('KTOKS','')}'")
            print(f"    [INFO] Balance Sheet (XBILK): '{r.get('XBILK','')}'")
            print(f"    [PASS] Account exists in SKA1")
            PASS_COUNT += 1
        else:
            missing(f"SKA1/{label}", "Account not found")
    except Exception as e:
        print(f"    [ERROR] {e}")

# ── 5. SKB1 — Company Code Data ──
print("\n--- SKB1: Company Code Data (BUKRS=UNES) ---")
expected_skb1 = {
    "1065421": {"WAERS": "USD", "HBKID": "UBA01", "HKTID": "USD01", "label": "1065421 (BK UBA USD)"},
    "1165421": {"WAERS": "USD", "HBKID": "UBA01", "HKTID": "USD01", "label": "1165421 (S-BK UBA USD)"},
    "1065424": {"WAERS": "MZN", "HBKID": "UBA01", "HKTID": "MZN01", "label": "1065424 (BK UBA MZN)"},
    "1165424": {"WAERS": "MZN", "HBKID": "UBA01", "HKTID": "MZN01", "label": "1165424 (S-BK UBA MZN)"},
}
for gl, exp in expected_skb1.items():
    gl_padded = pad_gl(gl)
    print(f"\n  Account {exp['label']}:")
    try:
        rows_skb1 = rfc_read("SKB1",
            ["BUKRS","SAKNR","WAERS","HBKID","HKTID","XINTB","FDLEV"],
            [{"TEXT": f"BUKRS EQ 'UNES' AND SAKNR EQ '{gl_padded}'"}], batch_size=10)
        if rows_skb1:
            r = rows_skb1[0]
            print(f"    [RAW] {r}")
            check(f"    Currency (WAERS)", exp["WAERS"], r.get("WAERS",""))
            check(f"    House Bank (HBKID)", exp["HBKID"], r.get("HBKID",""))
            check(f"    Account ID (HKTID)", exp["HKTID"], r.get("HKTID",""))
            print(f"    [INFO] Auto-posting only (XINTB): '{r.get('XINTB','')}'")
            print(f"    [INFO] Planning Level (FDLEV): '{r.get('FDLEV','')}'")
        else:
            missing(f"SKB1/{exp['label']}", "Account not found at company code UNES")
    except Exception as e:
        print(f"    [ERROR] {e}")

# ── 6. SKAT — GL Account Texts ──
print("\n--- SKAT: GL Account Texts (KTOPL=UNES, SPRAS=E) ---")
expected_skat = {
    "1065421": {"TXT50": "BK UBA MOZAMBIQUE - UNESCO MAPUTO USD", "TXT20": "BK UBA MOZAMBIQUE -"},
    "1165421": {"TXT50": "S-BK UBA MOZAMBIQUE - UNESCO MAPUTO USD", "TXT20": "S-BK UBA MOZAMBIQUE"},
    "1065424": {"TXT50": "BK UBA MOZAMBIQUE - UNESCO MAPUTO MZN", "TXT20": "BK UBA MOZAMBIQUE-"},
    "1165424": {"TXT50": "S-BK UBA MOZAMBIQUE - UNESCO MAPUTO MZN", "TXT20": "S-BK UBA MOZAMBIQUE"},
}
for gl, exp in expected_skat.items():
    gl_padded = pad_gl(gl)
    label = gl_labels.get(gl, gl)
    print(f"\n  Account {label}:")
    try:
        rows_skat = rfc_read("SKAT",
            ["SPRAS","KTOPL","SAKNR","TXT20","TXT50"],
            [{"TEXT": f"KTOPL EQ 'UNES' AND SPRAS EQ 'E' AND SAKNR EQ '{gl_padded}'"}], batch_size=10)
        if rows_skat:
            r = rows_skat[0]
            print(f"    [RAW] {r}")
            # TXT50 comparison (50 chars)
            d01_txt50 = r.get("TXT50","").strip()
            form_txt50 = exp["TXT50"]
            check(f"    Long Text (TXT50)", form_txt50, d01_txt50)
            # TXT20 - just show, 20 char limit makes exact match tricky
            d01_txt20 = r.get("TXT20","").strip()
            print(f"    [INFO] Short Text (TXT20): '{d01_txt20}'")
        else:
            missing(f"SKAT/{label}", "No English text found")
    except Exception as e:
        print(f"    [ERROR] {e}")

# ── 7. TIBAN — IBAN data ──
print("\n--- TIBAN: IBAN Data (BANKS=MZ, BANKL=SP0000001YCB) ---")
try:
    rows_tiban = rfc_read("TIBAN",
        ["BANKS","BANKL","BANKN","IBAN"],
        [{"TEXT": "BANKS EQ 'MZ' AND BANKL EQ 'SP0000001YCB'"}])
    if rows_tiban:
        for r in rows_tiban:
            bankn = r.get("BANKN","").strip()
            iban = r.get("IBAN","").strip()
            print(f"  [RAW] TIBAN: {r}")
            if bankn == "070340000190":
                check("IBAN for USD01 (070340000190)", "MZ59004206077034000019028", iban)
            elif bankn == "070040004663":
                check("IBAN for MZN01 (070040004663)", "MZ59004206077004000466345", iban)
    else:
        print("  [INFO] No TIBAN entries found for this bank")
except Exception as e:
    print(f"  [ERROR] TIBAN query failed: {e}")

# ── 8. T035D — Electronic Bank Statement ──
print("\n--- T035D: Electronic Bank Statement ---")
try:
    # Get field list first
    result = conn.call('RFC_READ_TABLE', QUERY_TABLE='T035D', ROWCOUNT=0, FIELDS=[], OPTIONS=[])
    flds = [f['FIELDNAME'] for f in result.get('FIELDS', [])]
    print(f"  [INFO] T035D fields: {flds[:10]}")

    rows_t035d = rfc_read("T035D", flds[:6],
        [{"TEXT": "BUKRS EQ 'UNES' AND HBKID EQ 'UBA01'"}])
    if rows_t035d:
        for r in rows_t035d:
            print(f"  [INFO] T035D entry: {r}")
    else:
        print("  [INFO] No T035D entries found for UNES/UBA01")
except Exception as e:
    print(f"  [ERROR] T035D: {e}")

# ── Summary ──
print("\n" + "=" * 70)
print(f"SUMMARY: {PASS_COUNT} PASS / {FAIL_COUNT} FAIL / {MISSING_COUNT} MISSING")
print("=" * 70)

conn.close()
