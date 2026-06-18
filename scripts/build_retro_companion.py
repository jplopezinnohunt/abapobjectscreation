import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.scaffold_diagram import scaffold_file

nodes = [
    {
        "id": "OPEN:1",
        "x": 50,
        "y": 120,
        "label": "Session Open",
        "color": "blue",
        "details": "Goal: Unified Companion Governance & Ingestion\\nDate: 2026-05-22\\nStatus: Completed\\nRef: /session_start"
    },
    {
        "id": "RESEARCH:2",
        "x": 270,
        "y": 120,
        "label": "Codebase Research",
        "color": "cyan",
        "details": "Analysis: Found 28+ companions detached from graph\\nStaleness mitigation: Tracing DISCOVERED_IN session edges\\nStatus: Completed"
    },
    {
        "id": "PLAN:3",
        "x": 490,
        "y": 120,
        "label": "Implementation Plan",
        "color": "purple",
        "details": "Plan: Registry, ingestor update, landing page, validator, new companions\\nStatus: Approved\\nRef: implementation_plan.md"
    },
    {
        "id": "CODE:4",
        "x": 710,
        "y": 120,
        "label": "Code Execution",
        "color": "orange",
        "details": "Registry: companions.json update\\nIngestor: knowledge_ingestor.py updated\\nValidator: validate_companions.py created\\nLanding Page: build_landing_page.py created\\nScaffolder: scaffold_diagram.py created\\nStatus: Completed"
    },
    {
        "id": "VALIDATE:5",
        "x": 930,
        "y": 120,
        "label": "Verification",
        "color": "green",
        "details": "Graph rebuild: python brain_v2/rebuild_all.py\\nCompliance test: validate_companions.py runs\\nVisual inspection: landing page verified\\nStatus: Completed"
    },
    {
        "id": "CLOSE:6",
        "x": 1150,
        "y": 120,
        "label": "Session Close",
        "color": "teal",
        "details": "Retro: checklist completed\\nBrain vectors: companions ingested and linked\\nStatus: Pending Close\\nRef: /session_retro"
    },
    {
        "id": "CHECK:1",
        "x": 160,
        "y": 300,
        "label": "Check 1: SSoT Registry",
        "color": "green",
        "details": "Registry: companions/companions.json\\nStatus: Validated\\nEnsures single source of truth for all HTML assets."
    },
    {
        "id": "CHECK:2",
        "x": 360,
        "y": 300,
        "label": "Check 2: Self-Containment",
        "color": "green",
        "details": "Rule: No external CDN styles/scripts\\nStatus: Validated\\nValidator checks for links and forbidden libraries."
    },
    {
        "id": "CHECK:3",
        "x": 560,
        "y": 300,
        "label": "Check 3: Design System",
        "color": "green",
        "details": "Rule: Dark-neon theme variables\\nStatus: Validated\\nEnforces layout colors and styling."
    },
    {
        "id": "CHECK:4",
        "x": 760,
        "y": 300,
        "label": "Check 4: Geometry standard",
        "color": "green",
        "details": "Rule: Nodes size 180x80px\\nStatus: Validated\\nEnforces SVG element widths and heights."
    },
    {
        "id": "CHECK:5",
        "x": 960,
        "y": 300,
        "label": "Check 5: Graph Ingestion",
        "color": "green",
        "details": "Parser: knowledge_ingestor.py scans html contents\\nStatus: Validated\\nCreates DOCUMENTED_IN edges to referenced SAP objects."
    },
    {
        "id": "CHECK:6",
        "x": 1160,
        "y": 300,
        "label": "Check 6: Drift Detection",
        "color": "green",
        "details": "Algorithm: Compare companion last_updated with session retro dates\\nStatus: Validated\\nFlags stale companions in the landing page."
    },
    {
        "id": "CHECK:7",
        "x": 660,
        "y": 420,
        "label": "Check 7: Pipeline Integration",
        "color": "green",
        "details": "Integration: rebuild_all.py executes validation & builder\\nStatus: Validated\\nAutomates all steps on full rebuild."
    }
]

links = [
    {"source": "OPEN:1", "target": "RESEARCH:2", "color": "#4f8ef7"},
    {"source": "RESEARCH:2", "target": "PLAN:3", "color": "#22d3ee"},
    {"source": "PLAN:3", "target": "CODE:4", "color": "#a78bfa"},
    {"source": "CODE:4", "target": "VALIDATE:5", "color": "#fb923c"},
    {"source": "VALIDATE:5", "target": "CLOSE:6", "color": "#34d399"},
    {"source": "CODE:4", "target": "CHECK:1", "color": "#22c55e"},
    {"source": "CODE:4", "target": "CHECK:2", "color": "#22c55e"},
    {"source": "CODE:4", "target": "CHECK:3", "color": "#22c55e"},
    {"source": "CODE:4", "target": "CHECK:4", "color": "#22c55e"},
    {"source": "CODE:4", "target": "CHECK:5", "color": "#22c55e"},
    {"source": "CODE:4", "target": "CHECK:6", "color": "#22c55e"},
    {"source": "CODE:4", "target": "CHECK:7", "color": "#22c55e"}
]

metrics = [
    {"label": "Session ID", "value": "#075"},
    {"label": "Timeline Steps", "value": "6 Steps"},
    {"label": "AGI Checks", "value": "7/7 OK"},
    {"label": "Status", "value": "Active"}
]

scaffold_file(
    filepath="companions/session_075_retro.html",
    title="Session #075 Retrospective",
    domain="SUPPORT",
    description="Interactive Retrospective dashboard for Session #075, mapping the discovery path, modified graph nodes, and validation checklists.",
    nodes=nodes,
    links=links,
    metrics=metrics
)
