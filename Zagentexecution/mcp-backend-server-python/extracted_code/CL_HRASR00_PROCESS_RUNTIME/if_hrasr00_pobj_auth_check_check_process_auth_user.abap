METHOD if_hrasr00_pobj_auth_check~check_process_auth_user.
  DATA process_attributes TYPE hrasr00process_attr.
  DATA instance_pobj_runtime TYPE REF TO if_hrasr00_process_runtime.
  DATA content_name TYPE asr_content_name.
  DATA exception_obj TYPE REF TO cx_root.
  DATA application_log TYPE REF TO cl_hrasr00_application_log.
  DATA description TYPE balnrext.
  DATA msg_list TYPE REF TO cl_hrbas_message_list.
  DATA messages TYPE hrbas_message_tab.
  DATA message TYPE hrbas_message.
  DATA msg_exists_already TYPE boole_d.
  DATA msg TYPE symsg.
  DATA dummy(1) TYPE c.
  DATA message_context TYPE REF TO cl_hrasr00_message_context.
  DATA data_container TYPE xstring.
  DATA data_containers TYPE hrasr00data_container_tab.
  DATA data_containers_wa TYPE hrasr00data_container.
  DATA lines TYPE i.
  FIELD-SYMBOLS: <fs_authorizeduser_wa> TYPE hrasr00authorizeduser.

  is_ok = true.
  IF activity NE 'S' AND
     activity NE 'R' AND
     activity NE 'D' AND
     activity NE 'X' AND
     activity NE 'W'.
    LOOP AT authorizedusers ASSIGNING <fs_authorizeduser_wa>.
      <fs_authorizeduser_wa>-is_authorized = false.
    ENDLOOP.
    RETURN.
  ENDIF.

  TRY.
      " IF ( application IS INITIAL OR Note " 1689513 - Pass data container from process browser
      " object_key IS INITIAL OR
      " process_name IS INITIAL ) AND
*      IF process_guid IS NOT INITIAL.
*   ***** NOTE: 1852082 : in relation to the existing note 1689513.To avoid access of the data container read for authorizations that leads to performance issue.
    IF ( application IS INITIAL OR
      object_key IS INITIAL OR
      process_name IS INITIAL ) AND
      process_guid IS NOT INITIAL.

        CALL METHOD cl_hrasr00_process_runtime=>get_instance
          EXPORTING
            pobj_guid             = process_guid
            message_handler       = message_handler
            activity              = activity
          IMPORTING
            instance_pobj_runtime = instance_pobj_runtime
            is_ok                 = is_ok.

        CHECK is_ok EQ true.
        CALL METHOD instance_pobj_runtime->get_process_attributes
          EXPORTING
            message_handler    = message_handler
          IMPORTING
            process_attributes = process_attributes
            is_ok              = is_ok.

        CHECK is_ok EQ true.
        content_name = process_attributes-process.

***Correction : Pass the latest datacontainer as well to the check_auth method

        CALL METHOD instance_pobj_runtime->get_all_data_containers
          EXPORTING
            message_handler = message_handler
            activity        = activity
          IMPORTING
            data_containers = data_containers
            is_ok           = is_ok.
        CHECK is_ok EQ true.
        IF data_containers IS NOT INITIAL.
          DESCRIBE TABLE data_containers LINES lines.
          READ TABLE data_containers INTO data_containers_wa INDEX lines.
          data_container = data_containers_wa-data_container.
        ENDIF.

      ELSE.
        process_attributes-application = application.
        process_attributes-object_key = object_key.
        content_name = process_name.
      ENDIF.

* if there is no process specified, the auth check is immaterial
      IF content_name IS INITIAL.
        is_ok = true.
        LOOP AT authorizedusers ASSIGNING <fs_authorizeduser_wa>.
          <fs_authorizeduser_wa>-is_authorized = 'X'.
        ENDLOOP.
        EXIT.
      ENDIF.




* call authorization method
      CALL METHOD cl_hrasr00_auth_check=>check_authorization
        EXPORTING
          application     = process_attributes-application
          object_key      = process_attributes-object_key
          content_type    = c_content_type_process
          content_name    = content_name
          data_container  = data_container
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
      IF NOT process_attributes-reference_number IS INITIAL.
        CONCATENATE 'Prozessreferenznummer'(001) '-' process_attributes-reference_number INTO description.
      ELSE.
        CONCATENATE 'Prozess'(002) '-' content_name ';' 'Objektschlüssel'(003)  '-' process_attributes-object_key INTO description.
      ENDIF.

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
