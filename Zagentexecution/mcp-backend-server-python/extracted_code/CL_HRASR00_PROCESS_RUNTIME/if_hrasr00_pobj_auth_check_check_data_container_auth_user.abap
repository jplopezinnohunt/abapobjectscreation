METHOD if_hrasr00_pobj_auth_check~check_data_container_auth_user.
  DATA content_name TYPE asr_content_name.

  ASSERT activity IS NOT INITIAL.
  content_name = scenario.
  ASSERT content_name IS NOT INITIAL.

  is_ok = true.

* call authorization method
  CALL METHOD cl_hrasr00_auth_check=>check_authorization
    EXPORTING
      application     = application
      object_key      = object_key
      content_type    = c_content_type_scenario
      content_name    = content_name
      process         = process
      activity        = activity
      data_container  = data_container
      message_handler = message_handler
    IMPORTING
      is_ok           = is_ok
    CHANGING
      authorizedusers = authorizedusers.
ENDMETHOD.
