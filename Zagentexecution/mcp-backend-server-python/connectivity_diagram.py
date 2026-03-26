"""
connectivity_diagram.py — UNESCO SAP System Connectivity Map
=============================================================
Generates an interactive HTML diagram showing:
- All SAP systems connected from P01
- RFC destinations grouped by target system
- Integration points (Coupa, EBS, MuleSoft, UNJSPF)
- Impact analysis: "If system X goes down, what breaks?"

Usage:
    python connectivity_diagram.py
"""

import sqlite3
import json
import re
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
DB_PATH = PROJECT_ROOT / "Zagentexecution/sap_data_extraction/sqlite/p01_gold_master_data.db"
OUTPUT = PROJECT_ROOT / "Zagentexecution/mcp-backend-server-python/connectivity_diagram.html"


def parse_options(opts):
    result = {}
    if not opts:
        return result
    for pair in opts.split(','):
        if '=' in pair:
            k, v = pair.split('=', 1)
            result[k.strip()] = v.strip()
    return result


def extract_system_id(host):
    match = re.search(r'hq-sap-(\w+)', host, re.I)
    if match:
        return match.group(1).upper()
    if re.match(r'\d+\.\d+\.\d+\.\d+', host):
        return None
    return host.upper()[:12] if host else None


RFC_TYPE_LABELS = {
    '3': 'SAP-to-SAP', 'I': 'Internal', 'T': 'TCP/IP',
    'G': 'HTTP', 'X': 'XML/HTTP', 'H': 'HTTP-ABAP', 'L': 'Logical',
}

SYSTEM_ROLES = {
    'D01': ('Development', 'ECC Dev', '#3498DB'),
    'D11': ('Development', 'S/4 Dev', '#2980B9'),
    'TS1': ('Test/QA', 'Test System 1', '#E67E22'),
    'TS2': ('Test/QA', 'Test System 2', '#E67E22'),
    'TS3': ('Test/QA', 'Test System 3', '#E67E22'),
    'TS4': ('Test/QA', 'Test System 4', '#E67E22'),
    'V01': ('Validation', 'ECC Validation', '#9B59B6'),
    'V11': ('Validation', 'S/4 Validation', '#8E44AD'),
    'P11': ('Production', 'S/4 Production', '#E74C3C'),
    'BWD': ('BW', 'BW Development', '#1ABC9C'),
    'BWP': ('BW', 'BW Production', '#16A085'),
    'BRP': ('BW', 'BW Reporting', '#1ABC9C'),
    'SBP': ('Solution Manager', 'SolMan Prod', '#F39C12'),
    'SMA': ('Solution Manager', 'SolMan QA', '#F39C12'),
    'SMP': ('Solution Manager', 'SolMan Dev', '#F39C12'),
}

INTEGRATION_TARGETS = {
    'COUPA': {'name': 'Coupa (Procurement)', 'color': '#E74C3C', 'impact': [
        'P2P invoice posting (YFI_COUPA_POSTING_FILE)',
        'Coupa payment status notifications',
    ]},
    'EBS': {'name': 'EBS (Bank)', 'color': '#2ECC71', 'impact': [
        'SWIFT payment processing (ZFI_SWIFT_UPLOAD_BCM)',
        'Bank statement import (RBNK_IMPORT)',
    ]},
    'MULESOFT': {'name': 'MuleSoft (ESB)', 'color': '#3498DB', 'impact': [
        'IDoc routing (MULESOFT_P01_IDOC)',
        'API-based integrations',
    ]},
    'UNJSPF': {'name': 'UNJSPF (Pension)', 'color': '#9B59B6', 'impact': [
        'Pension fund interface (UNJSPF_INTERFACE1)',
        'Staff pension contributions',
    ]},
    'AWS': {'name': 'AWS Cloud', 'color': '#FF9900', 'impact': [
        'S3 storage (CSI_AWS_S3)',
        'EC2 compute (CSI_AWS_EC2)',
    ]},
    'SAP_SUPPORT': {'name': 'SAP Support Portal', 'color': '#888888', 'impact': [
        'Note downloads', 'OSS connections', 'SLD registration',
    ]},
}


