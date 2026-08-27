---
name: Integration Diagram Builder
description: >
  Standard for building container-based architecture diagrams using hub-and-spoke layout.
  Pure CSS/SVG — no vis.js, no external libraries. Dark theme with neon accents, orthogonal
  90° connections, functional zones, and interactive click-to-inspect nodes.
  Use this skill whenever building system connectivity maps, interface diagrams, or
  architecture visualizations.
domains:
  functional: [Integration]
  module: [BASIS]
  process: []
---

# Integration Diagram Builder

## Purpose

Generate clean, structured, visually balanced system architecture diagrams as standalone HTML files. Used for SAP system landscapes, interface maps, and any hub-and-spoke connectivity visualization.

## NEVER Do This

1. NEVER use vis.js, D3, GoJS, or any external library — pure CSS + inline SVG only
2. NEVER use physics-based or force-directed layout — all positions are fixed
3. NEVER use curved/parabolic lines — orthogonal (90°) routing only
4. NEVER use CDN links — everything must be self-contained (VSCode blocks CDNs)
5. NEVER let connections cross if avoidable — adjust node positions instead
6. NEVER put all nodes in a flat ring/snowflake — use functional zones

## Architecture Pattern

```
┌─────────────────────────────────────────────────────────────┐
│  ENVIRONMENT CONTAINER (bounded border, labeled)             │
│                                                              │
│  ┌──────────── EXTERNAL SERVICES (top) ──────────────┐      │
│  │  [Ext1]  [Ext2]  [Ext3]  [Ext4]  [Ext5]          │      │
│  └───────────────────────────────────────────────────┘      │
│                                                              │
│  ┌─────────┐  ┌──── CORE HUB (center) ────┐  ┌──────────┐  │
│  │ LEFT    │  │                            │  │ RIGHT    │  │
│  │ ZONE    │  │       ╔═══════╗            │  │ ZONE     │  │
│  │         │  │       ║  HUB  ║            │  │          │  │
│  │ [Node]  │  │       ╚═══════╝            │  │ [Node]   │  │
│  │ [Node]  │  │    [Satellite] [Satellite] │  │ [Node]   │  │
│  │ [Node]  │  │                            │  │ [Node]   │  │
│  └─────────┘  └────────────────────────────┘  └──────────┘  │
│                                                              │
│  ┌─── SPOKE 1 ───┐  ┌─── SPOKE 2 ───┐  ┌─── SPOKE 3 ───┐  │
│  │ [N1] [N2]     │  │ [N3] [N4] [N5]│  │ [N6] [N7]     │  │
│  └───────────────┘  └───────────────┘  └───────────────┘  │
│                                                              │
│  ┌──────────── BOTTOM ZONE ──────────────────────────┐      │
│  │  [B1]  [B2]  [B3]                                │      │
│  └───────────────────────────────────────────────────┘      │
│                                                              │
│  [Legend: color dots + line styles]                           │
└─────────────────────────────────────────────────────────────┘
```

## Zone Assignment Rules

When building a diagram, classify each node into a zone:

| Zone | Position | Purpose | Grid |
|------|----------|---------|------|
| External Services | Top | Entry points, external APIs, cloud | Horizontal flex row |
| Left Zone | Middle-left | Infrastructure, support systems | Vertical stack (200px) |
| Core Hub | Center | Primary system (largest, glowing) | Centered with satellites |
| Right Zone | Middle-right | Management, monitoring | Vertical stack (200px) |
| Spoke Groups | Bottom row | Secondary systems by category | 3-column grid |
| Bottom Zone | Bottom | Analytics, reporting, auxiliary | Horizontal flex row |

**Grid**: `middle-row` uses `grid-template-columns: 200px 1fr 200px`; `spoke-row` uses `1fr 1fr 1fr`.

## CSS Design System

### Color Palette (MANDATORY)

```css
:root {
  --bg: #080b12; --surface: #0c1018; --card: #111827;
  --border: #1a2540; --border-glow: #1e3a5f;
  --text: #c8d6e5; --muted: #4a5f80; --white: #eef2f7;
  --neon-blue: #4f8ef7;    /* Development, primary accent */
  --neon-cyan: #22d3ee;    /* External services */
  --neon-green: #22c55e;   /* Spoke labels */
  --neon-orange: #fb923c;  /* Test/QA systems */
  --neon-red: #ef4444;     /* Production systems */
  --neon-purple: #a78bfa;  /* Validation systems */
  --neon-yellow: #f59e0b;  /* Management (SolMan) */
  --neon-teal: #2dd4bf;    /* Analytics (BW) */
  --neon-gray: #64748b;    /* Infrastructure */
}
```

