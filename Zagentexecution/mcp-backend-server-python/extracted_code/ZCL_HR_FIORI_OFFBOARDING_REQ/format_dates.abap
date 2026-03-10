METHOD format_dates.

  " --------------------------------------------------------------------
  " Formatage de la date effective
  " --------------------------------------------------------------------
  " Vérifie si la date effective est initiale, non conforme (longueur ≠ 8)
  " ou égale à '00000000'. Dans ces cas, on renvoie une chaîne vide.
  IF iv_effective_date IS INITIAL
     OR strlen( iv_effective_date ) <> 8
     OR iv_effective_date = '00000000'.
    ev_effective_date = ''.
  ELSE.
    " Conversion de la date au format AAAA-MM-JJ
    ev_effective_date = iv_effective_date(4) && '-' &&  " Année
                        iv_effective_date+4(2) && '-' && " Mois
                        iv_effective_date+6(2).          " Jour
  ENDIF.

  " --------------------------------------------------------------------
  " Formatage de la date de fin
  " --------------------------------------------------------------------
  " Vérifie si la date de fin est initiale, non conforme ou égale à '00000000'
  IF iv_endda IS INITIAL
     OR strlen( iv_endda ) <> 8
     OR iv_endda = '00000000'.
    ev_endda = ''.
  ELSE.
    " Conversion de la date au format AAAA-MM-JJ
    ev_endda = iv_endda(4) && '-' &&      " Année
               iv_endda+4(2) && '-' &&   " Mois
               iv_endda+6(2).            " Jour
  ENDIF.

  " --------------------------------------------------------------------
  " Indication de succès de l'opération
  " --------------------------------------------------------------------
  rv_success = abap_true.

ENDMETHOD.