def build_data():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # RFC destinations
    cur.execute("SELECT RFCDEST, RFCTYPE, RFCOPTIONS FROM rfcdes")
    rfc_rows = cur.fetchall()

    # Job execution stats (no JOIN — TBTCP only for speed)
    cur.execute("""
        SELECT PROGNAME, COUNT(DISTINCT JOBNAME) as jobs, COUNT(*) as steps
        FROM tbtcp WHERE PROGNAME IS NOT NULL AND PROGNAME != ''
        GROUP BY PROGNAME ORDER BY steps DESC LIMIT 30
    """)
    top_jobs = cur.fetchall()

    # IDoc stats
    cur.execute("SELECT MESTYP, COUNT(*) FROM edidc GROUP BY MESTYP ORDER BY COUNT(*) DESC")
    idoc_stats = cur.fetchall()

    conn.close()

    # Build system map
    systems = defaultdict(lambda: {'dests': [], 'users': set(), 'purposes': set()})

    integrations = defaultdict(lambda: {'dests': [], 'hosts': set()})

    for dest, rtype, opts in rfc_rows:
        parsed = parse_options(opts)
        host = parsed.get('H', '')
        user = parsed.get('U', '')
        dest_upper = dest.upper()

        if rtype == '3':
            sys_id = extract_system_id(host)
            if sys_id:
                systems[sys_id]['dests'].append(dest)
                if user:
                    systems[sys_id]['users'].add(user)
                # Classify purpose
                if 'TMSADM' in dest or 'TMSSUP' in dest:
                    systems[sys_id]['purposes'].add('Transport Management')
                elif 'ALE' in user or 'MDT' in dest:
                    systems[sys_id]['purposes'].add('ALE/IDoc Distribution')
                elif 'DSM' in dest or 'DSM3' in dest:
                    systems[sys_id]['purposes'].add('Diagnostics/Monitoring')
                elif 'TRUSTING' in dest:
                    systems[sys_id]['purposes'].add('Trusted RFC')
                elif 'LOGON' in dest:
                    systems[sys_id]['purposes'].add('Logon Group')
                elif 'FINBTR' in dest:
                    systems[sys_id]['purposes'].add('Bank Transfer')
                elif 'CUA' in user:
                    systems[sys_id]['purposes'].add('Central User Admin')
                elif 'GLOSSARY' in dest or 'SAPTERM' in dest:
                    systems[sys_id]['purposes'].add('SAP Terminology')
                elif 'BW' in user or 'BW' in dest:
                    systems[sys_id]['purposes'].add('BW Data Transfer')

        elif rtype == 'G':
            for key, info in INTEGRATION_TARGETS.items():
                if key.lower() in dest_upper.lower() or key.lower() in host.lower():
                    integrations[key]['dests'].append(dest)
                    integrations[key]['hosts'].add(host)
            if 'fabsprd' in host.lower():
                integrations['FIORI_GW']['dests'].append(dest)
                integrations['FIORI_GW']['hosts'].add(host)

        elif rtype == 'T':
            if 'MULESOFT' in dest_upper or 'MULE' in dest_upper:
                integrations['MULESOFT']['dests'].append(dest)
            elif 'COUPA' in dest_upper:
                integrations['COUPA']['dests'].append(dest)

        elif rtype == 'H':
            if 'UNJSPF' in dest_upper or 'unjspf' in host:
                integrations['UNJSPF']['dests'].append(dest)

    return systems, integrations, top_jobs, idoc_stats


