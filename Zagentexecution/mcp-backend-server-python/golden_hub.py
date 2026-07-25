"""
golden_hub.py — read-only, tenant-scoped access to the golden DB VIA THE MANIFEST.

ADDITIVE MODULE (T5 / peldano 5). Nothing in this directory was renamed, moved or removed.
Depends on the standard library ONLY (json/sqlite3/pathlib/re) — no pyrfc, no mcp, no dotenv —
so it is importable and testable without the MCP runtime.

CONTRACT
--------
The caller NEVER supplies a .db path. It supplies (tenant_id, system_role, gold_table) and the
manifest resolves the rest. `golden_manifest.json` is the only place a path lives; the p01_/v01_
filename prefix is decoded exclusively in `scripts/extraction/build_golden_manifest.py`
(SID_ROLE / _sid_from_db_filename), so D3/T7 retires it without touching a single consumer.

SAFETY
------
* every connection is opened `file:...?mode=ro` (SQLite refuses writes at the driver level)
* `golden_query` accepts SELECT only, one statement, no ';', and rejects a denylist of DDL/DML
  and pragma/attach verbs; the table is not interpolated from user text but resolved against
  the manifest and re-quoted
* a LIMIT is ALWAYS enforced (default 1000, hard cap 10000) so no call can scan a 2.2M-row table
* nothing here ever writes to the golden (14.2 GB) or to the manifest
"""
from __future__ import annotations

import datetime as _dt
import json
import re
import sqlite3
from pathlib import Path

# repo root = .../abapobjectscreation  (this file: <repo>/Zagentexecution/mcp-backend-server-python/)
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_PATH = REPO_ROOT / "golden_manifest.json"

DEFAULT_MAX_ROWS = 1000
HARD_MAX_ROWS = 10000

# 'stale' thresholds by cadence family (days). Used by golden_freshness.
_STALE_DAYS = {"daily": 2, "weekly": 10, "monthly": 40, "_default": 35}

# `select|union|...` are forbidden inside `where` too: a subquery would read a table the
# manifest never scoped, silently bypassing tenant scoping. One table per call, by design.
_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|create|alter|replace|attach|detach|vacuum|reindex|"
    r"pragma|begin|commit|rollback|analyze|truncate|select|union|intersect|except|"
    r"load_extension|readfile|writefile)\b",
    re.IGNORECASE,
)
# KNOWN LIMITATION: the denylist is lexical, so a string literal that happens to contain one of
# these words as a whole word (e.g. where="ERNAM='CREATE'") is refused. Deliberate: on a 14.2 GB
# production golden, a false refusal is cheap and a false accept is not.
_IDENT_OK = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class GoldenHubError(RuntimeError):
    pass


# ---------------------------------------------------------------------------
# manifest
# ---------------------------------------------------------------------------
_CACHE: dict = {}


def load_manifest(refresh: bool = False) -> dict:
    """Load golden_manifest.json (cached by mtime)."""
    if not MANIFEST_PATH.exists():
        raise GoldenHubError(
            "golden_manifest.json not found at %s. Build it: "
            "python scripts/extraction/build_golden_manifest.py" % MANIFEST_PATH
        )
    mt = MANIFEST_PATH.stat().st_mtime
    if refresh or _CACHE.get("mtime") != mt:
        _CACHE["data"] = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        _CACHE["mtime"] = mt
    return _CACHE["data"]


def _match_system(s: dict, tenant_id=None, system_role=None, sap_sid=None) -> bool:
    if tenant_id and str(s.get("tenant_id", "")).upper() != str(tenant_id).upper():
        return False
    if system_role and str(s.get("system_role", "")).upper() != str(system_role).upper():
        return False
    if sap_sid and str(s.get("sap_sid", "")).upper() != str(sap_sid).upper():
        return False
    return True


def resolve_system(tenant_id=None, system_role=None, sap_sid=None) -> dict:
    """(tenant_id, system_role) -> the system record. THE path-decoupling point."""
    man = load_manifest()
    cands = [s for s in man["systems"] if _match_system(s, tenant_id, system_role, sap_sid)]
    if not cands:
        avail = ", ".join(
            "%s/%s (%s)" % (s.get("tenant_id"), s.get("system_role"), s.get("sap_sid"))
            for s in man["systems"]
        )
        raise GoldenHubError(
            "no system matches tenant_id=%r system_role=%r sap_sid=%r. Available: %s"
            % (tenant_id, system_role, sap_sid, avail)
        )
    if len(cands) > 1:
        prim = man.get("primary_sid")
        for c in cands:
            if c.get("sap_sid") == prim:
                return c
    return cands[0]


