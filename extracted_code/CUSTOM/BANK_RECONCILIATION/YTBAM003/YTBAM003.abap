*INCLUDE YTBAM003
*******************************************************************
* PROGRAM        YTBAM003
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
* 31/07/2002 E. Martorana Ajout type de pièce Z3 EMAR31072002
*
* 04/12/2002 F.Béchet    0004 Correction décimales - Landpark 9598
*                             Rajout dans les write d'impression du
*                             mot clé currency associé aux montants
* 26/12/2002 A.Ahounou   0005 Affichage Numéro de Chèque dans la
*                             colonne description
*
*******************************************************************


INCLUDE <LIST>.

*******************************************************************
*      Form  01_select_bsis
*******************************************************************
*       selection on bank account 11XXXX and 13XXXXX.
*******************************************************************
*  -->  tsako t_bsis_all
*  <--  t_bsis_tot
*******************************************************************
FORM 01_SELECT_BSIS.

  LOOP AT TSAKO WHERE Y_BQ_AC = ' '.
    SELECT * FROM BSIS APPENDING TABLE T_BSIS_ALL
                        WHERE BUKRS EQ TSAKO-BUKRS
                          AND HKONT EQ TSAKO-HKONT
                          AND BUDAT LE P_BUDAT
                          AND SHKZG EQ TSAKO-SHKZG.
  ENDLOOP.

  LOOP AT T_BSIS_ALL
    WHERE HKONT+3(2) = C_ACCOUNT_NUMBER_11
      OR  HKONT+3(2) = C_ACCOUNT_NUMBER_13.

    MOVE-CORRESPONDING T_BSIS_ALL TO T_BSIS_TOT.
    APPEND T_BSIS_TOT.
  ENDLOOP.

ENDFORM.                                         " 01_select_bsis

*******************************************************************
*      Form  03_select_BSEG
*******************************************************************
*       selection on bank account 11XXXX and 13XXXXX.
*******************************************************************
*  -->  tsako t_bsis_all
*  <--  t_bsis_tot
*******************************************************************
FORM 03_SELECT_BSEG.

  LOOP AT TSAKO WHERE Y_BQ_AC = ' '.
    SELECT *
      FROM BSEG
      INTO T_BSEG
     WHERE BUKRS EQ TSAKO-BUKRS
       AND HKONT EQ TSAKO-HKONT
       AND SHKZG EQ TSAKO-SHKZG
*AAHOUNOU11122006
       AND GJAHR >= 2004.
*AAHOUNOU11122006

      CHECK T_BSEG-AUGDT IS INITIAL
        OR  T_BSEG-AUGDT GT P_BUDAT.

      SELECT SINGLE *
        FROM BKPF
        INTO T_BKPF
       WHERE BUKRS = T_BSEG-BUKRS
         AND BELNR = T_BSEG-BELNR
         AND GJAHR = T_BSEG-GJAHR
         AND BUDAT LE P_BUDAT.

      IF SY-SUBRC EQ 0.
        MOVE-CORRESPONDING T_BSEG TO T_BSIS_ALL.
        MOVE-CORRESPONDING T_BKPF TO T_BSIS_ALL.
        APPEND T_BSIS_ALL.
      ENDIF.

    ENDSELECT.     " FROM BSEG
  ENDLOOP.

  LOOP AT T_BSIS_ALL
    WHERE HKONT+3(2) = C_ACCOUNT_NUMBER_11
      OR  HKONT+3(2) = C_ACCOUNT_NUMBER_13
      OR  HKONT+3(2) = C_ACCOUNT_NUMBER_15.

    MOVE-CORRESPONDING T_BSIS_ALL TO T_BSIS_TOT.
    APPEND T_BSIS_TOT.
  ENDLOOP.

ENDFORM.                                         " 03_select_bseg

*******************************************************************
*      Form  04_select_balance
*******************************************************************
*       text
*******************************************************************
*  -->  t_bnka t_t012k
*  <--  glt0   tsako
*******************************************************************
FORM 04_SELECT_BALANCE.

  CLEAR W_BALANCE.

  LOOP AT TSAKO
    WHERE HKONT+3(2) = C_ACCOUNT_NUMBER_10
      OR  HKONT+3(2) = C_ACCOUNT_NUMBER_12
      OR  HKONT+3(2) = C_ACCOUNT_NUMBER_14.

    CHECK TSAKO-Y_BQ_AC = ' '.

    SELECT *
      FROM  GLT0
     WHERE  RLDNR  = '00'
       AND  RRCTY  = '0'
       AND  RVERS  = '001'
       AND  BUKRS  = P_BUKRS

       AND  RYEAR  = P_BUDAT+0(4)

       AND  RACCT  = TSAKO-HKONT
