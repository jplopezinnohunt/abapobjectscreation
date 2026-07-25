"""
snapshot_model_state.py — the MODEL and its MATURITY as TABLES (the curve is the deliverable).
==============================================================================================
WHY THIS EXISTS
---------------
`capability_model/maturity.json`, `gold_extractor_maturity.json`, `meta_capability.json` and
`claims_health.json` are OVERWRITTEN on every rebuild. Each one keeps exactly ONE point in time.
For a product whose thesis is "measured understanding", the CURVE is the deliverable — and today
only the last dot exists. This script appends, on every run, a full immutable snapshot of the
model state into its own SQLite DB so the time series survives.

DESIGN (decision D9 — do not re-litigate)
-----------------------------------------
* SOURCES stay in JSON/git (ontology.json, capability_model.json cells + their `note`).
  `capability_model.json` has 0 programmatic writers ON PURPOSE. This script NEVER writes it.
* Only MEASUREMENTS become tables, here, in a MODEL DB of its own (layer P — small, backup-able).
  NOT the golden DB (layer T, 14.2 GB, gitignored). This script never opens the golden.
* HISTORY = one row per rebuild, no dedupe. "It was measured and it did not change" is exactly
  what makes the curve credible to an auditor. Tables are CREATE TABLE IF NOT EXISTS and are
  never dropped — this DB is APPEND-ONLY and is NOT reproducible from current state.

ORDERING (why this is a separate script and not part of build_active_db.py)
--------------------------------------------------------------------------
`build_active_db.py` runs as Step 2 of rebuild_all.py, but `maturity_score.py` (which writes
maturity.json) runs later, as Step 3b. Snapshotting from inside Step 2 would capture the
PREVIOUS run's measurements — silently off by one rebuild, forever. So this is a standalone
script meant to run AFTER Step 3b.

Usage:
    python brain_v2/capability_model/snapshot_model_state.py
    python brain_v2/capability_model/snapshot_model_state.py --tenant UNESCO --system-role P01
    python brain_v2/capability_model/snapshot_model_state.py --db some/other/model_state.db
    python brain_v2/capability_model/snapshot_model_state.py --dry-run   # read + report, no write
"""
import argparse
import hashlib
import json
import os
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent                     # brain_v2/capability_model
BRAIN = HERE.parent                              # brain_v2
ROOT = BRAIN.parent                              # project root

# ---- sources (all read-only) -------------------------------------------------------------
SRC = {
    "ontology":          HERE / "ontology.json",
    "capability_model":  HERE / "capability_model.json",
    "maturity":          HERE / "maturity.json",
    "applied_models":    HERE / "applied_models.json",
    "extractor":         BRAIN / "gold_extractor_maturity.json",
    "meta_capability":   BRAIN / "meta_capability.json",
    "claims_health":     BRAIN / "claims_health.json",
}

# NOT under brain_v2/output/. Everything else there is generated-and-reconstructible, so the
# whole directory is treated as disposable (and is gitignored wholesale, .gitignore L134). This
# DB is the ONLY copy of the time series — a `rm -rf brain_v2/output/` would delete the curve
# itself. It lives in its own directory, ignored by an EXPLICIT rule rather than by inheriting
# one. (Orchestrator decision, Ola 2 — the inverse of the Ola 1 finding, where an inherited
# .gitignore rule silently kept the whole extraction engine out of git.)
DEFAULT_DB = BRAIN / "model_state" / "model_state.db"
LEDGER = HERE / "maturity_history.jsonl"         # tiny, git-friendly durability copy

CELL_SCORE = {"NONE": 0.0, "PARTIAL": 0.5, "HAVE": 1.0}
TIERS = ("HAVE", "PARTIAL", "NONE")

# how stale a measurement file may be before we flag it in snapshot_run.sources_json
STALE_DAYS = 3


# =========================================================================================
# schema
# =========================================================================================
SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshot_run (
    run_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id     TEXT NOT NULL,
    system_role   TEXT NOT NULL,
    measured_at   TEXT NOT NULL,          -- ISO-8601 UTC, microsecond, one value per run
    git_commit    TEXT,
    tool_version  TEXT,
    sources_json  TEXT,                   -- {alias: {path, present, mtime, sha256, bytes, stale}}
    note          TEXT
);
CREATE INDEX IF NOT EXISTS idx_run_measured_at ON snapshot_run(measured_at);

