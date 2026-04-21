*-------------------------------------------------------------------*
*   INCLUDE YTBAM001                                                *
*-------------------------------------------------------------------*

*********************************************************************
* CHANGE HISTORY
*
* Date       By      Correction Number & Brief Description  Release
*
* 18/12/2001 AEM     0001 For all cheques, suppress leading zeros
*                         Send CHQ+cheqnumber into assignement zone
*
* 15/02/2002 EM      0001 Codes SWIFT CPS et Smartlink
*
* Modification EMAR06032002 : Modification Smartlink (transferts
* domestiques)
*
* 25/06/2002 FB250602 modification SMARTLINK pour les checks deposits
*
*********************************************************************


CONSTANTS: C_CHECT     LIKE FEBEP-CHECT VALUE 'NONREF',
           C_STRING(7) TYPE C VALUE 'CMBREF='.

*--------------------------------------------------------------------*
* Itss - Tecnologia
* Local Variables - Improvement Project to Brazil Payments
*--------------------------------------------------------------------*
DATA : IT_REGUP      TYPE TABLE OF REGUP,            "Internal Table
       WA_REGUP      LIKE LINE  OF IT_REGUP,         "Work Area
       IT_BDC        TYPE STANDARD TABLE OF BDCDATA, "Internal Table
       WA_BDC        TYPE BDCDATA,                   "Work Area
       IT_MESSAGES   TYPE STANDARD TABLE OF BDCMSGCOLL, "Internal Table
       VL_EVENT      TYPE T048-EVENT,
       VL_PROCESS(3) TYPE C,
*      vl_lifnr      TYPE regup-lifnr,
       VL_LIFNR      TYPE RF05A-KONTO,
       LV_GSBER      TYPE GSBER.

DATA LO_FEB_BSPROC_BS_ITEM TYPE REF TO YCL_FI_BSPROC_BS_ITEM.

*--------------------------------------------------------------------*
* Constants
*--------------------------------------------------------------------*
CONSTANTS C_FB09(4) TYPE C VALUE 'FB09'.

*--------------------------------------------------------------------*
* Macros
*--------------------------------------------------------------------*
DEFINE SET_BDC.
  " &1 - Screen
  " &2 - Screen'Field
  " &3 - Screen Number/ Field Value

  IF &1 EQ 'X'.
    MOVE: &2  TO WA_BDC-PROGRAM,
          &3  TO WA_BDC-DYNPRO,
          'X' TO WA_BDC-DYNBEGIN.
  ELSE.
    MOVE: &2  TO WA_BDC-FNAM,
          &3  TO WA_BDC-FVAL.
  ENDIF.

  APPEND WA_BDC TO IT_BDC.
  CLEAR  WA_BDC.
END-OF-DEFINITION.
*--------------------------------------------------------------------*

DATA: BEGIN OF ITAB OCCURS 0,
        WORD(20),
      END   OF ITAB.
*   deb FB250602
*** modifications apportées lorsque le n° de chèque contient 'NONREF'
*** table pour instructions split
*
DATA: BEGIN OF T_SPLIT OCCURS 0,
        WORD(256),
      END   OF T_SPLIT.

DATA: W_TAMPON(2560) TYPE C,
      W_NBRE         TYPE I,
      W_INDEX        LIKE SY-TABIX.
*
*   fin FB250602

DATA: Y_BUFFER(2000) TYPE C,
      Y_FDPOS        LIKE SY-FDPOS,
      Y_DMENUM(10)   TYPE N.
DATA: W_VBLNR_C(10) TYPE C.     " AEM181201+
DATA: INT TYPE I.

DATA LS_YBASUBST TYPE YBASUBST.

*UBO UBO UBO UBO UBO UBO UBO UBO UBO UBO UBO UBO
*Traitement pour Intégration bancaire / Brazil / UBO
IF ( I_FEBKO-EFART = 'E' ) AND  ( I_FEBKO-BUKRS = 'UBO' ).

