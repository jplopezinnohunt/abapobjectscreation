* 4.0C
* YWWAHRK005859 10031998 T706Z löschen
************************************************************************
*         Umsetzung der Tabelle T706B und T706C                        *
*         Füllen von T706D-WAERSKZ                                     *
*         Füllen von T706A-WAERSPZ und T706A-WAERSFA                   *
*         Umsetzen der Feldnamen in T706Z                              *
*----------------------------------------------------------------------*
*         o T706B1 enthält die Spesenarten mit ihren Attributen        *
*         o T706B2 enthält die Höchstsätze                             *
*         o T706B4 enthält die Lohnarten                               *
************************************************************************
REPORT RPRTRV11 MESSAGE-ID 56.
TABLES: T000,
        T706B,
        T706C,
        T706B1,
        T706B2,
        T706B4,
        T706B5,
        T706D,
        T706Z,
        T001,
        T500P,
        T706A.

DATA: MODIF(1)    VALUE 'X',           " 'X' for DB update
      PRINT_E(1)  VALUE ' ',
      PRINT_T(1)  VALUE 'X',
      GET_TIME(1) VALUE 'X',
      T0 TYPE T,
      T1 TYPE T,
      T2 TYPE P,
      LI TYPE P.

DATA: BEGIN OF 706B OCCURS 0.
        INCLUDE STRUCTURE T706B.
DATA: END OF 706B.

DATA: BEGIN OF 706C OCCURS 0.
        INCLUDE STRUCTURE T706C.
DATA: END OF 706C.

DATA: BEGIN OF 706B1 OCCURS 0.
        INCLUDE STRUCTURE T706B1.
DATA: END OF 706B1.

DATA: BEGIN OF 706B2 OCCURS 0.
        INCLUDE STRUCTURE T706B2.
DATA: END OF 706B2.

DATA: BEGIN OF 706B4 OCCURS 0.
        INCLUDE STRUCTURE T706B4.
DATA: END OF 706B4.

DATA: BEGIN OF 706B5 OCCURS 0.
        INCLUDE STRUCTURE T706B5.
DATA: END OF 706B5.

DATA: BEGIN OF 706Z OCCURS 0.
        INCLUDE STRUCTURE T706Z.
DATA: END OF 706Z.

DATA: BEGIN OF 706Z_APPEND OCCURS 0.
        INCLUDE STRUCTURE T706Z.
DATA: END OF 706Z_APPEND.

DATA: BEGIN OF I000 OCCURS 20.
        INCLUDE STRUCTURE T000.
DATA: END OF I000.

DATA: BEGIN OF MESS_TAB OCCURS 100.
        INCLUDE STRUCTURE SPROT_U.
DATA: END OF MESS_TAB.

DATA: BEGIN OF UMS OCCURS 100,
        ARG LIKE T706Z-FNAME,
        FKT LIKE T706Z-FNAME,
      END OF UMS.

DATA: UMS_KEY LIKE T706Z-FNAME.

DATA: BEGIN OF MOLGA_WAERS OCCURS 20,
        MANDT LIKE T500P-MANDT,
        MOLGA LIKE T500P-MOLGA,
        WAERS LIKE T706A-WAERSPZ,
      END OF MOLGA_WAERS.

DATA: BEGIN OF MOLGA_WAERS_KEY,
        MANDT LIKE T500P-MANDT,
        MOLGA LIKE T500P-MOLGA,
      END OF MOLGA_WAERS_KEY.

DATA: BEGIN OF MOREI_WAERS OCCURS 20,
        MANDT LIKE T706D-MANDT,
        MOREI LIKE T706D-MOREI,
        WAERS LIKE T706A-WAERSPZ,
      END OF MOREI_WAERS.

DATA: BEGIN OF MOREI_WAERS_KEY,
        MANDT LIKE T706D-MANDT,
        MOREI LIKE T706D-MOREI,
      END OF MOREI_WAERS_KEY.


* set breakpoint here if you need to execute this program
  data: exit value 'X'.
  if not exit is initial.
    exit.
  endif.


INCLUDE RPRUMS00.

************************************************************************
* detect clients
************************************************************************
SELECT * FROM T000 INTO TABLE I000.

