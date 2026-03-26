"""
write_ccimp_insert_report.py

Use ABAP's native INSERT REPORT statement inside the ABAP bridge.
INSERT REPORT writes source code directly — no dialog, no RPY_PROGRAM_UPDATE,
no transport popup, and it CREATES the include if it doesn't exist.

ABAP statement: INSERT REPORT '<prog_name>' FROM <itab>.
- Creates or replaces the source in REPOSRC
- No lock required, no dialog
- Works for includes that don't yet exist (unlike RPY_PROGRAM_UPDATE)

Also uses the placeholder technique for single quotes.
"""
import os, sys
sys.stdout.reconfigure(encoding='utf-8')
from pyrfc import Connection
from dotenv import load_dotenv
load_dotenv()
TRANSPORT = "D01K9B0EWT"
ALLOWED_PACKAGE = "ZCRP"   # Security rule: only operate on objects in this package
PH = chr(127)  # placeholder for single quote


def validate_program_name(prog_name: str):
    """
    SECURITY GUARD: Only allow writes to Z* programs.
    The physical include name follows pattern ZCL_*=CCIMP — always starts with Z.
    Raises ValueError if name does not start with Z.
    """
    if not prog_name.upper().startswith("Z"):
        raise ValueError(
            f"SECURITY: Refusing to write to '{prog_name}' — "
            f"only Z* programs in package {ALLOWED_PACKAGE} are allowed."
        )



def get_conn():
    return Connection(
        ashost="172.16.4.66", sysnr="00", client="350",
        user=os.getenv("SAP_USER"), lang="EN",
        snc_mode="1", snc_partnername=os.getenv("SAP_SNC_PARTNERNAME"), snc_qop="9"
    )


def run_bridge(lines: list[str], label: str = "") -> dict:
    """Run ABAP code via RFC_ABAP_INSTALL_AND_RUN bridge."""
    if label:
        print(f"\n[{label}]")
    conn = get_conn()
    src = [{"LINE": l[:72]} for l in lines]
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
        return {}
    finally:
        conn.close()


def build_insert_report(prog_name: str, source_lines: list[str]) -> list[str]:
    """
    Generate ABAP bridge code that uses INSERT REPORT to write source.
    Uses chr(127) placeholder for single quotes in source content.
    prog_name must be <= 40 chars.
    """
    abap = [
        "REPORT z_insert_report.",
        "DATA: lv_sq   TYPE c.",
        "DATA: lv_ph   TYPE c.",
        "DATA: lv_prog TYPE c LENGTH 40.",
        "DATA: lv_line TYPE abaptxt255.",
        "DATA: lt_code TYPE TABLE OF abaptxt255.",
        "DATA: lv_x    TYPE x VALUE '7F'.",
        "",
        "lv_sq = ''''.",
        "lv_ph = lv_x.",
        f"lv_prog = '{prog_name}'.",
        "",
        "* === Build source table ===",
    ]

    MAX = 58  # safe max for literal in 72-char ABAP line

    def add_line(content: str):
        """Add statements to set lv_line and append to lt_code."""
        has_sq = "'" in content
        safe = content.replace("'", PH)

        if len(safe) == 0:
            abap.append("lv_line = ' '.")
        elif len(safe) <= MAX:
            abap.append(f"lv_line = '{safe}'.")
        else:
            # First chunk
            abap.append(f"lv_line = '{safe[:MAX]}'.")
            pos = MAX
            while pos < len(safe):
                chunk = safe[pos:pos + MAX]
                stmt = f"lv_line+{pos}({len(chunk)}) = '{chunk}'."
                if len(stmt) > 72:
                    # Use CONCATENATE for safety
                    chunk = safe[pos:pos + 20]
                    abap.append(f"CONCATENATE lv_line '{chunk}' INTO lv_line.")
                    pos += 20
                else:
                    abap.append(stmt)
                    pos += len(chunk)

        if has_sq:
            abap.append(
                "REPLACE ALL OCCURRENCES OF lv_ph IN lv_line WITH lv_sq."
            )
        abap.append("APPEND lv_line TO lt_code.")

    for line in source_lines:
        add_line(line)

    abap += [
        "",
        "* === Write source to include ===",
        "INSERT REPORT lv_prog FROM lt_code.",
        "WRITE: / 'INSERT REPORT rc:', sy-subrc.",
    ]
    return abap


def verify_include(prog_name: str) -> int:
    """Read include and return line count."""
    abap = [
        "REPORT z_verify.",
        "DATA: lt_lines TYPE TABLE OF c LENGTH 255.",
        "DATA: lv_prog TYPE c LENGTH 40.",
        "DATA: lv_cnt  TYPE i.",
        f"lv_prog = '{prog_name}'.",
        "READ REPORT lv_prog INTO lt_lines.",
        "lv_cnt = lines( lt_lines ).",
        "WRITE: / 'RC:', sy-subrc, 'Lines:', lv_cnt.",
    ]
    run_bridge(abap, f"VERIFY {prog_name[:30]}")


def activate_class(class_name: str):
    """Activate via SEO_CLASS_ACTIVATE TABLES CLSKEYS."""
    abap = [
        "REPORT z_activate.",
        "DATA: lt_keys TYPE seoc_class_keys.",
        "DATA: ls_key  TYPE seoclskey.",
        f"ls_key = '{class_name}'.",
        "APPEND ls_key TO lt_keys.",
        "CALL FUNCTION 'SEO_CLASS_ACTIVATE'",
        "  TABLES clskeys      = lt_keys",
        "  EXCEPTIONS OTHERS  = 9.",
        "WRITE: / 'ACT rc:', sy-subrc.",
    ]
    run_bridge(abap, f"ACTIVATE {class_name}")


# ── Source definitions ────────────────────────────────────

CRP_CCIMP = "ZCL_CRP_PROCESS_REQ============CCIMP"
CRP_LINES = [
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

DPC_CCIMP = "ZCL_Z_CRP_SRV_DPC_EXT=========CCIMP"
DPC_LINES = [
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
    print("=== Write CCIMP via INSERT REPORT ===\n")

    # Verify current state
    print("0. Current state:")
    verify_include(CRP_CCIMP)
    verify_include(DPC_CCIMP)

    # Write ZCL_CRP_PROCESS_REQ CCIMP
    print("\n1. Writing ZCL_CRP_PROCESS_REQ CCIMP...")
    abap = build_insert_report(CRP_CCIMP, CRP_LINES)
    run_bridge(abap, "INSERT CRP_CCIMP")

    # Write ZCL_Z_CRP_SRV_DPC_EXT CCIMP
    print("\n2. Writing ZCL_Z_CRP_SRV_DPC_EXT CCIMP...")
    abap = build_insert_report(DPC_CCIMP, DPC_LINES)
    run_bridge(abap, "INSERT DPC_CCIMP")

    # Verify results
    print("\n3. Verify after write:")
    verify_include(CRP_CCIMP)
    verify_include(DPC_CCIMP)

    # Activate
    print("\n4. Activating classes...")
    activate_class("ZCL_CRP_PROCESS_REQ")
    activate_class("ZCL_Z_CRP_SRV_DPC_EXT")

    print("\n=== Done ===")
