METHOD if_hrasr00_pobj_save~flush_all.

  DATA exception_obj TYPE REF TO cx_root.

  is_ok = true.

  TRY.
      CALL METHOD me->lock
        EXPORTING
          message_handler = message_handler
        IMPORTING
          is_ok           = is_ok.

      CHECK is_ok = true.

      CALL METHOD me->save
        EXPORTING
          message_handler = message_handler
          dequeue         = dequeue
        IMPORTING
          is_ok           = is_ok.

      IF is_delete_draft EQ if_hrasr00_process_constants=>false. " Note 1381661
        CALL METHOD me->unlock
          EXPORTING
            message_handler = message_handler
          IMPORTING
            is_ok           = is_ok.
      ENDIF.

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
*  CALL METHOD cl_hrasr00_case=>save_all
*    EXPORTING
*      dequeue = if_srm=>true.

ENDMETHOD.
