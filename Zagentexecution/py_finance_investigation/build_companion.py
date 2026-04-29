"""Build PY-Finance Wage Type Configuration Companion v1 HTML."""
import json, os, sqlite3
from collections import Counter, defaultdict
os.chdir('c:/Users/jp_lopez/projects/abapobjectscreation')

# Load prior data
data = json.load(open('Zagentexecution/py_finance_investigation/transport_manifest_4yr.json'))
desc = json.load(open('Zagentexecution/py_finance_investigation/tr_descriptions.json'))
analysis = json.load(open('Zagentexecution/py_finance_investigation/analysis_4yr.json'))

# Re-classify with correct pattern taxonomy
import re
def classify(txt, user):
    if not txt: return 'UNDOCUMENTED'
    if re.match(r'^\s*\d{5,7}\s*[/\-]', txt) and user in ('FP_SPEZZANO','M_SPRONK'):
        return 'TICKET_NEW_COUNTRY_SETUP'
    if re.search(r'\bLCR[_ ]|local cost|payroll activit', txt, re.IGNORECASE): return 'LCR_MONTHLY'
    if re.search(r'Salary Scale|SC Salary|SC for|Scales SC|Scales for', txt): return 'SALARY_SCALE_FO'
    if re.search(r'\bCSI\b', txt): return 'CSI'
    if re.search(r'[Pp]ensionable|Pensi(o|ó)n', txt): return 'PENSIONABLE'
    if re.search(r'[Ss]ocial [Ss]ecurity|INSS', txt): return 'SOCIAL_SECURITY'
    if re.search(r'Currency|Payment Method', txt): return 'CURRENCY_PAYMT'
    if re.search(r'UBO|SCs Integration', txt): return 'UBO_INTEGRATION'
    if re.search(r'UNDP', txt): return 'UNDP_SPECIFIC'
    if re.search(r'\bWF\b|[Ww]orkflow', txt): return 'WF_WORKFLOW'
    return 'OTHER_CONFIG'

# Build object map
obj_map = defaultdict(list)
for o in data['objects']:
    obj_map[o['trkorr']].append({'object':o['object'],'name':o['obj_name']})

CORE_5 = {'T512T','T512W','T52DZ','T52EL','T52EZ'}
wt_set = CORE_5 | {'T500L','T500P','T510','T510A','T510D','T510F','T510G','T510I','T510J','T510M','T510N','T510S','T510U','T510W','T511','T511K','T511P','T512','T512C','T512E','T512N','T512Z','T514N','T514V','T539A','T539J','T52BK','T52BT','T52C0','T52C1','T52C5','T52CC','T52CD','T52CE','T52CT','T52D1','T52D2','T52D3','T52D4','T52D5','T52D6','T52D7','T52D8','T52D9','T52EG','T52EH','T52EK','T52EM','T52EN','T52EP','T52FA','T52FB','T527O','T513','T520S','T51P1'}

COUNTRIES = {
    'Mozambic':'Mozambique','Mozambique':'Mozambique','Mongolia':'Mongolia',
    'LKR':'Sri Lanka','STN':'Sao Tome','ZWG':'Zimbabwe','ZIG':'Zimbabwe (old)',
    'Algeria':'Algeria','India':'India','Kyrgyzstan':'Kyrgyzstan','Mauritania':'Mauritania',
    'Nigeria':'Nigeria','Brasilia':'Brasilia','Guinea-Bissau':'Guinea-Bissau','Uzbekistan':'Uzbekistan','UZB':'Uzbekistan',
    'MRU':'Mauritania','SBD':'Solomon Islands','ME':'Middle East','DZ':'Algeria','GH':'Ghana','GN':'Guinea','NG':'Nigeria','NP':'Nepal','MG':'Madagascar','PH':'Philippines','BD':'Bangladesh','Abuja':'Nigeria (Abuja)','Nairobi':'Kenya (Nairobi)','UNDP':'UNDP (global)','Paris':'France (HQ)','IBE':'IBE (Geneva)','ICBA':'ICBA','Jakarta':'Indonesia (Jakarta)','HAV':'Cuba (Havana)',
}

enriched = []
pattern_counter = Counter()
editor_pattern = defaultdict(Counter)
country_counter = Counter()
year_pattern = defaultdict(Counter)
ticket_setups = []

for tr in data['transports']:
    info = desc.get(tr['trkorr'],{}) or {}
    txt = info.get('text','').strip()
    wt_objs = []
    for o in obj_map.get(tr['trkorr'],[]):
        name = o['name']
        if name in wt_set or name.startswith(('V_T51','V_T52')) or o['object'] in ('PSCC','PCYC','PDWS'):
            wt_objs.append({'type':o['object'],'name':name})
    pattern = classify(txt, tr['as4user'])
    pattern_counter[pattern] += 1
    editor_pattern[tr['as4user']][pattern] += 1
    year_pattern[tr['year']][pattern] += 1
    countries_hit = []
    if txt:
        for k,v in COUNTRIES.items():
            if re.search(r'\b'+re.escape(k)+r'\b', txt):
                countries_hit.append(v)
                country_counter[v] += 1
    m = re.match(r'^\s*(\d{5,7})\s*[/\-]', txt)
    ticket_no = m.group(1) if m else None
    core5 = sum(1 for o in wt_objs if o['name'] in CORE_5)
    row = {
        'trkorr': tr['trkorr'], 'year': tr['year'], 'as4date': tr['as4date'],
        'as4user': tr['as4user'], 'obj_count': tr['obj_count'],
        'deploy_level': tr.get('deploy_level',''), 'trstatus': tr.get('trstatus',''),
        'text': txt, 'pattern': pattern, 'countries': list(set(countries_hit)),
        'wt_objects': wt_objs, 'wt_count': len(wt_objs), 'core5_count': core5, 'ticket_no': ticket_no,
    }
    enriched.append(row)
    if pattern == 'TICKET_NEW_COUNTRY_SETUP':
        ticket_setups.append(row)

enriched.sort(key=lambda x: x['as4date'], reverse=True)

# Editor tiers
TIERS = {
    'A_SEFIANI':    {'tier':1,'role':'PY-Finance lead (policy, salary scales, CSI, pensionable)'},
    'L_CABALLE':    {'tier':1,'role':'PY-Finance operations (LCR monthly cadence)'},
    'N_MENARD':     {'tier':1,'role':'PY-Finance schemas/PCRs (custom ZPPF/ZPP0/ZPP1 + 98100*)'},
    'FP_SPEZZANO':  {'tier':1,'role':'Finance core crossover (new-country payment setup via service desk ticket)'},
    'M_SPRONK':     {'tier':2,'role':'Treasury crossover (new-country ticket-driven payment setup)'},
    'S_IGUENINNI':  {'tier':3,'role':'HR dev bundles (WT schemas dragged along in Fiori app releases)'},
    'FP_SPEZZANO_BK':{'tier':4,'role':'Treasury backup'},
    'GD_SCHELLINC': {'tier':4,'role':'One-off schemas 98100029/34'},
    'R_CHAFIA':     {'tier':4,'role':'Single transport'},
    'R_RIOS':       {'tier':4,'role':'Single transport'},
    'F_GUILLOU':    {'tier':4,'role':'Single transport'},
}

rows_json = json.dumps(enriched, ensure_ascii=False)

