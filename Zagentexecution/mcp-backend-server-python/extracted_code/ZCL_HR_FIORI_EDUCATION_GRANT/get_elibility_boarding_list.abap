  METHOD get_elibility_boarding_list.

    DATA: ls_eligibility_boarding TYPE ty_eligibility_boarding,
          ls_dd07v                TYPE dd07v,
          lt_dd07v                TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'XFELD'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_eligibility_boarding.

      MOVE:
        ls_dd07v-domvalue_l TO ls_eligibility_boarding-id,
        ls_dd07v-ddtext TO ls_eligibility_boarding-txt.
      APPEND ls_eligibility_boarding TO ot_list.
    ENDLOOP.

  ENDMETHOD.
