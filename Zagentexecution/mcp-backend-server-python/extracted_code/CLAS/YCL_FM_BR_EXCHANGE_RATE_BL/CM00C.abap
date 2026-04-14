  METHOD check_conditions_3.
* Check Reconstruction Conditions for deletion

    rv_is_ok = abap_false.

    IF iv_rldnr IS NOT INITIAL.
      CHECK iv_rldnr NOT IN mr_rldnr.
    ENDIF.

    IF iv_bukrs IS NOT INITIAL.
      CHECK iv_bukrs NOT IN mr_bukrs.
    ENDIF.

    IF iv_fikrs IS NOT INITIAL.
      CHECK iv_fikrs NOT IN mr_fikrs.
    ENDIF.

    IF iv_gsber IS NOT INITIAL.
      CHECK iv_gsber NOT IN mr_gsber.
    ENDIF.

    IF iv_fipex IS NOT INITIAL.
      CHECK iv_fipex IN mr_fipex3.
    ENDIF.

    IF iv_vrgng IS NOT INITIAL.
      CHECK iv_vrgng IN mr_vrgng3.
    ENDIF.

    IF iv_ftype IS NOT INITIAL.
      CHECK iv_ftype IN mr_fund_type3.
    ENDIF.

    rv_is_ok = abap_true..

  ENDMETHOD.