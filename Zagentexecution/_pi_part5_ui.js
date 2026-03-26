// UI CONTROLLER — Intelligent Process Mining
let globalResult = null; let globalKey = null;
let chart_trend = null, chart_brs = null, chart_asIsToBe = null;

// SAP DATA SOURCES REGISTRY — what we actually read from this system
const SAP_SOURCES = {
    cts: { name: 'CTS Transport Log', icon: '📦', tables: ['E070', 'E071', 'E07T'], status: 'connected', records: '12,847', domain: 'Configuration & Enhancements', desc: 'Change requests track who changed what, which object types, and when — the definitive event log for config change process mining. Already extracted for this system.', mapTo: 'Case=Transport# (TRKORR), Activity=Object Type (PGMID/OBJECT), Timestamp=Release Date (AS4DATE)' },
    bdc: { name: 'BDC Session Log', icon: '🤖', tables: ['APQI', 'APQD', 'APQR'], status: 'connected', records: '3,241', domain: 'Configuration & Enhancements', desc: 'Batch input sessions reveal which transactions are automated, failure/retry patterns, and which screens are touched. Ideal for automation opportunity mining.', mapTo: 'Case=Session ID (GROUPID), Activity=Transaction Code (TCODE), Timestamp=Session Date (ERDAT)' },
    cdhdr: { name: 'Change Documents (CDHDR)', icon: '📋', tables: ['CDHDR', 'CDPOS'], status: 'available', records: '-', domain: 'Configuration & Enhancements', desc: 'Field-level change audit trail for master data (vendors, materials, cost centers, etc.) — reveals who changed what configuration and when.', mapTo: 'Case=Object ID (OBJECTID), Activity=Table/Field Changed, Timestamp=UDATE+UTIME' },
    fi: { name: 'FI Accounting Docs', icon: '💳', tables: ['BKPF', 'BSEG', 'BSID', 'BSAK'], status: 'available', records: '-', domain: 'Finance', desc: 'Financial document postings — P2P/O2C process mining from FI perspective', mapTo: 'Case=Document#, Activity=Posting Key, Timestamp=Posting Date' },
    fm: { name: 'Fund Management', icon: '💰', tables: ['FMFCTRT', 'FMIFIIT', 'FMBUBA', 'FMIT'], status: 'available', records: '-', domain: 'Public Sector (PSM)', desc: 'Budget commitments, fund transfers, and expenditure postings — full budget lifecycle. PSM: Fund Center = organizational budget owner.', mapTo: 'Case=Funds Center, Activity=FM Category, Timestamp=Posting Date' },
    costcenter: { name: 'Cost Center Accounting', icon: '🏢', tables: ['CSKS', 'CSKT', 'COSS', 'COSP', 'COEP'], status: 'available', records: '-', domain: 'Controlling (CO)', desc: 'Cost center plan vs actual postings — spend pattern mining per organizational unit. PSM: maps 1:1 to Fund Center hierarchy for budget vs actuals analysis.', mapTo: 'Case=Cost Center (KOSTL), Activity=Cost Element Group, Timestamp=Posting Period' },
    intorder: { name: 'Internal Orders (CO-OPA)', icon: '📋', tables: ['AUFK', 'AUFKV', 'COEP', 'RCOBJT'], status: 'available', records: '-', domain: 'Controlling (CO)', desc: 'Internal order lifecycle from creation to settlement — budget monitoring and project cost tracking. PSM: orders map to Grant/Budget Line items for expenditure control.', mapTo: 'Case=Order# (AUFNR), Activity=Order Status Change (STAT), Timestamp=Status Date' },
    wbs: { name: 'Project / WBS Elements', icon: '🗂️', tables: ['PROJ', 'PRPS', 'PRTE', 'PRHI', 'RPSCO'], status: 'available', records: '-', domain: 'Controlling (CO)', desc: 'Project structure and milestone lifecycle. PSM context: WBS Element ↔ Grant ↔ Sponsored Program. Enables project delivery and grant usage process mining.', mapTo: 'Case=WBS Element (POSID), Activity=Milestone / Network Status, Timestamp=Actual Date' },
    hr: { name: 'HR Personnel Actions', icon: '👥', tables: ['PA0000', 'PA0001', 'PA0002', 'T529A'], status: 'available', records: '-', domain: 'Human Resources', desc: 'Employee infotype action log — hire, transfer, promotion, termination sequences', mapTo: 'Case=PERNR, Activity=Action Type (MASSN), Timestamp=Begin Date' },
    travel: { name: 'Travel Management', icon: '✈️', tables: ['PTRV_HEAD', 'PTRV_SCOS', 'PTRV_DOC'], status: 'available', records: '-', domain: 'Travel', desc: 'Trip request to reimbursement — expense approval flow and payment processing', mapTo: 'Case=Trip#, Activity=Status Change, Timestamp=Status Date' },
    syslog: { name: 'System Log (SM21)', icon: '🖥️', tables: ['SM21', 'SYSLOG', 'MSGTXT'], status: 'available', records: '-', domain: 'System', desc: 'SAP system events, errors, and informational messages — operational health monitoring', mapTo: 'Case=Session ID, Activity=Message Class, Timestamp=Log Time' },
    joblog: { name: 'Background Jobs', icon: '⚙️', tables: ['SM37', 'TBTCO', 'TBTCS', 'TBTCP'], status: 'available', records: '-', domain: 'Operations', desc: 'Background job scheduling, execution, and failure — batch process optimization', mapTo: 'Case=Job Name, Activity=Step Status, Timestamp=Execution Time' },
    audit: { name: 'Security Audit Log', icon: '🔒', tables: ['SM20', 'RSAU_BUF_DATA', 'T000'], status: 'available', records: '-', domain: 'Security', desc: 'User access events, failed logins, authorization checks — compliance and security process mining', mapTo: 'Case=User ID, Activity=Audit Event, Timestamp=Log Time' },
    enhancement: { name: 'Enhancements / BADI / ENHO', icon: '🔧', tables: ['ENHMEM', 'ENHLOG', 'SE20', 'SXS_INTER'], status: 'connected', records: '347', domain: 'Configuration & Enhancements', desc: 'Enhancement implementation lifecycle — from SE20 implementation to transport to activation. Reveals which standard SAP processes have been extended and how.', mapTo: 'Case=Enhancement Name (ENHNAME), Activity=Lifecycle Step, Timestamp=Change Date (CHNGDATE)' },
    workflow: { name: 'Workflow Instances', icon: '🔄', tables: ['SWEL', 'SWI2', 'SWI5', 'SWW_CONTOB'], status: 'available', records: '-', domain: 'Configuration & Enhancements', desc: 'SAP Workflow execution — approval chains, agent assignments, escalation patterns, and SLA tracking across all business processes.', mapTo: 'Case=Work Item ID (WIID), Activity=Task Name (TASK_TEXT), Timestamp=Changed At (CHANGED_AT)' }
};

