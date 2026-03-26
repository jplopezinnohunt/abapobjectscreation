"""
cts_user_year_breakdown.py
Per-user, per-year breakdown separating Workbench (K) vs Customizing (W).
Excludes EPI-USE_LABS (third-party HCM product, not UNESCO team work).
"""
import json
from collections import defaultdict

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

# Exclude EPI-USE and SAP system transports
EXCLUDE = {'EPI-USE_LABS', 'EPI_USE_LABS', 'SAP', 'DDIC'}
transports = [
    t for t in raw['transports']
    if t.get('owner','').upper() not in {e.upper() for e in EXCLUDE}
    and not t.get('trkorr','').upper().startswith('E9BK')
]

# -- Year x User x Type aggregation --
# data[user][year] = {WB_trx, WB_obj, CU_trx, CU_obj}
data = defaultdict(lambda: defaultdict(lambda: {
    'WB_trx':0,'WB_obj':0,'CU_trx':0,'CU_obj':0,'OT_trx':0,'OT_obj':0
}))

years = set()
for t in transports:
    owner = t.get('owner','').strip().upper()
    year  = t.get('date','')[:4]
    fn    = t.get('type_code', t.get('type',''))
    cnt   = t.get('obj_count', 0)
    years.add(year)
    if fn in ('K', 'Workbench'):
        data[owner][year]['WB_trx'] += 1
        data[owner][year]['WB_obj'] += cnt
    elif fn in ('W', 'Customizing'):
        data[owner][year]['CU_trx'] += 1
        data[owner][year]['CU_obj'] += cnt
    else:
        data[owner][year]['OT_trx'] += 1
        data[owner][year]['OT_obj'] += cnt

years = sorted(y for y in years if y.isdigit())

# Total per user (for sorting)
user_totals = {
    u: sum(d['WB_trx']+d['CU_trx']+d['OT_trx'] for d in by_year.values())
    for u, by_year in data.items()
}
top_users = [u for u, _ in sorted(user_totals.items(), key=lambda x: -x[1]) if user_totals[u] > 0]

# ─── PRINT REPORT ───────────────────────────────────────────────────────────

print("=" * 100)
print("  UNESCO SAP — User Activity Breakdown by Year: Workbench (WB) vs Customizing (CU)")
print("  Source: cts_10yr_raw.json | Excluded: EPI-USE_LABS, SAP system users")
print("=" * 100)

# Header row
hdr = f"{'USER':<22}"
for y in years:
    hdr += f"  {y:>14}"
hdr += f"  {'TOTAL':>10}"
print(hdr)
print("-" * 100)

# Sub-header
sub = f"{'':22}"
for _ in years:
    sub += f"  {'WB':>6} {'CU':>6}"
sub += f"  {'WB':>4} {'CU':>4}"
print(sub)
print("-" * 100)

for user in top_users[:30]:
    row = f"{user.title():<22}"
    total_wb = total_cu = 0
    for y in years:
        d  = data[user].get(y, {})
        wb = d.get('WB_trx', 0)
        cu = d.get('CU_trx', 0)
        total_wb += wb
        total_cu += cu
        row += f"  {wb:>6} {cu:>6}"
    row += f"  {total_wb:>4} {total_cu:>4}"
    print(row)

print("-" * 100)

# Grand totals row
row = f"{'*** TOTAL ***':<22}"
gt_wb = gt_cu = 0
for y in years:
    wb = sum(data[u].get(y,{}).get('WB_trx',0) for u in top_users)
    cu = sum(data[u].get(y,{}).get('CU_trx',0) for u in top_users)
    gt_wb += wb; gt_cu += cu
    row += f"  {wb:>6} {cu:>6}"
row += f"  {gt_wb:>4} {gt_cu:>4}"
print(row)
print("=" * 100)

# ─── OBJECTS (not just transport count) ───────────────────────────────────────
print("\n  OBJECTS CHANGED (Workbench vs Customizing) — Top 15 users\n")
print(f"  {'USER':<22} {'Total Trx':>10} {'WB Trx':>8} {'WB Obj':>9} {'CU Trx':>8} {'CU Obj':>9}  {'Dominant Activity'}")
print(f"  {'-'*90}")

for user in top_users[:15]:
    wb_trx = sum(data[user][y]['WB_trx'] for y in years)
    cu_trx = sum(data[user][y]['CU_trx'] for y in years)
    wb_obj = sum(data[user][y]['WB_obj'] for y in years)
    cu_obj = sum(data[user][y]['CU_obj'] for y in years)
    total  = wb_trx + cu_trx
    dom    = 'DEVELOPER' if wb_trx > cu_trx else 'CONFIG/FUNCTIONAL'
    if wb_trx == 0 and cu_trx == 0:
        dom = 'OTHER'
    print(f"  {user.title():<22} {total:>10,} {wb_trx:>8,} {wb_obj:>9,} {cu_trx:>8,} {cu_obj:>9,}  {dom}")

# ─── YEAR TOTALS ──────────────────────────────────────────────────────────────
print("\n  YEAR TOTALS (all users)\n")
print(f"  {'Year':<6} {'WB Trx':>8} {'WB Obj':>10} {'CU Trx':>8} {'CU Obj':>10}  WB/CU split")
print(f"  {'-'*60}")
for y in years:
    wb_t = sum(data[u].get(y,{}).get('WB_trx',0) for u in top_users)
    cu_t = sum(data[u].get(y,{}).get('CU_trx',0) for u in top_users)
    wb_o = sum(data[u].get(y,{}).get('WB_obj',0) for u in top_users)
    cu_o = sum(data[u].get(y,{}).get('CU_obj',0) for u in top_users)
    total = wb_t + cu_t or 1
    bar   = '#' * int(wb_t/total*20) + '.' * int(cu_t/total*20)
    print(f"  {y:<6} {wb_t:>8,} {wb_o:>10,} {cu_t:>8,} {cu_o:>10,}  [{bar}]  {wb_t/total*100:.0f}%WB/{cu_t/total*100:.0f}%CU")
