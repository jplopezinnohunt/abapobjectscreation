  METHOD get_fm_area_from_company_code.

    IF iv_bukrs <> mv_bukrs.
      CLEAR mv_fikrs.
      SELECT SINGLE fikrs FROM t001 WHERE bukrs = @iv_bukrs INTO @mv_fikrs.
      mv_bukrs = iv_bukrs.
    ENDIF.

    rv_fikrs = mv_fikrs.

  ENDMETHOD.