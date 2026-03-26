"""
separate_objects_content.py
Adds Objects vs Content tab filter to Config Elements section.
Content types: TABU, TDAT, CDAT, DATED  (table DATA rows)
Object types:  everything else          (structural repository objects)

Also patches the 'Unique objects' KPI stat to only count structural objects.
"""
import json, os, re

# ── Content type set ──────────────────────────────────────────────────────────
CONTENT_TYPES = {'TABU', 'TDAT', 'CDAT', 'DATED'}

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

# Tag each entry with content_type flag
for name, v in cfg.items():
    v['is_content'] = v.get('obj_type','') in CONTENT_TYPES

n_content = sum(1 for v in cfg.values() if v.get('is_content'))
n_objects = len(cfg) - n_content
print(f'Content entries (TABU/TDAT/CDAT): {n_content}')
print(f'Object entries (structural):       {n_objects}')
print(f'Total:                             {len(cfg)}')

with open('cts_config_detail.json', 'w', encoding='utf-8') as f:
    json.dump(cfg, f, ensure_ascii=False)

# ── Patch HTML ────────────────────────────────────────────────────────────────
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# 1. Re-inject CFGDETAIL
NEW_CFG = 'const CFGDETAIL=' + json.dumps(cfg, separators=(',',':'), ensure_ascii=False) + ';\n'
s = html.find('const CFGDETAIL='); e = html.find(';\n', s)+2
html = html[:s] + NEW_CFG + html[e:]
print('Re-injected CFGDETAIL')

# 2. Add CONTENT_TYPES constant to JS
if 'const CONTENT_TYPES' not in html:
    insert_at = html.find('const CFGDETAIL=')
    html = html[:insert_at] + \
        "const CONTENT_TYPES=new Set(['TABU','TDAT','CDAT','DATED']);\n" + \
        html[insert_at:]
    print('Added CONTENT_TYPES constant')

# 3. Add data-is-content attribute to cfg-obj-row in JS template
#    Current: <tr class="cfg-obj-row" data-years='...'>
#    New:     <tr class="cfg-obj-row" data-years='...' data-is-content="${c.is_content?'1':'0'}">
OLD_ROW = "return `<tr class=\"cfg-obj-row\" data-years='${JSON.stringify(c.years_active||[])}'>"
NEW_ROW = "return `<tr class=\"cfg-obj-row\" data-years='${JSON.stringify(c.years_active||[])}' data-is-content=\"${c.is_content?'1':'0'}\">"
if OLD_ROW in html:
    html = html.replace(OLD_ROW, NEW_ROW, 1)
    print('Added data-is-content attribute to row template')
else:
    print('WARNING: row template pattern not matched')

# 4. Add Objects/Content tab filter UI + JS logic
#    Find the config section header and add filter tabs after it
#    Look for where the config container starts
CFG_FILTER_JS = """
// Config Objects vs Content filter
window._cfgMode = 'objects'; // default: show structural objects only
function setCfgMode(mode, el) {
  window._cfgMode = mode;
  document.querySelectorAll('.cfg-mode-btn').forEach(b => b.classList.remove('active'));
  if (el) el.classList.add('active');
  applyCfgFilter();
}
function applyCfgFilter() {
  var yr = window._cfgYear || 'all';
  var mode = window._cfgMode || 'all';
  document.querySelectorAll('.cfg-obj-row').forEach(row => {
    var isContent = row.dataset.isContent === '1';
    var modeOk = mode === 'all' || (mode === 'objects' && !isContent) || (mode === 'content' && isContent);
    var yrOk = yr === 'all';
    if (!yrOk) {
      try { yrOk = JSON.parse(row.dataset.years || '[]').includes(yr); } catch(e) { yrOk = true; }
    }
    row.style.display = (modeOk && yrOk) ? '' : 'none';
  });
  // Update group visibility: hide groups where all rows are hidden
  document.querySelectorAll('.cfg-group-panel').forEach(panel => {
    var visible = panel.querySelectorAll('.cfg-obj-row:not([style*="display: none"]):not([style*="display:none"])').length;
    var wrapper = panel.closest('.cc');
    if (wrapper) wrapper.style.display = visible === 0 ? 'none' : '';
  });
}
// Override setCfgYear to also apply mode filter
var _origSetCfgYear = window.setCfgYear;
window.setCfgYear = function(yr, el) {
  window._cfgYear = yr;
  document.querySelectorAll('.cfg-yr-btn').forEach(b => b.classList.remove('active'));
  if (el) el.classList.add('active');
  applyCfgFilter();
};
"""

