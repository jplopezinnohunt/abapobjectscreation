  METHOD init_table_histo_log.

    DATA : ls_breq_h TYPE zthrfiori_breq_h.

    ls_breq_h = CORRESPONDING zthrfiori_breq_h( is_request_header MAPPING status_code = request_status  first_name = creator_fname
                                                               last_name =  creator_lname  ).
    SELECT MAX( inc_nb ) FROM zthrfiori_breq_h INTO @DATA(lv_max_inc) WHERE guid EQ @is_request_header-guid.
    ADD 1 TO lv_max_inc.

*INC_NB
    ls_breq_h-inc_nb = lv_max_inc.
*REQUEST_TYPE --> same name as header
*STATUS_CODE --> mapping with request_status

*UPDATE_DATE
    ls_breq_h-update_date = sy-datum.
*UPDATE_TIME
    ls_breq_h-update_time = sy-uzeit.
*USR_ID
    ls_breq_h-usr_id = sy-uname.
*PERNR
*LAST_NAME
*FIRST_NAME
*ACTOR
    ls_breq_h-actor = zcl_hr_fiori_education_grant=>c_employee.


    INSERT INTO zthrfiori_breq_h VALUES ls_breq_h.

    DATA: ls_coment TYPE zthrfiori_coment.

*   Update table of coments

    ls_coment = CORRESPONDING zthrfiori_coment( is_request_header  MAPPING coment = note
                                                               first_name = creator_fname
                                                               last_name =  creator_lname ).


    ls_coment-creation_date = sy-datum.
    ls_coment-creation_time = sy-uzeit.
    ls_coment-usr_id = sy-uname.
*    ls_coment-pernr = iv_pernr.
    ls_coment-actor = zcl_hr_fiori_education_grant=>c_employee.
*    ls_coment-coment =  is_request_header-note.


    INSERT INTO zthrfiori_coment VALUES ls_coment.


*ls_histo-guid = iv_guid.
*    ls_histo-inc_nb = lv_inc_nb.
*    ls_histo-status_code = iv_new_status.
*    ls_histo-update_date = iv_update_date.
*    ls_histo-update_time = iv_update_time.
*    ls_histo-usr_id = iv_upd_usrid.
*    ls_histo-pernr = iv_upd_pernr.
*    ls_histo-last_name = iv_upd_last_name.
*    ls_histo-first_name = iv_upd_first_name.
*    ls_histo-actor = iv_actor.
*
*    INSERT INTO zthrfiori_breq_h VALUES ls_histo.
*    IF sy-subrc <> 0.
*      ov_return_code = 4.
*      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '003'
*        INTO ov_message
*          WITH ls_req-request_key.
*
*      ROLLBACK WORK.
*      RETURN.
*    ENDIF.
*
*    COMMIT WORK.

  ENDMETHOD.