-- ---------- conformed dimensions (snapshotted per run: an old score must be readable
-- ---------- against the ontology that was in force when it was taken) ---------------------
CREATE TABLE IF NOT EXISTS dim_domain (
    run_id              INTEGER NOT NULL REFERENCES snapshot_run(run_id),
    tenant_id           TEXT NOT NULL,
    system_role         TEXT NOT NULL,
    measured_at         TEXT NOT NULL,
    canonical_key       TEXT NOT NULL,
    aliases             TEXT,             -- JSON list
    parent              TEXT,
    subdomains          TEXT,             -- JSON list
    in_capability_model INTEGER NOT NULL DEFAULT 0,
    registry_keys       TEXT,             -- JSON list
    module_axis         TEXT,             -- JSON list
    process_axis        TEXT,             -- JSON list
    note                TEXT,
    PRIMARY KEY (run_id, canonical_key)
);

CREATE TABLE IF NOT EXISTS dim_dimension (
    run_id          INTEGER NOT NULL REFERENCES snapshot_run(run_id),
    tenant_id       TEXT NOT NULL,
    system_role     TEXT NOT NULL,
    measured_at     TEXT NOT NULL,
    dimension_key   TEXT NOT NULL,
    ordinal         INTEGER,
    question        TEXT,
    method          TEXT,
    method_tier     TEXT,                 -- VERIFIED | OWN | GAP
    advance_path    TEXT,                 -- NO_EXTRACTION | EXTRACTION | MIXED
    is_precondition_for TEXT,
    note            TEXT,
    PRIMARY KEY (run_id, dimension_key)
);

-- ---------- the matrix itself, as measured on this run ------------------------------------
CREATE TABLE IF NOT EXISTS model_cell (
    run_id          INTEGER NOT NULL REFERENCES snapshot_run(run_id),
    tenant_id       TEXT NOT NULL,
    system_role     TEXT NOT NULL,
    measured_at     TEXT NOT NULL,
    scope_level     TEXT NOT NULL,        -- DOMAIN | SUBDOMAIN
    domain_key      TEXT NOT NULL,        -- canonical_key
    subdomain_key   TEXT NOT NULL DEFAULT '',
    dimension_key   TEXT NOT NULL,
    tier            TEXT NOT NULL,        -- HAVE | PARTIAL | NONE
    tier_score      REAL NOT NULL,        -- 1.0 | 0.5 | 0.0
    PRIMARY KEY (run_id, domain_key, subdomain_key, dimension_key)
);
CREATE INDEX IF NOT EXISTS idx_cell_dim ON model_cell(dimension_key, tier);
CREATE INDEX IF NOT EXISTS idx_cell_dom ON model_cell(domain_key, subdomain_key);

-- ---------- movement of a cell = an EVENT (append-only, deduped by dedupe_key) -------------
CREATE TABLE IF NOT EXISTS model_cell_move (
    move_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id          INTEGER NOT NULL REFERENCES snapshot_run(run_id),
    tenant_id       TEXT NOT NULL,
    system_role     TEXT NOT NULL,
    measured_at     TEXT NOT NULL,        -- when the move was RECORDED (not when it happened)
    scope_level     TEXT NOT NULL,
    domain_key      TEXT NOT NULL,
    subdomain_key   TEXT NOT NULL DEFAULT '',
    dimension_key   TEXT NOT NULL,
    from_tier       TEXT,                 -- NULL when the source prose does not state it
    to_tier         TEXT NOT NULL,
    moved_session   TEXT,                 -- 's083' etc; NULL when not derivable
    origin          TEXT NOT NULL,        -- BACKFILL | OBSERVED
    extraction_rule TEXT NOT NULL,        -- exactly which rule produced this row
    source_file     TEXT,
    evidence        TEXT,                 -- verbatim source substring (audit trail)
    dedupe_key      TEXT NOT NULL UNIQUE
);
CREATE INDEX IF NOT EXISTS idx_move_cell ON model_cell_move(domain_key, subdomain_key, dimension_key);

-- ---------- measurements ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS maturity_score (
    run_id           INTEGER NOT NULL REFERENCES snapshot_run(run_id),
    tenant_id        TEXT NOT NULL,
    system_role      TEXT NOT NULL,
    measured_at      TEXT NOT NULL,
    scope_type       TEXT NOT NULL,       -- MODEL | CAPABILITY | DOMAIN | SUBDOMAIN | GAP_SPLIT
    scope_key        TEXT NOT NULL,       -- '*' for MODEL; dim key; domain key; 'Domain.sub'
    score            REAL,                -- percent 0..100 (GAP_SPLIT rows carry raw units)
    unit             TEXT NOT NULL DEFAULT 'pct',
    parent_scope_key TEXT,
    method_tier      TEXT,
    method_available INTEGER,
    advance_path     TEXT,
    n_have           INTEGER,
    n_partial        INTEGER,
    n_none           INTEGER,
    PRIMARY KEY (run_id, scope_type, scope_key)
);
CREATE INDEX IF NOT EXISTS idx_mat_scope ON maturity_score(scope_type, scope_key, measured_at);