function switchView(v) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.view === v));
    document.querySelectorAll('.view').forEach(el => el.classList.toggle('active', el.id === 'view-' + v));
    if (v === 'analyze' && globalResult) setTimeout(() => { MapRenderer.init(); MapRenderer.render(globalResult, globalKey); }, 100);
    if (v === 'operate' && globalResult && !chart_trend) renderOperateCharts();
    if (v === 'design' && globalResult) renderDesignView();
    if (v === 'implement' && globalResult) renderImplementView();
    if (v === 'insights' && globalResult) renderInsights();
    if (v === 'sources') renderSourcesView();
}

function loadSample(key) {
    if (!SAMPLES[key]) key = 'p2p';
    globalKey = key;
    document.getElementById('map-loading').style.display = 'flex';
    document.getElementById('conf-arc') && (document.getElementById('conf-arc').setAttribute('stroke-dashoffset', '138'));
    setTimeout(() => {
        globalResult = Engine.load(key);
        const s = SAMPLES[key];
        document.getElementById('breadcrumb-process').textContent = s.name;
        document.getElementById('upload-zone').style.display = 'none';
        renderDiscoverKPIs(globalResult, key);
        renderProcessList(globalResult, key);
        renderVariants(globalResult);
        renderAnalyzeConformance(globalResult);
        renderImplementStats(globalResult, key);
        // Reset charts on new load
        if (chart_trend) { chart_trend.destroy(); chart_trend = null; }
        if (chart_brs) { chart_brs.destroy(); chart_brs = null; }
        if (chart_asIsToBe) { chart_asIsToBe.destroy(); chart_asIsToBe = null; }
        document.getElementById('map-loading').style.display = 'none';
        document.getElementById('map-status').textContent = `${globalResult.nodes.length} activities · ${globalResult.edges.length} flows · ${globalResult.totalCases} cases`;
    }, 300);
}

