*&---------------------------------------------------------------------*
*& Include          ZRHR_PRINT_LOG_ALV_MODULE
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*& Module STATUS_9001 OUTPUT
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
MODULE STATUS_9001 OUTPUT.
  SET PF-STATUS 'S9001'.
  SET TITLEBAR 'T9001' WITH P_titre.
  PERFORM alim_fieldcat_9001.
  PERFORM transfer_data_9001.
ENDMODULE.
*&---------------------------------------------------------------------*
*&      Module  USER_COMMAND_9001  INPUT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
MODULE USER_COMMAND_9001 INPUT.
  MOVE ok_code TO ok_code_9001.
  CLEAR ok_code.
  CASE ok_code_9001.
*  WHEN 'BACK' OR 'EXIT' OR 'CANCEL'.
*    zaffichage = 'ZH'.
*    lt_report_aff[] = lt_report_out.
*    DELETE lt_report_aff WHERE zout NE 'DIF'.
*    LEAVE TO SCREEN 0.
    WHEN 'BACK'. LEAVE TO SCREEN 0.
    WHEN 'CANC' OR 'EXIT'. LEAVE PROGRAM.
    WHEN OTHERS.
  ENDCASE.
ENDMODULE.