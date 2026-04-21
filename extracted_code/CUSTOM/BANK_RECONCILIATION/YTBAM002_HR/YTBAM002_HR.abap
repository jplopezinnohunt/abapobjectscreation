*INCLUDE YTBAM002


*******************************************************************
* PROGRAM        YTBAM002
* TITLE          Bank reconciliation with type of funds
* AUTHOR         S.MAGAL
* DATE WRITTEN   July 2001
* R/3 RELEASE    4.6C
*******************************************************************
* COPIED FROM
* TITLE
*******************************************************************
* USED BY....... < user or usergroups >
*******************************************************************
* PROGRAM TYPE
* DEV.CLASS
* LOGICAL DB
*******************************************************************
* SCREENS
* GUI TITLE
* GUI STATUS
*******************************************************************
* CHANGE HISTORY
*
* Date       By      Correction Number & Brief Description  Release
*
* 16/05/2001 S.magal     0001 Correction ?????----------- -------
*
* 28/11/2001 A.Arkwright 0002 Update
*
* 04/12/2002 F.Béchet    0003 Correction décimales - Landpark 9598
*                             Rajout dans les write d'impression du
*                             mot clé currency associé au montant
*
*******************************************************************



*******************************************************************
*      Form  17_control_transaction
*******************************************************************
*  Execution of the CALL TRANSACTION
*******************************************************************
*  --> y_control t_bsis
*  <-- y_control
*******************************************************************
FORM 17_CONTROL_TRANSACTION
                TABLES T_BSIS    STRUCTURE T_BSIS_TEMP
              CHANGING Y_CONTROL LIKE Y_CONTROL_TRANSACTION.

  DATA: Y_OLD_GSBER  LIKE BSIS-GSBER.  "Business area
  DATA: Y_OLD_WAERS  LIKE BSIS-WAERS.  "Currency
  DATA: Y_TOT_WRBTR  LIKE BSIS-WRBTR.  "Amount
  DATA: Y_FLAG_11(1) TYPE C.           "Flag for account number 11xxxxx
  DATA: Y_FLAG_13(1) TYPE C.           "Flag for account number 13xxxxx

  CLEAR Y_OLD_GSBER.
  CLEAR Y_OLD_WAERS.
  CLEAR Y_TOT_WRBTR.
  CLEAR T_BSIS.
  CLEAR Y_CONTROL.


  LOOP AT T_BSIS.

* Calculate total amount
    IF T_BSIS-SHKZG = 'H'.          "Credit
      ADD T_BSIS-WRBTR TO Y_TOT_WRBTR.
    ENDIF.
    IF T_BSIS-SHKZG = 'S'.          "Debit
      SUBTRACT T_BSIS-WRBTR FROM Y_TOT_WRBTR.
    ENDIF.

    IF Y_OLD_WAERS NE SPACE.
* Control account number.
      IF (     T_BSIS-HKONT+3(2) NE C_ACCOUNT_NUMBER_13
           AND T_BSIS-HKONT+3(2) NE C_ACCOUNT_NUMBER_11 ).
        Y_CONTROL = 'X'.
        MESSAGE I398(00) WITH TEXT-014.
      ENDIF.

* Control business area
      IF (     T_BSIS-HKONT+3(2) = C_ACCOUNT_NUMBER_11
           AND Y_OLD_GSBER  NE SPACE
           AND T_BSIS-GSBER NE Y_OLD_GSBER ).
        Y_CONTROL = 'X'.
        MESSAGE I398(00) WITH TEXT-002
                              TEXT-003.
      ENDIF.

* Control currency
      IF T_BSIS-WAERS NE Y_OLD_WAERS.
        Y_CONTROL = 'X'.
      ENDIF.

    ENDIF.

* Initialize flags
    Y_OLD_WAERS = T_BSIS-WAERS.
    IF T_BSIS-HKONT+3(2) = C_ACCOUNT_NUMBER_11.
      Y_OLD_GSBER = T_BSIS-GSBER.
    ENDIF.

* Control number of document with account 13xxxxx
    IF T_BSIS-HKONT+3(2) = C_ACCOUNT_NUMBER_13.
      IF T_BSIS-GSBER NE 'X'.
        Y_CONTROL = 'X'.
        MESSAGE I398(00) WITH TEXT-013.
      ENDIF.
      IF Y_FLAG_13 = 'X'.
* There is more than one document with account nb 13xxxxx
        Y_CONTROL = 'X'.
        MESSAGE I398(00) WITH TEXT-005
                              TEXT-006.
      ELSE.
        Y_FLAG_13 = 'X'.
      ENDIF.
    ENDIF.

* Control number of document with account 13xxxxx and 11xxxxx
    IF T_BSIS-HKONT+3(2) = C_ACCOUNT_NUMBER_11.
      Y_FLAG_11 = 'X'.
    ENDIF.

  ENDLOOP.      "AT t_bsis

* Control total amount
  IF Y_TOT_WRBTR NE 0.
    Y_CONTROL = 'X'.
    MESSAGE I398(00) WITH TEXT-004.
  ENDIF.

* There must be at least one 13xxxxx and one 11xxxxx
  IF ( Y_FLAG_11 = SPACE AND Y_FLAG_13 = SPACE ).
    Y_CONTROL = 'X'.
    MESSAGE I398(00) WITH TEXT-011
                          TEXT-012.
  ENDIF.


ENDFORM.                               " 17_control_transaction