if 'setCfgMode' not in html:
    script_end = html.rfind('</script>')
    html = html[:script_end] + CFG_FILTER_JS + '\n' + html[script_end:]
    print('Added setCfgMode() JS function')

# 5. Find the Config Elements container and prepend mode filter buttons
#    Look for the config section header ID
#    In the HTML likely: id="config" or id="sect-config" 
#    We'll insert the filter bar right after content loads in the config section
#    Strategy: find the config section's first <div id= or section marker

# Find the config section JS render function and add mode buttons to its header
# The header is built dynamically; instead, inject static HTML into the config panel wrapper
# by adding a filter bar after the page loads via JS

CFG_UI_JS = """
// Inject config mode filter bar
(function() {
  var attempts = 0;
  function injectCfgBar() {
    var cfg = document.getElementById('config') || document.querySelector('[data-section="config"]');
    if (!cfg && attempts < 20) { attempts++; setTimeout(injectCfgBar, 300); return; }
    if (!cfg) return;
    if (document.getElementById('cfg-mode-bar')) return;
    var bar = document.createElement('div');
    bar.id = 'cfg-mode-bar';
    bar.style.cssText = 'display:flex;gap:8px;padding:12px 16px 0;align-items:center;flex-wrap:wrap';
    bar.innerHTML = '<span style="font-size:.7rem;color:var(--mu);margin-right:4px">Show:</span>'
      + '<button class="cfg-mode-btn active" onclick="setCfgMode(\\'objects\\',this)" '
      + 'style="background:rgba(79,142,247,.15);border:1px solid rgba(79,142,247,.3);color:#4f8ef7;'
      + 'border-radius:6px;padding:3px 12px;cursor:pointer;font-size:.72rem;font-family:inherit">'
      + '&#128196; Objects only</button>'
      + '<button class="cfg-mode-btn" onclick="setCfgMode(\\'content\\',this)" '
      + 'style="background:rgba(245,158,11,.1);border:1px solid rgba(245,158,11,.3);color:#f59e0b;'
      + 'border-radius:6px;padding:3px 12px;cursor:pointer;font-size:.72rem;font-family:inherit">'
      + '&#127758; Content only (TABU/TDAT)</button>'
      + '<button class="cfg-mode-btn" onclick="setCfgMode(\\'all\\',this)" '
      + 'style="background:rgba(100,116,139,.15);border:1px solid rgba(100,116,139,.3);color:#94a3b8;'
      + 'border-radius:6px;padding:3px 12px;cursor:pointer;font-size:.72rem;font-family:inherit">'
      + '&#128279; All</button>'
      + '<span style="margin-left:12px;font-size:.68rem;color:var(--mu2)">"""  \
      + f"{n_objects:,} objects · {n_content:,} content entries</span>" + """';
    cfg.insertBefore(bar, cfg.firstChild);
    // Apply default filter (objects only)
    setTimeout(function() { applyCfgFilter(); }, 500);
  }
  injectCfgBar();
})();
"""

FINAL_JS = """
<script>
""" + CFG_UI_JS + """
</script>
</body>"""

html = html.replace('</body>', FINAL_JS, 1)
print('Injected config mode bar UI')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Done! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
print(f'\nKey numbers:')
print(f'  Structural OBJECTS: {n_objects:,}')
print(f'  Content entries:    {n_content:,}')
print(f'  Total in transport: {len(cfg):,}')
