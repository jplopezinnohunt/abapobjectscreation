  METHOD get_fund_type_from_fund.

    SELECT SINGLE type FROM fmfincode WHERE fikrs = @iv_fikrs
                                      AND   fincode = @iv_fincode
                       INTO @rv_ftype.
    IF sy-subrc <> 0.
      CLEAR rv_ftype.
    ENDIF.

  ENDMETHOD.