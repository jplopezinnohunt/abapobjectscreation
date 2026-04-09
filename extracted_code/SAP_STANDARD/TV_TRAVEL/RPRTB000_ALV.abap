* 6.00
* KCNE8H2537190 21092017 Reiseländerversion Großbritannien: Verpflegungsabrechnung
*                        bei Reisen mit einem Reise-Ende nach 20 Uhr [note 2537190]
* KCNEHI2290457 22032016 Kanada: Wegstrecken mit Tax Jurisdiction Code [note 2290457]
* QKZN1950679   13012014 German travel requirement 2014 [1950679]
* KCNEH41826920 26022013 PS DE: Abzüge bei reduziertem Tagegeld/Auslandsreisen
*                        Teil 2 [note 1826920]
* KCNP2H1686404 17022012 P.S.: Frankreich: Alternative
*                        Verpflegungspauschale [note 1686404]
* KCNP2H1677116 24012011 IT: Fehlende Konstante 'MAXRE' führt zur
*                        Ablehnung [note 1677116]
* KCNEH51581544 20042011 Falsche Behandlung von Mahlzeiten im
*                        Unterkunftsbeleg [note 1581544]
* QKZEH6K018668 05072011 NO: Per diem last day international trip [1606761]
* VRD_CEE_UA    28072010 UA-Version, Deduction
* VJMK1378820 08/09  TGV: untertägiges Trennungsreisegeld
* QKZ_CEE_CZ_SK country version CZ and SK
*
* 6.04
* GLWE34K018616 03082009 problems with altern. wage types(1372612)
* GLWE34K016560 24042009 VERZU and ENTKM in Morei ne 01(1333109)
* MAWEH4K020779 03022009 Fehlerbehandlung in Report RPRTEC00 [note 1301495]
* VJMK128627 12/08 Änderung Versteuerung Trennungsgeld
* KCNEH4K014429 11072008 AT: Konstante REIES und Altreisen vor dem
*                        Jahr 2008                      [note  1230195]
* MAWEH4K005054 15052008 RPRTEC00: Sperren beim Fortschreiben des
*                        Abrechnungsstatus               [note 1160561]
* 6.0
* XCIN940846 0406 Verrechnung: Sachbezüge mit Werbungskosten (N:940846)
* VJMK1043474 04/07 Minimumsregel Sachbezug mit REIMN (n 1043474)
* QKZPTHK001053 16012007 Private receipts
* QIZPENK003159 22042005 Estimated costs for FM implemented
* 5.0
* KCNP3HK010787 05052006 NO: Konstante MAXBR nicht mehr gültig
*                        [note 942758]
* XCIN940846 0406 Verrechnung: Sachbezüge mit Werbungskosten (N:940846)
* VJMK902193 11-2005 Sonderregel Essensbon P.S.
* VJMKPSABZ01 Abzug NRW (Note: 828721 T: K005313)
* VJMKTGST03  Versteuerung Trennungsgeld anpassen
* QIZP3HK001038 01072004 SELECT statement corrected [751152]
* QIZP3HK000041 24052004 PERFORM Ablehnung adapted to 'PR_WEB...'
* MAWSLNK005517 28042004 RPRTEC00: Fehlerhafter Aufruf der Form-Routine
*                        RE706B4 [note 732121]
* QIZK082944 11032004 simulation via Face enabled
* 2.0
* VJMKBGC01 7/2003  Sachbezugswert generieren
* 1.10
* XCIPSDETRG Einbau der Trennungsgeldperioden
* XOWALNK057099 25062001 Error when reading constants (note 414880)
* QKZALNK000728 22062001 Unicodeumstellung
* 4.6C
* XOWL9CK022870 12092000 Mixed Currency in T706H - note 173981 (2)
* QIZL9CK006981 17042000 Transaction TRIP_EWT created
* WTLAHRK064642 25111999 Mixed Currency in T706H CSS 451073 1999
* 4.6B
* WBGPH9K009191 14061999 Start im Job verhinderte Sperren;

* 4.6A
* YEKAHRK049955 03291999 New enqueue logic
* QIZK049366 12041999 simulation for multiple trips
* XOWAHRK033175 14011999 D-maximum amount for receipts - form re706b2
* ABSBKK900038  new table-fields T702G in country version Norway
* 4.0C
* QIZPH4K003787 080698 Tec-Errors during simulation via memory
* WTLAHRK004776 110398 Erweiterung der T706S
* KI4
* 4.6B
* XCIKI4PSCO_CONST Korrektur Konstantenlesen
* KI4/4.5B
* XCIKI4PSOV02  06/99  Leseroutine der Konstanten erweitert/korrigiert
*

*---------------------------------------------------------------------*
*    Hilfsprogramme zum Tabellenlesen (ATAB)                          *
*    und                                                              *
*    Ablehnungsroutinen                                               *
*---------------------------------------------------------------------*

*---------------------------------------------------------------------*
*       FORM RE001                                                    *
*---------------------------------------------------------------------*
FORM  re001
USING VALUE(bukrs)
      ort01 ktopl land1 waers periv spras.

  CHECK t001_bukrs <> bukrs.

  CALL FUNCTION 'HRCA_COMPANYCODE_GETDETAIL'
    EXPORTING
      companycode = bukrs
      language    = sy-langu
    IMPORTING
      comp_name   = t001_butxt
      city        = t001_ort01
      country     = t001_land1
      currency    = t001_waers
      langu       = t001_spras
      chrt_accts  = t001_ktopl
      fy_variant  = t001_periv
    EXCEPTIONS
      not_found   = 1
      OTHERS      = 2.

  IF sy-subrc <> 0.
    NEW-PAGE.
    SKIP.
    WRITE: / text-r88, bukrs.
    PERFORM ablehnung.
  ENDIF.

  ort01 = t001_ort01.
  ktopl = t001_ktopl.
  land1 = t001_land1.
  waers = t001_waers.
  periv = t001_periv.
  spras = t001_spras.

* QIZ Quick and dirty!
  t001_bukrs = bukrs.

ENDFORM.                                                    "re001

*---------------------------------------------------------------------*
*       FORM RE001P                                                   *
*---------------------------------------------------------------------*
FORM  re001p
USING VALUE(werks) VALUE(btrtl).
  IF t001p-werks <> werks
  OR t001p-btrtl <> btrtl.
    t001p = space.
    t001p-werks = werks.
    t001p-btrtl = btrtl.
    *t001p = t001p.
    SELECT SINGLE * FROM t001p WHERE werks = werks
                               AND   btrtl = btrtl.
    IF sy-subrc NE 0.
      t001p = space.
      NEW-PAGE.
      SKIP.
      WRITE: / text-p13, 'T001P', *t001p.
      PERFORM ablehnung.
    ENDIF.
  ENDIF.
ENDFORM.                               "END OF FORM RE001P

*---------------------------------------------------------------------*
*       FORM RE500P                                                   *
*---------------------------------------------------------------------*
FORM re500p USING persa.
  CHECK t500p-persa <> persa.
  SELECT SINGLE * FROM t500p WHERE persa = persa.
  IF sy-subrc <> 0.
    t500p = space.
    NEW-PAGE.
    SKIP.
    WRITE: / text-p13, 'T500P', persa.
    PERFORM ablehnung.
  ENDIF.
ENDFORM.                                                    "re500p

*---------------------------------------------------------------------*
*       FORM RE511K                                                   *
*QKZK007494 Routine ersetzt durch ret706_const = neue Konstanten Tab. *
*---------------------------------------------------------------------*
*FORM  RE511K
*USING VALUE(MOLGA) VALUE(KONST) VALUE(DATUM)
*      ENDDA BEGDA KWERT.
*
*  IF T511K-MOLGA <> MOLGA OR
*     T511K-KONST <> KONST OR
*     NOT ( DATUM BETWEEN T511K-BEGDA AND T511K-ENDDA ).
*
*    T511K = SPACE.
*    T511K-MOLGA = MOLGA.
*    T511K-KONST = KONST.
*    T511K-ENDDA = DATUM.
*     *T511K = T511K.
*    SELECT * FROM T511K WHERE MOLGA  = MOLGA
*                        AND   KONST  = KONST
*                        AND   ENDDA >= DATUM
*                        AND   BEGDA <= DATUM.
*      EXIT.
*    ENDSELECT.
*
*    IF SY-SUBRC <> 0 OR
*       T511K-MOLGA <> MOLGA OR
*       T511K-KONST <> KONST OR
*       NOT ( DATUM BETWEEN T511K-BEGDA AND T511K-ENDDA ).
** Constant REIFA not found, use initial value '1'
*      IF KONST = 'REIFA'.
*        KWERT = T511K-KWERT = '1'.
*        ENDDA = DATUM.
*        BEGDA = DATUM.
*        EXIT.
*      ENDIF.
*      T511K = SPACE.
*      NEW-PAGE.
*      SKIP.
*      WRITE: / TEXT-P12, 'T511K', *T511K.
*      PERFORM ABLEHNUNG.
*    ENDIF.
*  ENDIF.
*
*  ENDDA = T511K-ENDDA.
*  BEGDA = T511K-BEGDA.
*  KWERT = T511K-KWERT.
*ENDFORM.                               "END OF RE511K

*---------------------------------------------------------------------*
*       FORM RE706A                                                   *
*---------------------------------------------------------------------*
FORM  re706a
USING VALUE(morei) VALUE(inaus) VALUE(abzkz)
      VALUE(kzrea) VALUE(kztkt)
      VALUE(erkla) VALUE(ergru) VALUE(datum)
      endda begda kzspa abzpz kzfpa abzfa waerspz waersfa.

  DATA: anmin LIKE t706v-ptrv_anmin,                     "QKZ_CEE_CZ_SK
        anstd LIKE argu-anstd.                           "QKZ_CEE_CZ_SK
  DATA: abzci(1) TYPE n.                                 "VRD_CEE_RU

* Zwischenpufferung holen
  CASE abzkz.
    WHEN 'F'.
      t706a = *t706a_f.
    WHEN 'M'.
      t706a = *t706a_m.
    WHEN 'E'.
      t706a = *t706a_e.
    WHEN 'A'.
      t706a = *t706a_a.
    WHEN 'B'.
      t706a = *t706a_b.
    WHEN 'R'.
      t706a = *t706a_r.
    WHEN OTHERS.
  ENDCASE.

* Begin VRD_CEE_PL - 121218 note 1796423
* Begin VRD_CEE_PL - 130219 note 1824167
* IF wa_head-molga = '46' AND inaus = 'I'. "Domestic deduction 100%
  IF wa_head-molga = '46' AND inaus = 'I' AND datum < '20130301'.
* End VRD_CEE_PL - 130219 note 1824167
    IF abzkz = 'F' OR abzkz = 'M' OR abzkz = 'A'.
      endda = '99991231'.
      begda = '20000101'.
      kzspa = 'X'.
      abzpz = 100.
      kzfpa = 'X'.
      abzfa = 100.
      EXIT.
    ENDIF.
* Begin VRD_CEE_PL - 130108 note 1806907
* Begin VRD_CEE_PL - 130219 note 1824167
* ELSEIF wa_head-molga = '46' AND inaus = 'A'. "Foreign rest control
  ELSEIF wa_head-molga = '46'.                 "Rest control
* End VRD_CEE_PL - 130219 note 1824167
    IF abzkz = 'R'.
      READ TABLE abzugswerte
            WITH KEY datv1 = argu-datv1 uhrv1 = argu-uhrv1
                     datb1 = argu-datb1 uhrb1 = argu-uhrb1
                     vpfph = 'P'        vpfkz = 'R'.
      IF sy-subrc EQ 0.
        CLEAR: endda, begda, kzspa, abzpz, kzfpa, abzfa, waerspz, waersfa.
        EXIT.
      ENDIF.
    ENDIF.
* End VRD_CEE_PL - 130108 note 1806907
  ENDIF.
* End VRD_CEE_PL - 121218 note 1796423

* VRD_CEE_UA begin deduction for UA
  IF wa_head-molga = '36'.
    IF datum IS INITIAL.
      MESSAGE e840 WITH text-e50.
    ENDIF.
    IF ( abzkz = 'F' OR abzkz = 'M' OR abzkz = 'A' ).
      abzci = 0.
      CASE abzkz.
        WHEN 'F'.
          abzci = 1.
        WHEN 'M'.
          abzci = 2.
        WHEN 'A'.
          abzci = 3.
      ENDCASE.
      abzkz = '0'.
      IF abzug-frstk = 'X'.
        abzkz = abzkz + 1.
      ENDIF.
      IF abzug-mitag = 'X'.
        abzkz = abzkz + 1.
      ENDIF.
      IF abzug-abend = 'X'.
        abzkz = abzkz + 1.
      ENDIF.
    ENDIF.
  ENDIF.
* VRD_CEE_UA begin deduction for UA

* QKZ_CEE_CZ_SK deductions for CZ and SK                                        1
  IF wa_head-molga = '18' AND                            "wa_head-datv1 > '20061231' AND
                        ( abzkz = 'F' OR abzkz = 'M' OR abzkz = 'A' ).
    abzkz = '0'.
    IF inaus = 'I'.
      anstd =  argu-anstd.
* Begin VRD_CEE_CZ 20140519 note 2018790
      READ TABLE sum_argu WITH KEY datv1 = argu-datv1   "datum CZDV 20220726
                                   zland = argu-zland.
      IF sy-subrc = 0 AND sum_argu-sum_hour(2) = anstd.
        anmin = sum_argu-sum_hour+2(2).
      ELSE.
        PERFORM berechne_minuten
          USING argu-uhrv1 argu-uhrb1 anmin.
      ENDIF.
* End VRD_CEE_CZ 20140519 note 2018790
      IF ( argu-anstd = 12 OR argu-anstd = 18 ) AND anmin > 0.
        anstd = anstd + 1.
      ENDIF.
      IF anstd < '5'.
        abzkz = abzkz + 1.
      ENDIF.
      IF anstd >= '5' AND anstd <= '12'.
        abzkz = abzkz + 1.
      ENDIF.
      IF anstd > '12' AND anstd <= '18'.
        abzkz = abzkz + 2.
      ENDIF.
      IF anstd > '18'.
        abzkz = abzkz + 3.
      ENDIF.
    ENDIF.
    IF inaus = 'A'.
      anstd =  argu-anstd.
* Begin VRD_CEE_CZ 20140519 note 2018790
      READ TABLE sum_argu WITH KEY datv1 = argu-datv1   "datum CZDV 20220726
                                   zland = argu-zland.
      IF sy-subrc = 0 AND sum_argu-sum_hour(2) = anstd.
        anmin = sum_argu-sum_hour+2(2).
      ELSE.
        PERFORM berechne_minuten
          USING argu-uhrv1 argu-uhrb1 anmin.
      ENDIF.
* End VRD_CEE_CZ 20140519 note 2018790
* Begin VRD_CEE_CZ 20111219 note 1661527
      IF datum >= '20120101'.
        IF ( argu-anstd = 12 OR argu-anstd = 18 ) AND anmin > 0.
          anstd = anstd + 1.
        ENDIF.
        IF anstd <= '12'.
          abzkz = abzkz + 1.
        ENDIF.
        IF anstd > '12' AND anstd <= '18'.
          abzkz = abzkz + 2.
        ENDIF.
        IF anstd > '18'.
          abzkz = abzkz + 3.
        ENDIF.
      ENDIF.
      IF datum >= '20070101' AND datum < '20120101'.
