"""
reinject_cfgdetail.py - Load corrected cfg + pkg_desc, re-inject into dashboard
"""
import json, os, re

# Load data
with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)
with open('cts_pkg_descriptions.json', encoding='utf-8') as f:
    pkg_desc = json.load(f)

# Enrich: add pkg_desc to any objects that now have a valid package
enriched = 0
for name, v in cfg.items():
    pkg = v.get('package','')
    if pkg and pkg in pkg_desc and not v.get('pkg_desc'):
        v['pkg_desc'] = pkg_desc[pkg]
        enriched += 1

print(f'Enriched {enriched} additional objects with pkg_desc')
print(f'Total with package: {sum(1 for v in cfg.values() if v.get("package"))}')
print(f'Total with pkg_desc: {sum(1 for v in cfg.values() if v.get("pkg_desc"))}')

# Sample spot-checks
for n in ['YTHR_UNDP','YVHR_REGGR_TXT','YTHR_ANSVH_DASH','TCALS','T16FV','T5ASRFSCNFLDPRP']:
    if n in cfg:
        v = cfg[n]
        print(f'  {n}: pkg={v.get("package","")} desc={v.get("pkg_desc","")}')

# Save updated cfg
with open('cts_config_detail.json','w',encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

# Re-inject into HTML
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

NEW_CFG = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
s = html.find('const CFGDETAIL=')
e = html.find(';\n', s) + 2
if s == -1:
    print('ERROR: CFGDETAIL not found in HTML')
else:
    html = html[:s] + NEW_CFG + html[e:]
    print(f'Re-injected CFGDETAIL ({len(NEW_CFG)//1024}KB)')

with open('cts_dashboard.html','w',encoding='utf-8') as f:
    f.write(html)
print(f'Dashboard saved: {os.path.getsize("cts_dashboard.html")//1024}KB')