*--------------------------------------------------------------------*
* Start - Itss Tecnologia - Adds the identifier to generate a letter
*--------------------------------------------------------------------*
  IF I_FEBKO-BUKRS  = 'UBO' AND I_FEBEP-VGINT = 'UBOA'.   "Pagamento aprovado
    VL_EVENT   = 'ZSP01'.
    VL_PROCESS = 'ZAH'.
  ELSEIF I_FEBKO-BUKRS  = 'UBO' AND I_FEBEP-VGINT = 'UBOR'.	"Pagamento rejeitado
    VL_EVENT   = 'ZSP09'.
    VL_PROCESS = 'BAN'.
* ENDIF.

    SELECT * FROM REGUP INTO TABLE IT_REGUP
      WHERE BUKRS EQ I_FEBKO-BUKRS
       AND  VBLNR EQ I_FEBEP-BELNR
*    AND  budat EQ i_febep-budat.
       AND  GJAHR EQ I_FEBEP-BUDAT(4).

    LOOP AT IT_REGUP INTO WA_REGUP.
*   Set data to call FB09
      VL_LIFNR = WA_REGUP-LIFNR.
      SET_BDC 'X' 'SAPMF05L' '0102'.
      SET_BDC ''  'BDC_CURSOR' 'RF05L-XKKRE'.
      SET_BDC ''  'BDC_OKCODE' '/00'.
      SET_BDC ''  'RF05L-BELNR' WA_REGUP-BELNR.
      SET_BDC ''  'RF05L-BUKRS' WA_REGUP-BUKRS.
      SET_BDC ''  'RF05L-GJAHR' WA_REGUP-GJAHR.
      SET_BDC ''  'RF05L-BUZEI' WA_REGUP-BUZEI.
      SET_BDC ''  'RF05L-XKKRE' 'X'.
      SET_BDC 'X' 'SAPMF05L' '0302'.
      SET_BDC ''  'BDC_CURSOR' 'BSEG-ZLSPR'.
      SET_BDC ''  'BDC_OKCODE' '=AE'.
      SET_BDC ''  'BSEG-ZLSPR' 'K'.

*   Call Transaction
      CALL TRANSACTION C_FB09 USING IT_BDC MODE 'N' UPDATE 'S'
          MESSAGES INTO IT_MESSAGES.
      REFRESH IT_BDC.
      CLEAR   WA_BDC.
    ENDLOOP.
  ENDIF.

* Call function to set
  CALL FUNCTION 'CORRESPONDENCE_REQUEST'
    EXPORTING
*     i_account       = vl_lifnr
      I_ACCOUNT_TYPE  = 'K'
      I_COMPANY_CODE  = I_FEBKO-BUKRS
      I_DBUPDATE      = 'X'
      I_DOCUMENT      = I_FEBEP-BELNR
      I_MESSAGE       = 'X'
      I_OVERWRITE_ACC = 'X'
*     i_overwrite_doc = 'X'
      I_PROCESS       = VL_PROCESS
      I_YEAR          = I_FEBEP-BUDAT(4)
      I_EVENT         = VL_EVENT.
*--------------------------------------------------------------------*

  MOVE-CORRESPONDING I_FEBEP TO E_FEBEP.
*business area
  "e_febep-gsber = 'X'.
*  IF i_febep-budat < '20221001'.
*    SELECT SINGLE * FROM ybasubst INTO ls_ybasubst WHERE bukrs = i_febko-bukrs
*                                                   AND   blart = 'Z1'
*                                                   AND   hkont = i_febko-hkont.
*    IF sy-subrc = 0.
*      e_febep-gsber = ls_ybasubst-gsber.
*    ELSE.
*
*        lo_feb_bsproc_bs_item = ycl_fi_bsproc_bs_item=>get_instance( ).
*        e_febep-gsber = lo_feb_bsproc_bs_item->get_gsber( iv_kukey = e_febep-kukey
*                                                           iv_esnum = e_febep-esnum ).
*    ENDIF.
*  ELSE.
  LV_GSBER = YCL_FI_ACCOUNT_SUBST_READ=>READ( IV_BUKRS = I_FEBKO-BUKRS
                                              IV_BLART = 'Z1'
                                              IV_HKONT = I_FEBKO-HKONT ).
  IF LV_GSBER IS NOT INITIAL.
    E_FEBEP-GSBER = LV_GSBER.
  ELSE.
    LO_FEB_BSPROC_BS_ITEM = YCL_FI_BSPROC_BS_ITEM=>GET_INSTANCE( ).
    E_FEBEP-GSBER = LO_FEB_BSPROC_BS_ITEM->GET_GSBER( IV_KUKEY = E_FEBEP-KUKEY
                                                      IV_ESNUM = E_FEBEP-ESNUM ).
  ENDIF.
