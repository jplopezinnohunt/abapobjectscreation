  METHOD get_commuting_distance_list.

    DATA: ls_commuting_distance TYPE ty_commuting_distance,
          ls_dd07v              TYPE dd07v,
          lt_dd07v              TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'XFELD'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_commuting_distance.

      MOVE:
        ls_dd07v-domvalue_l TO ls_commuting_distance-id,
        ls_dd07v-ddtext TO ls_commuting_distance-txt.
      APPEND ls_commuting_distance TO ot_list.
    ENDLOOP.

  ENDMETHOD.