# Build HTML
html_parts = []
html_parts.append("""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>PY-Finance Wage Type Configuration Companion v1 &mdash; UNESCO SAP</title>
<style>
:root{--bg:#0d1117;--card:#161b22;--border:#30363d;--text:#c9d1d9;--accent:#58a6ff;--green:#3fb950;--yellow:#d29922;--red:#f85149;--purple:#bc8cff;--orange:#f0883e;--cyan:#39d2c0;}
*{margin:0;padding:0;box-sizing:border-box;}
body{font-family:-apple-system,'Segoe UI',sans-serif;background:var(--bg);color:var(--text);}
.topnav{position:sticky;top:0;z-index:99;background:#0a0e17;border-bottom:1px solid #30363d;padding:6px 20px;display:flex;gap:16px;flex-wrap:wrap;font-size:.8em;}
.topnav a{text-decoration:none;color:#58a6ff;}
.header{background:linear-gradient(135deg,#1a2332,#0d2137);padding:22px 32px;border-bottom:1px solid var(--border);}
.header h1{font-size:1.6em;color:#fff;margin-bottom:4px;}
.header .sub{color:#8b949e;font-size:.9em;}
.tabs{display:flex;gap:0;background:var(--card);border-bottom:1px solid var(--border);padding:0 16px;overflow-x:auto;flex-wrap:nowrap;}
.tab{padding:12px 18px;cursor:pointer;color:#8b949e;border-bottom:2px solid transparent;white-space:nowrap;font-size:.85em;transition:all .2s;}
.tab:hover{color:var(--text);background:rgba(88,166,255,.05);}
.tab.active{color:var(--accent);border-bottom-color:var(--accent);}
.content{padding:22px 30px;max-width:1500px;margin:0 auto;}
.panel{display:none;}.panel.active{display:block;}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:18px;margin-bottom:16px;}
.card h3{color:var(--accent);margin-bottom:10px;font-size:1.08em;}
.card h4{color:var(--purple);margin:14px 0 8px;font-size:.95em;}
.card p{margin:8px 0;font-size:.9em;line-height:1.55;}
.card ul,.card ol{margin:8px 0 8px 22px;font-size:.9em;}.card li{margin:4px 0;}
table{width:100%;border-collapse:collapse;font-size:.82em;}
th{background:rgba(88,166,255,.1);color:var(--accent);text-align:left;padding:7px 10px;border:1px solid var(--border);white-space:nowrap;}
td{padding:6px 10px;border:1px solid var(--border);vertical-align:top;}
tr:hover{background:rgba(88,166,255,.05);}
.kpi-row{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin-bottom:18px;}
.kpi{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px;text-align:center;}
.kpi .val{font-size:1.7em;font-weight:700;color:#fff;}.kpi .label{font-size:.78em;color:#8b949e;margin-top:4px;}
.kpi.accent{border-color:var(--accent);}.kpi.green{border-color:var(--green);}.kpi.yellow{border-color:var(--yellow);}.kpi.red{border-color:var(--red);}.kpi.purple{border-color:var(--purple);}.kpi.cyan{border-color:var(--cyan);}
.badge{display:inline-block;padding:2px 7px;border-radius:4px;font-size:.72em;font-weight:600;white-space:nowrap;}
.badge-green{background:rgba(63,185,80,.2);color:var(--green);}.badge-yellow{background:rgba(210,153,34,.2);color:var(--yellow);}.badge-red{background:rgba(248,81,73,.2);color:var(--red);}.badge-blue{background:rgba(88,166,255,.2);color:var(--accent);}.badge-purple{background:rgba(188,140,255,.2);color:var(--purple);}.badge-cyan{background:rgba(57,210,192,.2);color:var(--cyan);}.badge-orange{background:rgba(240,136,62,.2);color:var(--orange);}
.flow{background:#0d1117;border:1px solid var(--border);border-radius:8px;padding:16px;margin:10px 0;font-family:'Courier New',monospace;font-size:.82em;line-height:1.55;white-space:pre;overflow-x:auto;color:var(--text);}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px;}
.grid-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;}
@media(max-width:900px){.grid-2,.grid-3{grid-template-columns:1fr;}}
.note{background:rgba(210,153,34,.1);border:1px solid rgba(210,153,34,.3);border-radius:6px;padding:10px;margin:10px 0;font-size:.86em;}.note::before{content:"NOTE: ";font-weight:bold;color:var(--yellow);}
.danger{background:rgba(248,81,73,.08);border:1px solid rgba(248,81,73,.3);border-radius:6px;padding:10px;margin:10px 0;font-size:.86em;}.danger::before{content:"RISK: ";font-weight:bold;color:var(--red);}
.good{background:rgba(63,185,80,.08);border:1px solid rgba(63,185,80,.3);border-radius:6px;padding:10px;margin:10px 0;font-size:.86em;}.good::before{content:"GOOD: ";font-weight:bold;color:var(--green);}
.bar{background:#0d1117;border:1px solid var(--border);border-radius:4px;height:14px;overflow:hidden;position:relative;}
.bar-fill{background:linear-gradient(90deg,var(--accent),var(--purple));height:100%;border-radius:4px;}
input,select{background:var(--card);border:1px solid var(--border);color:var(--text);padding:6px 10px;border-radius:4px;font-size:.85em;}
.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:10px;align-items:center;}
.mono{font-family:'Courier New',monospace;font-size:.82em;color:var(--cyan);}
.subtable-wrap{max-height:620px;overflow-y:auto;border:1px solid var(--border);border-radius:8px;}
.h2r-step{display:grid;grid-template-columns:50px 1fr;gap:12px;margin:10px 0;align-items:start;}
.h2r-step .num{background:var(--accent);color:#000;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9em;}
.tier-card{border-left:4px solid;padding-left:14px;margin:10px 0;}
.tier-1{border-color:var(--accent);}.tier-2{border-color:var(--purple);}.tier-3{border-color:var(--yellow);}.tier-4{border-color:#666;}
.pattern-card{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:14px;margin-bottom:12px;}
.pattern-card h4{color:var(--cyan);margin:0 0 8px;font-size:1em;}
</style></head><body>
<div class="topnav">
<a href="unesco_sap_landing.html">&#8592; Landing</a><span style="color:#30363d">|</span>
<a href="treasury_operations_companion_v1.html">Treasury</a>
<a href="payment_bcm_companion.html">Payments</a>
<a href="bank_statement_ebs_companion.html">Bank Statements</a>
<a href="cts_dashboard.html">Transports</a>
<a href="#" style="color:#3fb950;font-weight:600">PY-Finance (this page)</a>
</div>
<div class="header">
<h1>PY-Finance &mdash; Wage Type Configuration Companion <span style="color:#8b949e;font-size:.6em;">v1 &middot; 2026-04-21</span></h1>
<div class="sub">Reverse-engineered from 418 transports (2022-04 &rarr; 2026-04). Finance-owned wage type config at UNESCO: pay scales, salary scales, LCR activities, pensionable remuneration, country-level payroll config, custom schemas &amp; PCRs.</div>
</div>
<div class="tabs">
<div class="tab active" data-p="overview">Overview</div>
<div class="tab" data-p="who">Who does what</div>
<div class="tab" data-p="stack">Wage Type Stack</div>
<div class="tab" data-p="patterns">Config Patterns</div>
<div class="tab" data-p="francesco">Francesco / Marlies / Said</div>
<div class="tab" data-p="timeline">Timeline</div>
<div class="tab" data-p="risk">Risk &amp; Gaps</div>
<div class="tab" data-p="browser">Transport Browser</div>
<div class="tab" data-p="next">Next Actions</div>
</div>
<div class="content">
""")

