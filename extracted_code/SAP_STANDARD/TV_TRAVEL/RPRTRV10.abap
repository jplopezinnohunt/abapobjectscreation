* 4.6C
* YWWL9CK035324 22122000 Sicherheitsabfrage
* 4.5B
* YWWAHRK022807 04091998 Falsche laufende Nummer bei KMVER
* 4.5A
* YWWPH4K016493 22071998 Wiederholbarkeit
* YWWPH4K015659 20071998 Probleme auf Oracle
* YWWAHRK005859 10031998 PTRV_PERIO-WAERS füllen, wenn Upgrade von 3.0D
************************************************************************
*         Umsetzung der TE und TS-Cluster                              *
*----------------------------------------------------------------------*
*         o Versionsnummer wird auf 03 hochgesetzt                     *
*         o KOPF (PTK02) geht über in                                  *
*           TRANSPORT (PTP62) sowie die transparenten Tabellen         *
*           PTRV_PERIO (PTP42) und PTRV_HEAD (PTP02)                   *
*         o Kilometer aus KOPF (PTK02) ohne Verteilung werden in KMVER *
*           (PTK10) abgespeichert                                      *
*         o KMVER (PTK10) erhält neue Felder INLKM, AUSKM              *
*         o TE-KEY benutzt PTP00 statt PTK00                           *
*         o RPRIV (PTK26) entfällt                                     *
*         o TRANSPORT (PTP62), PASSENGERS (PTP63), RET_JOURNEY (PTP66) *
*           und ABSENCE (PTP69) neu                                    *
*         o V0SPLIT (PTP70) neu                                        *
*         o VPFPS (PTK22) erhält neue Felder V0TYP, V0ZNR              *
*         o VPFPA (PTK23) erhält neue Felder V0TYP, V0ZNR              *
*         o ROT (PTK30) erhält neue Felder WAERS, LINE, TXJCD          *
*         o AEND (PTK11): Feld REPID wurde verlängert                  *
************************************************************************
REPORT RPRTRV00 MESSAGE-ID 56.
TABLES: PERNR, PCL1, T000, PTRV_HEAD, PTRV_PERIO, PTRV_KMSUM, T549Q,
        PA0001.

DATA: BEGIN OF IPCL1 OCCURS 20,                           "QIZKXXXXXX
         CLIENT LIKE PCL1-CLIENT,                         "QIZKXXXXXX
         RELID LIKE PCL1-RELID,                           "QIZKXXXXXX
         SRTFD LIKE PCL1-SRTFD,                           "QIZKXXXXXX
         SRTF2 LIKE PCL1-SRTF2,                           "QIZKXXXXXX
         VERSN LIKE PCL1-VERSN,                           "QIZKXXXXXX
      END OF IPCL1.                                       "QIZKXXXXXX
DATA: T_HEAD  LIKE PTRV_HEAD  OCCURS 0 WITH HEADER LINE.  "QIZKXXXXXX
DATA: T_PERIO LIKE PTRV_PERIO OCCURS 0 WITH HEADER LINE.  "QIZKXXXXXX
DATA: T_KMSUM LIKE PTRV_KMSUM OCCURS 0 WITH HEADER LINE.  "QIZKXXXXXX

INCLUDE RPC1TE40.               "TE-Clusterbeschreibung Stand 4.0
INCLUDE RPC1TE30.               "abw. TE-Clusterbeschreibung Stand 3.0
INCLUDE RPC1TS30.               "TS-Clusterbeschreibung Stand 3.0
INCLUDE MP56TT99.               "Definition der Usertabelle USER.

FIELD-GROUPS: HEADER, TE_CLUSTER, TS_CLUSTER.
* diverse Zaehler fuer die Statistik
DATA: COUNTER_TE(8)        TYPE N.     "selektierte TE-Cluster
DATA: COUNTER_TS(8)        TYPE N.     "selektierte TS-Cluster
DATA: TE_ERROR(8)          TYPE N.     "fehlerhafte TE-Cluster
DATA: TS_ERROR(8)          TYPE N.     "fehlerhafte TS-Cluster
DATA: TE_TO_CONVERT(8)     TYPE N.     "umzusetzende TE-Cluster
DATA: TS_TO_CONVERT(8)     TYPE N.     "umzusetzende TS-Cluster
DATA: TE_CONVERTED(8)      TYPE N.     "umgesetzte TE-Cluster
DATA: ALREADY_CONVERTED_TE(8) TYPE N.  "bereits umgesetzte TE-Cluster
DATA: TS_CONVERTED(8)      TYPE N.     "umgesetzte TS-Cluster
DATA: ALREADY_CONVERTED_TS(8) TYPE N.  "bereits umgesetzte TS-Cluster
DATA: COUNTER_PERNR_TE(8)  TYPE N.     "berührte Personalnummern
* Hilfsfelder
DATA: H_PERNR LIKE PERNR-PERNR.
DATA: TE_KEY_REINR_LFDNR(14).
DATA: NUMBER_OF_LINES      TYPE P.     "Anzahl Zeilen in Tab. REISEN
DATA: SUBRC LIKE SY-SUBRC.
DATA: INDEX LIKE SY-INDEX.
DATA: GO_ON(1).
DATA: ZEILE(79).
DATA: CLIENT LIKE T000-MANDT.          "Hilfsfeld für Mandantenwechsel
DATA: C1 TYPE CURSOR.                  "Hilfsfeld für neuen OPEN-Befehl
DATA: COMMIT_COUNTER TYPE P.           "Hilfsfeld für COMMIT WORK
DATA: KMVER_LINES LIKE SYST-INDEX.
DATA: KMSUM_LINES LIKE SYST-INDEX.
DATA: OLD_PERNR LIKE PA0001-PERNR.

* Intervall fuer PCL1-Key
DATA: BEGIN OF SRTFDLOW,
*       hex(40) type x,                                     "QIZKXXXXXX
        CHAR(40) TYPE C,                                    "QIZKXXXXXX
      END OF SRTFDLOW.
DATA: BEGIN OF SRTFDHIGH,
*       hex(40) type x,                                     "QIZKXXXXXX
        CHAR(40) TYPE C,                                    "QIZKXXXXXX
      END OF SRTFDHIGH.
* Message Handling
DATA: BEGIN OF MESS_TAB OCCURS 100.
        INCLUDE STRUCTURE SPROT_U.
DATA: END OF MESS_TAB.

* Select-Options und Parameter
*elect-options: selpernr for te-key-pernr.               "QIZTestcoding
*elect-options: selreinr for te-key-reinr.               "QIZTestcoding
*ARAMETERS:     TESTL DEFAULT 'X'.                       "QIZTestcoding
*ARAMETERS:     PROTK DEFAULT 'X'.                       "QIZTestcoding
*arameters:     xpernr like ptp00-pernr default '00025000'. "WWW
*arameters:     zpernr like ptp00-pernr default '00025010'. "WWW
DATA:           TESTL VALUE   ' '.
DATA:           PROTK VALUE   ' '.
DATA: ROT_WAERS LIKE ROT-WAERS.                          "DDDDDD

DATA: BEGIN OF T_001 OCCURS 50,
        MANDT LIKE T001-MANDT,                           "QIZKXXXXXXX
        BUKRS LIKE T001-BUKRS,
        WAERS LIKE T001-WAERS,
      END OF T_001.

DATA: BUK LIKE PA0001-BUKRS,
      ABK LIKE PA0001-ABKRS.

