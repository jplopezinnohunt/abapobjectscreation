"""Merge Auth Config Tables + User Mgmt Tables → Security & Authorization."""
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

OLD = """const CFG_GROUPS = [
  {
    id: 'auth',
    label: 'Auth Config Tables',
    color: '#ef4444',
    icon: '🔐',
    desc: 'AGR_* authorization object tables — only a handful of unique tables, each transported hundreds of times by security admins every year',
    match: c => /^AGR_/.test(c.name) || ['TVDIR','TDDAT','PRGN_STAT'].includes(c.name),
  },
  {
    id: 'usermgmt',
    label: 'User Management Tables',
    color: '#f97316',
    icon: '👤',
    desc: 'USRxx / USTxx user master tables — produced automatically on every role transport. Modification count reflects security admin activity, not development.',
    match: c => /^USR|^UST|^SUSR/.test(c.name) || ['SPERS_OBJ','SPERS'].includes(c.name),
  },"""

NEW = """const CFG_GROUPS = [
  {
    id: 'security',
    label: 'Security & Authorization',
    color: '#ef4444',
    icon: '🔐',
    desc: 'AGR_* authorization tables + USRxx/USTxx user master tables — produced automatically on every role transport. Very few unique tables (10) but each transported 200–600x. Reflects security admin activity, not development.',
    match: c => /^AGR_|^USR|^UST|^SUSR/.test(c.name) || ['TVDIR','TDDAT','PRGN_STAT','SPERS_OBJ','SPERS'].includes(c.name),
  },"""

if OLD in html:
    html = html.replace(OLD, NEW, 1)
    with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Merged Auth Config + User Mgmt → Security & Authorization')
else:
    print('Pattern not found — searching...')
    idx = html.find("id: 'auth'")
    print(f"  'auth' group at char {idx}")
