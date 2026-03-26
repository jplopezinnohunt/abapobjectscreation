"""
patch_module_yearfilter.py
1. Re-injects enriched cts_config_detail.json (now has 'module' field) into the dashboard
2. Patches the sparkline/detail row template to add Module column
3. Adds a year filter bar above each group drilldown table
"""
import json, re, os

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg_detail = json.load(f)

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# ── 1. Replace the CFGDETAIL data block ───────────────────────────────────────
NEW_CFG_JS = 'const CFGDETAIL=' + json.dumps(cfg_detail, separators=(',',':'), ensure_ascii=False) + ';\n'

# Find and replace existing CFGDETAIL
start = html.find('const CFGDETAIL=')
end   = html.find(';\n', start) + 2
if start == -1:
    print('CFGDETAIL not found!')
    raise SystemExit(1)
html = html[:start] + NEW_CFG_JS + html[end:]
print('Replaced CFGDETAIL data block')

# ── 2. Replace the sparkline row template + header to add Module column ────────
OLD_ROWS_TEMPLATE = """    const rows = items.slice(0,50).map(c => {
      const pct = totalMods > 0 ? (c.total_mods/totalMods*100).toFixed(1) : 0;
      const sp  = sparkline(c, maxMods, g.color);
      const usrs= (c.users||[]).join(', ').toLowerCase().replace(/_/g,' ') || '\u2014';
      return `<tr>
        <td style="padding-left:16px"><code style="color:${g.color}">${c.name}</code></td>
        <td><code style="font-size:.64rem;color:var(--mu2)">${c.obj_type}</code></td>
        <td>
          <div style="display:flex;align-items:center;gap:6px">
            ${sp}
            <span style="font-family:'JetBrains Mono',monospace;font-size:.7rem;color:${g.color}">${c.total_mods}x</span>
          </div>
        </td>
        <td style="font-size:.7rem;color:var(--mu)">${c.user_count||0}</td>
        <td style="font-size:.68rem;color:var(--mu2)">${c.first_seen||''}\u2013${c.last_seen||''}</td>
        <td style="font-size:.65rem;color:var(--mu);max-width:180px;overflow:hidden;text-overflow:ellipsis">${usrs}</td>
        <td style="font-size:.68rem;color:var(--mu)">${pct}%</td>
      </tr>`;
    }).join('');"""

NEW_ROWS_TEMPLATE = """    const rows = items.slice(0,100).map(c => {
      const pct = totalMods > 0 ? (c.total_mods/totalMods*100).toFixed(1) : 0;
      const sp  = sparkline(c, maxMods, g.color);
      const usrs= (c.users||[]).slice(0,4).join(', ').toLowerCase().replace(/_/g,' ') || '\u2014';
      const mod = c.module || 'General IMG';
      const modCol = MOD_COLOR[mod.split(' ')[0]] || '#64748b';
      return `<tr class="cfg-obj-row" data-years='${JSON.stringify(c.years_active||[])}'>
        <td style="padding-left:16px"><code style="color:${g.color}">${c.name}</code></td>
        <td><code style="font-size:.64rem;color:var(--mu2)">${c.obj_type}</code></td>
        <td><span style="font-size:.65rem;padding:1px 6px;border-radius:5px;background:${modCol}22;color:${modCol}">${mod}</span></td>
        <td>
          <div style="display:flex;align-items:center;gap:6px">
            ${sp}
            <span style="font-family:'JetBrains Mono',monospace;font-size:.7rem;color:${g.color}">${c.total_mods}x</span>
          </div>
        </td>
        <td style="font-size:.7rem;color:var(--mu)">${c.user_count||0}</td>
        <td style="font-size:.68rem;color:var(--mu2)">${c.first_seen||''}\u2013${c.last_seen||''}</td>
        <td style="font-size:.65rem;color:var(--mu);max-width:160px;overflow:hidden;text-overflow:ellipsis">${usrs}</td>
      </tr>`;
    }).join('');"""