DATA: OLD_WAERS LIKE T001-WAERS.
DATA: WAEHRUNGEN_GLEICH(1) TYPE C.
* Begin of YWWK035324
data: old_records_exist(1) type c.
data: true value 'X',
      false value ' '.
* End of YWWK035324


START-OF-SELECTION.                    "Bearbeitung vor Datenselektion
  DETAIL.
  PERFORM INIT_SORTFIELDS.
  REFRESH MESS_TAB.
* Mandantenübergreifendes Lesen der Tabellen T549Q, T001..."QIZKXXXXXX
  PERFORM BUILD_TAB.                                       "QIZKXXXXXX
  PERFORM FILL_T_001.                                      "QIZKXXXXXX

  PERFORM SELECT_TE_TS_KEY.            "Cluster selektieren und umsetzen

END-OF-SELECTION.                      "Bearbeitung nach Datenselektion

* QIZKXXXXXX TS-Cluster wird nur einmal gelöscht!         "QIZKXXXXXX
* Eventuell in ein separates Programm auslagern!          "QIZKXXXXXX

* QIZTestcoding Delete TS-Cluster deaktiviert.
*  DELETE FROM PCL1 CLIENT SPECIFIED                       "QIZKXXXXXX
*                  WHERE RELID = 'ZB'.                     "QIZKXXXXXX
**                 where relid = 'TS'.                     "QIZKXXXXXX
*
  IF PROTK EQ 'X'.
    NEW-PAGE.
  ENDIF.
  CALL FUNCTION 'TR_APPEND_LOG'
       TABLES
            XMSG   = MESS_TAB
       EXCEPTIONS
            OTHERS = 4.
  IF SY-SUBRC NE 0.
    WRITE: 'Error in using the protocol interface'(001).
  ENDIF.

  CALL FUNCTION 'TR_FLUSH_LOG'                              "QIZKXXXXXX
       EXCEPTIONS                                           "QIZKXXXXXX
            OTHERS  = 1.                                    "QIZKXXXXXX

***********************************************************************
* Unterroutinen                                                       *
***********************************************************************

*---------------------------------------------------------------------*
*       FORM SELECT_TE/TS_KEY                                         *
*---------------------------------------------------------------------*
FORM SELECT_TE_TS_KEY.
* TE-Key selektiern
* Begin of YWWK035324
  old_records_exist = false.
  select * from pcl1 client specified
                     where relid = 'TE'
                       and versn = '02'.
    old_records_exist = true.
    exit.
  endselect.
  if old_records_exist = false.
    CLEAR MESS_TAB.
    MESS_TAB-LEVEL    = 3.
    MESS_TAB-SEVERITY = ' '.
    MESS_TAB-LANGU    = sy-langu.
    MESS_TAB-AG       = '56'.
    MESS_TAB-MSGNR    = '665'.
    MESS_TAB-NEWOBJ   = ' '.
    MESS_TAB-VAR1 = SPACE.
    MESS_TAB-VAR2 = SPACE.
    MESS_TAB-VAR3 = SPACE.
    MESS_TAB-VAR4 = SPACE.
    APPEND MESS_TAB.
    stop.
  endif.
* End of YWWK035324

  SELECT * FROM PTRV_HEAD CLIENT SPECIFIED.          "YWWK016493
    DELETE PTRV_HEAD CLIENT SPECIFIED.               "YWWK016493
  ENDSELECT.                                         "YWWK016493

  SELECT * FROM PTRV_PERIO CLIENT SPECIFIED.         "YWWK016493
    DELETE PTRV_PERIO CLIENT SPECIFIED.              "YWWK016493
  ENDSELECT.                                         "YWWK016493

  SELECT * FROM PTRV_KMSUM CLIENT SPECIFIED.         "YWWK016493
    DELETE PTRV_KMSUM CLIENT SPECIFIED.              "YWWK016493
  ENDSELECT.                                         "YWWK016493

  CALL FUNCTION 'DB_COMMIT'.                         "YWWK016493

  CLEAR CLIENT.
  OPEN CURSOR WITH HOLD C1 FOR
* select * from pcl1 client specified                  "QIZKXXXXXX
  SELECT CLIENT RELID SRTFD SRTF2 VERSN                "QIZKXXXXXX
                     FROM PCL1 CLIENT SPECIFIED        "QIZKXXXXXX
                     WHERE RELID = 'TE'                "WWW
*                    where relid = 'ZA'                "QIZTestcoding
*                    and srtfd                         "QIZTestcoding
*                    between srtfdlow and srtfdhigh    "QIZTestcoding
*                    and   srtf2 = '00'                "QIZKXXXXXX
                     AND   SRTF2 = '0         '        "QIZKXXXXXX
                     ORDER BY CLIENT
                              RELID
                              SRTFD
                              SRTF2.
  DO.
*   fetch next cursor c1 into pcl1.                         "QIZKXXXXXX
    FETCH NEXT CURSOR C1 INTO CORRESPONDING FIELDS OF       "QIZKXXXXXX
                              TABLE IPCL1 PACKAGE SIZE 100. "QIZKXXXXXX
    IF NOT ( SY-SUBRC IS INITIAL ).
      EXIT.
    ENDIF.
    LOOP AT IPCL1.                                          "QIZKXXXXXX
*     te-key_old = pcl1-srtfd.                              "QIZKXXXXXX
      TE-KEY_OLD = IPCL1-SRTFD.                             "QIZKXXXXXX
*     check: selpernr.                                   "QIZTestcoding
*     check: selreinr.                                   "QIZTestcoding
* Umsetzstatistik vor der Bearbeitung des neuen Mandanten
*     if not ( client is initial ) and pcl1-client ne client.  "QIZKXXX
      IF NOT ( CLIENT IS INITIAL ) AND IPCL1-CLIENT NE CLIENT. "QIZKXXX
        PERFORM STATISTICS USING CLIENT 'TE'.
      ENDIF.
*     if pcl1-client ne client.                             "QIZKXXXXXX
      IF IPCL1-CLIENT NE CLIENT.                            "QIZKXXXXXX
* QIZKXXXXXX Lesen der T549Q und T001 nach ober verlegt...
*       perform build_tab.                                  "QIZKXXXXXX
*       perform fill_t_001.                                 "QIZKXXXXXX
        PERFORM CURRENCIES_ARE_EQUAL                        "QIZKXXXXXX
                USING WAEHRUNGEN_GLEICH.                    "QIZKXXXXXX
      ENDIF.
      IF WAEHRUNGEN_GLEICH IS INITIAL.
*       if pcl1-client ne client or pcl1-srtfd(8) ne old_pernr.  "QIZKX
        IF IPCL1-CLIENT NE CLIENT OR IPCL1-SRTFD(8) NE OLD_PERNR."QIZKX
*         old_pernr = pcl1-srtfd(8).                        "QIZKXXXXXX
          OLD_PERNR = IPCL1-SRTFD(8).                       "QIZKXXXXXX
*         perform read_0001 using pcl1-srtfd(8).            "QIZKXXXXXX
          PERFORM READ_0001 USING IPCL1-SRTFD(8).           "QIZKXXXXXX
        ENDIF.
      ENDIF.

* Umsetzung
*     perform import_te  using pcl1-client go_on.           "QIZKXXXXXX
      PERFORM IMPORT_TE  USING IPCL1-CLIENT GO_ON.          "QIZKXXXXXX
