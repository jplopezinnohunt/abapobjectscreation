with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()
s = h.find('<div class="topbar">')
print(h[s:s+900])
