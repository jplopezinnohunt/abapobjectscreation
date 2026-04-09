* 6.4
* GLWEH4K002356 05022008 missing tax statement item 2 (1137858)
* 4.6C
* WKUL9CK029370 24112000 Saldo im Beleg: Rundungspfennig zweiter Ordnung
* WBGAHRK054105 04081999 business add-ins (user-exits);
* 4.6B
* WKUPH9K052668 14071999 Referenznummer XBLNR mit PERNR/REINR füllen
* 4.6A
* WKUPH9K002096 05051999 Steuerzeile auch für 0% wegen Tax-Bypass
* 4.5B LCP
* WKUL4DK001206 30041999 Steuerreform 1999 NAV mit CO-Objekten buchen

*---------------------------------------------------------------------*
*       INCLUDE LHRTSF05 .                                            *
*---------------------------------------------------------------------*

*---------------------------------------------------------------------*
*       FORM VAT_AMOUNT                                               *
*---------------------------------------------------------------------*
*  routine calculates the VAT-amount according to the VAT-indicator   *
* WKU New version for Prima Nota
*---------------------------------------------------------------------*
FORM vat_amount USING plusminus.
  DATA: store_posnr LIKE tax_item_out-posnr.
  DATA: bschl             LIKE bz-slbsl,
        post_key_cust_def.      "Posting key is new defined by customer

  IF net_amounts IS INITIAL OR
     bz-mwskz IS INITIAL.
    *ptrv_doc_tax-wrbtr = 0.
*    if plusminus = '-'.
*      wrbtr = wrbtr * -1.
*    endif.
    EXIT.
  ENDIF.

  CLEAR: vat_comparison,
         post_key_cust_def.

  IF plusminus = '+'.
    bschl = bz-slbsl.
* all line items for the debit side
    vat_comparison-w_slb = bz-slbsl.
    vat_comparison-w_hnb = space.
  ELSE.
    bschl = bz-hnbsl.
* all line items for the credit side
    vat_comparison-w_hnb = bz-hnbsl.
    vat_comparison-w_slb = space.
  ENDIF.

  vat_comparison-vat_delta = bz-vat_delta. "GLW note 2098779

  vat_comparison-tax_date = bz-txdat.  "GLW note 1819167
* only if amount is not initial
* CHECK NOT BZ-BETRG IS INITIAL.                         "WKUK002096
* only if account exists
*    check not bz-hnkto is initial.                      "WKUK010228

* is a special posting key for VAT gross amount defined ?
* QIZ posting keys will be set by posting modules LOAD_PAYABLE...
  IF vat_bschh IS INITIAL AND vat_bschs IS INITIAL.
*     select single * from t030b where ktosl = mwdat-ktosl.
    vat_bschh = bz-hnbsl.
    vat_bschs = bz-slbsl.
  ENDIF.

* Vorsteuer auf jeden Fall auf separates Konto
  MOVE-CORRESPONDING bz TO *ptrv_doc_tax.

  *ptrv_doc_tax-awref = bz-awref.
  *ptrv_doc_tax-aworg = bz-aworg.
  *ptrv_doc_tax-awlin = awlin.
  *ptrv_doc_tax-hkont = bz-hnkto.
  *ptrv_doc_tax-wrbtr = bz-betrg.     "Steuerbetrag
  *ptrv_doc_tax-curtp = '00'.         "Transaktionswährung

  IF plusminus = '+'.
    IF vat_bschs <> bz-slbsl.
      bschl = vat_bschs.
      vat_comparison-w_slb = vat_bschs.
      post_key_cust_def = 'X'.
    ENDIF.
  ELSE.
    IF vat_bschh <> bz-hnbsl.
      bschl = vat_bschh.
      vat_comparison-w_hnb = vat_bschh.
      post_key_cust_def = 'X'.
    ENDIF.
  ENDIF.

