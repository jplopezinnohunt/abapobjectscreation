METHOD get_file_content.

  " Déclaration de variables internes
  DATA: lt_binarchivobject TYPE STANDARD TABLE OF tbl1024, " Table pour stocker le contenu binaire depuis ArchiveLink
        lv_length          TYPE i,                        " Longueur du document
        lv_ar_object       TYPE string.                   " Type de document pour ArchiveLink

  " Réinitialiser les valeurs de sortie
  CLEAR: ev_content, ev_filename, ev_mime_type.

  "-------------------------------------------------------
  " 1. Récupérer le nom du fichier depuis TOAAT
  "-------------------------------------------------------
  SELECT SINGLE filename
    FROM toaat
    INTO ev_filename
    WHERE arc_doc_id = iv_arc_doc_id.                   " Filtre par arc_doc_id

  " Si le fichier n'existe pas, définir un type générique et sortir
  IF sy-subrc <> 0.
    ev_mime_type = 'application/octet-stream'.
    RETURN.
  ENDIF.

  "-------------------------------------------------------
  " 2. Récupérer le type de document depuis TOAHR
  "-------------------------------------------------------
  SELECT SINGLE ar_object
    FROM toahr
    INTO lv_ar_object
    WHERE arc_doc_id = iv_arc_doc_id ##WARN_OK.                 " Filtre par arc_doc_id

  " Si aucun type n'est trouvé, mettre PDF par défaut
  IF sy-subrc <> 0 OR lv_ar_object IS INITIAL.
    lv_ar_object = 'PDF'.
  ENDIF.

  "-------------------------------------------------------
  " 3. Récupérer le contenu binaire avec ArchiveLink
  "-------------------------------------------------------
  CALL FUNCTION 'ARCHIVOBJECT_GET_TABLE'
    EXPORTING
      archiv_id     = gc_archives-archive_id         " ID d'archive prédéfini
      archiv_doc_id = iv_arc_doc_id                  " ID du document à récupérer
      document_type = lv_ar_object                   " Type de document pour ArchiveLink
    IMPORTING
      length        = lv_length                      " Longueur du contenu récupéré
    TABLES
      binarchivobject = lt_binarchivobject           " Table contenant le contenu binaire
    EXCEPTIONS
      error_archiv             = 1
      error_communicationtable = 2
      error_kernel             = 3
      OTHERS                   = 4 ##COMPATIBLE.

  " Si erreur ou table vide, définir mime type générique et sortir
  IF sy-subrc <> 0 OR lines( lt_binarchivobject ) = 0.
    ev_mime_type = 'application/octet-stream'.
    RETURN.
  ENDIF.

  "-------------------------------------------------------
  " 4. Convertir le contenu binaire en XSTRING pour utilisation ABAP
  "-------------------------------------------------------
  CALL FUNCTION 'SCMS_BINARY_TO_XSTRING'
    EXPORTING
      input_length = lv_length                        " Longueur du contenu binaire
    IMPORTING
      buffer       = ev_content                       " Contenu converti en XSTRING
    TABLES
      binary_tab   = lt_binarchivobject.              " Table contenant le binaire

  "-------------------------------------------------------
  " 5. Déterminer le mime type selon l'extension du fichier
  "-------------------------------------------------------
  IF ev_filename CS '.pdf'.
    ev_mime_type = 'application/pdf'.
  ELSEIF ev_filename CS '.doc'.
    ev_mime_type = 'application/msword'.
  ELSEIF ev_filename CS '.docx'.
    ev_mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'.
  ELSEIF ev_filename CS '.jpg' OR ev_filename CS '.jpeg'.
    ev_mime_type = 'image/jpeg'.
  ELSEIF ev_filename CS '.png'.
    ev_mime_type = 'image/png'.
  ELSE.
    ev_mime_type = 'application/octet-stream'.      " Valeur par défaut si extension inconnue
  ENDIF.

ENDMETHOD.
