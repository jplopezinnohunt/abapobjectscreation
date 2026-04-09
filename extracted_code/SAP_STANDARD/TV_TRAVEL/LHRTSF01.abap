* EhP6
* VRD_CEE_RU             CEE_RU country version retrofit RU
* EhP5
* GLWE34K020939 28122009 diff. log. systems (1420293)
* GLWE34K020704 03122009 non deductable tax and comp code(1413518)
* GLWEH5K019383 13112009 FF 753 for zero amount tax lines(1406701)
* GLWEH5K018586 06112009 default jurisdiction code only for tax comp.code(1403866)
* GLWEAJK016353 21032009 balance in trx currency(1320740)
* GLWEH4K034997 28112008 balance in transaction currency(1279848)
* MAWEH5K000613 31102008 Profit Center fehlt bei Überleitung ins FI
*                        [note 1268550]
* EHP4
* EAJEAJK014624 22092008 balance again(1227657)
* GLWP7HK031047 21052008 balance in transaction currency(1169437)
* GLWP1HK015504 27022008 0 % NAV: error when posting(1146492)
* ERP 6.03 (EHP3)
* GLWE34K002560 30082007 Balance in transaction currency upon add. doc.split(1088210)
* GLWE34K002511 29082007 Balance in transaction currency upon add. doc.split(1088210)
* ERP 6.02 ( Enhnacement Package 2 )
* WKUEAJK002090 16122007 Balance in transaction currency for
*                        posting document per CO-object (1046841)
* 6.0
* KCNPTHK000108 09082006 PRRW: F5702 Saldo in Transaktionswährung bei Profitcenter
*                        [note 971446]
* WKUP7HK006457 04042006 'zusätzlicher Belegsplit pro Kreditor' führt zu
*                        'Saldo in Transaktionswährung' (938275)
* WKUPENK015647 19052005 correction for WKUK015412 (846579)
* WKUAENK017307 26112004 Problems with BUV and PD per Receipt (795309)
* WKUAENK015412 22112004 Determine and transfer profit center (791956)
* 5.0
* WKUP3HK002027 13082004 wrong error message when FM active (764447)
* WKUP3HK000048 13052004 not postable trips cause balance       (737060)
* XCISLNK006940 07052004 error in precheck (missing gl account)(734494)
* XCIALNK152901 14012004 posting with not postable costcenter (695043)
* WKUALNK068246 29102003 correction of WKUL9CK036842 (675639)
* WKUALNK068245 29102003 several non-deductible tax lines (675550)
* 2.0
* QIZALNK044326 10022003 Busines area of sustitution must be cleared too
* WKUALNK044557 21012003 Nachkorrektur zu WKUK000523 (588847)
* 1.0
* WKUP1HK000524 24062002 filterobject determination for all BUKRS
* WKUP1HK000523 24062002 BUV-Split only if BUKRS in separate FI systems
* QIZALNK017926 14012002 USA: Problems with old trips (TXJCD -> SPACE)
* QIZALNK002508 11012002 FKBER, GRANT and FIPEX implemented
* QIZALNK017135 11012002 Search for PSREF fields improved...
* 4.6C
* WKUALNK003592 18092001 Ersatz und Verbesserung WKUK031405
* WKUL9CK036842 10012001 Handle not tax relevant taxes
* WKUL9CK023693 19092000 Nachkorrektur zu WKUK005786
* WKUL9CK018316 01082000 Segmenttext über Selektionsbild steuerbar
* WKUL9CK002818 14072000 Nachkorrektur zu WKUK000635 für Beleg pro CO-Ob
*                        keine Vertauschung von BUKRS und BUKST mehr
* WKUL9CK002817 14072000 Nachkorrektur zu WKUK000635 für Beleg pro BUKRS
* WKUL9CK002816 14072000 all clearings of CO objects in PTRV_TRANSLATE
* WKUL9CK002815 14072000 change of BUKST for clearing account posting
* WKUL9CK008344 10052000 Nachkorrektur zu WKUAHRK063502
* WBGL9CK008343 10052000 Missing SGTXT when CO-Objects substituted;
* WKUL9CK005642 28042000 übergreifende Nummer bei BUV füllen
* WKUL9CK005786 14042000 Buchung von Auslandsbelegen mit TXJCD korr.
* WBGL9CK006193 18042000 CSS 1003266 (confusing error mess.);
* WKUPH9K009891 08022000 Nachkorrektur zu K063501: sort Achim's lines
*                        correctly (at end of normal document structure)
* WKUL9BK009890 08022000 Nachkorrektur zu K001723: TXJCD-Handling
* WKUPH0K004964 21012000 Nachkorrektur zu K002096 wegen TXJCD Kanada
* WKUPH0K001723 17121999 Mehrstufiger Jurisdiction Code jetzt korrekt
* WKUPH0K000624 09121999 calculation of net from gross, not from base
* WKUAHRK065591 02121999 Do not set master cc for 2.symb.account in BUV
*                        - remove BUV lines with zero amount
* WKUAHRK063502 19111999 One posting document if BUV into one system
*                        - Make BUV-split only when multiple FI-systems
* WKUAHRK063501 17111999 Improvement of tax posting for RW-interface:
*                        - Achim's lines for NAV in case of BUV
* WKUAHRK063503 22111999 check tax and CO-objects even if empty when
*                        no clearing account and no offsetting entry
* WKUAHRK059035 15111999 Wegsaldierte SAKO-Zeilen aus Steuerzeilen
*                        mit Pfennigbeträgen rekonstruieren
* QIZAHRK054176 05081999 USA: Problems with old trips (V0 -> SPACE)
* 4.6B
* WKUPH9K021052 06101999 Nachkorrektur zu WKUK002096: Steuerzeilen mit
*                        Betrag und Basis Null nicht übergeben
* 4.6A
* WKUPH9P005705 13051999 Fehlerbehandlung bei Steuerberechnung inkorrekt
* WKUPH9K002096 05051999 Steuerzeile auch für 0% wegen Tax-Bypass
* WKKPH9K001206 30041999 Steuerreform 1999 NAV mit CO-Objekten buchen
* WKUPH9K001403 26041999 Check Buchungskreisverrechnungskonten weicher
* 4.5B
* WKUPH4K029301 04021999 Buchungskreisübergreifende Buchung mit VBUND

*---------------------------------------------------------------------*
*       INCLUDE LHRTSF01 .                                            *
*---------------------------------------------------------------------*

*---------------------------------------------------------------------*
*       FORM FILL_TABLES_FOR_POSTING_CHECKS                           *
*---------------------------------------------------------------------*
FORM fill_tables_for_posting_checks.

  DATA: accountingobjects_wbs_elemt LIKE accountingobjects-wbs_elemt,
        budat_help                  LIKE budat,
        bldat_help                  LIKE bldat.
  DATA   lv_mstext2           TYPE symsgv.      "VRD_CEE_RU 100806
  DATA   lv_mstext4           TYPE symsgv.      "VRD_CEE_RU 100806

  STATICS: l_bukrs_for_cobl_check LIKE ep_translate-bukrs,  "WKUK015412
           l_gsber_for_cobl_check LIKE ep_translate-gsber.  "WKUK015412

* handle setting of posting date and posting document date
  IF budat = '11111111'.
    budat_help = ep_translate-datv1.
  ELSEIF budat = '99999999'.
    budat_help = ep_translate-datb1.
  ELSEIF budat = '22222222'.                           "Beleg pro Beleg
    budat_help = ep_translate-beldt.                   "Beleg pro Beleg
  ELSEIF budat = '33333333'.                           "VRD_CEE_RU
    budat_help = ep_translate-umdat.   "Reference date "VRD_CEE_RU
  ELSE.
    budat_help = budat.
  ENDIF.
  IF bldat = '11111111'.
    bldat_help = ep_translate-datv1.
  ELSEIF bldat = '99999999'.
    bldat_help = ep_translate-datb1.
  ELSEIF bldat = '22222222'.                           "Beleg pro Beleg
    bldat_help = ep_translate-beldt.                   "Beleg pro Beleg
  ELSEIF bldat = '33333333'.                           "VRD_CEE_RU
    bldat_help = ep_translate-umdat.   "Reference date "VRD_CEE_RU
  ELSE.
    bldat_help = bldat.
  ENDIF.

*Begin of VRD_CEE_RU_UA 100806
  IF cl_fitv_switch_check=>ptrm_loc_sfws_01( ) = abap_true.
    IF ( bldat = '33333333' OR budat = '33333333') AND
         ep_translate-umdat IS INITIAL.
      READ TABLE ep_translate WITH KEY
                tax_item_line = tax_item_out-posnr
                bukrs         = tax_item_out-bukrs
                bukst         = tax_item_out-bukrs.
      CLEAR return_table.
      lv_mstext2 =  ep_translate-pernr.
      lv_mstext4 =  ep_translate-reinr.
      CALL FUNCTION 'BALW_BAPIRETURN_GET2'
        EXPORTING
          type   = 'E'
          cl     = '56'
          number = 016
          row    = 0
          par1   = text-d01
          par2   = lv_mstext2
          par3   = text-d02
          par4   = lv_mstext4
        IMPORTING
          return = return_table.
      APPEND return_table.
      MESSAGE ID     return_table-id
              TYPE   return_table-type
              NUMBER return_table-number
              WITH   return_table-message_v1
                     return_table-message_v2
                     return_table-message_v3
                     return_table-message_v4
              RAISING fi_customizing_error.
    ENDIF.
  ENDIF.
*End of VRD_CEE_RU_UA 100806

* fill table for and perform the open item check
  READ TABLE open_item_check
      WITH KEY bukrs = ep_translate-bukrs.
  IF sy-subrc = 0.
  ELSE.

    CALL FUNCTION 'HRCA_DC_ACTIVE_CHECK'
      EXPORTING
        i_bukrs      = ep_translate-bukrs
      IMPORTING
*             ... Finanzbudgetüberwachung aktiv?
        e_cac_active = open_item_check-cac_active
*             ... Finanzmittelrechnung aktiv?
        e_cbm_active = open_item_check-cbm_active
*             ... CO-Finanzmittelrechnung aktiv?
        e_pcm_acitve = open_item_check-pcm_acitve
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

    open_item_check-bukrs = ep_translate-bukrs.

    APPEND open_item_check.

  ENDIF.

* fill table for accumulated VAT calculation...
** if not ep_translate-mwskz is initial.  "Beleg pro CO-Obj "WKUK063503
*  if not ep_translate-mwskz is initial   "Beleg pro CO-Obj "WKUK063503
*      and ep_translate-ptype ne 'G'.     "Beleg pro CO-Obj "WKUK063503
** ...only if VAT calculation is necessary (MWSKZ exists)   "WKUK063503
  SELECT SINGLE * FROM t706d                                "WKUK063503
      WHERE morei EQ ep_translate-morei.                    "WKUK063503
* look if MOREI requires VAT                                "WKUK063503
  IF ep_translate-ptype EQ 'K'         "no offsetting entry "WKUK063503
      AND ep_translate-koart NE 'F'    "no clearing account "WKUK063503
      AND t706d-pauvs NE 'N'.          "MOREI requires VAT  "WKUK063503
    IF ep_translate-mwskz IS INITIAL.                       "WKUK005786
      PERFORM check_jurisdiction_active.                    "WKUK005786
*   ELSE.                                       "WKUK005786 "WKUK023693
*     CLEAR jurisdiction_active.                "WKUK005786 "WKUK023693
    ENDIF.                                                  "WKUK005786
*   Begin of MAW_EUVAT
    ep_translate-tax_calculation = cl_fitv_vat=>check_vat_calculation(
                                                iv_vat_changed_man  = ep_translate-vat_changed_man
                                                iv_vat_posting_type = ep_translate-vat_posting_type ).
    IF ep_translate-tax_calculation = abap_true.
*     End of MAW_EUVAT
*     IF jurisdiction_active IS INITIAL.        "WKUK005786 "WKUK023693
*      IF jurisdiction_active IS INITIAL OR                  "WKUK023693
*          NOT ep_translate-mwskz IS INITIAL.                "WKUK023693
      IF NOT ep_translate-mwskz IS INITIAL OR NOT ep_translate-txjcd IS INITIAL. "GLW note 2146374
*        READ TABLE tax_item_in
        h_subrc = 4.                                 "GLW note 1645219
        LOOP AT tax_item_in WHERE                    "GLW note 1645219
*          WITH KEY bukrs = ep_translate-bukrs       "GLW note 1645219
*              WITH KEY bukrs = ep_translate-bukst
                     bukrs = ep_translate-bukst AND    "GLW note 1645219
                     mwskz = ep_translate-mwskz AND
                     txjcd = ep_translate-txjcd AND
                     waers = ep_translate-waers AND
                     bldat = bldat_help         AND
                     budat = budat_help         AND
                     wrbtr = ep_translate-betrg AND
                     txdat = ep_translate-tax_date. "GLW note 1819167
          h_tabix = sy-tabix.                         "GLW note 1645219
          IF util->check_tax_item_ccode( iv_bukrs = ep_translate-bukrs iv_posnr = tax_item_in-posnr  ) = abap_false. "GLW note 1645219
            h_subrc = 0.                              "GLW note 1645219
            EXIT.                                     "GLW note 1645219
          ENDIF.                                      "GLW note 1645219
        ENDLOOP.                                      "GLW note 1645219
        IF h_subrc = 0.                               "GLW note 1645219
        ELSE.
          tax_item_in-posnr = tax_item_in_tabix + 1.
          util->append_tax_item_ccode( iv_bukrs = ep_translate-bukrs iv_posnr = tax_item_in-posnr ). "GLW note 1645219
*         GLWP7HK037567 begin
*         tax_item_in-bukrs = ep_translate-bukrs.
*         as in the trip only the tax codes from the master company code country can be choosen and
*         as the tax is posted to the leading company code (=master company code) anyway, also the
*         check and calculation can be done for the master.
          tax_item_in-bukrs = ep_translate-bukst.
*         GLWP7HK037567 end
          tax_item_in-mwskz = ep_translate-mwskz.
          tax_item_in-txjcd = ep_translate-txjcd.
          tax_item_in-waers = ep_translate-waers.
          tax_item_in-bldat = bldat_help.
          tax_item_in-budat = budat_help.
          tax_item_in-wrbtr = ep_translate-betrg.  "Betrag in Belegwährung
          tax_item_in-txdat = ep_translate-tax_date. "GLW note 1819167
          APPEND tax_item_in.
          tax_item_in_tabix = sy-tabix.
          h_tabix = sy-tabix.                         "GLW note 1645219
        ENDIF.
*        ep_translate-tax_item_line = sy-tabix.
        ep_translate-tax_item_line = h_tabix.         "GLW note 1645219
      ENDIF.                                                "WKUK005786
*   Begin of MAW_EUVAT
    ELSE.
*      IF jurisdiction_active IS INITIAL OR                  "WKUK023693
*          NOT ep_translate-mwskz IS INITIAL.                "WKUK023693
      IF NOT ep_translate-mwskz IS INITIAL OR NOT ep_translate-txjcd IS INITIAL. "GLW note 2146374
*        READ TABLE tax_item_in_man
        h_subrc = 4.
        LOOP AT tax_item_in_man WHERE
*            WITH KEY bukrs = ep_translate-bukrs
*            WITH KEY bukrs = ep_translate-bukst
                     bukrs = ep_translate-bukst AND
                     mwskz = ep_translate-mwskz  AND
                     txjcd = ep_translate-txjcd  AND
                     waers = ep_translate-waers  AND
                     bldat = bldat_help          AND
                     budat = budat_help          AND
                     wrbtr = ep_translate-betrg  AND
                     fwste = ep_translate-fwste AND
                     txdat = ep_translate-tax_date. "GLW note 1819167
          h_tabix = sy-tabix.                         "GLW note 1645219
          IF  util->check_tax_item_ccode( iv_bukrs = ep_translate-bukrs iv_posnr = tax_item_in_man-posnr iv_man = 'X' ) = abap_false.
            h_subrc = 0.
            EXIT.
          ENDIF.
        ENDLOOP.
        IF h_subrc = 0.
        ELSE.
          tax_item_in_man-posnr = tax_item_in_tabix_man + 1.
          util->append_tax_item_ccode( iv_bukrs = ep_translate-bukrs iv_posnr = tax_item_in_man-posnr iv_man = 'X' ).
          tax_item_in_man-bukrs = ep_translate-bukst.
          tax_item_in_man-mwskz = ep_translate-mwskz.
          tax_item_in_man-txjcd = ep_translate-txjcd.
          tax_item_in_man-waers = ep_translate-waers.
          tax_item_in_man-bldat = bldat_help.
          tax_item_in_man-budat = budat_help.
          tax_item_in_man-wrbtr = ep_translate-betrg.
          tax_item_in_man-fwste = ep_translate-fwste.
          tax_item_in_man-txdat = ep_translate-tax_date. "GLW note 1819167
          APPEND tax_item_in_man.
          tax_item_in_tabix_man = sy-tabix.
          h_tabix = sy-tabix.                         "GLW note 1645219
        ENDIF.
*        ep_translate-tax_item_line = sy-tabix.
        ep_translate-tax_item_line = h_tabix.         "GLW note 1645219
      ENDIF.                                                "WKUK005786
    ENDIF.
*   End of MAW_EUVAT
  ENDIF.

* fill table for accumulated COBL_CHECK...
*  if ep_translate-ptype ne 'G'                             "WKUK063503
*      and not (    ep_translate-kostl is initial           "WKUK063503
*               and ep_translate-aufnr is initial           "WKUK063503
*               and ep_translate-kstrg is initial           "WKUK063503
*               and ep_translate-posnr is initial           "WKUK063503
*               and ep_translate-nplnr is initial           "WKUK063503
*               and ep_translate-vornr is initial           "WKUK063503
*               and ep_translate-fipos is initial           "WKUK063503
*               and ep_translate-fistl is initial           "WKUK063503
*               and ep_translate-geber is initial           "WKUK063503
*               and ep_translate-kdauf is initial           "WKUK063503
*               and ep_translate-kdpos is initial ).        "WKUK063503
** ...when accounting objects existent                      "WKUK063503
**     (i.e. no offsetting entry and no clearing account)   "WKUK063503
* BEGIN WKUK015412
* IF ep_translate-ptype EQ 'K'         "no offsetting entry  "WKUK063503
*     AND ep_translate-koart NE 'F'.   "no clearing account  "WKUK063503
* BEGIN WKUK002090
* IF prctr_tr EQ true OR
*    ep_translate-ptype EQ 'K' AND     "no offsetting entry
*    ep_translate-koart NE 'F'.        "no clearing account
*  IF prctr_tr           EQ true.
  IF prctr_tr EQ true OR segment_tr EQ true OR  "GLW note 2926207
     bl_spl EQ 'C' OR
     ( ep_translate-ptype EQ 'K' AND   "no offsetting entry
       ep_translate-koart NE 'F' ).    "no clearing account
    IF prctr_tr EQ true OR bl_spl EQ 'C' OR segment_tr EQ true.
