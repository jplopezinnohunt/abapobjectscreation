"""
build_golden_manifest.py — generates `golden_manifest.json` (Contrato A, peldano 5 / T5).

WHY
---
Today the hub serves its data by PATH COUPLING: every consumer must know where
`p01_gold_master_data.db` lives (11 files under `process_mining/` hardcode it, plus every
spoke's `refs_external.json`). While the consumer needs the path, the hub cannot mature:
the ceiling is set by the consumer.

This script publishes the indirection layer. A consumer asks the manifest
"what tables exist, from which system, how fresh, under what access contract"
and never learns a path.

INPUTS (all verified on disk 2026-07-25, not assumed)
-----------------------------------------------------
1. `<sqlite_dir>/*_gold_master_data.db`  -> systems + n_tables + db_bytes + per-table columns
                                            (sqlite_master / PRAGMA table_info ONLY: metadata,
                                             no scans, opened read-only via `mode=ro` URI)
2. `_gold_sync_log`   (in the .db, 41 rows)   ts|domain|table_type|gold|sap|strategy|
                                              n_new|n_changed|n_deleted|n_total|detail
                                              -> covers 28 distinct golds == the 28 curated
3. `_config_frontier_manifest` (in the .db, 101 rows)
                                              grp|tabname|system|exists_in_catalog|n_fields|
                                              n_rows|sqlite_table|note|extracted_at
                                              -> the ONLY extracted_at source for config tables
4. `brain_v2/gold_table_registry.json`        {domains:{<domain>:{<type>:[entry...]}}, _meta}
5. `brain_v2/gold_extractor_maturity.json`    {_design, overall_pct, n_tables, by_domain,
                                               by_type, tables:[{domain,type,gold,level,
                                               ladder,source}]}

REJECTED INPUT
--------------
`Zagentexecution/sap_data_extraction/gold_db_manifest_pre_dedup.json` — see NOTE_PRE_DEDUP.

NOT a rebuild. Reads only. Safe to run any time; takes ~2 s.

Run:  python scripts/extraction/build_golden_manifest.py [--out golden_manifest.json] [--no-columns]
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import sqlite3
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SQLITE_DIR = REPO / "Zagentexecution" / "sap_data_extraction" / "sqlite"
REGISTRY = REPO / "brain_v2" / "gold_table_registry.json"
MATURITY = REPO / "brain_v2" / "gold_extractor_maturity.json"
PRE_DEDUP = REPO / "Zagentexecution" / "sap_data_extraction" / "gold_db_manifest_pre_dedup.json"
DEFAULT_OUT = REPO / "golden_manifest.json"

MANIFEST_VERSION = "1.0.0"
HUB_ID = "abapobjectscreation"

NOTE_PRE_DEDUP = (
    "gold_db_manifest_pre_dedup.json REJECTED as an input (verified 2026-07-25): it lists 217 "
    "tables, of which 14 no longer exist in the .db (pre-dedup names: bpja_2024/2025/2026, "
    "coss_2024/2025/2026, prps_full, bphi, opsv, T042Z_FULL, ...), 22 are absent from the "
    "registry, and 10 disagree with the registry row counts. Its only unique field (`cols`) is "
    "obtained here from PRAGMA table_info, which is live and free. Its `as_of` is a session id "
    "(\"s079\"), not a timestamp, so staleness cannot even be measured. Keeping it as an input "
    "would import 14 phantom tables into the DaaS contract."
)

# ---------------------------------------------------------------------------
# THE ONLY PLACE THE d01_/v01_/p01_ FILENAME PREFIX CONVENTION IS ENCODED.
# D3 retires the prefix (T7, Ola 4). When it goes, change THIS MAP ONLY -- no
# consumer and no MCP tool may re-derive a sid or a role from a name.
# ---------------------------------------------------------------------------
SID_ROLE = {"P01": "PROD", "Q01": "QA", "V01": "VALIDATION", "D01": "DEV"}
SID_TENANT = {"P01": "UNESCO", "Q01": "UNESCO", "V01": "UNESCO", "D01": "UNESCO"}
DEFAULT_TENANT = "UNESCO"


def _sid_from_db_filename(name: str) -> str:
    """p01_gold_master_data.db -> 'P01'. Single point of truth for the prefix hack (D3/T7)."""
    stem = Path(name).stem
    head = stem.split("_", 1)[0].upper()
    if len(head) == 3 and head[0].isalpha() and head[1:].isdigit():
        return head
    return "UNKNOWN"


def _iso_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_ts(ts: str | None):
    """Accepts '2026-06-30T10:24:54Z' (_gold_sync_log) and '2026-06-19 09:06:10'
    (_config_frontier_manifest). Returns tz-aware datetime or None."""
    if not ts:
        return None
    s = str(ts).strip().replace("Z", "+00:00").replace(" ", "T", 1)
    try:
        d = _dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=_dt.timezone.utc)
    return d


def _freshness_days(ts: str | None, now: _dt.datetime):
    d = _parse_ts(ts)
    if d is None:
        return None
    return round((now - d).total_seconds() / 86400.0, 1)


# ---------------------------------------------------------------------------
# read-only golden access (metadata only -- never a data scan)
# ---------------------------------------------------------------------------
def _connect_ro(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect("file:%s?mode=ro" % db_path.as_posix(), uri=True)
    con.row_factory = sqlite3.Row
    return con


def _read_db_metadata(db_path: Path, want_columns: bool) -> dict:
    con = _connect_ro(db_path)
    try:
        objs = con.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table','view')"
        ).fetchall()
        names = [r["name"] for r in objs]
        data_tables = [n for n in names if not n.startswith("_")]
        meta_tables = [n for n in names if n.startswith("_")]

        columns = {}
        if want_columns:
            for t in data_tables:
                try:
                    columns[t] = [
                        r["name"] for r in con.execute('PRAGMA table_info("%s")' % t).fetchall()
                    ]
                except sqlite3.Error:
                    columns[t] = []

        sync_log = []
        if "_gold_sync_log" in meta_tables:
            sync_log = [dict(r) for r in con.execute("SELECT * FROM _gold_sync_log").fetchall()]

        frontier = []
        if "_config_frontier_manifest" in meta_tables:
            frontier = [
                dict(r) for r in con.execute("SELECT * FROM _config_frontier_manifest").fetchall()
            ]
        return {
            "all_names": set(names),
            "data_tables": data_tables,
            "meta_tables": meta_tables,
            "columns": columns,
            "sync_log": sync_log,
            "frontier": frontier,
        }
    finally:
        con.close()


def _latest_by_gold(sync_log: list) -> dict:
    """_gold_sync_log has multiple rows per gold; keep the newest ts per gold."""
    out = {}
    for r in sync_log:
        g = r.get("gold")
        if not g:
            continue
        prev = out.get(g)
        if prev is None or str(r.get("ts") or "") > str(prev.get("ts") or ""):
            out[g] = r
    return out


def _frontier_by_table(frontier: list) -> dict:
    out = {}
    for r in frontier:
        k = r.get("sqlite_table") or r.get("tabname")
        if not k:
            continue
        prev = out.get(k)
        if prev is None or str(r.get("extracted_at") or "") > str(prev.get("extracted_at") or ""):
            out[k] = r
    return out


# ---------------------------------------------------------------------------
# builder
# ---------------------------------------------------------------------------
def build(out_path: Path, want_columns: bool = True, verbose: bool = True) -> dict:
    now = _dt.datetime.now(_dt.timezone.utc)
    warnings: list[str] = []

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    maturity = json.loads(MATURITY.read_text(encoding="utf-8"))

    # --- flatten the registry ------------------------------------------------
    reg_entries = []
    for domain, by_type in registry.get("domains", {}).items():
        for ttype, rows in by_type.items():
            for e in rows:
                reg_entries.append((domain, ttype, e))

    # registry _meta vs measured reality (CONTRADICTION guard, do not silence)
    meta = registry.get("_meta", {})
    src_counts: dict[str, int] = {}
    for _, _, e in reg_entries:
        src_counts[e.get("source", "?")] = src_counts.get(e.get("source", "?"), 0) + 1
    measured = {"total_tables": len(reg_entries), **src_counts}
    if meta.get("total_tables") != len(reg_entries):
        warnings.append(
            "gold_table_registry.json `_meta.total_tables`=%s but %d entries are actually present. "
            "`_meta` is stale; the manifest uses the measured value."
            % (meta.get("total_tables"), len(reg_entries))
        )
    if meta.get("auto") != src_counts.get("auto"):
        warnings.append(
            "gold_table_registry.json `_meta.auto`=%s but measured auto=%s; `_meta` also omits "
            "source='override' (%s entries). Measured wins."
            % (meta.get("auto"), src_counts.get("auto"), src_counts.get("override"))
        )
    if maturity.get("n_tables") != len(reg_entries):
        warnings.append(
            "gold_extractor_maturity.json n_tables=%s != registry entries=%d"
            % (maturity.get("n_tables"), len(reg_entries))
        )

    mat_by_gold = {t["gold"]: t for t in maturity.get("tables", []) if t.get("gold")}

    # --- systems -------------------------------------------------------------
    db_files = sorted(SQLITE_DIR.glob("*_gold_master_data.db"))
    if not db_files:
        raise SystemExit("no *_gold_master_data.db under %s" % SQLITE_DIR)

    systems = []
    dbmeta_by_sid = {}
    for db in db_files:
        sid = _sid_from_db_filename(db.name)
        m = _read_db_metadata(db, want_columns=want_columns)
        dbmeta_by_sid[sid] = m
        systems.append(
            {
                "tenant_id": SID_TENANT.get(sid, DEFAULT_TENANT),
                "system_role": SID_ROLE.get(sid, "UNKNOWN"),
                "sap_sid": sid,
                "db_path": db.relative_to(REPO).as_posix(),
                "db_path_abs": db.as_posix(),
                "db_bytes": db.stat().st_size,
                "db_mtime": _dt.datetime.fromtimestamp(
                    db.stat().st_mtime, _dt.timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "n_tables": len(m["all_names"]),
                "n_data_tables": len(m["data_tables"]),
                "n_meta_tables": len(m["meta_tables"]),
                "access": "read-only SQL (sqlite mode=ro). Never copy, never write, never VACUUM.",
            }
        )

    # The registry describes ONE system today (the P01 golden). Anything else is
    # published as a system with tables=[] until its own registry exists.
    primary_sid = "P01" if "P01" in dbmeta_by_sid else systems[0]["sap_sid"]
    prim = dbmeta_by_sid[primary_sid]
    prim_sys = next(s for s in systems if s["sap_sid"] == primary_sid)
    sync_by_gold = _latest_by_gold(prim["sync_log"])
    frontier_by_table = _frontier_by_table(prim["frontier"])

    for s in systems:
        if s["sap_sid"] != primary_sid:
            warnings.append(
                "system %s (%s) has a golden .db but no entry in gold_table_registry.json -> "
                "published with 0 tables; it is invisible to the DaaS contract."
                % (s["sap_sid"], s["db_path"])
            )

    # --- tables --------------------------------------------------------------
    tables = []
    strategy_conflicts = []
    for domain, ttype, e in reg_entries:
        gold = e["gold"]
        syn = sync_by_gold.get(gold)
        fro = frontier_by_table.get(gold)
        mat = mat_by_gold.get(gold, {})

        # extracted_at: _gold_sync_log wins (per-sync truth); else the frontier manifest.
        if syn and syn.get("ts"):
            extracted_at, ea_src = syn["ts"], "_gold_sync_log.ts"
        elif fro and fro.get("extracted_at"):
            extracted_at, ea_src = fro["extracted_at"], "_config_frontier_manifest.extracted_at"
        else:
            extracted_at, ea_src = None, None

        delta = e.get("delta")
        observed = syn.get("strategy") if syn else None
        if delta and observed and delta != observed and not observed.startswith(str(delta)):
            strategy_conflicts.append((gold, delta, observed))

        rec = {
            "gold": gold,
            "sap": e.get("sap") or (syn.get("sap") if syn else None) or (fro.get("tabname") if fro else None),
            "domain": domain,
            "type": ttype,
            "tenant_id": prim_sys["tenant_id"],
            "system_role": prim_sys["system_role"],
            "sap_sid": primary_sid,
            "rows": e.get("rows"),
            "registry_source": e.get("source"),
            "exists_in_db": gold in prim["all_names"],
            "extractor_level": mat.get("level"),
            "ladder": mat.get("ladder"),
            "delta_strategy": delta,
            "observed_strategy": observed,
            "refresh_script": e.get("refresh_script"),
            "cadence": e.get("cadence"),
            "extracted_at": extracted_at,
            "extracted_at_source": ea_src,
            "freshness_days": _freshness_days(extracted_at, now),
            "key": e.get("key"),
            "fields": e.get("fields"),
            "gold_cols": e.get("gold_cols"),
            "value_fields": e.get("value_fields"),
            "partition": e.get("partition"),
            "where": e.get("where"),
            "created_field": e.get("created"),
            "changed_field": e.get("changed"),
            "note": e.get("note"),
            "provenance": {
                "source": "%s LIVE (RFC_READ_TABLE / refresh script)" % primary_sid,
                "db": prim_sys["db_path"],
                "last_sync": (
                    {
                        "ts": syn.get("ts"),
                        "strategy": syn.get("strategy"),
                        "n_new": syn.get("n_new"),
                        "n_changed": syn.get("n_changed"),
                        "n_deleted": syn.get("n_deleted"),
                        "n_total": syn.get("n_total"),
                        "detail": syn.get("detail"),
                    }
                    if syn
                    else None
                ),
                "frontier": (
                    {
                        "grp": fro.get("grp"),
                        "n_fields": fro.get("n_fields"),
                        "n_rows": fro.get("n_rows"),
                        "note": fro.get("note"),
                    }
                    if fro
                    else None
                ),
            },
            "access": "golden_query() MCP tool, or SQL read-only via this manifest. Never copy the .db.",
        }
        if want_columns:
            rec["columns"] = prim["columns"].get(gold, [])
        tables.append({k: v for k, v in rec.items() if v is not None or k in ("extracted_at", "freshness_days")})

    if strategy_conflicts:
        warnings.append(
            "registry `delta` disagrees with the strategy actually logged in _gold_sync_log for "
            "%d tables (e.g. %s). `delta:'external'` means 'refreshed by an out-of-band script', "
            "NOT a delta algorithm -- both are published (`delta_strategy` / `observed_strategy`)."
            % (
                len(strategy_conflicts),
                ", ".join("%s: %s vs %s" % c for c in strategy_conflicts[:3]),
            )
        )

    # tables physically in the .db that no registry entry claims
    unregistered = sorted(set(prim["data_tables"]) - {t["gold"] for t in tables})
    if unregistered:
        warnings.append(
            "%d table(s) exist in %s but are absent from gold_table_registry.json (%s): they are "
            "un-governed -- no domain, no maturity, no freshness."
            % (len(unregistered), prim_sys["db_path"], ", ".join(unregistered))
        )

    with_extracted_at = sum(1 for t in tables if t.get("extracted_at"))

    manifest = {
        "manifest_version": MANIFEST_VERSION,
        "hub_id": HUB_ID,
        "generated_at": _iso_now(),
        "generated_by": "scripts/extraction/build_golden_manifest.py",
        "_design": (
            "Contrato A (peldano 5 / T5). The hub's data interface. A consumer resolves a gold "
            "table -> system -> freshness -> provenance WITHOUT knowing any .db path. The "
            "p01_/v01_ filename prefix is decoded in exactly one place (SID_ROLE/_sid_from_db_filename "
            "in the builder); D3/T7 retires it by editing that map only."
        ),
        "systems": systems,
        "primary_sid": primary_sid,
        "tables": tables,
        "_inputs": {
            "golden_db": [s["db_path"] for s in systems],
            "golden_db_meta_tables_used": ["_gold_sync_log", "_config_frontier_manifest"],
            "registry": REGISTRY.relative_to(REPO).as_posix(),
            "maturity": MATURITY.relative_to(REPO).as_posix(),
            "rejected": {PRE_DEDUP.relative_to(REPO).as_posix(): NOTE_PRE_DEDUP},
        },
        "_stats": {
            "n_systems": len(systems),
            "n_tables": len(tables),
            "n_tables_with_extracted_at": with_extracted_at,
            "n_tables_without_extracted_at": len(tables) - with_extracted_at,
            "by_registry_source": src_counts,
            "registry_meta_declared": meta,
            "registry_meta_measured": measured,
            "n_sync_log_rows": len(prim["sync_log"]),
            "n_sync_log_golds": len(sync_by_gold),
            "n_frontier_rows": len(prim["frontier"]),
            "unregistered_db_tables": unregistered,
        },
        "_warnings": warnings,
        "ingest_contract_ref": "probe_suite_f0.json",
    }

    out_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    if verbose:
        print("wrote %s (%d systems, %d tables, %d warnings)"
              % (out_path, len(systems), len(tables), len(warnings)))
        for w in warnings:
            print("  WARN: %s" % w)
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build golden_manifest.json (Contrato A).")
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--no-columns", action="store_true",
                    help="skip PRAGMA table_info per table (smaller manifest)")
    a = ap.parse_args(argv)
    build(Path(a.out), want_columns=not a.no_columns)
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
