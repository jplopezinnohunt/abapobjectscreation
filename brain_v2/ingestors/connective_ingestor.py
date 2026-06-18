"""
Connective ingestor — the "synaptic tissue" of the brain.

Derives the relationships that the code parser and config ingestors CANNOT see,
from behavioural + ownership evidence already sitting in the Gold DB:

  * USER layer            <- bkpf.USNAM        (1,415 real users)
  * USER -OPERATES_TCODE-> TRANSACTION         <- bkpf (USNAM x TCODE, weight = #docs)
  * TRANSACTION -USED_IN_CC-> COMPANY_CODE     <- bkpf (TCODE x BUKRS)
  * object -BELONGS_TO_PACKAGE-> PACKAGE        <- tadir_enrichment (4,168 objects)
  * JOB -RUNS_PROGRAM-> PROGRAM                 <- tbtcp (job step -> program)

This is the layer that answers "who runs what, with which transaction, owned by
which package, scheduled by which job" — the web the brain was losing.

Re-runnable and idempotent: add_node/add_edge upsert by id, so running every
session re-weaves the same synapses and folds in new evidence. Nothing is lost.

It also reports an EXTRACTION BACKLOG: the edges it WANTS to build but cannot,
because the source table is not yet in the Gold DB (TSTC -> tcode→program,
MODSAP -> exit→program, USR02/AGR_* -> user→role). Silent gaps are the enemy.
"""
import sqlite3
import re
import json
from pathlib import Path

_PROG_RE = re.compile(r"RS38M-PROGRAMM=([A-Z0-9_/]+)")
_VIEW_RE = re.compile(r"VIEWNAME=([A-Z0-9_/]+)")


def _load_anchor_names(brain, cur):
    """The BOUNDED set of names worth wiring tcodes to. Deliberately NOT 'every
    node name' — that matched the whole parsed-code universe and exploded the graph
    with ~100K orphan program nodes (s079 lesson). Anchor = only:
      * existing TRANSACTION nodes (the 414 CTS tcodes + the process-spine tcodes),
      * tcodes actually used in postings (bkpf.TCODE),
      * every object referenced in our structured records (claims/incidents/annotations).
    So wiring grows with what we KNOW (process spine + real usage + reasoning),
    not with the existence of any parsed program."""
    anchors = set()
    for _, data in brain.G.nodes(data=True):
        if data.get("type") == "TRANSACTION":
            nm = data.get("name")
            if nm:
                anchors.add(nm)
    try:
        for (tc,) in cur.execute("SELECT DISTINCT TCODE FROM bkpf WHERE TCODE <> ''"):
            anchors.add(tc)
    except Exception:
        pass
    root = Path(__file__).resolve().parents[2]
    for rel in ("brain_v2/claims/claims.json", "brain_v2/incidents/incidents.json"):
        p = root / rel
        if p.exists():
            for rec in json.load(open(p, encoding="utf-8")):
                anchors.update(rec.get("related_objects", []))
    ann = root / "brain_v2/annotations/annotations.json"
    if ann.exists():
        anchors.update(json.load(open(ann, encoding="utf-8")).keys())
    return anchors

# TADIR object type -> (graph node type, id prefix). id prefix == node type for
# these, which matches the existing graph id convention (ABAP_REPORT:NAME, ...).
TADIR_MAP = {
    "PROG": "ABAP_REPORT",
    "CLAS": "ABAP_CLASS",
    "FUGR": "FUNCTION_MODULE",
    "TABL": "SAP_TABLE",
    "TRAN": "TRANSACTION",
    "DTEL": "DATA_ELEMENT",
    "DOMA": "DOMAIN_OBJECT",
    "ENHO": "ENHANCEMENT",
    "ENHS": "ENHANCEMENT",
}

