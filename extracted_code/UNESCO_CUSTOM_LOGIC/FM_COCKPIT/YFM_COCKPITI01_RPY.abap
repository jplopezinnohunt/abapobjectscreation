*&---------------------------------------------------------------------*
*&  Include           YFM_COCKPITI01
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*&      Module  USER_COMMAND_1000  INPUT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
MODULE USER_COMMAND_1000 INPUT.

  DATA : LV_FMAREA(4).
  CASE FCODE.
    WHEN 'BACK' OR 'EXIT'.
      LEAVE TO SCREEN 0.

    WHEN 'HELP'.
      PERFORM OPEN_DOC.
    WHEN C_TRANS_1 OR C_TRANS_2 OR C_TRANS_3.

      IF FCODE = C_TRANS_1.

        PERFORM CHECK_ROLE_FOR_FILTER CHANGING LV_FMAREA.

        IF LV_FMAREA = 'ALL'.
          CALL TRANSACTION FCODE.

        ELSEIF LV_FMAREA IS NOT INITIAL.
          PERFORM BATCH_FILTER.
          CALL TRANSACTION FCODE USING BDC_TAB MODE 'E'.

        ELSE.
          MESSAGE E202(FMSHERLOCK).
*   No authorization for this action

        ENDIF.

      ELSE.
        CALL TRANSACTION FCODE.
      ENDIF.
      IF FCODE = C_TRANS_1.
        W_STEP_1_DONE = ABAP_TRUE.

        PERFORM PROMPT_NEXT_STEP USING '2'.

      ELSEIF FCODE = C_TRANS_2.
        W_STEP_2_DONE = ABAP_TRUE.

        PERFORM PROMPT_NEXT_STEP USING '3'.

      ENDIF.
      CLEAR FCODE.

  ENDCASE.
ENDMODULE.
*&---------------------------------------------------------------------*
*&      Module  EXIT  INPUT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
MODULE EXIT INPUT.
  CASE FCODE.
    WHEN 'CANC'.
      LEAVE TO SCREEN 0.

  ENDCASE.
ENDMODULE.