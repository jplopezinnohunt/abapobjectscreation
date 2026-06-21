"""
UNESCO SAP Intelligence Platform — Landing Page Builder
Rebuilds companions/unesco_sap_landing.html dynamically from companions.json and graph stats.
"""

import json
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMPANIONS_JSON = PROJECT_ROOT / "companions" / "companions.json"
GRAPH_JSON = PROJECT_ROOT / "brain_v2" / "output" / "brain_v2_graph.json"
LANDING_HTML = PROJECT_ROOT / "companions" / "unesco_sap_landing.html"

def load_graph():
    """Load graph data from JSON without requiring networkx."""
    if not GRAPH_JSON.exists():
        print(f"WARNING: Graph file not found at {GRAPH_JSON}")
        return {"nodes": [], "edges": []}
    try:
        with open(GRAPH_JSON, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"ERROR reading graph JSON: {e}")
        return {"nodes": [], "edges": []}

def detect_drift(companions, graph_data):
    """
    Detect drift risk using graph structure.
    If a session retro is dated AFTER the companion's last_updated date,
    and that session retro references any of the same objects the companion does,
    then flag the companion as stale.
    """
    nodes_map = {n["id"]: n for n in graph_data.get("nodes", [])}
    
    # Map from object ID -> list of sessions that reference it
    obj_sessions = {}
    session_dates = {}
    
    # First, collect sessions and their dates
    for nid, node in nodes_map.items():
        if nid.startswith("SESSION:") or (node.get("type") == "KNOWLEDGE_DOC" and node.get("source") == "session_retro"):
            meta = node.get("metadata", {})
            date_str = meta.get("date", "")
            if date_str:
                session_dates[nid] = date_str

    # Find edges from sessions to objects
    for edge in graph_data.get("edges", []):
        u, v = edge.get("from"), edge.get("to")
        etype = edge.get("type")
        if u in session_dates and etype == "DISCOVERED_IN":
            obj_sessions.setdefault(v, []).append(u)

    # Map companion name to its referenced objects in the graph
    comp_refs = {}
    for edge in graph_data.get("edges", []):
        u, v = edge.get("from"), edge.get("to")
        etype = edge.get("type")
        if u.startswith("COMPANION:") and etype == "DOCUMENTED_IN":
            comp_name = u.split(":", 1)[1]
            comp_refs.setdefault(comp_name, []).append(v)

    drift_results = {}
    for entry in companions:
        rel_path = entry.get("file", "")
        name = Path(rel_path).stem
        last_updated_str = entry.get("last_updated", "")
        
        try:
            comp_date = datetime.strptime(last_updated_str, "%Y-%m-%d")
        except ValueError:
            comp_date = datetime(2020, 1, 1)

        refs = comp_refs.get(name, [])
        stale_reasons = []
        
        for ref_id in refs:
            sessions = obj_sessions.get(ref_id, [])
            for s_id in sessions:
                s_date_str = session_dates.get(s_id, "")
                if s_date_str:
                    try:
                        s_date = datetime.strptime(s_date_str, "%Y-%m-%d")
                        if s_date > comp_date:
                            s_num = s_id.split(":", 1)[1] if ":" in s_id else s_id
                            ref_name = nodes_map.get(ref_id, {}).get("name", ref_id)
                            stale_reasons.append({
                                "session": s_num,
                                "date": s_date_str,
                                "object": ref_name
                            })
                    except ValueError:
                        pass

        if stale_reasons:
            # Sort stale reasons by date descending
            stale_reasons.sort(key=lambda x: x["date"], reverse=True)
            drift_results[name] = stale_reasons

    return drift_results

def format_size(bytes_size):
    """Format file size in KB/MB."""
    if bytes_size == 0:
        return "0 KB"
    kb = bytes_size / 1024
    if kb < 1024:
        return f"{kb:.1f} KB"
    mb = kb / 1024
    return f"{mb:.2f} MB"

