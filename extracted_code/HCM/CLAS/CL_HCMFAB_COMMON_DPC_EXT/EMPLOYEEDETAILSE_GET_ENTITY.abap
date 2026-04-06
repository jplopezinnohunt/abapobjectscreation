method EMPLOYEEDETAILSE_GET_ENTITY.

  DATA: lv_pernr           TYPE pernr_d,
        lv_pernr_employee  type pernr_d,
        lv_for_manager     TYPE boole_d,
        lt_key             TYPE /iwbep/t_mgw_tech_pairs,
        ls_key             TYPE /iwbep/s_mgw_tech_pair,
        lt_navigation_path TYPE /iwbep/t_mgw_tech_navi,
        lx_exception       TYPE REF TO cx_static_check,
        lv_application_id  Type  hcmfab_application_id.


  FIELD-SYMBOLS: <ls_navigation_path> TYPE /iwbep/s_mgw_tech_navi.


  CLEAR: er_entity, es_response_context.

  TRY.
      me->set_no_cache( ).

      lt_navigation_path = io_tech_request_context->get_navigation_path( ).
      LOOP AT lt_navigation_path ASSIGNING <ls_navigation_path>
                                 WHERE nav_prop = 'TOEMPLOYEEDETAILS'
                                    OR nav_prop = 'TOMANAGER'.
        EXIT.
      ENDLOOP.
      IF sy-subrc = 0.
        "navigation path
        lt_key = io_tech_request_context->get_source_keys( ).
        LOOP AT lt_key INTO ls_key.
          CASE ls_key-name.
            WHEN 'APPLICATION_ID'.
              lv_application_id = ls_key-value.
            WHEN 'EMPLOYEE_NUMBER'.
              lv_pernr_employee = ls_key-value.
          ENDCASE.
        ENDLOOP.
        IF lv_pernr_employee is initial or lv_application_id is initial.
          RAISE EXCEPTION TYPE cx_hcmfab_common
            EXPORTING
              textid         = cx_hcmfab_common=>missing_key_information
              mv_entity_name = io_tech_request_context->get_entity_type_name( ).
        ENDIF.

*       check whether employee details to be read for the manager of the PERNR
        lv_for_manager = boolc( <ls_navigation_path>-nav_prop = 'TOMANAGER' ).

      ELSE.
        lt_key = io_tech_request_context->get_keys( ).
        LOOP AT lt_key INTO ls_key.
          CASE ls_key-name.
            WHEN 'APPLICATION_ID'.
              lv_application_id = ls_key-value.
            WHEN 'EMPLOYEE_NUMBER'.
              lv_pernr_employee = ls_key-value.
          ENDCASE.
        ENDLOOP.
        IF lv_pernr_employee is initial or lv_application_id is initial.
          RAISE EXCEPTION TYPE cx_hcmfab_common
            EXPORTING
              textid         = cx_hcmfab_common=>missing_key_information
              mv_entity_name = io_tech_request_context->get_entity_type_name( ).
        ENDIF.
      endif.

      IF lv_for_manager = abap_true.
        "read the details for the manager of the provided employee
        go_employee_api = cl_hcmfab_employee_api=>get_instance( ).
        lv_pernr = go_employee_api->get_employeenumber_of_manager( iv_application_id = lv_application_id
                                                                   iv_employee_pernr = lv_pernr_employee ).
        IF lv_pernr IS INITIAL.
          RETURN.
        ENDIF.
      ELSE.
        lv_pernr = lv_pernr_employee.
*       make entity usable for all Ps (note 2898715)
        "check whether PERNR actually belongs to the logon user
*        go_employee_api->do_employeenumber_validation(
*          iv_pernr          = lv_pernr
*          iv_application_id = lv_application_id ).
      ENDIF.

***********************************************************************
*     get the employee details
***********************************************************************
      er_entity =
        go_employee_api->get_employee_details( iv_application_id = lv_application_id
                                               iv_pernr          = lv_pernr ).
      er_entity-application_id = lv_application_id.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

endmethod.
