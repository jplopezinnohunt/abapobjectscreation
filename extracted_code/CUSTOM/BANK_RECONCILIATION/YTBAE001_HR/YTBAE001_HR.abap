REPORT YTBAE001  LINE-SIZE  200
                 LINE-COUNT  65
                 MESSAGE-ID  FG
                 NO STANDARD PAGE HEADING.

*******************************************************************
* PROGRAM        YTBAE001
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
* Date       By      Correction Number & Brief Description  Release
*
* 16/05/2001 S.magal     0001 Correction ?????----------- -------
*
* 16/11/2001 AEM         0002 Reconciliation for SOGE
*
* 28/11/2001 A.Arkwright 0003 Update
*
* 20/02/2002 EMAR20022002
* 11/12/2006 AAHOUNOU11122006 - Optimization of selections
*******************************************************************

*******************************************************************
*                   Tables
*******************************************************************
TABLES: BSIS,     "Accounting: Secondary Index for G/L Account
        T012K,    "House Bank Accounts
        BNKA,     "Bank master record
        T012,     "House Bank
        T012T,    "House Bank Account Names
        SKB1,     "G/L account master (company code)
        T001,     "Company Codes
        T100,     "Messages
        BDCDATA,  "Batch input: New table field structure
        PAYR,     "Payment Medium File
        GLT0.     "G/L account master record transaction figures

*******************************************************************
*                      Data
*******************************************************************
* internal table for correspondance DME/Document  " AEM161101
DATA: BEGIN OF T_CORRESP OCCURS 0,                          " AEM161101
         NUMREF(13) TYPE C,                                 " AEM161101
         BELNR LIKE BKPF-BELNR,                             " AEM161101
*AHOUNOU14032007
         DMBTR LIKE BSIS-DMBTR,
*AHOUNOU14032007
      END OF T_CORRESP.                                     " AEM161101


*Declaration of TABLECONTROL 'T_CONTROL_TEMP' ITSELF
CONTROLS: T_CONTROL_TEMP TYPE TABLEVIEW USING SCREEN 9000.

*Lines of TABLECONTROL 'T_CONTROL_TEMP'
DATA: G_T_CONTROL_TEMP_LINES LIKE SY-TABIX.

*For user command
DATA: OK_CODE     LIKE SY-UCOMM,
      Y_SAVE_CODE LIKE SY-UCOMM.

*Data for summing amount
DATA: W_BALANCE    LIKE BSIS-WRBTR,
      SUM_AMOUNT_A LIKE BSIS-WRBTR,
      SUM_AMOUNT_B LIKE BSIS-WRBTR,
      SUM_AMOUNT_C LIKE BSIS-WRBTR,
      SUM_AMOUNT_D LIKE BSIS-WRBTR.

DATA: W_STATUS TYPE SY-PFKEY.

*Temporary data for edition
DATA: Y_OLD_CHAR(3) TYPE C.
DATA: Y_OLD_WRBTR   LIKE BSIS-WRBTR.

*Line number on screen for Call transaction FBS1
DATA: Y_TABIX4(4) TYPE N.

*Temporary variable for Call transaction FBS1
DATA: Y_FELDN17(17) TYPE N,
      Y_BELNR(17)   TYPE N.

*Control for call transaction
*X = call transaction possible
*space = call transaction not possible
DATA: Y_CONTROL_TRANSACTION(1) TYPE C.


DATA  : W_LINES LIKE SY-TABIX,
        W_NODOC LIKE BSEG-BELNR,
        W_LAST_PAGE(1) TYPE C,
        W_NOPAGE(4) TYPE C,
        WTEXT_K34(16) TYPE C ,
        W_TYP_ENTETE(1) TYPE C.

*******************************************************************
*                      Constants
*******************************************************************
*Constants to identify account number
CONSTANTS: C_ACCOUNT_NUMBER_10 TYPE I VALUE '10',
           C_ACCOUNT_NUMBER_11 TYPE I VALUE '11',
           C_ACCOUNT_NUMBER_12 TYPE I VALUE '12',
           C_ACCOUNT_NUMBER_13 TYPE I VALUE '13',
           C_ACCOUNT_NUMBER_14 TYPE I VALUE '14',
           C_ACCOUNT_NUMBER_15 TYPE I VALUE '15'.

