  METHOD get_special_arrangement_list.

    DATA: ls_special_arrangement TYPE zshr_vh_generic,
          ls_dd07v               TYPE dd07v,
          lt_dd07v               TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'PUN_EGSAR'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_special_arrangement.

      MOVE:
        ls_dd07v-domvalue_l TO ls_special_arrangement-id,
        ls_dd07v-ddtext TO ls_special_arrangement-txt.
      APPEND ls_special_arrangement TO ot_list.
    ENDLOOP.

  ENDMETHOD.
