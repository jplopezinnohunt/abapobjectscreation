"""
f0_probe.py — the F0 INGEST GATE runner
=======================================
Executes the probes declared in `probe_suite_f0.json` against ONE SAP system and
emits `system_profile.json`: the machine-readable NEGATIVE CONTRACT of that system
(what the RFC boundary will NOT let us read, and the extraction strategy that works
anyway). Run it FIRST on any new tenant/system, before writing a single extractor.

Design rules (do not relax them):
  * READ-ONLY. Only the function modules in the suite's `read_only_allowlist` may be
    called, and SADT_REST_RFC_ENDPOINT is pinned to HTTP GET. Enforced in `_guard_fm`.
  * The suite JSON is the SPECIFICATION. This runner CONSUMES it; it never rewrites it.
  * Three outcomes, never conflated:
        CONSTRAINT_CONFIRMED  the expected failure reproduced -> the restriction EXISTS
                              here -> apply `derived_strategy`.   (suite: CONFIRMED)
        NO_CONSTRAINT         the call worked -> the restriction does NOT exist here ->
                              the naive/fast path is allowed.     (suite: NOT_PRESENT)
        COULD_NOT_PROBE       no connection / control call failed / unrecognised error ->
                              NOTHING is derived from it.         (suite: INCONCLUSIVE)
    "I could not probe" is NEVER reported as "the restriction exists". That single
    confusion is what makes a system_profile actively harmful.
  * Nothing blocks forever: every RFC call runs in a daemon thread with a hard
    per-call timeout, and the whole run is bounded by a global budget.
  * If we cannot connect at all, NO profile is written (exit 3). A half-written
    profile is worse than no profile.

Usage:
    python f0_probe.py --system P01 --dry-run          # list probes, never connects
    python f0_probe.py --system P01                    # full gate -> system_profile.json
    python f0_probe.py --system D01 --probe rowskips_rejected --out d01_profile.json
    python f0_probe.py --system Q99 --allow-unknown-system      # new tenant SID

Exit codes:
    0  profile written, every probe evaluated (no COULD_NOT_PROBE)
    1  profile written but INCOMPLETE (>=1 COULD_NOT_PROBE) — do not treat as a baseline
    2  usage / suite error (nothing written)
    3  could not connect to SAP (nothing written)
    4  --fail-on-kill was given and a KILL-severity constraint was confirmed

Contract: sapilot/analysis/arch/C1-extraccion-hub.md §3 "Contrato C — probe_suite_f0".
"""
import argparse
import json
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# --- repo layout (same pattern as scripts/extraction/gold_refresh.py L34-38) -------
HERE = Path(__file__).resolve().parent                       # .../sap_data_extraction/scripts
REPO = HERE.parents[2]                                       # .../abapobjectscreation
MCP = REPO / "Zagentexecution" / "mcp-backend-server-python"
sys.path.insert(0, str(MCP))
# NOTE: rfc_helpers is imported LAZILY (see _load_rfc_helpers) so that --dry-run works
# on a machine without pyrfc / python-dotenv installed.

DEFAULT_SUITE = HERE / "probe_suite_f0.json"
DEFAULT_OUT = HERE / "system_profile.json"
KNOWN_SYSTEMS = ("P01", "D01", "V01")
PROFILE_VERSION = "1.0.0"

# status vocabulary — this runner's names, and the suite's names, kept side by side
CONFIRMED = "CONSTRAINT_CONFIRMED"
NO_CONSTRAINT = "NO_CONSTRAINT"
COULD_NOT_PROBE = "COULD_NOT_PROBE"
SUITE_STATUS = {
    CONFIRMED: "CONFIRMED",
    NO_CONSTRAINT: "NOT_PRESENT",
    COULD_NOT_PROBE: "INCONCLUSIVE",
}
# `readable` = was the naive/fast read path usable for this probe's scope?
READABLE = {CONFIRMED: False, NO_CONSTRAINT: True, COULD_NOT_PROBE: None}

CONN_ERROR_HINTS = (
    "connection closed", "partner not reached", "timeout", "communication failure",
    "cpic_", "rfc_communication_failure", "rfc_invalid_handle", "rfc_closed",
    "connection to partner", "broken", "wsaeconnreset", "wsaetimedout",
    "connection reset", "rfc_logon_failure", "name or password", "logon",
)


# =============================================================== infrastructure
class ProbeTimeout(Exception):
    """A single RFC call did not return inside its hard timeout."""


class BudgetExhausted(Exception):
    """The run's global time budget ran out; remaining probes are not attempted."""


def _run_with_timeout(fn, timeout, *args, **kwargs):
    """Run fn in a daemon thread; raise ProbeTimeout if it does not return in time.

    The thread is NOT killable (CPython), but it is a daemon: the process can still
    exit. This is what keeps a hung RFC call from freezing the gate.
    """
    box = {}

    def _target():
        try:
            box["value"] = fn(*args, **kwargs)
        except BaseException as exc:      # noqa: BLE001 - re-raised in the caller
            box["error"] = exc

    th = threading.Thread(target=_target, daemon=True, name="f0-rfc-call")
    th.start()
    th.join(timeout)
    if th.is_alive():
        raise ProbeTimeout("no response within %.0fs" % timeout)
    if "error" in box:
        raise box["error"]
    return box.get("value")


def _err_info(exc):
    """Capture the REAL SAP symptom, not our paraphrase of it."""
    info = {"type": type(exc).__name__, "raw": str(exc).strip()}
    for attr in ("code", "key", "message", "msg_class", "msg_type", "msg_number"):
        val = getattr(exc, attr, None)
        if val not in (None, ""):
            info[attr] = str(val)
    return info