* ENDIF.
*récupération assignment
  CLEAR T_FEBRE.
  READ TABLE T_FEBRE INDEX 3.
  CHECK SY-SUBRC EQ 0.

  SPLIT T_FEBRE AT ' ' INTO TABLE ITAB.
  CLEAR ITAB.
  LOOP AT ITAB.
  ENDLOOP.
  CHECK SY-SUBRC EQ 0.

  WRITE: ITAB-WORD
     TO W_VBLNR_C NO-ZERO.
  CONDENSE W_VBLNR_C NO-GAPS.
  MOVE   W_VBLNR_C TO E_FEBEP-ZUONR.

*IIEP IIEP IIEP IIEP IIEP IIEP IIEP IIEP
*Traitement pour Intégration bancaire IIEP
ELSEIF ( I_FEBKO-EFART = 'E' ) AND ( I_FEBKO-BUKRS = 'IIEP' ).
  MOVE-CORRESPONDING I_FEBEP TO E_FEBEP.
  "e_febep-gsber = 'X'.
*  IF i_febep-budat < '20221001'.
*    SELECT SINGLE * FROM ybasubst INTO ls_ybasubst WHERE bukrs = i_febko-bukrs
*                                                 AND   blart = 'Z1'
*                                                 AND   hkont = i_febko-hkont.
*    IF sy-subrc = 0.
*      e_febep-gsber = ls_ybasubst-gsber.
*    ELSE.
*      lo_feb_bsproc_bs_item = ycl_fi_bsproc_bs_item=>get_instance( ).
*      e_febep-gsber = lo_feb_bsproc_bs_item->get_gsber( iv_kukey = e_febep-kukey
*                                                        iv_esnum = e_febep-esnum ).
*    ENDIF.
*  ELSE.
  LV_GSBER = YCL_FI_ACCOUNT_SUBST_READ=>READ( IV_BUKRS = I_FEBKO-BUKRS
                                              IV_BLART = 'Z1'
                                              IV_HKONT = I_FEBKO-HKONT ).
  IF LV_GSBER IS NOT INITIAL.
    E_FEBEP-GSBER = LV_GSBER.
  ELSE.
    LO_FEB_BSPROC_BS_ITEM = YCL_FI_BSPROC_BS_ITEM=>GET_INSTANCE( ).
    E_FEBEP-GSBER = LO_FEB_BSPROC_BS_ITEM->GET_GSBER( IV_KUKEY = E_FEBEP-KUKEY
                                                      IV_ESNUM = E_FEBEP-ESNUM ).
  ENDIF.
*  ENDIF.

  CASE E_FEBEP-TEXTS.
    WHEN 'NTRF'.
      CLEAR T_FEBRE.
      LOOP AT T_FEBRE.
        Y_BUFFER = T_FEBRE-VWEZW+2(5).
        EXIT.
      ENDLOOP.
*     DME number for mass payments
      IF I_FEBKO-BUKRS = 'IIEP' AND
         I_FEBKO-HBKID = 'SOG02' AND
         I_FEBKO-HKTID = 'EUR06' AND
         Y_BUFFER EQ 'FR021'  AND
        ( E_FEBEP-CHECT(1) = '1' OR E_FEBEP-CHECT(1) = '0' ).
        LOOP AT T_FEBRE.
          IF ( T_FEBRE-VWEZW+0(5) = '<REF>'
            AND T_FEBRE-VWEZW+5(7) CO '0123456789' ).
*AHOUNOU06012014 / SEPA / 10 digits
            IF T_FEBRE-VWEZW+12(3) CO '0123456789'.
              CALL FUNCTION 'COMPUTE_CONTROL_NUMBER'
                EXPORTING
                  I_REFNO  = T_FEBRE-VWEZW+6(7)
                IMPORTING
                  E_RESULT = Y_DMENUM.

              CONCATENATE 'DME'
                          Y_DMENUM
                     INTO E_FEBEP-ZUONR.
