"""
nuke_buttons.py - Complete button removal + topbar text fix
"""
import re, os

with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

print(f'File: {len(h)//1024}KB')

# Count button elements
btns = list(re.finditer(r'<button', h, re.IGNORECASE))
print(f'Total <button> tags: {len(btns)}')
for m in btns:
    print(f'  pos={m.start()}: snippet={ascii(h[m.start():m.start()+100])}')

# Remove all button elements (any button, not just sb-toggle)
# We'll keep filter chip buttons that exist in the year-filter section
# Only remove buttons with onclick=toggleSidebar or id=sb-toggle
BTN_RE = re.compile(r'<button\b[^>]*(?:id=["\']sb-toggle["\']|onclick=["\']toggleSidebar[^"\']*["\'])[^>]*>.*?</button>', re.DOTALL | re.IGNORECASE)
matches = BTN_RE.findall(h)
print(f'\nButtons matching removal pattern: {len(matches)}')
for m in matches:
    print(f'  -> {ascii(m[:80])}')

h = BTN_RE.sub('', h)
print('Removed')

# Also check if the JS injection from previous run left a duplicate script block
sb_scripts = [m.start() for m in re.finditer(r'Sidebar toggle button.*?injected via JS', h, re.DOTALL)]
print(f'\nJS injection script blocks: {len(sb_scripts)}')

# Remove duplicate JS injection blocks (keep only last one)
JS_BLOCK_RE = re.compile(r'\n<script>\n// Sidebar toggle button.*?</script>', re.DOTALL)
js_matches = JS_BLOCK_RE.findall(h)
print(f'JS script blocks for sidebar: {len(js_matches)}')
if len(js_matches) > 1:
    # Remove all, re-add one at end
    h = JS_BLOCK_RE.sub('', h)
    print('Removed all JS duplicates')
elif len(js_matches) == 0:
    print('No JS block found')

# Inject ONE clean JS block before </body>  
CLEAN_JS = """
<script>
// Sidebar toggle - injected via JS
(function() {
  if (document.getElementById('sb-toggle')) return; // guard against duplicates
  var btn = document.createElement('button');
  btn.id = 'sb-toggle';
  btn.title = 'Collapse sidebar';
  btn.innerHTML = '&#9664;&nbsp;Collapse';
  Object.assign(btn.style, {
    position:'fixed', top:'12px', right:'16px', zIndex:'9999',
    background:'rgba(79,142,247,.15)', border:'1px solid rgba(79,142,247,.3)',
    color:'#4f8ef7', borderRadius:'8px', padding:'5px 12px',
    cursor:'pointer', fontSize:'.74rem', fontFamily:'inherit',
    display:'flex', alignItems:'center', gap:'4px', whiteSpace:'nowrap'
  });
  btn.onclick = function() {
    var lbl = document.getElementById('sb-lbl');
    toggleSidebar();
    var sb = document.querySelector('.sidebar');
    btn.innerHTML = sb && sb.dataset.collapsed ? '&#9654;&nbsp;Menu' : '&#9664;&nbsp;Collapse';
  };
  document.body.appendChild(btn);
})();
</script>
</body>"""

h = h.replace('</body>', CLEAN_JS, 1)
print('Injected one clean sidebar button via JS')

# Fix topbar text concatenation "Unique-object viewUNIQUE OBJ"
# The issue is that the tb-stats label for UNIQUE OBJ is concatenating into the subtitle
# Find and add a separator
h = re.sub(r'(Unique-object view)(UNIQUE OBJ)', r'\1 · \2', h)
h = re.sub(r'(Unique-object view)\s*(UNIQUE)', r'\1  ', h)

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Done! {os.path.getsize("cts_dashboard.html")//1024}KB')
