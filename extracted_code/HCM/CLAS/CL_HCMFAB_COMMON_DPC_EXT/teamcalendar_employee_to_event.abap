METHOD teamcalendar_employee_to_event.

  TYPES: BEGIN OF lty_employee_to_event.
          INCLUDE TYPE cl_hcmfab_common_mpc=>ts_teamcalendaremployee.
  TYPES:  toteamcalendarevent TYPE STANDARD TABLE OF cl_hcmfab_common_mpc=>ts_teamcalendarevent WITH DEFAULT KEY.
  TYPES: END OF lty_employee_to_event.

  DATA: lt_employee_set         TYPE TABLE OF lty_employee_to_event,
        ls_employee_set         TYPE lty_employee_to_event,
        lv_root_object_mode     TYPE hcmfab_tcal_root_mode,
        lv_root_pernr           TYPE pernr_d,
        lv_view_id              TYPE hcmfab_view_id,
        lv_view_type            TYPE hcmfab_view_type,
        lv_start_date           TYPE dats,
        lv_end_date             TYPE dats,
        lv_employee_assignment  TYPE pernr_d,
        ls_filter               TYPE /iwbep/s_cod_select_option,
        lv_application_id       TYPE hcmfab_application_id,
        lv_instance_id          TYPE hcmfab_tcal_instance_id,
        lv_requester_id         TYPE pernr_d,
        lx_exception            TYPE REF TO cx_static_check,
        ls_key                  TYPE /iwbep/s_mgw_name_value_pair,
        ls_filter_select_option TYPE /iwbep/s_mgw_select_option,
        ls_calendar_event       TYPE hcmfab_s_tcal_event,
        lt_calendar_events      TYPE hcmfab_t_tcal_event,
        ls_employee             TYPE hcmfab_s_tcal_employee,
        lt_employees            TYPE hcmfab_t_tcal_employee,
        lt_pernr                TYPE pernr_tab,
        lv_index                TYPE sy-tabix,
        lt_event_type           TYPE hcmfab_t_tcal_event_type,
        ls_event_type           TYPE hcmfab_s_tcal_event_type,
        lv_personalization_allowed TYPE boolean,
        ls_employee_entity      TYPE cl_hcmfab_common_mpc=>ts_teamcalendaremployee.

  FIELD-SYMBOLS: <ls_employee_ui> TYPE lty_employee_to_event,
                 <ls_timeevent>   TYPE cl_hcmfab_common_mpc=>ts_teamcalendarevent.


  CLEAR: er_entityset, es_response_context.

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

* calculate start and end date for selection
  me->get_dates_from_filter(
    EXPORTING
      it_filter_select_options = it_filter_select_options
    IMPORTING
      ev_start_date            = lv_start_date
      ev_end_date              = lv_end_date
  ).

  TRY.
*     No pernr? Determine default pernr
      IF lv_employee_assignment IS INITIAL.
        lv_employee_assignment = go_employee_api->get_employeenumber_from_user( ).
      ELSE.
        "check whether PERNR actually belongs to the logon user
        go_employee_api->do_employeenumber_validation(
          iv_pernr = lv_employee_assignment
          iv_application_id = lv_application_id
        ).
      ENDIF.

      IF lv_view_id IS INITIAL
       OR lv_start_date IS INITIAL
       OR lv_end_date IS INITIAL.
        RETURN. "ex
      ENDIF.

*     check if personalization is allowed
      lv_personalization_allowed = me->is_personalization_allowed(
          iv_application_id          = lv_application_id
          iv_instance_id             = lv_instance_id
          iv_employee_assignment     = lv_employee_assignment
          iv_view_type               = lv_view_type
          iv_view_id                 = lv_view_id
      ).

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
      LOOP AT lt_employees INTO ls_employee.
        IF lv_personalization_allowed = abap_true
          AND ls_employee-display_state <> if_hcmfab_tcal_constants=>gc_display_state-visible AND ls_employee-display_state <> if_hcmfab_tcal_constants=>gc_display_state-added .
*         don't read the data for hidden an not allowed employees
          CONTINUE.
        ENDIF.
        APPEND ls_employee-employee_id TO lt_pernr.
      ENDLOOP.

