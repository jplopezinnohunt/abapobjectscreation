"""
patch_config_filter.py  (final version)
Patches assignCfgGroups() to filter content/object types BEFORE computing group stats.
buildConfig() re-calls assignCfgGroups every time by resetting cfgGroupData on mode change.
"""
import os

with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

CONTENT_TYPES_JS = "new Set(['TABU','TDAT','CDAT','DATED'])"

# ── Patch 1: assignCfgGroups — add content filter to source ──────────────────
OLD_ASSIGN = (
    "function assignCfgGroups() {\n"
    "  if (cfgGroupData) return cfgGroupData;\n"
    "  const source = Object.entries(CFGDETAIL).map(([name, v]) => ({name, ...v}));\n"
    "  source.sort((a,b) => b.total_mods - a.total_mods);"
)

NEW_ASSIGN = (
    "function assignCfgGroups() {\n"
    "  if (cfgGroupData) return cfgGroupData;\n"
    "  const _CONTENT = " + CONTENT_TYPES_JS + ";\n"
    "  const _mode = window._cfgMode || 'objects';\n"
    "  let source = Object.entries(CFGDETAIL).map(([name, v]) => ({name, ...v}));\n"
    "  if (_mode === 'objects') source = source.filter(c => !_CONTENT.has(c.obj_type));\n"
    "  else if (_mode === 'content') source = source.filter(c => _CONTENT.has(c.obj_type));\n"
    "  source.sort((a,b) => b.total_mods - a.total_mods);"
)

if OLD_ASSIGN in h:
    h = h.replace(OLD_ASSIGN, NEW_ASSIGN, 1)
    print('Patched assignCfgGroups() to filter by mode')
else:
    print('ERROR: assignCfgGroups pattern not matched')
    print('Looking for:')
    print(repr(OLD_ASSIGN[:100]))

# ── Patch 2: setCfgMode — reset cfgGroupData and re-render ───────────────────
OLD_SETMODE = (
    "function setCfgMode(mode, el) {\n"
    "  window._cfgMode = mode;\n"
    "  \n"
    "  document.querySelectorAll('.cfg-mode-btn').forEach(b => b.classList.remove('active'));\n"
    "  if (el) el.classList.add('active');\n"
    "  applyCfgFilter();\n"
    "}"
)

NEW_SETMODE = (
    "function setCfgMode(mode, el) {\n"
    "  window._cfgMode = mode;\n"
    "  document.querySelectorAll('.cfg-mode-btn').forEach(b => b.classList.remove('active'));\n"
    "  if (el) el.classList.add('active');\n"
    "  // Reset group cache so assignCfgGroups re-filters on next buildConfig call\n"
    "  cfgGroupData = null;\n"
    "  // Re-render config section\n"
    "  const ct = document.getElementById('cfg-ct');\n"
    "  if (ct) { ct.innerHTML = ''; buildConfig(); }\n"
    "}"
)

if OLD_SETMODE in h:
    h = h.replace(OLD_SETMODE, NEW_SETMODE, 1)
    print('Patched setCfgMode() to reset and re-render')
else:
    print('WARNING: setCfgMode pattern not matched exactly — trying loose match')
    idx = h.find('function setCfgMode(mode, el)')
    if idx != -1:
        end = h.find('\n}', idx) + 2
        print(f'Found at {idx}-{end}')
        print('Current:', repr(h[idx:end]))
    else:
        print('setCfgMode NOT FOUND at all')

# ── Patch 3: Override setCfgYear to also reset cfgGroupData ──────────────────
# Find the injected setCfgYear that calls applyCfgFilter, update to reset+re-render
OLD_YEAR = (
    "window.setCfgYear = function(yr, el) {\n"
    "  window._cfgYear = yr;\n"
    "  document.querySelectorAll('.cfg-yr-btn').forEach(b => b.classList.remove('active'));\n"
    "  if (el) el.classList.add('active');\n"
    "  applyCfgFilter();\n"
    "};"
)

NEW_YEAR = (
    "window.setCfgYear = function(yr, el) {\n"
    "  window._cfgYear = yr;\n"
    "  document.querySelectorAll('.cfg-yr-btn').forEach(b => b.classList.remove('active'));\n"
    "  if (el) el.classList.add('active');\n"
    "  applyCfgFilter();\n"
    "};\n"
)

# This one is likely fine as-is; year filter just hides rows, doesn't need re-render

# ── Patch 4: Default mode = objects in the window variables ──────────────────
if "window._cfgMode = 'all'" in h:
    h = h.replace("window._cfgMode = 'all'", "window._cfgMode = 'objects'", 1)
    print("Set default _cfgMode to 'objects'")
elif "window._cfgMode" not in h:
    print("_cfgMode not set yet — will rely on assignCfgGroups default")

# ── Save ──────────────────────────────────────────────────────────────────────
with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Done! {os.path.getsize("cts_dashboard.html")//1024}KB')
