"""
write_ccimp_abap_bridge.py
Write CCIMP code using ABAP bridge local execution.
RPY_PROGRAM_UPDATE is not remotely callable - must use ABAP bridge to call it locally.
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection, RFCError
from dotenv import load_dotenv
load_dotenv()

def get_conn():
    p = {"ashost": "172.16.4.66", "sysnr": "00", "client": "350",
         "user": os.getenv("SAP_USER"), "lang": "EN",
         "snc_mode": "1", "snc_partnername": os.getenv("SAP_SNC_PARTNERNAME"),
         "snc_qop": "9"}
    return Connection(**p)

def execute_abap(code, label=""):
    conn = get_conn()
    if label: print(f"\n[{label}]")
    src = [{"LINE": l[:72]} for l in code.split('\n')]
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
        for w in res.get("WRITES", []):
            print(f"  SAP: {w.get('ZEILE') or list(w.values())[0]}")
        if res.get("ERRORMESSAGE"):
            print(f"  ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
    finally:
        conn.close()

def write_include_via_bridge(include_name, code_lines):
    """Use RPY_PROGRAM_UPDATE via ABAP bridge to write to class include."""
    
    # Build the ABAP that:
    # 1. Constructs the source line by line into an ABAPTXT255 table
    # 2. Calls RPY_PROGRAM_UPDATE locally
    
    abap_lines = [
        "REPORT Z_WRITE_INCL.",
        "DATA: lt_source TYPE TABLE OF abaptxt255.",
        "DATA: lv_line   TYPE abaptxt255.",
        "",
    ]
    for line in code_lines:
        escaped = line.replace("'", "''")[:70]
        abap_lines.append(f"lv_line = '{escaped}'.")
        abap_lines.append(f"APPEND lv_line TO lt_source.")
    
    abap_lines += [
        "",
        f"CALL FUNCTION 'RPY_PROGRAM_UPDATE'",
        f"  EXPORTING",
        f"    program_name     = '{include_name}'",
        f"    transport_number = 'D01K9B0EWT'",
        f"  TABLES",
        f"    source_extended  = lt_source",
        f"  EXCEPTIONS",
        f"    not_found        = 1",
        f"    OTHERS           = 2.",
        f"WRITE: / 'WRITE subrc:', sy-subrc.",
    ]
    
    conn = get_conn()
    print(f"\nWriting {len(code_lines)} lines to {include_name} via ABAP bridge RPY_PROGRAM_UPDATE...")
    src = [{"LINE": l[:72]} for l in abap_lines]
    try:
        res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=src)
        for w in res.get("WRITES", []):
            print(f"  SAP: {w.get('ZEILE') or list(w.values())[0]}")
        if res.get("ERRORMESSAGE"):
            print(f"  ERROR: {res.get('ERRORMESSAGE')}")
        return res
    except Exception as e:
        print(f"  FAILED: {e}")
    finally:
        conn.close()

# ── ZCL_CRP_PROCESS_REQ CCIMP ─────────────────────────────────────────
CRP_PROCESS_REQ_CCIMP = [
    "CLASS ZCL_CRP_PROCESS_REQ IMPLEMENTATION.",
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

DPC_EXT_CCIMP = [
    "CLASS ZCL_Z_CRP_SRV_DPC_EXT IMPLEMENTATION.",
    "",
    "  METHOD crpcertificateset_get_entityset.",
    "    DATA: lt_certs TYPE TABLE OF zcrp_cert.",
    "    DATA: ls_cert  TYPE zcrp_cert.",
    "    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "",
    "    SELECT * FROM zcrp_cert INTO TABLE lt_certs.",
    "",
    "    LOOP AT lt_certs INTO ls_cert.",
    "      CLEAR ls_entity.",
    "      ls_entity-company_code    = ls_cert-bukrs.",
    "      ls_entity-fiscal_year     = ls_cert-gjahr.",
    "      ls_entity-certificate_id  = ls_cert-certificate_id.",
    "      ls_entity-status          = ls_cert-status.",
    "      ls_entity-calculated_amount = ls_cert-calc_amount.",
    "      ls_entity-currency        = ls_cert-currency.",
    "      APPEND ls_entity TO et_entityset.",
    "    ENDLOOP.",
    "  ENDMETHOD.",
    "",
    "  METHOD crpcertificateset_get_entity.",
    "    DATA: ls_cert TYPE zcrp_cert.",
    "    DATA: ls_key  TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "",
    "    io_tech_request_context->get_keys(",
    "      IMPORTING es_key_values = ls_key ).",
    "",
    "    SELECT SINGLE * FROM zcrp_cert INTO ls_cert",
    "      WHERE bukrs           = ls_key-company_code",
    "      AND   gjahr          = ls_key-fiscal_year",
    "      AND   certificate_id = ls_key-certificate_id.",
    "",
    "    IF sy-subrc <> 0.",
    "      /iwbep/cx_mgw_busi_exception=>raise( 'Not found' ).",
    "    ENDIF.",
    "",
    "    er_entity-company_code     = ls_cert-bukrs.",
    "    er_entity-fiscal_year      = ls_cert-gjahr.",
    "    er_entity-certificate_id   = ls_cert-certificate_id.",
    "    er_entity-status           = ls_cert-status.",
    "    er_entity-calculated_amount = ls_cert-calc_amount.",
    "    er_entity-currency         = ls_cert-currency.",
    "  ENDMETHOD.",
    "",
    "  METHOD crpcertificateset_create_entity.",
    "    DATA: ls_cert   TYPE zcrp_cert.",
    "    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "",
    "    io_data_provider->read_entry_data(",
    "      IMPORTING es_entry_data = ls_entity ).",
    "",
    "    ls_cert-bukrs          = ls_entity-company_code.",
    "    ls_cert-gjahr          = ls_entity-fiscal_year.",
    "    ls_cert-certificate_id = ls_entity-certificate_id.",
    "    ls_cert-status         = '01'.",
    "    ls_cert-calc_amount    = ls_entity-calculated_amount.",
    "    ls_cert-currency       = ls_entity-currency.",
    "    ls_cert-created_by     = sy-uname.",
    "    ls_cert-bldat          = sy-datum.",
    "",
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
    print("=== Writing CCIMP code via ABAP bridge ===")
    write_include_via_bridge("ZCL_CRP_PROCESS_REQ============CCIMP", CRP_PROCESS_REQ_CCIMP)
    write_include_via_bridge("ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP", DPC_EXT_CCIMP)
