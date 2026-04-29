REPORT YTBAE002 LINE-SIZE  200
                 LINE-COUNT  65
                 MESSAGE-ID  FG
                 NO STANDARD PAGE HEADING.

**********************************************************************
* CHANGE HISTORY
*--------------------------------------------------------------------*
* Date       By           Brief Description & Release
*--------------------------------------------------------------------*
* 24/10/2007 D.Andros     First delivery.
*                         Only reporting part is revised and updated.
*                         0.7
*
*
**********************************************************************

*Constants to identify account number
CONSTANTS: GC_ACCOUNT_NUMBER_10 TYPE I VALUE '10',
           GC_ACCOUNT_NUMBER_11 TYPE I VALUE '11',
           GC_ACCOUNT_NUMBER_12 TYPE I VALUE '12',
           GC_ACCOUNT_NUMBER_13 TYPE I VALUE '13',
           GC_ACCOUNT_NUMBER_14 TYPE I VALUE '14',
           GC_ACCOUNT_NUMBER_15 TYPE I VALUE '15'.

* For transaction calls
CONSTANTS: GC_MOD     TYPE C VALUE 'E',
***********'A' Display the screens
***********'E' Only display if an error occurs
***********'N' Do not display
           GC_UPD     TYPE C VALUE 'S',
           GC_FB08(4) TYPE C VALUE 'FB08',
           GC_FBRA(4) TYPE C VALUE 'FBRA',
           GC_F04(4)  TYPE C VALUE 'F-04'.

* For authority checks
CONSTANTS: GC_ACTVT(2)  TYPE C VALUE '03',
           GC_KOART     TYPE KOART VALUE 'S'.

*....................................................................*
*   Data
*....................................................................*
* internal table for correspondance DME/Document  " AEM161101
DATA: BEGIN OF GT_CORRESP OCCURS 0,
         NUMREF(13) TYPE C,
         BELNR LIKE BKPF-BELNR,
      END OF GT_CORRESP.


*Declaration of TABLECONTROL 'T_CONTROL_TEMP' ITSELF
CONTROLS: T_CONTROL_TEMP TYPE TABLEVIEW USING SCREEN 9000.

*Lines of TABLECONTROL 'T_CONTROL_TEMP'
DATA: G_T_CONTROL_TEMP_LINES LIKE SY-TABIX.

*For user command
DATA: OK_CODE     LIKE SY-UCOMM,
      Y_SAVE_CODE LIKE SY-UCOMM.

*Data for summing amount
DATA: SUM_AMOUNT_A LIKE BSIS-WRBTR,
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

DATA: GD_ACCOUNT_CR_FRWD LIKE FDBL_BALANCE_LINE-BALANCE,
      GD_ACCOUNT_DEBIT   LIKE FDBL_BALANCE_LINE-DEBIT,
      GD_ACCOUNT_CREDIT  LIKE FDBL_BALANCE_LINE-CREDIT,
      GD_ACCOUNT_BALANCE LIKE FDBL_BALANCE_LINE-BALANCE,
      GD_SAKNR           LIKE SKA1-SAKNR,
      GD_CURTP           LIKE RFPDO2-ALLGCRTP,
      GD_STIDA           LIKE RFPDO-ALLGSTID.

DATA: GD_YEAR TYPE GJAHR.

DATA: GD_RC TYPE SYSUBRC,
      GD_RETURN   TYPE C.

* Ranges needed to call ldb
DATA: GR_SAKNR    TYPE RANGE OF SAKNR,
      GR_SAKNR_OI TYPE RANGE OF SAKNR,
      GR_BUKRS    TYPE RANGE OF BUKRS,
      GR_GJAHR    TYPE RANGE OF GJAHR,
      GR_AUGDT    TYPE RANGE OF AUGDT,
      GR_GSBER    TYPE RANGE OF GSBER.

DATA: BEGIN OF GS_BUKRS,
        SIGN(1)   TYPE C,
        OPTION(2) TYPE C,
        LOW       TYPE BUKRS,
        HIGH      TYPE BUKRS,
      END OF GS_BUKRS.

DATA: BEGIN OF GS_SAKNR,
        SIGN(1)   TYPE C,
        OPTION(2) TYPE C,
        LOW       TYPE SAKNR,
        HIGH      TYPE SAKNR,
      END OF GS_SAKNR.

DATA: BEGIN OF GS_GJAHR,
        SIGN(1)   TYPE C,
        OPTION(2) TYPE C,
        LOW       TYPE GJAHR,
        HIGH      TYPE GJAHR,
      END OF GS_GJAHR.

DATA: BEGIN OF GS_AUGDT,
        SIGN(1)   TYPE C,
        OPTION(2) TYPE C,
        LOW       TYPE GJAHR,
        HIGH      TYPE GJAHR,
      END OF GS_AUGDT.

DATA: GS_PARAMS   LIKE RSPARAMS.

DATA: GT_BALANCE  TYPE FDBL_BALANCE.

* House bank account
DATA GT_T012K TYPE STANDARD TABLE OF V_T012K WITH HEADER LINE.

* House bank
DATA GT_BNKA TYPE STANDARD TABLE OF BNKA WITH HEADER LINE.

* Information for transaction fb08
DATA: BEGIN OF GS_BSIS_FB08,
        BUKRS LIKE BSIS-BUKRS,   "Company code
        BELNR LIKE BSIS-BELNR,   "Accounting document number
        BUDAT LIKE BSIS-BUDAT,   "Posting date in the document
        GJAHR LIKE BSIS-GJAHR,   "Fiscal year
      END OF GS_BSIS_FB08.

* Information for transaction f-04
DATA: BEGIN OF GS_BSIS_F04,
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
        SGTXT     LIKE BSIS-SGTXT,   "Item Text
      END OF GS_BSIS_F04.

* Information for transaction f-04 - List of the documents
DATA: BEGIN OF GT_BSIS_BELNR OCCURS 0,
        BELNR LIKE BSIS-BELNR.
DATA: END OF GT_BSIS_BELNR.

*Editing structure
DATA: BEGIN OF GT_BSIS_EDIT OCCURS 0,
        Y_CHAR(3) TYPE C,        "Clearing key
        BUKRS LIKE BSIS-BUKRS,   "Company code
        BELNR LIKE BSIS-BELNR,   "Accounting document number
        BUZEI LIKE BSIS-BUZEI,   "Number of Line Item
        BUDAT LIKE BSIS-BUDAT,   "Posting date in the document
        BLDAT LIKE BSIS-BLDAT,   "Document date in document
        VALUT LIKE BSIS-VALUT,   "Value date
        MONAT LIKE BSIS-MONAT,   "Fiscal period
        GJAHR LIKE BSIS-GJAHR,   "Fiscal year
        ZUONR LIKE BSIS-ZUONR,   "Assignment number
        GSBER LIKE BSIS-GSBER,   "Business Area
        SHKZG LIKE BSIS-SHKZG,   "Debit/credit indicator
        HKONT LIKE BSIS-HKONT,   "General ledger account
        WRBTR LIKE BSIS-WRBTR,   "Amount in document currency
        WAERS LIKE BSIS-WAERS,   "Currency Key
        SGTXT LIKE BSIS-SGTXT.   "Item Text
DATA: END OF GT_BSIS_EDIT.

*Temporaly structure used for call transaction and edition
DATA: BEGIN OF GT_BSIS_TEMP OCCURS 0,
        Y_CHAR(3) TYPE C,        "Clearing key
        BUKRS LIKE BSIS-BUKRS,   "Company code
        BELNR LIKE BSIS-BELNR,   "Accounting document number
        BUZEI LIKE BSIS-BUZEI,   "Number of Line Item
        BUDAT LIKE BSIS-BUDAT,   "Posting date in the document
        BLDAT LIKE BSIS-BLDAT,   "Document date in document
        VALUT LIKE BSIS-VALUT,   "Value date
        MONAT LIKE BSIS-MONAT,   "Fiscal period
        GJAHR LIKE BSIS-GJAHR,   "Fiscal year
        ZUONR LIKE BSIS-ZUONR,   "Assignment number
        GSBER LIKE BSIS-GSBER,   "Business Area
        SHKZG LIKE BSIS-SHKZG,   "Debit/credit indicator
        HKONT LIKE BSIS-HKONT,   "General ledger account
        WRBTR LIKE BSIS-WRBTR,   "Amount in document currency
        WAERS LIKE BSIS-WAERS,   "Currency Key
        SGTXT LIKE BSIS-SGTXT,   "Item Text
        Y_CALL(1) TYPE C.        "Flag for call transaction
DATA: END OF GT_BSIS_TEMP.

* Tables to edit all reconciliations at the end of the session
DATA: BEGIN OF GT_BSIS_RECONCIL OCCURS 0,
        Y_RECONCIL   TYPE I,     "Reconciliation number
        BUKRS LIKE BSIS-BUKRS,   "Company code
        BELNR LIKE BSIS-BELNR,   "Accounting document number
        BUZEI LIKE BSIS-BUZEI,   "Number of Line Item
        BUDAT LIKE BSIS-BUDAT,   "Posting date in the document
        BLDAT LIKE BSIS-BLDAT,   "Document date in document
        VALUT LIKE BSIS-VALUT,   "Value date
        MONAT LIKE BSIS-MONAT,   "Fiscal period
        GJAHR LIKE BSIS-GJAHR,   "Fiscal year
        ZUONR LIKE BSIS-ZUONR,   "Assignment number
        GSBER LIKE BSIS-GSBER,   "Business Area
        SHKZG LIKE BSIS-SHKZG,   "Debit/credit indicator
        HKONT LIKE BSIS-HKONT,   "General ledger account
        WRBTR LIKE BSIS-WRBTR,   "Amount in document currency
        WAERS LIKE BSIS-WAERS,   "Currency Key
        SGTXT LIKE BSIS-SGTXT.   "Item Text
"or Transaction status/message
DATA: END OF GT_BSIS_RECONCIL.

DATA: BEGIN OF GT_RECONCIL_MESS OCCURS 0,
        Y_RECONCIL    TYPE I,    "Reconciliation number
        Y_TRANS(4)    TYPE C,    "Transaction number
        Y_MSGTYPE(11) TYPE C,    "Status
        Y_MSGTX(130)  TYPE C.    "Message
DATA: END OF GT_RECONCIL_MESS.

*Table of item to be cleared account all records
DATA: BEGIN OF GT_BSIS_TOT OCCURS 0.
        INCLUDE STRUCTURE BSIS.
DATA:   Y_CHAR(3) TYPE C.
DATA: END OF GT_BSIS_TOT.

*Table of item to be cleared
DATA: BEGIN OF GT_BSIS_ALL OCCURS 0.
        INCLUDE STRUCTURE BSIS.
DATA: END OF GT_BSIS_ALL.

DATA: BEGIN OF GS_BSIS.
        INCLUDE STRUCTURE BSIS.
DATA: END OF GS_BSIS.

DATA: BEGIN OF GS_BSEG.
        INCLUDE STRUCTURE BSEG.
DATA: END OF GS_BSEG.

DATA: BEGIN OF GS_PAYR.
        INCLUDE STRUCTURE PAYR.
DATA: END OF GS_PAYR.

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



*....................................................................*
*   selection screen
*....................................................................*
SELECTION-SCREEN BEGIN OF BLOCK BLOCK10 WITH FRAME.
PARAMETERS: GP_BUKRS LIKE BSEG-BUKRS DEFAULT 'UNES' OBLIGATORY,
            GP_HBKID LIKE T012-HBKID  OBLIGATORY,
            GP_HKTID LIKE T012K-HKTID OBLIGATORY,
            GP_BUDAT LIKE BSIS-BUDAT  OBLIGATORY DEFAULT SY-DATUM.
SELECTION-SCREEN END OF BLOCK BLOCK10.


SELECTION-SCREEN BEGIN OF BLOCK BLOCK20 WITH FRAME.
PARAMETERS: GP_STATE RADIOBUTTON GROUP RADI DEFAULT 'X',
            GP_RECON RADIOBUTTON GROUP RADI.
SELECTION-SCREEN END OF BLOCK BLOCK20.

SELECTION-SCREEN BEGIN OF BLOCK BLOCK30 WITH FRAME TITLE TEXT-F01.
PARAMETERS: GP_AUGDT LIKE BSEG-AUGDT.
SELECTION-SCREEN END OF BLOCK BLOCK30.

*....................................................................*
*   initialization
*....................................................................*
INITIALIZATION.
  LOOP AT SCREEN.
    IF   SCREEN-NAME = 'GP_STATE'
      OR SCREEN-NAME = 'GP_RECON'
      OR SCREEN-NAME = 'GP_AUGDT'.
      SCREEN-INVISIBLE = 0.
      SCREEN-INPUT = 0.
      MODIFY SCREEN.
    ENDIF.

  ENDLOOP.

*....................................................................*
*   at selection-screen
*....................................................................*
AT SELECTION-SCREEN.

*...perform validations..............................................*
  PERFORM CHECK_AUTHORITY.
  PERFORM HOUSE_BANK_VALIDATE.
  IF GP_RECON = 'X'.
    PERFORM CHECK_CLEARING_DATE.
  ENDIF.

*...get house bank accounts..........................................*
  PERFORM HOUSE_BANK_ACCOUNTS_GET.

*....................................................................*
*   start-of-selection
*....................................................................*
START-OF-SELECTION.

  IF GP_RECON = 'X'.
    SET PF-STATUS 'RECO'.
  ENDIF.

  IF GP_STATE = 'X'.
    SET PF-STATUS 'STAT'.
  ENDIF.

*...get local range for company code.................................*
  REFRESH GR_BUKRS.
  GS_BUKRS-SIGN   = 'I'.
  GS_BUKRS-OPTION = 'EQ'.
  CLEAR GS_BUKRS-HIGH.
  GS_BUKRS-LOW    = GP_BUKRS.
  APPEND GS_BUKRS TO GR_BUKRS.