*     call BADI to get the required event categories
      CALL BADI go_badi_tcal_settings->get_event_types
        EXPORTING
          iv_application_id      = lv_application_id
          iv_instance_id         = lv_instance_id
          iv_employee_assignment = lv_employee_assignment
          iv_view_type           = lv_view_type
          iv_view_id             = lv_view_id
        IMPORTING
          et_event_types         = lt_event_type.


*     read the data for the required categories
*     leave data or attendance data
      READ TABLE lt_event_type WITH KEY event_category = gc_event_category-leave TRANSPORTING NO FIELDS.
      IF sy-subrc <> 0. "note 2804021
        READ TABLE lt_event_type WITH KEY event_category = gc_event_category-attendance TRANSPORTING NO FIELDS.
      ENDIF.
      IF sy-subrc = 0.
        me->get_absence_data(
          EXPORTING
            iv_application_id      = lv_application_id
            iv_instance_id         = lv_instance_id
            iv_employee_assignment = lv_employee_assignment
            iv_begda               = lv_start_date
            iv_endda               = lv_end_date
            it_pernr               = lt_pernr
          CHANGING
            ct_calendar_events = lt_calendar_events
        ).
      ENDIF.

*     Birthday/Anniversary
      READ TABLE lt_event_type WITH KEY event_category = gc_event_category-birthday_anniversary TRANSPORTING NO FIELDS.
      IF sy-subrc = 0.
        me->get_bday_anniversaries(
          EXPORTING
            iv_application_id      = lv_application_id
            iv_instance_id         = lv_instance_id
            iv_employee_assignment = lv_employee_assignment
            iv_begda               = lv_start_date
            iv_endda               = lv_end_date
            it_pernr               = lt_pernr
          CHANGING
            ct_calendar_events = lt_calendar_events
        ).
      ENDIF.

*     Trainings
      READ TABLE lt_event_type WITH KEY event_category = gc_event_category-training TRANSPORTING NO FIELDS.
      IF sy-subrc = 0.
        me->get_training_data(
          EXPORTING
            iv_application_id      = lv_application_id
            iv_instance_id         = lv_instance_id
            iv_employee_assignment = lv_employee_assignment
            iv_begda               = lv_start_date
            iv_endda               = lv_end_date
            it_pernr               = lt_pernr
          CHANGING
            ct_calendar_events = lt_calendar_events
        ).
      ENDIF.

*     Work schedule (Non-working days)
      READ TABLE lt_event_type WITH KEY event_category = gc_event_category-work_schedule TRANSPORTING NO FIELDS.
      IF sy-subrc = 0.
        me->get_workschedule(
          EXPORTING
            iv_application_id      = lv_application_id
            iv_instance_id         = lv_instance_id
            iv_employee_assignment = lv_employee_assignment
            iv_begda               = lv_start_date
            iv_endda               = lv_end_date
            it_pernr               = lt_pernr
          CHANGING
            ct_calendar_events = lt_calendar_events
        ).
      ENDIF.

*     Additional Data (provided by BADI)
      READ TABLE lt_event_type WITH KEY event_category = gc_event_category-additional_data TRANSPORTING NO FIELDS.
      IF sy-subrc = 0.
        me->get_additional_data(
          EXPORTING
            iv_application_id      = lv_application_id
            iv_instance_id         = lv_instance_id
            iv_employee_assignment = lv_employee_assignment
            iv_begda               = lv_start_date
            iv_endda               = lv_end_date
            it_pernr               = lt_pernr
          CHANGING
            ct_calendar_events = lt_calendar_events
        ).
      ENDIF.


*     fill the resulting entity set
      SORT lt_calendar_events BY employee_id start_date.
      LOOP AT lt_employees INTO ls_employee.

        APPEND INITIAL LINE TO lt_employee_set ASSIGNING <ls_employee_ui>.
        <ls_employee_ui>-employee_id = ls_employee-employee_id.
        <ls_employee_ui>-view_type = lv_view_type.
        <ls_employee_ui>-view_id = lv_view_id.
        <ls_employee_ui>-application_id = lv_application_id.
        <ls_employee_ui>-instance_id = lv_instance_id.
        <ls_employee_ui>-name = ls_employee-name.
        <ls_employee_ui>-sort_name = ls_employee-sort_name.
        <ls_employee_ui>-description = ls_employee-description.
        <ls_employee_ui>-tooltip = ls_employee-tooltip.     "AE2650135
        <ls_employee_ui>-display_state = ls_employee-display_state.
        <ls_employee_ui>-start_date = gc_low_date. "employee set is constant for view
        <ls_employee_ui>-end_date = gc_high_date.
        <ls_employee_ui>-requester_id = lv_requester_id.

