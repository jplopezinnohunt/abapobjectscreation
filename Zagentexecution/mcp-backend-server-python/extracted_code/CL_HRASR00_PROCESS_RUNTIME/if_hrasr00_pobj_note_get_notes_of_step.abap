METHOD if_hrasr00_pobj_note~get_notes_of_step.
  DATA stepguid TYPE asr_guid.
  DATA exception_obj TYPE REF TO cx_root.
  DATA ls_step_note_read TYPE pobjs_level_key.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA lt_step_note_read TYPE pobjt_level_key.
  DATA lt_step_notes TYPE pobjt_notes.
  DATA ls_step_notes TYPE pobjs_note.
  DATA ls_notes TYPE  hrasr00_note.
  clear notes.
  is_ok = true.
  IF step_guid IS NOT INITIAL.
    stepguid = step_guid.
  ELSE.
    stepguid = a_step.
  ENDIF.

  TRY.
*get the pobj instance.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = me->a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.

*fill the paramters to read the note key from the pobj api.
      ls_step_note_read-level_id = 3.
      ls_step_note_read-level_guid = stepguid.
      APPEND ls_step_note_read TO lt_step_note_read.

*call the read method passing the above filled paramters to read the notes.

          CALL METHOD lo_pobj_instance->read
            EXPORTING
              note_params = lt_step_note_read
            IMPORTING
              notes       = lt_step_notes.

*map the obtained notes from the pobj_api class to the exporting parameter.
      LOOP AT lt_step_notes INTO ls_step_notes.
        MOVE-CORRESPONDING ls_step_notes-note_key TO ls_notes.
        MOVE-CORRESPONDING ls_step_notes-note_attributes TO ls_notes.
        ls_notes-content = ls_step_notes-note_content.
        APPEND ls_notes TO notes.
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