function handleFileUpload(e) {
    const f = e.target.files[0]; if (!f) return;
    const reader = new FileReader();
    reader.onload = ev => {
        document.getElementById('map-loading').style.display = 'flex';
        setTimeout(() => {
            globalResult = Engine.loadCSV(ev.target.result);
            globalKey = 'custom';
            document.getElementById('breadcrumb-process').textContent = 'Custom Process';
            document.getElementById('upload-zone').style.display = 'none';
            renderDiscoverKPIs(globalResult, 'custom');
            renderVariants(globalResult);
            renderAnalyzeConformance(globalResult);
            document.getElementById('map-loading').style.display = 'none';
        }, 200);
    };
    reader.readAsText(f);
}

function showUpload() { document.getElementById('upload-zone').style.display = 'block'; document.getElementById('upload-zone').scrollIntoView({ behavior: 'smooth' }); }

function renderDiscoverKPIs(r, key) {
    const s = SAMPLES[key];
    document.getElementById('discover-kpis').innerHTML = `
    <div class="kpi-card"><div class="kpi-label">Total Cases</div><div class="kpi-value">${r.totalCases.toLocaleString()}</div><div class="kpi-trend up">↑ 12% vs prior period</div><div class="kpi-bar"><div class="kpi-bar-fill" style="width:${Math.min(r.totalCases / 600 * 100, 100)}%;background:#1B6EF3"></div></div></div>
    <div class="kpi-card"><div class="kpi-label">Median Cycle Time</div><div class="kpi-value">${r.medianCycle.toFixed(1)}<span>days</span></div><div class="kpi-trend ${r.medianCycle > 15 ? 'down' : 'up'}">${r.medianCycle > 15 ? '⚠ Above target' : '✓ On track'}</div><div class="kpi-bar"><div class="kpi-bar-fill" style="width:${Math.min(r.medianCycle / 30 * 100, 100)}%;background:#00875a"></div></div></div>
    <div class="kpi-card"><div class="kpi-label">Conformance Rate</div><div class="kpi-value">${r.conformance}<span>%</span></div><div class="kpi-trend ${r.conformance > 75 ? 'up' : 'down'}">${r.conformance > 75 ? '✓ On track' : '⚠ Below target'}</div><div class="kpi-bar"><div class="kpi-bar-fill" style="width:${r.conformance}%;background:${r.conformance > 75 ? '#00875a' : '#ff8b00'}"></div></div></div>
    <div class="kpi-card"><div class="kpi-label">Rework Rate</div><div class="kpi-value">${r.reworkRate}<span>%</span></div><div class="kpi-trend ${r.reworkRate > 20 ? 'down' : 'neutral'}">${r.reworkRate}% of cases loop</div><div class="kpi-bar"><div class="kpi-bar-fill" style="width:${r.reworkRate}%;background:${r.reworkRate > 20 ? '#de350b' : '#6554c0'}"></div></div></div>`;
}

function renderProcessList(r, key) {
    const allKeys = ['p2p', 'o2c', 'incident', 'fm', 'hr', 'travel'];
    const list = document.getElementById('process-list');
    list.innerHTML = allKeys.map(k => {
        const s = SAMPLES[k];
        const brs = s.brs; const color = brs >= 85 ? '#00875a' : brs >= 65 ? '#ff8b00' : '#de350b';
        const steps = s.targetFlow.slice(0, 5); const stepHtml = steps.map(st => `<div class="chevron-step">${st.length > 10 ? st.substring(0, 9) + '…' : st}</div>`).join('');
        const cases = k === key ? r.totalCases : s.activities.length * 50;
        return `<div class="process-tile ${k === key ? 'selected' : ''}" onclick="loadSample('${k}');document.getElementById('breadcrumb-process').textContent='${s.name}'">
      <div class="process-icon" style="background:${s.bg}">${s.icon}</div>
      <div class="process-chevron">${stepHtml}</div>
      <div class="process-info">
        <div class="process-name">${s.name}</div>
        <div class="process-cases">${cases.toLocaleString()} cases · <span style="font-size:10px;color:#9e9e9e">${s.sapSources.slice(0, 3).join(', ')}</span></div>
      </div>
      <div class="brs-container">
        <div class="brs-label">Best-Run Score</div>
        <div style="position:relative;margin:4px 0">
          <div class="brs-bar-wrap"><div class="brs-marker" style="left:${brs}%"></div></div>
        </div>
        <div style="display:flex;justify-content:space-between">
          <span style="font-size:9px;color:#bdbdbd">0</span>
          <div class="brs-score" style="color:${color};font-size:14px;font-weight:800">${brs}%</div>
          <span style="font-size:9px;color:#bdbdbd">100</span>
        </div>
      </div></div>`;
    }).join('');
}

