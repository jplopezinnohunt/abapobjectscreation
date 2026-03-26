"""
rebuild_module_view.py
Replaces the hardcoded CFG_GROUPS config view with a dynamic:
  Module → Package → Objects drill-down.
Rendered lazily (table only built when module expanded).
"""
import json, os
from collections import defaultdict, Counter

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# Build summary per module → package
mod_data = defaultdict(list)
for name, v in cfg.items():
    mod = v.get('module') or 'General IMG'
    mod_data[mod].append({'name': name, **v})

# Sort modules: specific ones first, General IMG last
def mod_order(mod):
    if mod == 'General IMG': return (1, 0)
    return (0, -len(mod_data[mod]))

sorted_mods = sorted(mod_data.keys(), key=mod_order)

print('Module summary:')
for mod in sorted_mods:
    items = mod_data[mod]
    pkgs = Counter(v.get('package','') for v in items)
    mods_sum = sum(v.get('total_mods',0) for v in items)
    print(f'  {mod}: {len(items)} objects, {mods_sum} mods, {len(pkgs)} packages')

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# Build the JS for the new module view
NEW_JS = r"""
// ═══════════════════════════════════════════════════════
// CONFIG BY MODULE → PACKAGE VIEW
// ═══════════════════════════════════════════════════════
const CONTENT_TYPES_SET = new Set(['TABU','TDAT','CDAT','DATED']);

function buildConfigByModule() {
  const ct = document.getElementById('cfg-ct');
  if (!ct) return;
  ct.innerHTML = '';

  // Group all CFGDETAIL by module
  const byModule = {};
  Object.entries(CFGDETAIL).forEach(([name, v]) => {
    const mod = v.module || 'General IMG';
    if (!byModule[mod]) byModule[mod] = [];
    byModule[mod].push({name, ...v});
  });

  // Sort modules: specific before general, by obj count
  const modOrder = (m) => m === 'General IMG' ? 1e9 : -byModule[m].length;
  const mods = Object.keys(byModule).sort((a,b) => modOrder(a) - modOrder(b));

  // Module colors
  const MOD_COLORS = {
    'HCM-PY (Payroll)':    '#a78bfa',
    'HCM/Config View':     '#c084fc',
    'HCM-PA (Personnel Admin)': '#e879f9',
    'FI/CO Config View':   '#38bdf8',
    'FI (Finance)':        '#60a5fa',
    'FI (Accounts)':       '#93c5fd',
    'CO (Controlling)':    '#34d399',
    'CO-PA (Profitability)':'#6ee7b7',
    'PSM/FM':              '#f59e0b',
    'BC-Sec / User Mgmt':  '#f87171',
    'BC-Sec / Auth':       '#fca5a5',
    'BC-IMG (Cust Tree)':  '#94a3b8',
    'BC-Payroll Post':     '#c4b5fd',
    'BC-NR (Number Ranges)':'#a5b4fc',
    'MM (Procurement)':    '#fb923c',
    'MDG':                 '#facc15',
    'General IMG':         '#64748b',
  };

  mods.forEach(mod => {
    const items = byModule[mod];
    items.sort((a,b) => b.total_mods - a.total_mods);
    const color = MOD_COLORS[mod] || '#64748b';
    const totalMods = items.reduce((s,c) => s+c.total_mods, 0);

    // Package summary for this module
    const pkgMap = {};
    items.forEach(c => {
      const p = c.package || '(no pkg)';
      if (!pkgMap[p]) pkgMap[p] = {count:0, mods:0, desc: c.pkg_desc||''};
      pkgMap[p].count++;
      pkgMap[p].mods += c.total_mods;
    });
    const pkgs = Object.entries(pkgMap).sort((a,b) => b[1].count - a[1].count);

    const modId = 'mod-' + mod.replace(/[^a-z0-9]/gi,'_');
    const isFirst = mod === mods[0];

    const card = document.createElement('div');
    card.className = 'cc module-card';
    card.style.cssText = 'border-radius:12px;overflow:hidden;background:rgba(15,23,42,.6);border:1px solid rgba(255,255,255,.07);margin-bottom:12px';

    card.innerHTML = `
      <div class="module-hdr" onclick="toggleModuleCard('${modId}')"
           style="padding:16px 20px;cursor:pointer;display:flex;align-items:center;gap:16px;background:rgba(0,0,0,.2)">
        <div style="width:3px;height:40px;background:${color};border-radius:2px;flex-shrink:0"></div>
        <div style="flex:1;min-width:0">
          <div style="font-size:.95rem;font-weight:700;color:#f1f5f9">${mod}</div>
          <div style="font-size:.7rem;color:var(--mu);margin-top:2px">${items.length.toLocaleString()} objects · ${totalMods.toLocaleString()} modifications · ${pkgs.length} packages</div>
        </div>
        <div style="display:flex;gap:20px;align-items:center">
          <div style="text-align:right">
            <div style="font-size:1.4rem;font-weight:800;color:${color}">${items.length.toLocaleString()}</div>
            <div style="font-size:.62rem;color:var(--mu);letter-spacing:.05em">OBJECTS</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:1.1rem;font-weight:700;color:#94a3b8">${totalMods.toLocaleString()}</div>
            <div style="font-size:.62rem;color:var(--mu);letter-spacing:.05em">MODS</div>
          </div>
          <div id="${modId}-arrow" style="color:var(--mu);font-size:1rem;transition:.2s">${isFirst ? '▼' : '▶'}</div>
        </div>
      </div>
      <div id="${modId}-body" style="display:${isFirst?'block':'none'}">
        <!-- Package pills -->
        <div id="${modId}-pills" style="padding:12px 20px 8px;display:flex;flex-wrap:wrap;gap:6px;border-bottom:1px solid rgba(255,255,255,.05)">
          <button class="pkg-pill active" onclick="filterModPkg('${modId}','',this)"
            style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#f1f5f9;
            border-radius:20px;padding:3px 12px;cursor:pointer;font-size:.7rem;font-family:inherit">
            All (${items.length})
          </button>
          ${pkgs.slice(0,40).map(([pkg,info]) => `
          <button class="pkg-pill" onclick="filterModPkg('${modId}','${pkg}',this)"
            title="${info.desc}"
            style="background:rgba(${color.replace('#','').match(/.{2}/g).map(h=>parseInt(h,16)).join(',')}, .12);
            border:1px solid rgba(${color.replace('#','').match(/.{2}/g).map(h=>parseInt(h,16)).join(',')}, .3);
            color:${color};border-radius:20px;padding:3px 12px;cursor:pointer;font-size:.7rem;font-family:inherit">
            ${pkg} <span style="opacity:.6">${info.count}</span>
          </button>`).join('')}
        </div>
        <!-- Object table (lazy-rendered) -->
        <div id="${modId}-tbl" data-items='${JSON.stringify(items.map(c=>c.name))}' data-rendered="0"
             style="max-height:600px;overflow-y:auto">
          <div style="padding:20px;text-align:center;color:var(--mu);font-size:.8rem">Click to load objects...</div>
        </div>
      </div>
    `;
    ct.appendChild(card);

    // Auto-render first module
    if (isFirst) renderModTable(modId, items, '');
  });
}

// ── Render object table for a module ─────────────────────────────────────────
function renderModTable(modId, items, pkgFilter) {
  const tbl = document.getElementById(modId + '-tbl');
  if (!tbl) return;
  const filtered = pkgFilter ? items.filter(c => (c.package||'(no pkg)') === pkgFilter) : items;
  const YEARS = ['2017','2018','2019','2020','2021','2022','2023','2024','2025','2026'];

  const rows = filtered.map(c => {
    const isContent = CONTENT_TYPES_SET.has(c.obj_type);
    const typeLabel = c.type_label || c.obj_type || '—';
    const pkg = c.package || '';
    const pkgDesc = c.pkg_desc || '';
    const desc = c.short_desc || c.description || '';
    const spark = YEARS.map(y => {
      const has = (c.years_active||[]).includes(y);
      return `<span style="display:inline-block;width:4px;height:${has?14:4}px;
        background:${has?'#4f8ef7':'rgba(255,255,255,.1)'};border-radius:1px;vertical-align:bottom"></span>`;
    }).join('');

    return `<tr style="border-bottom:1px solid rgba(255,255,255,.04);${isContent?'opacity:.6':''}">
      <td style="padding:8px 16px;vertical-align:top;min-width:160px">
        <div style="font-weight:700;color:#f1f5f9;font-size:.8rem;font-family:monospace">${c.name}</div>
        ${desc ? `<div style="font-size:.67rem;color:var(--mu);margin-top:1px;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${desc}</div>` : ''}
        ${isContent ? '<span style="font-size:.6rem;background:rgba(245,158,11,.15);color:#f59e0b;padding:1px 5px;border-radius:3px">content</span>' : ''}
      </td>
      <td style="padding:8px 12px;vertical-align:top;white-space:nowrap;font-size:.7rem;color:#94a3b8">${typeLabel}</td>
      <td style="padding:8px 12px;vertical-align:top">
        ${pkg ? `<div style="font-weight:700;color:#f1f5f9;font-size:.75rem;font-family:monospace">${pkg}</div>
        ${pkgDesc ? `<div style="font-size:.65rem;color:var(--mu)">${pkgDesc}</div>` : ''}` : '<span style="color:var(--mu2);font-size:.7rem">—</span>'}
      </td>
      <td style="padding:8px 12px;vertical-align:middle;text-align:right;font-size:.8rem;font-weight:700;color:#4f8ef7">${c.total_mods}</td>
      <td style="padding:8px 16px;vertical-align:middle">${spark}</td>
    </tr>`;
  }).join('');

  tbl.innerHTML = `
    <div style="padding:6px 16px;font-size:.67rem;color:var(--mu)">${filtered.length.toLocaleString()} objects shown</div>
    <table style="width:100%;border-collapse:collapse">
      <thead><tr style="background:rgba(0,0,0,.3)">
        <th style="padding:6px 16px;text-align:left;font-size:.65rem;color:var(--mu);letter-spacing:.08em">OBJECT / DESCRIPTION</th>
        <th style="padding:6px 12px;text-align:left;font-size:.65rem;color:var(--mu)">TYPE</th>
        <th style="padding:6px 12px;text-align:left;font-size:.65rem;color:var(--mu)">PACKAGE</th>
        <th style="padding:6px 12px;text-align:right;font-size:.65rem;color:var(--mu)">MODS</th>
        <th style="padding:6px 16px;font-size:.65rem;color:var(--mu)">TIMELINE</th>
      </tr></thead>
      <tbody>${rows}</tbody>
    </table>`;
}

// ── Toggle module expand/collapse ─────────────────────────────────────────────
function toggleModuleCard(modId) {
  const body  = document.getElementById(modId + '-body');
  const arrow = document.getElementById(modId + '-arrow');
  if (!body) return;
  const open = body.style.display !== 'none';
  body.style.display = open ? 'none' : 'block';
  if (arrow) arrow.textContent = open ? '▶' : '▼';
  // Lazy render on first open
  if (!open) {
    const tbl = document.getElementById(modId + '-tbl');
    if (tbl && tbl.dataset.rendered === '0') {
      const names = JSON.parse(tbl.dataset.items || '[]');
      const items = names.map(n => ({name:n, ...CFGDETAIL[n]}));
      renderModTable(modId, items, '');
      tbl.dataset.rendered = '1';
    }
  }
}

// ── Filter by package within a module ─────────────────────────────────────────
function filterModPkg(modId, pkg, btn) {
  // Update pill active state
  const pills = document.getElementById(modId + '-pills');
  if (pills) pills.querySelectorAll('.pkg-pill').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');
  // Re-render table with filter
  const tbl = document.getElementById(modId + '-tbl');
  if (!tbl) return;
  const names = JSON.parse(tbl.dataset.items || '[]');
  const items = names.map(n => ({name:n, ...CFGDETAIL[n]}));
  tbl.dataset.rendered = '1';
  renderModTable(modId, items, pkg);
}
"""

# Inject the new JS before </body>
INJECT = f'<script>{NEW_JS}</script>\n</body>'
html = html.replace('</body>', INJECT, 1)

# Patch buildConfig() to call buildConfigByModule instead
OLD_BC_CALL = 'buildConfig()'
# Find where buildConfig is called on page load / go() navigation
# The main call is in the go() function or DOMContentLoaded
# We need to replace the call when going to the config section

# Find the go() function and add a hook
old_go = "function go(id,btn){"
new_go = """function go(id,btn){
  if (id === 'cfg') {
    setTimeout(function() {
      var ct = document.getElementById('cfg-ct');
      if (ct && ct.innerHTML.trim() === '' || ct.children.length < 2) buildConfigByModule();
    }, 50);
  }"""
html = html.replace(old_go, new_go, 1)
print('Hooked buildConfigByModule into go() navigation')

# Also call on initial load if config is the default section
if "buildConfig()" in html:
    html = html.replace("buildConfig()", "buildConfigByModule()", 1)
    print('Replaced initial buildConfig() call')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Done! {os.path.getsize("cts_dashboard.html")//1024}KB')
