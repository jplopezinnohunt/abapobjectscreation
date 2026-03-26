"""
Final deploy: Write actual code to CCIMP includes and activate
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection, RFCError
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    p = {"ashost": "172.16.4.66", "sysnr": "00", "client": "350",
         "user": os.getenv("SAP_USER"), "lang": "EN"}
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"
        p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = "9"
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
        return None
    finally:
        conn.close()

def write_include(include_name, code_lines):
    conn = get_conn()
    print(f"\nWriting {len(code_lines)} lines to {include_name}...")
    tab_code = [{"LINE": l[:255]} for l in code_lines]
    try:
        conn.call("SIW_RFC_WRITE_REPORT", I_NAME=include_name, I_TAB_CODE=tab_code)
        print(f"  [OK] Written.")
        return True
    except Exception as e:
        print(f"  [FAIL]: {e}")
        return False
    finally:
        conn.close()

# ── ZCL_CRP_PROCESS_REQ CCIMP ─────────────────────────────────────────
CRP_PROCESS_REQ_CCIMP = [
    "CLASS ZCL_CRP_PROCESS_REQ IMPLEMENTATION.",
    "",
    "  METHOD resolve_staff_from_user.",
    "    DATA: ls_pa0001 TYPE pa0001.",
    "    SELECT SINGLE pernr INTO rv_staff_id",
    "      FROM pa0001",
    "      WHERE usrid = iv_uname",
    "        AND endda >= sy-datum",
    "        AND begda <= sy-datum.",
    "    IF sy-subrc <> 0.",
    "      RAISE EXCEPTION TYPE cx_bo_error",
    "        EXPORTING",
    "          textid = cx_bo_error=>cx_bo_error",
    "          text   = |Staff record not found for user { iv_uname }|.",
    "    ENDIF.",
    "  ENDMETHOD.",
    "",
    "  METHOD determine_gl_account.",
    "    \" Default GL account for CRP postings - derived from cost element config",
    "    \" UNESCO-specific: GL account for consultancy certificate costs",
    "    rv_gl_account = '0001004010'.  \" Consultancy/contractual services",
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

# ── ZCL_Z_CRP_SRV_DPC_EXT CCIMP ──────────────────────────────────────
DPC_EXT_CCIMP = [
    "CLASS ZCL_Z_CRP_SRV_DPC_EXT IMPLEMENTATION.",
    "",
    "  METHOD crpcertificateset_get_entityset.",
    "    DATA: lt_certs TYPE TABLE OF zcrp_cert.",
    "    DATA: ls_cert  TYPE zcrp_cert.",
    "    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "",  
    "    SELECT * FROM zcrp_cert INTO TABLE lt_certs",
    "      WHERE created_by = sy-uname",
    "      ORDER BY created_at DESCENDING.",
    "",
    "    LOOP AT lt_certs INTO ls_cert.",
    "      CLEAR ls_entity.",
    "      ls_entity-company_code     = ls_cert-bukrs.",
    "      ls_entity-fiscal_year      = ls_cert-gjahr.",
    "      ls_entity-certificate_id   = ls_cert-certificate_id.",
    "      ls_entity-status           = ls_cert-status.",
    "      ls_entity-staff_id         = ls_cert-staff_id.",
    "      ls_entity-staff_name       = ls_cert-staff_name.",
    "      ls_entity-grade            = ls_cert-grade.",
    "      ls_entity-document_date    = ls_cert-bldat.",
    "      ls_entity-posting_date     = ls_cert-budat.",
    "      ls_entity-calculated_amount = ls_cert-calc_amount.",
    "      ls_entity-currency         = ls_cert-currency.",
    "      APPEND ls_entity TO et_entityset.",
    "    ENDLOOP.",
    "  ENDMETHOD.",
    "",
    "  METHOD crpcertificateset_get_entity.",
    "    DATA: ls_cert TYPE zcrp_cert.",
    "    DATA: lo_key  TYPE REF TO /iwbep/if_mgw_req_entity.",
    "    DATA: ls_key  TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "",
    "    io_tech_request_context->get_keys( IMPORTING es_key_values = ls_key ).",
    "",
    "    SELECT SINGLE * FROM zcrp_cert INTO ls_cert",
    "      WHERE bukrs           = ls_key-company_code",
    "      AND   gjahr          = ls_key-fiscal_year",
    "      AND   certificate_id = ls_key-certificate_id.",
    "",
    "    IF sy-subrc <> 0.",
    '      /iwbep/cx_mgw_busi_exception=>raise( "Certificate not found" ).',
    "    ENDIF.",
    "",
    "    er_entity-company_code     = ls_cert-bukrs.",
    "    er_entity-fiscal_year      = ls_cert-gjahr.",
    "    er_entity-certificate_id   = ls_cert-certificate_id.",
    "    er_entity-status           = ls_cert-status.",
    "    er_entity-staff_id         = ls_cert-staff_id.",
    "    er_entity-staff_name       = ls_cert-staff_name.",
    "    er_entity-grade            = ls_cert-grade.",
    "    er_entity-calculated_amount = ls_cert-calc_amount.",
    "    er_entity-currency         = ls_cert-currency.",
    "    er_entity-gl_account       = ls_cert-gl_account.",
    "    er_entity-description      = ls_cert-description.",
    "  ENDMETHOD.",
    "",
    "  METHOD crpcertificateset_create_entity.",
    "    DATA: ls_cert  TYPE zcrp_cert.",
    "    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "    DATA: helper  TYPE REF TO zcl_crp_process_req.",
    "",
    "    io_data_provider->read_entry_data( IMPORTING es_entry_data = ls_entity ).",
    "",
    "    CREATE OBJECT helper.",
    "",
    "    ls_cert-bukrs          = ls_entity-company_code.",
    "    ls_cert-gjahr          = ls_entity-fiscal_year.",
    "    ls_cert-certificate_id = ls_entity-certificate_id.",
    "    ls_cert-status         = '01'. \" Draft",
    "    ls_cert-staff_id       = helper->resolve_staff_from_user( sy-uname ).",
    "    ls_cert-bldat          = sy-datum.",
    "    ls_cert-budat          = sy-datum.",
    "    ls_cert-calc_amount    = ls_entity-calculated_amount.",
    "    ls_cert-currency       = ls_entity-currency.",
    "    ls_cert-created_by     = sy-uname.",
    "    ls_cert-created_at     = sy-datum.",
    "    ls_cert-gl_account     = helper->determine_gl_account( ).",
    "",
    "    INSERT zcrp_cert FROM ls_cert.",
    "    IF sy-subrc <> 0.",
    '      /iwbep/cx_mgw_busi_exception=>raise( "Failed to create certificate" ).',
    "    ENDIF.",
    "    COMMIT WORK AND WAIT.",
    "",
    "    er_entity = ls_entity.",
    "    er_entity-status = '01'.",
    "  ENDMETHOD.",
    "",  
    "  METHOD crpcertificateset_update_entity.",
    "    DATA: ls_cert TYPE zcrp_cert.",
    "    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "",
    "    io_data_provider->read_entry_data( IMPORTING es_entry_data = ls_entity ).",
    "",
    "    UPDATE zcrp_cert SET",
    "      status         = ls_entity-status",
    "      calc_amount    = ls_entity-calculated_amount",
    "      description    = ls_entity-description",
    "      changed_by     = sy-uname",
    "      changed_at     = sy-datum",
    "    WHERE bukrs           = ls_entity-company_code",
    "      AND gjahr          = ls_entity-fiscal_year",
    "      AND certificate_id = ls_entity-certificate_id.",
    "",
    "    IF sy-subrc <> 0.",
    '      /iwbep/cx_mgw_busi_exception=>raise( "Certificate update failed" ).',
    "    ENDIF.",
    "    COMMIT WORK AND WAIT.",
    "    er_entity = ls_entity.",
    "  ENDMETHOD.",
    "",
    "  METHOD submitforapproval_fi.",
    "    DATA: ls_cert TYPE zcrp_cert.",
    "    DATA: ls_result TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "",
    "    SELECT SINGLE * FROM zcrp_cert INTO ls_cert",
    "      WHERE certificate_id = io_tech_request_context->get_function_import_pars( )-certificate_id.",
    "",
    "    IF sy-subrc <> 0 OR ls_cert-status <> '01'.",
    '      /iwbep/cx_mgw_busi_exception=>raise("Only Draft certificates can be submitted").',
    "    ENDIF.",
    "",
    "    UPDATE zcrp_cert SET status = '02' \" Submitted",
    "      WHERE certificate_id = ls_cert-certificate_id.",
    "    COMMIT WORK AND WAIT.",
    "",
    "    ls_result-certificate_id = ls_cert-certificate_id.",
    "    ls_result-status = '02'.",
    "    copy_data_to_ref( EXPORTING is_data = ls_result CHANGING cr_data = er_data ).",
    "  ENDMETHOD.",
    "",
    "ENDCLASS.",
]

if __name__ == "__main__":
    # 1. Write CCIMP code
    print("=== Phase 1: Write Implementation Code ===")
    write_include("ZCL_CRP_PROCESS_REQ============CCIMP", CRP_PROCESS_REQ_CCIMP)
    write_include("ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP", DPC_EXT_CCIMP)

    # 2. Activate via ABAP bridge using correct CLSKEYS as IMPORTING table
    print("\n=== Phase 2: Activate Classes ===")
    for cls_name in ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]:
        abap = f"""
REPORT Z_ACTIVATE.
DATA: lt_clskeys TYPE STANDARD TABLE OF seoclskey.
DATA: ls_clskey  TYPE seoclskey.
ls_clskey-clsname = '{cls_name}'.
APPEND ls_clskey TO lt_clskeys.

CALL FUNCTION 'SEO_CLASS_ACTIVATE'
  IMPORTING
    clskeys      = lt_clskeys
  EXCEPTIONS
    inconsistent = 1
    not_existing = 2
    not_specified = 3
    OTHERS       = 4.

WRITE: / 'ACTIVATE subrc:', sy-subrc.
DATA: lv_state TYPE seostate.
SELECT SINGLE state FROM seoclassdf
  INTO lv_state WHERE clsname = '{cls_name}'.
WRITE: / 'POST-ACTIVATE state:', lv_state.
"""
        execute_abap(abap, f"ACTIVATE {cls_name}")
