  METHOD get_school_type_list.

    DATA: ls_school_type TYPE zshr_vh_generic,
          ls_dd07v       TYPE dd07v,
          lt_dd07v       TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'PUN_EGSTY'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_school_type.

      MOVE:
        ls_dd07v-domvalue_l TO ls_school_type-id,
        ls_dd07v-ddtext TO ls_school_type-txt.
      APPEND ls_school_type TO ot_list.
    ENDLOOP.

  ENDMETHOD.
