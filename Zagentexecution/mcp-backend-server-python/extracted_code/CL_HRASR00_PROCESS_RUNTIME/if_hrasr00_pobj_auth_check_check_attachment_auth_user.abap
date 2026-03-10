METHOD if_hrasr00_pobj_auth_check~check_attachment_auth_user.
  DATA content_name TYPE asr_content_name.
  DATA dummy(1) TYPE c.
  DATA exception_obj TYPE REF TO cx_root.
  DATA application_log TYPE REF TO cl_hrasr00_application_log.
  DATA description TYPE balnrext.
  DATA msg_list TYPE REF TO cl_hrbas_message_list.
  DATA messages TYPE hrbas_message_tab.
  DATA message TYPE hrbas_message.
  DATA msg_exists_already TYPE boole_d.
  DATA msg TYPE symsg.
  DATA message_context TYPE REF TO cl_hrasr00_message_context.
  FIELD-SYMBOLS: <fs_authorizeduser_wa> TYPE hrasr00authorizeduser.

  is_ok = true.
  IF activity NE 'R' AND
     activity NE 'W'.
    LOOP AT authorizedusers ASSIGNING <fs_authorizeduser_wa>.
      <fs_authorizeduser_wa>-is_authorized = 'X'.
    ENDLOOP.
    EXIT.
  ENDIF.

  content_name = attachment_type.
  IF content_name IS INITIAL.
    is_ok = false.
    EXIT.
  ENDIF.

  TRY.
* call authorization method
      CALL METHOD cl_hrasr00_auth_check=>check_authorization
        EXPORTING
          application     = application
          object_key      = object_key
          content_type    = c_content_type_attachment
          content_name    = content_name
          process         = process
          activity        = activity
          message_handler = message_handler
        IMPORTING
          is_ok           = is_ok
        CHANGING
          authorizedusers = authorizedusers.
      CHECK is_ok EQ true.
    CATCH cx_root INTO exception_obj.
*     Populate a general message in message handler if it does not exist already
      msg_list ?= message_handler.

      CALL METHOD msg_list->get_message_list
        IMPORTING
          messages = messages.
      LOOP AT messages INTO message.
        IF message-msgty = 'E' AND
           message-msgid = 'HRASR00_POBJ' AND
           message-msgno = '021'.
          msg_exists_already = true.
          EXIT.
        ENDIF.
      ENDLOOP.
      IF msg_exists_already = false.
        CREATE OBJECT message_context.
* Fill the cause of message with context
        CALL METHOD message_context->set_error_category
          EXPORTING
            error_category = 'POBJEXE'.
        MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '021' INTO dummy.
        MOVE-CORRESPONDING sy TO msg.
        CALL METHOD message_handler->add_message
          EXPORTING
            message = msg
            context = message_context.
      ENDIF.

*     Write the exception to application log
      CONCATENATE 'Inhaltsname'(004) '-' content_name ';' 'Objektschlüssel'(003)  '-' object_key INTO description.

      application_log = cl_hrasr00_application_log=>get_instance( description = description
                                                                  object      = c_application_log_object
                                                                  subobject   = c_application_log_subobject ).
      CALL METHOD application_log->add_exception
        EXPORTING
          exception = exception_obj.

      IF msg_list IS BOUND.
        CALL METHOD application_log->add_messages
          EXPORTING
            message_list = msg_list.
      ENDIF.

* Do a rollback/commit if the flag 'no_commit' is not set by the caller of POBJ runtime
      IF no_commit = false.
* Discard any changes made in the backend and / or process object
        ROLLBACK WORK.
        CALL METHOD application_log->persist_log.
* Commit work so that the application log entries are persisted to DB
        COMMIT WORK.
      ELSE.
        CALL METHOD application_log->persist_log.
      ENDIF.

      is_ok = false.
      RETURN.
  ENDTRY.
ENDMETHOD.
