import os
base = r'C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution'
out_path = os.path.join(base, 'process-intelligence.html')
html_parts = ['_pi_part1_head.html', '_pi_part2_body.html']
js_parts   = ['_pi_part3_data.js', '_pi_part3b_realdata.js', '_pi_part4_map.js', '_pi_part5_ui.js']
with open(out_path, 'w', encoding='utf-8') as out:
    for p in html_parts:
        out.write(open(os.path.join(base, p), encoding='utf-8').read())
        out.write('\n')
    out.write('<script>\n')
    for p in js_parts:
        out.write(open(os.path.join(base, p), encoding='utf-8').read())
        out.write('\n')
    out.write('</script>\n</body>\n</html>\n')
size = os.path.getsize(out_path)
print(f'SUCCESS — process-intelligence.html created: {size:,} bytes ({size//1024} KB)')
