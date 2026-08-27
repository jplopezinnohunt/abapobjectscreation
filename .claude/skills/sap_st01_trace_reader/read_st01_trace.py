"""
SAP ST01 Trace Reader — programmatic reader for SAP System Trace data.

Two layers:
  1. DISCOVERY    — list trace files on the SAP app server filesystem (via RFC).
  2. PARSING      — parse the ASCII export of an ST01 trace into structured records.

Usage:
    python read_st01_trace.py --system TS3 --discover
    python read_st01_trace.py --system TS3 --read-file /path/on/server.txt
    python read_st01_trace.py --system TS3 --parse-file ./local_export.txt

Or as a module:
    from read_st01_trace import discover_traces, fetch_file, parse_text
"""

import argparse
import dataclasses
import json
import os
import re
import sys
from typing import Optional

# ============================================================================
# CANONICAL DATA STRUCTURES
# ============================================================================

@dataclasses.dataclass
class TraceLine:
    """Compact one-line view of an ST01 record (list view)."""
    time: str               # 'HH:MM:SS,microseconds'
    type: str               # 'SQL' | 'BUFF' | 'AUTH' | 'KERN' | 'RFC' | 'HTTP' | 'APC' | 'AMC' | 'LOCK'
    duration_us: int        # duration in microseconds
    object: str             # DB table / auth object / FM name / etc.
    program: Optional[str]  # ABAP program (e.g., 'SAPLF051')
    source_line: Optional[int]  # source line number
    extras: dict            # type-specific extras (Buffer state, ReturnCode, etc.)


@dataclasses.dataclass
class TraceRecord:
    """Full detail record (one per event)."""
    # Common header
    date: str               # 'DD.MM.YYYY'
    time: str               # 'HH:MM:SS,microseconds'
    work_process: int
    process_id: int
    client: str
    user: str
    transaction: str
    transaction_id: str     # 16-byte hex GUID
    epp_full_context_id: Optional[str] = None
    epp_connection_id: Optional[str] = None
    epp_call_counter: Optional[int] = None

    # Type
    type: str = ''          # 'SQL' | 'BUFF' | 'AUTH' | 'KERN' | 'RFC' | 'HTTP' | 'APC' | 'AMC' | 'LOCK'

    # Type-specific body (one of the dataclasses below, stored as dict)
    body: dict = dataclasses.field(default_factory=dict)


@dataclasses.dataclass
class SQLBody:
    call: str
    cls: str                # Class
    operation: str          # 0A=SELECT, 06=INSERT, 05=UPDATE, 09=DELETE, etc.
    table: str
    program: str
    source_line: int
    duration_us: int
    rows: int
    return_code: int
    sql_command: str
    db_answer: Optional[str] = None


@dataclasses.dataclass
class BUFFBody:
    call: str
    cls: str
    operation: str
    table: str
    program: str
    source_line: int
    duration_us: int
    buffer_state: str       # I (insert) | R (read hit) | M (miss) | D (delete)
    search_string: Optional[str] = None


@dataclasses.dataclass
class AUTHBody:
    auth_object: str
    fields: dict            # {fieldname: value, ...}
    cls: str
    result: str             # 'OK' | 'FAIL'


@dataclasses.dataclass
class RFCBody:
    function_module: str
    destination: Optional[str]
    direction: str          # 'in' | 'out'
    duration_us: int
    return_code: int


# ============================================================================
# OPERATION CODE TABLE — SQL operations (kernel codes)
# ============================================================================

SQL_OPS = {
    '06': 'INSERT',
    '05': 'UPDATE',
    '09': 'DELETE',
    '0A': 'SELECT',
    '0B': 'SELECT_FOR_UPDATE',
    '0C': 'OPEN_CURSOR',
    '0D': 'FETCH',
    '0E': 'CLOSE_CURSOR',
    '0F': 'PREPARE',
    '03': 'COMMIT',
    '04': 'ROLLBACK',
}


# ============================================================================
# DISCOVERY — find trace files on SAP app server via RFC
# ============================================================================