def _looks_like_connection_error(text):
    low = (text or "").lower()
    return any(hint in low for hint in CONN_ERROR_HINTS)


def _matched(signatures, text):
    low = (text or "").lower()
    return [s for s in (signatures or []) if s and s.lower() in low]


def _parse_rows(result):
    """RFC_READ_TABLE without DELIMITER -> fixed-width WA + FIELDS(OFFSET,LENGTH)."""
    meta = result.get("FIELDS", []) or []
    rows = []
    for row in result.get("DATA", []) or []:
        wa = row.get("WA", "")
        rows.append({
            f["FIELDNAME"]: wa[int(f["OFFSET"]):int(f["OFFSET"]) + int(f["LENGTH"])].strip()
            for f in meta
        })
    return rows


def _options(where):
    """RFC_READ_TABLE OPTIONS lines are 72 chars max — wrap on whitespace."""
    if not where:
        return []
    out, line = [], ""
    for token in str(where).split(" "):
        candidate = token if not line else line + " " + token
        if len(candidate) > 72 and line:
            out.append({"TEXT": line})
            line = token
        else:
            line = candidate
    if line:
        out.append({"TEXT": line})
    return out


def _load_rfc_helpers():
    """Lazy import so --dry-run never needs pyrfc/dotenv. Returns (get_connection, MAX_FIELDS)."""
    from rfc_helpers import get_connection, MAX_FIELDS_PER_CALL  # type: ignore
    return get_connection, MAX_FIELDS_PER_CALL


def _split_ladder(max_fields):
    """Derive the field-split ladder from the IMPLEMENTATION constant so it cannot drift.

    rfc_helpers.py: `chunk_size = MAX_FIELDS_PER_CALL; while chunk_size >= 2: ... //= 2`
    -> 8 -> 4 -> 2 (never 1; the caller aborts below 2).
    """
    ladder, chunk = [], int(max_fields)
    while chunk >= 2:
        ladder.append(chunk)
        chunk //= 2
    return ladder


# ================================================================= RFC surface
class RfcProbeSession:
    """Every SAP call the gate makes goes through here: allowlist-guarded, timed,
    and recorded as evidence with the REAL error text."""

    def __init__(self, guard, allowlist, call_timeout, deadline):
        self.guard = guard
        self.allowlist = set(allowlist or [])
        self.call_timeout = call_timeout
        self.deadline = deadline
        self.calls = []            # evidence for the probe currently running
        self.connection_lost = False

    # ---- read-only enforcement ------------------------------------------------
    def _guard_fm(self, fm, kwargs):
        if fm not in self.allowlist:
            raise RuntimeError(
                "READ-ONLY VIOLATION: '%s' is not in the suite read_only_allowlist %s"
                % (fm, sorted(self.allowlist))
            )
        if fm == "SADT_REST_RFC_ENDPOINT":
            for key, val in kwargs.items():
                if "METHOD" in key.upper() and isinstance(val, str) and val.upper() != "GET":
                    raise RuntimeError(
                        "READ-ONLY VIOLATION: ADT probe attempted HTTP %s; only GET is allowed" % val
                    )

    def _check_budget(self):
        if self.deadline is not None and time.time() > self.deadline:
            raise BudgetExhausted("global time budget exhausted before the call was issued")

    # ---- generic call ---------------------------------------------------------
    def call(self, fm, label="", **kwargs):
        """Never raises on a SAP error: returns a record. Raises only on budget/guard."""
        self._check_budget()
        self._guard_fm(fm, kwargs)
        rec = {"fm": fm, "label": label, "ok": False}
        if fm == "RFC_READ_TABLE":
            rec["query"] = {
                "table": kwargs.get("QUERY_TABLE"),
                "fields": [f.get("FIELDNAME") for f in kwargs.get("FIELDS", [])],
                "rowcount": kwargs.get("ROWCOUNT"),
                "rowskips": kwargs.get("ROWSKIPS"),
                "options": [o.get("TEXT") for o in kwargs.get("OPTIONS", [])],
            }
        started = time.time()
        if self.connection_lost:
            rec["error"] = {"type": "NoConnection", "raw": "connection already lost earlier in this run"}
            rec["fatal"] = True
            self.calls.append(rec)
            return rec
        try:
            result = _run_with_timeout(self.guard.call, self.call_timeout, fm, **kwargs)
            rec["ok"] = True
            rec["result"] = result
        except ProbeTimeout as exc:
            rec["error"] = {"type": "ProbeTimeout", "raw": str(exc)}
            rec["fatal"] = True          # a hung call means we can trust nothing after it
            self.connection_lost = True
        except BaseException as exc:     # noqa: BLE001 - SAP errors are DATA here
            info = _err_info(exc)
            rec["error"] = info
            if _looks_like_connection_error(info.get("raw", "")):
                rec["fatal"] = True
                self.connection_lost = True
        rec["elapsed_s"] = round(time.time() - started, 2)
        self.calls.append(rec)
        return rec

    # ---- RFC_READ_TABLE convenience ------------------------------------------
    def read_table(self, table, fields, where=None, rowcount=1, rowskips=None, label=""):
        kwargs = {
            "QUERY_TABLE": table,
            "FIELDS": [{"FIELDNAME": f} for f in fields],
            "ROWCOUNT": int(rowcount),
            "OPTIONS": _options(where),
        }
        if rowskips is not None:
            kwargs["ROWSKIPS"] = int(rowskips)
        rec = self.call("RFC_READ_TABLE", label=label or table, **kwargs)
        rec["rows"] = []
        rec["empty_signal"] = None
        if rec["ok"]:
            rec["rows"] = _parse_rows(rec.pop("result", {}) or {})
            rec["n_rows"] = len(rec["rows"])
        else:
            raw = rec.get("error", {}).get("raw", "")
            # rfc_helpers treats TABLE_WITHOUT_DATA as "zero rows", not as an error.
            # We keep the signal visible: wide_field_split reads it as an overflow symptom,
            # max_where_conditions reads it as a legitimately narrow filter.
            if "TABLE_WITHOUT_DATA" in raw and not rec.get("fatal"):
                rec["ok"] = True
                rec["n_rows"] = 0
                rec["empty_signal"] = "TABLE_WITHOUT_DATA"
        return rec

    # ---- evidence -------------------------------------------------------------
    def take_calls(self):
        calls, self.calls = self.calls, []
        # strip raw payloads: keep the shape, not megabytes of DATA
        for c in calls:
            c.pop("result", None)
        return calls