*...get local range for fiscal year..................................*
  REFRESH GR_GJAHR.
  GS_GJAHR-SIGN   = 'I'.
  GS_GJAHR-OPTION = 'EQ'.
  CLEAR GS_GJAHR-HIGH.
  GS_GJAHR-LOW    = GP_BUDAT(4).
  APPEND GS_GJAHR TO GR_GJAHR.

*...get local range for clearing date................................*
  REFRESH GR_AUGDT.
  GS_AUGDT-SIGN   = 'I'.
  GS_AUGDT-OPTION = 'EQ'.
  CLEAR GS_AUGDT-HIGH.
  GS_AUGDT-LOW    = GP_AUGDT.
  APPEND GS_AUGDT TO GR_AUGDT.

*...set default to "Company code currency"
  IF GD_CURTP IS INITIAL OR GD_CURTP EQ '00'.
    GD_CURTP = '10'.
  ENDIF.

*...set key date for open items
  GD_STIDA = GP_BUDAT.

*...check, if all company codes given use the same fiscal year.....*
  PERFORM CHECK_FISCAL_YEARS USING GR_BUKRS
                                   GD_RC.
  IF GD_RC NE 0.
    MESSAGE I021(FDBL).
    RETURN.
  ENDIF.

*...get open items
  PERFORM PROC_LDB_CALL USING GR_SAKNR_OI 'BSIS'.

*...get balance for 10xxxxx
  IF GP_STATE = 'X'.
    PERFORM PROC_LDB_CALL USING GR_SAKNR 'SKC1C'.
  ENDIF.


*....................................................................*
*   end-of-selection
*....................................................................*
END-OF-SELECTION.

  " init variables
  CLEAR : W_NOPAGE, W_LAST_PAGE , W_TYP_ENTETE.
  MOVE '0000' TO W_NOPAGE.

  PERFORM OUTPUT_HEADER_DETAIL_STAT.
  PERFORM PROC_SET_CORRESPONDANCE.

  IF GP_STATE = 'X'.
    PERFORM OUTPUT_SUBTOTAL_A.
    PERFORM OUTPUT_SUBTOTAL_B.
    PERFORM OUTPUT_SUBTOTAL_C.
    PERFORM OUTPUT_SUBTOTAL_D.
    PERFORM OUTPUT_BALANCE.
  ENDIF.

*  if GP_RECON = 'X'.
*    perform PROC_BSIS_SORT.
*    perform PROC_BSIS_EDIT.
*  endif.

*....................................................................*
*   at line-selection
*....................................................................*
* at line-selection is processed whenever a line is selected with F2.
AT LINE-SELECTION.

* Generate temporary table corresponding to the selected records
  CLEAR GT_BSIS_TEMP.
  REFRESH GT_BSIS_TEMP.
  LOOP AT GT_BSIS_EDIT WHERE Y_CHAR = SY-LISEL+15(3).
    MOVE-CORRESPONDING GT_BSIS_EDIT TO GT_BSIS_TEMP.
    APPEND GT_BSIS_TEMP.
  ENDLOOP.
  DESCRIBE TABLE GT_BSIS_TEMP LINES T_CONTROL_TEMP-LINES.

* "Change of clearing key" event
  IF SY-CUCOL BETWEEN 3 AND 19
 AND SY-LISEL+2(12) = TEXT-110.
    CALL SCREEN 9000 STARTING AT 1 1."  ENDING AT 100 30.
    IF Y_SAVE_CODE = 'VALI'.
      PERFORM PROC_BSIS_UPDATE_ITEMS.
      PERFORM OUTPUT_HEADER_DETAIL_STAT.
      PERFORM PROC_BSIS_EDIT.
      SY-LSIND = 0.
    ENDIF.
  ENDIF.

* "Reconciliation" event
  IF SY-CUCOL BETWEEN 23 AND 36
 AND SY-LISEL+21(14) = TEXT-001.
*   Validity control before call transaction
    PERFORM CHECK_TRANSACTION TABLES GT_BSIS_TEMP
                                   CHANGING Y_CONTROL_TRANSACTION.
*   Control Ok for call transaction
    IF Y_CONTROL_TRANSACTION = SPACE.
*     Call trasaction FB08 and f-04
      PERFORM PROC_CALL_TRANSACTION TABLES GT_BSIS_TEMP
                                         BDCDTAB
                                         Y_MESSTAB.

*     If call transaction ok
*     refresh GT_BSIS_EDIT, refresh t_subtotal and edit again
      LOOP AT  GT_BSIS_TEMP WHERE Y_CALL = 'X'.
        LOOP AT GT_BSIS_EDIT WHERE BUKRS = GT_BSIS_TEMP-BUKRS
                              AND BELNR = GT_BSIS_TEMP-BELNR
                              AND BUZEI = GT_BSIS_TEMP-BUZEI
                              AND ZUONR = GT_BSIS_TEMP-ZUONR.
          DELETE GT_BSIS_EDIT.
        ENDLOOP.
        LOOP AT T_SUBTOTAL WHERE Y_CHAR = GT_BSIS_TEMP-Y_CHAR.
          DELETE T_SUBTOTAL.
        ENDLOOP.
      ENDLOOP.

      PERFORM OUTPUT_HEADER_DETAIL_STAT.
      PERFORM PROC_BSIS_EDIT.
      SY-LSIND = 0.
    ENDIF.

  ENDIF.

*....................................................................*
*   at user-command
*....................................................................*
AT USER-COMMAND.

  CASE SY-UCOMM.
    WHEN 'LIST'.
* "Edition of operations report
      SET PF-STATUS 'LIST'.
      CLEAR W_NOPAGE.
      MOVE '0000' TO W_NOPAGE.
      PERFORM OUTPUT_REPORT_TRANSACTION.

  ENDCASE.


*....................................................................*
*   top-of-page
*....................................................................*
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
        PERFORM OUTPUT_HEADER_SUB_TOTAL_AC.

      ELSEIF W_TYP_ENTETE EQ '2'.

        ULINE AT /(133).
* Editing sub_total header
        PERFORM OUTPUT_HEADER_SUB_TOTAL_BD.

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

*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM CHECK_TRANSACTION
                TABLES T_BSIS    STRUCTURE GT_BSIS_TEMP
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
      IF (     T_BSIS-HKONT+3(2) NE GC_ACCOUNT_NUMBER_13
           AND T_BSIS-HKONT+3(2) NE GC_ACCOUNT_NUMBER_11 ).
        Y_CONTROL = 'X'.
        MESSAGE I398(00) WITH TEXT-014.
      ENDIF.

