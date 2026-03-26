"""
clean_button_inject.py
- Removes ALL sidebar button HTML instances inserted by previous patches
- Injects button via JS (appended before </body>) so it never corrupts the topbar HTML
- Button uses position:fixed top-right to avoid ALL layout interference
"""
import os, re

with open('cts_dashboard.html', encoding='utf-8') as f:
    html = f.read()

original_size = len(html)

# ── Step 1: Remove every button instance (multiple patterns) ─────────────────
patterns = [
    re.compile(r'\s*<button\s+id=["\']sb-toggle["\'][^>]*>.*?</button>', re.DOTALL),
    re.compile(r'\s*<button\s+onclick=["\']toggleSidebar\(\)["\'][^>]*>.*?</button>', re.DOTALL),
]
for p in patterns:
    before = len(html)
    html = p.sub('', html)
    removed = before - len(html)
    if removed > 0:
        print(f'Removed {removed} chars of button HTML')

# ── Step 2: Clean up topbar style mutations ───────────────────────────────────
# Remove position:relative added by previous patch to topbar
html = html.replace(' style="position:relative"', '', )
# Remove any display:flex accidentally prepended to .topbar CSS
html = re.sub(r'(\.topbar\{)display:flex;align-items:center;', r'\1', html)
print('Cleaned topbar CSS mutations')

# ── Step 3: Inject button via JS before </body> ───────────────────────────────
BUTTON_JS = """
<script>
// Sidebar toggle button — injected via JS to avoid HTML layout issues
(function() {
  var btn = document.createElement('button');
  btn.id = 'sb-toggle';
  btn.title = 'Collapse / expand sidebar';
  btn.innerHTML = '<span id="sb-ico">&#9664;</span>&nbsp;<span id="sb-lbl">Collapse</span>';
  btn.style.cssText = [
    'position:fixed',
    'top:14px',
    'right:18px',
    'z-index:9999',
    'background:rgba(79,142,247,.12)',
    'border:1px solid rgba(79,142,247,.3)',
    'color:#4f8ef7',
    'border-radius:8px',
    'padding:5px 14px',
    'cursor:pointer',
    'font-size:.75rem',
    'display:flex',
    'align-items:center',
    'gap:5px',
    'white-space:nowrap',
    'font-family:inherit',
  ].join(';');
  btn.onclick = function() { toggleSidebar(); };
  document.body.appendChild(btn);
})();
</script>
</body>"""

html = html.replace('</body>', BUTTON_JS, 1)
print('Injected sidebar button via JS (position:fixed top-right)')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f'Done! Size: {original_size//1024}KB -> {os.path.getsize("cts_dashboard.html")//1024}KB')
