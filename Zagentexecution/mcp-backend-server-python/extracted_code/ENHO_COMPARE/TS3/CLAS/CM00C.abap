  METHOD check_br_is_active.

    rv_is_ok = abap_false.

    IF sy-datum >= mv_start_date.
      rv_is_ok = abap_true.
    ENDIF.

  ENDMETHOD.
