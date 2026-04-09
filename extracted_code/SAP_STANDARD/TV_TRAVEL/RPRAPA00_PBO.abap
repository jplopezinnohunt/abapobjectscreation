* 6.05
* MAWEB5K015766 02022009 RPRAPA00: Auswahl des Infotyps / Subtyps
*                        [note 1300833]

*&---------------------------------------------------------------------*
*&  Include           RPRAPA00_PBO
*&---------------------------------------------------------------------*

*----------------------------------------------------------------------*
*  MODULE value_list OUTPUT
*----------------------------------------------------------------------*
*
*----------------------------------------------------------------------*
MODULE value_list OUTPUT.

  DATA lt_591a TYPE TABLE OF t591a.
  DATA lt_591s TYPE TABLE OF t591s.

  FIELD-SYMBOLS <lt_591a> TYPE t591a.
  FIELD-SYMBOLS <lt_591s> TYPE t591s.

  SUPPRESS DIALOG.
  LEAVE TO LIST-PROCESSING AND RETURN TO SCREEN 0.
  SET PF-STATUS space.
  NEW-PAGE NO-TITLE.

  CASE gv_subtype.
    WHEN '0006'.
*     U06 Subtyp Infotyp 0006 (Anschriften)
      WRITE text-u06 COLOR COL_HEADING.
    WHEN '0009'.
*     U07 Subtyp Infotyp 0009 (Bankverbindung)
      WRITE text-u07 COLOR COL_HEADING.
  ENDCASE.

  ULINE.

  SELECT * FROM t591a INTO TABLE lt_591a WHERE infty = gv_subtype .
  SELECT * FROM t591s INTO TABLE lt_591s WHERE infty = gv_subtype . "#EC CI_GENBUFF

  LOOP AT lt_591a ASSIGNING <lt_591a>.
    READ TABLE lt_591s ASSIGNING <lt_591s> WITH KEY sprsl = sy-langu
                                                    infty = <lt_591a>-infty
                                                    subty = <lt_591a>-subty.
    IF sy-subrc = 0.
      gv_subty = <lt_591s>-subty.
      WRITE: / <lt_591s>-stext.
      HIDE gv_subty.
    ELSE.
      gv_subty = <lt_591a>-subty.
      WRITE: / <lt_591a>-subty.
      HIDE gv_subty.
    ENDIF.
  ENDLOOP.

  CLEAR gv_subty.

ENDMODULE.                    "value_list OUTPUT