# ==== OVERVIEW ====
html_parts.append(f"""
<div class="panel active" id="overview">
  <div class="kpi-row">
    <div class="kpi accent"><div class="val">418</div><div class="label">Transports<br>4 years (2022-2026)</div></div>
    <div class="kpi green"><div class="val">{sum(1 for e in enriched if e['text'])}</div><div class="label">Documented<br>({round(100*sum(1 for e in enriched if e['text'])/len(enriched))}%)</div></div>
    <div class="kpi purple"><div class="val">400</div><div class="label">Tier-1 Finance core<br>(A_SEFIANI + L_CABALLE + N_MENARD)</div></div>
    <div class="kpi cyan"><div class="val">{len(ticket_setups)}</div><div class="label">Ticket-driven new-country<br>(Francesco + Marlies)</div></div>
    <div class="kpi yellow"><div class="val">8</div><div class="label">HR dev bundles<br>(Said, Fiori + schemas)</div></div>
    <div class="kpi red"><div class="val">2</div><div class="label">DEV_ONLY orphans<br>(never in P01)</div></div>
  </div>

  <div class="card">
    <h3>What this companion answers</h3>
    <p>At UNESCO the <strong>Finance team</strong> owns wage type configuration &mdash; not HR. This is non-standard and undocumented. This companion reverse-engineers <strong>4 years of configuration transports</strong> to answer four questions:</p>
    <ul>
      <li><strong>WHO</strong> maintains wage type config, split by tier of responsibility</li>
      <li><strong>WHAT</strong> SAP objects they touch (the real wage type stack, not just the 5 tables in the screenshot)</li>
      <li><strong>HOW</strong> the configuration is done (patterns, naming conventions, transport cadence)</li>
      <li><strong>WHY</strong> it matters (risk surface: silent salary miscalc, orphan transports, bundled patches)</li>
    </ul>
  </div>

  <div class="card">
    <h3>The story in one paragraph</h3>
    <p>From 2022-04 to 2026-04, UNESCO released <strong>418 transports</strong> touching wage type configuration. The work splits into <strong>3 tiers</strong>:</p>
    <ol>
      <li><strong>Tier 1 (404 TRs, 97%)</strong> &mdash; <span class="mono">A_SEFIANI</span> (252, structural: salary scales, CSI, pensionable), <span class="mono">L_CABALLE</span> (121, operational: LCR monthly per country), <span class="mono">N_MENARD</span> (27, custom PY schemas/PCRs), <span class="mono">FP_SPEZZANO</span> (4, Finance core - new-country payment setup via service desk ticket). This is the <strong>PY-Finance core team</strong>.</li>
      <li><strong>Tier 2 (2 TRs)</strong> &mdash; <span class="mono">M_SPRONK</span> (Marlies) Treasury senior. Touches WT twice in 4 years only when a <strong>service-desk ticket</strong> requires setting up a new country/FO payment method (133188 UNDP 2022, 168627 STN 2024). Her primary domain is Treasury-Finance.</li>
      <li><strong>Tier 3 (8 TRs)</strong> &mdash; <span class="mono">S_IGUENINNI</span> HR development. Large (70+ object) Fiori/WebDynpro bundles for apps like Offboarding and Benefits Enrollment that <strong>drag a handful of PY schemas along</strong>. Not real wage type config &mdash; just development collateral.</li>
    </ol>
    <p>The <strong>dominant recurring pattern</strong> is <span class="badge badge-blue">LCR_MONTHLY</span> (106 TRs, L_CABALLE) &mdash; monthly Local Cost Rate activities per country. The <strong>dominant ad-hoc pattern</strong> is <span class="badge badge-purple">SALARY_SCALE_FO</span> (41 TRs, A_SEFIANI) &mdash; Field Office salary scale revisions for Brasilia, India, Kyrgyzstan, Algeria, Mauritania, Nigeria, Guinea-Bissau, Solomon Islands, and more.</p>
  </div>
</div>
""")

# ==== WHO ====
tier1 = {u:editor_pattern.get(u,Counter()) for u in ['A_SEFIANI','L_CABALLE','N_MENARD']}
tier2 = {u:editor_pattern.get(u,Counter()) for u in ['FP_SPEZZANO','M_SPRONK']}
tier3 = {u:editor_pattern.get(u,Counter()) for u in ['S_IGUENINNI']}
tier4 = {u:editor_pattern.get(u,Counter()) for u in editor_pattern if u not in list(tier1)+list(tier2)+list(tier3)}

html_parts.append("""
<div class="panel" id="who">
  <div class="card">
    <h3>Responsibility tiers</h3>
    <p>Every wage type transport in the last 4 years came from one of 4 tiers of editors. Understanding the tier is the first step when reading a transport.</p>
  </div>

  <div class="tier-card tier-1">
    <h3 style="color:var(--accent)">Tier 1 &mdash; PY-Finance core (404 transports, 97%)</h3>
    <p>The people who <strong>intentionally design and release</strong> wage type config. Their work is the source of truth for UNESCO payroll configuration.</p>
    <table>
      <thead><tr><th>Editor</th><th>TRs</th><th>Role</th><th>Dominant patterns</th></tr></thead>
      <tbody>
""")
for u in ['A_SEFIANI','L_CABALLE','N_MENARD','FP_SPEZZANO']:
    role = TIERS[u]['role']
    counts = editor_pattern.get(u, Counter())
    total = sum(counts.values())
    top3 = ', '.join(f'<span class="badge badge-blue">{p}:{n}</span>' for p,n in counts.most_common(4))
    html_parts.append(f'        <tr><td class="mono">{u}</td><td>{total}</td><td>{role}</td><td>{top3}</td></tr>\n')
html_parts.append("""      </tbody>
    </table>
  </div>

  <div class="tier-card tier-2">
    <h3 style="color:var(--purple)">Tier 2 &mdash; Treasury crossover (2 transports)</h3>
    <p><strong>Marlies Spronk</strong> is a Treasury senior (bank config, payment methods, DMEE formats, account determination). She enters wage type tables <strong>only</strong> when a service desk ticket requires setting up <strong>a new country's payroll payment method</strong>. The trigger is always a numeric ticket in the description. Both transports touch the full 5-tuple (T512T + T512W + T52DZ + T52EL + T52EZ).</p>
    <table>
      <thead><tr><th>Editor</th><th>Total TRs 22-26</th><th>Direct WT TRs</th><th>Role</th></tr></thead>
      <tbody>
        <tr><td class="mono">M_SPRONK (Marlies)</td><td>190</td><td>2</td><td>Treasury senior. WT crossover = new Currency for UNDP FO (2022), STN Sao Tome payment method (2024). Primary work: 29 Payment Methods, 21 Account Determination, 12 DMEE, 4 Company Code. Heavy Treasury configurator.</td></tr>
      </tbody>
    </table>
    <div class="note">Marlies has <strong>190 total transports</strong> but only <strong>2 touch the 5 wage type tables directly</strong>. The rest are pure Treasury (payment method config for country banking). <strong>Her WT work is a small tail of a large Treasury footprint</strong>, not a primary responsibility. FP_SPEZZANO (Francesco) was originally placed in Tier 2 during session #60 drafting but was re-classified to Tier 1 Finance core after user correction: his 4 WT transports are part of his legitimate Finance role, not just Treasury crossover.</div>
  </div>

  <div class="tier-card tier-3">
    <h3 style="color:var(--yellow)">Tier 3 &mdash; HR dev bundles (8 transports, not config)</h3>
    <p><strong>Said Iguenini (S_IGUENINNI)</strong> is an HR developer maintaining Fiori apps (YHR_BEN_ENRL benefits enrollment, Offboarding, Family Sister) and WebDynpro. His 95 transports in 4 years are <strong>large development releases</strong> (typically 70+ objects each: methods, classes, i18n files, data elements). A handful of those transports happen to include PY schema/PCR objects. <strong>These are not wage type config &mdash; they are HR app releases that ship schemas as collateral.</strong></p>
    <table>
      <thead><tr><th>Editor</th><th>Total TRs 22-26</th><th>TRs w/ PY schema</th><th>Role</th></tr></thead>
      <tbody>
        <tr><td class="mono">S_IGUENINNI (Said)</td><td>95</td><td>8</td><td>HR developer. All 95 transports are UNDOCUMENTED. WT-touch is incidental (schemas shipped with Fiori/WebDynpro releases, obj_count per transport = ~70).</td></tr>
      </tbody>
    </table>
    <div class="note">Said's 95 transports have <strong>zero descriptions in E07T</strong>. This is a data quality gap. Nothing prevents him from legitimately using transports as dev containers, but the absence of description makes governance/audit difficult.</div>
  </div>

  <div class="tier-card tier-4">
    <h3 style="color:#aaa">Tier 4 &mdash; Backup / one-off (4 transports)</h3>
    <table>
      <thead><tr><th>Editor</th><th>TRs</th><th>Context</th></tr></thead>
      <tbody>
        <tr><td class="mono">GD_SCHELLINC</td><td>1</td><td>One-off schemas 98100029/34</td></tr>
        <tr><td class="mono">R_CHAFIA</td><td>1</td><td>Single transport</td></tr>
        <tr><td class="mono">R_RIOS</td><td>1</td><td>Single transport</td></tr>
        <tr><td class="mono">F_GUILLOU</td><td>1</td><td>Single transport</td></tr>
      </tbody>
    </table>
    <div class="danger">Concentrated in 2 people: A_SEFIANI and L_CABALLE cover 373 of 418 (89%). FP_SPEZZANO (Tier-1) and N_MENARD know specific corners (new-country setup, custom schemas) but there is no full backup for A_SEFIANI's salary scale / pensionable / CSI work. M_SPRONK (Tier-2 Treasury) knows the T512 core only in the "new country" context.</div>
  </div>
</div>
""")

