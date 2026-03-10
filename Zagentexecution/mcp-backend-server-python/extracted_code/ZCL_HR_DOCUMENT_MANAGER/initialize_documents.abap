METHOD initialize_documents.

  "--------------------------------------------------------
  " Déclaration d'une structure locale pour un document
  "--------------------------------------------------------
  DATA: ls_document TYPE zstr_document_entity.      " Structure interne représentant un document

  " Initialisation de la table de sortie pour éviter les doublons
  CLEAR rt_documents.                               " Nettoyer la table de retour

  "--------------------------------------------------------
  " Section 1 : Lettre de séparation
  "--------------------------------------------------------
  CLEAR ls_document.                                " Réinitialiser la structure avant usage
  ls_document-request_id    = iv_request_id.        " Associer l’ID de la requête
  ls_document-document_type = gc_document_types-separation_letter. " Type = Lettre de séparation
  ls_document-file_name     = text-001."'Separation Letter'.  " Nom lisible
*  ls_document-mime_type     = ''.                   " Vide par défaut
*  ls_document-content       = ''.                   " Pas de contenu encore chargé
  ls_document-file_num      = '1'.                  " Premier document de la liste

  " Statut selon existence du fichier
  ls_document-status = COND zde_status(             " Vérifie si déjà uploadé
    WHEN check_file_exists(
           iv_request_id = iv_request_id
           iv_type_doc   = gc_document_types-separation_letter ) = abap_true
    THEN gc_status-uploaded                         " Si existe → uploaded
    ELSE gc_status-not_uploaded ).                  " Sinon → not uploaded

  " Génération des URLs upload/download
  generate_document_urls(                           " Crée les liens d’upload et de download
    EXPORTING iv_request_id = iv_request_id
              iv_doc_type   = gc_document_types-separation_letter
    IMPORTING ev_upload_url   = ls_document-uploaded
              ev_download_url = ls_document-download ).

  " Ajout à la table de sortie
  APPEND ls_document TO rt_documents.               " Stocke dans la table de retour

  "--------------------------------------------------------
  " Section 2 : Document de rapatriement
  "--------------------------------------------------------
  CLEAR ls_document.                                " Réinitialiser la structure
  ls_document-request_id    = iv_request_id.        " Associer l’ID de la requête
  ls_document-document_type = gc_document_types-repatriation_travel. " Type = Document de rapatriement
  ls_document-file_name     = text-002."'Repatriation Travel'.  " Nom lisible
*  ls_document-mime_type     = ''.                   " Vide par défaut
*  ls_document-content       = ''.                   " Pas de contenu encore chargé
  ls_document-file_num      = '2'.                  " Deuxième document

  ls_document-status = COND zde_status(             " Vérifie si déjà uploadé
    WHEN check_file_exists(
           iv_request_id = iv_request_id
           iv_type_doc   = gc_document_types-repatriation_travel ) = abap_true
    THEN gc_status-uploaded
    ELSE gc_status-not_uploaded ).

  generate_document_urls(                           " Crée les liens d’upload et de download
    EXPORTING iv_request_id = iv_request_id
              iv_doc_type   = gc_document_types-repatriation_travel
    IMPORTING ev_upload_url   = ls_document-uploaded
              ev_download_url = ls_document-download ).

  APPEND ls_document TO rt_documents.               " Ajout du document dans la table

  "--------------------------------------------------------
  " Section 3 : Questionnaire de départ
  "--------------------------------------------------------
  CLEAR ls_document.                                " Réinitialiser la structure
  ls_document-request_id    = iv_request_id.        " Associer l’ID de la requête
  ls_document-document_type = gc_document_types-exit_questionnaire. " Type = Questionnaire de sortie
  ls_document-file_name     = text-003."'Exit Questionnaire'. " Nom lisible
*  ls_document-mime_type     = ''.                   " Vide par défaut
*  ls_document-content       = ''.                   " Pas de contenu encore chargé
  ls_document-file_num      = '3'.                  " Troisième document

  ls_document-status = COND zde_status(             " Vérifie si déjà uploadé
    WHEN check_file_exists(
           iv_request_id = iv_request_id
           iv_type_doc   = gc_document_types-exit_questionnaire ) = abap_true
    THEN gc_status-uploaded
    ELSE gc_status-not_uploaded ).

  generate_document_urls(                           " Crée les liens d’upload et de download
    EXPORTING iv_request_id = iv_request_id
              iv_doc_type   = gc_document_types-exit_questionnaire
    IMPORTING ev_upload_url   = ls_document-uploaded
              ev_download_url = ls_document-download ).

  APPEND ls_document TO rt_documents.               " Ajout du document dans la table

    "--------------------------------------------------------
  " Section 4 : Repatriation Shipment
  "--------------------------------------------------------
  CLEAR ls_document.                                " Réinitialiser la structure
  ls_document-request_id    = iv_request_id.        " Associer l’ID de la requête
  ls_document-document_type = gc_document_types-exit_questionnaire. " Type = Questionnaire de sortie
  ls_document-file_name     = text-004."'Repatriation Shipment'. " Nom lisible
*  ls_document-mime_type     = ''.                   " Vide par défaut
*  ls_document-content       = ''.                   " Pas de contenu encore chargé
  ls_document-file_num      = '4'.                  " Troisième document

  ls_document-status = COND zde_status(             " Vérifie si déjà uploadé
    WHEN check_file_exists(
           iv_request_id = iv_request_id
           iv_type_doc   = gc_document_types-repatriation_shipment ) = abap_true
    THEN gc_status-uploaded
    ELSE gc_status-not_uploaded ).

  generate_document_urls(                           " Crée les liens d’upload et de download
    EXPORTING iv_request_id = iv_request_id
              iv_doc_type   = gc_document_types-repatriation_shipment
    IMPORTING ev_upload_url   = ls_document-uploaded
              ev_download_url = ls_document-download ).

  APPEND ls_document TO rt_documents.               " Ajout du document dans la table

ENDMETHOD.
