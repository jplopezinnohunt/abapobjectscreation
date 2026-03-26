// SAMPLE DATA — ALL DOMAINS (P2P, O2C, Incident, Fund Management, HR, Travel)
const SAMPLES = {
    p2p: {
        name: 'Purchase to Pay', icon: '🛒', color: '#1B6EF3', bg: '#EBF2FF',
        activities: ['Create PR', 'Approve PR', 'Create PO', 'Approve PO', 'Goods Receipt', 'Invoice Receipt', 'Invoice Verification', 'Payment'],
        targetFlow: ['Create PR', 'Approve PR', 'Create PO', 'Approve PO', 'Goods Receipt', 'Invoice Receipt', 'Invoice Verification', 'Payment'],
        baseTime: [1, 2, 3, 1, 5, 3, 2, 2], brs: 72,
        sapSources: ['EKKO', 'EKPO', 'EINE', 'EBAN', 'MIGO', 'MIRO', 'T156', 'RBKP'],
        desc: 'Full P2P cycle from purchase request to vendor payment'
    },
    o2c: {
        name: 'Order to Cash', icon: '📦', color: '#00875a', bg: '#e3fcef',
        activities: ['Create Order', 'Credit Check', 'Pick Goods', 'Ship Goods', 'Invoice Customer', 'Payment Received', 'Close Order'],
        targetFlow: ['Create Order', 'Credit Check', 'Pick Goods', 'Ship Goods', 'Invoice Customer', 'Payment Received', 'Close Order'],
        baseTime: [0.5, 1, 2, 3, 1, 7, 0.1], brs: 88,
        sapSources: ['VBAK', 'VBAP', 'VBFA', 'LIKP', 'LIPS', 'VBRK', 'VBRP', 'BSID'],
        desc: 'Sales order lifecycle from creation to cash collection'
    },
    incident: {
        name: 'Incident Management', icon: '🎫', color: '#6554c0', bg: '#ede8ff',
        activities: ['Open Ticket', 'Classify', 'Assign L1', 'Resolve L1', 'Escalate L2', 'Resolve L2', 'Close'],
        targetFlow: ['Open Ticket', 'Classify', 'Assign L1', 'Resolve L1', 'Close'],
        baseTime: [0.1, 0.5, 1, 1, 0.5, 2, 0.2], brs: 65,
        sapSources: ['SM37', 'SM20', 'SWEL', 'SWI2', 'SOST'],
        desc: 'IT helpdesk ticket lifecycle — classification to resolution'
    },
    // NEW: FUND MANAGEMENT (PSM)
    fm: {
        name: 'Fund Management', icon: '💰', color: '#00b8d9', bg: '#e6fcff',
        activities: ['Budget Request', 'Budget Approval', 'Commitment', 'Funds Check', 'Obligation', 'Expenditure', 'Close Period'],
        targetFlow: ['Budget Request', 'Budget Approval', 'Commitment', 'Funds Check', 'Obligation', 'Expenditure', 'Close Period'],
        baseTime: [2, 5, 1, 0.5, 1, 3, 1], brs: 79,
        sapSources: ['FMFCTRT', 'FMIFIIT', 'FMBUBA', 'FMZUOB', 'BPDY', 'FMFINCODE', 'FMIT', 'FIFM'],
        desc: 'Public sector budget lifecycle — from request to expenditure (PSM/FM)'
    },
    // NEW: HR (Hire to Retire - Personnel Actions)
    hr: {
        name: 'Hire to Retire', icon: '👥', color: '#ff8b00', bg: '#fff4e5',
        activities: ['Job Posting', 'Application', 'Interview', 'Hire Decision', 'Onboarding', 'IT Provisioning', 'Payroll Active'],
        targetFlow: ['Job Posting', 'Application', 'Interview', 'Hire Decision', 'Onboarding', 'IT Provisioning', 'Payroll Active'],
        baseTime: [5, 3, 7, 2, 10, 2, 1], brs: 82,
        sapSources: ['PA0000', 'PA0001', 'PA0002', 'PA0105', 'T529A', 'PERNR', 'T513', 'PTEX2010'],
        desc: 'HR personnel action lifecycle — recruitment to active payroll'
    },
    // NEW: TRAVEL MANAGEMENT
    travel: {
        name: 'Travel & Expense', icon: '✈️', color: '#de350b', bg: '#ffebe6',
        activities: ['Create Trip Request', 'Manager Approval', 'Book Travel', 'Submit Expense', 'Finance Review', 'Pay Reimbursement'],
        targetFlow: ['Create Trip Request', 'Manager Approval', 'Book Travel', 'Submit Expense', 'Finance Review', 'Pay Reimbursement'],
        baseTime: [0.5, 1, 1, 2, 3, 1], brs: 71,
        sapSources: ['PTRV_HEAD', 'PTRV_PERIO', 'PTRV_SCOS', 'PTRV_COST', 'PTRV_DOC', 'FI_TRAVEL', 'T702N', 'HRPY_RGDIR'],
        desc: 'End-to-end travel management — trip request to reimbursement payment'
    }
};

function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; } }

