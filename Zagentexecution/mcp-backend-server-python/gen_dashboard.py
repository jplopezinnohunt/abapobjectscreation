"""
gen_dashboard.py – Generates cts_dashboard_v2.html embedding all three JSON data files.
Adds: corrected unique-object KPIs, Package Browser page, Config Element page.
"""
import json, os

with open('cts_dashboard_data.json', encoding='utf-8') as f: d1 = json.load(f)
with open('cts_unique_objects.json',  encoding='utf-8') as f: d2 = json.load(f)
with open('cts_package_config_data.json', encoding='utf-8') as f: d3 = json.load(f)

s   = d2['summary']
pkgs= d2['top_packages'][:25]
cfg = d2['top_cfg_tables'][:50]
hots= d2['hotspots'][:30]

# Serialise for embedding
JS = (
    'const DATA='+json.dumps(d1, separators=(',',':'), ensure_ascii=False)+';\n'
    'const UDATA='+json.dumps(d2, separators=(',',':'), ensure_ascii=False)+';\n'
    'const PDATA='+json.dumps(d3, separators=(',',':'), ensure_ascii=False)+';\n'
)

DCOL = {
    'HCM':'#a78bfa','Fiori/UI':'#22d3ee','Security':'#ef4444','FI':'#fb923c',
    'PSM/FM':'#86efac','CO':'#6ee7b7','OData/WF':'#67e8f9','Workflow':'#34d399',
    'CFG':'#f59e0b','Custom Z/Y':'#4d90fe','SAP Standard':'#475569','Other':'#334155',
    'EPI-USE':'#0ea5e9',
}

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SAP Transport Intelligence — UNESCO D01 (2017–2026)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
:root{{--bg:#080c14;--surf:#0d1320;--card:#111827;--b:#1a2540;--b2:#1e2d4a;
  --txt:#dde5f5;--mu:#4c6490;--mu2:#7892c0;--acc:#4f8ef7;
  --hcm:#a78bfa;--fi2:#22d3ee;--sec:#ef4444;--fi:#fb923c;--psm:#86efac;
  --wf:#34d399;--cfg:#f59e0b;--cust:#60a5fa;--grn:#22c55e;--epi:#0ea5e9;}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--txt);overflow-x:hidden}}
.topbar{{background:linear-gradient(90deg,#050913,#091428,#050913);border-bottom:1px solid var(--b);
  padding:0 28px;display:flex;align-items:center;justify-content:space-between;height:54px;
  position:sticky;top:0;z-index:200;backdrop-filter:blur(16px)}}
.tb-l{{display:flex;align-items:center;gap:10px}}
.tb-ico{{width:30px;height:30px;background:linear-gradient(135deg,var(--acc),var(--hcm));
  border-radius:7px;display:flex;align-items:center;justify-content:center;font-size:15px}}
.tb-stats{{display:flex;gap:20px}}
.tb-stat .v{{font-size:.88rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:var(--acc)}}
.tb-stat .l{{font-size:.6rem;color:var(--mu);text-transform:uppercase;letter-spacing:.05em}}
.shell{{display:flex;min-height:calc(100vh - 54px)}}
.sidebar{{width:210px;flex-shrink:0;background:var(--surf);border-right:1px solid var(--b);
  padding:12px 8px;position:sticky;top:54px;height:calc(100vh - 54px);overflow-y:auto}}
.content{{flex:1;padding:22px 26px 80px;overflow-y:auto}}
.nav-grp-lbl{{font-size:.6rem;font-weight:600;text-transform:uppercase;letter-spacing:.07em;
  color:var(--mu);padding:8px 8px 4px}}
.nb{{display:flex;align-items:center;gap:8px;width:100%;padding:7px 10px;border-radius:7px;
  cursor:pointer;font-size:.79rem;color:var(--mu2);border:none;background:none;text-align:left;
  transition:.12s;margin-bottom:1px}}
.nb:hover{{background:rgba(79,142,247,.08);color:var(--txt)}}
.nb.active{{background:rgba(79,142,247,.14);color:var(--acc);font-weight:500}}
.nd{{width:6px;height:6px;border-radius:50%;flex-shrink:0}}
.page{{display:none}}.page.active{{display:block}}
/* KPI */
.krow{{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:10px;margin-bottom:18px}}
.kpi{{background:var(--card);border:1px solid var(--b);border-radius:10px;padding:14px;position:relative;overflow:hidden}}
.kpi::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px}}
.kpi .note{{font-size:.58rem;color:var(--mu);margin-top:2px}}
.kv{{font-size:1.6rem;font-weight:800;font-family:'JetBrains Mono',monospace;line-height:1}}
.kl{{font-size:.62rem;color:var(--mu);text-transform:uppercase;letter-spacing:.04em;margin-top:5px}}
/* compare badge */
.cmp{{font-size:.65rem;padding:1px 6px;border-radius:5px;margin-left:6px}}
.cmp-raw{{background:rgba(239,68,68,.1);color:var(--sec)}}
/* Charts */
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:14px}}
.g3{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:14px}}
.cc{{background:var(--card);border:1px solid var(--b);border-radius:10px;padding:14px}}
.cc h3{{font-size:.68rem;font-weight:600;color:var(--mu2);text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px}}
.cw{{position:relative;height:200px}}.cw.tall{{height:270px}}.cw.sm{{height:160px}}
/* Table */
.tbl{{width:100%;border-collapse:collapse;font-size:.75rem}}
.tbl th{{font-size:.62rem;font-weight:600;text-transform:uppercase;letter-spacing:.05em;
  color:var(--mu);padding:7px 9px;border-bottom:1px solid var(--b);white-space:nowrap;text-align:left}}
