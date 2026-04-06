  method IF_EX_HCMFAB_COMMON~EMPLOYEE_IS_ONBEHALF_RELEVANT.
*CALL METHOD SUPER->IF_EX_HCMFAB_COMMON~EMPLOYEE_IS_ONBEHALF_RELEVANT
*  EXPORTING
*    IV_APPLICATION_ID  =
*    IV_EMPLOYEE_NUMBER =
*    IV_ONBEHALF_NUMBER =
**  IMPORTING
**    EV_IS_RELEVANT     =
*    .

* Check if a given employee is included in the list of employees who can be accessed on behalf of the current user
* Simple implementation would be:
* Call me->get_onbehalf_employees( ) and check if iv_onbehalf_number is included in the result

* More efficient way to check if the direct reports are used as on behalf employee set:
* Check if the manager of the given onbehalt employee is the current employee number
    DATA lt_manager_pernrs TYPE pernr_tab.

    ev_is_relevant = abap_false.

CALL METHOD ME->IF_EX_HCMFAB_COMMON~GET_CONFIGURATION
  EXPORTING
    IV_APPLICATION_ID              = iv_application_id
    IV_EMPLOYEE_NUMBER             = iv_onbehalf_number
  IMPORTING
*    EV_HIDE_EMPLOYEE_PICTURE       =
*    EV_HIDE_EMPLOYEE_NUMBER        =
*    EV_HIDE_CE_BUTTON              =
    EV_ENABLE_ONBEHALF             = ev_is_relevant.
*    EV_SHOW_EMPL_NUMBER_WO_ZEROS   =
*    EV_USE_ONBEHALF_BACKEND_SEARCH =
    .



*    me->get_manager(
*      EXPORTING
*        iv_application_id = iv_application_id
*        iv_employee_pernr = iv_onbehalf_number
*      IMPORTING
*        et_manager_pernrs  = lt_manager_pernrs
*    ).
*    READ TABLE lt_manager_pernrs WITH KEY table_line = iv_employee_number TRANSPORTING NO FIELDS.
*    IF sy-subrc = 0.
*      ev_is_relevant = abap_true.
*    ENDIF.
*


  endmethod.
