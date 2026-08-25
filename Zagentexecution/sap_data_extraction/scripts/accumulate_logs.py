"""
accumulate_logs.py  —  rolling-window LOG ACCUMULATOR for process mining
=======================================================================
P01 prunes operational log tables (STAD/SWNCMONI tcode-usage ~days, TBTCO/TBTCP
job log, SNAP/ST22 dumps, SM21 syslog, ...). Each run of this routine pulls the
CURRENT window from P01 and UPSERTS it into a permanent `<table>_history`
accumulation table in the Gold DB — so we build the HISTORY P01 deletes. Logs are
the raw event material for process mining (who ran which program/tcode, when,
status, what changed).

RETENTION POLICY (user requirement 2026-06-20): keep **≥6 months** of production
logs locally. Target is keep-ALL — there is NO prune/DELETE path by design. Because
P01 only holds a short live window, the ONLY way to satisfy ≥6 months is to run this
every ≤14 days so consecutive windows overlap and dedupe into a continuous history.
`--verify` reports the actual span per stream and FLAGS anything below 6 months.

Design:
  * APPEND/MERGE, never replace. Dedup by the table's natural key (PK on the history
    table -> INSERT OR IGNORE makes re-runs idempotent and overlap-safe).
  * Uses the extraction skill's shared helpers (rfc_helpers) — does NOT fork them.
  * Idempotent: run it every <=14 days; overlapping windows are deduped by PK.
  * Generic: add a table to LOG_TABLES to start accumulating it. Everything that is
    a LOG (append-only event stream) belongs here.
  * Freshness guard: warns at start if the last run is >14 days ago (gap risk) or
    never ran (anything already purged by P01 is unrecoverable).

Streams (all RFC_READ_TABLE-safe, verified reachable on the UNESCO EhP8 kernel 2026-06-20):
  TBTCO/TBTCP  job + step/variant log      (batch "how the landscape runs")
  CDHDR        change-document headers      (audit trail / field-change events)
  SNAP         ST22 ABAP dumps (index)      (runtime-error events)

NOT YET (next increment, do NOT fake): **STAD/SWNCMONI** tcode-usage workload is NOT a
transparent table — RFC_READ_TABLE cannot read it. It needs FM SAPWL_STATREC_READ_FILE
(date/time/host params, deep structure) via pyrfc, kernel-verified first. That is the
canonical "~15-day log" the way-of-working analysis wants most → tracked as accumulate_stad().
CDPOS (change-doc items) is a CLUSTER table (CDCLS) — needs the FOR-ALL-ENTRIES ABAP path,
not this RFC_READ_TABLE pattern (see sap_event_sources_catalog.md).

Run (P01 active):   python accumulate_logs.py            # pull + accumulate, then report
Coverage only:      python accumulate_logs.py --verify   # no P01 needed
Schedule:           see schedule_accumulate_logs.md (Windows Task, every 14 days, SNC/SSO)
NOTE: P01 is SNC/SSO — a headless scheduled task must run in the user's authenticated
context (Run only when user is logged on).
"""
import os, sys, sqlite3, json, time, hashlib, datetime

MCP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "mcp-backend-server-python")
sys.path.insert(0, os.path.abspath(MCP_DIR))
from rfc_helpers import get_connection  # shared connection helper (SNC/SSO, auto-reconnect)
from pyrfc import RFCError

# --- LO QUE YA APRENDIMOS DE ESTE INSTRUMENTO -------------------------------
# Se lee ANTES de minar. `algorithm_memory.json` guarda, por cada memoria, su `implication`:
# que deben hacer DISTINTO los demas algoritmos por su culpa. Escribirlas y no leerlas es
# aprender y no aprender a la vez -- y el error queda MECANIZADO, corriendo solo cada semana.
# La ruta se BUSCA subiendo hasta el directorio que CONTIENE process_mining; no se cuenta con
# dirname(). Contarla mal es como este bloque quedo ciego: dos dirname desde quality_checks/
# apuntan a Zagentexecution/process_mining, que no existe, el import fallaba en SILENCIO y el
# gate lo daba por bueno porque greppeaba la CADENA, no el efecto.
import os as _os, sys as _sys
_d = _os.path.dirname(_os.path.abspath(__file__))
while _d != _os.path.dirname(_d):
    if _os.path.isdir(_os.path.join(_d, "process_mining")):
        _sys.path.insert(0, _os.path.join(_d, "process_mining"))
        break
    _d = _os.path.dirname(_d)
