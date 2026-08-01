*&---------------------------------------------------------------------*
*& Report  YAM_AS02_COVER                                              *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*

REPORT  YAM_AS02_COVER.


TABLES: ANLA.


PARAMETERS:
  P_ANLN1 LIKE ANLA-ANLN1 NO-DISPLAY,
  P_INVNR LIKE ANLA-INVNR OBLIGATORY MATCHCODE OBJECT YAM_INVNR,
  P_BUKRS LIKE ANLA-BUKRS OBLIGATORY MEMORY ID BUK.


DATA: W_ANLN1 LIKE ANLA-ANLN1,
      W_INVNR LIKE ANLA-INVNR,
      W_INVLEN TYPE I,
      W_TCODE LIKE SY-TCODE.


START-OF-SELECTION.

***check for partial inv. number
W_INVLEN = STRLEN( P_INVNR ).
IF W_INVLEN < 10 AND P_INVNR NS '*'.
  CONCATENATE '*' P_INVNR INTO P_INVNR.
ENDIF.
***

IF P_INVNR CS '*'.
  CLEAR W_INVNR.
  W_INVNR = P_INVNR.
  REPLACE '*' IN W_INVNR WITH '%'.
  SELECT *
        FROM ANLA
        WHERE BUKRS = P_BUKRS
          AND INVNR LIKE W_INVNR.
  ENDSELECT. "anla
  IF SY-DBCNT = 1.
    P_INVNR = ANLA-INVNR.
   ELSE.
     MESSAGE 'More than one appropriate Inventory numbers' TYPE 'I'.
  ENDIF. "sy-dbcnt
ENDIF. "p_invnr

CLEAR W_ANLN1.
SELECT ANLN1
      INTO W_ANLN1
      FROM ANLA
      WHERE BUKRS = P_BUKRS
        AND INVNR = P_INVNR.
ENDSELECT. "anla

IF SY-SUBRC IS INITIAL.
  CLEAR W_TCODE.
  CASE SY-TCODE.
    WHEN 'YAS02'.
      W_TCODE = 'AS02'.
    WHEN 'YAS03'.
      W_TCODE = 'AS03'.
    WHEN OTHERS.
      W_TCODE = 'AS03'. "for debugging
  ENDCASE. "sy-tcode

  SET PARAMETER ID 'AN1' FIELD W_ANLN1.
  SET PARAMETER ID 'BUK' FIELD P_BUKRS.

  CALL TRANSACTION W_TCODE AND SKIP FIRST SCREEN.
 ELSE.
   MESSAGE 'Inventory Number not found or it is not unique!' TYPE 'I'.
ENDIF. "sy-subrc

END-OF-SELECTION.