  METHOD get_instance.

    IF mo_instance IS INITIAL.
      mo_instance = NEW ycl_idfi_cgi_dmee_fallback( ).
    ENDIF.

    ro_instance = mo_instance.

  ENDMETHOD.