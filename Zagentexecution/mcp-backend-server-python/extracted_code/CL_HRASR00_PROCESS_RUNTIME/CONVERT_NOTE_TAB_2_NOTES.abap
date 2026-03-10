method CONVERT_NOTE_TAB_2_NOTES.
  DATA ls_notes TYPE hrasr00_note.
  DATA ls_notes_pobj TYPE pobjs_note.

  LOOP AT hr_notes_tab INTO ls_notes.
    MOVE-CORRESPONDING ls_notes TO ls_notes_pobj-note_key.
    MOVE-CORRESPONDING ls_notes TO ls_notes_pobj-note_attributes.
    ls_notes_pobj-note_content  = ls_notes-content.
    ls_notes_pobj-level_id = level_key-level_id.
    ls_notes_pobj-level_guid = level_key-level_guid.
    APPEND ls_notes_pobj TO notes_pobj.
  ENDLOOP.
endmethod.
