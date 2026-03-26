"""Fix triple-brace f-string issue in gen_dashboard.py."""
with open('gen_dashboard.py', encoding='utf-8') as f:
    src = f.read()

# The bad pattern: Python f-string sees {peak[1]...} as an expression
# We fix it by using a JS variable assignment instead of inline .toLocaleString()
# Replace the problematic peak year line with a simpler version
OLD = '${{{peak[1].toLocaleString()}}}'
NEW = '${{peak[1].toLocaleString()}}'

if OLD in src:
    src2 = src.replace(OLD, NEW, 1)
    with open('gen_dashboard.py', 'w', encoding='utf-8') as f:
        f.write(src2)
    print('Fixed triple-brace issue.')
else:
    print('Pattern not found - checking context...')
    idx = src.find('peak[1].toLocaleString')
    if idx >= 0:
        print(repr(src[max(0,idx-15):idx+35]))
    else:
        print('Not found at all')