* Control business area
      IF (     T_BSIS-HKONT+3(2) = GC_ACCOUNT_NUMBER_11
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
    IF T_BSIS-HKONT+3(2) = GC_ACCOUNT_NUMBER_11.
      Y_OLD_GSBER = T_BSIS-GSBER.
    ENDIF.

* Control number of document with account 13xxxxx
    IF T_BSIS-HKONT+3(2) = GC_ACCOUNT_NUMBER_13.
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
    IF T_BSIS-HKONT+3(2) = GC_ACCOUNT_NUMBER_11.
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


ENDFORM.                    "CONTROL_TRANSACTION
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_CALL_TRANSACTION TABLES T_BSIS    STRUCTURE GT_BSIS_TEMP
                                BDCDTAB   STRUCTURE BDCDATA
                                Y_MESSTAB STRUCTURE BDCMSGCOLL.

  DATA: Y_TRANS(4) TYPE C.
  DATA: Y_NUMBER   TYPE I.
  DATA: Y_FB08_OK TYPE C. "Y : transaction fb08 OK
  "N : transaction fb08 KO

*** Get informations
  CLEAR T_BSIS.
  CLEAR GS_BSIS_FB08.
  CLEAR GS_BSIS_F04.
  REFRESH GT_BSIS_BELNR.

  LOOP AT T_BSIS.

* Get information for the transaction fb08
    IF T_BSIS-HKONT+3(2) = GC_ACCOUNT_NUMBER_13.
      GS_BSIS_FB08-BUKRS = T_BSIS-BUKRS.
      GS_BSIS_FB08-BELNR = T_BSIS-BELNR.
      GS_BSIS_FB08-BUDAT = T_BSIS-BUDAT.
      GS_BSIS_FB08-GJAHR = T_BSIS-GJAHR.
    ENDIF.

    IF T_BSIS-HKONT+3(2) = GC_ACCOUNT_NUMBER_11.
      GS_BSIS_F04-GSBER  = T_BSIS-GSBER.
      GT_BSIS_BELNR-BELNR = T_BSIS-BELNR.
*AHOUNOU15032007
      GS_BSIS_F04-ZUONR = T_BSIS-ZUONR.
*AHOUNOU15032007
      APPEND GT_BSIS_BELNR.
    ENDIF.

*Get information for the transaction f-04
    IF T_BSIS-HKONT+3(2) = GC_ACCOUNT_NUMBER_13.
      GS_BSIS_F04-BUKRS = T_BSIS-BUKRS.
      GS_BSIS_F04-BUDAT = T_BSIS-BUDAT.
      GS_BSIS_F04-BLDAT = T_BSIS-BLDAT.
      GS_BSIS_F04-MONAT = T_BSIS-MONAT.
      GS_BSIS_F04-VALUT = T_BSIS-VALUT.
      GS_BSIS_F04-GJAHR = T_BSIS-GJAHR.
      GS_BSIS_F04-HKONT = T_BSIS-HKONT.
      GS_BSIS_F04-ZUONR = T_BSIS-ZUONR.
      GS_BSIS_F04-SGTXT = T_BSIS-SGTXT.
      GS_BSIS_F04-SHKZG = T_BSIS-SHKZG.
      GS_BSIS_F04-WRBTR = T_BSIS-WRBTR.
      GS_BSIS_F04-WAERS = T_BSIS-WAERS.
    ENDIF.

  ENDLOOP.
***

* Get the reconciliation number
  PERFORM PROC_RECONCIL_GET CHANGING Y_NUMBER.

*** FB08
* Choose transaction code
  Y_TRANS = GC_FB08.

* Fill DBCDATA table
  PERFORM BDC_DTAB_FILLING_FB08 TABLES BDCDTAB
                                   USING  GS_BSIS_FB08.
* Call transaction
  CALL TRANSACTION Y_TRANS USING  BDCDTAB
                           MODE   GC_MOD
                           UPDATE GC_UPD
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
    LOOP AT T_BSIS WHERE HKONT+3(2) = GC_ACCOUNT_NUMBER_13.
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
  PERFORM PROC_RECONCIL_MESS_ADD TABLES Y_MESSTAB
                                 USING Y_NUMBER
                                       Y_TRANS.
* IF FB08 OK, process F-04
  IF Y_FB08_OK = 'Y'.

***F-04
* Choose transaction code
    Y_TRANS = GC_F04.

    REFRESH Y_MESSTAB.

* Fill DBCDATA table
    PERFORM BDC_DTAB_FILLING_F04 TABLES BDCDTAB
                                            GT_BSIS_BELNR
                                      USING GS_BSIS_F04.
* Call transaction
    CALL TRANSACTION Y_TRANS USING  BDCDTAB
                             MODE   GC_MOD
                             UPDATE GC_UPD
                             MESSAGES INTO Y_MESSTAB.

* Recherche du message de succes f5 312
    READ TABLE Y_MESSTAB WITH KEY MSGID = 'F5'
    MSGNR = '312'.

* If the transaction is done update flag
    IF SY-SUBRC = 0.

      LOOP AT T_BSIS WHERE HKONT+3(2) = GC_ACCOUNT_NUMBER_11.
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
      PERFORM PROC_RECONCIL_MESS_ADD TABLES Y_MESSTAB
                                     USING Y_NUMBER
                                           Y_TRANS.
    ELSE.

      Y_MESSTAB-MSGTYP = 'E'.
      MODIFY Y_MESSTAB TRANSPORTING MSGTYP
      WHERE MSGTYP NE 'E'.

* Create record in reconciliation message table
      PERFORM PROC_RECONCIL_MESS_ADD TABLES Y_MESSTAB
                                     USING Y_NUMBER
                                           Y_TRANS.

      Y_TRANS = GC_FBRA.
      REFRESH Y_MESSTAB.

* Renseignement des zones de FBRA
      PERFORM BDC_DATA_FBRA TABLES BDCDTAB
        GT_BSIS_BELNR
        USING GS_BSIS_F04.

* Call transaction
      CALL TRANSACTION Y_TRANS USING  BDCDTAB
                               MODE   GC_MOD
                               UPDATE GC_UPD
                               MESSAGES INTO Y_MESSTAB.

* If the transaction is done update flag
      IF SY-SUBRC = 0.

        LOOP AT T_BSIS WHERE HKONT+3(2) = GC_ACCOUNT_NUMBER_11.
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
      PERFORM PROC_RECONCIL_MESS_ADD TABLES Y_MESSTAB
                                     USING Y_NUMBER
                                           Y_TRANS.

      Y_TRANS = GC_FB08.
      REFRESH Y_MESSTAB.

* Renseignement des zones de FB08
      PERFORM BDC_DATA_FB08 TABLES BDCDTAB
        GT_BSIS_BELNR
        USING GS_BSIS_F04.

* Call transaction
      CALL TRANSACTION Y_TRANS USING  BDCDTAB
                               MODE   GC_MOD
                               UPDATE GC_UPD
                               MESSAGES INTO Y_MESSTAB.

* If the transaction is done update flag
      IF SY-SUBRC = 0.
        LOOP AT T_BSIS WHERE HKONT+3(2) = GC_ACCOUNT_NUMBER_11.
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
      PERFORM PROC_RECONCIL_MESS_ADD TABLES Y_MESSTAB
                                     USING Y_NUMBER
                                           Y_TRANS.

    ENDIF.

  ENDIF.    " y_FB08_OK = 'Y'.

* Create records in reconciliation report table
  PERFORM PROC_RECONCIL_ADD TABLES T_BSIS
                                 USING Y_NUMBER.

ENDFORM.                    "PROC_CALL_TRANSACTION
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_RECONCIL_MESS_ADD TABLES Y_MESSTAB  STRUCTURE BDCMSGCOLL
                            USING Y_NUMBER   TYPE I
                                  Y_TRANS    LIKE GC_F04.

  DATA BEGIN OF W_T100.
          INCLUDE STRUCTURE T100.
  DATA END OF W_T100.
  DATA: WV_MSGTX(500).
  DATA: WV_MSGTYPE(11) TYPE C.

  CLEAR Y_MESSTAB.
  LOOP AT Y_MESSTAB.

    SELECT * FROM T100 INTO W_T100
                       WHERE SPRSL = SY-LANGU
                         AND ARBGB = Y_MESSTAB-MSGID
                         AND MSGNR = Y_MESSTAB-MSGNR.
      MOVE W_T100-TEXT TO WV_MSGTX.
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

      MOVE  Y_NUMBER   TO GT_RECONCIL_MESS-Y_RECONCIL.
      MOVE  Y_TRANS    TO GT_RECONCIL_MESS-Y_TRANS.
      WRITE WV_MSGTYPE TO GT_RECONCIL_MESS-Y_MSGTYPE.
      WRITE WV_MSGTX   TO GT_RECONCIL_MESS-Y_MSGTX.
      APPEND GT_RECONCIL_MESS.

    ENDSELECT.
  ENDLOOP.

  REFRESH Y_MESSTAB.

ENDFORM.                    "PROC_RECONCIL_MESS_ADD
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_RECONCIL_GET CHANGING Y_NUMBER TYPE I.

  CLEAR Y_NUMBER.

  LOOP AT GT_BSIS_RECONCIL.
    IF GT_BSIS_RECONCIL-Y_RECONCIL > Y_NUMBER.
      MOVE GT_BSIS_RECONCIL-Y_RECONCIL TO Y_NUMBER.
    ENDIF.
  ENDLOOP.
  IF SY-SUBRC = '4'.
    Y_NUMBER = '1'.
  ELSE.
    ADD 1 TO Y_NUMBER.
  ENDIF.

ENDFORM.                    "PROC_RECONCIL_GET
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_RECONCIL_ADD TABLES T_BSIS   STRUCTURE GT_BSIS_TEMP
                            USING Y_NUMBER TYPE I.

  SORT T_BSIS BY GSBER DESCENDING.

  LOOP AT T_BSIS.
    MOVE-CORRESPONDING T_BSIS TO GT_BSIS_RECONCIL.
    GT_BSIS_RECONCIL-Y_RECONCIL = Y_NUMBER.
    APPEND GT_BSIS_RECONCIL.
  ENDLOOP.

ENDFORM.                    "PROC_RECONCIL_ADD
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM CHECK_AUTHORITY.

  PERFORM CHECK_AUTHORITY_BUKRS.
  PERFORM CHECK_AUTHORITY_KOART.

ENDFORM.                    "CHECK_AUTHORITY
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM CHECK_AUTHORITY_BUKRS.

  DATA BEGIN OF W_T001.
          INCLUDE STRUCTURE T001.
  DATA END OF W_T001.

  SELECT SINGLE * FROM T001 INTO W_T001
           WHERE BUKRS = GP_BUKRS.

  AUTHORITY-CHECK OBJECT 'F_BKPF_BUK'
    ID 'BUKRS' FIELD W_T001-BUKRS
    ID 'ACTVT' FIELD GC_ACTVT.

  IF SY-SUBRC NE 0.
    SET CURSOR FIELD 'GP_BUKRS'.
    MESSAGE E113 WITH W_T001-BUKRS.
  ENDIF.

ENDFORM.                                     "check_authority_bukrs
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM CHECK_AUTHORITY_KOART.

  AUTHORITY-CHECK OBJECT 'F_BKPF_KOA'
   ID 'KOART' FIELD GC_KOART
   ID 'ACTVT' FIELD GC_ACTVT.

  IF SY-SUBRC NE 0.
    MESSAGE E114 WITH TEXT-E01.
  ENDIF.

ENDFORM.                                     "check_authority_koart
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM HOUSE_BANK_VALIDATE.

  DATA BEGIN OF LS_BNKA.
          INCLUDE STRUCTURE BNKA.
  DATA END OF LS_BNKA.
  DATA BEGIN OF LS_T012.
          INCLUDE STRUCTURE T012.
  DATA END OF LS_T012.
  DATA BEGIN OF LS_T012K.
          INCLUDE STRUCTURE T012K.
  DATA END OF LS_T012K.
  DATA BEGIN OF LS_T012T.
          INCLUDE STRUCTURE T012T.
  DATA END OF LS_T012T.

  REFRESH: GT_T012K,  "holds info on account 10xxxxx + house bank
           GT_BNKA.   "holds info on house bank

* Get house bank by "Company Code" and "Short key for a house bank"
  SELECT SINGLE * FROM T012 INTO LS_T012
         WHERE  BUKRS  = GP_BUKRS
         AND    HBKID  = GP_HBKID.

  IF SY-SUBRC = 0.

* Get Bank master record by "Bank Country Key" and "Bank Key"
    SELECT SINGLE * FROM BNKA INTO LS_BNKA
           WHERE  BANKS  = LS_T012-BANKS
           AND    BANKL  = LS_T012-BANKL.

    IF SY-SUBRC = 0.
      MOVE-CORRESPONDING LS_BNKA TO GT_BNKA.
      APPEND GT_BNKA.

* GET HOUSE BANK ACCOUNTS (APPARANTLY THE FIRST ONE)
* by "Company Code" and "Short key for a house bank"
      SELECT SINGLE * FROM T012K INTO LS_T012K
             WHERE  BUKRS  = LS_T012-BUKRS
             AND    HBKID  = LS_T012-HBKID
             AND    HKTID  = GP_HKTID.

      IF SY-SUBRC = 0.
        MOVE-CORRESPONDING LS_T012K TO GT_T012K.

* Get House Bank name
        SELECT SINGLE * FROM  T012T INTO LS_T012T
             WHERE  BUKRS  = LS_T012-BUKRS
             AND    HBKID  = LS_T012-HBKID
             AND    HKTID  = GP_HKTID
             AND    SPRAS  = SY-LANGU.

        MOVE-CORRESPONDING LS_T012T TO GT_T012K.
        APPEND GT_T012K.

      ENDIF.
    ENDIF.
  ENDIF.

ENDFORM.                                        "HOUSE_BANK_VALIDATE
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM HOUSE_BANK_ACCOUNTS_GET.

  DATA: BEGIN OF W_SKB1,
    SAKNR LIKE SKB1-SAKNR,
    XOPVW LIKE SKB1-XOPVW.
  DATA: END OF W_SKB1.

  REFRESH GR_SAKNR.

  SELECT SAKNR XOPVW FROM SKB1 INTO W_SKB1
       WHERE BUKRS EQ GP_BUKRS
         AND HBKID EQ GP_HBKID
         AND HKTID EQ GP_HKTID.

    IF (    W_SKB1-SAKNR+3(2) = GC_ACCOUNT_NUMBER_10
         OR W_SKB1-SAKNR+3(2) = GC_ACCOUNT_NUMBER_12
         OR W_SKB1-SAKNR+3(2) = GC_ACCOUNT_NUMBER_14 ).

      GS_SAKNR-SIGN   = 'I'.
      GS_SAKNR-OPTION = 'EQ'.
      GS_SAKNR-LOW    = W_SKB1-SAKNR.
      GS_SAKNR-HIGH   = W_SKB1-SAKNR.
      APPEND GS_SAKNR TO GR_SAKNR.

    ELSEIF ( W_SKB1-SAKNR+3(2) = GC_ACCOUNT_NUMBER_11
          OR W_SKB1-SAKNR+3(2) = GC_ACCOUNT_NUMBER_13
          OR W_SKB1-SAKNR+3(2) = GC_ACCOUNT_NUMBER_15 ).

      IF W_SKB1-XOPVW EQ 'X'.
        GS_SAKNR-SIGN   = 'I'.
        GS_SAKNR-OPTION = 'EQ'.
        GS_SAKNR-LOW    = W_SKB1-SAKNR.
        GS_SAKNR-HIGH   = W_SKB1-SAKNR.
        APPEND GS_SAKNR TO GR_SAKNR_OI.
      ENDIF.

    ENDIF.

  ENDSELECT.

ENDFORM.                    "HOUSE_BANK_ACCOUNTS_GET
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM CHECK_CLEARING_DATE.

  IF GP_AUGDT IS INITIAL.
    MESSAGE E114 WITH TEXT-E02.
  ENDIF.


ENDFORM.                               " check_clearing_date
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_BSIS USING PS_BSIS LIKE GS_BSIS.

  IF (     PS_BSIS-HKONT+3(2) = GC_ACCOUNT_NUMBER_11
        OR PS_BSIS-HKONT+3(2) = GC_ACCOUNT_NUMBER_13  ).

    MOVE-CORRESPONDING PS_BSIS TO GT_BSIS_TOT.
    APPEND GT_BSIS_TOT.

  ENDIF.

ENDFORM.                                         " SELECT_BSIS
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_BSEG USING PS_BSEG LIKE GS_BSEG.

*  data: begin of LS_BKPF.
*          include structure BKPF.
*  data: end of LS_BKPF.

  CHECK PS_BSEG-AUGDT IS INITIAL
    OR  PS_BSEG-AUGDT GT GP_BUDAT.

*  select single * from BKPF
*    into corresponding fields of LS_BKPF
*                  where BUKRS = PS_BSEG-BUKRS
*                    and BELNR = PS_BSEG-BELNR
*                    and GJAHR = PS_BSEG-GJAHR
*                    and BUDAT le GP_BUDAT.

  IF SY-SUBRC EQ 0.
    MOVE-CORRESPONDING PS_BSEG TO GT_BSIS_ALL.
*    move-corresponding LS_BKPF to GT_BSIS_ALL.
    APPEND GT_BSIS_ALL.
  ENDIF.

  IF (     PS_BSEG-HKONT+3(2) = GC_ACCOUNT_NUMBER_11
        OR PS_BSEG-HKONT+3(2) = GC_ACCOUNT_NUMBER_13
        OR PS_BSEG-HKONT+3(2) = GC_ACCOUNT_NUMBER_15 ).

    MOVE-CORRESPONDING PS_BSEG TO GT_BSIS_TOT.
    APPEND GT_BSIS_TOT.

  ENDIF.

ENDFORM.                    "SELECT_BSEG
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_BALANCE USING PS_SKC1C STRUCTURE SKC1C
                        PD_ALLPERIODS TYPE C.

  DATA: LS_BALANCE_DATA TYPE FDBL_BALANCE_DATA_LINE,
        LS_BALANCE      TYPE FDBL_BALANCE_LINE.


  DATA: BEGIN OF LD_DEBIT_FIELD,
          TABLE(8) TYPE C VALUE 'PS_SKC1C',
          DASH(1)  TYPE C VALUE '-',
          FIELD    TYPE FIELDNAME,
        END OF LD_DEBIT_FIELD.


  DATA: BEGIN OF LD_CREDIT_FIELD,
          TABLE(8) TYPE C VALUE 'PS_SKC1C',
          DASH(1)  TYPE C VALUE '-',
          FIELD    TYPE FIELDNAME,
        END OF LD_CREDIT_FIELD.


  DATA: BEGIN OF LD_BALANCE_FIELD,
          TABLE(8) TYPE C VALUE 'PS_SKC1C',
          DASH(1)  TYPE C VALUE '-',
          FIELD    TYPE FIELDNAME,
        END OF LD_BALANCE_FIELD.


  DATA: BEGIN OF LD_CUM_FIELD,
          TABLE(8) TYPE C VALUE 'PS_SKC1C',
          DASH(1)  TYPE C VALUE '-',
          FIELD    TYPE FIELDNAME,
        END OF LD_CUM_FIELD.


  DATA: LD_DEBIT_CUM  LIKE FDBL_BALANCE_LINE-DEBIT,
        LD_CREDIT_CUM LIKE FDBL_BALANCE_LINE-CREDIT.


  DATA: LD_TABIX LIKE SY-TABIX,
        LD_POPER LIKE T009B-POPER,
        LD_PERIV LIKE T009B-PERIV.

  " Total of the Debit Postings for the Month
  " Accumulated balance as of fiscal month end
  FIELD-SYMBOLS: <LFS_VALUE> LIKE SKC1C-UM01S,
                 <LFS_CUM>   LIKE SKC1C-UM01K.


*...clear internal structures
  CLEAR LS_BALANCE.


*...get fiscal year variant for current company code
  SELECT SINGLE PERIV INTO LD_PERIV FROM T001
                      WHERE BUKRS = PS_SKC1C-BUKRS.

*...get transaction figures for each period
  CLEAR LS_BALANCE.
  CLEAR LD_DEBIT_CUM.
  CLEAR LD_CREDIT_CUM.
  LD_DEBIT_FIELD-FIELD   = 'WM00S'.
  LD_CREDIT_FIELD-FIELD  = 'WM00H'.
  LD_BALANCE_FIELD-FIELD = 'WM00O'.
  LD_CUM_FIELD-FIELD     = 'WM00K'.


  DO 16 TIMES.
    IF SY-INDEX LT 10.
      LD_DEBIT_FIELD-FIELD+2(1)    = '0'.
      LD_CREDIT_FIELD-FIELD+2(1)   = '0'.
      LD_BALANCE_FIELD-FIELD+2(1)  = '0'.
      LD_CUM_FIELD-FIELD+2(1)      = '0'.
      LD_DEBIT_FIELD-FIELD+3(1)    = SY-INDEX.
      LD_CREDIT_FIELD-FIELD+3(1)   = SY-INDEX.
      LD_BALANCE_FIELD-FIELD+3(1)  = SY-INDEX.
      LD_CUM_FIELD-FIELD+3(1)      = SY-INDEX.
    ELSE.
      LD_DEBIT_FIELD-FIELD+2(2)    = SY-INDEX.
      LD_CREDIT_FIELD-FIELD+2(2)   = SY-INDEX.
      LD_BALANCE_FIELD-FIELD+2(2)  = SY-INDEX.
      LD_CUM_FIELD-FIELD+2(2)      = SY-INDEX.
    ENDIF.

    LS_BALANCE-PERIOD(2)   = SY-INDEX.
    CLEAR LS_BALANCE-PERIOD+2.

    ASSIGN (LD_DEBIT_FIELD)  TO <LFS_VALUE>.
    LS_BALANCE-DEBIT       = <LFS_VALUE>.

    ASSIGN (LD_CREDIT_FIELD)  TO <LFS_VALUE>.
    LS_BALANCE-CREDIT      =  <LFS_VALUE>.

    ASSIGN (LD_BALANCE_FIELD)  TO <LFS_VALUE>.
    LS_BALANCE-BALANCE     = <LFS_VALUE>.

    ASSIGN (LD_CUM_FIELD)  TO <LFS_CUM>.
    LS_BALANCE-BALANCE_CUM = <LFS_CUM>.

    LD_DEBIT_CUM           = LD_DEBIT_CUM  + LS_BALANCE-DEBIT.
    LD_CREDIT_CUM          = LD_CREDIT_CUM + LS_BALANCE-CREDIT.

    LD_POPER = SY-INDEX.

    IF SY-SUBRC NE 0.
      LS_BALANCE-MONTH = LD_POPER.
    ENDIF.

    COLLECT LS_BALANCE INTO GT_BALANCE.

  ENDDO.

ENDFORM.                    "PROC_BALANCE
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM CHECK_FISCAL_YEARS USING PR_BUKRS LIKE GR_BUKRS
                              PD_RC    TYPE SYSUBRC.

  DATA: LD_PERIV      TYPE PERIV,
        LD_PERIV_TEMP TYPE PERIV.

*...initialize return code.............................................*

  PD_RC = 0.

*...check fiscal year variant of company codes given...................*

  SELECT PERIV INTO LD_PERIV_TEMP FROM T001 WHERE BUKRS IN PR_BUKRS.
    IF LD_PERIV IS INITIAL.
      LD_PERIV = LD_PERIV_TEMP.
    ENDIF.

    IF LD_PERIV NE LD_PERIV_TEMP.
      PD_RC = 4.
      EXIT.
    ENDIF.
  ENDSELECT.


ENDFORM.                    "CHECK_FISCAL_YEARS
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_BUILD_COSEL TABLES PT_COSEL STRUCTURE COSEL
                 USING  PR_BUKRS LIKE GR_BUKRS
                        PR_SAKNR LIKE GR_SAKNR
                        PR_GJAHR LIKE GR_GJAHR
                        PR_AUGDT LIKE GR_AUGDT
                        PR_GSBER LIKE GR_GSBER
                        PD_CURTP LIKE RFPDO2-ALLGCRTP
                        PD_STIDA LIKE RFPDO-ALLGSTID.

  DATA: LR_BUKRS TYPE RANGE OF BUKRS WITH HEADER LINE,
        LR_SAKNR TYPE RANGE OF SAKNR WITH HEADER LINE,
        LR_GJAHR TYPE RANGE OF GJAHR WITH HEADER LINE,
        LR_AUGDT TYPE RANGE OF AUGDT WITH HEADER LINE,
        LR_GSBER TYPE RANGE OF GSBER WITH HEADER LINE.

*...move selections into local ranges..................................*
  LR_BUKRS[] = PR_BUKRS[].
  LR_SAKNR[] = PR_SAKNR[].
  LR_GJAHR[] = PR_GJAHR[].
  LR_AUGDT[] = PR_AUGDT[].
  LR_GSBER[] = PR_GSBER[].

*...build COSEL-table for "normal" selection fields....................*
  PT_COSEL-FIELD = 'BUKRS'.
  LOOP AT LR_BUKRS.
    MOVE-CORRESPONDING LR_BUKRS TO PT_COSEL.
    APPEND PT_COSEL.
  ENDLOOP.

  PT_COSEL-FIELD = 'SAKNR'.
  LOOP AT LR_SAKNR.
    MOVE-CORRESPONDING LR_SAKNR TO PT_COSEL.
    APPEND PT_COSEL.
  ENDLOOP.

  PT_COSEL-FIELD = 'GJAHR'.
  LOOP AT LR_GJAHR.
    MOVE-CORRESPONDING LR_GJAHR TO PT_COSEL.
    APPEND PT_COSEL.
  ENDLOOP.

  PT_COSEL-FIELD = 'AUGDT'.
  LOOP AT LR_AUGDT.
    MOVE-CORRESPONDING LR_AUGDT TO PT_COSEL.
    APPEND PT_COSEL.
  ENDLOOP.

  PT_COSEL-FIELD = 'GSBER'.
  LOOP AT LR_GSBER.
    MOVE-CORRESPONDING LR_GSBER TO PT_COSEL.
    APPEND PT_COSEL.
  ENDLOOP.

  IF SY-SUBRC NE 0.
    PT_COSEL-SIGN   = 'I'.
    PT_COSEL-OPTION = 'CP'.
    PT_COSEL-LOW    = '*'.
    CLEAR PT_COSEL-HIGH.
    APPEND PT_COSEL.
  ENDIF.


  PT_COSEL-FIELD = 'CURTP'.
  PT_COSEL-LOW   = PD_CURTP.
  APPEND PT_COSEL.

  PT_COSEL-FIELD = 'STIDA'.
  PT_COSEL-LOW   = PD_STIDA.
  APPEND PT_COSEL.

  PT_COSEL-FIELD = 'RTCUR'.
  PT_COSEL-LOW   = '*'.
  APPEND PT_COSEL.

ENDFORM.                    "PROC_BUILD_COSEL
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_BUILD_RSPARAMS TABLES PT_COSEL  TYPE TCOSEL
                                PT_PARAMS STRUCTURE RSPARAMS
                         USING  PD_LDB    LIKE TRDIR-LDBNAME.


  CONSTANTS: LC_SELNAME_GSBER LIKE RSPARAMS-SELNAME VALUE 'SD_GSB_S'.


*...refresh return table...............................................*

  REFRESH PT_PARAMS.


*...process all entries in table PT_COSEL..............................*

  LOOP AT PT_COSEL.
    CASE PT_COSEL-FIELD.
      WHEN 'GSBER'.
        PT_PARAMS-SELNAME = LC_SELNAME_GSBER.
      WHEN OTHERS.
        PT_PARAMS-SELNAME(2)   = PD_LDB(2).
        PT_PARAMS-SELNAME+2(1) = '_'.
        PT_PARAMS-SELNAME+3    = PT_COSEL-FIELD.
    ENDCASE.
    MOVE-CORRESPONDING PT_COSEL TO PT_PARAMS.
    APPEND PT_PARAMS.
  ENDLOOP.


ENDFORM.                    "PROC_BUILD_RSPARAMS
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_LDB_CALLBACK USING PD_NODE LIKE LDBN-LDBNODE
                        PD_WORKAREA
                        PD_MODE     TYPE C
                        PD_SELECTED TYPE C.

  DATA: LS_SKC1C LIKE SKC1C,
        LS_BSEG  LIKE GS_BSEG,
        LS_BSIS  LIKE GS_BSIS.

  CASE PD_NODE.

    WHEN 'SKC1C'.
      LS_SKC1C = PD_WORKAREA.
      PERFORM PROC_BALANCE USING LS_SKC1C 'X'.

*    when 'BSEG'.
*      move-corresponding PD_WORKAREA to LS_BSEG.
*      perform PROC_BSEG using LS_BSEG.

    WHEN 'BSIS'.
      MOVE-CORRESPONDING PD_WORKAREA TO LS_BSIS.
      PERFORM PROC_BSIS USING LS_BSIS.

  ENDCASE.

  PD_SELECTED = 'X'.

ENDFORM.                    "PROS_LDB_CALLBACK
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_LDB_CALL USING PR_SAKNR LIKE GR_SAKNR
                         PD_NODE LIKE LDBN-LDBNODE.

  CONSTANTS: LC_LDB  TYPE TRDIR-LDBNAME VALUE 'SDF'.

  DATA: LT_COSEL     TYPE TCOSEL,
        LT_PARAMS    TYPE STANDARD TABLE OF RSPARAMS,
        LT_CALLBACKS TYPE STANDARD TABLE OF LDBCB.


*...build table with selection criteria..............................*
  PERFORM PROC_BUILD_COSEL TABLES LT_COSEL
                           USING  GR_BUKRS
                                  PR_SAKNR
                                  GR_GJAHR
                                  GR_AUGDT
                                  GR_GSBER
                                  GD_CURTP
                                  GD_STIDA.

*...build table with selections for LDB................................*
  PERFORM PROC_BUILD_RSPARAMS TABLES LT_COSEL
                                     LT_PARAMS
                              USING  LC_LDB.

*...build table with callbacks.........................................*
  PERFORM PROC_BUILD_CALLBACK TABLES LT_CALLBACKS
                              USING  PD_NODE.

*...get transaction data...............................................*
  CALL FUNCTION 'LDB_PROCESS'
    EXPORTING
      LDBNAME                     = LC_LDB
    TABLES
      CALLBACK                    = LT_CALLBACKS
      SELECTIONS                  = LT_PARAMS
    EXCEPTIONS
      LDB_SELECTIONS_NOT_ACCEPTED = 4
      OTHERS                      = 1.

ENDFORM.                    "proc_ldb_call
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_BUILD_CALLBACK TABLES PT_CALLBACK STRUCTURE LDBCB
                          USING PD_NODE LIKE LDBN-LDBNODE.

  PT_CALLBACK-LDBNODE     = PD_NODE.
  PT_CALLBACK-GET         = 'X'.
  PT_CALLBACK-GET_LATE    = ' '.
  PT_CALLBACK-CB_PROG     = SY-REPID.
  PT_CALLBACK-CB_FORM     = 'PROC_LDB_CALLBACK'.
  APPEND PT_CALLBACK.

ENDFORM.                    "PROC_BUILD_CALLBACK
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_SET_CORRESPONDANCE.

  DATA BEGIN OF LS_PAYR.
          INCLUDE STRUCTURE PAYR.
  DATA END OF LS_PAYR.

  DATA: BEGIN OF LT_BELEG OCCURS 0.
          INCLUDE STRUCTURE DTA_BELEGE.
  DATA: END OF LT_BELEG.

  DATA: W_VBLNR_C(10) TYPE C.

* Get correspondance
  REFRESH GT_CORRESP.
  CLEAR GT_BSIS_ALL.

  LOOP AT GT_BSIS_ALL.

    CHECK GT_BSIS_ALL-HKONT+3(2) = GC_ACCOUNT_NUMBER_11
       OR GT_BSIS_ALL-HKONT+3(2) = GC_ACCOUNT_NUMBER_13.

    CASE GT_BSIS_ALL-ZUONR(3).
* DME File
      WHEN 'DME'.
* Get documents corresponding to a DME
        CALL FUNCTION 'GET_DOCUMENTS'
          EXPORTING
            I_REFNO       = GT_BSIS_ALL-ZUONR+3(10)
          TABLES
            TAB_BELEGE    = LT_BELEG
          EXCEPTIONS
            NO_DOCUMENTS  = 1
            NO_REGUT      = 2
            WRONG_NUMBER  = 3
            MISSING_UBHKT = 4
            OTHERS        = 5.

        CHECK SY-SUBRC EQ 0.

* Store DME/Document correspondance
        LOOP AT LT_BELEG.
          GT_CORRESP-NUMREF = GT_BSIS_ALL-ZUONR.
          GT_CORRESP-BELNR  = LT_BELEG-BELNR.
          APPEND GT_CORRESP.
        ENDLOOP.

* CHEQUES
      WHEN 'CHQ'.
        WRITE: GT_BSIS_ALL-ZUONR+3(10)
            TO W_VBLNR_C NO-ZERO.
        CONDENSE W_VBLNR_C NO-GAPS.
* Get documents corresponding to cheque number
        SELECT * FROM  PAYR INTO LS_PAYR
               WHERE  ZBUKR  = GP_BUKRS
                AND   HBKID  = GP_HBKID
                AND   HKTID  = GP_HKTID
                AND   CHECT  = W_VBLNR_C.

* Store CHEQUE/Document correspondance
          GT_CORRESP-NUMREF = GT_BSIS_ALL-ZUONR.
          GT_CORRESP-BELNR  = LS_PAYR-VBLNR.
          APPEND GT_CORRESP.
        ENDSELECT.

    ENDCASE.

  ENDLOOP.     " at GT_BSIS_ALL

* Set correspondance
  CLEAR GT_CORRESP.
  LOOP AT GT_CORRESP.
    CLEAR GT_BSIS_ALL.
    LOOP AT GT_BSIS_ALL
      WHERE BELNR EQ GT_CORRESP-BELNR.
      GT_BSIS_ALL-ZUONR = GT_CORRESP-NUMREF.
      MODIFY GT_BSIS_ALL.
    ENDLOOP.    " at GT_BSIS_ALL

    CLEAR GT_BSIS_TOT.
    LOOP AT GT_BSIS_TOT
      WHERE BELNR EQ GT_CORRESP-BELNR.
      GT_BSIS_TOT-ZUONR = GT_CORRESP-NUMREF.
      MODIFY GT_BSIS_TOT.
    ENDLOOP.    " at GT_BSIS_TOT
  ENDLOOP.   " at GT_CORRESP

ENDFORM.                    "PROC_SET_CORRESPONDANCE
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_BSIS_SORT.

  DATA Y_N1 TYPE I VALUE 0.
  DATA Y_N2 TYPE I VALUE 0.
  DATA Y_N3 TYPE I VALUE 0.
  DATA Y_OLD_ZUONR LIKE BSIS-ZUONR.  "Assignment number

  CLEAR Y_OLD_ZUONR.

  SORT GT_BSIS_ALL BY ZUONR.
  SORT GT_BSIS_TOT BY ZUONR.


  LOOP AT GT_BSIS_ALL
    WHERE HKONT+3(2) = GC_ACCOUNT_NUMBER_11
      OR  HKONT+3(2) = GC_ACCOUNT_NUMBER_13.

    IF GT_BSIS_ALL-ZUONR NE Y_OLD_ZUONR.

      LOOP AT GT_BSIS_TOT WHERE ZUONR = GT_BSIS_ALL-ZUONR.

        CONCATENATE SY-ABCDE+Y_N3(1) SY-ABCDE+Y_N2(1) SY-ABCDE+Y_N1(1)
          INTO GT_BSIS_TOT-Y_CHAR.
        MODIFY GT_BSIS_TOT.

        MOVE-CORRESPONDING GT_BSIS_TOT TO GT_BSIS_EDIT.
* Collect table for subtotal sorted by Clearing key
        MOVE: GT_BSIS_EDIT-Y_CHAR TO T_SUBTOTAL-Y_CHAR,
              GT_BSIS_EDIT-WRBTR  TO T_SUBTOTAL-WRBTR,
              GT_BSIS_EDIT-WAERS  TO T_SUBTOTAL-WAERS.

        IF GT_BSIS_EDIT-SHKZG = 'S'.
          T_SUBTOTAL-WRBTR = T_SUBTOTAL-WRBTR * -1.
        ENDIF.

        COLLECT T_SUBTOTAL.

        APPEND GT_BSIS_EDIT.

      ENDLOOP.

** Increment alphabetic counter
      ADD 1 TO Y_N1.
      IF Y_N1 = 25.
        ADD  1 TO Y_N2.
        MOVE 0 TO Y_N1.
      ENDIF.
      IF Y_N2 = 25.
        ADD  1 TO Y_N3.
        MOVE 0 TO Y_N2.
      ENDIF.
**

    ENDIF.

    Y_OLD_ZUONR = GT_BSIS_ALL-ZUONR.

  ENDLOOP.

ENDFORM.                    "PROC_BSIS_SORT
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_BSIS_EDIT.

* Generate amounts (absolute value) for sorting subtotal table
  LOOP AT T_SUBTOTAL.
    COMPUTE T_SUBTOTAL-ABS_WRBTR = ABS( T_SUBTOTAL-WRBTR ).
    MODIFY T_SUBTOTAL.
  ENDLOOP.

  SORT GT_BSIS_EDIT BY Y_CHAR GSBER DESCENDING BELNR BUZEI.
  SORT T_SUBTOTAL  BY ABS_WRBTR WRBTR Y_CHAR ASCENDING.

  CLEAR Y_OLD_CHAR.
  CLEAR Y_OLD_WRBTR.

  FORMAT INTENSIFIED OFF.

  LOOP AT T_SUBTOTAL.

    IF T_SUBTOTAL-Y_CHAR NE Y_OLD_CHAR AND SY-TABIX NE 1.
      PERFORM OUTPUT_FOOTER_DETAIL.
    ENDIF.

    IF T_SUBTOTAL-Y_CHAR NE Y_OLD_CHAR OR SY-TABIX EQ 1.
      PERFORM OUTPUT_HEADER_DETAIL.
    ENDIF.

    IF T_SUBTOTAL-Y_CHAR = SPACE AND Y_OLD_CHAR = SPACE.
      ULINE.
    ENDIF.

    LOOP AT GT_BSIS_EDIT WHERE Y_CHAR = T_SUBTOTAL-Y_CHAR.


      WRITE:/  SY-VLINE,
               GT_BSIS_EDIT-Y_CHAR, " Key
               SY-VLINE,
               GT_BSIS_EDIT-BELNR,  " Doc. No.
               SY-VLINE,
           (4) GT_BSIS_EDIT-BUZEI,  " Item
               SY-VLINE,
          (12) GT_BSIS_EDIT-BUDAT,  " Posting date
               SY-VLINE,
               GT_BSIS_EDIT-VALUT,  " Value date
               SY-VLINE,
               GT_BSIS_EDIT-ZUONR,  " Assignment
               SY-VLINE,
               GT_BSIS_EDIT-GSBER,  " B.A.
               SY-VLINE,
               GT_BSIS_EDIT-HKONT,  " Acc. num.
               SY-VLINE,
               GT_BSIS_EDIT-WRBTR CURRENCY GT_T012K-WAERS,  " Amount
               GT_BSIS_EDIT-WAERS,  " Currency
               SY-VLINE.
      CASE GT_BSIS_EDIT-SHKZG.
        WHEN 'H'.      " Credit
          WRITE: ' C '.
        WHEN 'S'.      " Debit
          WRITE: ' D '.
        WHEN OTHERS.
          WRITE: '   '.
      ENDCASE.
      WRITE: SY-VLINE,
             GT_BSIS_EDIT-SGTXT,  " Description
             SY-VLINE.


    ENDLOOP. "AT GT_BSIS_EDIT


    Y_OLD_CHAR  = T_SUBTOTAL-Y_CHAR.
    Y_OLD_WRBTR = T_SUBTOTAL-WRBTR.

  ENDLOOP. "AT t_subtotal

  IF SY-SUBRC = 4.
* No Items to be cleared
    WRITE:/ TEXT-007.        "No items to be cleared
  ELSE.
    PERFORM OUTPUT_FOOTER_DETAIL.
  ENDIF.

ENDFORM.                    "PROC_BSIS_EDIT
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM PROC_BSIS_UPDATE_ITEMS.

  DATA: Y_OLD_CHAR(3)    TYPE C.
  DATA: Y_NEW_CHAR(3)    TYPE C.
  DATA: Y_FLAG_DELETE(1) TYPE C.
  DATA: Y_FLAG_ERROR(1) TYPE C.

* Check inconsistant currency
  CLEAR Y_FLAG_ERROR.
  LOOP AT  GT_BSIS_TEMP.

    LOOP AT GT_BSIS_EDIT WHERE Y_CHAR EQ GT_BSIS_TEMP-Y_CHAR
                          AND WAERS  NE GT_BSIS_TEMP-WAERS.
      Y_FLAG_ERROR = 'X'.
      EXIT.
    ENDLOOP.              " AT GT_BSIS_EDIT

*     Change to different currency is forbidden
    IF Y_FLAG_ERROR = 'X'.
      MESSAGE I398(00) WITH TEXT-008
                            TEXT-009.
      EXIT.
    ENDIF.
  ENDLOOP.                " AT  GT_BSIS_TEMP

  CHECK Y_FLAG_ERROR NE 'X'.

* Update GT_BSIS_EDIT
  LOOP AT  GT_BSIS_TEMP.

    LOOP AT GT_BSIS_EDIT WHERE BUKRS = GT_BSIS_TEMP-BUKRS
                          AND BELNR = GT_BSIS_TEMP-BELNR
                          AND BUZEI = GT_BSIS_TEMP-BUZEI
                          AND ZUONR = GT_BSIS_TEMP-ZUONR.

      Y_OLD_CHAR = GT_BSIS_EDIT-Y_CHAR.
      Y_NEW_CHAR = GT_BSIS_TEMP-Y_CHAR.

*     If there is a change of clearing key
      IF GT_BSIS_EDIT-Y_CHAR NE GT_BSIS_TEMP-Y_CHAR.

        CLEAR T_SUBTOTAL.

*       Update subtotal table
        T_SUBTOTAL-Y_CHAR = GT_BSIS_TEMP-Y_CHAR.
        T_SUBTOTAL-WAERS  = GT_BSIS_TEMP-WAERS.
        IF GT_BSIS_EDIT-SHKZG = 'H'.      "Credit
          T_SUBTOTAL-WRBTR = GT_BSIS_TEMP-WRBTR.
        ELSEIF GT_BSIS_EDIT-SHKZG = 'S'.  "Debit
          T_SUBTOTAL-WRBTR = GT_BSIS_TEMP-WRBTR * -1.
        ENDIF.
        COLLECT T_SUBTOTAL.

        T_SUBTOTAL-Y_CHAR = GT_BSIS_EDIT-Y_CHAR.
        T_SUBTOTAL-WAERS  = GT_BSIS_EDIT-WAERS.
        IF GT_BSIS_EDIT-SHKZG = 'H'.      "Credit
          T_SUBTOTAL-WRBTR = GT_BSIS_EDIT-WRBTR * -1.
        ELSEIF GT_BSIS_EDIT-SHKZG = 'S'.  "Debit
          T_SUBTOTAL-WRBTR = GT_BSIS_EDIT-WRBTR.
        ENDIF.
        COLLECT T_SUBTOTAL.

*       Update GT_BSIS_EDIT
        MOVE GT_BSIS_TEMP-Y_CHAR TO GT_BSIS_EDIT-Y_CHAR.
        MODIFY GT_BSIS_EDIT.

      ENDIF.


    ENDLOOP.

  ENDLOOP.

* Delete record from subtotal table if there is not any document
* for the old clearing key
  LOOP AT GT_BSIS_EDIT WHERE Y_CHAR = Y_OLD_CHAR.
  ENDLOOP.
  IF SY-SUBRC = 4.
* There is no document left
    Y_FLAG_DELETE = 'X'.
  ENDIF.

* Update absolute amount in subtotal table
  LOOP AT T_SUBTOTAL.
    IF ( T_SUBTOTAL-Y_CHAR = Y_OLD_CHAR AND Y_FLAG_DELETE = 'X' ).
      DELETE T_SUBTOTAL.
    ENDIF.
    IF T_SUBTOTAL-Y_CHAR = Y_NEW_CHAR.
      COMPUTE T_SUBTOTAL-ABS_WRBTR = ABS( T_SUBTOTAL-WRBTR ).
      MODIFY T_SUBTOTAL.
    ENDIF.
  ENDLOOP.

ENDFORM.                    "PROC_BSIS_UPDATE_ITEMS
**********************************************************************
**
**  OUTPUT
**
**********************************************************************
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_SUBTOTAL_A.

* Type d'entete EMAR20022002
  MOVE '1' TO W_TYP_ENTETE.

* Total of amounts A
  SUM_AMOUNT_A = 0.

* Editing list A
  SKIP.
  ULINE AT (15).
  WRITE:/      SY-VLINE.
  WRITE:  3(4) TEXT-K08.     "ADD
  WRITE:  15   SY-VLINE.
  ULINE AT /(70).
  WRITE:/      SY-VLINE,
               TEXT-K09,      "Items debited on bank...
               TEXT-K10,
            70 SY-VLINE .
  ULINE AT /(133).

* Editing sub_total header
  PERFORM OUTPUT_HEADER_SUB_TOTAL_AC.


* Editing list values
  LOOP AT GT_BSIS_TOT WHERE SHKZG = 'S'.

    CHECK GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_11
       OR GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_13
       OR GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_15.

    CHECK GT_BSIS_TOT-BLART = 'Z1'
       OR GT_BSIS_TOT-BLART = 'Z2'
       OR GT_BSIS_TOT-BLART = 'Z3'.

    SUM_AMOUNT_A = SUM_AMOUNT_A + GT_BSIS_TOT-WRBTR.

    WRITE:/     SY-VLINE,
                GT_BSIS_TOT-BUDAT,
                SY-VLINE,
                GT_BSIS_TOT-VALUT,
                SY-VLINE,
                GT_BSIS_TOT-BELNR,
                SY-VLINE,
                GT_BSIS_TOT-SGTXT,
                SY-VLINE,
                GT_BSIS_TOT-ZUONR,
                SY-VLINE,
                GT_BSIS_TOT-WRBTR CURRENCY GT_T012K-WAERS,
                SY-VLINE.
    ULINE AT /(133).

  ENDLOOP.

  WRITE:/     SY-VLINE.
  FORMAT COLOR 3 ON.         " Yellow
  WRITE: TEXT-K11,           " sub total ADD = A
     116 SUM_AMOUNT_A CURRENCY GT_T012K-WAERS.
  FORMAT COLOR 3 OFF.
  WRITE: SY-VLINE.
  ULINE AT /(133).

ENDFORM.                    "OUTPUT_SUBTOTAL_A
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_SUBTOTAL_B.

* Type d'entete EMAR20022002
  MOVE '2' TO W_TYP_ENTETE.
* nouvelle page EMAR20022002
  MOVE 'X' TO W_LAST_PAGE.
  NEW-PAGE.

* Total of amounts B
  SUM_AMOUNT_B = 0.

* Editing list B
  SKIP.
  ULINE AT /(72) .
  WRITE:/    SY-VLINE,
             TEXT-K12,      "Items received on bank journal...
          72 SY-VLINE .
  ULINE AT /(133).

* Effacement EMAR20022002
  CLEAR W_LAST_PAGE.

* Editing sub_total header
  PERFORM OUTPUT_HEADER_SUB_TOTAL_BD.

* Editing list values
  LOOP AT GT_BSIS_TOT WHERE SHKZG = 'S'.

    CHECK GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_11
       OR GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_13
       OR GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_15.

* Ajour de Z3 EMAR31072002
    CHECK GT_BSIS_TOT-BLART NE 'Z1'
      AND GT_BSIS_TOT-BLART NE 'Z2'
      AND GT_BSIS_TOT-BLART NE 'Z3'.

    SUM_AMOUNT_B = SUM_AMOUNT_B + GT_BSIS_TOT-WRBTR.

    WRITE:/     SY-VLINE ,
                GT_BSIS_TOT-BUDAT,
                SY-VLINE,
                GT_BSIS_TOT-VALUT,
                SY-VLINE,
                GT_BSIS_TOT-BELNR,
                SY-VLINE,
                GT_BSIS_TOT-SGTXT,
                SY-VLINE,
                GT_BSIS_TOT-ZUONR,
                SY-VLINE,
                GT_BSIS_TOT-WRBTR CURRENCY GT_T012K-WAERS,
                SY-VLINE.
    ULINE AT /(133).

  ENDLOOP.

  WRITE:/     SY-VLINE.
  FORMAT COLOR 3 ON.         " Yellow
  WRITE: TEXT-K13,           " Sub total ADD = B
     116 SUM_AMOUNT_B CURRENCY GT_T012K-WAERS.
  FORMAT COLOR 3 OFF.
  WRITE: SY-VLINE.
  ULINE AT /(133).

ENDFORM.                    "OUTPUT_SUBTOTAL_B
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_SUBTOTAL_C.

* Type d'entete EMAR20022002
  MOVE '1' TO W_TYP_ENTETE.
* nouvelle page EMAR20022002
  MOVE 'X' TO W_LAST_PAGE.
  NEW-PAGE.

* Total of amounts C
  SUM_AMOUNT_C = 0.

* Editing list C
  SKIP.
  ULINE AT (15).

  WRITE: AT /     SY-VLINE,
             3(6) TEXT-K14,      "DEDUCT
             15   SY-VLINE.
  ULINE AT /(70) .
  WRITE:/    SY-VLINE,
             TEXT-K15,           "Items credited on bank statement...
          70 SY-VLINE .
  ULINE AT /(133).

* Effacement EMAR20022002
  CLEAR W_LAST_PAGE.

* Editing sub_total header
  PERFORM OUTPUT_HEADER_SUB_TOTAL_AC.

  LOOP AT GT_BSIS_TOT WHERE SHKZG = 'H'.

    CHECK GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_11
       OR GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_13
       OR GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_15.

* Ajout de Z3 EAMR31072002
    CHECK GT_BSIS_TOT-BLART = 'Z1'
       OR GT_BSIS_TOT-BLART = 'Z2'
       OR GT_BSIS_TOT-BLART = 'Z3'.

    SUM_AMOUNT_C = SUM_AMOUNT_C + GT_BSIS_TOT-WRBTR.

    WRITE:/     SY-VLINE,
                GT_BSIS_TOT-BUDAT,
                SY-VLINE,
                GT_BSIS_TOT-VALUT,
                SY-VLINE,
                GT_BSIS_TOT-BELNR,
                SY-VLINE,
                GT_BSIS_TOT-SGTXT,
                SY-VLINE,
                GT_BSIS_TOT-ZUONR,
                SY-VLINE,
                GT_BSIS_TOT-WRBTR CURRENCY GT_T012K-WAERS,
                SY-VLINE.
    ULINE AT /(133).

  ENDLOOP.

  WRITE:/     SY-VLINE.
  FORMAT COLOR 3 ON.         " Yellow
  WRITE: TEXT-K16,           " Sub total DEDUCT = C
     116 SUM_AMOUNT_C CURRENCY GT_T012K-WAERS.
  FORMAT COLOR 3 OFF.
  WRITE: SY-VLINE.
  ULINE AT /(133).

ENDFORM.                    "OUTPUT_SUBTOTAL_C
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_SUBTOTAL_D.

  DATA : WA_CHECT LIKE PAYR-CHECT .
  DATA : WA_CHECT_DER(15) TYPE C.


* Type d'entete EMAR20022002
  MOVE '2' TO W_TYP_ENTETE.
* nouvelle page EMAR20022002
  MOVE 'X' TO W_LAST_PAGE.
  NEW-PAGE.

* Total of amounts
  SUM_AMOUNT_D = 0.

* Editing list C
  SKIP.
  ULINE AT /(70) .
  WRITE:/    SY-VLINE,
             TEXT-K17,        "Payments on bank journal...
             TEXT-K18,        "statement
          70 SY-VLINE .
  ULINE AT /(133).

* Effacement EMAR20022002
  CLEAR W_LAST_PAGE.

* Editing sub_total header
  PERFORM OUTPUT_HEADER_SUB_TOTAL_BD.

  LOOP AT GT_BSIS_TOT WHERE SHKZG = 'H'.

    CHECK GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_11
       OR GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_13
       OR GT_BSIS_TOT-HKONT+3(2) = GC_ACCOUNT_NUMBER_15.

* Ajout Z3 EMAR31072002
    CHECK GT_BSIS_TOT-BLART NE 'Z1'
      AND GT_BSIS_TOT-BLART NE 'Z2'
      AND GT_BSIS_TOT-BLART NE 'Z3'.

    SUM_AMOUNT_D = SUM_AMOUNT_D + GT_BSIS_TOT-WRBTR.


    SELECT CHECT FROM PAYR INTO WA_CHECT
    WHERE VBLNR = GT_BSIS_TOT-BELNR .
    ENDSELECT.

    IF SY-SUBRC = 0 .
*Préparation du numéro ce chèque à afficher précédé de CH
      IF NOT WA_CHECT IS INITIAL .
        CONCATENATE 'CHQ' WA_CHECT INTO WA_CHECT_DER .
        CLEAR WA_CHECT .
      ENDIF .
    ENDIF .

    WRITE:/     SY-VLINE,
                GT_BSIS_TOT-BUDAT,
                SY-VLINE,
                GT_BSIS_TOT-VALUT,
                SY-VLINE,
                GT_BSIS_TOT-BELNR,
                SY-VLINE,
         (50)   WA_CHECT_DER,
                SY-VLINE,
         (18)   GT_BSIS_TOT-ZUONR,
                SY-VLINE,
         (16)   GT_BSIS_TOT-WRBTR CURRENCY GT_T012K-WAERS,
                SY-VLINE.
    ULINE AT /(133).

    CLEAR WA_CHECT_DER .

  ENDLOOP.

  WRITE:/     SY-VLINE.
  FORMAT COLOR 3 ON.         " Yellow
  WRITE: TEXT-K19,           " Sub total DEDUCT = D
     116 SUM_AMOUNT_D CURRENCY GT_T012K-WAERS.
  FORMAT COLOR 3 OFF.
  WRITE: SY-VLINE.
  ULINE AT /(133).

  SKIP.
  SKIP.

ENDFORM.                    "OUTPUT_SUBTOTAL_D
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_BALANCE.

  DATA: LS_BALANCE TYPE FDBL_BALANCE_LINE.

  DATA: SUM_E   LIKE BSIS-WRBTR,
        SUM_F   LIKE BSIS-WRBTR,
        SUM_H   LIKE BSIS-WRBTR,
        SUM_G   LIKE BSIS-WRBTR,
        SUM_E_F LIKE BSIS-WRBTR.

* dernière page EMAR20022002
  MOVE 'X' TO W_LAST_PAGE.

  NEW-PAGE.

  PERFORM OUTPUT_HEADER_DETAIL_STAT.
  WRITE: / 'OVERVIEW'.

* Sub total ADD
  SUM_F = SUM_AMOUNT_A + SUM_AMOUNT_B.

* Sub total DEDUCT
  SUM_G = SUM_AMOUNT_C + SUM_AMOUNT_D.

* Bank balance at clearing date
* sum_e -> initialized to 10xxxxx cumulutive balance
* for current period
  READ TABLE GT_BALANCE INDEX GP_BUDAT+4(2) INTO LS_BALANCE.
  IF SY-SUBRC EQ 0.
    SUM_E = LS_BALANCE-BALANCE_CUM.
  ENDIF.

* Sub total DEDUCT Cumulative
  SUM_H = SUM_E + SUM_F - SUM_G.
* Sub total E + F
  SUM_E_F = SUM_E + SUM_F .

* Edition
  ULINE AT /64(70).
  WRITE: AT /64   SY-VLINE,
             (30) TEXT-K20,          "Sub Total
                  SY-VLINE,
                  TEXT-K21,          "Cumulative
             133  SY-VLINE.
  ULINE (133).

* Bank balance edition
  WRITE: AT /    SY-VLINE,
                 TEXT-K22,           "Bank balance at
                 GP_BUDAT,
             64  SY-VLINE,
            (30) '  ',
                 SY-VLINE,
            (30) SUM_E CURRENCY GT_T012K-WAERS,
            133  SY-VLINE.
  ULINE (133).

* Add A edition
  WRITE:/      SY-VLINE,             "blank line
               ' ' ,
          64   SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) '   ',
           133 SY-VLINE.

  WRITE:/      SY-VLINE,
               TEXT-K08,             "ADD
          64   SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) '   ',
           133 SY-VLINE.


  WRITE:/      SY-VLINE,
          (60) TEXT-K26,             "A = Items debited on bank...
               SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) ' ',
           133 SY-VLINE,
        /      SY-VLINE,
               TEXT-K27,            "accounted on bank journal
          64   SY-VLINE,
          (30) SUM_AMOUNT_A CURRENCY GT_T012K-WAERS,
               SY-VLINE,
          (30) '  ',
           133 SY-VLINE.