**         AND  rbusa  NE 'X'
       AND  RTCUR  = T_T012K-WAERS
       AND  DRCRK  = TSAKO-SHKZG.
*         AND  rpmax  = '016'


      CASE GLT0-DRCRK.
        WHEN 'H'.
          W_BALANCE = W_BALANCE + GLT0-TSLVT.
        WHEN 'S'.
          W_BALANCE = W_BALANCE - GLT0-TSLVT.
      ENDCASE.


    ENDSELECT.
  ENDLOOP.      " AT tsako

ENDFORM.                                         " 04_select_balance.

*******************************************************************
*      Form  05_header_detail_stat
*******************************************************************
*       text
*******************************************************************
*  -->  t_bnka t_t012k
*  <--  p2        text
*******************************************************************
FORM 05_HEADER_DETAIL_STAT.

* Report title
  GET PF-STATUS W_STATUS.
  CASE W_STATUS.
    WHEN 'STAT'.
      WRITE: 34 TEXT-H01,
                P_BUDAT.
    WHEN 'RECO'.
      WRITE: 44 TEXT-H09,
                P_BUDAT.
    WHEN 'LIST'.
      WRITE: 45 TEXT-H10,
                P_BUDAT.
  ENDCASE.
  WRITE: 117 TEXT-H08,        "Day Date
             SY-DATUM.

* Bank and account info
  READ TABLE T_BNKA INDEX 1.
  WRITE:/    TEXT-H02,        "Name of Bank:
             T_BNKA-BANKA.

  READ TABLE T_T012K INDEX 1.
  WRITE:/    TEXT-H03,        "Name of bank account:
             T_T012K-TEXT1.
  WRITE:/    TEXT-H04,        "House bank:
             T_T012K-HBKID,
             T_BNKA-BANKL.
  WRITE:/    TEXT-H05,        "Account Number:
             T_T012K-HKTID,
             T_T012K-BANKN,
         120 TEXT-H06,        "Currency:
             T_T012K-WAERS.
  WRITE /.


ENDFORM.                               " 05_header_detail_stat


*******************************************************************
*      Form  07_edition_stat
*******************************************************************
*       text
*******************************************************************
*  -->
*  <--
*******************************************************************
FORM 07_EDITION_STAT.

* EMAR20022002
*  WRITE: / 'DETAILS - PAGE:',
*           SY-PAGNO.

*selecting sub totals A B C D :
  PERFORM 071_SUBTOTAL_A.
  PERFORM 073_SUBTOTAL_B.
  PERFORM 075_SUBTOTAL_C.
  PERFORM 077_SUBTOTAL_D.
  PERFORM 079_BALANCE.

ENDFORM.                                          " 07_edition_stat

*******************************************************************
*      FORM 09_set_correspondance                    " AEM161101
*******************************************************************
*       text
*******************************************************************
*  -->  p1        text
*  <--  p2        text
*******************************************************************
FORM 09_SET_CORRESPONDANCE.

  DATA: BEGIN OF T_BELEG OCCURS 0.
          INCLUDE STRUCTURE  DTA_BELEGE.
  DATA: END OF T_BELEG.

  DATA: W_VBLNR_C(10) TYPE C.

* Get correspondance
  REFRESH T_CORRESP.
  CLEAR T_BSIS_ALL.
  LOOP AT T_BSIS_ALL.

    CHECK T_BSIS_ALL-HKONT+3(2) = C_ACCOUNT_NUMBER_11
       OR T_BSIS_ALL-HKONT+3(2) = C_ACCOUNT_NUMBER_13.
*{   INSERT         DUBK900809                                        1
*Traitement spécifique UBO /
IF T_BSIS_ALL-BUKRS EQ 'UBO'.
* Get the  corresponding documents
        CALL FUNCTION 'GET_DOCUMENTS'
             EXPORTING
                  I_REFNO       = T_BSIS_ALL-ZUONR
             TABLES
                  TAB_BELEGE    = T_BELEG
             EXCEPTIONS
                  NO_DOCUMENTS  = 1
                  NO_REGUT      = 2
                  WRONG_NUMBER  = 3
                  MISSING_UBHKT = 4
                  OTHERS        = 5.

        CHECK SY-SUBRC EQ 0.

* Store DME/Document correspondance
        LOOP AT T_BELEG.
          T_CORRESP-NUMREF = T_BSIS_ALL-ZUONR.
          T_CORRESP-BELNR  = T_BELEG-BELNR.
          APPEND T_CORRESP.
        ENDLOOP.


ELSE.

*}   INSERT

    CASE T_BSIS_ALL-ZUONR(3).

* DME File
      WHEN 'DME'.

