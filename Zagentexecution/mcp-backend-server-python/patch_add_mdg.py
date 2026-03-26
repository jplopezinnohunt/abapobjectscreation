"""Add MDG Config group to CFG_GROUPS in the dashboard."""
with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

OLD = """  {
    id: 'general',
    label: 'General Customizing (IMG / Other)',"""

NEW = """  {
    id: 'mdg',
    label: 'MDG Config (Master Data Governance)',
    color: '#38bdf8',
    icon: '🗄️',
    desc: 'USMD* tables for SAP Master Data Governance (MDG) personalization — default data models, UI models per data model. Despite the USR-like prefix, these are MDG framework config, not user security.',
    match: c => /^USMD/.test(c.name),
  },
  {
    id: 'general',
    label: 'General Customizing (IMG / Other)',"""

if OLD in html:
    html = html.replace(OLD, NEW, 1)
    with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    import os
    print('Done! Added MDG Config group. Dashboard: ' + str(os.path.getsize('cts_dashboard.html')//1024) + 'KB')
else:
    print('Pattern not found')
