* 6.6
* VRD_CEE_RU             CEE_RU country version retrofit RU
* 6.4
* GLWEH5K014605 09092009 tax statement item(1383567)
* GLWEH5K009842 18052009 tax statement item missing(1342016)
* GLWP2HK019471 30062008 tax statement item missing(1225463)
* GLWEH4K002356 05022008 missing tax statement item 2 (1137858)
* 6.0
* GLWEH4K001640 11012008 missing tax statement item(1131266)
* WKUPENK015647 19052005 correction for WKUK015412 (846579)
* WKUAENK017307 26112004 Problems with BUV and PD per Receipt (795309)
* WKUAENK015412 22112004 Determine and transfer profit center (791956)
* 5.0
* XCIALNK152901 14012004 posting with not postable costcenter (695043)
* 1.10
* WKUP1HK001347 27082002 Vendor not unique due to T706K/T030 (549523)
* WKUP1HK000971 26072002 tax for posting doc per CO object wrong(540870)
* WKUP1HK000968 24072002 Fehler wegen Hinweis 418144 behoben (H:539863)
*                        zwar kein Fehler in 1.10, aber Beleg inkorrekt
*                        determine LEADING_BUKRS only if posting happens
* WKUP1HK000524 24062002 filterobject determination for all BUKRS
* WKUP1HK000523 24062002 BUV-Split only if BUKRS in separate FI systems
* QIZALNK002508 11012002 FKBER, GRANT aund FIPEX implemented
* WKUALNK003898 18092001 Nachkorrektur WKUK006565
* 4.6C
* WKUL9CK029369 09112000 Saldo im Beleg: SAKO-Zeile zuviel erzeugt
* WKUL9CK002818 14072000 Nachkorrektur zu WKUK000635 für Beleg pro CO-Ob
*                        keine Vertauschung von BUKRS und BUKST mehr
* WBGL9CK008343 10052000 Missing SGTXT when CO-Objects substituted;
* WKUL9CK005642 28042000 übergreifende Nummer bei BUV füllen
* WKUPH0K008017 28012000 Zuordnung teilweise NAV/NVV zu SAKO korrigiert
* WKUPH0K006565 24012000 Neue BAPI-Felder (ISO-Währung und Steuer-BUKRS)
* WKUAHRK065591 02121999 Do not set master cc for 2.symb.account in BUV
*                        - remove BUV lines with zero amount
* WKUAHRK063502 19111999 One posting document if BUV into one system
*                        - Make BUV-split only when multiple FI-systems
* WKUAHRK063501 17111999 Improvement of tax posting for RW-interface:
*                        - Achim's lines for NAV in case of BUV
* YWWAHRK058351 16111999 Fehler bei Zugriff auf Debitoren-Suchhilfe
* WKUAHRK059035 15111999 Wegsaldierte SAKO-Zeilen aus Steuerzeilen
*                        mit Pfennigbeträgen rekonstruieren
* 4.5B LCP
* WKUL4DK001206 30041999 Steuerreform 1999 NAV mit CO-Objekten buchen
* 4.5B
* WKUPH4K029301 04021999  Buchungskreisübergreifende Buchung mit VBUND

*---------------------------------------------------------------------*
*       INCLUDE LHRTSF03 .                                            *
*---------------------------------------------------------------------*

*---------------------------------------------------------------------*
*       FORM FILL_VENDOR_CUSTOMER_CHECK_TABLES                        *
*---------------------------------------------------------------------*
FORM fill_vend_cust_check_tables
    USING VALUE(elementary_shlp).

* look if entry for vendor/customer already in table
  READ TABLE fi_acct_det_hr
      WITH KEY bukrs      = ep_translate-bukrs
               ktosl      = ep_translate-ktosl
*              symb_acct  =                             "not yet needed
               momagkomok = momagkomok
*              add_modif  =                             "not yet needed
               pernr      = ep_translate-pernr.
  IF sy-subrc = 0.
    tabix = sy-tabix.
  ELSE.
    fi_acct_det_hr-pernr = ep_translate-pernr.
    fi_acct_det_hr_append_flag = 'X'.
    CASE fi_acct_det_hr-koart.
      WHEN 'K'.
* entry is a vendor => fill vendor selection table
        CLEAR: vendor_selopt_tab.

        vendor_selopt_tab-comp_code  = fi_acct_det_hr-bukrs.

* dynamisches Auswerten der Suchhilfe
        PERFORM evaluate_search_help
                    USING 'KRED'
                          elementary_shlp
                          vendor_selopt_tab-tabname
                          vendor_selopt_tab-fieldname.

        vendor_selopt_tab-fieldvalue = ep_translate-pernr.
*       append vendor_selopt_tab.                           "WKUK001347
        COLLECT vendor_selopt_tab.                          "WKUK001347
        fi_acct_det_hr-vend_cust_line = sy-tabix.
      WHEN 'D'.
* entry is a customer => fill customer selection table
        CLEAR: customer_selopt_tab.

        customer_selopt_tab-comp_code  = fi_acct_det_hr-bukrs.
        customer_selopt_tab-tabname    = 'KNB1'.

* dynamisches Auswerten der Suchhilfe
        PERFORM evaluate_search_help
                    USING 'DEBI'
                          elementary_shlp
*                         VENDOR_SELOPT_TAB-TABNAME    "YWWK058351
                          customer_selopt_tab-tabname       "YWWK058351
                          customer_selopt_tab-fieldname.

        customer_selopt_tab-fieldvalue = ep_translate-pernr.
*       append customer_selopt_tab.                         "WKUK001347
        COLLECT customer_selopt_tab.                        "WKUK001347
        fi_acct_det_hr-vend_cust_line = sy-tabix.
    ENDCASE.
  ENDIF.

ENDFORM.                        "FORM FILL_VENDOR_CUSTOMER_CHECK_TABLES



*---------------------------------------------------------------------*
*       FORM EMPTY_BZ                                                 *
*---------------------------------------------------------------------*
*       stellt Inhalt der Tabelle BZ in  Buchungsbeleg(e)             *
*---------------------------------------------------------------------*
FORM empty_bz.

  DATA: aworg                      LIKE bz-aworg,
        brlin                      TYPE i,
        no_new_posting_document(1),
        leading_bukrs              LIKE bz-bukst,           "WKUK006565
        budat_help                 LIKE budat,
        bldat_help                 LIKE bldat.

  FIELD-SYMBOLS: <bz> LIKE bz.

  DATA: BEGIN OF buv_leading_bukrs OCCURS 1,
          awref LIKE ptrv_doc_hd-awref,
          uebnr LIKE ptrv_doc_hd-uebnr,
          bukrs LIKE ptrv_doc_hd-bukrs,
        END OF buv_leading_bukrs.

  DATA: wa_buv_leading_bukrs LIKE buv_leading_bukrs.        "GLWK001640
  DATA: wa_buv_help LIKE buv_help.                          "GLWK001640
  DATA: leading_bukrs_determined TYPE xfeld.                "GLWK001640
  DATA: counter TYPE i.                                     "GLWK001640
  DATA: use_bz TYPE xfeld.                                  "GLWK002356

  DATA: BEGIN OF bz_help OCCURS 1,                          "GLWK002356
          awref         LIKE bz-awref,
          bukrs         LIKE bz-bukrs,
          bukst         LIKE bz-bukst,
          ktosl         LIKE bz-ktosl,
          tax_indicator LIKE bz-tax_indicator,                  "GLWEH5K014605
*          mwksz         LIKE bz-mwskz,                                  "GLW note 1658377
          mwskz         LIKE bz-mwskz,    "GLW note 2133000
        END OF bz_help.

  DATA: help_bukrs LIKE bz-bukrs,
        help_bukst LIKE bz-bukst,
        help_ktosl LIKE bz-ktosl.

  TYPES: BEGIN OF t_awref,                                "note GLW 1514353
           awref LIKE bz-awref,
         END OF t_awref.

  STATICS: saved_awref TYPE SORTED TABLE OF t_awref WITH UNIQUE KEY awref. "note GLW 1514353
  DATA: wa_awref TYPE t_awref.                "note GLW 1514353
  DATA: no_tax TYPE xfeld.                    "GLW note 1658377

  DESCRIBE TABLE bz LINES bz_anzhl.
  CHECK bz_anzhl > 0.

  LOOP AT buv_help INTO wa_buv_help.                        "GLWK001640
    MOVE-CORRESPONDING wa_buv_help TO wa_buv_leading_bukrs.
    APPEND wa_buv_leading_bukrs TO buv_leading_bukrs.
  ENDLOOP.

  IF bz_anzhl EQ 1.
* Die Buchung besteht nur aus einer Zeile:
* 1. Betrag = Saldo <> 0 =>  Belegsplit
* 2. Betrag = Saldo =  0 =>  Keine Buchung notwendig.
    IF bz_saldo = 0.
      CLEAR  : bz.
      REFRESH: bz.
      CLEAR  : bz_anzhl, last_koart.
      CLEAR  : vat_comparison.
      REFRESH: vat_comparison.
      EXIT.
    ENDIF.
  ENDIF.
  NEW-PAGE.

  bz_saldo = 0.

  net_amounts = 'X'.

* move 'Reiseübertragungsbelege werden abgespeichert' to progress_text.
* call function 'SAPGUI_PROGRESS_INDICATOR'
*     exporting
*       text       = progress_text.

  SORT bz BY awref ASCENDING
             ep_line DESCENDING
             tax_line ASCENDING
             tax_indicator DESCENDING.                      "WKUK008017

  LOOP AT bz.                                               "GLWK002356
    MOVE-CORRESPONDING bz TO bz_help.
    APPEND bz_help.
  ENDLOOP.