# ==================================================================== the probes
def _fail_signature(rec, spec):
    return _matched(spec.get("failure_signatures"), rec.get("error", {}).get("raw", ""))


def _err_text(rec, limit=400):
    err = rec.get("error", {}) or {}
    bits = [err.get("key"), err.get("raw")]
    return " | ".join(b for b in bits if b)[:limit]


def probe_rowskips_rejected(spec, rt):
    par = spec["params"]
    table, field = par["probe_table"], par["field"]
    rowcount = int(par.get("rowcount", 1))
    ctl = rt.read_table(table, [field], rowcount=rowcount, rowskips=0, label="control ROWSKIPS=0")
    if not ctl["ok"]:
        return COULD_NOT_PROBE, {}, ("control read (ROWSKIPS=0) failed, so a ROWSKIPS failure could "
                                     "not be attributed: " + _err_text(ctl)), []
    tst = rt.read_table(table, [field], rowcount=rowcount, rowskips=int(par.get("rowskips", 1)),
                        label="ROWSKIPS=%s" % par.get("rowskips", 1))
    if tst["ok"]:
        return NO_CONSTRAINT, {"rowskips_accepted": True, "rows": tst.get("n_rows", 0)}, \
            "ROWSKIPS=%s accepted (%d row(s)) -> ordinary pagination is allowed on this system." \
            % (par.get("rowskips", 1), tst.get("n_rows", 0)), []
    sigs = _fail_signature(tst, spec)
    if sigs:
        return CONFIRMED, {"rowskips_accepted": False}, \
            "ROWSKIPS rejected by the RFC wrapper: " + _err_text(tst), sigs
    return COULD_NOT_PROBE, {}, ("ROWSKIPS call failed with an error that does NOT match the expected "
                                 "signatures - not attributing it to the wrapper: " + _err_text(tst)), []


def probe_in_clause_rejected(spec, rt):
    par = spec["params"]
    table, field = par["probe_table"], par["field"]
    values = par.get("values") or []
    ctl = rt.read_table(table, [field], where="%s = '%s'" % (field, values[0]),
                        label="control single equality")
    if not ctl["ok"]:
        return COULD_NOT_PROBE, {}, "control read (single equality WHERE) failed: " + _err_text(ctl), []
    in_list = ", ".join("'%s'" % v for v in values)
    tst = rt.read_table(table, [field], where="%s IN (%s)" % (field, in_list), label="IN (...) list")
    if tst["ok"]:
        return NO_CONSTRAINT, {"in_clause_accepted": True, "rows": tst.get("n_rows", 0)}, \
            "IN (...) accepted -> value lists may be batched (still cap the OPTIONS text length).", []
    sigs = _fail_signature(tst, spec)
    if sigs:
        return CONFIRMED, {"in_clause_accepted": False}, \
            "IN (...) rejected by the anti-injection WHERE guard: " + _err_text(tst), sigs
    return COULD_NOT_PROBE, {}, ("IN (...) failed with an unrecognised error - not attributed to the "
                                 "WHERE guard: " + _err_text(tst)), []


def probe_max_where_conditions(spec, rt):
    par = spec["params"]
    table = par["probe_table"]
    conds = list(par.get("conditions") or [])[:int(par.get("max_ladder", 6))]
    if not conds:
        return COULD_NOT_PROBE, {}, "suite provided no ladder conditions", []
    field = conds[0].split()[0]
    max_ok, first_fail = 0, None
    for n in range(1, len(conds) + 1):
        where = " AND ".join(conds[:n])
        rec = rt.read_table(table, [field], where=where, label="ladder n=%d" % n)
        if rec["ok"]:
            # zero rows is SUCCESS here: the filter is simply narrow, the parser coped.
            max_ok = n
            continue
        if rec.get("fatal"):
            return COULD_NOT_PROBE, {"max_where_conditions_ok": max_ok}, \
                "ladder aborted at n=%d by a connection/timeout failure: %s" % (n, _err_text(rec)), []
        first_fail = (n, rec)
        break
    if first_fail is None:
        return NO_CONSTRAINT, {"max_where_conditions": ">= %d" % max_ok, "tested_ceiling": max_ok}, \
            ("no ladder step failed up to n=%d; the ceiling is table- and length-dependent, so still "
             "cap conservatively." % max_ok), []
    n, rec = first_fail
    sigs = _fail_signature(rec, spec)
    measured = {"max_where_conditions": max_ok, "first_failing_n": n}
    if sigs:
        return CONFIRMED, measured, \
            "WHERE parser accepted %d ANDed condition(s); n=%d failed: %s" % (max_ok, n, _err_text(rec)), sigs
    return COULD_NOT_PROBE, measured, \
        ("ladder failed at n=%d with an unrecognised error; the measurement is recorded but NO strategy "
         "is derived: %s" % (n, _err_text(rec))), []