.tbl td{{padding:6px 9px;border-bottom:1px solid rgba(26,37,64,.5);white-space:nowrap}}
.tbl tbody tr:hover td{{background:rgba(79,142,247,.04)}}
.tbl tr:last-child td{{border-bottom:none}}
/* Badges */
.bd{{display:inline-block;font-size:.61rem;font-weight:600;padding:2px 7px;border-radius:7px}}
.bd-dev{{background:rgba(79,142,247,.14);color:var(--acc)}}
.bd-cfg{{background:rgba(245,158,11,.14);color:var(--cfg)}}
.bd-hcm{{background:rgba(167,139,250,.14);color:var(--hcm)}}
.bd-sec{{background:rgba(239,68,68,.14);color:var(--sec)}}
.bd-fiori{{background:rgba(34,211,238,.14);color:var(--fi2)}}
.bd-epi{{background:rgba(14,165,233,.14);color:var(--epi)}}
/* User tabs */
.utabs{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}}
.utab{{padding:5px 12px;border-radius:20px;font-size:.74rem;font-weight:500;cursor:pointer;
  background:var(--card);border:1px solid var(--b);color:var(--mu2);transition:.12s}}
.utab:hover,.utab.active{{border-color:var(--acc);color:var(--acc);background:rgba(79,142,247,.1)}}
/* Domain tabs */
.dtabs{{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px}}
.dtab{{padding:5px 14px;border-radius:20px;font-size:.74rem;font-weight:500;cursor:pointer;
  border:1px solid var(--b);background:var(--card);color:var(--mu2);transition:.12s}}
.dtab.active{{color:#fff;border-color:transparent}}
/* Mini bars */
.mbr{{display:flex;align-items:center;gap:8px;margin-bottom:4px;font-size:.72rem}}
.mbl{{width:140px;color:var(--mu2);flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.mbt{{flex:1;height:5px;background:var(--b2);border-radius:3px;overflow:hidden}}
.mbf{{height:100%;border-radius:3px}}
.mbv{{width:55px;text-align:right;color:var(--mu);font-family:'JetBrains Mono',monospace;font-size:.68rem}}
.sec-hdr{{font-size:.78rem;font-weight:600;color:var(--mu2);margin-bottom:12px;
  display:flex;align-items:center;gap:10px}}
.sec-hdr::after{{content:'';flex:1;height:1px;background:var(--b)}}
.info-box{{background:rgba(79,142,247,.07);border:1px solid rgba(79,142,247,.2);border-radius:8px;
  padding:10px 14px;font-size:.76rem;margin-bottom:12px;color:var(--mu2)}}
code{{font-family:'JetBrains Mono',monospace;font-size:.68rem;background:rgba(255,255,255,.05);
  padding:1px 5px;border-radius:3px}}
.hot-badge{{display:inline-block;font-size:.6rem;padding:1px 5px;border-radius:4px;
  background:rgba(239,68,68,.1);color:var(--sec);font-family:'JetBrains Mono',monospace}}
</style>
</head>
<body>
<div class="topbar">
  <div class="tb-l">
    <div class="tb-ico">📦</div>
    <div>
      <div style="font-size:.9rem;font-weight:700">SAP Transport Intelligence</div>
      <div style="font-size:.63rem;color:var(--mu)">UNESCO D01 · 2017–2026 · Unique-object view</div>
    </div>
  </div>
  <div class="tb-stats">
    <div class="tb-stat"><div class="v">{s['unique_objects']:,}</div><div class="l">Unique Obj</div></div>
    <div class="tb-stat"><div class="v">7,745</div><div class="l">Transports</div></div>
    <div class="tb-stat"><div class="v">{s['avg_mods']}x</div><div class="l">Avg mods</div></div>
    <div class="tb-stat"><div class="v">28</div><div class="l">Contributors</div></div>
  </div>
</div>
<div class="shell">
<nav class="sidebar">
  <div class="nav-grp-lbl">Overview</div>
  <button class="nb active" onclick="go('overview',this)"><span class="nd" style="background:var(--acc)"></span>Dashboard</button>
  <button class="nb" onclick="go('yearly',this)"><span class="nd" style="background:var(--wf)"></span>Year Timeline</button>
  <div class="nav-grp-lbl">Analysis</div>
  <button class="nb" onclick="go('domains',this)"><span class="nd" style="background:var(--fi2)"></span>Domain Navigator</button>
  <button class="nb" onclick="go('packages',this)"><span class="nd" style="background:var(--grn)"></span>Package Browser</button>
  <button class="nb" onclick="go('config',this)"><span class="nd" style="background:var(--cfg)"></span>Config Elements</button>
  <div class="nav-grp-lbl">People</div>
  <button class="nb" onclick="go('profiles',this)"><span class="nd" style="background:var(--hcm)"></span>Team Profiles</button>
  <button class="nb" onclick="go('team',this)"><span class="nd" style="background:var(--acc)"></span>Contribution Table</button>
  <div class="nav-grp-lbl">Special</div>
  <button class="nb" onclick="go('hotspots',this)"><span class="nd" style="background:var(--sec)"></span>Hotspot Objects</button>
  <button class="nb" onclick="go('epiuse',this)"><span class="nd" style="background:var(--epi)"></span>EPI-USE</button>
  <button class="nb" onclick="go('taxonomy',this)"><span class="nd" style="background:var(--mu)"></span>Taxonomy</button>
</nav>
<div class="content">

<!-- OVERVIEW -->
<div id="page-overview" class="page active">
  <div class="info-box">ℹ All counts show <strong>unique objects</strong> (deduped by type+name).
    Raw transport pairs: <strong>{s['total_transport_pairs']:,}</strong> — avg <strong>{s['avg_mods']}x</strong> re-modification per object over 10 years.</div>
  <div class="krow">
    <div class="kpi" style="--c:var(--acc)"><div class="kpi" style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--acc)"></div>
      <div class="kv" style="color:var(--acc)">{s['unique_dev']:,}</div><div class="kl">Unique Dev Objects</div>
      <div class="note">was ~30K pairs</div></div>
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--fi2)"></div>
      <div class="kv" style="color:var(--fi2)">553</div><div class="kl">Unique Fiori/UI</div></div>
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--hcm)"></div>
      <div class="kv" style="color:var(--hcm)">3,984</div><div class="kl">Unique HCM Obj</div></div>
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--sec)"></div>
      <div class="kv" style="color:var(--sec)">{s['unique_sec']:,}</div><div class="kl">Unique Roles</div></div>
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--cfg)"></div>
      <div class="kv" style="color:var(--cfg)">{s['unique_cfg']:,}</div><div class="kl">Unique Config Tbl</div></div>
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--epi)"></div>
      <div class="kv" style="color:var(--epi)">{s['unique_epi']:,}</div><div class="kl">EPI-USE (excl)</div></div>
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--mu)"></div>
      <div class="kv" style="color:var(--mu2)">{s['avg_mods']}x</div><div class="kl">Avg re-mods</div></div>
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--grn)"></div>
      <div class="kv" style="color:var(--grn)">{s['unique_objects']:,}</div><div class="kl">Total Unique Obj</div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Unique Objects by Nature</h3><div class="cw"><canvas id="ch-nature"></canvas></div></div>
    <div class="cc"><h3>Unique vs Modifications — Domain</h3><div class="cw"><canvas id="ch-uniq-vs-mods"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3>Domain (Unique Objects)</h3><div class="cw"><canvas id="ch-domain"></canvas></div></div>
    <div class="cc"><h3>Object Type (Unique)</h3><div class="cw"><canvas id="ch-types"></canvas></div></div>
  </div>
