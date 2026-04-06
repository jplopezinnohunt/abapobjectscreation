METHOD is_personalization_allowed.

  DATA: lt_views TYPE hcmfab_t_tcal_view,
        ls_view TYPE hcmfab_s_tcal_view,
        lv_app_pers_mode TYPE hcmfab_tcal_app_pers_mode.

* check if global personalization is allowed
  me->get_tcal_personalization_mode(
    EXPORTING
      iv_application_id       = iv_application_id
      iv_instance_id          = iv_instance_id
      iv_employee_assignment  = iv_employee_assignment
    RECEIVING
      rv_personalization_mode = lv_app_pers_mode
  ).

  IF lv_app_pers_mode = if_hcmfab_tcal_constants=>gc_app_pers_mode-none.
*   personaliation is switched off for the whole application
    rv_personalization_allowed = abap_false.
    RETURN.
  ENDIF.

* check if personalization is allowed for given view
  IF iv_view_type = if_hcmfab_constants=>gc_viewtype-custom.
    rv_personalization_allowed = abap_true.
    RETURN.
  ENDIF.
  CALL BADI go_badi_tcal_settings->get_views
    EXPORTING
      iv_application_id      = iv_application_id
      iv_instance_id         = iv_instance_id
      iv_employee_assignment = iv_employee_assignment
    IMPORTING
      et_views               = lt_views.
  READ TABLE lt_views INTO ls_view WITH KEY view_type = iv_view_type view_id = iv_view_id.
  IF sy-subrc = 0.
    IF ls_view-personalization_mode = if_hcmfab_tcal_constants=>gc_view_pers_mode-none.
      rv_personalization_allowed = abap_false.
    ELSE.
      rv_personalization_allowed = abap_true.
    ENDIF.
  ELSE.
    rv_personalization_allowed = abap_false.
  ENDIF.

ENDMETHOD.