function renderVariants(r) {
    const total = r.totalCases;
    document.getElementById('variant-count').textContent = r.variantList.length + ' found';
    document.getElementById('variant-list').innerHTML = r.variantList.slice(0, 20).map((v, i) => {
        const pct = Math.round(v.count / total * 100);
        const tags = v.trace.map(t => `<span class="vtag">${t.length > 9 ? t.substring(0, 8) + '…' : t}</span>`).join('');
        return `<div class="variant-item ${i === 0 ? 'active' : ''}" onclick="selectVariant(this,${i})">
      <div class="variant-rank">VARIANT ${i + 1} ${i === 0 ? '<span style="color:#00875a">✓ HAPPY PATH</span>' : i < 3 ? '<span style="color:#ff8b00">⚠ COMMON</span>' : '<span style="color:#bdbdbd">RARE</span>'}</div>
      <div class="variant-trace">${tags}</div>
      <div class="variant-meta"><span>${v.count} cases (<strong>${pct}%</strong>)</span><span>${v.trace.length} steps</span></div>
      <div class="kpi-bar" style="margin-top:6px"><div class="kpi-bar-fill" style="width:${pct}%;background:${i === 0 ? '#00875a' : i < 3 ? '#ff8b00' : '#bdbdbd'}"></div></div>
    </div>`;
    }).join('');
}

function selectVariant(el, i) {
    document.querySelectorAll('.variant-item').forEach(e => e.classList.remove('active'));
    el.classList.add('active');
    if (globalResult && globalResult.variantList[i]) MapRenderer.highlightVariant(globalResult.variantList[i].trace);
}

function renderAnalyzeConformance(r) {
    const pct = r.conformance;
    const circ = 2 * Math.PI * 22; const offset = circ * (1 - pct / 100);
    const arc = document.getElementById('conf-arc');
    if (arc) { arc.setAttribute('stroke-dashoffset', offset.toFixed(1)); arc.setAttribute('stroke', pct >= 75 ? '#00875a' : pct >= 50 ? '#ff8b00' : '#de350b'); }
    const scoreEl = document.getElementById('conf-score-txt'); if (scoreEl) scoreEl.textContent = pct + '%';
    const subEl = document.getElementById('conf-sub-txt'); if (subEl) subEl.textContent = `${pct}% conform · Median ${r.medianCycle.toFixed(1)}d · P90 ${r.p90Cycle.toFixed(1)}d · ${r.reworkRate}% rework`;
    const nameEl = document.getElementById('conf-process-name'); if (nameEl) nameEl.textContent = SAMPLES[globalKey] ? SAMPLES[globalKey].name : 'Custom Process';
}

function setFreqMode(mode) {
    MapRenderer.setMode(mode);
    if (globalResult) MapRenderer._doRender(globalResult, globalKey);
    document.querySelectorAll('.filter-chip').forEach(e => e.classList.toggle('active', e.textContent.toLowerCase().includes(mode.substring(0, 4))));
}
function zoomIn() { MapRenderer.zoomIn(); } function zoomOut() { MapRenderer.zoomOut(); } function fitView() { MapRenderer.fitView(); }
function resetHighlight() { MapRenderer.highlightVariant(null); }

function renderImplementStats(r, key) {
    const s = SAMPLES[key];
    document.getElementById('impl-title').textContent = (s ? s.icon + ' ' + s.name : 'Custom Process') + ' — Transformation Initiative';
    document.getElementById('impl-cases').textContent = r.totalCases.toLocaleString();
    document.getElementById('impl-variants').textContent = r.variantList.length;
    document.getElementById('impl-conf').textContent = r.conformance + '%';
    document.getElementById('impl-saving').textContent = Math.round(r.medianCycle * 0.2) + 'd';
    switchPhaseTab(document.querySelector('.phase-tab'), 'gaps');
}

