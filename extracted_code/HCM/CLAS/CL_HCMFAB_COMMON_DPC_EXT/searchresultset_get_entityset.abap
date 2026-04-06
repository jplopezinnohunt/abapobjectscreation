METHOD searchresultset_get_entityset.
  DATA: lt_pernrs_found      TYPE pernr_tab,
        lv_top               TYPE i,
        ls_return            TYPE bapiret2,
        lo_employee_search   TYPE REF TO if_hcmfab_employee_search,
        lx_exception         TYPE REF TO cx_static_check,
        ls_searchresult      TYPE hcmfab_s_tcal_search_result_ui,
        lv_application_id    TYPE hcmfab_application_id,
        lv_instance_id       TYPE hcmfab_tcal_instance_id,
        lv_employee_assignment   TYPE pernr_d,
        lv_view_type             TYPE hcmfab_view_type,
        lv_view_id               TYPE hcmfab_view_id,
        lv_search_string         TYPE string,
        lt_filter_select_options TYPE /iwbep/t_mgw_select_option,
        lo_filter                TYPE REF TO /iwbep/if_mgw_req_filter,
        ls_filter                TYPE /iwbep/s_mgw_select_option,
        ls_select                TYPE /iwbep/s_cod_select_option,
        lv_is_valid              TYPE boole_d,
        lv_tabix                 TYPE sytabix.


  FIELD-SYMBOLS: <lv_pernr>  TYPE pernr_d.
  FIELD-SYMBOLS: <ls_search_result> TYPE hcmfab_s_tcal_search_result_ui.


  CLEAR: et_entityset, es_response_context.

* get the result list (query parameter 'search')
  TRY.

*     get key fields from filter
      lo_filter = io_tech_request_context->get_filter( ).
      lt_filter_select_options = lo_filter->get_filter_select_options( ).
      LOOP AT lt_filter_select_options INTO ls_filter.
        READ TABLE ls_filter-select_options INTO ls_select INDEX 1 TRANSPORTING low.
        CASE ls_filter-property.
          WHEN 'APPLICATION_ID'.
            lv_application_id = ls_select-low.
          WHEN 'INSTANCE_ID'.
            lv_instance_id = ls_select-low.
          WHEN 'EMPLOYEE_ASSIGNMENT'.
            lv_employee_assignment = ls_select-low.
          WHEN 'VIEW_TYPE'.
            lv_view_type = ls_select-low.
          WHEN 'VIEW_ID'.
            lv_view_id = ls_select-low.
        ENDCASE.
      ENDLOOP.

*     execute the search
      lv_search_string = io_tech_request_context->get_search_string( ).
      CALL BADI go_badi_tcal_settings->execute_employee_search
        EXPORTING
          iv_application_id      = lv_application_id
          iv_instance_id         = lv_instance_id
          iv_employee_assignment = lv_employee_assignment
          iv_view_type           = lv_view_type
          iv_view_id             = lv_view_id
          iv_search_string       = lv_search_string
        IMPORTING
          et_employees_found     = lt_pernrs_found.

*     check if found employee is allowed to be added (note 2873167)
      LOOP AT lt_pernrs_found ASSIGNING <lv_pernr>.
        lv_tabix = sy-tabix.
        CALL BADI go_badi_tcal_settings->validate_custom_employee
          EXPORTING
            iv_employee_id = <lv_pernr>
          RECEIVING
            rv_is_valid    = lv_is_valid.
        IF lv_is_valid = abap_false.
          DELETE lt_pernrs_found INDEX lv_tabix.
        ENDIF.
      ENDLOOP.

*     ensure max. 300 search results are sent to the frontend
      IF lines( lt_pernrs_found ) > 300.
        DELETE lt_pernrs_found FROM 301.
      ENDIF.

*     handle count request ($count)
      IF io_tech_request_context->has_count( ) = abap_true.
        es_response_context-count = lines( lt_pernrs_found ).
        RETURN.
      ENDIF.

*     fill data basic into the result structure (to get sort name)
      LOOP AT lt_pernrs_found ASSIGNING <lv_pernr>.
        ls_searchresult-application_id = lv_application_id. "note 2611191
        ls_searchresult-instance_id = lv_instance_id.
        ls_searchresult-employee_assignment = lv_employee_assignment.
        ls_searchresult-view_type = lv_view_type.
        ls_searchresult-view_id = lv_view_id.
        ls_searchresult-employee_id = <lv_pernr>.
        ls_searchresult-sort_name   = go_employee_api->get_sortable_name( iv_pernr = <lv_pernr> iv_no_auth_check = abap_true ).
        APPEND ls_searchresult TO et_entityset.
      ENDLOOP.

      "default sorting as per sortable name
      SORT et_entityset BY sort_name.

*     calculate number of result set rows ($inlinecount)
      IF io_tech_request_context->has_inlinecount( ) = abap_true.
        es_response_context-inlinecount = lines( et_entityset ).
      ENDIF.

*     apply paging ($skip, $top)
      lv_top = io_tech_request_context->get_top( ).
      IF lv_top IS NOT INITIAL.
        cl_hcmfab_utilities=>apply_paging(
          EXPORTING
             iv_top  = lv_top
             iv_skip = io_tech_request_context->get_skip( )
          CHANGING
             ct_data = et_entityset
        ).
      ENDIF.

*     add additional data
      LOOP AT et_entityset ASSIGNING <ls_search_result>.
        <ls_search_result>-name  = go_employee_api->get_name( iv_pernr = <ls_search_result>-employee_id iv_no_auth_check = abap_true ).
        <ls_search_result>-description = me->get_employee_description(
            iv_application_id       = lv_application_id
            iv_calendar_instance_id = lv_instance_id
            iv_employee_assignment  = lv_employee_assignment
            iv_employee_id          =  <ls_search_result>-employee_id ).
        <ls_search_result>-access_state = me->get_tcal_access_state(
            iv_application_id        = lv_application_id
            iv_instance_id           = lv_instance_id
            iv_employee_assignment   = lv_employee_assignment
            iv_requested_employee_id = <ls_search_result>-employee_id ).

*       call extension BADI for search result
        me->enrich_search_result(
          CHANGING
            cs_search_result = <ls_search_result>
        ).
      ENDLOOP.

*     ensure data is not cached on client
      es_response_context-do_not_cache_on_client = /iwbep/if_mgw_appl_types=>gcs_cache_on_client-do_not_cache.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
