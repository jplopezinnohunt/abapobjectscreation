METHOD teamcalendarsh01_get_entityset.

  DATA ls_filter_select_option TYPE /iwbep/s_mgw_select_option.
  DATA ls_filter TYPE /iwbep/s_cod_select_option.
  DATA lt_keys TYPE /iwbep/t_mgw_tech_pairs.
  DATA ls_key TYPE /iwbep/s_mgw_tech_pair.
  DATA lt_navigation_path TYPE /iwbep/t_mgw_tech_navi.
  DATA lv_employee_id TYPE pernr_d.
  DATA lv_application_id TYPE hcmfab_application_id.
  DATA lv_instance_id TYPE hcmfab_tcal_instance_id.
  DATA lv_filter_default TYPE string.
  DATA lx_exception TYPE REF TO cx_static_check.
  DATA ls_entity TYPE cl_hcmfab_common_mpc=>ts_teamcalendarsharedemployee.
  DATA ls_shared_employee TYPE hcmfab_d_tcalsha.
  DATA lt_shared_employees TYPE STANDARD TABLE OF hcmfab_d_tcalsha.

  CLEAR: et_entityset, es_response_context.

  me->set_no_cache( ).

  lt_navigation_path = io_tech_request_context->get_navigation_path( ).
  READ TABLE lt_navigation_path WITH KEY nav_prop = 'TOTEAMCALENDARSHAREDEMPLOYEE' TRANSPORTING NO FIELDS.
  IF sy-subrc = 0.
    "navigation path
    lt_keys = io_tech_request_context->get_source_keys( ).
    LOOP AT lt_keys INTO ls_key.
      CASE ls_key-name.
        WHEN 'APPLICATION_ID'.
          lv_application_id = ls_key-value.
        WHEN 'INSTANCE_ID'.
          lv_instance_id = ls_key-value.
        WHEN 'EMPLOYEE_ID'.
          lv_employee_id = ls_key-value.
      ENDCASE.
    ENDLOOP.
  ELSE.
*   Read filter values
    LOOP AT it_filter_select_options INTO ls_filter_select_option.
      READ TABLE ls_filter_select_option-select_options INDEX 1 INTO ls_filter.
      CASE ls_filter_select_option-property.
        WHEN 'ApplicationId'.
          lv_application_id = ls_filter-low.
        WHEN 'InstanceId'.
          lv_instance_id = ls_filter-low.
        WHEN 'EmployeeId'.
          lv_employee_id = ls_filter-low.
      ENDCASE.
    ENDLOOP.
  ENDIF.

  TRY.
      SELECT * FROM hcmfab_d_tcalsha INTO TABLE lt_shared_employees
        WHERE employee_id = lv_employee_id.

      LOOP AT lt_shared_employees INTO ls_shared_employee.
        ls_entity-application_id = lv_application_id.
        ls_entity-instance_id = lv_instance_id.
        ls_entity-employee_id = lv_employee_id.
        ls_entity-shared_employee_id = ls_shared_employee-shared_employee_id.
        ls_entity-status = ls_shared_employee-share_state.
        ls_entity-name = go_employee_api->get_name(
            iv_pernr         = ls_shared_employee-shared_employee_id
            iv_no_auth_check = abap_true "note 3413385
        ).
        ls_entity-sort_name = go_employee_api->get_sortable_name(
            iv_pernr         = ls_shared_employee-shared_employee_id
            iv_no_auth_check = abap_true
        ).
        CALL BADI go_badi_tcal_settings->get_employee_description
          EXPORTING
            iv_application_id      = lv_application_id
            iv_instance_id         = lv_instance_id
            iv_employee_assignment = ls_shared_employee-employee_id
            iv_employee_id         = ls_shared_employee-shared_employee_id
          RECEIVING
            ev_description         = ls_entity-description.
        APPEND ls_entity TO et_entityset.
      ENDLOOP.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