* User-Exit/ Business Add-In;
  PERFORM modify_ptrv_doc_tax CHANGING *ptrv_doc_tax.       "WBGK054105

  INSERT *ptrv_doc_tax.
  IF sy-subrc NE 0.
    WRITE: / 'Schlüssel'(001), *ptrv_doc_tax(36).
    WRITE: / 'bereits in PTRV_DOC_TAX:'(004),
             'Programm mußte abgebrochen werden.'(006).
    STOP.
  ENDIF.

*  if plusminus = '-'.
*    wrbtr = wrbtr * -1.
*  endif.

  MOVE-CORRESPONDING bz TO vat_comparison.

  IF post_key_cust_def = 'X'.
    vat_comparison-slbsl = vat_bschs.
    vat_comparison-hnbsl = vat_bschh.
  ENDIF.
  vat_comparison-wmwst = bz-betrg.     "Steuerbetrag
  vat_comparison-betrg = bz-brutto.    "Bruttobetrag
* determine net amount by re-reading G/L account line in BZ "WKUK029370
* that belongs to the current BZ tax line (its line number  "WKUK029370
* is stored in parameter AWLIN)                             "WKUK029370
  READ TABLE bz INTO wa_bz                                  "WKUK029370
                WITH KEY awref = vat_comparison-awref       "WKUK029370
                         awlin = awlin                      "WKUK029370
                         aworg = vat_comparison-aworg       "WKUK029370
                         tax_indicator = space.             "WKUK029370
  vat_comparison-wrbtr = wa_bz-betrg.  "Nettobetrag         "WKUK029370
  CLEAR wa_bz.                                              "WKUK029370
  vat_comparison-awref = *ptrv_doc_tax-awref.
  vat_comparison-aworg = *ptrv_doc_tax-aworg.
  vat_comparison-awlin = *ptrv_doc_tax-awlin.
  IF NOT vat_comparison-w_slb IS INITIAL.
    READ TABLE vat_comparison INTO wa_vat_comparison
                              WITH KEY w_slb = vat_bschs
*                                        ktosl = bz-ktosl"WKUK010228
                                       kschl = bz-kschl     "WKUK010228
                                       mwskz = bz-mwskz
                                       txjcd = bz-txjcd.
    IF sy-subrc = 0.
      wa_vat_comparison-awref = vat_comparison-awref.
      wa_vat_comparison-aworg = vat_comparison-aworg.
      wa_vat_comparison-awlin = vat_comparison-awlin.
      MODIFY vat_comparison FROM wa_vat_comparison INDEX sy-tabix.
    ENDIF.
  ELSEIF NOT vat_comparison-w_hnb IS INITIAL.
    READ TABLE vat_comparison INTO wa_vat_comparison
                              WITH KEY w_hnb = vat_bschh
*                                        ktosl = bz-ktosl"WKUK010228
                                       kschl = bz-kschl     "WKUK010228
                                       mwskz = bz-mwskz
                                       txjcd = bz-txjcd.
    IF sy-subrc = 0.
      wa_vat_comparison-awref = vat_comparison-awref.
      wa_vat_comparison-aworg = vat_comparison-aworg.
      wa_vat_comparison-awlin = vat_comparison-awlin.
      MODIFY vat_comparison FROM wa_vat_comparison INDEX sy-tabix.
    ENDIF.
  ENDIF.
  COLLECT vat_comparison.

ENDFORM.                               "VAT_AMOUNT



*----------------------------------------------------------------------*
*       Form  VAT_CORRECTION
*----------------------------------------------------------------------*
* routine corrects the tax amounts on the debit and credit side.       *
* WKU New version for Prima Nota
*----------------------------------------------------------------------*
FORM vat_correction USING s_wmwst h_wmwst.
  DATA: difference LIKE vat_comparison-wmwst.
  DATA: w_betrg    LIKE bz-betrg.

* Now the head-line of VAT_COMPARISON contains the amounts of debit-side
  difference = s_wmwst - h_wmwst.

* modify tax
  CLEAR ptrv_doc_tax.
* select single * from ptrv_doc_tax into *ptrv_doc_tax      "WKUK013477
  SELECT * FROM ptrv_doc_tax INTO *ptrv_doc_tax             "WKUK013477
                                    WHERE awref = vat_comparison-awref
                                      AND aworg = vat_comparison-aworg
                                      AND awlin = vat_comparison-awlin.
