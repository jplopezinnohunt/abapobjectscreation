  METHOD get_elec_incl_list.

    DATA: ls_elec_incl TYPE ty_elec_incl,
          ls_dd07v     TYPE dd07v,
          lt_dd07v     TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'XFELD'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      MOVE:
        ls_dd07v-domvalue_l TO ls_elec_incl-id,
        ls_dd07v-ddtext TO ls_elec_incl-txt.
      APPEND ls_elec_incl TO ot_list.
    ENDLOOP.

  ENDMETHOD.