* END WKUK002090
      IF ep_translate-ptype EQ 'K'.
        l_bukrs_for_cobl_check = ep_translate-bukrs.
        l_gsber_for_cobl_check = ep_translate-gsber.
      ELSE.
        IF l_bukrs_for_cobl_check IS INITIAL.
          l_bukrs_for_cobl_check = ep_translate-bukrs.
        ENDIF.
        IF l_gsber_for_cobl_check IS INITIAL.
          l_gsber_for_cobl_check = ep_translate-gsber.
        ENDIF.
      ENDIF.
    ELSE.
      l_bukrs_for_cobl_check = ep_translate-bukrs.
      l_gsber_for_cobl_check = ep_translate-gsber.
    ENDIF.
* END WKUK015412
    CLEAR accountingobjects.
    WRITE ep_translate-posnr TO accountingobjects_wbs_elemt.
    READ TABLE accountingobjects
* BEGIN WKUK015412
*       WITH KEY comp_code       = ep_translate-bukrs
*                bus_area        = ep_translate-gsber
        WITH KEY comp_code       = l_bukrs_for_cobl_check
                 bus_area        = l_gsber_for_cobl_check
* END WKUK015412
                 posting_date    = budat_help
                 costcenter      = ep_translate-kostl
                 orderid         = ep_translate-aufnr
                 cost_obj        = ep_translate-kstrg
*                wbs_elemt       = ep_translate-posnr
                 wbs_elemt       = accountingobjects_wbs_elemt
                 network         = ep_translate-nplnr
                 activity        = ep_translate-vornr
                 cmmt_item       = ep_translate-fipos
                 cmmt_item_long  = ep_translate-fipex       "QIZK002508
                 funds_ctr       = ep_translate-fistl
                 fund            = ep_translate-geber
                 budget_period   = ep_translate-budget_period "XMW EhP5 Budget Period
                 func_area       = ep_translate-fkber       "QIZK002508
                 grant_nbr       = ep_translate-grant_nbr   "QIZK002508
                 sales_ord       = ep_translate-kdauf
                 s_ord_item      = ep_translate-kdpos
                 costcenter_empl = ep_translate-kstst
                 co_busproc      = ep_translate-prznr
                 res_doc         = ep_translate-kblnr
                 res_item        = ep_translate-kblpos
                 compl_ind       = ep_translate-erlkz
                 bus_area_empl   = ep_translate-gsbst.
    IF sy-subrc = 0.
    ELSE.
* BEGIN WKUK015412
*     accountingobjects-comp_code       = ep_translate-bukrs.
*     accountingobjects-bus_area        = ep_translate-gsber.
      accountingobjects-comp_code       = l_bukrs_for_cobl_check.
      accountingobjects-bus_area        = l_gsber_for_cobl_check.
* END WKUK015412
      accountingobjects-posting_date    = budat_help.
      accountingobjects-costcenter      = ep_translate-kostl.
      accountingobjects-co_busproc      = ep_translate-prznr.
      accountingobjects-res_doc         = ep_translate-kblnr.
      accountingobjects-res_item        = ep_translate-kblpos.
      accountingobjects-compl_ind       = ep_translate-erlkz.
      accountingobjects-orderid         = ep_translate-aufnr.
      accountingobjects-cost_obj        = ep_translate-kstrg.
*     accountingobjects-wbs_elemt       = ep_translate-posnr.
      WRITE ep_translate-posnr TO accountingobjects-wbs_elemt.
      accountingobjects-network         = ep_translate-nplnr.
      accountingobjects-activity        = ep_translate-vornr.
      accountingobjects-cmmt_item       = ep_translate-fipos.
      accountingobjects-cmmt_item_long  = ep_translate-fipex. "QIZK002508
      accountingobjects-funds_ctr       = ep_translate-fistl.
      accountingobjects-fund            = ep_translate-geber.
      accountingobjects-budget_period   = ep_translate-budget_period. "XMW EhP5 Budget Period
      accountingobjects-func_area       = ep_translate-fkber. "QIZK002508
      accountingobjects-grant_nbr   = ep_translate-grant_nbr. "QIZK002508
      accountingobjects-sales_ord       = ep_translate-kdauf.
      accountingobjects-s_ord_item      = ep_translate-kdpos.
      accountingobjects-costcenter_empl = ep_translate-kstst.
      accountingobjects-bus_area_empl   = ep_translate-gsbst.
      APPEND accountingobjects.
    ENDIF.
    ep_translate-cobl_check_line = sy-tabix.
  ENDIF.

* handle reading of T030 for posting document split account in BUKST
  momagkomok+0(1) = ep_translate-momag.
  momagkomok+1(2) = ep_translate-komok.
  PERFORM administrate_fi_acct_det_hr
      USING momagkomok
            ep_translate-bukrs
            ep_translate-ktosl
            ep_translate-pernr
            fi_acct_det_hr_append_flag
            tabix.

  IF fi_acct_det_hr-konto = fi_acct_det_hr-hnkto.
    accts_are_equal = 'X'.
  ENDIF.

* debit side account is determined dynamically (pers. vendor/customer)
  IF fi_acct_det_hr-konto(1) = '*'.
    PERFORM fill_vend_cust_check_tables
        USING fi_acct_det_hr-konto+2(1).
  ENDIF.

* credit side account is determined dynamically (pers. vendor/customer)
  IF fi_acct_det_hr-hnkto(1) = '*'.
    IF accts_are_equal EQ 'X'.
      fi_acct_det_hr-hnkto = fi_acct_det_hr-konto.
    ELSE.
      IF fi_acct_det_hr-pernr IS INITIAL.
        fi_acct_det_hr-pernr = ep_translate-pernr.
      ENDIF.
      PERFORM fill_vend_cust_check_tables
          USING fi_acct_det_hr-hnkto+2(1).
    ENDIF.
  ENDIF.

  IF fi_acct_det_hr_append_flag = 'X'.
    APPEND fi_acct_det_hr.
    tabix = sy-tabix.
  ENDIF.

  ep_translate-acc_det_line = tabix.

  READ TABLE filterobjects_values                           "WKUK000524
      WITH KEY objvalue = ep_translate-bukrs.               "WKUK000524
  IF sy-subrc NE 0.                                         "WKUK000524
    filterobjects_values-objtype = 'COMP_CODE'.             "WKUK000524
    filterobjects_values-objvalue = ep_translate-bukrs.     "WKUK000524
    APPEND filterobjects_values.                            "WKUK000524
  ENDIF.                                                    "WKUK000524

ENDFORM.                               "FILL_TABLES_FOR_POSTING_CHECKS

*---------------------------------------------------------------------*
*       FORM POSTING_CHECKS                                           *
*---------------------------------------------------------------------*
FORM posting_checks.
  DATA: tax_item_index LIKE sy-tabix.

*   Begin of MAW_EUVAT
  DATA   lt_tax_item_out_man  LIKE rtax1u38   OCCURS 0 WITH HEADER LINE.
  DATA   lt_tax_errors_man    LIKE bapiret2   OCCURS 0 WITH HEADER LINE.
  DATA   ls_tax_item_man      TYPE rtax1u38.
  DATA   ls_tax_man_help      TYPE cl_fitv_vat=>ts_tax_man_help.
  DATA   lt_tax_man_help      TYPE cl_fitv_vat=>tt_tax_man_help.
  DATA   lv_ale_error         TYPE abap_bool VALUE abap_false.
  DATA   lv_tax_line          TYPE sy-tabix.
  DATA   lv_count             TYPE sy-tabix.

  FIELD-SYMBOLS
         <ls_tax_item_man>    TYPE rtax1u38.
  FIELD-SYMBOLS
         <ls_ep_translate>    TYPE ts_ep_translate.
  FIELD-SYMBOLS
         <ls_tax_man_help>    TYPE cl_fitv_vat=>ts_tax_man_help.
* End of MAW_EUVAT

  CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
    EXPORTING
      text = text-p02.

* Accumulated VAT calculation
  CALL FUNCTION 'HRCA_CALCULATE_TAXES_GROSS'
    TABLES
      tax_item_in  = tax_item_in
      tax_item_out = tax_item_out
      return       = tax_errors
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

* GLWE34K020704 begin
* first read the tax data with the leading comp code and then reset the comp code again for the
* not deductible tax lines!
  LOOP AT tax_item_out.
    ADD 1 TO tax_item_index.
    READ TABLE ep_translate WITH KEY
      tax_item_line = tax_item_out-posnr
      bukrs         = tax_item_out-bukrs
      bukst         = tax_item_out-bukrs TRANSPORTING NO FIELDS.
    IF sy-subrc IS NOT INITIAL.
      READ TABLE ep_translate WITH KEY
       tax_item_line = tax_item_out-posnr TRANSPORTING bukrs.
      IF sy-subrc IS INITIAL AND tax_item_out-stazf = abap_true.
        MOVE ep_translate-bukrs TO tax_item_out-bukrs.
        MODIFY tax_item_out INDEX tax_item_index TRANSPORTING bukrs.
      ENDIF.
    ENDIF.
    cl_fitv_posting_util=>check_rounding( CHANGING c_tax_item_out = tax_item_out ).    "GLW note 1599200
    MODIFY tax_item_out INDEX tax_item_index TRANSPORTING fwbas fwste.                  "GLW note 1599200
  ENDLOOP.
* GLWE34K020704 end

  CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
    EXPORTING
      text = text-p03.

* Begin of MAW_EUVAT
  CLEAR lt_tax_item_out_man.
  CLEAR lt_tax_errors_man.
  CLEAR return_table.

  REFRESH lt_tax_item_out_man.
  REFRESH lt_tax_errors_man.
  REFRESH return_table.
*
  CALL METHOD cl_fitv_vat=>build_tax_help_table
    IMPORTING
      et_tax_man_help    = lt_tax_man_help[]
    CHANGING
      ct_tax_item_in_man = tax_item_in_man[].
*
* Calculate the VAT
  CALL FUNCTION 'HRCA_CALCULATE_TAXES_GROSS'
    TABLES
      tax_item_in  = tax_item_in_man
      tax_item_out = lt_tax_item_out_man
      return       = lt_tax_errors_man
      return_table = return_table.
*
  READ TABLE return_table INDEX 1.
  IF sy-subrc = 0.
    lv_ale_error = abap_true.
    EXIT.
  ENDIF.
*
  IF lv_ale_error = abap_true.
    MESSAGE ID     return_table-id
            TYPE   return_table-type
            NUMBER return_table-number
            WITH   return_table-message_v1
                   return_table-message_v2
                   return_table-message_v3
                   return_table-message_v4
            RAISING ale_communication_error.
  ENDIF.
*
  CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
    EXPORTING
      text = text-p03.
*
* now we have to merge the table tax_item_out_man into tax_item_out
* adapting the field tax_item_line.
  lv_tax_line = lines( tax_item_in ).
  LOOP AT ep_translate ASSIGNING <ls_ep_translate>
                           WHERE tax_calculation = abap_false.
    CALL METHOD cl_fitv_vat=>merge_tax_item
      EXPORTING
        it_tax_man_help     = lt_tax_man_help
      CHANGING
        cv_tax_line_counter = lv_tax_line
        cv_ep_tax_item_line = <ls_ep_translate>-tax_item_line
        ct_tax_item_out     = tax_item_out[]
        ct_tax_item_out_man = lt_tax_item_out_man[]
        ct_tax_item_in      = tax_item_in[]
        ct_tax_item_in_man  = tax_item_in_man[].
  ENDLOOP.
* End of MAW_EUVAT

* XCIK006940 begin
  LOOP AT accountingobjects.
    accountingobjects-obj_typ_p = 'TRAVL'.
    MODIFY accountingobjects.
  ENDLOOP.
* XCIK006940 end

* Accumulated COBL-PRECHECK
*  CALL FUNCTION 'HRCA_CODINGBLOCK_PRECHECK_HR'
*    TABLES
*      accountingobjects = accountingobjects
*      return            = cobl_errors
*      return_table      = return_table.

  cl_fitv_posting_util=>co_precheck(
    IMPORTING
      return            = cobl_errors[]
      return_table      = return_table[]
    CHANGING
      accountingobjects = accountingobjects[] ).

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

  CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
    EXPORTING
      text = text-p04.

* accumulated customer check
  CALL FUNCTION 'HRCA_FIND_CUSTOMER_FOR_PERSNO'
    TABLES
      selopt_tab   = customer_selopt_tab
      result_tab   = customer_result_tab
      return_table = return_table
    EXCEPTIONS
      OTHERS       = 0.

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

  CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
    EXPORTING
      text = text-p05.

* accumulated vendor check
  CALL FUNCTION 'HRCA_FIND_VENDOR_FOR_PERSNO'
    TABLES
      selopt_tab   = vendor_selopt_tab
      result_tab   = vendor_result_tab
      return_table = return_table
    EXCEPTIONS
      OTHERS       = 0.

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

ENDFORM.                               "POSTING_CHECKS

*---------------------------------------------------------------------*
*       FORM COLLECT_PSREF_FIELDS.                                    *
*---------------------------------------------------------------------*
FORM collect_psref_fields TABLES psref_fields STRUCTURE psref_fields.
  CLEAR   psref_fields.
  REFRESH psref_fields.

* QIZK017135 begin...
  DATA: BEGIN OF psref_dfies_tab OCCURS 50.
          INCLUDE STRUCTURE dfies.
  DATA: END OF psref_dfies_tab.
* Alle Felder aus der Struktur PSREF sammeln

  CALL FUNCTION 'DDIF_FIELDINFO_GET'
    EXPORTING
*     tabname        = 'PSREF'                              "AKAK011844
      tabname        = 'PTRV_PSREF'                         "AKAK011844
    TABLES
      dfies_tab      = psref_dfies_tab
    EXCEPTIONS
      not_found      = 1
      internal_error = 2
      OTHERS         = 3.

  IF sy-subrc <> 0.
* should not occurr...
  ENDIF.

  LOOP AT psref_dfies_tab.
    psref_fields-field = psref_dfies_tab-fieldname.
    psref_fields-text  = psref_dfies_tab-fieldtext.
    APPEND psref_fields.
  ENDLOOP.

*  SELECT * FROM dd03l WHERE tabname EQ 'PSREF'
*                      AND   as4local  EQ 'A'.
*    psref_fields-field = dd03l-fieldname.
*    SELECT * FROM dd04t WHERE rollname EQ dd03l-rollname AND
*                              ddlanguage EQ syst-langu   AND
*                              as4local   EQ 'A'.
*      psref_fields-text = dd04t-scrtext_l.
*      EXIT.
*    ENDSELECT.
*    APPEND psref_fields.
*  ENDSELECT.

* QIZK017135 end...

ENDFORM.                               "COLLECT_PSREF_FIELDS

*---------------------------------------------------------------------*
*       FORM BUILD_EPK_FROM_EP                                        *
*---------------------------------------------------------------------*
FORM build_epk_from_ep.

*  data: allocatable_tax like tax_item_out-fwbas,            WKUK000624
  DATA: bukrs_save    LIKE epk-bukrs,
        gsber_save    LIKE epk-gsber,
        epk_field(24).

* DATA bukrs LIKE epk-bukrs.                                "WKUK002818

  DATA: tax_item_out_lines LIKE sy-tabix,                   "WKUK004964
        act_tabix          LIKE sy-tabix.                   "WKUK004964

  DATA: store_ep_line LIKE epk-ep_line.                     "WKUK009891

  DATA: epk_store LIKE epk.                                 "WKUK068245

  FIELD-SYMBOLS <f>.

  DESCRIBE TABLE ep_translate LINES table_lines.

  LOOP AT ep_translate.

    IF table_lines GE 20.
      rest = sy-tabix MOD ( table_lines / 20 ).
      IF rest = 0.
        percentage = sy-tabix / ( table_lines / 20 ) * 5.
        CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
          EXPORTING
            percentage = percentage
            text       = text-p06.
      ENDIF.
    ENDIF.

    CLEAR: epk,
           no_append_flag.

    MOVE-CORRESPONDING ep_translate TO wa_ep_translate.

    CHECK wa_ep_translate-betrg <> 0.

    MOVE-CORRESPONDING wa_ep_translate TO epk.       "Kontierung
    epk-mandt = sy-mandt.
    epk-sexbl = wa_ep_translate-exbel. "Sortierfeld füllen
    epk-smwkz = wa_ep_translate-mwskz. "Sortierfeld füllen
    epk-stxjc_deep = wa_ep_translate-txjcd. "Sortierfeld füllen
    epk-stxjc = wa_ep_translate-txjcd. "Sortierfeld füllen
    epk-pernr_store = wa_ep_translate-pernr.
    epk-reinr_store = wa_ep_translate-reinr.
    CLEAR: epk-exbel,                  "Feld zur Sortierung löschen
           epk-mwskz,                  "Feld zur Sortierung löschen
           epk-txjcd.                  "Feld zur Sortierung löschen
* remove master cost account, business area and KOKEY  "Verdichtung
    CLEAR: epk-kstst,                  "Verdichtung
           epk-gsbst,                  "Verdichtung
           epk-kokey.                  "Verdichtung
    epk-tax_line = 0.

    PERFORM re001
        USING   epk-bukrs              "eingegebener Bukrs
                epk-bukst.             "GLWEH5K018586

* VRD_CEE_RU begin RU-Version - negative posting
    IF cl_glo_vs_check=>negative_posting( epk-bukrs ) = abap_true.
      IF epk-antrg = '4' AND
         epk-abrec = '3'.
        epk-xnegp = 'X'.
      ENDIF.
    ENDIF.
* VRD_CEE_RU end RU-Version - negative posting

    IF epk-ptype = 'K'.