*******************************************************************
*      Form  19_CALL_TRANSACTION
*******************************************************************
*  Execution of the CALL TRANSACTION
*******************************************************************
*  --> bdcdtab t_bsis y_messtab
*  <-- y_messtab
*******************************************************************
FORM 19_CALL_TRANSACTION TABLES T_BSIS    STRUCTURE T_BSIS_TEMP
                                BDCDTAB   STRUCTURE BDCDATA
                                Y_MESSTAB STRUCTURE BDCMSGCOLL.

  DATA: Y_TRANS(4) TYPE C.
  DATA: Y_NUMBER   TYPE I.
  DATA: Y_FB08_OK TYPE C. "Y : transaction fb08 OK
  "N : transaction fb08 KO

*** Get informations
  CLEAR T_BSIS.
  CLEAR T_BSIS_FB08.
  CLEAR T_BSIS_F-04.
  REFRESH T_BSIS_BELNR.

  LOOP AT T_BSIS.

* Get information for the transaction fb08
    IF T_BSIS-HKONT+3(2) = C_ACCOUNT_NUMBER_13.
      T_BSIS_FB08-BUKRS = T_BSIS-BUKRS.
      T_BSIS_FB08-BELNR = T_BSIS-BELNR.
      T_BSIS_FB08-BUDAT = T_BSIS-BUDAT.
      T_BSIS_FB08-GJAHR = T_BSIS-GJAHR.
    ENDIF.

     IF T_BSIS-HKONT+3(2) = C_ACCOUNT_NUMBER_11.
      T_BSIS_F-04-GSBER  = T_BSIS-GSBER.
*{   REPLACE        A01K920068                                        6
*\      t_bsis_belnr-belnr = t_bsis-belnr.
      T_BSIS_BELNR-BELNR = T_BSIS-BELNR.
      T_BSIS_F-04-BELNR = T_BSIS-BELNR.
*}   REPLACE
*AHOUNOU15032007
*{   REPLACE        A01K920068                                        5
*\      t_bsis_f-04-zuonr = t_bsis-zuonr.
      T_BSIS_F-04-ZUONR = T_BSIS-ZUONR.
      T_BSIS_F-04-ZUONR_HR = T_BSIS-ZUONR_HR.
*}   REPLACE
*AHOUNOU15032007
      APPEND T_BSIS_BELNR.
    ENDIF.

*Get information for the transaction f-04
    IF T_BSIS-HKONT+3(2) = C_ACCOUNT_NUMBER_13.
      T_BSIS_F-04-BUKRS = T_BSIS-BUKRS.
      T_BSIS_F-04-BUDAT = T_BSIS-BUDAT.
      T_BSIS_F-04-BLDAT = T_BSIS-BLDAT.
      T_BSIS_F-04-MONAT = T_BSIS-MONAT.
      T_BSIS_F-04-VALUT = T_BSIS-VALUT.
      T_BSIS_F-04-GJAHR = T_BSIS-GJAHR.
      T_BSIS_F-04-HKONT = T_BSIS-HKONT.
      T_BSIS_F-04-ZUONR = T_BSIS-ZUONR.
*{   INSERT         A01K920068                                        3
      T_BSIS_F-04-BELNR   = T_BSIS-BELNR.
      T_BSIS_F-04-PAYTYPE = T_BSIS-PAYTYPE.
*}   INSERT
      T_BSIS_F-04-SGTXT = T_BSIS-SGTXT.
      T_BSIS_F-04-SHKZG = T_BSIS-SHKZG.
      T_BSIS_F-04-WRBTR = T_BSIS-WRBTR.
      T_BSIS_F-04-WAERS = T_BSIS-WAERS.
    ENDIF.

  ENDLOOP.
***

* Get the reconciliation number
  PERFORM 191_GET_RECONCIL_NUMBER CHANGING Y_NUMBER.

*** FB08
* Choose transaction code
  Y_TRANS = C_FB08.

* Fill DBCDATA table
  PERFORM 193_BDCDTAB_FILLING_FB08 TABLES BDCDTAB
                                   USING  T_BSIS_FB08.
* Call transaction
  CALL TRANSACTION Y_TRANS USING  BDCDTAB
                           MODE   C_MOD
                           UPDATE C_UPD
                           MESSAGES INTO Y_MESSTAB.
  Y_FB08_OK = 'N'.

* Recherche du message de succes f5 312
  READ TABLE Y_MESSTAB WITH KEY MSGID = 'F5'
  MSGNR = '312'.

* If the transaction is done update flag
  IF SY-SUBRC = 0.
    CLEAR W_NODOC.
    MOVE Y_MESSTAB-MSGV1 TO W_NODOC.


    Y_FB08_OK = 'Y'.
    LOOP AT T_BSIS WHERE HKONT+3(2) = C_ACCOUNT_NUMBER_13.
      T_BSIS-Y_CALL = 'X'.
      MODIFY T_BSIS.
    ENDLOOP.

* Si succès conservation du dernier message uniquement
    DESCRIBE TABLE Y_MESSTAB LINES W_LINES.
    W_LINES = W_LINES - 1 .
    IF W_LINES >= 1.
      DELETE Y_MESSTAB FROM 1 TO W_LINES.
    ENDIF.
  ENDIF.

* Create record in reconciliation message table
  PERFORM 195_ADD_RECONCIL_MESS TABLES Y_MESSTAB
                                 USING Y_NUMBER
                                       Y_TRANS.
* IF FB08 OK, process F-04
  IF Y_FB08_OK = 'Y'.

***F-04
* Choose transaction code
    Y_TRANS = C_F-04.

    REFRESH Y_MESSTAB.

* Fill DBCDATA table
    PERFORM 197_BDCDTAB_FILLING_F-04 TABLES BDCDTAB
                                            T_BSIS_BELNR
                                      USING T_BSIS_F-04.
