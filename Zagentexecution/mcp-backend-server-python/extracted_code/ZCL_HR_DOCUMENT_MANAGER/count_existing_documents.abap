METHOD count_existing_documents.

  "--------------------------------------------------------
  " Déclaration des variables locales
  "--------------------------------------------------------
  DATA: lv_count          TYPE i,
        lv_object_id      TYPE string,
        lv_ar_object      TYPE string,
        lt_connections    TYPE STANDARD TABLE OF toa03,
        lv_temp_count     TYPE i,
        lt_doc_types      TYPE STANDARD TABLE OF string,
        lv_doc_type_temp  TYPE zde_doctype,
        lv_object_id_loop TYPE string,
        lv_ar_object_loop TYPE string.

  " Réinitialisation des variables de sortie
  CLEAR: rv_count, ev_message.

  "--------------------------------------------------------
  " Validation du paramètre obligatoire
  "--------------------------------------------------------
  IF iv_request_id IS INITIAL.
*    ev_message = 'Missing Request ID - no count performed'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '091'
      INTO ev_message.
    rv_count = 0.
    RETURN.
  ENDIF.

  "--------------------------------------------------------
  " Étape 1 : Génération de l'object_id
  "--------------------------------------------------------
  TRY.
      IF iv_doc_type IS NOT INITIAL.
        " Générer un object_id spécifique au type de document
        lv_object_id = me->generate_object_id(
                          iv_request_id = iv_request_id
                          iv_doc_type   = iv_doc_type ).
      ELSE.
        " Si pas de doc_type, on utilise un pattern générique pour LIKE
        lv_object_id = |%{ iv_request_id }%|.
      ENDIF.

      " Déterminer l'objet ArchiveLink correspondant
      lv_ar_object = me->map_doc_type_to_archive( iv_doc_type = iv_doc_type ).

      "--------------------------------------------------------
      "  Comptage direct dans TOA03
      "--------------------------------------------------------
      SELECT COUNT( * )
        FROM toa03
        WHERE sap_object = @gc_archives-sap_object
          AND ar_object  = @lv_ar_object
          AND object_id LIKE @lv_object_id
          AND archiv_id = @gc_archives-archive_id
        INTO @lv_count.

    CATCH cx_root INTO DATA(lx_error) ##NEEDED.
      " Si erreur, on considère qu'il n'y a aucun document
      lv_count = 0.
  ENDTRY.

  "--------------------------------------------------------
  "  Comptage via ARCHIV_GET_CONNECTIONS pour tous les types
  " si aucun document trouvé et pas de doc_type spécifique
  "--------------------------------------------------------
  IF lv_count = 0 AND iv_doc_type IS INITIAL.
    " Définition des types de documents à vérifier
    APPEND 'PDF_DOC'   TO lt_doc_types.
    APPEND 'EXCEL_DOC' TO lt_doc_types.
    APPEND 'WORD_DOC'  TO lt_doc_types.
    APPEND 'IMAGE_DOC' TO lt_doc_types.
    APPEND 'OTHER_DOC' TO lt_doc_types.

    " Boucle sur chaque type de document
    LOOP AT lt_doc_types INTO lv_doc_type_temp.
      " Déterminer l'objet ArchiveLink et l'object_id
      lv_ar_object_loop = me->map_doc_type_to_archive( iv_doc_type = lv_doc_type_temp ).
      lv_object_id_loop = me->generate_object_id(
                              iv_request_id = iv_request_id
                              iv_doc_type   = lv_doc_type_temp ).

      " Récupération des connexions ArchiveLink
      CALL FUNCTION 'ARCHIV_GET_CONNECTIONS'
        EXPORTING
          ar_object   = lv_ar_object_loop
          object_id   = lv_object_id_loop
          sap_object  = gc_archives-sap_object
        TABLES
          connections = lt_connections
        EXCEPTIONS
          OTHERS      = 1 ##ARG_OK ##COMPATIBLE.

      " Ajout du nombre de connexions trouvées
      IF sy-subrc = 0.
        lv_temp_count = lines( lt_connections ).
        ADD lv_temp_count TO lv_count.
      ENDIF.

      " Réinitialiser la table pour le prochain type
      CLEAR lt_connections.
    ENDLOOP.
  ENDIF.

  "--------------------------------------------------------
  " Log et retour de la valeur
  "--------------------------------------------------------
*  ev_message = |Document count - REQUEST_ID: { iv_request_id }, DOC_TYPE: { iv_doc_type }, COUNT: { lv_count }|.
  MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '092'
      INTO ev_message WITH iv_request_id iv_doc_type lv_count.
  rv_count = lv_count.

ENDMETHOD.