*     perform convert_te using pcl1-client go_on.           "QIZKXXXXXX
      PERFORM CONVERT_TE USING IPCL1-CLIENT GO_ON.          "QIZKXXXXXX
* Zähler auf Anraten der Basis auf 50.000 gesetzt.          "QIZKXXXXXX
*     if commit_counter ge 1000.                            "QIZKXXXXXX
      IF COMMIT_COUNTER GE 50000.                           "QIZKXXXXXX
* Interne Tabellen T_HEAD und T_PERIO vorher wegschreiben.
        INSERT PTRV_HEAD CLIENT SPECIFIED FROM TABLE T_HEAD. "QIZKXXXXX
        INSERT PTRV_PERIO CLIENT SPECIFIED FROM TABLE T_PERIO. "QIZKXXX
        CLEAR: T_HEAD, T_PERIO.                             "QIZKXXXXXX
        REFRESH: T_HEAD, T_PERIO.                           "QIZKXXXXXX
        IF SY-DBSYS(3) NE 'ORA'.                            "YWWK015659
          CALL FUNCTION 'DB_COMMIT'.
        ENDIF.                                              "YWWK015659
        CLEAR COMMIT_COUNTER.
      ENDIF.
*     client = pcl1-client.                                 "QIZKXXXXXX
      CLIENT = IPCL1-CLIENT.                                "QIZKXXXXXX
    ENDLOOP.                                                "QIZKXXXXXX
  ENDDO.
* Rest wegschreiben.                                        "QIZKXXXXXX
  INSERT PTRV_HEAD CLIENT SPECIFIED FROM TABLE T_HEAD.      "QIZKXXXXXX
  INSERT PTRV_PERIO CLIENT SPECIFIED FROM TABLE T_PERIO.    "QIZKXXXXXX
  CLEAR: T_HEAD, T_PERIO.                                   "QIZKXXXXXX
  REFRESH: T_HEAD, T_PERIO.                                 "QIZKXXXXXX
  CALL FUNCTION 'DB_COMMIT'.                                "QIZKXXXXXX
  CLEAR COMMIT_COUNTER.                                     "QIZKXXXXXX

  CLOSE CURSOR C1.
* Umsetzstatistik für den letzten Mandanten.
  PERFORM STATISTICS USING CLIENT 'TE'.

* TS-Key selektiern
  CLEAR CLIENT.
  OPEN CURSOR WITH HOLD C1 FOR
* select * from pcl1 client specified                    "QIZKXXXXXX
  SELECT CLIENT RELID SRTFD SRTF2 VERSN                  "QIZKXXXXXX
                     FROM PCL1 CLIENT SPECIFIED          "QIZKXXXXXX
                     WHERE RELID = 'TS'                  "WWW
*                    where relid = 'ZB'                  "QIZTestcoding
*                    and srtfd                           "QIZTestcoding
*                    between srtfdlow and srtfdhigh      "QIZTestcoding
*                    and   srtf2 = '00'                  "QIZKXXXXXX
                     AND   SRTF2 = '0         '          "QIZKXXXXXX
                     ORDER BY CLIENT
                              RELID
                              SRTFD
                              SRTF2.
  DO.
*   fetch next cursor c1 into pcl1.                         "QIZKXXXXXX
    FETCH NEXT CURSOR C1 INTO CORRESPONDING FIELDS OF       "QIZKXXXXXX
                              TABLE IPCL1 PACKAGE SIZE 100. "QIZKXXXXXX
    IF NOT ( SY-SUBRC IS INITIAL ).
      EXIT.
    ENDIF.
    LOOP AT IPCL1.                                       "QIZKXXXXXX
*     te-key_old = pcl1-srtfd.                           "QIZKXXXXXX
      TE-KEY_OLD = IPCL1-SRTFD.                          "QIZKXXXXXX
      TE-KEY-PERNR = TE-KEY_OLD-PERNR.                   "FEHLT
      DATA: PCL1_SRTFD LIKE PCL1-SRTFD.                  "FEHLT
*     pcl1_srtfd = pcl1-srtfd.                           "QIZKXXXXXX
      PCL1_SRTFD = IPCL1-SRTFD.                          "QIZKXXXXXX
*     check: selpernr.                                   "QIZTestcoding
* Umsetzstatistik vor der Bearbeitung des neuen Mandanten
*     if not ( client is initial ) and pcl1-client ne client.  "QIZKXX
      IF NOT ( CLIENT IS INITIAL ) AND IPCL1-CLIENT NE CLIENT. "QIZKXX
        PERFORM STATISTICS USING CLIENT 'TS'.
      ENDIF.
*     perform import_ts  using pcl1-client go_on.      "QIZKXXXXXX
      PERFORM IMPORT_TS  USING IPCL1-CLIENT GO_ON.     "QIZKXXXXXX
*     perform convert_ts using pcl1-client go_on.      "QIZKXXXXXX
      PERFORM CONVERT_TS USING IPCL1-CLIENT GO_ON.     "QIZKXXXXXX
* Zähler auf Anraten der Basis auf 50.000 gesetzt.     "QIZKXXXXXX
*     if commit_counter ge 1000.                       "QIZKXXXXXX
      IF COMMIT_COUNTER GE 50000.                      "QIZKXXXXXX
        INSERT PTRV_KMSUM CLIENT SPECIFIED FROM TABLE T_KMSUM."QIZKXXXXX
        CLEAR: T_KMSUM.                                "QIZKXXXXXX
        REFRESH: T_KMSUM.                              "QIZKXXXXXX
        IF SY-DBSYS(3) NE 'ORA'.                            "YWWK015659
          CALL FUNCTION 'DB_COMMIT'.
        ENDIF.                                              "YWWK015659
        CLEAR COMMIT_COUNTER.
      ENDIF.
*     client = pcl1-client.                            "QIZKXXXXXX
      CLIENT = IPCL1-CLIENT.                           "QIZKXXXXXX
* QIZKXXXXX Beginn...
* Löschen des kompletten TS-Clusters ans Ende des Programms gesetzt.
* Man sollte die vielleicht in ein separates Programm auslagern!
*      DELETE FROM PCL1 CLIENT SPECIFIED
*                       WHERE RELID = 'ZB'
**                      where relid = 'TS'                   "WWW
**                        and srtfd = ts-key                 "FEHLT
*                         AND SRTFD = PCL1_SRTFD             "FEHLT
*                         AND SRTF2 = '00'.
* QIZKXXXXX Ende...
    ENDLOOP.
  ENDDO.

* Rest wegschreiben.                                        "QIZKXXXXXX
  INSERT PTRV_KMSUM CLIENT SPECIFIED FROM TABLE T_KMSUM.    "QIZKXXXXXX
  CLEAR: T_KMSUM.                                           "QIZKXXXXXX
  REFRESH: T_KMSUM.                                         "QIZKXXXXXX
  CALL FUNCTION 'DB_COMMIT'.                                "QIZKXXXXXX
  CLOSE CURSOR C1.
* Umsetzstatistik für den letzten Mandanten.
  PERFORM STATISTICS USING CLIENT 'TS'.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM IMPORT_TE                                                *
*---------------------------------------------------------------------*
*  -->  CLIENT                                                        *
*  -->  GO_ON                                                         *
*---------------------------------------------------------------------*
FORM IMPORT_TE USING VALUE(CLIENT) GO_ON.
  CLEAR GO_ON.