CREATE TABLE IF NOT EXISTS extractor_maturity (
    run_id       INTEGER NOT NULL REFERENCES snapshot_run(run_id),
    tenant_id    TEXT NOT NULL,
    system_role  TEXT NOT NULL,
    measured_at  TEXT NOT NULL,
    scope_type   TEXT NOT NULL,           -- OVERALL | DOMAIN | TYPE | TABLE
    scope_key    TEXT NOT NULL,
    score        REAL,                    -- percent 0..100
    unit         TEXT NOT NULL DEFAULT 'pct',
    n            INTEGER,
    level        INTEGER,                 -- TABLE rows: ladder level 0..4
    ladder       TEXT,                    -- TABLE rows: L0_unclassified .. L4_synced_verified
    table_type   TEXT,
    domain_key   TEXT,
    source       TEXT,
    dist_json    TEXT,
    PRIMARY KEY (run_id, scope_type, scope_key)
);
CREATE INDEX IF NOT EXISTS idx_extr_scope ON extractor_maturity(scope_type, scope_key, measured_at);

CREATE TABLE IF NOT EXISTS meta_capability (
    run_id           INTEGER NOT NULL REFERENCES snapshot_run(run_id),
    tenant_id        TEXT NOT NULL,
    system_role      TEXT NOT NULL,
    measured_at      TEXT NOT NULL,
    scope_type       TEXT NOT NULL,       -- META | DIMENSION | SUB
    scope_key        TEXT NOT NULL,       -- '*' | 'EXTRACT' | 'EXTRACT.registry_resolver'
    score            REAL,                -- percent 0..100
    unit             TEXT NOT NULL DEFAULT 'pct',
    parent_scope_key TEXT,
    src              TEXT,                -- 'M' measured / 'E' estimated
    is_weakest       INTEGER NOT NULL DEFAULT 0,
    note             TEXT,
    PRIMARY KEY (run_id, scope_type, scope_key)
);
CREATE INDEX IF NOT EXISTS idx_meta_scope ON meta_capability(scope_type, scope_key, measured_at);

CREATE TABLE IF NOT EXISTS claims_health (
    run_id       INTEGER NOT NULL REFERENCES snapshot_run(run_id),
    tenant_id    TEXT NOT NULL,
    system_role  TEXT NOT NULL,
    measured_at  TEXT NOT NULL,
    metric_type  TEXT NOT NULL,           -- TOTAL | BUCKET | RATE | WORKLIST
    metric_key   TEXT NOT NULL,           -- 'live' | 'STRONG' | 'verification_rate' | 'weak_tier1'
    value        REAL,
    unit         TEXT NOT NULL DEFAULT 'count',
    detail_json  TEXT,
    PRIMARY KEY (run_id, metric_type, metric_key)
);
CREATE INDEX IF NOT EXISTS idx_claims_metric ON claims_health(metric_type, metric_key, measured_at);
"""

TOOL_VERSION = "snapshot_model_state/1.0.0"


# =========================================================================================
# helpers
# =========================================================================================
def _now():
    return datetime.now(timezone.utc).isoformat()


def _sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(path):
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _git_commit():
    try:
        out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=str(ROOT),
                             capture_output=True, text=True, timeout=10)
        return out.stdout.strip() or None
    except Exception:
        return None


def _source_manifest(now_iso):
    now_ts = datetime.now(timezone.utc).timestamp()
    man = {}
    for alias, path in SRC.items():
        if not path.exists():
            man[alias] = {"path": str(path.relative_to(ROOT)).replace("\\", "/"), "present": False}
            continue
        st = path.stat()
        age_days = (now_ts - st.st_mtime) / 86400.0
        man[alias] = {
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "present": True,
            "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(),
            "bytes": st.st_size,
            "sha256": _sha(path),
            "age_days": round(age_days, 2),
            "stale": age_days > STALE_DAYS,
        }
    return man


# =========================================================================================
# loaders
# =========================================================================================
def load_dim_domain(conn, ctx, ontology):
    """17 canonical domains from the C-1 ontology contract."""
    if not ontology:
        return 0
    rows = 0
    for d in ontology.get("domains", []):
        conn.execute(
            """INSERT OR REPLACE INTO dim_domain
               (run_id, tenant_id, system_role, measured_at, canonical_key, aliases, parent,
                subdomains, in_capability_model, registry_keys, module_axis, process_axis, note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ctx["run_id"], ctx["tenant"], ctx["system"], ctx["at"],
             d["canonical_key"],
             json.dumps(d.get("aliases", []), ensure_ascii=False),
             d.get("parent"),
             json.dumps(d.get("subdomains", []), ensure_ascii=False),
             1 if d.get("in_capability_model") else 0,
             json.dumps(d.get("registry_keys", []), ensure_ascii=False),
             json.dumps(d.get("module_axis", []), ensure_ascii=False),
             json.dumps(d.get("process_axis", []), ensure_ascii=False),
             d.get("_note")))
        rows += 1
    return rows


