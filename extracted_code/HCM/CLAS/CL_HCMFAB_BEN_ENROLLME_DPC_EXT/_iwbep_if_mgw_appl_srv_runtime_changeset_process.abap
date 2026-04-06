METHOD /iwbep/if_mgw_appl_srv_runtime~changeset_process.

  DATA: ls_changeset_request         TYPE /iwbep/if_mgw_appl_types=>ty_s_changeset_request,
        ls_changeset_response        TYPE /iwbep/if_mgw_appl_types=>ty_s_changeset_response,
        ls_changeset_response_pcheck TYPE /iwbep/if_mgw_appl_types=>ty_s_changeset_response,
        ls_offer                     TYPE cl_hcmfab_ben_enrollme_mpc=>ts_offer,
        ls_event                     TYPE cl_hcmfab_ben_enrollme_mpc=>ts_benefitevent,
        ls_beneficiary               TYPE cl_hcmfab_ben_enrollme_mpc=>ts_beneficiary,
        ls_dependent                 TYPE cl_hcmfab_ben_enrollme_mpc=>ts_dependent,
        ls_investment                TYPE cl_hcmfab_ben_enrollme_mpc=>ts_investment,
        ls_paycheck_form             TYPE cl_hcmfab_ben_enrollme_mpc=>ts_paychecksimulation,
        ls_enrl_reason               TYPE rpbenenrollmentreason,
        lt_offer_add                 TYPE cl_hcmfab_ben_enrollme_mpc=>tt_offer,
        lt_offer_del                 TYPE cl_hcmfab_ben_enrollme_mpc=>tt_offer,
        lt_beneficiary               TYPE cl_hcmfab_ben_enrollme_mpc=>tt_beneficiary,
        lt_dependent                 TYPE cl_hcmfab_ben_enrollme_mpc=>tt_dependent,
        lt_investment                TYPE cl_hcmfab_ben_enrollme_mpc=>tt_investment,
        lt_error                     TYPE hrben00err_ess,
        lt_cons_error                TYPE hrben00err_ess_det_consistency,
        ls_cons_error                TYPE rpbenerr_ess_det_consistency,
        ls_error                     TYPE rpbenerr,
        lo_context                   TYPE REF TO /iwbep/if_mgw_req_entity_c,
        lv_entity_type               TYPE string,
        lv_operation                 TYPE char1,
        lv_subrc                     TYPE sy-subrc,
        lv_locked                    TYPE boole_d,
        lv_count                     TYPE i,
        lv_pernr                     TYPE pernr_d,
        lv_current_index             TYPE sytabix,     "Note 2820848
        lx_exception                 TYPE REF TO cx_hcmfab_common.

  LOOP AT it_changeset_request INTO ls_changeset_request.
    lo_context ?= ls_changeset_request-request_context.
    lv_entity_type = lo_context->get_entity_type_name( ).
    IF lv_entity_type = 'Offer'.

      ls_changeset_request-entry_provider->read_entry_data( IMPORTING es_data = ls_offer ).
      lv_operation = ls_offer-ui_action.

      IF ls_offer-opt_out = c_true.
        APPEND ls_offer TO lt_offer_del.
      ELSE.
        APPEND ls_offer TO lt_offer_add.
      ENDIF.

      lv_count = lv_count + 1.
      ls_changeset_response-operation_no = lv_count.

      copy_data_to_ref(
        EXPORTING
          is_data = ls_offer
        CHANGING
          cr_data = ls_changeset_response-entity_data ).

      APPEND ls_changeset_response TO ct_changeset_response.
      CLEAR ls_changeset_response.
      CLEAR ls_offer.

    ELSEIF lv_entity_type = 'Beneficiary'.

      ls_changeset_request-entry_provider->read_entry_data( IMPORTING es_data = ls_beneficiary ).

      APPEND ls_beneficiary TO lt_beneficiary.

      lv_count = lv_count + 1.
      ls_changeset_response-operation_no = lv_count.

      copy_data_to_ref(
        EXPORTING
          is_data = ls_beneficiary
        CHANGING
          cr_data = ls_changeset_response-entity_data ).

      APPEND ls_changeset_response TO ct_changeset_response.
      CLEAR ls_changeset_response.
      CLEAR ls_beneficiary.

    ELSEIF lv_entity_type = 'Dependent'.

      ls_changeset_request-entry_provider->read_entry_data( IMPORTING es_data = ls_dependent ).

      APPEND ls_dependent TO lt_dependent.

      lv_count = lv_count + 1.
      ls_changeset_response-operation_no = lv_count.

      copy_data_to_ref(
        EXPORTING
          is_data = ls_dependent
        CHANGING
          cr_data = ls_changeset_response-entity_data ).

      APPEND ls_changeset_response TO ct_changeset_response.
      CLEAR ls_changeset_response.
      CLEAR ls_dependent.

    ELSEIF lv_entity_type = 'Investment'.

      ls_changeset_request-entry_provider->read_entry_data( IMPORTING es_data = ls_investment ).

      APPEND ls_investment TO lt_investment.

      lv_count = lv_count + 1.
      ls_changeset_response-operation_no = lv_count.

      copy_data_to_ref(
        EXPORTING
          is_data = ls_investment
        CHANGING
          cr_data = ls_changeset_response-entity_data ).

      APPEND ls_changeset_response TO ct_changeset_response.
      CLEAR ls_changeset_response.
      CLEAR ls_investment.


    ELSEIF lv_entity_type = 'BenefitEvent'.

      ls_changeset_request-entry_provider->read_entry_data( IMPORTING es_data = ls_event ).

      lv_count = lv_count + 1.
      ls_changeset_response-operation_no = lv_count.

      copy_data_to_ref(
        EXPORTING
          is_data = ls_event
        CHANGING
          cr_data = ls_changeset_response-entity_data ).

      APPEND ls_changeset_response TO ct_changeset_response.
      CLEAR ls_changeset_response.

    ENDIF.

  ENDLOOP.
  CLEAR:ls_offer.
  READ TABLE lt_offer_add INTO ls_offer INDEX 1.
  IF sy-subrc NE 0.
    READ TABLE lt_offer_del INTO ls_offer INDEX 1.
  ENDIF.
  lv_pernr = ls_offer-pernr.
  MOVE-CORRESPONDING ls_event TO ls_enrl_reason.
  ls_enrl_reason-begda =  ls_event-enrol_begda. "Note 2820848
  ls_enrl_reason-endda =  ls_event-enrol_endda.
  TRY.
