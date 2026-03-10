METHOD generate_guid.

  "----------------------------------------------------------------------
  " Génération d’un identifiant unique (GUID)
  "----------------------------------------------------------------------
  " Cette méthode génère un identifiant unique global (GUID) au format RAW 16
  " à l’aide de la fonction standard SAP 'GUID_CREATE'.
  " En cas d’échec de la génération, un message d’erreur est retourné.
  "----------------------------------------------------------------------

  " Déclaration de la variable locale pour stocker le GUID généré
  DATA: lv_guid TYPE sysuuid_x.
  TRY.
      CALL METHOD cl_system_uuid=>create_uuid_x16_static
        RECEIVING
          uuid = lv_guid.
    CATCH cx_uuid_error ##NO_HANDLER.
*      RAISE EXCEPTION TYPE cx_os_internal_error.
  ENDTRY.

  " Vérification du résultat de la génération du GUID
  IF lv_guid IS INITIAL.

    " Mise à jour de la structure de retour avec une erreur si la génération a échoué
    es_return-type    = 'E'.
    es_return-message = TEXT-009. " Message : Échec de la génération du GUID

    RETURN.
  ENDIF.

  " Affectation du GUID généré au paramètre de retour
  rv_guid = lv_guid.

  " Mise à jour de la structure de retour avec un message de succès
  es_return-type    = 'S'.
  es_return-message = TEXT-010. " Message : GUID généré avec succès

ENDMETHOD.