</div>

<!-- YEARLY -->
<div id="page-yearly" class="page">
  <div class="sec-hdr">New Unique Objects Introduced per Year</div>
  <div class="info-box">Each bar = unique objects that appeared for the <strong>first time</strong> in that year (by earliest transport date).</div>
  <div class="cc" style="margin-bottom:14px"><h3>New Unique Objects by Year (stacked by nature)</h3><div class="cw tall"><canvas id="ch-yr-new"></canvas></div></div>
  <div class="cc"><h3>Transports Released per Year</h3><div class="cw"><canvas id="ch-yr-trans"></canvas></div></div>
</div>

<!-- DOMAIN NAVIGATOR -->
<div id="page-domains" class="page">
  <div class="sec-hdr">Domain Navigator — click a domain</div>
  <div class="dtabs" id="dom-tabs"></div>
  <div class="g2">
    <div class="cc"><h3 id="dom-t1">Unique Objects per Domain</h3><div class="cw"><canvas id="ch-dom-uniq"></canvas></div></div>
    <div class="cc"><h3 id="dom-t2">Top Contributors</h3><div class="cw"><canvas id="ch-dom-users"></canvas></div></div>
  </div>
  <div class="cc"><h3 id="dom-t3">Stack by Contributor</h3><div class="cw tall"><canvas id="ch-dom-stack"></canvas></div></div>
</div>

<!-- PACKAGE BROWSER -->
<div id="page-packages" class="page">
  <div class="sec-hdr">Package Browser — Unique Objects per Z/Y Namespace</div>
  <div class="info-box">Package groups inferred from object name prefix (DEVCLASS unavailable via RFC). Each entry = a coherent namespace family.</div>
  <div class="g2">
    <div class="cc"><h3>Top Packages — Unique Object Count</h3><div class="cw tall"><canvas id="ch-pkg-uniq"></canvas></div></div>
    <div class="cc"><h3>Top Packages — Modification Volume</h3><div class="cw tall"><canvas id="ch-pkg-mods"></canvas></div></div>
  </div>
  <div class="cc"><h3>Package Detail</h3>
    <table class="tbl" style="margin-top:6px">
      <thead><tr><th>Package / Namespace</th><th>Domain</th><th>Unique Obj</th><th>Mods</th><th>Avg</th><th>Users</th><th>Years</th><th>Sample Objects</th></tr></thead>
      <tbody id="pkg-tbody"></tbody>
    </table>
  </div>
</div>

<!-- CONFIG ELEMENTS -->
<div id="page-config" class="page">
  <div class="sec-hdr">Configuration Element Drill-Down (TABU / VDAT / HCM config)</div>
  <div class="info-box">Each row = one unique SAP table/view being customized. <strong>Mods</strong> = how many times it was transported. High-mod tables are your most-maintained config areas.</div>
  <div class="g2">
    <div class="cc"><h3>Top 15 Config Hotspots (mods)</h3><div class="cw tall"><canvas id="ch-cfg-hot"></canvas></div></div>
    <div class="cc"><h3>Config by Type</h3><div class="cw tall"><canvas id="ch-cfg-type"></canvas></div></div>
  </div>
  <div class="cc"><h3>Config Table Details</h3>
    <table class="tbl" style="margin-top:6px">
      <thead><tr><th>Table / View</th><th>Type</th><th>Mods</th><th>Users</th><th>Years Active</th><th>Business Area</th></tr></thead>
      <tbody id="cfg-tbody"></tbody>
    </table>
  </div>
