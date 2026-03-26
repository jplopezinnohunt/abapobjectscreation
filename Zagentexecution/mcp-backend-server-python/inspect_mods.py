import json
from collections import Counter

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

for name in ['T510', 'YTHR_UNDP', 'T5ASRFSCNFLDPRP', 'T524']:
    if name in cfg:
        v = cfg[name]
        tm = v.get('total_mods')
        uc = v.get('user_count')
        ya = v.get('years_active')
        yr = v.get('first_seen')
        ls = v.get('last_seen')
        print(f'{name}: total_mods={tm} users={uc} years={ya} ({yr}-{ls})')

print()
dist = Counter(v.get('total_mods', 0) for v in cfg.values())
for k in sorted(dist)[:15]:
    print(f'  total_mods={k}: {dist[k]} objects')
