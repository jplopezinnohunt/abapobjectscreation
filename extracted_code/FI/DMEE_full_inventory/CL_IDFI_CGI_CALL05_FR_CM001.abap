  METHOD country_specific_call.

    DATA:
      lv_paval        TYPE paval.

*   Get Company Code additional parameters SIRET number
    lv_paval = cl_idfi_cgi_dmee_utils=>get_par_value(
                  iv_bukrs = is_fpayh-absbu
                  iv_party = 'SAPFR1').

    cs_fpayhx_fref-ref14(16) = lv_paval.

  ENDMETHOD.