* End VRD_CEE_CZ 20111219 note 1661527
        IF ( argu-anstd = 6 OR argu-anstd = 12 ) AND anmin > 0.
          anstd = anstd + 1.
        ENDIF.
        IF anstd <= '6'.
          abzkz = abzkz + 1.
        ENDIF.
        IF anstd > '6' AND anstd <= '12'.
          abzkz = abzkz + 2.
        ENDIF.
        IF anstd > '12'.
          abzkz = abzkz + 3.
        ENDIF.
      ENDIF.                 "VRD_CEE_CZ 20111219 note 1661527
    ENDIF.
  ENDIF.
* QKZ_CEE_CZ_SK end

  PERFORM exb706a
  USING   morei inaus abzkz
          kzrea kztkt
          erkla ergru datum.

  IF t706a-morei <> morei OR
     t706a-inaus <> inaus OR
     t706a-abzkz <> abzkz OR
     t706a-kzrea <> kzrea OR
     t706a-kztkt <> kztkt OR
     t706a-erkla <> erkla OR
     t706a-ergru <> ergru OR
     NOT ( datum BETWEEN t706a-begda
                 AND     t706a-endda ).

    t706a = space.
    t706a-morei = morei.
    t706a-inaus = inaus.
    t706a-abzkz = abzkz.
    t706a-erkla = erkla.
    t706a-kzrea = kzrea.
    t706a-kztkt = kztkt.
    t706a-ergru = ergru.
    t706a-endda = datum.
    *t706a = t706a.

    SELECT * FROM t706a WHERE morei  = morei
                        AND   inaus  = inaus
                        AND   abzkz  = abzkz
                        AND   erkla  = erkla
                        AND   kzrea  = kzrea
                        AND   kztkt  = kztkt
                        AND   ergru  = ergru
                        AND   begda  <= datum
                        AND   endda  >= datum.
      EXIT.
    ENDSELECT.

    IF sy-subrc    <> 0     OR
       t706a-morei <> morei OR
       t706a-inaus <> inaus OR
       t706a-abzkz <> abzkz OR
       t706a-kzrea <> kzrea OR
       t706a-kztkt <> kztkt OR
       t706a-erkla <> erkla OR
       t706a-ergru <> ergru OR
       NOT ( datum BETWEEN t706a-begda
                   AND     t706a-endda ).
      t706a = space.
*QKZK000728 Unicodeumstellung Beginn
*      PERFORM reise_ablehnung USING text-r70 *t706a+3(35).
*     PERFORM reise_ablehnung USING text-r70 *t706a(20).    "MAWK020779
      PERFORM reise_ablehnung USING text-r70                "MAWK020779
                                    *t706a(20)              "MAWK020779
                                    space.                  "MAWK020779
*QKZK000728 Unicodeumstellung Ende
      PERFORM error_t706a.
      CLEAR t706a.

    ENDIF.
  ENDIF.

  endda = t706a-endda.
  begda = t706a-begda.
  kzspa = t706a-kzspa.
  abzpz = t706a-abzpz.
  kzfpa = t706a-kzfpa.
  abzfa = t706a-abzfa.

  PERFORM exa706a
  USING   endda begda kzspa abzpz kzfpa abzfa.

* Zwischenpufferung bereitstellen
  CASE abzkz.
    WHEN 'F'.
      *t706a_f = t706a.
    WHEN 'M'.
      *t706a_m = t706a.
    WHEN 'E'.
      *t706a_e = t706a.
    WHEN 'A'.
      *t706a_a = t706a.
    WHEN 'B'.
      *t706a_b = t706a.
    WHEN 'R'.
      *t706a_r = t706a.
    WHEN OTHERS.
  ENDCASE.

* QKZ_CEE_CZ_SK deductions CZ SK begin
  IF wa_head-molga = '18'.
    CASE abzkz.
      WHEN 'F' OR '1' OR '2' OR '3'.
        abzkz = 'F'.
        *t706a_f = t706a.
      WHEN 'M' OR '4' OR '5' OR '6'.
        abzkz = 'M'.
        *t706a_m = t706a.
      WHEN 'A' OR '7' OR '8' OR '9'.
        abzkz = 'A'.
        *t706a_a = t706a.
    ENDCASE.
  ENDIF.
* QKZ_CEE_CZ_SK end
* VRD_CEE_UA begin deduction for UA
  IF wa_head-molga = '36'.
    CLEAR: *t706a_f, *t706a_m, *t706a_a.
    CASE abzkz.
      WHEN '1'.
        IF abzug-frstk = 'X'.
          abzkz = 'F'.
          *t706a_f = t706a.
        ENDIF.
        IF abzug-mitag = 'X'.
          abzkz = 'M'.
          *t706a_m = t706a.
        ENDIF.
        IF abzug-abend = 'X'.
          abzkz = 'A'.
          *t706a_a = t706a.
        ENDIF.
      WHEN '2'.
        IF abzug-frstk = 'X' AND abzug-mitag = 'X'.
          IF abzci = 1.
            abzkz = 'F'.
            *t706a_f = t706a.
          ELSE.
            CLEAR: t706a.
          ENDIF.
        ENDIF.
        IF abzug-frstk = 'X' AND abzug-abend = 'X'.
          IF abzci = 1.
            abzkz = 'F'.
            *t706a_f = t706a.
          ELSE.
            CLEAR: t706a.
          ENDIF.
        ENDIF.
        IF abzug-mitag = 'X' AND abzug-abend = 'X'.
          IF abzci = 3.
            abzkz = 'A'.
            *t706a_a = t706a.
          ELSE.
            CLEAR: t706a.
          ENDIF.
        ENDIF.
      WHEN '3'.
        IF abzci = 1.
          abzkz = 'F'.
          *t706a_f = t706a.
        ELSE.
          CLEAR: t706a.
        ENDIF.
    ENDCASE.
  ENDIF.
* VRD_CEE_UA begin deduction for UA
ENDFORM.                                                    "re706a
*---------------------------------------------------------------------*
*       FORM RE706B1                                                  *
*---------------------------------------------------------------------*
FORM  re706b1
USING VALUE(morei)
      VALUE(spkzl)
      VALUE(datum)
      endda begda
      mwskz beart
*     paush nbkkl                                           "QIZK003159
      paush nbkkl est_c                                     "QIZK003159
      privc                                                 "QKZK001053
      firma.

  PERFORM exb706b1
  USING   morei
          spkzl datum.

  IF t706b1-morei <> morei OR
     t706b1-spkzl <> spkzl OR
     NOT ( datum BETWEEN t706b1-begda
                 AND     t706b1-endda ).

    t706b1 = space.
    t706b1-morei = morei.
    t706b1-spkzl = spkzl.
    t706b1-endda = datum.
    *t706b1 = t706b1.

    SELECT * FROM t706b1 WHERE morei = morei
                         AND   spkzl = spkzl
                         AND   endda >= datum
                         AND   begda <= datum.
      EXIT.
    ENDSELECT.

    IF sy-subrc     <> 0     OR
       t706b1-morei <> morei OR
       t706b1-spkzl <> spkzl OR
       NOT ( datum BETWEEN t706b1-begda
                   AND     t706b1-endda ).
      t706b1 = space.

*     PERFORM reise_ablehnung USING text-r71 *t706b1+3(14). "MAWK020779
      PERFORM reise_ablehnung USING text-r71                "MAWK020779
                                    *t706b1+3(14)           "MAWK020779
                                    space.                  "MAWK020779
      PERFORM error_t706b1.
      CLEAR t706b1.
    ENDIF.
  ENDIF.

  endda = t706b1-endda.
  begda = t706b1-begda.
  mwskz = t706b1-mwskz.
  beart = t706b1-beart.
  paush = t706b1-paush.
  nbkkl = t706b1-nbkkl.
  est_c = t706b1-est_c.                                     "QIZK003159
  privc = t706b1-privc.                                     "QKZK001053
  firma = t706b1-firma.

  PERFORM exa706b1
  USING   endda begda
          mwskz beart
          paush nbkkl
          firma.

ENDFORM.                                                    "re706b1

*---------------------------------------------------------------------*
*       FORM RE706B4                                                  *
*---------------------------------------------------------------------*
* Begin MAWK005517
* FORM  re706b4
* USING value(morei)
*       value(spkzl)
*       value(payot)
*       value(datum)
*       value(paush)
*       endda begda
*       lgarl lgarh
*       lgarp.
FORM  re706b4
USING VALUE(morei) TYPE t706b4-morei
      VALUE(spkzl) TYPE t706b4-spkzl
      VALUE(payot) TYPE t706b4-payot
      VALUE(datum) TYPE ptk21-datum
      VALUE(paush) TYPE t706b1-paush
      endda        TYPE t706b4-endda
      begda        TYPE t706b4-begda
      lgarl        TYPE t706b4-lgarl
      lgarh        TYPE t706b4-lgarh
      lgarp        TYPE t706b4-lgarp.
* End MAWK005517

  PERFORM exb706b4
  USING   morei spkzl
          payot datum.

  IF t706b4-morei <> morei OR
     t706b4-spkzl <> spkzl OR
     t706b4-payot <> payot OR
     NOT ( datum BETWEEN t706b4-begda
                 AND     t706b4-endda ) OR  "GLWE34K018616
    regel_kz NE regel_kz_memory.            "GLWE34K018616

    t706b4 = space.
    t706b4-morei = morei.
    t706b4-spkzl = spkzl.
    t706b4-payot = payot.
    t706b4-endda = datum.
    *t706b4 = t706b4.

    SELECT * FROM t706b4 WHERE morei = morei
                        AND   spkzl = spkzl
                        AND   payot = payot
                        AND   endda >= datum
                        AND   begda <= datum.
      EXIT.
    ENDSELECT.

    IF sy-subrc    <> 0     OR
       t706b4-morei <> morei OR
       t706b4-spkzl <> spkzl OR
       t706b4-payot <> payot OR
       NOT ( datum BETWEEN t706b4-begda
                   AND     t706b4-endda ).
      t706b4 = space.
*     PERFORM reise_ablehnung USING text-r72 *t706b4+3(16). "MAWK020779
      PERFORM reise_ablehnung USING text-r72                "MAWK020779
                                    *t706b4+3(16)           "MAWK020779
                                    space.                  "MAWK020779
      PERFORM error_t706b4 USING paush.
      CLEAR t706b4.
    ENDIF.
  ENDIF.

  endda = t706b4-endda.
  begda = t706b4-begda.
  lgarl = t706b4-lgarl.
  lgarh = t706b4-lgarh.
  lgarp = t706b4-lgarp.

  CLEAR: regel_kz_memory.          "GLWE34K018616

  PERFORM exa706b4
  USING   endda begda
          lgarl lgarh
          lgarp.

ENDFORM.                                                    "re706b4

* XCIPSDETRG begin
*---------------------------------------------------------------------*
*       FORM RE706B4_ALTERN                                           *
*---------------------------------------------------------------------*
FORM  re706b4_altern
USING VALUE(morei)
      VALUE(regel_kz)
      VALUE(limit)
      VALUE(spkzl)
      VALUE(payot)
      VALUE(datum)
      VALUE(paush)
* XCI2376172 begin
*      endda begda
*      lgarl lgarh
*      lgarp.
      endda        TYPE t706b4-endda
      begda        TYPE t706b4-begda
      lgarl        TYPE t706b4-lgarl
      lgarh        TYPE t706b4-lgarh
      lgarp        TYPE t706b4-lgarp.
* XCI2376172 end

  PERFORM exb706b4_altern
  USING   morei regel_kz spkzl
          payot datum.

  IF t706b4_altern-morei <> morei OR
     t706b4_altern-regel_kz <> regel_kz OR
     t706b4_altern-limit <> limit OR
     t706b4_altern-spkzl <> spkzl OR
*     T706B4-PAYOT <> PAYOT OR
     t706b4_altern-payot <> payot OR "GLW note 1699999
     NOT ( datum BETWEEN t706b4-begda
                 AND     t706b4-endda ).

    t706b4_altern = space.
    t706b4_altern-morei = morei.
    t706b4_altern-regel_kz = regel_kz.
    t706b4_altern-limit = limit.
    t706b4_altern-spkzl = spkzl.
    t706b4_altern-payot = payot.
    t706b4_altern-endda = datum.
    *t706b4_altern = t706b4_altern.

    SELECT * FROM t706b4_altern
                        WHERE morei    = morei
                        AND   regel_kz = regel_kz
                        AND   limit    = limit
                        AND   spkzl    = spkzl
                        AND   payot    = payot
                        AND   endda    >= datum
                        AND   begda    <= datum.
      EXIT.
    ENDSELECT.

    IF sy-subrc <> 0     OR
       t706b4_altern-morei <> morei OR
       t706b4_altern-regel_kz <> regel_kz OR
       t706b4_altern-limit <> limit OR
       t706b4_altern-spkzl <> spkzl OR
       t706b4_altern-payot <> payot OR
       NOT ( datum BETWEEN t706b4_altern-begda
                   AND     t706b4_altern-endda ).
*     Eintrag wurde nicht in Tabelle T706B4_ALTERN gefunden
*     PERFORM reise_ablehnung USING text-r93 *t706b4_altern+3(16)."MAWK020779
      if regel_kz <> 'GD'.                                  "XCI2376172
        PERFORM reise_ablehnung USING text-r93                "MAWK020779
                                      *t706b4_altern+3(16)    "MAWK020779
                                      space.                  "MAWK020779
      endif.                                                "XCI2376172
*   PERFORM error_t706b4 USING paush.
      CLEAR t706b4_altern.
    ENDIF.
  ENDIF.

  endda = t706b4_altern-endda.
  begda = t706b4_altern-begda.
  lgarl = t706b4_altern-lgarl.
  lgarh = t706b4_altern-lgarh.
  lgarp = t706b4_altern-lgarp.

  PERFORM exa706b4
  USING   endda begda
          lgarl lgarh
          lgarp.

  regel_kz_memory = regel_kz.       "GLWE34K018616

ENDFORM.                    "re706b4_altern

* XCIPSDETRG end

*---------------------------------------------------------------------*
*       FORM RE706D                                                   *
*---------------------------------------------------------------------*
FORM re706d
USING VALUE(morei)
*     kzrea kztkt                                           "WTLK004776
      kzpmf pauvs mwskz mwaus
      molga kurst land1 waerskz waers.
  PERFORM exb706d
  USING   morei.

  IF t706d-morei <> morei.

    SELECT SINGLE * FROM t706d WHERE morei = morei.

    IF sy-subrc <> 0.
      t706d = space.
      *t706d = space.
      *t706d-morei = morei.

      NEW-PAGE.
      SKIP.
      WRITE: / text-r73, *t706d.
      PERFORM ablehnung.

    ENDIF.

  ENDIF.

* kzrea = t706d-kzrea.                                      "WTLK004776
* kztkt = t706d-kztkt.                                      "WTLK004776
  kzpmf = t706d-kzpmf.
  pauvs = t706d-pauvs.
  mwskz = t706d-mwskz.
  mwaus = t706d-mwaus.
  molga = t706d-molga.
  kurst = t706d-kurst.
  land1 = t706d-land1.

  PERFORM exa706d
  USING
*         kzrea kztkt                                       "WTLK004776
          kzpmf pauvs mwskz mwaus
          molga kurst land1.

ENDFORM.                                                    "re706d

