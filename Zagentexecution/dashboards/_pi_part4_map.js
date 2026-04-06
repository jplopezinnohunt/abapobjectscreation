// D3 PROCESS MAP RENDERER
const MapRenderer = {
    svg: null, g: null, zoom: null, currentMode: 'frequency', activeVariant: null,

    init() {
        const el = document.getElementById('dfg-svg');
        const w = el.parentElement.clientWidth || 900;
        const h = el.parentElement.clientHeight || 600;
        this.svg = d3.select('#dfg-svg').attr('width', w).attr('height', h);
        this.g = this.svg.append('g').attr('class', 'graph-layer');
        this.zoom = d3.zoom().scaleExtent([0.2, 4]).on('zoom', e => this.g.attr('transform', e.transform));
        this.svg.call(this.zoom);
        // arrowhead marker
        this.svg.append('defs').append('marker').attr('id', 'arrow').attr('viewBox', '0 -5 10 10').attr('refX', 22).attr('refY', 0).attr('markerWidth', 6).attr('markerHeight', 6).attr('orient', 'auto').append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', '#1B6EF3').attr('fill-opacity', 0.5);
        this.svg.append('defs').append('marker').attr('id', 'arrow-slow').attr('viewBox', '0 -5 10 10').attr('refX', 22).attr('refY', 0).attr('markerWidth', 6).attr('markerHeight', 6).attr('orient', 'auto').append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', '#ff8b00').attr('fill-opacity', 0.7);
        this.svg.append('defs').append('marker').attr('id', 'arrow-bad').attr('viewBox', '0 -5 10 10').attr('refX', 22).attr('refY', 0).attr('markerWidth', 6).attr('markerHeight', 6).attr('orient', 'auto').append('path').attr('d', 'M0,-5L10,0L0,5').attr('fill', '#de350b').attr('fill-opacity', 0.8);
    },

    render(mineResult, sampleKey) {
        document.getElementById('map-loading').style.display = 'flex';
        setTimeout(() => this._doRender(mineResult, sampleKey), 50);
    },

    _doRender(r, sampleKey) {
        this.g.selectAll('*').remove();
        const { nodes, edges } = r;
        const W = document.getElementById('dfg-svg').parentElement.clientWidth || 900;
        const H = document.getElementById('dfg-svg').parentElement.clientHeight || 600;
        const NW = 140, NH = 56;
        // Layered layout
        const pos = this._layout(nodes, edges, W, H, NW, NH);
        // Edge stats
        const maxEdge = Math.max(...edges.map(e => e.count), 1);
        const maxDur = Math.max(...edges.map(e => e.avgHours), 1);
        // Draw edges
        edges.forEach(e => {
            const s = pos[e.src], t = pos[e.tgt]; if (!s || !t) return;
            const x1 = s.x + NW / 2, y1 = s.y + NH / 2, x2 = t.x - NW / 2, y2 = t.y + NH / 2;
            const mid = (x1 + x2) / 2;
            const durRatio = e.avgHours / maxDur;
            let cls = '', marker = 'url(#arrow)';
            if (durRatio > 0.7) { cls = 'bottleneck'; marker = 'url(#arrow-bad)'; }
            else if (durRatio > 0.4) { cls = 'slow'; marker = 'url(#arrow-slow)'; }
            const strokeW = 1 + Math.round((e.count / maxEdge) * 6);
            const eg = this.g.append('g').attr('class', 'dfg-edge ' + cls);
            eg.append('path').attr('d', `M${x1},${y1} C${mid},${y1} ${mid},${y2} ${x2},${y2}`)
                .attr('stroke', durRatio > 0.7 ? '#de350b' : durRatio > 0.4 ? '#ff8b00' : '#1B6EF3')
                .attr('stroke-width', strokeW).attr('stroke-opacity', 0.45).attr('fill', 'none')
                .attr('marker-end', marker);
            const lx = (x1 + x2) / 2, ly = (y1 + y2) / 2 - 6;
            const label = this.currentMode === 'frequency' ? e.count + '×' : fmtHours(e.avgHours);
            eg.append('text').attr('class', 'edge-label').attr('x', lx).attr('y', ly).attr('text-anchor', 'middle').attr('font-size', '9').attr('fill', '#6b6b6b').text(label);
        });
        // Draw nodes
        const sample = sampleKey && SAMPLES[sampleKey] ? SAMPLES[sampleKey] : null;
        const maxFreq = Math.max(...nodes.map(n => n.count), 1);
        nodes.forEach(n => {
            const p = pos[n.id]; if (!p) return;
            const isStart = sample && n.id === sample.targetFlow[0];
            const isEnd = sample && n.id === sample.targetFlow[sample.targetFlow.length - 1];
            const ng = this.g.append('g').attr('class', 'dfg-node' + (isStart ? ' start' : isEnd ? ' end' : '')).attr('transform', `translate(${p.x},${p.y})`).style('cursor', 'pointer');
            const fill = isStart ? '#e3fcef' : isEnd ? '#ffebe6' : n.count / maxFreq > 0.7 ? '#EBF2FF' : '#ffffff';
            const stroke = isStart ? '#00875a' : isEnd ? '#de350b' : '#dadce0';
            ng.append('rect').attr('width', NW).attr('height', NH).attr('rx', 8).attr('fill', fill).attr('stroke', stroke).attr('stroke-width', 1.5).style('filter', 'drop-shadow(0 2px 4px rgba(0,0,0,0.08))');
            // Color accent bar
            const accentColor = isStart ? '#00875a' : isEnd ? '#de350b' : '#1B6EF3';
            ng.append('rect').attr('width', 4).attr('height', NH).attr('rx', 2).attr('fill', accentColor).attr('opacity', 0.7);
            // freq bar
            const bw = (n.count / maxFreq) * (NW - 20);
            ng.append('rect').attr('x', 10).attr('y', NH - 6).attr('width', bw).attr('height', 3).attr('rx', 1.5).attr('fill', accentColor).attr('opacity', 0.3);
            // Text
            const label = n.id.length > 16 ? n.id.substring(0, 14) + '…' : n.id;
            ng.append('text').attr('x', NW / 2 + 2).attr('y', 22).attr('text-anchor', 'middle').attr('font-size', '11').attr('font-weight', '600').attr('fill', '#1c1c1c').text(label);
            const sub = this.currentMode === 'frequency' ? n.count + ' cases' : fmtHours(n.avgDurHours);
            ng.append('text').attr('x', NW / 2 + 2).attr('y', 38).attr('text-anchor', 'middle').attr('font-size', '10').attr('fill', '#6b6b6b').text(sub);
            ng.on('click', () => this._onNodeClick(n, r));
            ng.on('mouseover', function () { d3.select(this).select('rect:first-child').attr('stroke', '#1B6EF3').attr('stroke-width', 2); });
            ng.on('mouseout', function () { d3.select(this).select('rect:first-child').attr('stroke', stroke).attr('stroke-width', 1.5); });
        });
        document.getElementById('map-loading').style.display = 'none';
        document.getElementById('map-status').textContent = `${nodes.length} activities · ${edges.length} flows · ${r.totalCases} cases`;
        this.fitView();
    },

    _layout(nodes, edges, W, H, NW, NH) {
        // Build adjacency maps
        const succ = {}; const pred = {};
        nodes.forEach(n => { succ[n.id] = []; pred[n.id] = []; });
        edges.forEach(e => {
            if (succ[e.src] && pred[e.tgt]) { succ[e.src].push(e.tgt); pred[e.tgt].push(e.src); }
        });
        // DFS topological sort (cycle-safe: skip already visited)
        const visited = new Set(); const topoOrder = [];
        const dfs = id => {
            if (visited.has(id)) return; visited.add(id);
            (succ[id] || []).forEach(t => dfs(t));
            topoOrder.unshift(id);
        };
        nodes.forEach(n => dfs(n.id));
        // Longest-path layer assignment (forward pass through topo order)
        const layers = {};
        topoOrder.forEach(id => {
            const maxPredLayer = (pred[id] || []).reduce((m, p) => Math.max(m, (layers[p] !== undefined ? layers[p] : -1) + 1), 0);
            layers[id] = maxPredLayer;
        });
        // Group by layer
        const byLayer = {};
        nodes.forEach(n => { const l = layers[n.id] || 0; if (!byLayer[l]) byLayer[l] = []; byLayer[l].push(n.id); });
        const maxLayer = Math.max(...Object.keys(byLayer).map(Number), 0);
        // Guarantee non-overlapping columns
        const hGap = Math.max(NW + 60, Math.min(NW + 100, (W - 80) / Math.max(maxLayer + 1, 1)));
        const pos = {};
        Object.entries(byLayer).forEach(([l, ids]) => {
            const x = 40 + parseInt(l) * hGap;
            const vPad = 28;
            const totalH = ids.length * NH + (ids.length - 1) * vPad;
            const startY = Math.max(20, (H - totalH) / 2);
            ids.forEach((id, i) => { pos[id] = { x, y: startY + i * (NH + vPad) }; });
        });
        return pos;
    },
    _onNodeClick(node, r) {
        const filtered = r.caseList.filter(c => c.acts.includes(node.id));
        document.getElementById('map-status').textContent = `Filtered: ${filtered.length} cases through "${node.id}"`;
    },

    highlightVariant(variant) {
        if (!variant) {
            this.g.selectAll('.dfg-node').style('opacity', 1);
            return;
        }
        this.g.selectAll('.dfg-node').each(function () {
            const label = d3.select(this).select('text').text();
            d3.select(this).style('opacity', variant.some(v => label && v.startsWith(label.replace('…', ''))) ? 1 : 0.18);
        });
    },

    setMode(mode) { this.currentMode = mode; },
    fitView() { this.svg.transition().duration(400).call(this.zoom.transform, d3.zoomIdentity.translate(20, 20).scale(0.88)); },
    zoomIn() { this.svg.transition().call(this.zoom.scaleBy, 1.3); },
    zoomOut() { this.svg.transition().call(this.zoom.scaleBy, 0.75); }
};


function fmtHours(h) { if (h < 1) return Math.round(h * 60) + 'm'; if (h < 24) return h.toFixed(1) + 'h'; return (h / 24).toFixed(1) + 'd'; }
