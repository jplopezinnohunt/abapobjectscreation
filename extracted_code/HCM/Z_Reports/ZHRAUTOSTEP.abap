*&---------------------------------------------------------------------*
*& Report  ZHRAUTOSTEP                                                 *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*
REPORT  ZHRAUTOSTEP                             .
include LXPADTAP.
DATA: BEGIN OF TBLGART OCCURS 20,
        SEQNR(3),                      " Fuer die Reihenfolge der LGART
        LGART LIKE P0008-LGA01,        " Lohnarten fuer P0008
        LGMOD,                         " Modus der Lohnart
        LGTXT LIKE T512T-LGTXT,        " Lohnartentext aus T512T
        OPKEN LIKE P0008-OPK01,        " OPKEN aus T511
        BETRG LIKE P0008-BET01,
        WAERS LIKE P0008-WAERS,                             "XPSK015490
        INDBW LIKE P0008-IND01,        " Kennzeichen fuer indirekte Bew
        ANZHL LIKE P0008-ANZ01,
        EITXT LIKE Q0008-EITXT,        " Externe Einheiten. "K11K099467
        EIN   LIKE T538T-ZEINH,        " Interne Einheiten.
        ZEINH LIKE T511-ZEINH,         " Gueltigkeit von ANZ/EIN.
        MODNA LIKE T511-MODNA,         " Modulname fuer indirekte Bew.
        MOD02 LIKE T511-MOD02,         " Ueberschreibbarkeit Basisbez.
        KOMBI LIKE T511-KOMBI,         " Gueltige Eingabekombination.
        ADSUM(1),
      END OF TBLGART.
tables : p0007, p0001, p0230 .
FORM prg_compute_trfst_pai  USING    P_ACTUAL
                                 P_NEW
                                 p_betrg
                                 p_date
                                 p_trfst
                                 p_pernr
                                 p_massn
                                 p_massg
                                 cprel structure prelp
                                 psyst structure psyst
                                 wg_message.
*AAHOUNOU06112013
  Data tag_m . " permet savoir si on a utilisé la table T510 ou T510M pour ne pas av
  clear tag_m.
  Data wa510M TYPE T510M.
* Get hire date
  data wa_hire_date like HRMS_BIW_IO_OCCUPANCY-NCSDATE.
  clear wa_hire_date.
  CALL FUNCTION 'HR_ENTRY_DATE'
      EXPORTING
        persnr                     = cprel-pernr
*        RCLAS                      =
*        BEGDA                      = '18000101'
*        ENDDA                      = '99991231'
*        VARKY                      =
     IMPORTING
        entrydate                  = wa_hire_date
*        TABLES
*        ENTRY_DATES                =
   EXCEPTIONS
     entry_date_not_found       = 1
     pernr_not_assigned         = 2
     OTHERS                     = 3.
*AAHOUNOU06112013
  data s0008 like p0008.