</div>

<!-- TEAM PROFILES -->
<div id="page-profiles" class="page">
  <div class="sec-hdr">Team Profiles — Unique Objects per Person</div>
  <div class="utabs" id="user-tabs"></div>
  <div class="g2">
    <div class="cc"><h3 id="prof-t1">Objects by Year</h3><div class="cw"><canvas id="ch-prof-yr"></canvas></div></div>
    <div class="cc"><h3 id="prof-t2">Domain Profile</h3><div class="cw"><canvas id="ch-prof-dom"></canvas></div></div>
  </div>
  <div class="g2">
    <div class="cc"><h3 id="prof-t3">Object Types</h3><div class="cw"><canvas id="ch-prof-typ"></canvas></div></div>
    <div class="cc" id="prof-card"><h3>Profile Card</h3><div id="prof-card-body" style="padding-top:6px"></div></div>
  </div>
</div>

<!-- CONTRIBUTION TABLE -->
<div id="page-team" class="page">
  <div class="sec-hdr">Unique Object Contribution — All Users</div>
  <div style="overflow-x:auto">
  <table class="tbl"><thead><tr>
    <th>User</th><th>Role</th><th>Unique Obj Touched</th><th>Unique Owned</th>
    <th>HCM</th><th>Fiori/UI</th><th>Security</th><th>FI</th><th>Workflow</th><th>Custom Z/Y</th>
  </tr></thead><tbody id="team-tbody"></tbody></table>
  </div>
</div>

<!-- HOTSPOTS -->
<div id="page-hotspots" class="page">
  <div class="sec-hdr">Most Re-Modified Objects (Hotspots)</div>
  <div class="info-box">These unique objects were transported the most times — indicating active development, frequent reconfiguration, or shared ownership.</div>
  <table class="tbl">
    <thead><tr><th>Type</th><th>Object Name</th><th>Domain</th><th>Mods</th><th>Users</th><th>Years</th></tr></thead>
    <tbody>
      {''.join(f'<tr><td><code>{h["ot"]}</code></td><td>{h["on"]}</td><td>{h["dom"]}</td><td><span class="hot-badge">{h["mods"]}x</span></td><td>{h["users"]}</td><td>{h["years"]}</td></tr>' for h in hots)}
    </tbody>
  </table>
</div>

<!-- EPI-USE -->
<div id="page-epiuse" class="page">
  <div class="krow">
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--epi)"></div>
      <div class="kv" style="color:var(--epi)">{s['unique_epi']:,}</div><div class="kl">Unique EPI-USE Obj</div></div>
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--epi)"></div>
      <div class="kv" style="color:var(--epi)">9</div><div class="kl">Installations</div></div>
    <div class="kpi"><div style="position:absolute;top:0;left:0;right:0;height:2px;background:var(--epi)"></div>
      <div class="kv" style="color:var(--epi)">E9BK</div><div class="kl">Source System</div></div>
  </div>
  <div class="info-box">⚠ EPI-USE objects are excluded from all uniqueness metrics above. Without exclusion, they would inflate unique HCM dev counts by ~21%.</div>
  <div class="g2">
    <div class="cc"><h3>EPI-USE Delivery Volume by Year</h3><div class="cw"><canvas id="ch-epi-yr"></canvas></div></div>
    <div class="cc"><h3>Object Type Mix</h3><div class="cw"><canvas id="ch-epi-typ"></canvas></div></div>
  </div>
</div>

<!-- TAXONOMY -->
<div id="page-taxonomy" class="page">
  <div class="sec-hdr">Object Type Reference</div>
  <table class="tbl">
    <thead><tr><th>Short</th><th>Type Codes</th><th>Description</th><th>Unique #</th></tr></thead>
    <tbody id="tax-tbody"></tbody>
  </table>
</div>

</div></div>

<script>
{JS}

// ── Nav ───────────────────────────────────────────────────────────────────────
function go(id,btn){{
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('active'));
  document.querySelectorAll('.nb').forEach(b=>b.classList.remove('active'));
  document.getElementById('page-'+id).classList.add('active');
  if(btn) btn.classList.add('active');
}}

// ── Chart defaults ────────────────────────────────────────────────────────────
Chart.defaults.color='#4c6490';Chart.defaults.borderColor='#1a2540';
Chart.defaults.font.family='Inter';Chart.defaults.font.size=10;
const GC='rgba(26,37,64,.65)';
function mkC(id,type,labels,datasets,opts={{}}){{
  const el=document.getElementById(id);if(!el)return;
  if(el._ch)el._ch.destroy();
  const iHorz=opts.horz;
  const iStack=opts.stack;
  const sc=type==='pie'||type==='doughnut'?{{}}:{{
    x:{{stacked:iStack,grid:{{color:GC}},ticks:{{color:'#4c6490',font:{{size:9}}}}}},
    y:{{stacked:iStack,grid:{{color:GC}},ticks:{{color:'#4c6490',font:{{size:9}}}}}}
  }};
  el._ch=new Chart(el,{{type,data:{{labels,datasets}},options:{{
    responsive:true,maintainAspectRatio:false,
    plugins:{{
      legend:{{labels:{{boxWidth:opts.lsz||8,padding:8,color:'#7892c0',font:{{size:opts.lsz||8}}}}}},
      tooltip:{{backgroundColor:'#0d1320',borderColor:'#1a2540',borderWidth:1,
        titleFont:{{size:10}},bodyFont:{{size:9}},padding:8}}
    }},
    scales:sc,
    ...(iHorz?{{indexAxis:'y'}}:{{}})
  }}}});
}}

