  METHOD get_dwel_rent_type_list.

    DATA: ls_t7unpad_rsdr_t  TYPE t7unpad_rsdr_t,
          ls_dwell_rent_type TYPE zshr_vh_generic,
          lt_t7unpad_rsdr_t  TYPE STANDARD TABLE OF t7unpad_rsdr_t.

    SELECT * INTO TABLE lt_t7unpad_rsdr_t
      FROM t7unpad_rsdr_t
        WHERE sprsl = sy-langu
          AND molga = c_molga_un.

    LOOP AT lt_t7unpad_rsdr_t INTO ls_t7unpad_rsdr_t.
      ls_dwell_rent_type-id = ls_t7unpad_rsdr_t-rsdrt.
      ls_dwell_rent_type-txt = ls_t7unpad_rsdr_t-rsdrx.
      APPEND ls_dwell_rent_type TO ot_list.
    ENDLOOP.


  ENDMETHOD.
