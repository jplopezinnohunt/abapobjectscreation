*******************************************************************
* INCLUDE                           YFFORI10                      *
* TITLE                             International Payment Medium  *
*                                   Include: MT100                *
* AUTHOR                            PWC-AEM                       *
* DATE WRITTEN                      October 2001                  *
* R/3 RELEASE                       4.6C                          *
*******************************************************************
* COPIED FROM                       RFFORI10                      *
* TITLE                             International Payment Medium  *
*                                   Include: MT100                *
*******************************************************************
* USED BY....... < user or usergroups >                           *
*                                                                 *
*                                                                 *
*******************************************************************
* PROGRAM TYPE                      Include                       *
* DEV.CLASS                         YA                            *
* LOGICAL DB                                                      *
*******************************************************************
* CHANGE HISTORY                                                  *
*                                                                 *
* 1. 08/10/2001 PwC, Alain EL MOUCHNINO                 AEM081001 *
*       Modification of call function in order to insert total    *
*       amount with decimals in trailer                           *
* 2. 08/10/2001 PwC, Alain EL MOUCHNINO                 AEM101001 *
*       For PPD : add a counter for line number                   *
* 3. 24/01/2002 PwC, Eric MARTORANA                    EMAR240102 *
*       For SmartLink : Add bank key in tag 59                    *
* 4. 23/12/2002 UNESCO, Alain AHOUNOU                             *
*       For SmartLink : account number in front of the bank key   *
*       when the country of beneficiary's account = DE or AT.     *
*******************************************************************

************************************************************************
* Includebaustein RFFORI10 zum Zahlungsträgerdruckprogramm RFFOM100    *
* Unterprogrammen für den Datenträgeraustausch MT100                   *
* Include RFFORI10, used in the payment print program RFFOM100         *
* with subroutines for MT100                                           *
*                                                                      *
* subroutine                         called by report / in subroutine  *
* -------------------------------------------------------------------  *
* MT100                                                      RFFOM100  *
*                                                                      *
************************************************************************

*----------------------------------------------------------------------*
* FORM MT100                                                           *
*----------------------------------------------------------------------*
* Ausgabe der MT100-Files                                              *
* gerufen von END-OF-SELECTION (RFFOM100)                              *
*----------------------------------------------------------------------*
* program produces MT100-files                                         *
* called by END-OF-SELECTION (RFFOM100)                                *
*----------------------------------------------------------------------*
* keine USING-Parameter                                                *
* no USING-parameters                                                  *
*----------------------------------------------------------------------*
FORM MT100.
*----------------------------------------------------------------------*
* Vorbereitung zum Datenträgeraustausch                                *
* preparations for DME                                                 *
*----------------------------------------------------------------------*
* AEM101001+
  DATA: W_CPT(5) TYPE N.    " counter
* AEM101001+

* Sortieren des Datenbestandes unter Beachtung von Gut-/Lastschrift
* sort of extract considering incoming and outgoing payments
*AHOUNOU05072006
*  DATA: up_crlf(2)          TYPE x VALUE '0D0A',
*    DATA : up_crlf(2)   TYPE C VALUE cl_abap_char_utilities=>newline,
  DATA : UP_CRLF(2)      TYPE C VALUE CL_ABAP_CHAR_UTILITIES=>CR_LF,
*AHOUNOU05072006
      UP_LEN              TYPE I,
      UP_WAERS(3)         TYPE C,
      UP_AUFTR_GEB_1(35),
      UP_AUFTR_GEB_2(35),
      UP_AUFTR_GEB_3(35),
      UP_AUFTR_GEB_4(35),
      UP_ZAHL_EMPF_1(35),
      UP_ZAHL_EMPF_2(35),
      UP_ZAHL_EMPF_3(35),
      UP_ZAHL_EMPF_4(35),
      UP_LFDNR(8) TYPE N,
      UP_FILECNT  TYPE I,
      FLG_UNIX(1) TYPE C,
      _OPEN_FI(1) TYPE C.

*---------------------------------------------------------------------*
  SORT BY
    REGUH-ZBUKR                        "paying company code
    REGUH-UBNKS                        "country of house bank
    REGUH-UBNKY                        "bank key (for sort)
    REGUH-UBNKL                        "bank number of house bank
    REGUH-RZAWE                        "X - incoming payment
    REGUH-UBKNT                        "account number at house bank
    REGUH-ZBNKS                        "country of payee's bank
    REGUH-ZBNKY                        "bank key (for sort)
    REGUH-ZBNKL                        "bank number of payee's bank
    REGUH-ZBNKN                        "account number of payee
    REGUH-LIFNR                        "creditor number
    REGUH-KUNNR                        "debitor number
    REGUH-EMPFG                        "payee is CPD / alternative payee
    REGUH-VBLNR                        "payment document number
    HLP_SORTP1                         "sort field for single items
    HLP_SORTP2                         "sort field for single items
    HLP_SORTP3                         "sort field for single items
    REGUP-BELNR.                       "invoice document number

* Dateiformat bestimmen
  IF T042OFI-FORMT IS INITIAL.
    HLP_DTFOR      = 'MT100'.
    HLP_DTFOR_LONG = 'MT100'.
  ELSE.
    HLP_DTFOR      = T042OFI-FORMT.
    HLP_DTFOR_LONG = T042OFI-FORMT.
  ENDIF.

* Falls kein TemSe-Eintrag und falls kein Dateiname angegeben, Namen
* der sequentiellen Files vorbelegen: DTAUS0.Datum.Uhrzeit.lfdNr
* If no file-name is specified and no name will be generated later
* (because of TemSe), a new name is generated here: DTAUS0.Date.Time.nn
  IF PAR_UNIX NE SPACE.
    FLG_UNIX = 1.
  ENDIF.
  IF HLP_TEMSE NA PAR_DTYP.            "Kein TemSe-Format / No TemSe
    IF PAR_UNIX EQ SPACE.              "kein Name   / unspecified name
      PAR_UNIX    = HLP_DTFOR.
      PAR_UNIX+6  = '.'.
      WRITE SY-DATUM TO PAR_UNIX+7(6) DDMMYY.
      PAR_UNIX+13 = '.'.
      PAR_UNIX+14 = SY-UZEIT.
      PAR_UNIX+20 = '.'.
    ELSE.
      IF PAR_CBXX IS INITIAL.          "Einzelzahlung
        CLEAR UP_FILECNT.
        LOOP AT DTA_FILECNT.
          UP_FILECNT = UP_FILECNT + DTA_FILECNT-ANZAHL.
        ENDLOOP.
        DTA_FILECNT-ANZAHL = UP_FILECNT.
      ELSE.                            "Sammelzahlung
        DESCRIBE TABLE DTA_FILECNT LINES DTA_FILECNT-ANZAHL.
      ENDIF.

      CALL FUNCTION 'GET_SHORTKEY_FOR_FEBKO'
        EXPORTING
          I_TNAME             = 'MT100'
          I_ANZNR             = DTA_FILECNT-ANZAHL
        IMPORTING
          E_KUKEY             = UP_LFDNR
        EXCEPTIONS
          FEBKEY_UPDATE_ERROR = 1.

      UP_LFDNR = UP_LFDNR - DTA_FILECNT-ANZAHL.
      IF SY-SUBRC = 1.
        IF SY-BATCH EQ SPACE.
          MESSAGE A228 WITH 'FEBKEY'.
        ELSE.
          MESSAGE S228 WITH 'FEBKEY'.
          STOP.
        ENDIF.
      ENDIF.
    ENDIF.
  ENDIF.
  CNT_FILENR = 0.

  CALL FUNCTION 'NAMETAB_GET'
    EXPORTING
      TABNAME = 'DTAM100'
    TABLES
      NAMETAB = NAMETAB.

*----------------------------------------------------------------------*
* Abarbeiten der extrahierten Daten                                    *
* loop at extracted data                                               *
*----------------------------------------------------------------------*
* AEM101001*********+
  CLEAR W_CPT.
* AEM101001*********+
  LOOP.