*---------------------------------------------------------------------*
*       FORM RE706F                                                   *
*---------------------------------------------------------------------*
FORM  re706f
USING VALUE(morei) VALUE(kzrea) VALUE(kztkt)
      VALUE(land1) VALUE(rgion) VALUE(berei)
      VALUE(kzpmf) VALUE(kznza)
      VALUE(pkwkl) VALUE(pekez) VALUE(kmgre) VALUE(datum)
      endda begda waers betfz betfa betku.

  STATICS: lv_not_paid TYPE ptrv_perio-not_paid. "GLW note 2802510

  DATA: l_ignore_error,                                     "ZFJ2717557
        l_abrec TYPE abrec,                 "ZFJ2717557
        l_called_from_web.                  "ZFJ2717557

* Prepare key for reading T706F according to customizing:
  IF cumulation_period_type NE '1'.
    CLEAR pekez.
  ENDIF.
  IF cumulation_active NE '1'.
    CLEAR kmgre.
  ENDIF.

  PERFORM re706f_trvct USING  t702n-f08                     "WNZK050579
                              t702n-f10                     "KR2341748
                              t702n-f09                     "WNZK050579
                              t702n-f11                     "WNZK050579
                              t001_land1                    "WNZK050579
                    CHANGING  kzrea                         "WNZK050579
                              berei                         "KR2341748
                              kztkt                         "WNZK050579
                              land1                         "WNZK050579
                              rgion.                        "WNZK050579

  PERFORM exb706f
  USING   morei kzrea kztkt
          land1 rgion berei kzpmf kznza
          pkwkl pekez kmgre datum.

  betfz = betfa = betku = 0.

* if varia_f-var3 eq '0'.                                "XFUAHRK001931
  IF cumulation_active NE '1'.         "XFUAHRK001931
*   Ohne Kilometer-Kumulation
    IF t706f-morei <> morei OR
       t706f-kzrea <> kzrea OR
       t706f-kztkt <> kztkt OR
       t706f-land1 <> land1 OR
       t706f-rgion <> rgion OR
       t706f-berei <> berei OR
       t706f-kzpmf <> kzpmf OR
       t706f-kznza <> kznza OR
       t706f-pkwkl <> pkwkl OR
       t706f-pekez <> pekez OR
       t706f-kmgre <> kmgre OR
       lv_not_paid <> wa_perio-not_paid OR  "GLW note 2802510
* wegen möglicher Änderung der Versteuerung müssen die Fahrtkosten für
* Trennungsgelder immer von der Datenbank gelesen werden, nie aus dem Puffer
       ( wa_perio-perio > 000 AND pubsec_germany = true ) OR "ZFJ1790738
       NOT ( datum BETWEEN t706f-begda
                       AND t706f-endda ).

      lv_not_paid = wa_perio-not_paid.  "GLW note 2802510

      t706f = space.
      t706f-morei = morei.
      t706f-kzrea = kzrea.
      t706f-kztkt = kztkt.
      t706f-land1 = land1.
      t706f-rgion = rgion.
      t706f-berei = berei.
      t706f-kzpmf = kzpmf.
      t706f-kznza = kznza.
      t706f-pkwkl = pkwkl.
      t706f-pekez = pekez.
      t706f-kmgre = kmgre.
      t706f-endda = datum.
      *t706f = t706f.

* QIZK001038 begin...
*      SELECT * FROM t706f WHERE    morei = morei
*                          AND      kzrea = kzrea
*                          AND      kztkt  = kztkt
*                          AND      land1  = land1
*                          AND      rgion  = rgion
*                          AND      berei  = berei
*                          AND      kzpmf  = kzpmf
*                          AND      kznza  = kznza
*                          AND      pkwkl  = pkwkl
*                          AND      pekez  = pekez
*                          AND      kmgre >= kmgre
*                          AND      endda >= datum
*                          AND      begda <= datum.
*        EXIT.
*      ENDSELECT.
      SELECT * FROM t706f UP TO 1 ROWS
                          WHERE    morei = morei
                          AND      kzrea = kzrea
                          AND      kztkt  = kztkt
                          AND      land1  = land1
                          AND      rgion  = rgion
                          AND      berei  = berei
                          AND      kzpmf  = kzpmf
                          AND      kznza  = kznza
                          AND      pkwkl  = pkwkl
                          AND      pekez  = pekez
                          AND      kmgre >= kmgre
                          AND      endda >= datum
                          AND      begda <= datum
                          ORDER BY PRIMARY KEY.
      ENDSELECT.
* QIZK001038 end...

      IF sy-subrc    <> 0     OR
         t706f-morei <> morei OR
         t706f-kzrea <> kzrea OR
         t706f-kztkt <> kztkt OR
         t706f-land1 <> land1 OR
         t706f-rgion <> rgion OR
         t706f-berei <> berei OR
         t706f-kzpmf <> kzpmf OR
         t706f-kznza <> kznza OR
         t706f-pkwkl <> pkwkl OR
         t706f-pekez <> pekez OR
         t706f-kmgre <> kmgre OR
         NOT ( datum BETWEEN t706f-begda
                         AND t706f-endda ).
*           nicht den richtigen Eintrag gefunden
        CLEAR t706f.
* QKZK000728 Unicodeumstellung Beginn
*       PERFORM reise_ablehnung USING text-r75 *t706f+3(64).
*       PERFORM reise_ablehnung USING text-r75 *t706f(36).  "MAWK020779
* begin ZFJ2717557
        IF sy-tcode IS INITIAL AND pubsec_germany = 'X'.
          CLEAR l_ignore_error.
          IMPORT l_called_from_web FROM MEMORY ID 'CALLED_FROM_WEB'.
          IF l_called_from_web = 'X'.
            SELECT SINGLE abrec
                         FROM ptrv_perio INTO l_abrec
                         WHERE pernr = wa_perio-pernr
                           AND reinr = wa_perio-reinr
                           AND perio = wa_perio-perio
                           AND pdvrs = ( SELECT MIN( pdvrs ) FROM ptrv_perio
                                           WHERE pernr = wa_perio-pernr
                                             AND reinr = wa_perio-reinr
                                             AND perio = wa_perio-perio ).
            IF l_abrec = '4'.    "save as draft in WebDynpro
              l_ignore_error = 'X'.
            ENDIF.
          ENDIF.
        ENDIF.
        IF l_ignore_error IS INITIAL.
* end ZFJ2717557
        PERFORM reise_ablehnung USING text-r75              "MAWK020779
                                      *t706f(36)            "MAWK020779
                                      space.                "MAWK020779
        ENDIF. "ZFJ2717557
* QKZK000728 Unicodeumstellung Ende
        PERFORM error_t706f.
      ENDIF.

    ENDIF.
  ELSE.
* Mit Kilometer-Kumulation
    IF t706f-morei <> morei OR
       t706f-kzrea <> kzrea OR
       t706f-kztkt <> kztkt OR
       t706f-land1 <> land1 OR
       t706f-rgion <> rgion OR
       t706f-berei <> berei OR
       t706f-kzpmf <> kzpmf OR
       t706f-kznza <> kznza OR
       t706f-pkwkl <> pkwkl OR
       t706f-pekez <> pekez OR
       t706f-kmgre <  kmgre OR
       lv_not_paid <> wa_perio-not_paid OR   "GLW note 2802510
       NOT ( datum BETWEEN t706f-begda
                       AND t706f-endda ).
*        Lesen notwendig
      lv_not_paid = wa_perio-not_paid. "GLW note 2802510
      t706f = space.
      t706f-morei = morei.
      t706f-kzrea = kzrea.
      t706f-kztkt = kztkt.
      t706f-land1 = land1.
      t706f-rgion = rgion.
      t706f-berei = berei.
      t706f-kzpmf = kzpmf.
      t706f-kznza = kznza.
      t706f-pkwkl = pkwkl.
      t706f-pekez = pekez.
      t706f-kmgre = kmgre.
      t706f-endda = datum.             "XFUAHRK001931
      *t706f = t706f.

* QIZK001038 begin...
*      SELECT * FROM t706f WHERE    morei  = morei
*                          AND      kzrea  = kzrea
*                          AND      kztkt  = kztkt
*                          AND      land1  = land1
*                          AND      rgion  = rgion
*                          AND      berei  = berei
*                          AND      kzpmf  = kzpmf
*                          AND      kznza  = kznza
*                          AND      pkwkl  = pkwkl
*                          AND      pekez  = pekez
*                          AND      kmgre >= kmgre
*                          AND      endda >= datum
*                          AND      begda <= datum.
*        EXIT.
*      ENDSELECT.
      SELECT * FROM t706f UP TO 1 ROWS
                          WHERE    morei  = morei
                          AND      kzrea  = kzrea
                          AND      kztkt  = kztkt
                          AND      land1  = land1
                          AND      rgion  = rgion
                          AND      berei  = berei
                          AND      kzpmf  = kzpmf
                          AND      kznza  = kznza
                          AND      pkwkl  = pkwkl
                          AND      pekez  = pekez
                          AND      kmgre >= kmgre
                          AND      endda >= datum
                          AND      begda <= datum
                          ORDER BY PRIMARY KEY.
      ENDSELECT.
* QIZK001038 end...

      IF sy-subrc    <> 0     OR
         t706f-morei <> morei OR
         t706f-kzrea <> kzrea OR
         t706f-kztkt <> kztkt OR
         t706f-land1 <> land1 OR
         t706f-rgion <> rgion OR
         t706f-berei <> berei OR
         t706f-kzpmf <> kzpmf OR
         t706f-kznza <> kznza OR
         t706f-pkwkl <> pkwkl OR
         t706f-pekez <> pekez OR
         t706f-kmgre <  kmgre .
*           nicht den richtigen Eintrag gefunden
        CLEAR t706f.
*QKZK000728 Unicodeumstellung Beginn
*       PERFORM reise_ablehnung USING text-r75 *t706f+3(64).
*       PERFORM reise_ablehnung USING text-r75 *t706f(36).  "MAWK020779
* begin ZFJ2717557
        IF sy-tcode IS INITIAL AND pubsec_germany = 'X'.
          CLEAR l_ignore_error.
          IMPORT l_called_from_web FROM MEMORY ID 'CALLED_FROM_WEB'.
          IF l_called_from_web = 'X'.
            SELECT SINGLE abrec
                         FROM ptrv_perio INTO l_abrec
                         WHERE pernr = wa_perio-pernr
                           AND reinr = wa_perio-reinr
                           AND perio = wa_perio-perio
                           AND pdvrs = ( SELECT MIN( pdvrs ) FROM ptrv_perio
                                           WHERE pernr = wa_perio-pernr
                                             AND reinr = wa_perio-reinr
                                             AND perio = wa_perio-perio ).
            IF l_abrec = '4'.    "save as draft in WebDynpro
              l_ignore_error = 'X'.
            ENDIF.
          ENDIF.
        ENDIF.
        IF l_ignore_error IS INITIAL.
* end ZFJ2717557

        PERFORM reise_ablehnung USING text-r75              "MAWK020779
                                      *t706f(36)            "MAWK020779
                                      space.                "MAWK020779
        ENDIF.        "ZFJ2717557
*QKZK000728 Unicodeumstellung Ende
        PERFORM error_t706f.

*************** XFUAHRK001931 Begin of Deletion ************************
*         ELSE.
*            T706F-ENDDA = DATUM.
*            *T706F = T706F.
*
*            SELECT * FROM T706F WHERE    MOREI  = MOREI
*                                AND      KZREA  = KZREA
*                                AND      KZTKT  = KZTKT
*                                AND      LAND1  = LAND1
*                                AND      RGION  = RGION
*                                AND      BEREI  = BEREI
*                                AND      KZPMF  = KZPMF
*                                AND      KZNZA  = KZNZA
*                                AND      PKWKL  = PKWKL
*                                AND      PEKEZ  = PEKEZ
*                                AND      KMGRE >= KMGRE
*                                AND      ENDDA >= DATUM
*                                AND      BEGDA <= DATUM.
*                 EXIT.
*            ENDSELECT.
*
*            IF SY-SUBRC    <> 0     OR
*               T706F-MOREI <> MOREI OR
*               T706F-KZREA <> KZREA OR
*               T706F-KZTKT <> KZTKT OR
*               T706F-LAND1 <> LAND1 OR
*               T706F-RGION <> RGION OR
*               T706F-BEREI <> BEREI OR
*               T706F-KZPMF <> KZPMF OR
*               T706F-KZNZA <> KZNZA OR
*               T706F-PKWKL <> PKWKL OR
*               T706F-PEKEZ <> PEKEZ OR
*               T706F-KMGRE <  KMGRE OR
*               NOT ( DATUM BETWEEN T706F-BEGDA
*                               AND T706F-ENDDA ).
**              nicht den richtigen Eintrag gefunden
*               CLEAR T706F.
*               PERFORM REISE_ABLEHNUNG USING TEXT-R75 *T706F+3(64).
*               PERFORM ERROR_T706F.
*            ENDIF.
*************** XFUAHRK001931 End of Deletion **************************

      ENDIF.                           "Eintrag nicht gefunden?

    ENDIF.                             "Lesen notwendig

  ENDIF.                               "Kilometerkumulation

  endda = t706f-endda.
  begda = t706f-begda.
  waers = t706f-waers.
  betfz = t706f-betfz.
  betfa = t706f-betfa.
  betku = t706f-betku.

* VJMKTGST03 alles in die Aufrufroutine verlagert:
** begin VJMPSTRG00
*  IF pubsec_germany = true
*  AND ( trg_tr = true OR trg_av = true ).
*    erstform = 'W'.
*    proz_stfr = 0.   "VJMTODO: Konstante definieren
*    perform tg_set_versteuerung using datum
*                                      erstform
*                                      T706f-betfz
*                                      proz_stfr.
*  ENDIF.
** end VJMPSTRG00
  PERFORM exa706f
  USING   endda begda waers betfz betfa betku.

  t706f-betfz = betfz.                         "PGE Note 2790547 : Start
  t706f-betfa = betfa.
  t706f-betku = betku.                         "PGE Note 2790547 : End

ENDFORM.                                                    "re706f

*---------------------------------------------------------------------*
*       FORM RE706H                                                   *
*---------------------------------------------------------------------*
FORM re706h
USING VALUE(morei) VALUE(kzpah) VALUE(kzrea) VALUE(kztkt)
      VALUE(lndgr) VALUE(rgion) VALUE(berei)
      VALUE(erkla) VALUE(ergru)
      VALUE(anzta) VALUE(beguz) VALUE(enduz) VALUE(datum)
      endda begda
      waers betfz betfa betku
      mahlzeiten.

  DATA: zaehler TYPE p.
  DATA: mahlzeit_liste(3).

  PERFORM exb706h
  USING   morei kzpah kzrea kztkt
          lndgr rgion berei erkla ergru
          anzta beguz enduz datum.

  betfz = betfa = betku = 0.
  zaehler = 0.
  mahlzeit_liste = mahlzeiten.

* QIZK001038 begin..
*  SELECT * FROM t706h WHERE morei  = morei
*                        AND kzpah  = kzpah
*                        AND kzrea  = kzrea
*                        AND kztkt  = kztkt
*                        AND lndgr  = lndgr
*                        AND rgion  = rgion
*                        AND berei  = berei
*                        AND erkla  = erkla
*                        AND ergru  = ergru
*                        AND anzta  = anzta
*                        AND beguz >= '000000'
*                        AND enduz <= '240000'
*                        AND begda <= datum
*                        AND endda >= datum.
  SELECT * FROM t706h WHERE morei  = morei
                        AND kzpah  = kzpah
                        AND kzrea  = kzrea
                        AND kztkt  = kztkt
                        AND lndgr  = lndgr
                        AND rgion  = rgion
                        AND berei  = berei
                        AND erkla  = erkla
                        AND ergru  = ergru
                        AND anzta  = anzta
                        AND beguz >= '000000'
                        AND enduz <= '240000'
                        AND begda <= datum
                        AND endda >= datum
                        ORDER BY PRIMARY KEY.