function switchPhaseTab(el, tab) {
    document.querySelectorAll('.phase-tab').forEach(e => e.classList.remove('active'));
    if (el) el.classList.add('active');
    const cont = document.getElementById('impl-tab-content');
    if (tab === 'gaps') cont.innerHTML = renderGapsTable();
    else if (tab === 'automation') cont.innerHTML = renderAutomationTable();
    else cont.innerHTML = renderSAPConfigTable();
}

function renderGapsTable() {
    if (!globalResult) return '<p style="padding:20px;color:#9e9e9e">Load a process first</p>';
    const rows = globalResult.variantList.slice(1, 8).map((v, i) => `<tr><td>${i + 2}</td><td style="max-width:300px;font-size:11px">${v.trace.join(' → ').substring(0, 60)}…</td><td>${v.count}</td><td><span class="badge ${i < 2 ? 'red' : i < 5 ? 'orange' : 'blue'}">${i < 2 ? 'High' : i < 5 ? 'Medium' : 'Low'}</span></td><td><span class="badge ${i === 0 ? 'orange' : 'green'}">${i === 0 ? 'In Progress' : 'Planned'}</span></td></tr>`).join('');
    return `<table class="gap-table"><thead><tr><th>#</th><th>Process Variant / Gap</th><th>Cases</th><th>Priority</th><th>Status</th></tr></thead><tbody>${rows}</tbody></table>`;
}
function renderAutomationTable() {
    const s = SAMPLES[globalKey]; const acts = (s ? s.activities : ['Activity 1', 'Activity 2']);
    return `<table class="gap-table"><thead><tr><th>Activity</th><th>Occurrence</th><th>Type</th><th>Effort</th><th>Cycle Save</th></tr></thead><tbody>${acts.slice(0, 5).map((a, i) => `<tr><td><strong>${a}</strong></td><td>${[98, 76, 65, 89, 45][i] || 60}%</td><td><span class="badge blue">${['RPA', 'Workflow', 'BPA', 'RPA', 'AI'][i] || 'RPA'}</span></td><td><span class="badge ${i % 2 === 0 ? 'green' : 'orange'}">${i % 2 === 0 ? 'Low' : 'Medium'}</span></td><td><strong>${[2, 3, 1, 1.5, 2.5][i] || 1}d</strong></td></tr>`).join('')}</tbody></table>`;
}
function renderSAPConfigTable() {
    const rows = [{ area: 'Approval Thresholds', cur: '€500 auto', tgt: '€5,000 auto', impact: 'green' }, { area: 'Duplicate Check', cur: 'Manual', tgt: 'Auto MIRO', impact: 'green' }, { area: 'GR/IR Tolerance', cur: '0%', tgt: '3% auto-clear', impact: 'orange' }, { area: 'Partner Rules', cur: 'Manual', tgt: 'Rules-based', impact: 'blue' }];
    return `<table class="gap-table"><thead><tr><th>Config Area</th><th>Current State</th><th>Target State</th><th>Impact</th></tr></thead><tbody>${rows.map(r => `<tr><td><strong>${r.area}</strong></td><td>${r.cur}</td><td>${r.tgt}</td><td><span class="badge ${r.impact}">${r.impact === 'green' ? 'High' : r.impact === 'orange' ? 'Medium' : 'Low'}</span></td></tr>`).join('')}</tbody></table>`;
}

