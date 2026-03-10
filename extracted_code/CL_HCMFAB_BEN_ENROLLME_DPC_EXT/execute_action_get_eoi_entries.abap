METHOD execute_action_get_eoi_entries.
  DATA: lt_error_table TYPE hrben00err_ess,
        lt_t74hb  TYPE TABLE OF t74hb,
        ls_t74hb  TYPE t74hb,
        ls_processed_plan TYPE rpben_gen_plan_info,
        ls_param  LIKE LINE OF it_parameter,
        lv_etype  TYPE ben_enrtyp,
        lv_event  TYPE ben_event,
        lv_event_group TYPE ben_evtgr,
        lv_subrc  TYPE sysubrc,
        lx_exception      TYPE REF TO cx_static_check,
        lx_busi_exception TYPE REF TO /iwbep/cx_mgw_busi_exception.

  DATA: ls_insure_selection   TYPE rpben_sb,
        lt_insure_selection   TYPE TABLE OF rpben_sb,
        ls_health_selection   TYPE rpben_sa,
        lt_health_selection   TYPE TABLE OF rpben_sa,
        lt_health_offer       TYPE TABLE OF rpben_oa,
        ls_health_offer       TYPE rpben_oa,
        lt_health_offer_out   TYPE TABLE OF rpben_oa,
        ls_health_offer_out   TYPE rpben_oa,
        lt_insure_offer       TYPE TABLE OF rpben_ob,
        ls_insure_offer       TYPE rpben_ob,
        lt_insure_offer_out   TYPE TABLE OF rpben_ob,
        ls_insure_offer_out   TYPE rpben_ob,
        lt_health_eoi_entries TYPE TABLE OF rpben_sa,
        ls_health_eoi_entry   TYPE rpben_sa,
        lt_insure_eoi_entries TYPE TABLE OF  rpben_sb,
        ls_insure_eoi_entry   TYPE rpben_sb,
        lv_consistency_status TYPE rpbenrpt01-consi,
        lt_consistency_errors TYPE hrben00err_ess,
        lv_coverage           TYPE ben_eecova,
        ls_h74fa              TYPE t74fa,
        lv_lines              TYPE i,
        lv_currency           TYPE ben_curr,
        ls_benefit_data       TYPE rpbeneedat,
        lt_offer              TYPE cl_hcmfab_ben_enrollme_mpc=>tt_offer,
        ls_offer_un           TYPE cl_hcmfab_ben_enrollme_mpc=>ts_offer,
        ls_offer              TYPE cl_hcmfab_ben_enrollme_mpc=>ts_offer.

  CONSTANTS: c_requires_doc   TYPE ben_consis VALUE '1'.
  REFRESH:lt_error_table,lt_health_offer,lt_insure_offer,lt_health_eoi_entries,lt_insure_eoi_entries.
  LOOP AT it_parameter INTO ls_param.
    CASE ls_param-name.
      WHEN 'EmployeeNumber'.
        ls_processed_plan-pernr = ls_param-value.
      WHEN 'BeginDate'.
        ls_processed_plan-begda = ls_param-value.
      WHEN 'EndDate'.
        ls_processed_plan-endda = ls_param-value.
      WHEN 'BenefitArea'.
        ls_processed_plan-barea = ls_param-value.
      WHEN 'BenefitCategory'.
        ls_processed_plan-bpcat = ls_param-value.
      WHEN 'PlanType'.
        ls_processed_plan-pltyp = ls_param-value.
      WHEN 'Plan'.
        ls_processed_plan-bplan = ls_param-value.
      WHEN 'Event'.
        lv_event = ls_param-value.
      WHEN 'EventType'.
        lv_etype = ls_param-value.
      WHEN 'HealthPlanOption'.
        ls_health_selection-bopti = ls_param-value.
      WHEN 'DepenCoverage'.
        ls_health_selection-depcv = ls_param-value.
      WHEN 'InsuranceOption'.
        ls_insure_selection-bcovr = ls_param-value.
      WHEN 'AddnlInsCovNum'.
        ls_insure_selection-addno = ls_param-value.
      WHEN 'PreTaxDedInd'.
        ls_insure_selection-pretx = ls_param-value.
        ls_health_selection-pretx = ls_param-value.
    ENDCASE.
  ENDLOOP.
  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation( iv_pernr          = ls_processed_plan-pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).

      CALL METHOD me->hr_get_offer
        EXPORTING
          iv_pernr        = ls_processed_plan-pernr
          iv_datum        = sy-datum
          iv_ben_area     = ls_processed_plan-barea
          iv_event        = lv_event
          iv_event_type   = lv_etype
        IMPORTING
          ev_subrc        = lv_subrc
          et_error_table  = lt_error_table
          et_health_offer = lt_health_offer
          et_insure_offer = lt_insure_offer.
      IF lt_error_table IS INITIAL.
        IF lv_etype = 'E'. "Fill the permissions if the event is an adjustment reason.
          CLEAR:lv_subrc.
          CALL FUNCTION 'HR_BEN_GET_FROM_FEATURE_EVTGR'
            EXPORTING
              pernr       = ls_processed_plan-pernr
              begda       = sy-datum
              endda       = sy-datum
              barea       = ls_processed_plan-barea
              reaction    = c_reaction_n
            IMPORTING
              evtgr       = lv_event_group
              subrc       = lv_subrc
            TABLES
              error_table = lt_error_table.
