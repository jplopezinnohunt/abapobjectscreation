*&---------------------------------------------------------------------*
*& Report  YAM_INV_CHECK                                               *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*

REPORT  YAM_INV_CHECK LINE-SIZE 120 LINE-COUNT 90.

TABLES: ANLA,
        ANLZ.



PARAMETERS: P_FILE(200) OBLIGATORY.

SELECTION-SCREEN SKIP.

PARAMETERS: P_BUKRS LIKE T001-BUKRS OBLIGATORY MEMORY ID BUK,
            P_IDATE TYPE D DEFAULT SY-DATUM.



DATA: BEGIN OF T_ITAB OCCURS 0.
        INCLUDE STRUCTURE YAM_INVRES_STR.
DATA: END OF T_ITAB.


DATA: BEGIN OF T_RTAB OCCURS 0,
        NWERKS LIKE ANLZ-WERKS,
        NLOCAT LIKE ANLZ-STORT,
        NLBCOD LIKE YAM_INVRES_STR-LBCOD,
        OWERKS LIKE ANLZ-WERKS,
        OLOCAT LIKE ANLZ-STORT,
        ABCOD  LIKE YAM_INVRES_STR-ABCOD,
        BUKRS  LIKE ANLA-BUKRS,
        ANLN1  LIKE ANLA-ANLN1,
        ANLN2  LIKE ANLA-ANLN2,
        TXT50  LIKE ANLA-TXT50,
        STATUS,
*status: space if OK
*        M if new location is different
*        N if asset not found in database
      END OF T_RTAB.


DATA: W_FILENAME TYPE STRING,
      W_SORTCRIT(7),
      W_LNUMBER  LIKE SY-TABIX.



START-OF-SELECTION.

SET PF-STATUS 'INVC'.

W_FILENAME = P_FILE.

CALL FUNCTION 'Y_AM_INV_TXT_IMPORT'
  EXPORTING
    FNAME              = W_FILENAME
  TABLES
    ADATA_TAB          = T_ITAB
  EXCEPTIONS
    FILE_PROBLEM       = 1
    OTHERS             = 2.

IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
ENDIF.

CLEAR T_ITAB.
SORT T_ITAB BY WERKS LOCAT LBCOD ABCOD.
LOOP AT T_ITAB.
**check the location in database
  CLEAR ANLA.
  SELECT SINGLE *
        FROM ANLA
        WHERE BUKRS = P_BUKRS
          AND INVNR = T_ITAB-ABCOD.
  CLEAR ANLZ.
  SELECT SINGLE *
        FROM ANLZ
        WHERE BUKRS = ANLA-BUKRS
          AND ANLN1 = ANLA-ANLN1
          AND ANLN2 = ANLA-ANLN2
          AND BDATU >= P_IDATE
          AND ADATU <= P_IDATE.

  CLEAR T_RTAB.
  T_RTAB-NWERKS = T_ITAB-WERKS.
  T_RTAB-NLOCAT = T_ITAB-LOCAT.
  T_RTAB-NLBCOD = T_ITAB-LBCOD.
  T_RTAB-OWERKS = ANLZ-WERKS.
  T_RTAB-OLOCAT = ANLZ-STORT.
  T_RTAB-ABCOD  = T_ITAB-ABCOD.
  T_RTAB-BUKRS  = ANLA-BUKRS.
  T_RTAB-ANLN1  = ANLA-ANLN1.
  T_RTAB-ANLN2  = ANLA-ANLN2.
  T_RTAB-TXT50  = ANLA-TXT50.
  IF ANLA-ANLN1 IS INITIAL. "asset with this bar-code not found
    T_RTAB-STATUS = 'N'.
   ELSEIF ( ANLZ-WERKS <> T_ITAB-WERKS ) OR "asset moved
          ( ANLZ-STORT <> T_ITAB-LOCAT ).
     T_RTAB-STATUS = 'M'.
    ELSEIF T_ITAB-LOCAT IS INITIAL. "new location to create?
      T_RTAB-STATUS = 'L'.
     ELSE.
  ENDIF.
  APPEND T_RTAB.

ENDLOOP. "t_itab


PERFORM PRINT_LIST USING 'NEWLOC'.

