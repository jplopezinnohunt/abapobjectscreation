METHOD teamcalendarshar_update_entity.
  DATA ls_share_mode TYPE hcmfab_s_tcal_share_mode.
  DATA ls_share_mode_db TYPE hcmfab_d_tcalmod.
  DATA lx_exception TYPE REF TO cx_static_check.
  DATA lt_undecided_shared_employees TYPE STANDARD TABLE OF hcmfab_d_tcalsha.
  DATA ls_undecided_shared_employee TYPE hcmfab_d_tcalsha.
  DATA lv_approval_mode TYPE hcmfab_tcal_approval_mode.

* retrieve the new employee data
  CALL METHOD io_data_provider->read_entry_data
    IMPORTING
      es_data = ls_share_mode.

* do employee validation
  TRY.
      go_employee_api->do_employeenumber_validation(
              iv_pernr          = ls_share_mode-employee_id
              iv_application_id = ls_share_mode-application_id ).
    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

* store new mode in data base
  ls_share_mode_db-mandt = sy-mandt.
  MOVE-CORRESPONDING ls_share_mode TO ls_share_mode_db.
  MODIFY hcmfab_d_tcalmod FROM ls_share_mode_db.

* when share mode is set to NONE -> cancel all pending requests
  IF ls_share_mode-share_mode = if_hcmfab_tcal_constants=>gc_emp_share_mode-none.
    SELECT * FROM hcmfab_d_tcalsha INTO TABLE lt_undecided_shared_employees
      WHERE employee_id = ls_share_mode-employee_id AND share_state = if_hcmfab_tcal_constants=>gc_emp_share_state-undecided.
    LOOP AT lt_undecided_shared_employees INTO ls_undecided_shared_employee.
      CALL METHOD cl_hcmfab_common_dpc_ext=>remove_tcal_sharing
        EXPORTING
          iv_employee_id        = ls_share_mode-employee_id
          iv_shared_employee_id = ls_undecided_shared_employee-shared_employee_id.

*     cancel corresponding workflow requests
      CALL BADI go_badi_tcal_settings->get_approval_settings
        IMPORTING
          ev_approval_mode = lv_approval_mode.
      IF lv_approval_mode = if_hcmfab_tcal_constants=>gc_approval_mode-workflow.
        CALL BADI go_badi_tcal_settings->cancel_approval
          EXPORTING
            iv_requester_pernr = ls_undecided_shared_employee-shared_employee_id
            iv_approver_pernr  = ls_share_mode-employee_id
            iv_approval_state  = if_hcmfab_tcal_constants=>gc_approval_state-rejected.
      ENDIF.
    ENDLOOP.
  ENDIF.

* fill result entity
  er_entity-application_id = ls_share_mode-application_id.
  er_entity-instance_id = ls_share_mode-instance_id.
  er_entity-employee_id = ls_share_mode-employee_id.
  er_entity-share_mode = ls_share_mode-share_mode.

ENDMETHOD.
