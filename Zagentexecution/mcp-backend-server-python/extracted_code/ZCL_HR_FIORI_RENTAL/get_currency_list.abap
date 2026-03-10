  METHOD get_currency_list.

    DATA: lr_waers    TYPE RANGE OF waers,
          ls_waers    LIKE LINE OF lr_waers,
          ls_tcurt    TYPE tcurt,
          ls_currency TYPE ZSHR_VH_GENERIC,
          ls_tcurc    TYPE tcurc,
          lt_tcurc    TYPE STANDARD TABLE OF tcurc,
          lt_tcurt    TYPE STANDARD TABLE OF tcurt.

    SELECT * INTO TABLE lt_tcurc
       FROM tcurc
        WHERE gdatu = '00000000'.

    ls_waers-sign = 'I'.
    ls_waers-option = 'EQ'.
    LOOP AT lt_tcurc INTO ls_tcurc.
      ls_waers-low = ls_tcurc-waers.
      APPEND ls_waers TO lr_waers.
    ENDLOOP.

    SELECT * INTO TABLE lt_tcurt
      FROM tcurt
        WHERE spras = sy-langu
          AND waers IN lr_waers.

    LOOP AT lt_tcurt INTO ls_tcurt.
      ls_currency-id = ls_tcurt-waers.
      ls_currency-txt = ls_tcurt-ltext.
      APPEND ls_currency TO ot_list.
    ENDLOOP.


  ENDMETHOD.