*-- Neuer zahlender Buchungskreis --------------------------------------
*-- new paying company code --------------------------------------------
    AT NEW REGUH-ZBUKR.

      PERFORM BUCHUNGSKREIS_DATEN_LESEN.

    ENDAT.                             "AT NEW REGUH-ZBUKR


*-- Neue Hausbank ------------------------------------------------------
*-- new house bank -----------------------------------------------------
    AT NEW REGUH-UBNKL.

      PERFORM HAUSBANK_DATEN_LESEN.
      IF NOT PAR_CBXX IS INITIAL.
        PERFORM ZUSATZFELD_FUELLEN USING *REGUT-DTKEY 'D  '.
        IF HLP_TEMSE NA PAR_DTYP AND   "Kein TemSe-Format / No TemSe
           FLG_UNIX NE SPACE.          "kein Name   / unspecified name
          PERFORM DATEI_OEFFNEN_1 USING UP_LFDNR.
          UP_LFDNR = UP_LFDNR + 1.
        ELSE.
          PERFORM DATEI_OEFFNEN.
        ENDIF.

*------ Prepare Open FI und User-Exit for multi payments
        CLEAR DTA_FILECNT.
        DTA_FILECNT-ZBUKR = REGUH-ZBUKR.
        DTA_FILECNT-UBNKS = REGUH-UBNKS.
        DTA_FILECNT-UBNKL = REGUH-UBNKL.
        READ TABLE DTA_FILECNT.
        DTAM100S-S00   = DTA_FILECNT-SZBNKN.
        DTAM100S-S01   = DTA_FILECNT-SVBETR.
        DTAM100S-S02   = DTA_FILECNT-ANZAHL.
        DTAM100S-S03   = HLP_RESULTAT.
        DTAM100S-S04   = PAR_SBNK.     "sending bank of MT101
        DTAM100H-XCRLF_SUPP = SPACE.

*       Open FI / BTE (multi payments)
        IF PAR_MOFI NE SPACE.
          IF NOT T042OFI-XACTIVE1 IS INITIAL.
            REFRESH TAB_SUM_PER_CURRENCY.
            LOOP AT TAB_SUM_PER_CURRENCY_EXT
                               WHERE ZBUKR EQ REGUH-ZBUKR
                                 AND UBNKS EQ REGUH-UBNKS
                                 AND UBNKY EQ REGUH-UBNKY.
              TAB_SUM_PER_CURRENCY = TAB_SUM_PER_CURRENCY_EXT.
              APPEND TAB_SUM_PER_CURRENCY.
              DELETE TAB_SUM_PER_CURRENCY_EXT.
            ENDLOOP.
* AEM081001*********
            CALL FUNCTION 'Y_FI_PERFORM_00002010_P'
*            CALL FUNCTION 'OPEN_FI_PERFORM_00002010_P'
* AEM081001*********
                 EXPORTING
                      I_FORMAT           = T042OFI-FORMT
                      I_REGUH            = REGUH
                      I_DTAM100S         = DTAM100S
                      I_DTAM100H         = DTAM100H
                      I_CBXX             = PAR_CBXX
* AEM241001+++++++++++++++++++
*{   REPLACE        D11K938454                                        1
*\                      i_crsupp           = P_CRSUPP
                      I_CRSUPP           = P_CRSUPP
                      I_DATE             = PAR_DATE
*}   REPLACE
* AEM241001+++++++++++++++++++
                 IMPORTING
                      E_DTAM100H         = DTAM100H
                 TABLES
                      T_SUM_PER_CURRENCY = TAB_SUM_PER_CURRENCY
                 EXCEPTIONS
                      NO_ADD_ON_FOUND    = 1.
            IF SY-SUBRC NE 0.
              MESSAGE ID SY-MSGID TYPE 'S'  NUMBER SY-MSGNO
                      WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
            ELSE.
              _OPEN_FI = 'X'.
            ENDIF.
          ENDIF.
        ENDIF.

*       User-Exit for header (multi payments)
        PERFORM EXIT_901(RFFOEXIT)
                USING REGUH
                      DTAM100S
                      DTAM100H
                      PAR_CBXX
                      UP_USREX.
        IF NOT UP_USREX IS INITIAL OR  "modified by user
           NOT _OPEN_FI IS INITIAL.
           *REGUT-USREX = UP_USREX.
          CLEAR: UP_USREX, _OPEN_FI.
          IF DTAM100H-H01 IS INITIAL.
            UP_LEN = STRLEN( DTAM100H-H00 ).
          ELSE.
            UP_LEN = DTAM100H-H01.
          ENDIF.
          IF UP_LEN GT 0.
            IF NOT DTAM100H-XCRLF_SUPP IS INITIAL.
              PERFORM STORE_ON_FILE USING DTAM100H-H00(UP_LEN).
            ELSE.
              PERFORM STORE_ON_FILE USING:
                      DTAM100H-H00(UP_LEN), UP_CRLF.
            ENDIF.
          ENDIF.
          CLEAR DTAM100H.
        ENDIF.

      ENDIF.

*     Lesen des Default-Weisungsschlüssels der Hausbank
*     Read parameters in T012D
      SELECT SINGLE * FROM T012D
        WHERE BUKRS EQ REGUH-ZBUKR
        AND   HBKID EQ REGUH-HBKID.
      IF SY-SUBRC NE 0.
        CLEAR T012D.
      ENDIF.

      CLEAR SUM_REGUT.

    ENDAT.


*-- Neuer Zahlweg ------------------------------------------------------
*-- new payment method -------------------------------------------------
    AT NEW REGUH-RZAWE.

      PERFORM ZAHLWEG_DATEN_LESEN.

    ENDAT.


*-- Neue Empfängerbank -------------------------------------------------
*-- new bank of payee --------------------------------------------------
    AT NEW REGUH-ZBNKL.

      PERFORM EMPFBANK_DATEN_LESEN.

    ENDAT.


*-- Neue Kontonummer bei der Empfängerbank------------------------------
*-- new bank account number of payee -----------------------------------
    AT NEW REGUH-ZBNKN.

      HLP_ZBNKN = REGUH-ZBNKN.

    ENDAT.


*-- Neue Zahlungsbelegnummer -------------------------------------------
*-- new payment document number ----------------------------------------
    AT NEW REGUH-VBLNR.

      IF PAR_CBXX IS INITIAL.          "Einzelzahlung
        PERFORM ZUSATZFELD_FUELLEN USING *REGUT-DTKEY 'D  '.
        IF HLP_TEMSE NA PAR_DTYP AND   "Kein TemSe-Format / No TemSe
           FLG_UNIX NE SPACE.          "kein Name   / unspecified name
          PERFORM DATEI_OEFFNEN_1 USING UP_LFDNR.
          UP_LFDNR = UP_LFDNR + 1.
        ELSE.
          PERFORM DATEI_OEFFNEN.
        ENDIF.
        DTAM100H-XCRLF_SUPP = SPACE.

*------ Open FI / BTE and User-Exit for single payments
*       Update tab_sum_per_currency for single payments
        REFRESH TAB_SUM_PER_CURRENCY.
        TAB_SUM_PER_CURRENCY-WAERS = REGUH-WAERS.
        TAB_SUM_PER_CURRENCY-RWBTR = REGUH-RWBTR.
        APPEND TAB_SUM_PER_CURRENCY.
*       Update DTAM100S for single payments
        DTAM100S-S00 = REGUH-ZBNKN.
        PERFORM DTA_VORKOMMA(RFFOD__L) USING REGUH-WAERS REGUH-RWBTR.
        DTAM100S-S01 = SPELL-NUMBER.
        DTAM100S-S02 = 1.
        DTAM100S-S03 = HLP_RESULTAT.
        DTAM100S-S04 = PAR_SBNK.       "Sending bank of MT101

*       Open-FI / BTE (single payments)
        IF PAR_MOFI NE SPACE.
          IF NOT T042OFI-XACTIVE1 IS INITIAL.
* AEM081001*********
            CALL FUNCTION 'Y_FI_PERFORM_00002010_P'