def probe_wide_field_split(spec, rt, ladder=None):
    par = spec["params"]
    limit = int(par.get("wa_limit_bytes", 512))
    ladder = ladder or [8, 4, 2]
    candidates = [par["wide_table"]] + list(par.get("fallback_wide_tables") or [])
    chosen = None
    for table in candidates:
        dd03 = rt.read_table("DD03L", ["FIELDNAME", "POSITION", "LENG", "DATATYPE"],
                             where="TABNAME = '%s'" % table, rowcount=0, label="DD03L %s" % table)
        if not dd03["ok"] or not dd03.get("rows"):
            if dd03.get("fatal"):
                return COULD_NOT_PROBE, {}, "DD03L read failed (connection): " + _err_text(dd03), []
            continue
        rows = [r for r in dd03["rows"] if r.get("FIELDNAME") and not r["FIELDNAME"].startswith(".")]
        try:
            rows.sort(key=lambda r: int(r.get("POSITION") or 0))
        except (TypeError, ValueError):
            pass
        wide, total = [], 0
        for r in rows:
            try:
                total += int(r.get("LENG") or 0)
            except ValueError:
                pass
            wide.append(r["FIELDNAME"])
            if total > limit:
                break
        if total <= limit:
            continue                                   # this table is not wide enough to test
        ctl = rt.read_table(table, wide[:2], rowcount=1, label="control 2 fields %s" % table)
        if not ctl["ok"] or ctl.get("n_rows", 0) == 0:
            continue                                   # empty table -> useless as a probe object
        chosen = (table, wide, total)
        break
    if chosen is None:
        return COULD_NOT_PROBE, {}, \
            ("no usable wide probe table among %s (needed >%d bytes of leading fields AND non-empty "
             "content)" % (candidates, limit)), []
    table, wide, total = chosen
    full = rt.read_table(table, wide, rowcount=1, label="wide read %d fields" % len(wide))
    measured = {"probe_table": table, "fields_requested": len(wide),
                "estimated_wa_bytes": total, "wa_limit_bytes": limit, "ladder": ladder}
    if full["ok"] and full.get("n_rows", 0) > 0:
        return NO_CONSTRAINT, measured, \
            "%d fields (~%d bytes) returned data in ONE call -> no field-split needed on this system." \
            % (len(wide), total), []
    sigs = _fail_signature(full, spec)
    if full["ok"] and full.get("n_rows", 0) == 0:
        # the wrapper's silent surface of the same overflow: control returned rows, wide did not
        sigs = sigs or ([full["empty_signal"]] if full.get("empty_signal") else ["silently empty DATA"])
    if not sigs:
        return COULD_NOT_PROBE, measured, \
            "wide read failed with an unrecognised error: " + _err_text(full), []
    chunk = None
    for size in ladder:
        test = rt.read_table(table, wide[:size], rowcount=1, label="split ladder chunk=%d" % size)
        if test["ok"] and test.get("n_rows", 0) > 0:
            chunk = size
            break
        if test.get("fatal"):
            break
    measured["chunk_size"] = chunk
    if chunk is None:
        return COULD_NOT_PROBE, measured, \
            ("wide read failed AND no ladder step (%s) returned data - the probe object or the auth is "
             "the problem, not the buffer." % ladder), sigs
    return CONFIRMED, measured, \
        ("%s: %d fields (~%d bytes) overflow the %d-byte work area; the split ladder %s first returns "
         "data at chunk=%d. Merge chunks BY ROW POSITION with an equal-rowcount guard."
         % (table, len(wide), total, limit, ladder, chunk)), sigs


def probe_cluster_unreadable(spec, rt):
    par = spec["params"]
    table, field = par["cluster_table"], par["field"]
    dd02 = rt.read_table("DD02L", ["TABNAME", "TABCLASS"], where="TABNAME = '%s'" % table,
                         label="DD02L %s" % table)
    declared = dd02["rows"][0].get("TABCLASS") if (dd02["ok"] and dd02.get("rows")) else None
    measured = {"declared_tabclass": declared}
    rec = rt.read_table(table, [field], rowcount=1, label="direct read %s" % table)
    extra = {}
    for other in (par.get("also_check") or []):
        # resolve a real field of THAT table first - reusing `field` would fail with
        # FIELD_NOT_VALID and be mistaken for a cluster symptom.
        meta = rt.read_table("DD03L", ["FIELDNAME", "POSITION"], where="TABNAME = '%s'" % other,
                             rowcount=0, label="DD03L %s" % other)
        names = [r["FIELDNAME"] for r in (meta.get("rows") or [])
                 if r.get("FIELDNAME") and not r["FIELDNAME"].startswith(".")]
        if not names:
            extra[other] = "no DD03L field list (%s)" % (_err_text(meta, 120) or "empty")
            continue
        o = rt.read_table(other, [names[0]], rowcount=1, label="also_check %s" % other)
        extra[other] = ("readable" if (o["ok"] and o.get("n_rows", 0) > 0)
                        else ("empty" if o["ok"] else _err_text(o, 160)))
    measured["also_check"] = extra
    if rec["ok"] and rec.get("n_rows", 0) > 0:
        measured["physically_readable"] = True
        return NO_CONSTRAINT, measured, \
            ("%s is declared %s but RFC_READ_TABLE returned rows -> declustered on this kernel; treat it "
             "as TRANSP under the rowskips/where/field-split constraints measured above."
             % (table, declared)), []
    if rec["ok"]:
        return COULD_NOT_PROBE, measured, \
            ("%s returned zero rows without an error (%s) - cannot distinguish 'declustered but empty' "
             "from 'not readable'." % (table, rec.get("empty_signal") or "no signal")), []
    sigs = _fail_signature(rec, spec)
    if sigs:
        measured["physically_readable"] = False
        return CONFIRMED, measured, \
            "%s (declared %s) is not reachable by RFC_READ_TABLE: %s" % (table, declared, _err_text(rec)), sigs
    return COULD_NOT_PROBE, measured, \
        "%s read failed with an unrecognised error: %s" % (table, _err_text(rec)), []


