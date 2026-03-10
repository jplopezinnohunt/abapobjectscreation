METHOD get_request_coments.
"$$
"$$
"$$
"$$
"$$

    DATA: lv_pernr      TYPE persno,
          lv_first_name TYPE pad_vorna,
          lv_last_name  TYPE pad_nachn,
          ls_actors     TYPE zthrfiori_actor,
          lt_coments    TYPE STANDARD TABLE OF zthrfiori_coment,
          lt_actors     TYPE STANDARD TABLE OF zthrfiori_actor.

    FIELD-SYMBOLS <fs_coment> TYPE zthrfiori_coment.
"$$

*   Get coments for selected request
    SELECT * INTO TABLE lt_coments
      FROM zthrfiori_coment
        WHERE guid = iv_guid.
*   Get actor types
    SELECT * INTO TABLE lt_actors
      FROM zthrfiori_actor
        WHERE language = sy-langu.
    SORT lt_actors BY id ASCENDING.

*   Complete data if necessary
    SORT lt_coments BY pernr ASCENDING.
    LOOP AT lt_coments ASSIGNING <fs_coment>.
      AT FIRST.
        lv_pernr = <fs_coment>-pernr.
      ENDAT.
"$$
"$$
"$$
"$$

      IF <fs_coment>-first_name IS NOT INITIAL OR
        <fs_coment>-last_name IS NOT INITIAL.

        IF lv_first_name IS INITIAL OR lv_pernr <> <fs_coment>-pernr.
          CLEAR: lv_first_name, lv_last_name.
          lv_pernr = <fs_coment>-pernr.

          get_actor_infos( EXPORTING iv_pernr = <fs_coment>-pernr
                           IMPORTING ov_first_name = <fs_coment>-first_name
                                     ov_last_name = <fs_coment>-last_name ).

        ENDIF.
        <fs_coment>-first_name = lv_first_name.
        <fs_coment>-last_name = lv_last_name.
      ENDIF.
      IF <fs_coment>-actor_name IS NOT INITIAL.
        READ TABLE lt_actors INTO ls_actors WITH KEY id = <fs_coment>-actor.
        <fs_coment>-actor_name = ls_actors-name.
      ENDIF.

    ENDLOOP.
"$$
"$$

*   Return results
    ot_coments = lt_coments.
"$$
"$$

  ENDMETHOD.
