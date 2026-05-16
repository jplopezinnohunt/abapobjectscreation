"""Verify CP BOURG payment + hunt real SEPA EMPFG alternatives — narrow reads."""
import os
from dotenv import load_dotenv
from pyrfc import Connection

load_dotenv('Zagentexecution/mcp-backend-server-python/.env')
params = dict(
    ashost=os.getenv('SAP_ASHOST'), sysnr=os.getenv('SAP_SYSNR'),
    client=os.getenv('SAP_CLIENT'), user=os.getenv('SAP_USER'),
    lang='EN', snc_mode='1',
    snc_partnername=os.getenv('SAP_SNC_PARTNERNAME'), snc_qop='9',
)
conn = Connection(**params)
print("Connected D01")

def rd(t, opts, fields, n=2000):
    r = conn.call('RFC_READ_TABLE', QUERY_TABLE=t,
                  OPTIONS=[{'TEXT': x} for x in opts],
                  FIELDS=[{'FIELDNAME': x} for x in fields],
                  DELIMITER='|', ROWCOUNT=n)
    cols = [f['FIELDNAME'] for f in r.get('FIELDS',[])] or fields
    return [dict(zip(cols, d['WA'].split('|'))) for d in r.get('DATA', [])]

# ── 1. REGUH for 20210316/TST — split into 2 passes ──
print("\n=== REGUH 20210316/TST status flags (split reads) ===")
try:
    p1 = rd("REGUH",
            ["LAUFD = '20210316'", " AND LAUFI = 'TST'", " AND ZBUKR = 'UNES'"],
            ["LIFNR","XVORL","XEB1","VBLNR"], n=50)
    p2 = rd("REGUH",
            ["LAUFD = '20210316'", " AND LAUFI = 'TST'", " AND ZBUKR = 'UNES'"],
            ["LIFNR","XVORL","XAVIS","VOIDS"], n=50)
    p3 = rd("REGUH",
            ["LAUFD = '20210316'", " AND LAUFI = 'TST'", " AND ZBUKR = 'UNES'"],
            ["LIFNR","XVORL","EMPFG"], n=50)
    # Merge by index
    for a, b, c in zip(p1, p2, p3):
        emp = c['EMPFG'].strip()
        mark = '★' if emp else ' '
        print(f"  {mark} LIFNR={a['LIFNR']} XVORL='{a['XVORL'].strip()}' XEB1='{a['XEB1'].strip()}' XAVIS='{b['XAVIS'].strip()}' VOIDS='{b['VOIDS'].strip()}' VBLNR={a['VBLNR']} EMPFG='{emp}'")
except Exception as e:
    print(f"  ERR: {e}")

# ── 2. All CP BOURG REGUH ──
print("\n=== ALL D01 REGUH for 0000700085 (CP BOURG) ===")
try:
    rows = rd("REGUH",
              ["LIFNR = '0000700085'"],
              ["LAUFD","LAUFI","ZBUKR","XVORL","VBLNR"], n=200)
    print(f"  {len(rows)} REGUH rows")
    for r in rows:
        v = r['VBLNR'].strip()
        is_placeholder = v in ('0100000000','0000000000','')
        mark = 'real' if not is_placeholder and r['XVORL'].strip()=='' else ('proposal' if r['XVORL'].strip()=='X' else 'placeholder')
        print(f"    {r['LAUFD']}/{r['LAUFI']}/{r['ZBUKR']} VBLNR={r['VBLNR']} XVORL='{r['XVORL'].strip()}' → {mark}")
except Exception as e:
    print(f"  ERR: {e}")

# ── 3. Hunt for SEPA runs with EMPFG AND real-looking VBLNR ──
print("\n=== Hunt: D01 SEPA runs with EMPFG + real VBLNR (split reads) ===")
dfpg = rd("DFPAYG", ["FORMI = '/SEPA_CT_UNES'"],
          ["LAUFD","LAUFI","ZBUKR","ANZ_ERZ","ANZ_ERL"], n=100)
print(f"  {len(dfpg)} SEPA-UNES DFPAYG runs total\n")
real_hits = []
for g in dfpg:
    laufd, laufi, zb = g['LAUFD'].strip(), g['LAUFI'].strip(), g['ZBUKR'].strip()
    try:
        # Pass A: LIFNR + EMPFG
        a = rd("REGUH",
               [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
               ["LIFNR","EMPFG"], n=200)
        # Pass B: XVORL + VBLNR  (positional zip)
        b = rd("REGUH",
               [f"LAUFD = '{laufd}'", f" AND LAUFI = '{laufi}'", f" AND ZBUKR = '{zb}'"],
               ["LIFNR","XVORL","VBLNR"], n=200)
        # Join by index (same query, same order)
        for ra, rb in zip(a, b):
            emp = ra['EMPFG'].strip()
            v = rb['VBLNR'].strip()
            xv = rb['XVORL'].strip()
            if emp and xv == '' and v not in ('0100000000','0000000000',''):
                real_hits.append({'laufd':laufd,'laufi':laufi,'zb':zb,
                                  'lifnr':ra['LIFNR'].strip(),'empfg':emp,'vblnr':v})
    except Exception:
        pass

print(f"  REAL payment hits (XVORL='', VBLNR non-placeholder, EMPFG populated): {len(real_hits)}")
for h in real_hits:
    print(f"  ★ {h['laufd']}/{h['laufi']}/{h['zb']} LIFNR={h['lifnr']} VBLNR={h['vblnr']} EMPFG={h['empfg']}")

# ── 4. Also look at ALL EMPFG-populated rows in REGUH and their VBLNR pattern ──
print("\n=== D01 REGUH all EMPFG-populated rows (any format) — show VBLNR pattern ===")
try:
    all_empfg = rd("REGUH",
                   ["EMPFG <> ' '"],
                   ["LIFNR","EMPFG"], n=2000)
    all_vblnr = rd("REGUH",
                   ["EMPFG <> ' '"],
                   ["LIFNR","XVORL","VBLNR"], n=2000)
    by_pattern = {}
    for ra, rb in zip(all_empfg, all_vblnr):
        v = rb['VBLNR'].strip()
        xv = rb['XVORL'].strip()
        pattern = f"XVORL='{xv}' VBLNR_prefix={v[:4] if v else '(empty)'}"
        by_pattern[pattern] = by_pattern.get(pattern, 0) + 1
    print("  VBLNR patterns among EMPFG-populated rows:")
    for p, n in sorted(by_pattern.items(), key=lambda x: -x[1]):
        print(f"    {p}: {n}")
except Exception as e:
    print(f"  err: {e}")
