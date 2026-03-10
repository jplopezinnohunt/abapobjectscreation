METHOD add_gen_msg_to_handler.

  DATA msg_list              TYPE REF TO cl_hrbas_message_list.
  DATA messages              TYPE hrbas_message_tab.
  DATA message               TYPE hrbas_message.
  DATA msg_exists_already    TYPE boole_d.
  DATA msg                   TYPE symsg.
  DATA dummy(1)              TYPE c.
  DATA msgno                 TYPE symsgno.
  DATA message_context TYPE REF TO cl_hrasr00_message_context.

  CREATE OBJECT message_context.
* Fill the cause of message with context
  CALL METHOD message_context->set_error_category
    EXPORTING
      error_category = 'POBJEXE'.

  CASE gen_msg_typ.
    WHEN 'READ'.
      msgno = '021'.
    WHEN 'UPDATE'.
      msgno = '022'.
  ENDCASE.

* Populate a suitable message in message handler if it does not exist alredy
  msg_list ?= message_handler.

  IF msg_list IS BOUND.
    CALL METHOD msg_list->get_message_list
      IMPORTING
        messages = messages.

    LOOP AT messages INTO message.
      IF message-msgty = 'E'            AND
         message-msgid = 'HRASR00_POBJ' AND
         message-msgno = msgno.
        msg_exists_already = true.
        EXIT.
      ENDIF.
    ENDLOOP.

    IF msg_exists_already = false.
      MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER msgno INTO dummy.
      MOVE-CORRESPONDING sy TO msg.
      CALL METHOD message_handler->add_message
        EXPORTING
          message = msg
          context = message_context.
    ENDIF.
  ENDIF.
ENDMETHOD.