function buildTrace(acts, base, key, rng) {
    const trace = [];
    for (let i = 0; i < acts.length; i++) {
        const a = acts[i]; const prob = rng();
        trace.push({ act: a, hours: (base[i] || 1) * 24 * (0.5 + rng()) });
        // Domain-specific rework / loops
        if (key === 'p2p' && a === 'Approve PO' && prob < 0.15) trace.push({ act: a, hours: base[i] * 24 * 0.5 });
        if (key === 'incident' && a === 'Assign L1' && prob < 0.2) trace.push({ act: a, hours: base[i] * 24 * 0.4 });
        if (key === 'incident' && a === 'Resolve L1' && prob < 0.25) { trace.push({ act: 'Escalate L2', hours: 4 }); trace.push({ act: 'Resolve L2', hours: base[5] * 24 * (0.5 + rng()) }); }
        if (key === 'fm' && a === 'Funds Check' && prob < 0.3) trace.push({ act: a, hours: base[i] * 24 * 0.6 }); // budget re-check
        if (key === 'hr' && a === 'Interview' && prob < 0.4) trace.push({ act: a, hours: base[i] * 24 * 0.5 }); // multiple interviews
        if (key === 'travel' && a === 'Finance Review' && prob < 0.25) trace.push({ act: 'Submit Expense', hours: base[3] * 24 }); // resubmission
    }
    return trace;
}

function generateEvents(key, n) {
    const s = SAMPLES[key]; const rng = mulberry32(42);
    const events = []; const start0 = new Date('2024-01-01').getTime();
    for (let i = 0; i < n; i++) {
        const cid = key.toUpperCase() + '-' + (1000 + i);
        let t = new Date(start0 + rng() * 31536000000);
        const trace = buildTrace(s.activities, s.baseTime, key, rng);
        for (const step of trace) { t = new Date(t.getTime() + step.hours * 3600000); events.push({ caseId: cid, activity: step.act, timestamp: t.toISOString() }); }
    }
    return events;
}

function isSubsequence(target, actual) { let i = 0; for (const a of actual) { if (i < target.length && a === target[i]) i++; } return i >= target.length; }

// MINING ENGINE
const Engine = {
    eventLog: [], currentKey: null,
    load(key) {
        this.currentKey = key;
        const counts = { p2p: 500, o2c: 300, incident: 400, fm: 250, hr: 180, travel: 350 };
        this.eventLog = generateEvents(key, counts[key] || 300);
        return this.mine();
    },
    loadCSV(csvText) {
        const res = Papa.parse(csvText, { header: true, skipEmptyLines: true });
        const cols = res.meta.fields || [];
        const cc = cols.find(c => /case|id/i.test(c)) || cols[0];
        const ac = cols.find(c => /activ|step|event/i.test(c)) || cols[1];
        const tc = cols.find(c => /time|date|stamp/i.test(c)) || cols[2];
        this.eventLog = res.data.map(r => ({ caseId: r[cc] || '', activity: (r[ac] || '').trim(), timestamp: r[tc] || new Date().toISOString() })).filter(e => e.caseId && e.activity);
        this.currentKey = 'custom'; return this.mine();
    },
    mine() {
        const log = this.eventLog;
        const cases = {};
        log.forEach(e => { if (!cases[e.caseId]) cases[e.caseId] = []; cases[e.caseId].push(e); });
        Object.values(cases).forEach(evs => evs.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp)));
        const dfgFreq = {}, dfgDur = {}, actFreq = {}, actDur = {}, variants = {};
        const caseList = [];
        Object.entries(cases).forEach(([cid, evs]) => {
            const acts = evs.map(e => e.activity);
            variants[acts.join('›')] = (variants[acts.join('›')] || 0) + 1;
            const cycleDays = (new Date(evs[evs.length - 1].timestamp) - new Date(evs[0].timestamp)) / 86400000;
            caseList.push({ id: cid, acts, startDate: evs[0].timestamp, endDate: evs[evs.length - 1].timestamp, cycleDays });
            acts.forEach((a, i) => {
                actFreq[a] = (actFreq[a] || 0) + 1;
                if (i > 0) { const k = acts[i - 1] + '→' + a; dfgFreq[k] = (dfgFreq[k] || 0) + 1; const dur = (new Date(evs[i].timestamp) - new Date(evs[i - 1].timestamp)) / 3600000; dfgDur[k] = (dfgDur[k] || 0) + dur; actDur[a] = (actDur[a] || 0) + dur; }
            });
        });
        const nodes = Object.entries(actFreq).map(([id, count]) => ({ id, count, avgDurHours: (actDur[id] || 0) / count }));
        const edges = Object.entries(dfgFreq).map(([k, count]) => { const [src, tgt] = k.split('→'); return { src, tgt, count, avgHours: (dfgDur[k] || 0) / count }; });
        const variantList = Object.entries(variants).map(([trace, count]) => ({ trace: trace.split('›'), count })).sort((a, b) => b.count - a.count);
        const cycleTimes = caseList.map(c => c.cycleDays).sort((a, b) => a - b);
        const median = cycleTimes[Math.floor(cycleTimes.length / 2)] || 0;
        const p90 = cycleTimes[Math.floor(cycleTimes.length * 0.9)] || 0;
        const target = this.currentKey && SAMPLES[this.currentKey] ? SAMPLES[this.currentKey].targetFlow : null;
        let confRate = 70;
        if (target && caseList.length) { const conformCases = caseList.filter(c => isSubsequence(target, c.acts)).length; confRate = Math.round(conformCases / caseList.length * 100); }
        const reworkCases = caseList.filter(c => { const seen = new Set(); for (const a of c.acts) { if (seen.has(a)) return true; seen.add(a); } return false; }).length;
        return { nodes, edges, variantList, caseList, totalCases: caseList.length, medianCycle: median, p90Cycle: p90, conformance: confRate, reworkRate: Math.round(reworkCases / caseList.length * 100), avgActivities: Math.round(log.length / caseList.length * 10) / 10, actFreq, actDur };
    }
};
