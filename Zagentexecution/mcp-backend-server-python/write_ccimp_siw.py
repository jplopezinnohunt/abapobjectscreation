"""
write_ccimp_siw.py

Write ABAP class CCIMP include source using SIW_RFC_WRITE_REPORT.
Called DIRECTLY from pyrfc (no ABAP bridge needed) — completely avoids:
  - 72-char ABAP bridge line limit
  - Single quote issues in generated ABAP code
  - Dialog popups from RPY_PROGRAM_UPDATE

SIW_RFC_WRITE_REPORT parameters:
  I_NAME    SYREPID       : Include program name (e.g. ZCL_CRP_PROCESS_REQ============CCIMP)
  I_OBJECT  TADIR-OBJECT  : Object type (PROG)
  I_OBJNAME TADIR-OBJ_NAME: Object name (same as program name)
  I_PROGTYPE SUBC         : Program type (I = include)
  I_TAB_CODE SIW_TAB_CODE : Source code table (has ZEILE field)
  E_STR_EXCEPTION         : Output exception struct
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection
from dotenv import load_dotenv
load_dotenv()

TRANSPORT = "D01K9B0EWT"


def get_conn():
    return Connection(
        ashost="172.16.4.66", sysnr="00", client="350",
        user=os.getenv("SAP_USER"), lang="EN",
        snc_mode="1", snc_partnername=os.getenv("SAP_SNC_PARTNERNAME"), snc_qop="9"
    )


def write_ccimp(include_name: str, source_lines: list[str]) -> bool:
    """
    Write ABAP source to a class CCIMP include using SIW_RFC_WRITE_REPORT.
    No ABAP bridge, no dialog, no 72-char limit, no quote encoding needed.
    """
    print(f"\n[SIW] Writing {include_name} ({len(source_lines)} lines)...")

    # Build SIW_TAB_CODE table — each entry has ZEILE field (line of code)
    tab_code = [{"ZEILE": line} for line in source_lines]

    conn = get_conn()
    try:
        result = conn.call(
            "SIW_RFC_WRITE_REPORT",
            I_NAME=include_name,
            I_OBJECT="PROG",
            I_OBJNAME=include_name,
            I_PROGTYPE="I",  # I = Include
            I_TAB_CODE=tab_code,
        )
        exc = result.get("E_STR_EXCEPTION", {})
        msg_text = exc.get("MSGTEXT", "") or exc.get("MESSAGE", "") or str(exc)
        if msg_text and msg_text.strip():
            print(f"  [SIW] Exception: {msg_text}")
            return False
        else:
            print(f"  [SIW] Write OK — no exception")
            return True
    except Exception as e:
        print(f"  [SIW] FAILED: {e}")
        return False
    finally:
        conn.close()


def read_include(include_name: str) -> list[str]:
    """Read source lines of a CCIMP include (using SE_REPO_PROGRAM_READ or direct)."""
    print(f"\n[READ] Reading {include_name}...")
    conn = get_conn()
    try:
        result = conn.call(
            "RPY_PROGRAM_READ",
            PROGRAM_NAME=include_name,
        )
        lines = [r.get("LINE", "").rstrip() for r in result.get("SOURCE_EXTENDED", [])]
        print(f"  Lines read: {len(lines)}")
        return lines
    except Exception as e:
        print(f"  FAILED: {e}")
        return []
    finally:
        conn.close()


def activate_classes(class_names: list[str]) -> bool:
    """Activate one or more ABAP classes using SEO_CLASS_ACTIVATE."""
    print(f"\n[ACT] Activating: {class_names}")
    conn = get_conn()
    try:
        clskeys = [{"CLSNAME": name} for name in class_names]
        result = conn.call("SEO_CLASS_ACTIVATE", CLSKEYS=clskeys)
        print(f"  Activation successful")
        return True
    except Exception as e:
        print(f"  FAILED: {e}")
        return False
    finally:
        conn.close()


# ── Source code definitions ──────────────────────────────
# Note: No escaping needed — passed directly as Python strings

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
    print("=== Writing CCIMP via SIW_RFC_WRITE_REPORT ===\n")

    # Step 1: Write ZCL_CRP_PROCESS_REQ CCIMP
    ok1 = write_ccimp(CRP_PROCESS_REQ_CCIMP, CRP_PROCESS_REQ_LINES)
    print(f"  ZCL_CRP_PROCESS_REQ: {'OK' if ok1 else 'FAILED'}")

    # Step 2: Write ZCL_Z_CRP_SRV_DPC_EXT CCIMP
    ok2 = write_ccimp(DPC_EXT_CCIMP, DPC_EXT_LINES)
    print(f"  ZCL_Z_CRP_SRV_DPC_EXT: {'OK' if ok2 else 'FAILED'}")

    # Step 3: Read back to confirm
    print("\n=== Verifying written content ===")
    lines1 = read_include(CRP_PROCESS_REQ_CCIMP)
    if lines1:
        print(f"  ZCL_CRP_PROCESS_REQ: {len(lines1)} lines")
        for l in lines1[:5]:
            print(f"    {l}")

    lines2 = read_include(DPC_EXT_CCIMP)
    if lines2:
        print(f"  ZCL_Z_CRP_SRV_DPC_EXT: {len(lines2)} lines")
        for l in lines2[:5]:
            print(f"    {l}")

    # Step 4: Activate both classes
    if ok1 or ok2:
        print("\n=== Activating classes ===")
        activate_classes(["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"])
