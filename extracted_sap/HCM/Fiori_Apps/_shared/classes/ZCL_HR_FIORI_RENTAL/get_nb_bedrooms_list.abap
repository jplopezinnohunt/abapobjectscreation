  METHOD get_nb_bedrooms_list.

    DATA: ls_nb_bedrooms TYPE ty_nb_bedrooms,
          ls_dd07v     TYPE dd07v,
          lt_dd07v     TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'PUN_RSNBR'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      MOVE:
        ls_dd07v-domvalue_l TO ls_nb_bedrooms-id,
        ls_dd07v-ddtext TO ls_nb_bedrooms-txt.
      APPEND ls_nb_bedrooms TO ot_list.
    ENDLOOP.

  ENDMETHOD.
