"""
rpy_include_insert.py
Use RPY_INCLUDE_INSERT with SOURCE_EXTENDED (ABAPTXT255 table) to write 
CCIMP code to class includes, then activate via ABAP bridge.
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

def write_include(include_name, code_lines):
    """Use RPY_INCLUDE_INSERT to write ABAP source to include."""
    conn = get_conn()
    print(f"\nWriting {len(code_lines)} lines to {include_name}...")
    source = [{"LINE": l[:255]} for l in code_lines]
    try:
        result = conn.call(
            "RPY_INCLUDE_INSERT",
            INCLUDE_NAME=include_name,
            DEVELOPMENT_CLASS="ZCRP",
            TRANSPORT_NUMBER="D01K9B0EWT",
            SUPPRESS_DIALOG="X",
            SOURCE_EXTENDED=source,
        )
        print(f"  [OK] Include written.")
        return True
    except RFCError as e:
        err = str(e)
        if "ALREADY_EXISTS" in err:
            # Try update instead
            print(f"  Include exists - trying RPY_INCLUDE_UPDATE...")
            try:
                conn2 = get_conn()
                conn2.call(
                    "RPY_INCLUDE_UPDATE",
                    INCLUDE_NAME=include_name,
                    SOURCE_EXTENDED=source,
                )
                print(f"  [OK] Include updated.")
                conn2.close()
                return True
            except Exception as e2:
                print(f"  [FAIL] Update: {e2}")
                return False
        print(f"  [FAIL]: {err}")
        return False
    except Exception as e:
        print(f"  [ERROR]: {e}")
        return False
    finally:
        conn.close()

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

# ── ZCL_Z_CRP_SRV_DPC_EXT CCIMP ───────────────────────────────────────
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
    "      ls_entity-company_code    = ls_cert-bukrs.",
    "      ls_entity-fiscal_year     = ls_cert-gjahr.",
    "      ls_entity-certificate_id  = ls_cert-certificate_id.",
    "      ls_entity-status          = ls_cert-status.",
    "      ls_entity-staff_id        = ls_cert-staff_id.",
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
    "    er_entity-staff_id         = ls_cert-staff_id.",
    "    er_entity-calculated_amount = ls_cert-calc_amount.",
    "    er_entity-currency         = ls_cert-currency.",
    "    er_entity-gl_account       = ls_cert-gl_account.",
    "  ENDMETHOD.",
    "",
    "  METHOD crpcertificateset_create_entity.",
    "    DATA: ls_cert   TYPE zcrp_cert.",
    "    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "    DATA: lo_helper TYPE REF TO zcl_crp_process_req.",
    "",
    "    io_data_provider->read_entry_data(",
    "      IMPORTING es_entry_data = ls_entity ).",
    "",
    "    CREATE OBJECT lo_helper.",
    "",
    "    ls_cert-bukrs          = ls_entity-company_code.",
    "    ls_cert-gjahr          = ls_entity-fiscal_year.",
    "    ls_cert-certificate_id = ls_entity-certificate_id.",
    "    ls_cert-status         = '01'.",
    "    ls_cert-bldat          = sy-datum.",
    "    ls_cert-budat          = sy-datum.",
    "    ls_cert-calc_amount    = ls_entity-calculated_amount.",
    "    ls_cert-currency       = ls_entity-currency.",
    "    ls_cert-created_by     = sy-uname.",
    "    ls_cert-gl_account = lo_helper->determine_gl_account( ).",
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
    "  METHOD crpcertificateset_update_entity.",
    "    DATA: ls_entity TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "",
    "    io_data_provider->read_entry_data(",
    "      IMPORTING es_entry_data = ls_entity ).",
    "",
    "    UPDATE zcrp_cert SET",
    "      status      = ls_entity-status",
    "      calc_amount = ls_entity-calculated_amount",
    "      changed_by  = sy-uname",
    "      changed_at  = sy-datum",
    "    WHERE bukrs           = ls_entity-company_code",
    "      AND gjahr          = ls_entity-fiscal_year",
    "      AND certificate_id = ls_entity-certificate_id.",
    "",
    "    COMMIT WORK AND WAIT.",
    "    er_entity = ls_entity.",
    "  ENDMETHOD.",
    "",
    "  METHOD submitforapproval_fi.",
    "    DATA: ls_cert   TYPE zcrp_cert.",
    "    DATA: ls_result TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "    DATA: ls_pars   TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
    "",
    "    io_tech_request_context->get_function_import_pars(",
    "      IMPORTING es_pars = ls_pars ).",
    "",
    "    SELECT SINGLE * FROM zcrp_cert INTO ls_cert",
    "      WHERE certificate_id = ls_pars-certificate_id.",
    "",
    "    IF sy-subrc <> 0 OR ls_cert-status <> '01'.",
    "      /iwbep/cx_mgw_busi_exception=>raise(",
    "        'Only Draft certificates can be submitted' ).",
    "    ENDIF.",
    "",
    "    UPDATE zcrp_cert SET status = '02'",
    "      WHERE certificate_id = ls_cert-certificate_id.",
    "    COMMIT WORK AND WAIT.",
    "",
    "    ls_result-certificate_id = ls_cert-certificate_id.",
    "    ls_result-status = '02'.",
    "    copy_data_to_ref(",
    "      EXPORTING is_data = ls_result",
    "      CHANGING  cr_data = er_data ).",
    "  ENDMETHOD.",
    "",
    "ENDCLASS.",
]

if __name__ == "__main__":
    print("=== Phase 1: Write CCIMP Code via RPY_INCLUDE_INSERT ===")
    write_include("ZCL_CRP_PROCESS_REQ============CCIMP", CRP_PROCESS_REQ_CCIMP)
    write_include("ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP", DPC_EXT_CCIMP)

    print("\n=== Phase 2: Activate via ABAP bridge ===")
    for cls_name in ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]:
        execute_abap(f"""
REPORT Z_ACTIVATE.
DATA: lv_clsname TYPE seoclsname VALUE '{cls_name}'.
DATA: lv_state   TYPE seostate.

* Check state before
SELECT SINGLE state FROM seoclassdf
  INTO lv_state WHERE clsname = lv_clsname.
WRITE: / 'Pre-activate state:', lv_state.

* Use syntactically valid call for SEO_CLASS_ACTIVATE_P (single class)
PERFORM activate_class USING lv_clsname.

SELECT SINGLE state FROM seoclassdf
  INTO lv_state WHERE clsname = lv_clsname.
WRITE: / 'Post-activate state:', lv_state.

FORM activate_class USING iv_clsname TYPE seoclsname.
  CALL FUNCTION 'SEO_CLASS_ACTIVATE_P'
    EXPORTING
      clsname = iv_clsname
    EXCEPTIONS
      OTHERS  = 1.
  WRITE: / 'SEO_CLASS_ACTIVATE_P subrc:', sy-subrc.
ENDFORM.
""", f"ACTIVATE {cls_name}")