def _printable_ratio(text):
    if not text:
        return 0.0
    ok = sum(1 for ch in text if ch.isprintable())
    return ok / float(len(text))


def probe_strg_pool_unreadable(spec, rt, max_fields=8):
    par = spec["params"]
    table = par["pool_table"]
    raw_types = set(par.get("raw_datatypes") or [])
    dd02 = rt.read_table("DD02L", ["TABNAME", "TABCLASS"], where="TABNAME = '%s'" % table,
                         label="DD02L %s" % table)
    declared = dd02["rows"][0].get("TABCLASS") if (dd02["ok"] and dd02.get("rows")) else None
    dd03 = rt.read_table("DD03L", ["FIELDNAME", "KEYFLAG", "DATATYPE", "LENG", "POSITION"],
                         where="TABNAME = '%s'" % table, rowcount=0, label="DD03L %s" % table)
    if not dd03["ok"] or not dd03.get("rows"):
        return COULD_NOT_PROBE, {"declared_tabclass": declared}, \
            "could not read the DD03L field list for %s: %s" % (table, _err_text(dd03)), []
    fields = [r for r in dd03["rows"] if r.get("FIELDNAME") and not r["FIELDNAME"].startswith(".")]
    keys = [r["FIELDNAME"] for r in fields if r.get("KEYFLAG") == "X"]
    raws = [r["FIELDNAME"] for r in fields if (r.get("DATATYPE") or "").upper() in raw_types]
    measured = {"declared_tabclass": declared, "key_fields": keys,
                "raw_content_fields": raws, "raw_datatypes": sorted(raw_types)}
    if not keys:
        return COULD_NOT_PROBE, measured, "no KEYFLAG='X' fields found for %s" % table, []
    if not raws:
        return COULD_NOT_PROBE, measured, \
            "no RAW-content field (%s) found in %s - nothing to probe" % (sorted(raw_types), table), []
    ctl = rt.read_table(table, keys[:max_fields], rowcount=1, label="key-only read")
    if not ctl["ok"] or ctl.get("n_rows", 0) == 0:
        return COULD_NOT_PROBE, measured, \
            ("the key-only control read returned nothing (%s) - without it, a content failure proves "
             "nothing." % (_err_text(ctl) or "empty table")), []
    content_field = raws[0]
    tst = rt.read_table(table, [keys[0], content_field], rowcount=1,
                        label="content read %s" % content_field)
    if tst["ok"] and tst.get("n_rows", 0) > 0:
        value = (tst["rows"][0].get(content_field) or "")
        ratio = _printable_ratio(value)
        measured["content_len"] = len(value)
        measured["content_printable_ratio"] = round(ratio, 2)
        if value.strip() and ratio > 0.5:
            return NO_CONSTRAINT, measured, \
                ("the pooled payload column %s came back with usable content (%d chars) - verify the "
                 "bytes decode before trusting them." % (content_field, len(value))), []
        return CONFIRMED, measured, \
            ("key read SUCCEEDS but the payload column %s comes back empty/non-interpretable "
             "(len=%d, printable=%.2f) -> the RFC layer exposes the pool key, never the payload."
             % (content_field, len(value), ratio)), ["unusable bytes"]
    sigs = _fail_signature(tst, spec)
    if sigs:
        return CONFIRMED, measured, \
            "key read SUCCEEDS, content read of %s fails: %s" % (content_field, _err_text(tst)), sigs
    return COULD_NOT_PROBE, measured, \
        "content read of %s failed with an unrecognised error: %s" % (content_field, _err_text(tst)), []


# GET-only candidate signatures for SADT_REST_RFC_ENDPOINT. The parameter names differ
# across kernels; every candidate pins METHOD='GET' (enforced again in _guard_fm).
_ADT_SIGNATURES = (
    ("METHOD", "URI"),
    ("IV_METHOD", "IV_URI"),
    ("REQUEST_METHOD", "REQUEST_URI"),
    ("I_METHOD", "I_URI"),
    ("METHOD", "URL"),
)


def _flatten_text(obj, out, budget=200):
    if len(out) > budget:
        return
    if isinstance(obj, str):
        out.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            _flatten_text(v, out, budget)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            _flatten_text(v, out, budget)