*            CALL FUNCTION 'OPEN_FI_PERFORM_00002010_P'
* AEM081001*********
                 EXPORTING
                      I_FORMAT           = T042OFI-FORMT
                      I_REGUH            = REGUH
                      I_DTAM100S         = DTAM100S
                      I_DTAM100H         = DTAM100H
                      I_CBXX             = PAR_CBXX
* AEM241001+++++++++++++++++++
*{   REPLACE        D11K938454                                        2
*\                      i_crsupp           = P_CRSUPP
                      I_CRSUPP           = P_CRSUPP
                      I_DATE             = PAR_DATE
*}   REPLACE
* AEM241001+++++++++++++++++++
                 IMPORTING
                      E_DTAM100H         = DTAM100H
                 TABLES
                      T_SUM_PER_CURRENCY = TAB_SUM_PER_CURRENCY
                 EXCEPTIONS
                      NO_ADD_ON_FOUND    = 1.
            IF SY-SUBRC NE 0.
              MESSAGE ID SY-MSGID TYPE 'S'  NUMBER SY-MSGNO
                      WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
            ELSE.
              _OPEN_FI = 'X'.
            ENDIF.
          ENDIF.
        ENDIF.

*       User-Exit for header (single payments)
        PERFORM EXIT_901(RFFOEXIT)
                USING REGUH
                      DTAM100S
                      DTAM100H
                      PAR_CBXX
                      UP_USREX.
        IF NOT UP_USREX IS INITIAL OR  "modified by user
           NOT _OPEN_FI IS INITIAL.
           *REGUT-USREX = UP_USREX.
          CLEAR: UP_USREX, _OPEN_FI.
          IF DTAM100H-H01 IS INITIAL.
            UP_LEN = STRLEN( DTAM100H-H00 ).
          ELSE.
            UP_LEN = DTAM100H-H01.
          ENDIF.
          IF UP_LEN GT 0.
            IF NOT DTAM100H-XCRLF_SUPP IS INITIAL.
              PERFORM STORE_ON_FILE USING DTAM100H-H00(UP_LEN).
            ELSE.
              PERFORM STORE_ON_FILE USING:
                      DTAM100H-H00(UP_LEN), UP_CRLF.
            ENDIF.
          ENDIF.
          CLEAR DTAM100H.
        ENDIF.

        CLEAR SUM_REGUT.
      ENDIF.

      PERFORM ZAHLUNGS_DATEN_LESEN.
      PERFORM SUMMENFELDER_INITIALISIEREN.
      PERFORM BELEGDATEN_SCHREIBEN.
      SET LANGUAGE HLP_SPRACHE.        " Buchungskreis-/Empfängersprache
      IF SY-SUBRC <> 0.
        SET LANGUAGE SY-LANGU.         " Anmeldesprache
      ENDIF.

*     Verwendungszweck auf Segmenttext untersuchen
*     examine whether note to payee has to be filled with segment text
      FLG_SGTXT = 0.
      IF TEXT-703 CS '&SGTXT'.
        FLG_SGTXT = 1.                 "Global für Segmenttext existiert
      ENDIF.                           "global for segment text exists

*     Weisungsschlüssel lesen
*     Read instruction key
      IF NOT ( T012D-DTAWS IS INITIAL AND REGUH-DTAWS IS INITIAL ).
        PERFORM WEISUNGSSCHLUESSEL_LESEN.
      ELSE.
        CLEAR T015W.
      ENDIF.

      UP_AUFTR_GEB_1  = REGUD-AUST1.   "Name des Auftraggebers
      IF REGUD-ABSTX EQ SPACE.
        UP_AUFTR_GEB_2 = REGUD-AUST2.
        UP_AUFTR_GEB_3 = REGUD-AUST3.
        UP_AUFTR_GEB_4 = REGUD-AUSTO.
      ELSE.
        UP_AUFTR_GEB_2 = REGUD-AUSTO.
        UP_AUFTR_GEB_3 = REGUD-ABSTX.
        UP_AUFTR_GEB_4 = REGUD-ABSOR.
      ENDIF.

      UP_ZAHL_EMPF_1 = REGUH-KOINH.
      IF REGUH-KOINH EQ REGUH-ZNME1 AND
         NOT REGUH-ZNME2 IS INITIAL AND
         HLP_LAUFK NE 'P'.
        UP_ZAHL_EMPF_2 = REGUH-ZNME2.
      ELSE.
        CLEAR UP_ZAHL_EMPF_2.
      ENDIF.
      UP_ZAHL_EMPF_3 = REGUD-ZPFST.
      UP_ZAHL_EMPF_4 = REGUD-ZPLOR.
      CLEAR UP_WSCHL.
*     interne Tabelle DTA_MT100 initialisieren
*     initialize internal table DTA_MT100
      PERFORM MT100_INIT.

*     Interne Tabelle DTA_MT100 füllen
*     fill internal table DTA_MT100
      PERFORM GET_VALUE_DATE.   " Set reguh-valut, if initial
      PERFORM ISOCODE_UMSETZEN USING REGUH-WAERS UP_WAERS.
* AEM111201+
      CLEAR: UP_AUFTR_GEB_3,
             UP_AUFTR_GEB_4.
* AEM111201+
      PERFORM PUT_MT100 USING: '20'    REGUH-VBLNR     1,
                               '32A'   REGUH-VALUT     1,
                               '32A'   UP_WAERS        2,
                               '32A'   REGUH-RWBTR     3,
                               '50_1'  UP_AUFTR_GEB_1  1,
                               '50_2'  UP_AUFTR_GEB_2  1,
                               '50_3'  UP_AUFTR_GEB_3  1,
                               '50_4'  UP_AUFTR_GEB_4  1,
                               '53_1'  REGUH-UBKNT     1.
      IF NOT REGUH-ZSWIF IS INITIAL.
        PERFORM PUT_MT100 USING '57A' REGUH-ZSWIF 1.
      ELSEIF NOT REGUH-ZBNKL IS INITIAL.
        PERFORM PUT_MT100 USING '57A' HLP_ZBNKL 2.
      ELSE.
        PERFORM PUT_MT100 USING: '57_1' BNKA-BANKA 1,
                                 '57_2' BNKA-STRAS 1,
                                 '57_3' BNKA-ORT01 1,
                                 '57_4' BNKA-PROVZ 1.
      ENDIF.
      PERFORM PUT_MT100 USING: '59_1'  REGUH-ZBNKN     1,
                               '59_2'  UP_ZAHL_EMPF_1  1,
                               '59_3'  UP_ZAHL_EMPF_2  1,
                               '59_4'  UP_ZAHL_EMPF_3  1,
                               '59_5'  UP_ZAHL_EMPF_4  1,
                               '71A'   T015W-DTKVS     1,
                               '72_1'  T015W-DTWS1     1,
                               '72_2'  T015W-DTWS2     1,
                               '72_3'  T015W-DTWS3     1,
                               '72_4'  T015W-DTWS4     1.
* AEM081001-
*                               '99'    '-'             1.
* AEM081001-

*     Fill DME fields for sender's and receiver's correspondent
*     and intermediary
      CALL FUNCTION 'FI_GET_CORRESP_INTERMED_BANKS'
        EXPORTING
          I_REGUH     = REGUH
          I_DTAFORMAT = HLP_DTFOR_LONG
        TABLES
          T_DTAMT100  = DTA_MT100.


*     Prüfung, ob Avishinweis erforderlich
*     check if advice note is necessary
      IF FLG_SGTXT = 1.
        CNT_ZEILEN = REGUH-RPOST + REGUH-RTEXT.
      ELSE.
        CNT_ZEILEN = REGUH-RPOST.
      ENDIF.
      CLEAR DTA_ZEILEN.
      REFRESH TAB_DTAM100V.
      IF CNT_ZEILEN GT PAR_ZEIL.       "Avishinweis ausgeben
        "print advice note
        PERFORM DTA_ERWEITERUNGSTEIL USING TEXT-704.
        PERFORM DTA_ERWEITERUNGSTEIL USING TEXT-705.
        ADD 1 TO CNT_HINWEISE.
        DTAM100-XAVIS_REQ = 'X'.
      ELSE.
        DTAM100-XAVIS_REQ = ' '.
      ENDIF.

    ENDAT.