* Call transaction
    CALL TRANSACTION Y_TRANS USING  BDCDTAB
                             MODE   C_MOD
                             UPDATE C_UPD
                             MESSAGES INTO Y_MESSTAB.

* Recherche du message de succes f5 312
    READ TABLE Y_MESSTAB WITH KEY MSGID = 'F5'
    MSGNR = '312'.

* If the transaction is done update flag
    IF SY-SUBRC = 0.

      LOOP AT T_BSIS WHERE HKONT+3(2) = C_ACCOUNT_NUMBER_11.
        T_BSIS-Y_CALL = 'X'.
        MODIFY T_BSIS.
      ENDLOOP.

* Si succès conservation du dernier message uniquement
      DESCRIBE TABLE Y_MESSTAB LINES W_LINES.
      W_LINES = W_LINES - 1 .
      IF W_LINES >= 1.
        DELETE Y_MESSTAB FROM 1 TO W_LINES.
      ENDIF.

* Create record in reconciliation message table
      PERFORM 195_ADD_RECONCIL_MESS TABLES Y_MESSTAB
                                     USING Y_NUMBER
                                           Y_TRANS.
    ELSE.

      Y_MESSTAB-MSGTYP = 'E'.
      MODIFY Y_MESSTAB TRANSPORTING MSGTYP
      WHERE MSGTYP NE 'E'.

* Create record in reconciliation message table
      PERFORM 195_ADD_RECONCIL_MESS TABLES Y_MESSTAB
                                     USING Y_NUMBER
                                           Y_TRANS.

      Y_TRANS = C_FBRA.
      REFRESH Y_MESSTAB.

* Renseignement des zones de FBRA
      PERFORM BDCDATA_FBRA TABLES BDCDTAB
        T_BSIS_BELNR
        USING T_BSIS_F-04.

* Call transaction
      CALL TRANSACTION Y_TRANS USING  BDCDTAB
                               MODE   C_MOD
                               UPDATE C_UPD
                               MESSAGES INTO Y_MESSTAB.

* If the transaction is done update flag
      IF SY-SUBRC = 0.

        LOOP AT T_BSIS WHERE HKONT+3(2) = C_ACCOUNT_NUMBER_11.
          T_BSIS-Y_CALL = 'X'.
          MODIFY T_BSIS.
        ENDLOOP.

* Si succès conservation du dernier message uniquement
        DESCRIBE TABLE Y_MESSTAB LINES W_LINES.
        W_LINES = W_LINES - 1 .
        IF W_LINES >= 1.
          DELETE Y_MESSTAB FROM 1 TO W_LINES.
        ENDIF.
      ENDIF.
* Create record in reconciliation message table
        PERFORM 195_ADD_RECONCIL_MESS TABLES Y_MESSTAB
                                       USING Y_NUMBER
                                             Y_TRANS.

        Y_TRANS = C_FB08.
        REFRESH Y_MESSTAB.

* Renseignement des zones de FB08
        PERFORM BDCDATA_FB08 TABLES BDCDTAB
          T_BSIS_BELNR
          USING T_BSIS_F-04.

* Call transaction
        CALL TRANSACTION Y_TRANS USING  BDCDTAB
                                 MODE   C_MOD
                                 UPDATE C_UPD
                                 MESSAGES INTO Y_MESSTAB.

* If the transaction is done update flag
        IF SY-SUBRC = 0.
          LOOP AT T_BSIS WHERE HKONT+3(2) = C_ACCOUNT_NUMBER_11.
            T_BSIS-Y_CALL = 'X'.
            MODIFY T_BSIS.
          ENDLOOP.

* Si succès conservation du dernier message uniquement
          DESCRIBE TABLE Y_MESSTAB LINES W_LINES.
          W_LINES = W_LINES - 1 .
          IF W_LINES >= 1.
            DELETE Y_MESSTAB FROM 1 TO W_LINES.
          ENDIF.

        ENDIF.

* Create record in reconciliation message table
        PERFORM 195_ADD_RECONCIL_MESS TABLES Y_MESSTAB
                                       USING Y_NUMBER
                                             Y_TRANS.

    ENDIF.

  ENDIF.    " y_FB08_OK = 'Y'.

* Create records in reconciliation report table
  PERFORM 199_ADD_BSIS_RECONCIL TABLES T_BSIS
                                 USING Y_NUMBER.

ENDFORM.                               " 19_call_transaction

*******************************************************************
*       FORM 21_REPORT_TRANSACTION
*******************************************************************
*       Authority check BUKRS and KOART
*******************************************************************
*  -->  t_bsis_edit
*  <--
*******************************************************************
FORM 21_REPORT_TRANSACTION.

  DATA: W_RECONCIL(3) TYPE N.
  CLEAR W_LAST_PAGE.
   NEW-PAGE.
 PERFORM 05_HEADER_DETAIL_STAT.

