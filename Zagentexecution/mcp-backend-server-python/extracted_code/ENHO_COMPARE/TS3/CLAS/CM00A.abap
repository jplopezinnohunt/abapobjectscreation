  METHOD check_conditions_2.
* Check Staff Conditions

    rv_is_ok = abap_false.

    IF iv_rldnr IS NOT INITIAL.
      CHECK iv_rldnr IN mr_rldnr.
    ENDIF.

    IF iv_bukrs IS NOT INITIAL.
      CHECK iv_bukrs IN mr_bukrs.
    ENDIF.

    IF iv_fikrs IS NOT INITIAL.
      CHECK iv_fikrs IN mr_fikrs.
    ENDIF.

    IF iv_gsber IS NOT INITIAL.
      CHECK iv_gsber IN mr_gsber.
    ENDIF.
    "staff
    IF iv_waers IS NOT INITIAL.
      CHECK iv_waers IN mr_waers2.
    ENDIF.

    IF iv_fipex IS NOT INITIAL.
      CHECK iv_fipex IN mr_fipex.
    endif.

    IF iv_hkont IS NOT INITIAL.
       CHECK iv_hkont in  mr_hkont.
    ENDIF.

    "staff
    IF iv_vrgng IS NOT INITIAL.
      CHECK iv_vrgng IN mr_vrgng2.
    ENDIF.

    IF iv_ftype IS NOT INITIAL.
      CHECK iv_ftype IN mr_fund_type.
    ENDIF.

    rv_is_ok = abap_true..

  ENDMETHOD.
