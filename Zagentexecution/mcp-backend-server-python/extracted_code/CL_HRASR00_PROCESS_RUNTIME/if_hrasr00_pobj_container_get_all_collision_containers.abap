METHOD if_hrasr00_pobj_container~get_all_collision_containers.
  DATA scenarios              TYPE hrasr00scenarios_tab.
  DATA scenarios_wa           TYPE asr_guid.
  DATA collision_container    TYPE hrasr00data_container.
  DATA exception_obj          TYPE REF TO cx_root.

  is_ok = 'X'.
  is_authorized = false.
  CLEAR collision_containers.

  TRY.
* get all scenarios of process
      CALL METHOD me->get_all_scenarios
        EXPORTING
          message_handler = message_handler
        IMPORTING
          scenarios       = scenarios
          is_ok           = is_ok.

      CHECK is_ok EQ 'X'.

      LOOP AT scenarios INTO scenarios_wa.
        CALL METHOD me->get_collision_container
          EXPORTING
            scenario_guid       = scenarios_wa
            message_handler     = message_handler
            no_auth_check       = no_auth_check
            activity            = activity
          IMPORTING
            collision_container = collision_container-data_container
            is_ok               = is_ok
            is_authorized       = is_authorized.
        IF is_ok EQ space.
          CLEAR collision_containers.
          RETURN.
        ENDIF.
        IF no_auth_check EQ false.
          CHECK is_authorized EQ true.
        ENDIF.
        MOVE scenarios_wa TO collision_container-scenario_guid.
        APPEND collision_container TO collision_containers.
        CLEAR collision_container.
      ENDLOOP.

    CATCH cx_root INTO exception_obj.
*     Populate a general message in message handler if it does not exist alredy
      CALL METHOD me->add_gen_msg_to_handler
        EXPORTING
          message_handler = message_handler
          gen_msg_typ     = 'READ'.

*     Write the exception to application log
      CALL METHOD me->write_application_log
        EXPORTING
          message_handler = message_handler
          exception_obj   = exception_obj.

      is_ok = false.
      RETURN.
  ENDTRY.

ENDMETHOD.