def probe_adt_404_ehp8(spec, rt):
    par = spec["params"]
    fm = par["adt_fm"]
    tf = rt.read_table("TFDIR", ["FUNCNAME"], where="FUNCNAME = '%s'" % fm, label="TFDIR %s" % fm)
    if not tf["ok"]:
        return COULD_NOT_PROBE, {}, "could not read TFDIR: " + _err_text(tf), []
    if tf.get("n_rows", 0) == 0:
        # This IS a real answer from SAP (the read worked, the row is absent), not a probe failure.
        return CONFIRMED, {"adt_rfc_bridge_present": False}, \
            ("%s does not exist in TFDIR -> there is no ADT-over-RFC bridge on this system; DDIC "
             "table/index work cannot be routed through ADT here." % fm), ["collection absent"]
    uri = par.get("discovery_uri", "/sap/bc/adt/discovery")
    required = [c.lower() for c in (par.get("required_collections") or [])]
    attempts = []
    for method_key, uri_key in _ADT_SIGNATURES:
        rec = rt.call(fm, label="ADT GET %s (%s/%s)" % (uri, method_key, uri_key),
                      **{method_key: "GET", uri_key: uri})
        if rec["ok"]:
            chunks = []
            _flatten_text(rec.pop("result", {}) or {}, chunks)
            body = " ".join(chunks).lower()
            missing = [c for c in required if c not in body]
            measured = {"adt_rfc_bridge_present": True, "discovery_uri": uri,
                        "signature_used": [method_key, uri_key],
                        "required_collections": required, "missing_collections": missing,
                        "body_chars": len(body)}
            if "404" in body or "not found" in body:
                return CONFIRMED, measured, \
                    "the ADT discovery GET reported 404/Not Found for %s" % uri, ["404", "Not Found"]
            if missing:
                return CONFIRMED, measured, \
                    ("the ADT discovery document does not enumerate %s -> NW 7.40 / EhP8 class kernel; "
                     "do not route DDIC work through ADT here." % missing), ["collection absent"]
            return NO_CONSTRAINT, measured, \
                "the ADT discovery document enumerates %s -> NW 7.50+ ADT DDIC endpoints are usable." % required, []
        attempts.append("%s/%s -> %s" % (method_key, uri_key, _err_text(rec, 180)))
        if rec.get("fatal"):
            break
    return COULD_NOT_PROBE, {"adt_rfc_bridge_present": True, "attempts": attempts}, \
        ("the %s bridge EXISTS but none of the known GET parameter signatures was accepted, so the "
         "discovery document could not be read: %s" % (fm, " ;; ".join(attempts)[:600])), []


def probe_fmavc_not_rfc(spec, rt):
    par = spec["params"]
    prefix = par.get("fm_prefix", "FMAVC")
    remote_flag = par.get("rfc_enabled_fmode", "R")
    rec = rt.read_table("TFDIR", ["FUNCNAME", "FMODE"], where="FUNCNAME LIKE '%s%%'" % prefix,
                        rowcount=0, label="TFDIR %s*" % prefix)
    if not rec["ok"]:
        return COULD_NOT_PROBE, {}, "could not read TFDIR: " + _err_text(rec), []
    rows = rec.get("rows") or []
    remote = [r["FUNCNAME"] for r in rows if (r.get("FMODE") or "").upper() == remote_flag]
    spot = {}
    wanted = set(par.get("spot_check") or [])
    for r in rows:
        if r.get("FUNCNAME") in wanted:
            spot[r["FUNCNAME"]] = r.get("FMODE") or ""
    for name in wanted - set(spot):
        spot[name] = "NOT FOUND"
    measured = {"fm_prefix": prefix, "total_fms": len(rows), "rfc_enabled": len(remote),
                "rfc_enabled_sample": sorted(remote)[:10], "spot_check": spot}
    if not rows:
        return COULD_NOT_PROBE, measured, \
            ("no %s* function module exists in TFDIR at all - this is not the expected 'local-only' "
             "symptom; the capability may simply be absent (different component set)." % prefix), []
    if remote:
        return NO_CONSTRAINT, measured, \
            ("%d of %d %s* function modules are FMODE='%s' -> call the standard FM directly; that is "
             "strictly better than any table reconstruction." % (len(remote), len(rows), prefix, remote_flag)), []
    return CONFIRMED, measured, \
        ("%d %s* function modules exist and NONE is FMODE='%s' -> the standard AVC read is not "
         "reachable over plain RFC on this system." % (len(rows), prefix, remote_flag)), ["0 rfc_enabled"]


PROBE_IMPL = {
    "rowskips_rejected": probe_rowskips_rejected,
    "in_clause_rejected": probe_in_clause_rejected,
    "max_where_conditions": probe_max_where_conditions,
    "wide_field_split": probe_wide_field_split,
    "cluster_unreadable": probe_cluster_unreadable,
    "strg_pool_unreadable": probe_strg_pool_unreadable,
    "adt_404_ehp8": probe_adt_404_ehp8,
    "fmavc_not_rfc": probe_fmavc_not_rfc,
}


# ===================================================================== assembly
def load_suite(path):
    with open(path, "r", encoding="utf-8") as fh:
        suite = json.load(fh)
    missing = [p["id"] for p in suite.get("probes", []) if p["id"] not in PROBE_IMPL]
    if missing:
        raise SystemExit("[F0] suite declares probes with no implementation: %s" % missing)
    return suite