* "WKUK010228                      and ktosl = vat_comparison-ktosl
* new selection criterion for "WKUPH4K010228
* "WKUK013477                         and kschl = vat_comparison-kschl.
    IF *ptrv_doc_tax-kschl = vat_comparison-kschl.          "WKUK013477
      *ptrv_doc_tax-wrbtr = *ptrv_doc_tax-wrbtr - difference.
    ENDIF.                                                  "WKUK013477
    *ptrv_doc_tax-fwbas = *ptrv_doc_tax-fwbas + difference.

* User-Exit/ Business Add-In;
    PERFORM modify_ptrv_doc_tax CHANGING *ptrv_doc_tax.     "WBGK054105

    MODIFY *ptrv_doc_tax.
  ENDSELECT.                                                "WKUK013477
* only when tax line is not statistical                     "WKUK013477
  IF vat_comparison-kstat IS INITIAL.                       "WKUK013477
* modify net amount
    CLEAR ptrv_doc_it.
    SELECT SINGLE * FROM ptrv_doc_it INTO *ptrv_doc_it
                                     WHERE awref = vat_comparison-awref
                                       AND aworg = vat_comparison-aworg
                                       AND awlin = vat_comparison-awlin.
    *ptrv_doc_it-wrbtr = *ptrv_doc_it-wrbtr + difference.

* User-Exit/ Business Add-In;
    PERFORM modify_ptrv_doc_it CHANGING *ptrv_doc_it.       "WBGK054105

    MODIFY *ptrv_doc_it.
  ENDIF.                                                    "WKUK013477
ENDFORM.                               "VAT_CORRECTION
*&---------------------------------------------------------------------*
*&      Form  IT_AMOUNT
*&---------------------------------------------------------------------*
FORM it_amount
     USING VALUE(use_bz) TYPE xfeld.

* fill data line in prima nota
  MOVE-CORRESPONDING bz TO *ptrv_doc_it.

  awlin = bz-awlin.

  CASE bz-koart.
* in order to determine business transaction (GLVOR) we have to
* serch for KOART = 'K' or KOART = 'D'.
* GLVOR must be set in ptrv_doc_hd
    WHEN 'S'.
      IF *ptrv_doc_hd-glvor IS INITIAL.
* first G/L account posting
        *ptrv_doc_hd-glvor = 'RFT1'.
        *ptrv_doc_hd-int_glvor = 'TRV1'.            "interner GLVOR
        IF use_bz IS INITIAL.                               "GLWK002356
          *ptrv_doc_hd-bukrs = bz-bukrs.
        ELSE.
          *ptrv_doc_hd-bukrs = bz-bukst.
        ENDIF.                                              "GLWK002356
      ENDIF.
      IF bz-betrg GT 0.
        MOVE bz-konto TO *ptrv_doc_it-hkont.
      ELSE.
        MOVE bz-hnkto TO *ptrv_doc_it-hkont.
      ENDIF.
    WHEN 'K'.
      IF *ptrv_doc_hd-int_glvor IS INITIAL OR
         *ptrv_doc_hd-int_glvor EQ 'TRV1'.
* first A/P account posting
        *ptrv_doc_hd-glvor = 'RFT1'.
        *ptrv_doc_hd-int_glvor = 'TRV3'.            "interner GLVOR
        *ptrv_doc_hd-blart = blart_vendor. "GLW note 2725186
        *ptrv_doc_hd-bukrs = bz-bukrs.
      ENDIF.
      IF bz-betrg GT 0.
        MOVE bz-konto TO *ptrv_doc_it-lifnr.
      ELSE.
        MOVE bz-hnkto TO *ptrv_doc_it-lifnr.
      ENDIF.
    WHEN 'D'.
      IF *ptrv_doc_hd-int_glvor IS INITIAL OR
         *ptrv_doc_hd-int_glvor EQ 'TRV1'.
