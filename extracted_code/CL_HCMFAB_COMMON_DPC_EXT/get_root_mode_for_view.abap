METHOD get_root_mode_for_view.

  DATA: lt_views TYPE hcmfab_t_tcal_view,
        ls_view TYPE hcmfab_s_tcal_view.


  IF iv_view_type = if_hcmfab_constants=>gc_viewtype-custom.
    rv_root_object_mode = if_hcmfab_tcal_constants=>gc_root_mode-employee_assignment.
  ELSE.
* get all standard views
    CALL BADI go_badi_tcal_settings->get_views
      EXPORTING
        iv_application_id      = iv_application_id
        iv_instance_id         = iv_instance_id
        iv_employee_assignment = iv_employee_assignment
      IMPORTING
        et_views               = lt_views.

    READ TABLE lt_views INTO ls_view WITH KEY view_type = iv_view_type view_id = iv_view_id.
    IF sy-subrc = 0.
      rv_root_object_mode = ls_view-root_object_mode.
    ENDIF.
  ENDIF.
ENDMETHOD.
