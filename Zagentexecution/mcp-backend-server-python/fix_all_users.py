"""
fix_all_users.py
Updates top_users in dashboard DATA to include ALL 47 contributors.
Merges duplicates: V.VAURETTE→V_VAURETTE, P.IKOUNA→P_IKOUNA
Sorts by objects touched (descending).
"""
import json, re, os, sys
sys.stdout.reconfigure(encoding='utf-8')

# All contributors sorted by objects touched (from check_all_users output)
# Merge duplicates: keep canonical underscore version
MERGE = {
    'V.VAURETTE': 'V_VAURETTE',
    'P.IKOUNA': 'P_IKOUNA',
}

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

from collections import Counter
user_objs = Counter()
for name, v in cfg.items():
    for u in v.get('users', []):
        canonical = MERGE.get(u, u)
        user_objs[canonical] += 1

# Full sorted user list (exclude system/batch users)
EXCLUDE = {'EPI-USE_LABS', 'USER_SPDD', 'SM36623'}
all_users_sorted = [u for u, _ in user_objs.most_common() if u not in EXCLUDE]
print(f'Total contributors (after dedup): {len(all_users_sorted)}')
for u in all_users_sorted:
    print(f'  {u}: {user_objs[u]} objects')

# Patch the dashboard HTML
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

m = re.search(r'"top_users":\[([^\]]+)\]', html)
if m:
    old_str = m.group(0)
    new_arr = json.dumps(all_users_sorted, ensure_ascii=False)
    new_str = '"top_users":' + new_arr
    html = html.replace(old_str, new_str, 1)
    print(f'\nReplaced top_users: was {old_str[:60]}...')
    print(f'Now: {new_str[:80]}...')
else:
    print('ERROR: top_users not found in HTML')

# Also patch buildUserTabs to handle duplicates in user data
# The users list is now canonical, good

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'\nDone! {os.path.getsize("cts_dashboard.html")//1024}KB')
