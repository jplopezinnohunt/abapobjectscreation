import json
from collections import Counter, defaultdict

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# Count by module
mod_counts = Counter(v.get('module','(none)') for v in cfg.values())
print('=== MODULES ===')
for mod, cnt in mod_counts.most_common(30):
    print(f'  {mod:<40} {cnt:>5}')

# For top modules, show what packages they have
print('\n=== PACKAGES PER MODULE (top 5 modules) ===')
mod_pkgs = defaultdict(Counter)
for name, v in cfg.items():
    mod = v.get('module','(none)')
    pkg = v.get('package','(no pkg)')
    mod_pkgs[mod][pkg] += 1

for mod, _ in mod_counts.most_common(8):
    print(f'\n  Module: {mod}')
    for pkg, cnt in mod_pkgs[mod].most_common(8):
        print(f'    {pkg:<35} {cnt}')
