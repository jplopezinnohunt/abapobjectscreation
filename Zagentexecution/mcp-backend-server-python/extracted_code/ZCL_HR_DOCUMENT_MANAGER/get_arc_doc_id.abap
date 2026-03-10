method get_arc_doc_id.

  "--------------------------------------------------------
  " Générer l’object_id unique à partir du request_id + doc_type
  "--------------------------------------------------------
  data lv_object_id type string.

  lv_object_id = generate_object_id(
                   iv_request_id = iv_request_id   " ID de la demande
                   iv_doc_type   = iv_doc_type ).  " Type de document

  "--------------------------------------------------------
  " Récupérer l’arc_doc_id depuis TOAHR
  "--------------------------------------------------------
  select single arc_doc_id
    into @rv_arc_doc_id
    from toahr
    where object_id  = @lv_object_id              " Filtre sur object_id généré
      and archiv_id  = @gc_archives-archive_id    " ID d’archive prédéfini
      and sap_object = @gc_archives-sap_object ##WARN_OK.   " Objet SAP prédéfini

  "--------------------------------------------------------
  " Vérification optionnelle : correspondance exacte avec filename
  " (dans la table TOAAT qui stocke les noms des fichiers)
  "--------------------------------------------------------
  if iv_filename is not initial and rv_arc_doc_id is not initial.
    select single arc_doc_id
      into @rv_arc_doc_id
      from toaat
      where arc_doc_id = @rv_arc_doc_id
        and filename   = @iv_filename.
  endif.

endmethod.
