  METHOD update_histo_table.

    DATA: lv_inc_nb TYPE ze_hrfiori_incrment_nb,
          ls_req    TYPE zthrfiori_breq,
          ls_histo  TYPE zthrfiori_breq_h,
          lt_histo  TYPE STANDARD TABLE OF zthrfiori_breq_h.

    lv_inc_nb = '00'.

*   Get benefits request
    SELECT SINGLE * INTO ls_req
      FROM zthrfiori_breq
        WHERE guid = iv_guid.

*   Update history log
    SELECT * INTO TABLE lt_histo
      FROM zthrfiori_breq_h
        WHERE guid = iv_guid.

    IF sy-subrc = 0.
      SORT lt_histo BY inc_nb DESCENDING.
      READ TABLE lt_histo INTO ls_histo INDEX 1.
      lv_inc_nb = ls_histo-inc_nb + 1.
    ENDIF.

    ls_histo-guid = iv_guid.
    ls_histo-inc_nb = lv_inc_nb.
    ls_histo-status_code = iv_new_status.
    ls_histo-update_date = iv_update_date.
    ls_histo-update_time = iv_update_time.
    ls_histo-usr_id = iv_upd_usrid.
    ls_histo-pernr = iv_upd_pernr.
    ls_histo-last_name = iv_upd_last_name.
    ls_histo-first_name = iv_upd_first_name.
    ls_histo-actor = iv_actor.

    INSERT INTO zthrfiori_breq_h VALUES ls_histo.
    IF sy-subrc <> 0.
      ov_return_code = 4.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '003'
        INTO ov_message
          WITH ls_req-request_key.

      ROLLBACK WORK.
      RETURN.
    ENDIF.

    COMMIT WORK.

  ENDMETHOD.