def load_dim_dimension(conn, ctx, model, maturity):
    """11 capability dimensions. advance_path is taken from maturity.json when present
    (it is the value maturity_score.py actually used), else from the dimension def."""
    if not model:
        return 0
    by_cap = (maturity or {}).get("level1_by_capability", {})
    rows = 0
    for i, (key, d) in enumerate(model.get("dimensions", {}).items()):
        advance = (by_cap.get(key) or {}).get("advance_path") or d.get("advance_path")
        conn.execute(
            """INSERT OR REPLACE INTO dim_dimension
               (run_id, tenant_id, system_role, measured_at, dimension_key, ordinal,
                question, method, method_tier, advance_path, is_precondition_for, note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ctx["run_id"], ctx["tenant"], ctx["system"], ctx["at"], key, i,
             d.get("question"), d.get("method"), d.get("method_tier"), advance,
             d.get("is_precondition_for"), d.get("note")))
        rows += 1
    return rows


def iter_cells(model):
    """Yield (scope_level, domain, subdomain, dimension, tier) for every cell in the matrix."""
    dims = list(model["dimensions"].keys())
    for dom, cov in model["domains"].items():
        for dk in dims:
            yield ("DOMAIN", dom, "", dk, cov.get(dk, "NONE"))
        for sub, scells in (cov.get("subdomains") or {}).items():
            if not isinstance(scells, dict):
                continue
            for dk in dims:
                yield ("SUBDOMAIN", dom, sub, dk, scells.get(dk, "NONE"))


def load_model_cell(conn, ctx, model):
    if not model:
        return 0
    rows = 0
    for level, dom, sub, dk, tier in iter_cells(model):
        tier = tier if tier in CELL_SCORE else "NONE"
        conn.execute(
            """INSERT OR REPLACE INTO model_cell
               (run_id, tenant_id, system_role, measured_at, scope_level,
                domain_key, subdomain_key, dimension_key, tier, tier_score)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (ctx["run_id"], ctx["tenant"], ctx["system"], ctx["at"], level,
             dom, sub, dk, tier, CELL_SCORE[tier]))
        rows += 1
    return rows


def load_maturity_score(conn, ctx, maturity):
    """maturity.json -> (scope_type, scope_key, score) rows. GAP_SPLIT rows carry raw units."""
    if not maturity:
        return 0
    ins = []
    ins.append(("MODEL", "*", maturity.get("model_maturity_pct"), "pct",
                None, None, None, None, None, None, None))

    for key, v in (maturity.get("level1_by_capability") or {}).items():
        ins.append(("CAPABILITY", key, v.get("maturity_pct"), "pct", "*",
                    v.get("method_tier"), 1 if v.get("method_available") else 0,
                    v.get("advance_path"), v.get("have"), v.get("partial"), v.get("none")))

    for key, v in (maturity.get("level2_by_domain") or {}).items():
        cells = v.get("cells") or {}
        ins.append(("DOMAIN", key, v.get("maturity_pct"), "pct", "*", None, None, None,
                    sum(1 for t in cells.values() if t == "HAVE"),
                    sum(1 for t in cells.values() if t == "PARTIAL"),
                    sum(1 for t in cells.values() if t == "NONE")))

    for key, v in (maturity.get("level3_by_subdomain") or {}).items():
        cells = v.get("cells") or {}
        ins.append(("SUBDOMAIN", key, v.get("maturity_pct"), "pct", v.get("domain"), None, None, None,
                    sum(1 for t in cells.values() if t == "HAVE"),
                    sum(1 for t in cells.values() if t == "PARTIAL"),
                    sum(1 for t in cells.values() if t == "NONE")))

    gs = maturity.get("gap_split") or {}
    for key, val in gs.items():
        unit = "pct" if key.endswith("_pct") or key.startswith("pct_") else "cell_units"
        ins.append(("GAP_SPLIT", key, val, unit, "*", None, None, None, None, None, None))

    for row in ins:
        conn.execute(
            """INSERT OR REPLACE INTO maturity_score
               (run_id, tenant_id, system_role, measured_at, scope_type, scope_key, score, unit,
                parent_scope_key, method_tier, method_available, advance_path,
                n_have, n_partial, n_none)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ctx["run_id"], ctx["tenant"], ctx["system"], ctx["at"]) + row)
    return len(ins)


def load_extractor_maturity(conn, ctx, extr):
    """gold_extractor_maturity.json. Scores normalised to PERCENT (source mixes pct and 0..1)."""
    if not extr:
        return 0
    rows = []
    rows.append(("OVERALL", "*", extr.get("overall_pct"), extr.get("n_tables"),
                 None, None, None, None, None, None))
    for dom, v in (extr.get("by_domain") or {}).items():
        rows.append(("DOMAIN", dom, round(100.0 * v.get("score", 0.0), 1), v.get("n"),
                     None, None, None, dom, None,
                     json.dumps(v.get("dist", {}), ensure_ascii=False)))
    for t, v in (extr.get("by_type") or {}).items():
        rows.append(("TYPE", t, round(100.0 * v.get("score", 0.0), 1), v.get("n"),
                     None, None, t, None, None,
                     json.dumps(v.get("dist", {}), ensure_ascii=False) if v.get("dist") else None))
    for tb in (extr.get("tables") or []):
        key = "%s|%s" % (tb.get("domain"), tb.get("gold"))
        lvl = tb.get("level")
        rows.append(("TABLE", key, round(100.0 * (lvl / 4.0), 1) if lvl is not None else None, 1,
                     lvl, tb.get("ladder"), tb.get("type"), tb.get("domain"),
                     tb.get("source"), None))

    for r in rows:
        conn.execute(
            """INSERT OR REPLACE INTO extractor_maturity
               (run_id, tenant_id, system_role, measured_at, scope_type, scope_key, score, n,
                level, ladder, table_type, domain_key, source, dist_json)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (ctx["run_id"], ctx["tenant"], ctx["system"], ctx["at"],
             r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9]))
    return len(rows)