*  PERFORM check_awlin.

  LOOP AT bz.

    CLEAR: *ptrv_doc_it,
           *ptrv_doc_tax,
           *ptrv_doc_mess,
           no_new_posting_document.

    CLEAR: use_bz.                                          "GLWK002356

    MOVE: bz-bukst TO help_bukst,
          bz-bukrs TO help_bukrs,
          bz-ktosl TO help_ktosl.

* handle setting of posting date and posting document date
    IF budat = '11111111'.
      budat_help = bz-datv1.
    ELSEIF budat = '99999999'.
      budat_help = bz-datb1.
    ELSEIF budat = '22222222'.                         "Beleg pro Beleg
      budat_help = bz-beldt.                           "Beleg pro Beleg
    ELSEIF budat = '33333333'.                         "VRD_CEE_RU
      budat_help = bz-umdat.           "Reference date "VRD_CEE_RU
    ELSE.
      budat_help = budat.
    ENDIF.
    IF bldat = '11111111'.
      bldat_help = bz-datv1.
    ELSEIF bldat = '99999999'.
      bldat_help = bz-datb1.
    ELSEIF bldat = '22222222'.                         "Beleg pro Beleg
      bldat_help = bz-beldt.                           "Beleg pro Beleg
    ELSEIF bldat = '33333333'.                         "VRD_CEE_RU
      bldat_help = bz-umdat.           "Reference date "VRD_CEE_RU
    ELSE.
      bldat_help = bldat.
    ENDIF.

    IF bz-advance = 'V'.        "GLW note 2520560
      CASE adv_proc.   "GLW note 2713017
        WHEN space.
          bldat_help = budat_help = bz-beldt.
        WHEN '1'.
          bldat_help = bz-beldt.
        WHEN '2'.
          budat_help = bz-beldt.
      ENDCASE.
    ENDIF.

*    IF bz-kokey(1) = 'X'.                      "note GLW 1514353
*      no_new_posting_document = bz-kokey(1).
    CLEAR bz-kokey(1).
*    ENDIF.

* handle creation of new posting document
    aworg = bz-aworg.
    AT NEW awref.

* GLWK002356 begin
*if a the AWREF is not in buv_help and the determining master line has
*different BUKRS and BUKST, the PTRV_DOC_HD-BUKRS will be wrong; so in this
*case we set it to BUKST, which is correct.
      DO.
        READ TABLE buv_help WITH KEY
          awref = bz-awref.
        IF  sy-subrc IS INITIAL.
          LOOP AT bz_help WHERE    "GLW note 2015149
             awref = bz-awref AND
             bukrs NE help_bukrs.
            EXIT.
          ENDLOOP.
          IF sy-subrc IS NOT INITIAL.  "GLW note 2015149
            EXIT.
          ENDIF.
        ENDIF.
        IF ( help_ktosl EQ 'HRT' ) AND ( help_bukrs NE help_bukst ).
          LOOP AT bz_help WHERE
            awref = bz-awref AND
            bukrs EQ help_bukst. " AND
*            ktosl EQ 'VST'.
*            tax_indicator EQ 'X'.           "GLWEH5K014605

*            READ TABLE bz_help WITH KEY     "GLW note 2133000
*              awref = bz-awref
*              bukrs = help_bukst
*              tax_indicator = space TRANSPORTING NO FIELDS.
*
*            IF sy-subrc IS INITIAL.  "GLW note 2133000 there is no GL posting line in tax comp code
*            IF sy-subrc IS NOT INITIAL. "GLW note 2184659
              use_bz = 'X'.  "Whenever there are posting lines in master , use this
*            ENDIF.
            EXIT.
          ENDLOOP.
* GLW note 1658377 begin
          IF use_bz IS INITIAL.
            LOOP AT bz_help WHERE
*              mwksz IS NOT INITIAL.
              mwskz IS NOT INITIAL.  "GLW note 2133000
              EXIT.
            ENDLOOP.
            IF sy-subrc IS NOT INITIAL.
              no_tax = 'X'.
            ENDIF.
          ENDIF.
* GLW note 1658377 end
        ENDIF.
        EXIT.
      ENDDO.
* GLWK002356 end

* for each new posting document number fill header table for PRIMA NOTA
      CLEAR *ptrv_doc_hd.
      CHECK NOT bz-awref IS INITIAL.
      READ TABLE saved_awref WITH KEY            "note GLW 1514353
        awref = bz-awref BINARY SEARCH TRANSPORTING NO FIELDS .
      IF sy-subrc IS NOT INITIAL.                 "note GLW 1514353
* no_new_posting_document based on bz-kokey(1) is not reliable because depending on the sorting of bz table. So don't create
* new ptrv_doc_hd entry only in case, a doc with this awref was really created up till now: note GLW 1514353
*      IF no_new_posting_document NE 'X'.  "nur wenn kein Belegsplit
        *ptrv_doc_hd-awref = bz-awref.
        *ptrv_doc_hd-aworg = aworg.
        *ptrv_doc_hd-budat = budat_help.
        *ptrv_doc_hd-bldat = bldat_help.
        IF NOT soper IS INITIAL.
          MOVE soper TO *ptrv_doc_hd-monat.
        ENDIF.
        MOVE blart TO *ptrv_doc_hd-blart.
        MOVE runid TO *ptrv_doc_hd-runid.
        READ TABLE buv_help                                 "WKUK005642
            WITH KEY awref = bz-awref.                      "WKUK005642
        IF sy-subrc = 0.                                    "WKUK005642
          *ptrv_doc_hd-uebnr = buv_help-uebnr.              "WKUK005642
        ENDIF.                                              "WKUK005642
        INSERT *ptrv_doc_hd.
        IF sy-subrc NE 0.
          WRITE: / 'Schlüssel'(001), *ptrv_doc_hd(23).
          WRITE: / 'bereits in PTRV_DOC_HD:'(002),
                   'Programm mußte abgebrochen werden.'(006).
          STOP.
        ENDIF.
        MOVE bz-awref TO wa_awref.                "note GLW 1514353
        INSERT wa_awref INTO  TABLE saved_awref.  "note GLW 1514353
      ENDIF.
    ENDAT.

* BEGIN OF WKUK0006565
* Determine leading company code for tax calculation check...
* Cannot remember reason for old line...                     WKUK003898
*   if leading_bukrs is initial or leading_bukrs eq bz-bukrs.WKUK003898
* ...but normally the LEADING_BUKRS should change if BUKST   WKUK003898
* changes and is not initial                                 WKUK003898
    IF ( leading_bukrs IS INITIAL OR                        "WKUK003898
         leading_bukrs NE bz-bukst ) AND                    "WKUK003898
*        not bz-bukst is initial.               "WKUK068426 "WKUK000968
* ...but determine LEADING_BUKRS only when BUKST appears    "WKUK000968
* as BUKRS in BZ in a real posting line (no tax line)       "WKUK000968
       ( NOT bz-bukst IS INITIAL AND bz-bukrs = bz-bukst AND "WKUK000968
         bz-tax_indicator IS INITIAL ).                     "WKUK000968
      leading_bukrs = bz-bukst.
      leading_bukrs_determined = 'X'.                       "GLW
    ENDIF.
* ...and modify current header line with that leading company code
    AT END OF awref.
      IF leading_bukrs_determined IS INITIAL AND leading_bukrs IS INITIAL.
* This can happen for certain kinds of delta postings, where no offsetting account
* is used. Leads to FF805.
        IF no_tax IS INITIAL.          "GLW note 1658377
          leading_bukrs = help_bukst.  "GLWEH5K009842
        ELSE.                          "GLW note 1658377
          leading_bukrs = *ptrv_doc_hd-bukrs. "GLW note 1658377
        ENDIF.                                "GLW note 1658377
      ENDIF.
      *ptrv_doc_hd-leading_bukrs = leading_bukrs.
      MODIFY *ptrv_doc_hd.
* begin of GLWEH4K001640
* sometimes the AWREFs with same UEBNR are interupted be AWREF witout or with other
* UEBNR. Therefore a wrong leading bukrs can occur. So in case for the same UEBNR already a
* leading bukrs is determined, we take this one, because AWREFs with same UEBNR must
* have same leading bukrs anyway
      READ TABLE buv_leading_bukrs WITH KEY
      awref = bz-awref.
      counter = sy-tabix.
      IF sy-subrc IS INITIAL.
        IF leading_bukrs_determined = 'X'.
          buv_leading_bukrs-bukrs = leading_bukrs.
          MODIFY buv_leading_bukrs INDEX counter .
        ENDIF.
        IF leading_bukrs_determined IS INITIAL.
          LOOP AT buv_leading_bukrs WHERE
            uebnr = *ptrv_doc_hd-uebnr.
            IF buv_leading_bukrs-bukrs IS INITIAL.
              CONTINUE.
            ELSE.
              EXIT.
            ENDIF.
          ENDLOOP.
          IF NOT buv_leading_bukrs-bukrs IS INITIAL.
            *ptrv_doc_hd-leading_bukrs = buv_leading_bukrs-bukrs.
            MODIFY *ptrv_doc_hd.
          ENDIF.
          DO 1 TIMES.
            LOOP AT bz ASSIGNING <bz> WHERE
               awref = bz-awref AND
               mwskz NE space AND
               tax_indicator EQ space.
              EXIT.    "tax relevant posting line
            ENDLOOP.
            IF sy-subrc IS NOT INITIAL.
              EXIT.
            ENDIF.
            LOOP AT bz ASSIGNING <bz> WHERE
               awref EQ bz-awref AND
               tax_indicator EQ 'X'.
              EXIT.  " tax line is existing.
            ENDLOOP.
            IF sy-subrc IS INITIAL.
              EXIT.
            ENDIF.
            LOOP AT bz ASSIGNING <bz> WHERE
               awref EQ bz-awref AND
               bukst NE *ptrv_doc_hd-leading_bukrs AND
               ktosl NE 'BUV'.
              EXIT.
            ENDLOOP.
            IF sy-subrc IS NOT INITIAL.
              EXIT.
            ENDIF.
            IF *ptrv_doc_hd-leading_bukrs NE <bz>-bukst.
              MOVE <bz>-bukst TO *ptrv_doc_hd-leading_bukrs.
              MODIFY *ptrv_doc_hd.
            ENDIF.
          ENDDO.
        ENDIF.
      ENDIF.
      CLEAR leading_bukrs_determined.
