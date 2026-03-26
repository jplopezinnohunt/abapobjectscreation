"""
Builds _pi_part3b_realdata.js by embedding the CTS event log
as a JS constant (REAL_CTS_DATA) into the HTML tool.
Run this after _build_cts_eventlog.py
"""
import json, os

evlog_path = r'mcp-backend-server-python/cts_eventlog.json'
out_path = r'_pi_part3b_realdata.js'

with open(evlog_path, encoding='utf-8') as f:
    evlog = json.load(f)

meta = evlog['meta']
kpis = evlog['kpis']
events = evlog['events']

# Build JS file
lines = []
lines.append('// REAL SAP DATA — CTS Transport Event Log (embedded at build time)')
lines.append(f'// Source: {meta["source"]}')
lines.append(f'// Years: {meta["years"]} | Transports: {meta["total_transports"]} | Sampled: {meta["sampled_cases"]} cases')
lines.append('')
lines.append(f'const REAL_CTS_DATA = {json.dumps(evlog, ensure_ascii=False)};')
lines.append('')
# Wire into Engine as a loadable source
lines.append("""
// Wire real CTS data into the Engine
Engine.loadRealCTS = function() {
    const events = REAL_CTS_DATA.events.map(e => ({
        caseId: e.caseId,
        activity: e.activity,
        timestamp: e.timestamp,
        owner: e.owner,
        year: e.year,
        complexity: e.complexity
    }));
    this.eventLog = events;
    this.currentKey = 'cts_real';
    return this.mine();
};

// Override the sample loader for 'cts' key to use real data
const _origLoad = Engine.load.bind(Engine);
Engine.load = function(key) {
    if (key === 'cts') {
        this.currentKey = 'cts_real';
        this.eventLog = REAL_CTS_DATA.events;
        return this.mine();
    }
    return _origLoad(key);
};

// Add CTS Real as a SAMPLE entry so the Process List shows it
SAMPLES['cts'] = {
    name: 'CTS Change Management',
    icon: '📦',
    color: '#00b8d9',
    bg: '#e6fcff',
    activities: ['Create Transport', 'Config/ViewData', 'Code/Program', 'Other/METH', 'Release Transport'],
    targetFlow: ['Create Transport', 'Config/ViewData', 'Release Transport'],
    baseTime: [1, 3, 0.1],
    brs: 78,
    sapSources: ['E070', 'E071', 'E07T'],
    desc: 'REAL DATA — SAP System D01: ' + REAL_CTS_DATA.meta.total_transports + ' transports (2022–2024)',
    realData: true
};

// CTS KPI overlay for Discover view (real numbers)
const CTS_REAL_KPIS = {
    totalTransports: REAL_CTS_DATA.kpis.totalTransports,
    byType: REAL_CTS_DATA.kpis.byType,
    byYear: REAL_CTS_DATA.kpis.byYear,
    topCategories: REAL_CTS_DATA.kpis.topCategories,
    complexCases: REAL_CTS_DATA.kpis.complexCases,
    simpleCases: REAL_CTS_DATA.kpis.simpleCases
};
""")

js_content = '\n'.join(lines)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(js_content)

size = os.path.getsize(out_path)
print(f'Written: {out_path} ({size:,} bytes / {size//1024} KB)')
