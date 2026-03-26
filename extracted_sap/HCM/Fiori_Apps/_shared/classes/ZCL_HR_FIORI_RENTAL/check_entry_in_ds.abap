  METHOD check_entry_in_ds.

    CONSTANTS: lc_7_years     TYPE cmp_noyrs VALUE 7,
               lc_datetype_u6 TYPE datar VALUE 'U6'.

    DATA: lv_nb_years    TYPE cmp_noyrs,
          lv_date_it0041 TYPE dardt,
          lo_msg_handler TYPE REF TO if_hrpa_message_handler.

*   Initialize return value
    ov_is_eligible = abap_false.

*   Check if date U6 in infotype 0041 is inferior to 7 years
    CALL FUNCTION 'HR_ECM_GET_DATETYP_FROM_IT0041'
      EXPORTING
        pernr           = iv_pernr
        keydt           = sy-datum
        datar           = lc_datetype_u6
        message_handler = lo_msg_handler
      IMPORTING
        date            = lv_date_it0041.

    CALL FUNCTION 'HRCM_TIME_PERIOD_CALCULATE'
      EXPORTING
        begda = lv_date_it0041
        endda = sy-datum
      IMPORTING
        noyrs = lv_nb_years.

    IF lv_nb_years < lc_7_years.
      ov_is_eligible = abap_true.
    ENDIF.

  ENDMETHOD.