* ADD B edition
  WRITE:/      SY-VLINE,
               ' ' ,
          64   SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) '   ',
           133 SY-VLINE.

  WRITE:/      SY-VLINE,
          (60) TEXT-K28,            "B = Items received on bank...
               SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) ' ',
           133 SY-VLINE,
          /    SY-VLINE,
               TEXT-K29,            "on bank statement
            64 SY-VLINE,
          (30) SUM_AMOUNT_B CURRENCY GT_T012K-WAERS,
               SY-VLINE,
          (30) '  ',
           133 SY-VLINE.

  WRITE : / SY-VLINE,
               ' ' ,
               64 SY-VLINE,
               (30) ' ',
               SY-VLINE,
               (30) '   ',
           133 SY-VLINE.
  ULINE (133).

* Sub total ADD edition
  WRITE:/      SY-VLINE,
          (60) TEXT-K23,            "Sub total ADD
          64   SY-VLINE,
          (30) SUM_F CURRENCY GT_T012K-WAERS,
               SY-VLINE,
          (30) SUM_E_F CURRENCY GT_T012K-WAERS,
          133  SY-VLINE.
  ULINE (133).

* DEDUCT C edition
  WRITE:/      SY-VLINE,            "blank line
               ' ' ,
          64   SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) '   ',
           133 SY-VLINE.

  WRITE:/      SY-VLINE,
               'DEDUCT',
          64   SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) '   ',
           133 SY-VLINE.

  WRITE:/      SY-VLINE,
          (60) TEXT-K30,            "C = Items credited on bank...
               SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) ' ',
           133 SY-VLINE,
          /    SY-VLINE,
               TEXT-K27,            "accounted on bank journal
          64   SY-VLINE,
          (30) SUM_AMOUNT_C CURRENCY GT_T012K-WAERS,
               SY-VLINE,
          (30) '  ',
           133 SY-VLINE.

