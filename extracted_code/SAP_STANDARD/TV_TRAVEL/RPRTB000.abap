* 6.04
* VJMK1286257 12/08 TRG: geänderte Versteuerung
* KCNEH4K014429 11072008 AT: Konstante REIES und Altreisen vor dem
*                        Jahr 2008                      [note  1230195]
* 6.0
* note  1000239 16112006
* KCNP7HK007073 05052006 NO: Konstante MAXBR nicht mehr gültig
*                        [note 942758]
* VJMK902193 11-2005 Sonderregel Essensbon P.S. (n. 902193)
* VJMKPSABZ01 Abzug NRW (Note: 828721 T: K005313)
* 5.0
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
*{   INSERT         KI4K055620                                        1
* KI4
* 4.6B
* XCIKI4PSCO_CONST Korrektur Konstantenlesen
* KI4/4.5B
* XCIKI4PSOV02  06/99  Leseroutine der Konstanten erweitert/korrigiert
*
*}   INSERT

*---------------------------------------------------------------------*
*    Hilfsprogramme zum Tabellenlesen (ATAB)                          *
*    und                                                              *
*    Ablehnungsroutinen                                               *
*---------------------------------------------------------------------*

*---------------------------------------------------------------------*
*       FORM RE001                                                    *
*---------------------------------------------------------------------*
FORM  re001
USING value(bukrs)
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
USING value(werks) value(btrtl).
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
USING value(morei) value(inaus) value(abzkz)
      value(kzrea) value(kztkt)
      value(erkla) value(ergru) value(datum)
      endda begda kzspa abzpz kzfpa abzfa waerspz waersfa.

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
      PERFORM reise_ablehnung USING text-r70 *t706a(20).
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

ENDFORM.                                                    "re706a

*---------------------------------------------------------------------*
*       FORM RE706B1                                                  *
*---------------------------------------------------------------------*
FORM  re706b1
USING value(morei)
      value(spkzl)
      value(datum)
      endda begda
      mwskz beart
      paush nbkkl
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

      PERFORM reise_ablehnung USING text-r71 *t706b1+3(14).
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
USING value(morei) TYPE t706b4-morei
      value(spkzl) TYPE t706b4-spkzl
      value(payot) TYPE t706b4-payot
      value(datum) TYPE ptk21-datum
      value(paush) TYPE t706b1-paush
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
                 AND     t706b4-endda ).

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
      PERFORM reise_ablehnung USING text-r72 *t706b4+3(16).
      PERFORM error_t706b4 USING paush.
      CLEAR t706b4.
    ENDIF.
  ENDIF.

  endda = t706b4-endda.
  begda = t706b4-begda.
  lgarl = t706b4-lgarl.
  lgarh = t706b4-lgarh.
  lgarp = t706b4-lgarp.

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
USING value(morei)
      value(regel_kz)
      value(limit)
      value(spkzl)
      value(payot)
      value(datum)
      value(paush)
      endda begda
      lgarl lgarh
      lgarp.

  PERFORM exb706b4_altern
  USING   morei regel_kz spkzl
          payot datum.

  IF t706b4_altern-morei <> morei OR
     t706b4_altern-regel_kz <> regel_kz OR
     t706b4_altern-limit <> limit OR
     t706b4_altern-spkzl <> spkzl OR
     t706b4-payot <> payot OR
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
      PERFORM reise_ablehnung USING text-r93 *t706b4_altern+3(16).
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

ENDFORM.                    "re706b4_altern

* XCIPSDETRG end

*---------------------------------------------------------------------*
*       FORM RE706D                                                   *
*---------------------------------------------------------------------*
FORM re706d
USING value(morei)
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
USING value(morei) value(kzrea) value(kztkt)
      value(land1) value(rgion) value(berei)
      value(kzpmf) value(kznza)
      value(pkwkl) value(pekez) value(kmgre) value(datum)
      endda begda waers betfz betfa betku.

* Prepare key for reading T706F according to customizing:
  IF cumulation_period_type NE '1'.
    CLEAR pekez.
  ENDIF.
  IF cumulation_active NE '1'.
    CLEAR kmgre.
  ENDIF.

  PERFORM re706f_trvct USING  t702n-f08                     "WNZK050579
                              t702n-f09                     "WNZK050579
                              t702n-f11                     "WNZK050579
                              t001_land1                    "WNZK050579
                    CHANGING  kzrea                         "WNZK050579
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
       NOT ( datum BETWEEN t706f-begda
                       AND t706f-endda ).

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
*        PERFORM reise_ablehnung USING text-r75 *t706f+3(64).
        PERFORM reise_ablehnung USING text-r75 *t706f(36).
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
       NOT ( datum BETWEEN t706f-begda
                       AND t706f-endda ).
