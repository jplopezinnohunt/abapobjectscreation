METHOD execute_action_spending_check.
  DATA : lt_check_error TYPE hrben00err_ess_det_consistency,
       lt_error_table TYPE hrben00err_ess,
       ls_param       LIKE LINE OF it_parameter,
       ls_check_error TYPE rpbenerr_ess_det_consistency,
       ls_error       TYPE rpbenerr,
       ls_processed_plan TYPE rpben_gen_plan_info,
       ls_fsacontrib_trans TYPE rpben_fsacontrib_trans,
       lv_subrc TYPE sysubrc,
       lv_event TYPE string,
       lv_etype TYPE string,
       lx_exception TYPE REF TO cx_static_check,
       ls_selected_enroll_reason TYPE rpbenenrollmentreason,
       lv_datum TYPE sydatum.

  DATA : lt_enroll_event         TYPE hrben00enrollmentreason.  "2904166RAJUG
  CLEAR:ls_processed_plan, lv_event,lv_etype,ls_fsacontrib_trans,lt_check_error,lt_error_table,lv_subrc.
  LOOP AT it_parameter INTO ls_param.
    CASE ls_param-name.
      WHEN 'EmployeeNumber'.
        ls_processed_plan-pernr = ls_param-value.
      WHEN 'Event'.
        lv_event = ls_param-value.
      WHEN 'EventType'.
        lv_etype = ls_param-value.
      WHEN 'BenefitArea'.
        ls_processed_plan-barea = ls_param-value.
      WHEN 'BenefitCategory'.
        ls_processed_plan-bpcat = ls_param-value.
      WHEN 'PlanType'.
        ls_processed_plan-pltyp = ls_param-value.
      WHEN 'Plan'.
        ls_processed_plan-bplan = ls_param-value.
      WHEN 'BeginDate'.
        ls_processed_plan-begda = ls_param-value.
      WHEN 'EndDate'.
        ls_processed_plan-endda = ls_param-value.
      WHEN 'LockIndicator'.
        ls_processed_plan-sprps = ls_param-value.
      WHEN 'Currency'.
        ls_fsacontrib_trans-curre = ls_param-value.
      WHEN 'Contribution'.
        ls_fsacontrib_trans-camnt = ls_param-value.
      WHEN 'FsaMaxContrib'.
        ls_fsacontrib_trans-rmaxa = ls_param-value.
      WHEN 'FsaMinContrib'.
        ls_fsacontrib_trans-rmina = ls_param-value.
      WHEN OTHERS.
    ENDCASE.
  ENDLOOP.
  lv_datum = sy-datum.
  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation( iv_pernr          = ls_processed_plan-pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).

**      MOVE-CORRESPONDING ls_processed_plan TO ls_selected_enroll_reason.    "2904166RAJUG
**      ls_selected_enroll_reason-event = lv_event.
**      ls_selected_enroll_reason-enrty = lv_etype.
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
          reaction               = c_reaction_n
        IMPORTING
          subrc                  = lv_subrc
        TABLES
          error_table            = lt_error_table.
      IF lv_subrc EQ 0.
        CALL FUNCTION 'HR_BEN_ESS_CHECK_FSACONTRIB'
          EXPORTING
            processed_plan         = ls_processed_plan
            fsacontrib_trans       = ls_fsacontrib_trans
          IMPORTING
            fsacontrib_check_error = lt_check_error
            error_table            = lt_error_table
            subrc                  = lv_subrc.
        LOOP AT lt_check_error INTO ls_check_error.
          CLEAR ls_error.   "3307800RAJUG
          MOVE-CORRESPONDING ls_check_error TO ls_error.
          APPEND ls_error TO lt_error_table.
        ENDLOOP.
      ENDIF.
      IF lt_error_table IS NOT INITIAL.
        me->raise_exceptions(
         EXPORTING
           it_messages = lt_error_table
           iv_entity_name = iv_action_name
         ).
      ENDIF.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = iv_action_name
      ).
  ENDTRY.
ENDMETHOD.