*save actual grade/level
  data : begin of w_actual,
   trfar like p0008-trfar,
   trfgb like p0008-trfgb,
   trfgr like p0008-trfgr,
   trfst like p0008-trfst,
   trfg2 like p0008-trfgr,
   trfs2 like p0008-trfst,
  end of w_actual.
  data w_grad_mod like p0008-trfgr.
  data w_newstr like w_actual.
  data w_veil type d.
  w_veil = psyst-begda - 1.
  CONSTANTS: INITIAL VALUE '3',
           NOP(3)  VALUE 'NOP'.
  PERFORM READ_INFOTYPE(SAPFP50P)                           "N0741079
  USING cprel-pernr '0008'           "pernr infty           "N0741079
        SPACE SPACE                  "subty objps           "N0741079
        SPACE                        "sprps                 "N0741079
        w_veil w_veil                "begda endda           "N0741079
        INITIAL                      "record-selection      "N0741079
        NOP                          "authority-flag        "N0741079
        s0008.                       "infty-structure       "N0741079
  w_actual-trfar = s0008-trfar.
  w_actual-trfgb = s0008-trfgb.
  w_actual-trfgr = s0008-trfgr.
  w_actual-trfst = s0008-trfst.
  w_grad_mod = cprel-data1+4(8).
  data w_lgart like p0008-lga01.
  data w_lgart1 like p0008-lga01.
  data w_betrg like p0008-bet01.
  data w_betac like p0008-bet01.    " actual salary
  data w_ind like p0008-ind01.
  data w_0008 like p0008.
  data w_trfst like p0008-trfst.
  CALL METHOD CL_HR_PNNNN_TYPE_CAST=>PRELP_TO_PNNNN
    EXPORTING
      PRELP = cprel
    IMPORTING
      PNNNN = w_0008.
  DATA: BEGIN OF TBINDBW OCCURS 20,                         "QEAK70329
          SEQNR(3).                        "sequence number
          INCLUDE STRUCTURE PTBINDBW.                       "QNOK062433
  DATA: END OF TBINDBW.
  data indbw_end_out type d.
  perform FILL_TBLGART tables tblgart
                            using s0008 psyst.
  loop at tblgart.
    move-corresponding tblgart to TBINDBW.
    append TBINDBW.
  endloop.
  PERFORM READ_INFOTYPE(SAPFP50P)                           "N0741079
    USING cprel-pernr '0007'           "pernr infty           "N0741079
          SPACE SPACE                  "subty objps           "N0741079
          SPACE                        "sprps                 "N0741079
          w_veil w_veil                "begda endda           "N0741079
          INITIAL                      "record-selection      "N0741079
          NOP                          "authority-flag        "N0741079
          P0007.                       "infty-structure       "N0741079
  data w_trfkz like t503-trfkz.
  PERFORM READ_INFOTYPE(SAPFP50P)                           "N0741079
    USING cprel-pernr '0001'           "pernr infty           "N0741079
          SPACE SPACE                  "subty objps           "N0741079
          SPACE                        "sprps                 "N0741079
          w_veil w_veil                "begda endda           "N0741079
          INITIAL                      "record-selection      "N0741079
          NOP                          "authority-flag        "N0741079
          P0001.                       "infty-structure       "N0741079
  select single trfkz into w_trfkz from t503 where persg = p0001-persg and
  persk = p0001-persk.
  CALL FUNCTION 'RP_EVALUATE_INDIRECTLY_P0008'
    EXPORTING
      conv_curr                    = ' '                    "HCMOPS2737
      msgflg                       = 'S'                    "XPS-42
      ptclas                       = 'A'                    "N0410732
      ppernr                       = cprel-pernr
      pmolga                       = 'UN'
      pbegda                       = w_veil
      pp0001                       = p0001
      pp0007                       = p0007
      pp0008                       = s0008
      pp0230                       = p0230                  "XPMK035581
*     pp0304                       = p0304                             "MERP30K09797
    IMPORTING
      pendda                       = indbw_end_out
    TABLES
      ptbindbw                     = tbindbw
    EXCEPTIONS
      error_at_indirect_evaluation = 1.
  LOOP AT tblgart WHERE lgart NE space
                    AND indbw EQ 'I'.
    LOOP AT tbindbw WHERE lgart EQ tblgart-lgart.
      MOVE tbindbw-waers TO tblgart-waers.                  "XPSK015490
      MOVE tbindbw-betrg TO tblgart-betrg.
      MOVE tbindbw-anzhl TO tblgart-anzhl.              "YBBP30K107440
      MOVE tbindbw-zeinh TO tblgart-ein.                    "MELN956275
    endloop.
    modify tblgart.
  endloop.
* type of promotion 2-2/2-1/1-1
  data w_begda type begda.
  data w_persg like p0001-persg.
  data w_promty.               " Type de promotion.
  w_begda = psyst-begda - 1.
  select single persg from pa0001 into w_persg where pernr = w_0008-pernr and
                                 begda le w_begda and
                                 endda ge w_begda.
  if sy-subrc = 0.
    if w_persg ne psyst-persg.
      w_promty = '1'.
    else.
      w_promty = '2'.
    endif.
  else.
    message 'cannot find the type of promoation G-G or G-P or P-P' type 'S'.
    wg_message = 'cannot find the type of promoation G-G or G-P or P-P'.
    export wg_message to memory id 'WG_MESSAGE'.
    exit.
  endif.
 do 20 times varying w_lgart from s0008-lga01 next s0008-lga02
              varying w_betrg from s0008-bet01 next s0008-bet02
              varying w_ind from s0008-ind01 next s0008-ind02.
    case w_lgart.
      when '0032'.
        if w_ind ne 'I'.
          w_betac = w_betrg.
        else.
          loop at tblgart where lgart = w_lgart.
            w_betac = tblgart-betrg.
          endloop.
        endif.
    endcase.
  enddo.
  if w_0008 is not initial and
  w_0008-bsgrd ne '100'.
    w_betac = w_betac * ( 100 / s0008-bsgrd ).
  endif.
