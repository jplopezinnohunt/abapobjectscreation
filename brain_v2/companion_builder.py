"""
Brain v2 Companion Builder — Generates interactive HTML explorer.

Usage:
    python -m brain_v2.companion_builder

Output: brain_v2/output/brain_v2_explorer.html
"""

import json
import sys
from pathlib import Path
from collections import Counter

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
BRAIN_JSON = PROJECT_ROOT / "brain_v2" / "output" / "brain_v2_graph.json"
OUTPUT_HTML = PROJECT_ROOT / "brain_v2" / "output" / "brain_v2_explorer.html"

# Types to exclude from companion data (mass/taxonomic)
EXCLUDE_NODE_TYPES = {
    "FUND", "FUND_CENTER", "FUND_AREA", "GL_ACCOUNT", "COST_ELEMENT",
    "TRANSPORT", "CODE_OBJECT", "DATA_ELEMENT", "DOMAIN_OBJECT",
}
EXCLUDE_EDGE_TYPES = {
    "TRANSPORTS", "BELONGS_TO", "HAS_FUND_CENTER", "POSTS_TO_GL",
}

# Node type colors for visualization
TYPE_COLORS = {
    "ABAP_CLASS": "#4A90D9",
    "ABAP_METHOD": "#6BA3E0",
    "FUNCTION_MODULE": "#7B68EE",
    "ABAP_REPORT": "#5B9BD5",
    "ENHANCEMENT": "#FF6B6B",
    "BSP_APP": "#45B7D1",
    "ODATA_SERVICE": "#4ECDC4",
    "PACKAGE": "#95A5A6",
    "SAP_TABLE": "#2ECC71",
    "TABLE_FIELD": "#27AE60",
    "DOMAIN_VALUE": "#1ABC9C",
    "DMEE_TREE": "#E74C3C",
    "PAYMENT_METHOD": "#E67E22",
    "BCM_RULE": "#D35400",
    "HOUSE_BANK": "#F39C12",
    "JOB_DEFINITION": "#9B59B6",
    "COMPANY_CODE": "#34495E",
    "PROCESS": "#E91E63",
    "PROCESS_STEP": "#F06292",
    "SAP_SYSTEM": "#00BCD4",
    "EXTERNAL_SYSTEM": "#FF9800",
    "RFC_DESTINATION": "#795548",
    "ICF_SERVICE": "#607D8B",
    "IDOC_TYPE": "#8BC34A",
    "KNOWLEDGE_DOC": "#78909C",
    "SKILL": "#546E7A",
    "TRANSACTION": "#BDBDBD",
    "NUMBER_RANGE": "#A1887F",
}


def build_companion():
    """Generate the Brain v2 Explorer HTML companion."""
    from brain_v2.core.graph import BrainGraph
    from brain_v2.queries.gap import find_gaps
    from brain_v2.queries.impact import impact_analysis
    from brain_v2.core.schema import IMPACT_DIRECTION, RISK_WEIGHTS

    print("Loading brain...")
    brain = BrainGraph.load_json(str(BRAIN_JSON))

    # --- Filter data for companion ---
    print("Filtering data...")
    nodes_data = []
    edges_data = []
    node_set = set()

    # Collect filtered edges first
    for e in brain.edges:
        if e["type"] in EXCLUDE_EDGE_TYPES:
            continue
        fn = brain.nodes.get(e["from"], {})
        tn = brain.nodes.get(e["to"], {})
        if fn.get("type") in EXCLUDE_NODE_TYPES or tn.get("type") in EXCLUDE_NODE_TYPES:
            continue
        edges_data.append({
            "f": e["from"], "t": e["to"], "type": e["type"],
            "w": round(e.get("weight", 1.0), 2),
            "c": round(e.get("confidence", 1.0), 2),
        })
        node_set.add(e["from"])
        node_set.add(e["to"])

    # Collect connected nodes
    for nid in node_set:
        if nid not in brain.nodes:
            continue
        d = brain.nodes[nid]
        nodes_data.append({
            "id": nid, "type": d.get("type", ""),
            "name": d.get("name", ""), "domain": d.get("domain", ""),
            "layer": d.get("layer", ""),
        })

    print(f"  Nodes: {len(nodes_data)}, Edges: {len(edges_data)}")

    # --- Stats ---
    stats = brain.stats()

    # --- Gap analysis (CRITICAL + HIGH only) ---
    print("Running gap analysis...")
    gaps = find_gaps(brain, min_severity="HIGH")
    gap_items = []
    for cat_name, items in gaps.items():
        if cat_name == "summary" or not isinstance(items, list):
            continue
        for item in items:
            if item.get("severity") in ("CRITICAL", "HIGH"):
                gap_items.append({
                    "cat": cat_name, "id": item.get("node_id", ""),
                    "name": item.get("name", ""), "type": item.get("type", ""),
                    "sev": item.get("severity", ""), "domain": item.get("domain", ""),
                    "concern": item.get("concern", ""),
                })
    gap_summary = gaps["summary"]

    # --- Pre-compute impact for key nodes ---
    print("Pre-computing sample impacts...")
    sample_impacts = {}
    key_nodes = [
        "FIELD:FPAYP.XREF3", "CLASS:YCL_IDFI_CGI_DMEE_FR",
        "DMEE:/CGI_XML_CT_UNESCO", "TABLE:REGUH",
        "PROCESS:Payment_E2E", "TABLE:FMIFIIT",
    ]
    for nid in key_nodes:
        if brain.has_node(nid):
            r = impact_analysis(brain, nid, max_depth=4)
            if r.get("total_affected", 0) > 0:
                sample_impacts[nid] = {
                    "total": r["total_affected"],
                    "affected": [{
                        "id": a["node_id"],
                        "name": a["node"].get("name", ""),
                        "type": a["node"].get("type", ""),
                        "risk": a["risk"],
                        "depth": a["depth"],
                        "via": a["edge_type"],
                    } for a in r["affected"][:50]],
                }

    # --- Top critical nodes ---
    print("Computing critical nodes...")
    try:
        critical = brain.critical_nodes(top_n=30)
        critical_data = [{"id": nid, "score": s, "name": n} for nid, s, n in critical]
    except Exception:
        critical_data = []

    # --- Impact direction + risk weights for client-side computation ---
    impact_config = {
        "directions": {k: v for k, v in IMPACT_DIRECTION.items() if v},
        "weights": RISK_WEIGHTS,
    }

    # --- Build JSON payload ---
    payload = {
        "nodes": nodes_data,
        "edges": edges_data,
        "stats": {
            "total_nodes": stats["nodes"],
            "total_edges": stats["edges"],
            "node_types": stats["node_types"],
            "edge_types": stats["edge_types"],
            "domains": stats["domains"],
        },
        "gaps": {"items": gap_items, "summary": gap_summary},
        "impacts": sample_impacts,
        "critical": critical_data,
        "impact_config": impact_config,
        "colors": TYPE_COLORS,
    }

    payload_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    print(f"  Payload size: {len(payload_json) / 1024:.0f} KB")

    # --- Generate HTML ---
    print("Generating HTML...")
    html = _generate_html(payload_json)

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    size_kb = OUTPUT_HTML.stat().st_size / 1024
    print(f"Saved: {OUTPUT_HTML} ({size_kb:.0f} KB)")


