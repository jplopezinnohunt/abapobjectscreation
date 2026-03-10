  METHOD is_hra_or_hro_actor.

    DATA: lv_usrid        TYPE sysid,
          lv_uname        TYPE xubname,
          lv_agr_role_hra TYPE agr_name,
          lv_agr_role_hro TYPE agr_name,
          lr_agr_name     TYPE RANGE OF agr_name,
          ls_agr_name     LIKE LINE OF lr_agr_name,
          ls_agr_users    TYPE agr_users.

    CONSTANTS: lc_agr_role_hra TYPE agr_name VALUE 'YSF:HR:HRA_______________:',
               lc_agr_role_hro TYPE agr_name VALUE 'YSF:HR:HRO_______________:'.

    lv_usrid = iv_uname.
    IF lv_usrid IS INITIAL.
      lv_usrid = sy-uname.
    ENDIF.

    MOVE lv_usrid TO lv_uname.

*   Prepare filters
    CONCATENATE lc_agr_role_hra '*'
      INTO lv_agr_role_hra.
    CONCATENATE lc_agr_role_hro '*'
      INTO lv_agr_role_hro.
    ls_agr_name-sign = 'I'.
    ls_agr_name-option = 'CP'.
    ls_agr_name-low = lv_agr_role_hro.
    APPEND ls_agr_name TO lr_agr_name.

*   By default, the person is an amployee
    ov_actor_role = c_employee.

*   Check first if user is a HRO
    SELECT SINGLE * INTO ls_agr_users
      FROM agr_users
        WHERE agr_name IN lr_agr_name
          AND uname = lv_uname
          AND from_dat <= sy-datum
          AND to_dat >= sy-datum ##WARN_OK.
    IF sy-subrc = 0.
      ov_actor_role = c_hro.
    ELSE.
*     Check if user is then HRA
      CLEAR: lr_agr_name[].
      ls_agr_name-low = lv_agr_role_hra.
      APPEND ls_agr_name TO lr_agr_name.

      SELECT SINGLE * INTO ls_agr_users
        FROM agr_users
          WHERE agr_name IN lr_agr_name
            AND uname = lv_uname
            AND from_dat <= sy-datum
            AND to_dat >= sy-datum ##WARN_OK.
      IF sy-subrc = 0.
        ov_actor_role = c_hra.
      ENDIF.

    ENDIF.

  ENDMETHOD.
