  METHOD get_multiple_attendance_list.

    DATA: ls_multiple_attendance TYPE zshr_vh_generic,
          ls_dd07v               TYPE dd07v,
          lt_dd07v               TYPE STANDARD TABLE OF dd07v.

    CALL FUNCTION 'DD_DOMVALUES_GET'
      EXPORTING
        domname   = 'EGMUL'
        text      = 'X'
        langu     = sy-langu
      TABLES
        dd07v_tab = lt_dd07v.

    LOOP AT lt_dd07v INTO ls_dd07v.
      CLEAR: ls_multiple_attendance.

      MOVE:
        ls_dd07v-domvalue_l TO ls_multiple_attendance-id,
        ls_dd07v-ddtext TO ls_multiple_attendance-txt.
      APPEND ls_multiple_attendance TO ot_list.
    ENDLOOP.

  ENDMETHOD.
