METHOD teamcalendarview_get_entityset.

  DATA: ls_filter_select_option TYPE /iwbep/s_mgw_select_option,
        ls_filter               TYPE /iwbep/s_cod_select_option,
        lv_employee_assignment  TYPE pernr_d,
        lv_filter_default       TYPE string,
        lv_application_id       TYPE hcmfab_application_id,
        lv_instance_id          TYPE hcmfab_tcal_instance_id,
        lv_view_type            TYPE hcmfab_view_type,
        lx_exception            TYPE REF TO cx_static_check,
        lt_views                TYPE cl_hcmfab_common_mpc=>tt_teamcalendarview,
        lv_first_view           TYPE boolean.

  FIELD-SYMBOLS: <ls_entity> TYPE cl_hcmfab_common_mpc=>ts_teamcalendarview,
                 <ls_view>   TYPE cl_hcmfab_common_mpc=>ts_teamcalendarview.


  CLEAR: et_entityset, es_response_context.

  me->set_no_cache( ).

* Read filter values
  LOOP AT it_filter_select_options INTO ls_filter_select_option.
    READ TABLE ls_filter_select_option-select_options INDEX 1 INTO ls_filter.
    CASE ls_filter_select_option-property.
      WHEN 'EmployeeAssignment'.
        lv_employee_assignment = ls_filter-low.
      WHEN 'InstanceId'.
        lv_instance_id = ls_filter-low.
      WHEN 'IsDefaultView'.
        lv_filter_default = ls_filter-low.
      WHEN 'ApplicationId'.
        lv_application_id = ls_filter-low.
      WHEN 'ViewType'.
        lv_view_type = ls_filter-low.
    ENDCASE.
  ENDLOOP.

  TRY.
      IF lv_employee_assignment IS INITIAL.
*       No pernr? Determine default pernr
        lv_employee_assignment = go_employee_api->get_employeenumber_from_user( ).
      ELSE.
        "check whether PERNR actually belongs to the logon user
        go_employee_api->do_employeenumber_validation(
          iv_pernr = lv_employee_assignment
          iv_application_id = lv_application_id ).
      ENDIF.

*     get all views (standard and custom)
      call method me->get_all_views(
        exporting
          iv_application_id      = lv_application_id
          iv_instance_id         = lv_instance_id
          iv_employee_assignment = lv_employee_assignment
        importing
          et_views               = lt_views
      ).

*     Filter for view type
      IF lv_view_type IS NOT INITIAL.
        DELETE lt_views WHERE view_type <> lv_view_type.
      ENDIF.

*     Verify that a default view is set and that only one is set
      lv_first_view = abap_true.
      LOOP AT lt_views ASSIGNING <ls_view> WHERE is_default_view IS NOT INITIAL.
        IF lv_first_view = abap_true.
*         First default view: Make sure that flag contains a valid value
          <ls_view>-is_default_view = abap_true.
          lv_first_view = abap_false.
        ELSE.
*         Following default views: Remove default flag
          <ls_view>-is_default_view = abap_false.
        ENDIF.
      ENDLOOP.
      IF sy-subrc <> 0.
*       No default view? Make first view the default
        READ TABLE lt_views ASSIGNING <ls_view> INDEX 1.
        IF sy-subrc = 0.
          <ls_view>-is_default_view = abap_true.
        ENDIF.
      ENDIF.


      LOOP AT lt_views ASSIGNING <ls_view>.
        APPEND INITIAL LINE TO et_entityset ASSIGNING <ls_entity>.
        MOVE-CORRESPONDING <ls_view> TO <ls_entity>.
        <ls_entity>-application_id = lv_application_id.
        <ls_entity>-instance_id = lv_instance_id.
        <ls_entity>-employee_assignment = lv_employee_assignment.

*       call extension BADI for view
        me->enrich_view(
          CHANGING
            cs_view = <ls_entity>
        ).

      ENDLOOP.

*     Filter for default view?
      IF lv_filter_default IS NOT INITIAL.
        DELETE et_entityset WHERE is_default_view <> 'X'.
      ENDIF.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.
ENDMETHOD.
