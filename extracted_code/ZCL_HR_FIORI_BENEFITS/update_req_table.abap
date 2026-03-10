  METHOD update_req_table.

    DATA: ls_req TYPE zthrfiori_breq.

*   Get benefits request
    SELECT SINGLE * INTO ls_req
      FROM zthrfiori_breq
        WHERE guid = iv_guid.

*   Update table of  request
    SELECT SINGLE name INTO ls_req-request_status_txt
      FROM zthrfiori_status
        WHERE id = iv_new_status
          AND language = sy-langu.

    ls_req-request_status = iv_new_status.
    ls_req-last_upd_date = iv_update_date.
    ls_req-last_upd_time = iv_update_time.
    ls_req-upd_usr_id = iv_upd_usrid.
    ls_req-upd_pernr = iv_upd_pernr.
    ls_req-upd_lname = iv_upd_last_name.
    ls_req-upd_fname = iv_upd_first_name.
    ls_req-next_actor = iv_next_actor.
    ls_req-flag_deleted = iv_del_flag.

    UPDATE zthrfiori_breq FROM ls_req.
    IF sy-subrc <> 0.
      ov_return_code = 4.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '002'
        INTO ov_message
          WITH ls_req-request_key iv_new_status.

      ROLLBACK WORK.
      RETURN.
    ENDIF.

    COMMIT WORK.

  ENDMETHOD.
