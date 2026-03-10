METHOD change_employee_display_state.

  DATA: ls_personalization_entry TYPE hcmfab_d_tcalper.

  CASE iv_display_state.

    WHEN if_hcmfab_tcal_constants=>gc_display_state-deleted
      OR if_hcmfab_tcal_constants=>gc_display_state-visible.
*     personalization entry can be deleted
      DELETE FROM hcmfab_d_tcalper
        WHERE emp_assignment = iv_employee_assignment
        AND view_type = iv_view_type
        AND view_id = iv_view_id
        AND employee_id = iv_employee_id.

    WHEN if_hcmfab_tcal_constants=>gc_display_state-added
      OR if_hcmfab_tcal_constants=>gc_display_state-hidden
      OR if_hcmfab_tcal_constants=>gc_display_state-requested.
*     add/update personalization entry
      ls_personalization_entry-mandt = sy-mandt.
      ls_personalization_entry-emp_assignment = iv_employee_assignment.
      ls_personalization_entry-view_type = iv_view_type.
      ls_personalization_entry-view_id = iv_view_id.
      ls_personalization_entry-employee_id = iv_employee_id.
      ls_personalization_entry-display_state = iv_display_state.
      MODIFY hcmfab_d_tcalper FROM ls_personalization_entry.

  ENDCASE.

ENDMETHOD.