* Satz bereits umgesetzt?
* if pcl1-versn eq '03'.                                    "QIZKXXXXXX
  IF IPCL1-VERSN EQ '03'.                                   "QIZKXXXXXX
    COUNTER_TE = COUNTER_TE + 1.
    ALREADY_CONVERTED_TE = ALREADY_CONVERTED_TE + 1.
    IF PROTK EQ 'X'.
      WRITE: / 'TE-Cluster is already converted:'(E03),
                TE-KEY-PERNR, TE-KEY-REINR, TE-KEY-PDVRS.
    ENDIF.
    EXIT.
  ENDIF.

* Cluster muß eingelesen werden; CLEAR auf neue Strukturen
* CLEAR: TRANSPORT, PASSENGERS, RET_JOURNEY, ABSENCE,
*        V0SPLIT.
  CLEAR: BELEG, ABZUG, ZIEL, ZWECK, KONTI, KMVER, USER, KOSTR,
         KOSTZ, KOSTB, PAUFA, UEBPA, BELER, VPFPS, VPFPA, VSCH, ROT,
         OTE-VERSION, RUW, KOPF, STATU, KOSTK, AEND, EXBEL,
         TRANSPORT.
* CLEAR auf alte Strukturen
  CLEAR: AEND_OLD, VPFPS_OLD, VPFPA_OLD, ROT_OLD, KMVER_OLD.
* REFRESH auf neue Tabellen
  REFRESH: BELEG, ABZUG, ZIEL, ZWECK, KONTI, KMVER, USER, KOSTR,
           KOSTZ, KOSTB, PAUFA, UEBPA, BELER, VPFPS, VPFPA, VSCH, ROT,
           RUW, KOSTK, AEND, EXBEL.

* REFRESH auf alte Tabellen
  REFRESH: AEND_OLD, VPFPS_OLD, VPFPA_OLD, ROT_OLD, KMVER_OLD.

  PERFORM RP-IMP-C1-TE USING CLIENT SUBRC.
* te-key-pernr(1) = '8'.                                          "WWW
* te-key_old-pernr(1) = '8'.
  TE-KEY-PERNR = IPCL1-SRTFD(8).                            "QIZKXXXXXX
  TE-KEY_OLD-PERNR = IPCL1-SRTFD(8).                        "QIZKXXXXXX
  IF SUBRC NE 0.
    TE_ERROR = TE_ERROR + 1.           "fehlerhaftes TE-Cluster
*   WRITE: / 'Fehler beim Einlesen des TE_Clusters:'(E02),
*             TE-KEY-PERNR, TE-KEY-REINR, TE-KEY-LFDNR.
  ELSE.
* Cluster erfolgreich eingelesen
    COUNTER_TE = COUNTER_TE + 1.
    GO_ON = 'X'.                                "weitermachen!
    IF H_PERNR <> TE-KEY-PERNR.
      H_PERNR = TE-KEY-PERNR.
      COUNTER_PERNR_TE = COUNTER_PERNR_TE + 1.  "Anzahl Personalnummern
    ENDIF.
  ENDIF.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM CONVERT_TE                                               *
*---------------------------------------------------------------------*
*  -->  CLIENT                                                        *
*  -->  GO_ON                                                         *
*---------------------------------------------------------------------*
FORM CONVERT_TE USING VALUE(CLIENT) GO_ON.
* DATA: H_C1ZNR(2) TYPE P.

  CHECK GO_ON EQ 'X'.
  COMMIT_COUNTER = COMMIT_COUNTER + 1. "Zähler für COMMIT WORK
* aktuelle Versionsnummer setzen
  TE-VERSION-SAPRL = SY-SAPRL.
  TE-VERSION-NUMBR = '03'.

  TE_TO_CONVERT = TE_TO_CONVERT + 1.
* eingelesene Tabellen initialisieren wegen Neuaufbau dieser Tabellen
* CLEAR KOPF.
* CLEAR KONTI. REFRESH KONTI.
* CLEAR KOSTB. REFRESH KOSTB.
* CLEAR BELER. REFRESH BELER.
* CLEAR ROT.   REFRESH ROT.
  MOVE-CORRESPONDING TE-KEY_OLD TO TE-KEY.
  TE-KEY-PDVRS = TE-KEY_OLD-LFDNR.
  MOVE-CORRESPONDING KOPF TO TRANSPORT.                        "PKWRG
  DATA: I_KMVNR(4) TYPE C.                                 "YWWK022807
  I_KMVNR = '0000'.                                        "YWWK022807
  LOOP AT KMVER_OLD.                                       "YWWK005859
    I_KMVNR = I_KMVNR + 1.                                 "YWWK022807
    MOVE-CORRESPONDING KMVER_OLD TO KMVER.                 "YWWK005859
*   kmver-kmvnr = sy-tabix.                                "YWWK022807
    KMVER-KMVNR = I_KMVNR(3).                              "YWWK022807
    TRANSLATE KMVER-KMVNR USING ' 0'.                      "YWWK022807
    APPEND KMVER.                                          "YWWK005859
  ENDLOOP.                                                 "YWWK005859
  IF NOT ( KOPF-KMGES IS INITIAL ).
    DESCRIBE TABLE KMVER LINES KMVER_LINES.
    IF KMVER_LINES = 0.
      MOVE-CORRESPONDING KOPF TO KMVER.
      KMVER-DATUM = KOPF-DATV1.
      KMVER-KMVNR = 1.                                     "YWWK005859
      APPEND KMVER.
    ENDIF.
  ENDIF.
* LOOP AT KMVER.                                           "YWWK005859
*   CHECK KMVER-KMVNR IS INITIAL.                          "YWWK005859
*   KMVER-KMVNR = SY-TABIX.                                "YWWK005859
*   MODIFY KMVER.                                          "YWWK005859
* ENDLOOP.                                                 "YWWK005859
***********************************************************************
* T_HEAD versorgen...
  MOVE-CORRESPONDING KOPF TO PTRV_HEAD.
* ptrv_head-mandt = pcl1-client.                            "QIZKXXXXXX
  PTRV_HEAD-MANDT = IPCL1-CLIENT.                           "QIZKXXXXXX
  PTRV_HEAD-PERNR = TE-KEY_OLD-PERNR.
  PTRV_HEAD-REINR = TE-KEY_OLD-REINR.
  PTRV_HEAD-HDVRS = TE-KEY_OLD-LFDNR.
* insert ptrv_head client specified.                        "QIZKXXXXXX
  CLEAR T_HEAD.                                             "QIZKXXXXXX
  T_HEAD = PTRV_HEAD.                                       "QIZKXXXXXX
  APPEND T_HEAD.                                            "QIZKXXXXXX
* T_PERIO versorgen...
  MOVE-CORRESPONDING KOPF TO PTRV_PERIO.
  IF KOPF-WAERS IS INITIAL.                              "YWWK005859
    IF WAEHRUNGEN_GLEICH IS INITIAL.                     "YWWK005859
      PERFORM GET_WAERS.                                 "YWWK005859
    ENDIF.                                               "YWWK005859
    PTRV_PERIO-WAERS = ROT_WAERS.                        "YWWK005859
  ENDIF.                                                 "YWWK005859
  MOVE-CORRESPONDING STATU TO PTRV_PERIO.