function renderDesignView() {
    const r = globalResult; if (!r) return;
    const opp = document.getElementById('design-opportunities');
    if (opp) opp.innerHTML = r.variantList.slice(1, 4).map((v, i) => `<div style="padding:10px;border-left:3px solid ${['#de350b', '#ff8b00', '#1B6EF3'][i]};margin-bottom:10px;background:${['#ffebe6', '#fff4e5', '#EBF2FF'][i]};border-radius:0 6px 6px 0"><div style="font-size:10px;font-weight:700;color:${['#de350b', '#ff8b00', '#1B6EF3'][i]}">${['🔴 CRITICAL GAP', '🟡 HIGH PRIORITY', '🔵 OPPORTUNITY'][i]}</div><div style="font-size:12px;font-weight:600;margin-top:3px">${v.trace.join(' → ').substring(0, 55)}…</div><div style="font-size:11px;color:#6b6b6b;margin-top:2px">${v.count} cases (${Math.round(v.count / r.totalCases * 100)}% of total)</div></div>`).join('');
    const svg = document.getElementById('tobe-svg');
    if (!svg || !SAMPLES[globalKey]) return;
    const target = SAMPLES[globalKey].targetFlow; const W = 900, H = 200, nw = 110, nh = 44, gap = 28;
    const totalW = target.length * (nw + gap) - gap; const sx = (W - totalW) / 2;
    let html = `<defs><marker id="tobe-arrow" viewBox="0 -5 10 10" refX="10" refY="0" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,-5L10,0L0,5" fill="#1B6EF3"/></marker></defs>`;
    target.forEach((act, i) => { const x = sx + i * (nw + gap), y = (H - nh) / 2; html += `<rect x="${x}" y="${y}" width="${nw}" height="${nh}" rx="8" fill="#FFFBEB" stroke="#f0c040" stroke-width="1.5"/><text x="${x + nw / 2}" y="${y + nh / 2 + 4}" text-anchor="middle" font-size="10" font-weight="600" fill="#1c1c1c">${act.length > 14 ? act.substring(0, 13) + '…' : act}</text>`; if (i < target.length - 1) html += `<line x1="${x + nw + 2}" y1="${H / 2}" x2="${x + nw + gap - 4}" y2="${H / 2}" stroke="#1B6EF3" stroke-width="1.5" marker-end="url(#tobe-arrow)"/>`; });
    svg.innerHTML = html;
    if (!chart_asIsToBe) { chart_asIsToBe = new Chart(document.getElementById('asIs-tobe-chart'), { type: 'bar', data: { labels: ['Cycle Time (d)', 'Variants', 'Rework %', 'Conformance %'], datasets: [{ label: 'As-Is', data: [r.medianCycle, Math.min(r.variantList.length, 50), r.reworkRate, r.conformance], backgroundColor: 'rgba(222,53,11,0.7)' }, { label: 'Target', data: [r.medianCycle * 0.7, 3, 5, 95], backgroundColor: 'rgba(0,135,90,0.7)' }] }, options: { responsive: true, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: true } } } }); }
}

function renderOperateCharts() {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const r = globalResult; const base = r ? r.medianCycle : 20;
    if (!chart_trend) chart_trend = new Chart(document.getElementById('trend-chart'), { type: 'line', data: { labels: months, datasets: [{ label: 'Cycle Time (days)', data: months.map((_, i) => +(base * (1 - i * 0.015 + Math.random() * 0.08)).toFixed(1)), borderColor: '#1B6EF3', backgroundColor: 'rgba(27,110,243,0.08)', tension: 0.4, fill: true }, { label: 'Target', data: months.map(() => +(base * 0.75).toFixed(1)), borderColor: '#00875a', borderDash: [5, 5], fill: false }] }, options: { responsive: true, plugins: { legend: { position: 'bottom' } }, scales: { y: { beginAtZero: false } } } });
    const scores = Object.values(SAMPLES).map(s => s.brs); const labels = Object.values(SAMPLES).map(s => s.name.split(' ')[0]);
    if (!chart_brs) chart_brs = new Chart(document.getElementById('brs-chart'), { type: 'radar', data: { labels, datasets: [{ label: 'Your Company', data: scores, backgroundColor: 'rgba(27,110,243,0.2)', borderColor: '#1B6EF3', pointBackgroundColor: '#1B6EF3' }, { label: 'Best in Class', data: scores.map(() => 95), backgroundColor: 'rgba(0,135,90,0.1)', borderColor: '#00875a', borderDash: [4, 4] }] }, options: { responsive: true, scales: { r: { min: 0, max: 100 } }, plugins: { legend: { position: 'bottom' } } } });
    renderCompanyGrid();
}

