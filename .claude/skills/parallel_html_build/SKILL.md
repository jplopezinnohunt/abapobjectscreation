---
name: Parallel HTML Build
description: Protocol for building large single-file HTML/JS web applications in parallel parts to avoid LLM token limits, then joining them into one final file. Use this whenever building any complex web tool, dashboard, or HTML application.
domains:
  functional: [*]
  module: [*]
  process: []
---

# Parallel HTML Build Skill

## Problem This Solves
LLM token limits prevent writing large HTML files (>1500 lines) in a single generation. This skill breaks the build into focused parallel parts, each well within limits, then joins them using a Python script.

## When To Use
- Building any HTML app >800 lines
- Creating dashboards, tools, or rich UI with embedded JS/CSS
- Any time a previous attempt exceeded the token limit on a single write_to_file

## Protocol

### Step 1 — Plan Parts (BEFORE writing anything)
Decide on file split. Standard split for an HTML app:

| Part File | Content | Typical Size |
|---|---|---|
| `_app_part1_head.html` | DOCTYPE, `<head>`, ALL `<style>` CSS | ~500 lines |
| `_app_part2_body.html` | `<body>` HTML structure, all views/tabs | ~400 lines |
| `_app_part3_data.js` | Sample data, data generators, constants | ~200 lines |
| `_app_part4_engine.js` | Business logic, algorithms, core engine | ~300 lines |
| `_app_part5_ui.js` | UI controllers, chart renderers, event handlers, init | ~300 lines |

### Step 2 — Write All Parts IN PARALLEL
Call `write_to_file` for ALL parts simultaneously in a single response:
```
# Call these in parallel (no waitForPreviousTools):
write_to_file(_app_part1_head.html)   # CSS + head
write_to_file(_app_part2_body.html)   # HTML structure
write_to_file(_app_part3_data.js)     # Data layer
write_to_file(_app_part4_engine.js)   # Engine
write_to_file(_app_part5_ui.js)       # UI + init
```
> ⚠️ If 5 parallel calls are too many, write 3 in parallel then 2 more.

### Step 3 — Write the Joiner Script
Write `_join_parts.py`:
```python
import os
base = r'C:\path\to\output\dir'
out_path = os.path.join(base, 'final-app.html')
html_parts = ['_app_part1_head.html', '_app_part2_body.html']
js_parts   = ['_app_part3_data.js', '_app_part4_engine.js', '_app_part5_ui.js']
with open(out_path, 'w', encoding='utf-8') as out:
    for p in html_parts:
        out.write(open(os.path.join(base, p), encoding='utf-8').read())
    out.write('<script>\n')
    for p in js_parts:
        out.write(open(os.path.join(base, p), encoding='utf-8').read())
    out.write('</script>\n</body>\n</html>\n')
size = os.path.getsize(out_path)
print(f'SUCCESS: {size:,} bytes')
```

### Step 4 — Run the Joiner
```bash
python _join_parts.py
```
Use `SafeToAutoRun: true`.

### Step 5 — Verify in Browser
Use `browser_subagent` to open the final HTML file and take a screenshot. Confirm all views render correctly.

### Step 6 — Cleanup (Optional)
Delete part files after confirming the join worked:
```bash
Remove-Item _app_part*.html, _app_part*.js, _join_parts.py
```

## Key Rules

### vis.js MUST be inlined
VSCode webview blocks CDN requests. If the dashboard uses vis-network.js:
- Read `Zagentexecution/mcp-backend-server-python/vis-network.min.js` (644KB)
- Embed it as `<script>{content}</script>` in the head part
- NEVER use `<script src="https://unpkg.com/vis-network/..."></script>`
- Also verify all vis.DataSet node IDs are unique — duplicates cause silent blank render

### HTML Part Structure (part1 head)
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <!-- CDN scripts (INLINE vis.js if used — see rule above) -->
  <style>
    /* ALL CSS HERE */
  </style>
</head>
<!-- NO </html> NO </body> — joiner adds those -->
```

### Body Part Structure (part2 body)
```html
<body>
  <!-- ALL HTML structure -->
  <!-- Views, panels, modals, etc. -->
  <!-- DO NOT close </body></html> — joiner adds those -->
