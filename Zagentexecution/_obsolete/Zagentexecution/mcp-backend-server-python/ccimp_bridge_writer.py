"""
ccimp_bridge_writer.py

Clean ABAP bridge writer for CCIMP includes.
Root cause fix: single quotes in ABAP source lines break the ABAP bridge
because the generated `lv_line = 'code...'` statement gets truncated at 72 chars.

Solution:
  1. Replace ' with a placeholder char (chr(127)) in source lines
  2. Generate safe ABAP bridge code without any single quotes in the data
  3. REPLACE ALL OCCURRENCES in ABAP after building each line
  4. Use chunking for lines > 59 chars (72 - len("lv_line = ''.") overhead)
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection
from dotenv import load_dotenv
load_dotenv()

TRANSPORT = "D01K9B0EWT"
PH = chr(127)  # placeholder for single quote - DEL character, won't appear in ABAP


def get_conn():
    return Connection(
        ashost="172.16.4.66", sysnr="00", client="350",
        user=os.getenv("SAP_USER"), lang="EN",
        snc_mode="1", snc_partnername=os.getenv("SAP_SNC_PARTNERNAME"), snc_qop="9"
    )


def build_abap_writer(include_name: str, source_lines: list[str]) -> list[str]:
    """
    Build ABAP program lines (<=72 chars each).
    Handles single quotes via chr(127) placeholder + REPLACE ALL OCCURRENCES.
    """
    SQ   = "lv_sq"
    LINE = "lv_line"
    PH_CHAR = PH

    abap = [
        "REPORT z_write_ccimp.",
        "DATA: lv_sq   TYPE c.",
        "DATA: lv_ph   TYPE c.",
        "DATA: lv_prog TYPE c LENGTH 40.",
        "DATA: lv_line TYPE abaptxt255.",
        "DATA: lt_code TYPE TABLE OF abaptxt255.",
        "DATA: lv_x    TYPE x VALUE '7F'.",
        "",
        "lv_sq = ''''.",
        "lv_ph = lv_x.",
        "",
    ]

    def safe_assign(content: str) -> list[str]:
        stmts = []
        has_sq = "'" in content
        safe = content.replace("'", PH_CHAR)
        MAX = 58

        if len(safe) == 0:
            stmts.append(f"{LINE} = ''.")
        elif len(safe) <= MAX:
            stmts.append(f"{LINE} = '{safe}'.")
        else:
            chunk = safe[:MAX]
            stmts.append(f"{LINE} = '{chunk}'.")
            pos = MAX
            while pos < len(safe):
                chunk = safe[pos:pos+MAX]
                stmt = f"CONCATENATE {LINE} '{chunk}' INTO {LINE}."
                if len(stmt) > 72:
                    chunk = safe[pos:pos+20]
                    stmt = f"CONCATENATE {LINE} '{chunk}' INTO {LINE}."
                    pos += 20
                else:
                    pos += MAX
                stmts.append(stmt)

        if has_sq:
            stmts.append(
                f"REPLACE ALL OCCURRENCES OF lv_ph IN {LINE} WITH {SQ}."
            )
        stmts.append(f"APPEND {LINE} TO lt_code.")
        return stmts

    abap.append("* === Build source code table ===")
    for line in source_lines:
        for stmt in safe_assign(line):
            abap.append(stmt)
    abap.append("")

    # Use variable for program name - 38-char include name overflows 72-char line limit
    abap += [
        "* === Write to include ===",
        f"lv_prog = '{include_name[:40]}'.",
        f"CALL FUNCTION 'RPY_PROGRAM_UPDATE'",
        f"  EXPORTING",
        f"    program_name      = lv_prog",
        f"    transport_number  = '{TRANSPORT}'",
        f"    save_inactive     = 'X'",
        f"    temporary         = ' '",
        f"  TABLES",
        f"    source_extended   = lt_code",
        f"  EXCEPTIONS",
        f"    not_found         = 1",
        f"    cancelled         = 2",
        f"    OTHERS            = 3.",
        f"WRITE: / 'Write rc:', sy-subrc.",
    ]
    return abap


def run_abap_bridge(abap_lines: list[str], label: str = ""):
    conn = get_conn()
    if label:
        print(f"\n[{label}]")
    src = [{"LINE": l[:72]} for l in abap_lines]
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
        for w in res.get("WRITES", []):
            val = w.get("ZEILE") or list(w.values())[0]
            print(f"  SAP: {val}")
        if res.get("ERRORMESSAGE"):
            print(f"  ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
    finally:
        conn.close()


def verify_include(include_name: str):
    """Verify include via variable-based program name (avoids 72-char overflow)."""
    short = include_name[:30]
    abap = [
        "REPORT z_verify.",
        "DATA: lt_lines TYPE TABLE OF abaptxt255.",
        "DATA: lv_prog TYPE c LENGTH 40.",
        "DATA: lv_cnt  TYPE i.",
        f"lv_prog = '{include_name[:40]}'.",
        f"CALL FUNCTION 'RPY_PROGRAM_READ'",
        f"  EXPORTING program_name   = lv_prog",
        f"  TABLES source_extended   = lt_lines",
        f"  EXCEPTIONS not_found     = 1.",
        f"lv_cnt = lines( lt_lines ).",
        f"WRITE: / 'Include {short[:20]}'.",
        f"WRITE: / 'Lines:', lv_cnt.",
        f"WRITE: / 'RC:', sy-subrc.",
    ]
    run_abap_bridge(abap, f"VERIFY {short}")


def activate_class_via_bridge(class_name: str):
    """Activate class via SEO_CLASS_ACTIVATE (TABLES CLSKEYS = SEOC_CLASS_KEYS)."""
    abap = [
        "REPORT z_activate.",
        "DATA: lt_keys TYPE seoc_class_keys.",
        "DATA: ls_key  TYPE seoclskey.",
        f"ls_key = '{class_name}'.",
        "APPEND ls_key TO lt_keys.",
        "CALL FUNCTION 'SEO_CLASS_ACTIVATE'",
        "  TABLES clskeys       = lt_keys",
        "  EXCEPTIONS OTHERS   = 9.",
        "WRITE: / 'Activate rc:', sy-subrc.",
    ]
    run_abap_bridge(abap, f"ACTIVATE {class_name}")



# ── Source code definitions ──────────────────────────────────────────────────

CRP_PROCESS_REQ_CCIMP = "ZCL_CRP_PROCESS_REQ============CCIMP"
CRP_PROCESS_REQ_LINES = [
    "CLASS zcl_crp_process_req IMPLEMENTATION.",
    "",
    "  METHOD resolve_staff_from_user.",
    "    SELECT SINGLE pernr INTO rv_staff_id",
    "      FROM pa0001",
    "      WHERE usrid = iv_uname",
    "        AND endda >= sy-datum",
    "        AND begda <= sy-datum.",
    "    IF sy-subrc <> 0.",
    "      rv_staff_id = space.",
    "    ENDIF.",
    "  ENDMETHOD.",
    "",
    "  METHOD determine_gl_account.",
    "    rv_gl_account = '0001004010'.",
    "  ENDMETHOD.",
    "",
    "  METHOD save_data.",
    "    MODIFY zcrp_cert FROM is_cert.",
    "    IF sy-subrc <> 0.",
    "      INSERT zcrp_cert FROM is_cert.",
    "    ENDIF.",
    "    COMMIT WORK AND WAIT.",
    "    ev_success = abap_true.",
    "  ENDMETHOD.",
    "",
    "ENDCLASS.",
]

DPC_EXT_CCIMP = "ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP"
DPC_EXT_LINES = [
    "CLASS zcl_z_crp_srv_dpc_ext IMPLEMENTATION.",
    "",
    "  METHOD crpcertificateset_get_entityset.",
    "    DATA: lt_certs TYPE TABLE OF zcrp_cert.",
    "    DATA: ls_cert  TYPE zcrp_cert.",
    "    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "    SELECT * FROM zcrp_cert INTO TABLE lt_certs.",
    "    LOOP AT lt_certs INTO ls_cert.",
    "      CLEAR ls_entity.",
    "      ls_entity-company_code   = ls_cert-bukrs.",
    "      ls_entity-fiscal_year    = ls_cert-gjahr.",
    "      ls_entity-certificate_id = ls_cert-certificate_id.",
    "      ls_entity-status         = ls_cert-status.",
    "      APPEND ls_entity TO et_entityset.",
    "    ENDLOOP.",
    "  ENDMETHOD.",
    "",
    "  METHOD crpcertificateset_create_entity.",
    "    DATA: ls_cert   TYPE zcrp_cert.",
    "    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "    io_data_provider->read_entry_data(",
    "      IMPORTING es_entry_data = ls_entity ).",
    "    ls_cert-bukrs          = ls_entity-company_code.",
    "    ls_cert-gjahr          = ls_entity-fiscal_year.",
    "    ls_cert-certificate_id = ls_entity-certificate_id.",
    "    ls_cert-status         = '01'.",
    "    ls_cert-calc_amount    = ls_entity-calculated_amount.",
    "    ls_cert-currency       = ls_entity-currency.",
    "    ls_cert-created_by     = sy-uname.",
    "    INSERT zcrp_cert FROM ls_cert.",
    "    IF sy-subrc <> 0.",
    "      /iwbep/cx_mgw_busi_exception=>raise( 'Create failed' ).",
    "    ENDIF.",
    "    COMMIT WORK AND WAIT.",
    "    er_entity = ls_entity.",
    "    er_entity-status = '01'.",
    "  ENDMETHOD.",
    "",
    "ENDCLASS.",
]


if __name__ == "__main__":
    # Step 1: test that the placeholder technique works on a simple case
    print("=== Phase 0: Test placeholder technique ===")
    test_lines = ["    ls_cert-status = '01'.", "    er_entity-status = '01'."]
    test_abap  = build_abap_writer("ZZZZ_TEST_INCLUDE", test_lines)
    print("Generated ABAP (first 15 lines):")
    for i, l in enumerate(test_abap[:15]):
        print(f"  [{len(l):2d}] {l}")

    # Step 2: Check include existence before writing
    print("\n=== Phase 1: Verify includes exist ===")
    verify_include(CRP_PROCESS_REQ_CCIMP)
    verify_include(DPC_EXT_CCIMP)

    # Step 3: Write ZCL_CRP_PROCESS_REQ CCIMP (doesn't exist - NOT_FOUND expected)
    print("\n=== Phase 2: Write ZCL_CRP_PROCESS_REQ CCIMP ===")
    abap_lines = build_abap_writer(CRP_PROCESS_REQ_CCIMP, CRP_PROCESS_REQ_LINES)
    run_abap_bridge(abap_lines, "WRITE ZCL_CRP_PROCESS_REQ CCIMP")

    # Step 4: Write ZCL_Z_CRP_SRV_DPC_EXT CCIMP (exists - should update)
    print("\n=== Phase 3: Write ZCL_Z_CRP_SRV_DPC_EXT CCIMP ===")
    abap_lines = build_abap_writer(DPC_EXT_CCIMP, DPC_EXT_LINES)
    run_abap_bridge(abap_lines, "WRITE ZCL_Z_CRP_SRV_DPC_EXT CCIMP")

    # Step 5: Verify written content
    print("\n=== Phase 4: Verify results ===")
    verify_include(CRP_PROCESS_REQ_CCIMP)
    verify_include(DPC_EXT_CCIMP)

    # Step 6: Activate
    print("\n=== Phase 5: Activate classes ===")
    activate_class_via_bridge("ZCL_CRP_PROCESS_REQ")
    activate_class_via_bridge("ZCL_Z_CRP_SRV_DPC_EXT")
