"""
rfc_helpers.py
==============
Shared RFC extraction helpers for all SAP extraction scripts.

Key features:
  - Auto field-splitting for wide tables (RFC_READ_TABLE 512-byte buffer limit)
  - TABLE_WITHOUT_DATA handling (empty periods = normal)
  - DATA_BUFFER_EXCEEDED fallback
  - Auto-reconnect on VPN drops (ConnectionGuard wrapper)
  - Proven defaults: batch_size=5000, throttle=3.0 (from 2M FMIFIIT extraction)

Usage:
    from rfc_helpers import get_connection, rfc_read_paginated
"""

import os
import time
from dotenv import load_dotenv

MAX_FIELDS_PER_CALL = 8   # RFC_READ_TABLE 512-byte line buffer limit
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_WAIT_SEC = 10


def _build_connection_params(system_id="P01", env_path=None):
    """Build pyrfc connection params dict (reusable for reconnect)."""
    if env_path is None:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)
    prefix = f"SAP_{system_id}_"
    def env(k, d=None): return os.getenv(prefix + k) or os.getenv("SAP_" + k) or d
    params = {
        "ashost": env("ASHOST"), "sysnr": env("SYSNR"),
        "client": env("CLIENT"), "user": env("USER"), "lang": env("LANG", "EN"),
    }
    passwd = env("PASSWD") or env("PASSWORD")
    if passwd:
        params["passwd"] = passwd
    if env("SNC_MODE") == "1":
        params["snc_mode"] = "1"
        params["snc_partnername"] = env("SNC_PARTNERNAME")
        params["snc_qop"] = env("SNC_QOP", "9")
    return params


class ConnectionGuard:
    """Wrapper around pyrfc.Connection with auto-reconnect on VPN drops.

    Usage:
        guard = ConnectionGuard("P01")
        guard.connect()
        result = guard.call("RFC_READ_TABLE", ...)   # auto-reconnects if needed
        guard.close()

    Detects connection-closed / timeout errors and reconnects up to
    MAX_RECONNECT_ATTEMPTS times with RECONNECT_WAIT_SEC delay between attempts.
    """

    # Error substrings that indicate a dropped connection (VPN, timeout, etc.)
    # Session #038 addition: RFC_CLOSED + "broken" + WSAE* for mid-RFC drops
    # (connection succeeds, then gets reset by peer during the call).
    RECONNECTABLE_ERRORS = [
        "connection closed",
        "partner not reached",
        "timeout",
        "communication failure",
        "CPIC_",
        "RFC_COMMUNICATION_FAILURE",
        "RFC_INVALID_HANDLE",
        "connection has been closed",
        # Added #038 after h29_skat_update.py crashed at batch 31
        "RFC_CLOSED",
        "connection to partner",
        "broken",
        "WSAECONNRESET",
        "WSAETIMEDOUT",
        "connection reset",
    ]

    def __init__(self, system_id="P01", env_path=None):
        self.system_id = system_id
        self.env_path = env_path
        self._params = _build_connection_params(system_id, env_path)
        self._conn = None
        self.reconnect_count = 0

    def connect(self):
        from pyrfc import Connection
        self._conn = Connection(**self._params)
        return self

    def close(self):
        if self._conn:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    def _is_reconnectable(self, error):
        err_lower = str(error).lower()
        return any(tag.lower() in err_lower for tag in self.RECONNECTABLE_ERRORS)

    def call(self, func_name, **kwargs):
        """Call an RFC function with auto-reconnect on connection drops."""
        from pyrfc import RFCError
        last_err = None
        for attempt in range(MAX_RECONNECT_ATTEMPTS + 1):
            try:
                return self._conn.call(func_name, **kwargs)
            except (RFCError, OSError, Exception) as e:
                if not self._is_reconnectable(e):
                    raise  # Not a connection issue -> propagate immediately
                last_err = e
                if attempt < MAX_RECONNECT_ATTEMPTS:
                    self.reconnect_count += 1
                    wait = RECONNECT_WAIT_SEC * (attempt + 1)
                    print(f"    [RECONNECT] Connection lost ({e}). "
                          f"Attempt {attempt+1}/{MAX_RECONNECT_ATTEMPTS} in {wait}s...")
                    self.close()
                    time.sleep(wait)
                    try:
                        self.connect()
                        print(f"    [RECONNECT] Reconnected to {self.system_id}.")
                    except Exception as ce:
                        print(f"    [RECONNECT] Reconnect failed: {ce}")
        raise last_err  # All retries exhausted


def get_connection(system_id="P01", env_path=None):
    """Connect to SAP via pyrfc with auto-reconnect guard.

    Returns a ConnectionGuard that behaves like pyrfc.Connection
    but automatically reconnects on VPN drops / timeouts.
    """
    guard = ConnectionGuard(system_id, env_path)
    guard.connect()
    return guard