LOOP AT I000 WHERE MANDT <> '000'.        "xbhtest
*loop at i000 where mandt = '000'.        "xbhtest

  PERFORM APPEND_MESS_TAB
  USING   '3' ' '
          'E' '56' '666'
          'X'
          I000-MANDT SPACE SPACE SPACE.

  IF GET_TIME = 'X'.
    GET TIME. T0 = SY-UZEIT.
  ENDIF.

  T000 = I000.

* Kill table entries in the NEW tables T706B1, T706B2, T706B4
* -> Able to rerun the program
  IF MODIF = 'X'.

    SELECT * FROM T706B1 CLIENT SPECIFIED
                         WHERE MANDT = T000-MANDT.
      DELETE T706B1 CLIENT SPECIFIED.
    ENDSELECT.

    SELECT * FROM T706B2 CLIENT SPECIFIED
                         WHERE MANDT = T000-MANDT.
      DELETE T706B2 CLIENT SPECIFIED.
    ENDSELECT.

    SELECT * FROM T706B4 CLIENT SPECIFIED
                         WHERE MANDT = T000-MANDT.
      DELETE T706B4 CLIENT SPECIFIED.
    ENDSELECT.

    SELECT * FROM T706B5 CLIENT SPECIFIED
                         WHERE MANDT = T000-MANDT.
      DELETE T706B5 CLIENT SPECIFIED.
    ENDSELECT.

  ENDIF.

************************************************************************
* T706B
************************************************************************
  REFRESH: 706B, 706B1, 706B2, 706B4.

  SELECT * FROM T706B CLIENT SPECIFIED
                      INTO TABLE 706B
                      WHERE MANDT = T000-MANDT.

  LOOP AT 706B.

    CLEAR: 706B1, 706B2, 706B4.

    MOVE-CORRESPONDING 706B TO 706B1.
    706B1-SCMER = '-'.         "Ausblenden Feld Leistungserbringer
    IF 706B-PR04X IS INITIAL   "Spesenart wird in PR04 nicht verwendet
    AND 706B-PAUSH <> 'P'.             "keine pauschale Spesenart
      706B1-PR04X = 'Z'.               "Ende Liste TA PR04 aber
      706B1-PR04O = 'D'.               "nicht verwendet im Wochenbericht
    ENDIF.
    PERFORM DRUCK_E USING 706B1.
    APPEND 706B1.

    MOVE-CORRESPONDING 706B TO 706B2.
    IF NOT 706B-SBETR IS INITIAL.      "Vorschlagswert
      706B2-ATYPE = 'A'.
      706B2-BETRG = 706B-SBETR.
      PERFORM DRUCK_E USING 706B2.
      APPEND 706B2.
    ENDIF.
    IF NOT 706B-HBETR IS INITIAL.      "Höchstbetrag
      706B2-BETRG = 706B-HBETR.
      IF 706B-MESSA IS INITIAL.        "mit Warnung
        706B2-ATYPE = 'C'.
      ELSE.
        706B2-ATYPE = 'E'.             "mit Fehlermeldung
      ENDIF.
      PERFORM DRUCK_E USING 706B2.
      APPEND 706B2.
    ENDIF.

    MOVE-CORRESPONDING 706B TO 706B4.
    PERFORM DRUCK_E USING 706B4.
    APPEND 706B4.

  ENDLOOP.                             "at 706b

  DESCRIBE TABLE 706B1 LINES LI.
  PERFORM DRUCK_T USING '706B1' LI.

  DESCRIBE TABLE 706B2 LINES LI.
  PERFORM DRUCK_T USING '706B2' LI.

  DESCRIBE TABLE 706B4 LINES LI.
  PERFORM DRUCK_T USING '706B4' LI.

  IF MODIF = 'X'.

    INSERT T706B1 CLIENT SPECIFIED FROM TABLE 706B1
                 ACCEPTING DUPLICATE KEYS.
    PERFORM DRUCK_T USING 'T706B1' SY-DBCNT.

    INSERT T706B2 CLIENT SPECIFIED FROM TABLE 706B2
                 ACCEPTING DUPLICATE KEYS.
    PERFORM DRUCK_T USING 'T706B2' SY-DBCNT.

    INSERT T706B4 CLIENT SPECIFIED FROM TABLE 706B4
                 ACCEPTING DUPLICATE KEYS.
    PERFORM DRUCK_T USING 'T706B4' SY-DBCNT.

  ENDIF.

