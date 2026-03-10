  method IF_EX_HCMFAB_COMMON~GET_ONBEHALF_EMPLOYEES.

* Determine the set of employees which can be accessed on behalf of the current user

  DATA: lt_onbehalf_pernrs  TYPE TABLE OF HCMFAB_S_ONBEHALF_EMPLOYEE,
        lS_onbehalf_pernrs  TYPE  HCMFAB_S_ONBEHALF_EMPLOYEE,
*        lt_direct_reports   TYPE pernr_tab,
        lv_pernr            TYPE pernr_d,
        lv_onbehalf_enabled TYPE boole_d,
        lv_hide_pernr       TYPE boole_d,
        lv_hide_pic         TYPE boole_d.

  FIELD-SYMBOLS: <ls_entity> TYPE hcmfab_s_onbehalf_employee.
 data : ls_entity type hcmfab_s_onbehalf_employee.


  CLEAR et_onbehalf_employees.

* check whether on-behalf is active at all for the given employee number
  me->get_configuration(
    EXPORTING
      iv_application_id       = iv_application_id
      iv_employee_number      = iv_employee_number
    IMPORTING
      ev_enable_onbehalf      = lv_onbehalf_enabled
  ).
  IF lv_onbehalf_enabled = abap_false.
    RETURN.
  ENDIF.

*  SELECT PERNR INTO TABLE lt_direct_reports  FROM PA0000
*    WHERE begda <= sy-datum
*    and endda >= sy-datum
*    and STAT2 = '3'.

  LOOP AT et_onbehalf_employees INTO   lS_onbehalf_pernrs  WHERE application_id         = iv_application_id.
   EXIT.
  ENDLOOP.
  IF SY-SUBRC NE 0.

  SELECT DISTINCT p0~PERNR as employee_number, p1~ename as employee_name , p1~sname as employee_sortname
    INTO CORRESPONDING FIELDS OF TABLE @lt_onbehalf_pernrs
    FROM PA0000 AS p0
      INNER JOIN PA0001 AS p1
      ON p0~pernr EQ p1~pernr
    WHERE p0~begda <= @sy-datum
    and p0~endda >= @sy-datum
    and p0~STAT2 = '3'
    and p1~begda <= @sy-datum
    and p1~endda >= @sy-datum.

*  lt_onbehalf_pernrs = lt_direct_reports.


* for the given PERNRs read the corresponding data
*  LOOP AT lt_onbehalf_pernrs INTO lv_pernr.
*    APPEND INITIAL LINE TO et_onbehalf_employees ASSIGNING <ls_entity>.
*  LOOP AT lt_onbehalf_pernrs INTO DATA(ls_pernr).
*    APPEND INITIAL LINE TO et_onbehalf_employees ASSIGNING <ls_entity>.
*
*   <ls_entity>-application_id         = iv_application_id.
*    <ls_entity>-employee_number        = lv_pernr.
*    <ls_entity>-employee_name          = go_employee_api->get_name( iv_pernr         = lv_pernr
*                                                                    iv_no_auth_check = abap_true ).
*    <ls_entity>-employee_sortname      = go_employee_api->get_sortable_name( iv_pernr         = lv_pernr
*                                                                             iv_no_auth_check = abap_true ).
*    <ls_entity>-requester_number       = iv_employee_number.

*    READ TABLE lt_direct_reports WITH KEY table_line = lv_pernr TRANSPORTING NO FIELDS.
*    IF sy-subrc = 0.
*      <ls_entity>-employee_category      = gc_employee_category-direct_report.
*      <ls_entity>-is_hidden_in_list      = abap_false.
****CODE TO BE ACTIVATED BY CUSTOMERS USING MY TEAM WITH DRILLDOWN AND ON-BEHALF***
**    ELSE.
**      <ls_entity>-employee_category      = gc_employee_category-indirect_report.
**      <ls_entity>-is_hidden_in_list      = abap_true. "to ensure these employees do not appear in the onBehalf button
****CODE TO BE ACTIVATED BY CUSTOMERS USING MY TEAM WITH DRILLDOWN AND ON-BEHALF***
*    ENDIF.

*   Leave default version id empty. It will then automatically be calculated later on, but only for the relevant employees.
*    CLEAR <ls_entity>-default_version_id.

*   get the configuration info for the "on-behalf employee"
*    me->get_configuration(
*      EXPORTING
*        iv_application_id            = iv_application_id
*        iv_employee_number           = lv_pernr
*      IMPORTING
*        ev_hide_employee_picture     = lv_hide_pic
*        ev_hide_employee_number      = lv_hide_pernr
*        ev_show_empl_number_wo_zeros = <ls_entity>-show_employee_number_wo_zeros
*    ).
*
*    <ls_entity>-show_employee_number      = abap_false .
*    <ls_entity>-show_employee_picture     = abap_false .
*
*    IF <ls_entity>-show_employee_number = abap_true.
*      "display the personal number in the dialog (additional properties can be added as comma separated list)
*      <ls_entity>-displayed_properties = 'EmployeeId'.
*    ELSE.
*      "if no employee number should be shown we display the employee´s position to better distinguish the employees
*      <ls_entity>-description =
*         go_employee_api->get_employee_details( iv_application_id   = iv_application_id
*                                                iv_pernr            = lv_pernr )-employee_position_longtext.
*    ENDIF.

    "in SAP-standard, managers are not allowed to change the employee picture of the onBehalf-employees
*    <ls_entity>-is_change_picture_enabled = abap_false.
*  ENDLOOP.



  et_onbehalf_employees[] = lt_onbehalf_pernrs[].

 ls_entity-application_id         = iv_application_id.
  modify et_onbehalf_employees from  ls_entity TRANSPORTING application_id where application_id = ''.
 ls_entity-employee_category      =  gc_employee_category-direct_report.
  modify et_onbehalf_employees from  ls_entity TRANSPORTING employee_category where employee_category = ''.

  ls_entity-show_employee_number = abap_true .
  modify et_onbehalf_employees from  ls_entity TRANSPORTING show_employee_number where show_employee_number IS INITIAL.

  ls_entity-show_employee_picture = abap_false .
  modify et_onbehalf_employees from  ls_entity TRANSPORTING show_employee_picture where show_employee_picture IS INITIAL.

  ls_entity-is_change_picture_enabled = abap_false.
  modify et_onbehalf_employees from  ls_entity TRANSPORTING is_change_picture_enabled where is_change_picture_enabled IS INITIAL.

  ls_entity-requester_number = iv_employee_number.
  modify et_onbehalf_employees from  ls_entity TRANSPORTING requester_number where requester_number IS INITIAL.

  ls_entity-displayed_properties = 'EmployeeId'.
  modify et_onbehalf_employees from  ls_entity TRANSPORTING displayed_properties where displayed_properties IS INITIAL.


  SORT et_onbehalf_employees BY employee_category employee_sortname.
  DELETE et_onbehalf_employees where employee_name is initial.

  ENDIF.
  endmethod.
