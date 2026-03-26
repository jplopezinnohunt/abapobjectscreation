"""Quick owner + object-count stats from raw transport JSON."""
import json
from collections import Counter

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

transports = raw['transports']

# Owner stats
owner_stats = {}
for t in transports:
    owner = t.get('owner', '').strip().upper()
    cnt   = t.get('obj_count', 0)
    if owner not in owner_stats:
        owner_stats[owner] = {'trx': 0, 'objs': 0, 'high': 0}
    owner_stats[owner]['trx']  += 1
    owner_stats[owner]['objs'] += cnt
    if cnt >= 100:
        owner_stats[owner]['high'] += 1

SVC_DIGITS = set('0123456789')

def classify(owner):
    if owner in {'SAP','DDIC','BASIS','SAP_SUPPORT'}:
        return 'SAP_SYSTEM'
    if owner.startswith('I') and len(owner) >= 7 and owner[1:].isdigit():
        return 'SVC_ACCT'
    return 'REAL_USER'

top = sorted(owner_stats.items(), key=lambda x: -x[1]['trx'])[:30]
print(f"\nTop 30 owners:")
print(f"{'Owner':<22} {'Trx':>6} {'Objects':>9} {'>100obj trx':>12}  Class")
print('-' * 60)
for owner, d in top:
    cls = classify(owner)
    print(f"{owner:<22} {d['trx']:>6} {d['objs']:>9,} {d['high']:>12}  {cls}")

# Object count buckets
print("\nObject count distribution per transport:")
buckets = Counter()
for t in transports:
    c = t.get('obj_count', 0)
    if c == 0:     b = '0 (empty)'
    elif c <= 5:   b = '1-5'
    elif c <= 20:  b = '6-20'
    elif c <= 50:  b = '21-50'
    elif c <= 100: b = '51-100'
    elif c <= 500: b = '101-500'
    else:          b = '500+'
    buckets[b] += 1

order = ['0 (empty)','1-5','6-20','21-50','51-100','101-500','500+']
for k in order:
    print(f"  {k:<12} {buckets[k]:>6} transports")

# User-class summary
print("\nUser class summary:")
uc = Counter(classify(t.get('owner','').strip().upper()) for t in transports)
for cls, cnt in uc.most_common():
    pct = cnt / len(transports) * 100
    objs = sum(t.get('obj_count',0) for t in transports
               if classify(t.get('owner','').strip().upper()) == cls)
    print(f"  {cls:<20} {cnt:>6} trx ({pct:>5.1f}%)   {objs:>9,} objects")
