METHOD if_hrasr00_pobj_header_info~is_persistent.

  DATA exception_obj TYPE REF TO cx_root.
  DATA pobj_instance_process_obj TYPE REF TO if_pobj_process_object.
  is_ok = true.

* Get the process object instance
  TRY.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          consumer_id   = c_consumer_id
          pobj_guid     = me->a_pobj
        IMPORTING
          pobj_instance = pobj_instance_process_obj.

      CALL METHOD pobj_instance_process_obj->is_persistent
        RECEIVING
          return = return.

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
