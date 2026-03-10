METHOD get_employee_data.

  " Initialiser la structure de retour
  CLEAR rs_return.                  " Structure de retour pour type/message
  CLEAR: ev_nachn, ev_vorna.       " Initialiser nom et prénom

  " Déclaration des variables locales pour l’infotype 0002
  DATA: lt_p0002 TYPE TABLE OF p0002,  " Table tampon pour les données personnelles
        ls_p0002 TYPE p0002.          " Ligne de travail

  " Lecture de l’infotype 0002 (données personnelles) via fonction standard HR_READ_INFOTYPE
  CALL FUNCTION 'HR_READ_INFOTYPE'
    EXPORTING
      pernr         = iv_persno        " Numéro de personnel fourni en entrée
      infty         = '0002'           " Infotype PA0002
      begda         = sy-datum          " Date début : aujourd’hui
      endda         = sy-datum          " Date fin : aujourd’hui
    TABLES
      infty_tab     = lt_p0002          " Résultat : table locale
    EXCEPTIONS
      infty_not_found = 1               " Infotype non trouvé
      others          = 2.              " Autres erreurs

  " Vérification si des données ont été trouvées
  IF sy-subrc = 0 AND lt_p0002 IS NOT INITIAL.
    " Lire la première ligne du résultat
    READ TABLE lt_p0002 INTO ls_p0002 INDEX 1.
    IF sy-subrc = 0.
      ev_nachn = ls_p0002-nachn.  " Récupération du nom
      ev_vorna = ls_p0002-vorna.  " Récupération du prénom

      " Remplir la structure de retour en cas de succès
      rs_return-type    = 'S'.
      rs_return-message = text-013. " Message standard : Employé trouvé
    ENDIF.
  ELSE.
    " Aucun résultat trouvé
    rs_return-type    = 'W'.
    rs_return-message = text-014.  " Message standard : Employé introuvable
  ENDIF.

ENDMETHOD.
