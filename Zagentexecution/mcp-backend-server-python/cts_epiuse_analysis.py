"""EPI-USE_LABS transport deep dive."""
import json
from collections import Counter, defaultdict

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

epi = [t for t in raw['transports']
       if 'EPI' in t.get('owner','').upper() or 'EPI-USE' in t.get('owner','').upper()]

print(f"\n=== EPI-USE_LABS Deep Dive ===")
print(f"Total transports: {len(epi)}")
print(f"Total objects   : {sum(t.get('obj_count',0) for t in epi):,}\n")

# Timeline
by_quarter = defaultdict(lambda: {'trx': 0, 'objs': 0})
for t in epi:
    d = t.get('date','')
    if len(d) >= 6:
        y, m = d[:4], int(d[4:6])
        q = f"{y}-Q{(m-1)//3+1}"
        by_quarter[q]['trx']  += 1
        by_quarter[q]['objs'] += t.get('obj_count', 0)

print("Timeline (when they worked):")
for q in sorted(by_quarter):
    d = by_quarter[q]
    bar = '#' * min(d['trx'], 40)
    print(f"  {q}  {d['trx']:>3} trx  {d['objs']:>7,} obj   {bar}")

# Object type breakdown
print("\nWhat they transported (object categories):")
cat_ctr = Counter()
obj_ctr = Counter()
for t in epi:
    for o in t.get('objects', []):
        cat_ctr[o.get('change_cat','?')] += 1
        obj_ctr[o.get('obj_type','?')]   += 1

for cat, cnt in cat_ctr.most_common(15):
    print(f"  {cat:<35} {cnt:>6} objects")

print("\nTop raw object types (ABAP type code):")
for ot, cnt in obj_ctr.most_common(15):
    print(f"  {ot:<10} {cnt:>6}")

# Biggest single transports
print("\nTop 10 biggest transports (by object count):")
big = sorted(epi, key=lambda x: -x.get('obj_count',0))[:10]
for t in big:
    d = t.get('date','')
    y = d[:4] if d else '?'
    print(f"  {t['trkorr']:<22}  {y}  {t.get('obj_count',0):>6,} objects  {t.get('type','')}")

# Object namespace: Z vs standard
z_objs = 0
std_objs = 0
for t in epi:
    for o in t.get('objects', []):
        n = o.get('obj_name','').upper()
        if n.startswith(('Z','Y','/UN','/IDF')):
            z_objs += 1
        else:
            std_objs += 1

total_o = z_objs + std_objs
print(f"\nObject namespace split:")
print(f"  Customer (Z/Y/UNESCO) : {z_objs:>7,}  ({z_objs/total_o*100:.1f}%)")
print(f"  SAP Standard          : {std_objs:>7,}  ({std_objs/total_o*100:.1f}%)")
print(f"\nConclusion:")
if std_objs / total_o > 0.8:
    print("  Likely: HR data migration / payroll config (mostly SAP standard tables)")
elif z_objs / total_o > 0.5:
    print("  Likely: Custom HCM development / Z-object delivery")
else:
    print("  Mixed: Both SAP config and custom objects delivered")
