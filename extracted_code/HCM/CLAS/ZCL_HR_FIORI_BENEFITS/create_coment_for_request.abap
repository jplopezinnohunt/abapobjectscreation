  METHOD create_coment_for_request.

    DATA: ls_coment TYPE zthrfiori_coment,
          ls_req    TYPE zthrfiori_breq.

*   Get benefits request
    SELECT SINGLE * INTO ls_req
      FROM zthrfiori_breq
        WHERE guid = iv_guid.

*   Update table of coments
    ls_coment-guid = iv_guid.
    ls_coment-creation_date = iv_date.
    ls_coment-creation_time = iv_time.
    ls_coment-usr_id = iv_usrid.
    ls_coment-pernr = iv_pernr.
    ls_coment-actor = iv_actor.
    ls_coment-coment = iv_coment.


    INSERT INTO zthrfiori_coment VALUES ls_coment.
    IF sy-subrc <> 0.
      ov_return_code = 4.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '004'
        INTO ov_message
          WITH ls_req-request_key.

      ROLLBACK WORK.
      RETURN.
    ENDIF.

    COMMIT WORK.


  ENDMETHOD.
