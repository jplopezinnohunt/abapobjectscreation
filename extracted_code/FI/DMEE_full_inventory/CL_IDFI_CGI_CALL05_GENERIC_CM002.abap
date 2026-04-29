  METHOD compare_by_chars.
* Compare Character-Like values Character by Character, if any
* character in Generic Character-Like value is replaced by
* Country-Specific character, raise an error

    DATA:
      lv_len_generic     TYPE i,
      lv_len_cntry_spec  TYPE i,
      lv_pos             TYPE i,
      lv_char_generic    TYPE c,
      lv_char_cntry_spec TYPE c.

*   Check if the structures are equal, if yes, do nothing
    CHECK iv_generic NE iv_cntry_spec.

*   Compare length
    DESCRIBE FIELD:
      iv_generic    LENGTH lv_len_generic    IN CHARACTER MODE,
      iv_cntry_spec LENGTH lv_len_cntry_spec IN CHARACTER MODE.

    IF lv_len_generic NE lv_len_cntry_spec.
*     Length of Generic structure and Country-Specific structure is not
*     the same
      RAISE change_found.
    ENDIF.

    DO lv_len_generic TIMES.
      CLEAR: lv_char_generic, lv_char_cntry_spec.

*     Get characters on position
      lv_pos = sy-index - 1.   "position has to be allways less then sy-index
      lv_char_generic    = iv_generic+lv_pos(1).
      lv_char_cntry_spec = iv_cntry_spec+lv_pos(1).

      IF lv_char_generic IS NOT INITIAL AND
         lv_char_generic NE lv_char_cntry_spec.
*       Generic character is not empty and is changed by Country-Specific
*       character
        RAISE change_found.
      ENDIF.
    ENDDO. "DO lv_len_generic TIMES.

  ENDMETHOD.