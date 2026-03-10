METHOD teamcalendarshar_get_entity.
  DATA lt_keys TYPE /iwbep/t_mgw_tech_pairs.
  DATA ls_key TYPE /iwbep/s_mgw_tech_pair.
  DATA ls_share_mode TYPE hcmfab_d_tcalmod.
  DATA lv_share_mode TYPE hcmfab_tcal_emp_share_mode.
  DATA lv_employee_id TYPE pernr_d.
  DATA lv_application_id TYPE hcmfab_application_id.
  DATA lv_instance_id TYPE hcmfab_tcal_instance_id.

  lt_keys = io_tech_request_context->get_keys( ).
  LOOP AT lt_keys INTO ls_key.
    CASE ls_key-name.
      WHEN 'APPLICATION_ID'.
        lv_application_id = ls_key-value.
      WHEN 'INSTANCE_ID'.
        lv_instance_id = ls_key-value.
      WHEN 'EMPLOYEE_ID'.
        lv_employee_id = ls_key-value.
    ENDCASE.
  ENDLOOP.

  CALL METHOD me->get_employee_share_mode
    EXPORTING
      iv_employee_id = lv_employee_id
    IMPORTING
      ev_share_mode  = lv_share_mode.

  er_entity-application_id = lv_application_id.
  er_entity-instance_id = lv_instance_id.
  er_entity-employee_id = lv_employee_id.
  er_entity-share_mode = lv_share_mode.

ENDMETHOD.
