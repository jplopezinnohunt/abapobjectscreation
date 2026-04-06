METHOD get_display_state.

  DATA: lv_personalization_allowed TYPE boolean,
        lt_personalization TYPE STANDARD TABLE OF hcmfab_d_tcalper,
        ls_personalization TYPE hcmfab_d_tcalper,
        lv_approval_mode TYPE hcmfab_tcal_approval_mode,
        lv_share_mode TYPE hcmfab_tcal_approval_mode,
        lv_is_in_standard_view TYPE boolean,
        lv_access_state TYPE hcmfab_tcal_emp_access_state.

  IF iv_personalization_allowed IS SUPPLIED.
    lv_personalization_allowed = iv_personalization_allowed.
  ELSE.
    lv_personalization_allowed = me->is_personalization_allowed(
        iv_application_id          = iv_application_id
        iv_instance_id             = iv_instance_id
        iv_employee_assignment     = iv_employee_assignment
        iv_view_type               = iv_view_type
        iv_view_id                 = iv_view_id
    ).
  ENDIF.

  IF lv_personalization_allowed = abap_false.
*   no personalization allowed => employee is always visible
    rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-visible.
    RETURN.
  ENDIF.

* read the personalization data
  SELECT * FROM hcmfab_d_tcalper INTO TABLE lt_personalization
    WHERE emp_assignment = iv_employee_assignment
    AND view_type = iv_view_type
    AND view_id = iv_view_id.

* calculate the diplay state
  READ TABLE lt_personalization INTO ls_personalization WITH KEY employee_id = iv_employee_id.
  IF sy-subrc = 0.
*   state defined in personalization
    rv_display_state = ls_personalization-display_state.

*   for added, requested and rejected employees check the current approval settings and update the display state if needed
    IF rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-requested
      OR rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-rejected
      OR rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-added.

      IF lv_approval_mode = if_hcmfab_tcal_constants=>gc_approval_mode-none.
        rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-added.
      ELSE.
        me->get_tcal_access_state(
          EXPORTING
            iv_application_id        = iv_application_id
            iv_instance_id           = iv_instance_id
            iv_employee_assignment   = iv_employee_assignment
            iv_requested_employee_id = iv_employee_id
          RECEIVING
            rv_access_state          = lv_access_state ).
        CASE lv_access_state.
          WHEN if_hcmfab_tcal_constants=>gc_access_state-allowed.
            rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-added.
          WHEN if_hcmfab_tcal_constants=>gc_access_state-forbidden.
            rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-rejected.
          WHEN if_hcmfab_tcal_constants=>gc_access_state-requested.
            rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-requested.
          WHEN if_hcmfab_tcal_constants=>gc_access_state-restricted.
            IF ls_personalization-display_state = if_hcmfab_tcal_constants=>gc_display_state-requested.
*             requested remains requested
              rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-requested.
            ELSE.
              rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-rejected.
            ENDIF.
        ENDCASE.
      ENDIF.
    ENDIF.
  ELSE.
*   no personalization for this employee (default is visible)
    rv_display_state = if_hcmfab_tcal_constants=>gc_display_state-visible.
  ENDIF.


ENDMETHOD.