* end of GLWEH4K001640
    ENDAT.
* END OF WKUK0006565

* handle default SGTXT filling via reading of table T053
    IF bz-sgtxt IS INITIAL.
* when no text in posting document line, read table T053 for a text
      CALL FUNCTION 'HRCA_READ_LINE_ITEM_TEXT'
        EXPORTING
          text_key     = 'REIS'
          doc_date     = bldat_help
          pstng_date   = budat_help
*         bline_date   =
*         fis_period   =
*         fisc_year    =
*         ref_doc_no   =
          comp_code    = bz-bukrs
          langu        = sy-langu
        IMPORTING
          item_text    = bz-sgtxt
*         return       =
        TABLES
          return_table = return_table.

      READ TABLE return_table INDEX 1.
      IF sy-subrc = 0.
        MESSAGE ID     return_table-id
                TYPE   return_table-type
                NUMBER return_table-number
                WITH   return_table-message_v1
                       return_table-message_v2
                       return_table-message_v3
                       return_table-message_v4
                RAISING ale_communication_error.
      ENDIF.

    ENDIF.

* for sorting reasons, in some cases pernr and exbel were not cleared
* but set to the maximum possible value.
    IF bz-pernr = max_pernr.
      CLEAR bz-pernr.
    ENDIF.
    IF bz-exbel = max_exbel.
      CLEAR bz-exbel.
    ENDIF.
    IF bz-exbel = max_exbel.                           "Beleg pro Beleg
      CLEAR bz-exbel.                                  "Beleg pro Beleg
    ENDIF.                                             "Beleg pro Beleg

*   IF BZ-FWBAS IS INITIAL.                         "WKUK001206
    IF bz-tax_indicator IS INITIAL.                         "WKUK001206
* BZ-line is not a tax line => fill item line in prima nota
      PERFORM it_amount
           USING use_bz.                                    "GLWK002356
    ELSE.
* BZ-line is a tax line => depending on sign of amount...
      IF bz-betrg >= 0.
* ...fill tax lines in PRIMA NOTA and VAT correction table positive or
        PERFORM vat_amount USING '+'.
      ELSE.
* ...fill tax lines in PRIMA NOTA and VAT correction table negative
        PERFORM vat_amount USING '-'.
      ENDIF.
    ENDIF.

* database update for every posting document               "Performance
    AT END OF awref.                   "Performance

      IF  cl_fitv_posting_util=>is_new_int_glvor(             "GLW note 2392616
      i_bukrs1        =  *ptrv_doc_hd-bukrs
      i_bukrs2        =  *ptrv_doc_hd-leading_bukrs
      io_trip_post_fi = exit_trip_post_fi ) = 'X'.
        *ptrv_doc_hd-int_glvor = 'TRV4'.
        MODIFY *ptrv_doc_hd.
      ENDIF.

      COMMIT WORK.                     "Performance
    ENDAT.                             "Performance

  ENDLOOP.

* correction of rounding differences caused by tax calculations
  PERFORM vat_comparison.

  CLEAR  : bz,
           vat_comparison,
           bz_anzhl,
           last_koart.
  REFRESH: bz,
           vat_comparison.

  CLEAR: counter, wa_buv_leading_bukrs, buv_leading_bukrs, leading_bukrs_determined.
  REFRESH: buv_leading_bukrs.

ENDFORM.                               "EMPTY_BZ



*&---------------------------------------------------------------------*
*&      Form  NUMBER_GET_NEXT
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
FORM number_get_next.

  DATA message_number LIKE sy-msgno.

  CALL FUNCTION 'NUMBER_GET_NEXT'
    EXPORTING
      nr_range_nr             = '01'
      object                  = 'HRTR_PDOC'
*     QUANTITY                = '1'
*     SUBOBJECT               = ' '
*     TOYEAR                  = '0000'
*     IGNORE_BUFFER           = ' '
    IMPORTING
*     NUMBER                  = I_AWREF   " WBG Hotline 175746
      number                  = n_awref   " WBG Hotline 175746
*     QUANTITY                =
*     RETURNCODE              =
    EXCEPTIONS
      interval_not_found      = 1
      number_range_not_intern = 2
      object_not_found        = 3
      quantity_is_0           = 4
      quantity_is_not_1       = 5
      interval_overflow       = 6
*     others                  = 7.                          "WKUK001347
      buffer_overflow         = 7                           "WKUK001347
      OTHERS                  = 8.                          "WKUK001347

  IF sy-subrc NE 0.
    CASE sy-subrc.
      WHEN 1.
        message_number = 780.
      WHEN 2.
        message_number = 781.
      WHEN 3.
        message_number = 782.
      WHEN 4.
        message_number = 783.
      WHEN 5.
        message_number = 784.
      WHEN 6.
        message_number = 785.
      WHEN 7.
        message_number = 786.
      WHEN 8.                                               "WKUK001347
        message_number = 787.                               "WKUK001347
    ENDCASE.

    MESSAGE ID     '56'
            TYPE   'E'
            NUMBER message_number
            WITH   'HRTR_PDOC'
            RAISING number_range_error.
  ELSE.                                "Performance
* database update for every new number to free the NREF    "Performance
    COMMIT WORK.                       "Performance
  ENDIF.

ENDFORM.                               " NUMBER_GET_NEXT



*&---------------------------------------------------------------------*
*&      Form  CONDENSE_TAX_LINES
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      --> SLBSL  Buchungsschlüssel
*      --> KONTO  Kontonummer
*----------------------------------------------------------------------*
FORM condense_tax_lines
    USING slbsl
          konto
          vbund.                                            "WKUK029301

  DATA: epk_field(29),
        wa_epk        LIKE epk,
        BEGIN OF help_epk OCCURS 0.
          INCLUDE STRUCTURE epk.
  DATA:   line_to_insert TYPE i,
          END OF help_epk,
          help_epk_lines        TYPE i,
          line_to_insert        TYPE i,
          lines_inserted_so_far TYPE i.

  CLEAR: help_epk,
         wa_epk.
  REFRESH help_epk.

* all epk tax lines connected to the summed line have to be selected...
  LOOP AT remember_summed_lines.
    LOOP AT epk INTO wa_epk
        WHERE ep_line = remember_summed_lines-ep_line
*     AND NOT FWBAS IS INITIAL.                             "WKUK001206
      AND NOT tax_indicator IS INITIAL.                     "WKUK001206
      tabix = sy-tabix.
* look if just a line with the same KSCHL in the help table
      READ TABLE help_epk
*         with key ktosl = wa_epk-ktosl.                    "WKUK010228
          WITH KEY kschl = wa_epk-kschl.                    "WKUK010228
      IF sy-subrc = 0.
* if so, condense tax and net amount into help table
        help_epk-betrg   = help_epk-betrg + wa_epk-betrg.
        help_epk-fwbas   = help_epk-fwbas + wa_epk-fwbas.
        help_epk-ep_line = wa_epk-ep_line.
        help_epk-line_to_insert = tabix.
        MODIFY help_epk INDEX sy-tabix.
      ELSE.
* if not, create a new line in the help table
        MOVE-CORRESPONDING wa_epk TO help_epk.
        help_epk-slbsl = slbsl.
        help_epk-konto = konto.
        help_epk-vbund = vbund.                             "WKUK029301
* clear all CO objects of the new lines
* but only when posting document not per CO-object          "WKUK002818
        IF bl_spl NE 'C'.                                   "WKUK002818
          LOOP AT psref_fields.
            epk_field(9) = 'HELP_EPK-'.
            epk_field+9(20) = psref_fields-field.
            ASSIGN (epk_field) TO <f>.
            CLEAR <f>.
          ENDLOOP.
        ENDIF.                                              "WKUK002818
* refill master company code and text
        help_epk-bukrs = wa_epk-bukst.
        help_epk-sgtxt = wa_epk-sgtxt.
        CLEAR help_epk-kokey.
        help_epk-line_to_insert = tabix.
        APPEND help_epk.
      ENDIF.
      DELETE epk.
    ENDLOOP.
  ENDLOOP.
  DESCRIBE TABLE help_epk LINES help_epk_lines.
  IF NOT help_epk_lines IS INITIAL.
    lines_inserted_so_far = 0.
    LOOP AT help_epk.
* look if condensed tax line is already in table EPK
      IF bl_spl NE 'C'.                                     "WKUK000971
* when posting document not per CO-object, read epk         "WKUK000971
* without CO information...                                 "WKUK000971
        READ TABLE epk INTO wa_epk
            WITH KEY pernr = help_epk-pernr
                pernr_konto_sort = help_epk-pernr_konto_sort "WKUK015647
*               ktosl = help_epk-ktosl                      "WKUK010228
                kschl = help_epk-kschl                      "WKUK010228
                slbsl = help_epk-slbsl
                konto = help_epk-konto
                bukrs = help_epk-bukrs
                sexbl = help_epk-sexbl
                sexbl_konto_sort = help_epk-sexbl_konto_sort "WKUK015647
                belnr = help_epk-belnr     "Beleg pro Beleg "WKUK017307
*               konto_sort = help_epk-konto_sort "WKUK015412"WKUK015647
                konto_sort = help_epk-konto_sort            "WKUK015647
                smwkz = help_epk-smwkz