************************************************************************
* T706C
************************************************************************
  REFRESH: 706C, 706B5.

  SELECT * FROM T706C CLIENT SPECIFIED
                      INTO TABLE 706C
                      WHERE MANDT = T000-MANDT.

  LOOP AT 706C.

    CLEAR: 706B5.

    MOVE-CORRESPONDING 706C TO 706B5.
    PERFORM DRUCK_E USING 706B5.
    APPEND 706B5.

  ENDLOOP.                             "at 706c

  DESCRIBE TABLE 706B5 LINES LI.
  PERFORM DRUCK_T USING '706B5' LI.

  IF MODIF = 'X'.

    INSERT T706B5 CLIENT SPECIFIED FROM TABLE 706B5
                 ACCEPTING DUPLICATE KEYS.
    PERFORM DRUCK_T USING 'T706B5' SY-DBCNT.

  ENDIF.

************************************************************************
* modify T706Z (new field names, new fields VERPA and PAYOT)
************************************************************************
  REFRESH: 706Z, 706Z_APPEND.

  SELECT * FROM T706Z CLIENT SPECIFIED
                      INTO TABLE 706Z
                      WHERE MANDT = T000-MANDT.

  LOOP AT 706Z.

    UMS_KEY = SPACE.
    UMS_KEY(5) = 706Z-FNAME(5).
    READ TABLE UMS WITH KEY UMS_KEY BINARY SEARCH.
    IF SY-SUBRC = 0.
      DELETE 706Z.
      706Z-FNAME(5) = UMS-FKT.
      APPEND 706Z.
    ELSE.
      UMS_KEY = 706Z-FNAME.
      READ TABLE UMS WITH KEY UMS_KEY BINARY SEARCH.
      IF SY-SUBRC = 0.
        DELETE 706Z.
        706Z-FNAME = UMS-FKT.
        APPEND 706Z.
        IF 706Z-FNAME = 'PTP42-VERPA'  "new field ptp42_verpa
        AND 706Z-AUSWL = '-'.          "suppressed if ptp42-verpa
          706Z-FNAME = 'PTP42_VERPA'.  "is suppressed
          APPEND 706Z.
        ENDIF.
      ENDIF.
    ENDIF.
    ON CHANGE OF 706Z-MOREI.           "append field payot
      CLEAR: 706Z-TRIPF, 706Z-DEFLT.   "on D1300 and D1350
      MOVE-CORRESPONDING 706Z TO 706Z_APPEND.
      706Z_APPEND-AUSWL = '-'.
      706Z_APPEND-DYNNR = 1300.
      706Z_APPEND-FNAME = 'PTK03_PAYOT'.
      APPEND 706Z_APPEND.              "D1300 PTK03_PAYOT
      706Z_APPEND-FNAME = 'PTK03-PAYOT'.
      APPEND 706Z_APPEND.              "D1300 PTK03-PAYOT
      706Z_APPEND-DYNNR = 1350.
      APPEND 706Z_APPEND.              "D1350 PTK03-PAYOT
    ENDON.
  ENDLOOP.

  APPEND LINES OF 706Z_APPEND TO 706Z.
  SORT 706Z.

  DESCRIBE TABLE 706Z LINES LI.
  PERFORM DRUCK_T USING '706Z' LI.

  IF MODIF = 'X'.

*   delete t706z client specified.     "total refresh "YWWK005859
    DELETE FROM T706Z CLIENT SPECIFIED "total refresh "YWWK005859
           WHERE MANDT = T000-MANDT.                  "YWWK005859
    INSERT T706Z CLIENT SPECIFIED FROM TABLE 706Z
                 ACCEPTING DUPLICATE KEYS.

    PERFORM DRUCK_T USING 'T706Z' SY-DBCNT.

  ENDIF.

************************************************************************
* fill T706D-WAERSKZ
************************************************************************
  IF MODIF = 'X'.
    SELECT * FROM T706D CLIENT SPECIFIED
                         WHERE MANDT = T000-MANDT.
      T706D-WAERSKZ = '1'.
      MODIFY T706D CLIENT SPECIFIED.
    ENDSELECT.
    PERFORM DRUCK_T USING 'T706D' SY-DBCNT.
  ENDIF.

