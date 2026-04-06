METHOD get_value_help.

*  DATA: lt_result TYPE ztthr_vh_generic.
*
*  IF iv_lang_field IS INITIAL.
*
*
*    SELECT
*          (iv_key_field)
*    FROM (iv_tabname)
*    INTO TABLE @lt_result.
*  ELSE.
*
*    SELECT ( iv_key_field ) AS ID,
*           ( iv_text_field ) AS NAME
*      FROM (iv_tabname)
*      INTO TABLE @lt_result
*      WHERE ( iv_lang_field ) = @SY-langu
*      .
*
*  ENDIF.
*
*  rt_result = lt_result.
ENDMETHOD.