*               txjcd = help_epk-txjcd                      "GLW note 1512212
                stxjc = help_epk-stxjc                      "GLW note 1512212
                stxlv = help_epk-stxlv                      "GLW note 1512212
                stxjc_deep = help_epk-stxjc_deep            "GLW note 1512212
                waers = help_epk-waers
                vbund = help_epk-vbund.                     "WKUK029301
      ELSE.                                                 "WKUK000971
* ...but when posting document per CO-object, read epk      "WKUK000971
* with complete CO information                              "WKUK000971
        READ TABLE epk INTO wa_epk                          "WKUK000971
            WITH KEY pernr = help_epk-pernr                 "WKUK000971
                kschl = help_epk-kschl                      "WKUK010228
                slbsl = help_epk-slbsl                      "WKUK000971
                konto = help_epk-konto                      "WKUK000971
                bukrs = help_epk-bukrs                      "WKUK000971
                sexbl = help_epk-sexbl                      "WKUK000971
                smwkz = help_epk-smwkz                      "WKUK000971
                txjcd = help_epk-txjcd                      "WKUK000971
                waers = help_epk-waers                      "WKUK000971
* now the fields contained in PSREF are required            "WKUK000971
*               BUKRS = help_epk-BUKRS   "already done      "WKUK000971
                gsber = help_epk-gsber                      "WKUK000971
                kokrs = help_epk-kokrs                      "WKUK000971
                kostl = help_epk-kostl                      "WKUK000971
                aufnr = help_epk-aufnr                      "WKUK000971
                kstrg = help_epk-kstrg                      "WKUK000971
                posnr = help_epk-posnr                      "WKUK000971
                nplnr = help_epk-nplnr                      "WKUK000971
                vornr = help_epk-vornr                      "WKUK000971
                kdauf = help_epk-kdauf                      "WKUK000971
                kdpos = help_epk-kdpos                      "WKUK000971
                paobjnr = help_epk-paobjnr                  "WKUK000971
                prznr = help_epk-prznr                      "WKUK000971
                fistl = help_epk-fistl                      "WKUK000971
                fipos = help_epk-fipos                      "WKUK000971
                geber = help_epk-geber                      "WKUK000971
                budget_period = help_epk-budget_period      "XMW EhP5 Budget Period
                ebeln = help_epk-ebeln                      "WKUK000971
                ebelp = help_epk-ebelp                      "WKUK000971
                lstnr = help_epk-lstnr                      "WKUK000971
                ltlst = help_epk-ltlst                      "WKUK000971
                sbukr = help_epk-sbukr                      "WKUK000971
                sgsbr = help_epk-sgsbr                      "WKUK000971
                skost = help_epk-skost                      "WKUK000971
                lstar = help_epk-lstar                      "WKUK000971
*               EXBEL = help_epk-EXBEL    "already done     "WKUK000971
*               MWSKZ = help_epk-MWSKZ    "already done     "WKUK000971
                otype = help_epk-otype                      "WKUK000971
                stell = help_epk-stell                      "WKUK000971
                pohrs = help_epk-pohrs                      "WKUK000971
                dart  = help_epk-dart                       "WKUK000971
                udart = help_epk-udart                      "WKUK000971
                sgtxt = help_epk-sgtxt                      "WKUK000971
*               TXJCD = help_epk-TXJCD   "already done      "WKUK000971
                fipex = help_epk-fipex                      "WKUK000971
                fkber = help_epk-fkber    "neu zu QIZK002508"WKUK000971
            grant_nbr = help_epk-grant_nbr"neu zu QIZK002508"WKUK000971
                prctr = help_epk-prctr                      "WKUK015412
                segment = help_epk-segment  "GLW note 2926207
* end of PSREF fields                                       "WKUK000971
                vbund = help_epk-vbund.                     "WKUK000971
      ENDIF.                                                "WKUK000971
      IF sy-subrc = 0.
* if so, condense further
        wa_epk-betrg   = wa_epk-betrg + help_epk-betrg.
        wa_epk-fwbas   = wa_epk-fwbas + help_epk-fwbas.
        wa_epk-ep_line = help_epk-ep_line.
        MODIFY epk FROM wa_epk INDEX sy-tabix.
      ELSE.
* if not, create new entry in table EPK
        line_to_insert =
            help_epk-line_to_insert + lines_inserted_so_far.
        INSERT help_epk INTO epk INDEX line_to_insert.
        ADD 1 TO lines_inserted_so_far.
      ENDIF.
    ENDLOOP.
  ENDIF.

ENDFORM.                               " CONDENSE_TAX_LINES

*&---------------------------------------------------------------------*
*&      Form  CHECK_CAP_DETERMINATION
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->FIELDS
*      -->BUKRS_1
*      -->BUKRS_2
*----------------------------------------------------------------------*
FORM check_cap_determination
    USING fields    STRUCTURE acct_det_c_c_bf
          bukrs_1
          bukrs_2.

  IF fields-hkont IS INITIAL AND
     fields-saknr IS INITIAL AND
     fields-kunnr IS INITIAL AND
     fields-lifnr IS INITIAL.
* Error in clearing account determination in table T001U
* create account determination error message for exception
    CONCATENATE bukrs_1
                bukrs_2
                fields-ktosl
           INTO par2
      SEPARATED BY ' '.
    MESSAGE ID     '56'
            TYPE   'E'
            NUMBER '001'
            WITH   'T001U'
            par2
            RAISING fi_customizing_error.
  ENDIF.

ENDFORM.                               " CHECK_CAP_DETERMINATION



*---------------------------------------------------------------------*
*       FORM HANDLE_POSTING_DOCUMENT_SPLIT                            *
*---------------------------------------------------------------------*
*       ........                                                      *
*---------------------------------------------------------------------*
*  -->  P_STORE                                                       *
*  -->  P_BUKRS                                                       *
*  -->  P_KOART                                                       *
*  -->  PSREF                                                         *
*  -->  PERNR                                                         *
*  -->  EXBEL                                                         *
*  -->  MWSKZ                                                         *
*  -->  TXJCD                                                         *
*  -->  NO_NEW_POSTING_DOCUMENT                                       *
*  -->  POSTING_DOCUMENT_SPLIT                                        *
*---------------------------------------------------------------------*
FORM handle_posting_document_split
    TABLES   p_store LIKE store_bz[]
             p_int_rot_awkey STRUCTURE  ptrv_rot_awkey    "GLW note 2178197
    USING    p_bukrs
             p_koart
             p_koart_pds                                    "WKUK012485
             psref
             pernr
             exbel
             belnr                                     "Beleg pro Beleg
             konto_sort                                     "WKUK015412
             bl_spl_tmp                                     "WKUK015412
             prctr                                          "WKUK015412
             segment
    CHANGING mwskz
             txjcd
             no_new_posting_document
             posting_document_split.

* handle reading of T030 for posting document split account in BUKST
  momagkomok = '1BS'.

  PERFORM administrate_fi_acct_det_hr
      USING momagkomok
            p_bukrs
*           epk-ktosl
            'HRT'
            '          '
            fi_acct_det_hr_append_flag
            tabix.

  IF fi_acct_det_hr_append_flag = 'X'.
    APPEND fi_acct_det_hr.
  ENDIF.

  IF fi_acct_det_hr-konto IS INITIAL AND
     fi_acct_det_hr-hnkto IS INITIAL.

* Error in posting document split account determination in table T030
* create account determination error message for exception
    CONCATENATE fi_acct_det_hr-bukrs
                fi_acct_det_hr-ktosl
                fi_acct_det_hr-momagkomok
           INTO par2
           SEPARATED BY ' '.
    MESSAGE ID     '56'
            TYPE   'E'
            NUMBER '001'
            WITH   'T030'
                   par2
           RAISING fi_customizing_error.
  ENDIF.

* handle line for posting document split account in old posting document
* (always with tax and jurisdiction code)
* look if line similar to current line is already in posting document
  READ TABLE bz INTO wa_bz
      WITH KEY awref = n_awref
               pernr = bz-pernr
               ktosl = fi_acct_det_hr-ktosl
               koart = fi_acct_det_hr-koart
               slbsl = fi_acct_det_hr-slbsl
               hnbsl = fi_acct_det_hr-hnbsl
               konto = fi_acct_det_hr-konto
               hnkto = fi_acct_det_hr-hnkto
               bukrs = p_bukrs
               exbel = bz-exbel
               mwskz = bz-mwskz
               txjcd = bz-txjcd
               waers = bz-waers.

  IF sy-subrc = 0.
* if so, add current amount to amount of the found posting document line
    wa_bz-betrg   = wa_bz-betrg + epk-betrg.
    wa_bz-ep_line = bz-ep_line.
* posting document lines created by cross company postings  "WKUK065591
* are deleted if their amount is zero (looks better!)       "WKUK065591
    IF wa_bz-betrg = 0.                                     "WKUK065591
      DELETE bz INDEX sy-tabix.                             "WKUK065591
    ELSE.                                                   "WKUK065591
      MODIFY bz FROM wa_bz INDEX sy-tabix.
    ENDIF.                                                  "WKUK065591
    bz_anzhl_store = bz_anzhl_store - 1.
  ELSE.
