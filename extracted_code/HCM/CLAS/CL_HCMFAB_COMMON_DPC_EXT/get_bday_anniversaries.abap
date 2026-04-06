METHOD get_bday_anniversaries.

* call BADI to read birthdays and anniversaries
  CALL BADI go_badi_tcal_settings->get_bday_anniversaries
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