* Einzelposten ist Aufwandsbuchung (auf Kostenkonto)
* QIZK054176 begin...
      IF t706d-morei NE wa_ep_translate-morei.
        SELECT SINGLE * FROM t706d WHERE morei EQ wa_ep_translate-morei.
        IF sy-subrc NE 0.
          CLEAR t706d.
        ENDIF.
      ENDIF.
      IF t706d-molga EQ '10'.
        CLEAR epk-smwkz.               "no VAT-Code possible
        CLEAR epk-stxjc. "... and also no jurisdiction code "QIZK017926
        CLEAR epk-stxjc_deep.                               "QIZK017926
      ENDIF.
* QIZK054176 end...
* BEGIN WKUK029301 nach oben verlagertes Coding
* EP-GSBER only if GSBER_A is not initial.
      IF gsber_a = 'X'.
        IF NOT ( wa_ep_translate-gsbst IS INITIAL ) AND
               ( wa_ep_translate-gsber IS INITIAL ).
          IF wa_ep_translate-koart <> 'F'.
            IF epk-bukst = epk-bukrs.
* nur wenn kein abweichender Buchungskreis...
              epk-gsber = wa_ep_translate-gsbst.
            ENDIF.
          ENDIF.
        ENDIF.
      ELSE.
        CLEAR epk-gsber.
      ENDIF.
* END WKUK029301 nach oben verlagertes Coding

* BEGIN DELETION for WKUK002818
*      IF bl_spl = 'C'.
** when accounting document is per CO object:
*
** 1. PTYPE of G/L-account must be turned to sort these lines before the
** vendor lines in table EPK
*        epk-ptype = 'A'.
** 2. master company code must be turned into company code in case of
** difference and this code must be stored for the vendor line
*        IF epk-bukrs NE epk-bukst.
*          bukrs = epk-bukrs.
*          epk-bukst = epk-bukrs.
*        ELSE.
*          CLEAR bukrs.
*        ENDIF.
*      ENDIF.
* END DELETION for WKUK002818

* BEGIN QIZK017926
* when vat code filled but jurisdiction code empty and jurisdiction code
* available in T001, then fill ite has a TXJCD
*     if epk-txjcd is initial and not t001_txjcd is initial.
      IF NOT epk-smwkz IS INITIAL AND
             epk-stxjc IS INITIAL AND NOT t001_txjcd IS INITIAL.
* no TXJCD in trip but companycode has a TXJCD
*       epk-txjcd = t001_txjcd.
        epk-stxjc = epk-stxjc_deep = t001_txjcd.
* END QIZK017926
      ENDIF.

* BEGIN WKUK029301 Coding nach oben verlagert
** EP-GSBER only if GSBER_A is not initial.
*      IF GSBER_A = 'X'.
*        IF NOT ( WA_EP_TRANSLATE-GSBST IS INITIAL ) AND
*               ( WA_EP_TRANSLATE-GSBER IS INITIAL ).
*          IF WA_EP_TRANSLATE-KOART <> 'F'.
*            IF EPK-BUKST = EPK-BUKRS.
** nur wenn kein abweichender Buchungskreis
*              EPK-GSBER = WA_EP_TRANSLATE-GSBST.
*            ENDIF.
*          ENDIF.
*        ENDIF.
*      ELSE.
*        CLEAR EPK-GSBER.
*      ENDIF.
* END WKUK029301 Coding nach oben verlagert

* Besinnungsaufsatz zur Buchungszeilenverdichtung:
* Damit bei Sortierung der Tabelle EPK die Gegenbuchungszeilen immer vor
* den Aufwandsbuchungszeilen stehen, dürfen Personalnummer und
* Reisenummer nur initialisiert werden, wenn der Verdichtungsgrad der
* Gegenbuchungszeile gleich oder größer dem Verdichtungsgrad der
* Aufwandsbuchungszeile ist. Wenn der Verdichtungsgrad der
* Gegenbuchungszeile kleiner als der Verdichtungsgrad der
* Aufwandsbuchungszeile ist, müssen Personalnummer bzw. Reisenummer
* in der Aufwandsbuchungszeile maximal gesetzt werden, damit sie auf
* jeden Fall größer als die der Gegenbuchungszeile ist und die
* Gegenbuchungszeile auch jetzt nach vorne sortiert wird.
      IF epk-belnr+0(1) = 'V' AND a_verd NE 'Q'.  "GLW note 2520560
* nothing
      ELSE.
        CASE a_verd.                     "Verdichtung Aufwandszeile
          WHEN 'Q'.                      "pro Beleg      "Beleg pro Beleg
* keine Aktion nötig, da REINR, PERNR und BELNR bereits auf EPK
          WHEN 'R'.                      "pro Reise
* keine Aktion nötig, da Reisenummer und Personalnummer bereits auf EPK
            CLEAR epk-belnr.                             "Beleg pro Beleg
          WHEN 'P'.                      "pro Pernr
            IF g_verd = 'R'              "Verdichtung Gegenzeile kleiner
                OR g_verd = 'Q'                          "Beleg pro Beleg
                AND bl_spl NE 'C'.
              epk-sexbl = max_exbel.     "Reisenummer auf Maximum setzen
              epk-belnr = max_belnr.                     "Beleg pro Beleg
            ELSE.
              CLEAR epk-sexbl.           "Reisenummer initialisien
              CLEAR epk-belnr.                           "Beleg pro Beleg
            ENDIF.
* all trip specific informations have to be deleted
            CLEAR: epk-sgtxt,            "Segmenttext lös"Beleg pro CO-Obj
                   epk-datv1,
                   epk-datb1,
                   epk-begda,
                   epk-endda,
                   epk-antrg,
                   epk-abrec.
          WHEN 'K'.                      "pro Kostenstelle/Auftrag/Projekt
* BEGIN Beleg pro Beleg
*         IF ( g_verd = 'R' OR g_verd = 'P' ) "Verdichtung Gegenzeile kl
            IF ( g_verd = 'R' OR g_verd = 'P' OR g_verd = 'Q' )
* END Beleg pro Beleg
                AND bl_spl NE 'C'.
              epk-sexbl = max_exbel.     "Reisenummer auf Maximum setzen
              epk-pernr = max_pernr.    "Personalnummer auf Maximum setzen
              epk-belnr = max_belnr.                     "Beleg pro Beleg
            ELSE.
              CLEAR epk-sexbl.           "Reisenummer löschen
              CLEAR epk-pernr.           "Personalnr. löschen
              CLEAR epk-belnr.                           "Beleg pro Beleg
            ENDIF.
* all trip specific informations have to be deleted
            CLEAR: epk-sgtxt,            "Segmenttext löschen
                   epk-datv1,
                   epk-datb1,
                   epk-begda,
                   epk-endda,
                   epk-antrg,
                   epk-abrec.
        ENDCASE.
      ENDIF.

    ELSEIF epk-ptype = 'G'.
* Einzelposten ist Gegenbuchung zur Aufwandsbuchung
* (auf Kontokorrentkonto/Verrechnungskonto)
* MANDT, BUPJM, PABRJ, PABRP, ABKRS...   bleiben gleich.
* BEGIN DELETION for WKUK002818
*      IF bl_spl = 'C'.
** when accounting document is per CO object...
*
** ...master company code of vendor line must be turned into stored
** company code of G/L account line when for that line company code was
** not equal to master company code
*        IF NOT bukrs IS INITIAL.
*          epk-bukst = bukrs.
*          CLEAR bukrs.
*        ENDIF.
*        CLEAR: epk-smwkz,
*               epk-txjcd.
*      ENDIF.
* END DELETION for WKUK002818

*      WBG Hotline 163914: Buchen mit/ohne G.bereich fkt. nicht;
*      Überflüssig, da WA_EP_TRANSLATE-GSBER immer leer
*      IF NOT GSBER_G IS INITIAL.
*        EPK-GSBER = WA_EP_TRANSLATE-GSBER.
*      ENDIF.
      IF wa_ep_translate-belnr+0(1) = 'V' AND g_verd NE 'X'.
        epk-belnr = wa_ep_translate-belnr.           "Beleg pro Beleg
        epk-sexbl = wa_ep_translate-exbel.           "Beleg pro Beleg
        epk-pernr = wa_ep_translate-pernr.
      ELSE.
        CASE g_verd.                     "Verdichtung
          WHEN 'Q'.                                      "Beleg pro Beleg
            epk-belnr = wa_ep_translate-belnr.           "Beleg pro Beleg
            epk-sexbl = wa_ep_translate-exbel.           "Beleg pro Beleg
            epk-pernr = wa_ep_translate-pernr.           "Beleg pro Beleg
          WHEN 'R'.                      "pro Reise
            CLEAR epk-belnr.                             "Beleg pro Beleg
            epk-sexbl = wa_ep_translate-exbel.
            epk-pernr = wa_ep_translate-pernr.
          WHEN 'P'.                      "pro Pernr
            IF a_verd = 'R'              "Verdichtung Geg
               AND bl_spl = 'C'.
              epk-sexbl = max_exbel.     "Reisenummer auf Maximum setzen
              epk-belnr = max_belnr.                     "Beleg pro Beleg
            ELSE.
              CLEAR epk-sexbl.           "Reisenummer i
              CLEAR epk-belnr.                           "Beleg pro Beleg
            ENDIF.
* all trip specific informations have to be deleted
            CLEAR: epk-sgtxt,            "Segmenttext lös
                   epk-datv1,
                   epk-datb1,
                   epk-begda,
                   epk-endda,
                   epk-antrg,
                   epk-abrec.
          WHEN 'K'.                      "pro Kostenstell
* BEGIN Beleg pro Beleg
*         IF ( a_verd = 'R' OR a_verd = 'P' ) "Zeile pro Reise oder Pers
            IF ( a_verd = 'R' OR a_verd = 'P' OR a_verd = 'Q' )
* END Beleg pro Beleg
                AND bl_spl = 'C'.
              epk-sexbl = max_exbel.     "Reisenummer auf Maximum setzen
              epk-pernr = max_pernr.    "Personalnummer auf Maximum setzen
              epk-belnr = max_belnr.                     "Beleg pro Beleg
            ELSE.
              CLEAR epk-sexbl.           "Reisenummer löschen
              CLEAR epk-pernr.           "Personalnr. löschen
              CLEAR epk-belnr.                           "Beleg pro Beleg
            ENDIF.
* all trip specific informations have to be deleted
            CLEAR: epk-sgtxt,            "Segmenttext löschen
                   epk-datv1,
                   epk-datb1,
                   epk-begda,
                   epk-endda,
                   epk-antrg,
                   epk-abrec.
        ENDCASE.
      ENDIF.
    ENDIF.

* analyse open item check results
    READ TABLE open_item_check
        WITH KEY bukrs = wa_ep_translate-bukrs.
    IF NOT open_item_check-cac_active IS INITIAL.
*     IF NOT ( a_verd = 'R' AND g_verd = 'R' ).             "WKUK002027
      IF bl_spl NE 'R'.                                     "WKUK002027
        CLEAR wa_bapiret2.
        brlin = 1.
* create open item error message for post_result
        par1 = open_item_check-bukrs.
        CALL FUNCTION 'BALW_BAPIRETURN_GET2'
          EXPORTING
            type   = 'E'
            cl     = '56'
*           number = '861'                                  "WKUK002027
*           par1   = par1                                   "WKUK002027
            number = '563'                                  "WKUK002027
            row    = 0
          IMPORTING
            return = wa_bapiret2.

        PERFORM administrate_post_result USING 'X' ' '.

      ENDIF.

    ENDIF.

* analyse VAT calculation results
*   READ TABLE TAX_ITEM_OUT                                 "WKUK005705
*       WITH KEY POSNR = WA_EP_TRANSLATE-TAX_ITEM_LINE.     "WKUK005705
*   IF NOT TAX_ITEM_OUT-ERROR IS INITIAL.                   "WKUK005705
* tax item errors occurred
    brlin = 1.
*     LOOP AT TAX_ERRORS WHERE ROW = TAX_ITEM_OUT-POSNR.    "WKUK005705
    LOOP AT tax_errors                                      "WKUK005705
       WHERE row = wa_ep_translate-tax_item_line.           "WKUK005705
      CLEAR wa_bapiret2.
      MOVE-CORRESPONDING tax_errors TO wa_bapiret2.

      PERFORM administrate_post_result USING 'X' ' '.

      brlin = brlin + 1.

    ENDLOOP.

*   ENDIF.                                                  "WKUK005705

* analyse cobl_check results
    CLEAR accountingobjects.
    READ TABLE accountingobjects
        INDEX wa_ep_translate-cobl_check_line.
    IF wa_ep_translate-ktosl EQ 'HRP' OR wa_ep_translate-ptype EQ 'G' OR wa_ep_translate-koart EQ 'F' OR  wa_ep_translate-ktosl EQ 'HRV'. "GLW note 2379656
      MOVE accountingobjects-profit_ctr TO epk-prctr.  "GLWEH5K028190
      MOVE accountingobjects-segment TO epk-segment. "GLW note 2926207
    ENDIF.
    IF sy-subrc EQ 0 AND ( wa_ep_translate-ktosl NE 'HRP' AND wa_ep_translate-ktosl NE 'HRV' AND wa_ep_translate-ptype NE 'G' AND wa_ep_translate-koart NE 'F' ). "don't analyze CO check result for not CO relevant posting lines
      "GLWEH5K028190  "GLW note 2379656
      CLEAR: cobl_errors,
             post_result,
             append_replace_line,
             append_error_line.
      brlin = 1.
* bring cobl_check messages to result table
      LOOP AT cobl_errors
          WHERE row = wa_ep_translate-cobl_check_line.
        CLEAR wa_bapiret2.
* transport cobl error messages
        MOVE-CORRESPONDING cobl_errors TO wa_bapiret2.
* error sign in result table only when cobl_check error
        IF NOT replace IS INITIAL.
* substitution procedure wanted.
          IF accountingobjects-result = '3'.

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
        CASE accountingobjects-result.
          WHEN '0'.
* posting to accounting object is possible, no action necessary"WKU_TUNE
          WHEN '1'.
* substitution of accounting object by employee cost center possible
            LOOP AT psref_fields.
              CHECK psref_fields-field <> 'SGTXT'. "#EC NOTEXT"WBGK008343
              CHECK psref_fields-field <> 'EXBEL'. "#EC NOTEXT"WBGK008343
              CHECK psref_fields-field <> 'FISTL'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'FIPOS'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'GEBER'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'FIPEX'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'FKBER'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'GRANT_NBR'. "#EC NOTEXT"152901
              epk_field(4) = 'EPK-'.
              epk_field+4(20) = psref_fields-field.
              ASSIGN (epk_field) TO <f>.
              CLEAR <f>.
            ENDLOOP.
            MOVE: epk-bukst                         TO epk-bukrs,
                  accountingobjects-bus_area_empl   TO epk-gsber,
                  accountingobjects-costcenter_empl TO epk-kostl.
            IF gsber_a = 'X'.                               "QIZK044326
* nothing to do...                                          "QIZK044326
            ELSE.                                           "QIZK044326
              CLEAR epk-gsber.                              "QIZK044326
            ENDIF.                                          "QIZK044326
* message in result table about successful substitution
            IF append_replace_line = 'X'.
              PERFORM clear_post_result_bapiret2.
              post_result-brlin = post_result-brlin + 1.
              CLEAR wa_bapiret2.
              par1 = accountingobjects-costcenter_empl.
              row  = wa_ep_translate-cobl_check_line.
              CALL FUNCTION 'BALW_BAPIRETURN_GET2'
                EXPORTING
                  type   = 'R'
                  cl     = '56'
                  number = '851'
                  par1   = par1
                  row    = row
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
              CHECK psref_fields-field <> 'SGTXT'. "#EC NOTEXT"WBGK008343
              CHECK psref_fields-field <> 'EXBEL'. "#EC NOTEXT"WBGK008343
              CHECK psref_fields-field <> 'FISTL'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'FIPOS'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'GEBER'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'FIPEX'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'FKBER'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'GRANT_NBR'. "#EC NOTEXT"152901
              epk_field(4) = 'EPK-'.
              epk_field+4(20) = psref_fields-field.
              ASSIGN (epk_field) TO <f>.
              CLEAR <f>.
            ENDLOOP.
            MOVE: bukrs_save                           TO epk-bukrs,
                  gsber_save                           TO epk-gsber,
                  accountingobjects-costcenter_default TO epk-kostl.
* message in result table about successful substitution
            IF append_replace_line = 'X'.
              PERFORM clear_post_result_bapiret2.
              post_result-brlin  = post_result-brlin + 1.
              CLEAR wa_bapiret2.
              par1 = accountingobjects-costcenter_default.
              row  = wa_ep_translate-cobl_check_line.
              CALL FUNCTION 'BALW_BAPIRETURN_GET2'
                EXPORTING
                  type   = 'R'
                  cl     = '56'
                  number = '852'
                  par1   = par1
                  row    = row
                IMPORTING
                  return = wa_bapiret2.
              MOVE-CORRESPONDING wa_bapiret2 TO post_result.
              APPEND post_result.
            ENDIF.
          WHEN '3'.
* everything done already
        ENDCASE.
      ENDIF.
*     IF prctr_tr IS NOT INITIAL.               "KCNK000108 "MAWK000613
      MOVE accountingobjects-profit_ctr TO epk-prctr.       "WKUK015412
      MOVE accountingobjects-segment TO epk-segment. "GLW note 2926207
*     ENDIF.                                    "KCNK000108 "MAWK000613
    ENDIF.

* analyse fi_acct_det_hr and vendor/customer-checks
    CLEAR fi_acct_det_hr.
    READ TABLE fi_acct_det_hr
        INDEX wa_ep_translate-acc_det_line.
    IF ( fi_acct_det_hr-konto IS INITIAL AND
       fi_acct_det_hr-hnkto IS INITIAL )
       OR fi_acct_det_hr-slbsl IS INITIAL                   "WBGK006193
       OR fi_acct_det_hr-hnbsl IS INITIAL.                  "WBGK006193

* Error in account determination in table T030 or ...
      CLEAR wa_bapiret2.

      brlin = 1.
