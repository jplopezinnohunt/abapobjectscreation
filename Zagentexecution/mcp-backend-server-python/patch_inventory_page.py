"""
patch_inventory_page.py
Adds the True Inventory page to cts_dashboard.html and reorganizes
Config Elements, Package Browser, and Hotspots by the same grouping rules.
"""
import json, re

# Load data
with open('cts_true_inventory.json', encoding='utf-8') as f:
    inv = json.load(f)

# Inject INVDATA into existing dashboard
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

INV_JS = 'const INVDATA=' + json.dumps(inv, separators=(',',':'), ensure_ascii=False) + ';\n'

# Insert after existing const declarations (after the last JSON data block)
# Find the closing of PDATA const and insert after
html = html.replace('const PDATA=', INV_JS + 'const PDATA=', 1)

# ── Add sidebar nav button for True Inventory ─────────────────────────────────
html = html.replace(
    '<button class="nb" onclick="go(\'packages\',this)">',
    '<button class="nb" onclick="go(\'inventory\',this)"><span class="nd" style="background:var(--grn)"></span>True Inventory</button>\n  <button class="nb" onclick="go(\'packages\',this)">',
    1
)

# ── Add the True Inventory page HTML before closing </div></div> ───────────────
INVENTORY_PAGE = """
<!-- TRUE INVENTORY PAGE -->
<div id="page-inventory" class="page">
  <div class="sec-hdr">True Object Inventory — 30,002 Unique Objects Classified</div>
  <div class="info-box">Every unique object grouped by <strong>what it actually is</strong>. Raw transport count was 92,424 pairs — but only 30,002 distinct objects exist across 10 years.</div>

  <!-- Group KPI row -->
  <div class="krow" id="inv-krow"></div>

  <div class="g2">
    <div class="cc"><h3>Object Groups — Unique Count</h3><div class="cw"><canvas id="ch-inv-donut"></canvas></div></div>
    <div class="cc"><h3>Group vs Modification Volume</h3><div class="cw"><canvas id="ch-inv-mods"></canvas></div></div>
  </div>

  <!-- Expandable group sections -->
  <div id="inv-groups"></div>
</div>
"""

html = html.replace('</div></div>\n\n<script>', INVENTORY_PAGE + '</div></div>\n\n<script>', 1)

