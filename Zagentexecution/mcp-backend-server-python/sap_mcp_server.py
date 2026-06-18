import os
from dotenv import load_dotenv
from typing import Any
from pyrfc import Connection, RFCError
from mcp.server.fastmcp import FastMCP

# ADT RFC client (replaces sap_adt_client.py HTTP stack)
# Proven on ECC EhP8 D01: SADT_REST_RFC_ENDPOINT exists and works.
# Zero HTTP plumbing — same pyrfc auth as all other tools.
from sap_adt_rfc_client import SapAdtRfcClient, AdtRfcError

# Load SAP credentials from .env
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("SAP_Backend_MCP")

# ── ADT RFC client cache (one persistent connection per system) ───────────────
_adt_clients: dict = {}


def get_adt_client(system_id: str = "D01") -> SapAdtRfcClient:
    """
    Return cached SapAdtRfcClient for the given system.
    Creates+warms up a new client on first call per system_id.
    If the connection is stale, reconnects automatically.
    """
    global _adt_clients

    if system_id in _adt_clients:
        return _adt_clients[system_id]

    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    prefix = f"SAP_{system_id}_"

    def _get(key, default=None):
        return (os.getenv(prefix + key)
                or os.getenv("SAP_" + key)
                or default)

    conn = Connection(
        ashost=_get("ASHOST"),
        sysnr=_get("SYSNR"),
        client=_get("CLIENT"),
        user=_get("USER"),
        passwd=_get("PASSWD") or _get("PASSWORD"),
        lang="EN",
    )
    client = SapAdtRfcClient(conn)
    client._warmup()  # Required on ECC EhP8: initializes ADT HTTP session context
    _adt_clients[system_id] = client
    return client

def get_sap_connection(system_id="D01") -> Connection:
    """Establish and return a connection to the SAP backend.
    Supports system_id (e.g., 'D01', 'P01') to choose configuration.
    """
    # Load .env from the server directory
    dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(dotenv_path)

    try:
        # Prefix for system-specific environment variables
        prefix = f"SAP_{system_id}_"
        
        # Fallback to generic SAP_* if specific prefix not found
        def get_env(key, default=None):
            return os.getenv(prefix + key) or os.getenv("SAP_" + key) or default

        conn_params = {
            "ashost": get_env("ASHOST"),
            "sysnr": get_env("SYSNR"),
            "client": get_env("CLIENT"),
            "user": get_env("USER"),
            "lang": get_env("LANG", "EN")
        }
        
        passwd = get_env("PASSWD") or get_env("PASSWORD")
        if passwd:
            conn_params["passwd"] = passwd

        if get_env("SNC_MODE") == "1":
            conn_params["snc_mode"] = "1"
            conn_params["snc_partnername"] = get_env("SNC_PARTNERNAME")
            conn_params["snc_qop"] = get_env("SNC_QOP", "9")
            
        conn = Connection(**conn_params)
        return conn
    except Exception as e:
        raise RuntimeError(f"Failed to connect to SAP system {system_id}: {str(e)}")

