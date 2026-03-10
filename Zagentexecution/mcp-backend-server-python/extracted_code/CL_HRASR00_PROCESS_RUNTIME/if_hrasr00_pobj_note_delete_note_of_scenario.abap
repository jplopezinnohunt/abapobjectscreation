METHOD if_hrasr00_pobj_note~delete_note_of_scenario.
  DATA exception_obj TYPE REF TO cx_root.
  DATA scenarioguid TYPE asr_guid.
  DATA ls_notes_pobj TYPE pobjs_note.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA lt_notes_pobj TYPE pobjt_notes.

  CLEAR ls_notes_pobj.
  CLEAR lt_notes_pobj.
  is_ok = true.
  IF scenario_guid IS NOT INITIAL.
    scenarioguid = scenario_guid.
  ELSE.
    scenarioguid = a_scenario.
  ENDIF.

  TRY.

*get the pobj instance.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = me->a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.
*fill the parameters for the update method.
*the function of delete_all when note_key is initial is taken care by the update api method.
      IF delete_all NE 'X'.
        MOVE-CORRESPONDING note_key TO ls_notes_pobj-note_key.
      ENDIF.
      ls_notes_pobj-level_id = 2.
      ls_notes_pobj-level_guid = scenarioguid.
      ls_notes_pobj-operation = 'DEL_OBJ'.
      APPEND ls_notes_pobj TO lt_notes_pobj.

      CALL METHOD lo_pobj_instance->update
        CHANGING
          notes = lt_notes_pobj.
    CATCH cx_root INTO exception_obj.
*     Populate a general message in message handler if it does not exist alredy
      CALL METHOD me->add_gen_msg_to_handler
        EXPORTING
          message_handler = message_handler
          gen_msg_typ     = 'UPDATE'.

*     Write the exception to application log
      CALL METHOD me->write_application_log
        EXPORTING
          message_handler = message_handler
          exception_obj   = exception_obj.

      is_ok = false.
      RETURN.
  ENDTRY.
ENDMETHOD.
