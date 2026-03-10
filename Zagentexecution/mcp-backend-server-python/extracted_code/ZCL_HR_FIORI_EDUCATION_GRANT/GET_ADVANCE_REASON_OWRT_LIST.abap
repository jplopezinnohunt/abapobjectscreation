  METHOD GET_ADVANCE_REASON_OWRT_LIST.

    DATA: ls_t7unpad_egadcr_t TYPE t7unpad_egadcr_t,
          ls_return           TYPE ty_adv_reason_overwrite,
          lt_t7unpad_egadcr_t TYPE STANDARD TABLE OF t7unpad_egadcr_t.

    SELECT * INTO TABLE lt_t7unpad_egadcr_t
      FROM t7unpad_egadcr_t
        WHERE sprsl = sy-langu
          AND molga = c_molga_un.

    LOOP AT lt_t7unpad_egadcr_t INTO ls_t7unpad_egadcr_t.
      CLEAR: ls_return.

      MOVE:
        ls_t7unpad_egadcr_t-egadv_chgrsn TO ls_return-id,
        ls_t7unpad_egadcr_t-egadv_chgrsnt TO ls_return-txt.
      APPEND ls_return TO ot_list.
    ENDLOOP.

  ENDMETHOD.