* DEDUCT D edition
  WRITE:/      SY-VLINE,            "blank line.
               ' ' ,
          64   SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) '   ',
           133 SY-VLINE.

  WRITE:/      SY-VLINE,
          (60) TEXT-K31,            "D = Payments on bank...
               SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) ' ',
           133 SY-VLINE,
         /     SY-VLINE,
               TEXT-K29,            "on bank statement
          64   SY-VLINE,
          (30) SUM_AMOUNT_D CURRENCY GT_T012K-WAERS,
               SY-VLINE,
          (30) '  ',
           133 SY-VLINE.

  WRITE:/      SY-VLINE,
               ' ' ,
          64   SY-VLINE,
          (30) ' ',
               SY-VLINE,
          (30) '   ',
           133 SY-VLINE.
  ULINE (133).

* Sub total DEDUCT edition
  WRITE:/      SY-VLINE,
          (60) TEXT-K32,            "Sub total DEDUCT
          64   SY-VLINE,
          (30) SUM_G CURRENCY GT_T012K-WAERS,
               SY-VLINE,
          (30) SUM_H CURRENCY GT_T012K-WAERS,
           133 SY-VLINE.
  ULINE (133).
  SKIP.
  ULINE (133).

  WRITE:/      SY-VLINE,
               TEXT-K25,          "Balance in accounting at
               GP_BUDAT,
          64   SY-VLINE,
          (32) ' ',
          (30) SUM_H CURRENCY GT_T012K-WAERS,
          133  SY-VLINE.
  ULINE (133).