* QIZK001038 end..

    zaehler = zaehler + 1.

    IF beguz <= t706h-beguz AND t706h-enduz <= enduz.
      CASE zaehler.
        WHEN '1'.
          mahlzeit_liste+0(1) = 'X'.
        WHEN '2'.
          mahlzeit_liste+1(1) = 'X'.
        WHEN '3'.
          mahlzeit_liste+2(1) = 'X'.
        WHEN OTHERS.
      ENDCASE.

      PERFORM waers_bwert                                   "WTLK064642
        USING varia_r-recurr                                "WTLK064642
              datum                                         "WTLK064642
              t706h-betfz                                   "WTLK064642
              t706h-betfa                                   "WTLK064642
              t706h-betku                                   "WTLK064642
              t706h-waers.                                  "WTLK064642

      betfz = betfz + t706h-betfz.
      betfa = betfa + t706h-betfa.
      betku = betku + t706h-betku.
      endda = t706h-endda.                                  "XOWK022870
      begda = t706h-begda.                                  "XOWK022870
      waers = t706h-waers.                                  "XOWK022870
    ENDIF.

  ENDSELECT.

*  IF sy-subrc = 0.                                          "XOWK022870
*    endda = t706h-endda.                                    "XOWK022870
*    begda = t706h-begda.                                    "XOWK022870
*    waers = t706h-waers.                                    "XOWK022870
*  ENDIF.                                                    "XOWK022870

  mahlzeiten = mahlzeit_liste.

  PERFORM exa706h
  USING   endda begda waers betfz betfa betku mahlzeiten.

ENDFORM.                                                    "re706h

*---------------------------------------------------------------------*
*       FORM RE706L                                                   *
*---------------------------------------------------------------------*
FORM  re706l
USING VALUE(morei) VALUE(land1) VALUE(rgion)
      VALUE(datum)
      endda begda
      lgrve lgrun lgrfa
      regve regun regfa
      lgrhb reghb.                                          "XOWK033175

  PERFORM exb706l
  USING   morei land1 rgion datum.

  IF t706l-morei <> morei OR
     t706l-land1 <> land1 OR
     t706l-rgion <> rgion OR
     NOT ( datum BETWEEN t706l-begda
                 AND     t706l-endda ).

    t706l = space.
    t706l-morei = morei.
    t706l-land1 = land1.
    t706l-rgion = rgion.
    t706l-endda = datum.
    *t706l = t706l.

    SELECT * FROM t706l WHERE morei = morei
                        AND   land1 = land1
                        AND   rgion = rgion
                        AND   endda >= datum
                        AND   begda <= datum.
      EXIT.
    ENDSELECT.

    IF sy-subrc    <> 0     OR
       t706l-morei <> morei OR
       t706l-land1 <> land1 OR
       t706l-rgion <> rgion OR
       NOT ( datum BETWEEN t706l-begda
                   AND     t706l-endda ).
      t706l = space.
    ENDIF.
  ENDIF.

  begda = t706l-begda.
  endda = t706l-endda.
  lgrve = t706l-lgrve.
  lgrun = t706l-lgrun.
  lgrfa = t706l-lgrfa.
  regve = t706l-regve.
  regun = t706l-regun.
  regfa = t706l-regfa.
  lgrhb = t706l-lgrhb.                                      "XOWK033175
  reghb = t706l-reghb.                                      "XOWK033175

  PERFORM exa706l
  USING   endda begda
          lgrve lgrun lgrfa
          regve regun regfa
          lgrhb reghb.                                      "XOWK033175

ENDFORM.                                                    "re706l

*---------------------------------------------------------------------*
*       FORM RE706M                                                   *
*---------------------------------------------------------------------*
FORM  re706m
USING VALUE(morei) VALUE(land1) VALUE(rgion)
      VALUE(datum)
      endda begda
      mwkzf mwkzu mwkzv.

  PERFORM exb706m
  USING   morei land1 rgion datum.
  IF t706m-morei <> morei OR
     t706m-land1 <> land1 OR
     t706m-rgion <> rgion OR
     NOT ( datum BETWEEN t706m-begda
                 AND     t706m-endda ).
    SELECT * FROM t706m WHERE morei =  morei
                        AND   land1 =  land1
                        AND   rgion =  rgion
                        AND   begda <= datum
                        AND   endda >= datum.
      EXIT.
    ENDSELECT.
    IF sy-subrc <> 0.
      t706m = space.
    ENDIF.
  ENDIF.

  mwkzf = t706m-mwkzf.
  mwkzu = t706m-mwkzu.
  mwkzv = t706m-mwkzv.

  PERFORM exa706m
  USING   endda begda mwkzf mwkzu mwkzv.

ENDFORM.                                                    "re706m

*---------------------------------------------------------------------*
*       FORM RE706P                                                   *
*---------------------------------------------------------------------*
FORM  re706p
USING VALUE(morei) VALUE(pekez) VALUE(datum)
      endda begda perna.

  PERFORM exb706p
  USING   morei pekez datum.
  IF t706p-morei <> morei OR
     t706p-pekez <> pekez OR
     NOT ( datum BETWEEN t706p-begda
                 AND     t706p-endda ).
    t706p = space.
    t706p-morei = morei.
    t706p-pekez = pekez.
    t706p-endda = datum.
    *t706p = t706p.
*   clear t706f.                                         "XFUAHRK001931
    CLEAR t706p.                       "XFUAHRK001931
    SELECT * FROM t706p WHERE morei =  morei
                        AND   pekez =  pekez
                        AND   endda >= datum
                        AND   begda <= datum.
    ENDSELECT.
    CLEAR t706f.                       "XFU????
    IF sy-subrc    <> 0     OR
       t706p-morei <> morei OR
       t706p-pekez <> pekez OR
       NOT ( datum BETWEEN t706p-begda
                   AND     t706p-endda ).
      CLEAR t706p.

*     PERFORM reise_ablehnung USING text-r80 *t706p+3(55).  "MAWK020779
      PERFORM reise_ablehnung USING text-r80                "MAWK020779
                                    *t706p+3(55)            "MAWK020779
                                    space.                  "MAWK020779
      PERFORM error_t706p.

    ENDIF.
  ENDIF.
  endda = t706p-endda.
  begda = t706p-begda.
  perna = t706p-perna.

  PERFORM exa706p
  USING   endda begda perna.

ENDFORM.                                                    "re706p

*---------------------------------------------------------------------*
*       FORM RE706S                                                   *
*---------------------------------------------------------------------*
FORM  re706s
USING VALUE(morei) VALUE(schem)
      inaus rland einme ankun
      frueh esbon kfzve
      split verpf berei numrv rgion.

  PERFORM exb706s
  USING   morei schem.

  IF t706s-morei <> morei OR
     t706s-schem <> schem.

    SELECT SINGLE * FROM t706s WHERE morei = morei
                               AND   schem = schem.

    IF sy-subrc <> 0.
      t706s = space.
      *t706s = space.
      *t706s-morei = morei.
      *t706s-schem = schem.

*     PERFORM reise_ablehnung USING text-r83 *t706s+3(22).  "MAWK020779
      PERFORM reise_ablehnung USING text-r83                "MAWK020779
                                    *t706s+3(22)            "MAWK020779
                                    space.                  "MAWK020779
      PERFORM error_t706s.

    ENDIF.

  ENDIF.

  inaus = t706s-inaus.
  rland = t706s-rland.
  einme = t706s-einme.
  ankun = t706s-ankun.
  frueh = t706s-frueh.
  esbon = t706s-esbon.
  kfzve = t706s-kfzve.
  split = t706s-split.
  verpf = t706s-verpf.
  berei = t706s-berei.
  numrv = t706s-numrv.
  rgion = t706s-rgion.

  PERFORM exa706s
  USING   inaus rland einme ankun
          frueh esbon kfzve
          split verpf berei numrv rgion.

ENDFORM.                                                    "re706s

*---------------------------------------------------------------------*
*       FORM RE706U                                                   *
*---------------------------------------------------------------------*
FORM  re706u
USING VALUE(morei) VALUE(kzpah) VALUE(kzrea) VALUE(kztkt)
      VALUE(lndgr) VALUE(rgion) VALUE(berei)
      VALUE(erkla) VALUE(ergru)
      VALUE(datum)
      endda begda waers betfz betfa betku.

  PERFORM exb706u
  USING   morei kzpah kzrea kztkt
          lndgr rgion berei
          erkla ergru
          datum.

  IF t706u-morei <> morei OR
     t706u-kzpah <> kzpah OR
     t706u-kzrea <> kzrea OR
     t706u-kztkt <> kztkt OR
     t706u-lndgr <> lndgr OR
     t706u-rgion <> rgion OR
     t706u-berei <> berei OR
     t706u-erkla <> erkla OR
     t706u-ergru <> ergru OR
     NOT ( datum BETWEEN t706u-begda
                 AND     t706u-endda ).

    t706u = space.
    t706u-morei = morei.
    t706u-kzpah = kzpah.
    t706u-kzrea = kzrea.
    t706u-kztkt = kztkt.
    t706u-lndgr = lndgr.
    t706u-rgion = rgion.
    t706u-berei = berei.
    t706u-erkla = erkla.
    t706u-ergru = ergru.
    t706u-endda = datum.
    *t706u = t706u.

    SELECT * FROM t706u WHERE morei = morei
                        AND   kzpah = kzpah
                        AND   kzrea = kzrea
                        AND   kztkt = kztkt
                        AND   lndgr = lndgr
                        AND   rgion = rgion
                        AND   berei = berei
                        AND   erkla = erkla
                        AND   ergru = ergru
                        AND   endda >= datum
                        AND   begda <= datum.
      EXIT.
    ENDSELECT.

    IF sy-subrc    <> 0     OR
       t706u-morei <> morei OR
       t706u-kzpah <> kzpah OR
       t706u-kzrea <> kzrea OR
       t706u-kztkt <> kztkt OR
       t706u-lndgr <> lndgr OR
       t706u-rgion <> rgion OR
       t706u-berei <> berei OR
       t706u-erkla <> erkla OR
       t706u-ergru <> ergru OR
       NOT ( datum BETWEEN t706u-begda
                   AND     t706u-endda ).
      t706u = space.
*QKZK000728 Unicodeumstellung Beginn
*     PERFORM reise_ablehnung USING text-r85 *t706u+3(56).
*     PERFORM reise_ablehnung USING text-r85 *t706u(28).    "MAWK020779
      PERFORM reise_ablehnung USING text-r85                "MAWK020779
                                    *t706u(28)              "MAWK020779
                                    space.                  "MAWK020779
* QKZK000728 Unicodeumstellung Ende
      PERFORM error_t706u.
      CLEAR t706u.

    ENDIF.
  ENDIF.

  endda = t706u-endda.
  waers = t706u-waers.
  begda = t706u-begda.
  betfz = t706u-betfz.
  betfa = t706u-betfa.
  betku = t706u-betku.
** VJMKTGST03  alles in Aufrufroutine verlagert:
** begin VJMPSTRG00
*
*  IF pubsec_germany = true
*  AND ( trg_tr = true OR trg_av = true ).
*    erstform = 'U'.
*    proz_stfr = 0.   "VJMTODO: Konstante definieren
*    perform tg_set_versteuerung using datum
*                                      erstform
*                                      T706u-betfz
*                                      proz_stfr.
*  ENDIF.
** end VJMPSTRG00

  PERFORM exa706u
  USING   endda begda waers betfz betfa betku.

ENDFORM.                                                    "re706u

*---------------------------------------------------------------------*
*       FORM RE706V                                                   *
*---------------------------------------------------------------------*
FORM  re706v
USING VALUE(morei) VALUE(kzpah) VALUE(kzrea) VALUE(kztkt)
      VALUE(lndgr) VALUE(rgion) VALUE(berei)
      VALUE(erkla) VALUE(ergru)
      VALUE(anzta) VALUE(anstd) VALUE(datum)
      endda begda waers betfz betfa betku.

  PERFORM exb706v
  USING   morei kzpah kzrea kztkt
          lndgr rgion berei
          erkla ergru
          anzta anstd datum.

  IF t706v-morei <> morei OR
     t706v-kzpah <> kzpah OR
     t706v-kzrea <> kzrea OR
     t706v-kztkt <> kztkt OR
     t706v-lndgr <> lndgr OR
     t706v-rgion <> rgion OR
     t706v-berei <> berei OR
     t706v-erkla <> erkla OR
     t706v-ergru <> ergru OR
     t706v-anzta <> anzta OR
     t706v-anstd <> anstd OR
     NOT ( datum BETWEEN t706v-begda
                 AND     t706v-endda ).
* QIZK001038 begin..
*    SELECT * FROM t706v WHERE morei =  morei AND
*                              kzpah =  kzpah AND
*                              kzrea =  kzrea AND
*                              kztkt =  kztkt AND
*                              lndgr =  lndgr AND
*                              rgion =  rgion AND
*                              berei =  berei AND
*                              erkla =  erkla AND
*                              ergru =  ergru AND
*                              anzta >= anzta AND
*                              anstd >= anstd AND
*                              begda <= datum AND
*                              endda >= datum.
*      EXIT.
*    ENDSELECT.
    SELECT * FROM t706v UP TO 1 ROWS
                        WHERE morei =  morei AND
                              kzpah =  kzpah AND
                              kzrea =  kzrea AND
                              kztkt =  kztkt AND
                              lndgr =  lndgr AND
                              rgion =  rgion AND
                              berei =  berei AND
                              erkla =  erkla AND
                              ergru =  ergru AND
                              anzta >= anzta AND
                              anstd >= anstd AND
                              begda <= datum AND
                              endda >= datum
                              ORDER BY PRIMARY KEY.
    ENDSELECT.
* QIZK001038 end..

    IF sy-subrc <> 0.
      IF pubsec_germany = true AND                          "QKZKORRVBELEG
         kzpah = 'H'.                                       "QKZKORRVBELEG
        t706v-betfz = 9999999.                              "QKZKORRVBELEG
        t706v-betfa = 9999999.                              "QKZKORRVBELEG
        t706v-betku = 9999999.                              "QKZKORRVBELEG
      ELSE.                                                 "QKZKORRVBELEG
        *t706v = space.
        *t706v-morei = morei.
        *t706v-kzpah = kzpah.
        *t706v-kzrea = kzrea.
        *t706v-kztkt = kztkt.
        *t706v-lndgr = lndgr.
        *t706v-rgion = rgion.
        *t706v-berei = berei.
        *t706v-erkla = erkla.
        *t706v-ergru = ergru.
        *t706v-anzta = anzta.
        *t706v-anstd = anstd.
        *t706v-endda = datum.
* QKZK000728 Unicodeumstellung Beginn
*       PERFORM REISE_ABLEHNUNG USING TEXT-R86 *T706V+3(61).
*       PERFORM reise_ablehnung USING text-r86 *t706v(33).  "MAWK020779
        PERFORM reise_ablehnung USING text-r86              "MAWK020779
                                      *t706v(33)            "MAWK020779
                                      space.                "MAWK020779
