  METHOD get_apply_23_rule_list.

    DATA: ls_apply_23_rule TYPE ty_apply_23_rule,
          ls_dd07v         TYPE dd07v,
          lt_dd07v         TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'EGRUL'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_apply_23_rule.

      MOVE:
        ls_dd07v-domvalue_l TO ls_apply_23_rule-id,
        ls_dd07v-ddtext TO ls_apply_23_rule-txt.
      APPEND ls_apply_23_rule TO ot_list.
    ENDLOOP.

  ENDMETHOD.