ENDFORM.                    "OUTPUT_BALANCE
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_HEADER_DETAIL_STAT.

* Report title
  GET PF-STATUS W_STATUS.
  CASE W_STATUS.
    WHEN 'STAT'.
      WRITE: 34 TEXT-H01,
                GP_BUDAT.
    WHEN 'RECO'.
      WRITE: 44 TEXT-H09,
                GP_BUDAT.
    WHEN 'LIST'.
      WRITE: 45 TEXT-H10,
                GP_BUDAT.
  ENDCASE.
  WRITE: 117 TEXT-H08,        "Day Date
             SY-DATUM.

* Bank and account info
  READ TABLE GT_BNKA INDEX 1.
  WRITE:/    TEXT-H02,        "Name of Bank:
             GT_BNKA-BANKA.

  READ TABLE GT_T012K INDEX 1.
  WRITE:/    TEXT-H03,        "Name of bank account:
             GT_T012K-TEXT1.
  WRITE:/    TEXT-H04,        "House bank:
             GT_T012K-HBKID,
             GT_BNKA-BANKL.
  WRITE:/    TEXT-H05,        "Account Number:
             GT_T012K-HKTID,
             GT_T012K-BANKN,
         120 TEXT-H06,        "Currency:
             GT_T012K-WAERS.
  WRITE /.


