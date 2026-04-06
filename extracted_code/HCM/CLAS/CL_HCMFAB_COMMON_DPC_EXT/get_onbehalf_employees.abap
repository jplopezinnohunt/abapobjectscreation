METHOD get_onbehalf_employees.

  DATA lv_onbehalf_enabled TYPE boole_d.

  CLEAR et_onbehalf_employees.

* check whether on-behalf is active at all for the given employee id
  CALL BADI gb_hcmfab_b_common->get_configuration
    EXPORTING
      iv_application_id  = iv_application_id
      iv_employee_number = iv_requester_number
    IMPORTING
      ev_enable_onbehalf = lv_onbehalf_enabled.
  IF lv_onbehalf_enabled = abap_false.
    RETURN.
  ENDIF.

* get the list of on-behalf employees
  et_onbehalf_employees = go_employee_api->get_onbehalf_employees( iv_application_id  = iv_application_id
                                                                   iv_employee_number = iv_requester_number ).

  IF iv_onbehalf_number IS NOT INITIAL.
    DELETE et_onbehalf_employees WHERE employee_number <> iv_onbehalf_number.

*   Check that the requested person was found (could happen because of inconsistent BAdI implementations)
    IF lines( et_onbehalf_employees ) = 0.
      RAISE EXCEPTION TYPE cx_hcmfab_common
        EXPORTING
          textid   = cx_hcmfab_common=>illegal_employeenumber
          mv_pernr = iv_onbehalf_number.
    ENDIF.

  ELSEIF iv_only_visible_pernrs = abap_true.
    DELETE et_onbehalf_employees WHERE is_hidden_in_list = abap_true.
  ENDIF.

ENDMETHOD.
