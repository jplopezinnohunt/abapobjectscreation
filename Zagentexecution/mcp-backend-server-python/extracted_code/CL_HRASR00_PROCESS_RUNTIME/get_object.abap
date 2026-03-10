METHOD get_object.
  DATA process_attributes TYPE hrasr00process_attr.

  CLEAR: application, object_key.

* get application and object key
  CALL METHOD me->get_process_attributes
    EXPORTING
      message_handler    = message_handler
    IMPORTING
      process_attributes = process_attributes
      is_ok              = is_ok.
  CHECK is_ok EQ true.
  application = process_attributes-application.
  object_key = process_attributes-object_key.
  process = process_attributes-process.

ENDMETHOD.
