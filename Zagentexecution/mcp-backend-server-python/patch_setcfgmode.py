"""patch_setcfgmode.py - Direct targeted patch of setCfgMode"""
import os

with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

# Find exact current setCfgMode text from the diagnostic output
OLD = (
    "function setCfgMode(mode, el) {\n"
    "  window._cfgMode = mode;\n"
    "  document.querySelectorAll('.cfg-mode-btn').forEach(b => b.classList.remove('active'));\n"
    "  if (el) el.classList.add('active');\n"
    "  applyCfgFilter();\n"
    "}"
)

NEW = (
    "function setCfgMode(mode, el) {\n"
    "  window._cfgMode = mode;\n"
    "  document.querySelectorAll('.cfg-mode-btn').forEach(b => b.classList.remove('active'));\n"
    "  if (el) el.classList.add('active');\n"
    "  cfgGroupData = null;\n"                         # reset cache
    "  var ct = document.getElementById('cfg-ct');\n"  # re-render
    "  if (ct) { ct.innerHTML = ''; buildConfig(); }\n"
    "}"
)

if OLD in h:
    h = h.replace(OLD, NEW, 1)
    print('setCfgMode patched — will now reset groups and re-render')
else:
    print('Exact pattern not found. Searching for setCfgMode...')
    idx = h.find("function setCfgMode(mode, el)")
    if idx != -1:
        end = h.find("\n}", idx) + 2
        current = h[idx:end]
        print(f'Current code:\n{current}')
        # Replace it regardless
        h = h[:idx] + NEW + h[end:]
        print('Replaced via index')
    else:
        print('ERROR: setCfgMode not found at all!')

# Also make sure _cfgMode starts as 'objects'
if "window._cfgMode = 'all'" in h:
    h = h.replace("window._cfgMode = 'all'", "window._cfgMode = 'objects'")
    print("Changed default _cfgMode to 'objects'")

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Done! {os.path.getsize("cts_dashboard.html")//1024}KB')
