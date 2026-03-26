  method IF_HCMFAB_ASR_PROCESS_CONFG~GET_ADMIN_PERNR.

  data : lw_AGR_USERSa type AGR_USERS,
        lv_returna type  BAPIRET2,
        l_pernra type persno.

   clear EV_ADMIN_PERNR.

    select single * into lw_AGR_USERSA from AGR_USERS
    WHERE UNAME = sy-uname
    and from_dat <= sy-datum
    AND TO_DAT >= sy-datum
    and ( AGR_NAME LIKE 'YSF:HR:HRA%' or AGR_NAME LIKE 'YSF:HR:HRO%'  ).
    if sy-subrc = 0 .
       CALL FUNCTION 'BAPI_USR01DOHR_GETEMPLOYEE'  "Determine employee from user name
         EXPORTING
          ID  = sy-uname
          BEGINDATE = sy-datum
          ENDDATE = sy-datum
         IMPORTING
          RETURN  = lv_returna
          EMPLOYEENUMBER  = l_pernra.
       EV_ADMIN_PERNR = l_pernra.
       RETURN.
      ENDIF.


  endmethod.
