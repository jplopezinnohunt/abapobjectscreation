  method BDC_FIELD.

    DATA: ls_bdcdata TYPE ty_bdcdata.

    ls_bdcdata-fnam = iv_fnam.
    ls_bdcdata-fval = iv_fval.

    APPEND ls_bdcdata TO ct_bdcdata.

  endmethod.
