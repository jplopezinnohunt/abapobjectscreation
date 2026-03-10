*&---------------------------------------------------------------------*
*&  Include           YFM_COCKPITO01
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*&      Module  STATUS_1000  OUTPUT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
MODULE STATUS_1000 OUTPUT.
  CLEAR WT_EXCLUDE.
  IF W_STEP_1_DONE = ABAP_FALSE.
    APPEND 'STEP_2' TO WT_EXCLUDE.
  ENDIF.
  IF W_STEP_2_DONE = ABAP_FALSE.
        APPEND 'STEP_3' TO WT_EXCLUDE.

  ENDIF.
  SET PF-STATUS 'MAIN' EXCLUDING WT_EXCLUDE.
  SET TITLEBAR '001'.



ENDMODULE.
*&---------------------------------------------------------------------*
*&      Module  OUTPUT_100  OUTPUT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
MODULE OUTPUT_100 OUTPUT.


  LOOP AT SCREEN.
    IF SCREEN-NAME = 'BUT_2' .
      IF W_STEP_1_DONE = ABAP_FALSE.
        SCREEN-INPUT = 0.
      ELSE.
        SCREEN-INPUT = 1.
        SCREEN-ACTIVE = 1.
      ENDIF.
      MODIFY SCREEN.
    ENDIF.
    IF SCREEN-NAME = 'BUT_3' .
      IF W_STEP_2_DONE = ABAP_FALSE.
        SCREEN-INPUT = 0.
      ELSE.
        SCREEN-INPUT = 1.
        SCREEN-ACTIVE = 1.
      ENDIF.
      MODIFY SCREEN.
    ENDIF.
  ENDLOOP.

ENDMODULE.