def get_connection(system_id: str):
    """Open SNC connection to a UNESCO SAP system. Loads .env from mcp-backend-server-python."""
    from pyrfc import Connection
    from dotenv import load_dotenv
    env_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), '..', '..', '..',
        'Zagentexecution', 'mcp-backend-server-python', '.env'
    ))
    load_dotenv(env_path)
    HOSTS = {
        'D01': ('172.16.4.66', 'p:CN=D01'),
        'P01': ('172.16.4.100', 'p:CN=P01'),
        'TS1': ('hq-sap-ts1.hq.int.unesco.org', 'p:CN=TS1'),
        'TS3': ('hq-sap-ts3', 'p:CN=TS3'),
        'V01': ('hq-sap-v01', 'p:CN=V01'),
    }
    if system_id not in HOSTS:
        raise ValueError(f'Unknown system: {system_id}')
    host, partner = HOSTS[system_id]
    return Connection(ashost=host, sysnr='00', client='350', lang='EN',
                      snc_mode='1', snc_partnername=partner, snc_qop='9',
                      config={'rstrip': True})


def discover_traces(system: str, sid_path_root: str = None) -> dict:
    """List trace-related files on the SAP app server.

    Returns:
        {
            'work_traces': [list of dev_w*],
            'rfc_traces':  [list of dev_rfc*],
            'audit_logs':  [list of *.AUD],
            'st01_exports': [list of files matching trace patterns],
        }
    """
    conn = get_connection(system)
    base = sid_path_root or f'/usr/sap/{system}/D00'
    result = {'work_traces': [], 'rfc_traces': [], 'audit_logs': [], 'st01_exports': []}

    for subpath, key, prefix_filter in [
        (f'{base}/work', 'work_traces', 'dev_w'),
        (f'{base}/work', 'rfc_traces', 'dev_rfc'),
        (f'{base}/log', 'audit_logs', None),
    ]:
        try:
            r = conn.call('RZL_READ_DIR_LOCAL', NAME=subpath, NRLINES=2000)
            for f in r.get('FILE_TBL', []):
                if not isinstance(f, dict):
                    continue
                name = f.get('NAME', '')
                size = f.get('SIZE', '0')
                if name in ('.', '..'):
                    continue
                if prefix_filter and not name.lower().startswith(prefix_filter.lower()):
                    continue
                if not prefix_filter and not name.upper().endswith('.AUD'):
                    continue
                result[key].append({
                    'path': f'{subpath}/{name}',
                    'name': name,
                    'size': int(size) if size.isdigit() else 0,
                })
        except Exception as e:
            result[key + '_error'] = str(e)[:200]

    # ST01 exports — search work + data dirs for non-standard named files (saved by user)
    for subpath in [f'{base}/work', f'{base}/data']:
        try:
            r = conn.call('RZL_READ_DIR_LOCAL', NAME=subpath, NRLINES=2000)
            for f in r.get('FILE_TBL', []):
                if not isinstance(f, dict):
                    continue
                name = f.get('NAME', '')
                if name in ('.', '..'):
                    continue
                # ST01 exports usually have user/trace/st01 in the name
                low = name.lower()
                if any(k in low for k in ['st01', 'trace_', '_trace', 'jp_lopez']):
                    result['st01_exports'].append({
                        'path': f'{subpath}/{name}',
                        'name': name,
                        'size': int(f.get('SIZE', '0')) if f.get('SIZE', '0').isdigit() else 0,
                    })
        except Exception:
            pass

    conn.close()
    return result


# ============================================================================
# FETCH — read a file from SAP app server via RFC
# ============================================================================

def fetch_file(system: str, server_path: str, max_lines: int = 50000) -> list:
    """Read a file from the SAP app server. Returns list of lines (strings)."""
    conn = get_connection(system)
    directory, name = os.path.split(server_path.replace('\\', '/'))
    r = conn.call('RZL_READ_FILE_LOCAL',
                  NAME=name,
                  DIRECTORY=directory,
                  FROMLINE=0,
                  NRLINES=max_lines)
    lines = []
    for line in r.get('LINE_TBL', []):
        if isinstance(line, dict):
            lines.append(line.get('LINE', ''))
        else:
            lines.append(str(line))
    conn.close()
    return lines


