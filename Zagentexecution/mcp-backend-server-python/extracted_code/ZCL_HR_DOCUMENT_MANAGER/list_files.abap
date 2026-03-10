METHOD list_files.

  "--------------------------------------------------------
  " 1. Déclaration des variables internes
  "--------------------------------------------------------
  DATA: lt_toahr    TYPE STANDARD TABLE OF toahr,       " Table interne pour stocker les enregistrements TOAHR
        ls_document TYPE zstr_document_entity,          " Structure document à retourner
        lv_doc_type TYPE zde_doctype,                   " Type de document (extrait de object_id)
        lv_pattern  TYPE string,                        " Motif de recherche pour LIKE
        lv_offset   TYPE i,                             " Position utilisée pour extraire le type
        lv_index    TYPE i,                             " Compteur d'itérations (numéro fichier)
        lv_content  TYPE xstring,                       " Contenu binaire du fichier
        lv_ext      TYPE string.                        " Extension de fichier

  DATA: ls_toaat TYPE toaat.                            " Structure pour lire infos TOAAT (nom, auteur, date...)

  CLEAR rt_files.                                       " Nettoyer la table de retour
  lv_index = 0.                                         " Initialiser compteur

  "--------------------------------------------------------
  " 2. Construire le motif pour LIKE : object_id commence par iv_request_id
  "--------------------------------------------------------
  DATA(lv_request_id_str) = |{ iv_request_id }|.        " Conversion explicite en string
  lv_pattern = lv_request_id_str && '%'.                " Exemple : 'REQ123%' pour récupérer tous les documents liés

  "--------------------------------------------------------
  " 3. Sélectionner tous les documents archivés liés à la demande
  "--------------------------------------------------------
  SELECT *                                              " Lecture des enregistrements d’archive
    FROM toahr
    INTO TABLE @lt_toahr
    WHERE object_id LIKE @lv_pattern                    " object_id commençant par la requête
      AND archiv_id  = @gc_archives-archive_id          " Archive spécifique
      AND sap_object = @gc_archives-sap_object.         " Objet SAP associé

  "--------------------------------------------------------
  " 4. Boucle sur chaque document trouvé
  "--------------------------------------------------------
  LOOP AT lt_toahr INTO DATA(ls_toahr).                 " Parcours de chaque ligne trouvée dans TOAHR

    CLEAR ls_document.
    lv_index = lv_index + 1.                            " Incrémenter numéro du fichier

    "------------------------------------------------------
    " 4a. Champs principaux
    "------------------------------------------------------
    ls_document-request_id = iv_request_id.             " Associer ID de la requête au document

    " Extraire le type de document depuis object_id
    lv_offset = strlen( lv_request_id_str ).             " Calculer longueur pour extraire type
    IF strlen( ls_toahr-object_id ) > lv_offset.
      lv_doc_type = ls_toahr-object_id+lv_offset.        " Extraire suffixe (ex: PDF_DOC)
    ELSE.
      lv_doc_type = 'UNKNOWN'.                           " Si extraction impossible
    ENDIF.
    ls_document-document_type = lv_doc_type.
    ls_document-file_num      = lv_index.

    "------------------------------------------------------
    " 4b. Récupérer le nom du fichier depuis TOAAT
    "------------------------------------------------------
    CLEAR ls_toaat.
    SELECT SINGLE filename, descr, creator, creatime
      FROM toaat
      INTO (@ls_toaat-filename, @ls_toaat-descr, @ls_toaat-creator, @ls_toaat-creatime)
      WHERE arc_doc_id = @ls_toahr-arc_doc_id.

    ls_document-file_name = ls_toaat-filename.

    "------------------------------------------------------
    " 4c. Déterminer le MIME_TYPE selon extension du fichier
    "------------------------------------------------------
    IF ls_document-file_name CS '.'.
      SPLIT ls_document-file_name AT '.' INTO DATA(lv_name) lv_ext ##NEEDED.
      lv_ext = to_lower( lv_ext ).
      CASE lv_ext.
        WHEN 'pdf'.  ls_document-mime_type = 'application/pdf'.
        WHEN 'doc'.  ls_document-mime_type = 'application/msword'.
        WHEN 'docx'. ls_document-mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'.
        WHEN 'xls'.  ls_document-mime_type = 'application/vnd.ms-excel'.
        WHEN 'xlsx'. ls_document-mime_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'.
        WHEN 'jpg'.  ls_document-mime_type = 'image/jpeg'.
        WHEN 'jpeg'. ls_document-mime_type = 'image/jpeg'.
        WHEN 'png'.  ls_document-mime_type = 'image/png'.
        WHEN OTHERS. ls_document-mime_type = 'application/octet-stream'.
      ENDCASE.
    ELSE.
      ls_document-mime_type = 'application/octet-stream'.
    ENDIF.

    "------------------------------------------------------
    " 4d. Lire le contenu binaire du fichier
    "------------------------------------------------------
    CALL FUNCTION 'ARCHIVOBJECT_GET_TABLE'
      EXPORTING
        archiv_id       = ls_toahr-archiv_id
        arc_doc_id      = ls_toahr-arc_doc_id
      IMPORTING
        binarchivobject = lv_content
      EXCEPTIONS
        OTHERS          = 1 ##ARG_OK ##FM_PAR_MIS.

    IF sy-subrc = 0.
      ls_document-content = lv_content.
    ENDIF.

    "------------------------------------------------------
    " 4e. Déterminer un nom lisible selon le type de document
    "------------------------------------------------------
    CASE lv_doc_type.
      WHEN gc_document_types-separation_letter.
        ls_document-file_name = TEXT-001. "'Separation Letter'.
      WHEN gc_document_types-repatriation_travel.
        ls_document-file_name = TEXT-002."'Repatriation Travel'.
      WHEN gc_document_types-exit_questionnaire.
        ls_document-file_name = TEXT-003."'Exit Questionnaire'.
      WHEN gc_document_types-repatriation_shipment.
        ls_document-file_name = TEXT-004."'Repatriation Shipment'.
      WHEN OTHERS.
        IF ls_document-file_name IS INITIAL.
          ls_document-file_name = TEXT-005."'Unknown Document'.
        ENDIF.
    ENDCASE.

    "------------------------------------------------------
    " 4f. Statut
    "------------------------------------------------------
    ls_document-status = gc_status-uploaded.

    "------------------------------------------------------
    " 4g. Générer les URLs upload et download
    "------------------------------------------------------
    me->generate_document_urls(
      EXPORTING
        iv_request_id = iv_request_id
        iv_doc_type   = lv_doc_type
      IMPORTING
        ev_upload_url   = ls_document-uploaded
        ev_download_url = ls_document-download ).

    "------------------------------------------------------
    " 4h. Ajouter le document dans la table de sortie
    "------------------------------------------------------
    APPEND ls_document TO rt_files.

  ENDLOOP.

ENDMETHOD.
