"""
smart_ccimp_write.py
Write CCIMP code using a chunked ABAP bridge approach.
Problem: ABAP source lines like lv_line = '..some code...'  get mangled.
Solution: Write code chunks of 20 lines at a time, handling escape carefully.
Also: Use INSERT INTO DYNPSOURCE (direct table write) as fallback.
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

def write_include_chunked(include_name, code_lines, chunk_size=20):
    """
    Write code in chunks via ABAP bridge.
    First chunk creates/appends, subsequent chunks append.
    """
    print(f"\n=== Writing {len(code_lines)} lines to {include_name} ===")
    
    # Check if include exists first
    exists_result = execute_abap(f"""
REPORT Z_CHECK.
DATA: lv_exists TYPE c.
CALL FUNCTION 'RPY_PROGRAM_READ'
  EXPORTING
    program_name     = '{include_name}'
  EXCEPTIONS
    not_found        = 1
    OTHERS           = 2.
WRITE: / 'EXISTS subrc:', sy-subrc.
""", f"CHECK {include_name}")

    # Now write using RPY_PROGRAM_UPDATE via bridge for each chunk
    total = len(code_lines)
    for start in range(0, total, chunk_size):
        chunk = code_lines[start:start+chunk_size]
        end = min(start + chunk_size, total)
        print(f"  Writing lines {start+1}-{end}/{total}...")
        
        abap_lines = [
            "REPORT Z_WRITE_CHUNK.",
            "DATA: lt_source TYPE TABLE OF abaptxt255.",
            "DATA: lv_line   TYPE abaptxt255.",
        ]
        for line in chunk:
            # Escape single quotes and truncate at runtime-safe length
            truncated = line[:70]
            escaped = truncated.replace("'", "''")
            abap_lines.append(f"lv_line = '{escaped}'.")
            abap_lines.append(f"APPEND lv_line TO lt_source.")
        
        abap_lines += [
            f"CALL FUNCTION 'RPY_PROGRAM_UPDATE'",
            f"  EXPORTING",
            f"    program_name     = '{include_name}'",
            f"  TABLES",
            f"    source_extended  = lt_source",
            f"  EXCEPTIONS",
            f"    not_found        = 1",
            f"    OTHERS           = 2.",
            f"WRITE: / 'Chunk write subrc:', sy-subrc.",
        ]
        
        conn = get_conn()
        abap_src = [{"LINE": l[:72]} for l in abap_lines]
        try:
            res = conn.call("RFC_ABAP_INSTALL_AND_RUN", PROGRAM=abap_src)
            for w in res.get("WRITES", []):
                val = w.get('ZEILE') or list(w.values())[0]
                print(f"    SAP: {val}")
            if res.get("ERRORMESSAGE"):
                print(f"    ERROR: {res.get('ERRORMESSAGE')}")
        except Exception as e:
            print(f"    FAILED: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    # Test with ZCL_Z_CRP_SRV_DPC_EXT CCIMP (this one exists)
    dpc_lines = [
        "CLASS ZCL_Z_CRP_SRV_DPC_EXT IMPLEMENTATION.",
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
        "  METHOD crpcertificateset_get_entity.",
        "    DATA: ls_cert TYPE zcrp_cert.",
        "    DATA: ls_key  TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.",
        "    io_tech_request_context->get_keys(",
        "      IMPORTING es_key_values = ls_key ).",
        "    SELECT SINGLE * FROM zcrp_cert INTO ls_cert",
        "      WHERE bukrs = ls_key-company_code",
        "      AND certificate_id = ls_key-certificate_id.",
        "    IF sy-subrc <> 0.",
        "      /iwbep/cx_mgw_busi_exception=>raise( |Not found| ).",
        "    ENDIF.",
        "    er_entity-company_code    = ls_cert-bukrs.",
        "    er_entity-certificate_id  = ls_cert-certificate_id.",
        "    er_entity-status          = ls_cert-status.",
        "  ENDMETHOD.",
        "",
        "ENDCLASS.",
    ]
    write_include_chunked("ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP", dpc_lines)