* Get documents corresponding to a DME
        CALL FUNCTION 'GET_DOCUMENTS'
             EXPORTING
                  I_REFNO       = T_BSIS_ALL-ZUONR+3(10)
             TABLES
                  TAB_BELEGE    = T_BELEG
             EXCEPTIONS
                  NO_DOCUMENTS  = 1
                  NO_REGUT      = 2
                  WRONG_NUMBER  = 3
                  MISSING_UBHKT = 4
                  OTHERS        = 5.

        CHECK SY-SUBRC EQ 0.

* Store DME/Document correspondance
        LOOP AT T_BELEG.
*AAHOUNOU20052010


* if t_bsis_all-belnr+0(2) eq '20 '.
          T_CORRESP-NUMREF = T_BSIS_ALL-ZUONR.
          T_CORRESP-BELNR  = T_BELEG-BELNR.
          APPEND T_CORRESP.
* else.
*          t_corresp-numref = t_bsis_all-zuonr.
*          t_corresp-belnr  = t_beleg-belnr.
*          append t_corresp.
*
* endif.
*AAHOUNOU20052010
        ENDLOOP.

* CHEQUES
      WHEN 'CHQ'.
        WRITE: T_BSIS_ALL-ZUONR+3(10)
            TO W_VBLNR_C NO-ZERO.
        CONDENSE W_VBLNR_C NO-GAPS.
* Get documents corresponding to cheque number
        SELECT * FROM  PAYR
               WHERE  ZBUKR  = P_BUKRS
                AND   HBKID  = P_HBKID
                AND   HKTID  = P_HKTID
                AND   CHECT  = W_VBLNR_C.

* Store CHEQUE/Document correspondance
          T_CORRESP-NUMREF = T_BSIS_ALL-ZUONR.
          T_CORRESP-BELNR  = PAYR-VBLNR.
          APPEND T_CORRESP.
        ENDSELECT.

    ENDCASE.
*{   INSERT         DUBK900809                                        2
ENDIF.
*}   INSERT

  ENDLOOP.     " at t_bsis_all

* Set correspondance
  CLEAR T_CORRESP.
  LOOP AT T_CORRESP.
    CLEAR T_BSIS_ALL.
    LOOP AT T_BSIS_ALL
      WHERE BELNR EQ T_CORRESP-BELNR.
      T_BSIS_ALL-ZUONR = T_CORRESP-NUMREF.
      MODIFY T_BSIS_ALL.
    ENDLOOP.    " at t_bsis_all

    CLEAR T_BSIS_TOT.
    LOOP AT T_BSIS_TOT
      WHERE BELNR EQ T_CORRESP-BELNR.
      T_BSIS_TOT-ZUONR = T_CORRESP-NUMREF.
      MODIFY T_BSIS_TOT.
    ENDLOOP.    " at t_bsis_tot
  ENDLOOP.   " at t_corresp

ENDFORM.                               " 09_set_correspondance

*******************************************************************
*      Form  11_sort_bsis_for_clearing
*******************************************************************
*       text
*******************************************************************
*  -->  t_bsis_all t_bsis_tot
*  <--  t_bsis_tot t_bsis_edit
*******************************************************************
FORM 11_SORT_BSIS_FOR_CLEARING.

  DATA Y_N1 TYPE I VALUE 0.
  DATA Y_N2 TYPE I VALUE 0.
  DATA Y_N3 TYPE I VALUE 0.
  DATA Y_OLD_ZUONR LIKE BSIS-ZUONR.  "Assignment number

  CLEAR Y_OLD_ZUONR.

  SORT T_BSIS_ALL BY ZUONR.
  SORT T_BSIS_TOT BY ZUONR.


  LOOP AT T_BSIS_ALL
    WHERE HKONT+3(2) = C_ACCOUNT_NUMBER_11
      OR  HKONT+3(2) = C_ACCOUNT_NUMBER_13.

    IF T_BSIS_ALL-ZUONR NE Y_OLD_ZUONR.

      LOOP AT T_BSIS_TOT WHERE ZUONR = T_BSIS_ALL-ZUONR.

        CONCATENATE SY-ABCDE+Y_N3(1) SY-ABCDE+Y_N2(1) SY-ABCDE+Y_N1(1)
          INTO T_BSIS_TOT-Y_CHAR.
        MODIFY T_BSIS_TOT.

        MOVE-CORRESPONDING T_BSIS_TOT TO T_BSIS_EDIT.
* Collect table for subtotal sorted by Clearing key
        PERFORM 111_SUB_TOTAL.
        APPEND T_BSIS_EDIT.

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

    Y_OLD_ZUONR = T_BSIS_ALL-ZUONR.

  ENDLOOP.      "AT t_bsis_all

ENDFORM.                               " 11_sort_bsis_for_clearing