*Datas for call transaction
CONSTANTS: C_MOD     TYPE C VALUE 'E',
***********'A' Display the screens
***********'E' Only display if an error occurs
***********'N' Do not display
           C_UPD     TYPE C VALUE 'S',
           C_FB08(4) TYPE C VALUE 'FB08',
           C_FBRA(4) TYPE C VALUE 'FBRA',
           C_F-04(4) TYPE C VALUE 'F-04'.

*For AUTHORITY-CHECK
CONSTANTS: C_ACTVT(2) TYPE C VALUE '03',
           C_KOART    LIKE BSEG-KOART VALUE 'S'.


*******************************************************************
*                      Internal tables
*******************************************************************
*Compagny definition
DATA: BEGIN OF Y_T001 OCCURS 1.
        INCLUDE STRUCTURE T001.
DATA: END OF Y_T001.

*House bank account
DATA  BEGIN OF T_T012K OCCURS 1.
        INCLUDE STRUCTURE V_T012K.
DATA  END OF T_T012K.

*House bank
DATA  BEGIN OF T_BNKA OCCURS 1.
        INCLUDE STRUCTURE BNKA.
DATA  END OF T_BNKA.

* Information for transaction fb08
DATA: BEGIN OF T_BSIS_FB08,
        BUKRS LIKE BSIS-BUKRS,   "Company code
        BELNR LIKE BSIS-BELNR,   "Accounting document number
        BUDAT LIKE BSIS-BUDAT,   "Posting date in the document
        GJAHR LIKE BSIS-GJAHR,   "Fiscal year
      END OF T_BSIS_FB08.

* Information for transaction f-04
DATA: BEGIN OF T_BSIS_F-04,
        BUKRS     LIKE BSIS-BUKRS,   "Company code
        BUDAT     LIKE BSIS-BUDAT,   "Posting date in the document
        BLDAT     LIKE BSIS-BLDAT,   "Document date in document
        VALUT     LIKE BSIS-VALUT,   "Value date
        MONAT     LIKE BSIS-MONAT,   "Fiscal period
        GJAHR     LIKE BSIS-GJAHR,   "Fiscal year
        GSBER     LIKE BSIS-GSBER,   "Business Area
        HKONT     LIKE BSIS-HKONT,   "General ledger account
        WRBTR     LIKE BSIS-WRBTR,   "Amount in document currency
        SHKZG     LIKE BSIS-SHKZG,   "Debit/credit indicator
        WAERS     LIKE BSIS-WAERS,   "Currency Key
        ZUONR     LIKE BSIS-ZUONR,   "Assignment number
*{   INSERT         A01K920068                                        2
        ZUONR_HR LIKE BSIS-ZUONR,
        BELNR LIKE BSIS-BELNR,
        PAYTYPE(1) TYPE C, "Payment type / Collectif / individuel
*}   INSERT
        SGTXT     LIKE BSIS-SGTXT,   "Item Text
      END OF T_BSIS_F-04.

* Information for transaction f-04 - List of the documents
DATA: BEGIN OF T_BSIS_BELNR OCCURS 0,
        BELNR LIKE BSIS-BELNR.   "Accounting document number
DATA: END OF T_BSIS_BELNR.

*Bank Accounts
DATA: BEGIN OF TSAKO OCCURS 0,
        BUKRS     LIKE T001-BUKRS,
        HKONT     LIKE BSIS-HKONT,
        SHKZG     LIKE BSIS-SHKZG,
        FDLEV     LIKE SKB1-FDLEV,
        XOPVW     LIKE SKB1-XOPVW,
*       House bank account flag
*       Contain X for the account declared in house bank
*       (the first bank account: i.e. acccount 12xxxxx)
        Y_BQ_AC(1) TYPE C,
      END OF TSAKO.

