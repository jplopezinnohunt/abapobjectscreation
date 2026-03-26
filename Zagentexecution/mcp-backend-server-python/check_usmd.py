import json
from collections import Counter

with open('cts_10yr_raw.json', encoding='utf-8') as f:
    raw = json.load(f)

targets = {'USMD2001', 'USMD2003'}
by_name = {}
for t in raw['transports']:
    for o in t.get('objects', []):
        on = o.get('obj_name', o.get('OBJ_NAME', '')).strip()
        ot = o.get('obj_type', o.get('OBJECT', '')).strip()
        if on in targets:
            if on not in by_name:
                by_name[on] = {'types': set(), 'owners': set(), 'years': set(), 'count': 0}
            by_name[on]['types'].add(ot)
            by_name[on]['owners'].add(t.get('owner', ''))
            by_name[on]['years'].add(t.get('date', '')[:4])
            by_name[on]['count'] += 1

for name, v in by_name.items():
    print(name + ': ' + str(v['count']) + 'x')
    print('  types=' + str(v['types']))
    print('  owners=' + str(v['owners']))
    print('  years=' + str(sorted(v['years'])))