*******************************************************************
*      Form  13_edit_bsis_for_clearing
*******************************************************************
*       text
*******************************************************************
*  -->  t_subtotal t_bsis_edit
*  <--
*******************************************************************
FORM 13_EDIT_BSIS_FOR_CLEARING.

* EMAR20022002
*  WRITE: / 'DETAILS - PAGE:',
*           SY-PAGNO.

* Generate amounts (absolute value) for sorting subtotal table
  PERFORM 131_GET_AMOUNTS_ABSOLUTE_VALUE.

  SORT T_BSIS_EDIT BY Y_CHAR GSBER DESCENDING BELNR BUZEI.
  SORT T_SUBTOTAL  BY ABS_WRBTR WRBTR Y_CHAR ASCENDING.

  CLEAR Y_OLD_CHAR.
  CLEAR Y_OLD_WRBTR.

  FORMAT INTENSIFIED OFF.

  LOOP AT T_SUBTOTAL.

    IF T_SUBTOTAL-Y_CHAR NE Y_OLD_CHAR AND SY-TABIX NE 1.
      PERFORM 133_FOOTER_DETAIL.
    ENDIF.

    IF T_SUBTOTAL-Y_CHAR NE Y_OLD_CHAR OR SY-TABIX EQ 1.
      PERFORM 135_HEADER_DETAIL.
    ENDIF.

    IF T_SUBTOTAL-Y_CHAR = SPACE AND Y_OLD_CHAR = SPACE.
      ULINE.
    ENDIF.

    LOOP AT T_BSIS_EDIT WHERE Y_CHAR = T_SUBTOTAL-Y_CHAR.


      WRITE:/  SY-VLINE,
               T_BSIS_EDIT-Y_CHAR, " Key
               SY-VLINE,
               T_BSIS_EDIT-BELNR,  " Doc. No.
               SY-VLINE,
           (4) T_BSIS_EDIT-BUZEI,  " Item
               SY-VLINE,
          (12) T_BSIS_EDIT-BUDAT,  " Posting date
               SY-VLINE,
               T_BSIS_EDIT-VALUT,  " Value date
               SY-VLINE,
               T_BSIS_EDIT-ZUONR,  " Assignment
               SY-VLINE,
               T_BSIS_EDIT-GSBER,  " B.A.
               SY-VLINE,
               T_BSIS_EDIT-HKONT,  " Acc. num.
               SY-VLINE,
               T_BSIS_EDIT-WRBTR CURRENCY T_T012K-WAERS,  " Amount
               T_BSIS_EDIT-WAERS,  " Currency
               SY-VLINE.
      CASE T_BSIS_EDIT-SHKZG.
        WHEN 'H'.      " Credit
          WRITE: ' C '.
        WHEN 'S'.      " Debit
          WRITE: ' D '.
        WHEN OTHERS.
          WRITE: '   '.
      ENDCASE.
      WRITE: SY-VLINE,
             T_BSIS_EDIT-SGTXT,  " Description
             SY-VLINE.


    ENDLOOP. "AT t_bsis_edit


    Y_OLD_CHAR  = T_SUBTOTAL-Y_CHAR.
    Y_OLD_WRBTR = T_SUBTOTAL-WRBTR.

  ENDLOOP. "AT t_subtotal

  IF SY-SUBRC = 4.
* No Items to be cleared
    WRITE:/ TEXT-007.        "No items to be cleared
  ELSE.
    PERFORM 133_FOOTER_DETAIL.
  ENDIF.

ENDFORM.                               " 13_edit_bsis_for_clearing

*******************************************************************
*      Form  15_update_items
*******************************************************************
*       text
*******************************************************************
*  -->  t_bsis_temp t_bsis_edit
*  <--  t_subtotal t_bsis_edit
*******************************************************************
FORM 15_UPDATE_ITEMS.

  DATA: Y_OLD_CHAR(3)    TYPE C.
  DATA: Y_NEW_CHAR(3)    TYPE C.
  DATA: Y_FLAG_DELETE(1) TYPE C.
  DATA: Y_FLAG_ERROR(1) TYPE C.

* Check inconsistant currency
  CLEAR Y_FLAG_ERROR.
  LOOP AT  T_BSIS_TEMP.

    LOOP AT T_BSIS_EDIT WHERE Y_CHAR EQ T_BSIS_TEMP-Y_CHAR
                          AND WAERS  NE T_BSIS_TEMP-WAERS.
      Y_FLAG_ERROR = 'X'.
      EXIT.
    ENDLOOP.              " AT t_bsis_edit

*     Change to different currency is forbidden
    IF Y_FLAG_ERROR = 'X'.
      MESSAGE I398(00) WITH TEXT-008
                            TEXT-009.
      EXIT.
    ENDIF.
  ENDLOOP.                " AT  t_bsis_temp

  CHECK Y_FLAG_ERROR NE 'X'.