# ==== WAGE TYPE STACK ====
html_parts.append(f"""
<div class="panel" id="stack">
  <div class="card">
    <h3>The core 5 tables (from Finance team screenshot) &mdash; direct impact on salary</h3>
    <table>
      <thead><tr><th>Table</th><th>Business meaning</th><th>Impact if wrong</th><th>TRs (4y)</th><th>In Gold DB?</th></tr></thead>
      <tbody>
        <tr>
          <td class="mono">T512T</td><td>Wage Type Texts (long/short per language)</td>
          <td>Cosmetic. Wrong label on payslips and reports.</td>
          <td><span class="badge badge-blue">26</span></td>
          <td><span class="badge badge-red">NO</span></td>
        </tr>
        <tr>
          <td class="mono">T512W</td><td><strong>Wage Type Valuation</strong> &mdash; amount, rate, percentage, deduction rule, payment method key (ZLSCH)</td>
          <td><span class="badge badge-red">CRITICAL</span>: wrong row &rarr; silent salary miscalc. No runtime error. Finance team screenshot flags this explicitly.</td>
          <td><span class="badge badge-blue">26</span></td>
          <td><span class="badge badge-red">NO</span></td>
        </tr>
        <tr>
          <td class="mono">T52DZ</td><td>Wage Type Permissibility per Payroll Period (customizing WT &rarr; model WT mapping)</td>
          <td>WT not allowed in the infotype/period &rarr; blocked or silently dropped at entry.</td>
          <td><span class="badge badge-blue">26</span></td>
          <td><span class="badge badge-red">NO</span></td>
        </tr>
        <tr>
          <td class="mono">T52EL</td><td>Valuation Bases for Averages</td>
          <td>Wrong base &rarr; systematic over/under-payment for sick/vacation/severance.</td>
          <td><span class="badge badge-blue">20</span></td>
          <td><span class="badge badge-red">NO</span></td>
        </tr>
        <tr>
          <td class="mono">T52EZ</td><td>Averaging Rules (formula controlling T52EL bases)</td>
          <td>Incorrect rule &rarr; wrong periods in the average.</td>
          <td><span class="badge badge-blue">20</span></td>
          <td><span class="badge badge-red">NO</span></td>
        </tr>
      </tbody>
    </table>
    <div class="danger">None of the 5 core tables are extracted to Gold DB. We cannot audit current wage type state vs. the 418 transports. <strong>Priority-1 extraction backlog.</strong></div>
  </div>

  <div class="card">
    <h3>The extended stack (revealed by reverse engineering)</h3>
    <p>The 5 screenshot tables are the tip. The full wage type stack actually touched by UNESCO in 4 years:</p>
    <div class="grid-2">
      <div>
        <h4>Pay Scale (T510 family) &mdash; most active</h4>
        <ul>
          <li><span class="mono">V_T510</span> &mdash; 157 TRs &mdash; pay scale type/area/group/level amounts per country</li>
          <li><span class="mono">V_T510_C</span> &mdash; 66 TRs &mdash; pay scale constants</li>
          <li><span class="mono">V_T510F_B</span> &mdash; 43 TRs &mdash; pay scale table forms</li>
          <li><span class="mono">V_T510M</span> &mdash; 29 TRs &mdash; pay scale multipliers</li>
          <li><span class="mono">T511</span> &mdash; 15 TRs &mdash; payroll constants</li>
          <li><span class="mono">T512Z</span> &mdash; 67 object hits &mdash; permissibility per period (pay scale level)</li>
        </ul>
      </div>
      <div>
        <h4>Custom schemas &amp; PCRs (UNESCO-specific)</h4>
        <ul>
          <li><span class="mono">PSCC 98100007-98100034</span> &mdash; UNESCO-owned payroll schemas</li>
          <li><span class="mono">PCYC UN25</span> &mdash; UN-specific cycle</li>
          <li><span class="mono">PCYC ZN31, ZN54, ZN60</span> &mdash; custom PCRs</li>
          <li><span class="mono">PCYC ZCSI</span> &mdash; CSI calculation cycle (9 TRs)</li>
          <li><span class="mono">PCYC ZOV0</span> &mdash; overtime</li>
          <li><span class="mono">PCYC ZPPF / ZPP0 / ZPP1</span> &mdash; maintained by N_MENARD</li>
          <li><span class="mono">PCYC ZUSD / ZUXX</span> &mdash; one of the DEV_ONLY orphans</li>
        </ul>
      </div>
    </div>
  </div>

  <div class="card">
    <h3>How wage type assignment is done &mdash; reconstructed workflow</h3>
    <p>The typical sequence when adding/modifying a wage type for a country or Field Office (inferred from transport object co-occurrence):</p>
    <div class="h2r-step"><div class="num">1</div><div><strong>Valuation</strong> in <span class="mono">T512W</span> &mdash; new validity row with amount/rate and payment method key. <em>Never overwrite, always additive</em>.</div></div>
    <div class="h2r-step"><div class="num">2</div><div><strong>Permissibility</strong> in <span class="mono">T52DZ</span> &mdash; customizing WT to model WT mapping for the payroll period. Example from Finance screenshot: <span class="mono">5$B3 &rarr; 5$B2</span> (Stockage devise MZN &rarr; Stockage devise SAR).</div></div>
    <div class="h2r-step"><div class="num">3</div><div><strong>Text</strong> in <span class="mono">T512T</span> per language (at UNESCO mostly EN/FR).</div></div>
    <div class="h2r-step"><div class="num">4</div><div><strong>If averaged</strong>: <span class="mono">T52EL</span> valuation base rows (which periods to include) + <span class="mono">T52EZ</span> averaging rule.</div></div>
    <div class="h2r-step"><div class="num">5</div><div><strong>Country pay scale</strong> in <span class="mono">V_T510</span> / <span class="mono">V_T510F_B</span> / <span class="mono">V_T510_C</span> / <span class="mono">V_T510M</span> &mdash; amounts for pay scale type/area of the Field Office.</div></div>
    <div class="h2r-step"><div class="num">6</div><div><strong>Currency / payment</strong> (new country or FX change): <span class="mono">V_T510</span> currency + <span class="mono">T550P</span> payment method per country + <span class="mono">T042 / V_T042ZL</span> (Treasury crossover).</div></div>
    <div class="h2r-step"><div class="num">7</div><div><strong>Transport</strong>: customizing request (<span class="mono">trfunction=W</span>), description <span class="badge badge-blue">"C - HR - PY : [scope]"</span>, release D01 &rarr; P01.</div></div>
  </div>

  <div class="card">
    <h3>Finance screenshot example decoded: wage type 5$B3 "Stockage devise MZN"</h3>
    <div class="flow">T512T  | 5$B3 | Stockage devise MZN                                    (text)
T512W  | 5$B3 | Valuation from 01.01.1901 to 31.12.9999                 (valuation row)
T52DZ  | 5$B3 (CWType) | Stockage devise MZN &rarr; 5$B2 (MWType) Stockage devise SAR
T52EL  | -350 UN 5$B3 019999 1231  (valuation base row)
       | -350 UN 5$B3 029999 1231  (second base row)
T52EZ  | 5$B3 | Averaging rule from 01.01.2012 to 31.12.9999</div>
    <p>This is a storage wage type for currency MZN (Mozambican metical) mapped to SAR (Saudi Riyal) &mdash; Finance screenshot confirms the <strong>countries-to-WT mapping</strong> pattern: every Field Office country that pays in its own currency gets a "Stockage devise XXX" WT, with valuation, text, permissibility, and averaging rules all aligned on the same 4-character WT code pattern (<span class="mono">5$B3</span>).</p>
  </div>
</div>
""")

