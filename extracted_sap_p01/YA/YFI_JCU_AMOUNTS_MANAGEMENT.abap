*&---------------------------------------------------------------------*
*& Report YFI_JCU_AMOUNTS
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT YFI_JCU_AMOUNTS.

TABLES YSFI_CASH_BALANCE_DYNP.

DATA GO_JCU_MANAGEMENT_BL TYPE REF TO YCL_FI_JCU_MANAGEMENT_BL.
"Screen management
DATA OK_CODE TYPE SY-UCOMM.
DATA GO_CUSTOM_CONTAINER TYPE REF TO CL_GUI_CUSTOM_CONTAINER.
DATA GO_GRID TYPE REF TO CL_GUI_ALV_GRID.
DATA GV_LOCKED TYPE XFELD.
DATA GV_MESSAGE TYPE TEXT100.
DATA GV_STRING TYPE STRING.

SELECTION-SCREEN BEGIN OF BLOCK B01 WITH FRAME TITLE TEXT-B01.
PARAMETERS P_BUKRS TYPE BUKRS OBLIGATORY.
PARAMETERS P_GJAHR TYPE GJAHR OBLIGATORY.
SELECTION-SCREEN END OF BLOCK B01.

INITIALIZATION.
  GET PARAMETER ID 'BUK' FIELD P_BUKRS.
  P_GJAHR = SY-DATUM(4).

START-OF-SELECTION.

  "Instanciate business class
  GO_JCU_MANAGEMENT_BL = NEW YCL_FI_JCU_MANAGEMENT_BL( ).
  GO_JCU_MANAGEMENT_BL->GET_DATA( IV_BUKRS = P_BUKRS
                                  IV_GJAHR = P_GJAHR ).
  "Lock table
  GO_JCU_MANAGEMENT_BL->LOCK_JCU_TABLE( EXPORTING IV_BUKRS = P_BUKRS
                                                  IV_GJAHR = P_GJAHR
                                        IMPORTING EV_LOCKED = GV_LOCKED
                                                  EV_MESSAGE = GV_MESSAGE ).
  IF GV_LOCKED = ABAP_FALSE.
    GO_JCU_MANAGEMENT_BL->MV_DISPLAY_ONLY = ABAP_TRUE.
    GV_STRING = |{ GV_MESSAGE }. Do you want to display data ?|.
    IF YCL_CA_UTILITIES=>POPUP_TO_CONFIRM( IV_TITLE = 'Data can''t be locked'
                                           IV_TEXT = GV_STRING ) <> '1'.
      EXIT.
    ENDIF.
  ENDIF.

  CALL SCREEN 0100.



*&---------------------------------------------------------------------*
*&      Module  STATUS_0100  OUTPUT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
MODULE STATUS_0100 OUTPUT.

  DATA LT_FCODE TYPE TABLE OF SY-UCOMM.

  APPEND 'SAVE' TO LT_FCODE.

  IF GO_JCU_MANAGEMENT_BL->MV_DISPLAY_ONLY = ABAP_TRUE.
    SET PF-STATUS 'MAIN_0100' EXCLUDING LT_FCODE.
  ELSE.
    SET PF-STATUS 'MAIN_0100'.
  ENDIF.
  SET TITLEBAR 'MAIN_TITLE'.

ENDMODULE.
*&---------------------------------------------------------------------*
*&      Module  PBO_0100  OUTPUT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
MODULE PBO_0100 OUTPUT.

  IF GO_CUSTOM_CONTAINER IS NOT BOUND.
    "Init grid
    GO_CUSTOM_CONTAINER = NEW CL_GUI_CUSTOM_CONTAINER( CONTAINER_NAME = 'MAIN_CONTAINER' ).
    GO_GRID = NEW CL_GUI_ALV_GRID( I_PARENT = GO_CUSTOM_CONTAINER ). "cl_gui_container=>default_screen ).
    GO_JCU_MANAGEMENT_BL->MO_GRID = GO_GRID.
    GO_JCU_MANAGEMENT_BL->DISPLAY_ALV( ).
  ENDIF.

  YSFI_CASH_BALANCE_DYNP-BUKRS = P_BUKRS.
  YSFI_CASH_BALANCE_DYNP-GJAHR = P_GJAHR.

ENDMODULE.
*&---------------------------------------------------------------------*
*&      Module  USER_COMMAND_0100  INPUT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
MODULE USER_COMMAND_0100 INPUT.

  DATA LV_OKCODE TYPE SY-UCOMM.
  LV_OKCODE = OK_CODE.
  CLEAR OK_CODE.

  CL_GUI_CFW=>DISPATCH( ).

  CASE LV_OKCODE.
    WHEN 'BACK'.
      IF GO_JCU_MANAGEMENT_BL->CHECK_DATA_CHANGED( ABAP_TRUE ) = ABAP_FALSE.
        GO_JCU_MANAGEMENT_BL->UNLOCK_JCU_TABLE( EXPORTING IV_BUKRS = P_BUKRS
                                                          IV_GJAHR = P_GJAHR ).
        LEAVE TO SCREEN 0.
      ENDIF.
    WHEN 'EXIT' OR 'CANC'.
      IF GO_JCU_MANAGEMENT_BL->CHECK_DATA_CHANGED( ABAP_TRUE ) = ABAP_FALSE.
        GO_JCU_MANAGEMENT_BL->UNLOCK_JCU_TABLE( EXPORTING IV_BUKRS = P_BUKRS
                                                          IV_GJAHR = P_GJAHR ).
        LEAVE PROGRAM.
      ENDIF.
    WHEN 'SAVE'.
      GO_JCU_MANAGEMENT_BL->SAVE_DATA( ).
  ENDCASE.

ENDMODULE.