import sys, json, re
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8')

# Check what CTS data files we have
import os
for f in os.listdir('.'):
    if 'cts' in f.lower() and f.endswith('.json'):
        sz = os.path.getsize(f)
        print(f'{f}: {sz//1024}KB')

print()

# Try loading the main CTS summary data
for fn in ['cts_summary.json', 'cts_data.json', 'cts_raw.json']:
    if os.path.exists(fn):
        with open(fn, encoding='utf-8') as f:
            d = json.load(f)
        print(f'=== {fn} ===')
        if isinstance(d, dict):
            print('Keys:', list(d.keys())[:20])
            if 'top_users' in d:
                print(f'top_users: {len(d["top_users"])}')
            if 'all_users' in d or 'users' in d:
                users = d.get('all_users') or d.get('users')
                print(f'all users: {len(users)}')
        break

# Check config_detail for user info across all objects
with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# Collect all users who touched any object
all_users = Counter()
for name, v in cfg.items():
    for u in v.get('users', []):
        all_users[u] += 1

print(f'\nUnique contributors across all config objects: {len(all_users)}')
for u, cnt in all_users.most_common(50):
    print(f'  {u:<25} {cnt} objects')
