METHOD get_document.

  DATA: lv_subrc           TYPE syst_subrc,
        lv_archiv_id       TYPE saearchivi,
        lv_arc_doc_id      TYPE saeardoid,
        lv_doc_type        TYPE saedoktyp,
        lv_ar_object       TYPE saeobjart ##NEEDED,
        ls_toahr           TYPE toahr,
        lt_binarchivobject TYPE STANDARD TABLE OF tbl1024,
        lv_binlength       TYPE num12,
        lv_binlength_int   TYPE i,
        ls_document        TYPE zthrfiori_attac,
        lv_fileext_up      TYPE string.

  CLEAR: ev_content, ev_mime_type, ev_filename, ev_success, ev_message.
  ev_success = abap_false.

  "------------------------------------------------------------
  " 1. Validation de la clé principale
  "------------------------------------------------------------
* For DEMO purpose only, coment this part
*  if iv_archive_doc_id is initial
*   and iv_request_id is initial
*   and iv_attach_type is initial
*   and iv_incnb is initial.
*    ev_message = 'No key provided (ArchiveDocId, RequestId, AttachType or IncNb required)'.
*    return.
*  endif.

  "------------------------------------------------------------
  " 2. Construction dynamique du WHERE - CORRECTION TYPE-SAFE
  "------------------------------------------------------------
  "------------------------------------------------------------
  " 1. Définition des variables locales typées
  "------------------------------------------------------------
  DATA: lv_request_id_local     TYPE ze_hrfiori_guidreq ##NEEDED,
        lv_attach_type_local    TYPE zde_doctype ##NEEDED,
        lv_incnb_local          TYPE ze_hrfiori_incrment_nb ##NEEDED,
        lv_archive_doc_id_local TYPE saeardoid ##NEEDED.

  " Copier les valeurs dans les variables locales
  lv_request_id_local     = iv_request_id.
  lv_attach_type_local    = iv_attach_type.
  lv_incnb_local          = iv_incnb.
  lv_archive_doc_id_local = iv_archive_doc_id.

  "------------------------------------------------------------
  " 2. SELECT type-safe avec conditions dynamiques
  "------------------------------------------------------------
*  DATA: lt_conditions TYPE string_table.

  " Tester si des conditions existent et construire la clause WHERE
  DATA: lv_where_clause TYPE string.

  IF iv_request_id IS NOT INITIAL.
    IF lv_where_clause IS NOT INITIAL.
      lv_where_clause = lv_where_clause && | AND |.
    ENDIF.
    lv_where_clause = lv_where_clause && |REQUEST_ID = '{ iv_request_id }'|.
  ENDIF.

  IF iv_attach_type IS NOT INITIAL.
    IF lv_where_clause IS NOT INITIAL.
      lv_where_clause = lv_where_clause && | AND |.
    ENDIF.
    " Mappage: AttachType (OData) -> FILE_TYPE (DB)
    lv_where_clause = lv_where_clause && |FILE_TYPE = '{ iv_attach_type }'|.
  ENDIF.

  IF iv_incnb IS NOT INITIAL.
    IF lv_where_clause IS NOT INITIAL.
      lv_where_clause = lv_where_clause && | AND |.
    ENDIF.
    " Mappage: IncNb (OData) -> INC_NB (DB)
    lv_where_clause = lv_where_clause && |INC_NB = '{ iv_incnb }'|.
  ENDIF.

  IF iv_archive_doc_id IS NOT INITIAL.
    IF lv_where_clause IS NOT INITIAL.
      lv_where_clause = lv_where_clause && | AND |.
    ENDIF.
    " Mappage: ArchiveDocId (OData) -> ARCHIVE_DOC_ID (DB)
    lv_where_clause = lv_where_clause && |ARCHIVE_DOC_ID = '{ iv_archive_doc_id }'|.
  ENDIF.

  " Tester si des conditions existent
  IF lv_where_clause IS INITIAL.
*    ev_message = 'No key provided'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '093'
      INTO ev_message.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " 3. SELECT dynamique (CORRIGÉ)
  "------------------------------------------------------------
  SELECT SINGLE *
    FROM zthrfiori_attac
    INTO @ls_document
    WHERE (lv_where_clause) ##WARN_OK.

  IF sy-subrc <> 0.
*    ev_message = 'Document not found'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '094'
      INTO ev_message.
    RETURN.
  ENDIF.
  "------------------------------------------------------------
  " 3. SELECT dynamique avec type-safe (CORRIGÉ)
  "------------------------------------------------------------
*  select single *
*    from zthrfiori_attac
*    into @ls_document
*    where (lt_conditions).
*
*  if sy-subrc <> 0.
*    ev_message = 'Document not found'.
*    return.
*  endif.
  "------------------------------------------------------------
  " 4. Lecture des métadonnées dans TOAHR
  "------------------------------------------------------------
  lv_arc_doc_id = ls_document-archive_doc_id.

  SELECT SINGLE *
    FROM toahr
    INTO ls_toahr
    WHERE arc_doc_id = lv_arc_doc_id ##WARN_OK.

  IF sy-subrc = 0.
    lv_archiv_id = ls_toahr-archiv_id.
    lv_ar_object = ls_toahr-ar_object.
  ELSE.
    " Valeurs par défaut si introuvable
    lv_archiv_id = gc_archives-archive_id.
    lv_ar_object = gc_archives-sap_object.
  ENDIF.

  IF lv_archiv_id IS INITIAL.