* ptrv_perio-mandt = pcl1-client.                           "QIZKXXXXXX
  PTRV_PERIO-MANDT = IPCL1-CLIENT.                          "QIZKXXXXXX
  PTRV_PERIO-PERNR = TE-KEY_OLD-PERNR.
  PTRV_PERIO-REINR = TE-KEY_OLD-REINR.
  PTRV_PERIO-PDVRS = TE-KEY_OLD-LFDNR.
  PTRV_PERIO-HDVRS = TE-KEY_OLD-LFDNR.
  PTRV_PERIO-PDATV = KOPF-DATV1.
  PTRV_PERIO-PDATB = KOPF-DATB1.
  PTRV_PERIO-PUHRV = KOPF-UHRV1.
  PTRV_PERIO-PUHRB = KOPF-UHRB1.
  PTRV_PERIO-ACCDT = '19720401'.       "Was soll das?       "QIZKXXXXXX
  PERFORM READ_TAB.
* insert ptrv_perio client specified.                       "QIZKXXXXXX
  CLEAR T_PERIO.                                            "QIZKXXXXXX
  T_PERIO = PTRV_PERIO.                                     "QIZKXXXXXX
  APPEND T_PERIO.                                           "QIZKXXXXXX
***********************************************************************
  LOOP AT AEND_OLD.
    MOVE-CORRESPONDING AEND_OLD TO AEND.
    APPEND AEND.
  ENDLOOP.
  LOOP AT VPFPS_OLD.
    MOVE-CORRESPONDING VPFPS_OLD TO VPFPS.
    APPEND VPFPS.
  ENDLOOP.
  LOOP AT VPFPA_OLD.
    MOVE-CORRESPONDING VPFPA_OLD TO VPFPA.
    APPEND VPFPA.
  ENDLOOP.
* LOOP AT KMVER_OLD.                                       "YWWK005859
*   MOVE-CORRESPONDING KMVER_OLD TO KMVER.                 "YWWK005859
*   APPEND KMVER.                                          "YWWK005859
* ENDLOOP.                                                 "YWWK005859
  CLEAR INDEX.
  LOOP AT ROT_OLD.
    MOVE-CORRESPONDING ROT_OLD TO ROT.
    ADD 1 TO INDEX.
    ROT-LINE = INDEX.
    IF NOT KOPF-WAERS IS INITIAL.
      ROT-WAERS = KOPF-WAERS.
    ELSE.
*     IF SY-TABIX = 1 AND WAEHRUNGEN_GLEICH IS INITIAL.   "YWWK005859
*       PERFORM GET_WAERS.                                "YWWK005859
*     ENDIF.                                              "YWWK005859
      ROT-WAERS = ROT_WAERS.
    ENDIF.
    APPEND ROT.
  ENDLOOP.
* letzten Aenderer festhalten.
  AEND-DATUM = SY-DATUM.
  AEND-UNAME = SY-UNAME.
  AEND-REPID = SY-REPID.
  AEND-UZEIT = SY-UZEIT.
  MOVE-CORRESPONDING STATU TO AEND.
  INSERT AEND INDEX 1.

  PERFORM EXPORT_TE USING CLIENT.

ENDFORM.

*---------------------------------------------------------------------*
*       FORM EXPORT_TE                                                *
*---------------------------------------------------------------------*
*  -->  CLIENT                                                        *
*---------------------------------------------------------------------*
FORM EXPORT_TE USING VALUE(CLIENT).
* kopf-morei = '01'.                                     "QIZTestcoding
  IF TESTL IS INITIAL.
* QIZKXXXXXX Delete entfernt Anfang...
*    TE-KEY_OLD(8) = '00002307'.                         "WWW
*    DELETE FROM PCL1 CLIENT SPECIFIED
*                WHERE RELID = 'ZA'    "WWW
**               where relid = 'TE'
*                  AND SRTFD = TE-KEY_OLD
**                 and srtf2 = '00'.                     "QIZKXXXXXX
*                  AND SRTF2 = '0         '.             "QIZKXXXXXX
*    TE-KEY_OLD(8) = XPERNR.                             "WWW
* QIZKXXXXXX Delete entfernt Ende...

    PERFORM RP-EXP-C1-TE USING CLIENT SUBRC.
    TE_CONVERTED = TE_CONVERTED + 1.
    IF SUBRC IS INITIAL.
      IF PROTK EQ 'X'.
        WRITE: / 'Converted TE-Cluster..............:'(002).
        WRITE:  TE-KEY-PERNR, TE-KEY-REINR, TE-KEY-PDVRS.
      ENDIF.
    ENDIF.
  ELSE.
    IF PROTK EQ 'X'.
      WRITE: / 'Test: Converted TE-Cluster........:'(003).
      WRITE:  TE-KEY-PERNR, TE-KEY-REINR, TE-KEY-PDVRS.
    ENDIF.
  ENDIF.
  DETAIL.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM IMPORT_TS                                                *
*---------------------------------------------------------------------*
*  -->  CLIENT                                                        *
*  -->  GO_ON                                                         *
*---------------------------------------------------------------------*
FORM IMPORT_TS USING VALUE(CLIENT) GO_ON.
  CLEAR:   GO_ON.
  CLEAR:   OTS-VERSION, KMSUM.
  REFRESH: KMSUM.

  TS-KEY-PERNR = TE-KEY-PERNR.
  PERFORM RP-IMP-C1-TS USING CLIENT SUBRC.

  IF SUBRC NE 0.
    TS_ERROR = TS_ERROR + 1.           "fehlerhaftes TS-Cluster
*   WRITE: / 'Fehler beim Einlesen des TS_Clusters:'(E01),
*            TS-KEY-PERNR.
  ELSE.
    COUNTER_TS = COUNTER_TS + 1.    "selekt. TS-Clstr zählen QIZKXXXXXX
    DESCRIBE TABLE KMSUM LINES NUMBER_OF_LINES.                   "DDDD
    IF NOT ( NUMBER_OF_LINES IS INITIAL ).
*     counter_ts = counter_ts + 1.  "selekt. TS-Clstr zählen QIZKXXXXXX
      GO_ON = 'X'.
      IF PROTK EQ 'X'.
        SKIP.
      ENDIF.
    ENDIF.
  ENDIF.

ENDFORM.

*---------------------------------------------------------------------*
*       FORM CONVERT_TS                                               *
*---------------------------------------------------------------------*
*  -->  CLIENT                                                        *
*  -->  GO_ON                                                         *
*---------------------------------------------------------------------*
FORM CONVERT_TS USING VALUE(CLIENT) GO_ON.
  CHECK GO_ON EQ 'X'.
  COMMIT_COUNTER = COMMIT_COUNTER + 1.          "Zähler für COMMIT WORK
  TS_TO_CONVERT = TS_TO_CONVERT + 1.
  PERFORM FILL_KMSUM USING CLIENT.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM FILL_kmsum                                               *
*---------------------------------------------------------------------*
*  -->  CLIENT_TS                                                     *
*---------------------------------------------------------------------*
FORM FILL_KMSUM USING VALUE(CLIENT).
  SUMMARY.
  IF TESTL IS INITIAL.
    PERFORM UPDATE_KMSUM USING CLIENT SUBRC.
    TS_CONVERTED = TS_CONVERTED + 1.
    IF SUBRC IS INITIAL.
      IF PROTK EQ 'X'.
        WRITE: / 'Converted TS-Cluster..............:'(004).
*       WRITE:  TS-KEY-PERNR.
      ENDIF.
    ENDIF.
  ELSE.
    IF PROTK EQ 'X'.
      WRITE: / 'Test: Converted TS-Cluster........:'(005).
