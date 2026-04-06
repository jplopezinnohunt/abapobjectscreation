  METHOD get_main_role.

    DATA: lv_pernr         TYPE pernr_d,
          lv_usrid         TYPE sysid,
          lv_agr_role_hra  TYPE agr_name,
          ls_agr_users     TYPE agr_users,
          lr_agr_name      TYPE RANGE OF agr_name,
          ls_agr_name      LIKE LINE OF lr_agr_name,
          ls_result        TYPE swhactor ##NEEDED,
          lt_result        TYPE STANDARD TABLE OF swhactor,
          lo_benefits_util TYPE REF TO zcl_hr_fiori_benefits.

    CONSTANTS: lc_agr_role_hra TYPE agr_name VALUE 'YSF:HR:HRA_______________:'.

*   Get user infos
    CREATE OBJECT lo_benefits_util.
    lo_benefits_util->get_actor_infos( IMPORTING ov_pernr = lv_pernr
                                                 ov_usrid = lv_usrid ).

*   Prepare filters
    CONCATENATE lc_agr_role_hra '*'
      INTO lv_agr_role_hra.
    ls_agr_name-sign = 'I'.
    ls_agr_name-option = 'CP'.
    ls_agr_name-low = lv_agr_role_hra.
    APPEND ls_agr_name TO lr_agr_name.

*   By default, the person is an amployee
    ov_actor = c_employee.

*   Check first if user is a HRA
    SELECT SINGLE * INTO ls_agr_users
      FROM agr_users
        WHERE agr_name IN lr_agr_name
          AND uname = lv_usrid
          AND from_dat <= sy-datum
          AND to_dat >= sy-datum ##WARN_OK.
    IF sy-subrc = 0.
      ov_actor = c_hra.
    ELSE.
*     Check if user a manager
      CALL FUNCTION 'RH_STRUC_GET'
        EXPORTING
          act_otype  = 'P'
          act_objid  = lv_pernr
          act_wegid  = 'SAP_MANG'
          act_plvar  = '01'
          act_begda  = sy-datum
          act_endda  = sy-datum
        TABLES
          result_tab = lt_result.

      LOOP AT lt_result INTO ls_result
        WHERE otype = 'O'.
        ov_actor = c_manager.
        EXIT.
      ENDLOOP.

    ENDIF.

  ENDMETHOD.
