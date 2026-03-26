"""
fix_all.py
1. Fix sidebar toggle button position
2. Auto-generate descriptions for ALL remaining objects without desc
3. Re-inject CFGDETAIL into dashboard
"""
import json, os, re

# ── Load data ─────────────────────────────────────────────────────────────────
with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# ── Auto-generate descriptions for still-missing objects ──────────────────────
def auto_desc(name, obj_type, type_label, module, package):
    """Generate a description from naming patterns when SAP lookup has no entry."""
    n = name.upper()

    # VARX: format is often PROGRAMNAME_VARIANT  → "Variant for <program>"
    if obj_type == 'VARX':
        parts = name.rsplit('_', 1)
        prog = parts[0] if len(parts) == 2 else name
        return f'Report variant for {prog}'

    # SOTT: OTR texts keyed by package
    if obj_type == 'SOTT':
        pkg = package.strip('/')
        return f'UI translation texts ({pkg})'

    # LODE: HR logical data object — derive from name suffix
    if obj_type == 'LODE':
        suffix = name.replace('LODE', '', 1).lstrip('_').replace('_', ' ').title()
        return f'HR data object: {suffix}' if suffix else 'HR logical data object'

    # TTYP: strip known prefix patterns
    if obj_type == 'TTYP':
        clean = name.replace('_', ' ').title()
        return f'Accounting obj type: {clean}'

    # OSOA: BW DataSource names are usually functional
    if obj_type == 'OSOA':
        clean = name.replace('_', ' ').title()
        return f'BW DataSource: {clean}'

    # SCVI: Screen variant
    if obj_type == 'SCVI':
        program = name.split('_')[0] if '_' in name else name
        return f'Screen variant for {program}'

    # AVAS / PMKC: classification / characteristics
    if obj_type in ('AVAS', 'PMKC'):
        return f'Classification attribute: {name}'

    # LODC / SOTU
    if obj_type == 'LODC':
        return f'Lock object customizing: {name}'
    if obj_type == 'SOTU':
        return f'Sort object texts: {name}'

    # CUAD / CUS0 / CUS1: use module as hint
    if obj_type in ('CUAD', 'CUS0', 'CUS1'):
        mod_hint = module.split('(')[0].strip() if module else 'General'
        return f'{mod_hint} customizing activity'

    # TABD / TABT: table definition
    if obj_type in ('TABD', 'TABT'):
        return f'Table definition: {name}'

    # Generic fallback: prettify name
    clean = name.replace('_', ' ').title()
    return f'{type_label}: {clean}'

filled = 0
for name, v in cfg.items():
    if not v.get('desc', '').strip():
        v['desc'] = auto_desc(
            name,
            v.get('obj_type', ''),
            v.get('type_label', 'Config Object'),
            v.get('module', ''),
            v.get('package', ''),
        )
        filled += 1

total_with_desc = sum(1 for v in cfg.values() if v.get('desc', '').strip())
print(f'Auto-filled: {filled} | Total with desc: {total_with_desc}/{len(cfg)} (100%)')

with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

# ── Load dashboard ────────────────────────────────────────────────────────────
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# ── Fix 1: Remove ALL misplaced/duplicate toggle buttons ─────────────────────
BTN_PATTERN = re.compile(r'<button\s+[^>]*onclick="toggleSidebar\(\)"[^>]*>.*?</button>', re.DOTALL)
matches = BTN_PATTERN.findall(html)
print(f'Found {len(matches)} existing button(s) — removing all')
html = BTN_PATTERN.sub('', html)

# ── Fix 2: Insert button ONCE inside the topbar (as last flex child) ──────────
# Find where topbar ends by locating its closing tag before <div class="shell">
# Use a tight pattern around the logo block end
TOPBAR_CLOSE = html.find('</div>', html.find('class="topbar"'))
# Walk forward to find the actual closing tag of topbar (skip nested divs)
depth = 1
pos = html.find('class="topbar"') + 1
while depth > 0 and pos < len(html):
    next_open  = html.find('<div', pos)
    next_close = html.find('</div>', pos)
    if next_open != -1 and next_open < next_close:
        depth += 1
        pos = next_open + 1
    elif next_close != -1:
        depth -= 1
        if depth == 0:
            TOPBAR_CLOSE = next_close
        pos = next_close + 1
    else:
        break

CLEAN_BTN = (
    '\n  <button id="sb-toggle" onclick="toggleSidebar()" '
    'title="Collapse menu" '
    'style="margin-left:auto;background:rgba(79,142,247,.1);'
    'border:1px solid rgba(79,142,247,.25);color:#4f8ef7;'
    'border-radius:8px;padding:6px 14px;cursor:pointer;'
    'font-size:.75rem;align-self:center;flex-shrink:0;'
    'display:flex;align-items:center;gap:5px;white-space:nowrap">'
    '<span id="sb-ico">\u25c4</span>&nbsp;'
    '<span id="sb-lbl">Collapse</span>'
    '</button>'
)
html = html[:TOPBAR_CLOSE] + CLEAN_BTN + html[TOPBAR_CLOSE:]
print('Inserted toggle button inside topbar')

# ── Fix 3: Ensure topbar is flex ─────────────────────────────────────────────
if '.topbar{' in html:
    tb_start = html.find('.topbar{')
    tb_end   = html.find('}', tb_start)
    topbar_css = html[tb_start:tb_end]
    if 'display:flex' not in topbar_css:
        html = html[:tb_start+8] + 'display:flex;align-items:center;' + html[tb_start+8:]
        print('Added display:flex to .topbar CSS')

# ── Fix 4: Re-inject enriched CFGDETAIL ──────────────────────────────────────
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
s = html.find('const CFGDETAIL='); e = html.find(';\n', s)+2
html = html[:s] + NEW_CFG_JS + html[e:]
print('Re-injected CFGDETAIL (all objects now have descriptions)')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Done! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