*     WRITE:  TS-KEY-PERNR.
    ENDIF.
  ENDIF.
  DETAIL.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM RP-IMP-C1-TE                                             *
*---------------------------------------------------------------------*
*  -->  CLIENT_TE                                                     *
*  -->  SUBRC                                                         *
*---------------------------------------------------------------------*
FORM RP-IMP-C1-TE USING VALUE(CLIENT_TE) SUBRC.
  IMPORT TE-VERSION TO OTE-VERSION
         KOPF
         STATU
         BELEG
         EXBEL
         ABZUG
         ZIEL
         ZWECK
         KONTI
         VSCH
         KMVER TO KMVER_OLD
         PAUFA
         UEBPA
         BELER
         VPFPS TO VPFPS_OLD
         VPFPA TO VPFPA_OLD
         ROT TO ROT_OLD
*        RPRIV
         RUW
         AEND TO AEND_OLD
         KOSTR
         KOSTZ
         KOSTB
         KOSTK
         USER
  FROM DATABASE PCL1(TE) CLIENT CLIENT_TE ID TE-KEY_OLD. "WWW
* from database pcl1(za) client client_te id te-key_old. "testcoding
  SUBRC = SY-SUBRC.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM RP-EXP-C1-TE                                             *
*---------------------------------------------------------------------*
*  -->  CLIENT_TE                                                     *
*  -->  SUBRC                                                         *
*---------------------------------------------------------------------*
FORM RP-EXP-C1-TE USING VALUE(CLIENT_TE) SUBRC.
  PCL1-AEDTM = SY-DATUM.
  PCL1-UNAME = SY-UNAME.
  PCL1-PGMID = SY-REPID.
  PCL1-VERSN = '03'.
  EXPORT TE-VERSION
         STATU
         BELEG
         EXBEL
         ABZUG
         ZIEL
         ZWECK
         KONTI
         VSCH
         KMVER
         TRANSPORT
         PASSENGERS
         RET_JOURNEY
         ABSENCE
         PAUFA
         UEBPA
         BELER
         VPFPS
         VPFPA
         ROT
         RUW
         AEND
         KOSTR
         KOSTZ
         KOSTB
         KOSTK
         V0SPLIT
         USER
  TO DATABASE PCL1(TE) CLIENT CLIENT_TE ID TE-KEY.
  SUBRC = SY-SUBRC.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM RP-IMP-C1-TS                                             *
*---------------------------------------------------------------------*
*  -->  CLIENT_TS                                                     *
*  -->  SUBRC                                                         *
*---------------------------------------------------------------------*
FORM RP-IMP-C1-TS USING VALUE(CLIENT_TS) SUBRC.
  IMPORT TS-VERSION TO OTS-VERSION
*        REISEN
         KMSUM
  FROM DATABASE PCL1(TS) CLIENT CLIENT_TS ID TS-KEY.   "WWW
* from database pcl1(zb) client client_ts id ts-key.   "QIZTestcoding
  SUBRC = SY-SUBRC.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM update_kmsum                                             *
*---------------------------------------------------------------------*
*  -->  CLIENT_TS                                                     *
*  -->  SUBRC                                                         *
*---------------------------------------------------------------------*
FORM UPDATE_KMSUM USING VALUE(CLIENT_TS) SUBRC.
  LOOP AT KMSUM.
    MOVE-CORRESPONDING KMSUM TO PTRV_KMSUM.
    PTRV_KMSUM-PERNR = TS-KEY-PERNR.
    PTRV_KMSUM-MANDT = CLIENT_TS.
*   insert ptrv_kmsum client specified.                     "QIZKXXXXXX
*   insert ptrv_kmsum into t_kmsum.             "QIZKXXXXXX "YWWK015659
    CLEAR T_KMSUM.                                          "YWWK015659
    T_KMSUM = PTRV_KMSUM.                                   "YWWK015659
    APPEND T_KMSUM.                                         "YWWK015659
  ENDLOOP.
* TS-Cluster wird am Ende gelöscht.                         "QIZKXXXXXX
* delete pcl1 client specified.                             "QIZKXXXXXX
ENDFORM.

*---------------------------------------------------------------------*
*     FORM INIT_SORTFIELDS                                            *
*---------------------------------------------------------------------*
FORM INIT_SORTFIELDS.

  DATA: LIN TYPE P.

* QIZKXXXXXX begin...
* srtfdhigh-hex+00(20) =  'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'.
* srtfdhigh-hex+20(20) =  'FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'.
  SRTFDHIGH-CHAR+00(20) = '9999999999999999999999999999999999999999'.
  SRTFDHIGH-CHAR+20(20) = '9999999999999999999999999999999999999999'.
* QIZKXXXXXX end....

* QIZTestcoding
* describe table selpernr lines lin.
* if lin = 1.
*   read table selpernr index 1.
*   if selpernr-sign   = 'I' and
*      selpernr-option = 'EQ'.
*     srtfdlow+0(8)  = selpernr-low.
*     srtfdhigh+0(8) = selpernr-low.
*   endif.
*   if selpernr-sign   = 'I' and
*      selpernr-option = 'BT'.
*     srtfdlow+0(8)  = selpernr-low.
*     srtfdhigh+0(8) = selpernr-high.
*   endif.
* endif.
* srtfdlow+0(8)  = xpernr.                               "QIZTestcoding
* srtfdhigh+0(8) = zpernr.                               "QIZTestcoding

ENDFORM.

*---------------------------------------------------------------------*
*       FORM STATISTICS                                               *
*---------------------------------------------------------------------*
FORM STATISTICS USING VALUE(CLIENT) TE_TS.
  IF NOT ( CLIENT IS INITIAL ).        "Es gibt TE/TS-Cluster.
    CASE TE_TS.
      WHEN 'TE'.
*       SKIP.
*       PERFORM ZENTRIEREN USING 'TE-Clusterumsetzung'(PTE) ZEILE.
*       SUMMARY. WRITE: / ZEILE. DETAIL.
*       ULINE.
*       WRITE: / 'Selektierte TE-Cluster...........:'(P10).
*       WRITE:  COUNTER_TE.
        CLEAR MESS_TAB.
        MESS_TAB-LEVEL    = 3.
        MESS_TAB-SEVERITY = ' '.
        MESS_TAB-LANGU    = 'E'.
        MESS_TAB-AG       = '56'.
        MESS_TAB-MSGNR    = '669'.     "Selected TE-Cluster
        MESS_TAB-NEWOBJ   = ' '.
        MESS_TAB-VAR1 = CLIENT.
        MESS_TAB-VAR2 = COUNTER_TE.
        MESS_TAB-VAR3 = SPACE.
        MESS_TAB-VAR4 = SPACE.
        APPEND MESS_TAB.
*       WRITE: / 'dabei berührte Personalnummern...:'(P11).
*       WRITE:  COUNTER_PERNR_TE.
*       WRITE: / 'Bereits umgesetzte TE-Cluster....:'(P13).
*       WRITE:  ALREADY_CONVERTED_TE.
*       SKIP.
        CLEAR MESS_TAB.
        MESS_TAB-LEVEL    = 3.
        MESS_TAB-SEVERITY = ' '.
        MESS_TAB-LANGU    = 'E'.
        MESS_TAB-AG       = '56'.
        MESS_TAB-MSGNR    = '670'.     "TE-Cl., already converted
        MESS_TAB-NEWOBJ   = ' '.
        MESS_TAB-VAR1 = CLIENT.
        MESS_TAB-VAR2 = ALREADY_CONVERTED_TE.
        MESS_TAB-VAR3 = SPACE.
        MESS_TAB-VAR4 = SPACE.
        APPEND MESS_TAB.