*-- Verarbeitung der Einzelposten-Informationen ------------------------
*-- single item information --------------------------------------------
    AT DATEN.

      PERFORM EINZELPOSTENFELDER_FUELLEN.

*     Externe Belegnummer mit interner füllen, falls externe leer ist
*     fill external doc.no. with internal, if external is empty
      IF REGUP-XBLNR EQ SPACE.
        REGUP-XBLNR = REGUP-BELNR.
      ENDIF.

*     Ausgabe der Einzelposten, falls kein Avishinweis augegeben wurde
*     single item information if no advice note
      IF CNT_ZEILEN LE PAR_ZEIL.
        IF HLP_LAUFK NA 'JP'           "keine Rechungsinfo bei HR und IS
            AND REGUP-VERTN EQ SPACE.  "HR/IS: no invoice information

          PERFORM DTA_ERWEITERUNGSTEIL USING  TEXT-702 .
        ENDIF.

        IF FLG_SGTXT = 1 AND REGUP-SGTXT NE SPACE.
          PERFORM DTA_ERWEITERUNGSTEIL USING TEXT-703.
        ENDIF.
      ENDIF.

      PERFORM SUMMENFELDER_FUELLEN.

    ENDAT.


*-- Ende der Zahlungsbelegnummer ---------------------------------------
*-- end of payment document number -------------------------------------
    AT END OF REGUH-VBLNR.

*---- Prepare Open FI and User-Exits
      PERFORM FILL_DTAM100.
      CLEAR DTAM100-XCRLF_SUPP.
      CLEAR DTAM100-XCHAR_NREP.

*     Open FI / BTE (transaction record)
      IF PAR_MOFI NE SPACE.
        IF NOT T042OFI-XACTIVE2 IS INITIAL.
* AEM101001*********+
          ADD 1 TO W_CPT.
* AEM101001*********+
* AEM081001*********
          CALL FUNCTION 'Y_FI_PERFORM_00002020_P'
*          CALL FUNCTION 'OPEN_FI_PERFORM_00002020_P'
* AEM081001*********
               EXPORTING
                    I_FORMAT        = T042OFI-FORMT
                    I_REGUH         = REGUH
                    I_DTAM100       = DTAM100
* AEM101001*********+
                    I_CPT           = W_CPT
* AEM101001*********+
* AEM241001+++++++++++++++++++
*{   REPLACE        D11K938454                                        3
*\                    i_crsupp        = P_CRSUPP
                    I_CRSUPP        = P_CRSUPP
                    I_DATE          = PAR_DATE
*}   REPLACE
* AEM241001+++++++++++++++++++
               IMPORTING
                    E_DTAM100       = DTAM100
               TABLES
                    T_REGUP         = TAB_REGUP
                    T_DTAM100V      = TAB_DTAM100V
               EXCEPTIONS
                    NO_ADD_ON_FOUND = 1.
          IF SY-SUBRC NE 0.
            MESSAGE ID SY-MSGID TYPE 'S'  NUMBER SY-MSGNO
                    WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
          ELSE.
            _OPEN_FI = 'X'.
          ENDIF.
        ENDIF.
      ENDIF.

*     User-Exit (transaction record)
      PERFORM EXIT_900(RFFOEXIT)
              TABLES TAB_REGUP
                     TAB_DTAM100V
              USING  REGUH
                     DTAM100
                     UP_USREX.
      IF NOT UP_USREX IS INITIAL OR    "modifiziert / modified by user
         NOT _OPEN_FI IS INITIAL.
         *REGUT-USREX+1(1) = UP_USREX.
        IF UP_USREX EQ '1' OR UP_USREX EQ '3' OR
           NOT _OPEN_FI IS INITIAL.
          PERFORM READ_DTAM100.
        ENDIF.
        IF UP_USREX EQ '2' OR UP_USREX EQ '3' OR
           NOT _OPEN_FI IS INITIAL.
          PERFORM READ_DTAM100V.
        ENDIF.
      ENDIF.

*     Sortierung nach Tag (Für Format MT101 nicht erwünscht)

      IF T042OFI-FORMT <> 'MT101'.
        SORT DTA_MT100 BY TAG.
      ENDIF.
**AHOUNOU05082004
*Mettre le Tag A à la fin si Smartlink 'CMI101'
*{   REPLACE        D11K940053                                        4
*\      if t042ofi-formt eq 'CMI101'.
      IF T042OFI-FORMT EQ 'CMI101' OR T042OFI-FORMT EQ 'CMIOLD'.
*}   REPLACE
        REFRESH DTA_MT100_TEMP .
        CLEAR DTA_MT100_TEMP .
        CLEAR WA_DTA_MT100_TEMP .
        CLEAR WA_DTA_MT100_TEMP_71.
        LOOP AT DTA_MT100  INTO WA_DTA_MT100_TEMP.
          IF WA_DTA_MT100_TEMP-TAG NE '71A'.
            APPEND WA_DTA_MT100_TEMP TO DTA_MT100_TEMP.
          ELSE.
            MOVE WA_DTA_MT100_TEMP TO WA_DTA_MT100_TEMP_71.
            CLEAR WA_DTA_MT100_TEMP .
          ENDIF.
        ENDLOOP.

        REFRESH DTA_MT100.
        CLEAR DTA_MT100.
        CLEAR WA_DTA_MT100_TEMP .
        LOOP AT DTA_MT100_TEMP INTO  WA_DTA_MT100_TEMP .
          APPEND WA_DTA_MT100_TEMP TO DTA_MT100.
          CLEAR WA_DTA_MT100_TEMP .
        ENDLOOP.
        APPEND WA_DTA_MT100_TEMP_71 TO DTA_MT100.

      ENDIF.
*AHOUNOU05082004
*     Kein Avis gefordert

      IF DTAM100-XAVIS_REQ IS INITIAL.
        MOVE-CORRESPONDING REGUH TO TAB_KEIN_AVIS.
        APPEND TAB_KEIN_AVIS.
      ENDIF.

*     Aufbereitung und Schreiben der Daten aus DTA_MT100
      LOOP AT DTA_MT100.
        IF DTAM100-XCHAR_NREP IS INITIAL.
          PERFORM: DTA_TEXT_AUFBEREITEN USING DTA_MT100-VALUE,
                   MT100_GUELTIGE_ZEICHEN USING DTA_MT100-VALUE.
        ENDIF.
        IF DTA_MT100-LEN IS INITIAL.
          DTA_MT100-LEN = STRLEN( DTA_MT100-VALUE ).
        ENDIF.
        IF UP_USREX IS INITIAL AND _OPEN_FI IS INITIAL.
          IF DTA_MT100-LEN GT DTA_MT100-MAXLEN.
            DTA_MT100-LEN = DTA_MT100-MAXLEN.
          ENDIF.
        ENDIF.

        IF DTA_MT100-LEN GT 5 OR
           DTA_MT100-LEN GT 0 AND DTA_MT100-VALUE NP ':*:'.
          IF NOT DTAM100-XCRLF_SUPP IS INITIAL.
            PERFORM STORE_ON_FILE USING DTA_MT100-VALUE(DTA_MT100-LEN).
          ELSE.
            PERFORM STORE_ON_FILE USING:
              DTA_MT100-VALUE(DTA_MT100-LEN), UP_CRLF.
          ENDIF.
        ENDIF.
      ENDLOOP.
      CLEAR: UP_USREX, _OPEN_FI.

      ADD REGUH-RBETR TO SUM_REGUT.

      IF PAR_CBXX IS INITIAL.          "Einzelzahlung
        DTAM100T-XCRLF_SUPP = SPACE.

*       Open FI / BTE (trailer for single payments)
        IF PAR_MOFI NE SPACE.
          IF NOT T042OFI-XACTIVE3 IS INITIAL.
