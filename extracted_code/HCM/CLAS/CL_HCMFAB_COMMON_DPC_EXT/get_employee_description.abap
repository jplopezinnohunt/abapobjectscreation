METHOD get_employee_description.

  CALL BADI go_badi_tcal_settings->get_employee_description
    EXPORTING
      iv_application_id       = iv_application_id
      iv_instance_id          = iv_calendar_instance_id
      iv_employee_assignment  = iv_employee_assignment
      iv_employee_id          = iv_employee_id
    RECEIVING
      ev_description          = rv_description.

ENDMETHOD.
