"""Rebuild connectivity diagram with vis.js inlined and no duplicate node IDs."""
import sqlite3, json, re, os
from collections import defaultdict

DB = os.path.join(os.path.dirname(__file__), '..', 'sap_data_extraction', 'sqlite', 'p01_gold_master_data.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

# ---- Parse RFC destinations ----
cur.execute("SELECT RFCDEST, RFCTYPE, RFCOPTIONS FROM rfcdes ORDER BY RFCTYPE, RFCDEST")
rows = cur.fetchall()

def parse_opts(opts):
    result = {}
    if not opts: return result
    for pair in opts.split(','):
        if '=' in pair:
            k, v = pair.split('=', 1)
            result[k.strip()] = v.strip()
    return result

SYSTEM_META = {
    'P01': {'label':'Production ECC','cat':'Production','color':'#E74C3C'},
    'P11': {'label':'S/4 Production','cat':'Production','color':'#C0392B'},
    'D01': {'label':'ECC Development','cat':'Development','color':'#3498DB'},
    'D11': {'label':'S/4 Development','cat':'Development','color':'#2980B9'},
    'TS1': {'label':'Test System 1','cat':'Test/QA','color':'#E67E22'},
    'TS2': {'label':'Test System 2','cat':'Test/QA','color':'#E67E22'},
    'TS3': {'label':'Test System 3','cat':'Test/QA','color':'#E67E22'},
    'TS4': {'label':'Test System 4','cat':'Test/QA','color':'#D35400'},
    'V01': {'label':'ECC Validation','cat':'Validation','color':'#9B59B6'},
    'V11': {'label':'S/4 Validation','cat':'Validation','color':'#8E44AD'},
    'BWD': {'label':'BW Development','cat':'BW/Analytics','color':'#1ABC9C'},
    'BWP': {'label':'BW Production','cat':'BW/Analytics','color':'#16A085'},
    'BRP': {'label':'BW Reporting','cat':'BW/Analytics','color':'#1ABC9C'},
    'SBP': {'label':'SolMan Production','cat':'Solution Manager','color':'#F39C12'},
    'SMA': {'label':'SolMan QA','cat':'Solution Manager','color':'#F39C12'},
    'SMP': {'label':'SolMan Dev','cat':'Solution Manager','color':'#F39C12'},
    'A01': {'label':'App Server 01','cat':'Infrastructure','color':'#95A5A6'},
    'A11': {'label':'App Server 11','cat':'Infrastructure','color':'#95A5A6'},
    'SAP_OSS': {'label':'SAP Support','cat':'External','color':'#7F8C8D'},
    'P11_OLD': {'label':'P11 Legacy','cat':'Decommissioned','color':'#555'},
}

IP_MAP = {
    '10.101.21.123': 'A01',
    '10.101.23.102': 'A01',
    '10.101.23.103': 'A11',
    '10.101.23.112': 'D01',
    '10.101.23.125': 'P01',
    '10.101.23.145': 'SMP',
    '172.16.4.107': 'SBP',
}

sys_conns = defaultdict(list)

for dest, rtype, opts in rows:
    if rtype != '3': continue
    parsed = parse_opts(opts)
    host = parsed.get('H', '')
    user = parsed.get('U', '')

    sys_id = None
    m = re.search(r'hq-sap-(\w+)', host, re.I)
    if m:
        sys_id = m.group(1).upper()
    elif re.match(r'\d+\.\d+\.\d+\.\d+', host):
        sys_id = IP_MAP.get(host)
    elif '/H/' in host:
        sys_id = 'SAP_OSS'
    elif host:
        raw = host.upper().replace('HQ-','')
        if 'P11-OLD' in raw: sys_id = 'P11_OLD'
        else: sys_id = raw

    if not sys_id or sys_id == 'P01':
        continue

    purpose = 'General'
    if 'TMSADM' in user or 'TMS' in dest: purpose = 'Transport Management'
    elif 'ALEREMOTE' in user or 'ALE_REMOTE' in user: purpose = 'ALE/IDoc Distribution'
    elif 'DSM' in user or 'DSM' in dest: purpose = 'Diagnostics/Monitoring'
    elif 'FINBTR' in user or 'FINBTR' in dest: purpose = 'Bank/Treasury Transfer'
    elif 'BWREMOTE' in user: purpose = 'BW Data Transfer'
    elif 'TRUSTING' in dest: purpose = 'Trusted RFC'
    elif 'SMB_' in user: purpose = 'Solution Manager'
    elif 'CUA_' in user: purpose = 'Central User Admin'
    elif 'OSS_RFC' in user: purpose = 'SAP Support'
    elif 'TERM_RFC' in user or 'GLOS' in user: purpose = 'SAP Terminology'

    sys_conns[sys_id].append({'dest': dest, 'user': user, 'purpose': purpose})

# ---- External integrations ----
externals = {
    'MuleSoft': {'color':'#3498DB', 'conns':['MULESOFT_PROD','MULESOFT_P01_IDOC'], 'impact':'API integrations + IDoc routing stops'},
    'UNJSPF': {'color':'#9B59B6', 'conns':['UNJSPF_INTERFACE1','UNICC_XI'], 'impact':'Pension fund interface fails'},
    'AWS': {'color':'#FF9900', 'conns':['CSI_AWS_S3','CSI_AWS_EC2'], 'impact':'Cloud storage + compute unavailable'},
    'Fiori GW': {'color':'#2ECC71', 'conns':['fabsprd1-4 (16 HTTP)'], 'impact':'ALL Fiori apps + ESS/MSS down'},
    'SAP Support': {'color':'#7F8C8D', 'conns':['SAP-SUPPORT_PORTAL'], 'impact':'SAP notes + support access lost'},
}

# ---- Build vis.js data ----
nodes = []
edges = []

# P01 central
nodes.append({
    'id': 'P01', 'label': 'P01\nProduction ECC',
    'color': '#E74C3C', 'shape': 'box',
    'font': {'color':'#fff','size':16,'bold':True},
    'size': 55, 'borderWidth': 3, 'shadow': True,
    'title': 'P01 - UNESCO Production ECC\nHost: hq-sap-p01\nClient: 350\n38 tables in Gold DB'
})

for sys_id, conns in sys_conns.items():
    meta = SYSTEM_META.get(sys_id, {'label':sys_id,'cat':'Other','color':'#95A5A6'})
    purposes = list(set(c['purpose'] for c in conns))
    users = list(set(c['user'] for c in conns if c['user']))

    impact_lines = []
    for p in purposes:
        if 'Transport' in p: impact_lines.append('Transport chain breaks')
        if 'ALE' in p: impact_lines.append('IDoc distribution fails')
        if 'Diagnostics' in p: impact_lines.append('System monitoring blind')
        if 'Bank' in p: impact_lines.append('Bank transfers blocked')
        if 'BW' in p: impact_lines.append('BW reporting stale')

    title = f"{sys_id} - {meta['label']}\nCategory: {meta['cat']}\nConnections: {len(conns)}\nPurposes: {', '.join(purposes)}\nUsers: {', '.join(users[:4])}"
    if impact_lines:
        title += '\n\nIF DOWN:\n' + '\n'.join(f'  {x}' for x in impact_lines)

    nodes.append({
        'id': sys_id, 'label': f"{sys_id}\n{meta['label']}",
        'color': meta['color'], 'shape': 'box',
        'font': {'color':'#fff','size':11},
        'size': 20 + len(conns) * 3,
        'title': title
    })
    edges.append({
        'from': 'P01', 'to': sys_id,
        'label': f"{len(conns)} RFC",
        'width': max(1, len(conns) // 2),
        'color': {'color': meta['color'], 'opacity': 0.7},
        'arrows': 'to'
    })

for name, ext in externals.items():
    ext_id = f'EXT_{name.upper().replace(" ","_").replace("/","")}'
    nodes.append({
        'id': ext_id, 'label': name,
        'color': ext['color'], 'shape': 'diamond',
        'font': {'color':'#fff','size':11},
        'size': 28,
        'title': f"{name}\nConnections: {', '.join(ext['conns'])}\n\nIF DOWN:\n  {ext['impact']}"
    })
    edges.append({
        'from': 'P01', 'to': ext_id,
        'label': str(len(ext['conns'])),
        'dashes': True,
        'color': {'color': ext['color'], 'opacity': 0.6},
        'arrows': 'to'
    })

# Verify uniqueness
ids = [n['id'] for n in nodes]
dupes = [x for x in ids if ids.count(x) > 1]
assert not dupes, f"DUPLICATE IDS: {dupes}"

# ---- IDoc + Job stats ----
cur.execute("SELECT MESTYP, COUNT(*) FROM edidc GROUP BY MESTYP ORDER BY COUNT(*) DESC LIMIT 10")
idoc_stats = cur.fetchall()
cur.execute("SELECT PROGNAME, COUNT(DISTINCT JOBNAME), COUNT(*) FROM tbtcp GROUP BY PROGNAME ORDER BY COUNT(*) DESC LIMIT 15")
job_stats = cur.fetchall()
conn.close()

# ---- Read vis.js ----
vis_path = os.path.join(os.path.dirname(__file__), 'vis-network.min.js')
vis_js = open(vis_path, 'r', encoding='utf-8').read()

nodes_json = json.dumps(nodes)
edges_json = json.dumps(edges)

idoc_rows = ''.join(f'<tr><td>{m}</td><td>{c:,}</td></tr>' for m, c in idoc_stats)
job_rows = ''.join(f'<tr><td>{p}</td><td>{j}</td><td>{r:,}</td></tr>' for p, j, r in job_stats)

html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>UNESCO SAP System Connectivity Map</title>
<script>{vis_js}</script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0a1a;font-family:'Segoe UI',sans-serif;color:#ddd}}
#header{{padding:14px 24px;background:#101030;border-bottom:2px solid #1a1a4e;display:flex;justify-content:space-between;align-items:center}}
#header h1{{font-size:18px;color:#4ECDC4}}
.meta{{font-size:11px;color:#888}}
#main{{display:flex;height:calc(100vh - 56px)}}
#network{{flex:1;background:#0d0d25}}
#sidebar{{width:420px;background:#101030;border-left:1px solid #1a1a4e;overflow-y:auto;padding:16px}}
.section{{margin-bottom:20px}}
.section h3{{color:#4ECDC4;font-size:13px;margin-bottom:8px;border-bottom:1px solid #1a1a4e;padding-bottom:4px}}
table{{width:100%;border-collapse:collapse;font-size:11px}}
th{{text-align:left;color:#888;padding:3px 6px;border-bottom:1px solid #1a1a4e}}
td{{padding:3px 6px;border-bottom:1px solid #0d0d25}}
.legend{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}}
.leg-item{{display:flex;align-items:center;gap:4px;font-size:10px}}
.leg-dot{{width:10px;height:10px;border-radius:2px}}
.leg-diamond{{width:10px;height:10px;transform:rotate(45deg)}}
#click-info{{background:#0d0d25;border:1px solid #1a1a4e;border-radius:6px;padding:12px;min-height:80px;font-size:11px;line-height:1.6;white-space:pre-line}}
</style></head>
<body>
<div id="header">
  <h1>UNESCO SAP System Connectivity Map</h1>
  <span class="meta">P01 Production | {len(nodes)} systems | {len(edges)} connections | Click any node for impact analysis</span>
</div>
<div id="main">
  <div id="network"></div>
  <div id="sidebar">
    <div class="section">
      <h3>Legend</h3>
      <div class="legend">
        <div class="leg-item"><div class="leg-dot" style="background:#E74C3C"></div>Production</div>
        <div class="leg-item"><div class="leg-dot" style="background:#3498DB"></div>Development</div>
        <div class="leg-item"><div class="leg-dot" style="background:#E67E22"></div>Test/QA</div>
        <div class="leg-item"><div class="leg-dot" style="background:#9B59B6"></div>Validation</div>
        <div class="leg-item"><div class="leg-dot" style="background:#1ABC9C"></div>BW/Analytics</div>
        <div class="leg-item"><div class="leg-dot" style="background:#F39C12"></div>Solution Manager</div>
        <div class="leg-item"><div class="leg-diamond" style="background:#E74C3C"></div>External</div>
      </div>
    </div>
    <div class="section">
      <h3>Click a Node for Details</h3>
      <div id="click-info">Click any system node to see:
- Connected RFC destinations
- Integration purposes
- Impact if system goes down</div>
    </div>
    <div class="section">
      <h3>Impact Analysis</h3>
      <table>
        <tr><th>Scenario</th><th>Systems</th><th>Risk</th><th>Impact</th></tr>
        <tr><td>BW Landscape</td><td>BRP, BWD, BWP</td><td style="color:#E74C3C;font-weight:bold">HIGH</td><td>All BW reporting stops. RSINFO IDocs fail.</td></tr>
        <tr><td>Dev/Transport</td><td>TS1-4, D01, V01</td><td style="color:#E67E22;font-weight:bold">MEDIUM</td><td>Transport chain breaks. No code to prod.</td></tr>
        <tr><td>MuleSoft ESB</td><td>External</td><td style="color:#E74C3C;font-weight:bold">HIGH</td><td>API integrations + IDoc routing stops.</td></tr>
        <tr><td>Fiori Gateway</td><td>fabsprd1-4</td><td style="color:#E74C3C;font-weight:bold">HIGH</td><td>ALL Fiori apps + ESS/MSS down.</td></tr>
      </table>
    </div>
    <div class="section">
      <h3>Top Background Jobs</h3>
      <table><tr><th>Program</th><th>Jobs</th><th>Runs</th></tr>{job_rows}</table>
    </div>
    <div class="section">
      <h3>IDoc Message Types</h3>
      <table><tr><th>Type</th><th>Count</th></tr>{idoc_rows}</table>
    </div>
  </div>
</div>
<script>
var nodes = new vis.DataSet({nodes_json});
var edges = new vis.DataSet({edges_json});
var container = document.getElementById('network');
var network = new vis.Network(container, {{nodes: nodes, edges: edges}}, {{
  physics: {{
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {{gravitationalConstant: -80, centralGravity: 0.01, springLength: 150, springConstant: 0.04}},
    stabilization: {{iterations: 200}}
  }},
  nodes: {{borderWidth: 2, shadow: {{enabled: true, color: 'rgba(0,0,0,0.3)', size: 8}}, font: {{face: 'Segoe UI'}}}},
  edges: {{font: {{size: 9, color: '#666', strokeWidth: 0}}, smooth: {{type: 'continuous'}}}},
  interaction: {{hover: true, tooltipDelay: 100}}
}});
network.on('click', function(params) {{
  var info = document.getElementById('click-info');
  if (params.nodes.length > 0) {{
    var node = nodes.get(params.nodes[0]);
    if (node && node.title) info.innerText = node.title;
  }}
}});
</script>
</body></html>"""

out = os.path.join(os.path.dirname(__file__), 'connectivity_diagram.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Written: {os.path.getsize(out):,} bytes")
print(f"Nodes: {len(nodes)}, Edges: {len(edges)}, No duplicates")