* AEM081001*********
            CALL FUNCTION 'Y_FI_PERFORM_00002030_P'
*            CALL FUNCTION 'OPEN_FI_PERFORM_00002030_P'
* AEM081001*********
                 EXPORTING
                      I_FORMAT        = T042OFI-FORMT
                      I_REGUH         = REGUH
                      I_DTAM100S      = DTAM100S
                      I_DTAM100T      = DTAM100T
* AEM241001+++++++++++++++++++
                      I_CRSUPP        = P_CRSUPP
* AEM241001+++++++++++++++++++
                 IMPORTING
                      E_DTAM100T      = DTAM100T
* AEM081001+
                 TABLES
                      T_SUM_PER_CURRENCY = TAB_SUM_PER_CURRENCY
* AEM081001+
                 EXCEPTIONS
                      NO_ADD_ON_FOUND = 1.
            IF SY-SUBRC NE 0.
              MESSAGE ID SY-MSGID TYPE 'S'  NUMBER SY-MSGNO
                      WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
            ELSE.
              _OPEN_FI = 'X'.
            ENDIF.
          ENDIF.
        ENDIF.

*       User-Exit (trailer for single payments)
        PERFORM EXIT_902(RFFOEXIT)
               TABLES TAB_REGUP
               USING  REGUH
                      DTAM100S
                      DTAM100T
                      PAR_CBXX
                      UP_USREX.
        IF NOT UP_USREX IS INITIAL OR  "modifiziert / modified by user
           NOT _OPEN_FI IS INITIAL.
           *REGUT-USREX+2 = UP_USREX.
          CLEAR: UP_USREX, _OPEN_FI.
          IF DTAM100T-T01 IS INITIAL.
            UP_LEN = STRLEN( DTAM100T-T00 ).
          ELSE.
            UP_LEN = DTAM100T-T01.
          ENDIF.
          IF UP_LEN GT 0.
            IF NOT DTAM100T-XCRLF_SUPP IS INITIAL.
              PERFORM STORE_ON_FILE USING DTAM100T-T00(UP_LEN).
            ELSE.
              PERFORM STORE_ON_FILE USING:
                      DTAM100T-T00(UP_LEN), UP_CRLF.
            ENDIF.
          ENDIF.
          CLEAR DTAM100T.
        ENDIF.

        PERFORM DATEI_SCHLIESSEN.
      ENDIF.
      SET LANGUAGE SY-LANGU.           " Anmeldesprache
    ENDAT.

    AT END OF REGUH-UBNKL.
      IF NOT PAR_CBXX IS INITIAL.      "mehrere Zahlungen
        DTAM100T-XCRLF_SUPP = SPACE.

*       Open FI / BTE (trailer for multi payments)
        IF PAR_MOFI NE SPACE.
          IF NOT T042OFI-XACTIVE3 IS INITIAL.
* AEM081001*********
            CALL FUNCTION 'Y_FI_PERFORM_00002030_P'
*            CALL FUNCTION 'OPEN_FI_PERFORM_00002030_P'
* AEM081001*********
                 EXPORTING
                      I_FORMAT        = T042OFI-FORMT
                      I_REGUH         = REGUH
                      I_DTAM100S      = DTAM100S
                      I_DTAM100T      = DTAM100T
* AEM241001+++++++++++++++++++
                      I_CRSUPP        = P_CRSUPP
* AEM241001+++++++++++++++++++
                 IMPORTING
                      E_DTAM100T      = DTAM100T
* AEM081001+
                 TABLES
                      T_SUM_PER_CURRENCY = TAB_SUM_PER_CURRENCY
* AEM081001+

                 EXCEPTIONS
                      NO_ADD_ON_FOUND = 1.
            IF SY-SUBRC NE 0.
              MESSAGE ID SY-MSGID TYPE 'S'  NUMBER SY-MSGNO
                      WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
            ELSE.
              _OPEN_FI = 'X'.
            ENDIF.
          ENDIF.
        ENDIF.

*       User-Exit for trailer (trailer for multi payment)
        PERFORM EXIT_902(RFFOEXIT)
                TABLES TAB_REGUP
                USING  REGUH
                       DTAM100S
                       DTAM100T
                       PAR_CBXX
                       UP_USREX.
        IF NOT UP_USREX IS INITIAL OR  "modifiziert / modified by user
           NOT _OPEN_FI IS INITIAL.
           *REGUT-USREX+2 = UP_USREX.
          CLEAR: UP_USREX, _OPEN_FI.
          IF DTAM100T-T01 IS INITIAL.
            UP_LEN = STRLEN( DTAM100T-T00 ).
          ELSE.
            UP_LEN = DTAM100T-T01.
          ENDIF.
          IF UP_LEN GT 0.
            IF NOT DTAM100T-XCRLF_SUPP IS INITIAL.
              PERFORM STORE_ON_FILE USING DTAM100T-T00(UP_LEN).
            ELSE.
              PERFORM STORE_ON_FILE USING:
                      DTAM100T-T00(UP_LEN), UP_CRLF.
            ENDIF.
          ENDIF.
          CLEAR DTAM100T.
        ENDIF.

        PERFORM DATEI_SCHLIESSEN.
      ENDIF.
    ENDAT.

    AT END OF REGUH-ZBUKR.
    ENDAT.

  ENDLOOP.

ENDFORM.                                                    "MT100


*----------------------------------------------------------------------*
* Form MT100_INIT
*----------------------------------------------------------------------*
FORM MT100_INIT.

  CLEAR DTA_MT100.
  REFRESH DTA_MT100.
  PERFORM MT100_INIT_WORK
          USING: '00'    ''      '' '3'  ,
                 '20'    ':20:'  '' '20' ,
                 '21'    ':21:'  '' '20' ,                  "MT101 only
                 '23E_1' ':23E:' '' '40' ,                  "MT101 only
                 '23E_2' ':23E:' '' '40' ,                  "MT101 only
                 '23E_3' ':23E:' '' '40' ,                  "MT101 only
                 '23E_4' ':23E:' '' '40' ,                  "MT101 only
                 '32A'   ':32A:' '' '29' ,
                 '32B'   ':32B:' '' '23' ,                  "MT101 only
                 '50_1'  ':50:'  '' '39' ,
                 '50_2'  ''      '' '35' ,
                 '50_3'  ''      '' '35' ,
                 '50_4'  ''      '' '35' ,
                 '50L'   ':50L:' '' '40' ,                  "MT101 only
                 '50H_1' ':50H:' '' '40' ,                  "MT101 only
                 '50H_2' ''      '' '35' ,                  "MT101 only
                 '50H_3' ''      '' '35' ,                  "MT101 only
                 '50H_4' ''      '' '35' ,                  "MT101 only
                 '50H_5' ''      '' '35' ,                  "MT101 only
                 '52_1'  ''      '' '40' ,
                 '52_2'  ''      '' '35' ,
                 '52_3'  ''      '' '35' ,
                 '52_4'  ''      '' '35' ,
                 '53_1'  ':53B:' '' '40' ,
                 '53_2'  ''      '' '35' ,
                 '53_3'  ''      '' '35' ,
                 '53_4'  ''      '' '35' ,
                 '54_1'  ''      '' '40' ,
                 '54_2'  ''      '' '35' ,
                 '54_3'  ''      '' '35' ,
                 '54_4'  ''      '' '35' ,
                 '54_5'  ''      '' '35' ,
                 '56_1'  ''      '' '40' ,
                 '56_2'  ''      '' '35' ,
                 '56_3'  ''      '' '35' ,
                 '56_4'  ''      '' '35' ,
                 '56_5'  ''      '' '35' ,
                 '57A'   ':57A:' '' '40' ,
                 '57_1'  ':57D:' '' '40' ,
                 '57_2'  ''      '' '35' ,
                 '57_3'  ''      '' '35' ,
                 '57_4'  ''      '' '35' ,
                 '59_1'  ':59:'  '' '39' ,
                 '59_2'  ''      '' '35' ,
                 '59_3'  ''      '' '35' ,
                 '59_4'  ''      '' '35' ,
                 '59_5'  ''      '' '35' ,
                 '70_1'  ''      '' '39' ,
                 '70_2'  ''      '' '35' ,
                 '70_3'  ''      '' '35' ,
                 '70_4'  ''      '' '35' ,
                 '77B_1' ':77B:' '' '40' ,                  "MT101 only
                 '77B_2' ''      '' '35' ,                  "MT101 only
                 '77B_3' ''      '' '35' ,                  "MT101 only
                 '71A'   ':71A:' '' '8'  ,
                 '25A'   ':25A:' '' '40' ,                  "MT101 only
                 '72_1'  ':72:'  '' '39' ,       "For User-Exit
                 '72_2'  ''      '' '35' ,       "For User-Exit
                 '72_3'  ''      '' '35' ,       "For User-Exit
                 '72_4'  ''      '' '35' ,       "For User-Exit
                 '72_5'  ''      '' '35' ,       "For User-Exit
                 '72_6'  ''      '' '35' .     "For User-Exit

