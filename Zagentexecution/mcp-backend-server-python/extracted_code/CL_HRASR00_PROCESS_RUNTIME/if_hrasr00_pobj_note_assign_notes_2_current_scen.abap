METHOD if_hrasr00_pobj_note~assign_notes_2_current_scen.
  DATA exception_obj TYPE REF TO cx_root.
  DATA ls_notes_pobj TYPE pobjs_note.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA lt_notes_pobj TYPE pobjt_notes.
  DATA ls_scen_note_read TYPE pobjs_level_key.
  DATA lt_scen_note_read TYPE pobjt_level_key.
  DATA lt_scen_notes TYPE pobjt_notes.
  DATA count         TYPE i. "Note 1404242
  CLEAR ls_notes_pobj.
  CLEAR lt_notes_pobj.
  CLEAR ls_scen_note_read.
  CLEAR lt_scen_note_read.
  CLEAR lt_scen_notes.
  is_ok = true.

  TRY.

*get the pobj instance.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = me->a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.

*fill the paramters to read the note key from the pobj api.
      ls_scen_note_read-level_id = 2.
      ls_scen_note_read-level_guid = me->a_scenario.
      APPEND ls_scen_note_read TO lt_scen_note_read.

*call the read method passing the above filled paramters to read the notes.

      CALL METHOD lo_pobj_instance->read
        EXPORTING
          note_params = lt_scen_note_read
        IMPORTING
          notes       = lt_scen_notes.
*map the importing notes parameter to notes table that is recognised by the pobj_api class
      CALL METHOD me->convert_note_tab_2_notes
        EXPORTING
          hr_notes_tab = notes
          level_key    = ls_scen_note_read
        IMPORTING
          notes_pobj   = lt_notes_pobj.

*check whether the imported notes parameter is present in the current scenario.
*if yes, update the note with the operation set to 'UPD_OBJ'.
*if no, insert the note with the operation set to 'INS_OBJ'.
      LOOP AT lt_notes_pobj INTO ls_notes_pobj.
        count = count + 1.
        READ TABLE lt_scen_notes WITH KEY note_key-object   = ls_notes_pobj-note_key-object
                                          note_key-name     = ls_notes_pobj-note_key-name
                                          note_key-category = ls_notes_pobj-note_key-category
                                  TRANSPORTING NO FIELDS.
        IF sy-subrc NE 0.
          ls_notes_pobj-operation = 'INS_OBJ'.

        ELSE.
          ls_notes_pobj-operation = 'UPD_OBJ'.
        ENDIF.
        MODIFY lt_notes_pobj INDEX count FROM ls_notes_pobj   TRANSPORTING operation. "Note 1404242
*       MODIFY lt_notes_pobj  INDEX sy-index FROM ls_notes_pobj   TRANSPORTING operation     .
      ENDLOOP.
*call the update api method.
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
