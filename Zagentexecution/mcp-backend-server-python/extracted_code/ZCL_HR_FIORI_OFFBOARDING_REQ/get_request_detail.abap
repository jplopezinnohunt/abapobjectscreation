METHOD get_request_detail.

  "======================================================================
  " Méthode : GET_REQUEST_DETAIL
  "----------------------------------------------------------------------
  " Objectif :
  "   Récupérer le détail complet d’une requête employé à partir d’un GUID
  "   ou d’un numéro de personnel (PERNR).
  "
  " Description :
  "   - Si un GUID est fourni, il est utilisé directement.
  "   - Sinon, la méthode recherche la dernière requête créée pour le PERNR donné.
  "   - Récupère la requête correspondante avec le numéro de séquence le plus élevé.
  "   - Convertit les codes de domaine (REASON, ACTION_TYPE) en libellés texte.
  "   - Retourne la structure de détail et le message de statut.
  "
  " Paramètres :
  "   iv_pernr  - Numéro de personnel du créateur de la requête
  "   iv_guid   - Identifiant unique (GUID) de la requête
  "
  " Résultats :
  "   es_detail - Structure contenant le détail complet de la requête
  "   rs_return - Structure de retour (type, message)
  "======================================================================


  " Initialisation des structures de sortie
  CLEAR: es_detail, rs_return.

  " Vérification des paramètres d’entrée
  IF iv_pernr IS INITIAL AND iv_guid IS INITIAL.
    rs_return-type    = 'E'.
*    rs_return-message = 'The PERNR or GUID is empty'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '046'
      INTO rs_return-message.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " Déclaration des variables locales
  "------------------------------------------------------------
  DATA: lv_max_seqno   TYPE zv_hrfiori_req-seqno,
        lv_guid_to_use TYPE raw16,
        lv_reason      TYPE string,
        lv_acttype     TYPE string.

  "------------------------------------------------------------
  " Détermination du GUID à utiliser
  "------------------------------------------------------------
  IF iv_guid IS NOT INITIAL.
    " GUID fourni en entrée
    lv_guid_to_use = iv_guid.
  ELSE.
    " Recherche du GUID le plus récent pour le PERNR
    SELECT guid
      FROM zv_hrfiori_req
      INTO lv_guid_to_use
      WHERE creator_pernr = iv_pernr
      ORDER BY seqno DESCENDING.
    ENDSELECT.

    IF sy-subrc <> 0.
      rs_return-type    = 'E'.
*      rs_return-message = 'No queries found'.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '047'
        INTO rs_return-message.
      RETURN.
    ENDIF.
  ENDIF.

  "------------------------------------------------------------
  " Récupération du numéro de séquence maximum
  "------------------------------------------------------------
  SELECT MAX( seqno )
    FROM zv_hrfiori_req
    INTO lv_max_seqno
    WHERE guid = lv_guid_to_use.

  IF lv_max_seqno IS INITIAL.
    rs_return-type    = 'E'.
*    rs_return-message = 'No queries found'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '047'
        INTO rs_return-message.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " Lecture du détail de la requête
  "------------------------------------------------------------
  SELECT SINGLE *
    FROM zv_hrfiori_req
    INTO CORRESPONDING FIELDS OF es_detail
    WHERE guid = lv_guid_to_use
      AND seqno = lv_max_seqno ##WARN_OK.

  IF sy-subrc <> 0.
    rs_return-type    = 'E'.
*    rs_return-message = 'Unable to retrieve the request'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '048'
        INTO rs_return-message.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " Conversion du champ REASON (code → texte de domaine)
  "------------------------------------------------------------
  IF es_detail-reason IS NOT INITIAL.
    lv_reason = me->get_domain_value_text(
                  iv_domain_name  = 'ZD_HRFIORI_REASON'
                  iv_domain_value = CONV #( es_detail-reason )
                  iv_language     = sy-langu ).
    IF lv_reason IS NOT INITIAL.
      es_detail-reason = lv_reason.
    ENDIF.
  ENDIF.

  "------------------------------------------------------------
  " Conversion du champ ACTION_TYPE (code → texte de domaine)
  "------------------------------------------------------------
  IF es_detail-action_type IS NOT INITIAL.
    lv_acttype = me->get_domain_value_text(
                   iv_domain_name  = 'ZD_HRFIORI_ACTTYPE'
                   iv_domain_value = CONV #( es_detail-action_type )
                   iv_language     = sy-langu ).
    IF lv_acttype IS NOT INITIAL.
      es_detail-action_type = lv_acttype.
    ENDIF.
  ENDIF.

  "------------------------------------------------------------
  " Mise à jour de la structure de retour (succès)
  "------------------------------------------------------------
  rs_return-type    = 'S'.
*  rs_return-message = 'Detail successfully retrieved'.
  MESSAGE ID 'ZHRFIORI' TYPE 'S' NUMBER '049'
        INTO rs_return-message.

ENDMETHOD.
