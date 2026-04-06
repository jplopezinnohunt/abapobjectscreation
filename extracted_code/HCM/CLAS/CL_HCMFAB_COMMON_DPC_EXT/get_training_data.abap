METHOD get_training_data.

* call BADI to read training data
  CALL BADI go_badi_tcal_settings->get_training_data
    EXPORTING
      iv_application_id      = iv_application_id
      iv_instance_id         = iv_instance_id
      iv_employee_assignment = iv_employee_assignment
      iv_begda               = iv_begda
      iv_endda               = iv_endda
      it_pernr               = it_pernr
    CHANGING
      ct_calendar_events     = ct_calendar_events.

ENDMETHOD.
