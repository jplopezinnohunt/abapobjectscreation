METHOD get_employee_share_mode.

  DATA ls_share_mode TYPE hcmfab_d_tcalmod.
  SELECT SINGLE * FROM hcmfab_d_tcalmod INTO ls_share_mode WHERE employee_id = iv_employee_id.
  IF ls_share_mode IS NOT INITIAL.
    ev_share_mode = ls_share_mode-share_mode.
  ELSE.
*   use default share mode
    CALL BADI go_badi_tcal_settings->get_approval_settings
      IMPORTING
        ev_default_share_mode = ev_share_mode.
  ENDIF.

ENDMETHOD.
