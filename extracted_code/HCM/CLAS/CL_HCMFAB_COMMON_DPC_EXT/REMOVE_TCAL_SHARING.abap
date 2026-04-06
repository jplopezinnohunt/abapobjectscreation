method REMOVE_TCAL_SHARING.

  DATA lt_updated_employees TYPE TABLE OF hcmfab_d_tcalper.
  FIELD-SYMBOLS <ls_updated_employee> TYPE hcmfab_d_tcalper.

* remove database entry
  DELETE FROM hcmfab_d_tcalsha WHERE employee_id = iv_employee_id AND shared_employee_id = iv_shared_employee_id.

* employee_id has not allowed iv_shared_employee to see his data in teamcalendar
* update STATE for employee_id in all custom views created by user iv_shared_employee.
  SELECT * FROM hcmfab_d_tcalper INTO TABLE lt_updated_employees
    WHERE emp_assignment = iv_shared_employee_id AND employee_id = iv_employee_id.

  LOOP AT lt_updated_employees ASSIGNING <ls_updated_employee>.
      <ls_updated_employee>-display_state = if_hcmfab_tcal_constants=>gc_display_state-rejected.
    UPDATE hcmfab_d_tcalper FROM <ls_updated_employee>.
  ENDLOOP.

endmethod.
