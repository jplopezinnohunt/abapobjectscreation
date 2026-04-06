METHOD execute_action_investment_chk.

  DATA:lt_consist_errors       TYPE hrben00err,
       lt_error_table          TYPE hrben00err_ess,
       lt_inv_selec            TYPE TABLE OF rpbensiv,
       ls_param                LIKE LINE OF it_parameter,
       ls_consist_errors       TYPE rpbenerr,
       ls_error                TYPE rpbenerr,
       ls_inv_selec            TYPE rpbensiv,
       lv_counter              TYPE n LENGTH 2,
       lv_var1                 TYPE char20,
       lv_var2                 TYPE char20,
       lv_var3                 TYPE char20,
       lv_begda                TYPE sydatum,
       lv_endda                TYPE sydatum,
       lv_barea                TYPE ben_area,
       lv_bpcat                TYPE ben_categ,
       lv_pltyp                TYPE ben_type,
       lv_bplan                TYPE ben_plan,
       lv_pernr                TYPE pernr_d,
       lv_levl1                TYPE ben_level1,
       lv_curre                TYPE ben_curr,
       lv_perio                TYPE ben_period,
       lv_spadt                TYPE ben_spadt,
       lv_subrc                TYPE sysubrc,
       lx_exception            TYPE REF TO cx_static_check,
       lx_busi_exception       TYPE REF TO /iwbep/cx_mgw_busi_exception.

  LOOP AT it_parameter INTO ls_param.
    CASE ls_param-name.
      WHEN 'EmployeeNumber'.
        lv_pernr = ls_param-value.
      WHEN 'BeginDate'.
        lv_begda = ls_param-value.
      WHEN 'EndDate'.
        lv_endda = ls_param-value.
      WHEN 'BenefitArea'.
        lv_barea = ls_param-value.
      WHEN 'BenefitCategory'.
        lv_bpcat = ls_param-value.
      WHEN 'PlanType'.
        lv_pltyp = ls_param-value.
      WHEN 'Plan'.
        lv_bplan = ls_param-value.
      WHEN 'Currency'.
        lv_curre = ls_param-value.
      WHEN 'MiscOption'.
        lv_levl1 = ls_param-value.
      WHEN 'Period'.
        lv_perio = ls_param-value.
      WHEN OTHERS.
    ENDCASE.
  ENDLOOP.
  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).
      lv_counter = '01'.
      WHILE lv_counter LE 20.
        CLEAR: ls_inv_selec, lv_var1, lv_var2, lv_var3.
        CONCATENATE 'InvType' lv_counter INTO lv_var1.
        CONCATENATE 'Percentage' lv_counter INTO lv_var2.
        CONCATENATE 'Amount' lv_counter INTO lv_var3.
        CLEAR ls_param.
        READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var1.
        IF ls_param-value IS NOT INITIAL.
          ls_inv_selec-begda = lv_begda.
          ls_inv_selec-endda = lv_endda.
          ls_inv_selec-barea = lv_barea.
          ls_inv_selec-pltyp = lv_pltyp.
          ls_inv_selec-bplan = lv_bplan.
          ls_inv_selec-curre = lv_curre.
          ls_inv_selec-inv_type = ls_param-value.
          CLEAR ls_param.
          READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var2.
          IF ls_param-value IS NOT INITIAL.
            ls_inv_selec-inv_pct = ls_param-value.
          ENDIF.
          CLEAR ls_param.
          READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var3.
          IF ls_param-value IS NOT INITIAL.
            ls_inv_selec-inv_amt = ls_param-value.
          ENDIF.
        ELSE.
          EXIT.
        ENDIF.
        APPEND ls_inv_selec TO lt_inv_selec.
        lv_counter = lv_counter + 1.
      ENDWHILE.
      DELETE lt_inv_selec WHERE inv_amt IS INITIAL AND inv_pct IS INITIAL.
      IF lt_inv_selec IS NOT INITIAL.
        CLEAR:lt_consist_errors,lt_error_table.
        CALL FUNCTION 'HR_BEN_CHECK_INVESTMENTS'
          EXPORTING
            pernr              = lv_pernr
            bpcat              = lv_bpcat
            barea              = lv_barea
            bplan              = lv_bplan
            levl1              = lv_levl1
            datum              = lv_begda
            curre              = lv_curre
            perio              = 02
            del_bplan          = c_false
            reaction           = c_reaction_n
          IMPORTING
            subrc              = lv_subrc
          TABLES
            inv_selec          = lt_inv_selec
            consistency_errors = lt_consist_errors
            error_table        = lt_error_table.
        IF lt_consist_errors IS NOT INITIAL.
          LOOP AT lt_consist_errors INTO ls_consist_errors.
            CLEAR ls_error.
            MOVE-CORRESPONDING ls_consist_errors TO ls_error.
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