* first A/R account posting
        *ptrv_doc_hd-glvor = 'RFT1'.
        *ptrv_doc_hd-int_glvor = 'TRV2'.            "interner GLVOR
        *ptrv_doc_hd-bukrs = bz-bukrs.
      ENDIF.
      IF bz-betrg GT 0.
        MOVE bz-konto TO *ptrv_doc_it-kunnr.
      ELSE.
        MOVE bz-hnkto TO *ptrv_doc_it-kunnr.
      ENDIF.
  ENDCASE.

*  IF  cl_fitv_posting_util=>is_new_int_glvor(             "GLW note 2392616
*       i_bukrs1        =  bz-bukrs
*       i_bukrs2        =  bz-bukst
*       io_trip_post_fi = exit_trip_post_fi ) = 'X'.
*    *ptrv_doc_hd-int_glvor = 'TRV4'.
*  ENDIF.

  *ptrv_doc_it-curtp = '00'.          "Transaktionswährung
  *ptrv_doc_it-wrbtr = bz-betrg.
* CLEAR *PTRV_DOC_IT-FWBAS. "bis auf Weiteres leerlassen!!! "WKUK001206
  *ptrv_doc_it-fwbas = bz-fwbas.                            "WKUK001206

* User-Exit/ Business Add-In;
  PERFORM modify_ptrv_doc_it CHANGING *ptrv_doc_it.         "WBGK054105

  INSERT *ptrv_doc_it.
  IF sy-subrc NE 0.
    WRITE: / 'Schlüssel'(001), *ptrv_doc_it(33).
    WRITE: / 'bereits in PTRV_DOC_IT:'(003),
             'Programm mußte abgebrochen werden.'(006).
    STOP.
  ENDIF.
* fill CO replacement lines in Prima Nota
  CLEAR accountingobjects.
  READ TABLE accountingobjects
      INDEX bz-cobl_check_line.
  IF sy-subrc = 0.
    CLEAR: brlin,
           cobl_errors.
    LOOP AT cobl_errors
        WHERE row = bz-cobl_check_line.
      CLEAR *ptrv_doc_mess.
      brlin = brlin + 1.
      MOVE-CORRESPONDING cobl_errors TO *ptrv_doc_mess.
      *ptrv_doc_mess-awref       = bz-awref.
      *ptrv_doc_mess-aworg       = bz-aworg.
      *ptrv_doc_mess-awlin       = bz-awlin.
      *ptrv_doc_mess-brlin       = brlin.
      *ptrv_doc_mess-number_x    = cobl_errors-number.
      *ptrv_doc_mess-parameter_x = cobl_errors-parameter.
      *ptrv_doc_mess-row_x       = cobl_errors-row.
      INSERT *ptrv_doc_mess.
      IF sy-subrc NE 0.
        WRITE: / 'Schlüssel'(001), *ptrv_doc_mess(36).
        WRITE: / 'bereits in PTRV_DOC_MESS:'(005),
                 'Programm mußte abgebrochen werden.'(006).
        STOP.
      ENDIF.
    ENDLOOP.
    CLEAR *ptrv_doc_mess.
    brlin = brlin + 1.
    CASE accountingobjects-result.
      WHEN '1'.
* substitution of accounting object by employee cost center possible
        *ptrv_doc_mess-awref       = bz-awref.
        *ptrv_doc_mess-aworg       = bz-aworg.
        *ptrv_doc_mess-awlin       = bz-awlin.
        *ptrv_doc_mess-brlin       = brlin.
        CLEAR wa_bapiret2.
        par1 = accountingobjects-costcenter_empl.
        row  = bz-cobl_check_line.
        CALL FUNCTION 'BALW_BAPIRETURN_GET2'
          EXPORTING
            type   = 'R'
            cl     = '56'
            number = '851'
            par1   = par1
            row    = row
          IMPORTING
            return = wa_bapiret2.
        MOVE-CORRESPONDING wa_bapiret2 TO *ptrv_doc_mess.
        *ptrv_doc_mess-number_x    = wa_bapiret2-number.
        *ptrv_doc_mess-parameter_x = wa_bapiret2-parameter.
        *ptrv_doc_mess-row_x       = wa_bapiret2-row.
        INSERT *ptrv_doc_mess.
        IF sy-subrc NE 0.
          WRITE: / 'Schlüssel'(001), *ptrv_doc_mess(36).
          WRITE: / 'bereits in PTRV_DOC_MESS:'(005),
                   'Programm mußte abgebrochen werden.'(006).
          STOP.
        ENDIF.
      WHEN '2'.
