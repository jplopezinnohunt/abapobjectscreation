METHOD save.

  DATA no_authority TYPE boole_d.
  DATA ls_msg TYPE symsg.
  DATA dummy(1) TYPE c.
  DATA lo_pobj_instance TYPE REF TO if_pobj_process_object.
  DATA exception_obj TYPE REF TO cx_root.


  is_ok = true.

  TRY.
*get the pobj_instance .

      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = me->a_pobj
          consumer_id   = c_consumer_id
        IMPORTING
          pobj_instance = lo_pobj_instance.
*Save to backend
      CALL METHOD lo_pobj_instance->flush
*  EXPORTING
*    NEW_TASK =  'X'
          .
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
