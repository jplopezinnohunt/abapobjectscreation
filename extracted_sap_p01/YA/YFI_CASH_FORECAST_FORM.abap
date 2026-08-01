*&---------------------------------------------------------------------*
*&  Include           YFI_CASH_FORECAST_FORM
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*&      Form  F_SEL_9000_EMPTY
*&---------------------------------------------------------------------*
FORM F_SEL_9000_EMPTY  USING FV_EMPTY.

  IF S_GSBER1[] IS INITIAL AND S_SAKNR1[] IS INITIAL.
    FV_EMPTY = ABAP_TRUE.

  ELSE.
    FV_EMPTY = ABAP_FALSE.
  ENDIF.

ENDFORM.