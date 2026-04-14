  METHOD fmavc_reinit_on_event.

    DATA lt_fund TYPE RANGE OF bp_geber.
    DATA lt_aldnr TYPE RANGE OF buavc_aldnr.

    CHECK kind = cl_system_transaction_state=>commit_work.

    APPEND VALUE #( sign = 'I' option = 'EQ' low = '9H' ) TO lt_aldnr.

    LOOP AT mt_avc_fund INTO DATA(ls_avc_fund).
      APPEND VALUE #( sign = 'I' option = 'EQ' low = ls_avc_fund-fonds ) TO lt_fund.
      AT END OF fikrs.
        SET PARAMETER ID 'FIK' FIELD ls_avc_fund-fikrs.
        SUBMIT rffmavc_reinit EXPORTING LIST TO MEMORY
                              WITH p_fikrs = ls_avc_fund-fikrs
                              WITH p_gjahr = ls_avc_fund-gjahr
                              WITH s_fund IN lt_fund
                              WITH s_aldnr IN lt_aldnr
                              AND  RETURN.
        CLEAR lt_fund.
      ENDAT.
    ENDLOOP.

    CLEAR mt_avc_fund.

  ENDMETHOD.
