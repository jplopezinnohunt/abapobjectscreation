METHOD calculate_per_period_cntr.
    DATA: lv_period TYPE ben_period,
        lv_iperiod TYPE ben_period VALUE '06',
        lv_subrc  TYPE sysubrc,
        lt_error_table TYPE hrben00err_ess.
    DATA lo_badi_contrib TYPE REF TO CL_BADI_BASE."Note 3025763
    DATA lv_badi_hrben00err_ess TYPE string VALUE 'HRBEN00ESS003'."Note 3025763
    DATA: lv_badi_method_name TYPE string VALUE 'CALCULATE_FSA_PAY_CONTRIB'."Note 3025763


  CLEAR:lv_period, lv_subrc,ev_cntr_amt_per_period.

  TRY. "Note 3025763
    GET BADI lo_badi_contrib TYPE (lv_badi_hrben00err_ess).
    CATCH cx_badi.
      CLEAR lo_badi_contrib. "No BADI implementation exist for single use BADI
  ENDTRY.

  IF lo_badi_contrib is NOT INITIAL. "Note 3025763
    CALL BADI lo_badi_contrib->(lv_badi_method_name) "Note 3025763
      EXPORTING
        iv_datum  = iv_datum
        iv_amount = iv_contrib_amount
        iv_pernr  = iv_pernr
      IMPORTING
        ev_amount = ev_cntr_amt_per_period.
  ELSE.
  CALL FUNCTION 'HR_BEN_GET_EE_PAY_FREQUENCY'
    EXPORTING
      pernr       = iv_pernr
      datum       = iv_datum
      reaction    = 'N'
    IMPORTING
      zeinh       = lv_period
      subrc       = lv_subrc
    TABLES
      error_table = lt_error_table.
  CHECK lv_subrc EQ 0.
  CALL FUNCTION 'HR_BEN_CALC_AMOUNT_CONVERSION'
    EXPORTING
      iperi       = lv_iperiod
      iamnt       = iv_contrib_amount
      operi       = lv_period
      reaction    = 'N'
    IMPORTING
      oamnt       = ev_cntr_amt_per_period
      subrc       = lv_subrc
    TABLES
      error_table = lt_error_table.
  ENDIF.
  ENDMETHOD.