*        Lesen notwendig
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
*        PERFORM reise_ablehnung USING text-r75 *t706f+3(64).
        PERFORM reise_ablehnung USING text-r75 *t706f(36).
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

ENDFORM.                                                    "re706f

*---------------------------------------------------------------------*
*       FORM RE706H                                                   *
*---------------------------------------------------------------------*
FORM re706h
USING value(morei) value(kzpah) value(kzrea) value(kztkt)
      value(lndgr) value(rgion) value(berei)
      value(erkla) value(ergru)
      value(anzta) value(beguz) value(enduz) value(datum)
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
USING value(morei) value(land1) value(rgion)
      value(datum)
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
USING value(morei) value(land1) value(rgion)
      value(datum)
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
USING value(morei) value(pekez) value(datum)
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

      PERFORM reise_ablehnung USING text-r80 *t706p+3(55).
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
USING value(morei) value(schem)
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

      PERFORM reise_ablehnung USING text-r83 *t706s+3(22).
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
USING value(morei) value(kzpah) value(kzrea) value(kztkt)
      value(lndgr) value(rgion) value(berei)
      value(erkla) value(ergru)
      value(datum)
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
*      PERFORM reise_ablehnung USING text-r85 *t706u+3(56).
      PERFORM reise_ablehnung USING text-r85 *t706u(28).
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
USING value(morei) value(kzpah) value(kzrea) value(kztkt)
      value(lndgr) value(rgion) value(berei)
      value(erkla) value(ergru)
      value(anzta) value(anstd) value(datum)
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
*{   INSERT         KI4K039449                                        1
      IF pubsec_germany = true AND                          "QKZKORRVBELEG
         kzpah = 'H'.                                       "QKZKORRVBELEG
        t706v-betfz = 9999999.                              "QKZKORRVBELEG
        t706v-betfa = 9999999.                              "QKZKORRVBELEG
        t706v-betku = 9999999.                              "QKZKORRVBELEG
      ELSE.                                                 "QKZKORRVBELEG
*}   INSERT
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
*      PERFORM REISE_ABLEHNUNG USING TEXT-R86 *T706V+3(61).
        PERFORM reise_ablehnung USING text-r86 *t706v(33).
* QKZK000728 Unicodeumstellung Ende
        PERFORM error_t706v.
        CLEAR t706v.
*{   INSERT         KI4K039449                                        2
      ENDIF.                                             "QKZKORRVBELEG
*}   INSERT
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
  IF pubsec_germany = true
  AND ( trg_tr = true OR trg_av = true ).
    erstform = 'T'.
    PERFORM tg_set_stfr USING datum
                              erstform
                              betfz
                              t706v-waers
                              st_mod1
*                             st_mod2.                  "VJMK1286257
                              st_mod2                   "VJMK1286257
                              kzrea.                    "VJMK1286257
  ENDIF.
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
USING value(gdatu) value(fcurr) value(tcurr).
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

    PERFORM reise_ablehnung USING text-r89 fcurr.
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
                           argument.

  DATA: e_type   LIKE sy-msgty,
        e_id     LIKE sy-msgid,
        e_no     LIKE sy-msgno,
        e_v1     LIKE sy-msgv1,
        e_v2     LIKE sy-msgv2,
        e_v3     LIKE sy-msgv3,
        e_v4     LIKE sy-msgv4.
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
        e_type = 'E'.
        e_id = '56'.
        e_no = 16.
        MOVE text TO e_v1.
        MOVE argument TO e_v2.
        CLEAR: e_v3, e_v4.
        EXPORT e_type e_id e_no e_v1 e_v2 e_v3 e_v4
               TO MEMORY ID 'TECERROR'.
      ELSE.
        SKIP.
        WRITE: / text-e01, wa_perio-reinr,
                 text-e02, pernr-pernr,
                 text-e03.
      ENDIF.
    ELSE.
* Abrechnung / Simulation mit PF-Taste
*     FREE MEMORY ID 'TS'.                                  "QIZK049366
*     FREE MEMORY ID 'TE'.                                  "QIZK049366
      FREE MEMORY ID te-key.                                "QIZK049366
      MESSAGE i016 WITH text argument.
* QIZK003787 used also for online simulation... begin
      e_type = 'E'.
      e_id = '56'.
      e_no = 16.
      MOVE text TO e_v1.
      MOVE argument TO e_v2.
      CLEAR: e_v3, e_v4.
      EXPORT e_type e_id e_no e_v1 e_v2 e_v3 e_v4
             TO MEMORY ID 'TECERROR'.
* QIZK003787 used also for online simulation... end
    ENDIF.
  ELSE.
    SKIP.
  ENDIF.
  DETAIL.
  rei_ablehn = 1.
  f = 1.