### Node Classes

Each node type has a consistent style pattern:

```css
.node.{type} {
  background: rgba({r},{g},{b}, 0.1);      /* 10% fill */
  border-color: rgba({r},{g},{b}, 0.3);    /* 30% border */
  color: var(--neon-{color});              /* neon text */
}
.node.{type}:hover {
  box-shadow: 0 0 20px rgba({r},{g},{b}, 0.12);  /* glow on hover */
}
```

| Class | Color Var | Use For |
|-------|-----------|---------|
| `.hub` | `--neon-red` | Central system (gradient bg, larger, double glow) |
| `.prod` | `--neon-red` | Production systems |
| `.dev` | `--neon-blue` | Development systems |
| `.test` | `--neon-orange` | Test/QA systems |
| `.val` | `--neon-purple` | Validation systems |
| `.solman` | `--neon-yellow` | Solution Manager / management |
| `.bwn` | `--neon-teal` | BW / Analytics |
| `.infra` | `--neon-gray` | Infrastructure, app servers |
| `.ext` | `--neon-cyan` | External services |
| `.legacy` | `--neon-gray` | Decommissioned (70% opacity) |

### Hub Node (special)

```css
.node.hub {
  background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.1));
  border-color: rgba(239,68,68,0.5);
  color: #fff;
  box-shadow: 0 0 30px rgba(239,68,68,0.12), 0 0 60px rgba(239,68,68,0.05);
  padding: 16px 28px;
}
```

### Zone Containers

```css
.zone {
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 16px 16px 12px;
  position: relative;
  background: rgba(17,24,39,0.4);
}
.zone-label {
  position: absolute; top: -9px; left: 16px;
  background: var(--surface);
  padding: 0 8px;
  font-size: 0.6em; text-transform: uppercase;
  letter-spacing: 0.1em; font-weight: 600;
}
```

Each zone type adds subtle glow:
```css
.zone.{type} {
  border-color: rgba({r},{g},{b}, 0.15);
  box-shadow: 0 0 20px rgba({r},{g},{b}, 0.03);
}
```

### Environment Container

```css
.env-border {
  border: 1px solid var(--border);
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(15,20,35,0.8), rgba(8,11,18,0.95));
  padding: 20px 24px 28px;
}
.env-label {
  position: absolute; top: -10px; left: 28px;
  background: var(--bg); padding: 0 12px;
  font-size: 0.65em; text-transform: uppercase;
  letter-spacing: 0.12em; color: var(--neon-blue);
}
```

## Connection Drawing (SVG Overlay)

### Setup

Place an SVG element inside the environment container with `position: absolute; pointer-events: none;`.

### Orthogonal Routing Algorithm

From each node to the hub, draw L-shaped paths (one turn, 90°):

```javascript
function drawConnections() {
  const svg = document.getElementById('connections');
  const container = document.querySelector('.env-border');
  const rect = container.getBoundingClientRect();
  svg.setAttribute('width', rect.width);
  svg.setAttribute('height', rect.height);

  const hub = document.querySelector('.node.hub');
  const hubRect = hub.getBoundingClientRect();
  const hubCx = hubRect.left + hubRect.width / 2 - rect.left;
  const hubCy = hubRect.top + hubRect.height / 2 - rect.top;

  let svgContent = '';

  document.querySelectorAll('.node[data-info]:not(.hub)').forEach(node => {
    const nr = node.getBoundingClientRect();
    const nx = nr.left + nr.width / 2 - rect.left;
    const ny = nr.top + nr.height / 2 - rect.top;
    const dx = Math.abs(nx - hubCx);
    const dy = Math.abs(ny - hubCy);

    let path;
    if (dy > dx) {
      // Mostly vertical: vertical first, then horizontal
      const midY = hubCy + (ny - hubCy) * 0.5;
      path = `M${nx},${ny} L${nx},${midY} L${hubCx},${midY} L${hubCx},${hubCy}`;
    } else {
      // Mostly horizontal: horizontal first, then vertical
      const midX = hubCx + (nx - hubCx) * 0.5;
      path = `M${nx},${ny} L${midX},${ny} L${midX},${hubCy} L${hubCx},${hubCy}`;
    }

    const color = getNodeColor(node);
    const dashed = node.classList.contains('ext');
    const dashAttr = dashed ? 'stroke-dasharray="6,4"' : '';
    const cls = dashed ? 'conn-secondary' : 'conn-primary';
    svgContent += `<path d="${path}" stroke="${color}" ${dashAttr} class="${cls}"/>`;
  });

  svg.innerHTML = svgContent;
}

window.addEventListener('load', () => setTimeout(drawConnections, 100));
window.addEventListener('resize', drawConnections);
```

