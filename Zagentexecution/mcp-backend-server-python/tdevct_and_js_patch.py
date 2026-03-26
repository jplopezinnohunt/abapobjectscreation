"""
tdevct_and_js_patch.py
1. Fetch package descriptions from TDEVCT (the correct SAP text table for packages)
2. Re-inject CFGDETAIL with pkg_desc fields
3. Patch JS: year filter + pagination (Load More) instead of hardcoded cap
"""
import json, os, re, time
from dotenv import load_dotenv
import pyrfc

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
CONN = dict(
    ashost=os.environ.get('SAP_ASHOST','172.16.4.66'),
    sysnr=os.environ.get('SAP_SYSNR','00'),
    client=os.environ.get('SAP_CLIENT','350'),
    user=os.environ.get('SAP_USER','jp_lopez'),
    passwd=os.environ.get('SAP_PASSWORD',''),
)

def build_opts(where, ml=72):
    words, lines, cur = where.split(' '), [], ''
    for w in words:
        c = (cur+' '+w).strip()
        if len(c) <= ml: cur = c
        else:
            if cur: lines.append({'TEXT': cur})
            cur = w
    if cur: lines.append({'TEXT': cur})
    return lines

def rfc_read(conn, table, where, fields, maxr=200):
    try:
        r = conn.call('RFC_READ_TABLE',
            QUERY_TABLE=table, DELIMITER='|', ROWSKIPS=0, ROWCOUNT=maxr,
            FIELDS=[{'FIELDNAME':f} for f in fields], OPTIONS=build_opts(where))
        out = []
        for row in r.get('DATA',[]):
            parts = [p.strip() for p in row['WA'].split('|')]
            out.append(dict(zip(fields, parts+['']*(len(fields)-len(parts)))))
        return out
    except Exception as e:
        print(f'  RFC error: {e}')
        return []

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

all_pkgs = sorted(set(v.get('package','') for v in cfg.values()
                       if v.get('package','') and re.match(r'^[A-Z0-9_/]{1,30}$', v.get('package',''))))
print(f'Unique valid packages: {len(all_pkgs)}')

conn = pyrfc.Connection(**CONN)
print('RFC connected')

# Try TDEVCT first (language-dependent package texts)
BATCH = 5
pkg_desc = {}
print('Querying TDEVCT...')
for i in range(0, len(all_pkgs), BATCH):
    batch = all_pkgs[i:i+BATCH]
    or_clause = ' OR '.join(f"DEVCLASS = '{p}'" for p in batch)
    rows = rfc_read(conn, 'TDEVCT', f"SPRAS = 'E' AND ( {or_clause} )", ['DEVCLASS','CTEXT'], maxr=BATCH+2)
    for r in rows:
        k = r.get('DEVCLASS','').strip()
        t = r.get('CTEXT','').strip()
        if k and t: pkg_desc[k] = t

print(f'TDEVCT: {len(pkg_desc)} descriptions')

# If still 0, try TDEVC directly (some systems store it there)
if not pkg_desc:
    print('Trying TDEVC...')
    for i in range(0, min(len(all_pkgs),50), BATCH):
        batch = all_pkgs[i:i+BATCH]
        or_clause = ' OR '.join(f"DEVCLASS = '{p}'" for p in batch)
        rows = rfc_read(conn, 'TDEVC', f"( {or_clause} )", ['DEVCLASS','CTEXT'], maxr=BATCH+2)
        for r in rows:
            k = r.get('DEVCLASS','').strip()
            t = r.get('CTEXT','').strip()
            if k and t: pkg_desc[k] = t
    print(f'TDEVC: {len(pkg_desc)}')

conn.close()

print('\nSample package descriptions:')
for p,d in list(pkg_desc.items())[:20]:
    print(f'  {p:<30} {d}')

# Add pkg_desc to cfg objects
for name, v in cfg.items():
    pkg = v.get('package','')
    if pkg and pkg in pkg_desc:
        v['pkg_desc'] = pkg_desc[pkg]
    elif 'pkg_desc' in v:
        del v['pkg_desc']

with open('cts_config_detail.json','w',encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)
with open('cts_pkg_descriptions.json','w',encoding='utf-8') as f:
    json.dump(pkg_desc, f, ensure_ascii=False)

print(f'pkg_desc assigned: {sum(1 for v in cfg.values() if v.get("pkg_desc"))}')

# ── Re-inject + JS patch ──────────────────────────────────────────────────────
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# Re-inject CFGDETAIL
NEW_CFG = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
s = html.find('const CFGDETAIL='); e = html.find(';\n', s)+2
html = html[:s] + NEW_CFG + html[e:]
print('Re-injected CFGDETAIL')

