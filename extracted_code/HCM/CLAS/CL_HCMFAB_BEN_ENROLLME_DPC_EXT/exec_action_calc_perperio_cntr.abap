METHOD exec_action_calc_perperio_cntr.
  DATA: ls_param  LIKE LINE OF it_parameter,
        lv_date TYPE sydatum,
        lv_emp_cntr TYPE ben_camnt,
        lv_emp_cntr_per_period TYPE ben_camnt,
        lv_pernr TYPE pernr_d,
        lr_emp_cntr_per_period TYPE REF TO data,
        lt_error     TYPE TABLE OF rpbenerr,
        lx_exception TYPE REF TO cx_static_check,
        lo_ex     TYPE REF TO cx_root.

  FIELD-SYMBOLS <ls_emp_cntr_per_period> TYPE cl_hcmfab_ben_enrollme_mpc=>calcperperiodcntr.
  CLEAR:lv_emp_cntr_per_period.

  TRY .
      LOOP AT it_parameter INTO ls_param.
        CASE ls_param-name.
          WHEN 'CurrentDate'.
            lv_date = ls_param-value.
          WHEN 'EmpContribution'.
            lv_emp_cntr = ls_param-value.
          WHEN 'EmployeeNumber'.
            lv_pernr = ls_param-value.
          WHEN OTHERS.
        ENDCASE.
      ENDLOOP.
    CATCH cx_root INTO lo_ex.

  ENDTRY.
  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation( iv_pernr          = lv_pernr
                                                     iv_application_id = gc_application_id-mybenefitsenrollment ).

      IF lv_date IS INITIAL.
        lv_date = sy-datum.
      ENDIF.

      CREATE DATA lr_emp_cntr_per_period TYPE cl_hcmfab_ben_enrollme_mpc=>calcperperiodcntr.
      ASSIGN lr_emp_cntr_per_period->* TO <ls_emp_cntr_per_period>.

      calculate_per_period_cntr(
        EXPORTING
             iv_pernr           =  lv_pernr
             iv_datum           =  lv_date
             iv_contrib_amount  =  lv_emp_cntr
        IMPORTING
             ev_cntr_amt_per_period = lv_emp_cntr_per_period
       ).


      <ls_emp_cntr_per_period>-perperiodcamnt = lv_emp_cntr_per_period.
      er_data = lr_emp_cntr_per_period.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = iv_action_name
      ).
  ENDTRY.

ENDMETHOD.
