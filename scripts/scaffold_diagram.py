"""
UNESCO SAP Intelligence Platform — Companion Diagram Scaffolder
Generates standard-compliant visual companion HTML files with orthogonal SVG layouts.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

def generate_orthogonal_path(x1, y1, x2, y2, bend="horizontal"):
    """
    Generate an SVG path data string for a 90-degree orthogonal line between two points.
    Outputs a zigzag path.
    """
    # Start at center of right side of node 1 (x1 + 180, y1 + 40)
    # End at center of left side of node 2 (x2, y2 + 40)
    # Assuming connection points are:
    # If x1 < x2: node1 right to node2 left
    # If x1 > x2: node1 left to node2 right
    # If x1 == x2: node1 bottom to node2 top
    
    if x1 + 180 < x2:
        # Node 1 is to the left of Node 2
        start_x, start_y = x1 + 180, y1 + 40
        end_x, end_y = x2, y2 + 40
        mid_x = start_x + (end_x - start_x) / 2
        return f"M {start_x} {start_y} H {mid_x} V {end_y} H {end_x}"
    elif x2 + 180 < x1:
        # Node 2 is to the left of Node 1
        start_x, start_y = x1, y1 + 40
        end_x, end_y = x2 + 180, y2 + 40
        mid_x = start_x - (start_x - end_x) / 2
        return f"M {start_x} {start_y} H {mid_x} V {end_y} H {end_x}"
    else:
        # Stacked vertically
        start_x, start_y = x1 + 90, y1 + 80
        end_x, end_y = x2 + 90, y2
        mid_y = start_y + (end_y - start_y) / 2
        return f"M {start_x} {start_y} V {mid_y} H {end_x} V {end_y}"

def scaffold_html(title, domain, description, nodes, links, metrics=None):
    # Predefined color palettes
    colors = {
        "blue": {"border": "#4f8ef7", "bg": "rgba(79, 142, 247, 0.08)", "glow": "rgba(79, 142, 247, 0.4)"},
        "green": {"border": "#22c55e", "bg": "rgba(34, 197, 94, 0.08)", "glow": "rgba(34, 197, 94, 0.4)"},
        "purple": {"border": "#a78bfa", "bg": "rgba(167, 139, 250, 0.08)", "glow": "rgba(167, 139, 250, 0.4)"},
        "orange": {"border": "#fb923c", "bg": "rgba(251, 146, 60, 0.08)", "glow": "rgba(251, 146, 60, 0.4)"},
        "cyan": {"border": "#22d3ee", "bg": "rgba(34, 211, 238, 0.08)", "glow": "rgba(34, 211, 238, 0.4)"},
        "red": {"border": "#ef4444", "bg": "rgba(239, 68, 68, 0.08)", "glow": "rgba(239, 68, 68, 0.4)"},
        "teal": {"border": "#34d399", "bg": "rgba(52, 211, 153, 0.08)", "glow": "rgba(52, 211, 153, 0.4)"},
        "grey": {"border": "#4c6490", "bg": "rgba(76, 100, 144, 0.08)", "glow": "rgba(76, 100, 144, 0.4)"},
    }

    # Generate node SVGs
    nodes_svg = ""
    nodes_map = {n["id"]: n for n in nodes}
    
    # Calculate bounding box for SVG viewbox
    max_x = max([n["x"] for n in nodes]) + 250 if nodes else 800
    max_y = max([n["y"] for n in nodes]) + 150 if nodes else 600
    
    for n in nodes:
        nid = n["id"]
        nx, ny = n["x"], n["y"]
        label = n.get("label", nid)
        col_type = n.get("color", "blue")
        col = colors.get(col_type, colors["blue"])
        details = n.get("details", "")
        
        # Word wrapping for white bold centered font
        # split label into lines if it is too long to fit in 180px
        words = label.split()
        lines = []
        curr_line = ""
        for w in words:
            if len(curr_line + " " + w) > 15:
                lines.append(curr_line.strip())
                curr_line = w
            else:
                curr_line += " " + w
        if curr_line:
            lines.append(curr_line.strip())
            
        text_y_start = 45 - (len(lines) - 1) * 8
        text_svg = ""
        for i, line in enumerate(lines[:3]):
            text_svg += f'<text x="90" y="{text_y_start + i * 18}" text-anchor="middle" font-size="14" fill="#fff" font-weight="bold" font-family="Segoe UI, sans-serif">{line}</text>'

        nodes_svg += f"""
    <g class="node-group" id="node-{nid}" onclick="inspectNode('{nid}')" data-details="{details.replace('"', '&quot;')}">
      <rect x="{nx}" y="{ny}" width="180" height="80" rx="10" ry="10" 
            fill="{col['bg']}" stroke="{col['border']}" stroke-width="2" class="node-rect"
            style="filter: drop-shadow(0 0 4px {col['border']}22); --glow-color: {col['glow']}" />
      <g transform="translate({nx}, {ny})">
        {text_svg}
      </g>
    </g>"""

    # Generate link SVGs
    links_svg = ""
    for link in links:
        src, dst = link["source"], link["target"]
        if src not in nodes_map or dst not in nodes_map:
            continue
        n1, n2 = nodes_map[src], nodes_map[dst]
        path_d = generate_orthogonal_path(n1["x"], n1["y"], n2["x"], n2["y"])
        
        # Determine stroke color
        link_color = link.get("color", "#4c6490") # default grey link
        links_svg += f"""
    <path d="{path_d}" fill="none" stroke="{link_color}" stroke-width="2" class="link-path link-from-{src} link-to-{dst}" marker-end="url(#arrow)" />"""

    # Metrics section
    metrics_html = ""
    if metrics:
        for m in metrics:
            metrics_html += f"""
      <div class="metric-card">
        <div class="mv">{m['value']}</div>
        <div class="ml">{m['label']}</div>
      </div>"""

    # Full template
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Visual Companion</title>
<style>
:root {{
  --bg: #080c14; --surf: #0d1320; --card: #111827; --card-hover: #162032;
  --b: #1a2540; --b2: #1e2d4a; --txt: #dde5f5; --mu: #4c6490; --mu2: #7892c0;
  --acc: #4f8ef7; --grn: #22c55e; --pur: #a78bfa; --org: #fb923c; --cyan: #22d3ee;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Segoe UI', -apple-system, sans-serif; background: var(--bg); color: var(--txt); min-height: 100vh; display: flex; flex-direction: column; overflow: hidden; }}

/* Layout */
header {{ padding: 20px 40px; background: var(--surf); border-bottom: 1px solid var(--b); display: flex; justify-content: space-between; align-items: center; }}
header h1 {{ font-size: 1.5em; font-weight: 800; color: #fff; display: flex; align-items: center; gap: 12px; }}
header h1 span.domain {{ font-size: 0.6em; text-transform: uppercase; background: rgba(79,142,247,0.15); color: var(--acc); padding: 4px 10px; border-radius: 6px; letter-spacing: 0.05em; }}
header p.desc {{ color: var(--mu2); font-size: 0.9em; margin-top: 4px; }}
.back-btn {{ text-decoration: none; color: var(--mu2); font-size: 0.9em; display: flex; align-items: center; gap: 6px; padding: 6px 12px; border: 1px solid var(--b); border-radius: 8px; background: var(--card); transition: all 0.2s; }}
.back-btn:hover {{ color: #fff; border-color: var(--acc); background: rgba(79,142,247,0.05); }}

.main-container {{ display: flex; flex: 1; overflow: hidden; position: relative; }}

/* Canvas styling */
.canvas-container {{ flex: 1; overflow: auto; background: radial-gradient(circle at center, #0b111e 0%, #080c14 100%); position: relative; padding: 40px; display: flex; justify-content: center; align-items: center; }}
svg.diagram {{ min-width: {max_x}px; min-height: {max_y}px; display: block; }}

/* SVG Elements Styling */
.node-group {{ cursor: pointer; }}
.node-rect {{ transition: all 0.25s ease; }}
.node-group:hover .node-rect {{ stroke-width: 3px; filter: drop-shadow(0 0 12px var(--glow-color)); }}
.link-path {{ stroke-dasharray: 4; stroke-dashoffset: 0; animation: dash 20s linear infinite; opacity: 0.6; transition: all 0.25s; }}
.link-path:hover {{ opacity: 1; stroke-width: 3px; stroke-dasharray: 0; }}

/* Inspector Side Panel */
.inspector {{ width: 360px; background: var(--surf); border-left: 1px solid var(--b); padding: 24px; display: flex; flex-direction: column; gap: 20px; overflow-y: auto; z-index: 10; }}
.inspector h3 {{ font-size: 1.2em; font-weight: 700; color: #fff; padding-bottom: 12px; border-bottom: 1px solid var(--b); }}
.inspector-details {{ color: var(--mu2); font-size: 0.9em; line-height: 1.6; flex: 1; }}
.inspector-details strong {{ color: var(--txt); }}
.inspector-placeholder {{ display: flex; align-items: center; justify-content: center; height: 200px; color: var(--mu); text-align: center; font-style: italic; font-size: 0.95em; border: 1px dashed var(--b); border-radius: 12px; }}

/* Metrics Bar */
.metrics-bar {{ display: flex; gap: 16px; padding: 12px 40px; background: var(--surf); border-top: 1px solid var(--b); }}
.metric-card {{ background: var(--card); border: 1px solid var(--b); border-radius: 8px; padding: 8px 16px; display: flex; flex-direction: column; justify-content: center; }}
.metric-card .mv {{ font-size: 1.2em; font-weight: 800; color: var(--acc); font-family: 'Consolas', monospace; }}
.metric-card .ml {{ font-size: 0.65em; color: var(--mu); text-transform: uppercase; letter-spacing: 0.05em; }}

@keyframes dash {{
  to {{
    stroke-dashoffset: -1000;
  }}
}}
</style>
</head>
<body>

<header>
  <div>
    <h1>{title} <span class="domain">{domain}</span></h1>
    <p class="desc">{description}</p>
  </div>
  <a href="unesco_sap_landing.html" class="back-btn">&larr; Back to Landing Page</a>
</header>

<div class="main-container">
  <div class="canvas-container">
    <svg class="diagram" viewBox="0 0 {max_x} {max_y}" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#4c6490" />
        </marker>
        <marker id="arrow-active" viewBox="0 0 10 10" refX="2" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 1 L 10 5 L 0 9 z" fill="#4f8ef7" />
        </marker>
      </defs>

      <!-- Connection Lines -->
      {links_svg}

      <!-- Nodes -->
      {nodes_svg}
    </svg>
  </div>

  <div class="inspector">
    <h3>Object Inspector</h3>
    <div id="inspector-content">
      <div class="inspector-placeholder">Click any node in the flow diagram to inspect its metadata, related tables, and system dependencies.</div>
    </div>
  </div>
</div>

<div class="metrics-bar">
  {metrics_html}
</div>

<script>
function inspectNode(nodeId) {{
  const g = document.getElementById('node-' + nodeId);
  const details = g.getAttribute('data-details');
  const rect = g.querySelector('.node-rect');
  const strokeColor = rect.getAttribute('stroke');
  const label = g.querySelector('text').textContent;

  // Highlight connections connected to this node
  document.querySelectorAll('.link-path').forEach(link => {{
    link.style.opacity = 0.1;
    link.style.strokeWidth = 2;
  }});
  
  // Highlight outgoing
  document.querySelectorAll('.link-from-' + nodeId).forEach(link => {{
    link.style.opacity = 1;
    link.style.stroke = '#4f8ef7';
    link.style.strokeWidth = 3;
    link.setAttribute('marker-end', 'url(#arrow-active)');
  }});

  // Highlight incoming
  document.querySelectorAll('.link-to-' + nodeId).forEach(link => {{
    link.style.opacity = 1;
    link.style.stroke = '#a78bfa';
    link.style.strokeWidth = 3;
    link.setAttribute('marker-end', 'url(#arrow-active)');
  }});

  // Format details as HTML
  let detailsHtml = `
    <div style="margin-bottom:16px;">
      <span style="font-size:0.75em; text-transform:uppercase; background:rgba(255,255,255,0.05); color:${{strokeColor}}; padding:3px 8px; border-radius:4px; font-weight:600; border: 1px solid ${{strokeColor}}33;">${{nodeId.split(':')[0] || 'OBJECT'}}</span>
      <h4 style="font-size:1.4em; font-weight:800; color:#fff; margin-top:8px;">${{label}}</h4>
    </div>
  `;
  
  if (details) {{
    // Split key-value pairs or paragraphs
    const paragraphs = details.split('\\n');
    paragraphs.forEach(p => {{
      if (p.includes(':')) {{
        const [k, v] = p.split(':', 1);
        const rest = p.substring(k.length + 1);
        detailsHtml += `<p style="margin-bottom:8px;"><strong>${{k}}:</strong> ${{rest}}</p>`;
      }} else {{
        detailsHtml += `<p style="margin-bottom:12px;">${{p}}</p>`;
      }}
    }});
  }} else {{
    detailsHtml += `<p style="font-style:italic; color:var(--mu);">No additional details specified for this object node.</p>`;
  }}

  document.getElementById('inspector-content').innerHTML = detailsHtml;
}}

// Reset highlights on background click
document.querySelector('.canvas-container').addEventListener('click', function(e) {{
  if (e.target.tagName === 'svg' || e.target.classList.contains('canvas-container')) {{
    document.querySelectorAll('.link-path').forEach(link => {{
      link.style.opacity = 0.6;
      link.style.stroke = '#4c6490';
      link.style.strokeWidth = 2;
      link.setAttribute('marker-end', 'url(#arrow)');
    }});
    document.getElementById('inspector-content').innerHTML = `
      <div class="inspector-placeholder">Click any node in the flow diagram to inspect its metadata, related tables, and system dependencies.</div>
    `;
  }}
}}, true);
</script>
</body>
</html>
"""
    return html

def scaffold_file(filepath, title, domain, description, nodes, links, metrics=None):
    html = scaffold_html(title, domain, description, nodes, links, metrics)
    Path(filepath).write_text(html, encoding="utf-8")
    print(f"SUCCESS: Scaffolded visual companion at {filepath}")