*       WRITE: / 'Umzusetzende TE-Cluster..........:'(P14).
*       WRITE:  TE_TO_CONVERT.
        CLEAR MESS_TAB.
        MESS_TAB-LEVEL    = 3.
        MESS_TAB-SEVERITY = ' '.
        MESS_TAB-LANGU    = 'E'.
        MESS_TAB-AG       = '56'.
        MESS_TAB-MSGNR    = '671'.     "TE-Cluster, to convert
        MESS_TAB-NEWOBJ   = ' '.
        MESS_TAB-VAR1 = CLIENT.
        MESS_TAB-VAR2 = TE_TO_CONVERT.
        MESS_TAB-VAR3 = SPACE.
        MESS_TAB-VAR4 = SPACE.
        APPEND MESS_TAB.
*       WRITE: / 'Umgesetzte TE-Cluster............:'(P15).
*       WRITE:  TE_CONVERTED.
*       SKIP.
        CLEAR MESS_TAB.
        MESS_TAB-LEVEL    = 3.
        MESS_TAB-SEVERITY = ' '.
        MESS_TAB-LANGU    = 'E'.
        MESS_TAB-AG       = '56'.
        MESS_TAB-MSGNR    = '672'.     "Converted TE-Cluster
        MESS_TAB-NEWOBJ   = ' '.
        MESS_TAB-VAR1 = CLIENT.
        MESS_TAB-VAR2 = TE_CONVERTED.
        MESS_TAB-VAR3 = SPACE.
        MESS_TAB-VAR4 = SPACE.
        APPEND MESS_TAB.
*       WRITE: / 'fehlerhaft eingelesene TE-Cluster:'(P12).
*       WRITE:  TE_ERROR.
*       SKIP.

* alle Zähler fuer neuen Mandanten zurücksetzen.
        CLEAR COUNTER_TE.
        CLEAR TE_ERROR.
        CLEAR TE_TO_CONVERT.
        CLEAR TE_CONVERTED.
        CLEAR ALREADY_CONVERTED_TE.
        CLEAR COUNTER_PERNR_TE.
      WHEN 'TS'.
*       PERFORM ZENTRIEREN USING 'TS-Clusterumsetzung'(PTS) ZEILE.
*       SUMMARY. WRITE: / ZEILE. DETAIL.
*       ULINE.
*       WRITE: / 'Selektierte TS-Cluster...........:'(P20).
*       WRITE:  COUNTER_TS.
        CLEAR MESS_TAB.
        MESS_TAB-LEVEL    = 3.
        MESS_TAB-SEVERITY = ' '.
        MESS_TAB-LANGU    = 'E'.
        MESS_TAB-AG       = '56'.
        MESS_TAB-MSGNR    = '673'.     "Selected TS-Cluster
        MESS_TAB-NEWOBJ   = ' '.
        MESS_TAB-VAR1 = CLIENT.
        MESS_TAB-VAR2 = COUNTER_TS.
        MESS_TAB-VAR3 = SPACE.
        MESS_TAB-VAR4 = SPACE.
        APPEND MESS_TAB.
*       WRITE: / 'Bereits umgesetzte TS-Cluster....:'(P22).
*       WRITE:  ALREADY_CONVERTED_TS.
        CLEAR MESS_TAB.
        MESS_TAB-LEVEL    = 3.
        MESS_TAB-SEVERITY = ' '.
        MESS_TAB-LANGU    = 'E'.
        MESS_TAB-AG       = '56'.
        MESS_TAB-MSGNR    = '674'.     "TS-Cl., already converted
        MESS_TAB-NEWOBJ   = ' '.
        MESS_TAB-VAR1 = CLIENT.
        MESS_TAB-VAR2 = ALREADY_CONVERTED_TS.
        MESS_TAB-VAR3 = SPACE.
        MESS_TAB-VAR4 = SPACE.
        APPEND MESS_TAB.
*       SKIP.
*       WRITE: / 'Umzusetzende TS-Cluster..........:'(P23).
*       WRITE:  TS_TO_CONVERT.
        CLEAR MESS_TAB.
        MESS_TAB-LEVEL    = 3.
        MESS_TAB-SEVERITY = ' '.
        MESS_TAB-LANGU    = 'E'.
        MESS_TAB-AG       = '56'.
        MESS_TAB-MSGNR    = '675'.     "TS-Cluster, to convert
        MESS_TAB-NEWOBJ   = ' '.
        MESS_TAB-VAR1 = CLIENT.
        MESS_TAB-VAR2 = TS_TO_CONVERT.
        MESS_TAB-VAR3 = SPACE.
        MESS_TAB-VAR4 = SPACE.
        APPEND MESS_TAB.
*       WRITE: / 'Umgesetzte TS-Cluster............:'(P24).
*       WRITE:  TS_CONVERTED.
*       SKIP.
        CLEAR MESS_TAB.
        MESS_TAB-LEVEL    = 3.
        MESS_TAB-SEVERITY = ' '.
        MESS_TAB-LANGU    = 'E'.
        MESS_TAB-AG       = '56'.
        MESS_TAB-MSGNR    = '676'.     "Converted TS-Cluster
        MESS_TAB-NEWOBJ   = ' '.
        MESS_TAB-VAR1 = CLIENT.
        MESS_TAB-VAR2 = TS_CONVERTED.
        MESS_TAB-VAR3 = SPACE.
        MESS_TAB-VAR4 = SPACE.
        APPEND MESS_TAB.
*       WRITE: / 'fehlerhaft eingelesene TS-Cluster:'(P21).
*       WRITE:  TS_ERROR.
* alle Zähler fuer neuen Mandanten zurücksetzen.
        CLEAR COUNTER_TS.
        CLEAR TS_ERROR.
        CLEAR TS_TO_CONVERT.
        CLEAR TS_CONVERTED.
        CLEAR ALREADY_CONVERTED_TS.
    ENDCASE.
  ELSE.                                "Keine TE/TS-Cluster vorhanden
    CASE TE_TS.
      WHEN 'TE'.
        CLEAR MESS_TAB.
        MESS_TAB-LEVEL    = 3.
        MESS_TAB-SEVERITY = ' '.
        MESS_TAB-LANGU    = 'E'.
        MESS_TAB-AG       = '56'.
        MESS_TAB-MSGNR    = '677'.     "No trips found.
        MESS_TAB-NEWOBJ   = ' '.
        MESS_TAB-VAR1 = SPACE.
        MESS_TAB-VAR2 = SPACE.
        MESS_TAB-VAR3 = SPACE.
        MESS_TAB-VAR4 = SPACE.
        APPEND MESS_TAB.
      WHEN 'TS'.
* Meldung bereits bei  "WHEN 'TE'" ausgegeben.
    ENDCASE.
  ENDIF.
ENDFORM.