*Editing structure
DATA: BEGIN OF T_BSIS_EDIT OCCURS 0,
        Y_CHAR(3) TYPE C,        "Clearing key
        BUKRS LIKE BSIS-BUKRS,   "Company code
        BELNR LIKE BSIS-BELNR,   "Accounting document number
        BUZEI LIKE BSIS-BUZEI,   "Number of Line Item
        BUDAT LIKE BSIS-BUDAT,   "Posting date in the document
        BLDAT LIKE BSIS-BLDAT,   "Document date in document
        VALUT LIKE BSIS-VALUT,   "Value date
        MONAT LIKE BSIS-MONAT,   "Fiscal period
        GJAHR LIKE BSIS-GJAHR,   "Fiscal year
*{   INSERT         A01K920068                                        3
        ZUONR_HR LIKE BSIS-ZUONR,
       PAYTYPE(1) TYPE C, "Payment type / Collectif / individuel
*}   INSERT
        ZUONR LIKE BSIS-ZUONR,   "Assignment number
        GSBER LIKE BSIS-GSBER,   "Business Area
        SHKZG LIKE BSIS-SHKZG,   "Debit/credit indicator
        HKONT LIKE BSIS-HKONT,   "General ledger account
        WRBTR LIKE BSIS-WRBTR,   "Amount in document currency
        WAERS LIKE BSIS-WAERS,   "Currency Key
        SGTXT LIKE BSIS-SGTXT.   "Item Text
DATA: END OF T_BSIS_EDIT.

*Temporaly structure used for call transaction and edition
DATA: BEGIN OF T_BSIS_TEMP OCCURS 0,
        Y_CHAR(3) TYPE C,        "Clearing key
        BUKRS LIKE BSIS-BUKRS,   "Company code
        BELNR LIKE BSIS-BELNR,   "Accounting document number
        BUZEI LIKE BSIS-BUZEI,   "Number of Line Item
        BUDAT LIKE BSIS-BUDAT,   "Posting date in the document
        BLDAT LIKE BSIS-BLDAT,   "Document date in document
        VALUT LIKE BSIS-VALUT,   "Value date
        MONAT LIKE BSIS-MONAT,   "Fiscal period
        GJAHR LIKE BSIS-GJAHR,   "Fiscal year
*{   INSERT         A01K920068                                        4
        ZUONR_HR LIKE BSIS-ZUONR,
     PAYTYPE(1) TYPE C, "Payment type / Collectif / individuel
*}   INSERT
        ZUONR LIKE BSIS-ZUONR,   "Assignment number
        GSBER LIKE BSIS-GSBER,   "Business Area
        SHKZG LIKE BSIS-SHKZG,   "Debit/credit indicator
        HKONT LIKE BSIS-HKONT,   "General ledger account
        WRBTR LIKE BSIS-WRBTR,   "Amount in document currency
        WAERS LIKE BSIS-WAERS,   "Currency Key
        SGTXT LIKE BSIS-SGTXT,   "Item Text
        Y_CALL(1) TYPE C.        "Flag for call transaction
DATA: END OF T_BSIS_TEMP.

* Tables to edit all reconciliations at the end of the session
DATA: BEGIN OF T_BSIS_RECONCIL OCCURS 0,
        Y_RECONCIL   TYPE I,     "Reconciliation number
        BUKRS LIKE BSIS-BUKRS,   "Company code
        BELNR LIKE BSIS-BELNR,   "Accounting document number
        BUZEI LIKE BSIS-BUZEI,   "Number of Line Item
        BUDAT LIKE BSIS-BUDAT,   "Posting date in the document
        BLDAT LIKE BSIS-BLDAT,   "Document date in document
        VALUT LIKE BSIS-VALUT,   "Value date
        MONAT LIKE BSIS-MONAT,   "Fiscal period
        GJAHR LIKE BSIS-GJAHR,   "Fiscal year
*{   INSERT         A01K920068                                        5
        ZUONR_HR LIKE BSIS-ZUONR,
      PAYTYPE(1) TYPE C, "Payment type / Collectif / individuel
*}   INSERT
        ZUONR LIKE BSIS-ZUONR,   "Assignment number
        GSBER LIKE BSIS-GSBER,   "Business Area
        SHKZG LIKE BSIS-SHKZG,   "Debit/credit indicator
        HKONT LIKE BSIS-HKONT,   "General ledger account
        WRBTR LIKE BSIS-WRBTR,   "Amount in document currency
        WAERS LIKE BSIS-WAERS,   "Currency Key
        SGTXT LIKE BSIS-SGTXT.   "Item Text