* AEM081001-
*                 '99'    ''      '' '1'  .
* AEM081001-

ENDFORM.                                                    "MT100_INIT


*----------------------------------------------------------------------*
* Form MT100_INIT_WORK
*----------------------------------------------------------------------*
FORM MT100_INIT_WORK USING TAG WERT LEN MAXLEN.

  CLEAR DTA_MT100.
  DTA_MT100-TAG    = TAG.
  DTA_MT100-VALUE  = WERT.
  DTA_MT100-LEN    = LEN.
  DTA_MT100-MAXLEN = MAXLEN.
  APPEND DTA_MT100.

ENDFORM.                               "MT100_INIT_WORK


*----------------------------------------------------------------------*
* Form DTA_ERWEITERUNGSTEIL                                            *
*----------------------------------------------------------------------*
* Füllen des Erweiterungsteils eines C-Satzes im DTA Inland            *
* fill file extension field with note to payee                         *
*----------------------------------------------------------------------*
* KZ      - Kennzeichen des Erweiterungsteils                          *
*           file extension indicator                                   *
* ERWTEIL - Erweiterungsteil                                           *
*           file extension                                             *
*----------------------------------------------------------------------*
FORM DTA_ERWEITERUNGSTEIL USING P_TEXT.

  DATA:
    UP_TAG    LIKE DTA_MT100-TAG VALUE '70_',
    UP_TABIX  LIKE SY-TABIX.

  TXT_ZEILE = P_TEXT.
  PERFORM DTA_GLOBALS_ERSETZEN USING TXT_ZEILE.

  ADD 1 TO DTA_ZEILEN.
  UP_TAG+3 = DTA_ZEILEN.
  CONDENSE UP_TAG NO-GAPS.
  DTA_MT100-TAG = UP_TAG.
  READ TABLE DTA_MT100 WITH KEY UP_TAG.
  UP_TABIX = SY-TABIX.


  IF DTA_ZEILEN EQ 1.

    DTA_MT100-VALUE   = ':70:'.
    DTA_MT100-VALUE+4 = TXT_ZEILE.
    DTA_MT100-MAXLEN  = 39.

  ELSE.
    DTA_MT100-VALUE  = TXT_ZEILE.
    DTA_MT100-MAXLEN = 35.
  ENDIF.
  IF UP_TABIX NE 0.
    MODIFY DTA_MT100 INDEX UP_TABIX.
  ENDIF.

* Fill internal table TAB_DTAM100V for user-exit / BTE with the
* further payment references
  IF PAR_ZEIL GT 4 AND CNT_ZEILEN LE PAR_ZEIL.
    TAB_DTAM100V-TAG   = DTA_MT100-TAG.
    TAB_DTAM100V-VALUE = DTA_MT100-VALUE.
    APPEND TAB_DTAM100V.
  ENDIF.

ENDFORM.                               "DTA_ERWEITERUNGSTEIL


*----------------------------------------------------------------------*
* Form DTA_GUELTIGE_ZEICHEN                                            *
*----------------------------------------------------------------------*
* Untersucht, ob ein Textstring nur gültige Zeichen enthält            *
* deletes invalid letters                                              *
*----------------------------------------------------------------------*
* TEXTFELD - zu untersuchendes Feld                                    *
*            text that is to be checked                                *
*----------------------------------------------------------------------*
FORM DTA_GUELTIGE_ZEICHEN USING TEXTFELD.

  WHILE TEXTFELD CN 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890 .,&-/+*$%'.
    WRITE SPACE TO TEXTFELD+SY-FDPOS(1).
  ENDWHILE.

ENDFORM.                               "DTA_GUELTIGE_ZEICHEN


*----------------------------------------------------------------------*
* Form PUT_MT100                                                       *
*----------------------------------------------------------------------*
* Füllt die interne Tabelle DTA_MT100                                  *
*----------------------------------------------------------------------*
FORM PUT_MT100 USING P_TAG     LIKE DTA_MT100-TAG
                     P_VALUE   TYPE ANY
                     P_COMP    TYPE I.

  DATA:
    UP_NUM(40)          TYPE N,
    UP_OFF              TYPE I,
    UP_BUFFER(6)        TYPE C,
    UP_LEN              LIKE DTA_MT100-LEN,
    UP_VALUE            LIKE DTA_MT100-VALUE,
    UP_CLEARING_CODE(4) TYPE C,
    UP_SYTABIX          LIKE SY-TABIX,
    LS_T012K            LIKE T012K,
    LC_BANKN            LIKE REGUH_BF-ZBNKN,
* Ajout bank key EMAR240102
    W_BANK_KEY LIKE REGUH_BF-ZBNKY,
* Fin ajout EMAR240102
    UP_ACCOUNT_DEF_LEN  TYPE I,
    UP_ACCOUNT_VAL_LEN  TYPE I.

  DESCRIBE FIELD LC_BANKN LENGTH UP_ACCOUNT_DEF_LEN IN CHARACTER MODE..

  READ TABLE DTA_MT100 WITH KEY P_TAG.
  DESCRIBE FIELD P_VALUE OUTPUT-LENGTH UP_LEN.
  UP_OFF = STRLEN( DTA_MT100-VALUE ).
  UP_SYTABIX = SY-TABIX.

  CASE P_TAG.
*   Field 32A
    WHEN '32A'.
      CASE P_COMP.
        WHEN 1.
          WRITE P_VALUE TO UP_BUFFER YYMMDD.
          UP_LEN = 6.
          DTA_MT100-VALUE+UP_OFF(UP_LEN) = UP_BUFFER.
        WHEN 2.
          UP_LEN = 3.
          DTA_MT100-VALUE+UP_OFF(UP_LEN) = P_VALUE.
        WHEN 3.
          CALL FUNCTION 'SPELL_AMOUNT'
            EXPORTING
              AMOUNT    = REGUH-RWBTR
              CURRENCY  = REGUH-WAERS
              FILLER    = SPACE
              LANGUAGE  = SPACE
            IMPORTING
              IN_WORDS  = SPELL
            EXCEPTIONS
              NOT_FOUND = 01
              TOO_LARGE = 02.
          UP_VALUE                       = SPELL-NUMBER.
          UP_VALUE+15                    = ','.
          IF SPELL-CURRDEC GT 0.
            UP_VALUE+16(SPELL-CURRDEC)   = SPELL-DECIMAL.
          ENDIF.
          WHILE UP_VALUE(1) EQ '0'.
            SHIFT UP_VALUE LEFT BY 1 PLACES.
          ENDWHILE.
          UP_LEN = STRLEN( UP_VALUE ).
          DTA_MT100-VALUE+UP_OFF(UP_LEN) = UP_VALUE.
      ENDCASE.
      MODIFY DTA_MT100 INDEX UP_SYTABIX.

