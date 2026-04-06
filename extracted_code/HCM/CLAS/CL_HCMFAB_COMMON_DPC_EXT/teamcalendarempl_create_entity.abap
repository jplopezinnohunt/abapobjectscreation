METHOD teamcalendarempl_create_entity.

  DATA: ls_employee TYPE cl_hcmfab_common_mpc=>ts_teamcalendaremployee.
  DATA lv_personalization_mode TYPE hcmfab_tcal_app_pers_mode.
  DATA: lo_message_container TYPE REF TO /iwbep/if_message_container,
        lx_error             TYPE REF TO /iwbep/cx_mgw_busi_exception.
  DATA lv_param TYPE symsgv.
  DATA lv_display_state TYPE hcmfab_tcal_display_state.
  DATA ls_shared_employee TYPE hcmfab_d_tcalsha.
  DATA lv_approval_mode TYPE hcmfab_tcal_approval_mode.
  DATA lv_access_state TYPE hcmfab_tcal_emp_access_state.

* retrieve the new employee data
  CALL METHOD io_data_provider->read_entry_data
    IMPORTING
      es_data = ls_employee.
  IF ls_employee-view_id IS INITIAL.
*   take stored view id from last view creation
    ls_employee-view_id = gv_last_created_tcal_view.
  ENDIF.

* check if personalization is allowed
  me->get_tcal_personalization_mode(
    EXPORTING
      iv_application_id       = ls_employee-application_id
      iv_instance_id          = ls_employee-instance_id
      iv_employee_assignment  = ls_employee-employee_assignment
    RECEIVING
      rv_personalization_mode = lv_personalization_mode
  ).
  IF lv_personalization_mode = if_hcmfab_tcal_constants=>gc_app_pers_mode-none.
    lv_param = ls_employee-employee_id.
    CREATE OBJECT lx_error.
    lo_message_container = lx_error->get_msg_container( ).
    lo_message_container->add_message(
      EXPORTING
        iv_msg_type               = 'E'
        iv_msg_id                 = 'HCMFAB_COMMON'
        iv_msg_number             = '001'
        iv_msg_v1                 = lv_param
    ).
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid            = if_t100_message=>default_textid
        message_container = lo_message_container.
  ENDIF.

* determine the display state for the added employee
* read access state
  CALL METHOD me->get_tcal_access_state
    EXPORTING
      iv_application_id        = ls_employee-application_id
      iv_instance_id           = ls_employee-instance_id
      iv_employee_assignment   = ls_employee-employee_assignment
      iv_requested_employee_id = ls_employee-employee_id
    RECEIVING
      rv_access_state          = lv_access_state.
  IF lv_access_state = if_hcmfab_tcal_constants=>gc_access_state-allowed.
*   employee can be added directly
    lv_display_state = if_hcmfab_tcal_constants=>gc_display_state-added.
  ELSE.
    lv_display_state = if_hcmfab_tcal_constants=>gc_display_state-requested.
*   add new entry to sharing table (if it doesn't exist already)
    IF lv_access_state = if_hcmfab_tcal_constants=>gc_access_state-restricted.
      ls_shared_employee-mandt = sy-mandt.
      ls_shared_employee-employee_id = ls_employee-employee_id.
      ls_shared_employee-shared_employee_id = ls_employee-employee_assignment.
      ls_shared_employee-share_state = if_hcmfab_tcal_constants=>gc_emp_share_state-undecided.
      MODIFY hcmfab_d_tcalsha FROM ls_shared_employee.

*     trigger approval workflow (if needed)
*     get approval mode
      CALL BADI go_badi_tcal_settings->get_approval_settings
        IMPORTING
          ev_approval_mode = lv_approval_mode.
      IF lv_approval_mode = if_hcmfab_tcal_constants=>gc_approval_mode-workflow.
        CALL BADI go_badi_tcal_settings->trigger_approval
          EXPORTING
            iv_requester_pernr = ls_employee-employee_assignment
            iv_approver_pernr  = ls_employee-employee_id.
      ENDIF.
    ENDIF.
  ENDIF.
* add employee to custom view
  me->change_employee_display_state(
    EXPORTING
      iv_employee_assignment = ls_employee-employee_assignment
      iv_view_type           = ls_employee-view_type
      iv_view_id             = ls_employee-view_id
      iv_employee_id         = ls_employee-employee_id
      iv_display_state       = lv_display_state
  ).

  er_entity-application_id = ls_employee-application_id.
  er_entity-instance_id = ls_employee-instance_id.
  er_entity-employee_assignment = ls_employee-employee_assignment.
  er_entity-view_type = ls_employee-view_type.
  er_entity-view_id = ls_employee-view_id.
  er_entity-employee_id = ls_employee-employee_id.
  er_entity-description = me->get_employee_description(
                          iv_application_id       = ls_employee-application_id
                          iv_calendar_instance_id = ls_employee-instance_id
                          iv_employee_assignment  = ls_employee-employee_assignment
                          iv_employee_id          = ls_employee-employee_id ).
  er_entity-name = go_employee_api->get_name( iv_pernr = ls_employee-employee_id iv_no_auth_check = abap_true ).
  er_entity-sort_name = go_employee_api->get_sortable_name( iv_pernr = ls_employee-employee_id iv_no_auth_check = abap_true ).
  er_entity-display_state = if_hcmfab_tcal_constants=>gc_display_state-added.
  er_entity-start_date = '18000101'.
  er_entity-end_date = '99991231'.
  er_entity-requester_id = ls_employee-requester_id.

* call the extension BADI
  me->enrich_employee(
    CHANGING
      cs_employee = er_entity
  ).

ENDMETHOD.