# ============================================================================
# PARSER — convert ASCII export to TraceLine / TraceRecord lists
# ============================================================================

# Compact line format (ST01 export = pipe-delimited), e.g.:
#   |09:58:00,532|BUFF |       11|INDX            |Prog: SAPFS_SECLOG Row: 396 Buffer: S SearchString ...|
LINE_RE = re.compile(
    r'^\|'
    r'(?P<time>\d{2}:\d{2}:\d{2},\d{3})'
    r'\s*\|'
    r'(?P<type>[A-Z]{2,7})'
    r'\s*\|'
    r'\s*(?P<dur>[\d,]+|---)'
    r'\s*\|'
    r'(?P<obj>[^|]*)'
    r'\|'
    r'(?P<extra>.*?)\|?\s*$'
)

# Block header line, e.g.:
#   |Client: 350  User: JP_LOPEZ  Transaction: FB60  Trans ID: FD194...
HEADER_RE = re.compile(
    r'\|Client:\s*(?P<client>\S+)\s+User:\s*(?P<user>\S+)\s+Transaction:\s*(?P<tcode>\S+)\s+Trans ID:\s*(?P<trans_id>\S+)'
)
HEADER_TIMES_RE = re.compile(
    r'\|Start:\s*(?P<start>\S+\s\S+)\s+Finish:\s*(?P<finish>\S+\s\S+)\s+No\.\s*of Records:\s*(?P<records>\d+)'
)
HEADER_WP_RE = re.compile(
    r'\|Work Process:\s*(?P<wp>\d+)\s+Process ID:\s*(?P<pid>[\d,]+)'
)

# Detail header parsers
HDR_FIELD_RE = re.compile(r'^(\w[\w\s]*?)\s*:\s*(.*)$')


def parse_compact_lines(text: str) -> list:
    """Parse the compact list-view text. Returns list of TraceLine.
    Also tracks the current block context (Trans ID + transaction) and stamps each line with it."""
    lines = []
    current_ctx = {'trans_id': '', 'tcode': '', 'user': '', 'client': '', 'wp': 0, 'pid': 0}

    for raw in text.splitlines():
        line = raw.rstrip()

        # Track block headers
        h = HEADER_RE.search(line)
        if h:
            current_ctx['client'] = h.group('client')
            current_ctx['user'] = h.group('user')
            current_ctx['tcode'] = h.group('tcode')
            current_ctx['trans_id'] = h.group('trans_id')
            continue
        h = HEADER_WP_RE.search(line)
        if h:
            current_ctx['wp'] = int(h.group('wp'))
            current_ctx['pid'] = int(h.group('pid').replace(',', ''))
            continue

        m = LINE_RE.match(line)
        if not m:
            continue
        gd = m.groupdict()
        # Skip column header line (Type column will literally say 'Type')
        if gd['type'].strip() in ('Type', 'TYPE'):
            continue
        extras_text = gd['extra']
        # Pull out Prog: NAME / Row: NUM / ReturnCode N / Buffer: X / SearchString S / Comment: text
        prog_m = re.search(r'Prog:\s*(\S+)', extras_text)
        row_m = re.search(r'Row:\s*([\d,]+)', extras_text)
        rc_m = re.search(r'ReturnCode[:\s]+(\-?\d+)', extras_text)
        buf_m = re.search(r'Buffer:\s*(\S+)', extras_text)
        search_m = re.search(r'SearchString\s+(\S+)', extras_text)
        comment_m = re.search(r'Comment:\s*(.*)', extras_text)
        extras = dict(current_ctx)  # carry context into each line
        if rc_m: extras['return_code'] = int(rc_m.group(1))
        if buf_m: extras['buffer_state'] = buf_m.group(1)
        if search_m: extras['search_string'] = search_m.group(1)
        if comment_m: extras['comment'] = comment_m.group(1).strip()
        # Duration may be '---' for parameter records
        dur_str = gd['dur'].strip()
        dur_us = 0 if dur_str == '---' else int(dur_str.replace(',', ''))
        lines.append(TraceLine(
            time=gd['time'],
            type=gd['type'].strip(),
            duration_us=dur_us,
            object=gd['obj'].strip(),
            program=prog_m.group(1) if prog_m else None,
            source_line=int(row_m.group(1).replace(',', '')) if row_m else None,
            extras=extras,
        ))
    return lines


