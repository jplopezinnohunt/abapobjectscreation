METHOD CHECK_FILE_EXISTS.
" Déclare une variable locale pour stocker l'identifiant objet généré
  DATA lv_object_id TYPE string. " Génère un identifiant objet unique basé sur l'ID de la demande et le type de document
       lv_object_id = generate_object_id( iv_request_id = iv_request_id " ID de la demande
       iv_doc_type = iv_type_doc ). " Type de document
       " Sélectionne un identifiant de document d'archive dans la table TOAHR
       " si une entrée correspond à l'identifiant objet et aux paramètres d'archivage
       SELECT SINGLE arc_doc_id INTO @DATA(lv_arc_doc_id) FROM toahr
         WHERE object_id = @lv_object_id " Filtre par identifiant objet généré
         AND archiv_id = @gc_archives-archive_id " Filtre par ID d'archive prédéfini
         AND sap_object = @gc_archives-sap_object ##WARN_OK." Filtre par type d'objet SAP prédéfini
          " Détermine la valeur de retour :
         " - Vrai (abap_true) si un enregistrement a été trouvé et que l'ID d'archive n'est pas vide
         " - Faux (abap_false) sinon
         rv_exists = COND #( WHEN sy-subrc = 0 AND lv_arc_doc_id IS NOT INITIAL THEN abap_true ELSE abap_false ).
  ENDMETHOD.