def dry_run(suite, system, selected):
    probes = [p for p in suite["probes"] if not selected or p["id"] in selected]
    try:
        _, max_fields = _load_rfc_helpers()
        ladder = _split_ladder(max_fields)
        ladder_note = "%s (derived from rfc_helpers.MAX_FIELDS_PER_CALL=%d)" % (ladder, max_fields)
    except Exception as exc:                                   # noqa: BLE001
        ladder_note = "unavailable at dry-run time (%s: %s)" % (type(exc).__name__, exc)
    print("=" * 100)
    print("F0 INGEST GATE - DRY RUN (no connection is opened)")
    print("  suite      : %s v%s  (%s)" % (suite["suite_id"], suite["suite_version"], DEFAULT_SUITE.name))
    print("  system     : %s" % system)
    print("  contract   : %s" % suite.get("contract_ref"))
    print("  read-only  : %s   (SADT_REST_RFC_ENDPOINT pinned to HTTP GET)"
          % ", ".join(suite.get("read_only_allowlist", [])))
    print("  split ladder: %s" % ladder_note)
    print("  probes     : %d of %d" % (len(probes), len(suite["probes"])))
    print("=" * 100)
    for p in probes:
        print("")
        print("[%d] %s   severity=%s   scope=%s" % (p.get("order", 0), p["id"], p["severity"], p.get("scope")))
        print("    QUESTION : %s" % p["question"])
        print("    HOW      : %s" % p["how"])
        print("    EXPECTED FAILURE : %s" % p["expected_failure"])
        print("    IF CONFIRMED  -> %s" % p["derived_strategy"])
        print("    IF NOT PRESENT-> %s" % p.get("fallback_strategy", "(none declared)"))
        if p.get("escalates_to"):
            print("    ESCALATES: %s" % p["escalates_to"])
        print("    FEEDS    : %s" % json.dumps(p.get("feeds", {})))
    print("")
    print("-" * 100)
    print("Outcome vocabulary: %s = the restriction EXISTS here (apply derived_strategy)" % CONFIRMED)
    print("                    %s = it does NOT exist here (fast path allowed)" % NO_CONSTRAINT)
    print("                    %s = not evaluated; NOTHING is derived from it" % COULD_NOT_PROBE)
    print("Dry run complete. Nothing was sent to SAP.")
    return 0


def build_summary(suite, results):
    by_status = {CONFIRMED: [], NO_CONSTRAINT: [], COULD_NOT_PROBE: []}
    for pid, res in results.items():
        by_status[res["status"]].append(pid)
    confirmed = by_status[CONFIRMED]
    kills = [p for p in confirmed if results[p]["severity"] == "KILL"]
    degrades = [p for p in confirmed if results[p]["severity"] == "DEGRADE"]
    infos = [p for p in confirmed if results[p]["severity"] == "INFO"]
    feeds = {"type_rules": {}, "overrides": {}}
    for pid in confirmed:
        spec_feeds = results[pid].get("feeds") or {}
        for bucket in ("type_rules", "overrides"):
            for target in spec_feeds.get(bucket, []) or []:
                feeds[bucket].setdefault(target, []).append({
                    "probe": pid,
                    "constraint": results[pid]["evidence"]["summary"],
                    "strategy": results[pid]["strategy"],
                })
    complete = not by_status[COULD_NOT_PROBE]
    if not complete:
        verdict = "INCOMPLETE"
    elif kills:
        verdict = "SCOPE_LIMITED"
    elif degrades:
        verdict = "GO_WITH_CONSTRAINTS"
    else:
        verdict = "GO"
    return {
        "total_probes": len(results),
        "constraints_confirmed": len(confirmed),
        "no_constraint": len(by_status[NO_CONSTRAINT]),
        "could_not_probe": len(by_status[COULD_NOT_PROBE]),
        "complete": complete,
        "verdict": verdict,
        "confirmed": confirmed,
        "not_present": by_status[NO_CONSTRAINT],
        "inconclusive": by_status[COULD_NOT_PROBE],
        "kill_confirmed": kills,
        "degrade_confirmed": degrades,
        "info_confirmed": infos,
        "measured": {pid: results[pid]["measured"] for pid in results if results[pid]["measured"]},
        "method_registry_feeds": feeds,
        "note": ("INCOMPLETE profiles must not be used as a tenant baseline: a COULD_NOT_PROBE is not a "
                 "confirmed constraint. Re-run the missing probes before onboarding."),
    }


