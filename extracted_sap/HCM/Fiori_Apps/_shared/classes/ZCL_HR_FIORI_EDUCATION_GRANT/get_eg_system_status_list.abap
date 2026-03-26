  METHOD get_eg_system_status_list.

    DATA: ls_eg_system_status TYPE ty_eg_system_status,
          ls_dd07v            TYPE dd07v,
          lt_dd07v            TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'PUN_EGSST'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_eg_system_status.

      MOVE:
        ls_dd07v-domvalue_l TO ls_eg_system_status-id,
        ls_dd07v-ddtext TO ls_eg_system_status-txt.
      APPEND ls_eg_system_status TO ot_list.
    ENDLOOP.

  ENDMETHOD.
