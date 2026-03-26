"""
patch_config_grouped_v2.py
Fully rewrites the Config Elements page of cts_dashboard.html:
- Injects cts_config_detail.json as CFGDETAIL JS variable
- Group headers are clickable: expand/collapse detailed object list
- Each object row shows: name, type, mod sparkline (10yr), user count, % of group mods
- Charts updated to be colored by group
"""
import json, re, os

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg_detail = json.load(f)

# ── 1. Inject CFGDETAIL data just after INVDATA ────────────────────────────────
cfg_js = 'const CFGDETAIL=' + json.dumps(cfg_detail, separators=(',',':'), ensure_ascii=False) + ';\n'
# Insert after INVDATA=
html = html.replace('const INVDATA=', cfg_js + 'const INVDATA=', 1)

# ── 2. Replace Config Elements page HTML ───────────────────────────────────────
OLD_CFG_PAGE_START = '<!-- CONFIG ELEMENTS -->'
OLD_CFG_PAGE_END   = '\n<!-- TEAM PROFILES -->'

cfg_page_start = html.find(OLD_CFG_PAGE_START)
cfg_page_end   = html.find(OLD_CFG_PAGE_END)

NEW_CFG_PAGE = """<!-- CONFIG ELEMENTS -->
<div id="page-config" class="page">
  <div class="sec-hdr">Configuration Element Drill-Down</div>
  <div class="info-box">
    <strong>4,168 unique config objects</strong> across the 10-year period, organized by configuration domain.
    Click any group header to expand and explore the individual tables and views inside.
  </div>

  <!-- Group summary KPI row -->
  <div class="krow" id="cfg-krow"></div>

  <div class="g2" style="margin-bottom:14px">
    <div class="cc"><h3>Top 15 Config Hotspots (mods)</h3><div class="cw tall"><canvas id="ch-cfg-hot"></canvas></div></div>
    <div class="cc"><h3>Config by Type</h3><div class="cw tall"><canvas id="ch-cfg-type"></canvas></div></div>
  </div>

  <!-- Grouped collapsible sections -->
  <div id="cfg-groups-container"></div>
</div>

"""

html = html[:cfg_page_start] + NEW_CFG_PAGE + html[cfg_page_end:]

# ── 3. Replace the buildConfig JS function ─────────────────────────────────────
START_MARK = '// ── CONFIG ELEMENTS ───────────────────────────────────────────────────────────'
# After the previous patch this might have changed — find the function directly
fn_start = html.find('// ── CONFIG ELEMENTS')
if fn_start == -1:
    fn_start = html.find('function buildConfig()')
    # look for comment block before it
    pre = html.rfind('\n// ', 0, fn_start)
    if pre != -1 and (fn_start - pre) < 80: fn_start = pre + 1

fn_end = html.find('\n// ── TEAM PROFILES', fn_start)
if fn_end == -1:
    fn_end = html.find('\nfunction buildUserTabs', fn_start)