* if not, creation of new posting document line is necessary
    CLEAR wa_bz.
    wa_bz-awref = n_awref.
    wa_bz-aworg = space.
    wa_bz-awlin = bz_anzhl.
    wa_bz-pernr = bz-pernr.
    wa_bz-datv1 = bz-datv1.
    wa_bz-datb1 = bz-datb1.
    wa_bz-sgtxt = bz-sgtxt.
    wa_bz-ktosl = fi_acct_det_hr-ktosl.
    wa_bz-koart = fi_acct_det_hr-koart.
    wa_bz-slbsl = fi_acct_det_hr-slbsl.
    wa_bz-hnbsl = fi_acct_det_hr-hnbsl.
    wa_bz-konto = fi_acct_det_hr-konto.
    wa_bz-hnkto = fi_acct_det_hr-hnkto.
    wa_bz-bukrs = p_bukrs.
    wa_bz-exbel = bz-exbel.
    wa_bz-mwskz = bz-mwskz.
    wa_bz-txjcd = bz-txjcd.
    wa_bz-kokey+1(1) = 'X'.            "MWSKZ only for display
    wa_bz-betrg = bz-betrg.
    wa_bz-waers = bz-waers.
    wa_bz-beldt = bz-beldt.   "GLW note 2114815
    wa_bz-ep_line = bz-ep_line.
    APPEND wa_bz TO bz.
    READ TABLE p_store
        WITH KEY awref = wa_bz-awref
                 aworg = wa_bz-aworg.
    MOVE-CORRESPONDING wa_bz TO p_store.
    p_store-psref = psref.
    p_store-pernr = pernr.
    p_store-exbel = exbel.
    p_store-koart = p_koart.                                "WKUK012485
    IF sy-subrc = 0.
      MODIFY p_store INDEX sy-tabix.
    ELSE.
      APPEND p_store.
    ENDIF.
  ENDIF.

* condense tax lines coming from condensed posting document split lines
  PERFORM condense_tax_lines
      USING fi_acct_det_hr-slbsl
            fi_acct_det_hr-konto
            space.                                          "WKUK029301

* handle line for posting document split account in new posting document
* (always without tax and jurisdiction code)
* look if new awkey for posting document is necessary
  READ TABLE store_bz_pds
      WITH KEY bukrs = p_bukrs
               psref = psref
               pernr = pernr
               exbel = exbel
               belnr = belnr                           "Beleg pro Beleg
               konto_sort = konto_sort                      "WKUK015412
               prctr = prctr                                "WKUK015412
               segment = segment "GLW note 2926207
               waers = epk-waers
               umdat = epk-umdat                         "QKZ_CEE_CZ_SK
               koart = p_koart_pds                          "WKUK012485
               xnegp = epk-xnegp.   "GLW note 2071158

  IF sy-subrc EQ 0.
* no new posting document necessary

    CASE bl_spl.
* in case there is a posting document with the key already there,
* it is necessary to check whether it was already written with EMPTY_BZ.
* If so, set a sign so that writing of new posting document header
* in EMPTY_BZ is prohibited.
* BEGIN Beleg pro Beleg
      WHEN 'Q'.                        "Posting document per receipt
        IF NOT ( store_bz_pds-belnr EQ bz-belnr AND
                 store_bz_pds-waers EQ bz-waers ).
          no_new_posting_document = 'X'.
        ENDIF.
* END Beleg pro Beleg
      WHEN 'R'.                        "Posting document per trip
        IF NOT ( store_bz_pds-exbel EQ bz-exbel AND
                 store_bz_pds-waers EQ bz-waers ).
          no_new_posting_document = 'X'.
        ENDIF.
      WHEN 'P'.                        "Posting document per employee
        IF NOT ( store_bz_pds-pernr EQ bz-pernr AND
                 store_bz_pds-waers EQ bz-waers ).
          no_new_posting_document = 'X'.
        ENDIF.
      WHEN 'C'.                        "Posting document per CO-object
        IF NOT (
* never in PSREF              store_bz_pds-psref-bukrs eq epk-bukrs and
              store_bz_pds-psref-gsber EQ epk-gsber AND
              store_bz_pds-psref-kokrs EQ epk-kokrs AND
              store_bz_pds-psref-kostl EQ epk-kostl AND
              store_bz_pds-psref-aufnr EQ epk-aufnr AND
              store_bz_pds-psref-kstrg EQ epk-kstrg AND
              store_bz_pds-psref-posnr EQ epk-posnr AND
              store_bz_pds-psref-nplnr EQ epk-nplnr AND
              store_bz_pds-psref-vornr EQ epk-vornr AND
              store_bz_pds-psref-kdauf EQ epk-kdauf AND
              store_bz_pds-psref-kdpos EQ epk-kdpos AND
              store_bz_pds-psref-paobjnr EQ epk-paobjnr AND
              store_bz_pds-psref-prznr EQ epk-prznr AND
              store_bz_pds-psref-fistl EQ epk-fistl AND
              store_bz_pds-psref-fipos EQ epk-fipos AND
              store_bz_pds-psref-fipex EQ epk-fipex AND     "QIZK002508
              store_bz_pds-psref-fkber EQ epk-fkber AND     "QIZK002508
              store_bz_pds-psref-grant_nbr EQ               "QIZK002508
                                      epk-grant_nbr AND     "QIZK002508
              store_bz_pds-prctr       EQ epk-prctr AND     "WKUK015412
              store_bz_pds-segment     EQ epk-segment AND "GLW note 2926207
              store_bz_pds-psref-geber EQ epk-geber AND
              store_bz_pds-psref-ebeln EQ epk-ebeln AND
              store_bz_pds-psref-ebelp EQ epk-ebelp AND
              store_bz_pds-psref-lstnr EQ epk-lstnr AND
              store_bz_pds-psref-ltlst EQ epk-ltlst AND
              store_bz_pds-psref-sbukr EQ epk-sbukr AND
              store_bz_pds-psref-sgsbr EQ epk-sgsbr AND
              store_bz_pds-psref-skost EQ epk-skost AND
              store_bz_pds-psref-lstar EQ epk-lstar AND
* never in PSREF              store_bz_pds-psref-exbel eq epk-exbel and
* never in PSREF              store_bz_pds-psref-mwskz eq epk-mwskz and
              store_bz_pds-psref-otype EQ epk-otype AND
              store_bz_pds-psref-stell EQ epk-stell AND
              store_bz_pds-psref-pohrs EQ epk-pohrs AND
              store_bz_pds-psref-dart  EQ epk-dart  AND
              store_bz_pds-psref-udart EQ epk-udart AND
* never in PSREF              store_bz_pds-psref-sgtxt eq epk-sgtxt and
* never in PSREF              store_bz_pds-psref-txjcd eq epk-txjcd and
              store_bz_pds-psref-fipex EQ epk-fipex AND
              store_bz_pds-waers EQ bz-waers ).
          no_new_posting_document = 'X'.
        ENDIF.
      WHEN 'B'.                 "Posting document per company code
        IF NOT ( store_bz_pds-bukrs EQ p_bukrs AND
                 store_bz_pds-waers EQ bz-waers ).
          no_new_posting_document = 'X'.
        ENDIF.
    ENDCASE.
* BEGIN WKUK015412
    IF bl_spl_tmp = 'K'.   "posting document per vendor
      IF NOT ( store_bz_pds-konto_sort EQ bz-konto_sort AND
               store_bz_pds-waers EQ bz-waers ).
        no_new_posting_document = 'X'.
      ENDIF.
    ENDIF.
* END WKUK015412

    n_awref  = store_bz_pds-awref.
    bz_anzhl = store_bz_pds-awlin + 1.

* look if line similar to current line is already in posting document
    READ TABLE bz INTO wa_bz
        WITH KEY awref = n_awref
                 pernr = bz-pernr
                 ktosl = fi_acct_det_hr-ktosl
                 koart = fi_acct_det_hr-koart
                 slbsl = fi_acct_det_hr-slbsl
                 hnbsl = fi_acct_det_hr-hnbsl
                 konto = fi_acct_det_hr-konto
                 hnkto = fi_acct_det_hr-hnkto
                 bukrs = p_bukrs
                 exbel = bz-exbel
                 belnr = bz-belnr "Beleg pro Beleg
                 konto_sort = bz-konto_sort                 "WKUK015412
                 prctr = bz-prctr                           "WKUK015412
                 segment = bz-segment "GLW note 2926207
                 waers = bz-waers.

    IF sy-subrc = 0.
* if so, add current amount to amount of the found posting document line
      wa_bz-betrg   = wa_bz-betrg - epk-betrg.
      wa_bz-ep_line = bz-ep_line.
* posting document lines created by cross company postings  "WKUK065591
* are deleted if their amount is zero (looks better!)       "WKUK065591
      IF wa_bz-betrg = 0.                                   "WKUK065591
        DELETE bz INDEX sy-tabix.                           "WKUK065591
      ELSE.                                                 "WKUK065591
        MODIFY bz FROM wa_bz INDEX sy-tabix.
      ENDIF.                                                "WKUK065591
    ELSE.
* if not, calculate next line number for posting document
      subrc = sy-subrc.
    ENDIF.

  ELSE.
* new posting document necessary for posting document split account

    subrc = sy-subrc.
    PERFORM number_get_next.
*   N_AWREF = I_AWREF.  " WBG Hotline 175746
    bz_anzhl = 1.

  ENDIF.

  PERFORM administrate_buv_help                             "WKUK005642
      USING n_awref.                                        "WKUK005642

  IF subrc NE 0.
