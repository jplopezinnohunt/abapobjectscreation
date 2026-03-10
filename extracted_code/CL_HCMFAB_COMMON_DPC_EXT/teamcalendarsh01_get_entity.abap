METHOD teamcalendarsh01_get_entity.

  DATA lt_keys TYPE /iwbep/t_mgw_tech_pairs.
  DATA ls_key TYPE /iwbep/s_mgw_tech_pair.
  DATA lt_navigation_path TYPE /iwbep/t_mgw_tech_navi.
  DATA lv_employee_id TYPE pernr_d.
  DATA lv_shared_employee_id TYPE pernr_d.
  DATA lv_application_id TYPE hcmfab_application_id.
  DATA lv_instance_id TYPE hcmfab_tcal_instance_id.
  DATA ls_shared_employee TYPE hcmfab_d_tcalsha.
  DATA lx_exception TYPE REF TO cx_static_check.

  lt_navigation_path = io_tech_request_context->get_navigation_path( ).
  READ TABLE lt_navigation_path WITH KEY nav_prop = 'TOTEAMCALENDARSHAREDEMPLOYEE' TRANSPORTING NO FIELDS.
  IF sy-subrc = 0.
    lt_keys = io_tech_request_context->get_source_keys( ).
  ELSE.
    lt_keys = io_tech_request_context->get_keys( ).
  ENDIF.
  LOOP AT lt_keys INTO ls_key.
    CASE ls_key-name.
      WHEN 'APPLICATION_ID'.
        lv_application_id = ls_key-value.
      WHEN 'INSTANCE_ID'.
        lv_instance_id = ls_key-value.
      WHEN 'EMPLOYEE_ID'.
        lv_employee_id = ls_key-value.
      WHEN 'SHARED_EMPLOYEE_ID'.
        lv_shared_employee_id = ls_key-value.
    ENDCASE.
  ENDLOOP.

  TRY.
      SELECT SINGLE * FROM hcmfab_d_tcalsha INTO ls_shared_employee
        WHERE employee_id = lv_employee_id AND shared_employee_id = lv_shared_employee_id.

      er_entity-application_id = lv_application_id.
      er_entity-instance_id = lv_instance_id.
      er_entity-employee_id = lv_employee_id.
      er_entity-shared_employee_id = lv_shared_employee_id.
      er_entity-status = ls_shared_employee-share_state.
      er_entity-name = go_employee_api->get_name(
          iv_pernr         = ls_shared_employee-shared_employee_id
          iv_no_auth_check = abap_true "note 3413385
      ).
      er_entity-sort_name = go_employee_api->get_sortable_name(
          iv_pernr         = ls_shared_employee-shared_employee_id
          iv_no_auth_check = abap_true
      ).
      CALL BADI go_badi_tcal_settings->get_employee_description
        EXPORTING
          iv_application_id      = lv_application_id
          iv_instance_id         = lv_instance_id
          iv_employee_assignment = lv_employee_id
          iv_employee_id         = lv_shared_employee_id
        RECEIVING
          ev_description         = er_entity-description.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