* create account determination error message for post_result
      CONCATENATE fi_acct_det_hr-bukrs
                  fi_acct_det_hr-ktosl
                  fi_acct_det_hr-momagkomok
          INTO wa_bapiret2-message_v1
          SEPARATED BY ' '.
      par2 = wa_bapiret2-message_v1.
      CALL FUNCTION 'BALW_BAPIRETURN_GET2'
        EXPORTING
          type   = 'E'
          cl     = '56'
          number = '001'
          par1   = 'T030'
          par2   = par2
          row    = 0
        IMPORTING
          return = wa_bapiret2.

      PERFORM administrate_post_result USING 'X' ' '.

* begin WBGK006193;
* Error in account determination in table T030B;
      CLEAR wa_bapiret2.

      brlin = 2.
* create account determination error message for post_result
      par2 = fi_acct_det_hr-ktosl.
      CALL FUNCTION 'BALW_BAPIRETURN_GET2'
        EXPORTING
          type   = 'E'
          cl     = '56'
          number = '001'
          par1   = 'T030B'
          par2   = par2
          row    = 0
        IMPORTING
          return = wa_bapiret2.

      PERFORM administrate_post_result USING 'X' ' '.
* end WBGK006193;

    ELSE.
      CASE fi_acct_det_hr-koart.
        WHEN 'K'.
* Vendor could be checked, evaluate check result.

          PERFORM evaluate_vendor_customer_check
              TABLES vendor_result_tab.

        WHEN 'D'.
* Customer could be checked, evaluate check result.

          PERFORM evaluate_vendor_customer_check
              TABLES customer_result_tab.

      ENDCASE.
    ENDIF.

    IF t_ptrv_rot_ep_lines GE 2.
* PTRV_ROT_EP more than one line, i.e PTRV_TRANSLATE called from >=4.0C
* lines with errors in VAT calculation, cobl_check or
* account check are not appended to epk
      CHECK no_append_flag IS INITIAL.
    ENDIF.

* BEGIN WKUK000624
* Net amount is gross amount minus taxes, so do no longer try to
* calculate net amount from tax base amount (it may be not unique for
* multi-level taxes) ...
* BEGIN DELETE OLD CALCULATION
*    clear allocatable_tax.
** look if allocatable tax exists (mostly when non-deductible)
*    loop at tax_item_out
*        where posnr = wa_ep_translate-tax_item_line
*          and stbkz = '3'.     "tax is allocatable to G/L-account
** when so, sum up allocatable tax
*      allocatable_tax = allocatable_tax + tax_item_out-fwste.
*    endloop.
** when allocatable tax exists
*    if sy-subrc = 0.
** sum net amount and allocatable tax from VAT calculation to EPK-BETRG
*      epk-betrg = tax_item_out-fwbas + allocatable_tax.
** when no allocatable tax exists
*    else.
** fill net amount from VAT calculation to EPK-BETRG
*      read table tax_item_out
*          with key posnr = wa_ep_translate-tax_item_line.
*      if sy-subrc = 0.
*        epk-betrg = tax_item_out-fwbas."Nettobetrag in EPK
*      endif.
*    endif.
* END DELETE OLD CALCULATION
* ... but subtract all taxes beside the non deductible but allocatable
*  ones from gross amount, that's the net amount!!!
* BEGIN INSERT NEW CALCULATION
    LOOP AT tax_item_out
        WHERE posnr = wa_ep_translate-tax_item_line.
* BEGIN WKUK068246
* ...no, subtract all taxes beside the allocatable ones from gross amount.
* It's not relevant whether the line is non deductible or not tax relevant!!!
*     CHECK NOT ( tax_item_out-stazf = 'X'    "ignore non deductible...
*             AND tax_item_out-stbkz = '3' ). "...allocatable tax
*     CHECK NOT tax_item_out-stgrp = '4'.  "not tax relevant WKUK036842
      CHECK NOT tax_item_out-stbkz = '3'.     "ignore allocatable tax
* END WKUK068246
      epk-betrg = epk-betrg - tax_item_out-fwste.
    ENDLOOP.
* END INSERT NEW CALCULATION
* END WKUK000624

* fill T030 reading results into EPK
    READ TABLE fi_acct_det_hr
        INDEX wa_ep_translate-acc_det_line.
    CASE fi_acct_det_hr-koart.
      WHEN 'K'.
* line was a vendor posting
        IF fi_acct_det_hr-konto(1) = '*'.
* vendor account was determined dynamically (pers. vendor)
          READ TABLE vendor_result_tab
              INDEX fi_acct_det_hr-vend_cust_line.
          epk-konto = vendor_result_tab-customer.
        ELSE.
* vendor account was fix
          epk-konto = fi_acct_det_hr-konto.
*         IF bl_spl = 'C'.                      "WKUK016310 "WKUK002818
*           epk-bukrs = epk-bukst.              "WKUK016310 "WKUK002818
*         ENDIF.                                "WKUK016310 "WKUK002818
        ENDIF.
        IF fi_acct_det_hr-hnkto(1) = '*'.
* vendor account was determined dynamically (pers. vendor)
          READ TABLE vendor_result_tab
              INDEX fi_acct_det_hr-vend_cust_line.
          epk-hnkto = vendor_result_tab-customer.
        ELSE.
* vendor account was fix
          epk-hnkto = fi_acct_det_hr-hnkto.
*         IF bl_spl = 'C'.                      "WKUK016310 "WKUK002818
*           epk-bukrs = epk-bukst.              "WKUK016310 "WKUK002818
*         ENDIF.                                "WKUK016310 "WKUK002818
        ENDIF.
      WHEN 'D'.
* line was a customer posting
        IF fi_acct_det_hr-konto(1) = '*'.
* customer account was determined dynamically (pers. customer)
          READ TABLE customer_result_tab
              INDEX fi_acct_det_hr-vend_cust_line.
          epk-konto = customer_result_tab-customer.
        ELSE.
* customer account is fix.
          epk-konto = fi_acct_det_hr-konto.
*         IF bl_spl = 'C'.                      "WKUK016310 "WKUK002818
*           epk-bukrs = epk-bukst.              "WKUK016310 "WKUK002818
*         ENDIF.                                "WKUK016310 "WKUK002818
        ENDIF.
        IF fi_acct_det_hr-hnkto(1) = '*'.
* customer account was determined dynamically (pers. customer)
          READ TABLE customer_result_tab
              INDEX fi_acct_det_hr-vend_cust_line.
          epk-hnkto = customer_result_tab-customer.
        ELSE.
* customer account is fix.
          epk-hnkto = fi_acct_det_hr-hnkto.
*         IF bl_spl = 'C'.                      "WKUK016310 "WKUK002818
*           epk-bukrs = epk-bukst.              "WKUK016310 "WKUK002818
*         ENDIF.                                "WKUK016310 "WKUK002818
        ENDIF.
      WHEN OTHERS.
* line was a G/L account posting
        epk-konto = fi_acct_det_hr-konto.
        epk-hnkto = fi_acct_det_hr-hnkto.
    ENDCASE.
* fill posting keys
    epk-slbsl = fi_acct_det_hr-slbsl.
    epk-hnbsl = fi_acct_det_hr-hnbsl.
*   IF ep_translate-koart EQ 'F' AND bl_spl = 'C'."WKUK002816WKUK015412
    IF ep_translate-koart EQ 'F'.                           "WKUK015412
      epk-koart_store = epk-koart.                          "WKUK002816
    ENDIF.                                                  "WKUK002816
    epk-koart = fi_acct_det_hr-koart.

    APPEND epk.

    CLEAR tax_item_out_lines.                               "WKUK004964
    LOOP AT tax_item_out                                    "WKUK004964
        WHERE posnr = wa_ep_translate-tax_item_line         "WKUK004964
          AND error IS INITIAL. "VAT calculation successful "WKUK004964
      ADD 1 TO tax_item_out_lines.                          "WKUK004964
    ENDLOOP.                                                "WKUK004964
    CLEAR act_tabix.                                        "WKUK004964

    CLEAR epk_store.                                        "WKUK068245
    MOVE-CORRESPONDING epk TO epk_store.                    "WKUK068245
* append additional tax lines to epk
    LOOP AT tax_item_out
        WHERE posnr = wa_ep_translate-tax_item_line
          AND error IS INITIAL.        "VAT calculation successful
*     AND NOT FWSTE IS INITIAL.        "VAT amount not Zero "WKUK002096
* BEGIN WKUK004964
* Not all tax lines with zero amount should be posted to FI!
* Because in Release 4.5 FI cannot handle multi-level jurisdiction
* codes, R/3 note 137604 proposes the simulation of canadian two-level
* jurisdiction codes by a pseudo-two-level mechanism, where the first
* level is always zero. Such zero lines are not relevant for tax
* reporting and therefore should be deleted.
* But in principle such lines do not appear if note 137604 is customized
* correctly (no percent, even not zero, in first level -> no tax line!)
      MOVE-CORRESPONDING epk_store TO epk.                  "WKUK068245
      ADD 1 TO act_tabix.
      CHECK NOT                        "remove lines with...
          ( NOT tax_item_out-txjcd IS INITIAL     "jurisdiction code
            AND tax_item_out-txjcd_deep IS INITIAL"but no deepest (4.5!)
            AND tax_item_out-txjlv IS INITIAL     "and no level   (4.5!)
            AND tax_item_out-fwste IS INITIAL     "and tax amount zero
            AND ( tax_item_out_lines GT act_tabix "and ( not last line
             OR   tax_item_out_lines EQ 1 ) ).    "       or only line )
* END WKUK004964
*          and stbkz ne '3'.      "VAT is not allocatable   "WKUK010228
      epk-bukrs = tax_item_out-bukrs.
      epk-smwkz = tax_item_out-mwskz.
      epk-stxjc = tax_item_out-txjcd.
      epk-stxjc_deep = tax_item_out-txjcd_deep.             "WKUK001723
      epk-stxlv = tax_item_out-txjlv.                       "WKUK001723
      epk-waers = tax_item_out-waers.
*               tax_item_out-bldat.                       "forget it!
*               tax_item_out-budat.                       "forget it!
      epk-txdat = tax_item_out-txdat.                       "WKUK010228
      epk-betrg = tax_item_out-fwste.
*      epk-msatz = tax_item_out-msatz.                       "WKUK010228
      epk-msatz_char = tax_item_out-msatz. "GLW note 2978229
      epk-fwbas = tax_item_out-fwbas.
      epk-brutto = tax_item_out-wrbtr.
      IF tax_item_out-stbkz NE 3.                           "WKUK010228
* when VAT is not allocatable...                            "WKUK010228
        IF tax_item_out-stazf = 'X'.                        "WKUK001206
* ... and not deductible, create statistical tax line       "WKUK001206
          epk-hnkto = tax_item_out-hkont.                   "WKUK001206
          epk-kstat = 'X'.         "tax line is statistical""WKUK001206
        ELSE.                                               "WKUK001206
* ... but deductible, create normal tax line                "WKUK001206
          epk-hnkto = tax_item_out-hkont.                   "WKUK010228
          CLEAR epk-kstat.                                  "WKUK010228
        ENDIF.                                              "WKUK001206
      ELSE.                                                 "WKUK010228
* when VAT is allocatable, clear account number             "WKUK010228
        CLEAR epk-hnkto.         "no tax account            "WKUK010228
        epk-kstat = 'X'.         "tax line is statistical   "WKUK010228
      ENDIF.                                                "WKUK010228
      epk-ktosl = tax_item_out-ktosl.
      epk-kschl = tax_item_out-kschl.                       "WKUK010228
      epk-tax_line = sy-tabix.
      epk-tax_indicator = 'X'.                              "WKUK001206
      APPEND epk.

      IF tax_item_out-stbkz NE 3.                           "WKUK001206
* when VAT is not allocatable...                            "WKUK001206
        IF tax_item_out-stazf = 'X'.                        "WKUK001206
* ... and not deductible, create additional G/L account line"WKUK001206
          epk-konto = tax_item_out-hkont.                   "WKUK001206
*         clear epk-fwbas.                                  "WKUK001206
          CLEAR epk-tax_indicator.                          "WKUK001206
          CLEAR epk-kstat.                                  "WKUK001206
*         append epk.                           "WKUK001206 "WKUK063501
* if no cross-company posting, then this one line is enough,"WKUK063501
          IF epk-bukst EQ epk-bukrs.                        "WKUK063501
            APPEND epk.                                     "WKUK063501
* but for cross-company postings, this line loses tax signs "WKUK063501
* and more lines must be created                            "WKUK063501
          ELSE.                                             "WKUK063501
            store_ep_line = epk-ep_line.                    "WKUK009891
            CLEAR: epk-smwkz,                               "WKUK063501
                   epk-stxjc,                               "WKUK063501
                   epk-stxjc_deep,                          "WKUK009890
                   epk-stxlv,                               "WKUK009890
                   epk-ep_line.                             "WKUK009891
            APPEND epk.                                     "WKUK063501
* 1) G/L account line in BUKST (for correct tax form),      "WKUK063501
*    this line has tax signs and as dummy CO-object the     "WKUK063501
*    master cost center                                     "WKUK063501
            LOOP AT psref_fields.                           "WKUK063501
              CHECK psref_fields-field <> 'BUKRS'.          "WKUK063501
              CHECK psref_fields-field <> 'SGTXT'.          "WKUK063501
              CHECK psref_fields-field <> 'EXBEL'.          "WKUK063501
              CHECK psref_fields-field <> 'GSBER'.          "WKUK063501
              CHECK psref_fields-field <> 'FISTL'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'FIPOS'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'GEBER'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'FIPEX'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'FKBER'. "#EC NOTEXT"XCIK152901
              CHECK psref_fields-field <> 'GRANT_NBR'. "#EC NOTEXT"152901
              epk_field(4) = 'EPK-'.                        "WKUK063501
              epk_field+4(20) = psref_fields-field.         "WKUK063501
              ASSIGN (epk_field) TO <f>.                    "WKUK063501
              CLEAR <f>.                                    "WKUK063501
            ENDLOOP.                                        "WKUK063501
            epk-bukrs = epk-bukst.                          "WKUK063501
            epk-gsber = accountingobjects-bus_area_empl.    "WKUK063501
            epk-kostl = accountingobjects-costcenter_empl.  "WKUK063501
            epk-smwkz = tax_item_out-mwskz.                 "WKUK063501
            epk-stxjc = tax_item_out-txjcd.                 "WKUK063501
            epk-stxjc_deep = tax_item_out-txjcd_deep.       "WKUK009890
            epk-stxlv = tax_item_out-txjlv.                 "WKUK009890
            epk-ep_line = store_ep_line.                    "WKUK009891
* check master cost assingment of additional NAV lines      "WKUK063501
            PERFORM check_master_cost_assignment.           "WKUK063501

            APPEND epk.                                     "WKUK063501
* 2) G/L account line in BUKST (to balance previous line),  "WKUK063501
*    this line has no tax signs and as dummy CO-object the  "WKUK063501
*    master cost center                                     "WKUK063501
            epk-betrg = -1 * epk-betrg.                     "WKUK063501
            CLEAR: epk-smwkz,                               "WKUK063501
                   epk-stxjc,                               "WKUK063501
                   epk-stxjc_deep,                          "WKUK063501
                   epk-stxlv,                               "WKUK009890
                   epk-ep_line.                             "WKUK009891
            APPEND epk.                                     "WKUK063501
          ENDIF.                                            "WKUK063501
        ENDIF.                                              "WKUK001206
      ENDIF.                                                "WKUK001206
    ENDLOOP.

  ENDLOOP.

  CLEAR ep_translate.
  REFRESH ep_translate.

ENDFORM.                               "BUILD_EPK_FROM_EP



*---------------------------------------------------------------------*
*       FORM CREATE_DOCUMENT_FROM EPK                                 *
*---------------------------------------------------------------------*
FORM create_document_from_epk.

  DATA: int_rot_awkey                    LIKE ptrv_rot_awkey OCCURS 10 WITH HEADER LINE,
        last_line                        LIKE sy-tabix,
        epk_lines                        TYPE i,
        old_bukrs                        LIKE epk-bukrs VALUE '    ',
        bukst                            LIKE epk-bukrs VALUE '    ', "WKUK002815
*        psref LIKE psref,                                  "AKAK011844
        psref                            LIKE ptrv_psref,   "AKAK011844
        pernr                            LIKE epk-pernr,
        exbel                            LIKE epk-sexbl,
        belnr                            LIKE epk-belnr,                          "Beleg pro Beleg
        konto_sort                       LIKE bz-konto,     "WKUK015412
        prctr                            LIKE epk-prctr,    "WKUK015412
        segment                          LIKE epk-segment, "GLW note 2926207
        clearing_account_posting(1),
        posting_document_split(1),
        koart                            LIKE bz-koart,     "WKUK012485
        ktosl                            LIKE bz-ktosl,     "WKUK012485
        konto                            LIKE bz-konto,
        hnkto                            LIKE bz-hnkto,
        vbund                            LIKE bz-vbund,     "WKUK029301
        mwskz                            LIKE bz-mwskz,
        txjcd                            LIKE bz-txjcd,
        no_new_posting_document(1),
        no_new_posting_document_bukrs(1).

  DATA: psref_fname(21),
        epk_field(23).

  DATA next_belnr LIKE epk-belnr.
  DATA next_tabix LIKE sy-tabix.
  DATA epk_next_belnr LIKE epk.

  FIELD-SYMBOLS: <fname>.

  DATA receivers_lines LIKE sy-tabix.                       "WKUK063502

  DATA: wa_bukrs_receivers LIKE bukrs_receivers,            "WKUK000523
        wa_bukst_receivers LIKE bukrs_receivers.            "WKUK000523

  DATA: l_tabix            LIKE sy-tabix,                   "WKUK015412
        l_tabix_work       LIKE sy-tabix,                   "WKUK015412
        l_subrc            LIKE sy-subrc,                   "WKUK015412
        bl_spl_temp        LIKE bl_spl,                     "WKUK015412
        real_epk_field(24),                                 "WKUK015412
        lwa_epk            LIKE epk.                        "WKUK015412

  DATA: split_because_country_diff   TYPE xfeld.            "GLWE34K019274

*  DATA: l_tabix_work_last LIKE sy-tabix,                    "GLWK002511
*        work_subrc LIKE sy-subrc.
*  DATA: hrp_found TYPE xfeld.                               "GLWK002560
*  DATA: last_ktosl LIKE epk-ktosl.                          "GLWK031047

  IF prctr_tr EQ true OR segment_tr = true.  "GLW note 2926207.  "WKUK015412
    bl_k = 'X'.                                             "WKUK015412
  ENDIF.                                                    "WKUK015412
  IF bl_k = 'X'.                                            "WKUK015412
    bl_spl_temp = 'K'.                                      "WKUK015412
  ENDIF.                                                    "WKUK015412

  PERFORM determine_no_of_receivers USING receivers_lines.  "WKUK063502