DATA: BEGIN OF PERMO_DATES OCCURS 100,                     "QIZKXXXXXX
         MANDT LIKE T549Q-MANDT,                           "QIZKXXXXXX
         PERMO LIKE T549Q-PERMO,                           "QIZKXXXXXX
         PABRJ LIKE T549Q-PABRJ,                           "QIZKXXXXXX
         PABRP LIKE T549Q-PABRP,                           "QIZKXXXXXX
         BEGDA LIKE T549Q-BEGDA,                           "QIZKXXXXXX
         ENDDA LIKE T549Q-ENDDA,                           "QIZKXXXXXX
       END OF PERMO_DATES.                                 "QIZKXXXXXX

DATA: BEGIN OF PERMO_DATES_KEY,
        MANDT LIKE T549Q-MANDT,                            "QIZKXXXXXX
        PERMO LIKE T549Q-PERMO,
        PABRJ LIKE T549Q-PABRJ,
        PABRP LIKE T549Q-PABRP,
      END OF PERMO_DATES_KEY.

*---------------------------------------------------------------------*
*       FORM BUILD_TAB                                                *
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM BUILD_TAB.
  CLEAR PERMO_DATES.
  REFRESH PERMO_DATES.
  SELECT MANDT PERMO PABRJ PABRP BEGDA ENDDA               "QIZKXXXXXX
         FROM T549Q CLIENT SPECIFIED                       "QIZKXXXXXX
         INTO TABLE PERMO_DATES.
    sort permo_dates by mandt permo pabrj pabrp.                           "QIZKXXXXXX
*        where ( mandt eq '000' or mandt eq '003' ).    "QIZTestcoding
* select * from t549q client specified                     "QIZKXXXXXX
*          into corresponding fields of permo_dates        "QIZKXXXXXX
*          where mandt = pcl1-client.                      "QIZKXXXXXX
*   append permo_dates.                                    "QIZKXXXXXX
* endselect.                                               "QIZKXXXXXX
ENDFORM.

*---------------------------------------------------------------------*
*       FORM READ_TAB                                                 *
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM READ_TAB.
* Für-Periode...
  PERMO_DATES_KEY-MANDT = IPCL1-CLIENT.                     "QIZKXXXXXX
  PERMO_DATES_KEY-PERMO = KOPF-PERM1.
  PERMO_DATES_KEY-PABRJ = KOPF-ABRJ1.
  PERMO_DATES_KEY-PABRP = KOPF-ABRP1.
  READ TABLE PERMO_DATES WITH KEY PERMO_DATES_KEY BINARY SEARCH.
  PTRV_PERIO-BEGP1 = PERMO_DATES-BEGDA.
  PTRV_PERIO-ENDP1 = PERMO_DATES-ENDDA.
* IN-Periode...
  PERMO_DATES_KEY-MANDT = IPCL1-CLIENT.                     "QIZKXXXXXX
  PERMO_DATES_KEY-PERMO = KOPF-PERM2.
  PERMO_DATES_KEY-PABRJ = KOPF-ABRJ2.
  PERMO_DATES_KEY-PABRP = KOPF-ABRP2.
  READ TABLE PERMO_DATES WITH KEY PERMO_DATES_KEY BINARY SEARCH.
  PTRV_PERIO-BEGP2 = PERMO_DATES-BEGDA.
  PTRV_PERIO-ENDP2 = PERMO_DATES-ENDDA.
ENDFORM.

DATA: BEGIN OF X0001 OCCURS 10,
        BEGDA LIKE PA0001-BEGDA,
        ENDDA LIKE PA0001-ENDDA,
        BUKRS LIKE PA0001-BUKRS,
        ABKRS LIKE PA0001-ABKRS,
      END OF X0001.

DATA: BEGIN OF X_0001,
        BEGDA LIKE PA0001-BEGDA,
        ENDDA LIKE PA0001-ENDDA,
        BUKRS LIKE PA0001-BUKRS,
        ABKRS LIKE PA0001-ABKRS,
      END OF X_0001.

DATA: X0001_INDEX LIKE SY-TABIX.

*---------------------------------------------------------------------*
*       FORM READ_0001                                                *
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM READ_0001 USING PERNR.
  CLEAR X0001.
  REFRESH X0001.
  CLEAR X_0001.
  CLEAR X0001_INDEX.
  SELECT BEGDA ENDDA BUKRS ABKRS FROM PA0001 CLIENT SPECIFIED
         INTO CORRESPONDING FIELDS OF X0001
*        where mandt = pcl1-client                         "QIZKXXXXXX
         WHERE MANDT = IPCL1-CLIENT                        "QIZKXXXXXX
         AND   PERNR = PERNR.
    IF X0001-ABKRS = X_0001-ABKRS AND X0001-BUKRS = X_0001-BUKRS.
      X0001-BEGDA = X_0001-BEGDA.
      MODIFY X0001 INDEX X0001_INDEX.
    ELSE.
      APPEND X0001.
      ADD 1 TO X0001_INDEX.
    ENDIF.
    X_0001 = X0001.
  ENDSELECT.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM GET_WAERS                                                *
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
FORM GET_WAERS.
  PERFORM GET_BUKRS_ABKRS USING KOPF-DATV1.
  READ TABLE T_001 WITH KEY MANDT = IPCL1-CLIENT BUKRS = BUK. "WWK005859
  IF SY-SUBRC = 0.
    ROT_WAERS = T_001-WAERS.
  ELSE.
    CLEAR ROT_WAERS.
  ENDIF.
ENDFORM.

*---------------------------------------------------------------------*
*       FORM FILL_T_001                                               *
*---------------------------------------------------------------------*
* QIZKXXXXX Routine liest T001 mandantenübergreifend                  *
*---------------------------------------------------------------------*
FORM FILL_T_001.
  CLEAR T_001.
  REFRESH T_001.
  SELECT MANDT BUKRS WAERS FROM T001 CLIENT SPECIFIED
         INTO TABLE T_001.
*        where mandt eq sy-mandt.                       "QIZTestcoding
ENDFORM.

*---------------------------------------------------------------------*
*       FORM CURRENCIES_ARE_EQUAL
*---------------------------------------------------------------------*
* QIZKXXXXXX Neue Routine
* Haben alle Buchungskreise eines Mandanten gleiche Währung?
*---------------------------------------------------------------------*
FORM CURRENCIES_ARE_EQUAL USING WAEHRUNGEN_GLEICH.
  CLEAR OLD_WAERS.
  WAEHRUNGEN_GLEICH = 'X'.
  LOOP AT T_001 WHERE MANDT EQ IPCL1-CLIENT.
    IF T_001-WAERS NE OLD_WAERS AND NOT OLD_WAERS IS INITIAL.
      WAEHRUNGEN_GLEICH = ' '.
    ENDIF.
    OLD_WAERS = T_001-WAERS.
  ENDLOOP.
  IF WAEHRUNGEN_GLEICH = 'X'.                            "YWWK005859
    ROT_WAERS = T_001-WAERS.                             "YWWK005859
  ENDIF.                                                 "YWWK005859
ENDFORM.

*---------------------------------------------------------------------*
*       FORM GET_BUKRS_ABKRS                                          *
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
*  -->  DAT                                                           *
*---------------------------------------------------------------------*
FORM GET_BUKRS_ABKRS USING DAT.
  LOOP AT X0001 WHERE BEGDA LE DAT AND ENDDA GE DAT.
    BUK = X0001-BUKRS.
    ABK = X0001-ABKRS.
  ENDLOOP.
  IF SY-SUBRC NE 0.
    CLEAR BUK.
    CLEAR ABK.
  ENDIF.
ENDFORM.