*&---------------------------------------------------------------------*
*&  Include           YFI_CASH_FORECAST_PBO
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*&      Module  STATUS_0100  OUTPUT
*&---------------------------------------------------------------------*
MODULE STATUS_0100 OUTPUT.

  SET PF-STATUS 'MAIN_0100'.
  SET TITLEBAR 'MAIN_TITLE'.

ENDMODULE.
*&---------------------------------------------------------------------*
*&      Module  PBO_0100  OUTPUT
*&---------------------------------------------------------------------*
MODULE PBO_0100 OUTPUT.

  IF GO_CUSTOM_CONTAINER IS NOT BOUND.
    "Init grid
    GO_CUSTOM_CONTAINER = NEW CL_GUI_CUSTOM_CONTAINER( CONTAINER_NAME = 'MAIN_CONTAINER' ).
    GO_GRID = NEW CL_GUI_ALV_GRID( I_PARENT = GO_CUSTOM_CONTAINER ). "cl_gui_container=>default_screen ).
    GO_CASH_FORECAST->MO_GRID = GO_GRID.
    GO_CASH_FORECAST->DISPLAY_ALV( ).
  ENDIF.

  "Set companu code
  YSFI_CASH_FORECAST_DYNP-BUKRS = P_BUKRS.

ENDMODULE.