"or Transaction status/message
DATA: END OF T_BSIS_RECONCIL.

DATA: BEGIN OF T_RECONCIL_MESS OCCURS 0,
        Y_RECONCIL    TYPE I,    "Reconciliation number
        Y_TRANS(4)    TYPE C,    "Transaction number
        Y_MSGTYPE(11) TYPE C,    "Status
        Y_MSGTX(130)  TYPE C.    "Message
DATA: END OF T_RECONCIL_MESS.

*Table of item to be cleared account all records
DATA: BEGIN OF T_BSIS_TOT OCCURS 0.
*{   INSERT         A01K920068                                        6
DATA : ZUONR_HR LIKE BSIS-ZUONR.
DATA : PAYTYPE(1) TYPE C. "Payment type / Collectif / individuel
*}   INSERT
        INCLUDE STRUCTURE BSIS.
DATA:   Y_CHAR(3) TYPE C.
DATA: END OF T_BSIS_TOT.

*Table of item to be cleared
DATA: BEGIN OF T_BSIS_ALL OCCURS 0.
        INCLUDE STRUCTURE BSIS.
*{   INSERT         A01K920068                                        7
DATA : ZUONR_HR LIKE BSIS-ZUONR.
DATA : PAYTYPE(1) TYPE C. "Payment type / Collectif / individuel
*}   INSERT
DATA: END OF T_BSIS_ALL.
*{   INSERT         A01K920068                                        1
*Table of item to be cleared
DATA: BEGIN OF T_BSIS_ALL_HR OCCURS 0.
        INCLUDE STRUCTURE BSIS.
DATA : ZUONR_HR LIKE BSIS-ZUONR.
DATA : PAYTYPE(1) TYPE C. "Payment type / Collectif / individuel
DATA: END OF T_BSIS_ALL_HR.
*}   INSERT

*Data of item reconciliated
*Table of item to be cleared
DATA: BEGIN OF T_BSEG_ALL OCCURS 0.
        INCLUDE STRUCTURE BSEG.
DATA: END OF T_BSEG_ALL.

DATA: BEGIN OF T_BKPF.
        INCLUDE STRUCTURE BKPF.
DATA: END OF T_BKPF.

DATA: BEGIN OF T_BSEG.
        INCLUDE STRUCTURE BSEG.
DATA: END OF T_BSEG.

* Table inyterne / Payment Medium File
DATA: BEGIN OF T_PAYR.
        INCLUDE STRUCTURE PAYR.
DATA: END OF T_PAYR.

*Table of Messages
DATA: BEGIN OF Y_MESSTAB OCCURS 0.
        INCLUDE STRUCTURE BDCMSGCOLL.
DATA: END OF Y_MESSTAB.

*Tables for call transaction
DATA: BEGIN OF BDCDTAB OCCURS 0.
        INCLUDE STRUCTURE BDCDATA.
DATA: END OF BDCDTAB.

*Sub-total for clearing account
DATA: BEGIN OF T_SUBTOTAL OCCURS 0,
        Y_CHAR(3) TYPE C,
        WRBTR     LIKE BSIS-WRBTR,
        ABS_WRBTR LIKE BSIS-WRBTR,  "Sub-total amount for sorting
        WAERS     LIKE BSIS-WAERS.
DATA: END OF T_SUBTOTAL.



*******************************************************************
*                      selection screen
*******************************************************************
SELECTION-SCREEN BEGIN OF BLOCK 1 WITH FRAME.
PARAMETERS: P_BUKRS LIKE BSEG-BUKRS DEFAULT 'UNES' OBLIGATORY,
            P_HBKID LIKE T012-HBKID  OBLIGATORY,
            P_HKTID LIKE T012K-HKTID OBLIGATORY,
            P_BUDAT LIKE BSIS-BUDAT  OBLIGATORY DEFAULT SY-DATUM.