if OLD_ROWS_TEMPLATE in html:
    html = html.replace(OLD_ROWS_TEMPLATE, NEW_ROWS_TEMPLATE, 1)
    print('Patched row template — added Module column')
else:
    print('Row template not found — searching...')
    idx = html.find('cfg-obj-row')
    print(f'  cfg-obj-row already at {idx}')

# ── 3. Update table header to add Module column ────────────────────────────────
OLD_THEAD = '<thead><tr>\n              <th>Table / View</th><th>Type</th><th style="min-width:130px">Mods (2017\u21922026 \u25b0)</th>\n              <th>Users</th><th>Active</th><th>Contributors</th><th>% of group</th>\n            </tr></thead>'
NEW_THEAD = '<thead><tr>\n              <th>Table / View</th><th>Type</th><th>Module (inferred)</th><th style="min-width:130px">Mods (2017\u21922026 \u25b0)</th>\n              <th>Users</th><th>Active</th><th>Contributors</th>\n            </tr></thead>'

if OLD_THEAD in html:
    html = html.replace(OLD_THEAD, NEW_THEAD, 1)
    print('Updated table header')

# ── 4. Add year filter bar + MOD_COLOR constant + filter function ─────────────
YEAR_FILTER_JS = r"""
// ── CONFIG year filter ────────────────────────────────────────────────────────
const MOD_COLOR = {
  'HCM-PY':   '#a78bfa', 'HCM/Config': '#c084fc', 'HCM-PA':   '#d8b4fe',
  'HCM-OM':   '#e9d5ff', 'HCM':        '#b197fc',
  'FI/CO':    '#f59e0b', 'FI':         '#fbbf24', 'CO':        '#fcd34d',
  'CO-PA':    '#f59e0b', 'PSM/FM':     '#86efac',
  'BC-Sec':   '#ef4444', 'BC-IMG':     '#475569', 'BC-Basis':  '#64748b',
  'BC-NR':    '#475569', 'BC-WF':      '#34d399', 'BC-Payroll':'#94a3b8',
  'MDG':      '#38bdf8', 'MM':         '#fb923c', 'SD':        '#f97316',
  'General':  '#475569', 'HR/Payroll': '#b197fc', 'PP/PM':     '#6ee7b7',
};

function buildYearFilter(panelId, color) {
  const YEARS = ['2017','2018','2019','2020','2021','2022','2023','2024','2025','2026'];
  let active = null;
  const bar = document.createElement('div');
  bar.style.cssText = 'display:flex;gap:4px;flex-wrap:wrap;padding:8px 16px;border-bottom:1px solid var(--b);background:var(--surf)';

  // All button
  const allBtn = document.createElement('button');
  allBtn.textContent = 'All years';
  allBtn.style.cssText = `padding:3px 10px;border-radius:12px;font-size:.7rem;cursor:pointer;border:1px solid ${color};background:${color};color:#fff;font-weight:600`;
  allBtn.onclick = () => {
    active = null;
    updateFilter(panelId, null);
    allBtn.style.background = color;
    allBtn.style.color = '#fff';
    yearBtns.forEach(b => { b.style.background = 'transparent'; b.style.color = color; });
  };
  bar.appendChild(allBtn);

  const yearBtns = YEARS.map(yr => {
    const btn = document.createElement('button');
    btn.textContent = yr;
    btn.dataset.yr = yr;
    btn.style.cssText = `padding:3px 9px;border-radius:12px;font-size:.7rem;cursor:pointer;border:1px solid ${color}55;background:transparent;color:${color};transition:.1s`;
    btn.onclick = () => {
      active = yr;
      updateFilter(panelId, yr);
      allBtn.style.background = 'transparent';
      allBtn.style.color = color;
      yearBtns.forEach(b => {
        const sel = b.dataset.yr === yr;
        b.style.background = sel ? color : 'transparent';
        b.style.color = sel ? '#fff' : color;
        b.style.borderColor = sel ? color : color+'55';
      });
    };
    bar.appendChild(btn);
    return btn;
  });
  return bar;
}

function updateFilter(panelId, yr) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  panel.querySelectorAll('.cfg-obj-row').forEach(row => {
    if (!yr) { row.style.display = ''; return; }
    let years = [];
    try { years = JSON.parse(row.dataset.years || '[]'); } catch(e){}
    row.style.display = years.includes(yr) ? '' : 'none';
  });
  // Update visible count
  const info = panel.querySelector('.yr-count');
  if (info) {
    const vis = panel.querySelectorAll('.cfg-obj-row:not([style*="none"])').length;
    const tot = panel.querySelectorAll('.cfg-obj-row').length;
    info.textContent = yr ? vis + ' of ' + tot + ' objects active in ' + yr : tot + ' objects';
  }
}
"""