def _table_index(man: dict) -> dict:
    idx = _CACHE.get("tidx")
    if idx is None or _CACHE.get("tidx_mtime") != _CACHE.get("mtime"):
        idx = {}
        for t in man["tables"]:
            idx.setdefault(t["gold"].lower(), []).append(t)
        _CACHE["tidx"] = idx
        _CACHE["tidx_mtime"] = _CACHE.get("mtime")
    return idx


def resolve_table(gold_table: str, tenant_id=None, system_role=None, sap_sid=None) -> dict:
    """gold table name (case-insensitive) + tenant scope -> the manifest table record."""
    man = load_manifest()
    cands = _table_index(man).get(str(gold_table).lower(), [])
    if not cands:
        raise GoldenHubError(
            "gold table %r is not in the manifest (%d tables). Use golden_manifest(domain=...) "
            "to discover what exists." % (gold_table, len(man["tables"]))
        )
    scoped = [
        t for t in cands
        if _match_system(t, tenant_id, system_role, sap_sid)
    ]
    if not scoped:
        raise GoldenHubError(
            "gold table %r exists but not for tenant_id=%r system_role=%r; it is published for %s"
            % (
                gold_table, tenant_id, system_role,
                ", ".join("%s/%s" % (t.get("tenant_id"), t.get("system_role")) for t in cands),
            )
        )
    return scoped[0]


def db_path_for(table_rec: dict) -> Path:
    """Internal. The ONLY place a consumer-visible call turns into a filesystem path."""
    man = load_manifest()
    for s in man["systems"]:
        if s.get("sap_sid") == table_rec.get("sap_sid"):
            p = Path(s.get("db_path_abs") or (REPO_ROOT / s["db_path"]))
            if not p.is_absolute():
                p = REPO_ROOT / p
            return p
    raise GoldenHubError("no system record for sap_sid=%r" % table_rec.get("sap_sid"))


def _connect_ro(db: Path) -> sqlite3.Connection:
    con = sqlite3.connect("file:%s?mode=ro" % db.as_posix(), uri=True)
    con.row_factory = sqlite3.Row
    return con


# ---------------------------------------------------------------------------
# 1. manifest slice
# ---------------------------------------------------------------------------
def golden_manifest(tenant_id=None, system_role=None, domain=None, gold_table=None,
                    include_columns: bool = False) -> dict:
    """A filtered slice of Contrato A. No path knowledge required by the caller."""
    man = load_manifest()
    systems = [s for s in man["systems"] if _match_system(s, tenant_id, system_role)]
    tabs = []
    for t in man["tables"]:
        if not _match_system(t, tenant_id, system_role):
            continue
        if domain and str(t.get("domain", "")).upper() != str(domain).upper():
            continue
        if gold_table and t["gold"].lower() != str(gold_table).lower():
            continue
        rec = dict(t)
        if not include_columns:
            rec.pop("columns", None)
        tabs.append(rec)
    return {
        "manifest_version": man.get("manifest_version"),
        "hub_id": man.get("hub_id"),
        "generated_at": man.get("generated_at"),
        "filter": {"tenant_id": tenant_id, "system_role": system_role,
                   "domain": domain, "gold_table": gold_table},
        "systems": [{k: v for k, v in s.items() if k not in ("db_path", "db_path_abs")}
                    for s in systems],
        "n_tables": len(tabs),
        "tables": tabs,
        "domains": sorted({t.get("domain") for t in tabs if t.get("domain")}),
        "_warnings": man.get("_warnings", []),
        "ingest_contract_ref": man.get("ingest_contract_ref"),
    }


# ---------------------------------------------------------------------------
# 2. read-only query
# ---------------------------------------------------------------------------
def _validate_cols(cols, table_rec) -> str:
    if not cols:
        return "*"
    known = {c.lower() for c in (table_rec.get("columns") or [])}
    out = []
    for c in cols:
        c = str(c).strip()
        if not _IDENT_OK.match(c):
            raise GoldenHubError("illegal column identifier %r" % c)
        if known and c.lower() not in known:
            raise GoldenHubError(
                "column %r not in %s. Known: %s"
                % (c, table_rec["gold"], ", ".join(sorted(table_rec.get("columns") or []))[:400])
            )
        out.append('"%s"' % c)
    return ", ".join(out)


def _validate_where(where: str) -> str:
    w = (where or "").strip().rstrip(";").strip()
    if not w:
        return ""
    if ";" in w:
        raise GoldenHubError("`where` must be a single expression (no ';')")
    if _FORBIDDEN.search(w):
        raise GoldenHubError("`where` contains a forbidden keyword; this endpoint is read-only")
    if "--" in w or "/*" in w:
        raise GoldenHubError("`where` must not contain SQL comments")
    return w


