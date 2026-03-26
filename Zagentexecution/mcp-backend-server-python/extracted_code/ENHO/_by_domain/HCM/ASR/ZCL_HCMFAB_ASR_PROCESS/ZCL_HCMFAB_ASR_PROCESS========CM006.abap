  method IF_HCMFAB_ASR_PROCESS_CONFG~GET_ADMIN_EMPLOYEES.
 data : lw_AGR_USERS type AGR_USERS.
    TYPES : BEGIN OF ty_pa0001,
              pernr TYPE pernr_d,
              ename	TYPE emnam,
              orgeh	TYPE orgeh,
              plans	TYPE plans,
            END OF ty_pa0001.
    DATA: lt_adminemplys_pernrs TYPE TABLE OF ty_pa0001,
          lt_position_text      TYPE TABLE OF t528t,
          ls_position           TYPE t528t,
          ls_adminemplys_pernr  TYPE ty_pa0001,
          lv_admin_pernr        TYPE pernr_d,
          ls_admin_emplys       TYPE hcmfab_s_startprc_admin_emplys,
          lt_admin_emplys       TYPE TABLE OF hcmfab_s_startprc_admin_emplys,
          l_pernr type persno,
          lv_return type  BAPIRET2,
          lv_pernr_qstr         TYPE string,
          lt_query_condition    TYPE TABLE OF string,
          ls_query_condition    TYPE string.




    select single * into lw_AGR_USERS from AGR_USERS
    WHERE UNAME = sy-uname
    and from_dat <= sy-datum
    AND TO_DAT >= sy-datum
    and ( AGR_NAME LIKE 'YSF:HR:HRA%' or AGR_NAME LIKE 'YSF:HR:HRO%'  ).
    if sy-subrc = 0 .

  SELECT PERNR into l_pernr FROM PA0000
    WHERE begda <= sy-datum
    and endda >= sy-datum
    and STAT2 = '3'.

        SELECT  pernr
          ename
            orgeh
            plans FROM pa0001 APPENDING TABLE lt_adminemplys_pernrs WHERE pernr = l_pernr  AND begda <= sy-datum AND endda >= sy-datum.

  endselect.

      else.
         clear l_pernr.
         CALL FUNCTION 'BAPI_USR01DOHR_GETEMPLOYEE'  "Determine employee from user name
         EXPORTING
          ID  = sy-uname
          BEGINDATE = sy-datum
          ENDDATE = sy-datum
         IMPORTING
          RETURN  = lv_return
          EMPLOYEENUMBER  = l_pernr.

         if l_pernr is not initial.
               SELECT  pernr
          ename
            orgeh
            plans FROM pa0001 APPENDING TABLE lt_adminemplys_pernrs WHERE pernr = l_pernr  AND begda <= sy-datum AND endda >= sy-datum.
         endif.
. " BAPI_USR01DOHR_GETEMPLOYEE

endif.

check lt_adminemplys_pernrs[] is not initial.

     SELECT * FROM t528t INTO TABLE lt_position_text FOR ALL ENTRIES IN lt_adminemplys_pernrs WHERE sprsl = sy-langu
                                    AND otype  = 'S'
                                    AND plans  = lt_adminemplys_pernrs-plans.
        SORT lt_position_text BY plans.
        LOOP AT lt_adminemplys_pernrs INTO ls_adminemplys_pernr.
          ls_admin_emplys-employee_number = ls_adminemplys_pernr-pernr.
          ls_admin_emplys-employee_name = ls_adminemplys_pernr-ename.
          ls_admin_emplys-organization_unit = ls_adminemplys_pernr-orgeh.
          ls_admin_emplys-position_id = ls_adminemplys_pernr-plans.
          CLEAR ls_position.
          READ TABLE lt_position_text INTO ls_position WITH KEY plans = ls_adminemplys_pernr-plans.
          ls_admin_emplys-position_name = ls_position-plstx.
          IF iv_emp_name IS NOT INITIAL.
            IF ls_admin_emplys-employee_name CS iv_emp_name. "cant include name in select. like cant be used in where clause
              APPEND ls_admin_emplys TO rt_admin_employees .
            ENDIF.
          ELSE.
            APPEND ls_admin_emplys TO rt_admin_employees .
          ENDIF.
        ENDLOOP.


  endmethod.
