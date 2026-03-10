METHOD get_employee_pic_settings.

  IF me->is_persinfo_application( iv_application_id ) = abap_true.

    CALL BADI gb_hcmfab_b_persinfo_settings->get_settings
      EXPORTING
        iv_application_id            = iv_application_id
        iv_employee_number           = iv_employee_number
      IMPORTING
        ev_employee_pic_max_filesize = ev_employee_pic_max_filesize.

  ENDIF.

  IF ev_employee_pic_max_filesize IS INITIAL.
    CLEAR ev_employee_pic_max_filesize.
  ENDIF.
ENDMETHOD.
