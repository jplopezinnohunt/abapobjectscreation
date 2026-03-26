"""
cts_probe_other.py — Inventory all unclassified object types
Tells us exactly what's in the OTHER 51% bucket.
"""
import json
from collections import Counter, defaultdict

# From cts_object_classification.py
DEV_TYPES = {
    'PROG','REPS','REPT','REPY','REPO',
    'CLAS','INTF',
    'FUGR','FUNC','FUGA',
    'ENHO','ENHS','ENHD',
    'XSLT','WDYN','WDCA','WDCC','WDCO',
    'IWSV','IWOM','IWSG','IOBJ',
    'WAPA','W3MI','W3HT','W3UD',
    'SWFP','SWFT','SWED','SWFL',
    'TYPE','TTYP',
    'MSAG','MESS',
    'SSFO','SFPF','SFPS',
    'SPRX','SHLP','SOBJ',
}
CONFIG_TYPES = {
    'TABU','VDAT','VIEW','VCLS','CUST',
    'CUAD','DYNT','DYNP','NROB',
    'PDTS','PDVS','PDAT','PARA','PARS',
}
DATA_MODEL_TYPES = {
    'TABL','DTEL','DOMA','INDX','SQLT','SQSC','TTYP',
}
INFRA_TYPES = {
    'DEVC','ACID','AUTH','SUSC','SUSO','PFCG',
    'TRAN','DOCT','DOCV','XPRA','STVI','STOB','SUCU',
}
KNOWN = DEV_TYPES | CONFIG_TYPES | DATA_MODEL_TYPES | INFRA_TYPES

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

other_types   = Counter()            # type_code -> count
type_by_user  = defaultdict(Counter) # user -> type_code -> count
type_examples = defaultdict(list)    # type_code -> [obj_name examples]

for t in raw['transports']:
    if t.get('trkorr','').upper().startswith('E9BK'): continue
    owner = t.get('owner','').strip().upper()
    for o in t.get('objects', []):
        ot = o.get('obj_type', o.get('OBJECT', '')).strip().upper()
        if ot not in KNOWN:
            other_types[ot] += 1
            type_by_user[owner][ot] += 1
            if len(type_examples[ot]) < 3:
                name = o.get('obj_name', o.get('OBJ_NAME',''))
                if name and name not in type_examples[ot]:
                    type_examples[ot].append(name)

print("=" * 75)
print("  UNCLASSIFIED OBJECT TYPES (the OTHER 51% bucket)")
print("  Sorted by frequency. Examples show what each type contains.")
print("=" * 75)
print(f"  {'Type':<8} {'Count':>8}  Examples")
print(f"  {'-'*70}")

for ot, cnt in other_types.most_common(50):
    examples = ', '.join(type_examples[ot][:3])
    print(f"  {ot:<8} {cnt:>8,}  {examples}")

# Show which users own the top mystery types
print(f"\n\n  TOP MYSTERY TYPES BY USER (top 10 types, top 5 users each)")
print(f"  {'-'*70}")
for ot, cnt in other_types.most_common(10):
    print(f"\n  [{ot}] {cnt:,} objects — e.g. {', '.join(type_examples[ot])}")
    user_top = type_by_user_sorted = sorted(
        ((u, c) for u, ctr in type_by_user.items() for t2, c in ctr.items() if t2 == ot),
        key=lambda x: -x[1]
    )[:5]
    for u, c in user_top:
        print(f"    {u.title():<25} {c:>6,}")