try:
    # ImportError y no Exception: cubre "metodo.py no esta" sin tragarse un fallo REAL dentro
    # de metodo.py. Y AVISA: un minero que corre sin memoria tiene que decirlo, no callarlo.
    from metodo import lo_que_ya_aprendimos as _aprendido   # noqa: E402
except ImportError as _e:
    print("  AVISO: corriendo SIN memoria de metodo (%s)" % _e)
    _aprendido = None
# NOTE: we deliberately do NOT use the shared rfc_read_paginated here. It paginates via
# ROWSKIPS, and P01's SECURED RFC_READ_TABLE rejects ROWSKIPS unless GET_SORTED is set
# ("ROWSKIPS requires GET_SORTED" — known constraint, reference_p01_strg_columns_unreadable).
# Instead we read ROWSKIPS-free, one call per DATE sub-window (_read_window + _date_chunks).

PROJECT_ROOT = r"c:\Users\jp_lopez\projects\abapobjectscreation"
GOLD_DB = os.path.join(PROJECT_ROOT, "Zagentexecution", "sap_data_extraction",
                       "sqlite", "p01_gold_master_data.db")
STATE = os.path.join(os.path.dirname(__file__), "accumulate_logs_state.json")

RETENTION_MIN_DAYS = 183  # ≥6 months (user requirement 2026-06-20). No prune path exists.
P01_WINDOW_DAYS    = 14   # SCHEDULE target (run at least this often), NOT a retention fact.
                          # Measured SM20 retention is >=62d -- see RSAU_MAX_DAYS.

# Each LOG table: SAP source, history table, natural key (PK -> dedup), fields,
# an optional date field + lookback (days) to bound the pull to the live window,
# and the snapshot table to seed history from on first creation (None = no seed).
LOG_TABLES = {
    "TBTCO": {
        "history": "tbtco_history",
        "key": ["JOBNAME", "JOBCOUNT"],
        "fields": ["JOBNAME", "JOBCOUNT", "STATUS", "SDLSTRTDT", "SDLSTRTTM",
                   "STRTDATE", "STRTTIME", "ENDDATE", "ENDTIME", "AUTHCKNAM",
                   "PRDMINS", "PRDHOURS", "PRDDAYS", "PRDWEEKS", "EVENTID"],
        "date_field": "SDLSTRTDT", "lookback_days": 180, "chunk_days": 15, "seed_from": "tbtco",
    },
    "TBTCP": {
        "history": "tbtcp_history",
        "key": ["JOBNAME", "JOBCOUNT", "STEPCOUNT"],
        "fields": ["JOBNAME", "JOBCOUNT", "STEPCOUNT", "PROGNAME", "VARIANT", "AUTHCKNAM"],
        "date_field": None, "lookback_days": None, "seed_from": "tbtcp",  # joined to TBTCO by job
    },
    # CDHDR last: heavy (snapshot ~7.8M + a wide live window). Per-table commits mean
    # the cheap streams above are already saved even if this one runs long.
    "CDHDR": {  # change-document headers = audit trail / field-change event stream
        "history": "cdhdr_history",
        "key": ["OBJECTCLAS", "OBJECTID", "CHANGENR"],
        "fields": ["OBJECTCLAS", "OBJECTID", "CHANGENR", "USERNAME", "UDATE", "UTIME", "TCODE"],
        "date_field": "UDATE", "lookback_days": 120, "chunk_days": 5, "seed_from": "cdhdr",
    },
    # SNAP (ST22 dumps) DISABLED on the RFC path: P01 returns TABLE_NOT_AVAILABLE for SNAP
    # via RFC_READ_TABLE (not RFC-exposed). Dumps must come through the ST22/dump-read FM
    # used by sap_system_monitor.py — tracked with STAD as the next increment.
    # CDPOS (change-doc items / old->new values) NOT here: CLUSTER table (CDCLS) — needs the
    # FOR-ALL-ENTRIES ABAP path (extract_cdpos_by_object.py), not RFC_READ_TABLE.
}


