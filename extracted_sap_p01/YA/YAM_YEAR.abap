*&---------------------------------------------------------------------*
*& Report  YAM_YEAR                                                    *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*

REPORT  YAM_YEAR LINE-SIZE 170 LINE-COUNT 58.

TABLES: ANLA,
        ANLZ,
        ANKA,
        ANKT,
        ANLC,
        ANEP,
        T001.


PARAMETERS: P_BUKRS LIKE ANLA-BUKRS DEFAULT 'UNES' OBLIGATORY,
            P_YEAR LIKE ANLC-GJAHR OBLIGATORY.

SELECT-OPTIONS: P_ANLKL FOR ANKA-ANLKL,
                P_ANLN1 FOR ANLA-ANLN1.

PARAMETERS: P_AFABE LIKE ANLC-AFABE DEFAULT '01'.

SELECTION-SCREEN SKIP.

SELECT-OPTIONS: P_BWASL FOR ANEP-BWASL,
                P_AMOUNT FOR ANLC-KANSW.

PARAMETERS: P_CLTOT AS CHECKBOX DEFAULT 'X', "only totals by class
            P_BAREA AS CHECKBOX, "show totals for BusAreas
            P_NLEGAC AS CHECKBOX. "include postponed legacy


DATA: BEGIN OF T_ITAB OCCURS 0, "working table
        BUKRS LIKE ANLA-BUKRS,
        ANLKL LIKE ANLA-ANLKL,
        ANLN1 LIKE ANLA-ANLN1,
        ANLN2 LIKE ANLA-ANLN2,
        INVNR LIKE ANLA-INVNR,
        TXT50 LIKE ANLA-TXT50,
        GSBER LIKE ANLZ-GSBER,
        STORT LIKE ANLZ-STORT,
        KANSW LIKE ANLC-KANSW,
        ACQUI LIKE ANEP-ANBTR, "acquisition
        RETIR LIKE ANEP-ANBTR, "retirement
      END OF T_ITAB.

DATA: BEGIN OF T_BUSAREA OCCURS 0, "totals for Business Areas
        GSBER LIKE ANLZ-GSBER,
        KANSW LIKE ANLC-KANSW,
        ACQUI LIKE ANEP-ANBTR, "acquisition
        RETIR LIKE ANEP-ANBTR, "retirement
      END OF T_BUSAREA.

DATA: W_BIEND LIKE ANEP-ANBTR,
      W_STORT LIKE ANLZ-STORT,
      W_GSBER LIKE ANLZ-GSBER,
      W_WFLAG.



START-OF-SELECTION.

REFRESH T_ITAB.

CLEAR ANLA.
SELECT *
      FROM ANLA
      WHERE BUKRS = P_BUKRS
        AND ANLN1 IN P_ANLN1
        AND ANLKL IN P_ANLKL.

  CLEAR: ANLZ.
  SELECT *
        FROM ANLZ
        WHERE BUKRS = ANLA-BUKRS
          AND ANLN1 = ANLA-ANLN1
          AND ANLN2 = ANLA-ANLN2
        ORDER BY PRIMARY KEY.
    IF ANLZ-BDATU(4) >= P_YEAR AND
       ANLZ-ADATU(4) <= P_YEAR.
      W_STORT = ANLZ-STORT.
      W_GSBER = ANLZ-GSBER.
    ENDIF.
  ENDSELECT. "anlz

  CLEAR ANLC. "look for value at biennium start
  SELECT *
        FROM ANLC
        WHERE BUKRS = ANLA-BUKRS
          AND ANLN1 = ANLA-ANLN1
          AND ANLN2 = ANLA-ANLN2
          AND GJAHR = P_YEAR
          AND AFABE = P_AFABE.
    CLEAR T_ITAB.
    MOVE-CORRESPONDING ANLC TO T_ITAB.
    T_ITAB-ANLKL = ANLA-ANLKL.
    T_ITAB-INVNR = ANLA-INVNR.
    T_ITAB-TXT50 = ANLA-TXT50.
    T_ITAB-GSBER = W_GSBER.
    T_ITAB-STORT = W_STORT.
    COLLECT T_ITAB.
  ENDSELECT. "anlc