def _generate_html(payload_json: str) -> str:
    """Generate the self-contained HTML companion."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Brain v2 Explorer - UNESCO SAP Intelligence</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, 'Segoe UI', Roboto, sans-serif; background: #0a0e17; color: #e0e6ed; overflow: hidden; height: 100vh; }}
.header {{ background: linear-gradient(135deg, #1a1f36 0%, #0d1321 100%); padding: 12px 24px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #2a3555; }}
.header h1 {{ font-size: 18px; font-weight: 600; color: #4fc3f7; }}
.header .stats {{ font-size: 13px; color: #8899aa; }}
.header .stats b {{ color: #4fc3f7; }}
.tabs {{ display: flex; background: #111827; border-bottom: 1px solid #2a3555; padding: 0 16px; }}
.tab {{ padding: 10px 20px; cursor: pointer; color: #8899aa; font-size: 13px; font-weight: 500; border-bottom: 2px solid transparent; transition: all 0.2s; }}
.tab:hover {{ color: #cdd; }}
.tab.active {{ color: #4fc3f7; border-bottom-color: #4fc3f7; }}
.tab-content {{ display: none; height: calc(100vh - 95px); overflow: auto; }}
.tab-content.active {{ display: flex; }}

/* Overview tab */
.overview {{ padding: 24px; gap: 20px; flex-wrap: wrap; align-content: flex-start; }}
.card {{ background: #1a1f36; border: 1px solid #2a3555; border-radius: 8px; padding: 20px; }}
.card h3 {{ color: #4fc3f7; margin-bottom: 12px; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; }}
.card-row {{ display: flex; gap: 20px; width: 100%; }}
.card-third {{ flex: 1; min-width: 280px; }}
.card-full {{ width: 100%; }}
.bar-row {{ display: flex; align-items: center; margin-bottom: 4px; font-size: 12px; }}
.bar-label {{ width: 180px; text-align: right; padding-right: 8px; color: #8899aa; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.bar-track {{ flex: 1; height: 16px; background: #0d1321; border-radius: 3px; overflow: hidden; }}
.bar-fill {{ height: 100%; border-radius: 3px; min-width: 2px; transition: width 0.3s; }}
.bar-value {{ width: 60px; text-align: right; font-size: 11px; color: #8899aa; padding-left: 6px; }}
.stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; }}
.stat-box {{ background: #0d1321; padding: 16px; border-radius: 6px; text-align: center; }}
.stat-box .num {{ font-size: 28px; font-weight: 700; color: #4fc3f7; }}
.stat-box .label {{ font-size: 11px; color: #8899aa; margin-top: 4px; text-transform: uppercase; }}

/* Explorer tab */
.explorer {{ flex: 1; display: flex; position: relative; }}
.explorer-sidebar {{ width: 320px; background: #111827; border-right: 1px solid #2a3555; display: flex; flex-direction: column; }}
.search-box {{ padding: 12px; border-bottom: 1px solid #2a3555; }}
.search-box input {{ width: 100%; padding: 8px 12px; background: #0d1321; border: 1px solid #2a3555; border-radius: 6px; color: #e0e6ed; font-size: 13px; outline: none; }}
.search-box input:focus {{ border-color: #4fc3f7; }}
.search-results {{ flex: 1; overflow-y: auto; }}
.search-item {{ padding: 8px 12px; cursor: pointer; border-bottom: 1px solid #1a1f36; font-size: 12px; }}
.search-item:hover {{ background: #1a1f36; }}
.search-item .si-name {{ color: #e0e6ed; font-weight: 500; }}
.search-item .si-type {{ color: #8899aa; font-size: 11px; }}
.search-item .si-type span {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 10px; }}
.node-detail {{ padding: 12px; background: #0d1321; border-top: 1px solid #2a3555; max-height: 40%; overflow-y: auto; }}
.node-detail h4 {{ color: #4fc3f7; margin-bottom: 8px; font-size: 13px; }}
.node-detail .nd-row {{ font-size: 12px; margin-bottom: 4px; color: #8899aa; }}
.node-detail .nd-row b {{ color: #e0e6ed; }}
.canvas-wrap {{ flex: 1; position: relative; }}
.canvas-wrap canvas {{ display: block; }}
.canvas-controls {{ position: absolute; top: 10px; right: 10px; display: flex; flex-direction: column; gap: 4px; }}
.canvas-controls button {{ width: 32px; height: 32px; background: #1a1f36; border: 1px solid #2a3555; border-radius: 4px; color: #8899aa; cursor: pointer; font-size: 16px; }}
.canvas-controls button:hover {{ background: #2a3555; color: #fff; }}
.canvas-legend {{ position: absolute; bottom: 10px; left: 10px; background: rgba(13,19,33,0.9); padding: 8px 12px; border-radius: 6px; display: flex; flex-wrap: wrap; gap: 6px 12px; }}
.legend-item {{ font-size: 10px; display: flex; align-items: center; gap: 4px; color: #8899aa; }}
.legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}
.view-label {{ position: absolute; top: 10px; left: 10px; font-size: 12px; color: #4fc3f7; background: rgba(13,19,33,0.9); padding: 4px 10px; border-radius: 4px; }}

/* Impact tab */
.impact-panel {{ padding: 24px; flex: 1; display: flex; flex-direction: column; }}
.impact-controls {{ display: flex; gap: 12px; margin-bottom: 16px; align-items: center; }}
.impact-controls input {{ flex: 1; max-width: 400px; padding: 8px 12px; background: #0d1321; border: 1px solid #2a3555; border-radius: 6px; color: #e0e6ed; font-size: 13px; }}
.impact-controls button {{ padding: 8px 16px; background: #4fc3f7; color: #0a0e17; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 13px; }}
.impact-controls button:hover {{ background: #29b6f6; }}
.impact-results {{ flex: 1; overflow-y: auto; }}
.impact-row {{ display: flex; align-items: center; padding: 6px 12px; border-bottom: 1px solid #1a1f36; font-size: 12px; }}
.impact-row .ir-risk {{ width: 60px; font-weight: 700; text-align: center; border-radius: 4px; padding: 2px 6px; }}
.impact-row .ir-risk.crit {{ background: #e74c3c33; color: #e74c3c; }}
.impact-row .ir-risk.high {{ background: #e67e2233; color: #e67e22; }}
.impact-row .ir-risk.med {{ background: #f39c1233; color: #f39c12; }}
.impact-row .ir-risk.low {{ background: #2ecc7133; color: #2ecc71; }}
.impact-row .ir-name {{ flex: 1; margin-left: 12px; }}
.impact-row .ir-type {{ width: 140px; color: #8899aa; }}
.impact-row .ir-via {{ width: 140px; color: #8899aa; font-size: 11px; }}
.impact-row .ir-depth {{ width: 40px; text-align: center; color: #8899aa; }}
.impact-header {{ font-weight: 600; color: #4fc3f7; background: #1a1f36; border-radius: 4px; }}
.impact-summary {{ margin-bottom: 16px; font-size: 13px; color: #8899aa; }}
.impact-precomputed {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; }}
.impact-chip {{ padding: 6px 12px; background: #1a1f36; border: 1px solid #2a3555; border-radius: 16px; cursor: pointer; font-size: 12px; color: #8899aa; }}
.impact-chip:hover {{ border-color: #4fc3f7; color: #4fc3f7; }}

/* Gaps tab */
.gaps-panel {{ padding: 24px; flex: 1; display: flex; flex-direction: column; }}
.gaps-summary {{ display: flex; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }}
.gap-stat {{ padding: 8px 16px; background: #1a1f36; border-radius: 6px; font-size: 13px; }}
.gap-stat b {{ color: #e74c3c; }}
.gap-stat.high b {{ color: #e67e22; }}
.gap-stat.med b {{ color: #f39c12; }}
.gaps-filter {{ margin-bottom: 12px; }}
.gaps-filter select {{ padding: 6px 10px; background: #0d1321; border: 1px solid #2a3555; border-radius: 4px; color: #e0e6ed; font-size: 13px; }}
.gap-table {{ flex: 1; overflow-y: auto; }}
.gap-row {{ display: flex; align-items: center; padding: 8px 12px; border-bottom: 1px solid #1a1f36; font-size: 12px; cursor: pointer; }}
.gap-row:hover {{ background: #1a1f36; }}
.gap-row .gr-sev {{ width: 70px; font-weight: 600; text-transform: uppercase; font-size: 11px; }}
.gap-row .gr-sev.CRITICAL {{ color: #e74c3c; }}
.gap-row .gr-sev.HIGH {{ color: #e67e22; }}
.gap-row .gr-name {{ flex: 1; color: #e0e6ed; }}
.gap-row .gr-type {{ width: 140px; color: #8899aa; }}
.gap-row .gr-cat {{ width: 180px; color: #8899aa; font-size: 11px; }}
.gap-header {{ font-weight: 600; color: #4fc3f7; background: #1a1f36; border-radius: 4px; }}

/* Critical tab */
.critical-panel {{ padding: 24px; flex: 1; overflow-y: auto; }}
.crit-row {{ display: flex; align-items: center; padding: 8px 12px; border-bottom: 1px solid #1a1f36; font-size: 12px; cursor: pointer; }}
.crit-row:hover {{ background: #1a1f36; }}
.crit-score {{ width: 80px; font-weight: 700; color: #e74c3c; }}
.crit-name {{ flex: 1; }}
</style>
</head>
<body>

<div class="header">
  <h1>Brain v2 Explorer</h1>
  <div class="stats" id="headerStats"></div>
</div>

<div class="tabs">
  <div class="tab active" onclick="switchTab('overview')">Overview</div>
  <div class="tab" onclick="switchTab('explorer')">Explorer</div>
  <div class="tab" onclick="switchTab('impact')">Impact Analysis</div>
  <div class="tab" onclick="switchTab('gaps')">Gap Analysis</div>
  <div class="tab" onclick="switchTab('critical')">Critical Nodes</div>
</div>

<div class="tab-content active overview" id="tab-overview"></div>
<div class="tab-content explorer" id="tab-explorer">
  <div class="explorer-sidebar">
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="Search nodes..." oninput="onSearch(this.value)">
    </div>
    <div class="search-results" id="searchResults"></div>
    <div class="node-detail" id="nodeDetail" style="display:none"></div>
  </div>
  <div class="canvas-wrap" id="canvasWrap">
    <canvas id="graphCanvas"></canvas>
    <div class="view-label" id="viewLabel">Top 30 Critical Nodes</div>
    <div class="canvas-controls">
      <button onclick="zoomIn()" title="Zoom in">+</button>
      <button onclick="zoomOut()" title="Zoom out">-</button>
      <button onclick="resetView()" title="Reset view">R</button>
    </div>
    <div class="canvas-legend" id="canvasLegend"></div>
  </div>
</div>
<div class="tab-content impact-panel" id="tab-impact"></div>
<div class="tab-content gaps-panel" id="tab-gaps"></div>
<div class="tab-content critical-panel" id="tab-critical"></div>

<script>
const D = {payload_json};

// Index nodes/edges for fast lookup
const nodeMap = {{}};
D.nodes.forEach(n => nodeMap[n.id] = n);
const adjOut = {{}};
const adjIn = {{}};
D.edges.forEach(e => {{
  (adjOut[e.f] = adjOut[e.f] || []).push(e);
  (adjIn[e.t] = adjIn[e.t] || []).push(e);
}});

// --- Tab switching ---
function switchTab(name) {{
  document.querySelectorAll('.tab').forEach((t, i) => {{
    const tabs = ['overview','explorer','impact','gaps','critical'];
    t.classList.toggle('active', tabs[i] === name);
  }});
  document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  if (name === 'explorer') resizeCanvas();
}}

// --- Header ---
document.getElementById('headerStats').innerHTML =
  `<b>${{D.stats.total_nodes.toLocaleString()}}</b> nodes &nbsp; <b>${{D.stats.total_edges.toLocaleString()}}</b> edges &nbsp; <b>${{D.nodes.length.toLocaleString()}}</b> connected &nbsp; Session #042`;

// --- Overview ---
function buildOverview() {{
  const s = D.stats;
  const topTypes = Object.entries(s.node_types).slice(0, 12);
  const topEdges = Object.entries(s.edge_types).slice(0, 12);
  const topDomains = Object.entries(s.domains).slice(0, 10);
  const maxT = topTypes[0]?.[1] || 1;
  const maxE = topEdges[0]?.[1] || 1;
  const maxD = topDomains[0]?.[1] || 1;

  const gs = D.gaps.summary;
  let html = `<div class="card-row"><div class="card card-full"><div class="stat-grid">
    <div class="stat-box"><div class="num">${{s.total_nodes.toLocaleString()}}</div><div class="label">Total Nodes</div></div>
    <div class="stat-box"><div class="num">${{s.total_edges.toLocaleString()}}</div><div class="label">Total Edges</div></div>
    <div class="stat-box"><div class="num">${{D.nodes.length.toLocaleString()}}</div><div class="label">Connected</div></div>
    <div class="stat-box"><div class="num">${{D.critical.length}}</div><div class="label">Critical</div></div>
    <div class="stat-box"><div class="num">${{gs.by_severity?.CRITICAL||0}}</div><div class="label" style="color:#e74c3c">Critical Gaps</div></div>
    <div class="stat-box"><div class="num">${{gs.by_severity?.HIGH||0}}</div><div class="label" style="color:#e67e22">High Gaps</div></div>
  </div></div></div>`;

  html += `<div class="card-row">`;
  html += `<div class="card card-third"><h3>Node Types</h3>${{topTypes.map(([t,c]) =>
    `<div class="bar-row"><div class="bar-label">${{t}}</div><div class="bar-track"><div class="bar-fill" style="width:${{c/maxT*100}}%;background:${{D.colors[t]||'#4fc3f7'}}"></div></div><div class="bar-value">${{c.toLocaleString()}}</div></div>`
  ).join('')}}</div>`;

  html += `<div class="card card-third"><h3>Edge Types</h3>${{topEdges.map(([t,c]) =>
    `<div class="bar-row"><div class="bar-label">${{t}}</div><div class="bar-track"><div class="bar-fill" style="width:${{c/maxE*100}}%;background:#4fc3f7"></div></div><div class="bar-value">${{c.toLocaleString()}}</div></div>`
  ).join('')}}</div>`;

  html += `<div class="card card-third"><h3>Domains</h3>${{topDomains.map(([t,c]) =>
    `<div class="bar-row"><div class="bar-label">${{t}}</div><div class="bar-track"><div class="bar-fill" style="width:${{c/maxD*100}}%;background:#2ecc71"></div></div><div class="bar-value">${{c.toLocaleString()}}</div></div>`
  ).join('')}}</div>`;
  html += `</div>`;

  document.getElementById('tab-overview').innerHTML = html;
}}

// --- Explorer (Canvas graph) ---
let gNodes = [], gEdges = [], gScale = 1, gOffX = 0, gOffY = 0;
let dragNode = null, dragStart = null, panStart = null, selectedNode = null;
let canvas, ctx;

function initExplorer() {{
  canvas = document.getElementById('graphCanvas');
  ctx = canvas.getContext('2d');
  resizeCanvas();
  window.addEventListener('resize', resizeCanvas);
  canvas.addEventListener('mousedown', onCanvasDown);
  canvas.addEventListener('mousemove', onCanvasMove);
  canvas.addEventListener('mouseup', onCanvasUp);
  canvas.addEventListener('wheel', onCanvasWheel);
  canvas.addEventListener('dblclick', onCanvasDblClick);
  // Show top critical nodes initially
  showCriticalView();
  buildLegend();
}}

function resizeCanvas() {{
  const wrap = document.getElementById('canvasWrap');
  if (!wrap) return;
  canvas.width = wrap.clientWidth;
  canvas.height = wrap.clientHeight;
  drawGraph();
}}

function showCriticalView() {{
  const ids = new Set(D.critical.slice(0, 30).map(c => c.id));
  loadSubgraph(ids, 'Top 30 Critical Nodes');
}}

function loadSubgraph(seedIds, label) {{
  // Expand seeds by 1 hop to show context
  const expanded = new Set(seedIds);
  D.edges.forEach(e => {{
    if (seedIds.has(e.f)) expanded.add(e.t);
    if (seedIds.has(e.t)) expanded.add(e.f);
  }});
  // Cap at 300 nodes for performance
  const nodeIds = [...expanded].slice(0, 300);
  const nodeSet = new Set(nodeIds);

  gNodes = nodeIds.map((id, i) => {{
    const n = nodeMap[id] || {{id, type:'?', name: id, domain:''}};
    const angle = (i / nodeIds.length) * Math.PI * 2;
    const r = 200 + Math.random() * 100;
    return {{
      id, x: canvas.width/2 + Math.cos(angle)*r, y: canvas.height/2 + Math.sin(angle)*r,
      vx: 0, vy: 0, type: n.type, name: n.name, domain: n.domain,
      radius: seedIds.has(id) ? 8 : 5,
      isSeed: seedIds.has(id),
    }};
  }});
  const nodeIdx = {{}};
  gNodes.forEach((n, i) => nodeIdx[n.id] = i);

  gEdges = [];
  D.edges.forEach(e => {{
    if (nodeSet.has(e.f) && nodeSet.has(e.t) && nodeIdx[e.f] !== undefined && nodeIdx[e.t] !== undefined) {{
      gEdges.push({{source: nodeIdx[e.f], target: nodeIdx[e.t], type: e.type}});
    }}
  }});

  document.getElementById('viewLabel').textContent = `${{label}} (${{gNodes.length}} nodes, ${{gEdges.length}} edges)`;
  gScale = 1; gOffX = 0; gOffY = 0;
  runLayout(120);
}}

function runLayout(iterations) {{
  // Simple force-directed layout
  for (let iter = 0; iter < iterations; iter++) {{
    const alpha = 1 - iter / iterations;
    // Repulsion
    for (let i = 0; i < gNodes.length; i++) {{
      for (let j = i + 1; j < gNodes.length; j++) {{
        let dx = gNodes[j].x - gNodes[i].x;
        let dy = gNodes[j].y - gNodes[i].y;
        let d = Math.sqrt(dx*dx + dy*dy) || 1;
        let f = alpha * 800 / (d * d);
        gNodes[i].vx -= dx/d * f;
        gNodes[i].vy -= dy/d * f;
        gNodes[j].vx += dx/d * f;
        gNodes[j].vy += dy/d * f;
      }}
    }}
    // Attraction (edges)
    gEdges.forEach(e => {{
      const s = gNodes[e.source], t = gNodes[e.target];
      let dx = t.x - s.x, dy = t.y - s.y;
      let d = Math.sqrt(dx*dx + dy*dy) || 1;
      let f = alpha * (d - 80) * 0.01;
      s.vx += dx/d * f; s.vy += dy/d * f;
      t.vx -= dx/d * f; t.vy -= dy/d * f;
    }});
    // Center gravity
    gNodes.forEach(n => {{
      n.vx += (canvas.width/2 - n.x) * 0.001 * alpha;
      n.vy += (canvas.height/2 - n.y) * 0.001 * alpha;
      n.x += n.vx * 0.5; n.y += n.vy * 0.5;
      n.vx *= 0.9; n.vy *= 0.9;
    }});
  }}
  drawGraph();
}}

function drawGraph() {{
  if (!ctx) return;
  ctx.save();
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.translate(gOffX, gOffY);
  ctx.scale(gScale, gScale);

  // Edges
  ctx.lineWidth = 0.5;
  gEdges.forEach(e => {{
    const s = gNodes[e.source], t = gNodes[e.target];
    ctx.strokeStyle = '#2a355544';
    ctx.beginPath();
    ctx.moveTo(s.x, s.y);
    ctx.lineTo(t.x, t.y);
    ctx.stroke();
  }});

  // Nodes
  gNodes.forEach((n, i) => {{
    ctx.fillStyle = D.colors[n.type] || '#4fc3f7';
    if (selectedNode === i) {{
      ctx.shadowColor = '#4fc3f7';
      ctx.shadowBlur = 12;
    }}
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.shadowBlur = 0;

    // Labels for seeds or selected
    if (n.isSeed || selectedNode === i) {{
      ctx.fillStyle = '#e0e6ed';
      ctx.font = '10px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(n.name.substring(0, 25), n.x, n.y - n.radius - 4);
    }}
  }});

  // Selected node highlight edges
  if (selectedNode !== null) {{
    const sel = gNodes[selectedNode];
    gEdges.forEach(e => {{
      if (e.source === selectedNode || e.target === selectedNode) {{
        const s = gNodes[e.source], t = gNodes[e.target];
        ctx.strokeStyle = '#4fc3f788';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);
        ctx.stroke();
        ctx.lineWidth = 0.5;
        // Edge label
        ctx.fillStyle = '#8899aa';
        ctx.font = '9px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(e.type, (s.x+t.x)/2, (s.y+t.y)/2 - 4);
      }}
    }});
  }}

  ctx.restore();
}}

function findNodeAt(mx, my) {{
  const x = (mx - gOffX) / gScale, y = (my - gOffY) / gScale;
  for (let i = gNodes.length - 1; i >= 0; i--) {{
    const n = gNodes[i];
    const dx = n.x - x, dy = n.y - y;
    if (dx*dx + dy*dy < (n.radius+3) * (n.radius+3)) return i;
  }}
  return null;
}}

function onCanvasDown(ev) {{
  const rect = canvas.getBoundingClientRect();
  const mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
  const hit = findNodeAt(mx, my);
  if (hit !== null) {{
    dragNode = hit;
    selectedNode = hit;
    showNodeDetail(gNodes[hit].id);
    drawGraph();
  }} else {{
    panStart = {{x: ev.clientX, y: ev.clientY, ox: gOffX, oy: gOffY}};
  }}
}}
function onCanvasMove(ev) {{
  if (dragNode !== null) {{
    const rect = canvas.getBoundingClientRect();
    gNodes[dragNode].x = (ev.clientX - rect.left - gOffX) / gScale;
    gNodes[dragNode].y = (ev.clientY - rect.top - gOffY) / gScale;
    drawGraph();
  }} else if (panStart) {{
    gOffX = panStart.ox + (ev.clientX - panStart.x);
    gOffY = panStart.oy + (ev.clientY - panStart.y);
    drawGraph();
  }}
}}
function onCanvasUp() {{ dragNode = null; panStart = null; }}
function onCanvasWheel(ev) {{
  ev.preventDefault();
  const factor = ev.deltaY < 0 ? 1.1 : 0.9;
  const rect = canvas.getBoundingClientRect();
  const mx = ev.clientX - rect.left, my = ev.clientY - rect.top;
  gOffX = mx - (mx - gOffX) * factor;
  gOffY = my - (my - gOffY) * factor;
  gScale *= factor;
  drawGraph();
}}
function onCanvasDblClick(ev) {{
  const rect = canvas.getBoundingClientRect();
  const hit = findNodeAt(ev.clientX - rect.left, ev.clientY - rect.top);
  if (hit !== null) {{
    // Expand neighbors of this node
    const nid = gNodes[hit].id;
    const neighbors = new Set([nid]);
    D.edges.forEach(e => {{
      if (e.f === nid) neighbors.add(e.t);
      if (e.t === nid) neighbors.add(e.f);
    }});
    loadSubgraph(neighbors, `Neighbors of ${{nodeMap[nid]?.name || nid}}`);
  }}
}}
function zoomIn() {{ gScale *= 1.2; drawGraph(); }}
function zoomOut() {{ gScale /= 1.2; drawGraph(); }}
function resetView() {{ gScale = 1; gOffX = 0; gOffY = 0; drawGraph(); }}

function buildLegend() {{
  const seen = new Set();
  gNodes.forEach(n => seen.add(n.type));
  // Add common types
  ['ABAP_CLASS','FUNCTION_MODULE','SAP_TABLE','TABLE_FIELD','DMEE_TREE',
   'PAYMENT_METHOD','HOUSE_BANK','PROCESS','EXTERNAL_SYSTEM','KNOWLEDGE_DOC'].forEach(t => seen.add(t));
  const el = document.getElementById('canvasLegend');
  el.innerHTML = [...seen].filter(t => D.colors[t]).map(t =>
    `<div class="legend-item"><div class="legend-dot" style="background:${{D.colors[t]}}"></div>${{t}}</div>`
  ).join('');
}}

function showNodeDetail(nid) {{
  const n = nodeMap[nid];
  if (!n) return;
  const out = adjOut[nid] || [];
  const inc = adjIn[nid] || [];
  const el = document.getElementById('nodeDetail');
  el.style.display = 'block';
  let html = `<h4>${{n.name}}</h4>`;
  html += `<div class="nd-row"><b>ID:</b> ${{nid}}</div>`;
  html += `<div class="nd-row"><b>Type:</b> ${{n.type}}</div>`;
  html += `<div class="nd-row"><b>Domain:</b> ${{n.domain}}</div>`;
  html += `<div class="nd-row"><b>Layer:</b> ${{n.layer}}</div>`;
  html += `<div class="nd-row"><b>Outgoing:</b> ${{out.length}} edges</div>`;
  html += `<div class="nd-row"><b>Incoming:</b> ${{inc.length}} edges</div>`;
  if (out.length > 0) {{
    html += `<div class="nd-row" style="margin-top:6px"><b>Reads/Calls:</b></div>`;
    out.slice(0, 10).forEach(e => {{
      const tn = nodeMap[e.t];
      html += `<div class="nd-row" style="padding-left:8px">[${{e.type}}] ${{tn?.name || e.t}}</div>`;
    }});
    if (out.length > 10) html += `<div class="nd-row" style="padding-left:8px">... +${{out.length-10}} more</div>`;
  }}
  if (inc.length > 0) {{
    html += `<div class="nd-row" style="margin-top:6px"><b>Used by:</b></div>`;
    inc.slice(0, 10).forEach(e => {{
      const fn = nodeMap[e.f];
      html += `<div class="nd-row" style="padding-left:8px">[${{e.type}}] ${{fn?.name || e.f}}</div>`;
    }});
    if (inc.length > 10) html += `<div class="nd-row" style="padding-left:8px">... +${{inc.length-10}} more</div>`;
  }}
  html += `<div style="margin-top:8px"><button onclick="runImpactFor('${{nid}}')" style="padding:4px 10px;background:#4fc3f7;color:#0a0e17;border:none;border-radius:4px;cursor:pointer;font-size:11px">Run Impact Analysis</button></div>`;
  el.innerHTML = html;
}}

function runImpactFor(nid) {{
  switchTab('impact');
  document.querySelector('#tab-impact input').value = nid;
  computeImpact(nid);
}}

// --- Search ---
function onSearch(query) {{
  const el = document.getElementById('searchResults');
  if (!query || query.length < 2) {{ el.innerHTML = ''; return; }}
  const q = query.toUpperCase();
  const matches = D.nodes.filter(n =>
    n.id.toUpperCase().includes(q) || n.name.toUpperCase().includes(q)
  ).slice(0, 50);
  el.innerHTML = matches.map(n => {{
    const color = D.colors[n.type] || '#4fc3f7';
    return `<div class="search-item" onclick="focusNode('${{n.id}}')">
      <div class="si-name">${{n.name}}</div>
      <div class="si-type"><span style="background:${{color}}33;color:${{color}}">${{n.type}}</span> ${{n.domain}}</div>
    </div>`;
  }}).join('');
}}

function focusNode(nid) {{
  const neighbors = new Set([nid]);
  D.edges.forEach(e => {{
    if (e.f === nid) neighbors.add(e.t);
    if (e.t === nid) neighbors.add(e.f);
  }});
  loadSubgraph(neighbors, `${{nodeMap[nid]?.name || nid}}`);
  // Select the node
  const idx = gNodes.findIndex(n => n.id === nid);
  if (idx >= 0) {{
    selectedNode = idx;
    showNodeDetail(nid);
    drawGraph();
  }}
}}

// --- Impact Analysis ---
function buildImpact() {{
  let html = `<div class="impact-controls">
    <input type="text" placeholder="Enter node ID (e.g. FIELD:FPAYP.XREF3)" list="impactSuggestions">
    <button onclick="computeImpact(this.previousElementSibling.value)">Analyze Impact</button>
    <datalist id="impactSuggestions">${{D.nodes.slice(0,500).map(n=>`<option value="${{n.id}}">`).join('')}}</datalist>
  </div>`;
  html += `<div class="impact-precomputed">Pre-computed: ${{Object.keys(D.impacts).map(k =>
    `<span class="impact-chip" onclick="document.querySelector('#tab-impact input').value='${{k}}';computeImpact('${{k}}')">${{nodeMap[k]?.name||k}} (${{D.impacts[k].total}})</span>`
  ).join('')}}</div>`;
  html += `<div class="impact-summary" id="impactSummary"></div>`;
  html += `<div class="impact-results" id="impactResults">
    <div class="impact-row impact-header">
      <div class="ir-risk">Risk</div><div class="ir-name">Node</div>
      <div class="ir-type">Type</div><div class="ir-via">Via Edge</div><div class="ir-depth">Depth</div>
    </div>
  </div>`;
  document.getElementById('tab-impact').innerHTML = html;
}}

function computeImpact(nodeId) {{
  if (!nodeId) return;
  // Check pre-computed first
  if (D.impacts[nodeId]) {{
    renderImpact(nodeId, D.impacts[nodeId]);
    return;
  }}
  // Client-side BFS impact (using embedded edge data)
  const dirs = D.impact_config.directions;
  const wts = D.impact_config.weights;
  const neighbors = {{}};
  D.edges.forEach(e => {{
    const dir = dirs[e.type];
    if (!dir) return;
    const w = wts[e.type] || 0.5;
    if (dir === 'forward') {{
      (neighbors[e.t] = neighbors[e.t] || []).push({{node: e.f, type: e.type, w}});
    }} else if (dir === 'backward') {{
      (neighbors[e.t] = neighbors[e.t] || []).push({{node: e.f, type: e.type, w}});
    }} else if (dir === 'bidirectional') {{
      (neighbors[e.t] = neighbors[e.t] || []).push({{node: e.f, type: e.type, w}});
      (neighbors[e.f] = neighbors[e.f] || []).push({{node: e.t, type: e.type, w}});
    }}
  }});

  const affected = {{}};
  const queue = [{{id: nodeId, risk: 1.0, depth: 0}}];
  const visited = new Set([nodeId]);

  while (queue.length > 0) {{
    const {{id, risk, depth}} = queue.shift();
    if (depth >= 4) continue;
    (neighbors[id] || []).forEach(nb => {{
      const nr = risk * nb.w;
      if (nr < 0.1) return;
      if (!affected[nb.node] || nr > affected[nb.node].risk) {{
        visited.add(nb.node);
        affected[nb.node] = {{id: nb.node, name: nodeMap[nb.node]?.name||nb.node, type: nodeMap[nb.node]?.type||'?', risk: nr, depth: depth+1, via: nb.type}};
        queue.push({{id: nb.node, risk: nr, depth: depth+1}});
      }}
    }});
  }}

  const result = {{
    total: Object.keys(affected).length,
    affected: Object.values(affected).sort((a,b) => b.risk - a.risk).slice(0, 50),
  }};
  renderImpact(nodeId, result);
}}

function renderImpact(nodeId, result) {{
  const sum = document.getElementById('impactSummary');
  const n = nodeMap[nodeId];
  sum.innerHTML = `Impact of <b>${{n?.name||nodeId}}</b> (${{n?.type||'?'}}): <b>${{result.total}}</b> objects affected`;

  const el = document.getElementById('impactResults');
  let html = `<div class="impact-row impact-header">
    <div class="ir-risk">Risk</div><div class="ir-name">Node</div>
    <div class="ir-type">Type</div><div class="ir-via">Via Edge</div><div class="ir-depth">Depth</div>
  </div>`;
  result.affected.forEach(a => {{
    const riskPct = Math.round(a.risk * 100);
    const cls = riskPct >= 80 ? 'crit' : riskPct >= 50 ? 'high' : riskPct >= 20 ? 'med' : 'low';
    html += `<div class="impact-row" onclick="focusNode('${{a.id}}');switchTab('explorer')">
      <div class="ir-risk ${{cls}}">${{riskPct}}%</div>
      <div class="ir-name">${{a.name}}</div>
      <div class="ir-type">${{a.type}}</div>
      <div class="ir-via">${{a.via}}</div>
      <div class="ir-depth">${{a.depth}}</div>
    </div>`;
  }});
  el.innerHTML = html;
}}

// --- Gap Analysis ---
function buildGaps() {{
  const gs = D.gaps.summary;
  let html = `<div class="gaps-summary">
    <div class="gap-stat"><b>${{gs.by_severity?.CRITICAL||0}}</b> Critical</div>
    <div class="gap-stat high"><b>${{gs.by_severity?.HIGH||0}}</b> High</div>
    <div class="gap-stat med"><b>${{gs.total_gaps}}</b> Total (all severities)</div>
  </div>`;
  html += `<div class="gaps-filter">Filter: <select id="gapFilter" onchange="filterGaps()">
    <option value="ALL">All Critical+High</option>
    <option value="CRITICAL">Critical only</option>
    <option value="configured_but_unused">Configured but unused</option>
    <option value="dead_code">Dead code</option>
    <option value="orphan_integrations">Orphan integrations</option>
  </select></div>`;
  html += `<div class="gap-table" id="gapTable">
    <div class="gap-row gap-header">
      <div class="gr-sev">Severity</div><div class="gr-name">Name</div>
      <div class="gr-type">Type</div><div class="gr-cat">Category</div>
    </div>`;
  D.gaps.items.forEach(g => {{
    html += `<div class="gap-row" data-sev="${{g.sev}}" data-cat="${{g.cat}}" onclick="focusNode('${{g.id}}');switchTab('explorer')">
      <div class="gr-sev ${{g.sev}}">${{g.sev}}</div>
      <div class="gr-name">${{g.name}}</div>
      <div class="gr-type">${{g.type||''}}</div>
      <div class="gr-cat">${{g.cat}}</div>
    </div>`;
  }});
  html += `</div>`;
  document.getElementById('tab-gaps').innerHTML = html;
}}

function filterGaps() {{
  const val = document.getElementById('gapFilter').value;
  document.querySelectorAll('#gapTable .gap-row:not(.gap-header)').forEach(row => {{
    if (val === 'ALL') {{ row.style.display = ''; return; }}
    if (val === 'CRITICAL') {{ row.style.display = row.dataset.sev === 'CRITICAL' ? '' : 'none'; return; }}
    row.style.display = row.dataset.cat === val ? '' : 'none';
  }});
}}

// --- Critical Nodes ---
function buildCritical() {{
  let html = `<div class="card card-full"><h3>Top 30 Critical Nodes (Betweenness Centrality)</h3>
  <p style="color:#8899aa;font-size:12px;margin-bottom:12px">Nodes that connect the most paths. Changing these has the widest ripple effect.</p>`;
  D.critical.forEach((c, i) => {{
    const n = nodeMap[c.id];
    const color = D.colors[n?.type] || '#4fc3f7';
    html += `<div class="crit-row" onclick="focusNode('${{c.id}}');switchTab('explorer')">
      <div class="crit-score">#${{i+1}} ${{(c.score*100).toFixed(1)}}%</div>
      <div class="crit-name" style="color:${{color}}">${{c.name}}</div>
      <div style="width:120px;color:#8899aa;font-size:11px">${{n?.type||''}}</div>
      <div style="width:80px;color:#8899aa;font-size:11px">${{n?.domain||''}}</div>
    </div>`;
  }});
  html += `</div>`;
  document.getElementById('tab-critical').innerHTML = html;
}}

// --- Init ---
buildOverview();
buildImpact();
buildGaps();
buildCritical();
setTimeout(initExplorer, 100);
</script>
</body>
</html>"""


if __name__ == "__main__":
    build_companion()