function renderCompanyGrid() {
    const areas = [
        { name: 'Purchase to Pay', icon: '🛒', kpi: globalResult ? globalResult.medianCycle.toFixed(1) + 'd' : '23d', label: 'Cycle Time', status: globalResult && globalResult.medianCycle < 20 ? 'green' : 'orange', onclick: "loadSample('p2p')" },
        { name: 'Order to Cash', icon: '📦', kpi: '93%', label: 'On-Time Delivery', status: 'green', onclick: "loadSample('o2c')" },
        { name: 'Fund Management', icon: '💰', kpi: '€2.3M', label: 'Budget Committed', status: 'orange', onclick: "loadSample('fm')" },
        { name: 'HR Actions', icon: '👥', kpi: '97%', label: 'Process Quality', status: 'green', onclick: "loadSample('hr')" },
        { name: 'Travel & Expense', icon: '✈️', kpi: '4.2d', label: 'Approval Time', status: 'orange', onclick: "loadSample('travel')" },
        { name: 'Incident Mgmt', icon: '🎫', kpi: globalResult && globalKey === 'incident' ? globalResult.conformance + '%' : '65%', label: 'SLA Compliance', status: 'orange', onclick: "loadSample('incident')" },
        { name: 'Finance Close', icon: '📊', kpi: '81%', label: 'Auto-Posting Rate', status: 'green', onclick: "loadSample('p2p')" },
        { name: 'CTS Changes', icon: '📦', kpi: '12.8K', label: 'Transports/Year', status: 'green', onclick: "switchView('sources')" },
        { name: 'BDC Automation', icon: '🤖', kpi: '3,241', label: 'Sessions Logged', status: 'green', onclick: "switchView('sources')" },
        { name: 'System Health', icon: '🖥️', kpi: '99.9%', label: 'Uptime', status: 'green', onclick: "switchView('sources')" }
    ];
    document.getElementById('company-grid').innerHTML = areas.map(a => `<div class="company-cell" onclick="${a.onclick};switchView('analyze')">
    <div class="company-cell-icon" style="background:${a.status === 'green' ? '#e3fcef' : a.status === 'orange' ? '#fff4e5' : '#ffebe6'}">${a.icon}</div>
    <div class="company-cell-name">${a.name}</div>
    <div class="company-cell-kpi">${a.kpi} <small>${a.label}</small></div>
    <div style="margin-top:6px"><span class="status-dot ${a.status}"></span><span style="font-size:10px;color:#6b6b6b">${a.status === 'green' ? 'On Track' : a.status === 'orange' ? 'Needs Attention' : 'Critical'}</span></div>
  </div>`).join('');
}

function renderSourcesView() {
    const el = document.getElementById('sources-list'); if (!el) return;
    const byDomain = {}; Object.values(SAP_SOURCES).forEach(s => { if (!byDomain[s.domain]) byDomain[s.domain] = []; byDomain[s.domain].push(s); });
    el.innerHTML = Object.entries(byDomain).map(([domain, srcs]) => `
    <div style="margin-bottom:20px">
      <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;color:#6b6b6b;padding:0 28px;margin-bottom:8px">${domain}</div>
      ${srcs.map(s => `<div class="insight-card" style="margin:0 28px 8px">
        <div class="insight-icon-wrap" style="background:${s.status === 'connected' ? '#e3fcef' : '#f1f3f4'}">${s.icon}</div>
        <div class="insight-content">
          <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
            <span class="insight-badge ${s.status === 'connected' ? 'opportunity' : 'info'}">${s.status === 'connected' ? '✓ CONNECTED' : 'AVAILABLE'}</span>
            <span style="font-size:9px;color:#9e9e9e;font-weight:600">${s.tables.join(' · ')}</span>
            ${s.status === 'connected' ? `<span style="font-size:10px;font-weight:700;color:#00875a;margin-left:auto">${s.records} records</span>` : ''}
          </div>
          <div class="insight-title">${s.name}</div>
          <div class="insight-desc">${s.desc}</div>
          <div style="margin-top:8px;padding:6px 10px;background:#f8f9fa;border-radius:6px;font-size:10px;color:#6b6b6b">
            <strong style="color:#3c4043">Event Log Mapping:</strong> ${s.mapTo}
          </div>
          <div class="insight-actions" style="margin-top:8px">
            ${s.status === 'connected' ? `<button class="btn-sm btn-primary" onclick="mineFromSource('${Object.keys(SAP_SOURCES).find(k => SAP_SOURCES[k] === s)}')">Mine Process</button>` : ''}
            <button class="btn-sm btn-ghost">View Schema</button>
          </div>
        </div></div>`).join('')}
    </div>`).join('');
}

