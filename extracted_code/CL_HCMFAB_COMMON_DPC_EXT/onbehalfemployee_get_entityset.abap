METHOD onbehalfemployee_get_entityset.

  DATA: lt_filter_select_options TYPE /iwbep/t_mgw_select_option,
        ls_filter_select_option  TYPE /iwbep/s_mgw_select_option,
        ls_filter                TYPE /iwbep/s_cod_select_option,
        lv_requester_pernr       TYPE pernr_d,
        lv_onbehalf_pernr        TYPE pernr_d,
        lv_only_visible_pernrs   TYPE boole_d,
        lv_logon_pernr           TYPE pernr_d,
        lt_pernr                 TYPE pccet_pernr,
        lx_exception             TYPE REF TO cx_static_check,
        lt_entityset             TYPE cl_hcmfab_common_mpc=>tt_onbehalfemployee,
        lo_filter                TYPE REF TO /iwbep/if_mgw_req_filter,
        lv_application_id        TYPE hcmfab_application_id,
        lv_top                   TYPE int4,
        lv_skip                  TYPE int4,
        lv_search_string         TYPE string,
        lv_from                  TYPE int4,
        lv_to                    TYPE int4.

  FIELD-SYMBOLS: <ls_entityset>  TYPE cl_hcmfab_common_mpc=>ts_onbehalfemployee.


  CLEAR: et_entityset, es_response_context.

  me->set_no_cache( ).

  TRY.
      lo_filter = io_tech_request_context->get_filter( ).
      lt_filter_select_options = lo_filter->get_filter_select_options( ).

      LOOP AT lt_filter_select_options INTO ls_filter_select_option.
        READ TABLE ls_filter_select_option-select_options INDEX 1 INTO ls_filter.
        CASE ls_filter_select_option-property.
          WHEN 'REQUESTER_NUMBER'.
            lv_requester_pernr = ls_filter-low.
          WHEN 'EMPLOYEE_NUMBER'.
            lv_onbehalf_pernr = ls_filter-low.
          WHEN 'APPLICATION_ID'.
            lv_application_id = ls_filter-low.
          WHEN 'IS_HIDDEN_IN_LIST'.                                         "MELN3434863
            lv_only_visible_pernrs = boolc( ls_filter-low = abap_false ).
        ENDCASE.
      ENDLOOP.

      lv_logon_pernr = go_employee_api->get_employeenumber_from_user( ).
      IF lv_requester_pernr IS NOT INITIAL.
        lt_pernr = go_employee_api->get_assignments( lv_logon_pernr ).

        "check whether requester PERNR actually is allowed to be read
        READ TABLE lt_pernr WITH TABLE KEY table_line = lv_requester_pernr  "MELN3434863
                            TRANSPORTING NO FIELDS.
        IF sy-subrc <> 0.
          RAISE EXCEPTION TYPE cx_hcmfab_common
            EXPORTING
              textid   = cx_hcmfab_common=>illegal_employeenumber
              mv_pernr = lv_requester_pernr.
        ENDIF.
      ELSE.
*       get default PERNR for user
        lv_requester_pernr = lv_logon_pernr.
      ENDIF.

      IF lv_onbehalf_pernr IS NOT INITIAL.
*       check whether onbehalf PERNR actually is allowed to be read
        go_employee_api->do_employeenumber_validation(
          iv_pernr          = lv_onbehalf_pernr
          iv_application_id = lv_application_id ).
      ENDIF.

*     retrieve on-behalf list with all relevant data
      me->get_onbehalf_employees(
        EXPORTING
          iv_application_id      = lv_application_id
          iv_requester_number    = lv_requester_pernr
          iv_onbehalf_number     = lv_onbehalf_pernr
          iv_only_visible_pernrs = lv_only_visible_pernrs                 "MELN3434863
        IMPORTING
          et_onbehalf_employees  = lt_entityset
      ).

*     Backend searching
      lv_search_string = io_tech_request_context->get_search_string( ).
      me->apply_onbehalf_filters(
        EXPORTING
          iv_search_string      = lv_search_string
          io_tech_request       = io_tech_request_context
        CHANGING
          ct_onbehalf_employees = lt_entityset
      ).

*     Paging support
      IF io_tech_request_context->has_count( ) = abap_true.
        es_response_context-count = lines( lt_entityset ).
        RETURN.
      ENDIF.
      IF io_tech_request_context->has_inlinecount( ) = abap_true.
        es_response_context-inlinecount = lines( lt_entityset ).
      ENDIF.

      IF lines( lt_entityset ) > 0.
        lv_from = 1.
        lv_to = lines( lt_entityset ).
        lv_skip = io_tech_request_context->get_skip( ).
        lv_top  = io_tech_request_context->get_top( ).
        IF lv_skip IS NOT INITIAL.
          lv_from = lv_skip + 1.
        ENDIF.
        IF lv_top IS NOT INITIAL.
          lv_to = lv_from + lv_top  - 1.
        ENDIF.

        APPEND LINES OF lt_entityset FROM lv_from TO lv_to TO et_entityset.

*       Check if default version id needs to be calculated
        LOOP AT et_entityset ASSIGNING <ls_entityset> WHERE default_version_id IS INITIAL.
          <ls_entityset>-default_version_id = go_employee_api->get_default_version_id( <ls_entityset>-employee_number ).
        ENDLOOP.

      ENDIF.

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
                iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDTRY.

ENDMETHOD.
