  METHOD bdc_dynpro.

    DATA: ls_bdcdata TYPE ty_bdcdata.

    ls_bdcdata-program = iv_program.
    ls_bdcdata-dynpro = iv_dynpro.
    ls_bdcdata-dynbegin = iv_dynbegin.

    APPEND ls_bdcdata TO ct_bdcdata.

  ENDMETHOD.
