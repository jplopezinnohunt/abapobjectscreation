  METHOD build_value.
    IF iv_value_c IS INITIAL.
      ev_value_c = iv_value_to_add.
    ELSE.
      ev_value_c = |{ iv_value_c }{ iv_value_to_add }|.
    ENDIF.
  ENDMETHOD.