ENDFORM.                    "OUTPUT_HEADER_DETAIL_STAT
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_HEADER_SUB_TOTAL_AC.

  WRITE: AT /      SY-VLINE,
                   TEXT-K33,      "Op. date
                   SY-VLINE,
                   TEXT-K00,      "Value date
                   SY-VLINE,
                   TEXT-K02,      "Doc no
                   SY-VLINE,
              (50) TEXT-K03,      "Description
                   SY-VLINE,
              (18) TEXT-K04,      "Reference
                   SY-VLINE,
              (16) TEXT-K05,      "Amount
                   SY-VLINE.
  ULINE AT /(133).

ENDFORM.                    "OUTPUT_HEADER_SUB_TOTAL_AC
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_HEADER_SUB_TOTAL_BD.

  WRITE: AT /      SY-VLINE,
                   TEXT-K07,      "Pstng date
                   SY-VLINE,
                   TEXT-K00,      "Value date
                   SY-VLINE,
                   TEXT-K02,      "SAP doc nb
                   SY-VLINE,
              (50) TEXT-K03,      "Description
                   SY-VLINE,
              (18) TEXT-K04,      "Reference
                   SY-VLINE,
              (16) TEXT-K05,      "Amount
                   SY-VLINE.
  ULINE AT /(133).

ENDFORM.                    "OUTPUT_HEADER_SUB_TOTAL_BD
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_FOOTER_DETAIL.

  WRITE:/1(180) SY-ULINE.
  WRITE:/ SY-VLINE.
* CLearing Key
  FORMAT HOTSPOT ON.
  FORMAT INTENSIFIED ON.
  FORMAT COLOR 6 ON.         "Red
  WRITE: TEXT-110,           "Clearing key
         Y_OLD_CHAR.
  FORMAT COLOR 6 OFF.
  FORMAT INTENSIFIED OFF.
  FORMAT HOTSPOT OFF.
  WRITE: SY-VLINE.
* Reconciliation button
  WRITE: ' '.
  FORMAT HOTSPOT ON.
  FORMAT INTENSIFIED ON.
  FORMAT COLOR 5 ON.         "Green
  WRITE: 22 TEXT-001.        "Reconciliation
  FORMAT COLOR 6 OFF.
  FORMAT INTENSIFIED OFF.
  FORMAT HOTSPOT OFF.
* Sub-total
  WRITE: 42  SY-VLINE,
         98  Y_OLD_WRBTR CURRENCY GT_T012K-WAERS,
         180 SY-VLINE.
  WRITE:/1(180) SY-ULINE.
  WRITE:/ .

ENDFORM.                                         " OUTPUT_FOOTER_DETAIL
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_HEADER_DETAIL.

  WRITE:/1(180)  SY-ULINE.
  WRITE:/ SY-VLINE,
      (3) TEXT-101,   " Key
          SY-VLINE,
     (10) TEXT-102,   " Doc no.
          SY-VLINE,
          TEXT-103,   " Item
          SY-VLINE,
          TEXT-104,   " Posting date
          SY-VLINE,
          TEXT-111,   " Value date
          SY-VLINE,
          TEXT-105,   " Assignment
          SY-VLINE,
          TEXT-106,   " B.A.
          SY-VLINE,
          TEXT-107,   " GL Account
          SY-VLINE,
          TEXT-108,   " Amount
          SY-VLINE,
          TEXT-112,   " D/C
          SY-VLINE,
          TEXT-109,   " Description
          SY-VLINE.
  WRITE:/1(180)  SY-ULINE.

ENDFORM.                    "OUTPUT_HEADER_DETAIL
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM OUTPUT_REPORT_TRANSACTION.

  DATA: W_RECONCIL(3) TYPE N.
  CLEAR W_LAST_PAGE.
  NEW-PAGE.
  PERFORM OUTPUT_HEADER_DETAIL_STAT.

* EMAR20022002
*  WRITE: / 'DETAILS - PAGE:',
*           SY-PAGNO.

  CLEAR GT_BSIS_RECONCIL.
  LOOP AT GT_BSIS_RECONCIL.

    AT NEW Y_RECONCIL.
      PERFORM OUTPUT_HEADER_DETAIL.
    ENDAT.


    W_RECONCIL = GT_BSIS_RECONCIL-Y_RECONCIL.
    WRITE:/  SY-VLINE,
             W_RECONCIL,
             SY-VLINE,
             GT_BSIS_RECONCIL-BELNR,  " Doc. No.
             SY-VLINE,
         (4) GT_BSIS_RECONCIL-BUZEI,  " Item
             SY-VLINE,
        (12) GT_BSIS_RECONCIL-BUDAT,  " Posting date
             SY-VLINE,
             GT_BSIS_RECONCIL-VALUT,  " Value date
             SY-VLINE,
             GT_BSIS_RECONCIL-ZUONR,  " Assignment
             SY-VLINE,
             GT_BSIS_RECONCIL-GSBER,  " B.A.
             SY-VLINE,
             GT_BSIS_RECONCIL-HKONT,  " Acc. num.
             SY-VLINE,
             GT_BSIS_RECONCIL-WRBTR CURRENCY GT_BSIS_RECONCIL-WAERS,
                                     " Amount
             GT_BSIS_RECONCIL-WAERS,  " Currency
             SY-VLINE.
    CASE GT_BSIS_RECONCIL-SHKZG.
      WHEN 'H'.      " Credit
        WRITE: ' C '.
      WHEN 'S'.      " Debit
        WRITE: ' D '.
      WHEN OTHERS.
        WRITE: '   '.
    ENDCASE.

    WRITE: SY-VLINE,
           GT_BSIS_RECONCIL-SGTXT,  " Description
           SY-VLINE.

    AT END OF Y_RECONCIL.
      WRITE: /1(180) SY-ULINE.
      CLEAR GT_RECONCIL_MESS.
      LOOP AT GT_RECONCIL_MESS
      WHERE Y_RECONCIL = GT_BSIS_RECONCIL-Y_RECONCIL.
        W_RECONCIL = GT_RECONCIL_MESS-Y_RECONCIL.
        WRITE:/  SY-VLINE,
                 W_RECONCIL,
                 SY-VLINE,
                 GT_RECONCIL_MESS-Y_TRANS,       "Transaction number
                 GT_RECONCIL_MESS-Y_MSGTYPE,     "Status
                 GT_RECONCIL_MESS-Y_MSGTX,       "Message
            180  SY-VLINE.
      ENDLOOP.     " AT GT_RECONCIL_MESS
      WRITE: /1(180) SY-ULINE.

    ENDAT.
  ENDLOOP.     " AT GT_BSIS_RECONCIL

*  PERFORM edit_bsis_for_clearing.

ENDFORM.                    "OUTPUT_REPORT_TRANSACTION
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM BDC_DATA_FBRA  TABLES  BDCDTAB      STRUCTURE BDCDATA
                            GT_BSIS_BELNR STRUCTURE GT_BSIS_BELNR
                    USING   T_BSIS       STRUCTURE GS_BSIS_F04.

  REFRESH BDCDTAB.

*------------screen 0122------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPMF05R'.
  BDCDTAB-DYNPRO   = '0100'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05R-AUGBL'.
  MOVE W_NODOC TO BDCDTAB-FVAL.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05R-BUKRS'.
  BDCDTAB-FVAL = GS_BSIS_F04-BUKRS .
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05R-GJAHR'.
  BDCDTAB-FVAL = SY-DATUM+0(4).
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=RAGL'.
  APPEND BDCDTAB.

ENDFORM.                    "BDC_DATA_FBRA
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
FORM BDC_DATA_FB08  TABLES  BDCDTAB      STRUCTURE BDCDATA
                            GT_BSIS_BELNR STRUCTURE GT_BSIS_BELNR
                    USING   T_BSIS       STRUCTURE GS_BSIS_F04.

  REFRESH BDCDTAB.

*------------screen 0122------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPMF05A'.
  BDCDTAB-DYNPRO   = '0105'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-BELNS'.
  MOVE W_NODOC TO BDCDTAB-FVAL.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BKPF-BUKRS'.
  BDCDTAB-FVAL = GS_BSIS_F04-BUKRS .
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-GJAHS'.
  BDCDTAB-FVAL = SY-DATUM+0(4).
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'UF05A-STGRD'.
  BDCDTAB-FVAL = '02'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=BU'.
  APPEND BDCDTAB.

ENDFORM.                    "BDC_DATA_FB08
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM BDC_DTAB_FILLING_FB08
      TABLES BDCDTAB STRUCTURE BDCDATA
        USING  T_BSIS  STRUCTURE GS_BSIS_FB08.

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
  WRITE GP_AUGDT DD/MM/YYYY TO BDCDTAB-FVAL.
*  bdcdtab-fval = GP_AUGDT.
  APPEND BDCDTAB.

* BDC OK-Code
  BDCDTAB-DYNPRO = '0000'.
  BDCDTAB-DYNBEGIN = ' '.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '/11'.
  APPEND BDCDTAB.

ENDFORM.                    "BDC_DTAB_FILLING_FB08
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM BDC_DTAB_FILLING_F04
     TABLES BDCDTAB      STRUCTURE BDCDATA
            GT_BSIS_BELNR STRUCTURE GT_BSIS_BELNR
      USING T_BSIS       STRUCTURE GS_BSIS_F04.

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
  WRITE GP_AUGDT DD/MM/YYYY TO BDCDTAB-FVAL.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BKPF-MONAT'.
  BDCDTAB-FVAL = GP_AUGDT+4(2).
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BKPF-WAERS'.
  BDCDTAB-FVAL = T_BSIS-WAERS.
  APPEND BDCDTAB.

*  CLEAR bdcdtab.
*  bdcdtab-fnam = 'FS006-DOCID'.
*  bdcdtab-fval = '*'.
*  APPEND bdcdtab.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-XPOS1(04)'.
  BDCDTAB-FVAL = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-NEWBS'.
  IF T_BSIS-SHKZG = 'S'.
    BDCDTAB-FVAL = '50'.
  ELSE.
    BDCDTAB-FVAL = '40'.
  ENDIF.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-NEWKO'.
  BDCDTAB-FVAL = T_BSIS-HKONT.
  BDCDTAB-FVAL+3(2) = '10'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'RF05A-NEWKO'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '/00'.
  APPEND BDCDTAB.


*------------screen 0300------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPMF05A'.
  BDCDTAB-DYNPRO   = '0300'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BSEG-WRBTR'.
*AHOUNOU29012007
*  WRITE t_bsis-wrbtr TO w_wrbtr RIGHT-JUSTIFIED.
  WRITE T_BSIS-WRBTR TO W_WRBTR  CURRENCY T_BSIS-WAERS RIGHT-JUSTIFIED.
*AHOUNOU29012007

  BDCDTAB-FVAL = W_WRBTR.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BSEG-VALUT'.
  WRITE T_BSIS-VALUT DD/MM/YYYY TO BDCDTAB-FVAL.
  APPEND BDCDTAB.
*AHOUNOU15032006
  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BSEG-ZUONR'.
  BDCDTAB-FVAL = T_BSIS-ZUONR.
  APPEND BDCDTAB.
*  CLEAR bdcdtab.
*  bdcdtab-fnam = 'BSEG-ZUONR'.
*  bdcdtab-fval = GS_BSIS_F04-zuonr.
*  APPEND bdcdtab.
*AHOUNOU15032006

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BSEG-SGTXT'.
  BDCDTAB-FVAL = T_BSIS-SGTXT.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'BSEG-WRBTR'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_SUBSCR'.
  BDCDTAB-FVAL = 'SAPLKACB'.
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

*  CLEAR bdcdtab.
*  bdcdtab-fnam = 'COBL-FIPOS'.
*  bdcdtab-fval = 'BANK'.
*  APPEND bdcdtab.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'COBL-GSBER'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_SUBSCR'.
  BDCDTAB-FVAL = 'SAPLKACB'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=ENTE'.
  APPEND BDCDTAB.


*------------screen 0710------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPMF05A'.
  BDCDTAB-DYNPRO   = '0710'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

*  CLEAR bdcdtab.
*  bdcdtab-fnam = 'RF05A-AGBUK'.
*  bdcdtab-fval = 'UNES'.
*  APPEND bdcdtab.

* Ajout du n° de compte xx --> 11
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
  BDCDTAB-FVAL = ''.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05A-XPOS1(06)'.
  BDCDTAB-FVAL = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'RF05A-XPOS1(06)'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=PA'.
  APPEND BDCDTAB.


* Enter all documents
  LOOP AT GT_BSIS_BELNR.
*------------screen 0731------------
    CLEAR BDCDTAB.
    BDCDTAB-PROGRAM  = 'SAPMF05A'.
    BDCDTAB-DYNPRO   = '0731'.
    BDCDTAB-DYNBEGIN = 'X'.
    APPEND BDCDTAB.

    CLEAR BDCDTAB.
    BDCDTAB-FNAM = 'RF05A-SEL01(01)'.
    BDCDTAB-FVAL = GT_BSIS_BELNR-BELNR.
    APPEND BDCDTAB.

    CLEAR BDCDTAB.
    BDCDTAB-FNAM = 'BDC_CURSOR'.
    BDCDTAB-FVAL = 'RF05A-SEL01(01)'.
    APPEND BDCDTAB.

    CLEAR BDCDTAB.
    BDCDTAB-FNAM = 'BDC_OKCODE'.
    BDCDTAB-FVAL = '/00'.
    APPEND BDCDTAB.
  ENDLOOP.


