"""
final_rpy_write.py

KEY LEARNINGS from previous investigation:
1. Classes exist in SEOCLASSDF (both state=1/inactive)
2. ZCL_CRP_PROCESS_REQ============CCIMP is empty (NAME_NOT_ALLOWED = include doesn't exist yet)  
3. ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP exists (insert triggers dialog fix = update path)
4. RPY_INCLUDE_UPDATE triggers dialog - use SUPPRESS_DIALOG flag
5. RPY_PROGRAM_INSERT can create new programs/includes
6. SEO_CLASS_ACTIVATE (plural CLSKEYS) can be called via ABAP bridge with correct fix

Strategy:
- Use RPY_PROGRAM_INSERT for new includes (ZCL_CRP_PROCESS_REQ CCIMP doesn't exist)
- Use RPY_INCLUDE_UPDATE suppressed for existing (ZCL_Z_CRP_SRV_DPC_EXT CCIMP) 
- Activate via direct Python RFC with CLSKEYS using PROGTAB-compatible row format
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

def write_via_rpy_program(program_name, code_lines, title=""):
    """RPY_PROGRAM_INSERT to create new ABAP programs/includes."""
    conn = get_conn()
    print(f"\nWriting {len(code_lines)} lines via RPY_PROGRAM_INSERT to {program_name}...")
    source = [{"LINE": l[:255]} for l in code_lines]
    try:
        conn.call(
            "RPY_PROGRAM_INSERT",
            PROGRAM_NAME=program_name,
            TITLE_STRING=title[:70] if title else program_name,
            DEVELOPMENT_CLASS="ZCRP",
            TRANSPORT_NUMBER="D01K9B0EWT",
            SUPPRESS_DIALOG="X",
            SOURCE_EXTENDED=source,
        )
        print(f"  [OK] Program inserted.")
        return True
    except RFCError as e:
        err = str(e)
        if "ALREADY_EXISTS" in err:
            print(f"  Already exists - trying RPY_PROGRAM_UPDATE...")
            try:
                conn2 = get_conn()
                conn2.call("RPY_PROGRAM_UPDATE",
                          PROGRAM_NAME=program_name,
                          SOURCE_EXTENDED=source)
                conn2.close()
                print(f"  [OK] Updated.")
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

# ── Implementation ────────────────────────────────────────────────────

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
    "    SELECT * FROM zcrp_cert INTO TABLE lt_certs",
    "      WHERE created_by = sy-uname.",
    "",
    "    LOOP AT lt_certs INTO ls_cert.",
    "      CLEAR ls_entity.",
    "      ls_entity-company_code   = ls_cert-bukrs.",
    "      ls_entity-fiscal_year    = ls_cert-gjahr.",
    "      ls_entity-certificate_id = ls_cert-certificate_id.",
    "      ls_entity-status         = ls_cert-status.",
    "      ls_entity-calculated_amount = ls_cert-calc_amount.",
    "      ls_entity-currency       = ls_cert-currency.",
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
    "    er_entity-gl_account       = ls_cert-gl_account.",
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
    "    ls_cert-bldat          = sy-datum.",
    "    ls_cert-budat          = sy-datum.",
    "    ls_cert-calc_amount    = ls_entity-calculated_amount.",
    "    ls_cert-currency       = ls_entity-currency.",
    "    ls_cert-created_by     = sy-uname.",
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
    "    WHERE bukrs           = ls_entity-company_code",
    "      AND gjahr          = ls_entity-fiscal_year",
    "      AND certificate_id = ls_entity-certificate_id.",
    "",
    "    COMMIT WORK AND WAIT.",
    "    er_entity = ls_entity.",
    "  ENDMETHOD.",
    "",
    "ENDCLASS.",
]

if __name__ == "__main__":
    print("=== Phase 1: Write CCIMP Code ===")
    # ZCL_CRP_PROCESS_REQ - doesn't exist yet, use INSERT
    write_via_rpy_program("ZCL_CRP_PROCESS_REQ============CCIMP",
                          CRP_PROCESS_REQ_CCIMP,
                          "ZCL_CRP_PROCESS_REQ Implementation")

    # ZCL_Z_CRP_SRV_DPC_EXT - exists, use UPDATE path
    write_via_rpy_program("ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP",
                          DPC_EXT_CCIMP,
                          "ZCL_Z_CRP_SRV_DPC_EXT Implementation")

    print("\n=== Phase 2: Verify Written Content ===")
    for incl in ["ZCL_CRP_PROCESS_REQ============CCIMP", "ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP"]:
        execute_abap(f"""
REPORT Z_VERIFY.
DATA: lt_lines TYPE TABLE OF abaptxt255.
DATA: lv_line  TYPE abaptxt255.
CALL FUNCTION 'SIW_RFC_READ_REPORT'
  EXPORTING i_name = '{incl}'
  IMPORTING e_tab_code = lt_lines
  EXCEPTIONS OTHERS = 1.
WRITE: / '{incl}:', lines( lt_lines ), 'lines'.
""", f"VERIFY {incl}")