SELECTION-SCREEN END OF BLOCK 1.


SELECTION-SCREEN BEGIN OF BLOCK 2 WITH FRAME.
PARAMETERS: P_STATE RADIOBUTTON GROUP RADI,
            P_RECON RADIOBUTTON GROUP RADI.
SELECTION-SCREEN END OF BLOCK 2.

SELECTION-SCREEN BEGIN OF BLOCK 3 WITH FRAME TITLE TEXT-F01.
PARAMETERS: P_AUGDT LIKE BSEG-AUGDT.
SELECTION-SCREEN END OF BLOCK 3.

*******************************************************************
*                     INITIALIZATION
*******************************************************************
INITIALIZATION.

*******************************************************************
*                     AT SELECTION-SCREEN
*******************************************************************
AT SELECTION-SCREEN.

  PERFORM CHECK_AUTHORITY.
  PERFORM CONTROL_HOUSE_BANK.
  PERFORM CONTROL_HOUSE_BANK_ACCOUNT.
  IF P_RECON = 'X'.
    PERFORM CHECK_CLEARING_DATE.
  ENDIF.


*******************************************************************
*                     START-OF-SELECTION
*******************************************************************
START-OF-SELECTION.

  IF P_RECON = 'X'.
    SET PF-STATUS 'RECO'.
* Select non reconcilated documents
    PERFORM 01_SELECT_BSIS.
  ENDIF.
********************************************************************
  IF P_STATE = 'X'.
    SET PF-STATUS 'STAT'.
* Select reconcilated and non reconcilated documents
    PERFORM 03_SELECT_BSEG.
    PERFORM 04_SELECT_BALANCE.
  ENDIF.

*******************************************************************
*                     END-OF-SELECTION
*******************************************************************
END-OF-SELECTION.

* Initialisations EMAR20022002
  PERFORM INITIALISATIONS.

  PERFORM 05_HEADER_DETAIL_STAT.
  PERFORM 09_SET_CORRESPONDANCE.                            " AEM161101

  IF P_STATE = 'X'.
    PERFORM 07_EDITION_STAT.
  ENDIF.
  IF P_RECON = 'X'.
    PERFORM 11_SORT_BSIS_FOR_CLEARING.
    PERFORM 13_EDIT_BSIS_FOR_CLEARING.
  ENDIF.

*******************************************************************
*                      AT LINE-SELECTION
*******************************************************************
* at line-selection is processed whenever a line is selected with F2.
AT LINE-SELECTION.

* Generate temporary table corresponding to the selected records
  CLEAR T_BSIS_TEMP.
  REFRESH T_BSIS_TEMP.
  LOOP AT T_BSIS_EDIT WHERE Y_CHAR = SY-LISEL+15(3).
    MOVE-CORRESPONDING T_BSIS_EDIT TO T_BSIS_TEMP.
    APPEND T_BSIS_TEMP.
  ENDLOOP.
  DESCRIBE TABLE T_BSIS_TEMP LINES T_CONTROL_TEMP-LINES.

* "Change of clearing key" event
  IF SY-CUCOL BETWEEN 3 AND 19
 AND SY-LISEL+2(12) = TEXT-110.
    CALL SCREEN 9000 STARTING AT 1 1."  ENDING AT 100 30.
    IF Y_SAVE_CODE = 'VALI'.
      PERFORM 15_UPDATE_ITEMS.
      PERFORM 05_HEADER_DETAIL_STAT.
      PERFORM 13_EDIT_BSIS_FOR_CLEARING.
      SY-LSIND = 0.
    ENDIF.
  ENDIF.

* "Reconciliation" event
  IF SY-CUCOL BETWEEN 23 AND 36
 AND SY-LISEL+21(14) = TEXT-001.
*   Validity control before call transaction
    PERFORM 17_CONTROL_TRANSACTION TABLES T_BSIS_TEMP
                                   CHANGING Y_CONTROL_TRANSACTION.
*   Control Ok for call transaction
    IF Y_CONTROL_TRANSACTION = SPACE.