*AHOUNOU06012014 / SEPA / 10 digits
            ELSE.
              CALL FUNCTION 'COMPUTE_CONTROL_NUMBER'
                EXPORTING
                  I_REFNO  = T_FEBRE-VWEZW+5(7)
                IMPORTING
                  E_RESULT = Y_DMENUM.

              CONCATENATE 'DME'
                          Y_DMENUM
                     INTO E_FEBEP-ZUONR.
            ENDIF.
          ENDIF.
        ENDLOOP.
      ENDIF.
**************
  ENDCASE.

*UNES UNES UNES UNES UNES UNES  UNES UNES UNES  UNES UNES UNES  UNES UNES UNES
*Traitement pour Intégration bancaire différent de IIEP  et UBO, donc UNES
ELSEIF ( I_FEBKO-EFART = 'E' ) AND ( I_FEBKO-BUKRS NE 'UBO' ) AND ( I_FEBKO-BUKRS NE 'IIEP' ).
  MOVE-CORRESPONDING I_FEBEP TO E_FEBEP.
*  IF i_febep-budat < '20221001'.
*    SELECT SINGLE * FROM ybasubst INTO ls_ybasubst WHERE bukrs = i_febko-bukrs
*                                                   AND   blart = 'Z1'
*                                                   AND   hkont = i_febko-hkont.
*    IF sy-subrc = 0.
*      e_febep-gsber = ls_ybasubst-gsber.
*    ELSE.
*      lo_feb_bsproc_bs_item = ycl_fi_bsproc_bs_item=>get_instance( ).
*      e_febep-gsber = lo_feb_bsproc_bs_item->get_gsber( iv_kukey = e_febep-kukey
*                                                        iv_esnum = e_febep-esnum ).
*    ENDIF.
*  ELSE.
  IF I_FEBKO-VGTYP = 'SOG_EUR4' AND I_FEBEP-AVKOA = 'D' AND I_FEBEP-AVKON = '0000500469'.
    E_FEBEP-GSBER = 'OPF'.
  ELSE.
    LV_GSBER = YCL_FI_ACCOUNT_SUBST_READ=>READ( IV_BUKRS = I_FEBKO-BUKRS
                                                IV_BLART = 'Z1'
                                                IV_HKONT = I_FEBKO-HKONT ).
    IF LV_GSBER IS NOT INITIAL.
      E_FEBEP-GSBER = LV_GSBER.
    ELSE.
      LO_FEB_BSPROC_BS_ITEM = YCL_FI_BSPROC_BS_ITEM=>GET_INSTANCE( ).
      E_FEBEP-GSBER = LO_FEB_BSPROC_BS_ITEM->GET_GSBER( IV_KUKEY = E_FEBEP-KUKEY
                                                        IV_ESNUM = E_FEBEP-ESNUM ).
    ENDIF.
  ENDIF.
*  ENDIF.


  CASE E_FEBEP-TEXTS.
* CPS ***************
* Transfer
*    when 'N195'
*    or 'N495'
*    or 'N275'
*    or 'N469'
*    or 'N575'.
*      if e_febep-chect ne c_chect.
*        e_febep-zuonr = e_febep-chect.
*      endif.
*
** check and deposit cash letter
*    when 'N475'.
*      if e_febep-chect ne c_chect.
**        write: e_febep-chect
**            to w_vblnr_c no-zero.
**        condense w_vblnr_c no-gaps.
**        concatenate 'CHQ'
**                    w_vblnr_c
**               into e_febep-zuonr.
*      write: e_febep-chect
*        to w_vblnr_c.
*        condense w_vblnr_c no-gaps.
**AAHOUNOU02062015
**                concatenate 'CHQ'
**                   w_vblnr_c
**               into e_febep-zuonr.
*       write w_vblnr_c to e_febep-zuonr.
**AAHOUNOU02062015
*      endif.
*
**   deb FB250602
**
**** nouveaux codes opération 'NCOL' 'NCLR'
**** ajoutés à 'N175'
**** when 'N175'
**
**   fin FB250602
*
*    when 'N175' or 'NCOL' or 'NCLR'.
*      if e_febep-chect ne c_chect.
*        e_febep-zuonr = e_febep-chect.
*      endif.