@mcp.tool()
def read_sap_table(table_name: str, max_rows: int = 10, delimiter: str = "|", options: str = "", system_id: str = "D01") -> str:
    """Read data from an SAP transparent table using the native RFC_READ_TABLE BAPI.
    
    Args:
        table_name: The name of the SAP table to read (e.g., 'T001', 'FMFINCODE').
        max_rows: Maximum number of rows to return.
        delimiter: Delimiter for the resulting table data columns.
        options: WHERE clause for filtering (e.g., "ERFDAT >= '20240101'").
        system_id: Target system ID ('D01' or 'P01').
    """
    conn = get_sap_connection(system_id)
    try:
        # Call the standard SAP BAPI to read table data
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE=table_name,
            DELIMITER=delimiter,
            ROWCOUNT=max_rows,
            OPTIONS=[{"TEXT": options}]
        )
        
        # Format the response clearly
        fields = [field["FIELDNAME"] for field in result.get("FIELDS", [])]
        data = result.get("DATA", [])
        
        output = [f"Data for SAP Table {table_name} (System: {system_id})"]
        output.append(f"Columns: {delimiter.join(fields)}")
        output.append("-" * 40)
        
        if not data:
            output.append("No records found.")
        else:
            for row in data:
                output.append(row["WA"])
                
        return "\n".join(output)
        
    except RFCError as e:
        return f"SAP RFC Error: {str(e)}"
    except Exception as e:
        return f"Unexpected Error: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def search_abap_objects(object_name: str, object_type: str = "PROG", max_results: int = 50, system_id: str = "D01") -> str:
    """Search for ABAP objects (Programs, Classes, Tables) based on a name pattern.
    
    Args:
        object_name: The pattern to search for (e.g., 'ZCRP*', 'MARA').
        object_type: Type of object (PROG = Program, CLAS = Class, TABL = Table).
        system_id: Target system ID ('D01' or 'P01').
    """
    conn = get_sap_connection(system_id)
    try:
        # Using TADIR to find objects
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TADIR",
            DELIMITER="|",
            ROWCOUNT=max_results,
            OPTIONS=[{"TEXT": f"OBJ_NAME LIKE '{object_name}' AND OBJECT = '{object_type}'"}]
        )
        
        data = result.get("DATA", [])
        if not data:
            return f"No results found in system {system_id} for {object_type} matching '{object_name}'."
            
        output = [f"Search Results ({system_id}) for {object_type} matching '{object_name}':"]
        for row in data:
            output.append(f"- {row['WA'].split('|')[0].strip()}")
            
        return "\n".join(output)
    except Exception as e:
        return f"Error searching objects: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def get_abap_source(object_name: str, object_type: str = "PROG", system_id: str = "D01") -> str:
    """Read the source code of an ABAP program or class method.
    
    Args:
        object_name: Name of the program or class.
        object_type: 'PROG' for programs/reports, 'CLAS' for classes.
        system_id: Target system ID ('D01' or 'P01').
    """
    conn = get_sap_connection(system_id)
    try:
        if object_type == "PROG":
            # Using SIW_RFC_READ_REPORT as verified replacement for RFC_READ_REPORT
            result = conn.call("SIW_RFC_READ_REPORT", I_NAME=object_name)
            lines = result.get("E_TAB_CODE", [])
            if not lines:
                return f"Source for {object_name} ({system_id}) is empty or not found."
            
            return "\n".join([line.get("LINE", "") for line in lines])
            
        elif object_type == "CLAS":
            # Use ADT RFC client — works natively for classes via SADT_REST_RFC_ENDPOINT
            try:
                adt = get_adt_client(system_id)
                source = adt.read_source("CLASS", object_name)
                lines = source.splitlines()
                return f"Class {object_name} ({system_id}): {len(lines)} lines\n\n{source}"
            except AdtRfcError as e:
                return f"ADT Error {e.status} {e.reason}: {e.body[:300]}"

        return f"Retrieval for {object_type} not yet implemented."
    except Exception as e:
        return f"Error reading source: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def get_class_methods(class_name: str, system_id: str = "D01") -> str:
    """List all methods of an ABAP class.
    
    Args:
        class_name: Name of the ABAP class (e.g., 'CL_SALV_TABLE').
        system_id: Target system ID ('D01' or 'P01').
    """
    conn = get_sap_connection(system_id)
    try:
        # SEOCOMPO contains components of classes/interfaces
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="SEOCOMPO",
            DELIMITER="|",
            OPTIONS=[{"TEXT": f"CLSNAME = '{class_name}' AND CMPTYPE = '1'"}] # CMPTYPE 1 = Method
        )
        
        data = result.get("DATA", [])
        if not data:
            return f"No methods found for class '{class_name}' in system {system_id}."
            
        output = [f"Methods for class {class_name} ({system_id}):"]
        for row in data:
            # Field 2 usually contains the CMPNAME (Component Name)
            fields = row['WA'].split('|')
            if len(fields) > 1:
                output.append(f"- {fields[1].strip()}")
                
        return "\n".join(output)
    except Exception as e:
        return f"Error reading class methods: {str(e)}"
    finally:
        conn.close()

