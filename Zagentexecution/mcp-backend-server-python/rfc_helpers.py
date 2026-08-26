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
import re
import time
from dotenv import load_dotenv

MAX_FIELDS_PER_CALL = 8   # RFC_READ_TABLE 512-byte line buffer limit
MAX_RECONNECT_ATTEMPTS = 3
RECONNECT_WAIT_SEC = 10


def _sid_del_bloque_generico():
    """QUE SISTEMA ES el bloque generico del .env — DERIVADO, no escrito a mano.

    El bloque sin prefijo (SAP_ASHOST, SAP_PASSWD...) es un sistema concreto, y saber cual es
    lo unico que permite distinguir un fallback LEGITIMO de uno silencioso. Se deduce de su
    SNC_PARTNERNAME ('p:CN=D01' -> D01). Hardcodear 'D01' aqui seria repetir el defecto un
    nivel mas arriba: si manana el generico apunta a otro sistema, la comprobacion mentiria.
    """
    pn = os.getenv("SAP_SNC_PARTNERNAME") or ""
    m = re.search(r"CN=([A-Z0-9]{3})", pn.upper())
    return m.group(1) if m else None


def sids_declarados(env_path=None):
    """Los SID que tienen bloque PROPIO en el .env, mas el del generico.

    Carga el .env por su cuenta: llamada antes de la primera conexion devolvia una lista
    VACIA, y una lista vacia en un mensaje de error dice 'no hay ninguno declarado' cuando
    hay tres. Un diagnostico que miente cuesta mas que no darlo.
    """
    load_dotenv(env_path or os.path.join(os.path.dirname(__file__), ".env"))
    out = {k[4:-7] for k in os.environ if k.startswith("SAP_") and k.endswith("_ASHOST")
           and len(k) == 15}
    g = _sid_del_bloque_generico()
    return (out | {g}) if g else out


def _build_connection_params(system_id="P01", env_path=None):
    """Build pyrfc connection params dict (reusable for reconnect).

    ⛔ UN SID QUE NO EXISTE YA NO SE CONECTA EN SILENCIO AL GENERICO (arreglado 2026-08-26).

    `env()` cae al bloque generico cuando no hay SAP_<SID>_<CLAVE>. Ese generico ES D01 y
    LLEVA PASSWORD, asi que la conexion no fallaba: tenia EXITO contra el sistema equivocado.
    Medido: `_build_connection_params('VO1')` y `('ZZZ')` devolvian parametros identicos a
    `('D01')`, y RFC_SYSTEM_INFO confirmaba pedido=VO1 -> SID REAL=D01 (host HQ-SAP-D). Un
    typo en `--systems` certificaba «alineado» un sistema que nadie habia leido.

    Ahora: si el SID pedido no tiene bloque propio Y no es el sistema del generico, se NIEGA
    en vez de conectar. Un error ruidoso es infinitamente mas barato que una certificacion
    falsa. Y la comprobacion dura -- que el sistema al otro lado sea el que se pidio -- la
    hace `verificar_sistema()` DESPUES de conectar: esto solo caza el typo, no la
    configuracion mal puesta.
    """
    if env_path is None:
        env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)
    sid = (system_id or "").strip().upper()
    propio = os.getenv(f"SAP_{sid}_ASHOST")
    generico = _sid_del_bloque_generico()
    if not propio and sid != generico:
        raise ValueError(
            f"SID '{system_id}' no tiene bloque SAP_{sid}_* en el .env y el bloque generico es "
            f"'{generico}'. Conectar de todas formas hablaria con {generico} creyendo hablar "
            f"con {sid} -- que es exactamente como un typo certifica alineado un sistema que "
            f"nadie leyo. Declarados: {sorted(sids_declarados())}")
    prefix = f"SAP_{sid}_"
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


ANCHO_OPTIONS = 72          # RFC_DB_OPT-TEXT es CHAR(72). No es un consejo: es la estructura.


