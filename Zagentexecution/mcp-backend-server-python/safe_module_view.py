"""
safe_module_view.py
Replaces the broken buildConfigByModule() with a simpler, safe version:
- No nested template literals with complex expressions
- Precomputes colors as plain objects
- Uses string concatenation for inner HTML parts
- Returns control to buildUserTabs / People section
"""
import re, os, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('cts_dashboard.html', encoding='utf-8') as f:
    h = f.read()

# 1. Remove the previously injected bad script block
old_start = h.find('\n<script>\n// ═══════════════════════════════════════════════════════\n// CONFIG BY MODULE')
old_end   = h.find('</script>', old_start) + len('</script>')
if old_start != -1 and old_end > old_start:
    h = h[:old_start] + h[old_end:]
    print(f'Removed old buildConfigByModule script ({old_end-old_start} chars)')
else:
    print('Old script block not found (may already be clean)')

# 2. Inject a clean, simple version
SAFE_JS = r"""
<script>
// ─── Config by Module → Package ─────────────────────────────────────────────
var MOD_COLORS = {
  'HCM-PY (Payroll)':       '#a78bfa',
  'HCM/Config View':        '#c084fc',
  'HCM-PA (Personnel Admin)':'#e879f9',
  'FI/CO Config View':      '#38bdf8',
  'FI (Finance)':           '#60a5fa',
  'FI (Accounts)':          '#93c5fd',
  'CO (Controlling)':       '#34d399',
  'CO-PA (Profitability)':  '#6ee7b7',
  'PSM/FM':                 '#f59e0b',
  'BC-Sec / User Mgmt':     '#f87171',
  'BC-Sec / Auth':          '#fca5a5',
  'BC-IMG (Cust Tree)':     '#94a3b8',
  'BC-Payroll Post':        '#c4b5fd',
  'BC-NR (Number Ranges)':  '#a5b4fc',
  'MM (Procurement)':       '#fb923c',
  'MDG':                    '#facc15',
  'General IMG':            '#64748b'
};

function buildConfigByModule() {
  var ct = document.getElementById('cfg-ct');
  if (!ct) return;
  ct.innerHTML = '';

  // Group by module
  var byMod = {};
  Object.keys(CFGDETAIL).forEach(function(name) {
    var v = CFGDETAIL[name];
    var mod = v.module || 'General IMG';
    if (!byMod[mod]) byMod[mod] = [];
    byMod[mod].push(name);
  });

  // Sort: specific modules first, General last
  var mods = Object.keys(byMod).sort(function(a, b) {
    if (a === 'General IMG') return 1;
    if (b === 'General IMG') return -1;
    return byMod[b].length - byMod[a].length;
  });

  mods.forEach(function(mod, mi) {
    var names    = byMod[mod];
    var color    = MOD_COLORS[mod] || '#64748b';
    var totalM   = names.reduce(function(s, n) { return s + (CFGDETAIL[n].total_mods || 0); }, 0);
    var modId    = 'MOD' + mi;
    var isFirst  = mi === 0;

    // Build package counts
    var pkgCnt = {};
    names.forEach(function(n) {
      var p = CFGDETAIL[n].package || '(no pkg)';
      pkgCnt[p] = (pkgCnt[p] || 0) + 1;
    });
    var pkgs = Object.keys(pkgCnt).sort(function(a, b) { return pkgCnt[b] - pkgCnt[a]; });

    // Build pill buttons HTML
    var pillHtml = '<button class="pkg-pill mpill active" onclick="filterModPkg(\'' + modId + '\',\'\',this)" '
      + 'style="background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);color:#f1f5f9;'
      + 'border-radius:20px;padding:3px 12px;cursor:pointer;font-size:.7rem;font-family:inherit">'
      + 'All (' + names.length + ')</button>';

    pkgs.slice(0, 40).forEach(function(pkg) {
      var desc = '';
      // Get desc from first object with this package
      for (var ni = 0; ni < names.length; ni++) {
        if ((CFGDETAIL[names[ni]].package || '(no pkg)') === pkg) {
          desc = CFGDETAIL[names[ni]].pkg_desc || '';
          break;
        }
      }
      pillHtml += '<button class="pkg-pill mpill" onclick="filterModPkg(\'' + modId + '\',\'' + pkg.replace(/'/g,"\\'") + '\',this)" '
        + 'title="' + desc.replace(/"/g,'&quot;') + '" '
        + 'style="background:rgba(0,0,0,.2);border:1px solid ' + color + '55;color:' + color + ';'
        + 'border-radius:20px;padding:3px 12px;cursor:pointer;font-size:.7rem;font-family:inherit">'
        + pkg + ' <span style="opacity:.6">' + pkgCnt[pkg] + '</span></button>';
    });

    var card = document.createElement('div');
    card.style.cssText = 'border-radius:12px;overflow:hidden;background:rgba(15,23,42,.6);border:1px solid rgba(255,255,255,.07);margin-bottom:12px';
    card.innerHTML =
      '<div onclick="toggleMod(\'' + modId + '\')" '
      + 'style="padding:14px 20px;cursor:pointer;display:flex;align-items:center;gap:14px;background:rgba(0,0,0,.2)">'
      + '<div style="width:3px;height:36px;background:' + color + ';border-radius:2px;flex-shrink:0"></div>'
      + '<div style="flex:1">'
      + '<div style="font-size:.9rem;font-weight:700;color:#f1f5f9">' + mod + '</div>'
      + '<div style="font-size:.68rem;color:#64748b">' + names.length + ' objects · ' + pkgs.length + ' packages</div>'
      + '</div>'
      + '<div style="font-size:1.3rem;font-weight:800;color:' + color + ';min-width:48px;text-align:right">' + names.length.toLocaleString() + '</div>'
      + '<div style="font-size:.95rem;font-weight:600;color:#94a3b8;min-width:56px;text-align:right">' + totalM.toLocaleString() + '</div>'
      + '<div id="' + modId + '-arrow" style="color:#64748b;margin-left:8px">' + (isFirst ? '▼' : '▶') + '</div>'
      + '</div>'
      + '<div id="' + modId + '-body" style="display:' + (isFirst ? 'block' : 'none') + '">'
      + '<div style="padding:10px 18px 8px;display:flex;flex-wrap:wrap;gap:5px;border-bottom:1px solid rgba(255,255,255,.05)">'
      + pillHtml + '</div>'
      + '<div id="' + modId + '-tbl" style="max-height:550px;overflow-y:auto"></div>'
      + '</div>';

    ct.appendChild(card);
    if (isFirst) renderModRows(modId, names, '');
  });
}

function toggleMod(modId) {
  var body  = document.getElementById(modId + '-body');
  var arrow = document.getElementById(modId + '-arrow');
  if (!body) return;
  var open = body.style.display !== 'none';
  body.style.display = open ? 'none' : 'block';
  if (arrow) arrow.textContent = open ? '▶' : '▼';
  if (!open) {
    var tbl = document.getElementById(modId + '-tbl');
    if (tbl && !tbl.dataset.loaded) {
      // Find names for this modId by scanning the pills
      var pills = document.getElementById(modId + '-body').querySelectorAll('.mpill');
      // All names for the module come from CFGDETAIL filtered by module
      // Re-derive from the card's full list (stored in data attr of tbl)
      renderModRows(modId, JSON.parse(tbl.dataset.names || '[]'), '');
    }
  }
}

function filterModPkg(modId, pkg, btn) {
  var tbl = document.getElementById(modId + '-tbl');
  if (!tbl) return;
  var allNames = JSON.parse(tbl.dataset.names || '[]');
  document.getElementById(modId + '-body').querySelectorAll('.mpill').forEach(function(b) {
    b.classList.remove('active');
    b.style.fontWeight = '';
  });
  if (btn) { btn.classList.add('active'); btn.style.fontWeight = '700'; }
  renderModRows(modId, allNames, pkg);
}

var CONTENT_SET = {TABU:1,TDAT:1,CDAT:1,DATED:1};

function renderModRows(modId, allNames, pkgFilter) {
  var tbl = document.getElementById(modId + '-tbl');
  if (!tbl) return;
  tbl.dataset.names = JSON.stringify(allNames);
  tbl.dataset.loaded = '1';

  var names = pkgFilter
    ? allNames.filter(function(n) { return (CFGDETAIL[n].package || '(no pkg)') === pkgFilter; })
    : allNames;

  var YEARS = ['2017','2018','2019','2020','2021','2022','2023','2024','2025','2026'];
  var rows = '';
  names.forEach(function(name) {
    var c = CFGDETAIL[name] || {};
    var isContent = CONTENT_SET[c.obj_type] ? 1 : 0;
    var desc = c.short_desc || c.description || '';
    var pkg  = c.package || '';
    var pdesc = c.pkg_desc || '';
    var ya   = c.years_active || [];
    var spark = YEARS.map(function(y) {
      var has = ya.indexOf(y) >= 0;
      return '<span style="display:inline-block;width:4px;height:' + (has ? 12 : 3) + 'px;background:'
        + (has ? '#4f8ef7' : 'rgba(255,255,255,.1)') + ';border-radius:1px;vertical-align:bottom;margin:0 1px"></span>';
    }).join('');

    rows += '<tr style="border-bottom:1px solid rgba(255,255,255,.04);opacity:' + (isContent ? '.55' : '1') + '">'
      + '<td style="padding:7px 14px;vertical-align:top">'
      + '<div style="font-weight:700;color:#f1f5f9;font-family:monospace;font-size:.78rem">' + name + '</div>'
      + (desc ? '<div style="font-size:.65rem;color:#64748b;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">' + desc + '</div>' : '')
      + (isContent ? '<span style="font-size:.58rem;background:rgba(245,158,11,.15);color:#f59e0b;padding:1px 4px;border-radius:3px">content</span>' : '')
      + '</td>'
      + '<td style="padding:7px 10px;white-space:nowrap;font-size:.68rem;color:#94a3b8;vertical-align:top">' + (c.type_label || c.obj_type || '') + '</td>'
      + '<td style="padding:7px 10px;vertical-align:top">'
      + (pkg ? '<div style="font-weight:700;color:#f1f5f9;font-family:monospace;font-size:.73rem">' + pkg + '</div>'
             + (pdesc ? '<div style="font-size:.62rem;color:#64748b">' + pdesc + '</div>' : '') : '<span style="color:#334155">—</span>')
      + '</td>'
      + '<td style="padding:7px 10px;text-align:right;font-weight:700;color:#4f8ef7;font-size:.78rem">' + (c.total_mods || 0) + '</td>'
      + '<td style="padding:7px 14px">' + spark + '</td>'
      + '</tr>';
  });

  tbl.innerHTML = '<div style="padding:5px 14px;font-size:.65rem;color:#64748b">' + names.length + ' objects</div>'
    + '<table style="width:100%;border-collapse:collapse">'
    + '<thead><tr style="background:rgba(0,0,0,.3)">'
    + '<th style="padding:5px 14px;text-align:left;font-size:.62rem;color:#475569">OBJECT</th>'
    + '<th style="padding:5px 10px;text-align:left;font-size:.62rem;color:#475569">TYPE</th>'
    + '<th style="padding:5px 10px;text-align:left;font-size:.62rem;color:#475569">PACKAGE</th>'
    + '<th style="padding:5px 10px;text-align:right;font-size:.62rem;color:#475569">MODS</th>'
    + '<th style="padding:5px 14px;font-size:.62rem;color:#475569">TIMELINE</th>'
    + '</tr></thead><tbody>' + rows + '</tbody></table>';
}
</script>
</body>
"""

# Remove old </body> and append safe JS
h = h.replace('</body>', SAFE_JS, 1)
print('Injected safe buildConfigByModule()')

with open('cts_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(h)
print(f'Done! {os.path.getsize("cts_dashboard.html")//1024}KB')