* Select the data for adjustment reason
          IF lv_event_group IS NOT INITIAL.
            SELECT * FROM t74hb INTO ls_t74hb WHERE barea = ls_processed_plan-barea
                                              AND   event = lv_event
                                              AND   evtgr = lv_event_group.
              APPEND ls_t74hb TO lt_t74hb.
            ENDSELECT.
          ENDIF.
        ENDIF.
        CASE ls_processed_plan-bpcat.
*Get EOI record for health Plan.
          WHEN  c_health_plan.
            CLEAR:lv_consistency_status,lv_subrc.
            MOVE-CORRESPONDING ls_processed_plan TO ls_health_selection.
* check whether eoi is required for the plan or not.
            CALL FUNCTION 'HR_BEN_TEST_ADMIN_HEALTH_EOIRQ'
              EXPORTING
                health_plan = ls_health_selection
                datum       = ls_health_selection-begda
                reaction    = c_reaction_n
              IMPORTING
                test_status = lv_consistency_status
                subrc       = lv_subrc
              TABLES
                test_errors = lt_consistency_errors
                error_table = lt_error_table.
            IF lv_subrc IS INITIAL AND lv_consistency_status = c_requires_doc.
              ls_health_selection-eoirq = c_true.
              ls_health_selection-eoipr = space.
              APPEND ls_health_selection TO lt_health_selection.
