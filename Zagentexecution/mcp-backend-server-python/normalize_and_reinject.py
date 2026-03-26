"""
Normalize old inconsistent module labels and re-inject 
updated CFGDETAIL into the dashboard HTML.
"""
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

# ── 1. Load updated config detail ─────────────────────────────────────────────
with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# ── 2. Normalize legacy label inconsistencies ─────────────────────────────────
LABEL_NORM = {
    'HCM/Config View':    'HCM-PA',
    'FI/CO Config View':  'FI',
    'FI (Finance)':       'FI',
    'FI (Accounts)':      'FI-GL',
    'PSM/FM':             'PSM-FM',
    'CO (Controlling)':   'CO',
    'CO-PA (Profitability)': 'CO',
    'BC-Sec / User Mgmt': 'SECURITY',
    'BC-Sec / Auth':      'SECURITY',
    'BC-Payroll Post':    'HCM-PY',
    'BC-IMG (Cust Tree)': 'BASIS',
    'BC-NR (Number Ranges)': 'BASIS-NR',
    'BC-Basis':           'BASIS',
    'BC-WF (Workflow)':   'BASIS-WF',
    'HCM-PA (Personnel Admin)': 'HCM-PA',
    'MM (Procurement)':   'MM',
    'HR/Payroll':         'HCM-PY',
    'MDG':                'BASIS',
}

norm_count = 0
for obj_name, item in cfg.items():
    old = item.get('module', '')
    if old in LABEL_NORM:
        item['module'] = LABEL_NORM[old]
        norm_count += 1

print(f'Normalized {norm_count} legacy labels')

# ── 3. Show final distribution ────────────────────────────────────────────────
import collections
modules = collections.Counter(v.get('module','?') for v in cfg.values())
print('\n=== FINAL MODULE DISTRIBUTION ===')
for m, c in modules.most_common(35):
    pct = c / len(cfg) * 100
    print(f'  {c:5d} ({pct:4.1f}%)  {m}')

# ── 4. Save updated JSON ──────────────────────────────────────────────────────
with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

print(f'\nTotal objects: {len(cfg)}')
unclassified = modules.get('General IMG', 0)
print(f'Still General IMG: {unclassified} ({unclassified/len(cfg)*100:.1f}%)')
classified = len(cfg) - unclassified
print(f'Now classified: {classified} ({classified/len(cfg)*100:.1f}%)')

# ── 5. Re-inject into dashboard HTML ──────────────────────────────────────────
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

cfg_json = json.dumps(cfg, ensure_ascii=False, separators=(',', ':'))

# Replace existing CFGDETAIL block
pattern = r'(var CFGDETAIL\s*=\s*)([\s\S]*?)(;\s*//\s*END CFGDETAIL|;(?=\s*\n\s*(var |//|function)))'
replacement = f'var CFGDETAIL = {cfg_json}; // END CFGDETAIL'

new_html = re.sub(pattern, replacement, html, count=1)

if new_html == html:
    # Fallback: try simpler pattern
    pattern2 = r'var CFGDETAIL\s*=\s*\{[\s\S]*?\};'
    new_html = re.sub(pattern2, f'var CFGDETAIL = {cfg_json};', html, count=1)

if new_html == html:
    print('WARNING: Could not find CFGDETAIL pattern in HTML')
else:
    with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_html)
    print('Re-injected CFGDETAIL into cts_dashboard.html')

print('Done.')