* QKZK000728 Unicodeumstellung Ende
        PERFORM error_t706v.
        CLEAR t706v.
      ENDIF.                                             "QKZKORRVBELEG
    ENDIF.

  ENDIF.

  t706v-anzta = anzta.
  t706v-anstd = anstd.

*  VJMKTGST03  alles in Aufrufroutineverlagert
** begin VJMPSTRG00
*  IF pubsec_germany = true
*  AND ( trg_tr = true OR trg_av = true ).
*    erstform = 'T'.
*    proz_stfr = 0.
*    PERFORM tg_set_stfr USING datum
*                              erstform
*                              t706v-betfz
*                              proz_stfr.
*  ENDIF.
** end VJMPSTRG00

  endda = t706v-endda.
  waers = t706v-waers.
  begda = t706v-begda.
  betfz = t706v-betfz.
  betfa = t706v-betfa.
  betku = t706v-betku.
* begin VJMKTGST03
* BEGIN VJMK1286257 DELETE
*  IF pubsec_germany = true
*  AND ( trg_tr = true OR trg_av = true ).
*    erstform = 'T'.
*    PERFORM tg_set_stfr USING datum
*                              erstform
*                              betfz
*                              t706v-waers
*                              st_mod1
*                              st_mod2.
*  ENDIF.
* END VJMK1286257 DELETE
* end VJMKTGST03

  PERFORM exa706v
  USING   endda begda waers betfz betfa betku.

ENDFORM.                                                    "RE706V

*---------------------------------------------------------------------*
*       FORM RECURR                                                   *
*---------------------------------------------------------------------*
*       Lesen Tabelle TCURR                                           *
*---------------------------------------------------------------------*
*       DATUM = Umrechnungsdatum                                      *
*       FWAE  = Fremdwaehrung                                         *
*       HWAE  = Hauswaehrung                                          *
*---------------------------------------------------------------------*
FORM  recurr
USING VALUE(gdatu) VALUE(fcurr) VALUE(tcurr).
  DATA: w-date TYPE d.

  CONVERT DATE gdatu INTO INVERTED-DATE w-date.
* QIZK001038 begin...
*  SELECT * FROM tcurr WHERE kurst = 'M   '
*                      AND   fcurr = fcurr
*                      AND   tcurr = tcurr
*                      AND   gdatu >= w-date.
*    EXIT.
*  ENDSELECT.
  SELECT * FROM tcurr UP TO 1 ROWS
                      WHERE kurst = 'M   '
                      AND   fcurr = fcurr
                      AND   tcurr = tcurr
                      AND   gdatu >= w-date
                      ORDER BY PRIMARY KEY.
  ENDSELECT.
* QIZK001038 end...

  IF sy-subrc <> 0.

*   PERFORM reise_ablehnung USING text-r89 fcurr.           "MAWK020779
    PERFORM reise_ablehnung USING text-r89                  "MAWK020779
                                  fcurr                     "MAWK020779
                                  space.                    "MAWK020779
    WRITE: tcurr, gdatu.

  ENDIF.

ENDFORM.                    "recurr

*---------------------------------------------------------------------*
*    HILFSMODULE ZUM STOP DER WEITERVERARBEITUNG                      *
*---------------------------------------------------------------------*

*---------------------------------------------------------------------*
*       FORM REISE_ABLEHNUNG                                          *
*---------------------------------------------------------------------*
FORM reise_ablehnung USING text
*                          argument.                        "MAWK020779
                           argument                         "MAWK020779
                           use_sy_msg    TYPE abap_bool.    "MAWK020779

  DATA: e_type LIKE sy-msgty,
        e_id   LIKE sy-msgid,
        e_no   LIKE sy-msgno,
        e_v1   LIKE sy-msgv1,
        e_v2   LIKE sy-msgv2,
        e_v3   LIKE sy-msgv3,
        e_v4   LIKE sy-msgv4.
*
  DATA: l_called_from_web.                                  "QIZK082944

  SUMMARY.
  IF rei_ablehn = 0.
*
* QIZK082944 begin...
    IF simulate = 'X'.
      IMPORT l_called_from_web FROM MEMORY ID 'CALLED_FROM_WEB'.
      IF sy-subrc NE 0.
        CLEAR l_called_from_web.
      ENDIF.
    ENDIF.
* QIZK082944 end...
*
    IF sy-tcode EQ 'PREC' OR
       sy-tcode EQ 'PRPY' OR
*      sy-tcode EQ 'TRIP' OR                    "QIZK049366 "QIZK006981
       sy-tcode CS 'TRIP' OR                                "QIZK006981
       ( sy-tcode(2) <> 'PR' AND sy-tcode(2) <> 'TG' )      "VJMPSTRG00
       OR sy-batch EQ 'X'
       OR NOT l_called_from_web IS INITIAL.                 "QIZK082944

      IF simulate EQ 'X'.
        IF NOT l_called_from_web IS INITIAL.                "QIZK082944
          CLEAR l_called_from_web.                          "QIZK082944
          FREE MEMORY ID 'CALLED_FROM_WEB'.                 "QIZK082944
        ENDIF.                                              "QIZK082944
* XUD: errorhandling for BAPI's
* only used within the function group HRTR, in form SUB_ABRECHNUNG
*       FREE MEMORY ID 'TS'.                                "QIZK049366
*       FREE MEMORY ID 'TE'.                                "QIZK049366
        FREE MEMORY ID te-key.                              "QIZK049366
* Begin of MAWK020779
*        e_type = 'E'.
*        e_id = '56'.
*        e_no = 16.
*        MOVE text TO e_v1.
*        MOVE argument TO e_v2.
*        CLEAR: e_v3, e_v4.
        IF use_sy_msg = abap_true.
          e_type = 'E'.
          e_id   = sy-msgid.
          e_no   = sy-msgno.
          e_v1   = sy-msgv1.
          e_v2   = sy-msgv2.
          e_v3   = sy-msgv3.
          e_v4   = sy-msgv4.
        ELSE.
          e_type = 'E'.
          e_id = '56'.
          e_no = 16.
          MOVE text TO e_v1.
          MOVE argument TO e_v2.
          CLEAR: e_v3, e_v4.
        ENDIF.
* End of MAWK020779
        EXPORT e_type e_id e_no e_v1 e_v2 e_v3 e_v4
               TO MEMORY ID 'TECERROR'.
      ELSE.
**********Start of ALV commenting  on 7 Feb 2005 --- C5056176 **********
*        SKIP.
*        WRITE: / text-e01, wa_perio-reinr,
*                 text-e02, pernr-pernr,
*                 text-e03.
*******End  of ALV commenting on 7 Feb 2005 --- C5056176 *********
**********Start of ALV coding on 7 Feb 2005 --- C5056176 **********
        READ TABLE gt_header INTO gs_header WITH KEY reinr = wa_perio-reinr.
        IF sy-subrc EQ 0.
* Begin KR2219041
          IF wa_perio-perio > 0 and PUBSEC_GERMANY eq true.
            MOVE text-e04 to gs_header-status.
          ELSEIF wa_perio-perio > 0 and PUBSEC_AUSTRIA eq true.
            MOVE text-e05 to gs_header-status.
          ELSE.
* End KR2219041
            MOVE text-e01 TO gs_header-status.
          ENDIF.                                          "KR2219041
          MOVE pernr-pernr TO gs_header-pernr.
          MODIFY gt_header FROM gs_header INDEX sy-tabix
                 TRANSPORTING status reinr pernr .
          CLEAR: gs_header-pernr,
                 gs_header-status.
***Start of changes after wdf review on 3 Mar 2005 --- C5056176
        ELSE.
* Begin KR2219041
          IF wa_perio-perio > 0 and PUBSEC_GERMANY eq true.
            MOVE text-e04 to gs_header-status.
          ELSEIF wa_perio-perio > 0 and PUBSEC_AUSTRIA eq true.
            MOVE text-e05 to gs_header-status.
          ELSE.
* End KR2219041
            MOVE text-e01 TO gs_header-status.
          ENDIF.                                          "KR2219041
          MOVE wa_perio-reinr TO gs_header-reinr.
          MOVE text-e02 TO gs_header-perstatus.
          MOVE pernr-pernr TO gs_header-pernr.
          APPEND gs_header TO gt_header.
          CLEAR: gs_header-pernr,
                 gs_header-status.
***end of changes after wdf review on 3 Mar 2005 --- C5056176

        ENDIF.
*******End  of ALV coding on 7 Feb 2005 --- C5056176************
      ENDIF.
    ELSE.
* Abrechnung / Simulation mit PF-Taste
*     FREE MEMORY ID 'TS'.                                  "QIZK049366
*     FREE MEMORY ID 'TE'.                                  "QIZK049366
      FREE MEMORY ID te-key.                                "QIZK049366
*     Begin of MAWK020779
*     MESSAGE i016 WITH text argument.
      IF use_sy_msg = abap_true.
        MESSAGE ID sy-msgid
              TYPE 'I'
            NUMBER sy-msgno
              WITH sy-msgv1
                   sy-msgv2
                   sy-msgv3
                   sy-msgv4.
      ELSE.
        MESSAGE i016 WITH text argument.
      ENDIF.
*     End of MAWK020779
* QIZK003787 used also for online simulation... begin
*     Begin of MAWK020779
*     e_type = 'E'.
*     e_id = '56'.
*     e_no = 16.
*     MOVE text TO e_v1.
*     MOVE argument TO e_v2.
*     CLEAR: e_v3, e_v4.
      IF use_sy_msg = abap_true.
        e_type = 'E'.
        e_id   = sy-msgid.
        e_no   = sy-msgno.
        e_v1   = sy-msgv1.
        e_v2   = sy-msgv2.
        e_v3   = sy-msgv3.
        e_v4   = sy-msgv4.
      ELSE.
        e_type = 'E'.
        e_id = '56'.
        e_no = 16.
        MOVE text TO e_v1.
        MOVE argument TO e_v2.
        CLEAR: e_v3, e_v4.
      ENDIF.
*     End of MAWK020779
      EXPORT e_type e_id e_no e_v1 e_v2 e_v3 e_v4
             TO MEMORY ID 'TECERROR'.
* QIZK003787 used also for online simulation... end
    ENDIF.
  ELSE.
**********Start of ALV commenting  on 7 Feb 2005 --- C5056176 **********
*    SKIP.
*******End  of ALV commenting on 7 Feb 2005 --- C5056176 *********
  ENDIF.
  DETAIL.
  rei_ablehn = 1.
  f = 1.
* GLW note 2029188 begin
  READ TABLE gt_ver WITH KEY
    reinr = wa_perio-reinr
    pernr = wa_perio-pernr TRANSPORTING NO FIELDS.
  IF sy-subrc IS NOT INITIAL.
    NEW-LINE.
  DATA: lv_line TYPE string.
  CONCATENATE text-z20 ': ' wa_perio-pernr ', ' text-i10 ': ' wa_perio-reinr INTO lv_line.
  WRITE lv_line INTENSIFIED ON COLOR COL_GROUP.
  NEW-LINE.
* GLW note 2029188 end
  ENDIF.
ENDFORM.                               "END OF REISE_ABLEHNUNG

*---------------------------------------------------------------------*
*       FORM ABLEHNUNG                                                *
*---------------------------------------------------------------------*
FORM ablehnung.

  DATA: e_type            LIKE sy-msgty,                    "QIZK000041
        e_id              LIKE sy-msgid,                    "QIZK000041
        e_no              LIKE sy-msgno,                    "QIZK000041
        e_v1              LIKE sy-msgv1,                    "QIZK000041
        e_v2              LIKE sy-msgv2,                    "QIZK000041
        e_v3              LIKE sy-msgv3,                    "QIZK000041
        e_v4              LIKE sy-msgv4,                    "QIZK000041
        l_called_from_web TYPE xfeld.                       "QIZK000041

* QIZK082944 begin...
  IF simulate = 'X'.
    IMPORT l_called_from_web FROM MEMORY ID 'CALLED_FROM_WEB'.
    IF sy-subrc NE 0.
      CLEAR l_called_from_web.
    ENDIF.
  ENDIF.
* QIZK082944 end...

  IF NOT ( sy-tcode    EQ 'PREC' OR
           sy-tcode    EQ 'PRPY' OR
*          sy-tcode    EQ 'TRIP' OR             "QIZK049366 "QIZK006981
           sy-tcode    CS 'TRIP' OR                         "QIZK006981
           sy-tcode(2) <> 'PR' OR
           NOT l_called_from_web IS INITIAL OR              "QIZK000041
           sy-batch EQ 'X' ).
* Abrechnung über Funktionstaste / Simulation
    FREE MEMORY ID 'TS'.
*   FREE MEMORY ID 'TE'.                                    "QIZK049366
    FREE MEMORY ID te-key.                                  "QIZK049366
    e_type = 'E'.                                           "QIZK000041
    e_id = '56'.                                            "QIZK000041
    e_no = 6.                                               "QIZK000041
    EXPORT e_type e_id e_no e_v1 e_v2 e_v3 e_v4             "QIZK000041
    TO MEMORY ID 'TECERROR'.                                "QIZK000041
    MESSAGE i006.
  ELSE.
* Abrechnung durch explizites Starten des RPRTEC
    SUMMARY.
    WRITE: / text-e10, pernr-pernr.
    SKIP 2.
    DETAIL.
    e_type = 'E'.                                           "QIZK000041
    e_id = '56'.                                            "QIZK000041
    e_no = 6.                                               "QIZK000041
    EXPORT e_type e_id e_no e_v1 e_v2 e_v3 e_v4             "QIZK000041
    TO MEMORY ID 'TECERROR'.                                "QIZK000041
  ENDIF.
  abgelehnt = abgelehnt + 1.

  IF NOT old_enqueue_active IS INITIAL."YEKAHRK049955
    PERFORM dequeue_pernr(sapfp50g) USING pernr-pernr.
  ELSE.                                "YEKAHRK049955
    PERFORM dequeue_trip USING pernr-pernr reinr_init.   "YEKAHRK049955
  ENDIF.                               "YEKAHRK049955
  PERFORM dequeue_epprele USING pernr-pernr.                "MAWK005054
  REJECT.
ENDFORM.                               "END OF ABLEHNUNG

*---------------------------------------------------------------------*
*       FORM CHECK_GESPERRT                                           *
*---------------------------------------------------------------------*
FORM check_gesperrt.
*  CHECK SY-BATCH IS INITIAL.                            "WBGK009191
  CHECK nolock = false.                                   "VJMPSTRG
  CHECK simulation IS INITIAL.
  CHECK sy-tcode    = 'PREC' OR        "WBGK009191 "QIZK010318
        sy-tcode(2) <> 'PR'.           "WBGK009191 "QIZK010318
  CHECK test = 'ON' OR
        test = 'OFF'.

  IF NOT old_enqueue_active IS INITIAL."YEKAHRK049955
    PERFORM enqueue_pernr(sapfp50g) USING pernr-pernr ' '.
  ELSE.                                "YEKAHRK049955
    PERFORM enqueue_trip USING pernr-pernr               "YEKAHRK049955
                               reinr_init                "YEKAHRK049955
                               space.  "YEKAHRK049955
  ENDIF.                               "YEKAHRK049955

  CHECK sy-subrc <> 0.
  gesperrt = gesperrt + 1.

