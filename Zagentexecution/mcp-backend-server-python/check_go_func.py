"""check_go_func.py - Check the go() function and people section"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

# Show go() function
idx = h.find('function go(id,btn){')
print('go() function:')
print(h[idx:idx+600])
print()

# Check people section
for kw in ['buildUserTabs', 'top_users', 'people', 'Contributors']:
    idx2 = h.find(kw)
    if idx2 != -1:
        print(f'{kw} at {idx2}: ...{h[idx2:idx2+80]}...')
    else:
        print(f'{kw}: NOT FOUND')
