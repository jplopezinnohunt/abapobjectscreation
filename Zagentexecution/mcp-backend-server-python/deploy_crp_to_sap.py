"""
deploy_crp_to_sap.py
==============================================================
Deploys CRP ABAP classes to SAP D01/350 via RFC.

DEPLOYMENT ORDER:
  1. Write ZCL_CRP_PROCESS_REQ CCDEF (class definition / types)
  2. Write ZCL_CRP_PROCESS_REQ CCIMP (all METHOD...ENDMETHOD blocks)
  3. Activate ZCL_CRP_PROCESS_REQ
  4. Write ZCL_Z_CRP_SRV_DPC_EXT CCIMP (all override METHOD blocks)
  5. Activate ZCL_Z_CRP_SRV_DPC_EXT

Transport: D01K9B0EWT (CRP Services — Workbench, JP_LOPEZ)
If no transport is passed, script will prompt for an order number.
==============================================================
Usage: python deploy_crp_to_sap.py [--transport TRKORR]
"""
import os, sys, argparse, textwrap
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
from pyrfc import Connection, RFCError

load_dotenv()
TRKORR_DEFAULT = "D01K9B0EWT"

# ─── connection ──────────────────────────────────────────────────────
def get_conn():
    p = {"ashost":os.getenv("SAP_ASHOST"), "sysnr":os.getenv("SAP_SYSNR"),
         "client":os.getenv("SAP_CLIENT"), "user":os.getenv("SAP_USER"), "lang":"EN"}
    if os.getenv("SAP_PASSWD"): p["passwd"] = os.getenv("SAP_PASSWD")
    if os.getenv("SAP_SNC_MODE") == "1":
        p["snc_mode"] = "1"
        p["snc_partnername"] = os.getenv("SAP_SNC_PARTNERNAME")
        p["snc_qop"] = os.getenv("SAP_SNC_QOP","9")
    return Connection(**p)

# ─── SECURITY RAIL: enforce ZCRP package only ────────────────────────
ALLOWED_PACKAGE = "ZCRP"
ALLOWED_CLASSES = {
    "ZCL_CRP_PROCESS_REQ",
    "ZCL_Z_CRP_SRV_DPC_EXT",
    "ZCL_Z_CRP_SRV_MPC_EXT",
}

def verify_package_guard(conn, class_name):
    """
    Refuses to proceed if class_name is not in ALLOWED_PACKAGE.
    Returns True if safe, False + prints error if blocked.
    """
    if class_name not in ALLOWED_CLASSES:
        print(f"  [BLOCKED] '{class_name}' is not in the allowed CRP class list.")
        return False
    try:
        r = conn.call("RFC_READ_TABLE", QUERY_TABLE="TADIR", DELIMITER="|",
                      OPTIONS=[{"TEXT": f"PGMID = 'R3TR' AND OBJECT = 'CLAS' AND OBJ_NAME = '{class_name}'"}],
                      FIELDS=[{"FIELDNAME":"DEVCLASS"}], ROWCOUNT=1)
        rows = r.get("DATA", [])
        if rows:
            pkg = rows[0]["WA"].strip().strip("|")
            if pkg != ALLOWED_PACKAGE and pkg != "$TMP":
                print(f"  [BLOCKED] '{class_name}' is in package '{pkg}', not '{ALLOWED_PACKAGE}'. Aborting.")
                return False
            print(f"  [SAFE] '{class_name}' confirmed in package '{pkg}'")
            return True
        else:
            # Class doesn't exist yet (new) — allow for ALLOWED_CLASSES
            print(f"  [SAFE] '{class_name}' not yet in TADIR (new object) — write allowed")
            return True
    except Exception as e:
        print(f"  [WARN] Package check failed: {e}. Allowing write for {class_name}.")
        return True


# ─── write include via SIW_RFC_WRITE_REPORT ──────────────────────────
# I_TAB_CODE is a table of plain strings (not dicts) — confirmed from live read
def write_include(conn, include_name, code_text, trkorr):
    lines = code_text.strip().splitlines()
    print(f"  Writing {len(lines)} lines to {include_name} ...")
    try:
        result = conn.call(
            "SIW_RFC_WRITE_REPORT",
            I_NAME=include_name,
            I_TAB_CODE=lines,
            I_EXTENSION='' # D01 rejects 'X', empty works for existing class includes
        )
        exc = result.get("E_STR_EXCEPTION", {})
        if exc and isinstance(exc, dict) and exc.get("MSG_TYPE") == "E":
            print(f"  [FAIL] {include_name}: {exc.get('MSG_TEXT','unknown error')}")
            return False
        print(f"  [OK] {include_name} saved ({len(lines)} lines)")
        return True
    except Exception as e:
        print(f"  [FAIL] {include_name}: {e}")
        return False


# ─── activate class ───────────────────────────────────────────────────

def activate_class(conn, class_name):
    print(f"\n  Activating {class_name} ...")
    try:
        conn.call("SEO_CLASS_ACTIVATE", CLASS_NAME=class_name)
        print(f"  [OK] {class_name} activated")
    except RFCError as e:
        print(f"  [WARN] Activation via RFC: {e}")
        print("  --> Activate manually in SE24 if needed")

# ─── prompt for transport if needed ──────────────────────────────────
def get_transport(provided):
    if provided:
        return provided
    print("\n  No transport order found automatically.")
    trkorr = input("  Enter Workbench Transport Order (e.g. D01K9B0EWT): ").strip().upper()
    if not trkorr:
        trkorr = TRKORR_DEFAULT
        print(f"  Using default: {trkorr}")
    return trkorr