* IF receivers_lines LE 1.                      "WKUK000635 "WKUK002818
*   LOOP AT epk WHERE tax_indicator EQ 'X'.     "WKUK000635 "WKUK002818
*     IF epk-bukst NE epk-bukrs.                "WKUK000635 "WKUK002818
*       epk-bukrs = epk-bukst.                  "WKUK000635 "WKUK002818
*       MODIFY epk TRANSPORTING bukrs.          "WKUK000635 "WKUK002818
*     ENDIF.                                    "WKUK000635 "WKUK002818
*   ENDLOOP.                                    "WKUK000635 "WKUK002818
* ENDIF.                                        "WKUK000635 "WKUK002818

* BEGIN WKUK000048
* coding moved from inside the EPK-LOOP into a separate loop
  LOOP AT epk.
    l_tabix = sy-tabix.                                     "WKUK015412
    IF t_ptrv_rot_ep_lines GE 2.
* PTRV_ROT_EP more than one line, i
*.e PTRV_TRANSLATE called from >=4.0C
* delete lines from epk being without errors itself,
* but coming from travels with errors in some epk line
      READ TABLE post_result
          WITH KEY pernr = epk-pernr_store
                   reinr = epk-reinr_store
                   perio = epk-perio                        "SVTK1921026
                   error = 'X'.
      IF sy-subrc IS INITIAL.
        DELETE epk.
        CONTINUE.                                           "WKUK015412
      ENDIF.
    ENDIF.

* CProject-objects are not relevant for sorting process     "AKAK011844
    CLEAR: epk-project_guid,                                "AKAK011844
           epk-project_ext_id,                              "AKAK011844
           epk-task_role_guid,                              "AKAK011844
           epk-task_role_ext_id,                            "AKAK011844
           epk-object_type.                                 "AKAK011844

    IF epk-koart = 'K' AND ( epk-ktosl EQ 'HRP' OR epk-ktosl EQ 'HRV' )."GLW note 2379656              "EH5K000068
*      IF bl_spl NE 'C'. "GLWK034997 is needed for sorting
      IF bl_spl NE 'C'.
        IF prctr_tr EQ false.
          CLEAR epk-prctr.
          CLEAR epk-gsber.
        ELSE.
          IF NOT ( epk-ktosl EQ 'HRV' AND epk-hnbsl = '39' AND epk-slbsl = '29' AND epk-keep_prctr_hrv = abap_true ) .  "GLW note 2607567
* not if: HRV is special GL and HRP is used together with special GL HRV
            CLEAR epk-prctr.
            CLEAR epk-gsber.
          ENDIF.
        ENDIF.
        IF segment_tr EQ false. "GLW note 2926207
          CLEAR epk-segment.
          IF prctr_tr EQ false.
            CLEAR epk-gsber.
          ENDIF.
        ELSE.
          IF NOT ( epk-ktosl EQ 'HRV' AND epk-hnbsl = '39' AND epk-slbsl = '29' AND epk-keep_prctr_hrv = abap_true ) .  "GLW note 2607567
* not if: HRV is special GL and HRP is used together with special GL HRV
            CLEAR epk-segment.
            IF prctr_tr EQ false.
              CLEAR epk-gsber.
            ENDIF.
          ENDIF.
        ENDIF.
      ENDIF.
    ENDIF.

* BEGIN WKUK015412 coding moved from beginning of FM PTRV_TRANSLATE
    IF prctr_tr EQ true OR segment_tr EQ true. "GLW note 2926207
      IF bl_spl NE 'C'.
* remove profit center only from vendor lines
*        IF epk-koart = 'K'.
*          CLEAR epk-prctr.
*          CLEAR epk-gsber.                    "WKUK006457 "EH5K000068
*        ENDIF.
* remove CO objects and tax information from vendor and clearing account posting lines
        IF epk-koart = 'K' OR epk-koart_store = 'F' OR
           epk-ktosl = 'HRP' OR epk-ktosl EQ 'HRV'.
          LOOP AT psref_fields.
            CHECK psref_fields-field <> 'BUKRS'.
            CHECK psref_fields-field <> 'SGTXT'.
            CHECK psref_fields-field <> 'EXBEL'.
            CHECK psref_fields-field <> 'GSBER'.
            IF prctr_tr EQ true.
              CHECK psref_fields-field <> 'PRCTR'.
            ENDIF.
            IF segment_tr EQ true.
              CHECK psref_fields-field <> 'SEGMENT'. "GLW note 2926207
            ENDIF.
            real_epk_field(5) = 'EPK-'.
            real_epk_field+4(20) = psref_fields-field.
            ASSIGN (real_epk_field) TO <f>.
            CLEAR <f>.
          ENDLOOP.
          CLEAR: epk-smwkz,
                 epk-stxjc_deep,
                 epk-stxjc,
                 epk-stxlv.
        ENDIF.
      ENDIF.
    ENDIF.

* finally disable this logic and replace by form do_split_per_vendor: GLWK014624
*    IF bl_spl = 'Q' OR
*       bl_spl = 'R' OR
*       bl_spl = 'P'.
*      IF bl_k IS NOT INITIAL. "Zusätzl.Belegsplit/Kred
*        IF epk-ktosl NE 'HRP'.
*          l_tabix_work = l_tabix + 1.
*          l_subrc = 1.
** GLWK002511 begin
*          CLEAR work_subrc.
*          CLEAR hrp_found.                                  "GLWK002560
*          LOOP AT epk INTO lwa_epk
*                      FROM l_tabix_work.
*
*            IF lwa_epk-ktosl = 'HRT'.
*              work_subrc = 1.
*              EXIT.
*            ELSEIF lwa_epk-ktosl = 'HRP'.
*              hrp_found = 'X'.                              "GLWK002560
*              EXIT.
*            ENDIF.
*          ENDLOOP.
*          IF sy-subrc NE 0.
*            work_subrc = sy-subrc.
*          ENDIF.
*          if ( work_subrc NE 0 ) OR ( hrp_found IS INITIAL )."GLWK002560
*            IF NOT ( last_ktosl EQ 'HRP' AND epk-ktosl EQ 'HRT' AND epk-koart_store EQ 'F' ).
*              l_tabix_work = l_tabix_work_last.
*            ENDIF.                                          "GLWK031047
*          endif.
** GLWK002511 end
*          LOOP AT epk INTO lwa_epk
*                      FROM l_tabix_work.
*            IF lwa_epk-ktosl = 'HRP'.
*              IF lwa_epk-betrg IS NOT INITIAL.
** BEGIN WKUK015647
**               MOVE lwa_epk-hnkto TO epk-konto_sort.
*                CASE bl_spl.
*                  WHEN 'Q'.
*                    MOVE lwa_epk-hnkto TO epk-konto_sort.
*                  WHEN 'R'.
*                    MOVE lwa_epk-hnkto TO epk-sexbl_konto_sort.
*                  WHEN 'P'.
*                    MOVE lwa_epk-hnkto TO epk-pernr_konto_sort.
*                ENDCASE.
** END WKUK015647
*                l_tabix_work_last = l_tabix_work.           "GLWK002511
*                l_subrc = 0.
*              ELSE.
*                l_subrc = 1.
*              ENDIF.
*              EXIT.
*            ELSEIF lwa_epk-ktosl = 'HRT'.
*              l_subrc = 1.
*              EXIT.
*            ELSE.
*              CONTINUE.
*            ENDIF.
*          ENDLOOP.
*          IF sy-subrc IS NOT INITIAL.
*            l_subrc = 1.
*          ENDIF.
*        ELSE.
*          IF epk-betrg IS NOT INITIAL.
** BEGIN WKUK015647
**           MOVE epk-hnkto TO epk-konto_sort.
*            CASE bl_spl.
*              WHEN 'Q'.
*                MOVE epk-hnkto TO epk-konto_sort.
*              WHEN 'R'.
*                MOVE epk-hnkto TO epk-sexbl_konto_sort.
*              WHEN 'P'.
*                MOVE epk-hnkto TO epk-pernr_konto_sort.
*            ENDCASE.
** END WKUK015647
*            l_subrc = 0.
*          ELSE.
*            l_subrc = 1.
*          ENDIF.
*        ENDIF.
*        IF l_subrc IS NOT INITIAL.
*          CASE bl_spl.
*            WHEN 'Q'.
**             MOVE epk-belnr TO epk-konto_sort.             "WKUK015647
*              MOVE epk-belnr TO epk-konto_sort.             "WKUK015647
*            WHEN 'R'.
**             MOVE epk-sexbl TO epk-konto_sort.             "WKUK015647
*              MOVE epk-sexbl TO epk-sexbl_konto_sort.       "WKUK015647
*            WHEN 'P'.
**             MOVE epk-pernr TO epk-konto_sort.             "WKUK015647
*              MOVE epk-pernr TO epk-pernr_konto_sort.       "WKUK015647
*          ENDCASE.
*        ENDIF.
*        IF epk-ktosl EQ 'HRP'.                               "GLWK031047
*          last_ktosl = epk-ktosl.                            "GLWK031047
**       ELSEIF epk-ktosl EQ 'HRT'.                           "GLWK031047
*        ELSEIF epk-ktosl EQ 'HRT' AND epk-koart_store NE 'F'."GLWK031047
*          CLEAR last_ktosl.                                  "GLWK031047
*        ENDIF.                                               "GLWK031047
*      ENDIF.
*    ENDIF.
*
* fill sort key:
*A  HRP Vendor
*B  HRP balance Sheet
*C  HRV Vendor
*D  HRV balance sheet
*E  HRT offsetting
*F  HRT expense line
*G  VAT posting line
*H  VAT tax line
    CASE epk-ktosl.
      WHEN 'HRV'.
        CASE epk-koart.
          WHEN  'S'.    "balance sheet posting
            epk-ktosl_sort = 'D'.
          WHEN OTHERS.  "vendor
            epk-ktosl_sort =  'C'.
        ENDCASE.
      WHEN 'HRP'.
        CASE epk-koart.
          WHEN  'S'.    "balance sheet posting
            epk-ktosl_sort = 'B'.
          WHEN OTHERS.  "vendor
            epk-ktosl_sort = 'A'.
        ENDCASE.

      WHEN 'HRT'.
        IF epk-koart_store = 'F'. "balance sheet.
          epk-ktosl_sort = 'E'.
        ELSE.
* expense posting
          epk-ktosl_sort = 'F'.
        ENDIF.
      WHEN OTHERS.  "VAT related.
        CASE epk-tax_indicator.
          WHEN abap_true.
            epk-ktosl_sort = 'H'.
          WHEN OTHERS.
            epk-ktosl_sort = 'G'.
        ENDCASE.
    ENDCASE.
    MODIFY epk INDEX l_tabix.
** END WKUK015412
  ENDLOOP.
* END WKUK000048

  IF     bl_spl = 'Q' OR
       bl_spl = 'R' OR
       bl_spl = 'P'.
    IF bl_k IS NOT INITIAL. "Zusätzl.Belegsplit/Kred

      PERFORM do_split_per_vendor.

    ENDIF.
  ENDIF.
* GLWK014624 end

* GLW note 2315344 begin
  IF bl_spl = 'Q' AND ( budat = '22222222' OR bldat = '22222222' ).
    FIELD-SYMBOLS <epk> LIKE LINE OF epk.
* if per travel document and posting date or receipt date shall be equal to travel document date:
    LOOP AT epk ASSIGNING <epk>.
      <epk>-beldt_split = <epk>-beldt.
    ENDLOOP.
  ENDIF.
* GLW note 2315344 end

  DESCRIBE TABLE epk LINES table_lines.

  SORT epk.
  LOOP AT epk.

    IF sy-tabix < lines( epk ).   "GLW note 2520560
      next_tabix = sy-tabix + 1.
      READ TABLE epk INDEX next_tabix INTO epk_next_belnr TRANSPORTING belnr.
      next_belnr = epk_next_belnr-belnr.
    ELSE.
      CLEAR next_belnr.
    ENDIF.

* comment and move down to 'append bz': GLWEAJK019353
*    IF ( epk-ktosl EQ 'NAV' ) AND ( epk-tax_indicator IS INITIAL ) AND
*       ( epk-tax_line IS NOT INITIAL ) AND ( epk-betrg IS INITIAL ).
*      CONTINUE.                                             "GLWK015504
*    ENDIF.

    IF table_lines GE 20.
      rest = sy-tabix MOD ( table_lines / 20 ).
      IF rest = 0.
        percentage = sy-tabix / ( table_lines / 20 ) * 5.
        CALL FUNCTION 'SAPGUI_PROGRESS_INDICATOR'
          EXPORTING
            percentage = percentage
            text       = text-p07.
      ENDIF.
    ENDIF.

    remember_summed_lines-ep_line = epk-ep_line.
    APPEND remember_summed_lines.

    CLEAR: bz,
           posting_document_split,
           clearing_account_posting.

    MOVE-CORRESPONDING epk TO bz.
    bz-exbel = epk-sexbl.              "bring sort field to bz
    bz-mwskz = epk-smwkz.              "bring sort field to bz
    bz-txjcd_deep = epk-stxjc_deep. "bring sort field to bz  WKUK001723
    bz-txjcd = epk-stxjc.              "bring sort field to bz
    bz-txjlv = epk-stxlv.           "bring sort field to bz  WKUK001723

    bz-msatz = epk-msatz_char. "GLW note 2978229

    IF epk-belnr+0(1) = 'V'.  "GLW note 2520560
      bz-advance = 'V'.
    ENDIF.

* BEGIN WKUK015412
    IF bl_spl = 'Q' OR
       bl_spl = 'R' OR
       bl_spl = 'P'.
      IF bl_k IS NOT INITIAL.            "Zusätzl.Belegsplit/Kred
        bz-pernr = epk-pernr_store.
      ENDIF.
    ENDIF.
* END WKUK015412

* initialize fields for bz storage table
    CLEAR: pernr,
           exbel,
           belnr,                      "Beleg pro Beleg
           psref.                      "Beleg pro CO-Obj
    IF epk-belnr+0(1) = 'V' AND bl_spl NE 'Q'.  "GLW note 2520560
      pernr = epk-pernr.
      exbel = epk-sexbl.
      belnr = epk-belnr.
    ELSE.
      CASE bl_spl.
* BEGIN Beleg pro Beleg
        WHEN 'Q'.
          pernr = epk-pernr.
          exbel = epk-sexbl.
          belnr = epk-belnr.
* END Beleg pro Beleg
        WHEN 'R'.                        "Posting document per trip
          pernr = epk-pernr.
          exbel = epk-sexbl.
        WHEN 'P'.                        "Posting document per employee
          pernr = epk-pernr.
        WHEN 'C'.                        "Posting document per CO-object
          MOVE-CORRESPONDING epk TO psref.
          CLEAR: psref-sgtxt,
                 psref-bukrs,
                 psref-gsber.
*       remove CO-Objects from vendor lines
          IF epk-koart = 'K'.                               "WKUK006457
            CLEAR epk-gsber.                                "WKUK006457
          ENDIF.                                            "WKUK006457
*       if epk-ptype = 'G'.                                 "WKUK002816
          IF epk-ptype = 'G' OR epk-koart_store = 'F'.      "WKUK002816
            LOOP AT psref_fields.
              CHECK psref_fields-field <> 'BUKRS'.
              CHECK psref_fields-field <> 'SGTXT'.
              CHECK psref_fields-field <> 'EXBEL'.
              CHECK psref_fields-field <> 'GSBER'.              " WBG
              epk_field(4) = 'BZ-'.
              epk_field+3(20) = psref_fields-field.
              ASSIGN (epk_field) TO <f>.
              CLEAR <f>.
            ENDLOOP.
            CLEAR bz-kokey.
          ENDIF.
        WHEN 'B'.                      "Posting document per company code
* nothing to do
      ENDCASE.
    ENDIF.
    IF bl_spl_temp = 'K'.                                   "WKUK015412
* BEGIN WKUK015647
*     konto_sort = epk-konto_sort.                          "WKUK015412
      IF epk-belnr+0(1) = 'V' AND bl_spl NE 'Q'.  "GLW note 2520560
        konto_sort = epk-konto_sort.
      ELSE.
        CASE bl_spl.
          WHEN 'Q'.
            konto_sort = epk-konto_sort.
          WHEN 'R'.
            konto_sort = epk-sexbl_konto_sort.
          WHEN 'P'.
            konto_sort = epk-pernr_konto_sort.
        ENDCASE.
      ENDIF.
* END WKUK015647
    ENDIF.                                                  "WKUK015412
    IF prctr_tr EQ true.                                    "WKUK015412
      CLEAR psref.                                          "WKUK015412
      prctr = epk-prctr.                                    "WKUK015412
    ENDIF.                                                  "WKUK015412

    IF segment EQ true.
      CLEAR psref.
      segment = epk-segment.     "GLW note 2926207
    ENDIF.

* BEGIN WKUK000048
* coding moved from inside the EPK-LOOP into a separate loop
*    IF t_ptrv_rot_ep_lines GE 2.
** PTRV_ROT_EP more than one line, i.e PTRV_TRANSLATE called from >=4.0C
** delete lines from epk being without errors itself,
** but coming from travels with errors in some epk line
*      READ TABLE post_result
*          WITH KEY pernr = epk-pernr_store
*                   reinr = epk-reinr_store
*                   error = 'X'.
*      IF sy-subrc IS INITIAL.
*        DELETE epk.
*        CLEAR  epk.
** error sign in result table must be set for all entries
** coming from travels with error sign in at least one entry
** don't need that because of sorting the messages correctly
**      loop at post_result
**          where pernr = epk-pernr
**            and reinr = epk-sexbl(10)
**            and error = ' '.
**        post_result-error = 'X'.
**        modify post_result.
**      endloop.
*      ENDIF.
*    ENDIF.
* END WKUK000048

    IF NOT epk IS INITIAL.

      AT NEW abkrs.
* no activities
      ENDAT.

      AT NEW stxjc.
        IF new_awkey = 'X'.
