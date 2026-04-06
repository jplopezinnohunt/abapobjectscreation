METHOD get_tcal_access_state.
  DATA ls_shared_employee TYPE hcmfab_d_tcalsha.
  DATA lv_is_in_standard_view TYPE boolean.
  DATA lv_approval_mode TYPE hcmfab_tcal_approval_mode.
  DATA lv_share_mode TYPE hcmfab_tcal_emp_share_mode.

* get approval mode
  CALL BADI go_badi_tcal_settings->get_approval_settings
    IMPORTING
      ev_approval_mode = lv_approval_mode.

* get share mode for requested employee
  CALL METHOD me->get_employee_share_mode
    EXPORTING
      iv_employee_id = iv_requested_employee_id
    IMPORTING
      ev_share_mode  = lv_share_mode.

* determine if the employee is allowed to see the data
  IF lv_approval_mode = if_hcmfab_tcal_constants=>gc_approval_mode-none OR lv_share_mode = if_hcmfab_tcal_constants=>gc_emp_share_mode-all.
*   data access is allowed
    rv_access_state = if_hcmfab_tcal_constants=>gc_access_state-allowed.
  ELSE.
*   check if employee is included in the standard views
    CALL METHOD me->is_employee_in_standard_view
      EXPORTING
        iv_application_id      = iv_application_id
        iv_instance_id         = iv_instance_id
        iv_employee_assignment = iv_employee_assignment
        iv_requester_id        = iv_employee_assignment
        iv_employee_id         = iv_requested_employee_id
      RECEIVING
        rt_is_in_standard_view = lv_is_in_standard_view.
    IF lv_is_in_standard_view = abap_true.
      rv_access_state = if_hcmfab_tcal_constants=>gc_access_state-allowed.
    ELSEIF lv_share_mode = if_hcmfab_tcal_constants=>gc_emp_share_mode-none.
      rv_access_state = if_hcmfab_tcal_constants=>gc_access_state-forbidden.
    ELSE.
*     check if requested employee has already allowed to see the data
      CLEAR ls_shared_employee.
      SELECT SINGLE * FROM hcmfab_d_tcalsha INTO ls_shared_employee
        WHERE employee_id = iv_requested_employee_id AND shared_employee_id = iv_employee_assignment.
      IF ls_shared_employee-share_state = if_hcmfab_tcal_constants=>gc_emp_share_state-allowed.
*       already allowed
        rv_access_state = if_hcmfab_tcal_constants=>gc_access_state-allowed.
      ELSEIF ls_shared_employee-share_state = if_hcmfab_tcal_constants=>gc_emp_share_state-undecided.
*       already requested
        rv_access_state = if_hcmfab_tcal_constants=>gc_access_state-requested.
      ELSE.
*       not yet allowed
        rv_access_state = if_hcmfab_tcal_constants=>gc_access_state-restricted.
      ENDIF.
    ENDIF.
  ENDIF.

ENDMETHOD.
