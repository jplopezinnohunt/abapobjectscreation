METHOD get_domain_value_text.

  " --------------------------------------------------------------------
  " Déclaration des variables locales
  " --------------------------------------------------------------------
  DATA: lt_dd07v TYPE TABLE OF dd07v,   " Table pour stocker les valeurs et textes du domaine
        ls_dd07v TYPE dd07v,           " Structure temporaire pour parcourir lt_dd07v
        lv_value TYPE string.          " Valeur normalisée du domaine

  " --------------------------------------------------------------------
  " Normalisation de la valeur passée en paramètre
  " --------------------------------------------------------------------
  " Supprime les espaces et convertit en majuscules pour correspondance exacte
  lv_value = iv_domain_value.
  CONDENSE lv_value NO-GAPS.
  lv_value = to_upper( lv_value ).

  " --------------------------------------------------------------------
  " 1️Tentative via la fonction standard DD_DOMVALUES_GET
  " --------------------------------------------------------------------
  " Récupère les valeurs et libellés du domaine dans la langue système
  CALL FUNCTION 'DD_DOMVALUES_GET'
    EXPORTING
      domname = iv_domain_name
      text    = 'X'          " Récupérer les textes
      langu   = sy-langu
    TABLES
      dd07v_tab = lt_dd07v
    EXCEPTIONS
      others = 1.

  " Si la fonction retourne des valeurs, rechercher la correspondance exacte
  IF sy-subrc = 0 AND lt_dd07v IS NOT INITIAL.
    LOOP AT lt_dd07v INTO ls_dd07v WHERE domvalue_l = lv_value.
      rv_text = ls_dd07v-ddtext. " Libellé correspondant à la valeur
      RETURN.                     " Sortir immédiatement si trouvé
    ENDLOOP.
  ENDIF.

  " --------------------------------------------------------------------
  " 2️Recherche directe dans DD07T pour la version active
  " --------------------------------------------------------------------
  SELECT SINGLE ddtext
    FROM dd07t
    INTO rv_text
    WHERE domname   = iv_domain_name
      AND domvalue_l = lv_value
      AND ddlanguage = sy-langu
      AND as4local   = 'A' ##WARN_OK.        " Version active uniquement

  " --------------------------------------------------------------------
  " 3️Recherche sans restriction de version si toujours vide
  " --------------------------------------------------------------------
  IF rv_text IS INITIAL.
    SELECT SINGLE ddtext
      FROM dd07t
      INTO rv_text
      WHERE domname   = iv_domain_name
        AND domvalue_l = lv_value
        AND ddlanguage = sy-langu ##WARN_OK.
  ENDIF.

  " --------------------------------------------------------------------
  " 4️Fallback : si aucune correspondance trouvée
  " --------------------------------------------------------------------
  " On retourne la valeur brute du domaine comme libellé
  IF rv_text IS INITIAL.
    CONCATENATE text-026 iv_domain_value
      INTO rv_text.
  ENDIF.

ENDMETHOD.