* Update t_bsis_edit
  LOOP AT  T_BSIS_TEMP.

    LOOP AT T_BSIS_EDIT WHERE BUKRS = T_BSIS_TEMP-BUKRS
                          AND BELNR = T_BSIS_TEMP-BELNR
                          AND BUZEI = T_BSIS_TEMP-BUZEI
                          AND ZUONR = T_BSIS_TEMP-ZUONR.

      Y_OLD_CHAR = T_BSIS_EDIT-Y_CHAR.
      Y_NEW_CHAR = T_BSIS_TEMP-Y_CHAR.

*     If there is a change of clearing key
      IF T_BSIS_EDIT-Y_CHAR NE T_BSIS_TEMP-Y_CHAR.

        CLEAR T_SUBTOTAL.

*       Update subtotal table
        T_SUBTOTAL-Y_CHAR = T_BSIS_TEMP-Y_CHAR.
        T_SUBTOTAL-WAERS  = T_BSIS_TEMP-WAERS.
        IF T_BSIS_EDIT-SHKZG = 'H'.      "Credit
          T_SUBTOTAL-WRBTR = T_BSIS_TEMP-WRBTR.
        ELSEIF T_BSIS_EDIT-SHKZG = 'S'.  "Debit
          T_SUBTOTAL-WRBTR = T_BSIS_TEMP-WRBTR * -1.
        ENDIF.
        COLLECT T_SUBTOTAL.

        T_SUBTOTAL-Y_CHAR = T_BSIS_EDIT-Y_CHAR.
        T_SUBTOTAL-WAERS  = T_BSIS_EDIT-WAERS.
        IF T_BSIS_EDIT-SHKZG = 'H'.      "Credit
          T_SUBTOTAL-WRBTR = T_BSIS_EDIT-WRBTR * -1.
        ELSEIF T_BSIS_EDIT-SHKZG = 'S'.  "Debit
          T_SUBTOTAL-WRBTR = T_BSIS_EDIT-WRBTR.
        ENDIF.
        COLLECT T_SUBTOTAL.

*       Update t_bsis_edit
        MOVE T_BSIS_TEMP-Y_CHAR TO T_BSIS_EDIT-Y_CHAR.
        MODIFY T_BSIS_EDIT.

      ENDIF.


    ENDLOOP.

  ENDLOOP.

* Delete record from subtotal table if there is not any document
* for the old clearing key
  LOOP AT T_BSIS_EDIT WHERE Y_CHAR = Y_OLD_CHAR.
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

ENDFORM.                                         " 15_update_items

*******************************************************************
*      Form  071_subtotal_a
*******************************************************************
*       text
*******************************************************************
*  -->  t_bsis_tot
*  <--  p2        text
*******************************************************************
FORM 071_SUBTOTAL_A.

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
  PERFORM 0711_HEADER_SUB_TOTAL_AC.


* Editing list values
  LOOP AT T_BSIS_TOT WHERE SHKZG = 'S'.

    CHECK T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_11
       OR T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_13
       OR T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_15.

* Ajour de Z3 EMAR31072002
    CHECK T_BSIS_TOT-BLART = 'Z1'
       OR T_BSIS_TOT-BLART = 'Z2'
       OR T_BSIS_TOT-BLART = 'Z3'.

    SUM_AMOUNT_A = SUM_AMOUNT_A + T_BSIS_TOT-WRBTR.

    WRITE:/     SY-VLINE,
                T_BSIS_TOT-BUDAT,
                SY-VLINE,
                T_BSIS_TOT-VALUT,
                SY-VLINE,
                T_BSIS_TOT-BELNR,
                SY-VLINE,
                T_BSIS_TOT-SGTXT,
                SY-VLINE,
                T_BSIS_TOT-ZUONR,
                SY-VLINE,
                T_BSIS_TOT-WRBTR CURRENCY T_T012K-WAERS,
                SY-VLINE.
    ULINE AT /(133).

  ENDLOOP.

  WRITE:/     SY-VLINE.
  FORMAT COLOR 3 ON.         " Yellow
  WRITE: TEXT-K11,           " sub total ADD = A
     116 SUM_AMOUNT_A CURRENCY T_T012K-WAERS.
  FORMAT COLOR 3 OFF.
  WRITE: SY-VLINE.
  ULINE AT /(133).

ENDFORM.                                           " 071_subtotal_a


*******************************************************************
*      Form  073_subtotal_b
*******************************************************************
*       text
*******************************************************************
*  -->  t_bsis_tot
*  <--
*******************************************************************
FORM 073_SUBTOTAL_B.

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
  PERFORM 0731_HEADER_SUB_TOTAL_BD.