* new AWKEY has to be drawn
          CLEAR new_awkey.

          PERFORM number_get_next.

*         N_AWREF = N_AWREF_STORE = I_AWREF.  " WBG Hotline 175746
          n_awref_store = n_awref.     " WBG Hotline 175746
          CLEAR bz_anzhl_store.
        ENDIF.
      ENDAT.

      n_awref  = n_awref_store. " number_get_next not always performed;
      bz_anzhl = bz_anzhl_store.

* Pointing table ROT <-> AWKEY will be filled
      IF epk-tax_line IS INITIAL.
        READ TABLE ptrv_rot_ep
            WITH KEY pernr = epk-pernr_store
                     reinr = epk-reinr_store
            BINARY SEARCH.
        LOOP AT ptrv_rot_ep FROM sy-tabix.
          IF ptrv_rot_ep-pernr EQ epk-pernr_store AND
             ptrv_rot_ep-reinr EQ epk-reinr_store.
            IF ptrv_rot_ep-ep_line = epk-ep_line.
              MOVE-CORRESPONDING ptrv_rot_ep TO int_rot_awkey.
              APPEND int_rot_awkey.
            ENDIF.
          ELSE.
            EXIT.
          ENDIF.
        ENDLOOP.

*      loop at ptrv_rot_ep where ep_line = epk-ep_line.
*        move-corresponding ptrv_rot_ep to int_rot_awkey.
*        append int_rot_awkey.
*      endloop.

      ENDIF.

      AT END OF stxjc.

*       if bz-koart = 'A' and a_sgtxt is initial.           "WKUK018316
        IF ( epk-ptype = 'K' OR epk-ptype = 'A' )           "WKUK018316
             AND a_sgtxt IS INITIAL.                        "WKUK018316
          CLEAR bz-sgtxt.
        ENDIF.
*       if bz-koart = 'G' and g_sgtxt is initial.           "WKUK018316
        IF epk-ptype = 'G' AND g_sgtxt IS INITIAL.          "WKUK018316
          CLEAR bz-sgtxt.
        ENDIF.
*      if kr_sgtxt is initial.
*        clear bz-sgtxt.
*      endif.

* create sum for posting line
        SUM.
        MOVE: epk-betrg TO bz-betrg,
              epk-fwbas TO bz-fwbas,
              epk-brutto TO bz-brutto.
*       IF BZ-BETRG <> 0                                    "WKUK021052
*           OR NOT BZ-TAX_INDICATOR IS INITIAL. "WKUK002096 "WKUK021052
        IF NOT ( bz-betrg = 0 AND bz-fwbas = 0 ).           "WKUK021052
          ADD epk-betrg TO bz_saldo.   "Saldo des Buchungsbeleges
          MOVE epk-waers TO bz_waers.  "Währung des Belegsaldos

          PERFORM treat_wandering_tax_line                  "WKUK059035
              TABLES int_rot_awkey                          "WKUK059035
*              USING old_bukrs.                 "WKUK059035 "WKUK015412
               USING old_bukrs                              "WKUK015412
                     psref.                                 "WKUK015412

*         IF BZ-FWBAS IS INITIAL.                           "WKUK001206
          IF bz-tax_indicator IS INITIAL.                   "WKUK001206
* current line is not a tax line

            ADD 1 TO bz_anzhl.         "Buchungszeilenanzahl
            bz_anzhl_store = bz_anzhl.

* BEGIN WKUK002815
*           if epk-bukrs eq epk-bukst and epk-bukst ne bukst.WKUK003592
            IF epk-bukst NE bukst.                          "WKUK003592
* Normally BUKST does not change within a trip. But it may change e.g.
* when the posting goes to a clearing account and this account should
* be in the same company code as the G/L account and the G/L accounts
* of one trip do not all lie in the same company code.
* It may also change when the offsetting entry of a paid     WKUK003592
* receipt goes to the master cost assignment (determined     WKUK003592
* now at trip end time and no longer at SY-DATUM) and there  WKUK003592
* was an organisational change with change of company code.  WKUK003592
* The G/L account posting itself may cause then a cross      WKUK003592
* company posting if its cost assignment was different       WKUK003592
* from master. But anyway condition EPK-BUKRS eq EPK-BUKST   WKUK003592
* is no longer a good criterion for new posting document.    WKUK003592
* In this case a new posting document may be necessary though it
* cannot be created via central FORM EMPTY_BZ.
* Thus the necessity of a new posting document is checked here.
              IF NOT bukst IS INITIAL.   "nicht beim ersten mal
* look if posting document for current company code already in BZ
                READ TABLE store_bz
                    WITH KEY bukrs = epk-bukst
                             psref = psref
                             pernr = pernr
                             exbel = exbel
                             belnr = belnr             "Beleg pro Beleg
                             konto_sort = konto_sort        "WKUK015412
                             umdat = epk-umdat           "QKZ_CEE_CZ_SK
                             waers = epk-waers
                             vat_delta = epk-vat_delta   "GLW note 1808477
                             xnegp     = epk-xnegp.  "GLW note 2071158
                IF sy-subrc EQ 0.
                  n_awref = store_bz-awref.
                  bz_anzhl = store_bz-awlin + 1.
                ELSE.
* if not, create a new posting document (i.e. new AWKEY)
                  PERFORM number_get_next.
                  bz_anzhl = 1.
                ENDIF.
              ELSE.                      "beim ersten mal
                bukst = epk-bukst.
              ENDIF.
            ENDIF.