ENDFORM.                               "END OF REISE_ABLEHNUNG

*---------------------------------------------------------------------*
*       FORM ABLEHNUNG                                                *
*---------------------------------------------------------------------*
FORM ablehnung.

  DATA: e_type   LIKE sy-msgty,                             "QIZK000041
        e_id     LIKE sy-msgid,                             "QIZK000041
        e_no     LIKE sy-msgno,                             "QIZK000041
        e_v1     LIKE sy-msgv1,                             "QIZK000041
        e_v2     LIKE sy-msgv2,                             "QIZK000041
        e_v3     LIKE sy-msgv3,                             "QIZK000041
        e_v4     LIKE sy-msgv4,                             "QIZK000041
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

  ULINE.
  FORMAT COLOR 1 INTENSIFIED OFF.
  WRITE: / sy-vline NO-GAP,
          'Gesperrte Personalnummer'(e09),
           pernr-pernr,
           79 sy-vline.
  ULINE.
  FORMAT RESET.
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
  name = text-050.

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

  DETAIL.
  ULINE.
  WRITE: / 'Kein Eintrag in'(vi1), viewname INTENSIFIED, 'für'(vi2).
  SUMMARY.
  WRITE: / 'Schlüssel'(vi3), 30 'Wert'(vi4).
  DETAIL.

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

    name+0(5) =  dd27p_tab-tabname.
    name+6(5) =  dd27p_tab-fieldname.
    ASSIGN TABLE FIELD (name) TO <f>.
    IF sy-subrc <> 0.
      ASSIGN (space) TO <f>.
    ENDIF.

    WRITE: / dd04t-scrtext_l(25) UNDER text-vi3,
             <f> INTENSIFIED     UNDER text-vi4.
  ENDLOOP.
  ULINE.
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
FORM error_t706b4 USING value(paush).
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
USING value(morei) value(konst) value(date)
*      endda begda kwert waers zeit datum.
      subrc                                                 "QKZK018282
      endda begda kwert waers zeit datum anzahl.            "QKZK018282

  CLEAR subrc.                                              "XOWK057099

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
*{   INSERT         KI4K047880                                        1
    subrc = sy-subrc.                                 "XCIKI4PSCO_CONST
*}   INSERT

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
      IF konst = 'USTR6'                                   "VJMKTGST03
      OR konst = 'USTR8'                                   "VJMKTGST03
      OR konst = 'USTR9'.                                  "VJMKTGST03
        kwert = t706_const-kwert = '0'.                    "VJMKTGST03
        endda = date.                                      "VJMKTGST03
        begda = date.                                      "VJMKTGST03
        EXIT.                                              "VJMKTGST03
      ENDIF.                                               "VJMKTGST03
      IF konst = 'UGVP '.                                 "VJMKPSABZ01
        anzahl = t706_const-anzahl = '0'.                 "VJMKPSABZ01
        endda = date.                                     "VJMKPSABZ01
        begda = date.                                     "VJMKPSABZ01
        EXIT.                                             "VJMKPSABZ01
      ENDIF.                                              "VJMKPSABZ01
      IF konst = 'ESSBO'.                                 "VJMK902193
        anzahl = t706_const-anzahl = '0'.                 "VJMK902193
        endda = date.                                     "VJMK902193
        begda = date.                                     "VJMK902193
        EXIT.                                             "VJMK902193
      ENDIF.                                              "VJMK902193
      if konst = 'MAXBR'.                                   "KCNK007073
        anzahl = t706_const-anzahl = '0'.                   "KCNK007073
        endda = date.                                       "KCNK007073
        begda = date.                                       "KCNK007073
        clear t706_const-konst.                             "note 1000239
        exit.                                               "KCNK007073
      endif.                                                "KCNK007073
      if konst = 'REIES'.                                   "KCNK014429
        anzahl = t706_const-anzahl = '0'.                   "KCNK014429
        endda = date.                                       "KCNK014429
        begda = date.                                       "KCNK014429
        exit.                                               "KCNK014429
      endif.                                                "KCNK014429
      t706_const = space.
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
USING value(morei) value(kzrea)
      value(berei) value(kztkt)
      value(lndgr) value(rgion)
      value(erkla) value(ergru)
      value(spkzl) value(atype)
      value(datum)
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
*      PERFORM reise_ablehnung USING text-r85 *t706b2+3(56).
      PERFORM reise_ablehnung USING text-r85 *t706b2(32).
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
        naechte_pausch LIKE sy-tabix,
        h_datb1 LIKE ptp02-datb1,
        h_uhrb1 LIKE ptp02-uhrb1,
        h_anuep LIKE ptp42-anuep.

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