# Tables we WANT for a complete web but that are not yet in the Gold DB.
# (tadir_enrichment holds only CUSTOMIZING objects — VDAT/TABU/OSOA/VARX — not
#  code, so object->package for PROG/CLAS/FUGR needs the real TADIR.)
EXTRACTION_BACKLOG = [
    ("MODSAP/SMOD/CMOD", "ENHANCEMENT -ENHANCES-> PROGRAM (user exits <-> their program)"),
    ("TADIR (code objs)", "PROG/CLAS/FUGR -BELONGS_TO_PACKAGE-> PACKAGE (ownership of code)"),
    ("USR02", "USER master (valid-from, lock status, user type) to enrich USER nodes"),
    ("AGR_USERS/AGR_1251", "USER -HAS_ROLE-> ROLE -GRANTS-> AUTH (the authorization web)"),
    ("TRDIR",  "PROGRAM attributes (author, type) to enrich program nodes"),
]


def ingest_connective(brain, db_path):
    """Add behavioural + ownership edges from the Gold DB. Returns a stats dict."""
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    stats = {"users": 0, "operates": 0, "used_in_cc": 0, "packages": 0,
             "belongs_to_package": 0, "job_runs_program": 0, "scheduled_by": 0,
             "executes_program": 0, "maintains_view": 0,
             "backlog": EXTRACTION_BACKLOG}

    def has(node_id):
        return brain.has_node(node_id)

    def _table_exists(name):
        return cur.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
        ).fetchone() is not None

    # ---- 1. USER layer + USER-OPERATES_TCODE->TRANSACTION  (from bkpf) ----
    # Aggregate so we add ~4,861 edges, not 1.8M.
    rows = cur.execute(
        "SELECT USNAM, TCODE, COUNT(*) AS n FROM bkpf "
        "WHERE USNAM <> '' AND TCODE <> '' GROUP BY USNAM, TCODE"
    ).fetchall()
    seen_users = set()
    for usnam, tcode, n in rows:
        uid = f"USER:{usnam}"
        if usnam not in seen_users:
            brain.add_node(uid, "USER", usnam, layer="org",
                           source="bkpf.USNAM", domain="Security")
            seen_users.add(usnam)
            stats["users"] += 1
        tid = f"TRANSACTION:{tcode}"
        if not has(tid):
            brain.add_node(tid, "TRANSACTION", tcode, layer="code",
                           source="bkpf.TCODE")
        brain.add_edge(uid, tid, "OPERATES_TCODE",
                       label=f"{n} docs", weight=min(1.0, n / 1000.0),
                       evidence="gold_db", discovered_in="s079")
        stats["operates"] += 1

    # ---- 2. TRANSACTION-USED_IN_CC->COMPANY_CODE  (from bkpf) ----
    rows = cur.execute(
        "SELECT DISTINCT TCODE, BUKRS FROM bkpf WHERE TCODE <> '' AND BUKRS <> ''"
    ).fetchall()
    for tcode, bukrs in rows:
        tid = f"TRANSACTION:{tcode}"
        cid = f"COCODE:{bukrs}"
        if not has(cid):
            brain.add_node(cid, "COMPANY_CODE", bukrs, layer="org", source="bkpf.BUKRS")
        if has(tid):
            brain.add_edge(tid, cid, "USED_IN_CC", evidence="gold_db", discovered_in="s079")
            stats["used_in_cc"] += 1

    # ---- 3. object-BELONGS_TO_PACKAGE->PACKAGE  (from tadir_enrichment) ----
    rows = cur.execute(
        "SELECT obj_type, obj_name, devclass FROM tadir_enrichment "
        "WHERE devclass <> ''"
    ).fetchall()
    seen_pkg = set()
    for obj_type, obj_name, devclass in rows:
        ntype = TADIR_MAP.get(obj_type)
        if not ntype:
            continue
        oid = f"{ntype}:{obj_name}"
        if not has(oid):  # only enrich objects we actually have as nodes
            continue
        pid = f"PACKAGE:{devclass}"
        if not has(pid):  # create package node only when it owns a real node
            brain.add_node(pid, "PACKAGE", devclass, layer="code", source="tadir_enrichment")
            stats["packages"] += 1
        brain.add_edge(oid, pid, "BELONGS_TO_PACKAGE", evidence="gold_db", discovered_in="s079")
        stats["belongs_to_package"] += 1

    # ---- 4. JOB-RUNS_PROGRAM->PROGRAM  (from tbtcp) ----
    # 18,351 distinct jobnames exist; only create a JOB node when its program is
    # a real node in the graph, otherwise we'd add thousands of orphan instances.
    rows = cur.execute(
        "SELECT DISTINCT JOBNAME, PROGNAME FROM tbtcp WHERE PROGNAME <> ''"
    ).fetchall()
    for jobname, progname in rows:
        pid = f"ABAP_REPORT:{progname}"
        if not has(pid):
            continue
        jid = f"JOB:{jobname}"
        if not has(jid):
            brain.add_node(jid, "JOB_DEFINITION", jobname, layer="process", source="tbtco")
        brain.add_edge(jid, pid, "RUNS_PROGRAM", evidence="gold_db", discovered_in="s079")
        stats["job_runs_program"] += 1

    # ---- 5. TRANSACTION-EXECUTES_PROGRAM->PROGRAM + MAINTAINS_VIEW->TABLE ----
    # From TSTC (dialog tcodes -> PGMNA) and TSTCP (report/param tcodes:
    # RS38M-PROGRAMM=<prog>, VIEWNAME=<view>). Anchored: only wire a tcode when
    # the tcode OR its target is something we already know (a node, or referenced
    # in our claims/incidents). This is what finally connects F.05->SAPF100 and
    # OB09->T030H. The target node is created if missing (so SAPF100 becomes real).
    # NOTE: tstc/tstct/tstcp were extracted from D01 (per user instruction) and are
    # named d01_* to preserve provenance — the Gold DB is otherwise P01. Transaction
    # definitions are SAP-standard and system-invariant, so D01 is a valid content
    # source for the tcode->program/view mapping. Never let a d01_ table back a claim
    # that asserts a P01 *data* fact (see verify_claims.py provenance guard).
    if _table_exists("d01_tstc"):
        anchors = _load_anchor_names(brain, cur)

        def wire(tcode, target_name, target_ntype, edge_type, stat_key):
            if not tcode or not target_name:
                return
            # strip leading slashes / namespaces commonly seen in PARAM
            target_name = target_name.strip("/")
            if tcode not in anchors and target_name not in anchors:
                return
            tid = f"TRANSACTION:{tcode}"
            if not has(tid):
                brain.add_node(tid, "TRANSACTION", tcode, layer="code", source="TSTC")
            oid = f"{target_ntype}:{target_name}"
            if not has(oid):
                brain.add_node(oid, target_ntype, target_name, layer="code",
                               source="TSTC/TSTCP")
            brain.add_edge(tid, oid, edge_type, evidence="gold_db", discovered_in="s079")
            stats[stat_key] += 1

        # TSTC: direct dialog tcode -> program
        for tcode, pgmna in cur.execute(
                "SELECT TCODE, PGMNA FROM d01_tstc WHERE PGMNA <> ''").fetchall():
            wire(tcode, pgmna, "ABAP_REPORT", "EXECUTES_PROGRAM", "executes_program")

        # TSTCP: report/parameter tcodes -> program (RS38M-PROGRAMM) and view (VIEWNAME)
        if _table_exists("d01_tstcp"):
            for tcode, param in cur.execute(
                    "SELECT TCODE, PARAM FROM d01_tstcp WHERE PARAM <> ''").fetchall():
                mp = _PROG_RE.search(param or "")
                if mp:
                    wire(tcode, mp.group(1), "ABAP_REPORT", "EXECUTES_PROGRAM", "executes_program")
                mv = _VIEW_RE.search(param or "")
                if mv:
                    view = mv.group(1)
                    # OB09 -> V_T030H: also try the base table (strip leading V_)
                    base = view[2:] if view.startswith("V_") else view
                    target = base if has(f"SAP_TABLE:{base}") else view
                    wire(tcode, target, "SAP_TABLE", "MAINTAINS_VIEW", "maintains_view")

    con.close()
    return stats
