"""Find CGI XML test cases in D01 for format inspection.

Goal: list real CGI media (REGUT, DTFOR LIKE /CGI%, XVORL='') that can be
replayed via ZSAPFPAYM_REPLAY, and characterize each run (co code, currency,
amount, #pmts, creditor countries) so we pick cases that exercise the
structured address across Dbtr/Cdtr/UltmtCdtr/UltmtDbtr.
"""
import sys, os
SCRIPTS_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPTS_DIR not in sys.path: sys.path.insert(0, SCRIPTS_DIR)
from rfc_helpers import ConnectionGuard
from collections import defaultdict

g = ConnectionGuard("D01"); g.connect()

# 1) Real CGI media in REGUT (DTFOR = CGI tree, XVORL='' = not a proposal)
rt_fields = ["LAUFD", "LAUFI", "GRPNO", "DTFOR", "ZBUKR", "BANKS", "WAERS", "RBETR", "XVORL", "TSUSR", "STATUS"]
res = g.call(
    "RFC_READ_TABLE", QUERY_TABLE="REGUT", DELIMITER="|",
    FIELDS=[{"FIELDNAME": f} for f in rt_fields],
    OPTIONS=[{"TEXT": "DTFOR LIKE '/CGI%'"}, {"TEXT": " AND XVORL = ' '"}],
    ROWCOUNT=2000,
)
media = []
for r in res.get("DATA", []):
    vals = [v.strip() for v in r["WA"].split("|")]
    media.append(dict(zip(rt_fields, vals)))

print(f"== REAL CGI media in D01 (REGUT, XVORL=''): {len(media)} ==")
# rank by LAUFD desc
media.sort(key=lambda m: (m["LAUFD"], m["LAUFI"]), reverse=True)
by_fmt = defaultdict(int)
for m in media: by_fmt[m["DTFOR"]] += 1
print("by format:", dict(by_fmt))
print(f"\n{'LAUFD':<10}{'LAUFI':<9}{'GRP':<5}{'CoCd':<6}{'Cur':<5}{'Amount':>16}  {'Format':<22}{'User':<10}")
print("-"*95)
for m in media[:25]:
    try: amt = f"{float(m['RBETR']):,.2f}"
    except: amt = m["RBETR"]
    print(f"{m['LAUFD']:<10}{m['LAUFI']:<9}{m['GRPNO']:<5}{m['ZBUKR']:<6}{m['WAERS']:<5}{amt:>16}  {m['DTFOR']:<22}{m['TSUSR']:<10}")

# 2) Characterize the most recent ~8 runs via REGUH (creditor countries / parties)
print("\n== Per-run creditor profile (REGUH) for the 8 most recent CGI runs ==")
reguh_fields = ["LIFNR", "EMPFG", "UBNKS", "ZLAND", "WAERS", "RBETR", "ZNME1", "ZSTRA", "ZORT1"]
seen = set()
picks = []
for m in media:
    k = (m["LAUFD"], m["LAUFI"])
    if k in seen: continue
    seen.add(k); picks.append(m)
    if len(picks) >= 8: break

for m in picks:
    res2 = g.call(
        "RFC_READ_TABLE", QUERY_TABLE="REGUH", DELIMITER="|",
        FIELDS=[{"FIELDNAME": f} for f in reguh_fields],
        OPTIONS=[{"TEXT": f"LAUFD = '{m['LAUFD']}'"}, {"TEXT": f" AND LAUFI = '{m['LAUFI']}'"}],
        ROWCOUNT=400,
    )
    rows = []
    for r in res2.get("DATA", []):
        rows.append(dict(zip(reguh_fields, [v.strip() for v in r["WA"].split("|")])))
    ubnks = sorted({r["UBNKS"] for r in rows if r["UBNKS"]})
    zland = sorted({r["ZLAND"] for r in rows if r["ZLAND"]})
    # alt-payee heuristic: EMPFG populated (alternative payee recipient)
    altpayee = sum(1 for r in rows if r["EMPFG"])
    print(f"\n  {m['LAUFD']}/{m['LAUFI']} grp={m['GRPNO']} {m['ZBUKR']} {m['DTFOR']}")
    print(f"    pmts={len(rows)}  bank-countries(UBNKS)={ubnks}  addr-countries(ZLAND)={zland}  alt-payee(EMPFG!='')={altpayee}")

g.close()