def load_meta_capability(conn, ctx, meta):
    """meta_capability.json — our own way of working (7 capabilities x sub-levers)."""
    if not meta:
        return 0
    weakest = meta.get("weakest") or meta.get("weakest_dim")
    rows = [("META", "*", meta.get("meta_maturity_pct"), None, None, 0, meta.get("doc"))]
    for dim, v in (meta.get("dimensions") or {}).items():
        rows.append(("DIMENSION", dim, round(100.0 * v.get("score", 0.0), 1), "*", None,
                     1 if dim == weakest else 0, None))
        for sub in (v.get("subs") or []):
            rows.append(("SUB", "%s.%s" % (dim, sub.get("name")),
                         round(100.0 * sub.get("score", 0.0), 1), dim,
                         sub.get("src"), 0, sub.get("note")))
    for r in rows:
        conn.execute(
            """INSERT OR REPLACE INTO meta_capability
               (run_id, tenant_id, system_role, measured_at, scope_type, scope_key, score,
                parent_scope_key, src, is_weakest, note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (ctx["run_id"], ctx["tenant"], ctx["system"], ctx["at"],
             r[0], r[1], r[2], r[3], r[4], r[5], r[6]))
    return len(rows)


def load_claims_health(conn, ctx, health):
    if not health:
        return 0
    rows = [("TOTAL", "live", health.get("live"), "count", None),
            ("RATE", "verification_rate", health.get("verification_rate"), "pct", None)]
    for bucket, n in (health.get("buckets") or {}).items():
        rows.append(("BUCKET", bucket, n, "count", None))
    wl = health.get("weak_tier1_worklist") or []
    rows.append(("WORKLIST", "weak_tier1", len(wl), "count",
                 json.dumps([c.get("id") for c in wl], ensure_ascii=False)))
    for r in rows:
        conn.execute(
            """INSERT OR REPLACE INTO claims_health
               (run_id, tenant_id, system_role, measured_at, metric_type, metric_key,
                value, unit, detail_json)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (ctx["run_id"], ctx["tenant"], ctx["system"], ctx["at"],
             r[0], r[1], r[2], r[3], r[4]))
    return len(rows)


