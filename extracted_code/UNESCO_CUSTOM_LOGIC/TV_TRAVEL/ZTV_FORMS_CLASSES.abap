*&---------------------------------------------------------------------*
*& Report  ZTV_FORMS_CLASSES                                           *
*&                                                                     *
*&---------------------------------------------------------------------*
*&                                                                     *
*&                                                                     *
*&---------------------------------------------------------------------*

REPORT  ZTV_FORMS_CLASSES                                           .

*---------------------------------------------------------------------*
*       FORM REISE_UEBERSCHNEIDUNG                                    *
*---------------------------------------------------------------------*
*       Test Ueberschneidung zweier Intervalle:                       *
*       Reise1: (reise1_datv,reise1_uhrv), (reise1_datb,reise1_uhrb)  *
*       Reise2: (reise2_datv,reise2_uhrv), (reise2_datb,reise2_uhrb)  *
*       check_ueb = 'X', falls Test erfolgreich                       *
*       check_ueb = ' ', sonst                                        *
*---------------------------------------------------------------------*
FORM reise_ueberschneidung
USING reise1_datv reise1_uhrv
      reise1_datb reise1_uhrb
      reise2_datv reise2_uhrv
      reise2_datb reise2_uhrb check_ueb.

  IF ( reise1_datv = reise2_datb AND reise1_uhrv = reise2_uhrb ) OR
     ( reise2_datv = reise1_datb AND reise2_uhrv = reise1_uhrb ).
    check_ueb = ' '.
  ELSE.
    PERFORM check_datum_in_intervall
    USING reise1_datv reise1_uhrv
          reise2_datv reise2_uhrv
          reise2_datb reise2_uhrb check_ueb.
    IF check_ueb = ' '.
      PERFORM check_datum_in_intervall
        USING reise1_datb reise1_uhrb
              reise2_datv reise2_uhrv
              reise2_datb reise2_uhrb check_ueb.
    ENDIF.
    IF check_ueb = ' '.
      PERFORM check_datum_in_intervall
        USING reise2_datv reise2_uhrv
              reise1_datv reise1_uhrv
              reise1_datb reise1_uhrb check_ueb.
    ENDIF.
    IF check_ueb = ' '.
      PERFORM check_datum_in_intervall
        USING reise2_datb reise2_uhrb
              reise1_datv reise1_uhrv
              reise1_datb reise1_uhrb check_ueb.
    ENDIF.
  ENDIF.
ENDFORM.                    "reise_ueberschneidung


*---------------------------------------------------------------------*
*       FORM CHECK_DATUM_IN_INTERVALL                                 *
*---------------------------------------------------------------------*
*       Test (von,uhrv)<=(dat,uhrd)<=(bis,uhrb)                       *
*       check_res = 'X', falls Test erfolgreich                       *
*       check_res = ' ', sonst                                        *
*---------------------------------------------------------------------*
FORM check_datum_in_intervall
USING check_dat check_uhrd
      check_von check_uhrv
      check_bis check_uhrb check_res.
  PERFORM vergl_datum
  USING check_von check_uhrv
        check_dat check_uhrd check_res.
  IF check_res = 'X'.
    PERFORM vergl_datum
    USING check_dat check_uhrd
          check_bis check_uhrb check_res.
  ENDIF.
ENDFORM.                    "check_datum_in_intervall

*---------------------------------------------------------------------*
*       FORM VERGL_DATUM                                              *
*---------------------------------------------------------------------*
*       Test (dat1,uhr1) <= (dat2,uhr2)                               *
*       vergl_res = 'X', falls erfolgreich,                           *
*       vergl_res = ' ', falls nicht.                                 *
*---------------------------------------------------------------------*
FORM vergl_datum
USING vergl_dat1 vergl_uhr1
      vergl_dat2 vergl_uhr2 vergl_res.
  vergl_res = ' '.
  IF vergl_dat1 = vergl_dat2.
    IF vergl_uhr1 <= vergl_uhr2.                          "#EC PORTABLE
      vergl_res = 'X'.
    ENDIF.
  ELSE.
    IF vergl_dat1 < vergl_dat2.                           "#EC PORTABLE
      vergl_res = 'X'.
    ENDIF.
  ENDIF.
ENDFORM.                    "vergl_datum