# Insert before the buildConfig function
INSERT_BEFORE = '// ── CONFIG ELEMENTS (Grouped + Drilldown) ─────────────────────────────────────'
if INSERT_BEFORE in html:
    html = html.replace(INSERT_BEFORE, YEAR_FILTER_JS + '\n' + INSERT_BEFORE, 1)
    print('Added year filter JS + MOD_COLOR constants')

# ── 5. Wire year filter into each group panel rendering ───────────────────────
# Find where each panel's drilldown div is inserted and add year filter bar before the table
OLD_PANEL = """      <!-- DRILLDOWN PANEL \u2014 hidden by default -->
      <div id="${panelId}" style="display:none">
        <div style="overflow-x:auto">
          <table class="tbl">"""

NEW_PANEL = """      <!-- DRILLDOWN PANEL \u2014 hidden by default -->
      <div id="${panelId}" style="display:none">
        <div id="${panelId}-yf-mount"></div>
        <div style="padding:4px 16px 4px;font-size:.68rem;color:var(--mu)"><span class="yr-count">${items.length} objects</span></div>
        <div style="overflow-x:auto">
          <table class="tbl">"""

if OLD_PANEL in html:
    html = html.replace(OLD_PANEL, NEW_PANEL)
    print('Added year filter mount point in panels')

# ── 6. Call buildYearFilter after toggleCfgGroup opens a panel ────────────────
OLD_TOGGLE = """function toggleCfgGroup(panelId, header) {
  const panel = document.getElementById(panelId);
  const arrow = document.getElementById(panelId+'-arrow');
  if (!panel) return;
  const isOpen = panel.style.display !== 'none';
  panel.style.display = isOpen ? 'none' : 'block';
  if (arrow) arrow.textContent = isOpen ? '\u25b6' : '\u25bc';
  header.style.borderBottomColor = isOpen ? 'transparent' : 'var(--b)';
}"""

NEW_TOGGLE = """function toggleCfgGroup(panelId, header) {
  const panel = document.getElementById(panelId);
  const arrow = document.getElementById(panelId+'-arrow');
  if (!panel) return;
  const isOpen = panel.style.display !== 'none';
  panel.style.display = isOpen ? 'none' : 'block';
  if (arrow) arrow.textContent = isOpen ? '\u25b6' : '\u25bc';
  header.style.borderBottomColor = isOpen ? 'transparent' : 'var(--b)';
  // Build year filter if not yet done
  if (!isOpen) {
    const mount = document.getElementById(panelId+'-yf-mount');
    if (mount && !mount.dataset.built) {
      mount.dataset.built = '1';
      const color = header.querySelector('[style*="color:"]')?.style?.color ||
                    header.querySelector('strong')?.style?.color || '#4f8ef7';
      const bar = buildYearFilter(panelId, color);
      mount.appendChild(bar);
    }
  }
}"""

if OLD_TOGGLE in html:
    html = html.replace(OLD_TOGGLE, NEW_TOGGLE)
    print('Patched toggleCfgGroup to mount year filter on first open')
else:
    print('toggleCfgGroup not found as expected')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'\nDone! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
