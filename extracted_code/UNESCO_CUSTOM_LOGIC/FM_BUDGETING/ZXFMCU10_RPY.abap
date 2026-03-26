**----------------------------------------------------------------------*
**   INCLUDE ZXFMCU10                                                   *
**----------------------------------------------------------------------*
*
** WARNING DOLLAR CONSTANT
** Erreur
** Si devise EURO
** Si 1 type de fond est GEF
** Si 1 autre est <> de GEF
** Si transaction FMX1
*if sy-tcode = 'FMX1' or sy-tcode = 'FMX2'.
*
** Init controle des BA
*  clear : w_gef,
*          w_autres.
*
** Recherche des types de fonds
****  loop at t_kbld.
*  loop at t_kbld where bukrs = 'UNES'.
*
** Si devise EUR
*    if t_kbld-waers eq 'EUR'.
*
** Recherche du type de fonds : GEF 099
** FM area : Unesco UNES
** N° de fond de la ligne en cours
*      data w_area like fmfincode.
*
****      select * from FMFINCODE
****      into w_area
****      where fincode eq t_kbld-geber
****      and fikrs eq 'UNES'
****      and type like '0%'.
****        exit.
****      endselect.
*      select single * from FMFINCODE into w_area
*                      where fikrs = t_kbld-fikrs
*                        and fincode = t_kbld-geber
*                        and type = '0%'.
*
** Si trouvé ==> le fond est un GEF
*      if sy-subrc eq 0.
*        move 'X' to w_gef.
*      else.
*        move 'X' to w_autres.
*      endif.
*
*    endif.
*
*  endloop.
*
** Test si GEF en EUR et autres
*  if w_autres eq 'X' and w_gef eq 'X'.
** Message erreur Dollar constant
*    message e002(zfi).
*  endif.
*
*
*endif.
*

DATA: W_XDATE TYPE D,
      W_KBLD TYPE KBLD.

IF SY-TCODE = 'FMX1' OR SY-TCODE = 'FMX2'.

CLEAR W_KBLD.
LOOP AT T_KBLD INTO W_KBLD.
  IF W_KBLD-XBLNR+2(1) <> '.' OR
     W_KBLD-XBLNR+5(1) <> '.'.
    MESSAGE E001(S5) WITH 'DD.MM.YYYY for Reference field in Header data'.
  ENDIF. "check for dots

  W_XDATE(4) = W_KBLD-XBLNR+6(4).
  W_XDATE+4(2) = W_KBLD-XBLNR+3(2).
  W_XDATE+6(2) = W_KBLD-XBLNR(2).

  CALL FUNCTION 'DATE_CHECK_PLAUSIBILITY'
    EXPORTING
      DATE                            = W_XDATE
    EXCEPTIONS
      PLAUSIBILITY_CHECK_FAILED       = 1
      OTHERS                          = 2.

  IF SY-SUBRC <> 0.
    MESSAGE E001(S5) WITH 'DD.MM.YYYY for Reference field in Header data'.
  ENDIF.
ENDLOOP. "t_kbld

ENDIF. "sy-tcode