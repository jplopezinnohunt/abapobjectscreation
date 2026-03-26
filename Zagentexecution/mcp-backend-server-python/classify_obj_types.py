"""
classify_obj_types.py
Adds semantic classification to each config object based on its obj_type.
Groups related types together, marks derivative/secondary ones,
and generates meaningful 'type_label' + 'type_category' fields.
Then patches dashboard to show type category instead of raw code.
"""
import json, os

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# ── Classification matrix ─────────────────────────────────────────────────────
# Categories: PRIMARY (real config work), SECONDARY (derived/generated), TECHNICAL
OBJ_TYPE_META = {
    # PRIMARY — real configuration content
    'TABU': {'label': 'Table Content',          'cat': 'PRIMARY',   'icon': '🗂️'},
    'TDAT': {'label': 'Sys-Indep Table Content', 'cat': 'PRIMARY',   'icon': '🗂️'},
    'CUAD': {'label': 'IMG Activity',            'cat': 'PRIMARY',   'icon': '⚙️'},
    'CUS0': {'label': 'Customizing BCS',         'cat': 'PRIMARY',   'icon': '⚙️'},
    'CUS1': {'label': 'Customizing Entry',        'cat': 'PRIMARY',   'icon': '⚙️'},
    'CDAT': {'label': 'Cluster Table Content',   'cat': 'PRIMARY',   'icon': '🗂️'},
    'TOBJ': {'label': 'Auth Object',             'cat': 'PRIMARY',   'icon': '🔐'},
    'NROB': {'label': 'Number Range Object',     'cat': 'PRIMARY',   'icon': '🔢'},
    'PARA': {'label': 'System Parameter',        'cat': 'PRIMARY',   'icon': '⚙️'},
    'PDTS': {'label': 'PD Object Type Set',      'cat': 'PRIMARY',   'icon': '👥'},

    # SECONDARY — derived from or related to a primary object
    'LODE': {'label': 'HR Logical Data Object',  'cat': 'SECONDARY', 'icon': '🔗',
             'note': 'Companion to TABU; HR logical grouping of related tables'},
    'SOTT': {'label': 'OTR Short Text',          'cat': 'SECONDARY', 'icon': '📝',
             'note': 'Online Text Repository (UI labels/translations)'},
    'TTYP': {'label': 'Accounting Object Type',  'cat': 'SECONDARY', 'icon': '🔗',
             'note': 'Object type metadata for CO/FI accounting'},
    'OSOA': {'label': 'BW/BI DataSource',        'cat': 'SECONDARY', 'icon': '📊',
             'note': 'Generic DataSource definition for BW reporting'},
    'VARX': {'label': 'Report Variant',          'cat': 'SECONDARY', 'icon': '📋',
             'note': 'Selection variant for a report/program'},
    'SCVI': {'label': 'Screen Variant',          'cat': 'SECONDARY', 'icon': '🖥️',
             'note': 'Field simplification/hide rules for a screen'},
    'AVAS': {'label': 'Classification',          'cat': 'SECONDARY', 'icon': '🏷️',
             'note': 'Characteristic value assignment (classification)'},
    'PMKC': {'label': 'PM Characteristic',      'cat': 'SECONDARY', 'icon': '🏷️'},
    'LODC': {'label': 'Lock Object Cust.',       'cat': 'SECONDARY', 'icon': '🔒',
             'note': 'Customizing lock object, companion to TABU'},
    'SOTU': {'label': 'Sort Object Text',        'cat': 'SECONDARY', 'icon': '📝'},
    'TABD': {'label': 'Table Definition',        'cat': 'TECHNICAL', 'icon': '🏗️',
             'note': 'DD table structure (transported with table)'},
    'TABT': {'label': 'Table Text',              'cat': 'TECHNICAL', 'icon': '📝'},

    # TECHNICAL — SAP internal
    'ELIN': {'label': 'Documentation Object',   'cat': 'TECHNICAL', 'icon': '📄'},
    'REPS': {'label': 'Program Source',         'cat': 'TECHNICAL', 'icon': '💻'},
    'PROG': {'label': 'ABAP Program',           'cat': 'TECHNICAL', 'icon': '💻'},
    'VIED': {'label': 'View Definition',        'cat': 'TECHNICAL', 'icon': '🏗️'},
    'CDAT': {'label': 'Cluster Content',        'cat': 'PRIMARY',   'icon': '🗂️'},
}

DEFAULT_META = {'label': 'Config Object', 'cat': 'PRIMARY', 'icon': '⚙️'}

# Apply to all cfg objects
for name, v in cfg.items():
    t = v.get('obj_type', '')
    meta = OBJ_TYPE_META.get(t, DEFAULT_META)
    v['type_label']    = meta['label']
    v['type_category'] = meta['cat']
    v['type_note']     = meta.get('note', '')

# Stats
from collections import Counter
cat_counts = Counter(v['type_category'] for v in cfg.values())
print('Category distribution:')
for cat, cnt in cat_counts.most_common():
    pct = cnt*100//len(cfg)
    print(f'  {cat:<12} {cnt:>5} ({pct}%)')

# How many SECONDARY objects exist
secondary = {n: v for n, v in cfg.items() if v['type_category'] == 'SECONDARY'}
print(f'\nSECONDARY objects: {len(secondary)}')
by_type = Counter(v['obj_type'] for v in secondary.values())
for t,c in by_type.most_common():
    lbl = OBJ_TYPE_META.get(t, {}).get('label', t)
    note = OBJ_TYPE_META.get(t, {}).get('note', '')
    print(f'  {t:<8} {c:>4}  {lbl}  {note}')

with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)
print('\nSaved cts_config_detail.json with type_label, type_category, type_note')

# ── Now patch dashboard to show type_category badge + type_label in rows ──────
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# Re-inject CFGDETAIL
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
s = html.find('const CFGDETAIL='); e = html.find(';\n', s)+2
html = html[:s] + NEW_CFG_JS + html[e:]

# Update the row template to show type_label instead of raw obj_type
# Also add a small category badge
OLD_TYPE_CELL = '`<td><code style="font-size:.64rem;color:var(--mu2)">${c.obj_type}</code></td>`'
# Find the broader pattern
OLD_TYPE_FRAG = '<td><code style="font-size:.64rem;color:var(--mu2)">${c.obj_type}</code></td>'
NEW_TYPE_FRAG = '''<td>
          <span style="font-size:.62rem;color:var(--mu2);display:block">${c.type_label||c.obj_type}</span>
          ${c.type_category==='SECONDARY'?`<span style="font-size:.55rem;padding:0 4px;border-radius:3px;background:rgba(234,179,8,.12);color:#ca8a04">derived</span>`:c.type_category==='TECHNICAL'?`<span style="font-size:.55rem;padding:0 4px;border-radius:3px;background:rgba(100,116,139,.2);color:#94a3b8">technical</span>`:''}
        </td>'''

if OLD_TYPE_FRAG in html:
    html = html.replace(OLD_TYPE_FRAG, NEW_TYPE_FRAG, 1)
    print('Patched type column to show type_label + category badge')
else:
    print('WARNING: type cell pattern not found — skipping visual patch')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
