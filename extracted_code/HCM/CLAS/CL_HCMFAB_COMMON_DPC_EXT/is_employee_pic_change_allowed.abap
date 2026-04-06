METHOD is_employee_pic_change_allowed.

  DATA lv_disable_picture_change TYPE boole_d.

  rv_is_picture_change_allowed = abap_false.

  IF me->is_persinfo_application( iv_application_id ) = abap_true.
*   check in BAdI HCMFAB_B_PERSINFO_SETTINGS whether picture change functionality is enabled
    CALL BADI gb_hcmfab_b_persinfo_settings->get_settings
      EXPORTING
        iv_application_id              = iv_application_id
        iv_employee_number             = iv_employee_number
      IMPORTING
        ev_disable_employee_pic_change = lv_disable_picture_change.

    rv_is_picture_change_allowed = boolc( lv_disable_picture_change = abap_false ).
  ENDIF.

ENDMETHOD.
