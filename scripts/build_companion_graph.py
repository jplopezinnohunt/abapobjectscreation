"""
build_companion_graph.py — Relate the companions as a KNOWLEDGE GRAPH, not a flat list.
=======================================================================================
Why: companions/companions.json is a flat catalogue. A companion that shares a domain,
an incident, or an SAP entity (BCM, GGB1, F110, AVC...) with another IS related — but
nothing captures that edge, so the companions are not usable AS knowledge. This builds
the relationship layer deterministically (CP-003: explainable, no embeddings):

  signal(companion) = domain ∪ keywords ∪ {INC-ids} ∪ {SAP vocabulary hits in the HTML}
  edge(a,b)         = weighted blend of Jaccard(signals) + shared-incident + shared-domain
                      (every edge records WHICH tokens it shares → traceable)

Outputs:
  companions/companion_graph.json   — nodes, weighted+explained edges, clusters, inventory
  prints a summary (orphans, top edges, clusters)

CLI:
  python scripts/build_companion_graph.py            # build + write graph + summary
  python scripts/build_companion_graph.py --threshold 0.14
  python scripts/build_companion_graph.py --write-related   # also inject `related` into companions.json
"""
import json, re, sys, argparse
from pathlib import Path
from itertools import combinations

ROOT = Path(__file__).parent.parent
COMP = ROOT / "companions"
REG = COMP / "companions.json"
OUT = COMP / "companion_graph.json"

# companions that are not content nodes (index / assembly source / generated views)
SKIP = {"unesco_sap_landing.html", "companion_graph_v1.html"}
SKIP_DIRS = {"bcm_structured_address_src"}

# curated SAP vocabulary — high-signal entities that mean two companions touch the same thing.
# (lowercased; word-ish boundary match). Kept explicit so every edge is explainable.
VOCAB = [
    "bcm", "f110", "dmee", "fbzp", "signatory", "payment", "house bank", "ebs", "mt940",
    "clearing", "treasury", "cash", "fmderive", "ggb1", "ggb0", "yrggbs00", "substitution",
    "validation", "derivation", "basu", "ybasubst", "xref", "ybseg", "ws90000003", "ws50100024",
    "avc", "fm-avc", "ps-avc", "budget", "fund", "fipex", "donor", "biennium", "wbs",
    "payroll", "wage type", "py-finance", "hcm", "travel", "busarea", "business area",
    "fx", "revaluation", "sapf100", "f.05", "closing", "period-end", "carry forward",
    "transport", "cts", "customizing", "upgrade", "spau", "rfc", "idoc", "sm59", "interface",
    "connectivity", "system", "landscape", "process mining", "p2p", "procure", "conformance",
    "okb9", "skb1", "skat", "bseg", "bsik", "bkpf", "fmifiit", "company code", "stem",
    "epiuse", "epi-use", "knowledge graph", "brain", "taxonomy", "maturity", "retro", "basis",
    "monitoring", "st22", "sm37", "audit", "dual control", "compliance",
]
INC_RE = re.compile(r"\bINC[-_]?0*\d{4,}\b", re.I)
TAG_RE = re.compile(r"<[^>]+>")

# inferred domains for companions not in companions.json (orphans)
ORPHAN_DOMAIN = {
    "bcm_signatory_companion.html": "finance",
    "inc_000011781_ubo_ritter.html": "finance",
    "model_maturity_dashboard.html": "general",
    "upgrade_history_measurement_v1.html": "transport",
}


def norm_inc(s):
    d = re.sub(r"\D", "", s)
    return "INC-" + d.zfill(9)


def text_of(p):
    try:
        raw = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return TAG_RE.sub(" ", raw)


def signals(name, txt, reg_entry):
    toks, incs, vocab = set(), set(), set()
    low = txt.lower()
    if reg_entry:
        if reg_entry.get("domain"):
            toks.add("dom:" + reg_entry["domain"])
        for k in reg_entry.get("keywords", []):
            kk = str(k).strip().lower()
            if len(kk) > 2:
                toks.add(kk)
    # entities from the rendered text
    for m in INC_RE.findall(txt):
        ni = norm_inc(m)
        incs.add(ni); toks.add(ni)
    for v in VOCAB:
        if v in low:
            vocab.add(v); toks.add(v)
    # filename-derived tokens (helps orphans with no keywords)
    for part in re.split(r"[_\-.]", name.replace(".html", "")):
        if len(part) > 2 and not part.isdigit():
            toks.add(part.lower())
    return toks, incs, vocab