* substitution of accounting object by reserve cost center possible
        *ptrv_doc_mess-awref       = bz-awref.
        *ptrv_doc_mess-aworg       = bz-aworg.
        *ptrv_doc_mess-awlin       = bz-awlin.
        *ptrv_doc_mess-brlin       = brlin.
        CLEAR wa_bapiret2.
        par1 = accountingobjects-costcenter_default.
        row  = bz-cobl_check_line.
        CALL FUNCTION 'BALW_BAPIRETURN_GET2'
          EXPORTING
            type   = 'R'
            cl     = '56'
            number = '852'
            par1   = par1
            row    = row
          IMPORTING
            return = wa_bapiret2.
        MOVE-CORRESPONDING wa_bapiret2 TO *ptrv_doc_mess.
        *ptrv_doc_mess-number_x    = wa_bapiret2-number.
        *ptrv_doc_mess-parameter_x = wa_bapiret2-parameter.
        *ptrv_doc_mess-row_x       = wa_bapiret2-row.
        INSERT *ptrv_doc_mess.
        IF sy-subrc NE 0.
          WRITE: / 'Schlüssel'(001), *ptrv_doc_mess(36).
          WRITE: / 'bereits in PTRV_DOC_MESS:'(005),
                   'Programm mußte abgebrochen werden.'(006).
          STOP.
        ENDIF.
      WHEN OTHERS.
* no action necessary.
    ENDCASE.

  ENDIF.

  IF ( bl_spl = 'R' OR bl_spl = 'Q' ).                      "WKUK052668 "GLW note 1883880: also when doc per doc.
    *ptrv_doc_hd-xblnr = bz-exbel.                          "WKUK052668
  ELSEIF bl_spl = 'P'.                                      "WKUK052668
    *ptrv_doc_hd-xblnr = bz-pernr.                          "WKUK052668
  ENDIF.                                                    "WKUK052668

* User-Exit/ Business Add-In;
  PERFORM modify_ptrv_doc_hd CHANGING *ptrv_doc_hd.         "WBGK054105

  MODIFY *ptrv_doc_hd.

ENDFORM.                               " IT_AMOUNT
FORM awref_commit USING VALUE(awref) VALUE(aworg) VALUE(commi) VALUE(log_sys).
* new with GLW note "GLW note 2252313
  UPDATE ptrv_doc_hd SET
          commi = commi
          receiver = log_sys
          WHERE awref = awref AND
                aworg = aworg.

  CALL FUNCTION 'DB_COMMIT'.

ENDFORM.
FORM run_status USING VALUE(runid).

  DATA t_pevsh TYPE TABLE OF pevsh.
  FIELD-SYMBOLS <pevsh> TYPE pevsh.

* if the status was previously set to '35' because it was not 35 before, but the commit faild,
* delete the new status entry and re-activate the previous one as current one.

  CALL FUNCTION 'HR_EVAL_RUN_HISTORY_GET'
    EXPORTING
      type              = 'TR'
      runid             = runid
    TABLES
      ipevsh            = t_pevsh
    EXCEPTIONS
      no_data_available = 1
      OTHERS            = 2.

  SORT t_pevsh BY seqno ASCENDING.

  READ TABLE t_pevsh INDEX lines( t_pevsh ) ASSIGNING <pevsh>.

  DELETE pevsh FROM <pevsh>.
  DELETE t_pevsh INDEX lines( t_pevsh ).
  READ TABLE t_pevsh INDEX lines( t_pevsh ) ASSIGNING <pevsh>.
  <pevsh>-actual = 'X'.
  UPDATE pevsh FROM <pevsh>.

ENDFORM.