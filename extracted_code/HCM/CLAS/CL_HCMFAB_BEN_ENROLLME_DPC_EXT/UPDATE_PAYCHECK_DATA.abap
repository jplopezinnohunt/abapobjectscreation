method UPDATE_PAYCHECK_DATA.

  DATA ls_paycheck TYPE hcmfab_enro_cont.

  DELETE FROM hcmfab_enro_cont WHERE pernr = iv_pernr.

  IF iv_content IS NOT INITIAL.

    ls_paycheck-mandt = sy-mandt.
    ls_paycheck-pernr = iv_pernr.
    ls_paycheck-content = iv_content.

    INSERT hcmfab_enro_cont FROM ls_paycheck.

  ENDIF.


endmethod.