# =========================================================================================
# model_cell_move — the movement history
# =========================================================================================
def _insert_move(conn, ctx, *, level, dom, sub, dim, from_tier, to_tier, session,
                 origin, rule, source_file, evidence, dedupe_key):
    cur = conn.execute(
        """INSERT OR IGNORE INTO model_cell_move
           (run_id, tenant_id, system_role, measured_at, scope_level, domain_key,
            subdomain_key, dimension_key, from_tier, to_tier, moved_session, origin,
            extraction_rule, source_file, evidence, dedupe_key)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (ctx["run_id"], ctx["tenant"], ctx["system"], ctx["at"], level, dom, sub, dim,
         from_tier, to_tier, session, origin, rule, source_file,
         (evidence or "")[:400], dedupe_key))
    return cur.rowcount


def detect_observed_moves(conn, ctx, model):
    """The real mechanism going forward: diff this run's cells against the previous run's.
    from_tier and to_tier are both KNOWN here — no prose parsing, no guessing."""
    prev = conn.execute(
        "SELECT MAX(run_id) FROM snapshot_run WHERE run_id < ? AND tenant_id = ? AND system_role = ?",
        (ctx["run_id"], ctx["tenant"], ctx["system"])).fetchone()[0]
    if prev is None:
        return 0, None
    old = {(d, s, k): t for d, s, k, t in conn.execute(
        "SELECT domain_key, subdomain_key, dimension_key, tier FROM model_cell WHERE run_id = ?",
        (prev,))}
    n = 0
    for level, dom, sub, dim, tier in iter_cells(model):
        tier = tier if tier in CELL_SCORE else "NONE"
        was = old.get((dom, sub, dim))
        if was is None or was == tier:
            continue
        n += _insert_move(
            conn, ctx, level=level, dom=dom, sub=sub, dim=dim,
            from_tier=was, to_tier=tier, session=None, origin="OBSERVED",
            rule="OBSERVED_RUN_DIFF",
            source_file="brain_v2/capability_model/capability_model.json",
            evidence="run %d -> run %d" % (prev, ctx["run_id"]),
            dedupe_key="OBS|%d|%s|%s|%s|%s|%s" % (ctx["run_id"], dom, sub, dim, was, tier))
    return n, prev


def backfill_moves(conn, ctx, model, applied):
    """Deterministic extraction of the movement history that exists ONLY as prose.

    Four rules, each recorded in `extraction_rule` with the verbatim `evidence` substring.
    Nothing is inferred beyond what the text literally states; `from_tier` stays NULL unless
    the source spells it out.
    """
    stats = {"NOTE_DIM_TIER_SESSION": 0, "NOTE_CHAINED_DIM_TIER_SESSION": 0,
             "NOTE_WAS_CLAUSE": 0, "APPLIED_MODELS_CELLS_MOVED": 0,
             "SKIPPED_STAYS": 0}
    if not model:
        return stats

    dims = list(model["dimensions"].keys())
    D = "|".join(re.escape(d) for d in dims)
    T = "|".join(TIERS)
    p_plain = re.compile(r"\b(%s)\s+(%s)\s+s(\d{3})" % (D, T))
    p_chain = re.compile(r"\b(%s)\s+(%s)\s*\+\s*(%s)\s+(%s)\s+s(\d{3})" % (D, T, D, T))
    p_was = re.compile(r"\b(%s)\s+(%s)\s*\(was\s+(%s)\)" % (D, T, T))
    p_sess = re.compile(r"\bs(\d{3})\b")
    src_model = "brain_v2/capability_model/capability_model.json"

    notes = []
    for dom, cov in model["domains"].items():
        if cov.get("note"):
            notes.append(("DOMAIN", dom, "", cov["note"]))
        for sub, scells in (cov.get("subdomains") or {}).items():
            if isinstance(scells, dict) and scells.get("note"):
                notes.append(("SUBDOMAIN", dom, sub, scells["note"]))

    for level, dom, sub, note in notes:
        # RULE 1 — "<DIM> <TIER> sNNN:" — the destination tier and the session are explicit.
        for m in p_plain.finditer(note):
            dim, to, sess = m.group(1), m.group(2), "s" + m.group(3)
            stats["NOTE_DIM_TIER_SESSION"] += _insert_move(
                conn, ctx, level=level, dom=dom, sub=sub, dim=dim, from_tier=None,
                to_tier=to, session=sess, origin="BACKFILL",
                rule="BACKFILL_NOTE_DIM_TIER_SESSION", source_file=src_model,
                evidence=note[max(0, m.start() - 10):m.end() + 60],
                dedupe_key="BF|R1|%s|%s|%s|%s|%s" % (dom, sub, dim, sess, to))

        # RULE 2 — "<DIM> <TIER> + <DIM> <TIER> sNNN" — the session governs BOTH; rule 1 only
        # catches the second half, so the first half is recovered here.
        for m in p_chain.finditer(note):
            dim, to, sess = m.group(1), m.group(2), "s" + m.group(5)
            stats["NOTE_CHAINED_DIM_TIER_SESSION"] += _insert_move(
                conn, ctx, level=level, dom=dom, sub=sub, dim=dim, from_tier=None,
                to_tier=to, session=sess, origin="BACKFILL",
                rule="BACKFILL_NOTE_CHAINED_DIM_TIER_SESSION", source_file=src_model,
                evidence=note[max(0, m.start() - 10):m.end() + 40],
                dedupe_key="BF|R2|%s|%s|%s|%s|%s" % (dom, sub, dim, sess, to))

        # RULE 3 — "<DIM> <TIER> (was <TIER>)" — the ONLY prose form that states from_tier.
        # Session = the nearest sNNN appearing BEFORE the match (deterministic, not "the first").
        for m in p_was.finditer(note):
            dim, to, frm = m.group(1), m.group(2), m.group(3)
            before = [s for s in p_sess.finditer(note[:m.start()])]
            sess = "s" + before[-1].group(1) if before else None
            stats["NOTE_WAS_CLAUSE"] += _insert_move(
                conn, ctx, level=level, dom=dom, sub=sub, dim=dim, from_tier=frm,
                to_tier=to, session=sess, origin="BACKFILL",
                rule="BACKFILL_NOTE_WAS_CLAUSE", source_file=src_model,
                evidence=note[max(0, m.start() - 40):m.end() + 40],
                dedupe_key="BF|R3|%s|%s|%s|%s|%s|%s" % (dom, sub, dim, sess, frm, to))

    # RULE 4 — applied_models.json `cells_moved`, present exactly ONCE and in prose.
    if applied:
        sess = "s" + str(applied.get("_created_session")) if applied.get("_created_session") else None
        p_arrow = re.compile(r"\b(%s)\s*->\s*(%s)" % (D, T))
        p_stay = re.compile(r"\b(%s)\s+stays\s+(%s)" % (D, T))
        for dom, blk in (applied.get("applied_by_domain") or {}).items():
            if not isinstance(blk, dict):
                continue
            cm = blk.get("cells_moved")
            if not cm:
                continue
            for m in p_arrow.finditer(cm):
                dim, to = m.group(1), m.group(2)
                stats["APPLIED_MODELS_CELLS_MOVED"] += _insert_move(
                    conn, ctx, level="DOMAIN", dom=dom, sub="", dim=dim, from_tier=None,
                    to_tier=to, session=sess, origin="BACKFILL",
                    rule="BACKFILL_APPLIED_MODELS_CELLS_MOVED",
                    source_file="brain_v2/capability_model/applied_models.json",
                    evidence=cm,
                    dedupe_key="BF|R4|%s||%s|%s|%s" % (dom, dim, sess, to))
            # "<DIM> stays <TIER>" is explicitly NOT a move — counted, never inserted.
            stats["SKIPPED_STAYS"] += len(p_stay.findall(cm))
    return stats


def backfill_coverage(conn, ctx):
    """How much of the matrix's movement history is actually backfilled.
    A cell that is not NONE today got there by moving at least once; if we have no move row
    for it, that history is UNRECOVERABLE from the sources (prose never recorded it)."""
    non_none = conn.execute(
        "SELECT domain_key, subdomain_key, dimension_key FROM model_cell "
        "WHERE run_id = ? AND tier <> 'NONE'", (ctx["run_id"],)).fetchall()
    have_move = {tuple(r) for r in conn.execute(
        "SELECT DISTINCT domain_key, subdomain_key, dimension_key FROM model_cell_move")}
    covered = [c for c in non_none if tuple(c) in have_move]
    return {
        "non_none_cells": len(non_none),
        "cells_with_at_least_one_move": len(covered),
        "cells_with_no_recoverable_history": len(non_none) - len(covered),
        "domain_level_uncovered": sum(1 for c in non_none if c[1] == "" and tuple(c) not in have_move),
        "subdomain_level_uncovered": sum(1 for c in non_none if c[1] != "" and tuple(c) not in have_move),
    }


# =========================================================================================
# main
# =========================================================================================
def snapshot(db_path, tenant, system_role, note=None, dry_run=False, write_ledger=True):
    at = _now()
    sources = _source_manifest(at)
    data = {alias: _load(path) for alias, path in SRC.items()}

    missing = [a for a, v in data.items() if v is None]
    if data["capability_model"] is None:
        print("FATAL: capability_model.json not readable — nothing to snapshot.")
        return 1
    if missing:
        print("  WARN: missing sources (snapshotted as absent): %s" % ", ".join(missing))
    stale = [a for a, m in sources.items() if m.get("stale")]
    if stale:
        print("  WARN: stale sources (> %dd old, recorded in snapshot_run): %s"
              % (STALE_DAYS, ", ".join(stale)))

    if dry_run:
        print("DRY RUN — sources read, nothing written.")
        print(json.dumps(sources, indent=2, ensure_ascii=False))
        return 0

    os.makedirs(Path(db_path).parent, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA)

    commit = _git_commit()
    cur = conn.execute(
        """INSERT INTO snapshot_run
           (tenant_id, system_role, measured_at, git_commit, tool_version, sources_json, note)
           VALUES (?,?,?,?,?,?,?)""",
        (tenant, system_role, at, commit, TOOL_VERSION,
         json.dumps(sources, ensure_ascii=False), note))
    ctx = {"run_id": cur.lastrowid, "tenant": tenant, "system": system_role, "at": at,
           "git_commit": commit}

    counts = {}
    counts["dim_domain"] = load_dim_domain(conn, ctx, data["ontology"])
    counts["dim_dimension"] = load_dim_dimension(conn, ctx, data["capability_model"], data["maturity"])
    counts["model_cell"] = load_model_cell(conn, ctx, data["capability_model"])
    counts["maturity_score"] = load_maturity_score(conn, ctx, data["maturity"])
    counts["extractor_maturity"] = load_extractor_maturity(conn, ctx, data["extractor"])
    counts["meta_capability"] = load_meta_capability(conn, ctx, data["meta_capability"])
    counts["claims_health"] = load_claims_health(conn, ctx, data["claims_health"])

    n_obs, prev_run = detect_observed_moves(conn, ctx, data["capability_model"])
    bf = backfill_moves(conn, ctx, data["capability_model"], data["applied_models"])
    counts["model_cell_move"] = n_obs + sum(v for k, v in bf.items() if k != "SKIPPED_STAYS")

    conn.commit()
    cov = backfill_coverage(conn, ctx)

    print("=== MODEL STATE SNAPSHOT run_id=%d  %s  tenant=%s system_role=%s"
          % (ctx["run_id"], at, tenant, system_role))
    for t in ("dim_domain", "dim_dimension", "model_cell", "model_cell_move",
              "maturity_score", "extractor_maturity", "meta_capability", "claims_health"):
        total = conn.execute("SELECT COUNT(*) FROM %s" % t).fetchone()[0]
        print("  %-20s +%-6d (table total %d)" % (t, counts.get(t, 0), total))
    print("  moves: observed(run-diff)=%d prev_run=%s | backfill=%s" % (n_obs, prev_run, bf))
    print("  backfill coverage: %s" % cov)

    headline = conn.execute(
        "SELECT score FROM maturity_score WHERE run_id=? AND scope_type='MODEL'",
        (ctx["run_id"],)).fetchone()
    headline = headline[0] if headline else None
    print("  MODEL MATURITY = %s%%" % headline)

    conn.close()

    if write_ledger:
        # Durability copy: brain_v2/output/ is gitignored AND is the "disposable, rebuildable"
        # dir. This DB is NOT rebuildable. One tiny line per run keeps the headline curve in git
        # even if output/ is wiped.  (~200 bytes/run)
        line = {"run_id": ctx["run_id"], "measured_at": at, "tenant_id": tenant,
                "system_role": system_role, "model_maturity_pct": headline,
                "extractor_pct": (data["extractor"] or {}).get("overall_pct"),
                "meta_maturity_pct": (data["meta_capability"] or {}).get("meta_maturity_pct"),
                "claims_live": (data["claims_health"] or {}).get("live"),
                "claims_verification_rate": (data["claims_health"] or {}).get("verification_rate"),
                "git_commit": ctx.get("git_commit")}
        with open(LEDGER, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(line, ensure_ascii=False) + "\n")

    print("\nsaved: %s" % db_path)
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Append an immutable snapshot of the capability model + its maturity "
                    "measurements to the model-state DB. Run AFTER Step 3b of rebuild_all.py.")
    ap.add_argument("--db", default=str(DEFAULT_DB), help="model-state DB path (default: %(default)s)")
    ap.add_argument("--tenant", default=os.environ.get("SAPILOT_TENANT_ID", "UNESCO"),
                    help="tenant_id stamped on every row (default: %(default)s)")
    ap.add_argument("--system-role", default=os.environ.get("SAPILOT_SYSTEM_ROLE", "P01"),
                    help="SAP landscape role/SID the measurement pertains to (default: %(default)s)")
    ap.add_argument("--note", default=None, help="free-text note stored on the run")
    ap.add_argument("--dry-run", action="store_true", help="read sources, print manifest, write nothing")
    ap.add_argument("--no-ledger", action="store_true", help="skip the git-friendly JSONL ledger")
    args = ap.parse_args(argv)
    return snapshot(args.db, args.tenant, args.system_role, note=args.note,
                    dry_run=args.dry_run, write_ledger=not args.no_ledger)


if __name__ == "__main__":
    sys.exit(main())