* Editing list values
  LOOP AT T_BSIS_TOT WHERE SHKZG = 'S'.

    CHECK T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_11
       OR T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_13
       OR T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_15.

* Ajour de Z3 EMAR31072002
    CHECK T_BSIS_TOT-BLART NE 'Z1'
      AND T_BSIS_TOT-BLART NE 'Z2'
      AND T_BSIS_TOT-BLART NE 'Z3'.

    SUM_AMOUNT_B = SUM_AMOUNT_B + T_BSIS_TOT-WRBTR.

    WRITE:/     SY-VLINE ,
                T_BSIS_TOT-BUDAT,
                SY-VLINE,
                T_BSIS_TOT-VALUT,
                SY-VLINE,
                T_BSIS_TOT-BELNR,
                SY-VLINE,
                T_BSIS_TOT-SGTXT,
                SY-VLINE,
                T_BSIS_TOT-ZUONR,
                SY-VLINE,
                T_BSIS_TOT-WRBTR CURRENCY T_T012K-WAERS,
                SY-VLINE.
    ULINE AT /(133).

  ENDLOOP.

  WRITE:/     SY-VLINE.
  FORMAT COLOR 3 ON.         " Yellow
  WRITE: TEXT-K13,           " Sub total ADD = B
     116 SUM_AMOUNT_B CURRENCY T_T012K-WAERS.
  FORMAT COLOR 3 OFF.
  WRITE: SY-VLINE.
  ULINE AT /(133).

ENDFORM.                                           " 073_subtotal_b

*******************************************************************
*      Form  075_subtotal_c
*******************************************************************
*       text
*******************************************************************
*  -->  t_bsis_tot
*  <--
*******************************************************************
FORM 075_SUBTOTAL_C.

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
  PERFORM 0711_HEADER_SUB_TOTAL_AC.

  LOOP AT T_BSIS_TOT WHERE SHKZG = 'H'.

    CHECK T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_11
       OR T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_13
       OR T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_15.

* Ajout de Z3 EAMR31072002
    CHECK T_BSIS_TOT-BLART = 'Z1'
       OR T_BSIS_TOT-BLART = 'Z2'
       OR T_BSIS_TOT-BLART = 'Z3'.

    SUM_AMOUNT_C = SUM_AMOUNT_C + T_BSIS_TOT-WRBTR.

    WRITE:/     SY-VLINE,
                T_BSIS_TOT-BUDAT,
                SY-VLINE,
                T_BSIS_TOT-VALUT,
                SY-VLINE,
                T_BSIS_TOT-BELNR,
                SY-VLINE,
                T_BSIS_TOT-SGTXT,
                SY-VLINE,
                T_BSIS_TOT-ZUONR,
                SY-VLINE,
                T_BSIS_TOT-WRBTR CURRENCY T_T012K-WAERS,
                SY-VLINE.
    ULINE AT /(133).

  ENDLOOP.

  WRITE:/     SY-VLINE.
  FORMAT COLOR 3 ON.         " Yellow
  WRITE: TEXT-K16,           " Sub total DEDUCT = C
     116 SUM_AMOUNT_C CURRENCY T_T012K-WAERS.
  FORMAT COLOR 3 OFF.
  WRITE: SY-VLINE.
  ULINE AT /(133).

ENDFORM.                                           " 075_subtotal_c


*******************************************************************
*      Form  077_subtotal_d
*******************************************************************
*       text
*******************************************************************
*  -->  p1        text
*  <--  p2        text
*******************************************************************
FORM 077_SUBTOTAL_D.

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
  PERFORM 0731_HEADER_SUB_TOTAL_BD.

  LOOP AT T_BSIS_TOT WHERE SHKZG = 'H'.

    CHECK T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_11
       OR T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_13
       OR T_BSIS_TOT-HKONT+3(2) = C_ACCOUNT_NUMBER_15.

* Ajout Z3 EMAR31072002
    CHECK T_BSIS_TOT-BLART NE 'Z1'
      AND T_BSIS_TOT-BLART NE 'Z2'
      AND T_BSIS_TOT-BLART NE 'Z3'.

    SUM_AMOUNT_D = SUM_AMOUNT_D + T_BSIS_TOT-WRBTR.


    SELECT CHECT FROM PAYR INTO WA_CHECT
    WHERE VBLNR = T_BSIS_TOT-BELNR .
    ENDSELECT.

    IF SY-SUBRC = 0 .
