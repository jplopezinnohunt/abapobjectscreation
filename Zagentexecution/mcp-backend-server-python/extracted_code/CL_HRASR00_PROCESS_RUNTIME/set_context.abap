METHOD set_context.

* Set the scenario
  IF NOT scenario_guid IS INITIAL.
    CALL METHOD me->set_current_scenario
      EXPORTING
        scenario_guid = scenario_guid.
  ENDIF.

* Set the step
  IF NOT step_guid IS INITIAL.
    CALL METHOD me->set_current_step
      EXPORTING
        step_guid = step_guid.
  ENDIF.

ENDMETHOD.