const YEARS=DATA.years;
const DCOL={{
  'HCM':'#a78bfa','Fiori/UI':'#22d3ee','Security':'#ef4444','FI':'#fb923c',
  'PSM/FM':'#86efac','CO':'#6ee7b7','OData/WF':'#67e8f9','Workflow':'#34d399',
  'CFG':'#f59e0b','Custom Z/Y':'#4d90fe','SAP Standard':'#475569',
  'Other':'#334155','EPI-USE':'#0ea5e9'
}};
const TCOL={{'REP':'#818cf8','CLAS':'#4f8ef7','FUNC':'#f59e0b','WF':'#34d399',
  'ENH':'#a78bfa','UI':'#22d3ee','FORM':'#fb923c','CFG':'#fbbf24',
  'MDL':'#22c55e','SEC':'#ef4444','MISC':'#94a3b8','OTH':'#475569','TXT':'#6b7280','INFRA':'#cbd5e1'}};
const ROLES={{'N_MENARD':'Full-Stack Lead','I_KONAKOV':'OO Class Dev','A_SEFIANI':'Functional Senior',
  'V.VAURETTE':'HCM Expert','P_IKOUNA':'Security Admin','F_GUILLOU':'Fiori Dev',
  'S_IGUENINNI':'HCM + Fiori','P.IKOUNA':'Security Admin','M_SPRONK':'FI/CO Consultant',
  'GD_SCHELLINC':'Fiori Dev','R_RIOS':'Consultant','S_ROCHA':'Consultant',
  'N_VIDAL':'HCM Consultant','AN_LEVEQUE':'Developer','G_SONNET':'HCM Dev',
  'C_ISAIA':'PSM Spec','JP_LOPEZ':'Dev Architect','E_FRATNIK':'Security Admin'}};

// Domain data from UDATA
const domKeys=Object.keys(UDATA.domain_unique).sort((a,b)=>UDATA.domain_unique[b].unique-UDATA.domain_unique[a].unique);

// ── OVERVIEW ──────────────────────────────────────────────────────────────────
mkC('ch-nature','doughnut',
  ['Dev/Tech','Config','Security','EPI-USE','Other'],
  [{{data:[UDATA.summary.unique_dev,UDATA.summary.unique_cfg,UDATA.summary.unique_sec,UDATA.summary.unique_epi,
    UDATA.summary.unique_objects-UDATA.summary.unique_dev-UDATA.summary.unique_cfg-UDATA.summary.unique_sec-UDATA.summary.unique_epi],
    backgroundColor:['#4f8ef7','#f59e0b','#ef4444','#0ea5e9','#475569'],borderWidth:0,hoverOffset:5}}]
);

const domForComp=domKeys.filter(d=>d!=='SAP Standard'&&d!=='Other').slice(0,8);
mkC('ch-uniq-vs-mods','bar',domForComp,[
  {{label:'Unique',data:domForComp.map(d=>UDATA.domain_unique[d]?.unique||0),backgroundColor:'rgba(79,142,247,.8)',borderRadius:3,borderWidth:0}},
  {{label:'Mods',  data:domForComp.map(d=>UDATA.domain_unique[d]?.mods  ||0),backgroundColor:'rgba(245,158,11,.6)',borderRadius:3,borderWidth:0}}
],{{lsz:8}});

mkC('ch-domain','bar',domForComp,
  [{{data:domForComp.map(d=>UDATA.domain_unique[d]?.unique||0),
    backgroundColor:domForComp.map(d=>DCOL[d]||'#475569'),borderWidth:0,borderRadius:3}}],
  {{horz:true,lsz:8}}
);

const typeKeys=Object.keys(UDATA.type_unique).sort((a,b)=>UDATA.type_unique[b].unique-UDATA.type_unique[a].unique).slice(0,10);
mkC('ch-types','bar',typeKeys,
  [{{data:typeKeys.map(t=>UDATA.type_unique[t]?.unique||0),
    backgroundColor:typeKeys.map(t=>TCOL[t]||'#475569'),borderWidth:0,borderRadius:3}}],
  {{horz:true,lsz:8}}
);

// ── YEARLY ────────────────────────────────────────────────────────────────────
const ynu=UDATA.year_new_unique;
const natures=['DEV','CFG','SEC','EPI-USE','MISC'];
const nColors=['#4f8ef7','#f59e0b','#ef4444','#0ea5e9','#475569'];
mkC('ch-yr-new','bar',YEARS,natures.map((n,i)=>{{
  return {{label:n,data:YEARS.map(yr=>(ynu[yr]||{{}})[n]||0),
    backgroundColor:nColors[i]+'cc',borderWidth:0,borderRadius:1}}
}}),{{stack:true,lsz:8}});
mkC('ch-yr-trans','bar',YEARS,[{{label:'Transports',
  data:[750,596,790,764,949,875,743,674,1097,333],
  backgroundColor:'rgba(79,142,247,.7)',borderWidth:0,borderRadius:3}}],{{lsz:8}});

