METHOD execute_action_dependent_check.

  DATA:lt_dep_selec            TYPE TABLE OF rpbensdp,
       lt_error_table          TYPE hrben00err_ess,
       lt_consist_errors       TYPE hrben00err,
       ls_consist_errors       TYPE rpbenerr,
       ls_error                TYPE rpbenerr,
       ls_dep_selec            TYPE rpbensdp,
       ls_dep_str              TYPE rpbendep,
       ls_param                LIKE LINE OF it_parameter.

  DATA:lv_begda                TYPE sydatum,
       lv_endda                TYPE sydatum,
       lv_barea                TYPE ben_area,
       lv_pltyp                TYPE ben_type,
       lv_bplan                TYPE ben_plan,
       lv_pernr                TYPE pernr_d,
       lv_sprps                TYPE sprps,
       lv_bopti                TYPE ben_option,
       lv_depcv                TYPE ben_depcov,
       lv_levl1                TYPE ben_level1,
       lv_counter              TYPE n LENGTH 2,
       lv_var1                 TYPE char20,
       lv_var2                 TYPE char20,
       lv_subrc                TYPE sysubrc,
       lx_exception            TYPE REF TO cx_static_check,
       lx_busi_exception       TYPE REF TO /iwbep/cx_mgw_busi_exception.


  FIELD-SYMBOLS : <fs_sprps>    TYPE sprps,
                  <fs_id>      TYPE ben_depid.

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
      WHEN 'HealthPlanOption'.
        lv_bopti = ls_param-value.
      WHEN 'DepenCoverage'.
        lv_depcv =  ls_param-value.
      WHEN 'MiscOption'.
        lv_levl1 = ls_param-value.
      WHEN 'LockIndicator'.
        lv_sprps =  ls_param-value.
      WHEN OTHERS.
    ENDCASE.
  ENDLOOP.
  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).
      lv_counter = '01'.
      WHILE lv_counter LE 20.
        CLEAR: ls_dep_selec, lv_var1, lv_var2.
        CONCATENATE 'DependentType' lv_counter INTO lv_var1.
        CONCATENATE 'DependentId' lv_counter INTO lv_var2.
        READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var1.
        IF ls_param-value IS NOT INITIAL.
          ls_dep_selec-begda = lv_begda.
          ls_dep_selec-endda = lv_endda.
          ls_dep_selec-barea = lv_barea.
          ls_dep_selec-pltyp = lv_pltyp.
          ls_dep_selec-bplan = lv_bplan.
          ASSIGN COMPONENT 'sprps' OF STRUCTURE ls_dep_selec TO <fs_sprps>.
          IF <fs_sprps> IS ASSIGNED.
            <fs_sprps> = lv_sprps.
          ENDIF.
          ls_dep_selec-dep_type = ls_param-value.
          CLEAR ls_param.
          READ TABLE it_parameter INTO ls_param WITH KEY name = lv_var2.
          IF ls_param-value IS NOT INITIAL.
            ls_dep_selec-dep_id = ls_param-value.
          ENDIF.
        ELSE.
          EXIT.
        ENDIF.
        APPEND ls_dep_selec TO lt_dep_selec.
        lv_counter = lv_counter + 1.
      ENDWHILE.

      CALL FUNCTION 'HR_BEN_CHECK_DEPENDENTS'
        EXPORTING
          pernr              = lv_pernr
          barea              = lv_barea
          bplan              = lv_bplan
          bopti              = lv_bopti
          depcv              = lv_depcv
          levl1              = lv_levl1
          datum              = lv_begda
          del_bplan          = c_false
          reaction           = c_reaction_n
        IMPORTING
          subrc              = lv_subrc
        TABLES
          dep_selec          = lt_dep_selec
          consistency_errors = lt_consist_errors
          error_table        = lt_error_table.
      IF lt_consist_errors IS NOT INITIAL.
        LOOP AT lt_consist_errors INTO ls_consist_errors.
          CLEAR ls_error.
          MOVE-CORRESPONDING ls_consist_errors TO ls_error.
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
