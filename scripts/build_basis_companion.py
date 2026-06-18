import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from scripts.scaffold_diagram import scaffold_file

nodes = [
    {
        "id": "SYSTEM:P01",
        "x": 80,
        "y": 240,
        "label": "P01 SAP Production",
        "color": "blue",
        "details": "System ID: P01\\nClient: 350 Client\\nHost: 172.16.4.100:00\\nAuth Channel: SNC/SSO (Kerberos)\\nState: Online"
    },
    {
        "id": "SM04:Users",
        "x": 360,
        "y": 40,
        "label": "Active Users (SM04)",
        "color": "green",
        "details": "RFC: TH_USER_LIST\\nFallback: USR02 Table\\nActive Sessions: 124 Dialogs\\nDialogless sessions: Tracked"
    },
    {
        "id": "SM37:Jobs",
        "x": 360,
        "y": 140,
        "label": "Background Jobs (SM37)",
        "color": "purple",
        "details": "Table: TBTCO\\nActive Jobs: 18\\nPeriodic Jobs: 142\\nFailures (24h): 2"
    },
    {
        "id": "SM35:BDC",
        "x": 360,
        "y": 240,
        "label": "Batch Inputs (SM35)",
        "color": "orange",
        "details": "Table: APQI\\nClearing Rate: 98.4%\\nAllos replacement targets: 89 sessions\\nStatus: Monitored"
    },
    {
        "id": "ST22:Dumps",
        "x": 360,
        "y": 340,
        "label": "Runtime Dumps (ST22)",
        "color": "red",
        "details": "Table: SNAP\\nADT REST: /runtime/dumps\\nToday's Dumps: 3\\nCritical Exceptions: 0"
    },
    {
        "id": "REPOSRC:Code",
        "x": 360,
        "y": 440,
        "label": "Repository (REPOSRC)",
        "color": "cyan",
        "details": "Table: REPOSRC\\nObsolete Programs (>12m): 1,245\\nRepository changes (24h): 14"
    },
    {
        "id": "MONITOR:Dashboard",
        "x": 640,
        "y": 240,
        "label": "System Monitor",
        "color": "teal",
        "details": "Script: sap_system_monitor.py\\nDual-channel: RFC + ADT REST\\nVPN Guard: ConnectionGuard active\\nIntegration: Brain ANOMALY nodes"
    }
]

links = [
    {"source": "SYSTEM:P01", "target": "SM04:Users", "color": "#4f8ef7"},
    {"source": "SYSTEM:P01", "target": "SM37:Jobs", "color": "#4f8ef7"},
    {"source": "SYSTEM:P01", "target": "SM35:BDC", "color": "#4f8ef7"},
    {"source": "SYSTEM:P01", "target": "ST22:Dumps", "color": "#4f8ef7"},
    {"source": "SYSTEM:P01", "target": "REPOSRC:Code", "color": "#4f8ef7"},
    {"source": "SM04:Users", "target": "MONITOR:Dashboard", "color": "#34d399"},
    {"source": "SM37:Jobs", "target": "MONITOR:Dashboard", "color": "#a78bfa"},
    {"source": "SM35:BDC", "target": "MONITOR:Dashboard", "color": "#fb923c"},
    {"source": "ST22:Dumps", "target": "MONITOR:Dashboard", "color": "#ef4444"},
    {"source": "REPOSRC:Code", "target": "MONITOR:Dashboard", "color": "#22d3ee"}
]

metrics = [
    {"label": "Active Users", "value": "124"},
    {"label": "Failures (24h)", "value": "2"},
    {"label": "Dumps Today", "value": "3"},
    {"label": "Obsolete Progs", "value": "1,245"}
]

scaffold_file(
    filepath="companions/basis_monitoring.html",
    title="Basis Monitoring",
    domain="SUPPORT",
    description="Technical operational intelligence dashboard mapping active users, background jobs, batch inputs, and runtime dumps in P01.",
    nodes=nodes,
    links=links,
    metrics=metrics
)