*******Start of ALV commenting on 07 Feb 2005 --- C5056176 **********
*  ULINE.
*  FORMAT COLOR 1 INTENSIFIED OFF.
*  WRITE: / sy-vline NO-GAP,
*          'Gesperrte Personalnummer'(e09),
*           pernr-pernr,
*           79 sy-vline.
*  ULINE.
*  FORMAT RESET.
*******End of ALV commenting on 07 Feb 2005 --- C5056176 **********
*******Start of ALV coding on 07 Feb 2005 --- C5056176 **********
  CLEAR gs_header.
  MOVE text-e09 TO gs_header-perstatus.
  MOVE pernr-pernr TO gs_header-pernr.
  APPEND gs_header TO gt_header.
*******End of ALV coding on 07 Feb 2005 --- C5056176 **********
  REJECT.
ENDFORM.                    "check_gesperrt

*---------------------------------------------------------------------*
*       FORM ERROR_TEXT                                               *
*---------------------------------------------------------------------*
FORM  error_text
USING viewname.

  TABLES: dd27p.

  DATA: BEGIN OF dd27p_tab OCCURS 20.
          INCLUDE STRUCTURE dd27p.
  DATA: END OF dd27p_tab.

  DATA: BEGIN OF dd27p_dummy OCCURS 20.
          INCLUDE STRUCTURE dd27p.
  DATA: END OF dd27p_dummy.

  DATA: got_state LIKE dcviewget-vifd,
        name(20).
*  name = text-050.    "KR2219041

  FIELD-SYMBOLS <f>.

  CALL FUNCTION 'DD_VIFD_GET'
    EXPORTING
      get_state     = 'M'
      langu         = sy-langu
      prid          = 0
      view_name     = viewname
      withtext      = ' '
    IMPORTING
      got_state     = got_state
    TABLES
      dd27p_tab_a   = dd27p_dummy
      dd27p_tab_n   = dd27p_tab
    EXCEPTIONS
      illegal_value = 01.

**********Start of ALV commenting  on 7 Feb 2005 --- C5056176 **********
*  DETAIL.
*  ULINE.
*  WRITE: / 'Kein Eintrag in'(vi1), viewname INTENSIFIED, 'für'(vi2).
*  SUMMARY.
*  WRITE: / 'Schlüssel'(vi3), 30 'Wert'(vi4).
*  DETAIL.
*******End  of ALV commenting on 7 Feb 2005 --- C5056176 *********
**********Start of ALV coding on 7 Feb 2005 --- C5056176 **********
  MOVE viewname TO gs_test-viewname.
  APPEND gs_test TO gt_test.
*******End  of ALV coding on 7 Feb 2005 --- C5056176************

  LOOP AT dd27p_tab WHERE keyflag = 'X'
                    AND   rollnamevi <> 'MANDT'.

    IF dd27p_tab-rollnamevi = 'ENDDA'.
      dd27p_tab-rollnamevi = 'DATE '.
    ENDIF.
    SELECT * FROM dd04t WHERE rollname   = dd27p_tab-rollnamevi
                        AND   ddlanguage = syst-langu
                        AND   as4local   = 'A'.
      EXIT.
    ENDSELECT.
    IF sy-subrc <> 0.
      CLEAR dd04t-scrtext_l.
    ENDIF.

* Begin KR2219041
*    name+0(5) =  dd27p_tab-tabname.
*    name+6(5) =  dd27p_tab-fieldname.
    CONCATENATE dd27p_tab-tabname '-' dd27p_tab-fieldname into name.
* End KR2219041
    ASSIGN TABLE FIELD (name) TO <f>.
    IF sy-subrc <> 0.
      ASSIGN (space) TO <f>.
    ENDIF.

**********Start of ALV commenting  on 7 Feb 2005 --- C5056176 **********
*    WRITE: / dd04t-scrtext_l(25) UNDER text-vi3,
*             <f> INTENSIFIED     UNDER text-vi4.
*******End  of ALV commenting on 7 Feb 2005 --- C5056176 *********
**********Start of ALV coding on 7 Feb 2005 --- C5056176 **********
    IF sy-tabix EQ 2.
      MOVE dd04t-scrtext_l(25) TO gv_keyvalue.
    ENDIF.
    MOVE dd04t-scrtext_l(25) TO gs_errtxt-key_value.
    WRITE <f> TO gs_errtxt-value.
    MOVE gs_header-reinr TO gs_errtxt-reinr.
    APPEND gs_errtxt TO gt_errtxt.
    CLEAR :gs_errtxt-key_value,
           gs_errtxt-value,
           gs_errtxt-reinr.
*******End  of ALV coding on 7 Feb 2005 --- C5056176************
  ENDLOOP.
**********Start of ALV commenting  on 7 Feb 2005 --- C5056176 **********
*  ULINE.
*******End  of ALV commenting on 7 Feb 2005 --- C5056176 *********
ENDFORM.                    "error_text

*---------------------------------------------------------------------*
*       FORM ERROR_T706A                                              *
*---------------------------------------------------------------------*
FORM error_t706a.
  t706a = *t706a.
  PERFORM error_text USING 'V_T706A'.
  CLEAR t706a.
ENDFORM.                    "error_t706a

*---------------------------------------------------------------------*
*       FORM ERROR_T706B1                                             *
*---------------------------------------------------------------------*
FORM error_t706b1.
  t706b1 = *t706b1.
  CASE t706b1-paush.
    WHEN ' '.
      PERFORM error_text USING 'V_T706B1'.
    WHEN 'P'.
      PERFORM error_text USING 'V_706B1_A'.
  ENDCASE.
  CLEAR t706b1.
ENDFORM.                    "error_t706b1

*---------------------------------------------------------------------*
*       FORM ERROR_T706B4                                             *
*---------------------------------------------------------------------*
FORM error_t706b4 USING VALUE(paush).
  t706b4 = *t706b4.
  CASE paush.
    WHEN ' '.
      PERFORM error_text USING 'V_T706B4'.
    WHEN 'P'.
      PERFORM error_text USING 'V_706B4_A'.
  ENDCASE.
  CLEAR t706b4.
ENDFORM.                    "error_t706b4

*---------------------------------------------------------------------*
*       FORM ERROR_T706F                                              *
*---------------------------------------------------------------------*
FORM error_t706f.
  t706f = *t706f.
  PERFORM error_text USING 'V_T706F'.
  CLEAR t706f.
ENDFORM.                    "error_t706f

*---------------------------------------------------------------------*
*       FORM ERROR_T706H                                              *
*---------------------------------------------------------------------*
FORM error_t706h.
  t706h = *t706h.
  CASE t706v-kzpah.
    WHEN 'P'.
      PERFORM error_text USING 'V_T706H'.
    WHEN 'H'.
      PERFORM error_text USING 'V_706H_B'.
  ENDCASE.
  CLEAR t706h.
ENDFORM.                    "error_t706h

*---------------------------------------------------------------------*
*       FORM ERROR_T706P                                              *
*---------------------------------------------------------------------*
FORM error_t706p.
  t706p = *t706p.
  PERFORM error_text USING 'V_T706P'.
  CLEAR t706p.
ENDFORM.                    "error_t706p

*---------------------------------------------------------------------*
*       FORM ERROR_T706S                                              *
*---------------------------------------------------------------------*
FORM error_t706s.
  t706s = *t706s.
  PERFORM error_text USING 'V_T706S'.
  CLEAR t706s.
ENDFORM.                    "error_t706s

*---------------------------------------------------------------------*
*       FORM ERROR_T706U                                              *
*---------------------------------------------------------------------*
FORM error_t706u.
  t706u = *t706u.
  CASE t706u-kzpah.
    WHEN 'P'.
      PERFORM error_text USING 'V_T706U'.
    WHEN 'H'.
      PERFORM error_text USING 'V_706U_B'.
  ENDCASE.
  CLEAR t706u.
ENDFORM.                    "error_t706u

*---------------------------------------------------------------------*
*       FORM ERROR_T706V                                              *
*---------------------------------------------------------------------*
FORM error_t706v.
  t706v = *t706v.
  CASE t706v-kzpah.
    WHEN 'P'.
      PERFORM error_text USING 'V_T706V'.
    WHEN 'H'.
      PERFORM error_text USING 'V_706V_B'.
  ENDCASE.
  CLEAR t706v.
ENDFORM.                    "error_t706v

*&---------------------------------------------------------------------*
*&      Form  ABRECHNUNG_SPERRT_PERNR
*&---------------------------------------------------------------------*
*       This routine checks if the personalnumber is locked by the
*       payroll accounting
*----------------------------------------------------------------------*
FORM abrechnung_sperrt_pernr.
  CHECK simulation IS INITIAL.  "GLW note 2096447
  CHECK lgpa3 IS NOT INITIAL.       "GLW note 2097650
  CHECK p0003-abrsp NE space.
  IF NOT ( sy-tcode    EQ 'PREC' OR
*          sy-tcode    EQ 'TRIP' OR             "QIZK049366 "QIZK006981
           sy-tcode    CS 'TRIP' OR                         "QIZK006981
           sy-tcode(2) <> 'PR'   OR
           sy-tcode    CS 'PR_WEB' OR                       "QIZK000041
           sy-batch EQ 'X' ).
* Abrechnung über Funktionstaste / Simulation
    FREE MEMORY ID 'TS'.
*   FREE MEMORY ID 'TE'.                                    "QIZK049366
    FREE MEMORY ID te-key.                                  "QIZK049366
    MESSAGE i165 WITH pernr-pernr.
  ELSE.
* Abrechnung durch explizites Starten des RPRTEC
    FORMAT INTENSIFIED ON.
    WRITE: / text-e19, pernr-pernr.
    SKIP 2.
    FORMAT INTENSIFIED OFF.
  ENDIF.
  abgelehnt = abgelehnt + 1.
  REJECT.
ENDFORM.                               " ABRECHNUNG_SPERRT_PERNR

*---------------------------------------------------------------------*
*       FORM RE706_CONST                                              *
*QKZK007494 Routine wurde zu 4.0C neu geschrieben und löst die Routine*
*           RE511K ab. Konstanten stehen in der neuen Tabelle         *
*---------------------------------------------------------------------*
FORM  re706_const
USING VALUE(morei) VALUE(konst) VALUE(date)
*      endda begda kwert waers zeit datum.
      subrc                                                 "QKZK018282
      endda begda kwert waers zeit datum anzahl.            "QKZK018282

  CLEAR subrc.                                              "XOWK057099

* begin ZFJ3102764
* legal change Baden-Württemberg 01.01.2022
* Für Reisen über den Stichtag Konstanten mit Reisebeginndatum lesen
* begin ZFJ3128309 LC NRW 2022
*  IF bwuert = true AND
  IF ( bwuert = true OR nrw = true ) AND
* end ZFJ3128309
     wa_perio-pdatv < '20220101' AND
     date >= '20220101'.
    date = wa_perio-pdatv.    "mit erstem Reisetag lesen
  ENDIF.
* end ZFJ3102764

  IF t706_const-morei <> morei OR
     t706_const-konst <> konst OR
     NOT ( date BETWEEN t706_const-begda AND t706_const-endda ).

    t706_const = space.
    t706_const-morei = morei.
    t706_const-konst = konst.
    t706_const-endda = date.
    *t706_const = t706_const.

    SELECT * FROM t706_const UP TO 1 ROWS WHERE morei = morei
                                          AND   konst = konst
                                          AND   begda =< date
                                          AND   endda >= date.
      EXIT.
    ENDSELECT.
    subrc = sy-subrc.                                 "XCIKI4PSCO_CONST

    IF sy-subrc <> 0 OR
       t706_const-morei <> morei OR
       t706_const-konst <> konst OR
       NOT ( date BETWEEN t706_const-begda AND t706_const-endda ).
* Constant REIFA not found, use initial value '1'
      IF konst = 'REIFA'.
        kwert = t706_const-kwert = '1'.
        endda = date.
        begda = date.
        EXIT.
      ENDIF.
      IF konst = 'UANTL'.                                   "VJMKTG01
        kwert = t706_const-kwert = '0'.                     "VJMKTG01
        endda = date.                                       "VJMKTG01
        begda = date.                                       "VJMKTG01
        EXIT.                                               "VJMKTG01
      ENDIF.                                                "VJMKTG01
      IF konst = 'GENSA'.                                   "VJMKBGC01
        kwert = t706_const-kwert = '0'.                     "VJMKBGC01
        endda = date.                                       "VJMKBGC01
        begda = date.                                       "VJMKBGC01
        EXIT.                                               "VJMKBGC01
      ENDIF.                                                "VJMKBGC01
      IF konst = 'BSRHW'.                                "VJMPSHWBAY03
        kwert = t706_const-kwert = '0'.                  "VJMPSHWBAY03
        endda = date.                                    "VJMPSHWBAY03
        begda = date.                                    "VJMPSHWBAY03
        EXIT.                                            "VJMPSHWBAY03
      ENDIF.                                             "VJMPSHWBAY03
      IF konst = 'USTR6'                                    "VJMKTGST03
      OR konst = 'USTR8'                                    "VJMKTGST03
      OR konst = 'USTR9'.                                   "VJMKTGST03
        kwert = t706_const-kwert = '0'.                     "VJMKTGST03
        endda = date.                                       "VJMKTGST03
        begda = date.                                       "VJMKTGST03
        EXIT.                                               "VJMKTGST03
      ENDIF.                                                "VJMKTGST03
      IF konst = 'UGVPF'.                                  "VJMKPSABZ01
        anzahl = t706_const-anzahl = '0'.                  "VJMKPSABZ01
        endda = date.                                      "VJMKPSABZ01
        begda = date.                                      "VJMKPSABZ01
        EXIT.                                              "VJMKPSABZ01
      ENDIF.                                               "VJMKPSABZ01
      IF konst = 'TAXRC'.                                   "XCI1763323
        anzahl = t706_const-anzahl = '0'.                   "XCI1763323
        endda = date.                                       "XCI1763323
        begda = date.                                       "XCI1763323
        EXIT.                                               "XCI1763323
      ENDIF.                                                "XCI1763323
      IF konst = 'ESSBO'.                                   "VJMK902193
        anzahl = t706_const-anzahl = '0'.                   "VJMK902193
        endda = date.                                       "VJMK902193
        begda = date.                                       "VJMK902193
        EXIT.                                               "VJMK902193
      ENDIF.                                                "VJMK902193
      IF konst = 'VRATG'.                                   "XCI1493904
        anzahl = t706_const-anzahl = '0'.                   "XCI1493904
        endda = date.                                       "XCI1493904
        begda = date.                                       "XCI1493904
        EXIT.                                               "XCI1493904
      ENDIF.                                                "XCI1493904
      IF konst = 'SBVER'.                                   "XCIN940846
        anzahl = t706_const-anzahl = '0'.                   "XCIN940846
        endda = date.                                       "XCIN940846
        begda = date.                                       "XCIN940846
        EXIT.                                               "XCIN940846
      ENDIF.                                                "XCIN940846
      IF konst = 'MAXBR'.                                   "KCNK010787
        anzahl = t706_const-anzahl = '0'.                   "KCNK010787
        endda = date.                                       "KCNK010787
        begda = date.                                       "KCNK010787
        CLEAR t706_const-konst.                             "ARIK019653
        EXIT.                                               "KCNK010787
      ENDIF.                                                "KCNK010787
      IF konst = 'SBVER'.                                   "XCIN940846
        anzahl = t706_const-anzahl = '0'.                   "XCIN940846
        endda = date.                                       "XCIN940846
        begda = date.                                       "XCIN940846
        EXIT.                                               "XCIN940846
      ENDIF.                                                "XCIN940846
      IF konst = 'HTLBD'.                                   "XCI1709579
        anzahl = t706_const-anzahl = '0'.                   "XCI1709579
        endda = date.                                       "XCI1709579
        begda = date.                                       "XCI1709579
        EXIT.                                               "XCI1709579
      ENDIF.                                                "XCI1709579
      IF konst = 'MAHUB'.                                   "XCI1581544
        anzahl = t706_const-anzahl = '0'.                   "XCI1581544
        endda = date.                                       "XCI1581544
        begda = date.                                       "XCI1581544
        EXIT.                                               "XCI1581544
      ENDIF.                                                "XCI1581544
      IF konst = 'REIMN'.                                  "VJMK1043474
        anzahl = t706_const-anzahl = '0'.                  "VJMK1043474
        endda = date.                                      "VJMK1043474
        begda = date.                                      "VJMK1043474
        CLEAR t706_const-konst.                            "VJMK1043474
        EXIT.                                              "VJMK1043474
      ENDIF.                                               "VJMK1043474
      IF konst = 'REIES'.                                   "KCNK014429
        anzahl = t706_const-anzahl = '0'.                   "KCNK014429
        endda = date.                                       "KCNK014429
        begda = date.                                       "KCNK014429
        EXIT.                                               "KCNK014429
      ENDIF.                                                "KCNK014429
      IF konst = 'MAXRE'.                                   "KCN1677116
        anzahl = t706_const-anzahl = '0'.                   "KCN1677116
        endda = date.                                       "KCN1677116
        begda = date.                                       "KCN1677116
        EXIT.                                               "KCN1677116
      ENDIF.                                                "KCN1677116
      IF konst = 'LASDA' AND wa_head-molga = '20'.          "QKZK018668
        anzahl = t706_const-anzahl = '0'.                   "QKZK018668
        endda = date.                                       "QKZK018668
        begda = date.                                       "QKZK018668
        EXIT.                                               "QKZK018668
      ENDIF.                                                "QKZK018668
      IF konst = 'FOWTD'.                                  "SVTK1558805
        anzahl = '0'.                                      "SVTK1558805
        endda = date.                                      "SVTK1558805
        begda = date.                                      "SVTK1558805
        CLEAR t706_const-konst.                            "SVTK1558805
        EXIT.                                              "SVTK1558805
      ENDIF.
