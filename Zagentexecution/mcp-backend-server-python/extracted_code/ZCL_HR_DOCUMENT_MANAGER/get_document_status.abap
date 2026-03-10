METHOD get_document_status.

  "--------------------------------------------------------
  " Déclaration des variables locales
  "--------------------------------------------------------
  DATA lv_object_id  TYPE string.
  DATA lv_arc_doc_id TYPE string.

  "--------------------------------------------------------
  " Génération de l'identifiant unique (object_id)
  " basé sur le Request ID et le DocType
  "--------------------------------------------------------
  lv_object_id = generate_object_id(
                    iv_request_id = iv_request_id    " Identifiant de la demande
                    iv_doc_type   = iv_doc_type ).  " Type de document

  "--------------------------------------------------------
  " Vérification de l'existence du document dans la table d'archivage TOAHR
  "--------------------------------------------------------
  SELECT SINGLE arc_doc_id
    INTO lv_arc_doc_id
    FROM toahr
    WHERE object_id  = lv_object_id             " Filtre sur l'identifiant généré
      AND archiv_id  = gc_archives-archive_id  " Filtre sur l'ID d'archive prédéfini
      AND sap_object = gc_archives-sap_object ##WARN_OK. " Filtre sur le type d'objet SAP prédéfini

  "--------------------------------------------------------
  " Détermination du statut du document
  "--------------------------------------------------------
  IF sy-subrc = 0 AND lv_arc_doc_id IS NOT INITIAL.
    " Document trouvé => statut 'UPLOADED'
    rv_status = gc_status-uploaded.
  ELSE.
    " Document non trouvé => statut 'NOT_UPLOADED'
    rv_status = gc_status-not_uploaded.
  ENDIF.

ENDMETHOD.