* creation of new posting document line is necessary
    CLEAR subrc.
    CLEAR wa_bz.
    wa_bz-awref = n_awref.
    wa_bz-aworg = space.
    wa_bz-awlin = bz_anzhl.
    wa_bz-pernr = bz-pernr.
    wa_bz-datv1 = bz-datv1.
    wa_bz-datb1 = bz-datb1.
    wa_bz-sgtxt = bz-sgtxt.
    wa_bz-ktosl = fi_acct_det_hr-ktosl.
    wa_bz-koart = fi_acct_det_hr-koart.
    wa_bz-slbsl = fi_acct_det_hr-slbsl.
    wa_bz-hnbsl = fi_acct_det_hr-hnbsl.
    wa_bz-konto = fi_acct_det_hr-konto.
    wa_bz-hnkto = fi_acct_det_hr-hnkto.
    wa_bz-bukrs = p_bukrs.
    wa_bz-exbel = bz-exbel.
    wa_bz-kokey(1) = no_new_posting_document.
    wa_bz-betrg = -1 * bz-betrg.
    wa_bz-waers = bz-waers.
    wa_bz-ep_line = bz-ep_line.
    wa_bz-beldt = bz-beldt.  "GLW note  2114815
    APPEND wa_bz TO bz.

    PERFORM handle_trip_assignment TABLES p_int_rot_awkey.  "GLW note 2178197

    READ TABLE store_bz_pds
        WITH KEY awref = wa_bz-awref
                 aworg = wa_bz-aworg.
    MOVE-CORRESPONDING wa_bz TO store_bz_pds.
    store_bz_pds-koart = p_koart_pds.                       "WKUK012485
    store_bz_pds-psref = psref.
    store_bz_pds-pernr = pernr.
    store_bz_pds-segment = segment. "GLW note 2926207
    store_bz_pds-exbel = exbel.
    store_bz_pds-belnr = belnr.                        "Beleg pro Beleg
    store_bz_pds-konto_sort = konto_sort.                   "WKUK015412
    store_bz_pds-prctr = prctr.                             "WKUK015412
    IF sy-subrc = 0.
      MODIFY store_bz_pds INDEX sy-tabix.
    ELSE.
      APPEND store_bz_pds.
    ENDIF.
    ADD 1 TO bz_anzhl.                 "Buchungszeilenanzahl
  ENDIF.

  posting_document_split = 'X'.
  CLEAR: mwskz,
         txjcd.

ENDFORM.                               "HANDLE_POSTING_DOCUMENT_SPLIT



*&---------------------------------------------------------------------*
*&      Form  TREAT_WANDERING_TAX_LINE
*&---------------------------------------------------------------------*
* Routine new for WKUK059035
* According to rounding differences it may happen that G/L account
* lines were condensed to zero but their corresponding tax lines will
* not. Such tax lines have base amount zero (due to condensation of
* G/L account lines) but amount not zero. They cannot be treated
* like normal tax lines, because they can not be connected to a
* corresponding G/L account line. This routine converts such tax
* lines into G/L account lines and creates the necessary tax lines
* (all with amount zero and in master company code) in the table BZ,
* so that the posting document is correct
*----------------------------------------------------------------------*
FORM treat_wandering_tax_line
    TABLES int_rot_awkey STRUCTURE ptrv_rot_awkey
*    USING old_bukrs.                                       "WKUK015412
     USING old_bukrs                                        "WKUK015412
           psref.                                           "WKUK015412

  DATA: wa_epk       LIKE epk,
        wa_bz        LIKE bz,                               "WKUK029369
        bz_field(23),
        bz_betrg     LIKE bz-betrg.

  IF ( NOT bz-tax_indicator IS INITIAL AND bz-fwbas IS INITIAL ).
* BEGIN WKUK029369
* IF-statement is not sufficient to identify a tax line without
* corresponding G/L account line. So look in table BZ with key
* EP_LINE whether a corresponding G/L account line is there.
    READ TABLE bz INTO wa_bz
        WITH KEY ep_line       = bz-ep_line
                 tax_indicator = space.
    IF NOT sy-subrc = 0.
* If such a line is not found, then..
* END WKUK029369
* Current line is a tax line without corresponding G/L account line

* First all necessary tax lines must be created

* Find one of the corresponding G/L account lines in table EPK
      READ TABLE epk INTO wa_epk
          WITH KEY ep_line       = bz-ep_line
                   tax_indicator = space.

* For posting document per company code or per CO-object a new posting
* document cannot be created via central FORM EMPTY_BZ.
* Thus the necessity of a new posting document is checked several times
      IF bl_spl = 'B' OR bl_spl = 'C'.
        IF NOT old_bukrs IS INITIAL.     "nicht beim 1.mal
          READ TABLE store_bz
              WITH KEY bukrs = epk-bukst
                       psref = psref
                       umdat = epk-umdat           "QKZ_CEE_CZ_SK
                       waers = epk-waers.
          IF sy-subrc EQ 0.
            n_awref  = store_bz-awref.
            bz_anzhl = store_bz-awlin + 1.
          ENDIF.
        ENDIF.
      ENDIF.

      bz-awref = n_awref.
      bz-aworg = space.
      CLEAR bz-awlin.                    "Not yet known, determined later

      bz_betrg = bz-betrg.               "save rounding difference

* reconstruct all tax lines with help of the TAX_ITEM_LINE of the
* original G/L account line
      LOOP AT tax_item_out
          WHERE posnr = wa_epk-tax_item_line
            AND error IS INITIAL.        "VAT calculation successful

        bz-bukrs = tax_item_out-bukrs.
        bz-mwskz = tax_item_out-mwskz.
        bz-txjcd = tax_item_out-txjcd.
        bz-waers = tax_item_out-waers.
        bz-txdat = tax_item_out-txdat.
        CLEAR bz-betrg.       "tax amount must be zero for all tax lines
        bz-msatz = tax_item_out-msatz.
        bz-fwbas = bz_betrg.  "base amount is amount of original tax line
        bz-brutto = bz_betrg.
        IF tax_item_out-stbkz NE 3.
* when VAT is not allocatable...
          IF tax_item_out-stazf = 'X'.
* ... and not deductible, create statistical tax line
            bz-hnkto = tax_item_out-hkont.  "no tax account
            bz-kstat = 'X'.              "tax line is statistical"
          ELSE.
* ... but deductible, create normal tax line
            bz-hnkto = tax_item_out-hkont.
            CLEAR bz-kstat.
          ENDIF.
        ELSE.
* when VAT is allocatable, create statistical tax line
          CLEAR bz-hnkto.                "no tax account
          bz-kstat = 'X'.                "tax line is statistical
        ENDIF.
        bz-ktosl = tax_item_out-ktosl.
        bz-kschl = tax_item_out-kschl.
        bz-tax_line = sy-tabix.
        bz-tax_indicator = 'X'.
        APPEND bz.

* now create G/L account line for non allocatable non deductible tax
        IF tax_item_out-stbkz NE 3.
* when VAT is not allocatable...
          IF tax_item_out-stazf = 'X'.
* ... and not deductible, create additional G/L account line
            bz-konto = tax_item_out-hkont.
*         clear bz-fwbas.
            CLEAR bz-tax_indicator.
            CLEAR bz-kstat.
* G/L account line for non deductible, non allocatable tax has
* amount zero and can (even in cross-company case) be posted to
* master company code
            bz-bukrs = wa_epk-bukst.
* But the CO-objects may not be existing there, so delete them and
* rely on default cost center for tax G/L account.
            LOOP AT psref_fields.
              CHECK psref_fields-field <> 'BUKRS'.
              CHECK psref_fields-field <> 'SGTXT'.
              CHECK psref_fields-field <> 'EXBEL'.
              CHECK psref_fields-field <> 'GSBER'.
              bz_field(3) = 'BZ-'.
              bz_field+3(20) = psref_fields-field.
              ASSIGN (bz_field) TO <f>.
              CLEAR <f>.
            ENDLOOP.

            ADD 1 TO bz_anzhl.           "Buchungszeilenanzahl
            bz_anzhl_store = bz_anzhl.

            bz-awlin = bz_anzhl.
* AWKEY + BZ_ANZHL wird in Zuordnungstabelle geschrieben
            LOOP AT int_rot_awkey.
              int_rot_awkey-awref = n_awref.
              int_rot_awkey-aworg = space.
              int_rot_awkey-awlin = bz_anzhl.
              MODIFY int_rot_awkey.
            ENDLOOP.
            MODIFY ptrv_rot_awkey FROM TABLE int_rot_awkey.

            APPEND bz.
          ENDIF.
        ENDIF.

      ENDLOOP.

* Then convert original "tax" line into a G/L account line.
      MOVE-CORRESPONDING wa_epk TO bz.
      CLEAR: bz-tax_indicator,
             bz-fwbas,
             bz-tax_line.
      bz-betrg = bz_betrg.
      bz-exbel = wa_epk-sexbl.
      bz-mwskz = wa_epk-smwkz.
      bz-txjcd_deep = wa_epk-stxjc_deep.
      bz-txjcd = wa_epk-stxjc.

      CLEAR: wa_epk,
             bz_betrg.

    ENDIF.                                                  "WKUK029369
    CLEAR wa_bz.                                            "WKUK029369

  ENDIF.

* After that, the newly created G/L account line should be treated like
* any other G/L account line...
ENDFORM.                               " TREAT_WANDERING_TAX_LINE



*&---------------------------------------------------------------------*
*&      Form  DETERMINE_NO_OF_RECEIVERS
*&---------------------------------------------------------------------*
* Routine new for WKUK063502, determines number of ALE-receivers
*----------------------------------------------------------------------*
*      -->P_RECEIVERS_LINES  number of logical systems in ALE scenario
*----------------------------------------------------------------------*
FORM determine_no_of_receivers USING    p_receivers_lines.

  DATA: receivers               LIKE bdibapi_dest OCCURS 0 WITH HEADER LINE,
        wa_receivers            LIKE bdibapi_dest,
*       filterobjects_values like bdi_fobj                  "WKUK000524
*                             occurs 0 with header line,    "WKUK000524
        zw_filterobjects_values LIKE bdi_fobj OCCURS 0 WITH HEADER LINE,
        append_flag.

  CLEAR bukrs_receivers. REFRESH bukrs_receivers.           "WKUK000523

