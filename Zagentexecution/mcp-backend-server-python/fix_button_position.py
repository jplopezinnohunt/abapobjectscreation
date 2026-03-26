"""
fix_button_position.py
Find and remove all misplaced sidebar toggle buttons, 
then insert one correctly inside the topbar as a right-aligned flex item.
"""
import os, re

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# ── Step 1: Remove ALL existing toggle button instances ───────────────────────
# The button may appear multiple times due to repeated patches
BTN_PATTERN = re.compile(
    r'<button\s+onclick="toggleSidebar\(\)".*?</button>\s*',
    re.DOTALL
)
count_before = len(BTN_PATTERN.findall(html))
html = BTN_PATTERN.sub('', html)
print(f'Removed {count_before} existing button instance(s)')

# ── Step 2: Insert button correctly inside the topbar ────────────────────────
# Find the topbar closing tag
# Topbar structure: <div class="topbar">...[logo]...[stats]...</div>
# We want the button as the last child of topbar, right-aligned

TOPBAR_END = '</div>\n<div class="shell">'
if TOPBAR_END not in html:
    TOPBAR_END = '</div><div class="shell">'

CLEAN_BTN = (
    '  <button id="sb-toggle" onclick="toggleSidebar()" '
    'title="Collapse / expand sidebar" '
    'style="margin-left:auto;background:rgba(79,142,247,.1);'
    'border:1px solid rgba(79,142,247,.25);color:#4f8ef7;'
    'border-radius:8px;padding:6px 14px;cursor:pointer;'
    'font-size:.75rem;align-self:center;flex-shrink:0;'
    'display:flex;align-items:center;gap:5px;white-space:nowrap">'
    '<span id="sb-ico">\u25c4</span>&nbsp;'
    '<span id="sb-lbl">Collapse</span>'
    '</button>\n'
)

html = html.replace(TOPBAR_END, CLEAN_BTN + TOPBAR_END, 1)
print('Inserted button correctly before topbar closing tag')

# ── Step 3: Make sure topbar uses flex so button aligns right ────────────────
# Add display:flex to topbar if not present
if '.topbar{' in html and 'display:flex' not in html[html.find('.topbar{'):html.find('.topbar{')+200]:
    html = html.replace('.topbar{', '.topbar{display:flex;align-items:center;', 1)
    print('Added display:flex to .topbar CSS')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Done! Dashboard: {os.path.getsize("cts_dashboard.html")//1024}KB')