* AEM181201-
****    WHEN 'N475' OR 'N175'.
*****     re-building of tag 86 contain
****      LOOP AT t_febre.
****        CONCATENATE y_buffer t_febre-vwezw+0(27) INTO y_buffer.
****      ENDLOOP.
*****     search CMBREF=
****      SEARCH  y_buffer FOR c_string.
****
****      IF sy-subrc = 0.
****        y_fdpos = sy-fdpos + 7.
*****       fill-in  assignment number
*****       with the sequence following CMBREF=
****        WHILE y_buffer+y_fdpos(1) NE space.
****          CONCATENATE e_febep-zuonr
****                      y_buffer+y_fdpos(1)
****                 INTO e_febep-zuonr.
****          y_fdpos = y_fdpos + 1.
****        ENDWHILE.
****      ENDIF.
*****     For checks only
****      IF e_febep-texts = 'N475'.
****         CONCATENATE 'CHQ'
****                     e_febep-zuonr
****                INTO e_febep-zuonr.
****      ENDIF.
* AEM181201-

** SMARTLINK ********
*   Smartlink Transfer
************************************************************************
****NTRF * NTRF *NTRF*NTRF****NTRF * NTRF *NTRF*NTRF****NTRF * NTRF ****
************************************************************************
    WHEN 'NTRF'.
      CLEAR T_FEBRE.
      LOOP AT T_FEBRE.
        Y_BUFFER = T_FEBRE-VWEZW+2(5).
        EXIT.
      ENDLOOP.

*     DME number for mass payments
      IF I_FEBKO-BUKRS = 'UNES' AND
         I_FEBKO-HBKID = 'SOG01' AND
         I_FEBKO-HKTID = 'EUR01' AND
         Y_BUFFER EQ 'FR021'  AND
        ( E_FEBEP-CHECT(1) = '1' OR E_FEBEP-CHECT(1) = '0' ).
        LOOP AT T_FEBRE.
          IF ( T_FEBRE-VWEZW+0(5) = '<REF>'
            AND T_FEBRE-VWEZW+5(7) CO '0123456789' ).
*AHOUNOU06012014 / SEPA / 10 digits
            IF T_FEBRE-VWEZW+12(3) CO '0123456789'.
              CALL FUNCTION 'COMPUTE_CONTROL_NUMBER'
                EXPORTING
                  I_REFNO  = T_FEBRE-VWEZW+6(7)
                IMPORTING
                  E_RESULT = Y_DMENUM.

              CONCATENATE 'DME'
                          Y_DMENUM
                     INTO E_FEBEP-ZUONR.
*AHOUNOU06012014 / SEPA / 10 digits
            ELSE.
              CALL FUNCTION 'COMPUTE_CONTROL_NUMBER'
                EXPORTING
                  I_REFNO  = T_FEBRE-VWEZW+5(7)
                IMPORTING
                  E_RESULT = Y_DMENUM.

              CONCATENATE 'DME'
                          Y_DMENUM
                     INTO E_FEBEP-ZUONR.
            ENDIF.
          ENDIF.
        ENDLOOP.
**********************************************
      ENDIF.

*     re-building of tag 86 first line contains AFB code
*      clear t_febre.
*      loop at t_febre.
*        y_buffer = t_febre-vwezw+2(5).
*        exit.
*      endloop.
**     DME number for mass payments
*      If i_febko-bukrs = 'UNES' and
*         i_febko-hbkid = 'SOG01' and
*         i_febko-hktid = 'EUR01' and
*         y_buffer eq 'FR021'  and
*        ( e_febep-chect(1) = '1' or e_febep-chect(1) = '0' ).
*
*        if ( e_febep-chect(7) CO '0123456789' ).
*
*          call function 'COMPUTE_CONTROL_NUMBER'
*            EXPORTING
*              i_refno  = e_febep-chect
*            IMPORTING
*              e_result = y_dmenum.
*
*          concatenate 'DME'
*                      y_dmenum
*                 into e_febep-zuonr.
*        endif.
*      endif.

