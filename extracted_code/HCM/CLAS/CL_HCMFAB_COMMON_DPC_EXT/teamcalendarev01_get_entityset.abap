METHOD teamcalendarev01_get_entityset.

  DATA: lv_employee_assignment  TYPE pernr_d,
        lv_application_id       TYPE hcmfab_application_id,
        lv_instance_id          TYPE hcmfab_tcal_instance_id,
        lv_view_type            TYPE hcmfab_view_type,
        lv_view_id              TYPE hcmfab_view_id,
        ls_key                  TYPE /iwbep/s_mgw_name_value_pair,
        ls_type                 TYPE cl_hcmfab_common_mpc=>ts_teamcalendareventtype,
        lt_event_type           TYPE hcmfab_t_tcal_event_type,
        ls_event_type           TYPE hcmfab_s_tcal_event_type,
        lt_views                TYPE cl_hcmfab_common_mpc=>tt_teamcalendarview,
        ls_view                 TYPE hcmfab_s_tcal_view_ui,
        ls_filter_select_option TYPE /iwbep/s_mgw_select_option,
        ls_filter               TYPE /iwbep/s_cod_select_option,
        lx_exception            TYPE REF TO cx_static_check.


  CLEAR: et_entityset, es_response_context.

  me->set_no_cache( ).

  IF lines( it_navigation_path ) > 0.
*   expand 'ToTeamCalendarEventType' is executed => evaluate the key fields
    READ TABLE it_key_tab INTO ls_key WITH KEY name = 'EmployeeAssignment'.
    lv_employee_assignment = ls_key-value.
    READ TABLE it_key_tab INTO ls_key WITH KEY name = 'ApplicationId'.
    lv_application_id = ls_key-value.
    READ TABLE it_key_tab INTO ls_key WITH KEY name = 'InstanceId'.
    lv_instance_id = ls_key-value.
    READ TABLE it_key_tab INTO ls_key WITH KEY name = 'ViewType'.
    lv_view_type = ls_key-value.
    READ TABLE it_key_tab INTO ls_key WITH KEY name = 'ViewId'.
    lv_view_id = ls_key-value.
  ELSE.
*   standard getEntitySet call => evaluate the filter fields
    LOOP AT it_filter_select_options INTO ls_filter_select_option.
      READ TABLE ls_filter_select_option-select_options INDEX 1 INTO ls_filter.
      CASE ls_filter_select_option-property.
        WHEN 'EmployeeAssignment'.
          lv_employee_assignment = ls_filter-low.
        WHEN 'ApplicationId'.
          lv_application_id = ls_filter-low.
        WHEN 'InstanceId'.
          lv_instance_id = ls_filter-low.
        WHEN 'ViewType'.
          lv_view_type = ls_filter-low.
        WHEN 'ViewId'.
          lv_view_id = ls_filter-low.
      ENDCASE.
    ENDLOOP.
  ENDIF.
  TRY.
      "check whether PERNR actually belongs to the logon user
      go_employee_api->do_employeenumber_validation(
        iv_pernr          = lv_employee_assignment
        iv_application_id = lv_application_id ).

      IF lv_view_id IS INITIAL.
*       no filter provided for view -> read event types for all views
*       get all views (standard and custom)
        CALL METHOD me->get_all_views(
          EXPORTING
            iv_application_id      = lv_application_id
            iv_instance_id         = lv_instance_id
            iv_employee_assignment = lv_employee_assignment
          IMPORTING
            et_views               = lt_views ).
      ELSE.
*       read data only for the given view
        ls_view-view_id = lv_view_id.
        ls_view-view_type = lv_view_type.
        APPEND ls_view TO lt_views.
      ENDIF.

      LOOP AT lt_views INTO ls_view.
*       call BADI to get the event types and categories
        CLEAR lt_event_type.
        CALL BADI go_badi_tcal_settings->get_event_types
          EXPORTING
            iv_application_id      = lv_application_id
            iv_instance_id         = lv_instance_id
            iv_employee_assignment = lv_employee_assignment
            iv_view_type           = ls_view-view_type
            iv_view_id             = ls_view-view_id
          IMPORTING
            et_event_types         = lt_event_type.

*       fill entity set
        ls_type-application_id = lv_application_id.
        ls_type-employee_assignment = lv_employee_assignment.
        ls_type-instance_id = lv_instance_id.
        ls_type-view_id = ls_view-view_id.
        ls_type-view_type = ls_view-view_type.
        LOOP AT lt_event_type INTO ls_event_type.
          ls_type-event_type = ls_event_type-color_type.
          ls_type-description = ls_event_type-description.
          ls_type-is_relevant_for_absence = ls_event_type-is_relevant_for_absence.
          ls_type-icon = ls_event_type-icon.
          ls_type-show_as_non_working_day = ls_event_type-show_as_non_working_day.
          ls_type-use_for_new_requested_leave = ls_event_type-use_for_new_requested_leave.
          ls_type-color = ls_event_type-color.
          ls_type-detailfields = ls_event_type-detailfields.
          ls_type-detailfield_labels = ls_event_type-detailfield_labels.

*         call extension BADI for event type
          me->enrich_event_type(
            CHANGING
              cs_event_type = ls_type
          ).

          APPEND ls_type TO et_entityset.
        ENDLOOP.
      ENDLOOP.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.
ENDMETHOD.