# ══════════════════════════════════════════════════════════════════════════════
#  BRAIN V2 TOOLS — Knowledge Graph queries exposed via MCP
# ══════════════════════════════════════════════════════════════════════════════

import json
import sys
from pathlib import Path

BRAIN_V2_JSON = Path(__file__).parent.parent.parent / "brain_v2" / "output" / "brain_v2_graph.json"


def _load_brain():
    """Load brain v2 graph. Returns None if not built yet."""
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    try:
        from brain_v2.core.graph import BrainGraph
        if BRAIN_V2_JSON.exists():
            return BrainGraph.load_json(str(BRAIN_V2_JSON))
    except ImportError:
        pass
    return None


@mcp.tool()
def brain_impact(node_id: str, max_depth: int = 4) -> str:
    """Analyze what breaks if a given SAP object changes.

    Examples: brain_impact("FIELD:FPAYP.XREF3"), brain_impact("CLASS:YCL_IDFI_CGI_DMEE_FR")
    """
    brain = _load_brain()
    if not brain:
        return "Brain v2 not available. Run: python -m brain_v2.cli build"
    from brain_v2.queries.impact import impact_analysis
    result = impact_analysis(brain, node_id, max_depth)
    return result.get("summary", json.dumps(result, indent=2, default=str))


@mcp.tool()
def brain_depends(node_id: str) -> str:
    """Show complete dependency tree for an object or process.

    Example: brain_depends("PROCESS:Payment_E2E")
    """
    brain = _load_brain()
    if not brain:
        return "Brain v2 not available. Run: python -m brain_v2.cli build"
    from brain_v2.queries.dependency import dependency_tree
    result = dependency_tree(brain, node_id)
    return result.get("summary", json.dumps(result, indent=2, default=str))


@mcp.tool()
def brain_search(query: str) -> str:
    """Search the brain for nodes matching a query string.

    Example: brain_search("DMEE"), brain_search("payment")
    """
    brain = _load_brain()
    if not brain:
        return "Brain v2 not available. Run: python -m brain_v2.cli build"
    query_upper = query.upper()
    matches = []
    for nid, d in brain.nodes.items():
        name = d.get("name", "")
        if query_upper in nid.upper() or query_upper in name.upper():
            matches.append(f"{nid} ({d.get('type','')}, {d.get('domain','')})")
    if not matches:
        return f"No nodes found matching '{query}'"
    result = f"Found {len(matches)} nodes matching '{query}':\n"
    result += "\n".join(matches[:30])
    if len(matches) > 30:
        result += f"\n... +{len(matches)-30} more"
    return result