*     Call trasaction FB08 and f-04
      PERFORM 19_CALL_TRANSACTION TABLES T_BSIS_TEMP
                                         BDCDTAB
                                         Y_MESSTAB.

*     If call transaction ok
*     refresh t_bsis_edit, refresh t_subtotal and edit again
      LOOP AT  T_BSIS_TEMP WHERE Y_CALL = 'X'.
        LOOP AT T_BSIS_EDIT WHERE BUKRS = T_BSIS_TEMP-BUKRS
                              AND BELNR = T_BSIS_TEMP-BELNR
                              AND BUZEI = T_BSIS_TEMP-BUZEI
                              AND ZUONR = T_BSIS_TEMP-ZUONR.
          DELETE T_BSIS_EDIT.
        ENDLOOP.
        LOOP AT T_SUBTOTAL WHERE Y_CHAR = T_BSIS_TEMP-Y_CHAR.
          DELETE T_SUBTOTAL.
        ENDLOOP.
      ENDLOOP.

      PERFORM 05_HEADER_DETAIL_STAT.
      PERFORM 13_EDIT_BSIS_FOR_CLEARING.
      SY-LSIND = 0.
    ENDIF.

  ENDIF.

*******************************************************************
*                      AT USER-COMMAND
*******************************************************************
AT USER-COMMAND.

* mise en commentaire EMAR20022002
** Clearing key is determined and total = 0.
*  LOOP AT t_subtotal WHERE wrbtr NE space
*                     AND  y_char NE space.*
*
*    LOOP AT t_bsis_edit WHERE y_char = t_subtotal-y_char.
*
** ???????????*
*
*    ENDLOOP.
*  ENDLOOP.
* fin mise en commentaire EMAR20022002

  CASE SY-UCOMM.
    WHEN 'LIST'.
* "Edition of operations report
      SET PF-STATUS 'LIST'.
      CLEAR W_NOPAGE.
      MOVE '0000' TO W_NOPAGE.
      PERFORM 21_REPORT_TRANSACTION.

  ENDCASE.


*******************************************************************
*                      TOP OF PAGE Pour REPORT
*******************************************************************
TOP-OF-PAGE .

* Affichage du n° de page
  ADD 1 TO W_NOPAGE.
  MOVE TEXT-K34 TO WTEXT_K34.
  REPLACE '&' WITH W_NOPAGE INTO WTEXT_K34.

  GET PF-STATUS W_STATUS.

  IF W_STATUS NE 'RECO'.

    WRITE :  100 WTEXT_K34  .

* Affichage des colonnes si pas dernière page
    IF W_LAST_PAGE NE 'X'.

* Type d'entete EMAR20022002
      IF W_TYP_ENTETE EQ '1'.

        ULINE AT /(133) .
* Editing sub_total header
        PERFORM 0711_HEADER_SUB_TOTAL_AC.

      ELSEIF W_TYP_ENTETE EQ '2'.

        ULINE AT /(133).
* Editing sub_total header
        PERFORM 0731_HEADER_SUB_TOTAL_BD.

      ENDIF.

    ENDIF.

  ENDIF.

TOP-OF-PAGE DURING LINE-SELECTION.

* Affichage du n° de page
  ADD 1 TO W_NOPAGE.
  MOVE TEXT-K34 TO WTEXT_K34.
  REPLACE '&' WITH W_NOPAGE INTO WTEXT_K34.

  GET PF-STATUS W_STATUS.

  IF W_STATUS EQ 'LIST'.
    WRITE :  100 WTEXT_K34  .
  ENDIF.
*******************************************************************
*                   Includes
*******************************************************************
INCLUDE YTBAM002_HR.
*  include ytbam002.
INCLUDE YTBAM003_HR.
*  include ytbam003.
INCLUDE YTBAM004_HR.
*  include ytbam004.

*&---------------------------------------------------------------------*
*&      Form  initialisations
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*  -->  p1        text
*  <--  p2        text
*----------------------------------------------------------------------*
FORM INITIALISATIONS.

  CLEAR : W_NOPAGE, W_LAST_PAGE , W_TYP_ENTETE.
  MOVE '0000' TO W_NOPAGE.

ENDFORM.                    " initialisations