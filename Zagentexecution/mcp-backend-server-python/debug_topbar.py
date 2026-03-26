"""
debug_topbar.py - show the topbar and surrounding HTML for inspection
"""
import re

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

# Show 800 chars around the topbar
tb = html.find('class="topbar"')
print("=== TOPBAR AREA ===")
print(repr(html[tb-50:tb+800]))

# Show all button occurrences
buttons = [m.start() for m in re.finditer(r'onclick="toggleSidebar', html)]
print(f"\n=== BUTTON POSITIONS ({len(buttons)} total) ===")
for pos in buttons:
    print(f"  pos={pos}: ...{repr(html[pos-100:pos+80])}...")

# Show what's just before <div class="shell">
shell = html.find('<div class="shell">')
print(f"\n=== BEFORE SHELL (pos={shell}) ===")
print(repr(html[shell-300:shell+50]))
