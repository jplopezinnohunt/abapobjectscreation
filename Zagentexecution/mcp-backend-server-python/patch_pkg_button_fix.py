"""
patch_pkg_button_fix.py
1. Re-injects enriched CFGDETAIL (now has 'package' field)
2. Adds Package column to the config drilldown row template
3. Fixes toggle button position (inside topbar flex, right-aligned)
4. Adds page description to Config Elements page header
"""
import json, os

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# 1. Re-inject CFGDETAIL
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
start = html.find('const CFGDETAIL=')
end   = html.find(';\n', start) + 2
html  = html[:start] + NEW_CFG_JS + html[end:]
print('Re-injected CFGDETAIL with package field')

# 2. Add Package to module badge cell
OLD_MOD_CELL = """      const mod = c.module || 'General IMG';
      const modCol = MOD_COLOR[mod.split(' ')[0]] || '#64748b';
      return `<tr class="cfg-obj-row" data-years='${JSON.stringify(c.years_active||[])}'>
        <td style="padding-left:16px">
          <code style="color:${g.color}">${c.name}</code>
          ${c.desc ? `<div style="font-size:.62rem;color:var(--mu2);margin-top:2px">${c.desc}</div>` : ''}
        </td>
        <td><code style="font-size:.64rem;color:var(--mu2)">${c.obj_type}</code></td>
        <td><span style="font-size:.65rem;padding:1px 6px;border-radius:5px;background:${modCol}22;color:${modCol}">${mod}</span></td>"""

NEW_MOD_CELL = """      const mod = c.module || 'General IMG';
      const pkg = c.package || '';
      const modCol = MOD_COLOR[mod.split(' ')[0]] || '#64748b';
      const pkgShort = pkg.replace(/\\(.*\\)/,'').trim();
      return `<tr class="cfg-obj-row" data-years='${JSON.stringify(c.years_active||[])}'>
        <td style="padding-left:16px">
          <code style="color:${g.color}">${c.name}</code>
          ${c.desc ? `<div style="font-size:.62rem;color:var(--mu2);margin-top:2px">${c.desc}</div>` : ''}
        </td>
        <td><code style="font-size:.64rem;color:var(--mu2)">${c.obj_type}</code></td>
        <td>
          <span style="font-size:.65rem;padding:1px 6px;border-radius:5px;background:${modCol}22;color:${modCol}">${mod}</span>
          ${pkg ? `<div style="font-size:.6rem;color:var(--mu2);margin-top:2px;font-family:'JetBrains Mono',monospace">${pkgShort}</div>` : ''}
        </td>"""

if OLD_MOD_CELL in html:
    html = html.replace(OLD_MOD_CELL, NEW_MOD_CELL, 1)
    print('Added Package sub-line under Module column')
else:
    print('WARNING: Module cell pattern not found')

# 3. Fix toggle button — replace mispositioned button with one inside the topbar flex properly
# The button currently sits outside the topbar wrapper div — move it inside the topbar
# as a flex child on the right side
OLD_BTN = """<button onclick="toggleSidebar()" id="sb-toggle"
  style="background:rgba(79,142,247,.12);border:1px solid rgba(79,142,247,.25);
         color:var(--acc);border-radius:6px;padding:4px 10px;cursor:pointer;
         font-size:.78rem;display:flex;align-items:center;gap:5px;margin-left:8px">
  <span id="sb-ico">\u25c4</span> <span id="sb-lbl">Hide</span>
</button>
</div>
<div class="shell">"""

NEW_BTN = """</div>
<div class="shell">"""

if OLD_BTN in html:
    html = html.replace(OLD_BTN, NEW_BTN, 1)
    print('Removed mispositioned button from after topbar')

# Now insert the toggle button properly INSIDE the topbar as a flex item
# The topbar has: logo-block | stats-block  — add: | toggle-button on right
# Find the topbar closing tag
OLD_TOPBAR = '<div class="topbar">'
topbar_start = html.find(OLD_TOPBAR)
topbar_end   = html.find('</div>\n<div class="shell">', topbar_start)

# Extract topbar content
topbar_html = html[topbar_start:topbar_end + 6]  # up to first </div>

# Insert button at end of topbar div (before closing </div>)
TOGGLE_BTN_HTML = """  <button onclick="toggleSidebar()" id="sb-toggle"
    style="margin-left:auto;background:rgba(79,142,247,.08);border:1px solid rgba(79,142,247,.2);
           color:var(--acc);border-radius:6px;padding:5px 12px;cursor:pointer;
           font-size:.75rem;display:flex;align-items:center;gap:4px;flex-shrink:0;
           align-self:center;white-space:nowrap">
    <span id="sb-ico">\u25c4</span>&nbsp;<span id="sb-lbl">Collapse</span>
  </button>
"""

# Insert toggle before the closing div of topbar
insert_pos = topbar_end
html = html[:insert_pos] + TOGGLE_BTN_HTML + html[insert_pos:]
print('Inserted toggle button inside topbar flex layout')

# 4. Fix toggleSidebar to handle width-based collapse so layout reflows correctly
OLD_SB_FN = """function toggleSidebar() {
  const sb  = document.querySelector('.sidebar');
  const ico = document.getElementById('sb-ico');
  const lbl = document.getElementById('sb-lbl');
  const open = sb.style.display !== 'none';
  sb.style.display = open ? 'none' : '';
  ico.textContent  = open ? '\u25b6' : '\u25c4';
  lbl.textContent  = open ? 'Menu' : 'Hide';
}"""

NEW_SB_FN = """function toggleSidebar() {
  const sb   = document.querySelector('.sidebar');
  const main = document.querySelector('.main-content') || document.querySelector('.content');
  const ico  = document.getElementById('sb-ico');
  const lbl  = document.getElementById('sb-lbl');
  const open = !sb.dataset.collapsed;
  if (open) {
    sb.dataset.collapsed = '1';
    sb.style.width = '0';
    sb.style.minWidth = '0';
    sb.style.overflow = 'hidden';
    sb.style.padding = '0';
    if (main) main.style.flex = '1 1 100%';
    ico.textContent = '\u25b6';
    lbl.textContent = 'Menu';
  } else {
    delete sb.dataset.collapsed;
    sb.style.width = '';
    sb.style.minWidth = '';
    sb.style.overflow = '';
    sb.style.padding = '';
    if (main) main.style.flex = '';
    ico.textContent = '\u25c4';
    lbl.textContent = 'Collapse';
  }
}"""

if OLD_SB_FN in html:
    html = html.replace(OLD_SB_FN, NEW_SB_FN, 1)
    print('Fixed toggleSidebar() to use width-collapse instead of display:none')
else:
    # Try to find and replace by function name
    fn_start = html.find('function toggleSidebar()')
    if fn_start != -1:
        fn_end = html.find('\n}', fn_start) + 2
        html = html[:fn_start] + NEW_SB_FN + html[fn_end:]
        print('Replaced toggleSidebar() (pattern fallback)')
    else:
        print('WARNING: toggleSidebar not found')

# 5. Add sidebar transition CSS
OLD_CSS_SIDEBAR = '.sidebar{'
if OLD_CSS_SIDEBAR in html:
    html = html.replace(OLD_CSS_SIDEBAR,
        '.sidebar{transition:width .25s ease,min-width .25s ease,padding .25s ease;',
        1)
    print('Added transition to sidebar CSS')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nDone! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