END-OF-SELECTION.


AT USER-COMMAND.
  CASE SY-UCOMM.
    WHEN 'EXIT' OR 'CANCEL'.
      LEAVE LIST-PROCESSING.

    WHEN 'PICK'.
      CALL TRANSACTION 'AS03'.

    WHEN 'SORT'.
      IF SY-CUCOL < 12.
        W_SORTCRIT = 'ABCODE'.
       ELSEIF SY-CUCOL < 25.
         W_SORTCRIT = 'ANLN1'.
        ELSEIF SY-CUCOL < 76.
          W_SORTCRIT = 'ANAME'.
         ELSEIF SY-CUCOL < 91.
           W_SORTCRIT = 'NEWLOC'.
          ELSE.
            W_SORTCRIT = 'OLDLOC'.
      ENDIF. "sy-colno
      PERFORM PRINT_LIST USING W_SORTCRIT.

    WHEN 'MOVE'.
      PERFORM PRINT_LIST USING W_SORTCRIT.

    WHEN 'RETURN'.
      READ TABLE T_RTAB WITH KEY ABCOD = SY-LISEL(10).
      IF SY-SUBRC = 0.
        CLEAR T_RTAB-STATUS.
        MODIFY T_RTAB INDEX SY-TABIX.
        PERFORM PRINT_LIST USING W_SORTCRIT.
      ENDIF.

    WHEN OTHERS.
      EXIT.
  ENDCASE.

AT LINE-SELECTION.
  SET PARAMETER ID 'BUK' FIELD T_RTAB-BUKRS.
  SET PARAMETER ID 'AN1' FIELD T_RTAB-ANLN1.
  SET PARAMETER ID 'AN2' FIELD T_RTAB-ANLN2.
  CALL TRANSACTION 'AS03' AND SKIP FIRST SCREEN.


*****************************************************************
FORM PRINT_LIST USING FP_SORT.
  DATA: W_SORT1(7),
        W_SORT2(7),
        W_SORT3(7),
        W_XINT.

  CLEAR: W_SORT1, W_SORT2, W_SORT3.
  CASE FP_SORT.
    WHEN 'NEWLOC'.
      W_SORT1 = 'NWERKS'.
      W_SORT2 = 'NLOCAT'.
      W_SORT3 = 'ABCOD'.
    WHEN 'OLDLOC'.
      W_SORT1 = 'OWERKS'.
      W_SORT2 = 'OLOCAT'.
      W_SORT3 = 'ABCOD'.
    WHEN 'ABCODE'.
      W_SORT1 = 'ABCOD'.
    WHEN 'ANLN1'.
      W_SORT1 = 'BUKRS'.
      W_SORT2 = 'ANLN1'.
    WHEN 'ANAME'.
      W_SORT1 = 'TXT50'.
  ENDCASE. "fp_sort
  SORT T_RTAB BY (W_SORT1) (W_SORT2) (W_SORT3).
  CLEAR: T_RTAB, W_XINT.
  NEW-PAGE WITH-TITLE WITH-HEADING.
  LOOP AT T_RTAB.
    IF W_XINT = 1.
      CLEAR W_XINT.
      FORMAT COLOR 2 INTENSIFIED ON.
     ELSE.
       W_XINT = 1.
       FORMAT COLOR 2 INTENSIFIED OFF.
    ENDIF. "w_xint
    IF T_RTAB-STATUS <> SPACE.
      FORMAT COLOR 3 INTENSIFIED ON.
    ENDIF.
    WRITE: /
           T_RTAB-ABCOD(10),
           T_RTAB-ANLN1,
           T_RTAB-TXT50,
           T_RTAB-OWERKS,
           T_RTAB-OLOCAT,
           T_RTAB-NWERKS,
           T_RTAB-NLOCAT,
           T_RTAB-NLBCOD.
    FORMAT COLOR OFF.
    HIDE T_RTAB-BUKRS.
    HIDE T_RTAB-ANLN1.
    HIDE T_RTAB-ANLN2.
    W_LNUMBER = SY-TABIX.
    HIDE W_LNUMBER.
  ENDLOOP. "t_rtab
ENDFORM. "print_list