def _rfc_read_single_page(conn, table, rfc_fields, rfc_options, batch_size, offset):
    """Single RFC_READ_TABLE call. Returns (rows_list, headers_list)."""
    from pyrfc import RFCError
    try:
        result = conn.call(
            "RFC_READ_TABLE", QUERY_TABLE=table, DELIMITER="|",
            ROWCOUNT=batch_size, ROWSKIPS=offset,
            OPTIONS=rfc_options, FIELDS=rfc_fields,
        )
    except RFCError as e:
        err_str = str(e)
        if "TABLE_WITHOUT_DATA" in err_str:
            return [], []
        if "DATA_BUFFER_EXCEEDED" in err_str:
            return [], []   # Caller will retry with fewer fields
        raise
    raw  = result.get("DATA", [])
    hdrs = [f["FIELDNAME"] for f in result.get("FIELDS", [])]
    rows = []
    for row in raw:
        parts = row["WA"].split("|")
        rows.append({h: (parts[i].strip() if i < len(parts) else "") for i, h in enumerate(hdrs)})
    return rows, hdrs


def rfc_read_paginated(conn, table, fields, where, batch_size=5000, throttle=3.0):
    """Read SAP table with automatic field-splitting for wide tables.

    If the first page returns TABLE_WITHOUT_DATA or DATA_BUFFER_EXCEEDED with
    the full field list, splits fields into chunks of MAX_FIELDS_PER_CALL and
    merges results by row position within each page.

    Args:
        conn: pyrfc Connection
        table: SAP table name
        fields: list of field names
        where: WHERE clause string OR list of {"TEXT": ...} dicts
        batch_size: rows per RFC call (default 5000, proven with FMIFIIT)
        throttle: seconds between calls (default 3.0, proven safe)
    """
    rfc_fields = [{"FIELDNAME": f} for f in fields]

    # Handle where as string or list
    if isinstance(where, list):
        rfc_options = where
    elif where:
        rfc_options = [{"TEXT": where}]
    else:
        rfc_options = []

    # Try full field list first
    rows, hdrs = _rfc_read_single_page(conn, table, rfc_fields, rfc_options, batch_size, 0)

    if rows:
        # Full field list works -- continue paginating normally
        all_rows = rows
        offset = len(rows)
        while len(rows) >= batch_size:
            if throttle > 0:
                time.sleep(throttle)
            rows, _ = _rfc_read_single_page(conn, table, rfc_fields, rfc_options, batch_size, offset)
            all_rows.extend(rows)
            offset += len(rows)
        return all_rows

    if len(fields) <= MAX_FIELDS_PER_CALL:
        # Few fields and still no data -- genuinely empty
        return []

    # Wide table: split fields into chunks and merge by row position
    # Find the right chunk size -- some tables have very wide fields (e.g. ESSR)
    chunk_size = MAX_FIELDS_PER_CALL
    while chunk_size >= 2:
        test_fields = fields[:chunk_size]
        rfc_test = [{"FIELDNAME": f} for f in test_fields]
        test_rows, _ = _rfc_read_single_page(conn, table, rfc_test, rfc_options, 1, 0)
        if test_rows:
            break
        chunk_size = chunk_size // 2

    if chunk_size < 2:
        # Even 1-2 fields fail -- genuinely empty or auth issue
        return []

    print(f"    [SPLIT] {table}: {len(fields)} fields too wide, splitting into chunks of {chunk_size}")
    all_rows = []
    offset = 0

    while True:
        # Read first chunk to get row count for this page
        chunk1_fields = fields[:chunk_size]
        rfc_chunk1 = [{"FIELDNAME": f} for f in chunk1_fields]
        page_rows, _ = _rfc_read_single_page(conn, table, rfc_chunk1, rfc_options, batch_size, offset)

        if not page_rows:
            break  # No more data

        # Read remaining field chunks at same offset
        remaining = fields[chunk_size:]
        extra_chunks = []
        while remaining:
            chunk = remaining[:chunk_size]
            remaining = remaining[chunk_size:]
            rfc_chunk = [{"FIELDNAME": f} for f in chunk]
            chunk_rows, _ = _rfc_read_single_page(conn, table, rfc_chunk, rfc_options, batch_size, offset)
            extra_chunks.append(chunk_rows)

        # Merge all chunks by row position
        for i, base_row in enumerate(page_rows):
            for chunk_rows in extra_chunks:
                if i < len(chunk_rows):
                    base_row.update(chunk_rows[i])
            all_rows.append(base_row)

        returned = len(page_rows)
        offset += returned
        if returned < batch_size:
            break
        if throttle > 0:
            time.sleep(throttle)

    print(f"    [SPLIT] {table}: {len(all_rows):,} rows extracted via split-field mode")
    return all_rows
