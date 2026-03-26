  METHOD get_yes_no_list.

    DATA: ls_yes_no TYPE ty_yes_no,
          ls_dd07v  TYPE dd07v,
          lt_dd07v  TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'XFELD'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_yes_no.

      MOVE:
        ls_dd07v-domvalue_l TO ls_yes_no-id,
        ls_dd07v-ddtext TO ls_yes_no-txt.
      APPEND ls_yes_no TO ot_list.
    ENDLOOP.

  ENDMETHOD.