*  data w_betrg type betrg.
  data w_510 like t510.
  data w_510M like t510M.
*AAHOUNOU06112013
*  find the wage type 0030 or 0040 that matchs the actual salary
  select single * from t510 into w_510 where trfar = w_actual(2) and
                           trfgb = w_actual+2(2) and
                           trfgr = w_actual+4(8) and
                           trfst = w_actual+12(2) and
                           begda le w_veil and
                           endda ge w_veil and
                           betrg = w_betac and
                           molga = 'UN' and
                           trfkz = w_trfkz.
  if sy-subrc = 0 and w_510-betrg is not initial.
    tag_m = 1.
    w_lgart = w_510-lgart.
  else.
    tag_m = 2.
    select  * from t510M into wa510M
                  where MOLGA = 'UN'
                  AND   TRFAR =  w_actual(2)
                  AND   TRFGB =  w_actual+2(2)
                  AND   TRFKZ =  w_trfkz
                  AND   TRFGR = w_actual+4(8)
                  AND   TRFST = w_actual+12(2)
*                    AND   LGART = LGART
                  AND   EHIRE >=  wa_hire_date
                  AND   BEGDA <= w_veil
                  AND   ENDDA >= w_veil
                  AND   BETRG = w_betac
                  ORDER BY EHIRE.
      EXIT.
    ENDSELECT.
    IF sy-subrc eq 0.
      w_lgart = wa510M-lgart.
    ELSE.
*    Message 'wage type 0030 or 0040 not found in T510 for actual salary' type 'S' .
*    wg_message = 'wage type 0030 or 0040 not found in T510 for actual salary'.
      export wg_message to memory id 'WG_MESSAGE'.
      exit.
    ENDIF.
  endif.
*AAHOUNOU06112013
*****************
  clear w_betac.
  if w_promty = '1'.
    do 20 times varying w_lgart1 from s0008-lga01 next s0008-lga02
                 varying w_betrg from s0008-bet01 next s0008-bet02
                 varying w_ind from s0008-ind01 next s0008-ind02.
      case w_lgart1.
        when '0032' or '0270' or '0280' or '0024'.
          if w_ind ne 'I'.
            w_betac = w_betac + w_betrg.
          else.
            loop at tblgart where lgart = w_lgart1.
              w_betac = w_betac +  tblgart-betrg.
            endloop.
          endif.
      endcase.
    enddo.
  else.
    do 20 times varying w_lgart1 from s0008-lga01 next s0008-lga02
                varying w_betrg from s0008-bet01 next s0008-bet02
                varying w_ind from s0008-ind01 next s0008-ind02.
      case w_lgart1.
        when '0032'.
          if w_ind ne 'I'.
            w_betac = w_betrg.
          else.
            loop at tblgart where lgart = w_lgart1.
              w_betac = tblgart-betrg.
            endloop.
          endif.
      endcase.
    enddo.
  endif.
  if w_0008 is not initial and
  w_0008-bsgrd ne '100'.
    w_betac = w_betac * ( 100 / s0008-bsgrd ).
  endif.
* delta calculation on the actual pay scale group.
  data w_cp type i.
  data line type i.
  data i_510 like t510 occurs 0 with header line.
*AAHOUNOU06112013
  If tag_m = 1.
    select * from t510 into table i_510 where trfar = w_actual(2) and
                           trfgb = w_actual+2(2) and
                           trfgr = w_actual+4(8) and
*                           trfst = w_actual+12(2) and
                           begda le w_veil and
                           endda ge w_veil and
                           lgart = w_lgart and
                           molga = 'UN'  and
                           trfkz = w_trfkz
                           and betrg is not null.
