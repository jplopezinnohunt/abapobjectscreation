"""
final_column_fix.py
1. Swap module/package prominence: real SAP DEVCLASS shown as primary, module badge as secondary
2. Fix topbar layout — remove concatenated label issue
3. Remove all duplicate sidebar buttons and insert ONE correctly
"""
import json, os, re

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# ── Fix 1: Update the MODULE column cell in the row template ─────────────────
# Find the td that builds the module column and replace it
# Pattern from our last patch: shows mod badge first, pkg as div sub-text
OLD_MOD_TD = (
    '<td>\n'
    '          <span style="font-size:.65rem;padding:1px 6px;border-radius:5px;'
    'background:${modCol}22;color:${modCol}">${mod}</span>\n'
    '          ${pkg ? `<div style="font-size:.6rem;color:var(--mu2);margin-top:2px;'
    'font-family:\'JetBrains Mono\',monospace">${pkgShort}</div>` : \'\'}\n'
    '        </td>'
)

NEW_MOD_TD = (
    '<td>\n'
    '          ${pkg ? `<code style="font-size:.7rem;color:#e2e8f0;font-weight:600">'
    '${pkg}</code>` : \'\'}\n'
    '          <div style="font-size:.6rem;padding:1px 5px;border-radius:4px;'
    'background:${modCol}20;color:${modCol};display:inline-block;margin-top:2px">'
    '${mod}</div>\n'
    '        </td>'
)

if OLD_MOD_TD in html:
    html = html.replace(OLD_MOD_TD, NEW_MOD_TD, 1)
    print('Fixed module/package column — DEVCLASS now primary')
else:
    # Try a looser find — search for the key phrase and replace the whole td
    pattern = re.compile(
        r'<td>\s*<span style="font-size:\.65rem[^"]*">\$\{mod\}</span>.*?</td>',
        re.DOTALL
    )
    match = pattern.search(html)
    if match:
        html = html[:match.start()] + NEW_MOD_TD + html[match.end():]
        print('Fixed module/package column via regex')
    else:
        # Manually target template literal content
        # Find the template literal that builds the row
        old_span = '`<span style="font-size:.65rem;padding:1px 6px;border-radius:5px;background:${modCol}22;color:${modCol}">${mod}</span>`'
        print(f'Trying alternative — old_span in html: {old_span[:60]}... : {old_span in html}')
        # Search for the closest match
        idx = html.find('background:${modCol}22;color:${modCol}">${mod}')
        if idx != -1:
            # Find surrounding td
            td_start = html.rfind('<td>', 0, idx)
            td_end   = html.find('</td>', idx) + 5
            old_td   = html[td_start:td_end]
            html = html[:td_start] + NEW_MOD_TD + html[td_end:]
            print('Fixed via index search')
        else:
            print('WARNING: Could not find module column — skipping')

# ── Fix 2: Update column header from "Module" to "Package / Module" ──────────
for old_th in ('Module (inferred)', 'Module'):
    if f'<th>{old_th}</th>' in html:
        html = html.replace(f'<th>{old_th}</th>',
                            '<th>Package / Module</th>', 1)
        print(f'Updated column header from {old_th}')
        break

# ── Fix 3: Fix topbar — remove all buttons and re-insert one correctly ────────
# Strip all existing toggle buttons
btn_re = re.compile(r'<button\s+id="sb-toggle"[^>]*>.*?</button>', re.DOTALL)
before = btn_re.findall(html)
print(f'Found {len(before)} button(s) to remove')
html = btn_re.sub('', html)

# The topbar ends with a </div> before the shell div
# Use the shell div as a reliable anchor, insert button right before it
SHELL_MARKER = '<div class="shell">'
shell_pos = html.find(SHELL_MARKER)
if shell_pos == -1:
    SHELL_MARKER = '<div class=\'shell\'>'
    shell_pos = html.find(SHELL_MARKER)

if shell_pos != -1:
    # Walk back to find the </div> that closes the topbar
    close_div_pos = html.rfind('</div>', 0, shell_pos)
    BTN_HTML = (
        '\n  <button id="sb-toggle" onclick="toggleSidebar()" title="Collapse sidebar"'
        ' style="position:absolute;right:16px;top:50%;transform:translateY(-50%);'
        'background:rgba(79,142,247,.12);border:1px solid rgba(79,142,247,.3);'
        'color:#4f8ef7;border-radius:8px;padding:5px 14px;cursor:pointer;'
        'font-size:.75rem;display:flex;align-items:center;gap:5px;white-space:nowrap;'
        'z-index:100">'
        '<span id="sb-ico">\u25c4</span>&nbsp;<span id="sb-lbl">Collapse</span>'
        '</button>'
    )
    # Also make topbar position:relative so absolute child works
    if 'class="topbar"' in html:
        html = html.replace('class="topbar"', 'class="topbar" style="position:relative"', 1)
    html = html[:close_div_pos] + BTN_HTML + html[close_div_pos:]
    print(f'Inserted button using absolute position inside topbar (before shell at {shell_pos})')
else:
    print('WARNING: Could not find shell div')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Done! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
