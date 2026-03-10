METHOD commentset_get_entityset.

  "--------------------------------------------------------------------
  " Déclaration des variables locales
  "--------------------------------------------------------------------
  DATA: lv_err_msg  TYPE string,
        lv_guid     TYPE string,                                " GUID reçu via les filtres OData
        lo_object   TYPE REF TO zcl_hr_fiori_offboarding_req,   " Référence vers la classe métier Offboarding
        lt_comments TYPE ztt_comments,                          " Table interne contenant les commentaires (retour métier)
        ls_comment  TYPE zstr_comments,                         " Structure de travail pour un commentaire
        ls_entity   TYPE zcl_zhrf_offboard_mpc=>ts_comment.     " Structure correspondant au modèle OData (Entity)

  DATA: ls_filter TYPE /iwbep/s_mgw_select_option,              " Filtre OData transmis par le client
        ls_selopt TYPE /iwbep/s_cod_select_option.              " Sélection individuelle extraite du filtre

  "--------------------------------------------------------------------
  " Nettoyage des paramètres de sortie avant traitement
  "--------------------------------------------------------------------
  CLEAR: et_entityset, es_response_context.

  "--------------------------------------------------------------------
  " Extraction du paramètre GUID à partir des filtres OData
  "--------------------------------------------------------------------
  " Récupération du GUID depuis les options de filtre
  LOOP AT it_filter_select_options INTO ls_filter WHERE property = 'Guid'.
    LOOP AT ls_filter-select_options INTO ls_selopt.
      lv_guid = ls_selopt-low. " Récupération de la valeur du filtre
      " Suppression des tirets
      REPLACE ALL OCCURRENCES OF '-' IN lv_guid WITH ''.
      EXIT.                    " Une seule valeur attendue
    ENDLOOP.

    IF lv_guid IS NOT INITIAL.
      EXIT.                    " GUID trouvé → sortie de la boucle
    ENDIF.
  ENDLOOP.

  " Vérification de la présence du GUID
  IF lv_guid IS INITIAL.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '101'
      INTO lv_err_msg.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid            = /iwbep/cx_mgw_busi_exception=>business_error
        message_unlimited = lv_err_msg
        http_status_code  = /iwbep/cx_mgw_busi_exception=>gcs_http_status_codes-bad_request.
  ENDIF.


  "--------------------------------------------------------------------
  " Bloc TRY...CATCH pour sécuriser les appels métier
  "--------------------------------------------------------------------
  TRY.
      " Instanciation de l’objet métier Offboarding
      lo_object = zcl_hr_fiori_offboarding_req=>get_instance( ).

      " Appel de la méthode métier pour récupérer la liste des commentaires
      lo_object->get_request_comments(
        EXPORTING
          iv_guid     = lv_guid
        IMPORTING
          et_comments = lt_comments
      ).

      "----------------------------------------------------------------
      " Transformation des données internes (lt_comments)
      " vers le format attendu par le modèle OData (et_entityset)
      "----------------------------------------------------------------
      LOOP AT lt_comments INTO ls_comment.
        CLEAR ls_entity.

        " Mapping champ par champ entre la structure interne et l’entité OData
        ls_entity-guid          = ls_comment-guid.
        ls_entity-upd_pernr     = ls_comment-upd_pernr.
        ls_entity-step_name     = ls_comment-step_name.
        ls_entity-upd_fname     = ls_comment-upd_fname.
        ls_entity-upd_lname     = ls_comment-upd_lname.
        ls_entity-date_approval = ls_comment-date_approval.
        ls_entity-comments      = ls_comment-comments.

        " Ajout de l’entité à la table de sortie exposée via OData
        APPEND ls_entity TO et_entityset.
      ENDLOOP.

      " Renseigner le nombre total d’éléments retournés (inlinecount OData)
      es_response_context-inlinecount = lines( et_entityset ).

      "----------------------------------------------------------------
      " Gestion des erreurs : transformation en exception OData générique
      " avec code HTTP 500 (Internal Server Error)
      "----------------------------------------------------------------
    CATCH cx_root INTO DATA(lx_error).
      RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
        EXPORTING
          textid            = /iwbep/cx_mgw_busi_exception=>business_error
          message_unlimited = lx_error->if_message~get_text( )
          http_status_code  = 500.
  ENDTRY.

ENDMETHOD.