*  describe table i_510 lines line.
*  IF line ne 0.
    loop at i_510.
      if not ( i_510-trfst co '0123456789' ).
        delete i_510.
      endif.
    endloop.
    sort i_510 by betrg ascending.
    loop at i_510 into w_510 .
      w_cp = w_cp + 1.
      if w_cp = 2.
        w_betrg = w_510-betrg - w_betrg.
        exit.
      endif.
      w_betrg = w_510-betrg.
    endloop.
*  if w_cp lt 2.
*    message 'pay scale step calculation failed' type 'S'.
*    wg_message = 'pay scale step calculation failed'.
*    export wg_message to memory id 'WG_MESSAGE'.
*    exit.
*  endif.
  ELSEIF tag_m = 2.
    data i_510M like t510M occurs 0 with header line.
    select  * from t510M into table i_510M
                 where MOLGA = 'UN'
                 AND   TRFAR =  w_actual(2)
                 AND   TRFGB =  w_actual+2(2)
                 AND   TRFKZ =  w_trfkz
                 AND   TRFGR = w_actual+4(8)
*                  AND   TRFST = w_actual+12(2)
                   AND   LGART = w_lgart
                 AND   EHIRE >=  wa_hire_date
                 AND   BEGDA <= w_veil
                 AND   ENDDA >= w_veil
                 AND   BETRG is not null
                 ORDER BY EHIRE betrg ascending.
    describe table i_510M lines line.
    IF line ne 0.
      loop at i_510M.
        if not ( i_510M-trfst co '0123456789' ).
          delete i_510M.
        endif.
      endloop.
*      sort i_510M by betrg ascending.
      loop at i_510M into w_510M .
        w_cp = w_cp + 1.
        if w_cp = 2.
          w_betrg = w_510M-betrg - w_betrg.
          exit.
        endif.
        w_betrg = w_510M-betrg.
      endloop.
      if w_cp lt 2.
        message 'pay scale step calculation failed' type 'S'.
        wg_message = 'pay scale step calculation failed'.
        export wg_message to memory id 'WG_MESSAGE'.
        exit.
      endif.
    ENDIF.
  ENDIF.
*AAHOUNOU06112013
* new salary
  w_betac = w_betac + 2 * w_betrg.
* rechercher le grade du nouveau psote
  data w_trfg1 like p1005-trfg1.
  data w_trfg2 like p1005-trfg2.
  perform get_grade using p_date
                          p_pernr
                          w_trfg1
                          w_trfg2.
  CALL METHOD zhr_it0008=>get_default_tarif
    EXPORTING
      ipsyst = psyst
    CHANGING
      innnn  = cprel.
  w_newstr = cprel-data1(14).
* find de new step in the new pay scale group
  if w_promty = '1'.
    w_lgart = '0030'.
    data w_waers like p0008-waers.
    data w_message_handler type ref to IF_HRPA_MESSAGE_HANDLER.
    DATA message_list     TYPE REF TO cl_hrpa_message_list.
    CREATE OBJECT message_list.
    w_message_handler = message_list.
*    CREATE OBJECT w_message_handler.
*AAHOUNOU21092009
*Prendre le taux de change au 15 du mois de la date de l'action
    data p_date15 like sy-datum.
    move  p_date to p_date15.
    move '15' to p_date15+6(2).
*AAHOUNOU21092009
    w_waers = s0008-waers.
    CALL FUNCTION 'HR_ECM_CONVERT_CURRENCY'
      EXPORTING
        OLD_AMOUNT      = w_betac
        OLD_CURRE       = w_waers
        NEW_CURRE       = 'USD'
*AAHOUNOU21092009
*        CONVERSION_DATE = p_date
        CONVERSION_DATE = p_date15
*AAHOUNOU21092009
        MESSAGE_HANDLER = w_message_handler
      IMPORTING
        new_amount      = w_betac.