def generate_html(systems, integrations, top_jobs, idoc_stats):
    # Build nodes and edges for vis.js
    nodes = []
    edges = []

    # P01 central node
    nodes.append({
        'id': 'P01', 'label': 'P01\\nProduction ECC',
        'color': '#E74C3C', 'shape': 'box', 'font': {'color': '#fff', 'size': 14, 'bold': True},
        'size': 50, 'borderWidth': 3, 'shadow': True,
        'title': 'P01 — UNESCO Production ECC<br>Host: hq-sap-p01<br>Client: 350<br>38 tables in Gold DB'
    })

    # SAP systems
    for sys_id, info in sorted(systems.items()):
        if any(x in sys_id for x in ['OSS', 'LDCI', 'SAPDP']):
            continue  # Skip SAP Support router hops
        role_info = SYSTEM_ROLES.get(sys_id, ('Other', sys_id, '#95A5A6'))
        role_cat, role_desc, color = role_info
        purposes = ', '.join(info['purposes']) if info['purposes'] else 'General'
        users = ', '.join(info['users']) if info['users'] else 'N/A'

        impact_lines = []
        if 'Transport Management' in info['purposes']:
            impact_lines.append('Transport import/export STOPS')
        if 'ALE/IDoc Distribution' in info['purposes']:
            impact_lines.append('IDoc distribution FAILS')
        if 'BW Data Transfer' in info['purposes']:
            impact_lines.append('BW reporting data STALE')
        if 'Diagnostics/Monitoring' in info['purposes']:
            impact_lines.append('System monitoring BLIND')
        if 'Bank Transfer' in info['purposes']:
            impact_lines.append('Bank transfers BLOCKED')

        impact_html = '<br>'.join(f'⚠ {i}' for i in impact_lines) if impact_lines else 'Low impact'

        title = (f'<b>{sys_id} — {role_desc}</b><br>'
                 f'Category: {role_cat}<br>'
                 f'Connections: {len(info["dests"])}<br>'
                 f'Purposes: {purposes}<br>'
                 f'Users: {users}<br>'
                 f'<br><b>If DOWN:</b><br>{impact_html}')

        nodes.append({
            'id': sys_id, 'label': f'{sys_id}\\n{role_desc}',
            'color': color, 'shape': 'box',
            'font': {'color': '#fff', 'size': 11},
            'size': 20 + len(info['dests']) * 3,
            'title': title
        })
        edges.append({
            'from': 'P01', 'to': sys_id,
            'label': f'{len(info["dests"])} RFC',
            'width': max(1, len(info['dests']) // 2),
            'color': {'color': color, 'opacity': 0.7},
            'arrows': 'to'
        })

    # Integration targets
    for key, info in INTEGRATION_TARGETS.items():
        int_data = integrations.get(key, {'dests': [], 'hosts': set()})
        if not int_data['dests']:
            continue
        nodes.append({
            'id': f'INT_{key}', 'label': f'{info["name"]}',
            'color': info['color'], 'shape': 'diamond',
            'font': {'color': '#fff', 'size': 11},
            'size': 30,
            'title': (f'<b>{info["name"]}</b><br>'
                      f'Connections: {len(int_data["dests"])}<br>'
                      f'<br><b>If DOWN:</b><br>' +
                      '<br>'.join(f'⚠ {i}' for i in info['impact']))
        })
        edges.append({
            'from': 'P01', 'to': f'INT_{key}',
            'label': f'{len(int_data["dests"])}',
            'dashes': True,
            'color': {'color': info['color'], 'opacity': 0.6},
            'arrows': 'to'
        })

    # Fiori Gateway (fabsprd servers)
    fiori_data = integrations.get('FIORI_GW', {'dests': [], 'hosts': set()})
    if fiori_data['dests']:
        nodes.append({
            'id': 'INT_FIORI', 'label': 'Fiori Gateway\\n(fabsprd1-4)',
            'color': '#2ECC71', 'shape': 'diamond',
            'font': {'color': '#fff', 'size': 11},
            'size': 35,
            'title': (f'<b>Fiori/Gateway Servers</b><br>'
                      f'Servers: {", ".join(fiori_data["hosts"])}<br>'
                      f'Connections: {len(fiori_data["dests"])}<br>'
                      f'<br><b>If DOWN:</b><br>'
                      f'⚠ ALL Fiori apps unavailable<br>'
                      f'⚠ OData services unreachable<br>'
                      f'⚠ ESS/MSS portals down')
        })
        edges.append({
            'from': 'P01', 'to': 'INT_FIORI',
            'label': f'{len(fiori_data["dests"])} HTTP',
            'width': 3,
            'color': {'color': '#2ECC71', 'opacity': 0.6},
            'arrows': 'to'
        })

    # Build impact analysis table
    impact_rows = []
    # BW impact
    bw_systems = [s for s in systems if s.startswith('BW') or s == 'BRP']
    if bw_systems:
        impact_rows.append(('BW Landscape', ', '.join(bw_systems), 'HIGH',
                            'All BW reporting stops. RSINFO IDocs (9.4K) fail. '
                            'Management dashboards show stale data.'))

    # Transport impact
    ts_systems = [s for s in systems if s.startswith('TS') or s in ('D01', 'V01')]
    if ts_systems:
        impact_rows.append(('Dev/Test/Transport', ', '.join(ts_systems), 'MEDIUM',
                            'Transport import chain breaks. Dev/QA environments isolated. '
                            'No code deployment to production.'))

    # Integration impact
    if integrations.get('COUPA', {}).get('dests'):
        impact_rows.append(('Coupa Integration', 'External', 'HIGH',
                            'Invoice posting stops (348 runs/period). '
                            'P2P cycle blocked at payment stage.'))
    if integrations.get('MULESOFT', {}).get('dests'):
        impact_rows.append(('MuleSoft ESB', 'External', 'HIGH',
                            'All API-based integrations fail. '
                            'IDoc routing through ESB stops.'))

    # Top jobs for context
    top_jobs_html = ''
    for prog, jobs, runs in top_jobs[:15]:
        top_jobs_html += f'<tr><td>{prog}</td><td>{jobs}</td><td>{runs:,}</td></tr>'

    # IDoc stats for context
    idoc_html = ''
    for mestyp, cnt in idoc_stats[:10]:
        idoc_html += f'<tr><td>{mestyp}</td><td>{cnt:,}</td></tr>'

    # Impact table HTML
    impact_table = ''
    for scenario, systems_affected, severity, desc in impact_rows:
        sev_color = {'HIGH': '#E74C3C', 'MEDIUM': '#E67E22', 'LOW': '#2ECC71'}[severity]
        impact_table += f'''<tr>
            <td>{scenario}</td>
            <td>{systems_affected}</td>
            <td style="color:{sev_color};font-weight:bold">{severity}</td>
            <td>{desc}</td>
        </tr>'''

    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)

    html = f'''<!DOCTYPE html>
<html>
<head>
<title>UNESCO SAP Connectivity Map</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#0a0a1a;font-family:'Segoe UI',Inter,sans-serif;color:#ddd}}
#header{{padding:14px 24px;background:#101030;border-bottom:2px solid #1a1a4e;
  display:flex;justify-content:space-between;align-items:center}}
#header h1{{font-size:18px;color:#4ECDC4}}
.meta{{font-size:11px;color:#888}}
#main{{display:flex;height:calc(100vh - 56px)}}
#network{{flex:1;background:#0d0d25}}
#sidebar{{width:420px;background:#101030;border-left:1px solid #1a1a4e;
  overflow-y:auto;padding:16px}}
.section{{margin-bottom:20px}}
.section h3{{color:#4ECDC4;font-size:13px;margin-bottom:8px;
  border-bottom:1px solid #1a1a4e;padding-bottom:4px}}
table{{width:100%;border-collapse:collapse;font-size:11px}}
th{{text-align:left;color:#888;padding:3px 6px;border-bottom:1px solid #1a1a4e}}
td{{padding:3px 6px;border-bottom:1px solid #0d0d25}}
.legend{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}}
.leg-item{{display:flex;align-items:center;gap:4px;font-size:10px}}
.leg-dot{{width:10px;height:10px;border-radius:2px}}
.leg-diamond{{width:10px;height:10px;transform:rotate(45deg)}}
#click-info{{background:#0d0d25;border:1px solid #1a1a4e;border-radius:6px;
  padding:12px;min-height:80px;font-size:11px;line-height:1.5}}
#click-info b{{color:#4ECDC4}}
</style>
</head>
<body>
<div id="header">
  <h1>UNESCO SAP System Connectivity Map</h1>
  <span class="meta">P01 Production | {len(systems)} SAP systems | {sum(len(v['dests']) for v in systems.values())} RFC connections | Click any node for impact analysis</span>
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
        <div class="leg-item"><div class="leg-diamond" style="background:#E74C3C"></div>External Integration</div>
      </div>
    </div>

    <div class="section">
      <h3>Click a Node for Details</h3>
      <div id="click-info">
        <b>Hover or click</b> any system node to see:<br>
        - Connected RFC destinations<br>
        - Integration purposes<br>
        - Impact if system goes down
      </div>
    </div>

    <div class="section">
      <h3>Impact Analysis — What Breaks?</h3>
      <table>
        <tr><th>Scenario</th><th>Systems</th><th>Risk</th><th>Impact</th></tr>
        {impact_table}
      </table>
    </div>

    <div class="section">
      <h3>Top Background Jobs (by executions)</h3>
      <table>
        <tr><th>Program</th><th>Jobs</th><th>Runs</th></tr>
        {top_jobs_html}
      </table>
    </div>

    <div class="section">
      <h3>IDoc Message Types</h3>
      <table>
        <tr><th>Message Type</th><th>Count</th></tr>
        {idoc_html}
      </table>
    </div>
  </div>
</div>

<script>
var nodes = new vis.DataSet({nodes_json});
var edges = new vis.DataSet({edges_json});

var container = document.getElementById('network');
var data = {{ nodes: nodes, edges: edges }};
var options = {{
  physics: {{
    solver: 'forceAtlas2Based',
    forceAtlas2Based: {{ gravitationalConstant: -80, centralGravity: 0.01,
      springLength: 150, springConstant: 0.04 }},
    stabilization: {{ iterations: 200 }}
  }},
  nodes: {{
    borderWidth: 2,
    shadow: {{ enabled: true, color: 'rgba(0,0,0,0.3)', size: 8 }},
    font: {{ face: 'Segoe UI', multi: true }}
  }},
  edges: {{
    font: {{ size: 9, color: '#666', strokeWidth: 0 }},
    smooth: {{ type: 'continuous' }}
  }},
  interaction: {{
    hover: true,
    tooltipDelay: 100
  }}
}};

var network = new vis.Network(container, data, options);

network.on('click', function(params) {{
  var info = document.getElementById('click-info');
  if (params.nodes.length > 0) {{
    var nodeId = params.nodes[0];
    var node = nodes.get(nodeId);
    if (node && node.title) {{
      info.innerHTML = node.title;
    }}
  }}
}});
</script>
</body>
</html>'''
    return html


def main():
    print("Building UNESCO SAP Connectivity Diagram...")
    systems, integrations, top_jobs, idoc_stats = build_data()
    html = generate_html(systems, integrations, top_jobs, idoc_stats)
    OUTPUT.write_text(html, encoding='utf-8')
    print(f"  Systems: {len(systems)}")
    print(f"  Integrations: {len([k for k, v in integrations.items() if v['dests']])}")
    print(f"  Output: {OUTPUT}")


if __name__ == '__main__':
    main()
