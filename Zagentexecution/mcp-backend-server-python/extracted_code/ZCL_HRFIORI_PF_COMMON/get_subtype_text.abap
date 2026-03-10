  METHOD get_subtype_text.

    SELECT SINGLE stext INTO ov_subtype_text
      FROM t591s
        WHERE sprsl = sy-langu
          AND infty = iv_infotype
          AND subty = iv_subtype.

  ENDMETHOD.
