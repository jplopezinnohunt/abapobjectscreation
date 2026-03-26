**----------------------------------------------------------------------*
**   INCLUDE ZXFMCU09                                                   *
**----------------------------------------------------------------------*
*
** WARNING DOLLAR CONSTANT
** Warning
** Si type de fond est GEF
** si devise EURO
** Si transaction FMX1
** Si taux différent de taux constant
*if not ( f_kbld-geber is initial )
*and sy-tcode = 'FMX1'
*and f_kbld-waers eq 'EUR'
*  .
*
** Taux de conversion : /0.869
*  perform recherche_taux changing w_taux.
*
** Recherche du type de fonds : GEF 099
** FM area : Unesco UNES
** N° de fond de la ligne en cours
*  data w_area like fmfincode.
*
*  select * from FMFINCODE
*  into w_area
*  where fincode eq f_kbld-geber
*  and fikrs eq F_KBLD-FIKRS
*  and type like '0%'.
*    exit.
*  endselect.
*
** Si trouvé ==> le fond est un GEF
** ==> vérification du taux
*  if sy-subrc eq 0
*  and f_kbld-kursf ne w_taux.
** Message Dollar constant
*    message e000(zfi) with w_taux f_kbld-kursf.
*  endif.
*
*endif.

*data: w_xdate type d.
*
*if f_kbld-xblnr <> space.
*  w_xdate(4) = f_kbld-xblnr+6(4).
*  w_xdate+4(2) = f_kbld-xblnr+3(2).
*  w_xdate+6(2) = f_kbld-xblnr(2).
*
*  CALL FUNCTION 'DATE_CHECK_PLAUSIBILITY'
*    EXPORTING
*      DATE                            = w_xdate
*    EXCEPTIONS
*      PLAUSIBILITY_CHECK_FAILED       = 1
*      OTHERS                          = 2.
*
*  IF SY-SUBRC <> 0.
*    call screen con_dynnr_head (SAPLFMFR).
*    message e001(s5) with 'DD.MM.YYYY FMCU09'.
*  ENDIF.
*endif.