def jaccard(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


CLUSTER_COLORS = ["#3aa0ff", "#6fd3a8", "#ffb454", "#c792ea", "#ff7a90", "#5ec6d6", "#e8c07d"]


def emit_html(graph, out_html):
    """Deterministic clustered layout → self-contained SVG knowledge map (no external libs)."""
    import math
    nodes = graph["nodes"]
    clusters = graph["clusters"]
    by_file = {n["file"]: i for i, n in enumerate(nodes)}
    cl_of = {}
    for ci, c in enumerate(clusters):
        for m in c["members"]:
            cl_of[m] = ci
    W, H, CX, CY = 1180, 800, 590, 410
    Rbig = 270
    C = len(clusters)
    pos = {}
    for ci, c in enumerate(clusters):
        ang = 2 * math.pi * ci / max(C, 1) - math.pi / 2
        ccx, ccy = CX + Rbig * math.cos(ang), CY + Rbig * math.sin(ang)
        m = len(c["members"])
        rr = 34 + 12 * m
        for j, name in enumerate(sorted(c["members"])):
            a = 2 * math.pi * j / max(m, 1)
            pos[name] = (ccx + (rr if m > 1 else 0) * math.cos(a),
                         ccy + (rr if m > 1 else 0) * math.sin(a))
    jn = []
    for n in nodes:
        x, y = pos.get(n["file"], (CX, CY))
        jn.append({"id": by_file[n["file"]], "t": n["title"], "f": n["file"],
                   "d": n["domain"], "c": cl_of.get(n["file"], 0),
                   "reg": n["registered"], "x": round(x, 1), "y": round(y, 1)})
    je = [{"a": by_file[e["a"]], "b": by_file[e["b"]], "w": e["weight"],
           "s": e["shared"][:6]} for e in graph["edges"]]
    legend = [{"i": ci, "label": c["label"], "size": c["size"],
               "color": CLUSTER_COLORS[ci % len(CLUSTER_COLORS)]} for ci, c in enumerate(clusters)]
    inv = graph["inventory"]
    data = json.dumps({"nodes": jn, "edges": je, "legend": legend, "inv": inv,
                       "stats": graph["stats"]}, ensure_ascii=False)
    html = _HTML_TEMPLATE.replace("/*DATA*/", data).replace("__W__", str(W)).replace("__H__", str(H))
    out_html.write_text(html, encoding="utf-8")


_HTML_TEMPLATE = r"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>UNESCO SAP — Companion Knowledge Map</title>
<style>
:root{--bg:#0e1726;--panel:#152033;--line:#27374f;--ink:#e8eef7;--mut:#9fb0c8;--dim:#6f819c;--accent:#3aa0ff}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.5 -apple-system,Segoe UI,Roboto,Arial,sans-serif}
.wrap{max-width:1240px;margin:0 auto;padding:22px}
.kick{color:var(--accent);font-weight:700;letter-spacing:.12em;text-transform:uppercase;font-size:11px}
h1{margin:6px 0 2px;font-size:24px}.sub{color:var(--mut);font-size:13px;max-width:95ch}
.bar{display:flex;gap:8px;flex-wrap:wrap;margin:12px 0}
.chip{background:#21314c;border:1px solid var(--line);color:var(--mut);border-radius:20px;padding:3px 11px;font-size:12px}
.stage{display:grid;grid-template-columns:1fr 320px;gap:14px;margin-top:10px}
@media(max-width:980px){.stage{grid-template-columns:1fr}}
.canvas{background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}
.side{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;font-size:13px;max-height:800px;overflow:auto}
.legend b{display:block;margin:0 0 6px;color:var(--ink)}
.leg{display:flex;align-items:center;gap:8px;margin:4px 0;cursor:pointer}
.dot{width:11px;height:11px;border-radius:50%}
.det h4{margin:14px 0 4px;font-size:13px;color:var(--accent)}
.rel{padding:4px 6px;border:1px solid var(--line);border-radius:6px;margin:4px 0;font-size:12px}
.rel .w{color:var(--dim);font-size:11px}
.tok{display:inline-block;background:#21314c;border:1px solid var(--line);border-radius:4px;padding:0 5px;font-size:10px;color:#8fc6ff;margin:1px}
.orph{color:#ffb454}.muted{color:var(--dim)}
text{font-family:inherit}
.nlabel{font-size:10px;fill:var(--mut);pointer-events:none}
circle.node{cursor:pointer;stroke:#0a1322;stroke-width:1.2}
line.edge{stroke:#3a4a66;stroke-opacity:.5}
footer{border-top:1px solid var(--line);margin-top:18px;padding-top:12px;color:var(--dim);font-size:12px}
</style></head><body><div class="wrap">
<div class="kick">UNESCO SAP Intelligence · Knowledge Graph</div>
<h1>Companion Knowledge Map</h1>
<div class="sub">Every companion as a NODE; an edge = a shared domain, incident, or SAP entity (deterministic IDF cosine — each edge lists the shared tokens, CP-003 traceable). Hover a node to see what it relates to and why. This is the relationship layer that turns a flat catalogue into knowledge.</div>
<div class="bar" id="bar"></div>
<div class="stage">
  <div class="canvas"><svg id="svg" viewBox="0 0 __W__ __H__" width="100%"></svg></div>
  <div class="side"><div class="legend" id="legend"></div><div class="det" id="det"><div class="muted">Hover or click a node…</div></div></div>
</div>
<footer>Generated by <code>scripts/build_companion_graph.py</code> from <code>companions/companion_graph.json</code>. Rebuild to refresh. The <code>related</code> edges are also written into <code>companions.json</code>.</footer>
</div>
<script>
const G=/*DATA*/;
const svg=document.getElementById('svg'),NS='http://www.w3.org/2000/svg';
const col=i=>(G.legend[i]||{}).color||'#888';
const adj={};G.nodes.forEach(n=>adj[n.id]=[]);
G.edges.forEach(e=>{adj[e.a].push(e);adj[e.b].push(e);});
function el(t,a){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;}
// edges
const eg=el('g',{});svg.appendChild(eg);
G.edges.forEach((e,i)=>{const a=G.nodes[e.a],b=G.nodes[e.b];
  const l=el('line',{class:'edge',x1:a.x,y1:a.y,x2:b.x,y2:b.y,'stroke-width':(0.5+e.w*3).toFixed(2),'data-e':i});eg.appendChild(l);e._l=l;});
// nodes
const ng=el('g',{});svg.appendChild(ng);
G.nodes.forEach(n=>{const r=8+adj[n.id].length*0.7;
  const c=el('circle',{class:'node',cx:n.x,cy:n.y,r:Math.min(r,16),fill:col(n.c),'data-n':n.id,opacity:n.reg?1:0.55});
  if(!n.reg)c.setAttribute('stroke','#ffb454'),c.setAttribute('stroke-width','2');
  ng.appendChild(c);n._c=c;
  const lab=el('text',{class:'nlabel',x:n.x,y:n.y-Math.min(r,16)-3,'text-anchor':'middle'});
  lab.textContent=n.t.length>22?n.t.slice(0,21)+'…':n.t;ng.appendChild(lab);
  c.addEventListener('mouseenter',()=>focus(n.id));
  c.addEventListener('click',()=>window.open(n.f.replace('companions/',''),'_blank'));});
function focus(id){
  const ne=adj[id],keep=new Set([id]);ne.forEach(e=>{keep.add(e.a);keep.add(e.b);});
  G.edges.forEach(e=>{const on=(e.a===id||e.b===id);e._l.style.stroke=on?'#3aa0ff':'#3a4a66';e._l.style.strokeOpacity=on?0.9:0.12;});
  G.nodes.forEach(n=>n._c.style.opacity=keep.has(n.id)?1:0.2);
  const n=G.nodes[id];let h=`<h4>${n.t}</h4><div class="muted">${n.f}${n.reg?'':' · <span class=orph>orphan (not in companions.json)</span>'}</div>`;
  const es=ne.slice().sort((a,b)=>b.w-a.w);
  h+=`<h4>Related (${es.length})</h4>`;
  es.forEach(e=>{const o=G.nodes[e.a===id?e.b:e.a];
    h+=`<div class="rel"><b>${o.t}</b> <span class="w">${e.w.toFixed(2)}</span><br>${e.s.map(t=>`<span class=tok>${t}</span>`).join('')}</div>`;});
  document.getElementById('det').innerHTML=h;
}
// legend + bar
document.getElementById('legend').innerHTML='<b>Clusters</b>'+G.legend.map(l=>
  `<div class="leg" data-c="${l.i}"><span class="dot" style="background:${l.color}"></span>${l.label} · ${l.size}</div>`).join('');
document.querySelectorAll('.leg').forEach(d=>d.addEventListener('mouseenter',()=>{
  const ci=+d.dataset.c;G.nodes.forEach(n=>n._c.style.opacity=n.c===ci?1:0.18);
  G.edges.forEach(e=>e._l.style.strokeOpacity=(G.nodes[e.a].c===ci&&G.nodes[e.b].c===ci)?0.8:0.08);}));
document.getElementById('bar').innerHTML=
  `<span class="chip">${G.stats.nodes} companions</span><span class="chip">${G.stats.edges} relations</span>`+
  `<span class="chip">${G.legend.length} clusters</span>`+
  `<span class="chip orph">${G.inv.orphans_unregistered.length} orphans</span>`+
  (G.inv.registered_missing_file.length?`<span class="chip">${G.inv.registered_missing_file.length} missing files</span>`:'');
</script></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.18)
    ap.add_argument("--write-related", action="store_true")
    ap.add_argument("--topk", type=int, default=6)
    a = ap.parse_args()

    reg = json.loads(REG.read_text(encoding="utf-8"))
    reg_by_file = {Path(e["file"]).name: e for e in reg}

    on_disk = sorted(
        p.name for p in COMP.glob("*.html")
        if p.name not in SKIP and not any(d in p.parts for d in SKIP_DIRS)
    )
    registered = set(reg_by_file) - SKIP
    orphans = [f for f in on_disk if f not in registered]                 # on disk, not registered
    missing = sorted(f for f in registered if not (COMP / f).exists())     # registered, no file

    nodes = []
    sig = {}
    for f in on_disk:
        entry = reg_by_file.get(f)
        toks, incs, vocab = signals(f, text_of(COMP / f), entry)
        sig[f] = toks
        nodes.append({
            "file": f,
            "title": (entry or {}).get("title", f.replace(".html", "").replace("_", " ")),
            "domain": (entry or {}).get("domain") or ORPHAN_DOMAIN.get(f, "unclassified"),
            "registered": entry is not None,
            "incidents": sorted(incs),
            "entities": sorted(vocab),
            "n_signals": len(toks),
        })

    # IDF weighting — generic tokens (bank, payment, brain) shared by many companions carry
    # ~0 signal; rare shared entities (a specific INC, FMDERIVE, SAPF100, STEM) carry the edge.
    import math
    N = len(on_disk)
    df = {}
    for f in on_disk:
        for t in sig[f]:
            df[t] = df.get(t, 0) + 1

    def idf(t):
        d = df.get(t, 0)
        if d < 2 or d > 0.55 * N:      # unique → can't relate; ubiquitous → boilerplate
            return 0.0
        return math.log(N / d)

    # pruned IDF-weighted vectors (drop domain marker + zero-idf tokens)
    vec = {f: {t: idf(t) for t in sig[f] if idf(t) > 0 and not t.startswith("dom:")}
           for f in on_disk}
    norm = {f: (math.sqrt(sum(w * w for w in v.values())) or 1.0) for f, v in vec.items()}
    idf_vals = sorted(i for i in (idf(t) for t in df) if i > 0)
    strong = idf_vals[len(idf_vals) // 2] if idf_vals else 0    # median idf = "real entity" bar

    edges = []
    for x, y in combinations(on_disk, 2):
        vx, vy = vec[x], vec[y]
        shared = set(vx) & set(vy)
        if not shared:
            continue
        dot = sum(vx[t] * vy[t] for t in shared)
        cos = dot / (norm[x] * norm[y])
        shared_inc = sorted(t for t in shared if t.startswith("INC-"))
        has_strong = bool(shared_inc) or any(idf(t) >= strong for t in shared)
        if cos < a.threshold or not has_strong:        # need real similarity AND a rare shared entity
            continue
        same_dom = any(t.startswith("dom:") for t in (sig[x] & sig[y]))
        edges.append({
            "a": x, "b": y, "weight": round(cos, 3),
            "shared": sorted(shared, key=lambda t: -idf(t)),
            "shared_incidents": shared_inc,
            "same_domain": same_dom,
        })
    edges.sort(key=lambda e: -e["weight"])

    # clusters = weighted MODULARITY communities (the sub-families inside the connected graph).
    # Connected-components would return one blob; modularity surfaces Treasury/AVC/Infra/etc.
    node_domain = {n["file"]: n["domain"] for n in nodes}
    try:
        import networkx as nx
        from networkx.algorithms.community import greedy_modularity_communities
        G = nx.Graph()
        G.add_nodes_from(on_disk)
        for e in edges:
            G.add_edge(e["a"], e["b"], weight=e["weight"])
        raw = [sorted(c) for c in greedy_modularity_communities(G, weight="weight")]
        method = "greedy_modularity"
    except Exception as ex:
        adj = {f: set() for f in on_disk}
        for e in edges:
            adj[e["a"]].add(e["b"]); adj[e["b"]].add(e["a"])
        seen, raw = set(), []
        for f in on_disk:
            if f in seen:
                continue
            stack, comp = [f], []
            while stack:
                c = stack.pop()
                if c in seen:
                    continue
                seen.add(c); comp.append(c); stack.extend(adj[c] - seen)
            raw.append(sorted(comp))
        method = f"connected_components (networkx unavailable: {ex})"
    clusters = []
    for comp in raw:
        doms = {}
        for c in comp:
            d = node_domain.get(c, "unclassified")
            doms[d] = doms.get(d, 0) + 1
        clusters.append({
            "label": max(doms, key=doms.get),
            "size": len(comp),
            "members": sorted(comp),
            "domain_mix": doms,
        })
    clusters.sort(key=lambda c: -c["size"])

    # top related per node (for companions.json injection / the visual)
    rel = {f: [] for f in on_disk}
    for e in edges:
        rel[e["a"]].append((e["b"], e["weight"]))
        rel[e["b"]].append((e["a"], e["weight"]))
    related = {f: [n for n, _ in sorted(v, key=lambda t: -t[1])[:a.topk]] for f, v in rel.items()}

    graph = {
        "_design": "Companion relationship graph. Deterministic Jaccard over {domain, keywords, "
                   "INC-ids, SAP-vocabulary}; every edge lists the shared tokens (CP-003 traceable). "
                   "Rebuild: python scripts/build_companion_graph.py",
        "generated_for": "UNESCO SAP companions",
        "threshold": a.threshold,
        "inventory": {
            "on_disk": len(on_disk), "registered": len(registered),
            "orphans_unregistered": orphans, "registered_missing_file": missing,
        },
        "stats": {"nodes": len(nodes), "edges": len(edges), "clusters": len(clusters),
                  "cluster_method": method},
        "nodes": nodes,
        "edges": edges,
        "clusters": clusters,
        "related": related,
    }
    OUT.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
    emit_html(graph, COMP / "companion_graph_v1.html")

    # ---- summary ----
    print(f"COMPANION GRAPH  ·  nodes={len(nodes)}  edges={len(edges)}  clusters={len(clusters)}")
    print(f"on_disk={len(on_disk)}  registered={len(registered)}")
    print(f"ORPHANS (on disk, NOT in companions.json): {orphans or 'none'}")
    print(f"MISSING (registered, no file): {missing or 'none'}")
    print("\nTOP 15 EDGES (most related):")
    for e in edges[:15]:
        sh = ", ".join(e["shared"][:6])
        print(f"  {e['weight']:.2f}  {e['a'][:34]:34} ~ {e['b'][:34]:34}  [{sh}]")
    print(f"\nCLUSTERS ({len(clusters)}):")
    for c in clusters:
        print(f"  [{c['label']:11}] size {c['size']:2}  {', '.join(m.replace('.html','') for m in c['members'][:6])}"
              + (" ..." if c["size"] > 6 else ""))

    if a.write_related:
        changed = 0
        for e in reg:
            f = Path(e["file"]).name
            if f in related:
                e["related"] = ["companions/" + r for r in related[f]]
                changed += 1
        REG.write_text(json.dumps(reg, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nInjected `related` into {changed} companions.json entries.")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
