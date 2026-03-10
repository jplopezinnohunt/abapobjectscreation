  METHOD get_dependency_status_list.

    DATA: ls_return     TYPE zshr_vh_generic,
          ls_dep_status TYPE t577s,
          lt_dep_status TYPE STANDARD TABLE OF t577s.

    SELECT * INTO TABLE lt_dep_status
      FROM t577s
        WHERE sprsl = sy-langu
          AND molga = c_molga_un
          AND eigsh = c_family_characteristic_child.

    LOOP AT lt_dep_status INTO ls_dep_status.
      CLEAR: ls_return.

      MOVE:
        ls_dep_status-auspr TO ls_return-id,
        ls_dep_status-atext TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
