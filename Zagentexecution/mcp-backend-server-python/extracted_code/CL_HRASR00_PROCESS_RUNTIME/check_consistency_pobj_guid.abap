METHOD check_consistency_pobj_guid.
  DATA process          TYPE asr_process.
  DATA no_authority     TYPE boole_d.
  DATA dummy(1)         TYPE c.
  DATA msg              TYPE symsg.
  DATA pobj_process_instance TYPE REF TO if_pobj_process_object.
  DATA message_context TYPE REF TO cl_hrasr00_message_context.

  is_ok = true.
  CLEAR is_consistent.

  TRY.
      CALL METHOD cl_pobj_process_object=>get
        EXPORTING
          pobj_guid     = pobj_guid
          consumer_id   = c_consumer_id  "TO BE CONFIRMED!!
        IMPORTING
          pobj_instance = pobj_process_instance.
    CATCH cx_pobj_process_object.
*   Raise a suitable message if POBJ guid is inconsistent
      CREATE OBJECT message_context.
* Fill the cause of message with context
      CALL METHOD message_context->set_error_category
        EXPORTING
          error_category = 'POBJEXE'.
      MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '025' WITH pobj_guid INTO dummy.
      MOVE-CORRESPONDING sy TO msg.

      CALL METHOD message_handler->add_message
        EXPORTING
          message = msg
          context = message_context.

      is_ok = false.
      RETURN.
  ENDTRY.


* POBJ guid is consistent if we are able to get a process instance
  IF pobj_process_instance IS BOUND.
    is_consistent = true.
  ELSE.
*   Raise a suitable message if POBJ guid is inconsistent
      CREATE OBJECT message_context.
* Fill the cause of message with context
      CALL METHOD message_context->set_error_category
        EXPORTING
          error_category = 'POBJEXE'.
      MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '025' WITH pobj_guid INTO dummy.
      MOVE-CORRESPONDING sy TO msg.

      CALL METHOD message_handler->add_message
        EXPORTING
          message = msg
          context = message_context.

    is_ok = false.
    RETURN.
  ENDIF.

ENDMETHOD.
