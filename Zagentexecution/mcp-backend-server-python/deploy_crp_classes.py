"""
deploy_crp_classes.py - Deploy ZCL_CRP_PROCESS_REQ and DPC_EXT methods to SAP D01
Strategy:
  - Step 1: Create ZCL_CRP_PROCESS_REQ class structure + method definitions via SEO_CLASS_CREATE
  - Step 2: Write method implementation to CM includes via RPY_PROGRAM_WRITE
  - Step 3: Write DPC_EXT method includes (already exist, just add logic)
  - Transport: Use existing ZCRP package transport request

Usage: python deploy_crp_classes.py
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

# ─── Load connection ─────────────────────────────────────────────────
load_dotenv()
def get_conn():
    params = {
        "ashost": os.getenv("SAP_ASHOST"),
        "sysnr":  os.getenv("SAP_SYSNR"),
        "client": os.getenv("SAP_CLIENT"),
        "user":   os.getenv("SAP_USER"),
        "lang":   os.getenv("SAP_LANG", "EN"),
    }
    pw = os.getenv("SAP_PASSWD")
    if pw: params["passwd"] = pw
    if os.getenv("SAP_SNC_MODE") == "1":
        params["snc_mode"]        = "1"
        params["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        params["snc_qop"]         = os.getenv("SAP_SNC_QOP", "9")
    return Connection(**params)

# ─── Helper: write source lines to an ABAP include via RPY_PROGRAM_WRITE ──
def write_include(conn, include_name, source_lines, trkorr=""):
    """
    Writes source_lines to an ABAP include program using RPY_PROGRAM_WRITE.
    source_lines: list of strings (one per line, no trailing newline needed)
    """
    print(f"  Writing {len(source_lines)} lines to {include_name} ...")
    abap_source = [{"LINE": line[:255]} for line in source_lines]

    try:
        result = conn.call(
            "RPY_PROGRAM_WRITE",
            PROG_NAME=include_name,
            SOURCE_EXTENDED=abap_source,
            WITH_CORRECTION_FLAG=trkorr,  # "" asks SAP to auto-find task
            SAVE="X",
        )
        print(f"  ✅ Saved {include_name}")
        return True
    except RFCError as e:
        print(f"  ❌ RFC error on {include_name}: {e}")
        return False

# ─── Helper: read source for an include ──────────────────────────────
def read_include(conn, include_name):
    try:
        res = conn.call("SIW_RFC_READ_REPORT", I_NAME=include_name)
        return [r.get("LINE", "") for r in res.get("E_TAB_CODE", [])]
    except Exception as e:
        print(f"  Could not read {include_name}: {e}")
        return []

# ─── Step 1: Find existing ZCRP transport request ────────────────────
def find_transport_request(conn):
    """Find open transport request for ZCRP package"""
    try:
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TADIR",
            DELIMITER="|",
            OPTIONS=[{"TEXT": "PGMID = 'R3TR' AND DEVCLASS = 'ZCRP' AND OBJECT = 'CLAS'"}],
            FIELDS=[{"FIELDNAME": "KORRNUM"}],
            ROWCOUNT=5,
        )
        for row in result.get("DATA", []):
            trkorr = row["WA"].strip().strip("|")
            if trkorr and trkorr != "000000000000":
                print(f"  Found transport from TADIR: {trkorr}")
                return trkorr
    except Exception:
        pass
    print("  ℹ️  No transport found via TADIR — SAP will prompt or use workbench default")
    return ""

# ─── Step 2: Create ZCL_CRP_PROCESS_REQ ──────────────────────────────
def create_process_req_class(conn, trkorr):
    """
    Creates the ZCL_CRP_PROCESS_REQ class header using SEO_CLASS_CREATE.
    Defines the methods and types. Implementation goes into CM includes later.
    """
    print("\n[STEP 1] Creating class ZCL_CRP_PROCESS_REQ ...")

    # Build class description
    class_desc = [
        {"CMPNAME": "ZCL_CRP_PROCESS_REQ", "DESCRIPT": "CRP Process Request — Business Logic Delegate for Z_CRP_SRV", "LANGU": "E"}
    ]

    # Method definitions
    methods = [
        {"CMPNAME": "RESOLVE_STAFF_FROM_USER", "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Resolve SY-UNAME to PERNR and HR data", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "DETERMINE_GL_ACCOUNT",    "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Determine GL account from grade category", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "GENERATE_CERTIFICATE_ID", "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Generate CRP certificate ID from number range", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "CHECK_BUDGET_AVAILABILITY","CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Check FM budget availability via BAPI", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "CHECK_DUPLICATE_RECOVERY", "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Check for prior cost recovery in FI", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "VALIDATE_HEADER",          "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Validate certificate header data", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "SUBMIT_FOR_APPROVAL",      "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Submit certificate for approval workflow", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "SIMULATE_JV",              "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Simulate JV posting — no commit", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "POST_JV",                  "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Post JV document via BAPI_ACC_DOCUMENT_POST", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "POST_ALLOTMENT",           "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Post allotment to Coremanager (stub)", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "WRITE_APPROVAL_HISTORY",   "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Write row to ZCRP_APRVL_HIST", "LANGU": "E", "EXPOSURE": "0"},
        {"CMPNAME": "GET_GRADE_CATEGORY",       "CMPTYPE": "0", "MTDTYPE": " ", "DESCRIPT": "Read grade category from ZCRP_GRADE_CFG", "LANGU": "E", "EXPOSURE": "2"},
    ]

    try:
        conn.call(
            "SEO_CLASS_CREATE",
            DEVCLASS="ZCRP",
            CLASS_NAME="ZCL_CRP_PROCESS_REQ",
            DESCRIPTION="CRP Process Request Business Logic",
            LANGU="E",
            CLSFINAL="X",    # FINAL class
            CLSACCESS="0",   # PUBLIC
            CORRNR=trkorr,
        )
        print("  ✅ Class header created")
    except RFCError as e:
        err = str(e)
        if "already exists" in err.lower() or "exists" in err.lower():
            print("  ℹ️  Class already exists — skipping create, will update methods")
        else:
            print(f"  ❌ Failed to create class: {e}")
            return False

    return True


# ─── Step 3: Write DPC_EXT method implementations ────────────────────
def write_dpc_ext_methods(conn, trkorr):
    """Write code to the DPC_EXT method includes that currently only have stubs"""
    print("\n[STEP 2] Writing DPC_EXT method implementations ...")

    # First find the CM includes for DPC_EXT
    try:
        result = conn.call(
            "RFC_READ_TABLE",
            QUERY_TABLE="TRDIR",
            DELIMITER="|",
            OPTIONS=[{"TEXT": "NAME LIKE 'ZCL_Z_CRP_SRV_DPC_EXT%CM%'"}],
            FIELDS=[{"FIELDNAME": "NAME"}],
            ROWCOUNT=50,
        )
        includes = [row["WA"].strip().strip("|") for row in result.get("DATA", [])]
        print(f"  Found {len(includes)} DPC_EXT method includes: {includes}")
    except RFCError as e:
        print(f"  ❌ Could not list DPC_EXT includes: {e}")
        return

    # Read current content + inspect which include handles which method
    for inc in sorted(includes):
        lines = read_include(conn, inc)
        if lines:
            first_method_line = next((l for l in lines if "method " in l.lower()), "")
            print(f"  Include {inc[-10:]} → {first_method_line.strip()[:80]}")


# ─── Step 4: Activate class ──────────────────────────────────────────
def activate_class(conn, class_name):
    print(f"\n[STEP 3] Activating {class_name} ...")
    try:
        conn.call(
            "SEO_CLASS_ACTIVATE",
            CLASS_NAME=class_name,
        )
        print(f"  ✅ {class_name} activated")
    except RFCError as e:
        print(f"  ⚠️  Activation: {e}")


# ─── MAIN ────────────────────────────────────────────────────────────
def main():
    conn = None
    try:
        print("=" * 60)
        print("CRP ABAP CLASS DEPLOYMENT — SAP D01/350")
        print("=" * 60)

        conn = get_conn()
        print(f"\n✅ Connected to SAP {os.getenv('SAP_ASHOST')} / Client {os.getenv('SAP_CLIENT')}")

        # Find transport order
        trkorr = find_transport_request(conn)

        # Create ZCL_CRP_PROCESS_REQ
        create_process_req_class(conn, trkorr)

        # List what DPC_EXT includes look like currently
        write_dpc_ext_methods(conn, trkorr)

        print("\n" + "=" * 60)
        print("DISCOVERY COMPLETE — Next: write method source to includes")
        print("=" * 60)

    except RFCError as e:
        print(f"\n❌ RFC Error: {e}")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
