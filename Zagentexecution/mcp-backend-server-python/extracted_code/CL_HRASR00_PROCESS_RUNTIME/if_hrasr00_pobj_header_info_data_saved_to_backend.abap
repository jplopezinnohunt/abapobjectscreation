METHOD if_hrasr00_pobj_header_info~data_saved_to_backend.

  DATA scenario_attributes TYPE hrasr00scenario_attr.
  DATA scenarios TYPE hrasr00scenarios_tab.
  DATA scenarios_wa TYPE asr_guid.
  DATA exception_obj TYPE REF TO cx_root.

  is_ok = true.

  TRY.
      CALL METHOD me->get_all_scenarios
        EXPORTING
          message_handler = message_handler
        IMPORTING
          scenarios       = scenarios
          is_ok           = is_ok.
      CHECK is_ok EQ true.
*
      LOOP AT scenarios INTO scenarios_wa.
        CALL METHOD me->get_scenario_attributes
          EXPORTING
            scenario_guid       = scenarios_wa
            message_handler     = message_handler
          IMPORTING
            scenario_attributes = scenario_attributes
            is_ok               = is_ok.
        IF scenario_attributes-saved_to_backend = 'X'.
          return = 'X'.
          EXIT.
        ENDIF.
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
