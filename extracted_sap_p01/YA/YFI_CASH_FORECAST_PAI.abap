*&---------------------------------------------------------------------*
*&  Include           YFI_CASH_FORECAST_PAI
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*&      Module  USER_COMMAND_0100  INPUT
*&---------------------------------------------------------------------*
MODULE USER_COMMAND_0100 INPUT.

  DATA LV_OKCODE TYPE SY-UCOMM.
  LV_OKCODE = OK_CODE.
  CLEAR OK_CODE.

  CL_GUI_CFW=>DISPATCH( ).

  CASE LV_OKCODE.
    WHEN 'BACK'.
      IF GO_CASH_FORECAST->CHECK_DATA_CHANGED( ABAP_TRUE ) = ABAP_FALSE.
        GO_CASH_FORECAST->UNLOCK_PERIODS( ).
        LEAVE TO SCREEN 0.
      ENDIF.
    WHEN 'EXIT' OR 'CANC'.
      IF GO_CASH_FORECAST->CHECK_DATA_CHANGED( ABAP_TRUE ) = ABAP_FALSE.
        GO_CASH_FORECAST->UNLOCK_PERIODS( ).
        LEAVE PROGRAM.
      ENDIF.
    WHEN 'SAVE'.
      GO_CASH_FORECAST->SAVE_DATA( ).
  ENDCASE.

ENDMODULE.