* EMAR20022002
*  WRITE: / 'DETAILS - PAGE:',
*           SY-PAGNO.

  CLEAR T_BSIS_RECONCIL.
  LOOP AT T_BSIS_RECONCIL.

    AT NEW Y_RECONCIL.
      PERFORM 135_HEADER_DETAIL.
    ENDAT.


    W_RECONCIL = T_BSIS_RECONCIL-Y_RECONCIL.
    WRITE:/  SY-VLINE,
             W_RECONCIL,
             SY-VLINE,
             T_BSIS_RECONCIL-BELNR,  " Doc. No.
             SY-VLINE,
         (4) T_BSIS_RECONCIL-BUZEI,  " Item
             SY-VLINE,
        (12) T_BSIS_RECONCIL-BUDAT,  " Posting date
             SY-VLINE,
             T_BSIS_RECONCIL-VALUT,  " Value date
             SY-VLINE,
             T_BSIS_RECONCIL-ZUONR,  " Assignment
             SY-VLINE,
             T_BSIS_RECONCIL-GSBER,  " B.A.
             SY-VLINE,
             T_BSIS_RECONCIL-HKONT,  " Acc. num.
             SY-VLINE,
             T_BSIS_RECONCIL-WRBTR CURRENCY T_BSIS_RECONCIL-WAERS,
                                     " Amount
             T_BSIS_RECONCIL-WAERS,  " Currency
             SY-VLINE.
    CASE T_BSIS_RECONCIL-SHKZG.
      WHEN 'H'.      " Credit
        WRITE: ' C '.
      WHEN 'S'.      " Debit
        WRITE: ' D '.
      WHEN OTHERS.
        WRITE: '   '.
    ENDCASE.

    WRITE: SY-VLINE,
           T_BSIS_RECONCIL-SGTXT,  " Description
           SY-VLINE.

AT END OF Y_RECONCIL.
      WRITE: /1(180) SY-ULINE.
      CLEAR T_RECONCIL_MESS.
      LOOP AT T_RECONCIL_MESS
      WHERE Y_RECONCIL = T_BSIS_RECONCIL-Y_RECONCIL.
        W_RECONCIL = T_RECONCIL_MESS-Y_RECONCIL.
        WRITE:/  SY-VLINE,
                 W_RECONCIL,
                 SY-VLINE,
                 T_RECONCIL_MESS-Y_TRANS,       "Transaction number
                 T_RECONCIL_MESS-Y_MSGTYPE,     "Status
                 T_RECONCIL_MESS-Y_MSGTX,       "Message
            180  SY-VLINE.
      ENDLOOP.     " AT t_reconcil_mess
      WRITE: /1(180) SY-ULINE.

    ENDAT.
  ENDLOOP.     " AT t_bsis_reconcil

*  PERFORM edit_bsis_for_clearing.

ENDFORM.                               " 21_report_transaction

*******************************************************************
*       FORM 191_get_reconcil_number
*******************************************************************
*  -->  t_bsis_reconcil
*  <--  y_number
*******************************************************************
FORM 191_GET_RECONCIL_NUMBER CHANGING Y_NUMBER TYPE I.

  CLEAR Y_NUMBER.

  LOOP AT T_BSIS_RECONCIL.
    IF T_BSIS_RECONCIL-Y_RECONCIL > Y_NUMBER.
      MOVE T_BSIS_RECONCIL-Y_RECONCIL TO Y_NUMBER.
    ENDIF.
  ENDLOOP.
  IF SY-SUBRC = '4'.
    Y_NUMBER = '1'.
  ELSE.
    ADD 1 TO Y_NUMBER.
  ENDIF.

ENDFORM.                               " 191_get_reconcil_number

*******************************************************************
*      Form  193_bdcdtab_filling_fb08
*******************************************************************
*  Filling bdcdtab for call transaction FB08
*******************************************************************
*  -->  bdcdtab t_bsis
*  <--  bdcdtab
*******************************************************************
FORM 193_BDCDTAB_FILLING_FB08 TABLES BDCDTAB STRUCTURE BDCDATA
                              USING  T_BSIS  STRUCTURE T_BSIS_FB08.

  REFRESH BDCDTAB.

*------------screen 0105------------
  BDCDTAB-PROGRAM = 'SAPMF05A'.
  BDCDTAB-DYNPRO = '0105'.
  BDCDTAB-DYNBEGIN = 'X'.
  BDCDTAB-FNAM = ' '.
  BDCDTAB-FVAL = ' '.
  APPEND BDCDTAB.

* Document number
  BDCDTAB-DYNPRO = '0000'.
  BDCDTAB-DYNBEGIN = ' '.
  BDCDTAB-FNAM = 'RF05A-BELNS'.
  BDCDTAB-FVAL = T_BSIS-BELNR.
  APPEND BDCDTAB.

* Company code
  BDCDTAB-DYNPRO = '0000'.
  BDCDTAB-DYNBEGIN = ' '.
  BDCDTAB-FNAM = 'BKPF-BUKRS'.
  BDCDTAB-FVAL = T_BSIS-BUKRS.
  APPEND BDCDTAB.

* Fiscal year
  BDCDTAB-DYNPRO = '0000'.
  BDCDTAB-DYNBEGIN = ' '.
  BDCDTAB-FNAM = 'RF05A-GJAHS'.
  BDCDTAB-FVAL = T_BSIS-GJAHR.
  APPEND BDCDTAB.

* Reversal reason
  BDCDTAB-DYNPRO = '0000'.
  BDCDTAB-DYNBEGIN = ' '.
  BDCDTAB-FNAM = 'UF05A-STGRD'.
  BDCDTAB-FVAL = '02'.
  APPEND BDCDTAB.

* Posting date
  BDCDTAB-DYNPRO = '0000'.
  BDCDTAB-DYNBEGIN = ' '.
  BDCDTAB-FNAM = 'BSIS-BUDAT'.
  WRITE P_AUGDT DD/MM/YYYY TO BDCDTAB-FVAL.
*  bdcdtab-fval = p_augdt.
  APPEND BDCDTAB.

* BDC OK-Code
  BDCDTAB-DYNPRO = '0000'.
  BDCDTAB-DYNBEGIN = ' '.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '/11'.
  APPEND BDCDTAB.

ENDFORM.                               " 193_bdcdtab_filling_fb08

