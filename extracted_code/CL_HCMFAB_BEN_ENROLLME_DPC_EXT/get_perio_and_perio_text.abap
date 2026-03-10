METHOD get_perio_and_perio_text.
  DATA :  lv_subrc  TYPE sysubrc,
          lt_error_table TYPE hrben00err_ess.

  CALL FUNCTION 'HR_BEN_GET_EE_PAY_FREQUENCY'
    EXPORTING
      pernr       = iv_pernr
      datum       = iv_datum
      reaction    = c_reaction_n
    IMPORTING
      zeinh       = ev_period
      subrc       = lv_subrc
    TABLES
      error_table = lt_error_table.
  IF lv_subrc EQ 0.

    CALL FUNCTION 'HR_BEN_GET_TEXT_DOMVALUE'
      EXPORTING
        domname     = 'PFREQ'
        domvalue    = ev_period
      IMPORTING
        text        = ev_period_text
        subrc       = lv_subrc
      TABLES
        error_table = lt_error_table.
  ENDIF.


ENDMETHOD.