* END WKUK002815

            READ TABLE bukrs_receivers                      "WKUK000523
                INTO wa_bukrs_receivers                     "WKUK000523
                WITH KEY bukrs = epk-bukrs.                 "WKUK000523
            READ TABLE bukrs_receivers                      "WKUK000523
                INTO wa_bukst_receivers                     "WKUK000523
                WITH KEY bukrs = epk-bukst.                 "WKUK000523

            PERFORM det_split_because_country_diff            "GLWE34K019274
                USING epk-bukrs
                      epk-bukst
                      epk-stxjc                              "GLWEH5K022539
                CHANGING
                      split_because_country_diff.

            IF ( epk-bukrs EQ epk-bukst
*             or receivers_lines le 1.          "WKUK000635 "WKUK002817
*             OR ( receivers_lines LE 1         "WKUK002817 "WKUK000523
            OR ( wa_bukrs_receivers-receiver =              "WKUK000523
                 wa_bukst_receivers-receiver                "WKUK000523
            AND NOT ( bl_spl EQ 'B'                         "WKUK002817
                   OR bl_spl EQ 'C' ) ) ) AND               "WKUK002818
              split_because_country_diff IS INITIAL.        "GLWE34K019274

* no cross company posting is necessary

* for posting document per company code or per CO-object a new posting
* document cannot be created via central FORM EMPTY_BZ.
* Thus the necessity of a new posting document is checked several times.
              IF bl_spl = 'B' OR bl_spl = 'C'.
                IF NOT old_bukrs IS INITIAL AND lines( store_bz ) > 0. "GLW note 3116862  "nicht beim 1.mal
* look if posting document for current company code already in BZ
                  READ TABLE store_bz
                      WITH KEY bukrs = epk-bukst
                               psref = psref
                               umdat = epk-umdat           "QKZ_CEE_CZ_SK
                               waers = epk-waers
                               vat_delta = epk-vat_delta  "GLW note 1808477
                               xnegp     = epk-xnegp. "GLW note 2071158
                  IF sy-subrc EQ 0.
                    n_awref  = n_awref_store  = store_bz-awref.
                    bz_anzhl = bz_anzhl_store = store_bz-awlin + 1.
                  ELSE.
* if not, create a new posting document (i.e. new AWKEY)
                    PERFORM number_get_next.
*                   N_AWREF  = N_AWREF_STORE  = I_AWREF. " WBG 175746
                    n_awref_store = n_awref.               " WBG 175746
                    bz_anzhl = bz_anzhl_store = 1.
                  ENDIF.
                ENDIF.
              ENDIF.

            ELSE.
* cross company posting is necessary

              mwskz = bz-mwskz.
              txjcd = bz-txjcd.
* for posting document per company code or per CO-object a new posting
* document cannot be created via central FORM EMPTY_BZ.
* Thus the necessity of a new posting document is checked several times.
              IF bl_spl = 'B' OR bl_spl = 'C'.
                IF NOT old_bukrs IS INITIAL AND lines( store_bz ) > 0. "GLW note 3116862   "nicht beim 1.mal
* look if posting document for current company code already in BZ
                  READ TABLE store_bz
                      WITH KEY bukrs = epk-bukst
                               psref = psref
                               umdat = epk-umdat           "QKZ_CEE_CZ_SK
                               waers = epk-waers
                               vat_delta = epk-vat_delta  "GLW note 1808477
                               xnegp     = epk-xnegp. "GLW note 2071158
                  IF sy-subrc EQ 0.
                    n_awref  = store_bz-awref.
                    bz_anzhl = store_bz-awlin + 1.
                  ELSE.                                     "WKU
* if not, create a new posting document (i.e. new AWKEY)      "WKU
                    PERFORM number_get_next.                "WKU
*        N_AWREF  = N_AWREF_STORE  = I_AWREF.      " WBG Hotline 175746
                    n_awref_store = n_awref.       " WBG Hotline 175746
                    bz_anzhl = bz_anzhl_store = 1.          "WKU
                  ENDIF.
                ENDIF.
              ENDIF.

              PERFORM administrate_buv_help                 "WKUK005642
                  USING n_awref.                            "WKUK005642

* read cross company clearing accounts for BUKST -> BUKRS
              CALL FUNCTION 'HRCA_FI_ACCT_DET_CROSS_COMPANY'
                EXPORTING
                  companycode_1     = epk-bukst
                  companycode_2     = epk-bukrs
                IMPORTING
                  fields_cc1_debit  = bukst_debit_fields
                  fields_cc1_credit = bukst_credit_fields
                  fields_cc2_debit  = bukrs_debit_fields
                  fields_cc2_credit = bukrs_credit_fields
                TABLES
                  return_table      = return_table.

* check if function call was technically successful
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

*  GLWE34K020939 begin
* if bukrs is in a different log. system maybe the accounts are maintained in the log. system
              IF ( wa_bukrs_receivers-receiver <> wa_bukst_receivers-receiver ) AND
                 ( bukrs_debit_fields IS INITIAL AND bukrs_credit_fields IS INITIAL ).

                CALL FUNCTION 'HRCA_FI_ACCT_DET_CROSS_COMPANY'
                  EXPORTING
                    companycode_1     = epk-bukrs
                    companycode_2     = epk-bukst
                  IMPORTING
                    fields_cc1_debit  = bukrs_debit_fields
                    fields_cc1_credit = bukrs_credit_fields
                  TABLES
                    return_table      = return_table.

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
* GLWE34K020939 end

* check if returned cross company clearing accounts are useful
              IF epk-betrg GT 0.                            "WKUK001403
                PERFORM check_cap_determination
                    USING bukst_debit_fields
                          epk-bukst
                          epk-bukrs.
                PERFORM check_cap_determination
                    USING bukrs_credit_fields
                          epk-bukrs
                          epk-bukst.
              ELSE.                                         "WKUK001403
                PERFORM check_cap_determination
                    USING bukst_credit_fields
                          epk-bukst
                          epk-bukrs.
                PERFORM check_cap_determination
                    USING bukrs_debit_fields
                          epk-bukrs
                          epk-bukst.
              ENDIF.                                        "WKUK001403
              IF epk-betrg GT 0.                            "WKUK012485
                koart = bukst_debit_fields-koart.           "WKUK012485
                ktosl = bukst_debit_fields-ktosl.           "WKUK012485
                vbund = bukst_debit_fields-vbund.           "WKUK029301
              ELSE.                                         "WKUK012485
                koart = bukst_credit_fields-koart.          "WKUK012485
                ktosl = bukst_credit_fields-ktosl.          "WKUK012485
                vbund = bukst_credit_fields-vbund.          "WKUK029301
              ENDIF.                                        "WKUK012485

* look if posting document split is necessary
              IF cl_fitv_posting_util=>is_new_int_glvor(          "GLW note 2392616
                i_bukrs1        = epk-bukrs
                i_bukrs2        = epk-bukst
                io_trip_post_fi = exit_trip_post_fi
                   )  IS INITIAL.

*           case bukst_debit_fields-koart.                  "WKUK012485
              CASE koart.                                   "WKUK012485

                WHEN 'S'.
* clearing account is G/L account
* => no posting document split account necessary

                WHEN OTHERS.
* clearing account is vendor or customer
* => posting document split account is necessary
                  PERFORM handle_posting_document_split
                      TABLES    store_bz
                                int_rot_awkey  "GLW note  2178197
                      USING     epk-bukst
                           ' '                              "WKUK012485
*                             bukst_debit_fields-koart      "WKUK012485
                           koart                            "WKUK012485
                                psref
                                pernr
                                exbel
                                belnr                  "Beleg pro Beleg
                                konto_sort                  "WKUK015412
                                bl_spl_temp                 "WKUK015412
                                prctr                       "WKUK015412
                                  segment
                       CHANGING mwskz
                                txjcd
                                no_new_posting_document
                                posting_document_split.
              ENDCASE.

              ENDIF.   "GLW note 2392616
* handle line for clearing account posting in master company code
* (only with tax and jurisdiction code when not cleared by posting
* document split)
*           case bukst_debit_fields-koart.                  "WKUK012485
              CASE koart.                                   "WKUK012485
                WHEN 'S'.
                  konto = bukst_debit_fields-hkont.
                  hnkto = bukst_credit_fields-hkont.
                WHEN 'K'.
                  konto = bukst_debit_fields-lifnr.
                  hnkto = bukst_credit_fields-lifnr.
                  CLEAR vbund.                              "WKUK029301
                WHEN 'D'.
                  konto = bukst_debit_fields-kunnr.
                  hnkto = bukst_credit_fields-kunnr.
                  CLEAR vbund.                              "WKUK029301
              ENDCASE.

* look if line similar to current line is already in posting document
              READ TABLE bz INTO wa_bz
                  WITH KEY awref = n_awref
                           pernr = bz-pernr
*                          ktosl = bukst_debit_fields-ktosl "WKUK012485
                           ktosl = ktosl                    "WKUK012485
*                          koart = bukst_debit_fields-koart "WKUK012485
                           koart = koart                    "WKUK012485
                           slbsl = bukst_debit_fields-bschl
                           hnbsl = bukst_credit_fields-bschl
                           konto = konto
                           hnkto = hnkto
                           vbund = vbund                    "WKUK029301
                           bukrs = epk-bukst
                           exbel = bz-exbel
                           mwskz = mwskz
                           txjcd = txjcd
                           prctr = prctr                    "WKUK015412
                           segment = segment  "GLW note 2926207
                           waers = bz-waers.
              IF sy-subrc = 0.
* if so, add current amount to amount of the found posting document line
                wa_bz-betrg   = wa_bz-betrg + epk-betrg.
                wa_bz-ep_line = bz-ep_line.
* posting document lines created by cross company postings  "WKUK065591
* are deleted if their amount is zero (looks better!)       "WKUK065591
                IF wa_bz-betrg = 0.                         "WKUK065591
                  DELETE bz INDEX sy-tabix.                 "WKUK065591
                ELSE.                                       "WKUK065591
                  MODIFY bz FROM wa_bz INDEX sy-tabix.
                ENDIF.                                      "WKUK065591
                IF posting_document_split IS INITIAL.
                  bz_anzhl_store = bz_anzhl_store - 1.
                ENDIF.
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
*               wa_bz-ktosl = bukst_debit_fields-ktosl.     "WKUK012485
                wa_bz-ktosl = ktosl.                        "WKUK012485
*               wa_bz-koart = bukst_debit_fields-koart.     "WKUK012485
                wa_bz-koart = koart.                        "WKUK012485
                wa_bz-slbsl = bukst_debit_fields-bschl.
                wa_bz-hnbsl = bukst_credit_fields-bschl.
                wa_bz-konto = konto.
*               wa_bz-hnkto = konto.                        "WKUK012485
                wa_bz-hnkto = hnkto.                        "WKUK012485
                wa_bz-vbund = vbund.                        "WKUK029301
                wa_bz-bukrs = epk-bukst.
                wa_bz-exbel = bz-exbel.
                wa_bz-beldt = bz-beldt. "GLW note 2114815
                IF NOT posting_document_split IS INITIAL.
                  wa_bz-kokey(1) = no_new_posting_document.
                ELSE.
                  wa_bz-kokey+1(1) = 'X'."MWSKZ only for display
                ENDIF.
                wa_bz-mwskz = mwskz.
                wa_bz-txjcd = txjcd.
                wa_bz-prctr = prctr.                        "WKUK015412
                wa_bz-betrg = bz-betrg.
                wa_bz-segment = segment. "GLW note 2926207
                wa_bz-waers = bz-waers.
                wa_bz-ep_line = bz-ep_line.
                APPEND wa_bz TO bz.
                IF NOT posting_document_split IS INITIAL.
                  READ TABLE store_bz_pds
                      WITH KEY awref = wa_bz-awref
                               aworg = wa_bz-aworg.
                  MOVE-CORRESPONDING wa_bz TO store_bz_pds.
                  store_bz_pds-psref = psref.
                  store_bz_pds-pernr = pernr.
                  store_bz_pds-exbel = exbel.
                  store_bz_pds-belnr = belnr.          "Beleg pro Beleg
                  store_bz_pds-konto_sort = konto_sort.     "WKUK015412
                  store_bz_pds-prctr = prctr.               "WKUK015412
                  store_bz_pds-segment = segment. "GLW note 2926207
                  IF sy-subrc = 0.
                    MODIFY store_bz_pds INDEX sy-tabix.
                  ELSE.
                    APPEND store_bz_pds.
                  ENDIF.
                ELSE.
                  READ TABLE store_bz
                      WITH KEY awref = wa_bz-awref
                               aworg = wa_bz-aworg.
                  MOVE-CORRESPONDING wa_bz TO store_bz.
                  store_bz-psref = psref.
                  store_bz-pernr = pernr.
                  store_bz-exbel = exbel.
                  store_bz-belnr = belnr.              "Beleg pro Beleg
                  store_bz-konto_sort = konto_sort.         "WKUK015412
                  store_bz-prctr = prctr.                   "WKUK015412
                  store_bz-segment = segment.  "GLW note 2926207
                  IF sy-subrc = 0.
                    MODIFY store_bz INDEX sy-tabix.
                  ELSE.
                    APPEND store_bz.
                  ENDIF.
                ENDIF.
              ENDIF.
              IF posting_document_split IS INITIAL.
* when posting document split was not necessary for current line
* condense tax lines coming from condensed clearing accnt posting lines
                PERFORM condense_tax_lines
                    USING bukst_debit_fields-bschl
                          konto
                        vbund.                              "WKUK029301

              ENDIF.
* handle line for clearing account posting in slave company code
* (always without tax and jurisdiction code)
              IF epk-betrg GT 0.                            "WKUK012485
                koart = bukrs_credit_fields-koart.          "WKUK012485
                ktosl = bukrs_credit_fields-ktosl.          "WKUK012485
                vbund = bukrs_credit_fields-vbund.          "WKUK029301
              ELSE.                                         "WKUK012485
                koart = bukrs_debit_fields-koart.           "WKUK012485
                ktosl = bukrs_debit_fields-ktosl.           "WKUK012485
                vbund = bukrs_debit_fields-vbund.           "WKUK029301
              ENDIF.                                        "WKUK012485
*           case bukrs_debit_fields-koart.                  "WKUK012485
              CASE koart.                                   "WKUK012485
                WHEN 'S'.
                  konto = bukrs_debit_fields-hkont.
                  hnkto = bukrs_credit_fields-hkont.
                WHEN 'K'.
                  konto = bukrs_debit_fields-lifnr.
                  hnkto = bukrs_credit_fields-lifnr.
                  CLEAR vbund.                              "WKUK029301
                WHEN 'D'.
                  konto = bukrs_debit_fields-kunnr.
                  hnkto = bukrs_credit_fields-kunnr.
                  CLEAR vbund.                              "WKUK029301
              ENDCASE.

* look if new awkey for clearing account posting is necessary
*              IF bl_spl = 'B'.                              "WKUK000523
              IF bl_spl = 'B' OR split_because_country_diff NE space.  "GLW note 1555436
* look for entries with same company code                   "WKUK000523
                READ TABLE store_bz_cap
                    WITH KEY bukrs = epk-bukrs
                             psref = psref "Beleg pro CO-Obj
                             koart = koart "GLW note 2087188
                             pernr = pernr
                             exbel = exbel
                             belnr = belnr             "Beleg pro Beleg
                             konto_sort = konto_sort        "WKUK015412
                             waers = epk-waers
                             umdat = epk-umdat           "QKZ_CEE_CZ_SK
                             vat_delta = epk-vat_delta  "GLW note 1808477
                             xnegp     = epk-xnegp. "GLW note 2071158
                koart = koart.                              "WKUK012485
                IF sy-subrc = 0.                            "WKUK000523
                  subrc = 0.                                "WKUK000523
*                 exit.                         "WKUK000523 "WKUK044557
                ELSE.                                       "WKUK000523
                  subrc = 1.                                "WKUK000523
                ENDIF.                                      "WKUK000523
              ELSE.                                         "WKUK000523
* do not look for entries with same company code but for    "WKUK000523
* entries whose company code goes to same ALE-receiver      "WKUK000523
                READ TABLE bukrs_receivers                  "WKUK000523
                    INTO     wa_bukrs_receivers             "WKUK000523
                    WITH KEY bukrs = epk-bukrs.             "WKUK000523
                LOOP AT bukrs_receivers                     "WKUK000523
                    WHERE receiver =                        "WKUK000523
                       wa_bukrs_receivers-receiver.         "WKUK000523
                  READ TABLE store_bz_cap                   "WKUK000523
                    WITH KEY bukrs = bukrs_receivers-bukrs  "WKUK000523
                             psref = psref "Beleg pro CO-Obj"WKUK000523
                             pernr = pernr                  "WKUK000523
                             exbel = exbel                  "WKUK000523
                             belnr = belnr "Beleg pro Beleg "WKUK017307
                             konto_sort = konto_sort        "WKUK015412
                             waers = epk-waers              "WKUK000523
                             umdat = epk-umdat           "QKZ_CEE_CZ_SK
                             koart = koart                  "WKUK000523
                             vat_delta = epk-vat_delta      "GLW note 1808477
                             xnegp     = epk-xnegp.  "GLW note 2071158
                  IF sy-subrc = 0.                          "WKUK000523
                    subrc = 0.                              "WKUK000523
                    EXIT.                                   "WKUK000523
                  ELSE.                                     "WKUK000523
                    subrc = 1.                              "WKUK000523
                  ENDIF.                                    "WKUK000523
                ENDLOOP.                                    "WKUK000523
              ENDIF.                                        "WKUK000523
*             IF sy-subrc EQ 0.                             "WKUK000523
              IF subrc EQ 0.                                "WKUK000523
* no new posting document necessary
                n_awref  = store_bz_cap-awref.
                bz_anzhl = store_bz_cap-awlin + 1.
* look if line similar to current line is already in posting document
                READ TABLE bz INTO wa_bz
                    WITH KEY awref = n_awref
                             pernr = bz-pernr
*                            ktosl = bukrs_debit_fields-ktosl"WKUK012485
                             ktosl = ktosl                  "WKUK012485
*                            koart = bukrs_debit_fields-koart"WKUK012485
                             koart = koart                  "WKUK012485
                             slbsl = bukrs_debit_fields-bschl
                             hnbsl = bukrs_credit_fields-bschl
                             konto = konto
                             hnkto = hnkto
                             segment  = segment "GLW note 2926207
                             vbund = vbund                  "WKUK029301
                             bukrs = epk-bukrs
                             exbel = bz-exbel
                             prctr = prctr                  "WKUK015412
                             waers = bz-waers.
                IF sy-subrc = 0.
* if so, add current amount to amount of the found posting document line

                  wa_bz-betrg   = wa_bz-betrg - epk-betrg.
                  wa_bz-ep_line = bz-ep_line.
* posting document lines created by cross company postings  "WKUK065591
* are deleted if their amount is zero (looks better!)       "WKUK065591
                  IF wa_bz-betrg = 0.                       "WKUK065591
                    DELETE bz INDEX sy-tabix.               "WKUK065591
                  ELSE.                                     "WKUK065591
                    MODIFY bz FROM wa_bz INDEX sy-tabix.
                  ENDIF.                                    "WKUK065591

                ELSE.
* if not, set mark for creating new posting document line
                  subrc = sy-subrc.

* for a pretty posting document in slave company code make all clearing
* account posting lines appear behind each other at top of document.
* Therefore:
* 1. determine last clearing account posting entry in BZ
                  LOOP AT bz INTO wa_bz
                      WHERE awref = n_awref
                        AND aworg = space
                        AND ktosl = ktosl.
                    tabix = wa_bz-awlin + 1.
                  ENDLOOP.
* 2. increase line count AWLIN of all following lines by one
                  LOOP AT bz INTO wa_bz
                      WHERE awref = n_awref
                        AND aworg = space
                        AND ktosl NE ktosl.
                    wa_bz-awlin = wa_bz-awlin + 1.
                    MODIFY bz FROM wa_bz TRANSPORTING awlin.
                  ENDLOOP.
* now line with AWLIN = TABIX is free for being filled with current
* clearing account posting line

                ENDIF.
              ELSE.
* new posting document necessary for clearing account posting
* is now already set with WKUK000523                        "WKUK000523
*               subrc = sy-subrc.                           "WKUK000523
                PERFORM number_get_next.
*               N_AWREF = I_AWREF.     " WBG Hotline 175746
                bz_anzhl = 1.
                tabix = 1.             "schöner Beleg
              ENDIF.

              PERFORM administrate_buv_help                 "WKUK005642
                   USING n_awref.                           "WKUK005642

              IF subrc NE 0.
* creation of new posting document line is necessary
                CLEAR subrc.
                CLEAR wa_bz.
                wa_bz-awref = n_awref.
                wa_bz-aworg = space.
                wa_bz-awlin = tabix.
                wa_bz-pernr = bz-pernr.
                wa_bz-datv1 = bz-datv1.
                wa_bz-datb1 = bz-datb1.
                wa_bz-sgtxt = bz-sgtxt.
*               wa_bz-ktosl = bukrs_debit_fields-ktosl.     "WKUK012485
                wa_bz-ktosl = ktosl.                        "WKUK012485
*               wa_bz-koart = bukrs_debit_fields-koart.     "WKUK012485
                wa_bz-koart = koart.                        "WKUK012485
                wa_bz-slbsl = bukrs_debit_fields-bschl.
                wa_bz-hnbsl = bukrs_credit_fields-bschl.
                wa_bz-konto = konto.
*               wa_bz-hnkto = konto.                        "WKUK012485
                wa_bz-hnkto = hnkto.                        "WKUK012485
                wa_bz-vbund = vbund.                        "WKUK029301
                wa_bz-bukrs = epk-bukrs.
                wa_bz-exbel = bz-exbel.
                wa_bz-prctr = prctr.                        "WKUK015412
                wa_bz-segment = segment.  "GLW note 2926207
                wa_bz-betrg = -1 * bz-betrg.
                wa_bz-waers = bz-waers.
                wa_bz-ep_line = bz-ep_line.
                wa_bz-beldt = bz-beldt. "GLW note 2114815
                APPEND wa_bz TO bz.
                READ TABLE store_bz_cap
                    WITH KEY awref = wa_bz-awref
                             aworg = wa_bz-aworg.
                MOVE-CORRESPONDING wa_bz TO store_bz_cap.
                store_bz_cap-awlin = bz_anzhl.
                store_bz_cap-psref = psref.
                store_bz_cap-pernr = pernr.
                store_bz_cap-segment = segment. "GLW note 2926207
                store_bz_cap-exbel = exbel.
                store_bz_cap-belnr = belnr.            "Beleg pro Beleg
                store_bz_cap-konto_sort = konto_sort.       "WKUK015412
                store_bz_cap-prctr = prctr.                 "WKUK015412
                store_bz_cap-koart = koart.                 "WKUK012485
                IF sy-subrc = 0.
                  MODIFY store_bz_cap INDEX sy-tabix.
                ELSE.
                  APPEND store_bz_cap.
                ENDIF.
                ADD 1 TO bz_anzhl.     "Buchungszeilenanzahl
              ENDIF.
              clearing_account_posting = 'X'.
* create bz line for G/L account posting in company code BUKRS
              bz-bukrs = epk-bukrs.

* end of decision between cross company posting or not
            ENDIF.

            CLEAR posting_document_split.
* when posting document per CO-object, even in the clearing account
* posting document a posting document split can be necessary
            IF bl_spl = 'C' AND clearing_account_posting = 'X'.
* look if posting document split is necessary
*           case bz-koart.
              IF  cl_fitv_posting_util=>is_new_int_glvor(        "GLW note 2392616
                     i_bukrs1        = epk-bukrs
                     i_bukrs2        = epk-bukst
                     io_trip_post_fi = exit_trip_post_fi
                        ) IS INITIAL.
*           case bukrs_debit_fields-koart.                  "WKUK012485
              CASE koart.                                   "WKUK012485
                WHEN 'S'.
* clearing account is G/L account
* => no posting document split account necessary
                WHEN OTHERS.
* clearing account is vendor or customer
* => posting document split account is necessary
                  PERFORM handle_posting_document_split
                      TABLES   store_bz_cap
                               int_rot_awkey  "GLW note 2178197
                      USING    epk-bukrs
                             koart                          "WKUK012485
                               bz-koart
                               psref
                               pernr
                               exbel
                               belnr                   "Beleg pro Beleg
                               konto_sort                   "WKUK015412
                               bl_spl_temp                  "WKUK015412
                               prctr                        "WKUK015412
                                 segment
                      CHANGING mwskz
                               txjcd
                               no_new_posting_document
                               posting_document_split.
              ENDCASE.
              ENDIF.
            ENDIF.

            bz-awref = n_awref.
            bz-aworg = space.
            bz-awlin = bz_anzhl.
* AWKEY + BZ_ANZHL wird in Zuordnungstabelle geschrieben
            LOOP AT int_rot_awkey.
              int_rot_awkey-awref = n_awref.
              int_rot_awkey-aworg = space.
              int_rot_awkey-awlin = bz_anzhl.
              MODIFY int_rot_awkey.
            ENDLOOP.
            MODIFY ptrv_rot_awkey FROM TABLE int_rot_awkey.


          ELSE.
* current line is a tax line

* for posting document per company code or per CO-object a new posting
* document cannot be created via central FORM EMPTY_BZ.
* Thus the necessity of a new posting document is checked several times.
*           if bl_spl = 'B' or bl_spl = 'C'.                "WKUK002815
            IF NOT old_bukrs IS INITIAL AND lines( store_bz ) > 0. "GLW note 3116862  "nicht beim 1.mal
              READ TABLE store_bz
                  WITH KEY bukrs = epk-bukst
                           psref = psref
                           pernr = pernr                    "WKUK002815
                           exbel = exbel                    "WKUK002815
                           belnr = belnr               "Beleg pro Beleg
                           konto_sort = konto_sort          "WKUK015412
                           umdat = epk-umdat           "QKZ_CEE_CZ_SK
                           waers = epk-waers
                           vat_delta = epk-vat_delta  "GLW note 1808477
                           xnegp     = epk-xnegp "GLW note 2071158
                           beldt_split     = epk-beldt_split. "GLW note 2315344
              IF sy-subrc EQ 0.
                n_awref  = store_bz-awref.
                bz_anzhl = store_bz-awlin + 1.
              ENDIF.
            ENDIF.
*           endif.                                          "WKUK002815

            bz-awref = n_awref.
            bz-aworg = space.
            CLEAR bz-awlin.            "Not yet known, determined later

            IF receivers_lines LE 1.                        "WKUK002818
              IF epk-bukst NE epk-bukrs.                    "WKUK002818
                bz-bukrs = epk-bukst.                       "WKUK002818
              ENDIF.                                        "WKUK002818
            ENDIF.                                          "WKUK002818

* end of decision between normal lines and tax lines
          ENDIF.
          IF ( bz-betrg > 0 OR bz-betrg < 0 ) OR bz-tax_indicator EQ 'X'
*               OR bz-ktosl NE 'NAV'.                                                      "GLWEAJK019353
            OR bz-ktosl+0(2) EQ 'HR'.                                                      "GLWEH5K019383
* do not append all tax lines with zero amount. These lead to problems
            APPEND bz.                   "Buchungszeile sammeln
          ENDIF.                                                                          "GLWEAJK019353

          IF NOT bz-awlin IS INITIAL.  "Line is no tax line
            IF NOT posting_document_split IS INITIAL.
* posting document split was necessary for clearing account posting
* in slave company code (occurs only for posting document per CO-object)
* => current BZ-line is a posting document split line in slave comp.code
              READ TABLE store_bz_pds
                  WITH KEY awref = wa_bz-awref
                           aworg = wa_bz-aworg.
              MOVE-CORRESPONDING bz TO store_bz_pds.
              store_bz_pds-psref = psref.
              store_bz_pds-pernr = pernr.
              store_bz_pds-exbel = exbel.
              store_bz_pds-belnr = belnr.              "Beleg pro Beleg
              store_bz_pds-konto_sort = konto_sort.         "WKUK015412
              IF sy-subrc = 0.
                MODIFY store_bz_pds INDEX sy-tabix.
              ELSE.
                APPEND store_bz_pds.
              ENDIF.
            ELSE.
* no posting document split necessary for clearing account posting
              IF NOT clearing_account_posting IS INITIAL.
* clearing account posting was necessary for cross-company-posting
* => current BZ-line is a clearing account posting line in slave comp.co
                READ TABLE store_bz_cap
                    WITH KEY awref = bz-awref
                             aworg = bz-aworg.
                MOVE-CORRESPONDING bz TO store_bz_cap.
                store_bz_cap-psref = psref.
                store_bz_cap-pernr = pernr.
                store_bz_cap-exbel = exbel.
                store_bz_cap-belnr = belnr.            "Beleg pro Beleg
                store_bz_cap-konto_sort = konto_sort.       "WKUK015412
                store_bz_cap-koart = koart.
                IF sy-subrc = 0.
                  MODIFY store_bz_cap INDEX sy-tabix.
                ELSE.
                  APPEND store_bz_cap.
                ENDIF.
              ELSE.
* no cross-company-posting
* => current BZ-line is a normal posting line and master=slave comp.code
                READ TABLE store_bz
                    WITH KEY awref = bz-awref
                             aworg = bz-aworg.
                MOVE-CORRESPONDING bz TO store_bz.
                IF bl_spl NE 'C'.                           "WKUK002818
                  store_bz-bukrs = epk-bukst.               "WKUK008344
                ENDIF.                                      "WKUK002818
                store_bz-psref = psref.               "Beleg pro CO-Obj
                store_bz-pernr = pernr.
                store_bz-exbel = exbel.
                store_bz-belnr = belnr.                "Beleg pro Beleg
                store_bz-beldt_split = epk-beldt_split.  "GLW 2315344
                store_bz-konto_sort = konto_sort.           "WKUK015412
                IF sy-subrc = 0.
                  MODIFY store_bz INDEX sy-tabix.
                ELSE.
                  APPEND store_bz.
                ENDIF.
              ENDIF.
            ENDIF.
          ENDIF.
          old_bukrs = epk-bukrs.
* BEGIN WKUK015412
          IF ( epk-ktosl EQ 'HRP' OR epk-ktosl EQ 'HRV' ) AND  "GLW note 2379656
             epk-koart EQ 'K'   AND
             bl_k      EQ 'X'.
            bl_spl_temp = 'K'.
          ENDIF.
        ELSE.
          IF ( epk-ktosl EQ 'HRP' OR epk-ktosl EQ 'HRV' ) AND  "GLW note 2379656
             epk-koart EQ 'K'.
            CLEAR bl_spl_temp.
          ENDIF.
* END WKUK015412
        ENDIF.
        CLEAR:   int_rot_awkey,
                 remember_summed_lines.
        REFRESH: int_rot_awkey,
                 remember_summed_lines.

      ENDAT.

    ENDIF.

* in any case new posting document for change in currency. This happens
* also when LOOP AT EPK was completed and is the only posting document
* creation when posting document is per company code or per CO object
    AT END OF waers.
      PERFORM empty_bz.           "create posting document (PRIMA NOTA)
      new_awkey = 'X'.            "new posting document number required
      CLEAR: no_new_posting_document,
             no_new_posting_document_bukrs.
      CLEAR old_bukrs.
      CLEAR bukst.                                          "WKUK002815
    ENDAT.

* BEGIN WKUK015412
* posting document per vendor
    IF bl_spl_temp = 'K'.
* BEGIN WKUK015647
** new posting document for change in receipt number
*      AT END OF konto_sort.
**     at end of konto_sort.
*        PERFORM empty_bz.         "create posting document (PRIMA NOTA)
*        new_awkey = 'X'.          "new posting document number required
*        CLEAR: no_new_posting_document,
*               no_new_posting_document_bukrs.
*        CLEAR old_bukrs.
*        CLEAR bukst.
*      ENDAT.
* new posting document for change in vendor number
      IF bl_spl NE 'Q' AND next_belnr+0(1) = 'V'. "GLW note 2520560
        AT END OF konto_sort.
          PERFORM empty_bz.         "create posting document (PRIMA NOTA)
          new_awkey = 'X'.          "new posting document number required
          CLEAR: no_new_posting_document,
                 no_new_posting_document_bukrs.
          CLEAR old_bukrs.
          CLEAR bukst.
        ENDAT.
      ELSE.
        CASE bl_spl.
          WHEN 'Q'.
            AT END OF konto_sort.
              PERFORM empty_bz.         "create posting document (PRIMA NOTA)
              new_awkey = 'X'.          "new posting document number required
              CLEAR: no_new_posting_document,
                     no_new_posting_document_bukrs.
              CLEAR old_bukrs.
              CLEAR bukst.
            ENDAT.
          WHEN 'R'.
            AT END OF sexbl_konto_sort.
              PERFORM empty_bz.         "create posting document (PRIMA NOTA)
              new_awkey = 'X'.          "new posting document number required
              CLEAR: no_new_posting_document,
                     no_new_posting_document_bukrs.
              CLEAR old_bukrs.
              CLEAR bukst.
            ENDAT.
          WHEN 'P'.
            AT END OF pernr_konto_sort.
              PERFORM empty_bz.         "create posting document (PRIMA NOTA)
              new_awkey = 'X'.          "new posting document number required
              CLEAR: no_new_posting_document,
                     no_new_posting_document_bukrs.
              CLEAR old_bukrs.
              CLEAR bukst.
            ENDAT.
        ENDCASE.
      ENDIF.
* END WKUK015647
    ELSE.
* END WKUK015412

* BEGIN Beleg pro Beleg
* posting document per receipt
      IF bl_spl = 'Q' OR next_belnr+0(1) = 'V'.   "GLW note 2520560
* new posting document for change in receipt number

        AT END OF belnr.
          PERFORM empty_bz.         "create posting document (PRIMA NOTA)
          new_awkey = 'X'.          "new posting document number required
          CLEAR: no_new_posting_document,
                 no_new_posting_document_bukrs.
          CLEAR old_bukrs.
          CLEAR bukst.
        ENDAT.
      ENDIF.
* END Beleg pro Beleg

* posting document per trip
      IF bl_spl = 'R'.
* new posting document for change in trip number
        AT END OF sexbl.
          PERFORM empty_bz.         "create posting document (PRIMA NOTA)
          new_awkey = 'X'.          "new posting document number required
          CLEAR: no_new_posting_document,
                 no_new_posting_document_bukrs.
          CLEAR old_bukrs.                                  "WKUK002815
          CLEAR bukst.                                      "WKUK002815
        ENDAT.
      ENDIF.

* posting document per employee
      IF bl_spl = 'P'.
* new posting document for change in personnel number
        AT END OF pernr.
          PERFORM empty_bz.         "create posting document (PRIMA NOTA)
          new_awkey = 'X'.          "new posting document number required
          CLEAR: no_new_posting_document,
                 no_new_posting_document_bukrs.
          CLEAR old_bukrs.                                  "WKUK002815
          CLEAR bukst.                                      "WKUK002815
        ENDAT.
      ENDIF.
    ENDIF.                                                  "WKUK015412

  ENDLOOP.

  CLEAR: epk,
         store_bz,
         store_bz_cap,
         store_bz_pds,
         bukrs_debit_fields,
         bukrs_credit_fields,
         bukst_debit_fields,
         bukst_credit_fields.
  REFRESH: epk,
           store_bz,
           store_bz_cap,
           store_bz_pds.

ENDFORM.                               "CREATE_DOCUMENT_FROM_EPK



*&---------------------------------------------------------------------*
*&      Form  CLEAR_GLOBAL_VARIABLES
*&---------------------------------------------------------------------*
FORM clear_global_variables.

* clear include rprida10_40.
  CLEAR: subrc,

* Decoupling T001...
         t001_bukrs,
         t001_butxt,
         t001_ort01,
         t001_land1,
         t001_waers,
         t001_ktopl,
         t001_periv,
         t001_txjcd,
         t001_spras.

* clear include rprida11_r_40.
  CLEAR: epk_fname,
         bz_fname,
         psref_fields,
         epk,
         bz,
         wa_bz,
         old_p_r,
         new_p_r,
         bz_anzhl,
         bz_anzhl_store,
         bz_saldo,
         bz_waers,
         last_koart,
         net_amounts,
         vat_comparison,
         wa_vat_comparison,
         used_psref_fields,
* posting key which is defined by customer for VAT gross amount
         vat_bschh,
         vat_bschs,
         string80,
         remember_summed_lines.

  REFRESH: psref_fields,
           epk,
           bz,
           vat_comparison,
           used_psref_fields,
           remember_summed_lines.

  CLEAR: store_bz,
         store_bz_cap,
         store_bz_pds,

* function parameters as global data
         budat,
         soper,
         bldat,
         blart_vendor, "GLW note 2725186
         gsber_a,
         gsber_g,
         a_sgtxt,
         g_sgtxt,
         blart,
         bl_spl,
         g_verd,
         a_verd,
         replace,

* global variables
*         I_AWREF,        " WBG Hotline 175746
         n_awref,
         n_awref_store,
         awlin,
         runid,
         saprel,
         tax_item_in_tabix,
*        Begin of MAW_EUVAT
         tax_item_in_tabix_man,
*        End of MAW_EUVAT
         wa_t_ptrv_post_result,
         momagkomok,
         accts_are_equal,
         fi_acct_det_hr_append_flag,
         tabix,
         t_ptrv_rot_ep_lines,
         no_append_flag,
         append_error_line,
         append_replace_line,
         brlin,
         wa_bapiret2,
         max_pernr,
         max_exbel,
         max_belnr,                                    "Beleg pro Beleg
         rest,
         percentage,
         table_lines,
         ep_translate,
         wa_ep_translate,
         ptrv_rot_ep,
         return_table,
         return_table_lines,

* data definition of check tables
         open_item_check,
         tax_item_in,
         tax_item_out,
         tax_errors,
*        Begin of MAW_EUVAT
         tax_item_in_man,
         tax_item_out_man,
         tax_errors_man,
*        End of MAW_EUVAT
         accountingobjects,
         cobl_errors,
         fi_acct_det_hr,
         customer_selopt_tab,
         customer_result_tab,
         vendor_selopt_tab,
         vendor_result_tab,
         bukst_debit_fields,
         bukst_credit_fields,
         bukrs_debit_fields,
         bukrs_credit_fields,

         post_result,

* Fields for search help KRED/DEBI...
         dd30v_wa,
         dd31v_tab,
         dd32p_tab,
         dd27p_tab,

* buffer table...
         search_help_buffer,

* dummy parameters for BAPI-RETURN fill function
         type,
         cl,
         number,
         par1,
         par2,
         par3,
         par4,
         log_no,
         log_msg_no,
         parameter,
         row,
         field.

  REFRESH: store_bz,
           store_bz_cap,
           store_bz_pds,
           ep_translate,
           ptrv_rot_ep,
           return_table,
           open_item_check,
           tax_item_in,
           tax_item_out,
           tax_errors,
*          Begin of MAW_EUVAT
           tax_item_in_man,
           tax_item_out_man,
           tax_errors_man,
*          End of MAW_EUVAT
           accountingobjects,
           cobl_errors,
           fi_acct_det_hr,
           customer_selopt_tab,
           customer_result_tab,
           vendor_selopt_tab,
           vendor_result_tab,
           post_result,
           dd31v_tab,
           dd32p_tab,
           dd27p_tab,
           search_help_buffer.

  new_awkey = 'X'.

ENDFORM.                               " CLEAR_GLOBAL_VARIABLE

*&---------------------------------------------------------------------*
*&      Form  do_split_per_vendor
*&---------------------------------------------------------------------*
*       fills the additional document split per vendor split fields
*       new with GLWK014624
*----------------------------------------------------------------------*
FORM do_split_per_vendor.

  DATA: epk_help LIKE epk OCCURS 10 WITH HEADER LINE.
  DATA: ptrv_rot_ep_help LIKE ptrv_rot_ep OCCURS 10.
  DATA: wa_ptrv_rot_ep LIKE LINE OF ptrv_rot_ep_help.
  FIELD-SYMBOLS: <ptrv_rot_ep> LIKE ptrv_rot_ep,
                 <epk>         LIKE epk.
  DATA: BEGIN OF rot_ep OCCURS 1.                                     "GLW note 1572396
          INCLUDE STRUCTURE  wa_ptrv_rot_ep.
  DATA:   done TYPE xfeld,
          END OF rot_ep.

  DATA: index_mem LIKE sy-tabix.     "GLW note 1689890


  epk_help[] = epk[].

  rot_ep[] = ptrv_rot_ep[] .                                       "GLW note 1572396

  LOOP AT epk_help WHERE
   ( ktosl EQ 'HRP' AND
     slbsl = 21 AND   " only if vendor! GLW note 1689890
     hnbsl = 31 ) OR ktosl EQ 'HRV' . "GLW note 2379656
* loop to every HRP line
    CASE bl_spl.
      WHEN 'Q'.
        MOVE epk_help-hnkto TO epk_help-konto_sort.
      WHEN 'R'.
        MOVE epk_help-hnkto TO epk_help-sexbl_konto_sort.
      WHEN 'P'.
        MOVE epk_help-hnkto TO epk_help-pernr_konto_sort.
    ENDCASE.

    MODIFY epk FROM epk_help INDEX sy-tabix.
    index_mem = sy-tabix.                              "GLW note 1689890

    REFRESH ptrv_rot_ep_help.
*    LOOP AT ptrv_rot_ep assigning <ptrv_rot_ep> WHERE
    LOOP AT ptrv_rot_ep INTO wa_ptrv_rot_ep WHERE                      "GLW note 1572396
* now look for all ROT lines, wich are contained in the actual HRP line
      ep_line EQ epk_help-ep_line     AND
      pernr   EQ epk_help-pernr_store AND
      reinr   EQ epk_help-reinr_store.
*      EXIT.
      APPEND wa_ptrv_rot_ep TO ptrv_rot_ep_help.
    ENDLOOP.

* GLW note 1689890 begin
    IF sy-subrc IS NOT INITIAL.
      CLEAR: epk_help-konto_sort, epk_help-sexbl_konto_sort, epk_help-pernr_konto_sort.
      MODIFY epk FROM epk_help INDEX index_mem TRANSPORTING konto_sort sexbl_konto_sort pernr_konto_sort.
      CONTINUE.
    ENDIF.
* GLW note 1689890 end

    LOOP AT ptrv_rot_ep_help ASSIGNING <ptrv_rot_ep>.                   "GLW note 1572396

      LOOP AT rot_ep WHERE
* now look for all EP lines, which contain the same ROT line but are not the HRP line --> all expense lines!
        reinr    EQ <ptrv_rot_ep>-reinr    AND
        pernr    EQ <ptrv_rot_ep>-pernr    AND
        pdvrs    EQ <ptrv_rot_ep>-pdvrs    AND
        rot_line EQ <ptrv_rot_ep>-rot_line AND
        ep_line  NE <ptrv_rot_ep>-ep_line AND
        done = abap_false.                                           "GLW note 1572396

        rot_ep-done = abap_true.                                      "GLW note 1572396
        MODIFY rot_ep INDEX sy-tabix.

        LOOP AT epk WHERE
        ep_line EQ rot_ep-ep_line.

          CASE bl_spl.
            WHEN 'Q'.
              MOVE epk_help-hnkto TO epk-konto_sort.
            WHEN 'R'.
              MOVE epk_help-hnkto TO epk-sexbl_konto_sort.
            WHEN 'P'.
              MOVE epk_help-hnkto TO epk-pernr_konto_sort.
          ENDCASE.

          MODIFY epk  INDEX sy-tabix.

        ENDLOOP.
* GLW note 2506446 begin
        IF sy-subrc IS NOT INITIAL.
* no entry in epk??
* now look for all EP lines, which contain the same ROT line but are not the HRP line regardless of pdvrs--> all expense lines!
          LOOP AT rot_ep WHERE
                reinr    EQ <ptrv_rot_ep>-reinr    AND
                pernr    EQ <ptrv_rot_ep>-pernr    AND
*                        pdvrs    EQ <ptrv_rot_ep>-pdvrs    AND
                rot_line EQ <ptrv_rot_ep>-rot_line AND
                ep_line  NE <ptrv_rot_ep>-ep_line AND
                done = abap_false.

            rot_ep-done = abap_true.
            MODIFY rot_ep INDEX sy-tabix.

            LOOP AT epk WHERE
            ep_line EQ rot_ep-ep_line.

              CASE bl_spl.
                WHEN 'Q'.
                  MOVE epk_help-hnkto TO epk-konto_sort.
                WHEN 'R'.
                  MOVE epk_help-hnkto TO epk-sexbl_konto_sort.
                WHEN 'P'.
                  MOVE epk_help-hnkto TO epk-pernr_konto_sort.
              ENDCASE.

              MODIFY epk  INDEX sy-tabix.

            ENDLOOP.
          ENDLOOP.
        ENDIF.
* GLW note 2506446 end
      ENDLOOP.
    ENDLOOP.
  ENDLOOP.

  LOOP AT epk WHERE
    konto_sort       IS INITIAL AND
    sexbl_konto_sort IS INITIAL AND
    pernr_konto_sort IS INITIAL.
* here all epk lines should be determined, which are no releated to any HRP offsetting posting ---> all
* lines with HRT offsetting posting
    IF epk-belnr+0(1) NE 'V' AND bl_spl NE 'Q'.  "GLW note 2520560
      MOVE epk-belnr TO epk-konto_sort.
    ELSE.
      CASE bl_spl.
        WHEN 'Q'.
          MOVE epk-belnr TO epk-konto_sort.
        WHEN 'R'.
          MOVE epk-sexbl TO epk-sexbl_konto_sort.
        WHEN 'P'.
          MOVE epk-pernr TO epk-pernr_konto_sort.
      ENDCASE.
    ENDIF.
    MODIFY epk INDEX sy-tabix.

  ENDLOOP.

ENDFORM.                    "do_split_per_vendor

*&---------------------------------------------------------------------*
*&      Form  det_split_because_country_diff
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->VALUE      text
*      -->(BUKRS)    text
*      -->VALUE      text
*      -->(BUKST)    text
*      -->SPLIT      text
*----------------------------------------------------------------------*
FORM det_split_because_country_diff
             USING VALUE(bukrs)
                   VALUE(bukst)
                   VALUE(stxjc)
             CHANGING
                   split TYPE xfeld.

* new with GLW

  STATICS: lv_no_split TYPE i.             "GLW note 2179323
  CONSTANTS: lc_attribute TYPE ta20switch-attribute VALUE 'CA_NO_SPLIT'.
  DATA: lwa_ta20switch TYPE ta20switch. "GLW note 2179323

  DATA: bukrs_country  LIKE t001-land1,
        bukst_country  LIKE t001-land1,
        one_jur_active TYPE xfeld.

  CLEAR split.

  CHECK: bukrs NE bukst.

* GLW note 2179323 begin
  IF lv_no_split IS INITIAL. "processed the first time
    SELECT SINGLE value FROM ta20switch INTO lwa_ta20switch-value WHERE
            attribute = lc_attribute.
    IF sy-subrc IS NOT INITIAL OR lwa_ta20switch NA 'X'.
      lv_no_split = 1.  " not maintained at all or not maintained with value X.
    ELSE.
      lv_no_split = 2.  " is maintained with X --> no split.
    ENDIF.
  ENDIF.

  CHECK lv_no_split NE 2. " if it has value 2,  no split shall be carried out
* GLW note 2179323 end.

*  CHECK: stxjc IS NOT INITIAL.   "GLWEH5K022539

  CALL FUNCTION 'HRCA_COMPANYCODE_GETDETAIL'
    EXPORTING
      companycode = bukrs
    IMPORTING
      country     = bukrs_country
    EXCEPTIONS
      not_found   = 1
      OTHERS      = 2.

  CALL FUNCTION 'HRCA_COMPANYCODE_GETDETAIL'
    EXPORTING
      companycode = bukst
    IMPORTING
      country     = bukst_country
    EXCEPTIONS
      not_found   = 1
      OTHERS      = 2.

  CHECK: bukrs_country NE bukst_country.

*  IF bukst_country = 'CA'. "GLW note 2087188 "GLW note 2173203
** always if canada
*    split = 'X'.
*    RETURN.
*  ENDIF.

*  CHECK stxjc IS NOT INITIAL.  "GLW note 2087188 "GLW note 2173203

  CALL FUNCTION 'HRCA_CHECK_JURISDICTION_ACTIVE'
    EXPORTING
      i_bukrs            = bukst
    IMPORTING
      e_txjcd_active     = one_jur_active
    EXCEPTIONS
      input_incomplete   = 1
      input_inconsistent = 2
      other_error        = 3
      OTHERS             = 4.

  IF one_jur_active IS NOT INITIAL.
    split = 'X'.
    RETURN.
  ENDIF.

*  CALL FUNCTION 'HRCA_CHECK_JURISDICTION_ACTIVE'   "GLW note 2173203
*    EXPORTING
*      i_bukrs            = bukrs
*    IMPORTING
*      e_txjcd_active     = one_jur_active
*    EXCEPTIONS
*      input_incomplete   = 1
*      input_inconsistent = 2
*      other_error        = 3
*      OTHERS             = 4.
*
*  IF one_jur_active IS NOT INITIAL.
*    split = 'X'.
*  ENDIF.

ENDFORM.                    "det_split_because_country_diff