*******************************************************************
*       FORM 195_add_reconcil_mess
*******************************************************************
*  -->  y_messtab y_number
*  <--  t_reconcil_mess
*******************************************************************
FORM 195_ADD_RECONCIL_MESS TABLES Y_MESSTAB  STRUCTURE BDCMSGCOLL
                            USING Y_NUMBER   TYPE I
                                  Y_TRANS    LIKE C_F-04.

  DATA: WV_MSGTX(500).
  DATA: WV_MSGTYPE(11) TYPE C.

  CLEAR Y_MESSTAB.
  LOOP AT Y_MESSTAB.

    SELECT * FROM T100 WHERE SPRSL = SY-LANGU
                         AND ARBGB = Y_MESSTAB-MSGID
                         AND MSGNR = Y_MESSTAB-MSGNR.
      MOVE T100-TEXT TO WV_MSGTX.
      REPLACE '&' WITH Y_MESSTAB-MSGV1 INTO WV_MSGTX.
      CONDENSE WV_MSGTX.
      REPLACE '&' WITH Y_MESSTAB-MSGV2 INTO WV_MSGTX.
      CONDENSE WV_MSGTX.
      REPLACE '&' WITH Y_MESSTAB-MSGV3 INTO WV_MSGTX.
      CONDENSE WV_MSGTX.
      REPLACE '&' WITH Y_MESSTAB-MSGV4 INTO WV_MSGTX.
      CONDENSE WV_MSGTX.

      CASE Y_MESSTAB-MSGTYP.
        WHEN 'I'.
          WRITE 'INFORMATION' TO WV_MSGTYPE.
        WHEN 'W'.
          WRITE 'WARNING' TO WV_MSGTYPE.
        WHEN 'E'.
          WRITE 'ERROR' TO WV_MSGTYPE.
        WHEN 'A'.
          WRITE 'ABEND' TO WV_MSGTYPE.
        WHEN 'X'.
          WRITE 'EXIT' TO WV_MSGTYPE.
        WHEN 'S'.
          WRITE 'SUCCESS' TO WV_MSGTYPE.
      ENDCASE.

      MOVE  Y_NUMBER   TO T_RECONCIL_MESS-Y_RECONCIL.
      MOVE  Y_TRANS    TO T_RECONCIL_MESS-Y_TRANS.
      WRITE WV_MSGTYPE TO T_RECONCIL_MESS-Y_MSGTYPE.
      WRITE WV_MSGTX   TO T_RECONCIL_MESS-Y_MSGTX.
      APPEND T_RECONCIL_MESS.

    ENDSELECT.
  ENDLOOP.

  REFRESH Y_MESSTAB.

ENDFORM.                               " 195_add_reconcil_mess

*******************************************************************
*      Form  197_bdcdtab_filling_f-04
*******************************************************************
*  Filling bdcdtab for call transaction F-04
*******************************************************************
*  -->  bdcdtab t_bsis_belnr t_bsis
*  <--  bdcdtab
*******************************************************************
FORM 197_BDCDTAB_FILLING_F-04
     TABLES BDCDTAB      STRUCTURE BDCDATA
            T_BSIS_BELNR STRUCTURE T_BSIS_BELNR
      USING T_BSIS       STRUCTURE T_BSIS_F-04.

  DATA: W_WRBTR(15)   TYPE N.


  REFRESH BDCDTAB.

*------------screen 0122------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPMF05A'.
  BDCDTAB-DYNPRO   = '0122'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BKPF-BLDAT'.
  WRITE T_BSIS-BLDAT DD/MM/YYYY TO BDCDTAB-FVAL.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BKPF-BLART'.
  BDCDTAB-FVAL = 'Z7'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BKPF-BUKRS'.
  BDCDTAB-FVAL = T_BSIS-BUKRS.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BKPF-BUDAT'.
  WRITE P_AUGDT DD/MM/YYYY TO BDCDTAB-FVAL.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BKPF-MONAT'.
  BDCDTAB-FVAL = P_AUGDT+4(2).
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BKPF-WAERS'.
  BDCDTAB-FVAL = T_BSIS-WAERS.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'FS006-DOCID'.
  BDCDTAB-FVAL = '*'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=SL'.
  APPEND BDCDTAB.
*{   INSERT         A01K920068                                        5

 CLEAR BDCDTAB.
 BDCDTAB-FNAM = 'RF05A-NEWKO'.
 BDCDTAB-FVAL = T_BSIS-HKONT.
 BDCDTAB-FVAL+3(2) = '10'.
  APPEND BDCDTAB.

 CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-NEWBS'.
 IF T_BSIS-SHKZG = 'S'.
    BDCDTAB-FVAL = '50'.
 ELSE.
    BDCDTAB-FVAL = '40'.
  ENDIF.
  APPEND BDCDTAB.

*------------screen 0300------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPMF05A'.
  BDCDTAB-DYNPRO   = '0300'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'BSEG-ZUONR'.

  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BSEG-VALUT'.
  WRITE T_BSIS-VALUT DD/MM/YYYY TO BDCDTAB-FVAL.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BSEG-WRBTR'.
  BDCDTAB-FVAL = T_BSIS-WRBTR.
  WRITE T_BSIS-WRBTR TO W_WRBTR  CURRENCY T_BSIS-WAERS RIGHT-JUSTIFIED.
  BDCDTAB-FVAL = W_WRBTR.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BSEG-ZUONR'.
  BDCDTAB-FVAL = T_BSIS-ZUONR.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_SUBSCR'.
  BDCDTAB-FVAL = 'SAPLKACB 0001BLOCK'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=PA'.
  APPEND BDCDTAB.


*------------screen 0002------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPLKACB'.
  BDCDTAB-DYNPRO   = '0002'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'COBL-GSBER'.
  BDCDTAB-FVAL = T_BSIS-GSBER.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'COBL-FIPOS'.
  BDCDTAB-FVAL = 'BANK'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'COBL-FIPEX'.
  BDCDTAB-FVAL = 'BANK'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'COBL-GSBER'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_SUBSCR'.
  BDCDTAB-FVAL = 'SAPLKACB 0003BLOCK1'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=ENTE'.
  APPEND BDCDTAB.


*}   INSERT

