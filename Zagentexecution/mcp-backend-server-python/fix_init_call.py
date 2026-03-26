import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

# The init block has:
# buildDomTabs();\nbuildPackages();\nbuildConfig();\nbuildUserTabs();\nbuildTeamTable();
# Replace buildConfig() with buildConfigByModule() in the init block
OLD = 'buildDomTabs();\nbuildPackages();\nbuildConfig();\nbuildUserTabs();\nbuildTeamTable();'
NEW = 'buildDomTabs();\nbuildPackages();\nbuildConfigByModule();\nbuildUserTabs();\nbuildTeamTable();'

if OLD in h:
    h = h.replace(OLD, NEW, 1)
    print('Fixed: replaced buildConfig() with buildConfigByModule() in init block')
else:
    # Try with different whitespace
    import re
    m = re.search(r'buildDomTabs\(\);\s*buildPackages\(\);\s*buildConfig\(\);', h)
    if m:
        old_text = m.group(0)
        new_text = old_text.replace('buildConfig()', 'buildConfigByModule()')
        h = h.replace(old_text, new_text, 1)
        print(f'Fixed via regex: replaced {old_text[:60]}')
    else:
        print('Pattern not found. Checking all buildConfig() calls...')
        for m2 in re.finditer(r'buildConfig\(\)', h):
            print(f'  {m2.start()}: {h[max(0,m2.start()-50):m2.start()+30]}')

import os
with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Done! {os.path.getsize("cts_dashboard.html")//1024}KB')