*if no value found - is it legacy?
  IF SY-SUBRC <> 0 AND ANLA-AKTIV < '20030101' AND P_NLEGAC = 'X'.
    SELECT SINGLE *
          FROM ANLC
          WHERE BUKRS = ANLA-BUKRS
            AND ANLN1 = ANLA-ANLN1
            AND ANLN2 = ANLA-ANLN2
            AND GJAHR > P_YEAR
            AND AFABE = P_AFABE.
      CLEAR T_ITAB.
      MOVE-CORRESPONDING ANLC TO T_ITAB.
      T_ITAB-ANLKL = ANLA-ANLKL.
      T_ITAB-INVNR = ANLA-INVNR.
      T_ITAB-TXT50 = ANLA-TXT50.
      T_ITAB-GSBER = W_GSBER.
      T_ITAB-STORT = W_STORT.
      COLLECT T_ITAB.
  ENDIF. "sy-subrc

  CLEAR ANEP.
  SELECT *
        FROM ANEP
        WHERE BUKRS = ANLA-BUKRS
          AND ANLN1 = ANLA-ANLN1
          AND ANLN2 = ANLA-ANLN2
          AND GJAHR = P_YEAR
          AND AFABE = P_AFABE.
    CHECK ANEP-BWASL IN P_BWASL.
    CLEAR T_ITAB.
    MOVE-CORRESPONDING ANEP TO T_ITAB.
    T_ITAB-ANLKL = ANLA-ANLKL.
    T_ITAB-INVNR = ANLA-INVNR.
    T_ITAB-TXT50 = ANLA-TXT50.
    T_ITAB-GSBER = W_GSBER.
    T_ITAB-STORT = W_STORT.
    IF ANEP-BWASL(1) = '1'.
      T_ITAB-ACQUI = ANEP-ANBTR.
     ELSEIF ANEP-BWASL(1) = 'Z'.
       T_ITAB-RETIR = ANEP-ANBTR.
    ENDIF. "anep-bwasl
    COLLECT T_ITAB.
  ENDSELECT."anep

ENDSELECT. "anla


*check for limited amount
LOOP AT T_ITAB.
  IF NOT ( ABS( T_ITAB-KANSW ) IN P_AMOUNT ) AND
     NOT ( ABS( T_ITAB-ACQUI ) IN P_AMOUNT ) AND
     NOT ( ABS( T_ITAB-RETIR ) IN P_AMOUNT ).
    DELETE T_ITAB.
  ENDIF.
ENDLOOP. "t_itab

*delete 0 assets
DELETE T_ITAB WHERE KANSW = 0
                AND ACQUI = 0
                AND RETIR = 0.

REFRESH T_BUSAREA.
CLEAR: T_ITAB, W_WFLAG.
SORT T_ITAB BY BUKRS ANLKL ANLN1.
LOOP AT T_ITAB.
  CLEAR T_BUSAREA.
  MOVE-CORRESPONDING T_ITAB TO T_BUSAREA.
  COLLECT T_BUSAREA.

  IF P_CLTOT = SPACE. "print all assets
    W_BIEND = T_ITAB-KANSW + T_ITAB-ACQUI + T_ITAB-RETIR.
    IF W_WFLAG = SPACE.
      W_WFLAG = 'X'.
      FORMAT COLOR 2 INTENSIFIED OFF.
     ELSE. "w_wflag
       W_WFLAG = SPACE.
       FORMAT COLOR 2 INTENSIFIED ON.
    ENDIF. "w_wflag
    WRITE: /
           T_ITAB-ANLN1,
           T_ITAB-INVNR(10),
           T_ITAB-TXT50,
           T_ITAB-STORT,
           T_ITAB-KANSW,
           T_ITAB-ACQUI,
           T_ITAB-RETIR,
           W_BIEND.
    FORMAT COLOR OFF.
  ENDIF. "p_cltot

  AT END OF ANLKL.
    CLEAR ANKT.
    SELECT SINGLE *
          FROM ANKT
          WHERE SPRAS = SY-LANGU
            AND ANLKL = T_ITAB-ANLKL.

    SUM.
    W_BIEND = T_ITAB-KANSW + T_ITAB-ACQUI + T_ITAB-RETIR.
    FORMAT COLOR 3 INTENSIFIED OFF.
    WRITE: /
           '***** Class',
           T_ITAB-ANLKL,
           ANKT-TXK50,
        87 T_ITAB-KANSW,
           T_ITAB-ACQUI,
           T_ITAB-RETIR,
           W_BIEND.
    FORMAT COLOR OFF.
  ENDAT. "anlkl

  AT END OF BUKRS.
    CLEAR T001.
    SELECT SINGLE *
          FROM T001
          WHERE BUKRS = T_ITAB-BUKRS.

    SUM.
    W_BIEND = T_ITAB-KANSW + T_ITAB-ACQUI + T_ITAB-RETIR.
    FORMAT COLOR 3 INTENSIFIED ON.
    WRITE: /
           '*** Company Code',
           T_ITAB-BUKRS,
           T001-BUTXT,
        87 T_ITAB-KANSW,
           T_ITAB-ACQUI,
           T_ITAB-RETIR,
           W_BIEND.
    FORMAT COLOR OFF.
  ENDAT. "bukrs
ENDLOOP. "t_itab

END-OF-SELECTION.


IF P_BAREA = 'X'.
  SKIP 2.
  ULINE.
  WRITE: / 'Business Area totals:' COLOR 1.
  SORT T_BUSAREA.
  LOOP AT T_BUSAREA.
    W_BIEND = T_BUSAREA-KANSW + T_BUSAREA-ACQUI + T_BUSAREA-RETIR.
    WRITE: /
           '****',
           T_BUSAREA-GSBER,
        87 T_BUSAREA-KANSW,
           T_BUSAREA-ACQUI,
           T_BUSAREA-RETIR,
           W_BIEND.
  ENDLOOP. "t_busarea
ENDIF. "p_barea