def trocear_where(where):
    """Parte un WHERE en lineas de 72 — ARREGLADO 2026-08-26.

    ⛔ AQUI HABIA `[{"TEXT": where}]`: el WHERE entero en UNA linea. RFC_DB_OPT-TEXT es
    CHAR(72), asi que todo lo que pasara de ahi se TRUNCABA. Medido en P01: un
    `VALFROM IN (...)` de 20 valores devolvia OPTION_NOT_VALID, «RFC_READ_TABLE with
    suspicious WHERE condition» -- y troceado a 72 la MISMA clausula funciona. Afectaba a
    TODO llamador con un WHERE largo, no solo al que lo destapo.

    Y el modo de fallo peor no es el error: es cuando el trozo truncado SIGUE siendo sintaxis
    valida. `SETCLASS = '0311' AND SUBCLASS IN ('UNES','ICTP',...` cortado a 72 puede quedar en
    una condicion mas ancha que devuelve filas de mas, sin avisar de nada.

    ⛔ Y SE CORTA POR UN ESPACIO, NUNCA EN MEDIO DE UN TOKEN, con el espacio al PRINCIPIO de la
    linea siguiente: un blanco FINAL no se puede guardar en un CHAR -- se pierde al rellenar --
    pero uno INICIAL si. Cortando a ciegas cada 72, un corte que caiga justo tras un espacio lo
    borra y pega dos tokens: `SETCLASS ='0311'AND`. Esa es la leccion que este proyecto ya
    pago con los separadores de PPC.
    """
    s = str(where).strip()
    if len(s) <= ANCHO_OPTIONS:
        return [{"TEXT": s}]
    lineas, resto = [], s
    while resto:
        if len(resto) <= ANCHO_OPTIONS:
            lineas.append(resto)
            break
        corte = resto.rfind(" ", 0, ANCHO_OPTIONS + 1)
        if corte <= 0:
            # un token mas largo que 72 (un IN gigante sin espacios): se parte donde toque.
            # Sigue siendo mejor que truncar, y se DICE en vez de callarlo.
            corte = ANCHO_OPTIONS
            lineas.append(resto[:corte])
            resto = resto[corte:]
            continue
        lineas.append(resto[:corte])
        resto = resto[corte:]          # empieza POR el espacio: inicial se conserva
    return [{"TEXT": x} for x in lineas]


def verificar_sistema(conn, sid_pedido, estricto=True):
    """LA PRUEBA DURA: preguntarle al sistema QUIEN ES, y compararlo con lo que se pidio.

    El .env dice a donde CREES que vas; RFC_SYSTEM_INFO dice a donde FUISTE. Solo la segunda
    cosa se puede escribir en un informe. Medido 2026-08-26: RFC_SYSTEM_INFO no se llamaba en
    NINGUN quality_check ni ejecutor -- solo en 4 sondas sueltas -- asi que ninguna puerta
    comprobaba con que sistema habia hablado, y todas rotulaban su salida con la cadena que
    tecleo el usuario.

    Devuelve el SID REAL. Con estricto=True (por defecto) LEVANTA si no coincide: un check que
    sigue adelante tras descubrir que hablo con otro sistema produce una certificacion falsa,
    que es peor que no producir nada.
    """
    try:
        info = conn.call("RFC_SYSTEM_INFO")
        real = str((info.get("RFCSI_EXPORT") or {}).get("RFCSYSID", "")).strip().upper()
        host = str((info.get("RFCSI_EXPORT") or {}).get("RFCHOST", "")).strip()
    except Exception as e:
        if estricto:
            raise RuntimeError(
                f"no se pudo verificar con que sistema se hablo ({type(e).__name__}: {e}). "
                f"NO rotules ninguna salida con '{sid_pedido}' sin esta prueba") from e
        return None
    pedido = (sid_pedido or "").strip().upper()
    if pedido and real and real != pedido:
        msg = (f"⛔ SISTEMA EQUIVOCADO: se pidio '{pedido}' y se hablo con '{real}' "
               f"(host {host}). Rotular esta salida como '{pedido}' seria certificar un "
               f"sistema que no se ha leido.")
        if estricto:
            raise RuntimeError(msg)
        print(msg)
    return real


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

    def __init__(self, system_id="P01", env_path=None, estricto=True):
        self.system_id = system_id
        self.env_path = env_path
        self.estricto = estricto      # False solo para SONDAS que quieren ver, no certificar
        self.sid_real = None          # lo que RFC_SYSTEM_INFO dijo: esto es lo que se rotula
        self._params = _build_connection_params(system_id, env_path)
        self._conn = None
        self.reconnect_count = 0

    def connect(self):
        from pyrfc import Connection
        self._conn = Connection(**self._params)
        # SE VERIFICA AQUI, NO EN CADA LLAMADOR. Poner la comprobacion en los scripts significa
        # que la tiene el que se acuerda; ponerla aqui significa que la tienen todos, incluido
        # el que se escriba manana. Tambien corre en la RECONEXION: una reconexion que aterrice
        # en otro sistema es el mismo defecto y ademas no lo veria nadie.
        self.sid_real = verificar_sistema(self._conn, self.system_id, estricto=self.estricto)
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