// ── DOMAIN NAVIGATOR ─────────────────────────────────────────────────────────
function buildDomTabs(){{
  const ct=document.getElementById('dom-tabs');
  const active=domKeys.filter(d=>d!=='SAP Standard').slice(0,10);
  active.forEach((d,i)=>{{
    const btn=document.createElement('button');
    btn.className='dtab'+(i===0?' active':'');
    btn.textContent=d;
    btn.style.borderColor=DCOL[d]||'#475569';
    btn.style.color=i===0?'#fff':(DCOL[d]||'#7892c0');
    if(i===0)btn.style.background=DCOL[d]||'#4f8ef7';
    btn.onclick=()=>{{
      document.querySelectorAll('.dtab').forEach(b=>{{b.classList.remove('active');const dd=b.textContent;b.style.background='';b.style.color=DCOL[dd]||'#7892c0';}});
      btn.classList.add('active');btn.style.background=DCOL[d];btn.style.color='#fff';
      loadDom(d);
    }};
    ct.appendChild(btn);
  }});
  if(active.length)loadDom(active[0]);
}}
function loadDom(dom){{
  document.getElementById('dom-t1').textContent=dom+' — Unique Objects per Year';
  document.getElementById('dom-t2').textContent=dom+' — Top Contributors (unique)';
  document.getElementById('dom-t3').textContent=dom+' — Contributor Stack (mods)';
  const col=DCOL[dom]||'#4f8ef7';
  // Year data from original DATA (user_year_domain)
  const yr_data=YEARS.map(yr=>Object.values(DATA.domain_user_year[dom]||{{}}).reduce((a,uyrs)=>a+(uyrs[yr]||0),0));
  mkC('ch-dom-uniq','bar',YEARS,[{{label:dom,data:yr_data,backgroundColor:col+'bb',borderWidth:0,borderRadius:3}}],{{lsz:8}});
  const topU=Object.entries(DATA.domain_user_year[dom]||{{}})
    .map(([u,y])=>([u,Object.values(y).reduce((a,b)=>a+b,0)]))
    .filter(([u,v])=>v>0).sort((a,b)=>b[1]-a[1]).slice(0,10);
  mkC('ch-dom-users','bar',topU.map(([u])=>u.replace('_',' ')),
    [{{data:topU.map(([,v])=>v),backgroundColor:col,borderWidth:0,borderRadius:3}}],{{horz:true,lsz:8}});
  const uColors=['#4f8ef7','#22d3ee','#a78bfa','#34d399','#f59e0b','#fb923c','#ef4444','#22c55e'];
  const d2=DATA.domain_user_year[dom]||{{}};
  const stackUsers=Object.entries(d2).filter(([u,y])=>Object.values(y).reduce((a,b)=>a+b,0)>5)
    .sort((a,b)=>Object.values(b[1]).reduce((x,y)=>x+y,0)-Object.values(a[1]).reduce((x,y)=>x+y,0)).slice(0,8);
  mkC('ch-dom-stack','bar',YEARS,stackUsers.map(([u,yrs],i)=>{{
    return{{label:u.replace('_',' '),data:YEARS.map(yr=>yrs[yr]||0),
      backgroundColor:uColors[i%uColors.length]+'cc',borderWidth:0,borderRadius:1}}
  }}),{{stack:true,lsz:8}});
}}

// ── PACKAGE BROWSER ───────────────────────────────────────────────────────────
function buildPackages(){{
  const pkgs=UDATA.top_packages.slice(0,20);
  mkC('ch-pkg-uniq','bar',pkgs.map(p=>p.pkg),
    [{{data:pkgs.map(p=>p.unique),backgroundColor:pkgs.map(p=>DCOL[p.dom]||'#4f8ef7'),borderWidth:0,borderRadius:3}}],
    {{horz:true,lsz:8}});
  mkC('ch-pkg-mods','bar',pkgs.map(p=>p.pkg),
    [{{data:pkgs.map(p=>p.mods),backgroundColor:pkgs.map(p=>(DCOL[p.dom]||'#4f8ef7')+'88'),borderWidth:0,borderRadius:3}}],
    {{horz:true,lsz:8}});
  const domBadge={{HCM:'bd-hcm','Fiori/UI':'bd-fiori',Security:'bd-sec',FI:'bd-cfg','PSM/FM':'bd-cfg',Workflow:'bd-dev','Custom Z/Y':'bd-dev',Custom:'bd-dev'}};
  const tbody=document.getElementById('pkg-tbody');
  pkgs.forEach(p=>{{
    const avg=p.unique>0?(p.mods/p.unique).toFixed(1):'—';
    const bc=domBadge[p.dom]||'bd-dev';
    const samples=(p.samples||[]).slice(0,2).join(', ');
    tbody.innerHTML+=`<tr>
      <td><strong>${{p.pkg}}</strong></td>
      <td><span class="bd ${{bc}}">${{p.dom}}</span></td>
      <td><strong>${{p.unique}}</strong></td>
      <td>${{p.mods}}</td>
      <td>${{avg}}x</td>
      <td>${{p.users}}</td>
      <td>${{p.years}}</td>
      <td style="color:var(--mu);font-size:.68rem">${{samples}}</td>
    </tr>`;
  }});
}}

