METHOD create_request.

  "======================================================================
  " Méthode : CREATE_REQUEST
  "----------------------------------------------------------------------
  " Objectif :
  "   Créer une nouvelle demande d'offboarding pour un employé.
  "   - Génère un GUID unique pour la demande
  "   - Récupère les informations de l'employé et de l'updater
  "   - Vérifie l'unicité de la demande
  "   - Insère la demande principale, le statut initial et l'approbation initiale
  "   - Log technique via BAL
  "
  " Paramètres :
  "   iv_pernr        - Numéro de personnel de l'employé
  "   iv_updater      - Numéro de personnel de l'updater
  "   iv_action_type  - Type d'action de la demande
  "   iv_reason       - Raison de la demande
  "   iv_endda        - Date de fin (optionnelle)
  "   iv_effective_date - Date effective
  "
  " Résultats :
  "   es_return       - Structure retour (type, message)
  "   rv_success      - Indicateur succès ('X') ou échec ('-')
  "======================================================================

  "------------------------------------------------------------
  " VARIABLES LOCALES
  "------------------------------------------------------------
  DATA: lv_guid            TYPE ze_hrfiori_guidreq,    " GUID généré automatiquement pour la demande
        lv_lname           TYPE pad_nachn,             " Nom de famille de l'employé
        lv_fname           TYPE pad_vorna,             " Prénom de l'employé
        ls_employee_return TYPE bapiret2,              " Structure retour pour employé
        ls_updater_return  TYPE bapiret2,              " Structure retour pour updater
        lv_existing_guid   TYPE ze_hrfiori_guidreq,    " GUID d'une demande existante éventuelle
        lv_upd_lname       TYPE pad_nachn,             " Nom de l'updater
        lv_upd_fname       TYPE pad_vorna,             " Prénom de l'updater
        lv_validation_type TYPE ze_hrfiori_valtype,    " Type de validation
        lv_exec_mode       TYPE ze_hrfiori_execmode,   " Mode d'exécution
        ls_status          TYPE zthrfiori_reqsta ##NEEDED.      " Structure statut

  "------------------------------------------------------------
  " ÉTAPE 1 : GÉNÉRATION DU GUID
  "------------------------------------------------------------
  lv_guid = me->generate_guid(
    IMPORTING es_return = es_return ).                 " Récupération message retour
  IF es_return-type = 'E'.                             " Vérifier si génération échoue
    rv_success = '-'.
    RETURN.
  ENDIF.

  ev_guid = lv_guid.

  "------------------------------------------------------------
  " ÉTAPE 2 : RÉCUPÉRER LES DONNÉES DE L'EMPLOYÉ
  "------------------------------------------------------------
  ls_employee_return = me->get_employee_data(
    EXPORTING iv_persno = iv_pernr
    IMPORTING ev_nachn = lv_lname
              ev_vorna = lv_fname ).
  IF ls_employee_return-type = 'E'.
    es_return = ls_employee_return.
    rv_success = '-'.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " ÉTAPE 2B : RÉCUPÉRER LES DONNÉES DE L'UPDATER
  "------------------------------------------------------------
  ls_updater_return = me->get_employee_data(
    EXPORTING iv_persno = iv_updater
    IMPORTING ev_nachn  = lv_upd_lname
              ev_vorna  = lv_upd_fname ).
  IF ls_updater_return-type = 'E'.
    es_return = ls_updater_return.
    rv_success = '-'.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " ÉTAPE 3 : VÉRIFIER L'UNICITÉ DE LA DEMANDE
  "------------------------------------------------------------
  SELECT SINGLE guid
    FROM zv_hrfiori_req
    INTO lv_existing_guid
    WHERE creator_pernr = iv_pernr
      AND action_type   = iv_action_type
      AND reason        = iv_reason
      AND closed <> 'X' ##WARN_OK
      AND cancelled <> 'X'.
  IF sy-subrc = 0.
    es_return-type    = 'E'.
    es_return-id      = 'ZHR_OFFBOARDING'.
    es_return-number  = '000'.
    es_return-message_v1 = iv_pernr.
    es_return-message_v2 = iv_action_type.
    es_return-message_v3 = iv_effective_date.
    rv_success = '-'.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " ÉTAPE 3B : INITIALISER LE STATUT POUR REQUEST_INIT
  "------------------------------------------------------------
  " Pour la création, on initialise toujours avec REQUEST_INIT
  CLEAR ls_status.
  ls_status-request_init = 'X'.
  lv_validation_type = '01'.
  lv_exec_mode = '01'.

  "------------------------------------------------------------
  " ÉTAPE 4 : INSÉRER LA DEMANDE PRINCIPALE
  "------------------------------------------------------------
  DATA(ls_hreq) = VALUE zthrfiori_hreq(
      mandt          = sy-mandt
      guid           = lv_guid
      reason         = iv_reason
      creator_pernr  = iv_pernr
      creator_lname  = lv_lname
      creator_fname  = lv_fname
      action_type    = iv_action_type
      endda          = iv_endda
      effective_date = iv_effective_date ).
  INSERT zthrfiori_hreq FROM ls_hreq.
  IF sy-subrc = 0.

    "------------------------------------------------------------
    " ÉTAPE 5 : INSÉRER STATUT INITIAL
    "------------------------------------------------------------
    DATA(ls_reqstat) = VALUE zthrfiori_reqsta(
      mandt        = sy-mandt
      guid         = lv_guid
      seqno        = '001'
      upd_pernr    = iv_updater
      upd_lname    = lv_upd_lname
      upd_fname    = lv_upd_fname
      request_init = 'X' ).
    INSERT zthrfiori_reqsta FROM ls_reqstat.

    IF sy-subrc = 0.

      "------------------------------------------------------------
      " ÉTAPE 6 : INSÉRER APPROBATION INITIALE
      "------------------------------------------------------------
