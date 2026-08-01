*&---------------------------------------------------------------------*
*& Report  YAM_SAVE_LIST_WITH_NAMES                                    *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*

REPORT  YAM_SAVE_LIST_WITH_NAMES.


TABLES: ANLA,
        ANLZ,
        PA0002,
        T499S.


PARAMETERS: P_BUKRS LIKE ANLA-BUKRS OBLIGATORY MEMORY ID BUK.

SELECT-OPTIONS: P_ANLKL FOR ANLA-ANLKL,
                P_ANLN1 FOR ANLA-ANLN1,
                P_WERKS FOR T499S-WERKS OBLIGATORY DEFAULT '0002'
                                        NO INTERVALS,
                P_STORT FOR T499S-STAND.

PARAMETERS:     P_BDATU LIKE ANLZ-BDATU OBLIGATORY DEFAULT SY-DATUM,
                P_FNAME(100) DEFAULT 'C:\AM\WOA\WEB\'.


DATA: BEGIN OF T_LIST OCCURS 0,
        BUKRS LIKE ANLA-BUKRS,
        ANLKL LIKE ANLA-ANLKL,
        ANLN1 LIKE ANLA-ANLN1,
        TXT50 LIKE ANLA-TXT50,
        TXA50 LIKE ANLA-TXA50,
        AKTIV LIKE ANLA-AKTIV,
        LAND1 LIKE ANLA-LAND1,
        HERST LIKE ANLA-HERST,
        INVNR LIKE ANLA-INVNR,
        SERNR LIKE ANLA-SERNR,
        STORT LIKE ANLZ-STORT,
        KTEXT LIKE T499S-KTEXT,
        PERNR LIKE ANLZ-PERNR,
        VORNA LIKE PA0002-VORNA,
        NACHN LIKE PA0002-NACHN,
      END OF T_LIST.


DATA: W_FSTR(300),
      W_LCOUNT TYPE I.


START-OF-SELECTION.

REFRESH T_LIST.

CLEAR ANLA.
SELECT *
      FROM ANLA
      WHERE BUKRS = P_BUKRS
        AND ANLN1 IN P_ANLN1
        AND ANLKL IN P_ANLKL.

  CLEAR T_LIST.

  CHECK ANLA-XLOEV IS INITIAL.
  CHECK ANLA-XSPEB IS INITIAL.
  CHECK ANLA-DEAKT IS INITIAL.

  CLEAR ANLZ.
  SELECT *
        FROM ANLZ
        WHERE BUKRS = ANLA-BUKRS
          AND ANLN1 = ANLA-ANLN1
          AND ANLN2 = ANLA-ANLN2.

    CHECK P_BDATU BETWEEN ANLZ-ADATU AND ANLZ-BDATU.
    CHECK ANLZ-WERKS IN P_WERKS.
    CHECK ANLZ-STORT IN P_STORT.

    MOVE-CORRESPONDING ANLZ TO T_LIST.

    CLEAR T499S.
    SELECT SINGLE *
          FROM T499S
          WHERE WERKS = ANLZ-WERKS
            AND STAND = ANLZ-STORT.

    T_LIST-KTEXT = T499S-KTEXT.

    CLEAR PA0002.
    SELECT *
          FROM PA0002
          WHERE PERNR = ANLZ-PERNR.
      CHECK P_BDATU BETWEEN PA0002-BEGDA AND PA0002-ENDDA.
      T_LIST-VORNA = PA0002-VORNA.
      T_LIST-NACHN = PA0002-NACHN.
    ENDSELECT. "pa0002
  ENDSELECT. "anlz

  MOVE-CORRESPONDING ANLA TO T_LIST.
  APPEND T_LIST.
ENDSELECT. "anla

END-OF-SELECTION.



SORT T_LIST.
LOOP AT T_LIST.
*  write: / t_list.
  CONCATENATE T_LIST-ANLN1
              T_LIST-BUKRS
              T_LIST-ANLKL
              T_LIST-TXT50
              T_LIST-TXA50
              T_LIST-AKTIV
              T_LIST-LAND1
              T_LIST-HERST
              T_LIST-INVNR
              T_LIST-SERNR
              T_LIST-VORNA
              T_LIST-NACHN
             INTO W_FSTR SEPARATED BY ';'.
  WRITE: / W_FSTR.

  SUBMIT Y_AM_GET_LONG_TEXT
        WITH P_BUKRS = T_LIST-BUKRS
        WITH P_ANLN1 = T_LIST-ANLN1
        WITH P_FNAME = P_FNAME
        AND RETURN.
ENDLOOP. "t_list

DESCRIBE TABLE T_LIST LINES W_LCOUNT.
SKIP.
ULINE.
SKIP.
WRITE: / 'Total lines:', W_LCOUNT.