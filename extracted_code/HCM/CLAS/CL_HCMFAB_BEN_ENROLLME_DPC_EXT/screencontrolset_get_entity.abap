METHOD screencontrolset_get_entity.
* Declarations
  DATA : ls_key_tab TYPE /iwbep/s_mgw_name_value_pair.


  DATA : ls_selected_enroll_reason TYPE rpbenenrollmentreason,
         lt_error_table TYPE hrben00err_ess,
         ls_processed_plan TYPE rpben_gen_plan_info,
         ls_costcred_ctrl TYPE rpben_costcred_ctrl,
         ls_contrib_ctrl TYPE rpben_contrib_ctrl,
         ls_fsa_contrib_ctrl TYPE rpben_fsacontrib_ctrl,
         lv_subrc TYPE sysubrc,
         lv_datum TYPE sydatum,
         lv_event TYPE string,
         lv_etype TYPE string.

  DATA : es_entity TYPE cl_hcmfab_ben_enrollme_mpc=>ts_screencontrol,
         lx_badi_error       TYPE REF TO cx_hcmfab_benefits_enrollment,
         lx_exception        TYPE REF TO cx_static_check.
  DATA : lt_enroll_event         TYPE hrben00enrollmentreason.  "2904166RAJUG
* Fetching All the Key information to be passed on to fetch related Screen Controls
  CLEAR:ls_processed_plan,lv_event,lv_etype,ls_selected_enroll_reason,lv_subrc,lt_error_table.
  IF it_key_tab IS NOT INITIAL.
    LOOP AT it_key_tab INTO ls_key_tab.
      CASE ls_key_tab-name.
        WHEN 'EmployeeNumber'.
          ls_processed_plan-pernr = ls_key_tab-value.
        WHEN 'Event'.
          lv_event = ls_key_tab-value.
        WHEN 'EventType'.
          lv_etype = ls_key_tab-value.
        WHEN 'BenefitArea'.
          ls_processed_plan-barea = ls_key_tab-value.
        WHEN 'BenefitCategory'.
          ls_processed_plan-bpcat = ls_key_tab-value.
        WHEN 'PlanType'.
          ls_processed_plan-pltyp = ls_key_tab-value.
        WHEN 'Plan'.
          ls_processed_plan-bplan = ls_key_tab-value.
        WHEN 'BeginDate'.
          ls_processed_plan-begda = ls_key_tab-value.
        WHEN 'EndDate'.
          ls_processed_plan-endda = ls_key_tab-value.
        WHEN 'LockIndicator'.
          ls_processed_plan-sprps = ls_key_tab-value.
      ENDCASE.
    ENDLOOP.
  ENDIF.

  TRY.
* Check if Pernr is valid or not
      go_employee_api->do_employeenumber_validation( iv_pernr          = ls_processed_plan-pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).

*      MOVE-CORRESPONDING ls_processed_plan TO ls_selected_enroll_reason. "2904166RAJUG
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
          reaction               = c_reaction_n
        IMPORTING
          subrc                  = lv_subrc
        TABLES
          error_table            = lt_error_table.
      IF lv_subrc EQ 0.
        CLEAR:ls_costcred_ctrl,lv_subrc,lt_error_table.
* Fetching the screen structures
        MOVE-CORRESPONDING ls_processed_plan TO es_entity.
        CASE ls_processed_plan-bpcat.
          WHEN c_credit_plan.     "Credits
            CALL FUNCTION 'HR_BEN_ESS_SCREEN_CTRL_CREDIT'
              EXPORTING
                processed_plan = ls_processed_plan
                reaction       = c_reaction_n
              IMPORTING
                costcred_ctrl  = ls_costcred_ctrl
                subrc          = lv_subrc
                error_table    = lt_error_table.
            CLEAR es_entity.
            MOVE-CORRESPONDING ls_costcred_ctrl TO es_entity.
          WHEN c_health_plan.     "Health
            CALL FUNCTION 'HR_BEN_ESS_SCREEN_CTRL_HEALTH'
              EXPORTING
                processed_plan = ls_processed_plan
                reaction       = c_reaction_n
              IMPORTING
                costcred_ctrl  = ls_costcred_ctrl
                subrc          = lv_subrc
                error_table    = lt_error_table.
            CLEAR es_entity.
            MOVE-CORRESPONDING ls_costcred_ctrl TO es_entity.
          WHEN c_insurance_plan.     "Insurance
            CALL FUNCTION 'HR_BEN_ESS_SCREEN_CTRL_INSURE'
              EXPORTING
                processed_plan = ls_processed_plan
                reaction       = c_reaction_n
              IMPORTING
                costcred_ctrl  = ls_costcred_ctrl
                subrc          = lv_subrc
                error_table    = lt_error_table.
            CLEAR es_entity.
            MOVE-CORRESPONDING ls_costcred_ctrl TO es_entity.
          WHEN c_savings_plan.     "Savings
            CALL FUNCTION 'HR_BEN_ESS_SCREEN_CTRL_SAVING'
              EXPORTING
                processed_plan = ls_processed_plan
                reaction       = c_reaction_n
              IMPORTING
                contrib_ctrl   = ls_contrib_ctrl
                subrc          = lv_subrc
                error_table    = lt_error_table.
            CLEAR es_entity.
            MOVE-CORRESPONDING ls_contrib_ctrl TO es_entity.
          WHEN c_spendings_plan.     "Spendings
            CALL FUNCTION 'HR_BEN_ESS_SCREEN_CTRL_SPENDA'
              EXPORTING
                processed_plan  = ls_processed_plan
                reaction        = c_reaction_n
              IMPORTING
                fsacontrib_ctrl = ls_fsa_contrib_ctrl
                subrc           = lv_subrc
                error_table     = lt_error_table.
            CLEAR es_entity.
            MOVE-CORRESPONDING ls_fsa_contrib_ctrl TO es_entity.
          WHEN c_miscellaneous_plan.     "Miscellaneous
            CALL FUNCTION 'HR_BEN_ESS_SCREEN_CTRL_MISCEL'
              EXPORTING
                processed_plan = ls_processed_plan
                reaction       = c_reaction_n
              IMPORTING
                costcred_ctrl  = ls_costcred_ctrl
                contrib_ctrl   = ls_contrib_ctrl
                subrc          = lv_subrc
                error_table    = lt_error_table.
            CLEAR es_entity.
            MOVE-CORRESPONDING ls_costcred_ctrl TO es_entity.
            MOVE-CORRESPONDING ls_contrib_ctrl TO es_entity.
          WHEN c_stock_purchase_plan.     "Stock Purchase
            CALL FUNCTION 'HR_BEN_ESS_SCREEN_CTRL_STOCKP'
              EXPORTING
                processed_plan = ls_processed_plan
                reaction       = c_reaction_n
              IMPORTING
                contrib_ctrl   = ls_contrib_ctrl
                subrc          = lv_subrc
                error_table    = lt_error_table.
            CLEAR es_entity.
            MOVE-CORRESPONDING ls_contrib_ctrl TO es_entity.
        ENDCASE.
      ENDIF.
      IF lv_subrc NE 0.
        me->raise_exceptions(
      EXPORTING
        it_messages = lt_error_table
        iv_entity_name = iv_entity_name
       ).
      ELSE.
        es_entity-event = lv_event.
        es_entity-enrty = lv_etype.
        me->enrich_screencontrol( CHANGING screencontrolentity = es_entity ).
        MOVE-CORRESPONDING es_entity TO er_entity.
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
