"""
Merge two group pairs in Config Elements:
  1. Auth Config Tables + User Mgmt Tables → Security & Authorization
  2. HCM Config Views (VDAT) + HCM Config Tables → HCM Config
"""
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# ── Find and replace the CFG_GROUPS array ─────────────────────────────────────
OLD_GROUPS_START = 'const CFG_GROUPS = ['
OLD_GROUPS_END   = '];\n\nlet cfgGroupData'

start = html.find(OLD_GROUPS_START)
end   = html.find(OLD_GROUPS_END, start)

if start == -1 or end == -1:
    print(f'Could not find CFG_GROUPS: start={start}, end={end}')
    raise SystemExit(1)

NEW_GROUPS = """const CFG_GROUPS = [
  {
    id: 'security',
    label: 'Security & Authorization',
    color: '#ef4444',
    icon: '🔐',
    desc: 'AGR_* authorization tables + USRxx/USTxx user master tables. Only 10 unique tables but transported 3,400+ times — each role transport automatically updates these system tables.',
    match: c => /^AGR_|^USR|^UST|^SUSR/.test(c.name) || ['TVDIR','TDDAT','PRGN_STAT','SPERS_OBJ','SPERS'].includes(c.name),
  },
  {
    id: 'hcm',
    label: 'HCM Config',
    color: '#a78bfa',
    icon: '👥',
    desc: 'HCM payroll & OM configuration — VDAT pay-scale views (V_T510, V_T7UNPAD*) and TABU T7/T5xx payroll schema tables. Active every year = ongoing HR config maintenance.',
    match: c => c.obj_type === 'VDAT' || c.obj_type === 'CDAT' ||
                (c.obj_type === 'TABU' && /^(T7|T5[0-9]|T50|T54|PA0|MOLGA|T001P|T500L|T508)/.test(c.name)),
  },
  {
    id: 'psm',
    label: 'PSM / Funds Management Config',
    color: '#86efac',
    icon: '💰',
    desc: 'Public Sector Management — UCUMxxx fund tables, UGWBxxxx FM integration config.',
    match: c => /^(UCU|UGW|FMFG|FM[A-Z])/.test(c.name),
  },
  {
    id: 'general',
    label: 'General Customizing (IMG / Other)',
    color: '#f59e0b',
    icon: '⚙️',
    desc: 'All other IMG entries — number ranges, variants, SCVI screen variants, OSOA output conditions, TTYP type definitions, and general SAP config.',
    match: () => true,
  },
]"""

html = html[:start] + NEW_GROUPS + html[end + len(OLD_GROUPS_END) - len('\n\nlet cfgGroupData'):]

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

import os
print(f'Done! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
print('Config groups now:')
print('  1. Security & Authorization (Auth + User Mgmt merged)')
print('  2. HCM Config (VDAT views + T7/T5xx tables merged)')
print('  3. PSM / Funds Management Config')
print('  4. General Customizing (catch-all)')