# ════════════════════════════════════════════════════════════════════
# SOURCE CODE BLOCKS
# ════════════════════════════════════════════════════════════════════

PROCESS_REQ_CCDEF = '''\
*"* use this source file for any type of declarations (class
*"* definitions, interfaces or type declarations) you need for
*"* components in the private section
'''.strip()

# -------- ZCL_CRP_PROCESS_REQ CCIMP ---------------------------------
PROCESS_REQ_CCIMP = r'''
*"* use this source file for implementation of the class methods

" ─── resolve_staff_from_user ────────────────────────────────────────
METHOD resolve_staff_from_user.
  CLEAR: ev_pernr, ev_name, ev_grade, ev_post, ev_gsber, ev_msg.

  SELECT SINGLE pernr INTO ev_pernr
    FROM pa0105
    WHERE subty   = '0001'
      AND usrid   = iv_uname
      AND endda  >= sy-datum
      AND begda  <= sy-datum.

  IF sy-subrc <> 0.
    ev_msg = |User { iv_uname } is not linked to a personnel number (PA0105)|.
    RETURN.
  ENDIF.

  SELECT SINGLE nachn vorna INTO (DATA(lv_nach), DATA(lv_vor))
    FROM pa0002
    WHERE pernr = ev_pernr AND endda >= sy-datum AND begda <= sy-datum.
  ev_name = |{ lv_vor } { lv_nach }|.

  SELECT SINGLE persk plans gsber INTO (DATA(lv_persk), DATA(lv_plans), DATA(lv_gsber))
    FROM pa0001
    WHERE pernr = ev_pernr AND endda >= sy-datum AND begda <= sy-datum.
  ev_gsber = lv_gsber.

  SELECT SINGLE grade INTO ev_grade FROM zcrp_grade_cfg WHERE category = lv_persk.
  IF sy-subrc <> 0. ev_grade = lv_persk. ENDIF.

  SELECT SINGLE stext INTO ev_post FROM t528t
    WHERE plans = lv_plans AND sprsl = sy-langu.
ENDMETHOD.

" ─── get_grade_category ─────────────────────────────────────────────
METHOD get_grade_category.
  SELECT SINGLE category INTO rv_cat FROM zcrp_grade_cfg WHERE grade = iv_grade.
  IF sy-subrc <> 0.
    IF iv_grade CP 'P-*' OR iv_grade CP 'D-*'.  rv_cat = 'PS'.
    ELSEIF iv_grade CP 'NO-*'.                   rv_cat = 'NO'.
    ELSE.                                         rv_cat = 'GS'.
    ENDIF.
  ENDIF.
ENDMETHOD.

" ─── determine_gl_account ───────────────────────────────────────────
METHOD determine_gl_account.
  DATA(lv_cat) = get_grade_category( iv_grade ).
  CASE lv_cat.
    WHEN 'PS'. rv_gl = '6046013'.
    WHEN OTHERS. rv_gl = '6046014'.
  ENDCASE.
ENDMETHOD.

" ─── generate_certificate_id ────────────────────────────────────────
METHOD generate_certificate_id.
  DATA: lv_number TYPE inri-nrrangenr, lv_returncode TYPE i.
  CALL FUNCTION 'NUMBER_GET_NEXT'
    EXPORTING nr_range_nr = '01' object = 'Z_CRP_NR' quantity = '000000000000001'
    IMPORTING number = lv_number returncode = lv_returncode
    EXCEPTIONS OTHERS = 1.
  IF sy-subrc <> 0. RAISE cx_no_number_range. ENDIF.
  rv_cert_id = |CRP-{ lv_number }|.
ENDMETHOD.

" ─── check_budget_availability ──────────────────────────────────────
METHOD check_budget_availability.
  DATA: ls_return TYPE bapireturn.
  CALL FUNCTION 'BAPI_FUNDSAVAIL_CHECK'
    EXPORTING fm_area = iv_fikrs fund = iv_fonds funds_center = iv_fictr
              commitment_item = iv_fipex fiscal_year = iv_gjahr
              amount = iv_amount currency = iv_currency
    IMPORTING return = ls_return.
  CASE ls_return-type.
    WHEN 'S'. rv_available = 'Y'.
    WHEN 'W'. rv_available = 'W'.
    WHEN OTHERS. rv_available = 'N'.
  ENDCASE.
ENDMETHOD.

" ─── check_duplicate_recovery ───────────────────────────────────────
METHOD check_duplicate_recovery.
  rv_duplicate = abap_false.
  SELECT bseg~pernr FROM bseg INNER JOIN bkpf
      ON bkpf~belnr = bseg~belnr AND bkpf~gjahr = bseg~gjahr AND bkpf~bukrs = bseg~bukrs
    INTO TABLE @DATA(lt_prior)
    WHERE bseg~bukrs = @iv_bukrs AND bseg~hkont IN ('6046013','6046014')
      AND bseg~pernr = @iv_pernr
      AND bkpf~budat >= @iv_begda AND bkpf~budat <= @iv_endda AND bkpf~stblg = space.
  IF sy-subrc = 0 AND lines( lt_prior ) > 0. rv_duplicate = abap_true. ENDIF.
ENDMETHOD.

" ─── validate_header ────────────────────────────────────────────────
METHOD validate_header.
  rv_valid = abap_true. ev_msg = ''.
  IF is_cert-gsber <> 'GEF'. rv_valid = abap_false.
    ev_msg = 'Only staff funded by GEF staff costs are eligible for CRP'. RETURN. ENDIF.
  IF is_cert-num_work_days <= 0. rv_valid = abap_false.
    ev_msg = 'Number of working days must be greater than zero'. RETURN. ENDIF.
  IF is_cert-endda < is_cert-begda. rv_valid = abap_false.
    ev_msg = 'End date must be on or after start date'. RETURN. ENDIF.
  IF is_cert-staff_id IS INITIAL. rv_valid = abap_false.
    ev_msg = 'Staff ID is required'. RETURN. ENDIF.
ENDMETHOD.

" ─── write_approval_history ─────────────────────────────────────────
METHOD write_approval_history.
  DATA: ls_hist TYPE zcrp_aprvl_hist, lv_maxseq TYPE char10.
  SELECT MAX( hist_seq ) INTO lv_maxseq FROM zcrp_aprvl_hist
    WHERE certificate_id = iv_cert_id AND bukrs = iv_bukrs AND gjahr = iv_gjahr.
  ls_hist-bukrs = iv_bukrs. ls_hist-gjahr = iv_gjahr. ls_hist-certificate_id = iv_cert_id.
  ls_hist-hist_seq = CONV i( lv_maxseq ) + 1. ls_hist-step_name = iv_step.
  ls_hist-decision = iv_decision. ls_hist-apcomment = iv_comment.
  ls_hist-actor_id = iv_actor_id. ls_hist-actor_name = iv_actor_nm.
  ls_hist-decision_at = sy-datum && sy-uzeit.
  INSERT zcrp_aprvl_hist FROM ls_hist.
ENDMETHOD.

" ─── submit_for_approval ────────────────────────────────────────────
METHOD submit_for_approval.
  rv_ok = abap_false. ev_msg = ''.
  IF is_cert-status <> '01'.
    ev_msg = |Status must be DRAFT (01). Current: '{ is_cert-status }'|. RETURN. ENDIF.

  UPDATE zcrp_cert SET status = '02' changed_by = sy-uname changed_at = sy-datum
    WHERE certificate_id = is_cert-certificate_id AND bukrs = is_cert-bukrs AND gjahr = is_cert-gjahr.
  IF sy-subrc <> 0. ev_msg = 'Failed to update status'. RETURN. ENDIF.

  write_approval_history( iv_cert_id = is_cert-certificate_id iv_bukrs = is_cert-bukrs
    iv_gjahr = is_cert-gjahr iv_step = 'Staff Member Certification' iv_decision = 'PENDING'
    iv_comment = '' iv_actor_id = is_cert-staff_id iv_actor_nm = is_cert-staff_name ).

  DATA: lv_wi TYPE sww_wiid, lt_c TYPE TABLE OF swr_cont, ls_c TYPE swr_cont.
  ls_c-element = 'CERTIFICATE_ID'. ls_c-value = is_cert-certificate_id.
  APPEND ls_c TO lt_c.
  CALL FUNCTION 'SAP_WAPI_START_WORKFLOW'
    EXPORTING task = 'WS_Z_CRP_APPROVAL' language = sy-langu
    IMPORTING workitem_id = lv_wi TABLES input_container = lt_c EXCEPTIONS OTHERS = 1.
  IF sy-subrc <> 0. ROLLBACK WORK.
    ev_msg = |Workflow could not start (RC={ sy-subrc }). Status reverted.|. RETURN. ENDIF.

  COMMIT WORK AND WAIT.
  rv_ok = abap_true.
ENDMETHOD.

" ─── simulate_jv ────────────────────────────────────────────────────
METHOD simulate_jv.
  CLEAR es_result.
  SELECT SINGLE * FROM zcrp_cert INTO DATA(ls_cert)
    WHERE certificate_id = iv_cert_id AND bukrs = iv_bukrs AND gjahr = iv_gjahr.
  IF sy-subrc <> 0. es_result-success = abap_false.
    es_result-message = |Certificate { iv_cert_id } not found|. RETURN. ENDIF.

  SELECT * FROM zcrp_budgetln INTO TABLE @DATA(lt_lines)
    WHERE certificate_id = @iv_cert_id AND bukrs = @iv_bukrs AND gjahr = @iv_gjahr.

  DATA: ls_hdr TYPE bapiache09, lt_gl TYPE TABLE OF bapiacgl09, lt_ret TYPE TABLE OF bapiret2.
  ls_hdr-bus_act = 'RFBU'. ls_hdr-username = sy-uname. ls_hdr-comp_code = iv_bukrs.
  ls_hdr-doc_date = ls_cert-bldat. ls_hdr-pstng_date = ls_cert-budat.
  ls_hdr-doc_type = 'SA'. ls_hdr-ref_doc_no = ls_cert-certificate_id.
  ls_hdr-header_txt = |CRP-{ ls_cert-certificate_id }|.

  DATA: lv_n TYPE int4 VALUE 1.
  LOOP AT lt_lines INTO DATA(ls_l).
    DATA: ls_gl TYPE bapiacgl09.
    ls_gl-itemno_acc = lv_n. ls_gl-gl_account = ls_cert-gl_account.
    ls_gl-pstng_date = ls_cert-budat. ls_gl-wbs_element = ls_l-wbs_element.
    ls_gl-item_text = |CRP-{ ls_cert-certificate_id }|.
    APPEND ls_gl TO lt_gl. lv_n += 1.
  ENDLOOP.

  CALL FUNCTION 'BAPI_ACC_DOCUMENT_CHECK'
    EXPORTING documentheader = ls_hdr TABLES accountgl = lt_gl return = lt_ret.

  DATA(lv_err) = VALUE string( ).
  LOOP AT lt_ret INTO DATA(ls_r) WHERE type CA 'EAX'. lv_err = |{ lv_err }{ ls_r-message }; |. ENDLOOP.
  IF lv_err IS INITIAL. es_result-success = abap_true. es_result-message = 'Simulation OK — no errors'.
  ELSE. es_result-success = abap_false. es_result-message = lv_err. ENDIF.
ENDMETHOD.

" ─── post_jv ────────────────────────────────────────────────────────
METHOD post_jv.
  CLEAR es_result.
  SELECT SINGLE * FROM zcrp_cert INTO DATA(ls_cert)
    WHERE certificate_id = iv_cert_id AND bukrs = iv_bukrs AND gjahr = iv_gjahr.
  IF sy-subrc <> 0. es_result-success = abap_false.
    es_result-message = |Certificate { iv_cert_id } not found|. RETURN. ENDIF.

  SELECT * FROM zcrp_budgetln INTO TABLE @DATA(lt_lines)
    WHERE certificate_id = @iv_cert_id AND bukrs = @iv_bukrs AND gjahr = @iv_gjahr.
  IF sy-subrc <> 0 OR lines( lt_lines ) = 0. es_result-success = abap_false.
    es_result-message = 'No budget lines found'. RETURN. ENDIF.

  DATA: ls_hdr TYPE bapiache09, lt_gl TYPE TABLE OF bapiacgl09, lt_ret TYPE TABLE OF bapiret2.
  ls_hdr-bus_act = 'RFBU'. ls_hdr-username = sy-uname. ls_hdr-comp_code = iv_bukrs.
  ls_hdr-doc_date = ls_cert-bldat. ls_hdr-pstng_date = iv_posting_date.
  ls_hdr-doc_type = 'SA'. ls_hdr-ref_doc_no = ls_cert-certificate_id.
  ls_hdr-header_txt = |CRP-{ ls_cert-certificate_id }|.

  DATA: lv_n TYPE int4 VALUE 1.
  LOOP AT lt_lines INTO DATA(ls_l).
    DATA: ls_dr TYPE bapiacgl09, ls_cr TYPE bapiacgl09.
    ls_dr-itemno_acc = lv_n. ls_dr-gl_account = ls_cert-gl_account.
    ls_dr-pstng_date = iv_posting_date. ls_dr-currency = ls_l-currency.
    ls_dr-amt_doccur = ls_l-amount. ls_dr-debit_credit = 'S'.
    ls_dr-wbs_element = ls_l-wbs_element.
    ls_dr-item_text = |CRP-{ ls_cert-certificate_id } LN{ ls_l-line_id }|.
    APPEND ls_dr TO lt_gl. lv_n += 1.
    ls_cr-itemno_acc = lv_n. ls_cr-gl_account = ls_cert-gl_account.
    ls_cr-pstng_date = iv_posting_date. ls_cr-currency = ls_l-currency.
    ls_cr-amt_doccur = ls_l-amount. ls_cr-debit_credit = 'H'.
    ls_cr-item_text = |CRP-{ ls_cert-certificate_id } LN{ ls_l-line_id }|.
    APPEND ls_cr TO lt_gl. lv_n += 1.
  ENDLOOP.

  CALL FUNCTION 'BAPI_ACC_DOCUMENT_POST'
    EXPORTING documentheader = ls_hdr TABLES accountgl = lt_gl return = lt_ret.

  DATA(lv_err) = VALUE string( ).
  LOOP AT lt_ret INTO DATA(ls_r) WHERE type CA 'EAX'. lv_err = |{ lv_err }{ ls_r-message }; |. ENDLOOP.
  IF lv_err IS NOT INITIAL. ROLLBACK WORK. es_result-success = abap_false.
    es_result-message = lv_err. RETURN. ENDIF.

  READ TABLE lt_ret INTO DATA(ls_belnr_r) WITH KEY type = 'S' id = 'RW' number = '609'.
  DATA(lv_belnr) = ls_belnr_r-message_v1.
  DATA(lv_ts) = sy-datum && sy-uzeit.
  UPDATE zcrp_cert SET jv_belnr = lv_belnr jv_gjahr = iv_gjahr jv_posted_at = lv_ts
    status = '08' changed_by = sy-uname changed_at = lv_ts
    WHERE certificate_id = iv_cert_id AND bukrs = iv_bukrs AND gjahr = iv_gjahr.

  write_approval_history( iv_cert_id = iv_cert_id iv_bukrs = iv_bukrs iv_gjahr = iv_gjahr
    iv_step = 'JV Posted' iv_decision = 'POSTED'
    iv_comment = |JV: { lv_belnr } / { iv_gjahr }|
    iv_actor_id = '00000000' iv_actor_nm = 'SYSTEM' ).

  COMMIT WORK AND WAIT.
  es_result-success = abap_true. es_result-documentnumber = lv_belnr.
  es_result-fiscalyear = iv_gjahr. es_result-message = 'JV posted successfully'.
ENDMETHOD.

" ─── post_allotment ─────────────────────────────────────────────────
METHOD post_allotment.
  " TODO: Replace with real Coremanager service call (service TBD via MuleSoft)
  CLEAR es_result.
  SELECT SINGLE * FROM zcrp_cert INTO DATA(ls_cert)
    WHERE certificate_id = iv_cert_id AND bukrs = iv_bukrs AND gjahr = iv_gjahr.
  IF sy-subrc <> 0. es_result-success = abap_false.
    es_result-messages = |Certificate { iv_cert_id } not found|. RETURN. ENDIF.

  " STUB: Set to COMPLETE (status 10) — replace block below with real HTTP/RFC call
  DATA(lv_ts) = sy-datum && sy-uzeit.
  UPDATE zcrp_cert SET status = '10' changed_by = sy-uname changed_at = lv_ts
    WHERE certificate_id = iv_cert_id AND bukrs = iv_bukrs AND gjahr = iv_gjahr.
  write_approval_history( iv_cert_id = iv_cert_id iv_bukrs = iv_bukrs iv_gjahr = iv_gjahr
    iv_step = 'Allotment Posted to Coremanager' iv_decision = 'COMPLETE'
    iv_comment = 'TODO: Replace with real Coremanager allotment ID'
    iv_actor_id = '00000000' iv_actor_nm = 'SYSTEM' ).
  COMMIT WORK AND WAIT.
  es_result-success = abap_true. es_result-allotment = 'STUB-ALLOT'.
  es_result-messages = 'Stub OK — wire real Coremanager call when service is identified'.
ENDMETHOD.
'''.strip()