# ── Add the JavaScript for the inventory page ─────────────────────────────────
INV_SCRIPT = """
// ── TRUE INVENTORY PAGE ───────────────────────────────────────────────────────
const INV_GROUP_COLORS = {
  'Custom Dev (all)':         '#4f8ef7',
  'SAP Standard (pulled in)': '#475569',
  'Config / Customizing':     '#f59e0b',
  'Security & Auth Admin':    '#ef4444',
  'Docs & Infra':             '#94a3b8',
  'EPI-USE (3rd party)':      '#0ea5e9',
  'Other/Misc':               '#334155',
};
const INV_GROUP_ICON = {
  'Custom Dev (all)':         '🛠',
  'SAP Standard (pulled in)': '📦',
  'Config / Customizing':     '⚙️',
  'Security & Auth Admin':    '🔐',
  'Docs & Infra':             '📄',
  'EPI-USE (3rd party)':      '🏭',
  'Other/Misc':               '🔧',
};
const INV_GROUP_DESC = {
  'Custom Dev (all)':         'Your team\\'s ABAP classes, reports, Fiori apps, function modules, workflows, enhancements, forms and custom data model — the real intellectual output',
  'SAP Standard (pulled in)': 'SAP-delivered objects automatically included when customizing or extending standard programs — not hand-coded by team',
  'Config / Customizing':     'IMG table entries, HCM pay-scale views, PSM/FM config, number ranges — the system configuration layer',
  'Security & Auth Admin':    'PFCG authorization roles + system auth tables (AGR_*, USR*, UST*). Only 10 unique tables but transported 3,400+ times',
  'Docs & Infra':             'Message classes, online documentation, SAP notes, transaction codes, package definitions',
  'EPI-USE (3rd party)':      'Data Sync Manager vendor product — shipped via E9BK system. Never count toward team productivity metrics',
  'Other/Misc':               'Edge-case object types: ABAP dictionaries, Query views, enhancement spots, etc.',
};

function buildInventory() {
  const sg = INVDATA.summary_groups;
  const bkts = INVDATA.buckets;
  const detail = INVDATA.summary_groups_detail;
  const total = INVDATA.total;
  const groups = Object.keys(INV_GROUP_COLORS);

  // KPI row
  const krow = document.getElementById('inv-krow');
  groups.forEach(g => {
    const cnt = sg[g] || 0;
    const col = INV_GROUP_COLORS[g];
    krow.innerHTML += `<div class="kpi">
      <div style="position:absolute;top:0;left:0;right:0;height:2px;background:${col}"></div>
      <div class="kv" style="color:${col};font-size:1.3rem">${cnt.toLocaleString()}</div>
      <div class="kl">${INV_GROUP_ICON[g]||''} ${g.replace(' (all)','').replace(' (pulled in)','')}</div>
      <div class="note">${(cnt/total*100).toFixed(1)}%</div>
    </div>`;
  });

  // Donut
  mkC('ch-inv-donut','doughnut',groups,[{
    data: groups.map(g=>sg[g]||0),
    backgroundColor: groups.map(g=>INV_GROUP_COLORS[g]),
    borderWidth: 0, hoverOffset: 6
  }],{lsz:8});

  // Grouped bar: unique vs mods
  const invMods = groups.map(g => {
    const members = detail[g]||[];
    return members.reduce((a,b)=>a+(bkts[b]?.mods||0),0);
  });
  mkC('ch-inv-mods','bar',groups.map(g=>g.replace(' (all)','').replace(' (pulled in)','')),[
    {label:'Unique', data:groups.map(g=>sg[g]||0),
     backgroundColor:groups.map(g=>INV_GROUP_COLORS[g]),borderWidth:0,borderRadius:3},
    {label:'Mods',   data:invMods,
     backgroundColor:groups.map(g=>INV_GROUP_COLORS[g]+'55'),borderWidth:0,borderRadius:3}
  ],{lsz:8});

  // Group detail sections
  const ct = document.getElementById('inv-groups');
  groups.forEach(g => {
    const members = detail[g]||[];
    const cnt = sg[g]||0;
    if (!cnt) return;
    const col = INV_GROUP_COLORS[g];
    const rows = members.map(b => {
      const v = bkts[b];
      if (!v || !v.unique) return '';
      const avg = (v.mods/v.unique).toFixed(1);
      const sample = (v.samples||[]).map(s=>s.split(':')[1]||s).join(', ');
      const barW = Math.round(v.unique/cnt*100);
      return `<tr>
        <td><strong>${b}</strong></td>
        <td>
          <div style="display:flex;align-items:center;gap:6px">
            <div style="flex:1;height:5px;background:var(--b2);border-radius:3px;overflow:hidden">
              <div style="width:${barW}%;height:100%;background:${col};border-radius:3px"></div>
            </div>
            <span style="font-family:'JetBrains Mono',monospace;font-size:.72rem;width:45px;text-align:right">${v.unique.toLocaleString()}</span>
          </div>
        </td>
        <td style="font-family:'JetBrains Mono',monospace;font-size:.72rem">${v.mods.toLocaleString()}</td>
        <td><span class="hot-badge">${avg}x</span></td>
        <td style="color:var(--mu);font-size:.68rem;max-width:280px;overflow:hidden;text-overflow:ellipsis">${sample}</td>
      </tr>`;
    }).join('');

    ct.innerHTML += `
    <div class="cc" style="margin-bottom:12px">
      <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
        <div style="width:10px;height:10px;border-radius:3px;background:${col};flex-shrink:0"></div>
        <h3 style="color:${col}">${g} — ${cnt.toLocaleString()} objects (${(cnt/total*100).toFixed(1)}%)</h3>
      </div>
      <div style="font-size:.73rem;color:var(--mu2);margin-bottom:10px">${INV_GROUP_DESC[g]||''}</div>
      <table class="tbl">
        <thead><tr><th>Object Type Category</th><th>Unique Count</th><th>Mods</th><th>Avg</th><th>Sample Objects</th></tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>`;
  });
}
buildInventory();
"""

# Insert before the closing </script>
html = html.replace('</script>\n</body>', INV_SCRIPT + '\n</script>\n</body>', 1)

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

import os
sz = os.path.getsize('cts_dashboard.html')
print(f'Done! Dashboard: {sz//1024}KB')
print('Added: True Inventory page with 7 group KPIs, donut chart, unique vs mods bars, expandable group detail tables')
