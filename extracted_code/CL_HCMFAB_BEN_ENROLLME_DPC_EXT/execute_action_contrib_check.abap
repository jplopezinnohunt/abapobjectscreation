METHOD execute_action_contrib_check.
  DATA:lt_check_error TYPE hrben00err_ess,
       lt_error_table TYPE hrben00err_ess,
       ls_param       LIKE LINE OF it_parameter,
       ls_check_error TYPE rpbenerr,
       ls_error       TYPE rpbenerr,
       ls_processed_plan TYPE rpben_gen_plan_info,
       ls_contrib_trans TYPE rpben_contrib_trans,
       lv_subrc TYPE sysubrc,
       lv_event TYPE string,
       lv_etype TYPE string,
       lx_exception TYPE REF TO cx_static_check,
       event_permissions TYPE t74hb,
       ls_selected_enroll_reason TYPE rpbenenrollmentreason,
       lv_datum TYPE sydatum.

  DATA: lv_eepct TYPE rpben_contrib_trans-eepct,
        lv_eeamt TYPE rpben_contrib_trans-eeamt,
        lv_eeunt TYPE rpben_contrib_trans-eeunt,
        lv_ptpct TYPE rpben_contrib_trans-ptpct,
        lv_ptamt TYPE rpben_contrib_trans-ptamt,
        lv_ptunt TYPE rpben_contrib_trans-ptunt,
        lv_bcpct TYPE rpben_contrib_trans-bcpct,
        lv_bcamt TYPE rpben_contrib_trans-bcamt,
        lv_bcunt TYPE rpben_contrib_trans-bcunt,
        lv_bppct TYPE rpben_contrib_trans-bppct,
        lv_bpamt TYPE rpben_contrib_trans-bpamt,
        lv_bpunt TYPE rpben_contrib_trans-bpunt.

  DATA : lt_enroll_event         TYPE hrben00enrollmentreason.  "2904166RAJUG
  CLEAR:ls_processed_plan, lv_event,lv_etype,ls_contrib_trans,lt_check_error,lt_error_table,lv_subrc.
  lv_datum = sy-datum.

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
      WHEN 'TextPlan'.
        ls_processed_plan-txt_plan = ls_param-value.
      WHEN 'BeginDate'.
        ls_processed_plan-begda = ls_param-value.
      WHEN 'EndDate'.
        ls_processed_plan-endda = ls_param-value.
      WHEN 'LockIndicator'.
        ls_processed_plan-sprps = ls_param-value.
      WHEN 'RegPreTaxPer'.
        lv_eepct = ls_param-value.
      WHEN 'RegPreTaxAmt'.
        lv_eeamt = ls_param-value.
      WHEN 'RegPreTaxUnit'.
        lv_eeunt = ls_param-value.
      WHEN 'RegPostTaxPer'.
        lv_ptpct = ls_param-value.
      WHEN 'RegPostTaxAmt'.
        lv_ptamt = ls_param-value.
      WHEN 'RegPostTaxUnit'.
        lv_ptunt = ls_param-value.
      WHEN 'BonPreTaxPer'.
        lv_bcpct = ls_param-value.
      WHEN 'BonPreTaxAmt'.
        lv_bcamt = ls_param-value.
      WHEN 'BonPreTaxUnit'.
        lv_bcunt = ls_param-value.
      WHEN 'BonPostTaxPer'.
        lv_bppct = ls_param-value.
      WHEN 'BonPostTaxAmt'.
        lv_bpamt = ls_param-value.
      WHEN 'BonPostTaxUnit'.
        lv_bpunt = ls_param-value.
      WHEN OTHERS.
    ENDCASE.
  ENDLOOP.
  lv_datum = sy-datum.
  TRY.
* Check if Pernr is valid or not
      go_employee_api->do_employeenumber_validation( iv_pernr          = ls_processed_plan-pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).

**      MOVE-CORRESPONDING ls_processed_plan TO ls_selected_enroll_reason.  "2904166RAJUG
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

        event_permissions(
         EXPORTING
          iv_pernr                   = ls_processed_plan-pernr
          iv_ben_area                = ls_processed_plan-barea
          iv_bpcat                   = ls_processed_plan-bpcat
          iv_pltyp                   = ls_processed_plan-pltyp
          iv_bplan                   = ls_processed_plan-bplan
          iv_txtplan                 = ls_processed_plan-txt_plan
          iv_begda                   = ls_processed_plan-begda
          iv_endda                   = ls_processed_plan-endda
          iv_eepct                   = lv_eepct
          iv_eeamt                   = lv_eeamt
          iv_eeunt                   = lv_eeunt
          iv_ptpct                   = lv_ptpct
          iv_ptamt                   = lv_ptamt
          iv_ptunt                   = lv_ptunt
          iv_bcpct                   = lv_bcpct
          iv_bcamt                   = lv_bcamt
          iv_bcunt                   = lv_bcunt
          iv_bppct                   = lv_bppct
          iv_bpamt                   = lv_bpamt
          iv_bpunt                   = lv_bpunt
         IMPORTING
          event_permissions          = event_permissions
          subrc                      = lv_subrc
          error_table                = lt_check_error
              ).

        IF lt_check_error IS NOT INITIAL.
          LOOP AT lt_check_error INTO ls_check_error.
            MOVE-CORRESPONDING ls_check_error TO ls_error.
            APPEND ls_error TO lt_error_table.
          ENDLOOP.
        ENDIF.
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