// ── CONFIG ELEMENTS ───────────────────────────────────────────────────────────
const CFG_AREA={{
  AGR_TIMEB:'Security Roles',UST12:'Authorizations',USR10:'Auth Objects',USR11:'Auth Fields',
  USR12:'Auth Values',UST10S:'Auth Groups',TVDIR:'Tcode security',TDDAT:'Table auth',
  SPERS_OBJ:'Personalization',V_T510:'Pay scales',V_T510_C:'Pay scale groups',
  V_T7UNPAD_DSDA:'HCM Payroll',V_T7UNPAD_DSPA:'HCM Config',UCUM020:'Fund Mgmt',
  UCUM04C:'FM Commitment',UCUM060:'Fund Center',UGWB1101:'FM Integration',
}};
function buildConfig(){{
  const cfg=UDATA.top_cfg_tables.slice(0,15);
  mkC('ch-cfg-hot','bar',cfg.map(c=>c.name),
    [{{data:cfg.map(c=>c.mods),backgroundColor:cfg.map(c=>{{
      if(c.obj_type==='TABU'&&c.name.startsWith('AGR'))return'rgba(239,68,68,.8)';
      if(c.obj_type==='TABU'&&c.name.startsWith('USR'))return'rgba(239,68,68,.6)';
      if(c.obj_type==='VDAT')return'rgba(167,139,250,.8)';
      return'rgba(245,158,11,.8)';
    }}),borderWidth:0,borderRadius:3}}],{{horz:true,lsz:8}});
  // Type breakdown
  const typeCount={{}};
  UDATA.top_cfg_tables.forEach(c=>{{typeCount[c.obj_type]=(typeCount[c.obj_type]||0)+1;}});
  mkC('ch-cfg-type','doughnut',Object.keys(typeCount),
    [{{data:Object.values(typeCount),
      backgroundColor:['#f59e0b','#a78bfa','#22d3ee','#fb923c','#ef4444'],borderWidth:0}}],{{lsz:8}});
  const tbody=document.getElementById('cfg-tbody');
  UDATA.top_cfg_tables.slice(0,40).forEach(c=>{{
    const area=CFG_AREA[c.name]||(c.name.startsWith('T7UN')||c.name.startsWith('V_T')?'HCM':'Config');
    tbody.innerHTML+=`<tr>
      <td><code>${{c.name}}</code></td>
      <td><code style="color:var(--cfg)">${{c.obj_type}}</code></td>
      <td><span class="hot-badge">${{c.mods}}x</span></td>
      <td>${{c.users}}</td>
      <td>${{c.years}}</td>
      <td style="color:var(--mu2)">${{area}}</td>
    </tr>`;
  }});
}}

// ── TEAM PROFILES ─────────────────────────────────────────────────────────────
function buildUserTabs(){{
  const users=DATA.top_users.filter(u=>u!=='EPI-USE_LABS');
  const ct=document.getElementById('user-tabs');
  users.forEach((u,i)=>{{
    const label=u.split('_').map(w=>w[0]+w.slice(1).toLowerCase()).join(' ');
    const btn=document.createElement('button');
    btn.className='utab'+(i===0?' active':'');
    btn.textContent=label;btn.dataset.u=u;
    btn.onclick=()=>{{document.querySelectorAll('.utab').forEach(b=>b.classList.remove('active'));btn.classList.add('active');loadProfile(u);}};
    ct.appendChild(btn);
  }});
  if(users.length)loadProfile(users[0]);
}}
function loadProfile(u){{
  const role=ROLES[u]||'Contributor';
  const label=u.split('_').map(w=>w[0]+w.slice(1).toLowerCase()).join(' ');
  document.getElementById('prof-t1').textContent=label+' — Objects by Year';
  document.getElementById('prof-t2').textContent=label+' — Domain';
  document.getElementById('prof-t3').textContent=label+' — Types';
  const uyt=DATA.user_year_type[u]||{{}};
  const activeTy=DATA.types.filter(t=>YEARS.some(yr=>(uyt[yr]||{{}})[t]));
  mkC('ch-prof-yr','bar',YEARS,activeTy.map(t=>{{
    return{{label:t,data:YEARS.map(yr=>(uyt[yr]||{{}})[t]||0),
      backgroundColor:(TCOL[t]||'#4f8ef7')+'bb',borderWidth:0,borderRadius:1}}
  }}),{{stack:true,lsz:7}});
  const uyd=DATA.user_year_domain[u]||{{}};
  const doms=Object.keys(DCOL).filter(d=>d!=='EPI-USE');
  const dvals=doms.map(d=>YEARS.reduce((a,yr)=>a+(uyd[yr]||{{}})[d]||0,0));
  const nonZ=doms.map((d,i)=>([d,dvals[i]])).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]).slice(0,8);
  mkC('ch-prof-dom','bar',nonZ.map(([d])=>d),[{{data:nonZ.map(([,v])=>v),
    backgroundColor:nonZ.map(([d])=>DCOL[d]),borderWidth:0,borderRadius:3}}],{{horz:true,lsz:8}});
  const typeTots=DATA.types.map(t=>YEARS.reduce((a,yr)=>a+(uyt[yr]||{{}})[t]||0,0));
  const nonZT=DATA.types.map((t,i)=>([t,typeTots[i]])).filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]);
  mkC('ch-prof-typ','bar',nonZT.map(([t])=>t),[{{data:nonZT.map(([,v])=>v),
    backgroundColor:nonZT.map(([t])=>TCOL[t]||'#4f8ef7'),borderWidth:0,borderRadius:3}}],{{lsz:8}});
  // Profile card using UDATA
  const uUniq=UDATA.user_unique[u]||{{}};
  const yrTots=YEARS.map((yr,i)=>([yr,Object.values(uyt[yr]||{{}}).reduce((a,b)=>a+b,0)]));
  const peak=yrTots.reduce((a,b)=>b[1]>a[1]?b:a,['?',0]);
  const topDom=nonZ.length>0?nonZ[0][0]:'—';
  const topTyp=nonZT.length>0?nonZT[0][0]:'—';
  document.getElementById('prof-card-body').innerHTML=`
    <div style="margin-bottom:8px"><span class="bd bd-dev">${{role}}</span></div>
    <div class="mbr"><span class="mbl">Unique Obj Touched</span><strong style="font-family:'JetBrains Mono',monospace">${{(uUniq.touched||0).toLocaleString()}}</strong></div>
    <div class="mbr"><span class="mbl">Unique Owned (solo)</span><span style="color:var(--mu2)">${{(uUniq.owned||0).toLocaleString()}}</span></div>
    <div class="mbr"><span class="mbl">Peak Year</span><strong>${{peak[0]}} <span style="color:var(--mu);font-weight:400">(${{peak[1].toLocaleString()}})</span></strong></div>
    <div class="mbr"><span class="mbl">Top Domain</span><span style="color:${{DCOL[topDom]||'var(--txt)'}};">${{topDom}}</span></div>
    <div class="mbr"><span class="mbl">Top Type</span><span style="color:${{TCOL[topTyp]||'var(--txt)'}};">${{topTyp}}</span></div>
    <hr style="border-color:var(--b);margin:8px 0">
    ${{yrTots.filter(([,v])=>v>0).map(([yr,v])=>`
    <div class="mbr"><span class="mbl">${{yr}}</span>
      <div class="mbt"><div class="mbf" style="width:${{Math.round(v/Math.max(...yrTots.map(x=>x[1])),1)*100}}%;background:var(--acc)"></div></div>
      <span class="mbv">${{v.toLocaleString()}}</span></div>`).join('')}}
  `;
}}