* Call the FM to generate the EOI entries for the current selection according to the customizing.
              CLEAR :lv_subrc.
              CALL FUNCTION 'HR_BEN_GENERATE_HEAL_EOI_SELEC'
                EXPORTING
                  reaction      = c_reaction_n
                IMPORTING
                  subrc         = lv_subrc
                TABLES
                  require_doc   = lt_health_selection
                  eoi_selection = lt_health_eoi_entries
                  error_table   = lt_error_table.
              LOOP AT lt_health_eoi_entries INTO ls_health_eoi_entry.
                CLEAR:ls_health_offer.
                READ TABLE lt_health_offer INTO ls_health_offer
                 WITH KEY barea = ls_health_eoi_entry-barea
                          pltyp = ls_health_eoi_entry-pltyp
                          bplan = ls_health_eoi_entry-bplan
                          bopti = ls_health_eoi_entry-bopti
                          depcv = ls_health_eoi_entry-depcv
                          begda = ls_health_eoi_entry-begda
                          endda = ls_health_eoi_entry-endda.
                MOVE-CORRESPONDING ls_health_eoi_entry TO ls_health_offer_out.
                MOVE-CORRESPONDING ls_health_offer TO ls_health_offer_out.
                ls_health_offer_out-sprps  = ls_health_eoi_entry-sprps.
                IF lt_t74hb IS NOT INITIAL.
                  READ TABLE lt_t74hb INTO ls_t74hb WITH KEY pltyp = ls_health_offer_out-pltyp.
                  ls_health_offer_out-del_bplan = ls_t74hb-del_bplan.
                ENDIF.
                ls_health_offer_out-enrolled = c_true.
                IF ls_health_offer_out-sprps = c_true.
                  ls_health_offer_out-add_bplan = c_false.
                  ls_health_offer_out-chg_bplan = c_false.
                  ls_health_offer_out-del_bplan = c_false.
                ELSE.
                  ls_health_offer_out-add_bplan = c_false.
                  ls_health_offer_out-chg_bplan = c_true.
                ENDIF.
                ls_health_offer_out-pretx = ls_health_selection-pretx.
                MOVE-CORRESPONDING ls_health_offer_out TO ls_offer.
                APPEND ls_offer TO lt_offer.
                CLEAR:ls_health_eoi_entry,ls_offer,ls_health_offer_out.
              ENDLOOP.
            ENDIF.

          WHEN  c_insurance_plan.
            MOVE-CORRESPONDING ls_processed_plan TO ls_insure_selection.
            "ls_insure_selection-pretx = what ever was passed from front end and it is already filled from the parameter.
            CLEAR:lv_consistency_status,lv_subrc.
            CALL FUNCTION 'HR_BEN_TEST_ADMIN_INSURE_EOIRQ'
              EXPORTING
                insure_plan = ls_insure_selection
                datum       = ls_insure_selection-begda
                reaction    = c_reaction_n
              IMPORTING
                test_status = lv_consistency_status
                subrc       = lv_subrc
              TABLES
                test_errors = lt_consistency_errors
                error_table = lt_error_table.
            IF lv_subrc IS INITIAL AND lv_consistency_status = c_requires_doc.
              ls_insure_selection-eoirq = c_true.
              ls_insure_selection-eoipr = space.
              APPEND ls_insure_selection TO lt_insure_selection.
              CLEAR:lv_subrc.
              CALL FUNCTION 'HR_BEN_GENERATE_INSU_EOI_SELEC'
                EXPORTING
                  reaction      = c_reaction_n
                IMPORTING
                  subrc         = lv_subrc
                TABLES
                  require_doc   = lt_insure_selection
                  eoi_selection = lt_insure_eoi_entries
                  error_table   = lt_error_table.
              LOOP AT lt_insure_eoi_entries INTO ls_insure_eoi_entry.
                CLEAR:ls_insure_offer.
                READ TABLE lt_insure_offer INTO ls_insure_offer
                 WITH KEY barea = ls_insure_eoi_entry-barea
                          pltyp = ls_insure_eoi_entry-pltyp
                          bplan = ls_insure_eoi_entry-bplan
                          bcovr = ls_insure_eoi_entry-bcovr
                          begda = ls_insure_eoi_entry-begda
                          endda = ls_insure_eoi_entry-endda.
                MOVE-CORRESPONDING ls_insure_offer TO ls_insure_offer_out.
                ls_insure_offer_out-covov = ls_insure_eoi_entry-covov.
                ls_insure_offer_out-eoirq = ls_insure_eoi_entry-eoirq.
                ls_insure_offer_out-eoipr = ls_insure_eoi_entry-eoipr.
                ls_insure_offer_out-eogrp = ls_insure_eoi_entry-eogrp.
                ls_insure_offer_out-sprps = ls_insure_eoi_entry-sprps.
                ls_insure_offer_out-addno = ls_insure_eoi_entry-addno.
                ls_insure_offer_out-pretx = ls_insure_selection-pretx.
                ls_insure_offer_out-enrolled = c_true.
                ls_insure_offer_out-add_bplan = c_false.
                IF ls_insure_offer_out-sprps = c_true.
                  ls_insure_offer_out-chg_bplan = c_false.
                  ls_insure_offer_out-del_bplan = c_false.
                ELSE.
                  ls_insure_offer_out-chg_bplan = c_true.
                  ls_insure_offer_out-del_bplan = c_true.
                  IF lt_t74hb IS NOT INITIAL.
                    READ TABLE lt_t74hb INTO ls_t74hb WITH KEY pltyp = ls_insure_offer_out-pltyp.
                    IF sy-subrc = 0.
                      ls_insure_offer_out-del_bplan = ls_t74hb-del_bplan.
                    ENDIF.
                  ENDIF.
                ENDIF.
                IF ls_benefit_data IS INITIAL.
                  CLEAR:lv_subrc.
                  CALL FUNCTION 'HR_BEN_GET_EE_BENEFIT_DATA'
                    EXPORTING
                      pernr           = ls_insure_offer_out-pernr
                      datum           = sy-datum
                      reaction        = c_reaction_n
                    IMPORTING
                      ee_benefit_data = ls_benefit_data
                      subrc           = lv_subrc
                    TABLES
                      error_table     = lt_error_table.
                ENDIF.
                CLEAR ls_h74fa.
                PERFORM re74fa IN PROGRAM sapfben0 TABLES   lt_error_table
                                         USING    ls_insure_offer_out-barea
                                                  ls_insure_offer_out-bplan
                                                  ls_insure_offer_out-bcovr
                                                  sy-datum
                                                  c_reaction_n
                                         CHANGING ls_h74fa
                                                  lv_subrc.
                CHECK ls_h74fa IS NOT INITIAL.
                CLEAR:lv_subrc.
                CALL FUNCTION 'HR_BEN_GET_PLAN_COVERAGE'
                  EXPORTING
                    ee_benefit_data = ls_benefit_data
                    bplan           = ls_insure_offer_out-bplan
                    bcove           = ls_h74fa-bcove
                    addno           = ls_insure_offer_out-addno
                    datum           = ls_insure_offer_out-begda
                    desired_curre   = ls_insure_offer_out-curre
                    reaction        = c_reaction_n
                  IMPORTING
                    coverage_amount = ls_insure_offer_out-covam
                    subrc           = lv_subrc
                  TABLES
                    error_table     = lt_error_table.
                IF ls_insure_offer_out-covov IS NOT INITIAL.
                  "alternative coverage amount is present then recalculate cost as per the alternative cov amount
                  ls_insure_offer_out-txt_option = text-t02.
                  lv_coverage = ls_insure_offer_out-covov.
                ELSE.
                  lv_coverage = ls_insure_offer_out-covam.
                ENDIF.
                CLEAR:lv_subrc.
                CALL FUNCTION 'HR_BEN_GET_PLAN_COST'
                  EXPORTING
                    ee_benefit_data = ls_benefit_data
                    bplan           = ls_insure_offer_out-bplan
                    bcost           = ls_h74fa-bcost
                    datum           = sy-datum
                    cover           = lv_coverage
                    out_curre       = ls_insure_offer_out-curre
                    out_period      = ls_insure_offer_out-perio
                    reaction        = c_reaction_n
                  IMPORTING
                    eecst           = ls_insure_offer_out-eecst
                    ercst           = ls_insure_offer_out-ercst
                    accst           = ls_insure_offer_out-accst
                    flxcr           = ls_insure_offer_out-flxcr
                    subrc           = lv_subrc
                  TABLES
                    error_table     = lt_error_table.
                CLEAR ls_offer.
                MOVE-CORRESPONDING ls_insure_offer_out TO ls_offer.
                APPEND ls_offer TO lt_offer.
                CLEAR:ls_insure_eoi_entry,ls_insure_offer_out,ls_offer.
              ENDLOOP.
            ENDIF.
        ENDCASE.
        copy_data_to_ref(
          EXPORTING
            is_data = lt_offer
          CHANGING
            cr_data = er_data ).
      ELSE.
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
