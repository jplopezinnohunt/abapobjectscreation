METHOD teamcalendarempl_get_entityset.

  DATA: ls_entity               TYPE cl_hcmfab_common_mpc=>ts_teamcalendaremployee,
        ls_key                  TYPE /iwbep/s_mgw_name_value_pair,
        ls_filter_select_option TYPE /iwbep/s_mgw_select_option,
        ls_filter               TYPE /iwbep/s_cod_select_option,
        lv_view_id              TYPE hcmfab_view_id,
        lv_view_type            TYPE hcmfab_view_type,
        lv_application_id       TYPE hcmfab_application_id,
        lv_employee_assignment  TYPE pernr_d,
        lv_instance_id          TYPE hcmfab_tcal_instance_id,
        lv_requester_id         TYPE pernr_d,
        lt_employees            TYPE hcmfab_t_tcal_employee,
        ls_employee             TYPE hcmfab_s_tcal_employee,
        lx_exception            TYPE REF TO cx_static_check,
        lv_root_object_mode     TYPE hcmfab_tcal_root_mode,
        lv_root_pernr           TYPE pernr_d.

  CLEAR: et_entityset, es_response_context.

* Read from a navigation property?
  READ TABLE it_key_tab INTO ls_key WITH KEY name = 'ViewId'.
  IF sy-subrc = 0.
    lv_view_id = ls_key-value.
  ENDIF.
  READ TABLE it_key_tab INTO ls_key WITH KEY name = 'ViewType'.
  IF sy-subrc = 0.
    lv_view_type = ls_key-value.
  ENDIF.
  READ TABLE it_key_tab INTO ls_key WITH KEY name = 'ApplicationId'.
  IF sy-subrc = 0.
    lv_application_id = ls_key-value.
  ENDIF.
  READ TABLE it_key_tab INTO ls_key WITH KEY name = 'EmployeeAssignment'.
  IF sy-subrc = 0.
    lv_employee_assignment = ls_key-value.
  ENDIF.
  READ TABLE it_key_tab INTO ls_key WITH KEY name = 'InstanceId'.
  IF sy-subrc = 0.
    lv_instance_id = ls_key-value.
  ENDIF.
  READ TABLE it_key_tab INTO ls_key WITH KEY name = 'RequesterId'.
  IF sy-subrc = 0.
    lv_requester_id = ls_key-value.
  ENDIF.


  LOOP AT it_filter_select_options INTO ls_filter_select_option.
    READ TABLE ls_filter_select_option-select_options INDEX 1 INTO ls_filter.
    CASE ls_filter_select_option-property.
      WHEN 'ViewId'.
        lv_view_id = ls_filter-low.
      WHEN 'ViewType'.
        lv_view_type = ls_filter-low.
      WHEN 'EmployeeAssignment'.
        lv_employee_assignment = ls_filter-low.
      WHEN 'ApplicationId'.
        lv_application_id = ls_filter-low.
      WHEN 'InstanceId'.
        lv_instance_id = ls_filter-low.
      WHEN 'RequesterId'.
        lv_requester_id = ls_filter-low.
    ENDCASE.
  ENDLOOP.

  TRY.
      IF lv_employee_assignment IS INITIAL.
*       No pernr? Determine default pernr
        lv_employee_assignment = go_employee_api->get_employeenumber_from_user( ).
      ELSE.
        "check whether PERNR actually belongs to the logon user
        go_employee_api->do_employeenumber_validation(
          iv_pernr          = lv_employee_assignment
          iv_application_id = lv_application_id ).
      ENDIF.

      IF lv_view_id IS INITIAL.
        RETURN. "ex
      ENDIF.

*     read the employees
      CALL METHOD me->get_employees
        EXPORTING
          iv_application_id      = lv_application_id
          iv_instance_id         = lv_instance_id
          iv_employee_assignment = lv_employee_assignment
          iv_view_id             = lv_view_id
          iv_view_type           = lv_view_type
          iv_requester_id        = lv_requester_id
        IMPORTING
          et_employees           = lt_employees.

*     fill the entity set
      ls_entity-application_id = lv_application_id.
      ls_entity-employee_assignment = lv_employee_assignment.
      ls_entity-instance_id = lv_instance_id.
      ls_entity-requester_id = lv_requester_id.
      ls_entity-view_id = lv_view_id.
      ls_entity-view_type = lv_view_type.
      LOOP AT lt_employees INTO ls_employee.
        ls_entity-employee_id = ls_employee-employee_id.
        ls_entity-name = ls_employee-name.
        ls_entity-sort_name = ls_employee-sort_name.
        ls_entity-description = ls_employee-description.
        ls_entity-tooltip = ls_employee-tooltip.            "AE2650135
        ls_entity-display_state = ls_employee-display_state.
        ls_entity-start_date = gc_low_date.
        ls_entity-end_date = gc_high_date.

*       call the extension BADI
        me->enrich_employee(
          CHANGING
            cs_employee = ls_entity
        ).

        APPEND ls_entity TO et_entityset.
      ENDLOOP.

*     sort employee table and put root PERNR on first position (note 3133516)
      SORT et_entityset BY sort_name.
*     determine root pernr
      lv_root_object_mode = me->get_root_mode_for_view(
          iv_application_id      = lv_application_id
          iv_instance_id         = lv_instance_id
          iv_employee_assignment = lv_employee_assignment
          iv_view_type           = lv_view_type
          iv_view_id             = lv_view_id ).
      IF lv_root_object_mode = gc_root_mode-requester.
        lv_root_pernr = lv_requester_id.
      ELSE.
        lv_root_pernr = lv_employee_assignment.
      ENDIF.
      READ TABLE et_entityset INTO ls_entity
                              WITH KEY employee_id = lv_root_pernr.
      IF sy-subrc = 0 AND
         sy-tabix <> 1.
        DELETE et_entityset INDEX sy-tabix.
        INSERT ls_entity INTO et_entityset INDEX 1.
      ENDIF.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