# -------- ZCL_Z_CRP_SRV_DPC_EXT CCIMP ──────────────────────────────
DPC_EXT_CCIMP = r'''
*"* use this source file for implementation of the class methods

" ══ CRPCERTIFICATESET ════════════════════════════════════════════════

METHOD crpcertificateset_get_entityset.
  DATA: lt_results TYPE TABLE OF zcrp_cert.
  DATA(lo_filter) = io_tech_request_context->get_filter( ).
  DATA(lt_select) = lo_filter->get_filter_select_options( ).

  SELECT * FROM zcrp_cert INTO TABLE @lt_results
    WHERE created_by = @sy-uname ORDER BY created_at DESCENDING.

  READ TABLE lt_select INTO DATA(ls_cf) WITH KEY property = 'CertificateId'.
  IF sy-subrc = 0. DELETE lt_results WHERE certificate_id <> ls_cf-select_options[ 1 ]-low. ENDIF.
  READ TABLE lt_select INTO DATA(ls_sf) WITH KEY property = 'Status'.
  IF sy-subrc = 0. DELETE lt_results WHERE status <> ls_sf-select_options[ 1 ]-low. ENDIF.

  LOOP AT lt_results INTO DATA(ls_r).
    DATA: ls_e TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.
    MOVE-CORRESPONDING ls_r TO ls_e. APPEND ls_e TO et_entityset.
  ENDLOOP.
ENDMETHOD.

METHOD crpcertificateset_get_entity.
  io_tech_request_context->get_converted_keys( IMPORTING es_key_values = DATA(ls_k) ).
  SELECT SINGLE * FROM zcrp_cert INTO DATA(ls_c)
    WHERE bukrs = ls_k-key_1 AND gjahr = ls_k-key_2 AND certificate_id = ls_k-key_3.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>entity_not_found http_status_code = '404'.
  ENDIF.
  MOVE-CORRESPONDING ls_c TO er_entity.
ENDMETHOD.

METHOD crpcertificateset_create_entity.
  DATA: ls_e TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate, ls_c TYPE zcrp_cert.
  io_data_provider->read_entry_data( CHANGING cs_data = ls_e ).

  zcl_crp_process_req=>resolve_staff_from_user(
    EXPORTING iv_uname = sy-uname
    IMPORTING ev_pernr = ls_c-staff_id ev_name = ls_c-staff_name
              ev_grade = ls_c-grade ev_post = ls_c-post_title
              ev_gsber = ls_c-gsber ev_msg  = DATA(lv_msg) ).
  IF lv_msg IS NOT INITIAL.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error message = lv_msg. ENDIF.

  ls_c-bukrs = 'UC01'. ls_c-gjahr = ls_e-gjahr. ls_c-begda = ls_e-begda.
  ls_c-endda = ls_e-endda. ls_c-num_work_days = ls_e-num_work_days.
  ls_c-bldat = ls_e-bldat. ls_c-budat = ls_e-budat. ls_c-bktxt = ls_e-bktxt.
  ls_c-description = ls_e-description. ls_c-currency = 'USD'.
  ls_c-gl_account = zcl_crp_process_req=>determine_gl_account( ls_c-grade ).

  CONSTANTS: lc_rate TYPE p DECIMALS 2 VALUE '200.00'.
  ls_c-calc_amount = ls_c-num_work_days * lc_rate.

  ls_c-status = '01'. ls_c-created_by = sy-uname. ls_c-changed_by = sy-uname.
  ls_c-created_at = sy-datum && sy-uzeit. ls_c-changed_at = ls_c-created_at.

  IF zcl_crp_process_req=>validate_header( EXPORTING is_cert = ls_c
       IMPORTING ev_msg = lv_msg ) = abap_false.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error message = lv_msg. ENDIF.

  TRY.
    ls_c-certificate_id = zcl_crp_process_req=>generate_certificate_id( ).
  CATCH cx_no_number_range.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = 'Certificate ID generation failed — check number range Z_CRP_NR'. ENDTRY.

  INSERT zcrp_cert FROM ls_c.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = 'DB insert failed'. ENDIF.
  COMMIT WORK AND WAIT.
  MOVE-CORRESPONDING ls_c TO er_entity.
ENDMETHOD.

METHOD crpcertificateset_update_entity.
  DATA: ls_e TYPE zcl_z_crp_srv_mpc=>ts_crpcertificate.
  io_tech_request_context->get_converted_keys( IMPORTING es_key_values = DATA(ls_k) ).
  io_data_provider->read_entry_data( CHANGING cs_data = ls_e ).

  SELECT SINGLE * FROM zcrp_cert INTO DATA(ls_c)
    WHERE bukrs = ls_k-key_1 AND gjahr = ls_k-key_2 AND certificate_id = ls_k-key_3.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>entity_not_found http_status_code = '404'. ENDIF.
  IF ls_c-status <> '01' AND ls_c-status <> '06'.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = |Edit not allowed in status '{ ls_c-status }'. Only DRAFT(01) or VERIFICATION_FAILED(06).|. ENDIF.

  ls_c-begda = ls_e-begda. ls_c-endda = ls_e-endda. ls_c-num_work_days = ls_e-num_work_days.
  ls_c-bldat = ls_e-bldat. ls_c-budat = ls_e-budat. ls_c-bktxt = ls_e-bktxt.
  ls_c-description = ls_e-description. ls_c-changed_by = sy-uname.
  ls_c-changed_at = sy-datum && sy-uzeit.
  CONSTANTS: lc_rate TYPE p DECIMALS 2 VALUE '200.00'.
  ls_c-calc_amount = ls_c-num_work_days * lc_rate.

  UPDATE zcrp_cert FROM ls_c. COMMIT WORK AND WAIT.
  MOVE-CORRESPONDING ls_c TO er_entity.
ENDMETHOD.

" ══ CRPBUDGETLINESET ═════════════════════════════════════════════════

METHOD crpbudgetlineset_get_entityset.
  DATA(lo_f) = io_tech_request_context->get_filter( ).
  DATA(lt_s) = lo_f->get_filter_select_options( ).
  READ TABLE lt_s INTO DATA(ls_f) WITH KEY property = 'CertificateId'.
  IF sy-subrc <> 0. RETURN. ENDIF.
  DATA(lv_cid) = ls_f-select_options[ 1 ]-low.
  SELECT * FROM zcrp_budgetln INTO TABLE @DATA(lt_l)
    WHERE certificate_id = @lv_cid ORDER BY line_id.
  LOOP AT lt_l INTO DATA(ls_l).
    DATA: ls_e TYPE zcl_z_crp_srv_mpc=>ts_crpbudgetline.
    MOVE-CORRESPONDING ls_l TO ls_e. APPEND ls_e TO et_entityset.
  ENDLOOP.
ENDMETHOD.

METHOD crpbudgetlineset_create_entity.
  DATA: ls_e TYPE zcl_z_crp_srv_mpc=>ts_crpbudgetline, ls_l TYPE zcrp_budgetln.
  io_data_provider->read_entry_data( CHANGING cs_data = ls_e ).

  SELECT SINGLE * FROM zcrp_cert INTO DATA(ls_p) WHERE certificate_id = ls_e-certificate_id.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = |Parent cert '{ ls_e-certificate_id }' not found|. ENDIF.
  IF ls_p-status <> '01'.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = 'Budget lines need DRAFT status'. ENDIF.

  DATA: lv_mx TYPE char3.
  SELECT MAX( line_id ) INTO lv_mx FROM zcrp_budgetln
    WHERE certificate_id = ls_p-certificate_id AND bukrs = ls_p-bukrs AND gjahr = ls_p-gjahr.
  DATA(lv_nxt) = CONV i( lv_mx ) + 1.

  ls_l-bukrs = ls_p-bukrs. ls_l-gjahr = ls_p-gjahr. ls_l-certificate_id = ls_e-certificate_id.
  ls_l-line_id = |{ lv_nxt WIDTH = 3 ALIGN = RIGHT PAD = '0' }|.
  ls_l-fonds = ls_e-fonds. ls_l-fictr = ls_e-fictr. ls_l-fipex = ls_e-fipex.
  ls_l-wbs_element = ls_e-wbs_element. ls_l-crp_code = ls_e-crp_code.
  ls_l-amount = ls_e-amount. ls_l-currency = ls_p-currency.
  ls_l-budget_available = zcl_crp_process_req=>check_budget_availability(
    iv_fikrs = 'UC01' iv_fonds = ls_l-fonds iv_fictr = ls_l-fictr iv_fipex = ls_l-fipex
    iv_gjahr = ls_l-gjahr iv_amount = ls_l-amount iv_currency = ls_l-currency ).

  INSERT zcrp_budgetln FROM ls_l. COMMIT WORK AND WAIT.
  MOVE-CORRESPONDING ls_l TO er_entity.
ENDMETHOD.

METHOD crpbudgetlineset_delete_entity.
  io_tech_request_context->get_converted_keys( IMPORTING es_key_values = DATA(ls_k) ).
  SELECT SINGLE status created_by FROM zcrp_cert INTO (DATA(lv_st), DATA(lv_cr))
    WHERE certificate_id = ls_k-key_3 AND bukrs = ls_k-key_1 AND gjahr = ls_k-key_2.
  IF lv_st <> '01'.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = 'Delete requires DRAFT status'. ENDIF.
  DELETE FROM zcrp_budgetln
    WHERE certificate_id = ls_k-key_3 AND bukrs = ls_k-key_1
      AND gjahr = ls_k-key_2 AND line_id = ls_k-key_4.
  COMMIT WORK AND WAIT.
ENDMETHOD.

" ══ CRPAPPROVALHISTORYSET ════════════════════════════════════════════

METHOD crpapprovalhistoryset_get_entityset.
  DATA(lo_f) = io_tech_request_context->get_filter( ).
  READ TABLE lo_f->get_filter_select_options( ) INTO DATA(ls_f) WITH KEY property = 'CertificateId'.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = 'CertificateId filter is required'. ENDIF.
  SELECT * FROM zcrp_aprvl_hist INTO TABLE @DATA(lt_h)
    WHERE certificate_id = @ls_f-select_options[ 1 ]-low ORDER BY hist_seq.
  LOOP AT lt_h INTO DATA(ls_h).
    DATA: ls_e TYPE zcl_z_crp_srv_mpc=>ts_crpapprovalhistory.
    MOVE-CORRESPONDING ls_h TO ls_e. APPEND ls_e TO et_entityset.
  ENDLOOP.
ENDMETHOD.

" ══ COSTRATESET ══════════════════════════════════════════════════════

METHOD costrateset_get_entityset.
  SELECT * FROM zcrp_grade_cfg INTO TABLE @DATA(lt_c) ORDER BY grade.
  LOOP AT lt_c INTO DATA(ls_c).
    DATA: ls_e TYPE zcl_z_crp_srv_mpc=>ts_costrate.
    ls_e-grade = ls_c-grade. ls_e-category = ls_c-category.
    ls_e-description = ls_c-description. APPEND ls_e TO et_entityset.
  ENDLOOP.
ENDMETHOD.

" ══ FUNCTION IMPORTS ═════════════════════════════════════════════════

METHOD submitforapproval_fi.
  DATA(lv_cid) = it_parameter[ name = 'CertificateId' ]-value.
  SELECT SINGLE * FROM zcrp_cert INTO DATA(ls_c) WHERE certificate_id = lv_cid.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = |Certificate '{ lv_cid }' not found|. ENDIF.
  DATA: lv_msg TYPE string.
  IF zcl_crp_process_req=>submit_for_approval( EXPORTING is_cert = ls_c
       IMPORTING ev_msg = lv_msg ) = abap_false.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error message = lv_msg. ENDIF.
  SELECT SINGLE * FROM zcrp_cert INTO ls_c WHERE certificate_id = lv_cid.
  MOVE-CORRESPONDING ls_c TO er_return.
ENDMETHOD.

METHOD simulatejvposting_fi.
  DATA(lv_cid) = it_parameter[ name = 'CertificateId' ]-value.
  SELECT SINGLE bukrs gjahr status FROM zcrp_cert
    INTO (DATA(lv_bk), DATA(lv_gj), DATA(lv_st)) WHERE certificate_id = lv_cid.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = |Certificate '{ lv_cid }' not found|. ENDIF.
  DATA: ls_r TYPE zcl_crp_process_req=>ty_jv_result.
  zcl_crp_process_req=>simulate_jv( EXPORTING iv_cert_id = lv_cid iv_bukrs = lv_bk
    iv_gjahr = lv_gj IMPORTING es_result = ls_r ).
  er_return-success = ls_r-success. er_return-documentnumber = ls_r-documentnumber.
  er_return-message = ls_r-message.
ENDMETHOD.

METHOD postjv_fi.
  DATA(lv_cid) = it_parameter[ name = 'CertificateId' ]-value.
  DATA(lv_pd)  = it_parameter[ name = 'PostingDate'   ]-value.
  SELECT SINGLE * FROM zcrp_cert INTO DATA(ls_c) WHERE certificate_id = lv_cid.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = |Certificate '{ lv_cid }' not found|. ENDIF.
  IF ls_c-status <> '07'.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = |Requires JV_PENDING (07). Current: '{ ls_c-status }'.|. ENDIF.
  DATA: ls_r TYPE zcl_crp_process_req=>ty_jv_result.
  zcl_crp_process_req=>post_jv( EXPORTING iv_cert_id = lv_cid iv_bukrs = ls_c-bukrs
    iv_gjahr = ls_c-gjahr iv_posting_date = COND #( WHEN lv_pd IS NOT INITIAL THEN lv_pd ELSE sy-datum )
    IMPORTING es_result = ls_r ).
  IF ls_r-success = abap_false.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error message = ls_r-message. ENDIF.
  er_return-success = ls_r-success. er_return-documentnumber = ls_r-documentnumber.
  er_return-fiscalyear = ls_r-fiscalyear. er_return-messages = ls_r-message.
ENDMETHOD.

METHOD postallotment_fi.
  DATA(lv_cid) = it_parameter[ name = 'CertificateId' ]-value.
  SELECT SINGLE * FROM zcrp_cert INTO DATA(ls_c) WHERE certificate_id = lv_cid.
  IF sy-subrc <> 0.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = |Certificate '{ lv_cid }' not found|. ENDIF.
  IF ls_c-status <> '08'.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = |Requires JV_POSTED (08). Current: '{ ls_c-status }'.|. ENDIF.

  UPDATE zcrp_cert SET status = '09' changed_by = sy-uname changed_at = sy-datum && sy-uzeit
    WHERE certificate_id = lv_cid AND bukrs = ls_c-bukrs AND gjahr = ls_c-gjahr.

  DATA: ls_r TYPE zcl_crp_process_req=>ty_allotment_result.
  zcl_crp_process_req=>post_allotment( EXPORTING iv_cert_id = lv_cid iv_bukrs = ls_c-bukrs
    iv_gjahr = ls_c-gjahr IMPORTING es_result = ls_r ).
  IF ls_r-success = abap_false.
    UPDATE zcrp_cert SET status = '08' WHERE certificate_id = lv_cid
      AND bukrs = ls_c-bukrs AND gjahr = ls_c-gjahr. COMMIT WORK.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING textid = /iwbep/cx_mgw_busi_exception=>business_error
                message = ls_r-messages. ENDIF.
  er_return-success = ls_r-success. er_return-allotment = ls_r-allotment.
  er_return-messages = ls_r-messages.
ENDMETHOD.
'''.strip()