def parse_detail_record(block: str) -> Optional[TraceRecord]:
    """Parse a single full-detail block (from 'Save As' export with --detail flag).

    Block starts with the record header (Date, Time, ...) and may include
    an extended section with type-specific fields (SQL Command, etc.).
    """
    rec_data = {'body': {}}
    in_body = False
    body_field = None
    body_lines_buffer = []

    for raw in block.splitlines():
        line = raw.rstrip()
        if not line.strip():
            if body_field and body_lines_buffer:
                rec_data['body'][body_field] = '\n'.join(body_lines_buffer).strip()
                body_field = None
                body_lines_buffer = []
            continue
        # Continuation of multi-line field (e.g., SQL Command)
        if body_field and (line.startswith(' ') or line.startswith('>')):
            body_lines_buffer.append(line.lstrip('> '))
            continue
        # Try field:value
        m = HDR_FIELD_RE.match(line)
        if not m:
            continue
        key = m.group(1).strip().lower().replace(' ', '_')
        val = m.group(2).strip()
        if body_field and body_lines_buffer:
            rec_data['body'][body_field] = '\n'.join(body_lines_buffer).strip()
            body_field = None
            body_lines_buffer = []
        # Header fields
        if key == 'date': rec_data['date'] = val
        elif key == 'time': rec_data['time'] = val
        elif key == 'work_process': rec_data['work_process'] = int(val) if val.isdigit() else 0
        elif key == 'process_id': rec_data['process_id'] = int(val.replace(',', '')) if val.replace(',', '').isdigit() else 0
        elif key == 'client': rec_data['client'] = val
        elif key == 'user': rec_data['user'] = val
        elif key == 'transaction': rec_data['transaction'] = val
        elif key == 'transaction_id': rec_data['transaction_id'] = val
        elif key == 'epp_full_context_id': rec_data['epp_full_context_id'] = val
        elif key == 'epp_connection_id': rec_data['epp_connection_id'] = val
        elif key == 'epp_call_counter': rec_data['epp_call_counter'] = int(val) if val.isdigit() else 0
        elif key in ('sql_command', 'answer_from_db'):
            body_field = key
            body_lines_buffer = [val] if val else []
        else:
            rec_data['body'][key] = val

    # Flush trailing body field
    if body_field and body_lines_buffer:
        rec_data['body'][body_field] = '\n'.join(body_lines_buffer).strip()

    if 'date' not in rec_data:
        return None  # not a valid record block

    # Infer type from body fields
    body = rec_data['body']
    if 'sql_command' in body or body.get('class') == '03' and body.get('operation') in SQL_OPS:
        rec_data['type'] = 'SQL'
        body['operation_name'] = SQL_OPS.get(body.get('operation', ''), body.get('operation', ''))
    elif 'buffer_state' in body or 'search_string' in body:
        rec_data['type'] = 'BUFF'
    elif 'auth_object' in body or 'object' in body:
        rec_data['type'] = 'AUTH'
    elif 'function_module' in body or 'destination' in body:
        rec_data['type'] = 'RFC'
    else:
        rec_data['type'] = 'KERN'

    return TraceRecord(**{k: v for k, v in rec_data.items() if k in TraceRecord.__dataclass_fields__})


def split_detail_blocks(text: str) -> list:
    """Detail records in ST01 export are typically separated by blank lines or section markers."""
    blocks = []
    current = []
    for line in text.splitlines():
        # New record begins when we see "Date" at column 1 of a section
        if line.startswith('Date') and current:
            blocks.append('\n'.join(current))
            current = [line]
        elif 'Trace Record' in line and current:
            blocks.append('\n'.join(current))
            current = []
        else:
            current.append(line)
    if current:
        blocks.append('\n'.join(current))
    return blocks


