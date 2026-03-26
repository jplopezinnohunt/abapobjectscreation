import sys, re
sys.stdout.reconfigure(encoding='utf-8')

with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

# Find all calls to buildTeamTable (not the definition)
for m in re.finditer(r'buildTeamTable\(\)', h):
    ctx = h[max(0,m.start()-120):m.start()+30]
    print(f'pos={m.start()}: ...{ctx.strip()[-150:]}...')

print()
# Find the page init block 
# Look for window.onload or script at bottom
for kw in ['window.onload', 'window.addEventListener(', 'buildDomTabs()', 'buildPackages()', 'buildUserTabs()']:
    idx = h.find(kw)
    if idx != -1:
        print(f'{kw} at {idx}: {h[idx:idx+80]}')
