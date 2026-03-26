*----------------------------------------------------------------------*
*   INCLUDE ZXFMCU14                                                   *
*----------------------------------------------------------------------*

* -------------------------------------------------------------------- *
*   Instauration dune limite dans le taux de dépassement du montant
*     de réservation de fonds.  Le 2/04/2003, ce taux a été fixé à :
*      2%   (  zone w_TauxMax )
*    Mais si ce taux une fois appliqué donne un montant supérieur au
*      plafond fixé à  500$  ( zone w_MontMax ), il est recalculé.
*
*
*  NB : La recommandation du test sur "sy-ucomm = 'DETA'" n'a pas été
*       suivie pour cause d'impact insuffisant sur le controle
*
* -------------------------------------------------------------------- *

* D_ANDROS ----------------------------------------------------------- *
*
* The code below should be implemented in "EXIT_SAPLFMFR_006"
* as it was in ver. 4.6
* -------------------------------------------------------------------- *

**  Montant maximum absolu de dépassement
*DATA : w_MontMax LIKE KBLD-HWGES  VALUE 2000.
*
** Taux maximum de dépassement  ( si montant max non atteint )
*DATA : w_TauxMax LIKE KBLD-UEBTO  VALUE 2.
*
*DATA : w_HWGES LIKE KBLD-HWGES.
*
*DATA : w_UEBTO-err LIKE KBLD-UEBTO.
*DATA : TErr1(44) VALUE '% tolerance level not authorized. Maximum : '.
*
*Check sy-tcode = 'FMX1' OR sy-tcode = 'FMX2'.
*Check F_KBLD-BLART = '12'.
*Check NOT F_KBLD-HWGES IS INITIAL.
*
*IF F_KBLD-UEBTO IS INITIAL.
*    w_HWGES = ( F_KBLD-HWGES * w_TauxMax ) / 100.
*    IF w_HWGES > w_MontMax.
*        F_KBLD-UEBTO  =  ( w_MontMax  * 100 ) / F_KBLD-HWGES.
*      ELSE.
*        F_KBLD-UEBTO  =  w_TauxMax.
*    ENDIF.
*  ELSE.
*    w_HWGES = ( F_KBLD-HWGES * F_KBLD-UEBTO ) / 100.
*    IF w_HWGES > w_MontMax OR F_KBLD-UEBTO > w_TauxMax.
*      w_UEBTO-err = F_KBLD-UEBTO.
*      IF F_KBLD-UEBTO > w_TauxMax and sy-uname <> 'L_CHABEAU'.
*        F_KBLD-UEBTO = w_TauxMax.
*      ENDIF.
*      w_HWGES = ( F_KBLD-HWGES * F_KBLD-UEBTO ) / 100.
*      IF w_HWGES > w_MontMax.
*        F_KBLD-UEBTO = ( w_MontMax  * 100 ) / F_KBLD-HWGES.
*      ENDIF.
*      message w009(zfi) with w_UEBTO-err TErr1 F_KBLD-UEBTO.
*    ENDIF.
*ENDIF.