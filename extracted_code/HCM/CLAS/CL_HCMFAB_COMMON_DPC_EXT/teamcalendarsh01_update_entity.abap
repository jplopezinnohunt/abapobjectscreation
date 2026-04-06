METHOD teamcalendarsh01_update_entity.

  DATA ls_shared_employee TYPE hcmfab_s_tcal_shared_employee.
  DATA lx_exception TYPE REF TO cx_static_check.
  DATA lv_approval_mode TYPE hcmfab_tcal_approval_mode.

* retrieve the new data
  CALL METHOD io_data_provider->read_entry_data
    IMPORTING
      es_data = ls_shared_employee.

* only change to allowed is possible
  IF ls_shared_employee-status <> if_hcmfab_tcal_constants=>gc_emp_share_state-allowed.
    RETURN.
  ENDIF.

* do employee validation
  TRY.
      go_employee_api->do_employeenumber_validation(
              iv_pernr          = ls_shared_employee-employee_id
              iv_application_id = ls_shared_employee-application_id ).
    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

* allow sharing
  CALL METHOD cl_hcmfab_common_dpc_ext=>add_tcal_sharing
    EXPORTING
      iv_employee_id        = ls_shared_employee-employee_id
      iv_shared_employee_id = ls_shared_employee-shared_employee_id.

* cancel corresponding workflow requests
  CALL BADI go_badi_tcal_settings->get_approval_settings
    IMPORTING
      ev_approval_mode = lv_approval_mode.
  IF lv_approval_mode = if_hcmfab_tcal_constants=>gc_approval_mode-workflow.
    CALL BADI go_badi_tcal_settings->cancel_approval
      EXPORTING
        iv_requester_pernr = ls_shared_employee-shared_employee_id
        iv_approver_pernr  = ls_shared_employee-employee_id
        iv_approval_state = if_hcmfab_tcal_constants=>gc_approval_state-approved.
  ENDIF.

* fill result entity
  er_entity = ls_shared_employee.

ENDMETHOD.
