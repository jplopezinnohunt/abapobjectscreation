METHOD GET_TCAL_PERSONALIZATION_MODE.

  DATA lv_logon_pernr TYPE pernr_d.
  DATA lt_pernrs TYPE pccet_pernr.

* check if global personalization is allowed
  CALL BADI go_badi_tcal_settings->get_ui_settings
    EXPORTING
      iv_application_id       = iv_application_id
      iv_instance_id          = iv_instance_id
      iv_employee_assignment  = iv_employee_assignment
    IMPORTING
      ev_personalization_mode = rv_personalization_mode.

  IF rv_personalization_mode = if_hcmfab_tcal_constants=>gc_app_pers_mode-none.
*   personaliation is switched off for the whole application
    RETURN.
  ENDIF.

* check if given employee assignment belongs to current user
* if not, then no personalization allowed (e.g. in on behalf mode)
  TRY.
      lv_logon_pernr = go_employee_api->get_employeenumber_from_user( ).
      lt_pernrs = go_employee_api->get_assignments( lv_logon_pernr ).
      READ TABLE lt_pernrs WITH TABLE KEY table_line = iv_employee_assignment
                           TRANSPORTING NO FIELDS.
      IF sy-subrc <> 0.
        rv_personalization_mode = if_hcmfab_tcal_constants=>gc_app_pers_mode-none.
      ENDIF.
    CATCH cx_hcmfab_common.
      rv_personalization_mode = if_hcmfab_tcal_constants=>gc_app_pers_mode-none.
  ENDTRY.

ENDMETHOD.
