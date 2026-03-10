METHOD write_application_log.

  DATA process_attributes TYPE hrasr00process_attr.
  DATA reference_number   TYPE asr_reference_number.
  DATA application_log    TYPE REF TO cl_hrasr00_application_log.
  DATA description        TYPE balnrext.
  DATA message_list       TYPE REF TO cl_hrbas_message_list.

  is_ok = true.

  CALL METHOD me->get_process_attributes
    EXPORTING
      message_handler    = message_handler
    IMPORTING
      process_attributes = process_attributes.

  reference_number = process_attributes-reference_number.

  IF NOT reference_number IS INITIAL.
    CONCATENATE 'Prozessreferenznummer'(001) '-' reference_number INTO description.
  ELSE.
    CONCATENATE 'Prozess'(002) '-' process_attributes-process ';' 'Objektschlüssel'(003)  '-' process_attributes-object_key INTO description.
  ENDIF.

  application_log = cl_hrasr00_application_log=>get_instance( description = description
                                                              object      = c_application_log_object
                                                              subobject   = c_application_log_subobject ).
  CALL METHOD application_log->add_exception
    EXPORTING
      exception = exception_obj.

  message_list ?= message_handler.
  IF message_list IS BOUND.
    CALL METHOD application_log->add_messages
      EXPORTING
        message_list = message_list.
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

ENDMETHOD.