### Connection Styles

```css
.conn-primary { stroke-width: 1.5; fill: none; opacity: 0.5; }
.conn-secondary { stroke-width: 1; fill: none; stroke-dasharray: 6,4; opacity: 0.4; }
```

| Type | Style | Use |
|------|-------|-----|
| Primary RFC | Solid, 1.5px | Internal SAP-to-SAP connections |
| External/HTTP | Dashed, 1px | External services, cloud, APIs |

### Color Mapping

Edge color matches the node's category color:
- `.ext` → `#22d3ee` (cyan)
- `.dev` → `#4f8ef7` (blue)
- `.test` → `#fb923c` (orange)
- `.val` → `#a78bfa` (purple)
- `.solman` → `#f59e0b` (yellow)
- `.bwn` → `#2dd4bf` (teal)
- `.infra` → `#64748b` (gray)
- `.prod`, `.legacy` → `#ef4444` (red)

## Node HTML Structure

```html
<div class="node {type}" data-info="Tooltip text&#10;Line 2&#10;Line 3">
  <div class="name">SYS_ID</div>
  <div class="desc">Description</div>
  <div class="rfc-count">N</div>  <!-- connection count badge -->
</div>
```

- `data-info`: multi-line tooltip (use `&#10;` for newlines)
- `.rfc-count`: absolute-positioned badge top-right, blue pill

## Interactive Features

### Click-to-Inspect Panel

```html
<div class="info-panel" id="infoPanel">
  <span class="close-btn" onclick="this.parentElement.classList.remove('visible')">&times;</span>
  <h3 id="infoTitle"></h3>
  <div class="info-body" id="infoBody"></div>
</div>
```

```javascript
document.querySelectorAll('.node[data-info]').forEach(node => {
  node.addEventListener('click', function() {
    document.getElementById('infoTitle').textContent =
      this.querySelector('.name').textContent;
    document.getElementById('infoBody').textContent = this.dataset.info;
    document.getElementById('infoPanel').classList.add('visible');
  });
});
```

### Header Stats Bar

```html
<div class="header">
  <h1><span>&#9670;</span> Title</h1>
  <div class="header-stats">
    <div class="hstat">
      <div class="v" style="color:var(--neon-blue)">26</div>
      <div class="l">Systems</div>
    </div>
    <!-- more stats -->
  </div>
</div>
```

### Legend

Always include at the bottom of the environment container:
```html
<div class="legend">
  <div class="legend-item">
    <div class="legend-dot" style="background:rgba(r,g,b,0.2);border-color:rgba(r,g,b,0.5);"></div>
    Label
  </div>
  <div class="legend-item">
    <div class="legend-line" style="border-color:var(--neon-blue);"></div>
    Primary RFC
  </div>
  <div class="legend-item">
    <div class="legend-line dashed" style="border-color:var(--neon-cyan);"></div>
    External/HTTP
  </div>
</div>
```

## Responsive

```css
@media (max-width: 900px) {
  .middle-row { grid-template-columns: 1fr; }
  .spoke-row { grid-template-columns: 1fr; }
}
```

## Reference Implementation

**Live example**: `Zagentexecution/mcp-backend-server-python/connectivity_diagram.html`

This is the canonical reference — when building a new integration diagram, start from this file's structure and adapt the nodes/zones to the new context.

## Adaptation Guide

To build a diagram for a different context (e.g., API architecture, microservices):

1. **Keep**: Color palette, zone container pattern, node classes, SVG routing, info panel, legend
2. **Change**: Zone labels, node data, header stats, environment label
3. **Add new node classes** if needed — follow the `rgba(r,g,b, 0.1/0.3)` pattern
4. **Add zones** if needed — follow the `.zone` + `.zone-label` pattern

## You Know It Worked When

- All nodes are inside labeled zone containers
- Hub is visually dominant (largest, glowing, center)
- Connections are orthogonal (L-shaped, 90° turns)
- No crossed connections (adjust positions if needed)
- File is self-contained HTML, no external dependencies
- File size < 30KB (no inlined libraries)
- Click on any node shows detail panel
- Responsive on mobile (single column)
- Dark theme with neon accents matches project companions
