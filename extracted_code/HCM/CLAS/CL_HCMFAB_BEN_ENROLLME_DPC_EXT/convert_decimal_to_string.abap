METHOD convert_decimal_to_string.

  DATA: decimal_amt_conv(30) TYPE c.
  DATA : iv_input_amt1 TYPE bapicurr-bapicurr.

* Covert the decimal format  to user configured format in SU01.

  IF iv_curr IS NOT INITIAL.
    CALL FUNCTION 'BAPI_CURRENCY_CONV_TO_EXTERNAL'
      EXPORTING
        currency        = iv_curr
        amount_internal = iv_input_amt
      IMPORTING
        amount_external = iv_input_amt1.
  ENDIF.
  MOVE iv_input_amt1 TO decimal_amt_conv.
  MOVE decimal_amt_conv TO ev_output_amt.
  CONDENSE ev_output_amt NO-GAPS.

ENDMETHOD.