def get_connection(system_id="P01", env_path=None, estricto=True):
    """Connect to SAP via pyrfc with auto-reconnect guard.

    Returns a ConnectionGuard that behaves like pyrfc.Connection
    but automatically reconnects on VPN drops / timeouts.

    Desde 2026-08-26 COMPRUEBA con RFC_SYSTEM_INFO que el sistema al otro lado es el que se
    pidio, y levanta si no. `guard.sid_real` lleva el SID que contesto: es lo que hay que
    rotular en cualquier salida, NUNCA la cadena que tecleo el usuario.
    """
    guard = ConnectionGuard(system_id, env_path, estricto=estricto)
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


def plan_field_chunks(fields, chunk_size):
    """Split a wide field list into chunks that fit RFC_READ_TABLE's 512-byte line buffer.

    Pure, so it can be gated. The reading itself needs a connection; the PLAN does not, and
    the plan is where the algorithm can be wrong: a chunking that drops a field or reorders
    one silently corrupts every row merged by position afterwards.

    Invariants the golden cases hold it to: every field appears exactly once, order is
    preserved, and no chunk exceeds the size the buffer allows.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    return [list(fields[i:i + chunk_size]) for i in range(0, len(fields), chunk_size)]


def merge_chunks_by_position(base_rows, extra_chunks):
    """Merge field chunks read at the same offset, by ROW POSITION.

    Position is the only join key available: RFC_READ_TABLE returns no row identity. That
    makes the merge correct only while every chunk is read at the same offset with the same
    WHERE — a constraint worth stating, because violating it produces rows that look valid
    and mix two different records.
    """
    out = []
    for i, base in enumerate(base_rows):
        for chunk_rows in extra_chunks:
            if i < len(chunk_rows):
                base.update(chunk_rows[i])
        out.append(base)
    return out


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
        rfc_options = trocear_where(where)
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
        extra_chunks = []
        for chunk in plan_field_chunks(fields[chunk_size:], chunk_size):
            rfc_chunk = [{"FIELDNAME": f} for f in chunk]
            chunk_rows, _ = _rfc_read_single_page(conn, table, rfc_chunk, rfc_options, batch_size, offset)
            extra_chunks.append(chunk_rows)

        all_rows.extend(merge_chunks_by_position(page_rows, extra_chunks))

        returned = len(page_rows)
        offset += returned
        if returned < batch_size:
            break
        if throttle > 0:
            time.sleep(throttle)

    print(f"    [SPLIT] {table}: {len(all_rows):,} rows extracted via split-field mode")
    return all_rows