# ── JS Patch 1: Show pkg description under package code ──────────────────────
# In the row template, pkg cell currently shows:
#   <code>${pkg}</code><div>${mod}</div>
# Add pkg_desc under it
OLD_PKG_CELL = (
    '${pkg ? `<code style="font-size:.7rem;color:#e2e8f0;font-weight:600">'
    '${pkg}</code>` : \'\'}\n'
    '          <div style="font-size:.6rem;padding:1px 5px;border-radius:4px;'
    'background:${modCol}20;color:${modCol};display:inline-block;margin-top:2px">'
    '${mod}</div>'
)
NEW_PKG_CELL = (
    '${pkg ? `<code style="font-size:.7rem;color:#e2e8f0;font-weight:600">'
    '${pkg}</code>` : \'\'}\n'
    '          ${c.pkg_desc ? `<div style="font-size:.58rem;color:var(--mu2);'
    'line-height:1.2;margin-top:1px;max-width:160px;overflow:hidden;text-overflow:ellipsis;'
    'white-space:nowrap">${c.pkg_desc}</div>` : \'\'}\n'
    '          <div style="font-size:.6rem;padding:1px 5px;border-radius:4px;'
    'background:${modCol}20;color:${modCol};display:inline-block;margin-top:2px">'
    '${mod}</div>'
)
if OLD_PKG_CELL in html:
    html = html.replace(OLD_PKG_CELL, NEW_PKG_CELL, 1)
    print('Added pkg_desc under package code')
else:
    print('WARNING: pkg cell pattern not matched — skipping pkg_desc display patch')

# ── JS Patch 2: Fix year filtering ───────────────────────────────────────────
# Find the year filter chip click handler in Config section
# Add a year-filter event after the year chip buttons are rendered
# Look for where cfgActiveYear is set / year chips are clicked
YEAR_FILTER_JS = """
// Config year filter logic
window._cfgYear = 'all';
function setCfgYear(yr, el) {
  window._cfgYear = yr;
  document.querySelectorAll('.cfg-yr-btn').forEach(b => b.classList.remove('active'));
  if (el) el.classList.add('active');
  document.querySelectorAll('.cfg-obj-row').forEach(row => {
    if (yr === 'all') {
      row.style.display = '';
    } else {
      try {
        var years = JSON.parse(row.dataset.years || '[]');
        row.style.display = years.includes(yr) ? '' : 'none';
      } catch(e) { row.style.display = ''; }
    }
  });
  // Update row count labels
  document.querySelectorAll('[data-cfg-count]').forEach(el => {
    var panel = el.closest('.cc');
    if (!panel) return;
    var visible = panel.querySelectorAll('.cfg-obj-row:not([style*="display: none"]):not([style*="display:none"])').length;
    el.textContent = visible + ' objects';
  });
}
"""

# Insert before </script> near end of file
if 'setCfgYear' not in html:
    script_end = html.rfind('</script>')
    html = html[:script_end] + YEAR_FILTER_JS + '\n' + html[script_end:]
    print('Added setCfgYear() JS function')

# ── JS Patch 3: Fix year chip buttons to call setCfgYear ─────────────────────
# Find year chip onClick handlers in the config section and update them
# Current chips likely call something different or nothing  
# Pattern: onclick="..." for year badges in config
html = re.sub(
    r'onclick="(filterCfg|setCfgFilter|cfgYearFilter)\(([^)]+)\)"',
    r'onclick="setCfgYear(\2, this)"', html
)

# ── JS Patch 4: Replace slice(0,100) + moreNote with Load More ───────────────
OLD_SLICE = "const rows = items.slice(0,100).map(c => {"
NEW_SLICE = "const rows = items.map(c => {"           # show ALL rows

OLD_MORE = (
    "const moreNote = items.length > 50\n"
    "      ? `<tr><td colspan=\"7\" style=\"text-align:center;color:var(--mu);font-size:.7rem;padding:8px\">+ ${items.length-50} more objects in this group</td></tr>`\n"
    "      : '';"
)
NEW_MORE = "const moreNote = '';"   # remove cap entirely

if OLD_SLICE in html:
    html = html.replace(OLD_SLICE, NEW_SLICE, 1)
    print('Removed slice(0,100) cap — all rows now rendered')
else:
    print('WARNING: slice pattern not found')

if OLD_MORE in html:
    html = html.replace(OLD_MORE, NEW_MORE, 1)
    print('Removed "+N more objects" note')
else:
    print('WARNING: moreNote pattern not found')

with open('cts_dashboard.html','w',encoding='utf-8') as f:
    f.write(html)
print(f'Done! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
