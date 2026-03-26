METHOD get_request_status.

  " Lecture en base du statut de la demande en fonction du GUID fourni
  SELECT SINGLE *
    FROM zthrfiori_reqsta           " Table Z contenant les statuts de requête
    INTO rt_request_status          " Résultat stocké dans la structure de sortie
    WHERE guid = iv_guid.           " Filtre sur l'identifiant unique de la requête

  " Vérification du résultat de la sélection
  IF sy-subrc <> 0.
    CLEAR rt_request_status.        " Par sécurité, vider la structure de sortie
  ENDIF.

ENDMETHOD.