*------------screen 0731------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPMF05A'.
  BDCDTAB-DYNPRO   = '0731'.
  BDCDTAB-DYNBEGIN = 'X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_CURSOR'.
  BDCDTAB-FVAL = 'RF05A-SEL01(01)'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=PA'.
  APPEND BDCDTAB.


*------------screen 3100------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPDF05X'.
  BDCDTAB-DYNPRO   = '3100'.
  BDCDTAB-DYNBEGIN = 'X'.
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
  BDCDTAB-FNAM = 'BDC_SUBSCR'.
  BDCDTAB-FVAL = 'SAPDF05X'.
  APPEND BDCDTAB.


  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=OMX'.
  APPEND BDCDTAB.

*------------screen 3100------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPDF05X'.
  BDCDTAB-DYNPRO   = '3100'.
  BDCDTAB-DYNBEGIN = 'X'.
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
  BDCDTAB-FNAM = 'BDC_SUBSCR'.
  BDCDTAB-FVAL = 'SAPDF05X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=Z+'.
  APPEND BDCDTAB.


*------------screen 3100------------
  CLEAR BDCDTAB.
  BDCDTAB-PROGRAM  = 'SAPDF05X'.
  BDCDTAB-DYNPRO   = '3100'.
  BDCDTAB-DYNBEGIN = 'X'.
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
  BDCDTAB-FNAM = 'BDC_SUBSCR'.
  BDCDTAB-FVAL = 'SAPDF05X'.
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=BU'.            " AEM
  APPEND BDCDTAB.


ENDFORM.                    "BDC_DTAB_FILLING_F04
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM DPRO_USER_OK_TC USING    P_TC_NAME TYPE DYNFNAM
                         P_TABLE_NAME
                         P_MARK_NAME
                CHANGING P_OK      LIKE SY-UCOMM.

  DATA: L_OK              TYPE SY-UCOMM,
        L_OFFSET          TYPE I.


* Table control specific operations
*   evaluate TC name and operations
  SEARCH P_OK FOR P_TC_NAME.
  IF SY-SUBRC <> 0.
    EXIT.
  ENDIF.

  L_OFFSET = STRLEN( P_TC_NAME ) + 1.
  L_OK = P_OK+L_OFFSET.

* execute general and TC specific operations
  CASE L_OK.

    WHEN 'INSR'.                                "insert row
      PERFORM DPRO_FCODE_INSERT_ROW USING P_TC_NAME
                                     P_TABLE_NAME.
      CLEAR P_OK.

    WHEN 'DELE'.                                "delete row
      PERFORM DPRO_FCODE_DELETE_ROW USING P_TC_NAME
                                     P_TABLE_NAME
                                     P_MARK_NAME.
      CLEAR P_OK.

    WHEN 'P--' OR                               "top of list
         'P-'  OR                               "previous page
         'P+'  OR                               "next page
         'P++'.                                 "bottom of list
      PERFORM DPRO_COMPUTE_SCROLLING_IN_TC USING P_TC_NAME
                                            L_OK.
      CLEAR P_OK.

    WHEN 'MARK'.                                "mark all filled lines
      PERFORM DPRO_FCODE_TC_MARK_LINES USING P_TC_NAME
                                        P_TABLE_NAME
                                        P_MARK_NAME   .
      CLEAR P_OK.

    WHEN 'DMRK'.                                "demark all filled lines
      PERFORM DPRO_FCODE_TC_DEMARK_LINES USING P_TC_NAME
                                          P_TABLE_NAME
                                          P_MARK_NAME .
      CLEAR P_OK.

  ENDCASE.

ENDFORM.                    "DPRO_USER_OK_TC
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM DPRO_FCODE_INSERT_ROW USING P_TC_NAME TYPE DYNFNAM
                            P_TABLE_NAME.

  DATA L_LINES_NAME       LIKE FELD-NAME.
  DATA L_SELLINE          LIKE SY-STEPL.
  DATA L_LASTLINE         TYPE I.
  DATA L_LINE             TYPE I.
  DATA L_TABLE_NAME       LIKE FELD-NAME.
  FIELD-SYMBOLS <TC>                 TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <TABLE>              TYPE STANDARD TABLE.
  FIELD-SYMBOLS <LINES>              TYPE I.


  ASSIGN (P_TC_NAME) TO <TC>.

* get the table, which belongs to the tc
  CONCATENATE P_TABLE_NAME '[]' INTO L_TABLE_NAME. "table body
  ASSIGN (L_TABLE_NAME) TO <TABLE>.                "not headerline

* get looplines of TableControl
  CONCATENATE 'G_' P_TC_NAME '_LINES' INTO L_LINES_NAME.
  ASSIGN (L_LINES_NAME) TO <LINES>.

* get current line
  GET CURSOR LINE L_SELLINE.
  IF SY-SUBRC <> 0.                             " append line to table
    L_SELLINE = <TC>-LINES + 1.
*   set top line and new cursor line
    IF L_SELLINE > <LINES>.
      <TC>-TOP_LINE = L_SELLINE - <LINES> + 1 .
      L_LINE = 1.
    ELSE.
      <TC>-TOP_LINE = 1.
      L_LINE = L_SELLINE.
    ENDIF.
  ELSE.                                         " insert line into table
    L_SELLINE = <TC>-TOP_LINE + L_SELLINE - 1.
*   set top line and new cursor line
    L_LASTLINE = L_SELLINE + <LINES> - 1.
    IF L_LASTLINE <= <TC>-LINES.
      <TC>-TOP_LINE = L_SELLINE.
      L_LINE = 1.
    ELSEIF <LINES> > <TC>-LINES.
      <TC>-TOP_LINE = 1.
      L_LINE = L_SELLINE.
    ELSE.
      <TC>-TOP_LINE = <TC>-LINES - <LINES> + 2 .
      L_LINE = L_SELLINE - <TC>-TOP_LINE + 1.
    ENDIF.
  ENDIF.
* insert initial line
  INSERT INITIAL LINE INTO <TABLE> INDEX L_SELLINE.
  <TC>-LINES = <TC>-LINES + 1.
* set cursor
  SET CURSOR LINE L_LINE.

ENDFORM.                    "DPRO_FCODE_INSERT_ROW
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM DPRO_FCODE_DELETE_ROW USING P_TC_NAME TYPE DYNFNAM
                            P_TABLE_NAME
                            P_MARK_NAME.

  DATA L_TABLE_NAME           LIKE FELD-NAME.

  FIELD-SYMBOLS <TC>          TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <TABLE>       TYPE STANDARD TABLE.
  FIELD-SYMBOLS <WA>.
  FIELD-SYMBOLS <MARK_FIELD>.

  ASSIGN (P_TC_NAME) TO <TC>.

* get the table, which belongs to the tc
  CONCATENATE P_TABLE_NAME '[]' INTO L_TABLE_NAME. "table body
  ASSIGN (L_TABLE_NAME) TO <TABLE>.                "not headerline

* delete marked lines
  DESCRIBE TABLE <TABLE> LINES <TC>-LINES.

  LOOP AT <TABLE> ASSIGNING <WA>.

*   access to the component 'FLAG' of the table header
    ASSIGN COMPONENT P_MARK_NAME OF STRUCTURE <WA> TO <MARK_FIELD>.

    IF <MARK_FIELD> = 'X'.
      DELETE <TABLE> INDEX SYST-TABIX.
      IF SY-SUBRC = 0.
        <TC>-LINES = <TC>-LINES - 1.
      ENDIF.
    ENDIF.

  ENDLOOP.

ENDFORM.                    "DPRO_FCODE_DELETE_ROW
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM DPRO_COMPUTE_SCROLLING_IN_TC USING P_TC_NAME
                                   P_OK.
  DATA L_TC_NEW_TOP_LINE     TYPE I.
  DATA L_TC_NAME             LIKE FELD-NAME.
  DATA L_TC_LINES_NAME       LIKE FELD-NAME.
  DATA L_TC_FIELD_NAME       LIKE FELD-NAME.

  FIELD-SYMBOLS <TC>         TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <LINES>      TYPE I.

  ASSIGN (P_TC_NAME) TO <TC>.
* get looplines of TableControl
  CONCATENATE 'G_' P_TC_NAME '_LINES' INTO L_TC_LINES_NAME.
  ASSIGN (L_TC_LINES_NAME) TO <LINES>.


* is no line filled?
  IF <TC>-LINES = 0.
*   yes, ...
    L_TC_NEW_TOP_LINE = 1.
  ELSE.
*   no, ...
    CALL FUNCTION 'SCROLLING_IN_TABLE'
      EXPORTING
        ENTRY_ACT             = <TC>-TOP_LINE
        ENTRY_FROM            = 1
        ENTRY_TO              = <TC>-LINES
        LAST_PAGE_FULL        = 'X'
        LOOPS                 = <LINES>
        OK_CODE               = P_OK
        OVERLAPPING           = 'X'
      IMPORTING
        ENTRY_NEW             = L_TC_NEW_TOP_LINE
      EXCEPTIONS
        NO_ENTRY_OR_PAGE_ACT  = 01
        NO_ENTRY_TO           = 02
        NO_OK_CODE_OR_PAGE_GO = 03
        OTHERS                = 99.
  ENDIF.

* get actual tc and column
  GET CURSOR FIELD L_TC_FIELD_NAME
             AREA  L_TC_NAME.

  IF SYST-SUBRC = 0.
    IF L_TC_NAME = P_TC_NAME.
*     set actual column
      SET CURSOR FIELD L_TC_FIELD_NAME LINE 1.
    ENDIF.
  ENDIF.

* set the new top line
  <TC>-TOP_LINE = L_TC_NEW_TOP_LINE.

ENDFORM.                    "DPRO_COMPUTE_SCROLLING_IN_TC
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM DPRO_FCODE_TC_MARK_LINES USING P_TC_NAME
                               P_TABLE_NAME
                               P_MARK_NAME.
  DATA L_TABLE_NAME       LIKE FELD-NAME.

  FIELD-SYMBOLS <TC>         TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <TABLE>      TYPE STANDARD TABLE.
  FIELD-SYMBOLS <WA>.
  FIELD-SYMBOLS <MARK_FIELD>.

  ASSIGN (P_TC_NAME) TO <TC>.

* get the table, which belongs to the tc
  CONCATENATE P_TABLE_NAME '[]' INTO L_TABLE_NAME. "table body
  ASSIGN (L_TABLE_NAME) TO <TABLE>.                "not headerline

* mark all filled lines
  LOOP AT <TABLE> ASSIGNING <WA>.

*   access to the component 'FLAG' of the table header
    ASSIGN COMPONENT P_MARK_NAME OF STRUCTURE <WA> TO <MARK_FIELD>.

    <MARK_FIELD> = 'X'.
  ENDLOOP.

ENDFORM.                    "DPRO_FCODE_TC_MARK_LINES
*--------------------------------------------------------------------*
*-
*--------------------------------------------------------------------*
FORM DPRO_FCODE_TC_DEMARK_LINES USING P_TC_NAME
                                 P_TABLE_NAME
                                 P_MARK_NAME .
  DATA L_TABLE_NAME       LIKE FELD-NAME.

  FIELD-SYMBOLS <TC>         TYPE CXTAB_CONTROL.
  FIELD-SYMBOLS <TABLE>      TYPE STANDARD TABLE.
  FIELD-SYMBOLS <WA>.
  FIELD-SYMBOLS <MARK_FIELD>.

  ASSIGN (P_TC_NAME) TO <TC>.

* get the table, which belongs to the tc
  CONCATENATE P_TABLE_NAME '[]' INTO L_TABLE_NAME. "table body
  ASSIGN (L_TABLE_NAME) TO <TABLE>.                "not headerline

* demark all filled lines
  LOOP AT <TABLE> ASSIGNING <WA>.
*   access to the component 'FLAG' of the table header
    ASSIGN COMPONENT P_MARK_NAME OF STRUCTURE <WA> TO <MARK_FIELD>.
    <MARK_FIELD> = SPACE.
  ENDLOOP.

ENDFORM.                    "DPRO_FCODE_TC_DEMARK_LINES
*--------------------------------------------------------------------*
* INPUT MODULE FOR TABLECONTROL 'T_CONTROL_TEMP': MODIFY TABLE
*--------------------------------------------------------------------*
MODULE T_CONTROL_TEMP_MODIFY INPUT.
  MODIFY GT_BSIS_TEMP
    INDEX T_CONTROL_TEMP-CURRENT_LINE.
ENDMODULE.                    "T_CONTROL_TEMP_MODIFY INPUT
*--------------------------------------------------------------------*
* INPUT MODULE FOR TABLECONTROL 'T_CONTROL_TEMP': PROCESS USER COMMAND
*--------------------------------------------------------------------*
MODULE T_CONTROL_TEMP_USER_COMMAND INPUT.
  PERFORM DPRO_USER_OK_TC USING    'T_CONTROL_TEMP'
                              'GT_BSIS_TEMP'
                              'Y_CHAR'
                     CHANGING OK_CODE.
ENDMODULE.                    "T_CONTROL_TEMP_USER_COMMAND INPUT
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
MODULE STATUS_9000 OUTPUT.

  SET PF-STATUS 'VALI'.
  SET TITLEBAR 'VALI'.

ENDMODULE.                    "STATUS_9000 OUTPUT
*--------------------------------------------------------------------*
*
*--------------------------------------------------------------------*
MODULE USER_COMMAND_9000 INPUT.

  CASE OK_CODE.
    WHEN 'VALI' OR 'STOP' OR 'RW'.
      Y_SAVE_CODE  = OK_CODE.
      SET SCREEN 0. LEAVE SCREEN.
  ENDCASE.
  CLEAR OK_CODE.

ENDMODULE.                    "USER_COMMAND_9000 INPUT

INCLUDE <LIST>.