************************************************************************
* fill T706A-WAERSPZ, T706A-WAERSFA
************************************************************************
  INCLUDE RPRUMS01.                    "fill table morei_waers
  IF MODIF = 'X'.
    SELECT * FROM T706A CLIENT SPECIFIED
                         WHERE MANDT = T000-MANDT.
      IF ( NOT T706A-ABZPZ IS INITIAL AND T706A-KZSPA IS INITIAL )
      OR ( NOT T706A-ABZFA IS INITIAL AND T706A-KZFPA IS INITIAL ).
        MOVE-CORRESPONDING T706A TO MOREI_WAERS_KEY.
        READ TABLE MOREI_WAERS WITH KEY MOREI_WAERS_KEY.
        IF SY-SUBRC = 0.
          IF NOT T706A-ABZPZ IS INITIAL AND T706A-KZSPA IS INITIAL.
            T706A-WAERSPZ = MOREI_WAERS-WAERS.
          ENDIF.
          IF NOT T706A-ABZFA IS INITIAL AND T706A-KZFPA IS INITIAL.
            T706A-WAERSFA = MOREI_WAERS-WAERS.
          ENDIF.
          MODIFY T706A CLIENT SPECIFIED.
        ELSE.
*                                "keine Währungsbestimmung möglich
        ENDIF.
      ENDIF.
    ENDSELECT.
    PERFORM DRUCK_T USING 'T706A' SY-DBCNT.
  ENDIF.

  PERFORM DRUCK_ZEIT.

ENDLOOP.                               "at i000.

* Aufruf der Protokollschnittstelle
CALL FUNCTION 'TR_APPEND_LOG'
     TABLES
          XMSG   = MESS_TAB
     EXCEPTIONS
          OTHERS = 4.
IF SY-SUBRC NE 0.
  WRITE: 'Error in using the protocol interface'(002).
ENDIF.


*---------------------------------------------------------------------*
*     FORM DRUCK_E                                                    *
*---------------------------------------------------------------------*
FORM DRUCK_E USING VALUE(TABL).
  IF PRINT_E = 'X'.
    WRITE: / TABL.
  ENDIF.
ENDFORM.

*---------------------------------------------------------------------*
*     FORM DRUCK_T                                                    *
*---------------------------------------------------------------------*
FORM DRUCK_T USING VALUE(TABL) VALUE(ZAEHLER).
  IF PRINT_T = 'X'.
    PERFORM APPEND_MESS_TAB
    USING   '4' ' '
            'E' '56' '667'
            ' '
            TABL ZAEHLER SPACE SPACE.
  ENDIF.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM DRUCK_ZEIT                                               *
*---------------------------------------------------------------------*
FORM DRUCK_ZEIT.
  DATA: TIME_FR(8),
        TIME_TO(8).
  IF GET_TIME = 'X'.
    GET TIME. T1 = SY-UZEIT.
    T2 = T1 - T0.
    WRITE T0 USING EDIT MASK '__:__:__' TO TIME_FR.
    WRITE T1 USING EDIT MASK '__:__:__' TO TIME_TO.

    PERFORM APPEND_MESS_TAB
    USING   '4' ' '
            'E' '56' '668'
            ' '
            T2 TIME_FR TIME_TO SPACE.

  ENDIF.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM APPEND_MESS_TAB                                          *
*---------------------------------------------------------------------*
FORM  APPEND_MESS_TAB
USING VALUE(LEVEL)
      VALUE(SEVERITY)
      VALUE(LANGU)
      VALUE(AG)
      VALUE(MSGNR)
      VALUE(NEWOBJ)
      VALUE(VAR1)
      VALUE(VAR2)
      VALUE(VAR3)
      VALUE(VAR4).

  CLEAR MESS_TAB.
  MESS_TAB-LEVEL    = LEVEL.
  MESS_TAB-SEVERITY = SEVERITY.
  MESS_TAB-LANGU    = LANGU.
  MESS_TAB-AG       = AG.
  MESS_TAB-MSGNR    = MSGNR.
  MESS_TAB-NEWOBJ   = NEWOBJ.
  MESS_TAB-VAR1     = VAR1.
  MESS_TAB-VAR2     = VAR2.
  MESS_TAB-VAR3     = VAR3.
  MESS_TAB-VAR4     = VAR4.
  APPEND MESS_TAB.

ENDFORM.