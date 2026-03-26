**----------------------------------------------------------------------*
**   INCLUDE ZXFMCU12                                                   *
**----------------------------------------------------------------------*
*
** Calcul du taux /0.869
*perform recherche_taux changing w_taux.
*
** WARNING DOLLAR CONSTANT
** Warning :
** Si devise EURO
** Si transaction FMX1
** Si taux différent de taux constant
*if sy-tcode = 'FMX1'
*and f_kblk-waers eq 'EUR'
*and f_kblk-kursf ne w_taux.
*
** Message transaction en EUR, checker le taux
*  message w001(zfi) with w_taux f_kblk-kursf.
*
*endif.
*