function mineFromSource(key) {
    const srcMap = { cts: 'p2p', bdc: 'incident', enhancement: 'incident', fi: 'p2p', fm: 'fm', hr: 'hr', travel: 'travel' };
    const sampleKey = srcMap[key] || 'p2p';
    loadSample(sampleKey);
    switchView('analyze');
}

function renderInsights() {
    const r = globalResult; if (!r) return;
    const topActivity = r.nodes.sort((a, b) => b.avgDurHours - a.avgDurHours)[0];
    const insights = [
        { type: 'critical', icon: '🔴', title: `Bottleneck: "${topActivity?.id || 'Activity'}" takes ${fmtHours(topActivity?.avgDurHours || 0)} on average`, desc: `This activity accounts for ${((topActivity?.avgDurHours || 0) / Math.max(r.medianCycle * 24, 1) * 100).toFixed(0)}% of total cycle time. ${Math.round((topActivity?.avgDurHours || 0) * 0.6)} hours could be saved per case through automation or parallel processing.`, actions: ['Analyze Root Cause', 'Create Improvement Task'] },
        { type: 'warning', icon: '🟡', title: `Rework Alert: ${r.reworkRate}% of cases contain loops (${Math.round(r.reworkRate / 100 * r.totalCases)} cases)`, desc: `Repeated activities indicate data quality issues or missing guardrails. In ${SAMPLES[globalKey]?.name || 'this process'}, the most common loop is in ${r.nodes.sort((a, b) => b.count - a.count)[0]?.id || 'the first activity'}.`, actions: ['View Affected Cases', 'Add Validation Rule'] },
        { type: 'info', icon: '🔵', title: `${r.variantList.length} variants found — top 3 cover ${Math.min(99, Math.round(r.variantList.slice(0, 3).reduce((s, v) => s + v.count, 0) / r.totalCases * 100))}% of cases`, desc: `Harmonizing to the top 3 variants could reduce training costs, errors, and system complexity by approximately 30%. ${r.variantList.length > 10 ? 'There are ' + r.variantList.slice(10).reduce((s, v) => s + v.count, 0) + ' cases in rare variants worth investigating.' : ''}`, actions: ['View Variants', 'Design Target Process'] },
        { type: 'opportunity', icon: '🟢', title: `Automation: ${r.nodes.filter(n => n.count / r.totalCases > 0.85).length} activities appear in >85% of cases`, desc: `High-frequency, low-variation activities are prime RPA candidates. Automating these in ${SAMPLES[globalKey]?.name || 'this process'} could save ${Math.round(r.medianCycle * 0.2)} days per case and reduce headcount requirements.`, actions: ['See Automation Plan', 'Estimate ROI'] },
        { type: 'info', icon: '📊', title: `SAP Data Sources: ${Object.values(SAP_SOURCES).filter(s => s.status === 'connected').length} connected, ${Object.values(SAP_SOURCES).filter(s => s.status === 'available').length} available`, desc: `You have ${Object.values(SAP_SOURCES).filter(s => s.status === 'available').length} additional SAP data sources available for process mining including System Logs (SM21), Background Jobs (SM37), Security Audit (SM20), and Workflow Instances (SWI2).`, actions: ['View Data Sources', 'Connect New Source'] }
    ];
    document.getElementById('insights-container').innerHTML = insights.map(ins => `<div class="insight-card">
    <div class="insight-icon-wrap" style="background:${ins.type === 'critical' ? '#ffebe6' : ins.type === 'warning' ? '#fff4e5' : ins.type === 'opportunity' ? '#e3fcef' : '#EBF2FF'}">${ins.icon}</div>
    <div class="insight-content">
      <span class="insight-badge ${ins.type}">${ins.type.toUpperCase()}</span>
      <div class="insight-title">${ins.title}</div>
      <div class="insight-desc">${ins.desc}</div>
      <div class="insight-actions">${ins.actions.map(a => `<button class="btn-sm btn-primary">${a}</button>`).join('')}</div>
    </div></div>`).join('');
}

// INIT
document.addEventListener('DOMContentLoaded', () => {
    MapRenderer.init();
    loadSample('p2p');
    setTimeout(() => switchView('discover'), 100);
});
