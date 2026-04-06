METHOD execute_action_recal_insure_em.
  DATA: lt_error_table TYPE hrben00err_ess,
          ls_processed_plan TYPE rpben_gen_plan_info,
          lv_subrc  TYPE sysubrc,
        ls_param        LIKE LINE OF it_parameter,
          lx_exception      TYPE REF TO cx_static_check.

  DATA: ls_cost_cred          TYPE cl_hcmfab_ben_enrollme_mpc_ext=>ts_costcredit,
        ls_h74fa              TYPE t74fa,
        ls_benefit_data       TYPE rpbeneedat,
        ls_insure_plan        TYPE rpben_sb,"Note 3145908
        lv_eoi_test_sts       TYPE rpbenrpt01-consi,
        lt_eoi_test_error     TYPE TABLE OF rpbenerr,
        lt_eoi_error          TYPE TABLE OF rpbenerr.

  LOOP AT it_parameter INTO ls_param.
    CASE ls_param-name.
      WHEN 'EmployeeNumber'.
        ls_processed_plan-pernr = ls_param-value.
        ls_insure_plan-pernr = ls_param-value.
      WHEN 'BeginDate'.
        ls_processed_plan-begda = ls_param-value.
        ls_insure_plan-begda = ls_param-value.
      WHEN 'EndDate'.
        ls_processed_plan-endda = ls_param-value.
        ls_insure_plan-endda = ls_param-value.
      WHEN 'BenefitArea'.
        ls_processed_plan-barea = ls_param-value.
        ls_insure_plan-barea = ls_param-value.
      WHEN 'BenefitCategory'.
        ls_processed_plan-bpcat = ls_param-value.
      WHEN 'PlanType'.
        ls_processed_plan-pltyp = ls_param-value.
        ls_insure_plan-pltyp = ls_param-value.
      WHEN 'Plan'.
        ls_processed_plan-bplan = ls_param-value.
        ls_insure_plan-bplan = ls_param-value.
      WHEN 'InsuranceOption'.
        ls_cost_cred-bcovr = ls_param-value.
        ls_insure_plan-bcovr = ls_param-value.
      WHEN 'AddnlInsCovNum'.
        ls_cost_cred-addno = ls_param-value.
        ls_insure_plan-addno = ls_param-value.
    ENDCASE.
  ENDLOOP.

  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation( iv_pernr          = ls_processed_plan-pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).
      CALL FUNCTION 'HR_BEN_READ_EE_BENEFIT_DATA'
        EXPORTING
          pernr           = ls_processed_plan-pernr
          datum           = ls_processed_plan-begda
          reaction        = c_reaction_n
        IMPORTING
          ee_benefit_data = ls_benefit_data
        TABLES
          error_table     = lt_error_table.
      CLEAR ls_h74fa.

      MOVE-CORRESPONDING ls_processed_plan TO ls_cost_cred.
      PERFORM re74fa IN PROGRAM sapfben0 TABLES   lt_error_table
                               USING    ls_cost_cred-barea
                                        ls_cost_cred-bplan
                                        ls_cost_cred-bcovr
                                        sy-datum
                                        c_reaction_n
                               CHANGING ls_h74fa
                                        lv_subrc.
      CHECK ls_h74fa IS NOT INITIAL.
      CLEAR:lv_subrc.
*
      CALL FUNCTION 'HR_BEN_GET_CURRENCY'
        EXPORTING
          barea       = ls_cost_cred-barea
          datum       = ls_processed_plan-begda
          reaction    = c_reaction_n
        IMPORTING
          currency    = ls_cost_cred-curre
          subrc       = lv_subrc
        TABLES
          error_table = lt_error_table.
      CALL FUNCTION 'HR_BEN_GET_PLAN_COVERAGE'
        EXPORTING
          ee_benefit_data = ls_benefit_data
          bplan           = ls_cost_cred-bplan
          bcove           = ls_h74fa-bcove
          addno           = ls_cost_cred-addno
          datum           = ls_cost_cred-begda
          desired_curre   = ls_cost_cred-curre
          reaction        = c_reaction_n
        IMPORTING
          coverage_amount = ls_cost_cred-covam
          subrc           = lv_subrc
        TABLES
          error_table     = lt_error_table.
*
      get_perio_and_perio_text(
   EXPORTING
      iv_pernr               = ls_processed_plan-pernr
      iv_datum               = ls_processed_plan-begda
    IMPORTING
      ev_period              = ls_cost_cred-perio
      "ev_period_text         = lv_perio_txt
).
      CALL FUNCTION 'HR_BEN_GET_PLAN_COST'
        EXPORTING
          ee_benefit_data = ls_benefit_data
          bplan           = ls_cost_cred-bplan
          bcost           = ls_h74fa-bcost
          datum           = ls_cost_cred-begda
          cover           = ls_cost_cred-covam
          out_curre       = ls_cost_cred-curre
          out_period      = ls_cost_cred-perio
          reaction        = c_reaction_n
        IMPORTING
          eecst           = ls_cost_cred-eecst
          ercst           = ls_cost_cred-ercst
*         accst           = ls_cost_cred-accst
*         flxcr           = ls_cost_cred-flxcr
        TABLES
          error_table     = lt_error_table.

      "Check EOI requirement ( modify of addon) "Note 3145908
      CALL FUNCTION 'HR_BEN_TEST_ADMIN_INSURE_EOIRQ'
        EXPORTING
          insure_plan = ls_insure_plan
          datum       = ls_insure_plan-begda
          reaction    = 'N'
        IMPORTING
          test_status = lv_eoi_test_sts
          subrc       = lv_subrc
        TABLES
          test_errors = lt_eoi_test_error
          error_table = lt_eoi_error.
        IF lv_eoi_test_sts = 1.
          ls_cost_cred-eoirq = 'X'.
          ls_cost_cred-eoipr = ''.
        ENDIF.
      copy_data_to_ref(
        EXPORTING
          is_data = ls_cost_cred
        CHANGING
          cr_data = er_data
          ).
    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = iv_action_name
      ).
  ENDTRY.

ENDMETHOD.