// ── CONTRIBUTION TABLE ────────────────────────────────────────────────────────
function buildTeamTable(){{
  const users=DATA.top_users.filter(u=>u!=='EPI-USE_LABS');
  const tbody=document.getElementById('team-tbody');
  const domKeys2=['HCM','Fiori/UI','Security','FI','OData/WF','Workflow','Custom Z/Y'];
  users.forEach(u=>{{
    const role=ROLES[u]||'Contributor';
    const label=u.split('_').map(w=>w[0]+w.slice(1).toLowerCase()).join(' ');
    const uu=UDATA.user_unique[u]||{{}};
    const domVals=domKeys2.map(d=>(uu.domains||{{}})[d]||0);
    tbody.innerHTML+=`<tr>
      <td><strong>${{label}}</strong></td>
      <td><span class="bd bd-dev">${{role}}</span></td>
      <td><strong>${{(uu.touched||0).toLocaleString()}}</strong></td>
      <td>${{(uu.owned||0).toLocaleString()}}</td>
      ${{domVals.map((v,i)=>`<td style="color:${{v>0?DCOL[domKeys2[i]]:'var(--mu)'}}">${{v>0?v.toLocaleString():'—'}}</td>`).join('')}}
    </tr>`;
  }});
}}

// ── TAXONOMY ──────────────────────────────────────────────────────────────────
function buildTaxonomy(){{
  const rows=[
    ['REP','PROG REPS REPT REPY','Executable programs & includes'],
    ['CLAS','CLAS INTF METH CINC','ABAP OO classes & interfaces'],
    ['FUNC','FUGR FUNC FUGA','Function groups, RFCs, BAPIs'],
    ['WF','SWFP SWFT SWED PDWS','Workflow templates & tasks'],
    ['ENH','ENHO ENHS ENHD ENHC','Enhancement implementations (BAdI)'],
    ['UI','WAPP SMIM WDYC IWSV SICF','Fiori apps, BSP, WebDynpro, OData'],
    ['FORM','SFPF SSFO DMEE F30','Adobe forms, Smart Forms, payments'],
    ['MDL','TABL DOMA DTEL VIEW INDX','Database tables & data model'],
    ['CFG','TABU NROB CUS0 TDAT VDAT','Customizing table entries, HR views'],
    ['SEC','ACGR AUTH ACID SUSC','Authorization roles & objects'],
    ['TXT','MSAG DOCU SHI3','Message classes, documentation'],
    ['META','RELE MERG','Transport metadata (not real objects)'],
  ];
  const tbody=document.getElementById('tax-tbody');
  rows.forEach(([ts,codes,desc])=>{{
    const uniq=(UDATA.type_unique[ts]||{{}}).unique||'—';
    tbody.innerHTML+=`<tr><td><code>${{ts}}</code></td><td><code>${{codes}}</code></td><td>${{desc}}</td><td>${{uniq}}</td></tr>`;
  }});
}}

// ── EPI-USE ───────────────────────────────────────────────────────────────────
mkC('ch-epi-yr','bar',YEARS,[{{label:'EPI-USE',
  data:YEARS.map(yr=>DATA.epi_by_year?.[yr]||0),
  backgroundColor:'rgba(14,165,233,.75)',borderWidth:0,borderRadius:3}}],{{lsz:8}});
mkC('ch-epi-typ','doughnut',['ABAP Classes','Auth Objects','Config','Other'],
  [{{data:[2883,88,50,12],backgroundColor:['#0ea5e9','#38bdf8','#7dd3fc','#bae6fd'],borderWidth:0}}],{{lsz:8}});

// ── Init ──────────────────────────────────────────────────────────────────────
buildDomTabs();
buildPackages();
buildConfig();
buildUserTabs();
buildTeamTable();
buildTaxonomy();
</script>
</body>
</html>"""

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(HTML)

print(f"Saved cts_dashboard.html ({os.path.getsize('cts_dashboard.html')//1024}KB)")
print("Pages: Overview, Year Timeline, Domain Navigator, Package Browser, Config Elements,")
print("       Team Profiles, Contribution Table, Hotspot Objects, EPI-USE, Taxonomy")