*   Field 53, first line
    WHEN '53_1'.
      DTA_MT100-VALUE+UP_OFF = '/'.
      ADD 1 TO UP_OFF.
      CALL FUNCTION 'GET_EXT_BANKACCOUNT_NO'
        EXPORTING
          I_BANK_COUNTRY     = REGUH-UBNKS
          I_BLZ              = REGUH-UBNKL
          I_BANK_ACCOUNT     = REGUH-UBKNT
          I_CONTROL_KEY      = REGUH-UBKON
        IMPORTING
          E_EXT_BANK_ACCOUNT = UP_VALUE.

      UP_ACCOUNT_VAL_LEN = NUMOFCHAR( UP_VALUE ).
      IF UP_ACCOUNT_VAL_LEN <= UP_ACCOUNT_DEF_LEN.
        LC_BANKN = UP_VALUE.
        CALL FUNCTION 'FI_HOUSEBANK_ACCOUNT_READ'
          EXPORTING
            IC_BUKRS = REGUH-ZBUKR
            IC_HBKID = REGUH-HBKID
            IC_HKTID = REGUH-HKTID
          IMPORTING
            ES_T012K = LS_T012K.
        CALL FUNCTION 'CONVERT_HOUSEBANK_ACCOUNT_NUM'
          EXPORTING
            I_LAND1      = REGUH-UBNKS
            I_BANKK      = REGUH-UBNKY
            I_BANKN      = LC_BANKN
            I_BKONT      = REGUH-UBKON
            I_REFZL      = LS_T012K-REFZL
            I_BANKL      = REGUH-UBNKL
          IMPORTING
            E_BANKN_LONG = UP_VALUE.
      ENDIF.
      DTA_MT100-VALUE+UP_OFF(34) = UP_VALUE.
      MODIFY DTA_MT100 INDEX UP_SYTABIX.

*   Field 57A
    WHEN '57A'.
      IF P_COMP = 2.
        PERFORM GET_CLEARING_CODE USING REGUH-ZBNKS
                                        REGUH-ZBNKL
                                        UP_CLEARING_CODE+2(2).
        IF NOT UP_CLEARING_CODE IS INITIAL.
          UP_CLEARING_CODE(2) = '//'.
          DTA_MT100-VALUE+UP_OFF(4) = UP_CLEARING_CODE.
          CLEAR UP_CLEARING_CODE.
          ADD 4 TO UP_OFF.
          ADD 4 TO UP_LEN.
          WRITE REGUH-ZBNKL TO DTA_MT100-VALUE+UP_OFF.
          CONDENSE DTA_MT100-VALUE NO-GAPS.
        ELSE.
          WRITE P_VALUE TO DTA_MT100-VALUE+UP_OFF NO-ZERO.
          CONDENSE DTA_MT100-VALUE NO-GAPS.
        ENDIF.
      ELSE.
        DTA_MT100-VALUE+UP_OFF = P_VALUE.
      ENDIF.
      MODIFY DTA_MT100 INDEX UP_SYTABIX.

*   Field 59, first line
    WHEN '59_1'.
      DTA_MT100-VALUE+UP_OFF = '/'.
      ADD 1 TO UP_OFF.
      CALL FUNCTION 'GET_EXT_BANKACCOUNT_NO'
           EXPORTING
                I_BANK_COUNTRY     = REGUH-ZBNKS
                I_BLZ              = REGUH-ZBNKL
                I_BANK_ACCOUNT     = REGUH-ZBNKN
                I_CONTROL_KEY      = REGUH-ZBKON
           IMPORTING
* Ajout bank key EMAR240102
                E_EXT_BLZ          = W_BANK_KEY
* Fin Ajout bank key EMAR240102
                E_EXT_BANK_ACCOUNT = UP_VALUE.

* Ajout bank key EMAR240102
* Ajout de la clef bancaire si renseignée
* Change request code DMD 10968 / Cas Allemangne et Autriche.
* Alain Ahounou 23/12/2002
      IF  W_BANK_KEY IS INITIAL.
*rien
      ELSEIF REGUH-ZBNKS NE 'DE' AND REGUH-ZBNKS NE 'AT'.
        CONCATENATE W_BANK_KEY UP_VALUE INTO UP_VALUE.
      ELSE.
        CONCATENATE UP_VALUE W_BANK_KEY  INTO UP_VALUE.
      ENDIF.

* Fin Ajout bank key EMAR240102

      UP_ACCOUNT_VAL_LEN = NUMOFCHAR( UP_VALUE ).
      IF UP_ACCOUNT_VAL_LEN <= UP_ACCOUNT_DEF_LEN.
        LC_BANKN = UP_VALUE.
        CALL FUNCTION 'CONVERT_BANK_ACCOUNT_NUMBER'
          EXPORTING
            I_BANKS      = REGUH-ZBNKS
            I_BANKK      = REGUH-ZBNKY
            I_BANKN      = LC_BANKN
            I_BKONT      = REGUH-ZBKON
            I_BKREF      = REGUH-BKREF
            I_BANKL      = REGUH-ZBNKL
          IMPORTING
            E_BANKN_LONG = UP_VALUE.
      ENDIF.
      DTA_MT100-VALUE+UP_OFF(34) = UP_VALUE.
      MODIFY DTA_MT100 INDEX UP_SYTABIX.

*   Field 71A
    WHEN '71A'.
      IF P_VALUE = '01'.
        DTA_MT100-VALUE+UP_OFF = 'OUR'.
        MODIFY DTA_MT100 INDEX UP_SYTABIX.
      ELSEIF P_VALUE = '02'.
        DTA_MT100-VALUE+UP_OFF = 'BEN'.
        MODIFY DTA_MT100 INDEX UP_SYTABIX.
      ENDIF.

*   Field 72, first line
    WHEN '72_1'.
      PERFORM WEISUNGSSCHLUESSEL_UMSETZEN USING '100' '1'
                                                P_VALUE
                                                TXT_ZEILE
                                                TXT_ZEILE+40(*).
      IF TXT_ZEILE(40) IS INITIAL.
        IF NOT P_VALUE IS INITIAL.
          FIMSG-MSGV1 = SY-REPID.
          FIMSG-MSGV2 = P_VALUE.
          FIMSG-MSGV3 = REGUH-UBNKS.
          FIMSG-MSGV4 = REGUH-RZAWE.
          PERFORM MESSAGE USING '460'.
        ENDIF.
      ELSE.
        CONDENSE TXT_ZEILE.
        DTA_MT100-VALUE+UP_OFF = TXT_ZEILE.
        MODIFY DTA_MT100 INDEX UP_SYTABIX.
      ENDIF.

*   Field 72, second line
    WHEN '72_2'.
      PERFORM WEISUNGSSCHLUESSEL_UMSETZEN USING '100' '2'
                                                P_VALUE
                                                TXT_ZEILE
                                                TXT_ZEILE+40(*).
      IF TXT_ZEILE(40) IS INITIAL.
        IF NOT P_VALUE IS INITIAL.
          FIMSG-MSGV1 = SY-REPID.
          FIMSG-MSGV2 = P_VALUE.
          FIMSG-MSGV3 = REGUH-UBNKS.
          FIMSG-MSGV4 = REGUH-RZAWE.
          PERFORM MESSAGE USING '460'.
        ENDIF.
      ELSE.
        CONDENSE TXT_ZEILE.
        DTA_MT100-VALUE+UP_OFF = TXT_ZEILE.
        MODIFY DTA_MT100 INDEX UP_SYTABIX.
      ENDIF.

*   Field 72, third line
    WHEN '72_3'.
      PERFORM WEISUNGSSCHLUESSEL_UMSETZEN USING '100' '3'
                                                P_VALUE
                                                TXT_ZEILE
                                                TXT_ZEILE+40(*).
      IF TXT_ZEILE(40) IS INITIAL.
        IF NOT P_VALUE IS INITIAL.
          FIMSG-MSGV1 = SY-REPID.
          FIMSG-MSGV2 = P_VALUE.
          FIMSG-MSGV3 = REGUH-UBNKS.
          FIMSG-MSGV4 = REGUH-RZAWE.
          PERFORM MESSAGE USING '460'.
        ENDIF.
      ELSE.
        CONDENSE TXT_ZEILE.
        DTA_MT100-VALUE+UP_OFF = TXT_ZEILE.
        MODIFY DTA_MT100 INDEX UP_SYTABIX.
      ENDIF.

