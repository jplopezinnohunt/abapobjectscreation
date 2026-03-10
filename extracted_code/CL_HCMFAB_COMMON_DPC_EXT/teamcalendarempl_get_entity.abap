METHOD teamcalendarempl_get_entity.

  DATA: lv_application_id       TYPE hcmfab_application_id,
        lv_employee_assignment  TYPE pernr_d,
        lv_instance_id          TYPE hcmfab_tcal_instance_id,
        lv_employee_id          TYPE pernr_d,
        lv_view_type            TYPE hcmfab_view_type,
        lv_view_id              TYPE hcmfab_view_id,
        lv_requester_id         TYPE pernr_d,
        lt_key_tab              TYPE /iwbep/t_mgw_tech_pairs,
        ls_tech_key             TYPE /iwbep/s_mgw_tech_pair.

  CLEAR: er_entity, es_response_context.

  lt_key_tab = io_tech_request_context->get_keys( ).
  LOOP AT lt_key_tab INTO ls_tech_key.
    CASE ls_tech_key-name.
      WHEN 'APPLICATION_ID'.
        lv_application_id = ls_tech_key-value.
      WHEN 'EMPLOYEE_ASSIGNMENT'.
        lv_employee_assignment = ls_tech_key-value.
      WHEN 'VIEW_TYPE'.
        lv_view_type = ls_tech_key-value.
      WHEN 'VIEW_ID'.
        lv_view_id = ls_tech_key-value.
      WHEN 'INSTANCE_ID'.
        lv_instance_id = ls_tech_key-value.
      WHEN 'EMPLOYEE_ID'.
        lv_employee_id = ls_tech_key-value.
      WHEN 'REQUESTER_ID'.
        lv_requester_id = ls_tech_key-value.
    ENDCASE.
  ENDLOOP.

* copy key fields
  er_entity-application_id = lv_application_id.
  er_entity-instance_id = lv_instance_id.
  er_entity-employee_assignment = lv_employee_assignment.
  er_entity-view_id = lv_view_id.
  er_entity-view_type = lv_view_type.
  er_entity-employee_id = lv_employee_id.
  er_entity-requester_id = lv_requester_id.

* fill data fields
  er_entity-name = go_employee_api->get_name( iv_pernr = lv_employee_id iv_no_auth_check = abap_true ).
  er_entity-sort_name = go_employee_api->get_sortable_name( iv_pernr = lv_employee_id iv_no_auth_check = abap_true ).

  er_entity-description = me->get_employee_description(
                          iv_application_id       = lv_application_id
                          iv_calendar_instance_id = lv_instance_id
                          iv_employee_assignment  = lv_employee_assignment
                          iv_employee_id          = lv_employee_id ).
  er_entity-tooltip = er_entity-name.                                  "AE2650135

  er_entity-display_state = me->get_display_state(
      iv_application_id          = lv_application_id
      iv_instance_id             = lv_instance_id
      iv_employee_assignment     = lv_employee_assignment
      iv_view_type               = lv_view_type
      iv_view_id                 = lv_view_id
      iv_requester_id            = lv_requester_id
      iv_employee_id             = lv_employee_id
  ).

  er_entity-start_date = '18000101'.
  er_entity-end_date = '99991231'.
  er_entity-requester_id = ''.

* call the extension BADI
  me->enrich_employee(
    CHANGING
      cs_employee = er_entity
  ).

ENDMETHOD.