NEW_CFG_JS = r"""
// ── CONFIG ELEMENTS (Grouped + Drilldown) ─────────────────────────────────────
const CFG_GROUPS = [
  {
    id: 'auth',
    label: 'Auth Config Tables',
    color: '#ef4444',
    icon: '🔐',
    desc: 'AGR_* authorization object tables — only a handful of unique tables, each transported hundreds of times by security admins every year',
    match: c => /^AGR_/.test(c.name) || ['TVDIR','TDDAT','PRGN_STAT'].includes(c.name),
  },
  {
    id: 'usermgmt',
    label: 'User Management Tables',
    color: '#f97316',
    icon: '👤',
    desc: 'USRxx / USTxx user master tables — produced automatically on every role transport. Modification count reflects security admin activity, not development.',
    match: c => /^USR|^UST|^SUSR/.test(c.name) || ['SPERS_OBJ','SPERS'].includes(c.name),
  },
  {
    id: 'hcmviews',
    label: 'HCM Config Views (VDAT)',
    color: '#a78bfa',
    icon: '👥',
    desc: 'Payroll & OM configuration views — V_T510 pay scales, V_T7UNPAD payroll schemas, org-unit config. High mods = active payroll/org structure maintenance.',
    match: c => c.obj_type === 'VDAT' || c.obj_type === 'CDAT',
  },
  {
    id: 'hcmtables',
    label: 'HCM Config Tables (TABU T7/T5xx)',
    color: '#c084fc',
    icon: '📋',
    desc: 'HCM customizing TABU entries — T7* payroll, T5xx pay grades, work schedule rules, molga country settings.',
    match: c => c.obj_type === 'TABU' && /^(T7|T5[0-9]|T50|T54|PA0|MOLGA|T001P|T500L|T508)/.test(c.name),
  },
  {
    id: 'psm',
    label: 'PSM / Funds Management Config',
    color: '#86efac',
    icon: '💰',
    desc: 'Public Sector Management — UCUMxxx fund tables, UGWBxxxx FM integration config.',
    match: c => /^(UCU|UGW|FMFG|FM[A-Z])/.test(c.name),
  },
  {
    id: 'general',
    label: 'General Customizing (IMG / Other)',
    color: '#f59e0b',
    icon: '⚙️',
    desc: 'All other IMG entries — number ranges, variants, SCVI screen variants, OSOA output conditions, TTYP type definitions, and general SAP config.',
    match: () => true,   // catch-all
  },
];

let cfgGroupData = null;

function assignCfgGroups() {
  if (cfgGroupData) return cfgGroupData;
  const source = Object.entries(CFGDETAIL).map(([name, v]) => ({name, ...v}));
  source.sort((a,b) => b.total_mods - a.total_mods);

  cfgGroupData = {};
  CFG_GROUPS.forEach(g => cfgGroupData[g.id] = []);

  const assigned = new Set();
  // Priority pass: all groups except catch-all
  CFG_GROUPS.filter(g => g.id !== 'general').forEach(g => {
    source.forEach(c => {
      if (!assigned.has(c.name) && g.match(c)) {
        cfgGroupData[g.id].push(c);
        assigned.add(c.name);
      }
    });
  });
  // Catch-all
  source.forEach(c => {
    if (!assigned.has(c.name)) {
      cfgGroupData['general'].push(c);
      assigned.add(c.name);
    }
  });
  return cfgGroupData;
}

function sparkline(obj, maxMod, color) {
  const YEARS = ['2017','2018','2019','2020','2021','2022','2023','2024','2025','2026'];
  const cells = YEARS.map(y => {
    const v = obj.mods_by_year?.[y] || 0;
    const h = maxMod > 0 ? Math.max(2, Math.round(v/maxMod*18)) : 0;
    const opacity = v > 0 ? 0.4 + (v/maxMod)*0.6 : 0.08;
    return `<div style="display:inline-block;width:9px;height:${h}px;background:${color};opacity:${opacity.toFixed(2)};border-radius:1px;vertical-align:bottom;margin-right:1px" title="${y}: ${v}x"></div>`;
  }).join('');
  return `<div style="display:flex;align-items:flex-end;height:20px;gap:0">${cells}</div>`;
}

function buildConfig() {
  const groups = assignCfgGroups();
  const YEARS = ['2017','2018','2019','2020','2021','2022','2023','2024','2025','2026'];

  // KPI row
  const krow = document.getElementById('cfg-krow');
  CFG_GROUPS.forEach(g => {
    const items = groups[g.id] || [];
    const mods  = items.reduce((a,b)=>a+b.total_mods,0);
    krow.innerHTML += `<div class="kpi">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;background:${g.color}"></div>
      <div class="kv" style="color:${g.color};font-size:1.15rem">${items.length.toLocaleString()}</div>
      <div class="kl">${g.icon} ${g.label.split('(')[0].trim()}</div>
      <div class="note">${mods.toLocaleString()} total mods</div>
    </div>`;
  });

  // Top 15 hotspot chart — colored by group
  const all = Object.entries(CFGDETAIL).map(([n,v])=>({name:n,...v}))
    .sort((a,b)=>b.total_mods-a.total_mods).slice(0,15);
  function colorFor(name, ot) {
    for (const g of CFG_GROUPS.filter(x=>x.id!=='general')) {
      if (g.match({name, obj_type:ot})) return g.color;
    }
    return '#f59e0b';
  }
  mkC('ch-cfg-hot','bar',all.map(c=>c.name),[{
    data: all.map(c=>c.total_mods),
    backgroundColor: all.map(c=>colorFor(c.name, c.obj_type)),
    borderWidth:0, borderRadius:3
  }],{horz:true,lsz:8});

  // Type donut
  const typeCount = {};
  Object.values(CFGDETAIL).forEach(v=>{typeCount[v.obj_type]=(typeCount[v.obj_type]||0)+1;});
  mkC('ch-cfg-type','doughnut',Object.keys(typeCount),[{
    data:Object.values(typeCount),
    backgroundColor:['#f59e0b','#a78bfa','#ef4444','#22d3ee','#fb923c','#86efac'],
    borderWidth:0
  }],{lsz:8});

  // Grouped collapsible sections
  const ct = document.getElementById('cfg-groups-container');
  CFG_GROUPS.forEach(g => {
    const items = groups[g.id] || [];
    if (!items.length) return;
    const totalMods = items.reduce((a,b)=>a+b.total_mods,0);
    const maxMods   = items[0]?.total_mods || 1;
    const totalUsers= new Set(items.flatMap(i=>i.users||[])).size;

    const panelId = 'cfg-panel-'+g.id;

    // Build item rows (show top 50 — more than enough)
    const rows = items.slice(0,50).map(c => {
      const pct = totalMods > 0 ? (c.total_mods/totalMods*100).toFixed(1) : 0;
      const sp  = sparkline(c, maxMods, g.color);
      const usrs= (c.users||[]).join(', ').toLowerCase().replace(/_/g,' ') || '—';
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
        <td style="font-size:.68rem;color:var(--mu2)">${c.first_seen||''}–${c.last_seen||''}</td>
        <td style="font-size:.65rem;color:var(--mu);max-width:180px;overflow:hidden;text-overflow:ellipsis">${usrs}</td>
        <td style="font-size:.68rem;color:var(--mu)">${pct}%</td>
      </tr>`;
    }).join('');

    const moreNote = items.length > 50
      ? `<tr><td colspan="7" style="text-align:center;color:var(--mu);font-size:.7rem;padding:8px">+ ${items.length-50} more objects in this group</td></tr>`
      : '';

    ct.innerHTML += `
    <div class="cc" style="margin-bottom:10px;padding:0;overflow:hidden">
      <!-- GROUP HEADER — clickable -->
      <div onclick="toggleCfgGroup('${panelId}', this)"
           style="display:flex;align-items:center;gap:10px;padding:12px 16px;
                  cursor:pointer;background:${g.color}14;
                  border-bottom:1px solid ${g.color}33;user-select:none">
        <span style="font-size:1.1rem">${g.icon}</span>
        <div style="flex:1">
          <div style="font-weight:600;color:${g.color};font-size:.84rem">${g.label}</div>
          <div style="font-size:.68rem;color:var(--mu2);margin-top:2px">${g.desc}</div>
        </div>
        <div style="text-align:right;flex-shrink:0">
          <div style="font-size:1rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:${g.color}">${items.length}</div>
          <div style="font-size:.6rem;color:var(--mu)">unique objects</div>
        </div>
        <div style="text-align:right;flex-shrink:0;margin-left:12px">
          <div style="font-size:1rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:var(--mu2)">${totalMods.toLocaleString()}</div>
          <div style="font-size:.6rem;color:var(--mu)">total mods</div>
        </div>
        <div style="text-align:right;flex-shrink:0;margin-left:12px">
          <div style="font-size:.9rem;font-weight:600;color:var(--mu2)">${totalUsers}</div>
          <div style="font-size:.6rem;color:var(--mu)">contributors</div>
        </div>
        <div id="${panelId}-arrow" style="font-size:.8rem;color:var(--mu);margin-left:8px;transition:.2s">▶</div>
      </div>
      <!-- DRILLDOWN PANEL — hidden by default -->
      <div id="${panelId}" style="display:none">
        <div style="overflow-x:auto">
          <table class="tbl">
            <thead><tr>
              <th>Table / View</th><th>Type</th><th style="min-width:130px">Mods (2017→2026 ▰)</th>
              <th>Users</th><th>Active</th><th>Contributors</th><th>% of group</th>
            </tr></thead>
            <tbody>${rows}${moreNote}</tbody>
          </table>
        </div>
      </div>
    </div>`;
  });
}

function toggleCfgGroup(panelId, header) {
  const panel = document.getElementById(panelId);
  const arrow = document.getElementById(panelId+'-arrow');
  if (!panel) return;
  const isOpen = panel.style.display !== 'none';
  panel.style.display = isOpen ? 'none' : 'block';
  if (arrow) arrow.textContent = isOpen ? '▶' : '▼';
  header.style.borderBottomColor = isOpen ? 'transparent' : 'var(--b)';
}

"""

if fn_start != -1 and fn_end != -1:
    html = html[:fn_start] + NEW_CFG_JS + '\n' + html[fn_end:]
    print(f'Replaced buildConfig JS block ({fn_end-fn_start} chars -> {len(NEW_CFG_JS)} chars)')
else:
    raise SystemExit(f'Could not find buildConfig bounds: start={fn_start}, end={fn_end}')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Done! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
print('Config Elements page now shows:')
print('  - 6 group KPI tiles')
print('  - Top 15 hotspot bar (colored by group)')
print('  - Type donut chart')
print('  - 6 collapsible groups, each with full object table + 10yr sparklines')