*    ev_message = 'Archive ID not found in TOAHR'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '095'
      INTO ev_message.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " 5. Détermination du type de document
  "------------------------------------------------------------
  IF ls_document-mime_type IS NOT INITIAL.
    CASE ls_document-mime_type.
      WHEN 'application/pdf'.
        lv_doc_type = 'PDF'.
      WHEN 'image/jpeg' OR 'image/jpg'.
        lv_doc_type = 'JPG'.
      WHEN 'image/png'.
        lv_doc_type = 'PNG'.
      WHEN 'image/tiff' OR 'image/tif'.
        lv_doc_type = 'TIF'.
      WHEN 'application/msword'
        OR 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'.
        lv_doc_type = 'DOC'.
      WHEN 'application/vnd.ms-excel'
        OR 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'.
        lv_doc_type = 'XLS'.
      WHEN 'text/plain'.
        lv_doc_type = 'TXT'.
      WHEN OTHERS.
        lv_doc_type = ''.
    ENDCASE.
  ENDIF.

  IF lv_doc_type IS INITIAL AND ls_document-fileext IS NOT INITIAL.
    lv_fileext_up = ls_document-fileext.
    TRANSLATE lv_fileext_up TO UPPER CASE.
    CASE lv_fileext_up.
      WHEN 'PDF'.
        lv_doc_type = 'PDF'.
      WHEN 'JPG' OR 'JPEG'.
        lv_doc_type = 'JPG'.
      WHEN 'PNG'.
        lv_doc_type = 'PNG'.
      WHEN 'TIF' OR 'TIFF'.
        lv_doc_type = 'TIF'.
      WHEN 'DOC' OR 'DOCX'.
        lv_doc_type = 'DOC'.
      WHEN 'XLS' OR 'XLSX'.
        lv_doc_type = 'XLS'.
      WHEN 'TXT'.
        lv_doc_type = 'TXT'.
      WHEN OTHERS.
        lv_doc_type = ''.
    ENDCASE.
  ENDIF.

  IF lv_doc_type IS INITIAL.
    lv_doc_type = 'PDF'.
  ENDIF.

  "------------------------------------------------------------
  " 6. Récupération du contenu via ARCHIVOBJECT_GET_TABLE
  "------------------------------------------------------------
  CLEAR lv_subrc.
  CALL FUNCTION 'ARCHIVOBJECT_GET_TABLE'
    EXPORTING
      archiv_id                = lv_archiv_id
      archiv_doc_id            = lv_arc_doc_id
      document_type            = lv_doc_type
    IMPORTING
      length                   = lv_binlength
    TABLES
      binarchivobject          = lt_binarchivobject
    EXCEPTIONS
      error_archiv             = 1
      error_communicationtable = 2
      error_kernel             = 3
      OTHERS                   = 4.

  lv_subrc = sy-subrc.

  IF lv_subrc <> 0.
    CASE lv_subrc.
      WHEN 1.
        MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '096'
          INTO ev_message.
*        ev_message = 'Archive system error - Check OAC0'.
      WHEN 2.
        MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '088'
          INTO ev_message.
*        ev_message = 'Communication table error'.
      WHEN 3.
        MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '089'
          INTO ev_message.
*        ev_message = 'SAP kernel error'.
      WHEN OTHERS.
        MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '097'
          INTO ev_message WITH lv_subrc.
*        ev_message = |Retrieval error (sy-subrc={ sy-subrc })|.
    ENDCASE.
    RETURN.
  ENDIF.

  IF lt_binarchivobject IS INITIAL OR lv_binlength = 0.
*    ev_message = 'Empty content - document missing from Content Server'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '098'
      INTO ev_message.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " 7. Conversion en XSTRING
  "------------------------------------------------------------
  lv_binlength_int = lv_binlength.

  CALL FUNCTION 'SCMS_BINARY_TO_XSTRING'
    EXPORTING
      input_length = lv_binlength_int
    IMPORTING
      buffer       = ev_content
    TABLES
      binary_tab   = lt_binarchivobject
    EXCEPTIONS
      OTHERS       = 1.

  IF sy-subrc <> 0 OR ev_content IS INITIAL.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '099'
      INTO ev_message.
*    ev_message = 'Binary to XSTRING conversion failed'.
    RETURN.
  ENDIF.

  "------------------------------------------------------------
  " 8. Préparer le nom de fichier final
  "------------------------------------------------------------
  DATA(lv_filename_temp) = ls_document-file_name.
  DATA(lv_ext_lower)     = to_lower( ls_document-fileext ).

  IF lv_ext_lower IS NOT INITIAL.
    IF lv_filename_temp CP |*.{ lv_ext_lower }|.
      ev_filename = lv_filename_temp.
    ELSE.
      ev_filename = |{ lv_filename_temp }.{ lv_ext_lower }|.
    ENDIF.
  ELSE.
    ev_filename = lv_filename_temp.
  ENDIF.

  IF ev_filename IS INITIAL.
    ev_filename = |document_{ lv_arc_doc_id }.pdf|.
  ENDIF.

  "------------------------------------------------------------
  " 9. Déterminer le MIME type
  "------------------------------------------------------------
  ev_mime_type = COND #( WHEN ls_document-mime_type IS NOT INITIAL
                         THEN ls_document-mime_type
                         ELSE 'application/pdf' ).

  "------------------------------------------------------------
  " 10. Succès
  "------------------------------------------------------------
  ev_success = abap_true.
*  ev_message = |Document retrieved successfully ({ lv_binlength } bytes)|.
  MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '100'
    INTO ev_message WITH lv_binlength.

ENDMETHOD.
