METHOD check_container_auth.
  DATA application TYPE asr_application.
  DATA object_key TYPE asr_object_key.
  DATA scenario_attributes TYPE hrasr00scenario_attr.
  DATA auth_users TYPE hrasr00authorizeduser_tab.
  DATA auth_users_wa TYPE hrasr00authorizeduser.
  DATA process TYPE asr_process.
  DATA dummy(1) TYPE c.
  DATA msg TYPE symsg.
  DATA message_context TYPE REF TO cl_hrasr00_message_context.

  is_ok = true.
  is_authorized = false.
* Fill the cause of message with context.
  CREATE OBJECT message_context.
  CALL METHOD message_context->set_error_category
    EXPORTING
      error_category = 'POBJEXE'.

* get application and object key and process
  CALL METHOD me->get_object
    EXPORTING
      message_handler = message_handler
    IMPORTING
      application     = application
      object_key      = object_key
      process         = process
      is_ok           = is_ok.
  CHECK is_ok EQ true.

* get scenario
  CALL METHOD me->get_scenario_attributes
    EXPORTING
      message_handler     = message_handler
      scenario_guid       = scenario_guid
    IMPORTING
      scenario_attributes = scenario_attributes
      is_ok               = is_ok.
  CHECK is_ok EQ true.

* error handling of scenario is initial
  IF scenario_attributes-scenario IS INITIAL.
    MESSAGE ID 'HRASR00_POBJ' TYPE 'E' NUMBER '000' INTO dummy.
    MOVE-CORRESPONDING sy TO msg.
    CALL METHOD message_handler->add_message
      EXPORTING
        message = msg
        context = message_context.
    is_ok = false.
    RETURN.
  ENDIF.

  auth_users_wa-uname = sy-uname.
  auth_users_wa-is_authorized = false.
  APPEND auth_users_wa TO auth_users.
  CLEAR auth_users_wa.
  CALL METHOD check_data_container_auth_user
    EXPORTING
      activity        = activity
      message_handler = message_handler
      application     = application
      object_key      = object_key
      scenario        = scenario_attributes-scenario
      process         = process
      data_container  = data_container
    IMPORTING
      is_ok           = is_ok
    CHANGING
      authorizedusers = auth_users.

  CHECK is_ok = true.

  READ TABLE auth_users WITH KEY uname = sy-uname
                                 is_authorized = true
  TRANSPORTING NO FIELDS.
  IF sy-subrc EQ 0.
    is_authorized = true.
  ELSE.
    is_authorized = false.
*    is_ok = false.
    EXIT.
  ENDIF.

ENDMETHOD.