# ==== PATTERNS ====
pattern_descriptions = {
    'LCR_MONTHLY':      ('L_CABALLE', 'blue', 'Local Cost Rate monthly activities, one transport per country per month. Example: "C - HR - PY : LCR_January payroll activities_GN"'),
    'SALARY_SCALE_FO':  ('A_SEFIANI', 'purple', 'Service Contract / Staff Category salary scale revision for a specific Field Office. Example: "C - HR - PY : SC Salary Scales for Brasilia from 01.01.2025"'),
    'CURRENCY_PAYMT':   ('A_SEFIANI', 'orange', 'Currency code or payment method change per country. Example: "C - HR - PY : Currency for Nigeria SC &amp; STC from 01.12.2023"'),
    'CSI':              ('A_SEFIANI', 'cyan', 'Cost of Staff Index adjustments for SC staff. Typically end-of-year. Example: "C - HR - PY : CSI for SC from 012023"'),
    'PENSIONABLE':      ('A_SEFIANI', 'green', 'Pensionable Remuneration updates for UNDP and International Staff. Annual. Example: "C - HR - PY : Pensionable Remuneration 022026 for Inter Staff"'),
    'UBO_INTEGRATION':  ('A_SEFIANI', 'blue', 'Integration with UBO Field Office .NET app (SCs Integration).'),
    'SOCIAL_SECURITY':  ('A_SEFIANI', 'red', 'Country-specific social security (e.g. INSS for Brasilia).'),
    'UNDP_SPECIFIC':    ('A_SEFIANI', 'yellow', 'UNDP-specific administrative WT config.'),
    'TICKET_NEW_COUNTRY_SETUP': ('FP_SPEZZANO / M_SPRONK', 'purple', 'Treasury team responds to a service-desk ticket to set up a new country/FO payment infrastructure. Full 5-table wage type chain is touched. Example: "180995 / Creat Payment Method Mozambic"'),
    'WF_WORKFLOW':      ('N_MENARD', 'yellow', 'Workflow-adjacent config bundled with WT transports.'),
    'OTHER_CONFIG':     ('mixed', '', 'Documented but does not fit a specific pattern.'),
    'UNDOCUMENTED':     ('mixed', 'red', 'No E07T description. Scope cannot be inferred without opening the transport.'),
}

html_parts.append("""
<div class="panel" id="patterns">
  <div class="card">
    <h3>Activity patterns detected</h3>
    <p>Each transport is classified into one pattern based on description text + editor. The patterns reveal the rhythm and triggers of UNESCO wage type work.</p>
    <table>
      <thead><tr><th>Pattern</th><th>Count</th><th>Share</th><th>Owner(s)</th><th>What it is</th></tr></thead>
      <tbody>
""")
total_p = sum(pattern_counter.values())
for p,n in pattern_counter.most_common():
    pct = round(100*n/total_p,1)
    owner, color, desc_txt = pattern_descriptions.get(p, ('-','','-'))
    badge = f'<span class="badge badge-{color}">{p}</span>' if color else f'<span class="badge">{p}</span>'
    html_parts.append(f'        <tr><td>{badge}</td><td>{n}</td><td>{pct}%</td><td class="mono">{owner}</td><td>{desc_txt}</td></tr>\n')

html_parts.append("""      </tbody>
    </table>
  </div>

  <div class="grid-2">
    <div class="pattern-card">
      <h4 style="color:var(--accent)">LCR monthly rhythm (L_CABALLE, 106 TRs)</h4>
      <p>Every month, transports per country cluster. The strongest naming discipline in the whole dataset.</p>
      <div class="flow">C - HR - PY : LCR_January payroll activities
C - HR - PY : LCR_January payroll activities_GN
C - HR - PY : LCR_December payroll activities_GH
C - HR - PY : LCR_December payroll activities_MG-PH
C - HR - PY : LCR_December payroll activities_NP_Cor
C - HR - PY : LCR_March 2026 payroll activities
C - HR - PY : LCR_February 2026 payroll activities_ME
C - HR - PY : LCR_December 2025 payroll activities_DZ_2024</div>
      <div class="good">100% of LCR transports follow the "<code>C - HR - PY : LCR_[Month] [Year?] payroll activities[_Country]</code>" template.</div>
    </div>

    <div class="pattern-card">
      <h4 style="color:var(--purple)">Salary Scale SC (A_SEFIANI, 41 TRs)</h4>
      <p>Ad-hoc per country/FO, triggered by cost-of-living revisions.</p>
      <div class="flow">C - HR - PY : SC Salary Scales for Brasilia from 01.01.2025
C - HR - PY : Salary Scales SC Guinea-Bissau
C - HR - PY : Salary Scale SC for India
SC - HR - PY : Salary Scale SC Kyrgyzstan
C - HR - PY : Salary Scales SC Guinea-Bissau
C - HR - PY : Salary Scale SC Field Offices from 042025 Bi
C - HR - PY : Currency and payment method MRU &amp; SBD</div>
      <p>Touches <span class="mono">V_T510</span> + <span class="mono">V_T510F_B</span> + <span class="mono">T512W</span>. Effective date embedded in description (<code>from DD.MM.YYYY</code>).</p>
    </div>

    <div class="pattern-card">
      <h4 style="color:var(--cyan)">CSI (A_SEFIANI, 17 TRs)</h4>
      <p>Cost of Staff Index for SC staff. End-of-year rollover.</p>
      <div class="flow">C - HR - PY : CSI for SC from 012023
C - HR - PY : CSI for SC from 012023 Bis
C - HR - PY : CSI for SC Staff from 01.01.2024</div>
      <p>Touches <span class="mono">PCYC ZCSI</span> + <span class="mono">T511</span> + <span class="mono">V_T510</span>.</p>
    </div>

    <div class="pattern-card">
      <h4 style="color:var(--green)">Pensionable remuneration (A_SEFIANI, 9 TRs)</h4>
      <p>Annual for UNDP and International Staff.</p>
      <div class="flow">C - HR - PY : Pensionable rem of the UNDP Admi 022026
C - HR - PY : Pensionable Remuner 022026 for Inter Staff</div>
    </div>

    <div class="pattern-card">
      <h4 style="color:var(--purple)">Ticket-driven new country (FP_SPEZZANO + M_SPRONK, 6 TRs)</h4>
      <p>Treasury team sets up new country/Field Office payment infrastructure. Full 5-table wage type chain is touched. Description always starts with a <strong>service desk ticket number</strong>.</p>
      <div class="flow">180995 / Creat Payment Method Mozambic
180995 - Payment Method U with currency LKR
172777 - Payment Method Mongolia_1
168627 - Payroll STN payment method U
133188 - New Currency for FO UNDP payroll payments</div>
      <p>Tickets known: 180995 (Mozambique + Sri Lanka LKR, 2024-11), 172777 (Mongolia, 2024-07), 168627 (Sao Tome STN, 2024-05), 133188 (UNDP, 2022-07).</p>
    </div>

    <div class="pattern-card">
      <h4 style="color:var(--red)">Undocumented (78 TRs, 19%)</h4>
      <p>Transports with no E07T description. Breakdown:</p>
      <ul>
        <li>Most are from A_SEFIANI during bursts of related config releases</li>
        <li>The single transport D01K9B0C78 (FP_SPEZZANO 2024-09-17, touches 5 WT tables) is likely a failed Mongolia/LKR attempt before 180995 ticket</li>
        <li>All 95 S_IGUENINNI transports are undocumented (HR dev bundles, separate issue)</li>
      </ul>
    </div>
  </div>

  <div class="card">
    <h3>Description-text discipline by editor</h3>
    <table>
      <thead><tr><th>Editor</th><th>TRs</th><th>With description</th><th>Pct</th><th>Verdict</th></tr></thead>
      <tbody>
""")

for u in ['A_SEFIANI','L_CABALLE','N_MENARD','FP_SPEZZANO','M_SPRONK','S_IGUENINNI']:
    ed_trs = [e for e in enriched if e['as4user'] == u]
    n = len(ed_trs)
    if n == 0: continue
    with_t = sum(1 for e in ed_trs if e['text'])
    pct = round(100*with_t/n,0)
    verdict = ("Excellent", "badge-green") if pct >= 90 else ("Good","badge-blue") if pct >= 75 else ("Needs improvement","badge-yellow") if pct >= 40 else ("Poor","badge-red")
    html_parts.append(f'        <tr><td class="mono">{u}</td><td>{n}</td><td>{with_t}</td><td>{pct:.0f}%</td><td><span class="badge {verdict[1]}">{verdict[0]}</span></td></tr>\n')