def parse_text(text: str) -> dict:
    """Parse an ST01 export. Returns {'compact_lines': [...], 'detail_records': [...]}."""
    return {
        'compact_lines': [dataclasses.asdict(l) for l in parse_compact_lines(text)],
        'detail_records': [
            dataclasses.asdict(r) for r in
            (parse_detail_record(b) for b in split_detail_blocks(text))
            if r
        ],
    }


# ============================================================================
# TRIAGE — filter the noise out of a full trace
# ============================================================================

# Pre-built filter profiles by ANALYSIS TYPE — matches the ST01 native categories
# (Authorization check, Kernel Functions, General Kernel, DB access, Table buffer,
#  RFC calls, HTTP Calls, APC Calls, AMC Calls, Lock operations)
#
# Each profile selects records of one or more trace TYPES. Optional secondary
# filters (tables, programs, auth_objects) can narrow further.

TRIAGE_PROFILES = {
    # ─── ST01 native categories (1-to-1) ──────────────────────────────────
    'auth_all': {
        'types': {'AUTH'},
        'description': 'All authorization checks (granted + denied)',
    },
    'auth_errors': {
        'types': {'AUTH'},
        'errors_only': True,
        'description': 'Only failed authorization checks',
    },
    'kernel_functions': {
        'types': {'KERN'},
        'description': 'Kernel Function calls (system-level)',
    },
    'general_kernel': {
        'types': {'KERN'},
        'description': 'General Kernel events (broad)',
    },
    'db_sql': {
        'types': {'SQL'},
        'description': 'DB access — all SQL statements (SELECT/INSERT/UPDATE/DELETE)',
    },
    'buffer': {
        'types': {'BUFF'},
        'description': 'Table buffer operations (read hit/miss/insert/delete)',
    },
    'rfc': {
        'types': {'RFC'},
        'description': 'RFC calls (inbound + outbound)',
    },
    'http': {
        'types': {'HTTP', 'HTTPC'},
        'description': 'HTTP calls',
    },
    'apc': {
        'types': {'APC'},
        'description': 'ABAP Channel APC calls',
    },
    'amc': {
        'types': {'AMC'},
        'description': 'ABAP Channel AMC calls',
    },
    'lock': {
        'types': {'LOCK', 'ENQ'},
        'description': 'Lock / enqueue operations',
    },

    # ─── Cross-cutting analysis profiles (combine types + filters) ─────────
    'errors_only': {
        'types': set(),  # any type
        'errors_only': True,
        'description': 'All failures across types: AUTH FAIL + SQL with ReturnCode != 0',
    },
    'slow_ops': {
        'types': set(),
        'min_duration_us': 10000,
        'description': 'Operations slower than 10ms',
    },

    # ─── Domain overlay (optional secondary narrowing on top of any type) ──
    'br_tables': {
        'types': {'SQL', 'BUFF'},
        'tables': {
            'FMIOI', 'FMIFIIT', 'FMIFIHD', 'FMAVCT', 'FMAVCTL',
            'KBLP', 'KBLPS', 'KBLE', 'KBLEW', 'KBLK',
            'BUAVCLDGR', 'BUAVCTPRO', 'BUAVCTOLASS', 'BUAVCSRC', 'BUAVCACTGRP',
            'FMAVCLDGRACT', 'FMAVCLDGRATT', 'FMCECVGRP', 'FMCEACT',
            'TCURR', 'TCURF', 'TVARVC', 'FMFINCODE', 'FMFUNDTYPE',
            'YTFM_BR_FMIFIIT', 'YTFM_BR_FMIOI', 'YTFM_BR_FM_POS',
        },
        'description': 'SQL/buffer ops touching BR-relevant FM/AVC tables',
    },
    'br_enhancements': {
        'types': set(),  # any
        'programs': {
            'ZFIX_EXCHANGERATE_AVC', 'ZFIX_EXCHANGERATE_CHECK_CONS',
            'ZFIX_EXCHANGERATE_FI', 'ZFIX_EXCHANGERATE_FUNDBLOCK',
            'ZFIX_EXCHANGERATE_KBLEW', 'ZFIX_EXCHANGERATE_NEW_ITEM',
            'ZFIX_EXCHANGERATE_PAYCOMMIT', 'ZFIX_EXCHANGERATE_PBC_POS_UPD',
            'YCL_FM_BR_EXCHANGE_RATE_BL',
        },
        'description': 'Records inside the 8 BR enhancements + class',
    },
}