* Begin ZFJ1944819 LC2014PS
      IF konst = 'GLVIN'.
        CLEAR datum.
        endda = date.
        begda = date.
        CLEAR t706_const-konst.
        EXIT.
      ENDIF.
      IF konst = 'GLVAU'.
        CLEAR datum.
        endda = date.
        begda = date.
        CLEAR t706_const-konst.
        EXIT.
      ENDIF.
* End ZFJ1944819 LC2014PS
* Begin ZFJ1962438 LC2014PS
      IF konst = 'LC14U'.
        anzahl = '0'.
        endda = date.
        begda = date.
        CLEAR t706_const-konst.
        EXIT.
      ENDIF.
* End ZFJ1962438 LC2014PS
      IF konst = 'REIZU'.                                  "SVTK2271096
        anzahl = 0.                                        "SVTK2271096
        endda = date.                                      "SVTK2271096
        begda = date.                                      "SVTK2271096
        CLEAR t706_const-konst.                            "SVTK2271096
        EXIT.                                              "SVTK2271096
      ENDIF.                                               "SVTK2271096
      IF konst = 'FALDA'.                                  "SVTK1579101
        anzahl = '0'.                                      "SVTK1579101
        endda = date.                                      "SVTK1579101
        begda = date.                                      "SVTK1579101
        CLEAR t706_const-konst.                            "SVTK1579101
        EXIT.                                              "SVTK1579101
      ENDIF.                                               "SVTK1579101
      IF konst = 'KAPUB'.                                  "SVTK2038385
        anzahl = '0'.                                      "SVTK2038385
        endda = date.                                      "SVTK2038385
        begda = date.                                      "SVTK2038385
        CLEAR t706_const-konst.                            "SVTK2038385
        EXIT.                                              "SVTK2038385
      ENDIF.                                               "SVTK2038385
* begin ZFJ2753126
      IF konst = 'DGBEG'.
        kwert = '0'.
        endda = date.
        begda = date.
        CLEAR t706_const-konst.
        EXIT.
      ENDIF.
* end ZFJ2753126
* XCI1977623 begin
      IF konst = 'UDH14'.
        kwert = '0'.
        endda = date.
        begda = date.
        CLEAR t706_const-konst.
        EXIT.
      ENDIF.
* XCI1977623 end
* XCI2579598 begin
      IF konst = 'NOWER'.
        kwert = '0'.
        endda = date.
        begda = date.
        CLEAR t706_const-konst.
        EXIT.
      ENDIF.
* XCI2579598 end
* begin ZFJ2005317
      IF konst = 'WGNOK'.
        anzahl = '0'.
        endda = date.
        begda = date.
        CLEAR t706_const-konst.
        EXIT.
      ENDIF.
* end ZFJ2005317
* begin ZFJ2636495
      IF konst = 'TRGFZ'.
        anzahl = '0'.
        endda = date.
        begda = date.
        CLEAR t706_const-konst.
        EXIT.
      ENDIF.
* end ZFJ2636495
* XCI3042835 begin
      IF konst = 'EIGKM'.
        anzahl = '0'.
        endda = date.
        begda = date.
        CLEAR t706_const-konst.
        EXIT.
      ENDIF.
* XCI3042835 end
      IF konst = 'IJMAX'.                                   "KCN1686404
        anzahl = '0'.                                       "KCN1686404
        endda = date.                                       "KCN1686404
        begda = date.                                       "KCN1686404
        CLEAR t706_const-konst.                             "KCN1686404
        EXIT.                                               "KCN1686404
      ENDIF.                                                "KCN1686404
      IF konst = 'FNOVM'.                                  "SVTK1615274
        anzahl = '0'.                                      "SVTK1615274
        endda = date.                                      "SVTK1615274
        begda = date.                                      "SVTK1615274
        CLEAR t706_const-konst.                            "SVTK1615274
        EXIT.                                              "SVTK1615274
      ENDIF.                                               "SVTK1615274
      IF konst = 'WEGST'.                                  "SVTK1930828
        anzahl = '0'.                                      "SVTK1930828
        endda = date.                                      "SVTK1930828
        begda = date.                                      "SVTK1930828
        CLEAR t706_const-konst.                            "SVTK1930828
        EXIT.                                              "SVTK1930828
      ENDIF.                                               "SVTK1930828
      IF konst = 'TRGFZ'.                                   "ZFJ2581607
        anzahl = '0'.                                       "ZFJ2581607
        endda = date.                                       "ZFJ2581607
        begda = date.                                       "ZFJ2581607
        CLEAR t706_const-konst.                             "ZFJ2581607
        EXIT.                                               "ZFJ2581607
      ENDIF.                                                "ZFJ2581607
      IF konst = 'ABWZH'.                                   "ZFJ1731527
        anzahl = '0'.                                       "ZFJ1731527
        endda = date.                                       "ZFJ1731527
        begda = date.                                       "ZFJ1731527
        CLEAR t706_const-konst.                             "ZFJ1731527
        EXIT.                                               "ZFJ1731527
      ENDIF.                                                "ZFJ1731527
      IF konst = 'ACMAX'.                                   "XCI2419310
        anzahl = t706_const-anzahl = '0'.                   "XCI2419310
        endda = date.                                       "XCI2419310
        begda = date.                                       "XCI2419310
        EXIT.                                               "XCI2419310
      ENDIF.                                                "XCI2419310
      IF konst = 'NAZUM'.                                   "ZFJ1766319
        anzahl = '0'.                                       "ZFJ1766319
        endda = date.                                       "ZFJ1766319
        begda = date.                                       "ZFJ1766319
        CLEAR t706_const-konst.                             "ZFJ1766319
        EXIT.                                               "ZFJ1766319
      ENDIF.                                                "ZFJ1766319
      IF konst = 'TRGRG'.                                   "VJMK1378820
        anzahl = t706_const-anzahl = '0'.                   "VJMK1378820
        endda = date.                                       "VJMK1378820
        begda = date.                                       "VJMK1378820
        EXIT.                                               "VJMK1378820
      ENDIF.                                                "VJMK1378820
      IF konst = 'ODBMX'.                                  "VJMK1490320
        anzahl = t706_const-anzahl = '0'.                  "VJMK1490320
        endda = date.                                      "VJMK1490320
        begda = date.                                      "VJMK1490320
        EXIT.                                              "VJMK1490320
      ENDIF.                                               "VJMK1490320
      IF konst = 'BFA11'.                                  "VJMK1616645
        anzahl = t706_const-anzahl = '0'.                  "VJMK1616645
        endda = date.                                      "VJMK1616645
        begda = date.                                      "VJMK1616645
        EXIT.                                              "VJMK1616645
      ENDIF.                                               "VJMK1616645
      IF konst = 'ABZ14'.                                   "KCN1826920
        anzahl = t706_const-anzahl = '0'.                   "KCN1826920
        endda = date.                                       "KCN1826920
        begda = date.                                       "KCN1826920
        EXIT.                                               "KCN1826920
      ENDIF.                                                "KCN1826920
      IF konst = 'EBPDM'.                                  "VJMK1830241
        anzahl = t706_const-anzahl = '0'.                  "VJMK1830241
        endda = date.                                      "VJMK1830241
        begda = date.                                      "VJMK1830241
        EXIT.                                              "VJMK1830241
      ENDIF.                                               "VJMK1830241
      IF konst = 'TRPDR'.                                  "ZFJ2676747
        anzahl = t706_const-anzahl = '0'.                  "ZFJ2676747
        endda = date.                                      "ZFJ2676747
        begda = date.                                      "ZFJ2676747
        EXIT.                                              "ZFJ2676747
      ENDIF.                                               "ZFJ2676747
      IF konst = 'UEBRS'.                                  "VJMK1868035
        anzahl = t706_const-anzahl = '0'.                  "VJMK1868035
        endda = date.                                      "VJMK1868035
        begda = date.                                      "VJMK1868035
        EXIT.                                              "VJMK1868035
      ENDIF.                                               "VJMK1868035
      IF konst = 'CATJC'.                                  "KCN2290457
        anzahl = t706_const-anzahl = '0'.                  "KCN2290457
        endda = date.                                      "KCN2290457
        begda = date.                                      "KCN2290457
        EXIT.                                              "KCN2290457
      ENDIF.                                               "KCN2290457
      IF konst = 'REDAC'.                                  "KR2288011
        anzahl = t706_const-anzahl = '0'.                  "KR2288011
        endda = date.                                      "KR2288011
        begda = date.                                      "KR2288011
        EXIT.                                              "KR2288011
      ENDIF.                                               "KR2288011
      IF konst = 'REIGH'.                                  "KR2361918
        zeit = t706_const-zeit = '000000'.                 "KR2361918
        endda = date.                                      "KR2361918
        begda = date.                                      "KR2361918
        EXIT.                                              "KR2361918
      ENDIF.                                               "KR2361918
      IF konst = 'REIGR'.                                  "KR2361918
        zeit = t706_const-zeit = '000000'.                 "KR2361918
        endda = date.                                      "KR2361918
        begda = date.                                      "KR2361918
        EXIT.                                              "KR2361918
      ENDIF.                                               "KR2361918
      IF konst = 'OVBGL'.                                  "KR2361918
        zeit = t706_const-zeit = '000000'.                 "KR2361918
        endda = date.                                      "KR2361918
        begda = date.                                      "KR2361918
        EXIT.                                              "KR2361918
      ENDIF.                                               "KR2361918
      IF konst = 'OVENL'.                                  "KR2361918
        zeit = t706_const-zeit = '000000'.                 "KR2361918
        endda = date.                                      "KR2361918
        begda = date.                                      "KR2361918
        EXIT.                                              "KR2361918
      ENDIF.                                               "KR2361918
      IF konst = 'OVMIN'.                                  "KR2361918
        zeit = t706_const-anzahl = '0'.                    "KR2361918
        endda = date.                                      "KR2361918
        begda = date.                                      "KR2361918
        EXIT.                                              "KR2361918
      ENDIF.                                               "KR2361918
      IF konst = 'VER10'.                                  "KCN2537190
        zeit = t706_const-zeit = '000000'.                 "KCN2537190
        endda = date.                                      "KCN2537190
        begda = date.                                      "KCN2537190
        EXIT.                                              "KCN2537190
      ENDIF.                                               "KCN2537190
      IF konst = 'VER15'.                                  "KCN2537190
        zeit = t706_const-zeit = '000000'.                 "KCN2537190
        endda = date.                                      "KCN2537190
        begda = date.                                      "KCN2537190
        EXIT.                                              "KCN2537190
      ENDIF.                                               "KCN2537190
      IF konst = 'KETGY'.                                  "XCI3249619
        zeit = t706_const-anzahl = '0'.                    "XCI3249619
        endda = date.                                      "XCI3249619
        begda = date.                                      "XCI3249619
        EXIT.                                              "XCI3249619
      ENDIF.                                               "XCI3249619
      IF konst = 'KETMO'.                                  "XCI3249619
        zeit = t706_const-anzahl = '0'.                    "XCI3249619
        endda = date.                                      "XCI3249619
        begda = date.                                      "XCI3249619
        EXIT.                                              "XCI3249619
      ENDIF.                                               "XCI3249619
      IF konst = 'KERTY'.                                  "KR2468994
        zeit = t706_const-anzahl = '0'.                    "KR2468994
        endda = date.                                      "KR2468994
        begda = date.                                      "KR2468994
        EXIT.                                              "KR2468994
      ENDIF.                                               "KR2468994
      IF konst = 'KERMO'.                                  "KR2468994
        zeit = t706_const-anzahl = '0'.                    "KR2468994
        endda = date.                                      "KR2468994
        begda = date.                                      "KR2468994
        EXIT.                                              "KR2468994
      ENDIF.                                               "KR2468994
      IF konst = 'TGFLX'.                                   "ZFJ2930337
        anzahl = t706_const-anzahl = '0'.                   "ZFJ2930337
        endda = date.                                       "ZFJ2930337
        begda = date.                                       "ZFJ2930337
        EXIT.                                               "ZFJ2930337
      ENDIF.                                                "ZFJ2930337
      IF konst = 'PRUAK'.                                  "XCI2535121
        zeit = t706_const-anzahl = '0'.                    "XCI2535121
        endda = date.                                      "XCI2535121
        begda = date.                                      "XCI2535121
        EXIT.                                              "XCI2535121
      ENDIF.                                               "XCI2535121
      IF konst = 'PRUAZ'.                                  "XCI2535121
        zeit = t706_const-anzahl = '0'.                    "XCI2535121
        endda = date.                                      "XCI2535121
        begda = date.                                      "XCI2535121
        EXIT.                                              "XCI2535121
      ENDIF.                                               "XCI2535121
      IF konst = 'KSTOV'.                                  "ZFJ2889423
        " Default: 1. Jan 2020                             "ZFJ2889423
        datum = '20200101'.                                "ZFJ2889423
        endda = date.                                      "ZFJ2889423
        begda = date.                                      "ZFJ2889423
        EXIT.                                              "ZFJ2889423
      ENDIF.                                               "ZFJ2889423
      IF konst = 'KSTOW'.                                  "XCI2993401
        zeit = t706_const-anzahl = '0'.                    "XCI2993401
        endda = date.                                      "XCI2993401
        begda = date.                                      "XCI2993401
        EXIT.                                              "XCI2993401
      ENDIF.                                               "XCI2993401
      IF konst = 'REIGT'.                                   "KCN3127335
        zeit = t706_const-anzahl = '0'.                     "KCN3127335
        endda = date.                                       "KCN3127335
        begda = date.                                       "KCN3127335
        EXIT.                                               "KCN3127335
      ENDIF.                                                "KCN3127335