html_parts.append("""      </tbody>
    </table>
    <div class="note">L_CABALLE and A_SEFIANI are the reference for naming discipline. S_IGUENINNI (0% described) needs governance intervention.</div>
  </div>
</div>
""")

# ==== FRANCESCO / MARLIES / SAID ====
# Rebuild list of TR details for the 3 editors' WT-touching transports
fp_wt = [e for e in enriched if e['as4user']=='FP_SPEZZANO']
ms_wt = [e for e in enriched if e['as4user']=='M_SPRONK']
si_wt = [e for e in enriched if e['as4user']=='S_IGUENINNI']

html_parts.append("""
<div class="panel" id="francesco">
  <div class="card">
    <h3>The Treasury / HR-Dev crossover &mdash; 3 editors, 3 different stories</h3>
    <p>Earlier analysis grouped these three under "wage type editors". That's misleading. A closer look shows each has a different relationship with wage type tables.</p>
  </div>

  <div class="card">
    <h3>FP_SPEZZANO (Francesco Spezzano) &mdash; Tier-1 Finance core, 4 WT transports</h3>
    <p>Francesco is part of the <strong>Tier-1 Finance core</strong> (user correction, session #60). His 70 transports over 4 years include Treasury work (Payment Methods, Account Determination, DMEE XML formats, bank configuration CIT05/BMN01/Banco de Chile/AIB01, cash journals HAV3 Havana / KHR Cambodia, ARGA Project) AND Finance-core wage type work when a service desk ticket requires a new country's payroll payment setup. The WT touches are a legitimate part of his Finance role, not Treasury crossover.</p>
    <table>
      <thead><tr><th>Date</th><th>TRKORR</th><th>Ticket</th><th>Description</th><th>5 WT tables</th><th>Other objects</th></tr></thead>
      <tbody>
""")
for e in sorted(fp_wt, key=lambda x: x['as4date'], reverse=True):
    d = e['as4date']; dstr = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    other = e['obj_count'] - e['core5_count'] - 1  # minus RELE
    html_parts.append(f'        <tr><td class="mono">{dstr}</td><td class="mono">{e["trkorr"]}</td><td class="mono">{e["ticket_no"] or "&mdash;"}</td><td>{(e["text"] or "(no description)")[:70]}</td><td>{e["core5_count"]}/5</td><td>{other}</td></tr>\n')

html_parts.append("""      </tbody>
    </table>
    <div class="note">User expectation ("should have maybe only 1") matches the <strong>most recent</strong> 180995 ticket for Mozambique. The other 3 are: D01K9B0CE6 (same ticket 180995, different country LKR/Sri Lanka, same day 2024-11-19), D01K9B0C1L (separate ticket 172777 Mongolia, 2024-07), D01K9B0C78 (undocumented 2024-09, likely a failed attempt before 180995 ticket was opened).</div>
  </div>

  <div class="card">
    <h3>M_SPRONK (Marlies Spronk) &mdash; Treasury senior, 2 WT-direct + 50+ WT-adjacent</h3>
    <p>Marlies is a <strong>senior Treasury configurator</strong>: 190 transports over 4 years with 729 object hits on Payment Methods (29), Account Determination (21), DMEE (12), Company Code (4), and deep work on CITI XML v3, SEPA IBAN, EBS settings, Cash Pool, Cheque payments, TMS project. Her wage-type-direct work is <strong>only 2 transports</strong>:</p>
    <table>
      <thead><tr><th>Date</th><th>TRKORR</th><th>Ticket</th><th>Description</th><th>5 WT tables</th></tr></thead>
      <tbody>
""")
for e in sorted(ms_wt, key=lambda x: x['as4date'], reverse=True):
    d = e['as4date']; dstr = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    html_parts.append(f'        <tr><td class="mono">{dstr}</td><td class="mono">{e["trkorr"]}</td><td class="mono">{e["ticket_no"] or "&mdash;"}</td><td>{(e["text"] or "(no description)")[:80]}</td><td>{e["core5_count"]}/5</td></tr>\n')

html_parts.append("""      </tbody>
    </table>
    <div class="note">User expectation ("will have a lot") is accurate if we count <strong>WT-adjacent work</strong>: payment methods and account determination enable the FI-side infrastructure that wage types post to. But <strong>direct wage type table touches are only 2</strong>. Her primary domain is Treasury-Finance, not PY-Finance. Her transports are covered in the Treasury companion.</div>
    <h4>Marlies's dominant WT-adjacent work (sample)</h4>
    <div class="flow">TMS - Import EBS settings
TMS - Update CITI XMLv3 with US CA travel rules
TMS - Update payment method A to CITI XMLv3
TMS - Update Payment method N UIS to CITI XMLv3
TMS - Remove Payment Method N to CITI XML v3
CR128 - UBO EBS Update Search String
CR128 - Payment Advice UBO
227 - Cash Pool EBS CIT04 USD04
Update SEPA IBAN country settings
Cheque without signature
130571 - Correction Cash position report
130768 - Close account SOG03 EUR02
133132 - Cheque payments BMN01 EUR01 Havana</div>
  </div>

  <div class="card">
    <h3>S_IGUENINNI (Said Iguenini) &mdash; HR developer, 95 TRs / 8 with PY schema collateral</h3>
    <p>Said is an <strong>HR developer</strong> maintaining Fiori apps and WebDynpro. His 95 transports have <strong>3,921 total object hits</strong> &mdash; average <strong>41 objects per transport</strong>. They are development release bundles, not configuration. Example contents of one of his 8 "WT-touching" transports:</p>
    <div class="flow">D01K9B0E7W  2025-12-04  obj_count=78
  DTED/ZE_HRFIORI_OFFBOARDING_DOC_TX     (data element texts)
  METH/ZCL_HRFIORI_CHANGE_SISTER          (ABAP method)
  METH/ZCL_ZHRF_OFFBOARD_DPC_EXT          (Fiori DPC_EXT redefine)
  WAPP/YHR_BEN_ENRL  COMPONENT.JS         (SAPUI5 Fiori app)
  WAPP/YHR_BEN_ENRL  CONTROLLER/ENROLLMENTCUSTOM.CONTROLLER.JS
  WAPP/YHR_BEN_ENRL  I18N/I18N_EN.PROPERTIES  (+26 more language files)
  ...
  PCYC/[one PY cycle]                     &lt;-- dragged along
  PSCC/[one PY schema]                    &lt;-- dragged along</div>
    <div class="danger">Said's 95 transports are 100% undocumented in E07T and 100% large dev bundles. The 8 classified as "WT-related" by my filter are <strong>false positives</strong> &mdash; the PY objects are collateral. A proper review should confirm these schemas are intentionally updated or accidentally bundled.</div>
  </div>

  <div class="card">
    <h3>Summary: three editors, three relationships with wage types</h3>
    <table>
      <thead><tr><th>Editor</th><th>Total TRs 22-26</th><th>Direct WT</th><th>WT-adjacent</th><th>Trigger</th><th>Real domain</th></tr></thead>
      <tbody>
        <tr><td class="mono">FP_SPEZZANO</td><td>70</td><td>4</td><td>9 paymt + 6 acct + 5 DMEE = 20</td><td>Service desk ticket (new country)</td><td>Treasury-Finance</td></tr>
        <tr><td class="mono">M_SPRONK</td><td>190</td><td>2</td><td>29 paymt + 21 acct + 12 DMEE = 62</td><td>Service desk ticket (new country) + TMS project</td><td>Treasury-Finance (senior)</td></tr>
        <tr><td class="mono">S_IGUENINNI</td><td>95</td><td>8 (collateral)</td><td>0 direct; 3921 objs in bundles</td><td>HR Fiori/WebDynpro app release</td><td>HR Development (not config)</td></tr>
      </tbody>
    </table>
  </div>
</div>
""")