*  loop at tax_item_in.                                     "WKUK000524
*    read table filterobjects_values                        "WKUK000524
*        with key objvalue = tax_item_in-bukrs.             "WKUK000524
*    if sy-subrc ne 0.                                      "WKUK000524
*      filterobjects_values-objtype = 'COMP_CODE'.          "WKUK000524
*      filterobjects_values-objvalue = tax_item_in-bukrs.   "WKUK000524
*      append filterobjects_values.                         "WKUK000524
*    endif.                                                 "WKUK000524
*  endloop.                                                 "WKUK000524

  LOOP AT filterobjects_values.

    CLEAR zw_filterobjects_values. REFRESH zw_filterobjects_values.
    MOVE-CORRESPONDING filterobjects_values TO zw_filterobjects_values.
    APPEND zw_filterobjects_values.

    CALL FUNCTION 'ALE_BAPI_GET_UNIQUE_RECEIVER'
      EXPORTING
        object                        = 'BUS6001'
        method                        = 'CHECKACCOUNTASSIGNMENT'
      IMPORTING
        receiver                      = receivers
      TABLES
        filterobjects_values          = zw_filterobjects_values
      EXCEPTIONS
        error_in_filterobjects        = 1
        error_in_ale_customizing      = 2
        not_unique_receiver           = 3
        no_rfc_destination_maintained = 4
        OTHERS                        = 5.

    IF sy-subrc = 0.
      CLEAR append_flag.
      LOOP AT receivers INTO wa_receivers.
        IF receivers = wa_receivers.
          append_flag = 'X'.
        ENDIF.
      ENDLOOP.
      IF append_flag NE 'X'.
        APPEND receivers.
      ENDIF.
      bukrs_receivers-bukrs    =                            "WKUK000523
          zw_filterobjects_values-objvalue.                 "WKUK000523
      bukrs_receivers-receiver = receivers.                 "WKUK000523
      APPEND bukrs_receivers.                               "WKUK000523
    ENDIF.
  ENDLOOP.
  DESCRIBE TABLE receivers LINES p_receivers_lines.

ENDFORM.                               " DETERMINE_NO_OF_RECEIVERS



*&---------------------------------------------------------------------*
*&      Form  CHECK_MASTER_COST_ASSIGNMENT
*&---------------------------------------------------------------------*
* Form neu zu WKUK063501: The master cost center, which is used as
* dummy cost assignment for additional NAV lines in case of cross
* company postings, was probably not checked in the accumulated
* COBL_CHECK. So it has to be checked here separately.
*----------------------------------------------------------------------*
FORM check_master_cost_assignment.
  DATA: epk_field(24),
        lines                        LIKE sy-tabix,
        budat_help                   LIKE budat,
        bukrs_save                   LIKE epk-bukrs,
        gsber_save                   LIKE epk-gsber,
        accountingobjects_tabix      LIKE sy-tabix,
        wa_result_accountingobjects  LIKE accountingobjects,
        wa_reading_accountingobjects LIKE accountingobjects,
        wa_cobl_errors               LIKE cobl_errors,
        w_cobl_errors                LIKE cobl_errors OCCURS 1 WITH HEADER LINE,
* tables for NAV COBL_CHECK
        nav_accountingobjects        LIKE accountingobjects
                   OCCURS 1 WITH HEADER LINE,
        nav_cobl_errors              LIKE cobl_errors
                   OCCURS 1 WITH HEADER LINE,
        nav_return_table             LIKE return_table
                   OCCURS 1 WITH HEADER LINE.

* tables for storing:
* 1) the NAV master cost assignments
  STATICS checked_nav_accountingobjects LIKE accountingobjects OCCURS 1.
* 2) the error messages concerning the NAV master cost assignments
  STATICS checked_nav_cobl_errors LIKE cobl_errors OCCURS 1.
* that were already checked in this routine

* handle setting of posting date and posting document date
  IF budat = '11111111'.
    budat_help = epk-datv1.
  ELSEIF budat = '99999999'.
    budat_help = epk-datb1.
  ELSEIF budat = '22222222'.                           "Beleg pro Beleg
    budat_help = epk-beldt.                            "Beleg pro Beleg
  ELSEIF budat = '33333333'.                           "VRD_CEE_RU
    budat_help = epk-umdat.            "Reference date "VRD_CEE_RU
  ELSE.
    budat_help = budat.
  ENDIF.

* fill work area only with master cost assignment
  wa_reading_accountingobjects-comp_code =
      ep_translate-bukst.
  wa_reading_accountingobjects-bus_area  =
      accountingobjects-bus_area_empl.
  wa_reading_accountingobjects-posting_date =
      budat_help.
  wa_reading_accountingobjects-costcenter =
      accountingobjects-costcenter_empl.
  wa_reading_accountingobjects-bus_area_empl =
      accountingobjects-bus_area_empl.
  wa_reading_accountingobjects-costcenter_empl =
      accountingobjects-costcenter_empl.

* look if master cost assignment already checked in accumul. COBL_CHECK
  READ TABLE accountingobjects
      WITH KEY
        comp_code       = wa_reading_accountingobjects-comp_code
        bus_area        = wa_reading_accountingobjects-bus_area
        posting_date    = wa_reading_accountingobjects-posting_date
        costcenter      = wa_reading_accountingobjects-costcenter
        orderid         = wa_reading_accountingobjects-orderid
        cost_obj        = wa_reading_accountingobjects-cost_obj
        wbs_elemt       = wa_reading_accountingobjects-wbs_elemt
        network         = wa_reading_accountingobjects-network
        activity        = wa_reading_accountingobjects-activity
        cmmt_item       = wa_reading_accountingobjects-cmmt_item
        funds_ctr       = wa_reading_accountingobjects-funds_ctr
        fund            = wa_reading_accountingobjects-fund
        sales_ord       = wa_reading_accountingobjects-sales_ord
        s_ord_item      = wa_reading_accountingobjects-s_ord_item
        costcenter_empl = wa_reading_accountingobjects-costcenter_empl
        bus_area_empl   = wa_reading_accountingobjects-bus_area_empl
      INTO wa_result_accountingobjects.
  IF sy-subrc = 0.
* cost assignment already checked in accumulated COBL_CHECK,
* fill error table
    LOOP AT cobl_errors INTO wa_cobl_errors
        WHERE row = wa_ep_translate-cobl_check_line.
      APPEND wa_cobl_errors TO w_cobl_errors.
    ENDLOOP.
  ELSE.
* look if cost assignment already checked in NAV COBL_CHECK
    READ TABLE checked_nav_accountingobjects
        WITH KEY
          comp_code       = wa_reading_accountingobjects-comp_code
          bus_area        = wa_reading_accountingobjects-bus_area
          posting_date    = wa_reading_accountingobjects-posting_date
          costcenter      = wa_reading_accountingobjects-costcenter
          orderid         = wa_reading_accountingobjects-orderid
          cost_obj        = wa_reading_accountingobjects-cost_obj
          wbs_elemt       = wa_reading_accountingobjects-wbs_elemt
          network         = wa_reading_accountingobjects-network
          activity        = wa_reading_accountingobjects-activity
          cmmt_item       = wa_reading_accountingobjects-cmmt_item
          funds_ctr       = wa_reading_accountingobjects-funds_ctr
          fund            = wa_reading_accountingobjects-fund
          sales_ord       = wa_reading_accountingobjects-sales_ord
          s_ord_item      = wa_reading_accountingobjects-s_ord_item
          costcenter_empl = wa_reading_accountingobjects-costcenter_empl
          bus_area_empl   = wa_reading_accountingobjects-bus_area_empl
        INTO wa_result_accountingobjects.
    IF sy-subrc = 0.
* cost assingment already checked in NAV COBL_CHECK
      accountingobjects_tabix = sy-tabix.
* fill error table
      LOOP AT checked_nav_cobl_errors INTO wa_cobl_errors
          WHERE row = accountingobjects_tabix.
        APPEND wa_cobl_errors TO w_cobl_errors.
      ENDLOOP.
    ELSE.
* cost assingment still to be checked
      APPEND wa_reading_accountingobjects TO nav_accountingobjects.
* COBL_CHECK for NAV cost assingment
      CALL FUNCTION 'HRCA_CODINGBLOCK_PRECHECK_HR'
        TABLES
          accountingobjects = nav_accountingobjects
          return            = nav_cobl_errors
          return_table      = nav_return_table.

      READ TABLE nav_return_table INDEX 1.
      IF sy-subrc = 0.
        MESSAGE ID     nav_return_table-id
                TYPE   nav_return_table-type
                NUMBER nav_return_table-number
                WITH   nav_return_table-message_v1
                       nav_return_table-message_v2
                       nav_return_table-message_v3
                       nav_return_table-message_v4
                RAISING ale_communication_error.
      ENDIF.

      CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
        EXPORTING
          text = text-p04.
* fill working area and table for result analysis
      READ TABLE nav_accountingobjects INDEX 1
          INTO wa_result_accountingobjects.
      LOOP AT nav_cobl_errors INTO wa_cobl_errors.
        APPEND wa_cobl_errors TO w_cobl_errors.
      ENDLOOP.

* fill storing tables
      APPEND wa_result_accountingobjects
          TO checked_nav_accountingobjects.
      DESCRIBE TABLE checked_nav_accountingobjects LINES lines.
      LOOP AT nav_cobl_errors INTO wa_cobl_errors.
        wa_cobl_errors-row = lines.
        APPEND wa_cobl_errors TO checked_nav_cobl_errors.
      ENDLOOP.
    ENDIF.

  ENDIF.

* analyse NAV cobl_check results (are in wa1_accountingobjects)
  CLEAR: w_cobl_errors,
         post_result,
         append_replace_line,
         append_error_line.
  brlin = 1.
* bring nav_cobl_check messages to result table
  LOOP AT w_cobl_errors.
    CLEAR wa_bapiret2.
