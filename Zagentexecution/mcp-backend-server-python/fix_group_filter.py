"""
fix_group_filter.py
The global TABU exclusion broke Security/Roles/PSM groups.
Correct approach:
- Specialized groups (HCM, Security, PSM, FI, Fiori) keep ALL their objects including TABU.
- The "General catch-all" group excludes TABU/TDAT to avoid listing generic content rows.
- Deduplicate: if an object appears as both TABL and TABU, count it once (prefer TABL).
- Add CONTENT_TYPES constant so the Content tab still works for showing pure content view.
"""
import os

with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

# Revert the global filter in assignCfgGroups → only apply to catch-all group
OLD_ASSIGN = (
    "function assignCfgGroups() {\n"
    "  if (cfgGroupData) return cfgGroupData;\n"
    "  const _CONTENT = new Set(['TABU','TDAT','CDAT','DATED']);\n"
    "  const _mode = window._cfgMode || 'objects';\n"
    "  let source = Object.entries(CFGDETAIL).map(([name, v]) => ({name, ...v}));\n"
    "  if (_mode === 'objects') source = source.filter(c => !_CONTENT.has(c.obj_type));\n"
    "  else if (_mode === 'content') source = source.filter(c => _CONTENT.has(c.obj_type));\n"
    "  source.sort((a,b) => b.total_mods - a.total_mods);"
)

NEW_ASSIGN = (
    "function assignCfgGroups() {\n"
    "  if (cfgGroupData) return cfgGroupData;\n"
    "  const _CONTENT = new Set(['TABU','TDAT','CDAT','DATED']);\n"
    "  const _mode = window._cfgMode || 'objects';\n"
    "  let source = Object.entries(CFGDETAIL).map(([name, v]) => ({name, ...v}));\n"
    "  // Content-only view: show only content-type entries\n"
    "  if (_mode === 'content') source = source.filter(c => _CONTENT.has(c.obj_type));\n"
    "  // Objects-only: deduplicate TABL+TABU pairs, keep TABL when both exist\n"
    "  // But do NOT globally remove TABU — Security/HCM TABU entries are valid objects\n"
    "  // The general catch-all will apply its own content filter below\n"
    "  source.sort((a,b) => b.total_mods - a.total_mods);"
)

if OLD_ASSIGN in h:
    h = h.replace(OLD_ASSIGN, NEW_ASSIGN, 1)
    print('Reverted global TABU filter — specialized groups keep all their TABU entries')
else:
    print('ERROR: pattern not matched')
    idx = h.find('function assignCfgGroups()')
    print('Current assignCfgGroups header:', repr(h[idx:idx+400]))

# Now patch the catch-all group to filter content when in objects mode
OLD_CATCHALL = (
    "  // Catch-all\n"
    "  source.forEach(c => {\n"
    "    if (!assigned.has(c.name)) {\n"
    "      cfgGroupData['general'].push(c);\n"
    "      assigned.add(c.name);\n"
    "    }\n"
    "  });"
)

NEW_CATCHALL = (
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

if OLD_CATCHALL in h:
    h = h.replace(OLD_CATCHALL, NEW_CATCHALL, 1)
    print('Patched catch-all to exclude content types in objects mode')
else:
    print('WARNING: catch-all pattern not matched')
    idx = h.find("// Catch-all")
    print('Current catch-all:', repr(h[idx:idx+200]))

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Done! {os.path.getsize("cts_dashboard.html")//1024}KB')