# ==== TIMELINE ====
html_parts.append("""
<div class="panel" id="timeline">
  <div class="card">
    <h3>Year &times; Pattern matrix</h3>
    <table>
      <thead><tr><th>Year</th><th>LCR</th><th>Salary Scale</th><th>Currency</th><th>CSI</th><th>Pensionable</th><th>UBO</th><th>Ticket NewCountry</th><th>Other</th><th>Undoc</th><th>Total</th></tr></thead>
      <tbody>
""")
ycols = ['LCR_MONTHLY','SALARY_SCALE_FO','CURRENCY_PAYMT','CSI','PENSIONABLE','UBO_INTEGRATION','TICKET_NEW_COUNTRY_SETUP','OTHER_CONFIG','UNDOCUMENTED']
for y in sorted(year_pattern):
    total_y = sum(year_pattern[y].values())
    row = f'        <tr><td class="mono">{y}</td>'
    for c in ycols:
        v = year_pattern[y].get(c,0)
        alpha = min(1, v/30)
        cell = f'<td style="text-align:right;background:rgba(88,166,255,{alpha:.2f})">{v if v else "&middot;"}</td>'
        row += cell
    row += f'<td style="text-align:right;font-weight:600">{total_y}</td></tr>\n'
    html_parts.append(row)
html_parts.append("""      </tbody>
    </table>
  </div>

  <div class="card">
    <h3>Recent activity (last 30 transports)</h3>
    <div class="subtable-wrap">
    <table>
      <thead><tr><th>Date</th><th>TRKORR</th><th>Editor</th><th>Pattern</th><th>Description</th><th>WT objs</th></tr></thead>
      <tbody>
""")
for e in enriched[:30]:
    d = e['as4date']; dstr = f"{d[:4]}-{d[4:6]}-{d[6:8]}" if len(d)==8 else d
    txt = (e['text'] or '&mdash; no description &mdash;')[:100].replace('<','&lt;')
    html_parts.append(f'        <tr><td class="mono">{dstr}</td><td class="mono">{e["trkorr"]}</td><td class="mono">{e["as4user"]}</td><td><span class="badge badge-purple">{e["pattern"]}</span></td><td>{txt}</td><td style="text-align:right">{e["wt_count"]}</td></tr>\n')

html_parts.append("""      </tbody>
    </table>
    </div>
  </div>
</div>
""")

# ==== RISK ====
html_parts.append("""
<div class="panel" id="risk">
  <div class="card">
    <h3>Risk matrix</h3>
    <table>
      <thead><tr><th>Risk</th><th>Likelihood</th><th>Impact</th><th>Detectability</th><th>Severity</th></tr></thead>
      <tbody>
        <tr><td><strong>T512W wrong row &rarr; silent salary miscalc</strong></td><td><span class="badge badge-yellow">Med</span></td><td><span class="badge badge-red">Critical</span></td><td><span class="badge badge-red">Hard (no error)</span></td><td><span class="badge badge-red">CRITICAL</span></td></tr>
        <tr><td><strong>V_T510 wrong amount for Field Office</strong></td><td><span class="badge badge-red">High (frequent edits)</span></td><td><span class="badge badge-red">Critical (whole FO)</span></td><td><span class="badge badge-yellow">Med (FO complaints)</span></td><td><span class="badge badge-red">CRITICAL</span></td></tr>
        <tr><td><strong>T52EL/EZ wrong avg base</strong></td><td><span class="badge badge-yellow">Med</span></td><td><span class="badge badge-orange">High</span></td><td><span class="badge badge-red">Very hard</span></td><td><span class="badge badge-orange">HIGH</span></td></tr>
        <tr><td><strong>LCR missed country in month</strong></td><td><span class="badge badge-yellow">Med</span></td><td><span class="badge badge-yellow">Med (1-month lag)</span></td><td><span class="badge badge-yellow">Med</span></td><td><span class="badge badge-yellow">MEDIUM</span></td></tr>
        <tr><td><strong>DEV_ONLY orphan (never in P01)</strong></td><td><span class="badge badge-green">Low (2 in 4y)</span></td><td><span class="badge badge-orange">High (D01&ne;P01)</span></td><td><span class="badge badge-orange">Hard (manual audit)</span></td><td><span class="badge badge-orange">HIGH</span></td></tr>
        <tr><td><strong>Bundled SAP patch silently ships WT changes</strong></td><td><span class="badge badge-red">High</span></td><td><span class="badge badge-yellow">Med</span></td><td><span class="badge badge-orange">Hard</span></td><td><span class="badge badge-orange">HIGH</span></td></tr>
        <tr><td><strong>Tier-1 single-point-of-failure (A_SEFIANI)</strong></td><td><span class="badge badge-yellow">Med</span></td><td><span class="badge badge-red">Critical</span></td><td><span class="badge badge-green">Easy (absence)</span></td><td><span class="badge badge-orange">HIGH</span></td></tr>
        <tr><td><strong>Undocumented transports (78 in 4y, 19%)</strong></td><td><span class="badge badge-red">High</span></td><td><span class="badge badge-yellow">Med (audit pain)</span></td><td><span class="badge badge-green">Easy</span></td><td><span class="badge badge-yellow">MEDIUM</span></td></tr>
      </tbody>
    </table>
  </div>

  <div class="card">
    <h3>DEV_ONLY orphan transports (never released to P01)</h3>
    <table>
      <thead><tr><th>TRKORR</th><th>Date</th><th>Editor</th><th>WT Objects</th><th>Action</th></tr></thead>
      <tbody>
""")
for orphan in analysis['orphans_dev_only']:
    html_parts.append(f'        <tr><td class="mono">{orphan["trkorr"]}</td><td class="mono">{orphan["as4date"]}</td><td class="mono">{orphan["as4user"]}</td><td class="mono">{", ".join(orphan["wt_objects"])}</td><td><span class="badge badge-yellow">Confirm intentional or release</span></td></tr>\n')

html_parts.append("""      </tbody>
    </table>
  </div>

  <div class="card">
    <h3>Data quality findings</h3>
    <ul>
      <li><span class="badge badge-red">DQ-1</span> <strong>5 core WT tables not in Gold DB</strong> (T512T/W/T52DZ/T52EL/T52EZ). Cannot audit current state against 418 transports. Must RFC-extract.</li>
      <li><span class="badge badge-red">DQ-2</span> <strong>78/418 transports lack E07T description</strong>. Worst offenders: S_IGUENINNI 95/95 (100%), then 2024 bursts from A_SEFIANI.</li>
      <li><span class="badge badge-yellow">DQ-3</span> <strong>113 transports are bundled SAP patches</strong> (&gt;30 objects or &lt;50% WT share). They drag WT objects along with SAP-delivered content. Makes audit of intentional-vs-collateral change harder.</li>
      <li><span class="badge badge-yellow">DQ-4</span> <strong>2 DEV_ONLY orphans</strong>. Process gap: no periodic check of released-on-D01-not-P01 transports.</li>
      <li><span class="badge badge-yellow">DQ-5</span> <strong>No automated WT consistency checker</strong> (e.g., T512W overlapping validity dates, zero amounts, orphan permissibilities).</li>
      <li><span class="badge badge-blue">DQ-6</span> <strong>CDPOS not in Gold DB</strong>. We have 7.8M CDHDR rows but not the field-level before/after needed for exact change reconstruction.</li>
      <li><span class="badge badge-blue">DQ-7</span> <strong>T550P payment method per country not extracted</strong>. Needed to link country setup transports (Francesco/Marlies) to the WT payment method key.</li>
    </ul>
  </div>
</div>
""")

# ==== TRANSPORT BROWSER ====
html_parts.append("""
<div class="panel" id="browser">
  <div class="card">
    <h3>Transport browser &mdash; 418 wage type transports (2022-2026)</h3>
    <div class="toolbar">
      <input type="text" id="tb-search" placeholder="Search description, TRKORR, editor, country..." style="flex:1;min-width:280px">
      <select id="tb-year"><option value="">All years</option><option>2022</option><option>2023</option><option>2024</option><option>2025</option><option>2026</option></select>
      <select id="tb-editor"><option value="">All editors</option><option>A_SEFIANI</option><option>L_CABALLE</option><option>N_MENARD</option><option>FP_SPEZZANO</option><option>M_SPRONK</option><option>S_IGUENINNI</option><option>FP_SPEZZANO</option></select>
      <select id="tb-pattern"><option value="">All patterns</option><option>LCR_MONTHLY</option><option>SALARY_SCALE_FO</option><option>CURRENCY_PAYMT</option><option>CSI</option><option>PENSIONABLE</option><option>UBO_INTEGRATION</option><option>TICKET_NEW_COUNTRY_SETUP</option><option>OTHER_CONFIG</option><option>UNDOCUMENTED</option></select>
      <span id="tb-count" style="color:#8b949e;font-size:.85em"></span>
    </div>
    <div class="subtable-wrap" style="max-height:720px">
      <table id="tb-table">
        <thead><tr><th>Date</th><th>TRKORR</th><th>Editor</th><th>Pattern</th><th>Description</th><th>Core 5</th><th>WT objs</th><th>Total objs</th><th>Deploy</th></tr></thead>
        <tbody id="tb-body"></tbody>
      </table>
    </div>
  </div>
</div>
""")

