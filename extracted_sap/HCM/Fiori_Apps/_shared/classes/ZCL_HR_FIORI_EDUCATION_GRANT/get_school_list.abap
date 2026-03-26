  METHOD get_school_list.

    DATA: ls_t7unpad_egsn TYPE t7unpad_egsn,
          ls_return       TYPE zshr_vh_generic,
          lt_t7unpad_egsn TYPE STANDARD TABLE OF t7unpad_egsn.

    SELECT * INTO TABLE lt_t7unpad_egsn
      FROM t7unpad_egsn
        WHERE molga = c_molga_un
          AND endda >= sy-datum
          AND begda <= sy-datum.

      SORT lt_t7unpad_egsn BY egsna ASCENDING.

    LOOP AT lt_t7unpad_egsn INTO ls_t7unpad_egsn.
      CLEAR: ls_return.

      MOVE:
        ls_t7unpad_egsn-egssl TO ls_return-id,
        ls_t7unpad_egsn-egsna TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
