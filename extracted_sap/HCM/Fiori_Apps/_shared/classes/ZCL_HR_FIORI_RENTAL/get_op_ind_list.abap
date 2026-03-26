  METHOD get_op_ind_list.

    DATA: ls_op_ind TYPE ty_op_ind,
          ls_dd07v  TYPE dd07v,
          lt_dd07v  TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'OPKEN'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      MOVE:
        ls_dd07v-domvalue_l TO ls_op_ind-id,
        ls_dd07v-ddtext TO ls_op_ind-txt.
      APPEND ls_op_ind TO ot_list.
    ENDLOOP.

  ENDMETHOD.
