"""Inject unique_objects.json into the enhanced dashboard."""
import json, os

# Load both data sets
with open('cts_dashboard_data.json', encoding='utf-8') as f:
    d1 = json.load(f)
with open('cts_unique_objects.json', encoding='utf-8') as f:
    d2 = json.load(f)
with open('cts_package_config_data.json', encoding='utf-8') as f:
    d3 = json.load(f)

js1 = 'const DATA = ' + json.dumps(d1, separators=(',',':'), ensure_ascii=False) + ';\n'
js2 = 'const UDATA = ' + json.dumps(d2, separators=(',',':'), ensure_ascii=False) + ';\n'
js3 = 'const PDATA = ' + json.dumps(d3, separators=(',',':'), ensure_ascii=False) + ';\n'

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# Replace placeholder
new_html = html.replace('/* DATA_PLACEHOLDER */', js1 + js2 + js3)
assert 'const DATA' in new_html, 'Injection error!'

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

size = os.path.getsize('cts_dashboard.html')
print(f'Done: {size//1024}KB')
print(f'Data: D1={len(js1)//1024}KB  D2={len(js2)//1024}KB  D3={len(js3)//1024}KB')

s = d2['summary']
print(f"\nReal unique counts injected:")
print(f"  Transport pairs (inflated): {s['total_transport_pairs']:,}")
print(f"  Unique objects (real):      {s['unique_objects']:,}")
print(f"  Unique dev:                 {s['unique_dev']:,}")
print(f"  Unique config:              {s['unique_cfg']:,}")
print(f"  Unique security:            {s['unique_sec']:,}")
print(f"  Unique EPI-USE:             {s['unique_epi']:,}")
print(f"  Avg mods/object:            {s['avg_mods']}x")