```

### JS Parts
- No `<script>` tags — joiner wraps all JS parts in one `<script>` block
- Each JS file is valid standalone JS (functions, classes, constants)
- Last JS part MUST contain the `DOMContentLoaded` init function

## Splitting Guidelines
- **CSS**: All design tokens, layout, components, animations in part1
- **HTML**: All views in part2 — use `display:none` for inactive views
- **Data**: All sample data, generators, constants in part3
- **Engine**: Core algorithms (mining engine, layout, parsers) in part4
- **UI**: All DOM manipulation, chart rendering, navigation, event handlers, app.init() in part5

## Real Data Embedding Pattern (NEW — v2)

When the HTML tool needs **real data** (not just samples), use a 2-stage pipeline:

### Stage 1 — Extract Real Data to JSON
```python
# _build_[source]_eventlog.py
import json
# Read SAP batch exports → convert to event log
# Output: { meta, kpis, events: [{caseId, activity, timestamp, ...}] }
with open('output_eventlog.json', 'w', encoding='utf-8') as f:
    json.dump(output, f)
```

### Stage 2 — Embed JSON as JS Constant
```python
# _build_realdata_js.py
with open('eventlog.json') as f:
    data = json.load(f)
js = f'const REAL_DATA = {json.dumps(data, ensure_ascii=False)};'
# Then wire into the Engine / override sample loader
```

Add the real data JS as an extra part (`_app_part3b_realdata.js`) in the joiner between data engine and map renderer.

**Limit sample size to ~400 cases / ~1500 events** for fast startup performance.

---

## Process Map Layout — Critical Algorithm Note

**NEVER use BFS for process graph layering.** BFS fails when:
- Event logs contain cycles (rework loops)
- Multiple paths to same node cause it to land in layer 0

**ALWAYS use: DFS Topological Sort + Longest-Path Layer Assignment**

```javascript
// Step 1: DFS topo sort (cycle-safe)
const visited = new Set(); const topoOrder = [];
const dfs = id => { if(visited.has(id))return; visited.add(id); succ[id].forEach(dfs); topoOrder.unshift(id); };
nodes.forEach(n => dfs(n.id));
// Step 2: Longest-path layer (forward pass)
const layers = {};
topoOrder.forEach(id => {
    layers[id] = pred[id].reduce((m,p) => Math.max(m, (layers[p]||0)+1), 0);
});
// Step 3: hGap = max(NW+60, ...) — guarantee no column overlap
```

---

## Iterative Part Updates (Post-Build)

After the initial full parallel build, use targeted edits instead of full rewrites:
1. `multi_replace_file_content` on the specific `_part*.js` file
2. Run `python _join_parts.py` to rebuild (autorun safe ✅)
3. **Always `view_file` before `replace_file_content`** — match exact whitespace/encoding

---

## Known Failure Modes

| Failure | Cause | Fix |
|---------|-------|-----|
| `target content not found` | Windows CRLF vs LF whitespace mismatch | Always `view_file` first to get exact content |
| All nodes pile at same x-position | BFS layout with cycles → all land at layer 0 | Use DFS topo sort + longest-path |
| Orphaned code after replace | `replace_file_content` matched too little | Always include closing `},` in target content |
| JSON UTF-16 decode error | Some SAP export files use UTF-16 | Probe with `open(f,'rb')` + check BOM bytes first |
| Browser `file://` blocked | Browser subagent cannot open local HTML | Ask user to open manually; use `browser_subagent` with server URL instead |
| Real data JS too large | 400+ cases × full event objects = >1MB | Sample to max 400 cases, strip non-essential fields |

## Success Criteria

You know it worked when:
- `python _join_parts.py` outputs `SUCCESS: X bytes` where X > expected minimum
- File opens in browser with no JS console errors
- All navigation views switch correctly
- Real data loader produces different results than the sample data

- ❌ DO NOT use PowerShell heredocs or echo to write HTML (quoting issues)
- ❌ DO NOT try to write everything in one file if it exceeds ~800 lines
- ❌ DO NOT close `</body></html>` in part2 — the joiner adds it
- ❌ DO NOT add `<script>` tags in JS parts — joiner wraps them

## Browser Verification Checklist
After joining and opening in browser, verify:
1. Page loads without JS console errors
2. All navigation tabs work
3. Default data renders on first load
4. Charts display correctly
5. Interactive elements (click, hover) respond