* Prendre en compte le coef. du poste adjustment
    data w_0960 type p0960.
    DATA g_ds_tab TYPE HRPADUN_DS.
    DATA l_is_ok TYPE boole_d.
    DATA l_ds TYPE PUN_DS.
    DATA g_message_handler TYPE REF TO cl_hrpa_message_list.
    DATA g_read_infotype TYPE REF TO if_hrpa_read_infotype.
    CREATE OBJECT g_message_handler.
    CALL METHOD cl_hrpa_masterdata_factory=>get_read_infotype
      IMPORTING
        read_infotype = g_read_infotype.
    CALL METHOD cl_hrpa_infotype_0960=>get_ds_tab
      EXPORTING
        pernr           = cprel-pernr
        read_infotype   = g_read_infotype
        message_handler = g_message_handler
      IMPORTING
        ds_tab          = g_ds_tab
        is_ok           = l_is_ok.
    CALL METHOD CL_HRPA_INFOTYPE_0960=>bl_ds
      EXPORTING
        date            = w_veil
        ds_tab          = g_ds_tab
        message_handler = g_message_handler
      IMPORTING
        ds              = l_ds.
    tables T7UNPAD_DSPA.
    select single * from T7UNPAD_DSPA where molga = 'UN' and
                                     dstat = l_ds-dstat and
                                     bentl le p_date and
                                     eentl ge p_date and
                                     begda le p_date and
                                     endda ge p_date and
                                     trfkz  = w_trfkz.
    if sy-subrc = 0 .
      w_betac = w_betac * 100 / ( 100 + T7UNPAD_DSPA-PAMUL ).
    else.
      message 'Post Adjustment Multiplier not found in T77UNPAD_DSPA' type 'S'.
      wg_message = 'Post Adjustment Multiplier not found in T77UNPAD_DSPA'.
      export wg_message to memory id 'WG_MESSAGE'.
      exit.
    endif.
  endif.
  select single trfkz into w_trfkz from t503 where persg = psyst-persg and
  persk = psyst-persk.
  clear w_510.
*AAHOUNOU06112013
  CASE tag_m.
    WHEN 1.
      select * from t510 into w_510 where trfar = w_newstr(2) and
                             trfgb = w_newstr+2(2) and
                             trfgr eq w_grad_mod and
*                           trfgr le w_newstr+14(8) and
                             begda le p_date and
                             endda ge p_date and
                             betrg ge w_betac and
                             lgart = w_lgart and
                             molga = 'UN' and
                             trfkz = w_trfkz and
                             ( trfst like '%0%' or
                                 trfst like '%1%' )
                               order by betrg ascending.
        exit.
      endselect.
      if w_510  is not initial.
        p_trfst = w_510-trfst.