*   Field 72, forth line
    WHEN '72_4'.
      PERFORM WEISUNGSSCHLUESSEL_UMSETZEN USING '100' '4'
                                                P_VALUE
                                                TXT_ZEILE
                                                TXT_ZEILE+40(*).
      IF TXT_ZEILE(40) IS INITIAL.
        IF NOT P_VALUE IS INITIAL.
          FIMSG-MSGV1 = SY-REPID.
          FIMSG-MSGV2 = P_VALUE.
          FIMSG-MSGV3 = REGUH-UBNKS.
          FIMSG-MSGV4 = REGUH-RZAWE.
          PERFORM MESSAGE USING '460'.
        ENDIF.
      ELSE.
        CONDENSE TXT_ZEILE.
        DTA_MT100-VALUE+UP_OFF = TXT_ZEILE.
        MODIFY DTA_MT100 INDEX UP_SYTABIX.
      ENDIF.

*   Alle other fields or lines
    WHEN OTHERS.
      IF UP_LEN GT 0.
        DTA_MT100-VALUE+UP_OFF(UP_LEN) = P_VALUE.
        MODIFY DTA_MT100 INDEX UP_SYTABIX.
      ENDIF.

  ENDCASE.

ENDFORM.                                                    "PUT_MT100


*----------------------------------------------------------------------*
* Form MT100_GUELTIGE_ZEICHEN
*----------------------------------------------------------------------*
FORM MT100_GUELTIGE_ZEICHEN USING TEXTFELD.

  WHILE TEXTFELD CN
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890?().,''''+ /:@-'.
    WRITE SPACE TO TEXTFELD+SY-FDPOS(1).
  ENDWHILE.

ENDFORM.                               "MT100_GUELTIGE_ZEICHEN


*----------------------------------------------------------------------*
* Form FILL_DTAM100
*----------------------------------------------------------------------*
FORM FILL_DTAM100.

  FIELD-SYMBOLS:
    <UP_FIELD>.

  DATA:
    UP_FIELD(20),
    UP_XAVIS LIKE DTAM100-XAVIS_REQ.

  UP_XAVIS = DTAM100-XAVIS_REQ.
  CLEAR DTAM100.
  DTAM100-XAVIS_REQ = UP_XAVIS.
  UP_FIELD = 'DTAM100-'.
  LOOP AT NAMETAB.
    CHECK NAMETAB-FIELDNAME NE 'XAVIS_REQ'.
    CHECK NAMETAB-FIELDNAME NE 'XCRLF_SUPP'.
    CHECK NAMETAB-FIELDNAME NE 'XCHAR_NREP'.
    UP_FIELD+8 = NAMETAB-FIELDNAME.
    ASSIGN  (UP_FIELD) TO <UP_FIELD>.
    CLEAR DTA_MT100.
    DTA_MT100-TAG = NAMETAB-FIELDNAME.
    READ TABLE DTA_MT100.
    <UP_FIELD> = DTA_MT100-VALUE.
  ENDLOOP.

ENDFORM.                               "FILL_DTAM100


*----------------------------------------------------------------------*
* Form READ_DTAM100
*----------------------------------------------------------------------*
FORM READ_DTAM100.

  FIELD-SYMBOLS:
    <UP_FIELD>.

  DATA: UP_FIELD(20),
        UP_LFDNR LIKE DTA_MT100-TAG.

  UP_FIELD = 'DTAM100-'.
  LOOP AT NAMETAB.
    UP_FIELD+8 = NAMETAB-FIELDNAME.
    ASSIGN  (UP_FIELD) TO <UP_FIELD>.
    CLEAR DTA_MT100.
    DTA_MT100-TAG = NAMETAB-FIELDNAME.
    READ TABLE DTA_MT100.
    DTA_MT100-VALUE = <UP_FIELD>.
*   DTA_MT100-LEN   = STRLEN( DTA_MT100-VALUE ).
    IF NAMETAB-FIELDNAME(3) EQ '70_'.
      UP_LFDNR = NAMETAB-FIELDNAME+3.
      IF UP_LFDNR = 1
      OR UP_LFDNR = 2
      OR UP_LFDNR LE PAR_ZEIL.
        IF SY-SUBRC EQ 0.
          MODIFY DTA_MT100 INDEX SY-TABIX.
        ELSE.
          APPEND DTA_MT100.
        ENDIF.
      ENDIF.
    ELSE.
      IF SY-SUBRC EQ 0.
        MODIFY DTA_MT100 INDEX SY-TABIX.
      ELSE.
        IF NAMETAB-FIELDNAME NE 'XAVIS_REQ' AND
           NAMETAB-FIELDNAME NE 'XCRLF_SUPP' AND
           NAMETAB-FIELDNAME NE 'XCHAR_NREP'.
          APPEND DTA_MT100.
        ENDIF.
      ENDIF.
    ENDIF.
  ENDLOOP.

ENDFORM.                               "READ_DTAM100


*----------------------------------------------------------------------*
* Form DATEI_OEFFNEN_1
*----------------------------------------------------------------------*
FORM DATEI_OEFFNEN_1 USING P_CNT_FILENR.

  IF HLP_TEMSE CA PAR_DTYP.            "TemSe-Format
    PERFORM TEMSE_OEFFNEN.
  ELSE.                                "disk-/tape-fmt on file-system
    PERFORM NAECHSTER_INDEX USING HLP_RENUM.
    PERFORM FUELLEN_REGUT USING *REGUT-DTKEY.
    HLP_FILENAME    = PAR_UNIX.
    HLP_FILENAME+39 = P_CNT_FILENR.
    CONDENSE HLP_FILENAME NO-GAPS.
*AHOUNOU05072006
*    OPEN DATASET hlp_filename IN BINARY MODE FOR OUTPUT.
    OPEN DATASET HLP_FILENAME IN TEXT MODE FOR OUTPUT  ENCODING
                                                          NON-UNICODE.

*AHOUNOU05072006
    IF SY-SUBRC NE 0.
      IF SY-BATCH EQ SPACE.
        MESSAGE A182(FR) WITH HLP_FILENAME.
      ELSE.
        MESSAGE S182(FR) WITH HLP_FILENAME.
        STOP.
      ENDIF.
    ENDIF.
  ENDIF.

* Referenznr für RFDT sichern, Tabelle für Zahlungsbelege löschen
* store reference-number, refresh table for document-numbers
  CALL FUNCTION 'COMPUTE_CONTROL_NUMBER'
    EXPORTING
      I_REFNO  = HLP_RENUM
    IMPORTING
      E_RESULT = HLP_RESULTAT.
  REGUD-LABEL = HLP_DTA_ID-REFNR = HLP_RESULTAT.
  CLEAR   TAB_BELEGE30A.
  REFRESH TAB_BELEGE30A.

ENDFORM.                               "DATEI_OEFFNEN_1


*----------------------------------------------------------------------*
* Form READ_DTAM100V
*----------------------------------------------------------------------*
* Read internal table tab_dtam100v filled by the user-exit
*----------------------------------------------------------------------*
FORM READ_DTAM100V.

  LOOP AT TAB_DTAM100V.
    CLEAR DTA_MT100.
    DTA_MT100-TAG = TAB_DTAM100V-TAG.
    READ TABLE DTA_MT100.
    DTA_MT100-VALUE = TAB_DTAM100V-VALUE.
    IF NOT TAB_DTAM100V-LENGTH IS INITIAL.
      DTA_MT100-LEN = TAB_DTAM100V-LENGTH.
    ENDIF.
    IF SY-SUBRC EQ 0.
      MODIFY DTA_MT100 INDEX SY-TABIX.
    ELSE.
      APPEND DTA_MT100.
    ENDIF.
  ENDLOOP.

ENDFORM.                               "READ_DTAM100V