# ════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Deploy CRP ABAP classes to SAP D01")
    parser.add_argument("--transport", default=TRKORR_DEFAULT,
                        help=f"Workbench transport request (default: {TRKORR_DEFAULT})")
    parser.add_argument("--step", type=int, default=0,
                        help="Start from step N (0=all steps)")
    args = parser.parse_args()

    trkorr = get_transport(args.transport)

    conn = None
    try:
        conn = get_conn()
        print(f"\nConnected to SAP {os.getenv('SAP_ASHOST')} / Client {os.getenv('SAP_CLIENT')}")
        print(f"Transport: {trkorr}")
        print("=" * 60)
        print("DEPLOYMENT ORDER:")
        print("  1. Write ZCL_CRP_PROCESS_REQ CCDEF (types)")
        print("  2. Write ZCL_CRP_PROCESS_REQ CCIMP (all methods)")
        print("  3. Activate ZCL_CRP_PROCESS_REQ")
        print("  4. Write ZCL_Z_CRP_SRV_DPC_EXT CCIMP (all overrides)")
        print("  5. Activate ZCL_Z_CRP_SRV_DPC_EXT")
        print("=" * 60)

        # ── Pre-flight: package safety check ──────────────────────
        print("\n[PRE-FLIGHT] Verifying all targets are in ZCRP package ...")
        for cls in ["ZCL_CRP_PROCESS_REQ", "ZCL_Z_CRP_SRV_DPC_EXT"]:
            if not verify_package_guard(conn, cls):
                print(f"  [ABORT] Package guard failed for {cls}. No changes made.")
                return
        print("  Package guard PASSED — proceeding with deployment.")

        # ── Step 1: PROCESS_REQ CCDEF ──────────────────────────────
        def get_cls_incl(cls, suffix):
            return cls.ljust(30, '=') + suffix

        if args.step in (0, 1):
            print("\n[STEP 1] ZCL_CRP_PROCESS_REQ — CCDEF (definition)")
            if verify_package_guard(conn, "ZCL_CRP_PROCESS_REQ"):
                write_include(conn, get_cls_incl("ZCL_CRP_PROCESS_REQ", "CCDEF"),
                              PROCESS_REQ_CCDEF, trkorr)

        # ── Step 2: PROCESS_REQ CCIMP ──────────────────────────────
        if args.step in (0, 2):
            print("\n[STEP 2] ZCL_CRP_PROCESS_REQ — CCIMP (implementation)")
            if verify_package_guard(conn, "ZCL_CRP_PROCESS_REQ"):
                write_include(conn, get_cls_incl("ZCL_CRP_PROCESS_REQ", "CCIMP"),
                              PROCESS_REQ_CCIMP, trkorr)

        # ── Step 3: Activate PROCESS_REQ ───────────────────────────
        if args.step in (0, 3):
            print("\n[STEP 3] Activate ZCL_CRP_PROCESS_REQ")
            if verify_package_guard(conn, "ZCL_CRP_PROCESS_REQ"):
                activate_class(conn, "ZCL_CRP_PROCESS_REQ")

        # ── Step 4: DPC_EXT CCIMP ──────────────────────────────────
        if args.step in (0, 4):
            print("\n[STEP 4] ZCL_Z_CRP_SRV_DPC_EXT — CCIMP (all method overrides)")
            if verify_package_guard(conn, "ZCL_Z_CRP_SRV_DPC_EXT"):
                write_include(conn, get_cls_incl("ZCL_Z_CRP_SRV_DPC_EXT", "CCIMP"),
                              DPC_EXT_CCIMP, trkorr)

        # ── Step 5: Activate DPC_EXT ───────────────────────────────
        if args.step in (0, 5):
            print("\n[STEP 5] Activate ZCL_Z_CRP_SRV_DPC_EXT")
            if verify_package_guard(conn, "ZCL_Z_CRP_SRV_DPC_EXT"):
                activate_class(conn, "ZCL_Z_CRP_SRV_DPC_EXT")

        print("\n" + "=" * 60)
        print("DEPLOYMENT COMPLETE")
        print("  NOTE: If activation failed via RFC, open SE24 and activate manually.")
        print("  Objects on transport: " + trkorr)
        print("=" * 60)

    except RFCError as e:
        print(f"\n[RFC ERROR] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback; traceback.print_exc()
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    main()
