"""
find_config_render.py - Find and print the config JS render function
"""
with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

import re

# Find all function definitions to understand the structure
funcs = list(re.finditer(r'function\s+\w+\s*\(', h))
print(f'Total functions: {len(funcs)}')
for m in funcs:
    print(f'  pos={m.start()}: {h[m.start():m.start()+60]}')

# Find where CFGDETAIL is iterated / used for rendering
idx = h.find('Object.entries(CFGDETAIL)')
if idx == -1:
    idx = h.find('CFGDETAIL[')
if idx == -1:
    idx = h.find('for.*CFGDETAIL')
print(f'\nCFGDETAIL iteration at: {idx}')
print(h[max(0,idx-200):idx+500])
