*&---------------------------------------------------------------------*
*&  Include           ZXFMCU17                                         *
*&---------------------------------------------------------------------*

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

*  Montant maximum absolu de dépassement
DATA : W_MONTMAX LIKE KBLD-HWGES  VALUE 2000.

* Taux maximum de dépassement  ( si montant max non atteint )
DATA : W_TAUXMAX LIKE KBLD-UEBTO  VALUE 2.

DATA : W_HWGES LIKE KBLD-HWGES.

DATA : W_UEBTO-ERR LIKE KBLD-UEBTO.
DATA : TERR1(44) VALUE '% tolerance level not authorized. Maximum : '.

DATA: W_UNAME TYPE XUBNAME.


CHECK SY-TCODE = 'FMX1' OR SY-TCODE = 'FMX2'.
CHECK F_KBLD-BLART = '12'.
CHECK NOT F_KBLD-HWGES IS INITIAL.

IF F_KBLD-UEBTO IS INITIAL.
    W_HWGES = ( F_KBLD-HWGES * W_TAUXMAX ) / 100.
    IF W_HWGES > W_MONTMAX.
        F_KBLD-UEBTO  =  ( W_MONTMAX  * 100 ) / F_KBLD-HWGES.
      ELSE.
        F_KBLD-UEBTO  =  W_TAUXMAX.
    ENDIF.
  ELSE.
    W_HWGES = ( F_KBLD-HWGES * F_KBLD-UEBTO ) / 100.
    IF W_HWGES > W_MONTMAX OR F_KBLD-UEBTO > W_TAUXMAX.
      W_UEBTO-ERR = F_KBLD-UEBTO.
***I_KONAKOV 05/2024 - add other users on request from BFM
***      IF F_KBLD-UEBTO > w_TauxMax and sy-uname <> 'L_CHABEAU'.
      IF F_KBLD-UEBTO > W_TAUXMAX.
        SELECT SINGLE UNAME
              INTO W_UNAME
              FROM YXUSER
              WHERE XTYPE = 'FRTL'
                AND UNAME = SY-UNAME.
        IF SY-SUBRC <> 0.
***end of insert
         F_KBLD-UEBTO = W_TAUXMAX.
***I_KONAKOV 05/2024
        ENDIF. "sy-subrc
***end of insert
      ENDIF.
      W_HWGES = ( F_KBLD-HWGES * F_KBLD-UEBTO ) / 100.
      IF W_HWGES > W_MONTMAX.
        F_KBLD-UEBTO = ( W_MONTMAX  * 100 ) / F_KBLD-HWGES.
      ENDIF.
      MESSAGE W009(ZFI) WITH W_UEBTO-ERR TERR1 F_KBLD-UEBTO.
    ENDIF.
ENDIF.