*       call extension BADI for employee
        MOVE-CORRESPONDING <ls_employee_ui> TO ls_employee_entity.
        me->enrich_employee(
          CHANGING
            cs_employee = ls_employee_entity
        ).
        MOVE-CORRESPONDING ls_employee_entity TO <ls_employee_ui>.

        READ TABLE lt_calendar_events WITH KEY employee_id = ls_employee-employee_id INTO ls_calendar_event BINARY SEARCH.
        IF sy-subrc = 0.
          WHILE sy-subrc = 0.
            lv_index = sy-tabix + 1.

*           Determine event type for the given event and check if the event should be displayed
            ls_event_type = me->get_event_type_for_event(
              it_event_types = lt_event_type
              is_event       = ls_calendar_event
            ).
            IF ls_event_type IS NOT INITIAL.
              APPEND INITIAL LINE TO <ls_employee_ui>-toteamcalendarevent ASSIGNING <ls_timeevent>.
              <ls_timeevent>-application_id = lv_application_id.
              <ls_timeevent>-instance_id = lv_instance_id.
              <ls_timeevent>-employee_assignment = lv_employee_assignment.
              <ls_timeevent>-requester_id = lv_requester_id.
              <ls_timeevent>-employee_id = ls_employee-employee_id.
              <ls_timeevent>-start_date = ls_calendar_event-start_date.
              <ls_timeevent>-end_date = ls_calendar_event-end_date.
              <ls_timeevent>-start_time = ls_calendar_event-start_time.
              <ls_timeevent>-end_time = ls_calendar_event-end_time.
              <ls_timeevent>-title = ls_calendar_event-title.
              <ls_timeevent>-description = ls_calendar_event-description.
              <ls_timeevent>-is_tentative = ls_calendar_event-is_tentative.
              <ls_timeevent>-event_type = ls_event_type-color_type.
              <ls_timeevent>-icon = ls_event_type-icon.

*             2650135: Additional propertys
              <ls_timeevent>-tooltip = ls_calendar_event-tooltip.
              <ls_timeevent>-absencetype = ls_calendar_event-absencetype.
              <ls_timeevent>-absencetypetext = ls_calendar_event-absencetypetext.
              <ls_timeevent>-absencestatus = ls_calendar_event-absencestatus.
              <ls_timeevent>-absencestatustext = ls_calendar_event-absencestatustext.
              <ls_timeevent>-absencedays = ls_calendar_event-absencedays.
              <ls_timeevent>-absencehours = ls_calendar_event-absencehours.
              <ls_timeevent>-absenceoperation = ls_calendar_event-absenceoperation.

*             call the extension BADI for event
              me->enrich_event(
                CHANGING
                  cs_event = <ls_timeevent>
              ).

*             Make sure that no invalid time values are sent (leave data might contain these)
              IF <ls_timeevent>-start_time = space.
                CLEAR <ls_timeevent>-start_time.
              ENDIF.
              IF <ls_timeevent>-end_time = space.
                CLEAR <ls_timeevent>-end_time.
              ENDIF.
            ENDIF.

            READ TABLE lt_calendar_events INTO ls_calendar_event INDEX lv_index COMPARING employee_id.
          ENDWHILE.
        ENDIF.
      ENDLOOP.

*     sort employee table and put root PERNR on first position (note 3133516)
      SORT lt_employee_set BY sort_name.
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
      READ TABLE lt_employee_set INTO ls_employee_set
                              WITH KEY employee_id = lv_root_pernr.
      IF sy-subrc = 0 AND
         sy-tabix <> 1.
        DELETE lt_employee_set INDEX sy-tabix.
        INSERT ls_employee_set INTO lt_employee_set INDEX 1.
      ENDIF.

      me->copy_data_to_ref(
        EXPORTING
          is_data = lt_employee_set
        CHANGING
          cr_data = er_entityset
      ).

    CATCH cx_hcmfab_common INTO lx_exception.
      cl_hcmfab_utilities=>raise_gateway_error(
          is_message  = cl_hcmfab_utilities=>get_bapiret2_from_exception( lx_exception )
          iv_entity   = iv_entity_name "note 2838116
      ).
  ENDTRY.
ENDMETHOD.
