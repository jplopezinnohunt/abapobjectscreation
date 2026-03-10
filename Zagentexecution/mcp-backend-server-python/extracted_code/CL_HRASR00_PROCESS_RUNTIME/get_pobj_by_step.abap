METHOD get_pobj_by_step .

  DATA step_instance TYPE REF TO if_hrasr00_step.
  DATA scenario_instance TYPE REF TO if_hrasr00_scenario.
  DATA pobj_instance TYPE REF TO if_hrasr00_process.
  DATA hrasr00_case_api TYPE REF TO if_hrasr00_case.
  DATA no_authority TYPE boole_d.
  DATA ls_msg TYPE symsg.
  DATA dummy(1) TYPE c.

  CLEAR pobj_guid.
  is_ok = true.

* Get the instance for step object using step guid
  CALL METHOD cl_hrasr00_step=>get
    EXPORTING
      step_guid    = step_guid
    IMPORTING
      instance     = step_instance
      no_authority = no_authority.

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

* Get the parent object i.e. scenario
  CALL METHOD step_instance->get_parent_scenario
    IMPORTING
      scenario_object = scenario_instance
      no_authority    = no_authority.

*     Raise suitable message, if no authority.
*     This authority failure flag is set in underlying layers of CM/RM, if sufficient authorizations are not maintained for CM/RM authorization objects.
    IF no_authority = true.
      MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '013' INTO dummy.
      MOVE-CORRESPONDING sy TO ls_msg.

      CALL METHOD message_handler->add_message
        EXPORTING
          message = ls_msg.

      is_ok = false.
      RETURN.
    ENDIF.

  CLEAR no_authority.

* Get the parent object of scenario i.e POBJ
  CALL METHOD scenario_instance->get_process_object
    IMPORTING
      process_object = pobj_instance
      no_authority   = no_authority.

*   Raise suitable message, if no authority.
    IF no_authority = true.
      MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '013' INTO dummy.
      MOVE-CORRESPONDING sy TO ls_msg.

      CALL METHOD message_handler->add_message
        EXPORTING
          message = ls_msg.

      is_ok = false.
      RETURN.
    ENDIF.

  CLEAR no_authority.

* Cast the POBJ interface instance to the POBJ class instance
  hrasr00_case_api ?= pobj_instance.

* Get the guid of created process object
  pobj_guid = hrasr00_case_api->a_guid.

ENDMETHOD.
