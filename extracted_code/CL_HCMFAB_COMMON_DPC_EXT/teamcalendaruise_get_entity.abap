METHOD teamcalendaruise_get_entity.

  DATA: lv_application_id       TYPE hcmfab_application_id,
        lv_employee_assignment  TYPE pernr_d,
        lv_instance_id          TYPE hcmfab_tcal_instance_id,
        ls_key                  TYPE /iwbep/s_mgw_name_value_pair.

  CLEAR: er_entity, es_response_context.

* get the key fields
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

  me->get_tcal_ui_settings(
    EXPORTING
      iv_application_id      = lv_application_id
      iv_instance_id         = lv_instance_id
      iv_employee_assignment = lv_employee_assignment
    IMPORTING
      es_ui_settings         = er_entity ).

ENDMETHOD.
