METHOD execute_action_beneficiary_chk.

  DATA:lt_consist_errors       TYPE hrben00err,
       lt_error_table          TYPE hrben00err_ess,
       lt_ben_selec            TYPE TABLE OF rpbensbf,
       ls_ben_selec            TYPE rpbensbf,
       ls_param                LIKE LINE OF it_parameter,
       lv_counter              TYPE n LENGTH 2,
       lv_var1                 TYPE char20,
       lv_var2                 TYPE char20,
       lv_var3                 TYPE char20,
       lv_var4                 TYPE char20,
       lv_var5                 TYPE char20,
       lv_begda                TYPE sydatum,
       lv_endda                TYPE sydatum,
       lv_barea                TYPE ben_area,
       lv_pltyp                TYPE ben_type,
       lv_bplan                TYPE ben_plan,
       lv_pernr                TYPE pernr_d,
       lv_spadt                TYPE ben_spadt,
       ls_consist_errors       TYPE rpbenerr,
       ls_error                TYPE rpbenerr,
       lv_subrc                TYPE sysubrc,
       lx_exception            TYPE REF TO cx_static_check,
       lx_busi_exception       TYPE REF TO /iwbep/cx_mgw_busi_exception.

  CLEAR:lv_pernr,lv_begda,lv_endda,lv_barea,lv_pltyp,lv_bplan,lv_spadt.
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
      WHEN 'PlanType'.
        lv_pltyp = ls_param-value.
      WHEN 'Plan'.
        lv_bplan = ls_param-value.
      WHEN 'SpouseApprDate'.
        lv_spadt = ls_param-value.
      WHEN OTHERS.
    ENDCASE.
  ENDLOOP.
  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).
      IF lv_spadt = '99991231'.
        CLEAR lv_spadt.
      ENDIF.
      lv_counter = '01'.
      WHILE lv_counter LE 20.
        CLEAR: ls_ben_selec, lv_var1, lv_var2, lv_var3, lv_var4,lv_var5.
        CONCATENATE 'BeneficiaryType' lv_counter INTO lv_var1.
        CONCATENATE 'BeneficiaryId' lv_counter INTO lv_var2.
        CONCATENATE 'Percentage' lv_counter INTO lv_var3.
        CONCATENATE 'ContingentInd' lv_counter INTO lv_var4.
        CONCATENATE 'BeneficiaryCateg' lv_counter INTO lv_var5.
        CLEAR ls_param.
        READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var1.
        IF ls_param-value IS NOT INITIAL.
          ls_ben_selec-begda = lv_begda.
          ls_ben_selec-endda = lv_endda.
          ls_ben_selec-barea = lv_barea.
          ls_ben_selec-pltyp = lv_pltyp.
          ls_ben_selec-bplan = lv_bplan.
          ls_ben_selec-ben_type = ls_param-value.
          CLEAR ls_param.
          READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var2.
          IF ls_param-value IS NOT INITIAL.
            ls_ben_selec-ben_id = ls_param-value.
          ENDIF.
          CLEAR ls_param.
          READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var3.
          IF ls_param-value IS NOT INITIAL.
            ls_ben_selec-ben_pct = ls_param-value.
          ENDIF.
          CLEAR ls_param.
          READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var4.
          IF ls_param-value IS NOT INITIAL.
            ls_ben_selec-contingent = ls_param-value.
          ENDIF.
          READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var5.
          IF ls_param-value IS NOT INITIAL.
            ls_ben_selec-ben_categ = ls_param-value.
          ENDIF.
        ELSE.
          EXIT.
        ENDIF.
        APPEND ls_ben_selec TO lt_ben_selec.
        lv_counter = lv_counter + 1.
      ENDWHILE.
      DELETE lt_ben_selec WHERE ben_pct IS INITIAL.
        CLEAR:lt_consist_errors,lt_error_table,lv_subrc.
        CALL FUNCTION 'HR_BEN_CHECK_BENEFICIARIES'
          EXPORTING
            pernr              = lv_pernr
            barea              = lv_barea
            bplan              = lv_bplan
            datum              = lv_begda
            spadt              = lv_spadt
            del_bplan          = c_false
            reaction           = c_reaction_n
          IMPORTING
            subrc              = lv_subrc
          TABLES
            ben_selec          = lt_ben_selec
            consistency_errors = lt_consist_errors
            error_table        = lt_error_table.
        LOOP AT lt_consist_errors INTO ls_consist_errors.
          CLEAR ls_error.
          MOVE-CORRESPONDING ls_consist_errors TO ls_error.
          APPEND ls_error TO lt_error_table.
        ENDLOOP.

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
