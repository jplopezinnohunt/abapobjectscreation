  METHOD get_special_eg_flag_list.

    DATA: ls_eg_flag TYPE ty_eg_flag,
          ls_dd07v   TYPE dd07v,
          lt_dd07v   TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'ANST_YESNO'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_eg_flag.

      MOVE:
        ls_dd07v-domvalue_l TO ls_eg_flag-id,
        ls_dd07v-ddtext TO ls_eg_flag-txt.
      APPEND ls_eg_flag TO ot_list.
    ENDLOOP.

  ENDMETHOD.
