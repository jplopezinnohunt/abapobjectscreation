METHOD get_conf_stmt_pdf.

  DATA:
          lt_enrollment_reason       TYPE hrben00enrollmentreason, "#EC NEEDED
          lt_error_table             TYPE hrben00err_ess,   "#EC NEEDED
          lt_plans_participating     TYPE hrben00_gen_plan_info, "#EC NEEDED
          lv_conf_form_avail         TYPE xfeld,            "#EC NEEDED
          lv_subrc                   TYPE sysubrc.          "#EC NEEDED


  CLEAR:lt_enrollment_reason,lt_error_table,lv_subrc.
  CALL FUNCTION 'HR_BEN_ESS_RFC_ENRO_REASONS'
    EXPORTING
      pernr              = iv_pernr
      datum              = iv_datum
    IMPORTING
      enrollment_reasons = lt_enrollment_reason
      error_table        = lt_error_table
      subrc              = lv_subrc.

  CLEAR:lt_plans_participating,lv_conf_form_avail,lt_error_table,lv_subrc.
  CALL FUNCTION 'HR_BEN_ESS_RFC_PARTICIPATION'
    EXPORTING
      pernr               = iv_pernr
      datum               = iv_datum
      end_date            = c_high_date"#EC ARGCHECKED
    IMPORTING
      plans_participating = lt_plans_participating
      conf_form_avail     = lv_conf_form_avail
      error_table         = lt_error_table
      subrc               = lv_subrc.

  IF lv_conf_form_avail EQ 'X'.
    CALL FUNCTION 'HR_BEN_ESS_RFC_CONF_FORM'
      IMPORTING
        form        = ev_pdf_data
        error_table = et_error
        subrc       = ev_subrc.
  ENDIF.


ENDMETHOD.
