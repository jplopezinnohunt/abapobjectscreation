METHOD map_doc_type_to_archive.

  "--------------------------------------------------------
  " Mappe un type de document à son objet ArchiveLink correspondant
  "--------------------------------------------------------

  CASE iv_doc_type.

      " Lettre de séparation
    WHEN gc_document_types-separation_letter.
      rv_ar_object = c_hroffboard_sep."'HROFFBOARD_SEP'.  " Objet ArchiveLink spécifique

      " Rapatriement
    WHEN gc_document_types-repatriation_travel.
      rv_ar_object = c_hroffboard_rep."'HROFFBOARD_REP'.  " Objet ArchiveLink spécifique

      " Questionnaire de départ
    WHEN gc_document_types-exit_questionnaire.
      rv_ar_object = c_hroffboard_exit."'HROFFBOARD_EXIT'. " Objet ArchiveLink spécifique

    WHEN gc_document_types-repatriation_shipment.
      rv_ar_object = c_hroffboard_ship."'HROFFBOARD_SHIP'. " Objet ArchiveLink spécifique


      " Tous les autres types de document
    WHEN OTHERS.
      rv_ar_object = gc_archives-doc_class.  " Objet ArchiveLink générique (classe documentaire par défaut)

  ENDCASE.

ENDMETHOD.
