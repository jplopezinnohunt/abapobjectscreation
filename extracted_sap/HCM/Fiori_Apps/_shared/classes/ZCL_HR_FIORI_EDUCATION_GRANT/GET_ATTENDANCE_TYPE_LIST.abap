  METHOD GET_ATTENDANCE_TYPE_LIST.

    DATA: ls_cost_type TYPE zshr_vh_generic,
          ls_dd07v     TYPE dd07v,
          lt_dd07v     TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'ZDHR_EG_TYPE_ATT'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_cost_type.

      MOVE:
        ls_dd07v-domvalue_l TO ls_cost_type-id,
        ls_dd07v-ddtext TO ls_cost_type-txt.
      APPEND ls_cost_type TO ot_list.
    ENDLOOP.

  ENDMETHOD.