def _span_days(lo, hi):
    """Days between two YYYYMMDD strings (0 if unparseable)."""
    try:
        d0 = datetime.datetime.strptime(lo, "%Y%m%d").date()
        d1 = datetime.datetime.strptime(hi, "%Y%m%d").date()
        return (d1 - d0).days
    except Exception:
        return 0


def ensure_history_table(db, spec):
    """Create <table>_history with a PRIMARY KEY for dedup. Seed from an existing
    snapshot table if present (so we don't lose what we already extracted)."""
    cols_sql = ", ".join(f'"{f}" TEXT' for f in spec["fields"])
    pk_sql = ", ".join(f'"{k}"' for k in spec["key"])
    db.execute(f'CREATE TABLE IF NOT EXISTS {spec["history"]} '
               f'({cols_sql}, _first_seen TEXT, PRIMARY KEY ({pk_sql}))')
    snap = spec.get("seed_from")
    if snap:
        existing = {r[0] for r in db.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
        if snap in existing and db.execute(
                f'SELECT COUNT(*) FROM {spec["history"]}').fetchone()[0] == 0:
            snap_cols = [r[1] for r in db.execute(f'PRAGMA table_info("{snap}")')]
            shared = [f for f in spec["fields"] if f in snap_cols]
            collist = ",".join(f'"{c}"' for c in shared)
            db.execute(f'INSERT OR IGNORE INTO {spec["history"]} ({collist}) '
                       f'SELECT {collist} FROM "{snap}"')
            seeded = db.execute(f'SELECT COUNT(*) FROM {spec["history"]}').fetchone()[0]
            print(f'  seeded {spec["history"]} from snapshot {snap}: {seeded} rows')


def _read_window(conn, table, fields, where):
    """One ROWSKIPS-free RFC_READ_TABLE call (P01-secured-safe). Returns list of dicts.
    Raises RFCError(DATA_BUFFER_EXCEEDED) so the caller can split the window further."""
    opts = [{"TEXT": where}] if where else []
    rfc_fields = [{"FIELDNAME": f} for f in fields]
    res = conn.call("RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
                    ROWCOUNT=0, FIELDS=rfc_fields, OPTIONS=opts)
    hdrs = [f["FIELDNAME"] for f in res.get("FIELDS", [])]
    out = []
    for row in res.get("DATA", []):
        parts = row["WA"].split("|")
        out.append({h: (parts[i].strip() if i < len(parts) else "")
                    for i, h in enumerate(hdrs)})
    return out


def _date_chunks(start, end, step):
    """Inclusive YYYYMMDD sub-windows [start..end], each <= step days."""
    out, cur = [], start
    while cur <= end:
        nxt = min(cur + datetime.timedelta(days=step - 1), end)
        out.append((cur.strftime("%Y%m%d"), nxt.strftime("%Y%m%d")))
        cur = nxt + datetime.timedelta(days=1)
    return out


def _read_windowed(conn, table, fields, date_field, d0, d1):
    """Read one date window; on DATA_BUFFER_EXCEEDED, recurse day-by-day. No ROWSKIPS."""
    where = f"{date_field} >= '{d0}' AND {date_field} <= '{d1}'"
    try:
        return _read_window(conn, table, fields, where)
    except RFCError as e:
        if "TABLE_WITHOUT_DATA" in str(e):
            return []
        if "DATA_BUFFER_EXCEEDED" not in str(e):
            raise
        s = datetime.datetime.strptime(d0, "%Y%m%d").date()
        e2 = datetime.datetime.strptime(d1, "%Y%m%d").date()
        if s >= e2:
            raise  # a single day already overflows the buffer — cannot split further
        rows = []
        for dd0, dd1 in _date_chunks(s, e2, max(1, (e2 - s).days // 2)):
            rows += _read_windowed(conn, table, fields, date_field, dd0, dd1)
        return rows


def accumulate(conn, db, src_table, spec, run_stamp):
    df, lb = spec.get("date_field"), spec.get("lookback_days")
    rows = []
    if df and lb:
        start = datetime.date.today() - datetime.timedelta(days=lb)
        end = datetime.date.today()
        for d0, d1 in _date_chunks(start, end, spec.get("chunk_days", 15)):
            rows += _read_windowed(conn, src_table, spec["fields"], df, d0, d1)
            time.sleep(0.3)
    else:
        try:
            rows = _read_window(conn, src_table, spec["fields"], "")  # full live table (bounded)
        except RFCError as e:
            if "TABLE_WITHOUT_DATA" not in str(e):
                raise
    before = db.execute(f'SELECT COUNT(*) FROM {spec["history"]}').fetchone()[0]
    ph = ",".join("?" * (len(spec["fields"]) + 1))
    collist = ",".join(f'"{f}"' for f in spec["fields"]) + ',"_first_seen"'
    db.executemany(
        f'INSERT OR IGNORE INTO {spec["history"]} ({collist}) VALUES ({ph})',
        [[r.get(f, "") for f in spec["fields"]] + [run_stamp] for r in rows])
    db.commit()
    after = db.execute(f'SELECT COUNT(*) FROM {spec["history"]}').fetchone()[0]
    added = after - before
    print(f'  {src_table}: pulled {len(rows)} rows, +{added} NEW into '
          f'{spec["history"]} (total {after})')
    return {"pulled": len(rows), "added": added, "total": after}


def freshness_guard():
    """Warn loudly if we are outside the P01 retention window (gap risk)."""
    if not os.path.exists(STATE):
        print("  [WARN] NEVER RUN before - first real accumulation. Anything already purged "
              f"by P01 (~{P01_WINDOW_DAYS}d) is unrecoverable.")
        return
    try:
        last = json.load(open(STATE)).get("run")
        days = (datetime.date.today() -
                datetime.datetime.strptime(last, "%Y-%m-%d").date()).days
        if days > P01_WINDOW_DAYS:
            # NO decir "perdido para siempre": es una suposicion, y el 2026-08-22 fue FALSA --
            # tras 62 dias parados P01 todavia servia el 22-jun (23.076 filas en 2h). Lo que se
            # pierde de verdad lo dice la retencion MEDIDA, no el intervalo de agenda; y la
            # ventana se ensancha sola (derive_rsau_days), no hace falta actuar a mano.
            print(f"  [WARN] GAP - last run {last} ({days}d ago) > schedule interval "
                  f"(~{P01_WINDOW_DAYS}d). RSAU widens its window automatically; "
                  f"beyond ~{RSAU_MAX_DAYS}d (measured SM20 retention) it IS unrecoverable.")
        else:
            print(f"  [OK] Last run {last} ({days}d ago) - within P01 window.")
    except Exception as e:
        print(f"  (could not read state: {e})")


def coverage_report(db):
    """Per-stream retention coverage vs the ≥6-month target. No P01 needed."""
    print("\n=== RETENTION / COVERAGE  (target >=6 months = "
          f"{RETENTION_MIN_DAYS}d) ===")
    tables = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for src, spec in LOG_TABLES.items():
        h = spec["history"]
        if h not in tables:
            print(f"  {h}: (not created yet)")
            continue
        n = db.execute(f'SELECT COUNT(*) FROM {h}').fetchone()[0]
        df = spec.get("date_field")
        span_txt = ""
        if df:
            lo, hi = db.execute(
                f'SELECT MIN({df}), MAX({df}) FROM {h} WHERE {df} > "00000000"').fetchone()
            if lo and hi:
                sd = _span_days(lo, hi)
                flag = "OK >=6mo" if sd >= RETENTION_MIN_DAYS else "[WARN] BELOW 6mo"
                span_txt = f" | {df} {lo}->{hi} ({sd}d, {flag})"
        fs = db.execute(
            f'SELECT MIN(_first_seen), MAX(_first_seen) FROM {h} '
            f'WHERE _first_seen IS NOT NULL').fetchone()
        live = f" | live-runs {fs[0]}..{fs[1]}" if fs[0] else " | live-runs none (seed only)"
        print(f"  {h:16s}: {n:>9,} rows{span_txt}{live}")
    _rsau_coverage(db)
    if os.path.exists(STATE):
        last = json.load(open(STATE)).get("run")
        print(f"  last accumulation run: {last}")
    else:
        print("  last accumulation run: NEVER")


def _rsau_coverage(db):
    """RSAU was ABSENT from this report until 2026-08-22 -- which is why a 45-day hole
    (July 2026 = 0 rows) sat there unseen while the report said everything was OK. A
    span MIN..MAX hides holes by construction, so count the days that are actually
    MISSING inside the span and name the biggest run of them."""
    try:
        days = sorted(r[0] for r in db.execute(
            f'SELECT DISTINCT SAL_DATE FROM {RSAU_HISTORY} WHERE SAL_DATE != ""'))
    except sqlite3.Error:
        print(f"  {RSAU_HISTORY}: (not created yet)")
        return
    if not days:
        print(f"  {RSAU_HISTORY}: 0 rows")
        return
    n = db.execute(f'SELECT COUNT(*) FROM {RSAU_HISTORY}').fetchone()[0]
    have = set(days)
    lo = datetime.datetime.strptime(days[0], "%Y%m%d").date()
    hi = datetime.datetime.strptime(days[-1], "%Y%m%d").date()
    total = (hi - lo).days + 1
    missing, worst, run, run_start = [], (0, None, None), 0, None
    for k in range(total):
        d = lo + datetime.timedelta(days=k)
        if d.strftime("%Y%m%d") in have:
            run, run_start = 0, None
        else:
            missing.append(d)
            run_start = run_start or d
            run += 1
            if run > worst[0]:
                worst = (run, run_start, d)
    flag = "OK >=6mo" if total >= RETENTION_MIN_DAYS else "[WARN] BELOW 6mo"
    print(f"  {RSAU_HISTORY:16s}: {n:>9,} rows | SAL_DATE {days[0]}->{days[-1]} "
          f"({total}d, {flag})")
    if missing:
        print(f"      [WARN] {len(missing)} of {total} days have NO rows - "
              f"biggest run {worst[0]}d ({worst[1]:%Y-%m-%d}..{worst[2]:%Y-%m-%d}). "
              f"Probe P01 before calling any of them lost - retention measured >=182d "
              f"and the boundary has never been found.")
    else:
        print(f"      [OK] no missing days inside the span")


# ---------------------------------------------------------------------------
# SM20 Security Audit Log (RSAU) — FM-based, NOT a transparent table.
# Real SAP source: SM20 / FM RSAU_API_GET_LOG_DATA. Volatile (~15d retention in
# P01, ~236K rows/day) -> THE system log that purges. Read CHUNKED by <=6h (a
# multi-day single call hangs on volume). Dedup by a row content-hash PK so
# overlapping windows never duplicate AND no distinct event is ever dropped.
RSAU_HISTORY = "rsau_audit_history"   # real-SAP-name convention (SM20 / RSAU / SAL)
RSAU_FIELDS = ["SID", "INSTANCE", "SAL_DATE", "SAL_TIME", "SLGMAND", "AREA", "SUBID",
               "MSG", "SLGUSER", "COUNTER", "SLGLTRM2", "TERM_IPV6", "SLGTC", "SLGREPNA",
               "SUBCLASID", "TXSUBCLSID", "SEVERITY", "SEVERITY_S", "TXSEVERITY", "FILE_NO",
               "TASKTYPE", "TASKNO", "SAL_DATA", "PARAM1", "PARAM2", "PARAM3", "PARAMX", "SRC"]
# The RSAU window is DERIVED from coverage, never a constant -- see derive_rsau_days().
# H110 (2026-08-22): it WAS a constant 16, so a run after a 62-day gap asked for 16 days and
# silently left 45 days behind (July = 0 rows) that P01 still held. freshness_guard() printed
# the gap as a WARN and the code then asked for 16 days anyway: detecting is not acting.
RSAU_MIN_DAYS   = 16   # floor: the routine 14-day schedule + margin
# Ceiling. FIRST SET TO 70 AND THAT WAS WRONG (2026-08-22): 70 came from the deepest day the
# probe happened to test, not from a boundary anybody found -- and claim #217 already said
# ">=4 months", more than the probe, sitting in the brain unread. A ceiling derived from your
# own partial probe silently redefines "unrecoverable" as "further back than I looked": the 12
# missing days of Feb-Mar got declared lost on exactly that reasoning, and they were not.
# Probed 2026-08-22, window 08-10h: 20260224 (179d back) -> 22,307 rows; 20260221 (182d)
# -> 12,663. THE TRUE BOUNDARY IS STILL NOT FOUND -- P01 was still serving data at the deepest
# day tested. So this is a floor on retention, and it is set past the >=183d target on purpose:
# too high only costs empty calls, too low silently abandons recoverable days.
RSAU_MAX_DAYS   = 200
RSAU_MARGIN_DAYS = 2   # overlap so consecutive windows dedupe into a continuous history
RSAU_CHUNK_HOURS = 6     # a 6h block stays well under the buffer/timeout


def ensure_rsau_table(db):
    cols = ", ".join(f'"{f}" TEXT' for f in RSAU_FIELDS)
    db.execute(f'CREATE TABLE IF NOT EXISTS {RSAU_HISTORY} '
               f'({cols}, _first_seen TEXT, _rowhash TEXT PRIMARY KEY)')


RSAU_RECONNECT_EVERY = 12  # the FM/connection poisons after ~18 heavy calls -> recycle the conn


def _rsau_call(conn, iv):
    res = conn.call("RSAU_API_GET_LOG_DATA", IS_INTERVAL=iv, ID_FILE_SEL_SIMPLE="X")
    return res.get("ET_LOG", [])


def _rsau_connect():
    """get_connection that returns None instead of raising — so a transient
    'partner not reached' / closed conn never aborts the whole accumulation."""
    try:
        return get_connection("P01")
    except Exception as e:
        print(f"    [connect retry] {str(e)[:90]}")
        return None


def derive_rsau_days(db, today=None):
    """How far back to ask P01 -- derived from what rsau_audit_history ACTUALLY HOLDS.

    Finds the OLDEST day with no rows inside the retention ceiling and stretches the window
    to reach it. That is deliberately not "days since the last run": a run that dies halfway
    still stamps the state, and once a later run fills the recent days a hole in the MIDDLE
    becomes invisible to any last-run arithmetic -- which is exactly how July 2026 went to
    zero. Coverage is the fact; the run date is only a claim about it.

    Returns (days, reason) -- reason is printed so the choice is auditable, never silent.
    """
    today = today or datetime.date.today()
    try:
        have = {r[0] for r in db.execute(
            f'SELECT DISTINCT SAL_DATE FROM {RSAU_HISTORY} WHERE SAL_DATE != ""')}
    except sqlite3.Error:
        return RSAU_MAX_DAYS, f"primera corrida (sin {RSAU_HISTORY}) -> ventana maxima"
    if not have:
        return RSAU_MAX_DAYS, "historia vacia -> ventana maxima"

    oldest_gap = None
    for back in range(RSAU_MAX_DAYS, -1, -1):          # del mas viejo al mas nuevo
        d = today - datetime.timedelta(days=back)
        if d.strftime("%Y%m%d") not in have:
            oldest_gap = (d, back)
            break
    if oldest_gap is None:
        return RSAU_MIN_DAYS, f"cobertura continua {RSAU_MAX_DAYS}d -> ventana minima"

    d, back = oldest_gap
    days = min(RSAU_MAX_DAYS, max(RSAU_MIN_DAYS, back + RSAU_MARGIN_DAYS))
    missing = sum((today - datetime.timedelta(days=b)).strftime("%Y%m%d") not in have
                  for b in range(back + 1))
    reason = (f"hueco mas antiguo {d:%Y-%m-%d} ({back}d atras), {missing} dia(s) sin datos "
              f"dentro del techo -> ventana {days}d")
    if back >= RSAU_MAX_DAYS:
        # NO decir "ya no esta en P01": el techo es NUESTRO, no de P01. Decirlo asi fue el
        # mismo error tres veces el 2026-08-22 -- declarar irrecuperable lo que esta mas atras
        # de donde uno miro. El techo es donde dejamos de preguntar; la frontera real solo la
        # sabe una sonda: a 200d P01 aun servia 87.184 filas.
        edge = today - datetime.timedelta(days=RSAU_MAX_DAYS)
        reason += ("\n"
                   f"    [WARN] el hueco llega al techo ({RSAU_MAX_DAYS}d, {edge:%Y-%m-%d}). Ese "
                   f"techo es NUESTRO limite, no la retencion de P01, que nunca se ha "
                   f"encontrado. Antes de dar por perdido nada anterior a {edge:%Y-%m-%d}: "
                   f"sondear P01 y subir RSAU_MAX_DAYS")
    return days, reason


def accumulate_rsau(db, run_stamp, lookback_days, chunk_hours=RSAU_CHUNK_HOURS,
                    only_missing=True, always_days=3):
    """only_missing: ask P01 ONLY for days the history does not already hold.

    Once the ceiling is honest (>=200d instead of a made-up 70) a contiguous window costs
    ~800 RFC calls to fill ~30 real gaps -- 85% of them re-fetching rows we already have and
    throwing them away at the PK. The window decides HOW FAR BACK to look; this decides WHICH
    days are actually worth a call. The last `always_days` are pulled regardless: today is
    still being written, and yesterday may have been captured half-done.
    """
    ensure_rsau_table(db)
    now = datetime.datetime.utcnow()
    start = now - datetime.timedelta(days=lookback_days)
    skip_days = set()
    if only_missing:
        have = {r[0] for r in db.execute(
            f'SELECT DISTINCT SAL_DATE FROM {RSAU_HISTORY} WHERE SAL_DATE != ""')}
        recent = {(now - datetime.timedelta(days=k)).strftime("%Y%m%d")
                  for k in range(always_days)}
        skip_days = have - recent
    before = db.execute(f'SELECT COUNT(*) FROM {RSAU_HISTORY}').fetchone()[0]
    ph = ",".join("?" * (len(RSAU_FIELDS) + 2))
    collist = ",".join(f'"{f}"' for f in RSAU_FIELDS) + ',"_first_seen","_rowhash"'
    total_pulled, cur, chunk_i, fail_n = 0, start, 0, 0
    mode = (f"solo dias ausentes ({len(skip_days)} dias ya cubiertos se saltan)"
            if only_missing else "ventana completa")
    print(f"  RSAU: {lookback_days}-day window, {chunk_hours}h chunks, {mode}, "
          f"recycle conn every {RSAU_RECONNECT_EVERY} chunks")
    conn = _rsau_connect()
    while cur < now:
        nxt = min(cur + datetime.timedelta(hours=chunk_hours), now)
        if cur.strftime("%Y%m%d") in skip_days:   # dia ya cubierto -> ni una llamada
            cur = nxt; continue
        chunk_i += 1
        if conn is None or chunk_i % RSAU_RECONNECT_EVERY == 0:   # recycle / recover
            try: conn.close()
            except Exception: pass
            conn = _rsau_connect()
            if conn is None:
                time.sleep(5); conn = _rsau_connect()
        if conn is None:                          # still down -> skip chunk, retry next
            fail_n += 1; cur = nxt; continue
        iv = {"DAT_FROM": cur.strftime("%Y%m%d"), "TIM_FROM": cur.strftime("%H%M%S"),
              "DAT_TO": nxt.strftime("%Y%m%d"), "TIM_TO": nxt.strftime("%H%M%S")}
        rows = None
        for attempt in (1, 2, 3):              # on error: SAFE reconnect + retry the chunk
            try:
                rows = _rsau_call(conn, iv); break
            except Exception as e:
                if attempt == 1:
                    print(f"    RSAU {iv['DAT_FROM']} {iv['TIM_FROM']}: retry after {str(e)[:130]}")
                try: conn.close()
                except Exception: pass
                time.sleep(1.5 * attempt)
                conn = _rsau_connect()
                if conn is None: break
        if rows is None:
            fail_n += 1; cur = nxt; continue
        total_pulled += len(rows)
        if rows:
            batch = []
            for r in rows:
                vals = [str(r.get(f, "")) for f in RSAU_FIELDS]
                h = hashlib.md5("|".join(vals).encode("utf-8", "replace")).hexdigest()
                batch.append(vals + [run_stamp, h])
            db.executemany(f'INSERT OR IGNORE INTO {RSAU_HISTORY} ({collist}) VALUES ({ph})', batch)
            db.commit()
            print(f"    RSAU {cur:%Y-%m-%d %H:%M}: {len(rows)} rows")
        cur = nxt
        time.sleep(0.15)
    try: conn.close()
    except Exception: pass
    if fail_n: print(f"  RSAU: {fail_n} chunks still failed after retries")
    after = db.execute(f'SELECT COUNT(*) FROM {RSAU_HISTORY}').fetchone()[0]
    lo, hi = db.execute(f'SELECT MIN(SAL_DATE), MAX(SAL_DATE) FROM {RSAU_HISTORY} '
                        f'WHERE SAL_DATE > "0"').fetchone()
    print(f"  RSAU TOTAL: pulled {total_pulled:,}, +{after - before:,} NEW "
          f"(table {after:,}, span {lo}->{hi}) -- real retention boundary visible above")
    return {"pulled": total_pulled, "added": after - before, "total": after, "span": [lo, hi]}


def main():
    verify_only = "--verify" in sys.argv
    db = sqlite3.connect(GOLD_DB, timeout=120)

    if verify_only:
        coverage_report(db)
        db.close()
        return

    rsau_only = "--rsau-only" in sys.argv
    rsau_days, rsau_why = None, None
    if "--rsau-days" in sys.argv:
        i = sys.argv.index("--rsau-days")
        if i + 1 < len(sys.argv):
            rsau_days = int(sys.argv[i + 1])
            rsau_why = "forzado por --rsau-days"
    if rsau_days is None:
        ensure_rsau_table(db)
        rsau_days, rsau_why = derive_rsau_days(db)
    rsau_full = "--rsau-full" in sys.argv   # re-pull days we already have (repair, not routine)

    run_stamp = datetime.datetime.now().strftime("%Y-%m-%d")
    print(f"=== accumulate_logs  (run {run_stamp}) ===")
    print("Connecting to P01 ...")
    conn = get_connection("P01")
    report = {"run": run_stamp, "tables": {}}
    try:
        if not rsau_only:
            freshness_guard()
            for spec in LOG_TABLES.values():
                ensure_history_table(db, spec)
            db.commit()
            for src, spec in LOG_TABLES.items():
                try:
                    report["tables"][src] = accumulate(conn, db, src, spec, run_stamp)
                except Exception as e:
                    print(f"  {src}: FAILED - {type(e).__name__}: {str(e)[:160]}")
                    report["tables"][src] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
        # SM20/RSAU Security Audit Log -- the headline volatile log that purges
        try:
            print(f"  RSAU ventana: {rsau_days}d - {rsau_why}")
            report["tables"]["RSAU"] = accumulate_rsau(db, run_stamp, rsau_days,
                                                       only_missing=not rsau_full)
        except Exception as e:
            print(f"  RSAU: FAILED - {type(e).__name__}: {str(e)[:160]}")
            report["tables"]["RSAU"] = {"error": f"{type(e).__name__}: {str(e)[:160]}"}
    finally:
        try: conn.close()
        except Exception: pass
    json.dump(report, open(STATE, "w", encoding="utf-8"), indent=2)
    # append-only RUN HISTORY (incremental log of every run -- never overwritten)
    runlog = os.path.join(os.path.dirname(__file__), "accumulate_logs_run_history.log")
    parts = []
    for k, v in report["tables"].items():
        if isinstance(v, dict):
            parts.append(f"{k}:+{v.get('added', v.get('error', '?'))}")
    with open(runlog, "a", encoding="utf-8") as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M}  {'  '.join(parts)}\n")
    print(f"\nState: {STATE}\nRun history: {runlog}")
    coverage_report(db)
    db.close()


if __name__ == "__main__":
    main()