************************************************************************
*END NTRF * NTRF *NTRF*NTRF****NTRF * NTRF *NTRF*NTRF****NTRF * NTRF ***
************************************************************************
*AAHOUNOU14042010
* Fin Modification EMAR06032002

*   Smartlink Check
    WHEN 'NCHK'.
* Debut ajout EMAR150202
*     Check number is last word of secund line of t_febre
*      clear t_febre.
*      read table t_febre index 2.
*      CHECK SY-SUBRC EQ 0.
*
*      SPLIT t_febre AT ' ' INTO TABLE ITAB.
*      CLEAR ITAB.
*      LOOP AT ITAB.
*      ENDLOOP.
*      CHECK SY-SUBRC EQ 0.
** AEM181201+
*      WRITE: ITAB-WORD
*         TO w_vblnr_c NO-ZERO.
*      CONDENSE w_vblnr_c NO-GAPS.
*      CONCATENATE 'CHQ'
*                  w_vblnr_c
*             INTO e_febep-zuonr.
* fin supprress EMAR150202

* Ajout EMAR150202
      IF E_FEBEP-CHECT NE C_CHECT.
*        write: e_febep-chect
*            to w_vblnr_c no-zero.
*        condense w_vblnr_c no-gaps.

*        concatenate 'CHQ'
*                 w_vblnr_c
*            into e_febep-zuonr.
        WRITE: E_FEBEP-CHECT
            TO W_VBLNR_C.
        CONDENSE W_VBLNR_C NO-GAPS.
*AAHOUNOU02062015
*        concatenate 'CHQ'
*                 w_vblnr_c
*            into e_febep-zuonr.
        WRITE W_VBLNR_C TO E_FEBEP-ZUONR.
*AAHOUNOU02062015
*   deb FB250602
*
*** lorsque le n° de chèque contient 'NONREF', recherche du n°
*** en dernière position du tag 'FR001' :
*
      ELSEIF E_FEBEP-CHECT = 'NONREF'.

*** 1. récupération des textes dans la zone w_tampon à partir du fichier
***    entrée

        CLEAR: W_TAMPON.
        LOOP AT T_FEBRE.
          CONCATENATE W_TAMPON T_FEBRE-VWEZW+0(27) INTO W_TAMPON.
        ENDLOOP.
*** 2. récupération dans la table t_split des textes de w_tampon se
***    se trouvant entre les caractères de séparation '/'

        REFRESH T_SPLIT.
        SPLIT W_TAMPON AT '/' INTO TABLE T_SPLIT.
*** 3. recherche dans la table t_split du tag 'FR001'
****   lecture de la ligne suivante et détermination du n° de chèque
****   se trouvant à la fin

        READ TABLE T_SPLIT WITH KEY WORD = 'FR001'.
        W_INDEX = SY-TABIX.
        ADD 1 TO W_INDEX.
        READ TABLE T_SPLIT INDEX W_INDEX.
        CHECK SY-SUBRC EQ 0.
        REFRESH ITAB.
        SPLIT T_SPLIT-WORD AT ' ' INTO TABLE ITAB.
        DESCRIBE TABLE ITAB LINES W_NBRE.
        READ TABLE ITAB INDEX W_NBRE.

***   concaténation du n° de chèque trouvé avec 'CHQ'
***   dans la zone assignement

        CHECK SY-SUBRC EQ 0.
        WRITE: ITAB-WORD
               TO W_VBLNR_C NO-ZERO.
        CONDENSE W_VBLNR_C NO-GAPS.
*AAHOUNOU02062015
*        concatenate 'CHQ'
*                 w_vblnr_c
*            into e_febep-zuonr.
        WRITE W_VBLNR_C TO E_FEBEP-ZUONR.
*AAHOUNOU02062015
      ENDIF.
*  fin FB250602

* Fin ajout EMAR150202

* AEM181201+
* AEM181201-
*      CONCATENATE 'CHQ'
*                  ITAB-WORD
*             INTO e_febep-zuonr.
* AEM181201-
  ENDCASE.
ENDIF.