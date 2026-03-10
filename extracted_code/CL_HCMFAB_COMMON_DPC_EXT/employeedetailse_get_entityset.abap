METHOD employeedetailse_get_entityset.

  DATA  ls_key                   TYPE /iwbep/s_mgw_name_value_pair.
  DATA  ls_filter                TYPE /iwbep/s_mgw_select_option.
  DATA  ls_select                TYPE /iwbep/s_cod_select_option.
  DATA  lt_filter_select_options TYPE /iwbep/t_mgw_select_option.
  DATA  lo_filter                TYPE REF TO /iwbep/if_mgw_req_filter.
  DATA: lv_pernr                 TYPE pernr_d,
        ls_entity                TYPE cl_hcmfab_common_mpc=>ts_employeedetail,
        lx_exception             TYPE REF TO cx_static_check.
  DATA  lv_application_id        TYPE hcmfab_application_id.

  CLEAR: et_entityset, es_response_context.

* Read from a navigation property?
  READ TABLE it_key_tab INTO ls_key WITH KEY name = 'ApplicationId'.
  IF sy-subrc = 0.
    lv_application_id = ls_key-value.
  ENDIF.
  READ TABLE it_key_tab INTO ls_key WITH KEY name = 'EmployeeAssignment'.
  IF sy-subrc = 0.
    lv_pernr = ls_key-value.
  ENDIF.

  TRY.
      me->set_no_cache( ).

      lo_filter = io_tech_request_context->get_filter( ).
      lt_filter_select_options = lo_filter->get_filter_select_options( ).

      LOOP AT lt_filter_select_options INTO ls_filter.
        READ TABLE ls_filter-select_options INTO ls_select INDEX 1 TRANSPORTING low.
        CASE ls_filter-property.
          WHEN 'EMPLOYEE_NUMBER'.
            lv_pernr = ls_select-low.
          WHEN 'APPLICATION_ID'.
            lv_application_id = ls_select-low.
        ENDCASE.
      ENDLOOP.

      IF lv_pernr IS INITIAL.
        lv_pernr = cl_hcmfab_persinfo_dpc_util=>get_pernr( io_tech_req_context_entityset = io_tech_request_context ).
      ENDIF.
*     make entity usable for all Ps (note 2898715)
      "check whether PERNR actually belongs to the logon user
*      go_employee_api->do_employeenumber_validation(
*        iv_pernr          = lv_pernr
*        iv_application_id = lv_application_id ).

***********************************************************************
*     get the employee details
***********************************************************************
      ls_entity = go_employee_api->get_employee_details( iv_application_id = lv_application_id
                                                          iv_pernr          = lv_pernr ).
      ls_entity-application_id = lv_application_id.
      APPEND ls_entity TO et_entityset.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.


ENDMETHOD.