*Préparation du numéro ce chèque à afficher précédé de CH
      IF NOT WA_CHECT IS INITIAL .
        CONCATENATE 'CHQ' WA_CHECT INTO WA_CHECT_DER .
        CLEAR WA_CHECT .
      ENDIF .
    ENDIF .

    WRITE:/     SY-VLINE,
                T_BSIS_TOT-BUDAT,
                SY-VLINE,
                T_BSIS_TOT-VALUT,
                SY-VLINE,
                T_BSIS_TOT-BELNR,
                SY-VLINE,
         (50)   WA_CHECT_DER,
                SY-VLINE,
         (18)   T_BSIS_TOT-ZUONR,
                SY-VLINE,
         (16)   T_BSIS_TOT-WRBTR CURRENCY T_T012K-WAERS,
                SY-VLINE.
    ULINE AT /(133).

    CLEAR WA_CHECT_DER .

  ENDLOOP.

  WRITE:/     SY-VLINE.
  FORMAT COLOR 3 ON.         " Yellow
  WRITE: TEXT-K19,           " Sub total DEDUCT = D
     116 SUM_AMOUNT_D CURRENCY T_T012K-WAERS.
  FORMAT COLOR 3 OFF.
  WRITE: SY-VLINE.
  ULINE AT /(133).

  SKIP.
  SKIP.

ENDFORM.                                           " 077_subtotal_d


*******************************************************************
*      Form  079_balance
*******************************************************************
*       text
*******************************************************************
*  -->  t_bseg
*  <--  p2        text
*******************************************************************
FORM 079_BALANCE.

* dernière page EMAR20022002
  MOVE 'X' TO W_LAST_PAGE.

  DATA: SUM_E   LIKE BSIS-WRBTR,
        SUM_F   LIKE BSIS-WRBTR,
        SUM_H   LIKE BSIS-WRBTR,
        SUM_G   LIKE BSIS-WRBTR,
        SUM_E_F LIKE BSIS-WRBTR.

  NEW-PAGE.
  PERFORM 05_HEADER_DETAIL_STAT.
  WRITE: / 'OVERVIEW'.

* Sub total ADD
  SUM_F = SUM_AMOUNT_A + SUM_AMOUNT_B.

* Sub total DEDUCT
  SUM_G = SUM_AMOUNT_C + SUM_AMOUNT_D.

* Bank balance at clearing date
* sum_e initialized to carryforward value


*  sum_e = w_balance.


*  clear t_bsis_all.
*  loop at t_bsis_all
*    where hkont+3(2) = c_account_number_10
*       or hkont+3(2) = c_account_number_12
*       or hkont+3(2) = c_account_number_14.
**AHOUNOU
*    check t_bsis_all-gjahr <= p_budat+0(4).
**AHOUNOU
*    case t_bsis_all-shkzg.
*      when 'S'.
*        sum_e = sum_e + t_bsis_all-wrbtr.
*      when 'H'.
*        sum_e = sum_e - t_bsis_all-wrbtr.
*    endcase.
*
*  endloop.

******************************************************
*AHOUNOU
CLEAR SUM_E.
  CLEAR T_BSIS_ALL.
  REFRESH T_BSIS_ALL.
    LOOP AT TSAKO WHERE Y_BQ_AC = ' '.
    SELECT * FROM BSIS APPENDING TABLE T_BSIS_ALL
                        WHERE BUKRS EQ TSAKO-BUKRS
                          AND HKONT EQ TSAKO-HKONT
                          AND BUDAT LE P_BUDAT
                          AND SHKZG EQ TSAKO-SHKZG.
   ENDLOOP.

  LOOP AT T_BSIS_ALL
    WHERE HKONT+3(2) = C_ACCOUNT_NUMBER_10
       OR HKONT+3(2) = C_ACCOUNT_NUMBER_12
       OR HKONT+3(2) = C_ACCOUNT_NUMBER_14.

    CHECK T_BSIS_ALL-GJAHR <= P_BUDAT+0(4).

      CASE T_BSIS_ALL-SHKZG.
      WHEN 'S'.
        SUM_E = SUM_E + T_BSIS_ALL-WRBTR.
      WHEN 'H'.
        SUM_E = SUM_E - T_BSIS_ALL-WRBTR.
    ENDCASE.


   ENDLOOP.
*AHOUNOU


******************************************************

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
                 P_BUDAT,
             64  SY-VLINE,
            (30) '  ',
                 SY-VLINE,
            (30) SUM_E CURRENCY T_T012K-WAERS,
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
          (30) SUM_AMOUNT_A CURRENCY T_T012K-WAERS,
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
          (30) SUM_AMOUNT_B CURRENCY T_T012K-WAERS,
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
          (30) SUM_F CURRENCY T_T012K-WAERS,
               SY-VLINE,
          (30) SUM_E_F CURRENCY T_T012K-WAERS,
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
          (30) SUM_AMOUNT_C CURRENCY T_T012K-WAERS,
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
          (30) SUM_AMOUNT_D CURRENCY T_T012K-WAERS,
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
          (30) SUM_G CURRENCY T_T012K-WAERS,
               SY-VLINE,
          (30) SUM_H CURRENCY T_T012K-WAERS,
           133 SY-VLINE.
  ULINE (133).
  SKIP.
  ULINE (133).

  WRITE:/      SY-VLINE,
               TEXT-K25,          "Balance in accounting at
               P_BUDAT,
          64   SY-VLINE,
          (32) ' ',
          (30) SUM_H CURRENCY T_T012K-WAERS,
          133  SY-VLINE.
  ULINE (133).