def triage(parsed: dict, profile: str = 'br_investigation') -> dict:
    """Reduce a full trace to the records that matter for a given investigation.

    Args:
        parsed: output of parse_text() — has 'compact_lines' and 'detail_records'
        profile: one of TRIAGE_PROFILES keys

    Returns:
        {'compact_lines': [...filtered...], 'detail_records': [...filtered...],
         'stats': {input_count, output_count, by_type, by_table, by_program}}
    """
    if profile not in TRIAGE_PROFILES:
        raise ValueError(f'Unknown profile: {profile}. Choose from {list(TRIAGE_PROFILES)}')
    p = TRIAGE_PROFILES[profile]
    types = p.get('types') or set()
    tables = {t.upper() for t in (p.get('tables') or set())}
    programs = p.get('programs') or set()
    auth_objs = p.get('auth_objects') or set()
    min_dur = p.get('min_duration_us', 0)
    errors_only = p.get('errors_only', False)

    def keep_line(l: dict) -> bool:
        # Primary filter: trace TYPE (matches ST01 native categories)
        if types and l['type'] not in types:
            return False
        if l['duration_us'] < min_dur:
            return False
        if errors_only:
            rc = l.get('extras', {}).get('return_code')
            if rc is None or rc == 0:
                # Also allow AUTH records that look like FAIL via extras
                ex = l.get('extras', {})
                if not (ex.get('result', '').upper() == 'FAIL'):
                    return False
        # Secondary filters: tables / programs / auth_objects (narrow further)
        if tables or programs or auth_objs:
            obj_up = (l.get('object') or '').upper()
            prog = l.get('program') or ''
            if tables and obj_up in tables: return True
            if programs and (prog in programs or any(p in prog for p in programs)): return True
            if l['type'] == 'AUTH' and auth_objs and obj_up in auth_objs: return True
            return False
        return True

    def keep_record(r: dict) -> bool:
        if types and r.get('type') not in types:
            return False
        body = r.get('body', {})
        if errors_only:
            rc = body.get('return_code')
            result = body.get('result', '').upper()
            if (rc is None or str(rc).strip() == '0') and result != 'FAIL':
                return False
        if tables or programs:
            tab = (body.get('table') or '').upper()
            prog = body.get('program') or ''
            if tables and tab in tables: return True
            if programs and (prog in programs or any(p in prog for p in programs)): return True
            return False
        return True

    f_lines = [l for l in parsed.get('compact_lines', []) if keep_line(l)]
    f_records = [r for r in parsed.get('detail_records', []) if keep_record(r)]

    # Stats
    by_type, by_table, by_program = {}, {}, {}
    for l in f_lines:
        by_type[l['type']] = by_type.get(l['type'], 0) + 1
        if l.get('object'):
            by_table[l['object']] = by_table.get(l['object'], 0) + 1
        if l.get('program'):
            by_program[l['program']] = by_program.get(l['program'], 0) + 1

    return {
        'profile': profile,
        'compact_lines': f_lines,
        'detail_records': f_records,
        'stats': {
            'input_compact_count': len(parsed.get('compact_lines', [])),
            'input_detail_count': len(parsed.get('detail_records', [])),
            'output_compact_count': len(f_lines),
            'output_detail_count': len(f_records),
            'by_type': dict(sorted(by_type.items(), key=lambda x: -x[1])),
            'by_table': dict(sorted(by_table.items(), key=lambda x: -x[1])[:30]),
            'by_program': dict(sorted(by_program.items(), key=lambda x: -x[1])[:30]),
        },
    }


