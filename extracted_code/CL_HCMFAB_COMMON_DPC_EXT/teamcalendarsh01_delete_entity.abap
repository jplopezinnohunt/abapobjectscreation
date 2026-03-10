METHOD teamcalendarsh01_delete_entity.

  DATA lt_key_tab TYPE /iwbep/t_mgw_tech_pairs.
  DATA ls_tech_key TYPE /iwbep/s_mgw_tech_pair.
  DATA lv_employee_id TYPE pernr_d.
  DATA lv_shared_employee_id TYPE pernr_d.
  DATA lv_application_id TYPE hcmfab_application_id.
  DATA lx_exception TYPE REF TO cx_static_check.
  DATA lv_approval_mode TYPE hcmfab_tcal_approval_mode.

* get the key fields
  lt_key_tab = io_tech_request_context->get_keys( ).
  LOOP AT lt_key_tab INTO ls_tech_key.
    CASE ls_tech_key-name.
      WHEN 'EMPLOYEE_ID'.
        lv_employee_id = ls_tech_key-value.
      WHEN 'SHARED_EMPLOYEE_ID'.
        lv_shared_employee_id = ls_tech_key-value.
      WHEN 'APPLICATION_ID'.
        lv_application_id = ls_tech_key-value.
    ENDCASE.
  ENDLOOP.

* do employee validation
  TRY.
      go_employee_api->do_employeenumber_validation(
              iv_pernr          = lv_employee_id
              iv_application_id = lv_application_id ).
    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

* remove the sharing
  CALL METHOD cl_hcmfab_common_dpc_ext=>remove_tcal_sharing
    EXPORTING
      iv_employee_id        = lv_employee_id
      iv_shared_employee_id = lv_shared_employee_id.

* cancel corresponding workflow requests
  CALL BADI go_badi_tcal_settings->get_approval_settings
    IMPORTING
      ev_approval_mode = lv_approval_mode.
  IF lv_approval_mode = if_hcmfab_tcal_constants=>gc_approval_mode-workflow.
    CALL BADI go_badi_tcal_settings->cancel_approval
      EXPORTING
        iv_requester_pernr = lv_shared_employee_id
        iv_approver_pernr  = lv_employee_id
        iv_approval_state  = if_hcmfab_tcal_constants=>gc_approval_state-rejected.
  ENDIF.

ENDMETHOD.