*------------screen 0710------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPMF05A'.
  BDCDTAB-DYNPRO   = '0710'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

*{   REPLACE        A01K920068                                        6
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_CURSOR'.
*\  bdcdtab-fval = 'RF05A-AGKON'.
*\  APPEND bdcdtab.
  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'RF05A-XPOS1(10)'.
  APPEND BDCDTAB.
*}   REPLACE

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-AGBUK'.
  BDCDTAB-FVAL = 'UNES'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-AGKON'.
  BDCDTAB-FVAL = T_BSIS-HKONT.
  BDCDTAB-FVAL+3(2) = '11'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-AGKOA'.
  BDCDTAB-FVAL = 'S'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-XNOPS'.
  BDCDTAB-FVAL = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-XPOS1(01)'.
  BDCDTAB-FVAL = ' '.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-XPOS1(10)'.
  BDCDTAB-FVAL = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=PA'.
  APPEND BDCDTAB.

**------------screen 0731------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPMF05A'.
  BDCDTAB-DYNPRO   = '0731'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

*{   DELETE         A01K920068                                       14
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_CURSOR'.
*\  bdcdtab-fval = 'RF05A-SEL01(01)'.
*\  APPEND bdcdtab.
*}   DELETE


*{   DELETE         A01K920068                                       13
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'RF05A-SEL01(01)'.
*}   DELETE
*{   REPLACE        A01K920068                                       10
*\  bdcdtab-fval = t_bsis-zuonr.


 IF  ( T_BSIS-HKONT+3(7) = '1175012'
 OR T_BSIS-HKONT+3(7) = '1175013'
 OR T_BSIS-HKONT+3(7) = '1175023'
 OR T_BSIS-HKONT+3(7) = '1175033'
 OR T_BSIS-HKONT+3(7) = '1375012'
 OR T_BSIS-HKONT+3(7) = '1375013'
 OR T_BSIS-HKONT+3(7) = '1375023'
 OR T_BSIS-HKONT+3(7) = '1375033' )
 AND T_BSIS-BELNR(2) = '86'
 AND ( T_BSIS-ZUONR_HR+4(1) EQ 1 OR T_BSIS-ZUONR_HR+4(1) EQ 2
       OR T_BSIS-ZUONR_HR+4(1) EQ 3 ) .

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'RF05A-SEL01(01)'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-SEL01(01)'.
  CONCATENATE T_BSIS-ZUONR(7) '0000000' INTO BDCDTAB-FVAL(14).
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-SEL02(01)'.
  CONCATENATE T_BSIS-ZUONR(7) '0999999' INTO BDCDTAB-FVAL(14).
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=PA'.
  APPEND BDCDTAB.

ELSEIF ( T_BSIS-HKONT+3(7) = '1175012'
 OR T_BSIS-HKONT+3(7) = '1175013'
 OR T_BSIS-HKONT+3(7) = '1175023'
 OR T_BSIS-HKONT+3(7) = '1175033'
 OR T_BSIS-HKONT+3(7) = '1375012'
 OR T_BSIS-HKONT+3(7) = '1375013'
 OR T_BSIS-HKONT+3(7) = '1375023'
 OR T_BSIS-HKONT+3(7) = '1375033' )
 AND T_BSIS-BELNR(2) = '86'
 AND T_BSIS-ZUONR_HR+4(1) NE 1
 AND T_BSIS-ZUONR_HR+4(1) NE 2
 AND T_BSIS-ZUONR_HR+4(1) NE 3 .

CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'RF05A-SEL01(01)'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-SEL01(01)'.
  BDCDTAB-FVAL = T_BSIS-ZUONR_HR.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=PA'.
  APPEND BDCDTAB.


ELSE.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'RF05A-SEL01(01)'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-SEL01(01)'.
  BDCDTAB-FVAL(7) = T_BSIS-ZUONR(7).
  APPEND BDCDTAB.

    CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=PA'.
  APPEND BDCDTAB.

ENDIF.

*{   DELETE         A01K920068                                       12
*\  APPEND bdcdtab.
*}   DELETE

*{   DELETE         A01K920068                                       15
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_OKCODE'.
*\  bdcdtab-fval = '=PA'.
*\  APPEND bdcdtab.
*}   DELETE


*------------screen 3100------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPDF05X'.
  BDCDTAB-DYNPRO   = '3100'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.


  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_SUBSCR'.
  BDCDTAB-FVAL = 'SAPDF05X 6103PAGE'.
  APPEND BDCDTAB.


  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'RF05A-ABPOS'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-ABPOS'.
  BDCDTAB-FVAL = '1'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
*{   REPLACE        A01K920068                                        8
*\  bdcdtab-fval = '=AB'.
  BDCDTAB-FVAL = '=BU'.
*}   REPLACE
  APPEND BDCDTAB.
*{   DELETE         A01K920068                                        9
*\
*\**------------screen 0700------------
*\  CLEAR bdcdtab.
*\  bdcdtab-program  = 'SAPMF05A'.
*\  bdcdtab-dynpro   = '0700'.
*\  bdcdtab-dynbegin = 'X'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_CURSOR'.
*\  bdcdtab-fval = 'RF05A-NEWKO'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'RF05A-NEWKO'.
*\  bdcdtab-fval = t_bsis-hkont.
*\  bdcdtab-fval+3(2) = '10'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'RF05A-NEWBS'.
*\  IF t_bsis-shkzg = 'S'.
*\    bdcdtab-fval = '50'.
*\  ELSE.
*\    bdcdtab-fval = '40'.
*\  ENDIF.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_OKCODE'.
*\  bdcdtab-fval = '/00'.
*\  APPEND bdcdtab.
*\
*\*------------screen 0300------------
*\  CLEAR bdcdtab.
*\  bdcdtab-program  = 'SAPMF05A'.
*\  bdcdtab-dynpro   = '0300'.
*\  bdcdtab-dynbegin = 'X'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_CURSOR'.
*\  bdcdtab-fval = 'BSEG-VALUT'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BSEG-VALUT'.
*\  WRITE t_bsis-valut DD/MM/YYYY TO bdcdtab-fval.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BSEG-WRBTR'.
*\  bdcdtab-fval = '*'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_SUBSCR'.
*\  bdcdtab-fval = 'SAPLKACB 0001BLOCK'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_OKCODE'.
*\  bdcdtab-fval = '=BU'.
*\  APPEND bdcdtab.
*\
*\*------------screen 0002------------
*\  CLEAR bdcdtab.
*\  bdcdtab-program  = 'SAPLKACB'.
*\  bdcdtab-dynpro   = '0002'.
*\  bdcdtab-dynbegin = 'X'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'COBL-GSBER'.
*\  bdcdtab-fval = t_bsis-gsber.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'COBL-FIPOS'.
*\  bdcdtab-fval = 'BANK'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'COBL-FIPEX'.
*\  bdcdtab-fval = 'BANK'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_CURSOR'.
*\  bdcdtab-fval = 'COBL-GSBER'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_SUBSCR'.
*\  bdcdtab-fval = 'SAPLKACB 0003BLOCK1'.
*\  APPEND bdcdtab.
*\
*\  CLEAR bdcdtab.
*\  bdcdtab-fnam = 'BDC_OKCODE'.
*\  bdcdtab-fval = '=ENTE'.
*\  APPEND bdcdtab.
*}   DELETE

**------------screen 3100------------
*  CLEAR bdcdtab.
*  bdcdtab-program  = 'SAPDF05X'.
*  bdcdtab-dynpro   = '3100'.
*  bdcdtab-dynbegin = 'X'.
*  APPEND bdcdtab.
*
*  CLEAR bdcdtab.
*  bdcdtab-fnam = 'BDC_CURSOR'.
*  bdcdtab-fval = 'RF05A-ABPOS'.
*  APPEND bdcdtab.
*
*  CLEAR bdcdtab.
*  bdcdtab-fnam = 'RF05A-ABPOS'.
*  bdcdtab-fval = '1'.
*  APPEND bdcdtab.
*
*  CLEAR bdcdtab.
*  bdcdtab-fnam = 'BDC_SUBSCR'.
*  bdcdtab-fval = 'SAPDF05X'.
*  APPEND bdcdtab.
*
*  CLEAR bdcdtab.
*  bdcdtab-fnam = 'BDC_OKCODE'.
*  bdcdtab-fval = '=BU'.            " AEM
*  APPEND bdcdtab.


ENDFORM.                               " 197_bdcdtab_filling_f-04

*******************************************************************
*       FORM 199_add_bsis_reconcil
*******************************************************************
*  -->  t_bsis y_number
*  <--  t_bsis_reconcil
*******************************************************************
FORM 199_ADD_BSIS_RECONCIL TABLES T_BSIS   STRUCTURE T_BSIS_TEMP
                            USING Y_NUMBER TYPE I.

  SORT T_BSIS BY GSBER DESCENDING.

  LOOP AT T_BSIS.
    MOVE-CORRESPONDING T_BSIS TO T_BSIS_RECONCIL.
    T_BSIS_RECONCIL-Y_RECONCIL = Y_NUMBER.
    APPEND T_BSIS_RECONCIL.
  ENDLOOP.

ENDFORM.                               " 199_add_bsis_reconcil

*******************************************************************
*       FORM CHECK_AUTHORITY
*******************************************************************
*       Authority check BUKRS and KOART
*******************************************************************
*  -->
*  <--
*******************************************************************
FORM CHECK_AUTHORITY.

  PERFORM CHECK_AUTHORITY_BUKRS.
  PERFORM CHECK_AUTHORITY_KOART.

ENDFORM.                                           "check_authority


*******************************************************************
*       FORM CHECK_AUTHORITY_BUKRS
*******************************************************************
*       Authority check on compagny code
*******************************************************************
*  -->
*  <--
*******************************************************************
FORM CHECK_AUTHORITY_BUKRS.

  CLEAR Y_T001.
  REFRESH Y_T001.

  SELECT SINGLE * FROM T001
           WHERE BUKRS = P_BUKRS.

  Y_T001 = T001.
  APPEND Y_T001.

  AUTHORITY-CHECK OBJECT 'F_BKPF_BUK'
    ID 'BUKRS' FIELD T001-BUKRS
    ID 'ACTVT' FIELD C_ACTVT.

  IF SY-SUBRC NE 0.
    SET CURSOR FIELD 'P_BUKRS'.
    MESSAGE E113 WITH T001-BUKRS.
  ENDIF.

ENDFORM.                                     "check_authority_bukrs


*******************************************************************
*       FORM CHECK_AUTHORITY_KOART
*******************************************************************
*        Authority check on type of account S
*******************************************************************
*  -->
*  <--
*******************************************************************
FORM CHECK_AUTHORITY_KOART.

  AUTHORITY-CHECK OBJECT 'F_BKPF_KOA'
   ID 'KOART' FIELD C_KOART
   ID 'ACTVT' FIELD C_ACTVT.

  IF SY-SUBRC NE 0.
    MESSAGE E114 WITH TEXT-E01.
  ENDIF.

ENDFORM.                                     "check_authority_koart


*******************************************************************
*      Form  control_house_bank
*******************************************************************
*       text
*******************************************************************
*  -->  t012 t012k
*  <--  t_t012k t_bnka
*******************************************************************
FORM CONTROL_HOUSE_BANK.

  REFRESH: T_T012K,
           T_BNKA.

  SELECT SINGLE * FROM  T012
         WHERE  BUKRS  = P_BUKRS
         AND    HBKID  = P_HBKID.

  IF SY-SUBRC = 0.

    SELECT SINGLE * FROM  BNKA
           WHERE  BANKS  = T012-BANKS
           AND    BANKL  = T012-BANKL.

    IF SY-SUBRC = 0.
      MOVE-CORRESPONDING BNKA TO T_BNKA.
      APPEND T_BNKA.
    ENDIF.

* Get House Bank Accounts
    SELECT SINGLE  * FROM  T012K
           WHERE  BUKRS  = T012-BUKRS
           AND    HBKID  = T012-HBKID
           AND    HKTID  = P_HKTID.

    IF SY-SUBRC = 0.
      MOVE-CORRESPONDING T012K TO T_T012K.
* Get House Bank Account Names
      SELECT SINGLE * FROM  T012T
           WHERE  BUKRS  = T012-BUKRS
           AND    HBKID  = T012-HBKID
           AND    HKTID  = P_HKTID
           AND    SPRAS  = SY-LANGU.
      MOVE-CORRESPONDING T012T TO T_T012K.
      APPEND T_T012K.
    ENDIF.
  ENDIF.

ENDFORM.                                        "control_house_bank


*******************************************************************
*      Form  control_house_bank_account
*******************************************************************
*       identification of bank accounts 13XXXX qnd 11XXXXXX
*******************************************************************
*  -->  y_t001 t_t012k
*  <--  TSako
*******************************************************************
FORM CONTROL_HOUSE_BANK_ACCOUNT.

  DATA: BEGIN OF SKB1TAB,
           BUKRS LIKE SKB1-BUKRS,
           SAKNR LIKE SKB1-SAKNR,
           FDLEV LIKE SKB1-FDLEV,
           XOPVW LIKE SKB1-XOPVW,
         END OF SKB1TAB.

  REFRESH TSAKO.

  LOOP AT Y_T001.
    LOOP AT T_T012K WHERE BUKRS = Y_T001-BUKRS.
      SELECT  BUKRS SAKNR FDLEV XOPVW
        FROM SKB1 INTO SKB1TAB WHERE BUKRS = Y_T001-BUKRS
                                 AND HBKID = T_T012K-HBKID
                                 AND HKTID = T_T012K-HKTID.

* account 10XXXXX TO 15XXXXX
        IF (    SKB1TAB-SAKNR+3(2) = C_ACCOUNT_NUMBER_10
             OR SKB1TAB-SAKNR+3(2) = C_ACCOUNT_NUMBER_11
             OR SKB1TAB-SAKNR+3(2) = C_ACCOUNT_NUMBER_12
             OR SKB1TAB-SAKNR+3(2) = C_ACCOUNT_NUMBER_13
             OR SKB1TAB-SAKNR+3(2) = C_ACCOUNT_NUMBER_14
             OR SKB1TAB-SAKNR+3(2) = C_ACCOUNT_NUMBER_15 ).
          TSAKO-BUKRS = SKB1TAB-BUKRS.
          TSAKO-HKONT = SKB1TAB-SAKNR.
          TSAKO-FDLEV = SKB1TAB-FDLEV.
          TSAKO-XOPVW = SKB1TAB-XOPVW.
          TSAKO-SHKZG = 'H'.
          APPEND TSAKO.
          TSAKO-BUKRS = SKB1TAB-BUKRS.
          TSAKO-HKONT = SKB1TAB-SAKNR.
          TSAKO-FDLEV = SKB1TAB-FDLEV.
          TSAKO-XOPVW = SKB1TAB-XOPVW.
          TSAKO-SHKZG = 'S'.
          APPEND TSAKO.
        ENDIF.
      ENDSELECT.
    ENDLOOP.
  ENDLOOP.

* control: is there any records in tsako.
  SORT TSAKO BY BUKRS HKONT.
  DESCRIBE TABLE TSAKO LINES SY-TFILL.

  IF SY-TFILL EQ 0.
*message e
  ELSEIF SY-TFILL GT 4.
*Message e
  ENDIF.
  READ TABLE TSAKO WITH KEY Y_BQ_AC = 'X'.
  IF   TSAKO-Y_BQ_AC = ' '.
*Message e
  ENDIF.

ENDFORM.                    " control_house_bank_account


*******************************************************************
*      Form  check_clearing_date
*******************************************************************
*
*******************************************************************
*  -->
*  <--
*******************************************************************
FORM CHECK_CLEARING_DATE.

  IF P_AUGDT IS INITIAL.
    MESSAGE E114 WITH TEXT-E02.
  ENDIF.


ENDFORM.                               " check_clearing_date