METHOD if_hrasr00_pobj_save~lock_all.

  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA ls_lock_pobj TYPE pobjs_lock_objects.
  DATA lt_lock_pobj TYPE pobjt_lock_objects.
  DATA exception_obj TYPE REF TO cx_root.
  is_ok = true.

**** Lock_all does exactly what Lock does, as locking is only possible at Process Level and not Scenario or Step level anymore.
  CALL METHOD me->lock
    EXPORTING
      message_handler = message_handler
    IMPORTING
      is_ok           = is_ok.

  RETURN.

*  TRY.
**get the pobj_instance .
*      CALL METHOD cl_pobj_process_object=>get
*        EXPORTING
*          pobj_guid     = me->a_pobj
*          consumer_id   = c_consumer_id
*        IMPORTING
*          pobj_instance = lo_pobj_instance.
*      IF no_lock_pobj EQ false.
*        ls_lock_pobj-level_id = 1.
*        ls_lock_pobj-level_guid = me->a_pobj.
*        APPEND ls_lock_pobj TO lt_lock_pobj.
*      ENDIF.
*      IF no_lock_scenobj EQ false.
*        IF NOT me->a_scenario IS INITIAL.
*          ls_lock_pobj-level_id = 2.
*          ls_lock_pobj-level_guid = me->a_scenario.
*          APPEND ls_lock_pobj TO lt_lock_pobj.
*        ENDIF.
*      ENDIF.
*      IF no_lock_stepobj EQ false.
*        IF NOT me->a_step IS INITIAL.
*          ls_lock_pobj-level_id = 3.
*          ls_lock_pobj-level_guid = me->a_step.
*          APPEND ls_lock_pobj TO lt_lock_pobj.
*        ENDIF.
*      ENDIF.
*      IF lt_lock_pobj IS NOT INITIAL.
*        CALL METHOD lo_pobj_instance->lock
*          EXPORTING
*            lock_object = lt_lock_pobj.
*      ENDIF.
*    CATCH cx_root INTO exception_obj.
**     Populate a general message in message handler if it does not exist alredy
*      CALL METHOD me->add_gen_msg_to_handler
*        EXPORTING
*          message_handler = message_handler
*          gen_msg_typ     = 'UPDATE'.
*
**     Write the exception to application log
*      CALL METHOD me->write_application_log
*        EXPORTING
*          message_handler = message_handler
*          exception_obj   = exception_obj.
*
*      is_ok = false.
*      RETURN.
*  ENDTRY.

ENDMETHOD.