def run(args):
    suite = load_suite(args.suite)
    selected = set(args.probe or [])
    valid = {p["id"] for p in suite["probes"]}
    unknown = selected - valid
    if unknown:
        print("[F0] unknown probe id(s): %s\n      valid: %s" % (sorted(unknown), sorted(valid)))
        return 2

    if args.dry_run:
        return dry_run(suite, args.system, selected)

    # ---------------------------------------------------------------- connect
    try:
        get_connection, max_fields = _load_rfc_helpers()
    except Exception as exc:                                   # noqa: BLE001
        print("[F0] cannot import rfc_helpers from %s (%s: %s)" % (MCP, type(exc).__name__, exc))
        print("[F0] no connection -> NO profile written. Use --dry-run to inspect the suite.")
        return 3
    ladder = _split_ladder(max_fields)
    print("[F0] connecting to %s (timeout %ds)..." % (args.system, args.connect_timeout))
    try:
        guard = _run_with_timeout(get_connection, args.connect_timeout, args.system, args.env)
    except ProbeTimeout:
        print("[F0] connection to %s did not complete within %ds (VPN/SNC/SSO?)."
              % (args.system, args.connect_timeout))
        print("[F0] NO profile written (a half-written profile is worse than none). exit 3")
        return 3
    except BaseException as exc:                               # noqa: BLE001
        print("[F0] connection to %s FAILED: %s: %s" % (args.system, type(exc).__name__, exc))
        print("[F0] NO profile written (a half-written profile is worse than none). exit 3")
        return 3
    print("[F0] connected.")

    deadline = time.time() + args.budget
    rt = RfcProbeSession(guard, suite.get("read_only_allowlist"), args.call_timeout, deadline)
    results = {}
    probes = [p for p in suite["probes"] if not selected or p["id"] in selected]
    probes.sort(key=lambda p: p.get("order", 0))

    for spec in probes:
        pid = spec["id"]
        print("[F0] probe %-24s ..." % pid, end="", flush=True)
        started = time.time()
        kwargs = {}
        if pid == "wide_field_split":
            kwargs["ladder"] = ladder
        if pid == "strg_pool_unreadable":
            kwargs["max_fields"] = max_fields
        try:
            status, measured, summary, sigs = PROBE_IMPL[pid](spec, rt, **kwargs)
        except BudgetExhausted as exc:
            status, measured, summary, sigs = COULD_NOT_PROBE, {}, str(exc), []
        except BaseException as exc:                           # noqa: BLE001
            status, measured, summary, sigs = COULD_NOT_PROBE, {}, \
                "runner error: %s: %s" % (type(exc).__name__, exc), []
        if status == CONFIRMED:
            strategy, kind = spec["derived_strategy"], "derived_strategy"
        elif status == NO_CONSTRAINT:
            strategy, kind = spec.get("fallback_strategy"), "fallback_strategy"
        else:
            strategy, kind = None, None                        # never derive from INCONCLUSIVE
        results[pid] = {
            "id": pid,
            "order": spec.get("order"),
            "question": spec["question"],
            "readable": READABLE[status],
            "status": status,
            "suite_status": SUITE_STATUS[status],
            "strategy": strategy,
            "strategy_kind": kind,
            "severity": spec["severity"],
            "severity_effective": spec["severity"] if status == CONFIRMED else "NONE",
            "scope": spec.get("scope"),
            "feeds": spec.get("feeds", {}),
            "expected_failure": spec["expected_failure"],
            "measured": measured,
            "evidence": {
                "summary": summary,
                "matched_signatures": sigs,
                "elapsed_s": round(time.time() - started, 2),
                "calls": rt.take_calls(),
            },
        }
        if spec.get("escalates_to") and status == CONFIRMED:
            results[pid]["escalates_to"] = spec["escalates_to"]
        print(" %-21s (%.1fs) %s" % (status, time.time() - started, summary[:120]))
        if rt.connection_lost:
            print("[F0] connection lost/hung - remaining probes will be recorded as %s." % COULD_NOT_PROBE)

    try:
        guard.close()
    except Exception:                                          # noqa: BLE001
        pass

    if all(r["status"] == COULD_NOT_PROBE for r in results.values()) and rt.connection_lost:
        print("[F0] every probe failed for connection reasons -> NO profile written. exit 3")
        return 3

    profile = {
        "profile_version": PROFILE_VERSION,
        "suite_id": suite["suite_id"],
        "suite_version": suite["suite_version"],
        "contract_ref": suite.get("contract_ref"),
        "system": args.system,
        "probed_at": datetime.now(timezone.utc).isoformat(),
        "probed_by": "f0_probe.py",
        "partial_run": bool(selected),
        "probes_selected": sorted(selected) if selected else "ALL",
        "status_vocabulary": {
            CONFIRMED: "the expected failure reproduced -> the restriction EXISTS here",
            NO_CONSTRAINT: "the call worked -> the restriction does NOT exist here",
            COULD_NOT_PROBE: "not evaluated -> derive NOTHING from it",
        },
        "probes": results,
        "summary": build_summary(suite, results),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2, ensure_ascii=False)
    s = profile["summary"]
    print("")
    print("[F0] verdict=%s  confirmed=%d  no_constraint=%d  could_not_probe=%d"
          % (s["verdict"], s["constraints_confirmed"], s["no_constraint"], s["could_not_probe"]))
    if s["kill_confirmed"]:
        print("[F0] KILL-scope constraints confirmed: %s" % s["kill_confirmed"])
    print("[F0] wrote %s" % out)
    if args.fail_on_kill and s["kill_confirmed"]:
        return 4
    return 0 if s["complete"] else 1


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="f0_probe.py",
        description="F0 ingest gate: execute probe_suite_f0.json against one SAP system "
                    "and emit system_profile.json (READ-ONLY).")
    ap.add_argument("--system", required=True,
                    help="SAP system id, e.g. %s (any SID with --allow-unknown-system)"
                         % "|".join(KNOWN_SYSTEMS))
    ap.add_argument("--allow-unknown-system", action="store_true",
                    help="accept a SID outside %s (the normal case when onboarding a new tenant)"
                         % (KNOWN_SYSTEMS,))
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="output profile path (default: %s)" % DEFAULT_OUT)
    ap.add_argument("--suite", default=str(DEFAULT_SUITE), help="probe suite JSON (default: %s)" % DEFAULT_SUITE)
    ap.add_argument("--env", default=None, help="path to the .env with SAP_<SID>_* credentials")
    ap.add_argument("--probe", action="append", default=None,
                    help="run only this probe id (repeatable)")
    ap.add_argument("--dry-run", action="store_true",
                    help="list the probes and their derived strategies; never connects")
    ap.add_argument("--call-timeout", type=float, default=30.0,
                    help="hard timeout per RFC call, seconds (default 30)")
    ap.add_argument("--connect-timeout", type=float, default=25.0,
                    help="hard timeout for the logon, seconds (default 25)")
    ap.add_argument("--budget", type=float, default=240.0,
                    help="global time budget for the whole run, seconds (default 240)")
    ap.add_argument("--fail-on-kill", action="store_true",
                    help="exit 4 when a KILL-severity constraint is confirmed (for CI gating)")
    args = ap.parse_args(argv)

    args.system = args.system.upper()
    if args.system not in KNOWN_SYSTEMS and not args.allow_unknown_system:
        print("[F0] '%s' is not one of %s. Pass --allow-unknown-system to probe a new tenant SID "
              "(and make sure the .env has SAP_%s_* entries)." % (args.system, KNOWN_SYSTEMS, args.system))
        return 2
    if not Path(args.suite).exists():
        print("[F0] suite not found: %s" % args.suite)
        return 2
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
