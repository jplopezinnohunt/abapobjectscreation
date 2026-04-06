  METHOD get_timeline.

    DATA : ls_actors TYPE zthrfiori_actor,
           lt_actors TYPE STANDARD TABLE OF zthrfiori_actor.
    FIELD-SYMBOLS <fs_line> TYPE zcl_zhr_benefits_reque_mpc=>ts_requesthistoryandcoments.

    SELECT * INTO TABLE lt_actors
      FROM zthrfiori_actor
        WHERE language = sy-langu ORDER BY id ASCENDING.

    SELECT h~guid h~inc_nb h~actor h~update_date h~update_time h~pernr
      h~last_name h~first_name c~coment
      INTO CORRESPONDING FIELDS OF TABLE et_result
        FROM zthrfiori_breq_h AS h LEFT JOIN zthrfiori_coment AS c
          ON h~guid = c~guid
          AND h~update_date = c~creation_date
          AND h~update_time = c~creation_time
            WHERE h~guid   EQ iv_request_guid.

    LOOP AT et_result ASSIGNING <fs_line>.
      IF <fs_line>-actor IS NOT INITIAL.
        READ TABLE lt_actors INTO ls_actors WITH KEY id = <fs_line>-actor.
        <fs_line>-actor_txt = ls_actors-name.
        CASE <fs_line>-actor.
          WHEN '01'. <fs_line>-icon = 'sap-icon://activity-individual'.
*           WHEN hra
          WHEN OTHERS. <fs_line>-icon = 'sap-icon://order-status'.
        ENDCASE.
      ENDIF.
    ENDLOOP.

  ENDMETHOD.
