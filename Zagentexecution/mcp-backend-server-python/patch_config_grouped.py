"""
patch_config_grouped.py
Rewrites the buildConfig() function in cts_dashboard.html
to show config tables organized by group (Auth, User Mgmt, HCM, PSM, General).
"""
import re

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# The new buildConfig JS function — grouped by category
NEW_BUILD_CONFIG = r"""
// ── CONFIG ELEMENTS — Grouped ─────────────────────────────────────────────────
const CFG_GROUPS = {
  'Auth Config Tables': {
    color: '#ef4444',
    icon: '🔐',
    desc: 'Authorization object tables — ONLY 4 unique tables, but each transported 100-600x by security admins',
    keys: ['AGR_TIMEB','TVDIR','TDDAT','PRGN_STAT','AGR_USERS','AGR_AGRS','AGR_DEFINE','AGR_TEXTS']
  },
  'User Mgmt Tables': {
    color: '#f87171',
    icon: '👤',
    desc: 'User master data tables — very few unique objects, extremely high modification frequency',
    keys: ['USR10','USR11','USR12','UST10S','UST12','SPERS_OBJ','SPERS','SUSR_FIELDS']
  },
  'HCM Config Views': {
    color: '#a78bfa',
    icon: '👥',
    desc: 'HCM Payroll & OM configuration views (VDAT type) — pay scales, pay grades, org structure',
    filter: (c) => c.obj_type === 'VDAT' || c.obj_type === 'CDAT'
  },
  'HCM Config Tables': {
    color: '#c084fc',
    icon: '📋',
    desc: 'HCM customizing tables — T7/T5xx payroll schemas, molga, work schedules',
    filter: (c) => c.obj_type === 'TABU' && /^(T7|T5[0-9]|T50[0-9]|T549|T54|PA0|MOLGA|T001P|T500L)/.test(c.name)
  },
  'PSM/FM Config': {
    color: '#86efac',
    icon: '💰',
    desc: 'Public Sector / Funds Management configuration — UCU*, UGW*, FM tables',
    filter: (c) => c.obj_type === 'TABU' && /^(UCU|UGW|FMFG|FM[A-Z])/.test(c.name)
  },
  'General Customizing': {
    color: '#f59e0b',
    icon: '⚙️',
    desc: 'All other IMG/customizing entries — number ranges, variants, general SAP config',
    filter: (c) => true  // catch-all
  },
};

function buildConfig() {
  if (!UDATA.top_cfg_tables || !UDATA.top_cfg_tables.length) return;
  const allCfg = UDATA.top_cfg_tables;

  // Summary top-15 chart (flat, colored by group)
  function getGroupForCfg(c) {
    for (const [grp, def] of Object.entries(CFG_GROUPS)) {
      if (def.keys && def.keys.includes(c.name)) return grp;
      if (def.filter && def.filter(c)) return grp;
    }
    return 'General Customizing';
  }

  const top15 = allCfg.slice(0,15);
  mkC('ch-cfg-hot','bar',top15.map(c=>c.name),[{
    data: top15.map(c=>c.mods),
    backgroundColor: top15.map(c=>CFG_GROUPS[getGroupForCfg(c)]?.color||'#f59e0b'),
    borderWidth:0, borderRadius:3
  }],{horz:true,lsz:8});

  // Type breakdown donut
  const typeCount={};
  allCfg.forEach(c=>{typeCount[c.obj_type]=(typeCount[c.obj_type]||0)+1;});
  mkC('ch-cfg-type','doughnut',Object.keys(typeCount),[{
    data:Object.values(typeCount),
    backgroundColor:['#f59e0b','#a78bfa','#22d3ee','#fb923c','#ef4444','#86efac'],
    borderWidth:0
  }],{lsz:8});

  // Grouped table
  const tbody = document.getElementById('cfg-tbody');
  tbody.innerHTML = '';

  // Assign each config item to a group
  const grouped = {};
  Object.keys(CFG_GROUPS).forEach(g => grouped[g] = []);
  const assigned = new Set();

  // Priority: explicit keys first
  for (const [grp, def] of Object.entries(CFG_GROUPS)) {
    if (!def.keys) continue;
    allCfg.forEach(c => {
      if (def.keys.includes(c.name) && !assigned.has(c.name)) {
        grouped[grp].push(c);
        assigned.add(c.name);
      }
    });
  }
  // Then filter-based groups (in order, stop at General)
  for (const [grp, def] of Object.entries(CFG_GROUPS)) {
    if (!def.filter || grp === 'General Customizing') continue;
    allCfg.forEach(c => {
      if (!assigned.has(c.name) && def.filter(c)) {
        grouped[grp].push(c);
        assigned.add(c.name);
      }
    });
  }
  // Remainder → General Customizing
  allCfg.forEach(c => {
    if (!assigned.has(c.name)) {
      grouped['General Customizing'].push(c);
      assigned.add(c.name);
    }
  });

  // Render with group headers
  for (const [grp, items] of Object.entries(grouped)) {
    if (!items.length) continue;
    const def = CFG_GROUPS[grp];
    const grpTotal = items.reduce((a,b)=>a+b.mods,0);
    const grpUniq  = items.length;
    // Group header row
    tbody.innerHTML += `<tr>
      <td colspan="6" style="background:${def.color}18;padding:8px 9px;border-bottom:1px solid ${def.color}44">
        <div style="display:flex;align-items:center;gap:8px">
          <span style="font-size:.85rem">${def.icon}</span>
          <strong style="color:${def.color}">${grp}</strong>
          <span style="font-size:.68rem;color:var(--mu);margin-left:4px">${grpUniq} tables · ${grpTotal.toLocaleString()} total mods</span>
        </div>
        <div style="font-size:.67rem;color:var(--mu2);margin-top:2px;padding-left:26px">${def.desc}</div>
      </td>
    </tr>`;
    // Item rows sorted by mods desc
    items.sort((a,b)=>b.mods-a.mods).forEach(c => {
      const area = CFG_AREA[c.name] || (
        c.name.startsWith('T7') || c.name.startsWith('V_T') ? 'HCM Payroll/Config' :
        c.name.startsWith('UCU') ? 'Funds Management' : 'Config');
      tbody.innerHTML += `<tr>
        <td style="padding-left:24px"><code>${c.name}</code></td>
        <td><code style="color:${def.color}">${c.obj_type}</code></td>
        <td><span class="hot-badge" style="background:${def.color}22;color:${def.color}">${c.mods}x</span></td>
        <td>${c.users}</td>
        <td>${c.years}</td>
        <td style="color:var(--mu2)">${area}</td>
      </tr>`;
    });
  }
}
"""

# Replace the old buildConfig function (from 'function buildConfig(){' to the next top-level function)
# Find the function bounds  
old_start = html.find('// ── CONFIG ELEMENTS ───────────────────────────────────────────────────────────')
if old_start == -1:
    old_start = html.find('function buildConfig(){')
    # back up to find comments just before it
    alt = html.rfind('\n// ', 0, old_start)
    if alt != -1 and (old_start - alt) < 100:
        old_start = alt + 1

old_end = html.find('\n// ── TEAM PROFILES', old_start)
if old_end == -1:
    old_end = html.find('\nfunction buildUserTabs', old_start)

if old_start != -1 and old_end != -1:
    html = html[:old_start] + NEW_BUILD_CONFIG + '\n' + html[old_end:]
    print(f'Replaced buildConfig block ({old_end - old_start} chars -> {len(NEW_BUILD_CONFIG)} chars)')
else:
    print(f'Could not find bounds: start={old_start}, end={old_end}')
    raise SystemExit(1)

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

import os
print(f'Done! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
