METHOD teamcalendareven_get_entityset.

  TYPES: BEGIN OF lty_employee_to_event.
          INCLUDE TYPE cl_hcmfab_common_mpc=>ts_teamcalendaremployee.
  TYPES:  toteamcalendarevent TYPE STANDARD TABLE OF cl_hcmfab_common_mpc=>ts_teamcalendarevent WITH DEFAULT KEY.
  TYPES: END OF lty_employee_to_event.

  DATA: lt_employee_to_event_set TYPE STANDARD TABLE OF lty_employee_to_event,
        ls_employee_to_event TYPE lty_employee_to_event,
        lr_data TYPE REF TO data.

  FIELD-SYMBOLS: <lt_employee_to_event_set> TYPE STANDARD TABLE.

  CLEAR: et_entityset, es_response_context.

  me->teamcalendar_employee_to_event(
        EXPORTING
          iv_entity_name           = iv_entity_name
          iv_entity_set_name       = iv_entity_set_name
          iv_source_name           = iv_source_name
          it_filter_select_options = it_filter_select_options
          is_paging                = is_paging
          it_key_tab               = it_key_tab
          it_navigation_path       = it_navigation_path
          it_order                 = it_order
          iv_filter_string         = iv_filter_string
          iv_search_string         = iv_search_string
        IMPORTING
          er_entityset             = lr_data
      ).

  ASSIGN lr_data->* TO <lt_employee_to_event_set>.
  lt_employee_to_event_set = <lt_employee_to_event_set>.
  LOOP AT lt_employee_to_event_set INTO ls_employee_to_event.
    APPEND LINES OF ls_employee_to_event-toteamcalendarevent TO et_entityset.
  ENDLOOP.

ENDMETHOD.