# ==== NEXT ACTIONS ====
html_parts.append("""
<div class="panel" id="next">
  <div class="card">
    <h3>Priority actions for PY-Finance domain</h3>
    <ol>
      <li><strong>[P1] Extract the 5 core WT tables + V_T510 family to Gold DB</strong>. Owner: sap_data_extraction skill. Effort ~1 day. Blocker for any audit of current-state vs 4-year history.</li>
      <li><strong>[P1] Resolve the 2 DEV_ONLY orphans</strong> (D01K9B0BYN ZUSD/ZUXX 2025-01-09, D01K9B0CFW V_T510 2024-11-26). Confirm with A_SEFIANI: intentional scratch or stuck release.</li>
      <li><strong>[P1] Automated WT consistency checker</strong> (<code>Zagentexecution/quality_checks/wt_consistency.py</code>): T512W overlapping validity dates, T52DZ orphan permissibilities, V_T510 amount outliers.</li>
      <li><strong>[P2] Document the LCR monthly SOP</strong>. L_CABALLE's country list + calendar + review steps + verification checklist.</li>
      <li><strong>[P2] Standardize description template</strong>: mandate "<code>C - HR - PY : [Activity] [Country] [EffectiveDate]</code>". Would bring 78 undocumented to 0 going forward. Also fix the S_IGUENINNI HR-dev 100% undocumented case (separate governance track).</li>
      <li><strong>[P2] WT-assignment traceability skill</strong>: given WT ID + country, return the transport lineage that brought it to current state.</li>
      <li><strong>[P3] Cross-train backups</strong> for Tier 1: FP_SPEZZANO (Tier-1) already owns new-country payment setup; extend his training to CSI / Salary Scale SC. M_SPRONK (Tier-2 Treasury) is only a limited emergency backup for T512 context.</li>
      <li><strong>[P3] Register PY-Finance as first-class domain</strong> in brain_state Layer 14 with owner, objects, claims, this companion as knowledge doc.</li>
      <li><strong>[P3] Extend Transport Companion</strong> to auto-tag wage type transports with the naming convention detection + pattern classification.</li>
    </ol>
  </div>

  <div class="card">
    <h3>Companion v2 candidates (what's not covered here)</h3>
    <ul>
      <li>Country &times; wage type matrix (needs T512W + T511P extraction)</li>
      <li>Actual before/after values per transport (needs CDPOS extraction)</li>
      <li>Payroll run results impact analysis (needs PCL2/RT cluster reading)</li>
      <li>FI posting mapping (T52EK symbolic accounts &rarr; GL) for the Finance visibility</li>
      <li>WT assignment chain from employee (IT0008/IT0014/IT0015) to payslip via T512W</li>
      <li>Treasury-WT bridge: how T042 payment methods, T012 house banks, T030 account determination connect to wage types in posting</li>
    </ul>
  </div>

  <div class="card">
    <h3>How this companion was built (reproducibility)</h3>
    <ul>
      <li>Source: <span class="mono">cts_transports</span> + <span class="mono">cts_objects</span> in Gold DB (7,745 transports / 108K objects).</li>
      <li>Filter: obj_name in 100+ WT-table whitelist OR obj_name LIKE 'V_T51%' / 'V_T52%' OR object IN ('PSCC','PCYC','PDWS'), AND as4date BETWEEN 20220421 AND 20260421.</li>
      <li>Classification: MICRO_CONFIG (&le;5 objs), MAJOR_CONFIG (6-30 objs), BUNDLED_PATCH (&gt;30 objs OR &lt;50% WT share).</li>
      <li>Descriptions: live via RFC <span class="mono">RFC_READ_TABLE E07T</span> against P01 (client 001), batched 6-10 TRKORRs per call to bypass "suspicious WHERE" limit. 340/418 (81%) retrieved.</li>
      <li>Patterns: regex over description + editor context (TICKET_NEW_COUNTRY_SETUP uses both rules).</li>
      <li>Raw data: <span class="mono">Zagentexecution/py_finance_investigation/{transport_manifest_4yr, transports_enriched, tr_descriptions, aggregate, fp_ms_si_footprint, fp_ms_si_categorized}.json</span></li>
      <li>Rebuild: <span class="mono">Zagentexecution/py_finance_investigation/build_companion.py</span></li>
    </ul>
  </div>
</div>
</div>

<script>
const ROWS = """)
html_parts.append(rows_json)
html_parts.append(""";
document.querySelectorAll('.tab').forEach(t => t.addEventListener('click', () => {
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));
  t.classList.add('active');
  document.getElementById(t.dataset.p).classList.add('active');
  if (t.dataset.p==='browser') renderBrowser();
}));
function renderBrowser() {
  const q = document.getElementById('tb-search').value.toLowerCase();
  const y = document.getElementById('tb-year').value;
  const ed = document.getElementById('tb-editor').value;
  const p = document.getElementById('tb-pattern').value;
  const filt = ROWS.filter(r => {
    if (y && String(r.year)!==y) return false;
    if (ed && r.as4user!==ed) return false;
    if (p && r.pattern!==p) return false;
    if (q) {
      const s = `${r.trkorr} ${r.as4user} ${r.text} ${r.pattern} ${r.countries.join(' ')}`.toLowerCase();
      if (!s.includes(q)) return false;
    }
    return true;
  });
  const body = document.getElementById('tb-body');
  body.innerHTML = filt.slice(0,500).map(r => {
    const d = r.as4date.length===8 ? `${r.as4date.slice(0,4)}-${r.as4date.slice(4,6)}-${r.as4date.slice(6,8)}` : r.as4date;
    const dep = r.deploy_level==='DEV_ONLY' ? `<span class="badge badge-red">${r.deploy_level}</span>` : `<span class="badge badge-green">${r.deploy_level||'-'}</span>`;
    const txt = (r.text||'&mdash;').replace(/&/g,'&amp;').replace(/</g,'&lt;');
    return `<tr><td class="mono">${d}</td><td class="mono">${r.trkorr}</td><td class="mono">${r.as4user}</td><td><span class="badge badge-purple">${r.pattern}</span></td><td>${txt}</td><td style="text-align:right">${r.core5_count}/5</td><td style="text-align:right">${r.wt_count}</td><td style="text-align:right">${r.obj_count}</td><td>${dep}</td></tr>`;
  }).join('');
  document.getElementById('tb-count').textContent = `${filt.length} of ${ROWS.length} transports (showing max 500)`;
}
['tb-search','tb-year','tb-editor','tb-pattern'].forEach(id => document.getElementById(id).addEventListener('input',renderBrowser));
document.getElementById('tb-year').addEventListener('change',renderBrowser);
document.getElementById('tb-editor').addEventListener('change',renderBrowser);
document.getElementById('tb-pattern').addEventListener('change',renderBrowser);
renderBrowser();
</script>
</body></html>
""")

html = ''.join(html_parts)
os.makedirs('companions', exist_ok=True)
with open('companions/py_finance_wage_type_companion_v1.html','w',encoding='utf-8') as f:
    f.write(html)
with open('py_finance_wage_type_companion_v1.html','w',encoding='utf-8') as f:
    f.write(html)
print(f"Saved: companions/py_finance_wage_type_companion_v1.html ({os.path.getsize('companions/py_finance_wage_type_companion_v1.html')/1024:.1f} KB)")
print(f"Saved: py_finance_wage_type_companion_v1.html")