ENDFORM.                                              " 079_balance

*******************************************************************
*      Form  0711_header_sub_total_ac
*******************************************************************
*       text
*******************************************************************
FORM 0711_HEADER_SUB_TOTAL_AC.

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

ENDFORM.                               " 0711_header_sub_total_ac

*******************************************************************
*      Form  0731_header_sub_total_bd
*******************************************************************
*       text
*******************************************************************
FORM 0731_HEADER_SUB_TOTAL_BD.

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

ENDFORM.                               " 0731_header_sub_total_bd

*******************************************************************
*      Form  111_sub_total
*******************************************************************
*       text
*******************************************************************
*  -->  t_bsis_edit
*  <--  t_subtotal
*******************************************************************
FORM 111_SUB_TOTAL.

  MOVE: T_BSIS_EDIT-Y_CHAR TO T_SUBTOTAL-Y_CHAR,
        T_BSIS_EDIT-WRBTR  TO T_SUBTOTAL-WRBTR,
        T_BSIS_EDIT-WAERS  TO T_SUBTOTAL-WAERS.

  IF T_BSIS_EDIT-SHKZG = 'S'.
    T_SUBTOTAL-WRBTR = T_SUBTOTAL-WRBTR * -1.
  ENDIF.

  COLLECT T_SUBTOTAL.

ENDFORM.                                         " 111_sub_total

*******************************************************************
*      Form  131_get_amounts_absolute_value
*******************************************************************
*       text
*******************************************************************
*  -->  t_subtotal
*  <--  t_subtotal
*******************************************************************
FORM 131_GET_AMOUNTS_ABSOLUTE_VALUE.

  LOOP AT T_SUBTOTAL.
    COMPUTE T_SUBTOTAL-ABS_WRBTR = ABS( T_SUBTOTAL-WRBTR ).
    MODIFY T_SUBTOTAL.
  ENDLOOP.

ENDFORM.                          " 131_get_amounts_absolute_value

*******************************************************************
*      Form  133_footer_detail
*******************************************************************
*       text
*******************************************************************
*  -->  y_old_char y_old_wrbtr
*  <--
*******************************************************************
FORM 133_FOOTER_DETAIL.

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
         98  Y_OLD_WRBTR CURRENCY T_T012K-WAERS,
         180 SY-VLINE.
  WRITE:/1(180) SY-ULINE.
  WRITE:/ .

ENDFORM.                                         " 133_footer_detail

*******************************************************************
*      Form  135_HEADER_DETAIL
*******************************************************************
*       text
*******************************************************************
FORM 135_HEADER_DETAIL.

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

ENDFORM.                               " 135_header_detail
*&---------------------------------------------------------------------*
*&      Form  bdcdata_fbra
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->P_BDCTAB  text
*      -->P_T_BSIS_BELNR  text
*      -->P_T_BSIS_F_04  text
*----------------------------------------------------------------------*
FORM BDCDATA_FBRA     TABLES BDCDTAB      STRUCTURE BDCDATA
            T_BSIS_BELNR STRUCTURE T_BSIS_BELNR
      USING T_BSIS       STRUCTURE T_BSIS_F-04.



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
  BDCDTAB-FVAL = T_BSIS_F-04-BUKRS .
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'RF05R-GJAHR'.
  BDCDTAB-FVAL = SY-DATUM+0(4).
  APPEND BDCDTAB.

  CLEAR BDCDTAB.
  BDCDTAB-FNAM = 'BDC_OKCODE'.
  BDCDTAB-FVAL = '=RAGL'.
  APPEND BDCDTAB.

ENDFORM.                    " bdcdata_fbra
*&---------------------------------------------------------------------*
*&      Form  bdcdata_fbra
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->P_BDCTAB  text
*      -->P_T_BSIS_BELNR  text
*      -->P_T_BSIS_F_04  text
*----------------------------------------------------------------------*
FORM BDCDATA_FB08     TABLES BDCDTAB      STRUCTURE BDCDATA
            T_BSIS_BELNR STRUCTURE T_BSIS_BELNR
      USING T_BSIS       STRUCTURE T_BSIS_F-04.



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
  BDCDTAB-FVAL = T_BSIS_F-04-BUKRS .
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

ENDFORM.                    " bdcdata_fbra