METHOD assign_step_to_scenario.

  DATA scenario_instance TYPE REF TO if_hrasr00_scenario.
  DATA no_authority TYPE boole_d.
  DATA ls_msg TYPE symsg.
  DATA dummy(1) TYPE c.

  is_ok = true.

* Get the scenario instance
  CALL METHOD cl_hrasr00_scenario=>get
    EXPORTING
      scenario_guid = a_scenario
    IMPORTING
      instance      = scenario_instance
      no_authority  = no_authority.

*     Raise suitable message, if no authority.
*     This authority failure flag is set in underlying layers of CM/RM, if sufficient authorizations are not maintained for CM/RM authorization objects.
      IF no_authority = true.
        MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '004' INTO dummy.
        MOVE-CORRESPONDING sy TO ls_msg.

        CALL METHOD message_handler->add_message
          EXPORTING
            message = ls_msg.

        is_ok = false.
        RETURN.
      ENDIF.

* Add the step to scenario.
  CALL METHOD scenario_instance->add_step
    EXPORTING
      step_guid    = a_step
    IMPORTING
      no_authority = no_authority.

*     Raise suitable message, if no authority.
*     This authority failure flag is set in underlying layers of CM/RM, if sufficient authorizations are not maintained for CM/RM authorization objects.
      IF no_authority = true.
        MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '012' INTO dummy.
        MOVE-CORRESPONDING sy TO ls_msg.

        CALL METHOD message_handler->add_message
          EXPORTING
            message = ls_msg.

        is_ok = false.
        RETURN.
      ENDIF.

ENDMETHOD.