* Check if Pernr is valid or not
      go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).
    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
      is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
      iv_entity   = 'Offer'
      ).
  ENDTRY.
  CALL FUNCTION 'HR_BEN_ESS_RFC_INIT_SELECTION'
    EXPORTING
      selected_enroll_reason = ls_enrl_reason
      datum                  = sy-datum
    IMPORTING
      error_table            = lt_error
      subrc                  = lv_subrc.

  IF lv_operation = 'S' AND lt_error IS NOT INITIAL.
    raise_exceptions(
    EXPORTING it_messages = lt_error
    ).
    RETURN.
  ENDIF.

  add_plan_to_selection(
    EXPORTING
      it_offer       = lt_offer_add
      it_dependent   = lt_dependent
      it_investment  = lt_investment
      it_beneficiary = lt_beneficiary
      iv_operation   = lv_operation
    IMPORTING
      et_error_table = lt_error
  ).

"Note 2820848
  SORT lt_offer_add by pltyp.
  CLEAR ls_offer.
  LOOP AT lt_offer_del INTO ls_offer.
    lv_current_index = sy-tabix.
    READ TABLE lt_offer_add TRANSPORTING NO FIELDS WITH KEY pltyp = ls_offer-pltyp BINARY SEARCH.
    IF sy-subrc = 0.
       DELETE lt_offer_del INDEX lv_current_index.
    ENDIF.
  ENDLOOP.
  IF lt_offer_del IS NOT INITIAL.
   remove_plan_from_selection( it_offer = lt_offer_del ).
  ENDIF.  "Note 2820848
*  remove_plan_from_selection( it_offer = lt_offer_del ).

  IF lv_operation = 'P'.        "" Paycheck simulation

    CALL FUNCTION 'HR_BEN_ESS_RFC_SIMUL_PAYCHECK'
      IMPORTING
        pdf_xstring        = ls_paycheck_form-file_content
        consistency_errors = lt_cons_error
        error_table        = lt_error.

    IF lt_cons_error IS NOT INITIAL.
      LOOP AT lt_cons_error INTO ls_cons_error.
        MOVE-CORRESPONDING ls_cons_error TO ls_error.
        APPEND ls_error TO lt_error.
        CLEAR ls_error.
      ENDLOOP.
    ENDIF.

    update_paycheck_data(
      EXPORTING
        iv_pernr     = lv_pernr
        iv_content   = ls_paycheck_form-file_content
    ).

  ELSEIF lv_operation = 'R'.    "" Review

    CALL FUNCTION 'HR_BEN_ESS_RFC_CHK_CONSISTENCY'
      IMPORTING
        consistency_errors = lt_cons_error
        error_table        = lt_error.

    IF lt_cons_error IS NOT INITIAL.
      LOOP AT lt_cons_error INTO ls_cons_error.
        MOVE-CORRESPONDING ls_cons_error TO ls_error.
        APPEND ls_error TO lt_error.
        CLEAR ls_error.
      ENDLOOP.
    ENDIF.

  ELSEIF lv_operation = 'S'.    "" Save

    CALL FUNCTION 'HR_BEN_ESS_RFC_CHK_CONSISTENCY'
      IMPORTING
        consistency_errors = lt_cons_error
        subrc              = lv_subrc
        error_table        = lt_error.

    IF lt_cons_error IS NOT INITIAL.
      LOOP AT lt_cons_error INTO ls_cons_error.
        MOVE-CORRESPONDING ls_cons_error TO ls_error.
        APPEND ls_error TO lt_error.
        CLEAR ls_error.
      ENDLOOP.
    ENDIF.

    IF lt_error IS INITIAL.

      CALL FUNCTION 'HR_BEN_ESS_RFC_ENROLL'
        IMPORTING
          error_table = lt_error.

    ENDIF.

    IF lt_error IS INITIAL.
      process_eoi_mail( it_offer = lt_offer_add ).
    ENDIF.


    """ Delete paycheck related content from temp. table
    update_paycheck_data(
      EXPORTING
        iv_pernr   = lv_pernr
    ).

  ENDIF.

  IF lt_error IS NOT INITIAL.
    raise_exceptions(
    EXPORTING it_messages = lt_error
    ).
  ENDIF.

ENDMETHOD.