def golden_query(gold_table: str, cols=None, where: str = "", tenant_id=None,
                 system_role=None, max_rows: int = DEFAULT_MAX_ROWS, order_by: str = "") -> dict:
    """SELECT-only, tenant-scoped read of a gold table. Returns rows + _meta provenance.

    The caller never sees or supplies a .db path.
    """
    rec = resolve_table(gold_table, tenant_id=tenant_id, system_role=system_role)
    if not rec.get("exists_in_db", True):
        raise GoldenHubError("table %r is in the manifest but absent from the .db" % gold_table)

    try:
        n = int(max_rows)
    except (TypeError, ValueError):
        n = DEFAULT_MAX_ROWS
    n = max(1, min(n, HARD_MAX_ROWS))

    sel = _validate_cols(cols, rec)
    wh = _validate_where(where)
    ob = _validate_where(order_by)

    sql = 'SELECT %s FROM "%s"' % (sel, rec["gold"])
    if wh:
        sql += " WHERE " + wh
    if ob:
        sql += " ORDER BY " + ob
    sql += " LIMIT %d" % n

    db = db_path_for(rec)
    con = _connect_ro(db)
    try:
        cur = con.execute(sql)
        rows = [dict(r) for r in cur.fetchall()]
        colnames = [d[0] for d in cur.description] if cur.description else []
    except sqlite3.Error as e:
        raise GoldenHubError("SQL error on %s: %s" % (rec["gold"], e))
    finally:
        con.close()

    return {
        "gold_table": rec["gold"],
        "columns": colnames,
        "n_rows": len(rows),
        "truncated": len(rows) >= n,
        "rows": rows,
        "_meta": {
            "tenant_id": rec.get("tenant_id"),
            "system_role": rec.get("system_role"),
            "source_sid": rec.get("sap_sid"),
            "sap": rec.get("sap"),
            "domain": rec.get("domain"),
            "type": rec.get("type"),
            "extracted_at": rec.get("extracted_at"),
            "extracted_at_source": rec.get("extracted_at_source"),
            "freshness_days": rec.get("freshness_days"),
            "rows_registry": rec.get("rows"),
            "extractor_level": rec.get("extractor_level"),
            "ladder": rec.get("ladder"),
            "delta_strategy": rec.get("delta_strategy"),
            "observed_strategy": rec.get("observed_strategy"),
            "provenance": rec.get("provenance"),
            "access": rec.get("access"),
            "sql_executed": sql,
            "read_only": True,
        },
    }


# ---------------------------------------------------------------------------
# 3. freshness
# ---------------------------------------------------------------------------
def _cadence_family(cadence):
    c = str(cadence or "").lower()
    for fam in ("daily", "weekly", "monthly"):
        if fam in c:
            return fam
    return "_default"


def _fresh_rec(t: dict, now: _dt.datetime) -> dict:
    fam = _cadence_family(t.get("cadence"))
    limit = _STALE_DAYS[fam]
    fd = t.get("freshness_days")
    if fd is None:
        stale, reason = None, "no extracted_at (never covered by _gold_sync_log nor _config_frontier_manifest)"
    else:
        stale = fd > limit
        reason = "%.1f d old vs %s threshold %d d" % (fd, fam, limit)
    return {
        "gold": t["gold"],
        "domain": t.get("domain"),
        "tenant_id": t.get("tenant_id"),
        "system_role": t.get("system_role"),
        "extracted_at": t.get("extracted_at"),
        "extracted_at_source": t.get("extracted_at_source"),
        "freshness_days": fd,
        "cadence": t.get("cadence"),
        "cadence_family": fam,
        "stale_threshold_days": limit,
        "stale": stale,
        "reason": reason,
        "refresh_script": t.get("refresh_script"),
    }


def golden_freshness(gold_table: str = "", domain: str = "", tenant_id=None,
                     system_role=None) -> dict:
    """Freshness of one gold table, or of a whole domain. Path-free."""
    man = load_manifest()
    now = _dt.datetime.now(_dt.timezone.utc)
    if gold_table:
        recs = [resolve_table(gold_table, tenant_id=tenant_id, system_role=system_role)]
    elif domain:
        recs = [t for t in man["tables"]
                if str(t.get("domain", "")).upper() == str(domain).upper()
                and _match_system(t, tenant_id, system_role)]
        if not recs:
            raise GoldenHubError("no tables for domain=%r in that tenant scope" % domain)
    else:
        raise GoldenHubError("give gold_table or domain")

    items = [_fresh_rec(t, now) for t in recs]
    known = [i for i in items if i["stale"] is not None]
    return {
        "manifest_generated_at": man.get("generated_at"),
        "n": len(items),
        "n_measurable": len(known),
        "n_stale": sum(1 for i in known if i["stale"]),
        "n_unknown": len(items) - len(known),
        "items": items if len(items) > 1 else items[0],
    }