*      if p_massn eq 'V4' and ( p_massg eq '01' or p_massg eq '02' or p_massg eq '09
*        cprel-data1+12(2) = w_510-trfst.
*      elseif p_massn eq 'V5' and ( p_massg eq '01' or p_massg eq '05' or p_massg eq
        cprel-data1+12(2) = w_510-trfst.
        cprel-data1+4(8) = w_510-trfgr.
        clear wg_message.
        export wg_message to memory id 'WG_MESSAGE'.
      endif.
    WHEN 2.
      clear w_510M.
      select  * from t510M into w_510M
                  where MOLGA = 'UN'
                  AND   TRFAR =  w_newstr(2)
                  AND   TRFGB =  w_newstr+2(2)
                  AND   TRFKZ =  w_trfkz
                  AND  ( trfst like '%0%' or
                             trfst like '%1%' )
                  AND   TRFGR = w_grad_mod
                  AND   LGART = w_lgart
                  AND   EHIRE >=  wa_hire_date
                  AND   BEGDA <= p_date
                  AND   ENDDA >= p_date
                  AND   BETRG ge w_betac
                  ORDER BY EHIRE ascending betrg ascending.
        EXIT.
      ENDSELECT.
      if w_510M  is not initial.
        p_trfst = w_510M-trfst.
        cprel-data1+12(2) = w_510M-trfst.
        cprel-data1+4(8) = w_510M-trfgr.
        clear wg_message.
        export wg_message to memory id 'WG_MESSAGE'.
      else.
        message 'No pay scale level matchs the new salary int tables T510 and T510M'
        wg_message = 'No pay scale level matchs the new salary in tables T510 and T5
        export wg_message to memory id 'WG_MESSAGE'.
        exit.
      endif.
*AAHOUNOU06112013
*    skip.
    WHEN OTHERS.
  endcase.
*      else.
*      cprel-data1+12(2) = s0008-trfst.
*      endif.
endform.
FORM FILL_TBLGART tables tblgart structure tblgart
                  using p0008 structure p0008
                        psyst structure psyst.
  DATA: BEGIN OF STR_P0008,
          LGART LIKE P0008-LGA01,
          BETRG LIKE P0008-BET01,
          ANZHL LIKE P0008-ANZ01,
          EIN   LIKE P0008-EIN01,
          OPKEN LIKE P0008-OPK01,
        END OF STR_P0008.
  DATA: TBLGART-COUNT(2) TYPE P.
  DATA: STR_INDBW LIKE P0008-IND01.                         "QNUK53916
  data w_veil type d.
  w_veil  = psyst-begda - 1.
  REFRESH TBLGART.
  TBLGART-COUNT = 0.
  DO 20 TIMES
     VARYING STR_P0008-LGART FROM P0008-LGA01                 "XPS-UNI
                             NEXT P0008-LGA02                 "XPS-UNI
     VARYING STR_P0008-BETRG FROM P0008-BET01                 "XPS-UNI
                             NEXT P0008-BET02                 "XPS-UNI
     VARYING STR_P0008-ANZHL FROM P0008-ANZ01                 "XPS-UNI
                             NEXT P0008-ANZ02                 "XPS-UNI
     VARYING STR_P0008-EIN   FROM P0008-EIN01                 "XPS-UNI
                             NEXT P0008-EIN02                 "XPS-UNI
     VARYING STR_P0008-OPKEN FROM P0008-OPK01                 "XPS-UNI
                             NEXT P0008-OPK02                 "XPS-UNI
     VARYING STR_INDBW FROM P0008-IND01 NEXT P0008-IND02.   "QEAK70329
    IF STR_P0008-LGART NE SPACE.                            "K025575
      CLEAR   TBLGART.
      TBLGART-WAERS = P0008-WAERS.                          "XPSK015490
      MOVE-CORRESPONDING STR_P0008 TO TBLGART.
      MOVE STR_INDBW TO TBLGART-INDBW.                      "QEAK62419
      tables t511.
      SELECT * FROM T511 UP TO 1 ROWS
                         WHERE MOLGA = 'UN'
                         AND   LGART = tbLGART-lgart
                         AND   ENDDA >= w_veil
                         AND   BEGDA <= w_veil.
        EXIT.
      ENDSELECT.
      if sy-subrc = 0.
        MOVE-CORRESPONDING t511 TO TBLGART.
      endif.
      IF PSYST-IOPER = INSERT OR PSYST-IOPER = COPY.        "XPSK065767
        IF TBLGART-BETRG EQ 0 AND TBLGART-MODNA NE SPACE.   "QEAK62419
          TBLGART-INDBW = 'I'.                              "QEAK62419
        ELSE.                                               "QEAK62419
          TBLGART-INDBW = SPACE.                            "QEAK62419
        ENDIF.                                              "QEAK62419
      ELSE.                                                 "XPSK065767
        IF     TBLGART-BETRG EQ 0
           AND TBLGART-INDBW NE 'I'
           AND TBLGART-MODNA NE SPACE.
          MESSAGE W839(RP) WITH TBLGART-LGART.
        ENDIF.
      ENDIF.                                                "XPSK065767
      APPEND TBLGART.
      ADD 1 TO TBLGART-COUNT.
    ENDIF.
  ENDDO.
ENDFORM.                    "FILL_TBLGART
FORM get_grade  USING    P_DATE
                         P_PERNR
                         P_trfg1
                         p_trfg2.
  data w_plans like p0001-plans.
  data w_trfg1 like p1005-trfg1.
  data w_trfg2 like p1005-trfg2.
  select single plans into w_plans from pa0001 where pernr = p_pernr and
                                 begda le p_date and
                                 endda ge p_date.
  if sy-subrc = 0.
    select single trfg1 trfg2 into (w_trfg1, w_trfg2) from hrp1005 where objid = w_p
                                                                         begda le p_
                                                                         endda ge p_
    p_trfg1 = w_trfg1 .
    p_trfg2 = w_trfg2 .
  endif.
ENDFORM.                    " get_grade