METHOD spendingset_get_entityset.
  DATA: ls_filter_range TYPE /iwbep/s_cod_select_option,
        ls_filter       TYPE /iwbep/s_mgw_select_option.

  DATA: lt_fsacontrib_trans TYPE hrben00_fsacontrib_trans,
        lt_error_table TYPE hrben00err_ess,
        ls_selected_enroll_reason TYPE rpbenenrollmentreason,
        ls_processed_plan TYPE rpben_gen_plan_info,
        ls_fsacontrib_trans TYPE rpben_fsacontrib_trans,
        lv_subrc TYPE sysubrc,
        lv_event TYPE string,
        lv_etype TYPE string,
        lv_datum TYPE sydatum.

  DATA: lt_entityset TYPE cl_hcmfab_ben_enrollme_mpc=>tt_spending,
        ls_entityset TYPE cl_hcmfab_ben_enrollme_mpc=>ts_spending,
        lx_badi_error       TYPE REF TO cx_hcmfab_benefits_enrollment,
        lx_exception        TYPE REF TO cx_static_check.
  DATA : lt_enroll_event         TYPE hrben00enrollmentreason.  "2904166RAJUG

* Check if the supplied filter is supported by standard gateway runtime process
  IF  iv_filter_string   IS NOT INITIAL
      AND it_filter_select_options IS INITIAL.
*    " If the string of the Filter System Query Option is not automatically converted
*    " filter option table (lt_filter_select_options), then the filtering combination is not supported
*    " Log message in the application log
    me->/iwbep/if_sb_dpc_comm_services~log_message(
      EXPORTING
        iv_msg_type   = 'E'
        iv_msg_id     = '/IWBEP/MC_SB_DPC_ADM'
        iv_msg_number = 025 ).
*    " Raise Exception
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_tech_exception
      EXPORTING
        textid = /iwbep/cx_mgw_tech_exception=>internal_error.
  ENDIF.

  CLEAR:ls_processed_plan,lv_event,lv_etype,ls_selected_enroll_reason,lv_subrc,lt_error_table.
* Get the filter data
  LOOP AT it_filter_select_options INTO ls_filter.
    READ TABLE ls_filter-select_options INTO ls_filter_range INDEX 1.
    IF sy-subrc = 0 AND
       ls_filter_range-sign EQ 'I' AND ls_filter_range-option EQ 'EQ'.
      CASE ls_filter-property.
        WHEN 'EmployeeNumber'.
          ls_processed_plan-pernr = ls_filter_range-low.
        WHEN 'Event'.
          lv_event = ls_filter_range-low.
        WHEN 'EventType'.
          lv_etype = ls_filter_range-low.
        WHEN 'BenefitArea'.
          ls_processed_plan-barea = ls_filter_range-low.
        WHEN 'BenefitCategory'.
          ls_processed_plan-bpcat = ls_filter_range-low.
        WHEN 'PlanType'.
          ls_processed_plan-pltyp = ls_filter_range-low.
        WHEN 'Plan'.
          ls_processed_plan-bplan = ls_filter_range-low.
        WHEN 'BeginDate'.
          ls_processed_plan-begda = ls_filter_range-low.
        WHEN 'EndDate'.
          ls_processed_plan-endda = ls_filter_range-low.
        WHEN 'LockIndicator'.
          ls_processed_plan-sprps = ls_filter_range-low.
        WHEN OTHERS.
      ENDCASE.
    ENDIF.
  ENDLOOP.

  TRY.
* Check if Pernr is valid or not
      go_employee_api->do_employeenumber_validation( iv_pernr          = ls_processed_plan-pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).

*      MOVE-CORRESPONDING ls_processed_plan TO ls_selected_enroll_reason.   "2904166RAJUG
*      ls_selected_enroll_reason-event = lv_event.
*      ls_selected_enroll_reason-enrty = lv_etype.
      lv_datum = sy-datum.
      CALL FUNCTION 'HR_BEN_ESS_RFC_ENRO_REASONS'
        EXPORTING
          pernr              = ls_processed_plan-pernr
          datum              = lv_datum
        IMPORTING
          enrollment_reasons = lt_enroll_event
          error_table        = lt_error_table
          subrc              = lv_subrc.

      READ TABLE lt_enroll_event INTO ls_selected_enroll_reason WITH KEY  event = lv_event enrty = lv_etype.  "2904166RAJUG
* Fill global tables
      CALL FUNCTION 'HR_BEN_ESS_GET_OFFER'
        EXPORTING
          selected_enroll_reason = ls_selected_enroll_reason
          datum                  = lv_datum
          reaction               = 'N'
        IMPORTING
          subrc                  = lv_subrc
        TABLES
          error_table            = lt_error_table.
      CHECK lv_subrc EQ 0.
      CLEAR:lt_fsacontrib_trans,lv_subrc,lt_error_table.
* Fetching the spending data
      CASE ls_processed_plan-bpcat.
        WHEN c_spendings_plan.     "Spendings
          CALL FUNCTION 'HR_BEN_ESS_SCREEN_CTRL_SPENDA'
            EXPORTING
              processed_plan   = ls_processed_plan
              reaction         = c_reaction_n
            IMPORTING
              fsacontrib_trans = lt_fsacontrib_trans
              subrc            = lv_subrc
              error_table      = lt_error_table.
      ENDCASE.
      IF lv_subrc NE 0.
        me->raise_exceptions(
      EXPORTING
        it_messages = lt_error_table
        iv_entity_name = iv_entity_name
       ).
      ELSE.
        CLEAR lt_entityset.
        LOOP AT lt_fsacontrib_trans INTO ls_fsacontrib_trans.
          MOVE-CORRESPONDING ls_processed_plan TO ls_entityset.
          MOVE-CORRESPONDING ls_fsacontrib_trans TO ls_entityset.
          calculate_per_period_cntr(
            EXPORTING
                 iv_pernr           =  ls_processed_plan-pernr
                 iv_datum           =  lv_datum
                 iv_contrib_amount  =  ls_fsacontrib_trans-camnt
            IMPORTING
                 ev_cntr_amt_per_period = ls_entityset-perperiodcamnt
           ).
          ls_entityset-event = lv_event.
          ls_entityset-event_type = lv_etype.
          me->enrich_spending( CHANGING spendingentity = ls_entityset ).
          APPEND ls_entityset TO lt_entityset.
        ENDLOOP.

        et_entityset = lt_entityset.
      ENDIF.
    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
    CATCH cx_hcmfab_benefits_enrollment INTO lx_badi_error.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_badi_error )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.
ENDMETHOD.
