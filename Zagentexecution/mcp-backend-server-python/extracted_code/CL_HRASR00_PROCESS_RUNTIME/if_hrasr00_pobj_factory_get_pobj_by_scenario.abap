METHOD if_hrasr00_pobj_factory~get_pobj_by_scenario.

  DATA dummy(1) TYPE c.
  DATA exception_obj TYPE REF TO cx_root.
  DATA application_log TYPE REF TO cl_hrasr00_application_log.
  DATA description TYPE balnrext.
  DATA msg_list TYPE REF TO cl_hrbas_message_list.
  DATA messages TYPE hrbas_message_tab.
  DATA message TYPE hrbas_message.
  DATA msg_exists_already TYPE boole_d.
  DATA msg TYPE symsg.

  CLEAR pobj_guid.
  is_ok = true.

  TRY.
** Get the guid of created process object
      call method cl_pobj_process_object=>get_top_level
        EXPORTING
          level       = '2'
          level_guid  = scenario_guid
          consumer_id = c_consumer_id
        IMPORTING
          level1_guid = pobj_guid.

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
        MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '021' INTO dummy.
        MOVE-CORRESPONDING sy TO msg.
        CALL METHOD message_handler->add_message
          EXPORTING
            message = msg.
      ENDIF.

*     Write the exception to application log
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