@mcp.tool()
def brain_stats() -> str:
    """Show brain v2 graph statistics (node/edge counts by type)."""
    brain = _load_brain()
    if not brain:
        return "Brain v2 not available. Run: python -m brain_v2.cli build"
    s = brain.stats()
    lines = [f"Brain v2: {brain.node_count():,} nodes, {brain.edge_count():,} edges", ""]
    lines.append("Top node types:")
    for t, c in list(s["node_types"].items())[:10]:
        lines.append(f"  {t}: {c:,}")
    lines.append("")
    lines.append("Top edge types:")
    for t, c in list(s["edge_types"].items())[:10]:
        lines.append(f"  {t}: {c:,}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  ADT RFC TOOLS — Source read/write/activate via SADT_REST_RFC_ENDPOINT
#  Replaces the old sap_adt_client.py HTTP/CSRF/cookie approach.
#  No CSRF tokens. No cookie jars. No SSL config. Pure RFC.
# ══════════════════════════════════════════════════════════════════════════════

def _adt_guard(system_id: str) -> str:
    """Return error string if system is not D01, else empty string."""
    if system_id.upper() != "D01":
        return (f"ADT tools operate on D01 (development) only. "
                f"For P01 use read_sap_table / search_abap_objects for data and logs.")
    return ""


def _adt_call(fn, system_id: str, *args, **kwargs):
    """
    Call an ADT client method with automatic reconnect on stale connection.
    Returns the method result.
    """
    try:
        adt = get_adt_client(system_id)
        return getattr(adt, fn)(*args, **kwargs)
    except AdtRfcError:
        raise
    except Exception:
        # Stale connection — clear and retry once
        _adt_clients.pop(system_id, None)
        adt = get_adt_client(system_id)
        return getattr(adt, fn)(*args, **kwargs)


@mcp.tool()
def adt_read_source(object_name: str, object_type: str = "CLASS") -> str:
    """Read ABAP source code from D01 development system.

    Supports ALL object types: CLASS, PROG, INTF, INCLUDE, FUGR, TABL, DTEL, DOMA, ENHO.

    Strategy (automatic):
      1. ADT via SADT_REST_RFC_ENDPOINT (indexed objects in proper packages)
      2. RFC fallback via CLIF_GET_SOURCE / SIW_RFC_READ_REPORT (for $TMP local package)

    So $TMP objects are supported — the client tries ADT first, falls back to RFC on 404.

    Args:
        object_name: Object name (e.g. 'ZCL_FI_ACCOUNT_SUBST', 'YCL_FI_ACC_DOCUMENT_ARGA').
        object_type: CLASS, PROG, INTF, INCLUDE, FUGR, TABL, DTEL, DOMA, ENHO.

    For P01 data/logs use read_sap_table instead.
    """
    try:
        source = _adt_call("read_source", "D01", object_type, object_name)
        lines = source.splitlines()
        return (f"Source {object_type}/{object_name} (D01): {len(lines)} lines\n\n"
                + source)
    except AdtRfcError as e:
        return f"ADT {e.status} {e.reason}: {e.body[:500]}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def adt_object_info(object_name: str, object_type: str = "CLASS") -> str:
    """Look up an ABAP object in TADIR (D01).

    Returns package, author, creation date — and whether it's in $TMP.
    Use this to diagnose why adt_read_source returns 404.

    Args:
        object_name: Object name to check (e.g. 'YCL_FI_ACC_DOCUMENT_ARGA').
        object_type: TADIR object type: CLASS, PROG, INTF, FUGR, TABL, DTEL, DOMA, ENHO.
    """
    try:
        info = _adt_call("check_tadir", "D01", object_type, object_name)
        if not info.get("found"):
            return (f"{object_type}/{object_name} — NOT FOUND in TADIR (D01).\n"
                    f"Object may not exist, or check the type.")
        pkg = info['package']
        is_tmp = info['is_tmp']
        lines = [
            f"TADIR info for {object_type}/{object_name} (D01):",
            f"  Package:  {pkg}{'  ← $TMP (local, no transport)' if is_tmp else ''}",
            f"  Author:   {info['author']}",
            f"  Created:  {info['created']}",
            f"  System:   {info['system']}",
            "",
        ]
        if is_tmp:
            lines.append("  ADT read: uses RFC fallback (CLIF_GET_SOURCE) — $TMP not indexed by ADT")
            lines.append("  ADT deploy: NOT possible from $TMP — move to transport package first")
        else:
            lines.append(f"  ADT read: direct via SADT_REST_RFC_ENDPOINT (package {pkg})")
        return "\n".join(lines)
    except AdtRfcError as e:
        return f"ADT {e.status} {e.reason}: {e.body[:500]}"
    except Exception as e:
        return f"Error: {str(e)}"


@mcp.tool()
def adt_search(query: str, object_type: str = "", max_results: int = 20) -> str:
    """Search SAP ADT repository for ABAP objects (D01).

    More powerful than TADIR search: supports wildcards, searches descriptions,
    returns package info. Uses ADT quickSearch endpoint.

    Args:
        query: Search term (e.g. 'ZCL_FI*', 'YCL_IDFI*', 'SAPF100').
        object_type: Filter by ADT type ID (e.g. 'CLAS/OC', 'PROG/P', 'TABL/DT').
                     Leave empty to search all types.
        max_results: Max results to return (default 20).

    For P01 object search use search_abap_objects (queries TADIR via RFC).
    """
    try:
        results = _adt_call("search", "D01", query,
                            obj_type=object_type, max_results=max_results)
        if not results:
            return f"No ADT objects found matching '{query}' in D01"
        lines = [f"ADT search '{query}' (D01): {len(results)} results"]
        lines.append(f"{'Type':<14} {'Name':<40} {'Package':<16} Description")
        lines.append("-" * 90)
        for r in results:
            lines.append(
                f"{r['type']:<14} {r['name']:<40} {r['package']:<16} {r['description']}"
            )
        return "\n".join(lines)
    except AdtRfcError as e:
        return f"ADT {e.status} {e.reason}: {e.body[:500]}"
    except Exception as e:
        return f"Error (connection reset): {str(e)}"


@mcp.tool()
def adt_syntax_check(object_name: str, object_type: str = "CLASS") -> str:
    """Run ADT syntax check on an ABAP object in D01 (read-only — no source modification).

    Returns findings list. Empty list = syntax clean.

    Args:
        object_name: Object name.
        object_type: CLASS, PROG, INTF, INCLUDE, FUGR, TABL.
    """
    try:
        findings = _adt_call("syntax_check", "D01", object_type, object_name)
        if not findings:
            return f"CLEAN — {object_type}/{object_name} (D01): 0 syntax findings"
        errors   = [f for f in findings if f.get("severity") in ("E", "A")]
        warnings = [f for f in findings if f.get("severity") == "W"]
        lines = [
            f"Syntax check {object_type}/{object_name} (D01): "
            f"{len(findings)} findings ({len(errors)} errors, {len(warnings)} warnings)"
        ]
        for finding in findings:
            lines.append(
                f"  [{finding.get('severity','?')}] "
                f"Line {finding.get('line','')}: {finding.get('message','')}"
            )
        return "\n".join(lines)
    except AdtRfcError as e:
        return f"ADT {e.status} {e.reason}: {e.body[:500]}"
    except Exception as e:
        return f"Error (connection reset): {str(e)}"


@mcp.tool()
def adt_deploy(object_name: str, source: str, object_type: str = "CLASS") -> str:
    """Full ABAP deploy cycle on D01: lock → write → syntax check → activate → unlock.

    Uses SADT_REST_RFC_ENDPOINT. No HTTP credentials. No CSRF tokens.
    Unlock always runs (even on error) — no stranded locks.

    Args:
        object_name: Name of the object to update.
        source: New ABAP source code string.
        object_type: CLASS, PROG, INTF, INCLUDE.

    Notes:
    - D01 only (development system). Never P01.
    - Requires S_DEVELOP authorization for the object's package.
      ACTVT=42 (Activate) needed to complete activation step.
    - $TMP objects: readable via RFC fallback but NOT deployable via ADT.
      To deploy a $TMP object: assign it to a transport package first.
    """
    try:
        result = _adt_call("deploy", "D01", object_type, object_name, source)
        lines = [f"Deploy {object_type}/{object_name} (D01):"]
        lines.append(f"  Locked:     {'OK' if result['locked']    else 'FAIL'}")
        lines.append(f"  Written:    {'OK' if result['written']   else 'FAIL'}")
        lines.append(f"  Syntax OK:  {'OK' if result['syntax_ok'] else 'FAIL (errors found)'}")
        lines.append(f"  Activated:  {'OK' if result['activated'] else 'FAIL'}")
        if result['findings']:
            lines.append(f"  Findings ({len(result['findings'])}):")
            for f in result['findings'][:20]:
                lines.append(f"    [{f['severity']}] Line {f['line']}: {f['message']}")
        lines.append(f"\n  Status: {'SUCCESS' if result['activated'] else 'PARTIAL'}")
        return "\n".join(lines)
    except AdtRfcError as e:
        return f"ADT {e.status} {e.reason}: {e.body[:500]}"
    except Exception as e:
        return f"Deploy error: {str(e)}"


if __name__ == "__main__":
    print("Starting SAP Backend MCP Server...")
    # By default, start with standard input/output transport for MCP
    mcp.run(transport="stdio")