*      MESSAGE ID 'ZHRFIORI' TYPE 'S' NUMBER '050'
*        INTO DATA(lv_coment). " ticket 1262
      DATA(ls_approval) = VALUE zthrfiori_dapprv(
        mandt           = sy-mandt
        guid            = lv_guid
        seqno           = '001'
        validation_type = lv_validation_type
        date_approval   = sy-datum
*        comments        = 'Request initialized automatically'
        comments        = '' "lv_coment " ticket 1262
        uname           = sy-uname
        exec_mode       = lv_exec_mode ).
      INSERT zthrfiori_dapprv FROM ls_approval.

      IF sy-subrc = 0.
        COMMIT WORK AND WAIT.                        " Valider transaction complète
        es_return-type       = 'S'.
        es_return-id         = 'ZHR_OFFBOARDING'.
        es_return-number     = '001'.
        es_return-message_v1 = iv_pernr.
        es_return-message_v2 = lv_lname.
        es_return-message_v3 = lv_fname.
        es_return-message_v4 = iv_action_type.
        rv_success = 'X'.

      ELSE.
        ROLLBACK WORK.
        es_return-type    = 'E'.
        es_return-id      = 'ZHR_OFFBOARDING'.
        es_return-number  = '002'.
        es_return-system  = sy-sysid.
        rv_success = '-'.
      ENDIF.

    ELSE.
      ROLLBACK WORK.
      es_return-type    = 'E'.
      es_return-id      = 'ZHR_OFFBOARDING'.
      es_return-number  = '003'.
      es_return-system  = sy-sysid.
      rv_success = '-'.
    ENDIF.

  ELSE.
    es_return-type    = 'E'.
    es_return-id      = 'ZHR_OFFBOARDING'.
    es_return-number  = '004'.
    es_return-system  = sy-sysid.
    rv_success = '-'.
  ENDIF.

  "------------------------------------------------------------
  " ÉTAPE 7 : LOG TECHNIQUE BAL
  "------------------------------------------------------------
  DATA(ls_msg) = VALUE bal_s_msg(
    msgty = es_return-type
    msgid = es_return-id
    msgno = es_return-number
    msgv1 = es_return-message_v1
    msgv2 = es_return-message_v2
    msgv3 = es_return-message_v3
    msgv4 = es_return-message_v4 ).
  CALL FUNCTION 'BAL_LOG_MSG_ADD'
    EXPORTING
      i_s_msg = ls_msg
    EXCEPTIONS
      OTHERS  = 0.

ENDMETHOD.
