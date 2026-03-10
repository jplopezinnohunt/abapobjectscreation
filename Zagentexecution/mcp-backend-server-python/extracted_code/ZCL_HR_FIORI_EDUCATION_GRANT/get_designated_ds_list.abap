  METHOD get_designated_ds_list.

    DATA: ls_designated_ds TYPE ty_designated_ds,
          ls_dd07v         TYPE dd07v,
          lt_dd07v         TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'XFELD'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_designated_ds.

      MOVE:
        ls_dd07v-domvalue_l TO ls_designated_ds-id,
        ls_dd07v-ddtext TO ls_designated_ds-txt.
      APPEND ls_designated_ds TO ot_list.
    ENDLOOP.

  ENDMETHOD.