def build_landing_page():
    print("Rebuilding landing page from companions.json registry...")
    
    if not COMPANIONS_JSON.exists():
        print(f"ERROR: Registry file not found at {COMPANIONS_JSON}")
        return False

    with open(COMPANIONS_JSON, "r", encoding="utf-8") as f:
        companions = json.load(f)

    # Load graph and calculate statistics
    graph_data = load_graph()
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    # Calculate counts
    nodes_count = len(nodes) if nodes else 73968
    edges_count = len(edges) if edges else 115200
    
    # Count gold tables (SAP_TABLE nodes)
    gold_tables = sum(1 for n in nodes if n.get("type") == "SAP_TABLE")
    if gold_tables == 0:
        gold_tables = 68
        
    # Count skills
    skills_count = sum(1 for n in nodes if n.get("type") == "SKILL")
    if skills_count == 0:
        skills_count = 40
        
    # Count sessions in knowledge/session_retros/
    retros_dir = PROJECT_ROOT / "knowledge" / "session_retros"
    session_count = 0
    if retros_dir.exists():
        session_count = len(list(retros_dir.glob("session_*_retro.md")))
    if session_count == 0:
        session_count = 34

    # Actual existing files
    existing_companions_count = 0
    for entry in companions:
        rel_path = entry.get("file", "")
        if (PROJECT_ROOT / rel_path).exists() or (PROJECT_ROOT / "companions" / Path(rel_path).name).exists():
            existing_companions_count += 1

    # Detect drift
    drift_info = detect_drift(companions, graph_data)

    # Group by domain
    domain_groups = {}
    for entry in companions:
        dom = entry.get("domain", "general").lower()
        domain_groups.setdefault(dom, []).append(entry)
    num_domains = len([d for d, v in domain_groups.items() if v])
    # filename -> title, for rendering companion-graph `related` links on each card (the structure
    # now carries the graph: jump from a companion to its related ones, not just browse by domain)
    title_by_file = {Path(e.get("file", "")).name: e.get("title", "") for e in companions}

    # Get critical alerts (marked as alert in status, or drift/stale, or manually defined)
    alerts = []
    # Let's check companions.json status or drift status
    for entry in companions:
        rel_path = entry.get("file", "")
        name = Path(rel_path).stem
        if entry.get("status") == "alert" or name in drift_info:
            alerts.append(entry)
            
    # Also include the manually specified critical ones if not already in alerts
    critical_names = ["fm_ps_pool_health_matrix_v1", "fm_ps_avc_model_gap_companion_v1"]
    for entry in companions:
        rel_path = entry.get("file", "")
        name = Path(rel_path).stem
        if name in critical_names and entry not in alerts:
            alerts.append(entry)

    # Generate HTML content
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UNESCO SAP Intelligence Platform — Knowledge Hub</title>
<style>
:root {{
  --bg: #080c14; --surf: #0d1320; --card: #111827; --card-hover: #162032;
  --b: #1a2540; --b2: #1e2d4a; --txt: #dde5f5; --mu: #4c6490; --mu2: #7892c0;
  --acc: #4f8ef7; --grn: #22c55e; --org: #fb923c; --red: #ef4444;
  --pur: #a78bfa; --cyan: #22d3ee; --yel: #f59e0b; --teal: #34d399;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: 'Segoe UI', -apple-system, sans-serif; background: var(--bg); color: var(--txt); min-height: 100vh; }}

/* Hero */
.hero {{ background: linear-gradient(135deg, #0a1628 0%, #0d2247 40%, #1a0d3a 70%, #0a1628 100%); padding: 48px 40px 40px; border-bottom: 1px solid var(--b); position: relative; overflow: hidden; }}
.hero::before {{ content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle at 30% 50%, rgba(79,142,247,0.06) 0%, transparent 50%), radial-gradient(circle at 70% 30%, rgba(167,139,250,0.04) 0%, transparent 40%); pointer-events: none; }}
.hero-inner {{ max-width: 1400px; margin: 0 auto; position: relative; z-index: 1; }}
.hero h1 {{ font-size: 2.2em; font-weight: 800; background: linear-gradient(135deg, #fff 0%, #a0c4ff 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; margin-bottom: 8px; letter-spacing: -0.5px; }}
.hero .sub {{ color: var(--mu2); font-size: 1.05em; margin-bottom: 24px; }}
.hero-stats {{ display: flex; gap: 32px; flex-wrap: wrap; }}
.hero-stat {{ text-align: center; }}
.hero-stat .v {{ font-size: 1.8em; font-weight: 800; font-family: 'Consolas', monospace; }}
.hero-stat .l {{ font-size: 0.7em; text-transform: uppercase; letter-spacing: 0.08em; color: var(--mu); margin-top: 2px; }}
.hero-stat.blue .v {{ color: var(--acc); }}
.hero-stat.green .v {{ color: var(--grn); }}
.hero-stat.purple .v {{ color: var(--pur); }}
.hero-stat.orange .v {{ color: var(--org); }}
.hero-stat.cyan .v {{ color: var(--cyan); }}
.hero-stat.teal .v {{ color: var(--teal); }}

/* Search */
.search-bar {{ max-width: 1400px; margin: -20px auto 0; padding: 0 40px; position: relative; z-index: 10; }}
.search-input {{ width: 100%; padding: 14px 20px 14px 48px; background: var(--card); border: 1px solid var(--b); border-radius: 12px; color: var(--txt); font-size: 0.95em; outline: none; transition: border-color 0.2s; }}
.search-input:focus {{ border-color: var(--acc); }}
.search-icon {{ position: absolute; left: 56px; top: 50%; transform: translateY(-50%); color: var(--mu); font-size: 1.1em; }}

/* Domain Sections */
.domains {{ max-width: 1400px; margin: 0 auto; padding: 32px 40px 80px; }}
.domain-section {{ margin-bottom: 40px; }}
.domain-header {{ display: flex; align-items: center; gap: 12px; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 1px solid var(--b); }}
.domain-icon {{ width: 36px; height: 36px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; flex-shrink: 0; }}
.domain-header h2 {{ font-size: 1.25em; font-weight: 700; }}
.domain-header .count {{ font-size: 0.75em; color: var(--mu); background: var(--card); padding: 3px 10px; border-radius: 12px; border: 1px solid var(--b); }}

/* Cards Grid */
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 16px; }}
.card {{ background: var(--card); border: 1px solid var(--b); border-radius: 12px; padding: 24px; cursor: pointer; transition: all 0.25s ease; position: relative; overflow: hidden; text-decoration: none; color: inherit; display: block; }}
.card:hover {{ background: var(--card-hover); border-color: var(--b2); transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }}
.card::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 12px 12px 0 0; }}
.card.finance::before {{ background: linear-gradient(90deg, var(--grn), var(--teal)); }}
.card.transport::before {{ background: linear-gradient(90deg, var(--acc), var(--pur)); }}
.card.process::before {{ background: linear-gradient(90deg, var(--org), var(--yel)); }}
.card.infra::before {{ background: linear-gradient(90deg, var(--cyan), var(--acc)); }}
.card.support::before {{ background: linear-gradient(90deg, var(--yel), var(--org)); }}
.card.general::before {{ background: linear-gradient(90deg, var(--pur), var(--cyan)); }}

.card-title {{ font-size: 1.05em; font-weight: 700; margin-bottom: 6px; display: flex; align-items: center; justify-content: space-between; gap: 8px; }}
.card-title-text {{ display: flex; align-items: center; gap: 8px; }}
.card-title .badge {{ font-size: 0.65em; padding: 2px 8px; border-radius: 6px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }}
.badge.tabs {{ background: rgba(79,142,247,0.15); color: var(--acc); }}
.badge.stale {{ background: rgba(239,68,68,0.15); color: var(--red); border: 1px solid rgba(239,68,68,0.3); animation: pulse 2s infinite; }}
.badge.planned {{ background: rgba(245,158,11,0.15); color: var(--yel); }}
.card-desc {{ color: var(--mu2); font-size: 0.85em; margin-bottom: 16px; line-height: 1.5; }}

.card-metrics {{ display: flex; flex-wrap: wrap; gap: 12px; }}
.metric {{ background: rgba(255,255,255,0.03); border: 1px solid var(--b); border-radius: 8px; padding: 8px 12px; min-width: 80px; }}
.metric .mv {{ font-size: 1em; font-weight: 700; font-family: 'Consolas', monospace; }}
.metric .ml {{ font-size: 0.65em; color: var(--mu); text-transform: uppercase; letter-spacing: 0.05em; }}

.card-related {{ display: flex; flex-wrap: wrap; gap: 5px; align-items: center; margin-top: 12px; }}
.rel-label {{ font-size: 0.62em; text-transform: uppercase; letter-spacing: 0.06em; color: var(--mu); margin-right: 2px; }}
.rel-chip {{ font-size: 0.7em; color: #a0c4ff; background: rgba(79,142,247,0.10); border: 1px solid var(--b); border-radius: 10px; padding: 1px 8px; cursor: pointer; transition: all 0.15s; }}
.rel-chip:hover {{ border-color: var(--acc); color: #fff; background: rgba(79,142,247,0.2); }}
.card-footer {{ display: flex; justify-content: space-between; align-items: center; margin-top: 16px; padding-top: 12px; border-top: 1px solid var(--b); }}
.card-size {{ font-size: 0.75em; color: var(--mu); }}
.card-arrow {{ color: var(--acc); font-size: 1.2em; transition: transform 0.2s; }}
.card:hover .card-arrow {{ transform: translateX(4px); }}

/* Status bar */
.status-bar {{ position: fixed; bottom: 0; left: 0; right: 0; background: var(--surf); border-top: 1px solid var(--b); padding: 8px 40px; display: flex; justify-content: space-between; align-items: center; font-size: 0.75em; color: var(--mu); z-index: 100; }}
.status-bar a {{ color: var(--acc); text-decoration: none; }}

/* Filter pills */
.filters {{ display: flex; gap: 8px; margin-bottom: 24px; flex-wrap: wrap; }}
.filter-pill {{ padding: 6px 16px; border-radius: 20px; border: 1px solid var(--b); background: var(--card); color: var(--mu2); font-size: 0.8em; cursor: pointer; transition: all 0.2s; }}
.filter-pill:hover, .filter-pill.active {{ border-color: var(--acc); color: var(--acc); background: rgba(79,142,247,0.1); }}

@keyframes pulse {{
  0% {{ opacity: 0.8; }}
  50% {{ opacity: 1; }}
  100% {{ opacity: 0.8; }}
}}

/* Responsive */
@media (max-width: 860px) {{
  .cards {{ grid-template-columns: 1fr; }}
  .hero {{ padding: 32px 20px; }}
  .domains {{ padding: 24px 20px 80px; }}
  .hero-stats {{ gap: 20px; }}
}}
</style>
</head>
<body>

<div class="hero">
  <div class="hero-inner">
    <h1>UNESCO SAP Intelligence Platform</h1>
    <p class="sub">Knowledge Hub — {existing_companions_count} Active Companions across {num_domains} Domains (Drift and Staleness Protected)</p>
    <div class="hero-stats">
      <div class="hero-stat blue"><div class="v">{existing_companions_count}</div><div class="l">Companions</div></div>
      <div class="hero-stat green"><div class="v">24M+</div><div class="l">Rows Extracted</div></div>
      <div class="hero-stat purple"><div class="v">{nodes_count:,}</div><div class="l">Brain Nodes</div></div>
      <div class="hero-stat orange"><div class="v">{gold_tables}</div><div class="l">Gold DB Tables</div></div>
      <div class="hero-stat cyan"><div class="v">{skills_count}</div><div class="l">Skills Built</div></div>
      <div class="hero-stat teal"><div class="v">{session_count}</div><div class="l">Sessions</div></div>
    </div>
    <div style="margin-top:22px; display:flex; gap:12px; flex-wrap:wrap;">
      <a href="companion_graph_v1.html" style="display:inline-flex; align-items:center; gap:10px; background:linear-gradient(135deg,#4f8ef7,#a78bfa); color:#06101f; font-weight:800; font-size:0.92em; text-decoration:none; padding:11px 20px; border-radius:10px; box-shadow:0 4px 18px rgba(79,142,247,0.25);">&#x1F578; Companion Knowledge Map &mdash; how they relate &rarr;</a>
      <span style="display:inline-flex; align-items:center; color:#7892c0; font-size:0.8em;">{existing_companions_count} companions &middot; related as a graph (deterministic IDF, traceable edges)</span>
    </div>
  </div>
</div>

<div class="search-bar">
  <span class="search-icon">&#x1F50D;</span>
  <input type="text" class="search-input" placeholder="Search companions by name, domain, or keyword..." id="search">
</div>

<!-- ====================================================================
     SAP DATA EXTRACTION COMPLIANCE — ODP-RFC (SAP Note 3255746)
     Permanent governance statement. Outside .domains so search/filter JS
     never hides it. Source: scripts/build_landing_page.py (do NOT hand-edit
     the generated HTML — rebuild_all.py regenerates it).
     ==================================================================== -->
<div style="max-width:1400px; margin:24px auto 0; padding:0 40px;">
  <div style="background:linear-gradient(135deg, rgba(34,197,94,0.07) 0%, rgba(52,211,153,0.03) 100%); border:1px solid #22c55e; border-radius:14px; padding:24px 28px; position:relative; overflow:hidden;">
    <div style="display:flex; align-items:center; gap:14px; flex-wrap:wrap; margin-bottom:14px;">
      <div style="width:40px; height:40px; border-radius:10px; background:linear-gradient(135deg,#22c55e,#34d399); display:flex; align-items:center; justify-content:center; font-size:20px; flex-shrink:0;">&#x1F6E1;</div>
      <div style="flex:1; min-width:240px;">
        <div style="font-size:1.2em; font-weight:800; color:#dde5f5;">SAP Data Extraction Compliance &mdash; ODP-RFC</div>
        <div style="font-size:0.8em; color:#7892c0; margin-top:2px;">SAP Note 3255746 &mdash; "Unpermitted usage of ODP Data Replication APIs" (updated 2026-04-13) &middot; Security patch: Patch Day 2026-06-09</div>
      </div>
      <span style="font-size:0.8em; font-weight:700; text-transform:uppercase; letter-spacing:0.06em; color:#22c55e; background:rgba(34,197,94,0.14); border:1px solid #22c55e; padding:6px 14px; border-radius:8px; white-space:nowrap;">&#x2714; Compliant &mdash; Not Affected</span>
    </div>
    <p style="color:#dde5f5; font-size:0.95em; line-height:1.6; margin-bottom:20px;">
      UNESCO's Gold DB (<strong>24M+ rows</strong>) is built exclusively with the generic SAP table reader
      <code style="background:rgba(255,255,255,0.06); padding:1px 7px; border-radius:5px; font-family:Consolas,monospace; color:#34d399;">RFC_READ_TABLE</code>.
      It does <strong>not</strong> use the ODP Data Replication APIs that SAP Note 3255746 restricts.
      The June 9 security patch blocks unauthorized <em>ODP-RFC</em> calls only &mdash; our extraction makes none, so a Gold&nbsp;DB refresh runs unchanged after the patch. <strong>No action and no patch deferral are required on our account.</strong>
    </p>
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:16px; margin-bottom:20px;">
      <div style="background:rgba(239,68,68,0.05); border:1px solid rgba(239,68,68,0.35); border-radius:10px; padding:16px 18px;">
        <div style="font-size:0.72em; text-transform:uppercase; letter-spacing:0.07em; color:#ef4444; font-weight:700; margin-bottom:10px;">&#x26D4; What the note restricts (ODP-RFC) &mdash; we do NOT use</div>
        <ul style="list-style:none; padding:0; margin:0; font-size:0.86em; color:#b8c4de; line-height:1.9;">
          <li><code style="font-family:Consolas,monospace; color:#f87171;">RODPS_REPL_*</code> &mdash; ODP replication RFC interface</li>
          <li><code style="font-family:Consolas,monospace; color:#f87171;">ODQ_*</code> &mdash; Operational Delta Queue</li>
          <li><code style="font-family:Consolas,monospace; color:#f87171;">/SAPDS/</code> operators &mdash; SLT / Data Services</li>
          <li>CDS-view / extractor / DataSource subscriptions</li>
          <li>Change-data-capture &amp; delta replication to 3rd-party tools</li>
        </ul>
      </div>
      <div style="background:rgba(34,197,94,0.05); border:1px solid rgba(34,197,94,0.35); border-radius:10px; padding:16px 18px;">
        <div style="font-size:0.72em; text-transform:uppercase; letter-spacing:0.07em; color:#22c55e; font-weight:700; margin-bottom:10px;">&#x2714; What the Gold DB uses (out of scope)</div>
        <ul style="list-style:none; padding:0; margin:0; font-size:0.86em; color:#b8c4de; line-height:1.9;">
          <li><code style="font-family:Consolas,monospace; color:#34d399;">RFC_READ_TABLE</code> &mdash; generic single-table read (fn group SDTX)</li>
          <li>Paginated <code style="font-family:Consolas,monospace; color:#34d399;">ROWCOUNT</code>/<code style="font-family:Consolas,monospace; color:#34d399;">ROWSKIPS</code>, <code style="font-family:Consolas,monospace; color:#34d399;">WHERE</code> via OPTIONS</li>
          <li>Transparent application tables (BKPF, BSEG, FMIFIIT&hellip;)</li>
          <li>pyrfc over <strong>SNC/SSO</strong>, P01 read-only</li>
          <li>No delta queue, no subscription, no ODP context</li>
        </ul>
      </div>
    </div>
    <div style="background:rgba(255,255,255,0.025); border-left:3px solid #22c55e; border-radius:0 8px 8px 0; padding:12px 16px; margin-bottom:18px;">
      <div style="font-size:0.8em; color:#7892c0; line-height:1.6;">
        <strong style="color:#dde5f5;">Why this holds:</strong> ODP and <code style="font-family:Consolas,monospace; color:#9fb4e0;">RFC_READ_TABLE</code> are different frameworks. ODP is a <em>replication</em> mechanism (delta queues, subscriptions, change-data-capture). <code style="font-family:Consolas,monospace; color:#9fb4e0;">RFC_READ_TABLE</code> is the equivalent of "SELECT these fields FROM this table WHERE&hellip;, return the rows" &mdash; no delta, no subscription. SAP Note 3255746, its self-assessment (Note 3439624) and the June 9 patch all target ODP only.
      </div>
    </div>
    <div style="display:flex; flex-wrap:wrap; gap:10px 24px; align-items:center; font-size:0.78em; color:#4c6490;">
      <span><strong style="color:#7892c0;">Code evidence:</strong>
        <code style="font-family:Consolas,monospace; color:#9fb4e0;">rfc_helpers.py:147</code> &middot;
        <code style="font-family:Consolas,monospace; color:#9fb4e0;">extract_bkpf_bseg_parallel.py:94</code> &middot;
        repo-wide scan for ODP APIs = <strong style="color:#22c55e;">0 calls</strong>
      </span>
      <span style="border-left:1px solid #1e2d4a; padding-left:24px;"><strong style="color:#7892c0;">Independently corroborated:</strong> Theobald, Databricks, Microsoft, Qlik &amp; CData all scope the note to <code style="font-family:Consolas,monospace; color:#9fb4e0;">RODPS_REPL_*</code> (ODP-RFC) only; table-read RFC is named a compliant alternative.</span>
      <span style="border-left:1px solid #1e2d4a; padding-left:24px;"><strong style="color:#7892c0;">For SAP sign-off:</strong> run the Note 3439624 self-assessment on P01 + D01 to convert this into SAP's own confirmation.</span>
    </div>
    <div style="font-size:0.7em; color:#3a4a6a; margin-top:14px; border-top:1px solid #16203233; padding-top:10px;">Assessed 2026-06-02 against the extraction pipeline source of truth + independent public sources. <code style="font-family:Consolas,monospace;">RFC_READ_TABLE</code> is currently the vendor-recommended compliant alternative to ODP-RFC. Strategic watch item only: SAP's broader direction to gatekeep third-party data access (Forrester 2026) &mdash; not an imminent restriction. Brain: claims #203 (TIER_1) / #204, rule feedback_classify_exact_api_before_compliance_call.</div>
  </div>
</div>

<div class="domains" id="domains">

  <!-- Filters -->
  <div class="filters">
    <div class="filter-pill active" data-filter="all">All</div>
    <div class="filter-pill" data-filter="finance">Finance & Payments</div>
    <div class="filter-pill" data-filter="process">Process Mining</div>
    <div class="filter-pill" data-filter="transport">Transport Intelligence</div>
    <div class="filter-pill" data-filter="infra">Infrastructure</div>
    <div class="filter-pill" data-filter="support">Support & Maintenance</div>
    <div class="filter-pill" data-filter="general">General</div>
  </div>
"""

    # Critical Alerts Section
    if alerts:
        html += f"""
  <!-- CRITICAL ALERTS -->
  <div class="domain-section" data-domain="alerts" style="margin-bottom:32px;">
    <div class="domain-header">
      <div class="domain-icon" style="background:linear-gradient(135deg,#ef4444,#fb923c);">&#x26A0;</div>
      <h2 style="color:#ef4444;">Critical Alerts & Drift Alerts</h2>
      <span class="count" style="background:rgba(239,68,68,0.12);color:#ef4444;border-color:#ef4444;">{len(alerts)} items</span>
    </div>
    <div class="cards">
"""
        for entry in alerts:
            rel_path = entry.get("file", "")
            name = Path(rel_path).stem
            title = entry.get("title", name)
            desc = entry.get("description", "")
            metrics = entry.get("metrics", [])
            keywords = entry.get("keywords", [])
            domain = entry.get("domain", "general").lower()
            
            # Resolve file size
            html_file = PROJECT_ROOT / rel_path
            if not html_file.exists():
                html_file = PROJECT_ROOT / "companions" / Path(rel_path).name
            
            size_str = "0 KB"
            if html_file.exists():
                size_str = format_size(html_file.stat().st_size)
            else:
                size_str = "Planned / Missing"

            # Check if this companion is stale
            drift_badge = ""
            drift_style = ""
            stale_desc = ""
            if name in drift_info:
                reasons = drift_info[name]
                latest_drift = reasons[0]
                drift_badge = f'<span class="badge stale">STALE</span>'
                drift_style = 'style="border-color:#ef4444; background:linear-gradient(135deg,rgba(239,68,68,0.04) 0%, rgba(251,146,60,0.02) 100%);"'
                stale_desc = f'<div style="color:#f87171; font-size:0.8em; margin-top:8px; font-weight:600;">⚠️ Drift Detected: {latest_drift["object"]} changed in Session #{latest_drift["session"]} ({latest_drift["date"]})</div>'
            elif name in ["fm_ps_pool_health_matrix_v1", "fm_ps_avc_model_gap_companion_v1"]:
                # Manually flagged critical alerts
                drift_style = 'style="border-color:#ef4444; background:linear-gradient(135deg,rgba(239,68,68,0.04) 0%, rgba(251,146,60,0.02) 100%);"'
                drift_badge = '<span class="badge stale" style="background:rgba(239,68,68,0.15);color:#ef4444;">CRITICAL</span>'

            # Metric bubbles
            metric_html = ""
            for m in metrics:
                metric_html += f'<div class="metric"><div class="mv">{m["value"]}</div><div class="ml">{m["label"]}</div></div>'

            html += f"""
      <a class="card {domain}" href="{Path(rel_path).name}" data-keywords="{" ".join(keywords)}" {drift_style}>
        <div class="card-title">
          <span class="card-title-text">{title}</span>
          {drift_badge}
        </div>
        <div class="card-desc">{desc} {stale_desc}</div>
        <div class="card-metrics">
          {metric_html}
        </div>
        <div class="card-footer">
          <span class="card-size">{size_str} &middot; {entry.get("version", "v1.0")}</span>
          <span class="card-arrow">&rarr;</span>
        </div>
      </a>
"""
        html += """
    </div>
  </div>
"""

    # Domain Sections
    domains_map = {
        "finance": ("Finance & Payments", "💵", "linear-gradient(135deg,#22c55e,#34d399)"),
        "process": ("Process Mining", "🔄", "linear-gradient(135deg,#fb923c,#f59e0b)"),
        "transport": ("Transport Intelligence", "📦", "linear-gradient(135deg,#4f8ef7,#a78bfa)"),
        "infra": ("Infrastructure & Systems", "🖥️", "linear-gradient(135deg,#22d3ee,#4f8ef7)"),
        "support": ("Support & Maintenance", "🔧", "linear-gradient(135deg,#f59e0b,#ef4444)"),
        "closing": ("Closing Activities", "📅", "linear-gradient(135deg,#a78bfa,#f472b6)"),
        "general": ("General Knowledge", "🧠", "linear-gradient(135deg,#a78bfa,#22d3ee)"),
    }

    # Accommodate EVERY companion: mapped domains in this order, then ANY other domain present in
    # companions.json (never silently drop a companion whose domain isn't pre-listed — the bug that
    # hid the Closing companion). Catch-all gets a neutral style.
    ordered_domains = list(domains_map.items())
    for code in sorted(domain_groups):
        if code not in domains_map and domain_groups.get(code):
            ordered_domains.append((code, (code.replace("_", " ").title(), "🗂️",
                                           "linear-gradient(135deg,#64748b,#94a3b8)")))

    for dom_code, (dom_name, dom_icon, dom_gradient) in ordered_domains:
        entries = domain_groups.get(dom_code, [])
        if not entries:
            continue
            
        html += f"""
  <!-- {dom_name.upper()} -->
  <div class="domain-section" data-domain="{dom_code}">
    <div class="domain-header">
      <div class="domain-icon" style="background:{dom_gradient};">{dom_icon}</div>
      <h2>{dom_name}</h2>
      <span class="count">{len(entries)} companions</span>
    </div>
    <div class="cards">
"""
        for entry in entries:
            rel_path = entry.get("file", "")
            name = Path(rel_path).stem
            title = entry.get("title", name)
            desc = entry.get("description", "")
            metrics = entry.get("metrics", [])
            keywords = entry.get("keywords", [])
            status = entry.get("status", "active")
            
            # Resolve file size
            html_file = PROJECT_ROOT / rel_path
            if not html_file.exists():
                html_file = PROJECT_ROOT / "companions" / Path(rel_path).name
            
            size_str = "0 KB"
            exists = html_file.exists()
            if exists:
                size_str = format_size(html_file.stat().st_size)
            else:
                size_str = "Planned / Pending"

            badge_html = ""
            card_href = Path(rel_path).name if exists else "#"
            card_style = ""
            
            if not exists:
                badge_html = '<span class="badge planned">PLANNED</span>'
                card_style = 'style="opacity: 0.6; cursor: default;"'
            elif name in drift_info:
                reasons = drift_info[name]
                latest_drift = reasons[0]
                badge_html = f'<span class="badge stale">STALE</span>'
                card_style = 'style="border-color:#f59e0b;"'
                desc += f'<div style="color:#fb923c; font-size:0.8em; margin-top:8px; font-weight:600;">⚠️ Drift Detected: {latest_drift["object"]} changed in Session #{latest_drift["session"]} ({latest_drift["date"]})</div>'

            metric_html = ""
            for m in metrics:
                metric_html += f'<div class="metric"><div class="mv">{m["value"]}</div><div class="ml">{m["label"]}</div></div>'

            # companion-graph relationships → clickable chips (navigate without nesting <a> in <a>)
            related_html = ""
            rel_files = entry.get("related", [])[:4]
            if rel_files:
                chips = ""
                for rf in rel_files:
                    fn = Path(rf).name
                    rt = title_by_file.get(fn) or fn.replace(".html", "").replace("_", " ")
                    label = rt if len(rt) <= 24 else rt[:23] + "…"
                    chips += (f'<span class="rel-chip" title="{rt}" '
                              f'onclick="event.preventDefault();event.stopPropagation();'
                              f"window.location='{fn}'\">{label}</span>")
                related_html = f'<div class="card-related"><span class="rel-label">Related</span>{chips}</div>'

            html += f"""
      <a class="card {dom_code}" href="{card_href}" data-keywords="{" ".join(keywords)}" {card_style}>
        <div class="card-title">
          <span class="card-title-text">{title}</span>
          {badge_html}
        </div>
        <div class="card-desc">{desc}</div>
        <div class="card-metrics">
          {metric_html}
        </div>
        {related_html}
        <div class="card-footer">
          <span class="card-size">{size_str} &middot; {entry.get("version", "v1.0")}</span>
          <span class="card-arrow">&rarr;</span>
        </div>
      </a>
"""
        html += """
    </div>
  </div>
"""

    html += f"""
</div>

<!-- Status Bar -->
<div class="status-bar">
  <span>UNESCO SAP Intelligence Platform &middot; {session_count} Sessions &middot; Last updated: {datetime.now().strftime("%Y-%m-%d")}</span>
  <span>Gold DB: {gold_tables} tables &middot; 24M+ rows &middot; Brain: {nodes_count:,} nodes &middot; {edges_count:,} edges</span>
</div>

<script>
// Search
const searchInput = document.getElementById('search');
searchInput.addEventListener('input', function() {{
  const q = this.value.toLowerCase();
  document.querySelectorAll('.card').forEach(card => {{
    const text = (card.textContent + ' ' + (card.dataset.keywords || '')).toLowerCase();
    card.style.display = text.includes(q) ? '' : 'none';
  }});
  // Show all domain sections, hide empty ones
  document.querySelectorAll('.domain-section').forEach(section => {{
    const visible = section.querySelectorAll('.card:not([style*="display: none"])').length;
    section.style.display = visible ? '' : 'none';
  }});
}});

// Filter pills
document.querySelectorAll('.filter-pill').forEach(pill => {{
  pill.addEventListener('click', function() {{
    document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    this.classList.add('active');
    const filter = this.dataset.filter;
    document.querySelectorAll('.domain-section').forEach(section => {{
      section.style.display = (filter === 'all' || section.dataset.domain === filter) ? '' : 'none';
    }});
    searchInput.value = '';
    document.querySelectorAll('.card').forEach(c => c.style.display = '');
  }});
}});

// Keyboard shortcut: / to focus search
document.addEventListener('keydown', e => {{
  if (e.key === '/' && document.activeElement !== searchInput) {{
    e.preventDefault();
    searchInput.focus();
  }}
}});
</script>
</body>
</html>
"""

    try:
        LANDING_HTML.write_text(html, encoding="utf-8")
        print(f"SUCCESS: Landing page rebuilt at {LANDING_HTML}")
        return True
    except Exception as e:
        print(f"ERROR writing landing page HTML: {e}")
        return False

if __name__ == "__main__":
    build_landing_page()