def group_by_transaction_phase(records: list) -> dict:
    """Cluster trace records by the BR process phase they belong to.
    Useful for understanding 'what happened in CHECK_CONS vs AVC vs FI'.
    """
    PHASE_MARKERS = {
        'PHASE_2_CHECK_CONS': ['CL_FM_EF_POSITION', 'CHECK_CONSUMPTION', 'ZFIX_EXCHANGERATE_CHECK_CONS'],
        'PHASE_3_NEW_ITEM':   ['VFH_FUNDS_CHECK_OI', 'CREATE_NEW_ITEM_FA', 'ZFIX_EXCHANGERATE_NEW_ITEM'],
        'PHASE_4_AVC':        ['FM_FUNDS_CHECK_OI', 'SAPLBUS_AVC', 'ZFIX_EXCHANGERATE_AVC'],
        'PHASE_5_PAYCOMMIT':  ['SAPLMR1M', 'GET_FA_COMMIT_DATA', 'ZFIX_EXCHANGERATE_PAYCOMMIT'],
        'PHASE_6_KBLEW':      ['CREATE_KBLEW_ENTRIES', 'ZFIX_EXCHANGERATE_KBLEW'],
        'PHASE_7_FI':         ['ZFIX_EXCHANGERATE_FI', 'YTFM_BR_FMIFIIT', 'Y_FM_UPDATE_BR_FMIFIIT'],
        'PHASE_9_REINIT':     ['fmavc_reinit_on_event', 'RFFMAVC_REINIT'],
    }
    phases = {p: [] for p in PHASE_MARKERS}
    phases['UNCLASSIFIED'] = []
    for r in records:
        body = r.get('body', {})
        prog = body.get('program') or ''
        cmd = body.get('sql_command', '')
        matched = False
        for phase, markers in PHASE_MARKERS.items():
            if any(m in prog or m in cmd for m in markers):
                phases[phase].append(r)
                matched = True
                break
        if not matched:
            phases['UNCLASSIFIED'].append(r)
    return {p: rs for p, rs in phases.items() if rs}


# ============================================================================
# CLI
# ============================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--system', help='SAP system ID (D01, P01, TS1, TS3)')
    ap.add_argument('--discover', action='store_true', help='List trace files on the server')
    ap.add_argument('--read-file', help='Read a specific file from the server (absolute path)')
    ap.add_argument('--parse-file', help='Parse a local file (already downloaded)')
    ap.add_argument('--triage', help=f'Triage profile: {list(TRIAGE_PROFILES.keys())}')
    ap.add_argument('--phases', action='store_true', help='Group records by BR process phase')
    ap.add_argument('--output', help='Output JSON path')
    args = ap.parse_args()

    out = None

    if args.discover:
        if not args.system:
            ap.error('--discover requires --system')
        out = discover_traces(args.system)
    elif args.read_file:
        if not args.system:
            ap.error('--read-file requires --system')
        lines = fetch_file(args.system, args.read_file)
        text = '\n'.join(lines)
        out = parse_text(text)
        out['_raw_size_lines'] = len(lines)
    elif args.parse_file:
        with open(args.parse_file, 'r', encoding='utf-8', errors='replace') as f:
            text = f.read()
        out = parse_text(text)
    else:
        ap.print_help()
        sys.exit(1)

    # Apply triage filter if requested
    if args.triage and out and 'compact_lines' in out:
        out = triage(out, profile=args.triage)
        print(f'\nTriage profile "{args.triage}" applied:')
        print(f'  Compact lines: {out["stats"]["input_compact_count"]} → {out["stats"]["output_compact_count"]}')
        print(f'  Detail records: {out["stats"]["input_detail_count"]} → {out["stats"]["output_detail_count"]}')

    # Group by BR phase
    if args.phases and out and 'detail_records' in out:
        out['phase_groups'] = {p: len(rs) for p, rs in
                               group_by_transaction_phase(out['detail_records']).items()}
        print(f'\nPhase distribution:')
        for p, n in out['phase_groups'].items():
            print(f'  {p}: {n} records')

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(out, f, indent=2, default=str)
        print(f'\nSaved: {args.output}')
    else:
        print(json.dumps(out, indent=2, default=str)[:5000])


if __name__ == '__main__':
    main()
