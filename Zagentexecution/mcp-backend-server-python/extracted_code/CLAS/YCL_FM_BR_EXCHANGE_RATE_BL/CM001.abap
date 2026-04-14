  METHOD get_instance.

    IF mo_instance IS INITIAL.
      mo_instance = NEW ycl_fm_br_exchange_rate_bl( ).
    ENDIF.

    ro_instance = mo_instance.

  ENDMETHOD.