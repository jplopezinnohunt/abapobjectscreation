METHOD teamcalendarsh01_create_entity.

  DATA ls_shared_employee TYPE hcmfab_s_tcal_shared_employee.
  DATA lx_exception TYPE REF TO cx_static_check.

* retrieve the new data
  CALL METHOD io_data_provider->read_entry_data
    IMPORTING
      es_data = ls_shared_employee.

* do employee validation
  TRY.
      go_employee_api->do_employeenumber_validation(
              iv_pernr          = ls_shared_employee-employee_id
              iv_application_id = ls_shared_employee-application_id ).

*     allow sharing
      CALL METHOD cl_hcmfab_common_dpc_ext=>add_tcal_sharing
        EXPORTING
          iv_employee_id        = ls_shared_employee-employee_id
          iv_shared_employee_id = ls_shared_employee-shared_employee_id.

*     fill result entity
      er_entity = ls_shared_employee.
      er_entity-name = go_employee_api->get_name(
          iv_pernr         = ls_shared_employee-shared_employee_id
      ).
      er_entity-sort_name = go_employee_api->get_sortable_name(
          iv_pernr         = ls_shared_employee-shared_employee_id
      ).
      CALL BADI go_badi_tcal_settings->get_employee_description
        EXPORTING
          iv_application_id      = ls_shared_employee-application_id
          iv_instance_id         = ls_shared_employee-instance_id
          iv_employee_assignment = ls_shared_employee-employee_id
          iv_employee_id         = ls_shared_employee-shared_employee_id
        RECEIVING
          ev_description         = er_entity-description.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
