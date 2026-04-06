METHOD apply_onbehalf_filters.

  DATA: lt_properties         TYPE TABLE OF string,
        lv_property           TYPE string,
        lo_request            TYPE REF TO /iwbep/cl_mgw_request,
        ls_request_detail     TYPE /iwbep/if_mgw_core_srv_runtime=>ty_s_mgw_request_context,
        lv_service_name       TYPE /iwbep/med_grp_technical_name,
        lo_model              TYPE REF TO /iwbep/if_mgw_odata_re_model,
        lo_entity             TYPE REF TO /iwbep/if_mgw_odata_re_etype,
        lt_odata_properties   TYPE /iwbep/if_mgw_odata_re_prop=>ty_t_mgw_odata_properties,
        lt_onbehalf_employees TYPE cl_hcmfab_common_mpc=>tt_onbehalfemployee,
        lv_value              TYPE string.

  FIELD-SYMBOLS: <ls_onbehalf>       TYPE cl_hcmfab_common_mpc=>ts_onbehalfemployee,
                 <ls_odata_property> TYPE /iwbep/if_mgw_odata_re_prop=>ty_s_mgw_odata_property,
                 <lv_value>          TYPE any.

* Nothing to do
  IF iv_search_string IS INITIAL.
    RETURN.
  ENDIF.

* Try to fetch the odata model, so that we can convert frontend property names to the ABAP names
  TRY.
      lo_request ?= io_tech_request.
      ls_request_detail = lo_request->get_request_details( ).
      lv_service_name = ls_request_detail-service_doc_name.
      lo_model = /iwbep/cl_mgw_med_provider=>get_med_provider( )->get_service_metadata(
        iv_internal_service_name    = lv_service_name
        iv_internal_service_version = ls_request_detail-version
      ).
      lo_entity = lo_model->get_entity_type( 'OnBehalfEmployee' ).
      lt_odata_properties = lo_entity->get_properties( ).
    CATCH cx_sy_move_cast_error.
    CATCH /iwbep/cx_mgw_med_exception.
  ENDTRY.

* Apply the search string against each visible property
  LOOP AT ct_onbehalf_employees ASSIGNING <ls_onbehalf>.
    IF <ls_onbehalf>-displayed_properties IS INITIAL.
      APPEND 'EmployeeId' TO lt_properties.
    ELSE.
      SPLIT <ls_onbehalf>-displayed_properties AT ',' INTO TABLE lt_properties.
    ENDIF.

*   Employee name is always shown on the UI, so add it as well
    APPEND 'EmployeeName' TO lt_properties.

    LOOP AT lt_properties INTO lv_property.
*     convert frontend property names to backend names
      LOOP AT lt_odata_properties ASSIGNING <ls_odata_property>.
        IF <ls_odata_property>-property->get_name( ) = lv_property.
          lv_property = <ls_odata_property>-property->get_abap_name( ).
          EXIT.
        ENDIF.
      ENDLOOP.
      IF sy-subrc = 0.
*       check actual filter condition
        ASSIGN COMPONENT lv_property OF STRUCTURE <ls_onbehalf> TO <lv_value>.
        IF sy-subrc = 0.
          lv_value = <lv_value>.
          IF lv_value CS iv_search_string.
            APPEND <ls_onbehalf> TO lt_onbehalf_employees.
            EXIT.
          ENDIF.
        ENDIF.
      ENDIF.
    ENDLOOP.
  ENDLOOP.

* Copy final result to output table
  ct_onbehalf_employees = lt_onbehalf_employees.

ENDMETHOD.
