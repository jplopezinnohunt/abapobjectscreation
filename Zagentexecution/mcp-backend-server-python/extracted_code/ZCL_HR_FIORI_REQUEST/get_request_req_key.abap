  METHOD get_request_req_key.

    DATA :
      lv_rc       TYPE nrreturn,
      lv_nrnr     TYPE nrnr, lv_nrobj TYPE nrobj,
      lv_pref_req TYPE c LENGTH 2.

    "Snro depdending on type
    lv_nrnr     = COND #( WHEN iv_request_type EQ '01' THEN co_range_eg-nrnr ELSE co_range_rs-nrnr ).
    lv_nrobj    = COND #( WHEN iv_request_type EQ '01' THEN co_range_eg-nrobj ELSE co_range_rs-nrobj ).
    lv_pref_req = COND #( WHEN iv_request_type EQ '01' THEN 'EG' ELSE 'RS' ).

    CALL FUNCTION 'NUMBER_GET_NEXT'
      EXPORTING
        nr_range_nr             = lv_nrnr
        object                  = lv_nrobj
      IMPORTING
        number                  = ev_request_key                    "-- Newly generated Number
        returncode              = lv_rc                             "-- The Return Code Number
      EXCEPTIONS
        interval_not_found      = 1
        number_range_not_intern = 2
        object_not_found        = 3
        quantity_is_0           = 4
        quantity_is_not_1       = 5
        interval_overflow       = 6
        buffer_overflow         = 7
        OTHERS                  = 8.
    IF sy-subrc NE 0.
      RAISE EXCEPTION TYPE zcx_hr_benef_exception
        MESSAGE ID sy-msgid TYPE sy-msgty NUMBER sy-msgno
        WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
    ENDIF.

    ev_request_key  = |{  lv_pref_req }{ ev_request_key }|.

  ENDMETHOD.
