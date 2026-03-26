"""
revert_content_filter.py
User wants ALL objects kept in ALL groups — no removal.
Instead: tag content rows with a visual "content" badge.
The Objects/Content buttons become a HIGHLIGHT filter, not a hide filter.
"""
import os

with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

# Revert the catch-all group content exclusion
OLD_CATCHALL = (
    "  // Catch-all — in objects mode, exclude pure content types (TABU/TDAT) from general bucket\n"
    "  source.forEach(c => {\n"
    "    if (!assigned.has(c.name)) {\n"
    "      if (_mode === 'objects' && _CONTENT.has(c.obj_type)) {\n"
    "        assigned.add(c.name); // skip content in general group when objects mode\n"
    "      } else {\n"
    "        cfgGroupData['general'].push(c);\n"
    "        assigned.add(c.name);\n"
    "      }\n"
    "    }\n"
    "  });"
)
NEW_CATCHALL = (
    "  // Catch-all — all remaining objects go here, no filtering\n"
    "  source.forEach(c => {\n"
    "    if (!assigned.has(c.name)) {\n"
    "      cfgGroupData['general'].push(c);\n"
    "      assigned.add(c.name);\n"
    "    }\n"
    "  });"
)

if OLD_CATCHALL in h:
    h = h.replace(OLD_CATCHALL, NEW_CATCHALL, 1)
    print('Reverted catch-all — no objects removed from groups')
else:
    print('Catch-all already clean')

# Also change setCfgMode to use highlight/dim instead of hide/show
OLD_APPLY = (
    "function applyCfgFilter() {\n"
    "  var yr = window._cfgYear || 'all';\n"
    "  var mode = window._cfgMode || 'all';\n"
    "  document.querySelectorAll('.cfg-obj-row').forEach(row => {\n"
    "    var isContent = row.dataset.isContent === '1';\n"
    "    var modeOk = mode === 'all' || (mode === 'objects' && !isContent) || (mode === 'content' && isContent);\n"
    "    var yrOk = yr === 'all';\n"
    "    if (!yrOk) {\n"
    "      try { yrOk = JSON.parse(row.dataset.years || '[]').includes(yr); } catch(e) { yrOk = true; }\n"
    "    }\n"
    "    row.style.display = (modeOk && yrOk) ? '' : 'none';\n"
    "  });\n"
    "  // Update group visibility: hide groups where all rows are hidden\n"
    "  document.querySelectorAll('.cfg-group-panel').forEach(panel => {\n"
    "    var visible = panel.querySelectorAll('.cfg-obj-row:not([style*=\"display: none\"]):not([style*=\"display:none\"])').length;\n"
    "    var wrapper = panel.closest('.cc');\n"
    "    if (wrapper) wrapper.style.display = visible === 0 ? 'none' : '';\n"
    "  });\n"
    "}"
)
NEW_APPLY = (
    "function applyCfgFilter() {\n"
    "  var yr = window._cfgYear || 'all';\n"
    "  var mode = window._cfgMode || 'all';\n"
    "  document.querySelectorAll('.cfg-obj-row').forEach(row => {\n"
    "    var isContent = row.dataset.isContent === '1';\n"
    "    // Year filter (hide/show)\n"
    "    var yrOk = yr === 'all';\n"
    "    if (!yrOk) {\n"
    "      try { yrOk = JSON.parse(row.dataset.years || '[]').includes(yr); } catch(e) { yrOk = true; }\n"
    "    }\n"
    "    row.style.display = yrOk ? '' : 'none';\n"
    "    // Mode: dim (not hide) content rows in objects mode, dim objects in content mode\n"
    "    if (mode === 'objects') row.style.opacity = isContent ? '0.35' : '1';\n"
    "    else if (mode === 'content') row.style.opacity = isContent ? '1' : '0.35';\n"
    "    else row.style.opacity = '1';\n"
    "  });\n"
    "}"
)

if OLD_APPLY in h:
    h = h.replace(OLD_APPLY, NEW_APPLY, 1)
    print('Changed applyCfgFilter to DIM (not hide) content/object rows based on mode')
else:
    print('WARNING: applyCfgFilter pattern not matched — skipping')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Done! {os.path.getsize("cts_dashboard.html")//1024}KB')
