METHOD check_attachment_auth.
  DATA auth_users TYPE hrasr00authorizeduser_tab.
  DATA auth_users_wa TYPE hrasr00authorizeduser.

  is_ok = true.
  is_authorized = false.

  auth_users_wa-uname = sy-uname.
  auth_users_wa-is_authorized = false.
  APPEND auth_users_wa TO auth_users.
  CLEAR auth_users_wa.
  CALL METHOD check_attachment_auth_user
    EXPORTING
      activity        = activity
      attachment_type = attachment_type
      message_handler = message_handler
      application     = application
      object_key      = object_key
      process         = process
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
    is_ok = false.
    EXIT.
  ENDIF.

ENDMETHOD.
