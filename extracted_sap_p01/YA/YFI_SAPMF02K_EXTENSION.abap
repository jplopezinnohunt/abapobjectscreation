*&---------------------------------------------------------------------*
*&  Include           YFI_SAPMF02K_EXTENSION
*&---------------------------------------------------------------------*
MODULE YYCHECK_BANK_DATA INPUT.

  DATA YYLV_COUNT TYPE I.

  CLEAR YYLV_COUNT.

  LOOP AT XLFBK INTO DATA(LS_XFLBK) WHERE YYTRAVEL = ABAP_TRUE.
    ADD 1 TO YYLV_COUNT.
  ENDLOOP.
  IF YYLV_COUNT > 1.
    MESSAGE E019(YFI1).
    "Flag 'Travel bank' can be set only for one bank
  ENDIF.

ENDMODULE.