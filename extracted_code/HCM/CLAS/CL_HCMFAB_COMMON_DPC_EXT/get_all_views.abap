METHOD get_all_views.


  DATA: lv_app_personalization_mode TYPE hcmfab_tcal_app_pers_mode,
        lt_custom_views TYPE STANDARD TABLE OF hcmfab_d_tcalcvw,
        ls_custom_view TYPE hcmfab_d_tcalcvw,
        lv_default_view_pers_mode TYPE hcmfab_tcal_view_pers_mode,
        lt_standard_views TYPE hcmfab_t_tcal_view,
        ls_standard_view TYPE hcmfab_s_tcal_view,
        ls_view_ui TYPE cl_hcmfab_common_mpc=>ts_teamcalendarview,
        lv_tabix TYPE sytabix.

  FIELD-SYMBOLS: <ls_standard_view> TYPE hcmfab_s_tcal_view.


* get the default view personalization mode
  CALL BADI go_badi_tcal_settings->get_ui_settings
    EXPORTING
      iv_application_id         = iv_application_id
      iv_instance_id            = iv_instance_id
      iv_employee_assignment    = iv_employee_assignment
    IMPORTING
      ev_default_view_pers_mode = lv_default_view_pers_mode.
  IF lv_default_view_pers_mode IS INITIAL.
    lv_default_view_pers_mode = if_hcmfab_tcal_constants=>gc_view_pers_mode-full.
  ENDIF.

* get the standard views for the given calendar usage
* call BADI to get the event types and categories
  CALL BADI go_badi_tcal_settings->get_views
    EXPORTING
      iv_application_id      = iv_application_id
      iv_instance_id         = iv_instance_id
      iv_employee_assignment = iv_employee_assignment
    IMPORTING
      et_views               = lt_standard_views.
  LOOP AT lt_standard_views ASSIGNING <ls_standard_view>.
    IF <ls_standard_view>-personalization_mode IS INITIAL.
      <ls_standard_view>-personalization_mode = lv_default_view_pers_mode.
    ENDIF.
    MOVE-CORRESPONDING <ls_standard_view> TO ls_view_ui.
    ls_view_ui-application_id = iv_application_id.
    ls_view_ui-instance_id = iv_instance_id.
    ls_view_ui-employee_assignment = iv_employee_assignment.
    APPEND ls_view_ui TO et_views.
  ENDLOOP.

* check app personalization mode
  me->get_tcal_personalization_mode(
    EXPORTING
      iv_application_id       = iv_application_id
      iv_instance_id          = iv_instance_id
      iv_employee_assignment  = iv_employee_assignment
    RECEIVING
      rv_personalization_mode = lv_app_personalization_mode
  ).

* add the custom views
  IF lv_app_personalization_mode = if_hcmfab_tcal_constants=>gc_app_pers_mode-full.

    IF iv_application_id IS NOT INITIAL.
      SELECT * FROM hcmfab_d_tcalcvw INTO TABLE lt_custom_views
        WHERE application_id = iv_application_id
        AND instance_id = iv_instance_id
        AND emp_assignment = iv_employee_assignment
        ORDER BY sequence_number view_id. "#EC CI_BYPASS
    ELSE.
      SELECT * FROM hcmfab_d_tcalcvw INTO TABLE lt_custom_views
        WHERE emp_assignment = iv_employee_assignment
        ORDER BY sequence_number view_id. "#EC CI_BYPASS
    ENDIF.
    LOOP AT lt_custom_views INTO ls_custom_view.
      lv_tabix = sy-tabix.
      ls_view_ui-description = ls_custom_view-description.
      ls_view_ui-is_default_view = abap_false.
      ls_view_ui-personalization_mode = if_hcmfab_tcal_constants=>gc_view_pers_mode-full.
      ls_view_ui-view_id = ls_custom_view-view_id.
      ls_view_ui-view_type = if_hcmfab_constants=>gc_viewtype-custom.
      IF ls_custom_view-sequence_number IS INITIAL.
        ls_view_ui-sequence_number = lv_tabix.
      ELSE.
        ls_view_ui-sequence_number = ls_custom_view-sequence_number.
      ENDIF.
      ls_view_ui-application_id = iv_application_id.
      ls_view_ui-instance_id = iv_application_id.
      ls_view_ui-employee_assignment = iv_employee_assignment.
      APPEND ls_view_ui TO et_views.
    ENDLOOP.

  ENDIF.

ENDMETHOD.