* transport cobl error messages
    MOVE-CORRESPONDING w_cobl_errors TO wa_bapiret2.
* error sign in result table only when cobl_check error
    IF NOT replace IS INITIAL.
* substitution procedure wanted.
      IF wa_result_accountingobjects-result = '3'.

        PERFORM administrate_post_result USING 'X' ' '.

      ELSE.

        PERFORM administrate_post_result USING ' ' ' '.

      ENDIF.
    ELSE.
* no subsititution -> no messages about substitution cost centers

      PERFORM administrate_post_result USING 'X' 'X'.

    ENDIF.
    brlin = brlin + 1.
  ENDLOOP.
* substitution procedure wanted.
  IF NOT replace IS INITIAL.
* manage substitution if necessary and construct replace message
    CASE wa_result_accountingobjects-result.
      WHEN '0'.
* posting to accounting object is possible, no action necessary"WKU_TUNE
      WHEN '1'.
* substitution of accounting object by employee cost center possible
        LOOP AT psref_fields.
          CHECK psref_fields-field <> 'SGTXT'. "#EC NOTEXT   "WBGK008343
          CHECK psref_fields-field <> 'EXBEL'. "#EC NOTEXT   "WBGK008343
          CHECK psref_fields-field <> 'FISTL'. "#EC NOTEXT   "XCIK152901
          CHECK psref_fields-field <> 'FIPOS'. "#EC NOTEXT   "XCIK152901
          CHECK psref_fields-field <> 'GEBER'. "#EC NOTEXT   "XCIK152901
          CHECK psref_fields-field <> 'FIPEX'. "#EC NOTEXT   "XCIK152901
          CHECK psref_fields-field <> 'FKBER'. "#EC NOTEXT   "XCIK152901
          CHECK psref_fields-field <> 'GRANT_NBR'.  "#EC NOTEXT"K152901
          epk_field(4) = 'EPK-'.
          epk_field+4(20) = psref_fields-field.
          ASSIGN (epk_field) TO <f>.
          CLEAR <f>.
        ENDLOOP.
        MOVE: epk-bukst                                   TO epk-bukrs,
              wa_result_accountingobjects-bus_area_empl   TO epk-gsber,
              wa_result_accountingobjects-costcenter_empl TO epk-kostl.
* message in result table about successful substitution
        IF append_replace_line = 'X'.
          PERFORM clear_post_result_bapiret2.
          post_result-brlin = post_result-brlin + 1.
          CLEAR wa_bapiret2.
          par1 = wa_result_accountingobjects-costcenter_empl.
*         row  = wa_ep_translate-cobl_check_line.
          CALL FUNCTION 'BALW_BAPIRETURN_GET2'
            EXPORTING
              type   = 'R'
              cl     = '56'
              number = '851'
              par1   = par1
*             row    = row
            IMPORTING
              return = wa_bapiret2.
          MOVE-CORRESPONDING wa_bapiret2 TO post_result.
          APPEND post_result.
        ENDIF.
      WHEN '2'.
* substitution of accounting object by reserve cost center possible
        bukrs_save = epk-bukrs.
        gsber_save = epk-gsber.
        LOOP AT psref_fields.
          CHECK psref_fields-field <> 'SGTXT'. "#EC NOTEXT   "WBGK008343
          CHECK psref_fields-field <> 'EXBEL'. "#EC NOTEXT   "WBGK008343
          CHECK psref_fields-field <> 'FISTL'.   "#EC NOTEXT"XCIK152901
          CHECK psref_fields-field <> 'FIPOS'.   "#EC NOTEXT"XCIK152901
          CHECK psref_fields-field <> 'GEBER'.   "#EC NOTEXT"XCIK152901
          CHECK psref_fields-field <> 'FIPEX'.   "#EC NOTEXT"XCIK152901
          CHECK psref_fields-field <> 'FKBER'.   "#EC NOTEXT"XCIK152901
          CHECK psref_fields-field <> 'GRANT_NBR'.   "#EC NOTEXT"152901
          epk_field(4) = 'EPK-'.
          epk_field+4(20) = psref_fields-field.
          ASSIGN (epk_field) TO <f>.
          CLEAR <f>.
        ENDLOOP.
        MOVE: bukrs_save                               TO epk-bukrs,
              gsber_save                               TO epk-gsber,
              wa_result_accountingobjects-costcenter_default
                                                       TO epk-kostl.
* message in result table about successful substitution
        IF append_replace_line = 'X'.
          PERFORM clear_post_result_bapiret2.
          post_result-brlin  = post_result-brlin + 1.
          CLEAR wa_bapiret2.
          par1 = wa_result_accountingobjects-costcenter_default.
*         row  = wa_ep_translate-cobl_check_line.
          CALL FUNCTION 'BALW_BAPIRETURN_GET2'
            EXPORTING
              type   = 'R'
              cl     = '56'
              number = '852'
              par1   = par1
*             row    = row
            IMPORTING
              return = wa_bapiret2.
          MOVE-CORRESPONDING wa_bapiret2 TO post_result.
          APPEND post_result.
        ENDIF.
      WHEN '3'.
* everything done already
    ENDCASE.
  ENDIF.

ENDFORM.                               " CHECK_MASTER_COST_ASSIGNMENT

*&---------------------------------------------------------------------*
*&      Form  check_awlin
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
FORM check_awlin.

  DATA: bz_copy LIKE bz OCCURS 1 WITH HEADER LINE.
  DATA: bz_final LIKE bz OCCURS 1 WITH HEADER LINE.
  DATA: relevant_for_check TYPE xfeld.


  LOOP AT bz INTO bz_copy.
    APPEND bz_copy.

    AT END OF awlin.
      CLEAR: relevant_for_check.
      LOOP AT bz_copy.
        IF bz_copy-bukrs NE bz_copy-bukst.
          relevant_for_check = 'X'.
        ENDIF.
      ENDLOOP.
      IF relevant_for_check IS INITIAL.
        APPEND LINES OF bz_copy TO bz_final.
        REFRESH bz_copy.
        CONTINUE.
      ENDIF.
      READ TABLE bz_copy INDEX 1.
      IF ( bz_copy-awlin = 1 ) AND ( bz_copy-bukst EQ bz_copy-bukrs ).
        APPEND LINES OF bz_copy TO bz_final.
        REFRESH bz_copy.
        CONTINUE.
      ENDIF.
      IF bz_copy-bukst EQ bz_copy-bukrs AND bz_copy-awlin <> 1.
        READ TABLE bz_copy WITH KEY
         awlin = 1 TRANSPORTING NO FIELDS.

        MODIFY bz_copy INDEX sy-tabix TRANSPORTING awlin.
        bz_copy-awlin = 1.
        MODIFY bz_copy INDEX 1.
      ENDIF.
      APPEND LINES OF bz_copy TO bz_final.
      REFRESH bz_copy.
    ENDAT.

  ENDLOOP.

  bz[] = bz_final[].

ENDFORM.                    "check_awlin
FORM handle_trip_assignment TABLES p_int_rot_awkey STRUCTURE  ptrv_rot_awkey.
* new with GLW note 2178197: also save a basic assignment to particular trips to ptrv_rot_awkey for these
* technical split documents
*  DATA: loc_it_rot_awkey TYPE SORTED TABLE OF ptrv_rot_awkey WITH NON-UNIQUE KEY pernr reinr perio pdvrs pdvrssqno.
  DATA loc_it_rot_awkey TYPE TABLE OF ptrv_rot_awkey.
*  STATICS: mem_it_rot_awkey TYPE TABLE OF ptrv_rot_awkey.
  STATICS mem_it_rot_awkey TYPE SORTED TABLE OF ptrv_rot_awkey WITH NON-UNIQUE KEY pernr reinr perio awref. "GLW note 2211062
  DATA: wa_it_rot_awkey TYPE ptrv_rot_awkey.
  DATA: lv_seqno TYPE ptrv_rot_awkey-pdvrssqno VALUE 9999.
  DATA:  wa_rot_awkey TYPE ptrv_rot_awkey.

  LOOP AT p_int_rot_awkey INTO wa_it_rot_awkey.

    READ TABLE mem_it_rot_awkey WITH KEY
       pernr = wa_it_rot_awkey-pernr
       reinr = wa_it_rot_awkey-reinr
       perio = wa_it_rot_awkey-perio
       awref = n_awref BINARY SEARCH TRANSPORTING NO FIELDS.

    IF sy-subrc IS NOT INITIAL.

      LOOP AT mem_it_rot_awkey INTO wa_rot_awkey WHERE
          pernr = wa_it_rot_awkey-pernr AND
          reinr = wa_it_rot_awkey-reinr AND
          perio = wa_it_rot_awkey-perio AND
          pdvrs = wa_it_rot_awkey-pdvrs AND
          postvrs = wa_it_rot_awkey-postvrs.

        lv_seqno = lv_seqno - 1.
      ENDLOOP.

      wa_it_rot_awkey-awref = n_awref.
      wa_it_rot_awkey-aworg = space.
      wa_it_rot_awkey-awlin = bz_anzhl.
      wa_it_rot_awkey-pdvrssqno = lv_seqno.
      CLEAR: wa_it_rot_awkey-rot_line, wa_it_rot_awkey-waers, wa_it_rot_awkey-betrg, wa_it_rot_awkey-waers, wa_it_rot_awkey-lgart.
      APPEND wa_it_rot_awkey TO loc_it_rot_awkey.

    ENDIF.
  ENDLOOP.

  IF loc_it_rot_awkey IS NOT INITIAL.
    MODIFY ptrv_rot_awkey FROM TABLE loc_it_rot_awkey.
  ENDIF.

  INSERT LINES OF loc_it_rot_awkey INTO TABLE mem_it_rot_awkey.

ENDFORM.