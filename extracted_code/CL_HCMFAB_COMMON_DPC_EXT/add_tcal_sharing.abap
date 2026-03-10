METHOD add_tcal_sharing.

  DATA ls_shared_employee_db TYPE hcmfab_d_tcalsha.
  DATA lt_updated_employees TYPE TABLE OF hcmfab_d_tcalper.
  FIELD-SYMBOLS <ls_updated_employee> TYPE hcmfab_d_tcalper.

* store mode in data base
  ls_shared_employee_db-mandt = sy-mandt.
  ls_shared_employee_db-employee_id = iv_employee_id.
  ls_shared_employee_db-shared_employee_id = iv_shared_employee_id.
  ls_shared_employee_db-share_state = if_hcmfab_tcal_constants=>gc_emp_share_state-allowed.
  MODIFY hcmfab_d_tcalsha FROM ls_shared_employee_db.

* employee_id has allowed iv_shared_employee to see his data in teamcalendar
* update STATE for employee_id in all custom views created by user iv_shared_employee.
  SELECT * FROM hcmfab_d_tcalper INTO TABLE lt_updated_employees
    WHERE emp_assignment = iv_shared_employee_id AND employee_id = iv_employee_id.

  LOOP AT lt_updated_employees ASSIGNING <ls_updated_employee>.
    <ls_updated_employee>-display_state = if_hcmfab_tcal_constants=>gc_display_state-added.
    UPDATE hcmfab_d_tcalper FROM <ls_updated_employee>.
  ENDLOOP.

ENDMETHOD.