* QKZN1950679 Begin Sachbezug 2014
      IF konst = 'SBZF' or konst = 'SBZM' or konst = 'SBZA'.
        kwert = t706_const-kwert = '0'.
        endda = date.
        begda = date.
        EXIT.
      ENDIF.
* QKZN1950679 end

* VRD_CEE_RU begin RU-Version - tax limit
      IF konst = 'DTXFR'.
        kwert = t706_const-kwert = '0'.
        endda = date.
        begda = date.
        EXIT.
      ENDIF.
* VRD_CEE_RU end RU-Version - tax limit
* begin ZFJ2991533
       IF konst = 'ENTK2'
          OR konst = 'EIGBW'.                 "ZFJ3203425
        kwert = t706_const-kwert = '0'.
        anzahl = t706_const-anzahl = '0'.
        endda = date.
        begda = date.
        EXIT.
      ENDIF.
* end ZFJ2991533
      IF ( konst = 'ENTKM' OR konst = 'VERZU' ) AND wa_head-molga NE '01'. "GLWE34K016560
        EXIT.                                                              "GLWE34K016560
      ENDIF.                                                               "GLWE34K016560
      IF konst = 'FD_FA'
      OR konst = 'FD_FZ'
      OR konst = 'FD_KU'
      OR konst = 'LD_FA'
      OR konst = 'LD_FZ'
      OR konst = 'LD_KU'.
        kwert = t706_const-kwert = '0'.
        endda = date.
        begda = date.
        EXIT.
      ENDIF.
      t706_const = space.
      NEW-PAGE.
      SKIP.
* QKZK000728 Unicodeumstellung Beginn
*      WRITE: / TEXT-P12, 'T706_CONST', *T706_CONST.
      WRITE: / text-p12, 'T706_CONST', *t706_const(18).
* QKZK000728 Unicodeumstellung Ende
      PERFORM ablehnung.
    ENDIF.
    IF NOT ( t706_const-waers IS INITIAL )
      AND t706_const-waers NE wa_perio-waers
      AND wa_perio-waers IS NOT INITIAL                     "XCI3042835
      AND varia_r-recurr EQ 1.
      IF NOT t706_const-kwert IS INITIAL.
        CALL FUNCTION 'CONVERT_TO_LOCAL_CURRENCY'
          EXPORTING
            date             = date
            foreign_amount   = t706_const-kwert
            foreign_currency = t706_const-waers
            local_currency   = wa_perio-waers
            rate             = 0
            type_of_rate     = t706d-kurst
          IMPORTING
            local_amount     = t706_const-kwert
          EXCEPTIONS
            no_rate_found    = 04
            overflow         = 08.

        PERFORM nicht_in_tcurr
        USING   sy-subrc t706_const-waers wa_perio-waers.
        t706_const-waers = wa_perio-waers.
      ENDIF.
    ENDIF.
  ENDIF.

  endda = t706_const-endda.
  begda = t706_const-begda.
  kwert = t706_const-kwert.
  waers = t706_const-waers.
  zeit = t706_const-zeit.
  datum = t706_const-datum.
  anzahl = t706_const-anzahl.                               "QKZK018282
  *t706_const = t706_const.

ENDFORM.                               "END OF RE706_const

* ABSBKK900038 start
*&---------------------------------------------------------------------*
*&      Form  RE702G
*&---------------------------------------------------------------------*
*----------------------------------------------------------------------*
*      --> FG_U_KZREA traveltype
*      <-- FG_INAUS key for special types of travel parts
*      <-- FG_DELEG key for delegation
*----------------------------------------------------------------------*
FORM re702g
USING    fg_u_kzrea
         fg_geskz
         fg_inaus
         fg_deleg.

  SELECT * FROM t702g WHERE morei EQ wa_head-morei AND
                            kzrea EQ fg_u_kzrea.
    fg_geskz = t702g-geskz.
    fg_inaus = t702g-tripsplitt.
    fg_deleg = t702g-delegation.
  ENDSELECT.

ENDFORM.                               "END OF RE702G
* ABSBKK900038 end

*---------------------------------------------------------------------*
*       FORM RE706B2                                                  *
*---------------------------------------------------------------------*
*       new in 99A        XOWK033175                                  *
*---------------------------------------------------------------------*

FORM  re706b2
USING VALUE(morei) VALUE(kzrea)
      VALUE(berei) VALUE(kztkt)
      VALUE(lndgr) VALUE(rgion)
      VALUE(erkla) VALUE(ergru)
      VALUE(spkzl) VALUE(atype)
      VALUE(datum)
      endda begda waers betrg.

*  PERFORM EXB706B2
*  USING   MOREI KZREA
*          BEREI  KZTKT
*          LNDGR RGION
*          ERKLA ERGRU
*          SPKZL ATYPE
*          DATUM.

  IF t706b2-morei <> morei OR
     t706b2-kzrea <> kzrea OR
     t706b2-berei <> berei OR
     t706b2-kztkt <> kztkt OR
     t706b2-lndgr <> lndgr OR
     t706b2-rgion <> rgion OR
     t706b2-erkla <> erkla OR
     t706b2-ergru <> ergru OR
     t706b2-spkzl <> spkzl OR
     t706b2-atype <> atype OR
     NOT ( datum BETWEEN t706b2-begda
                 AND     t706b2-endda ).

    t706b2 = space.
    t706b2-morei = morei.
    t706b2-kzrea = kzrea.
    t706b2-berei = berei.
    t706b2-kztkt = kztkt.
    t706b2-lndgr = lndgr.
    t706b2-rgion = rgion.
    t706b2-erkla = erkla.
    t706b2-ergru = ergru.
    t706b2-spkzl = spkzl.
    t706b2-atype = atype.
    t706b2-endda = datum.
    *t706b2 = t706b2.

    SELECT * FROM t706b2 WHERE morei = morei
                        AND   kzrea = kzrea
                        AND   berei = berei
                        AND   kztkt = kztkt
                        AND   lndgr = lndgr
                        AND   rgion = rgion
                        AND   erkla = erkla
                        AND   ergru = ergru
                        AND   spkzl = spkzl
                        AND   atype = atype
                        AND   endda >= datum
                        AND   begda <= datum.
      EXIT.
    ENDSELECT.

    IF sy-subrc    <> 0     OR
       t706b2-morei <> morei OR
       t706b2-kzrea <> kzrea OR
       t706b2-berei <> berei OR
       t706b2-kztkt <> kztkt OR
       t706b2-lndgr <> lndgr OR
       t706b2-rgion <> rgion OR
       t706b2-erkla <> erkla OR
       t706b2-ergru <> ergru OR
       t706b2-spkzl <> spkzl OR
       t706b2-atype <> atype OR
       NOT ( datum BETWEEN t706b2-begda
                   AND     t706b2-endda ).
      t706b2 = space.

* QKZK000728 Unicodeumstellung Beginn
*     PERFORM reise_ablehnung USING text-r85 *t706b2+3(56).
*     PERFORM reise_ablehnung USING text-r85 *t706b2(32).   "MAWK020779
      PERFORM reise_ablehnung USING text-r85                "MAWK020779
                                    *t706b2(32)             "MAWK020779
                                    space.                  "MAWK020779
*QKZK000728 Unicodeumstellung Ende
      PERFORM error_t706b2.
      CLEAR t706b2.

    ENDIF.
  ENDIF.

  endda = t706b2-endda.
  waers = t706b2-waers.
  begda = t706b2-begda.
  betrg = t706b2-betrg.

* PERFORM EXA706b2
* USING   ENDDA BEGDA WAERS BETrg.

ENDFORM.                                                    "re706b2

*---------------------------------------------------------------------*
*       FORM ERROR_T706B2                                             *
*---------------------------------------------------------------------*
FORM error_t706b2.
  t706b2 = *t706b2.
  PERFORM error_text USING 'V_T706B2'.
  CLEAR t706b2.
ENDFORM.                    "error_t706b2


*&--------------------------------------------------------------------*
*&      Form  xci_test
*&--------------------------------------------------------------------*
*       text
*---------------------------------------------------------------------*
*      -->DATUM      text
*      -->BETFA      text
*      -->BETKU      text
*---------------------------------------------------------------------*
FORM xci_test USING datum LIKE t706u-endda
                    betfa LIKE t706u-betfa
                    betku LIKE t706u-betku.

  DATA: hotl_max_naechte LIKE sy-tabix,
        naechte_pausch   LIKE sy-tabix,
        h_datb1          LIKE ptp02-datb1,
        h_uhrb1          LIKE ptp02-uhrb1,
        h_anuep          LIKE ptp42-anuep.

  LOOP AT exbel WHERE anzal > 0.
    READ TABLE beleg WITH KEY belnr = exbel-belnr.
    IF sy-subrc = 0 AND beleg-beart = 'U'.
      hotl_max_naechte = hotl_max_naechte + exbel-anzal.
    ENDIF.
  ENDLOOP.
  IF hotl_max_naechte > 0.
    IF datum < wa_head-datb1.
      h_datb1 = datum.
      h_uhrb1 = '240000'.
    ELSE.
      h_datb1 = wa_head-datb1.
      h_uhrb1 = wa_head-uhrb1.
    ENDIF.
    PERFORM get_nr_trip_overn_lumpsums
              USING
* XCIPSDETRG begin
                      wa_head-morei  wa_head-kzrea
                      wa_head-datv1  h_datb1
                      wa_head-uhrv1  h_uhrb1
                      h_anuep.
* XCIPSDETRG end


    IF h_anuep GE hotl_max_naechte.
      CLEAR betfa.
      CLEAR betku.
    ENDIF.
  ENDIF.

ENDFORM.                    "xci_test
*&---------------------------------------------------------------------*
*&      Form  RE706V_MIN
*&---------------------------------------------------------------------*
*       text
*----------------------------------------------------------------------*
*      -->P_WA_HEAD_MOREI  text
*      -->P_VPFPH  text
*      -->P_ARG_KZREA  text
*      -->P_ARG_KZTKT  text
*      -->P_ARG_LNDGR  text
*      -->P_ARG_RGION  text
*      -->P_ARG_BEREI  text
*      -->P_ARG_ERKLA  text
*      -->P_ARG_ERGRU  text
*      -->P_ANZTG  text
*      -->P_ANSTD  text
*      -->P_ANMIN  text
*      -->P_BEWERTUNGSTAG  text
*      -->P_T706V_ENDDA  text
*      -->P_T706V_BEGDA  text
*      -->P_WAERS  text
*      -->P_BETFZ  text
*      -->P_BETFA  text
*      -->P_BETKU  text
*----------------------------------------------------------------------*
FORM re706v_min  USING VALUE(morei) VALUE(kzpah) VALUE(kzrea) VALUE(kztkt)
      VALUE(lndgr) VALUE(rgion) VALUE(berei)
      VALUE(erkla) VALUE(ergru)
      VALUE(anzta) VALUE(anstd) VALUE(anmin) VALUE(datum)
      endda begda waers betfz betfa betku.

  PERFORM exb706v_min
    USING   morei kzpah kzrea kztkt
            lndgr rgion berei
            erkla ergru
            anzta anstd anmin datum.

  IF t706v-morei <> morei OR
     t706v-kzpah <> kzpah OR
     t706v-kzrea <> kzrea OR
     t706v-kztkt <> kztkt OR
     t706v-lndgr <> lndgr OR
     t706v-rgion <> rgion OR
     t706v-berei <> berei OR
     t706v-erkla <> erkla OR
     t706v-ergru <> ergru OR
     t706v-anzta <> anzta OR
     t706v-anstd <> anstd OR
     t706v-ptrv_anmin <> anmin OR
     NOT ( datum BETWEEN t706v-begda
                 AND     t706v-endda ).
    SELECT * FROM t706v UP TO 1 ROWS
                      WHERE morei =  morei AND
                            kzpah =  kzpah AND
                            kzrea =  kzrea AND
                            kztkt =  kztkt AND
                            lndgr =  lndgr AND
                            rgion =  rgion AND
                            berei =  berei AND
                            erkla =  erkla AND
                            ergru =  ergru AND
                            anzta >= anzta AND
                            anstd >= anstd AND
                            begda <= datum AND
                            endda >= datum
                            ORDER BY PRIMARY KEY.
    ENDSELECT.
    IF sy-subrc <> 0.
      *t706v = space.
      *t706v-morei = morei.
      *t706v-kzpah = kzpah.
      *t706v-kzrea = kzrea.
      *t706v-kztkt = kztkt.
      *t706v-lndgr = lndgr.
      *t706v-rgion = rgion.
      *t706v-berei = berei.
      *t706v-erkla = erkla.
      *t706v-ergru = ergru.
      *t706v-anzta = anzta.
      *t706v-anstd = anstd.
      *t706v-ptrv_anmin = anmin.
      *t706v-endda = datum.
      PERFORM reise_ablehnung USING text-r86
                                    *t706v(33)
                                    space.
      PERFORM error_t706v.
      CLEAR t706v.
    ENDIF.
    IF t706v-anstd = anstd.
      IF t706v-ptrv_anmin < anmin.
        anstd = anstd + 1.
        SELECT * FROM t706v UP TO 1 ROWS
                     WHERE morei =  morei AND
                           kzpah =  kzpah AND
                           kzrea =  kzrea AND
                           kztkt =  kztkt AND
                           lndgr =  lndgr AND
                           rgion =  rgion AND
                           berei =  berei AND
                           erkla =  erkla AND
                           ergru =  ergru AND
                           anzta >= anzta AND
                           anstd >= anstd AND
                           begda <= datum AND
                           endda >= datum
                           ORDER BY PRIMARY KEY.
        ENDSELECT.
        IF sy-subrc <> 0.
          *t706v = space.
          *t706v-morei = morei.
          *t706v-kzpah = kzpah.
          *t706v-kzrea = kzrea.
          *t706v-kztkt = kztkt.
          *t706v-lndgr = lndgr.
          *t706v-rgion = rgion.
          *t706v-berei = berei.
          *t706v-erkla = erkla.
          *t706v-ergru = ergru.
          *t706v-anzta = anzta.
          *t706v-anstd = anstd.
          *t706v-ptrv_anmin = anmin.
          *t706v-endda = datum.
          PERFORM reise_ablehnung USING text-r86
                                        *t706v(33)
                                        space.
          PERFORM error_t706v.
          CLEAR t706v.
        ENDIF.
      ENDIF.
    ENDIF.
  ENDIF.

  t706v-anzta = anzta.
  t706v-anstd = anstd.
  t706v-ptrv_anmin = anmin.

  endda = t706v-endda.
  waers = t706v-waers.
  begda = t706v-begda.
  betfz = t706v-betfz.
  betfa = t706v-betfa.
  betku = t706v-betku.

  PERFORM exa706v_min
          USING   endda begda waers betfz betfa betku.

ENDFORM.                    " RE706V_MIN