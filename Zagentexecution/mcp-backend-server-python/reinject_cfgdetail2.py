"""Re-inject improved CFGDETAIL into cts_dashboard.html using brace-counting."""
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

with open('cts_config_detail.json', encoding='utf-8') as f:
    cfg = json.load(f)

cfg_json = json.dumps(cfg, ensure_ascii=False, separators=(',', ':'))

marker = 'const CFGDETAIL={'
start = html.find(marker)
if start < 0:
    print('ERROR: const CFGDETAIL not found')
    raise SystemExit(1)

# Brace-count to find end of the JSON object
count = 0
i = start + len('const CFGDETAIL=')
end = -1
while i < len(html):
    c = html[i]
    if c == '{':
        count += 1
    elif c == '}':
        count -= 1
        if count == 0:
            end = i + 1
            break
    i += 1

if end < 0:
    print('ERROR: could not find end of CFGDETAIL object')
    raise SystemExit(1)

print(f'Found CFGDETAIL: chars {start}–{end}  ({end-start} chars)')
print(f'New CFGDETAIL blob: {len(cfg_json)} chars')

new_html = html[:start] + 'const CFGDETAIL=' + cfg_json + html[end:]

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(new_html)

print('SUCCESS: cts_dashboard.html updated')
print(f'Verification - still present: {"const CFGDETAIL=" in new_html}')
print(f'New file size: {len(new_html):,} chars')
