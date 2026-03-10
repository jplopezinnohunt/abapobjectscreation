  method IF_EX_HCMFAB_COMMON~GET_CONFIGURATION.
*CALL METHOD SUPER->IF_EX_HCMFAB_COMMON~GET_CONFIGURATION
*  EXPORTING
*    IV_APPLICATION_ID              =
*    IV_EMPLOYEE_NUMBER             =
**  IMPORTING
**    EV_HIDE_EMPLOYEE_PICTURE       =
**    EV_HIDE_EMPLOYEE_NUMBER        =
**    EV_HIDE_CE_BUTTON              =
**    EV_ENABLE_ONBEHALF             =
**    EV_SHOW_EMPL_NUMBER_WO_ZEROS   =
**    EV_USE_ONBEHALF_BACKEND_SEARCH =
*    .

  data : lw_AGR_USERS type AGR_USERS.
    ev_hide_employee_picture     = abap_true.
    ev_hide_employee_number      = abap_false.
    ev_hide_ce_button            = abap_true.

      ev_enable_onbehalf           = abap_false.
      ev_use_onbehalf_backend_search = abap_false.


*    select single * into lw_AGR_USERS from AGR_USERS
*    WHERE UNAME = sy-uname
*    and from_dat <= sy-datum
*    AND TO_DAT >= sy-datum
*    and ( AGR_NAME = 'YSF:HR:HRA_______________:' or AGR_NAME = 'YSF:HR:HRO_______________:'  ).

    select single * into lw_AGR_USERS from AGR_USERS
    WHERE UNAME = sy-uname
    and from_dat <= sy-datum
    AND TO_DAT >= sy-datum
    and ( AGR_NAME LIKE 'YSF:HR:HRA%' or AGR_NAME LIKE 'YSF:HR:HRO%'  ).
    if sy-subrc = 0.
         ev_enable_onbehalf           = abap_true.
         ev_use_onbehalf_backend_search = abap_true.
    endif.

    IF SY-uname = 'G_SONNET'. " to be removed only during dev test
         ev_enable_onbehalf           = abap_true.
        ev_use_onbehalf_backend_search = abap_true.
    endif.
     IF SY-uname = 'GD_SCHELLINC'. " to be removed only during dev test
         ev_enable_onbehalf           = abap_true.
        ev_use_onbehalf_backend_search = abap_true.
    endif.

    ev_show_empl_number_wo_zeros = abap_false.


* On_behalf is switched off by default for compatibility reasons
* To activate it for all users who are mangers the following code could be used:

*  ev_enable_onbehalf = boolc( go_employee_api->is_manager( iv_application_id = iv_application_id
*                                                           iv_pernr          = iv_employee_number ) = abap_true ).

* In case that on behalf is active, transfer all data to the frontend. This is faster for small number of employees.
* The backend search would only transfer the visible employees to the frontend, at the cost of multiple smaller requests.
  endmethod.
