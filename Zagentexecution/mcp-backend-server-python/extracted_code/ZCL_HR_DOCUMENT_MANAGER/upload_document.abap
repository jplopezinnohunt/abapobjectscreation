METHOD upload_document.

  DATA: lv_subrc          TYPE syst_subrc,
        lv_arc_doc_id     TYPE saeardoid,
        lv_object_id      TYPE saeobjid,
        lv_ar_object      TYPE saeobjart,
        lt_binary_table   TYPE TABLE OF tbl1024,
        lv_size           TYPE string,
        lv_file_ext       TYPE saedoktyp,
        lv_document_type  TYPE saedoktyp,
        lv_file_name(255) TYPE c,
        lv_nachn          TYPE pad_nachn,
        lv_vorna          TYPE pad_vorna,
        lv_creator        TYPE syuname,
        lv_uname          TYPE syuname,
        lv_old_arc_doc_id TYPE saeardoid,
        lv_inc_nb         TYPE ze_hrfiori_incrment_nb,
        ls_existing_attac TYPE zthrfiori_attac,
*        ls_existing_toaat TYPE toaat ##NEEDED,
*        ls_existing_toahr TYPE toahr ##NEEDED,
        lv_size_num       TYPE num12,
        lv_doc_exists     TYPE abap_bool,
        lv_step_name      TYPE string,
        ls_attac          TYPE zthrfiori_attac.

  CLEAR: ev_message, ev_success.
  ev_success    = abap_false.
  lv_doc_exists = abap_false.

  "========================================================
  " 1. VALIDATION DES PARAMÈTRES OBLIGATOIRES
  "========================================================
  IF is_file-request_id IS INITIAL.
*    ev_message = 'Missing mandatory parameter: Request ID (GUID)'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '062'
      INTO ev_message.
    RETURN.
  ENDIF.

  IF is_file-mime_type IS INITIAL.
*    ev_message = 'Missing mandatory parameter: MIME type'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '063'
      INTO ev_message.
    RETURN.
  ENDIF.

  IF is_file-content IS INITIAL.
*    ev_message = 'Missing file contents'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '064'
      INTO ev_message.
    RETURN.
  ENDIF.

  IF is_file-document_type IS INITIAL.
*    ev_message = 'Missing mandatory parameter: Document Type (step)'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '065'
      INTO ev_message.
    RETURN.
  ENDIF.

  "========================================================
  " 2. VALIDATION DU STEP
  "========================================================
  lv_step_name = is_file-document_type.

*  IF lv_step_name <> c_sep_letter       "'SEP_LETTER'
*     AND lv_step_name <> c_repat_travel "'REPAT_TRAVEL'
*     AND lv_step_name <> c_exit_quest   "'EXIT_QUEST'
*     AND lv_step_name <> c_repat_ship.  "'REPAT_SHIP'
*    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '066'
*      INTO ev_message WITH lv_step_name.
*    RETURN.
*  ENDIF.

  "========================================================
  " 3. DÉTERMINATION DU TYPE DE DOCUMENT (EXTENSION)
  "========================================================
  IF is_file-file_ext IS NOT INITIAL.
    lv_document_type = to_upper( is_file-file_ext ).
    lv_file_ext      = lv_document_type.
  ELSE.
    CASE is_file-mime_type.
      WHEN 'application/pdf'.
        lv_document_type = 'PDF'.
      WHEN 'application/vnd.ms-excel'.
        lv_document_type = 'XLS'.
      WHEN 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'.
        lv_document_type = 'XLSX'.
      WHEN 'application/msword'.
        lv_document_type = 'DOC'.
      WHEN 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'.
        lv_document_type = 'DOCX'.
      WHEN 'image/jpeg'.
        lv_document_type = 'JPG'.
      WHEN 'image/png'.
        lv_document_type = 'PNG'.
      WHEN 'image/gif'.
        lv_document_type = 'GIF'.
      WHEN OTHERS.
        lv_document_type = 'DAT'.
    ENDCASE.
    lv_file_ext = lv_document_type.
  ENDIF.

  "========================================================
  " 4. GÉNÉRATION DU NOM DE FICHIER (STEP.EXTENSION)
  "========================================================
  lv_file_name = |{ lv_step_name }.{ lv_file_ext }|.

  "========================================================
  " 5. EXTENSIONS INTERDITES
  "========================================================
  DATA: lv_file_ext_upper TYPE string.
  lv_file_ext_upper = lv_file_ext.
  TRANSLATE lv_file_ext_upper TO UPPER CASE.

  IF lv_file_ext_upper = 'ZIP' OR lv_file_ext_upper = 'EXE'
     OR lv_file_ext_upper = 'BAT' OR lv_file_ext_upper = 'CMD'
     OR lv_file_ext_upper = 'MSI' OR lv_file_ext_upper = 'SCR'
     OR lv_file_ext_upper = 'COM' OR lv_file_ext_upper = 'PIF'
     OR lv_file_ext_upper = 'DLL' OR lv_file_ext_upper = 'VBS'
     OR lv_file_ext_upper = 'JS'  OR lv_file_ext_upper = 'JAR'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '067'
      INTO ev_message WITH lv_file_ext_upper.
*    ev_message = |Incompatible file type: Extension .{ lv_file_ext_upper } not allowed|.
    RETURN.
  ENDIF.

  "========================================================
  " 6. GÉNÉRATION DE L'OBJECT_ID POUR ARCHIVELINK
  "========================================================
  DATA: lv_request_id_str TYPE ze_hrfiori_guidreq.
  lv_request_id_str = is_file-request_id.

  lv_object_id = me->generate_object_id(
                     iv_request_id = lv_request_id_str
                     iv_doc_type   = is_file-document_type ).
  CONDENSE lv_object_id NO-GAPS.

  IF strlen( lv_object_id ) = 0 OR strlen( lv_object_id ) > 90.
    DATA(lv_size_obj) = strlen( lv_object_id ).
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '068'
      INTO ev_message WITH lv_size_obj.
*    ev_message = |Invalid object_id generated: length={ strlen( lv_object_id ) }|.
    RETURN.
  ENDIF.

  "========================================================
  " 7. PARAMÈTRES ARCHIVELINK (DYNAMIQUE SELON LE TYPE)
  "========================================================
*  CASE is_file-document_type.
*    WHEN c_sep_letter. "'SEP_LETTER'.
*      lv_ar_object = c_obj_sepletter. "'SEPLETTER'.
*    WHEN c_repat_travel."'REPAT_TRAVEL'.
*      lv_ar_object = c_obj_repattrip. "'REPATTRIP'.
*    WHEN c_exit_quest. "'EXIT_QUEST'.
*      lv_ar_object = c_obj_exitquest."'EXITQUEST'.
*    WHEN c_repat_ship. "'REPAT_SHIP'.
*      lv_ar_object = c_obj_repat_ship. "'REPAT_SHIP'.
*    WHEN OTHERS.
*      lv_ar_object = me->map_doc_type_to_archive( iv_doc_type = lv_document_type ).
*  ENDCASE.
  lv_ar_object = is_file-document_type.

  "========================================================
  " 8. ⚠️ VÉRIFICATION D'EXISTENCE DU DOCUMENT
  "    => Rechercher par REQUEST_ID + FILE_TYPE (step)
  "========================================================
  SELECT SINGLE * INTO @ls_existing_attac
    FROM zthrfiori_attac
    WHERE request_id = @is_file-request_id
      AND file_type  = @lv_step_name ##WARN_OK.

  IF sy-subrc = 0.
    " Document existe déjà pour ce REQUEST_ID + STEP
    lv_doc_exists     = abap_true.
    lv_old_arc_doc_id = ls_existing_attac-archive_doc_id.
    lv_inc_nb         = ls_existing_attac-inc_nb + 1.

  ELSE.
    " Nouveau document pour ce step
    lv_inc_nb = 1.
  ENDIF.

  "========================================================
  " 9. ⚠️ VALIDATION DU MODE CREATE NEW vs OVERWRITE
  "========================================================
  IF lv_doc_exists = abap_true.
    " Document existe => Vérifier le flag replace
    IF is_file-replace_flag = abap_false.
      " Mode CREATE NEW avec document existant => ERREUR
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '069'
        INTO DATA(lv_str1) WITH lv_step_name ls_existing_attac-file_name.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '070'
        INTO DATA(lv_str2).
      CONCATENATE lv_str1 lv_str2 INTO ev_message.
      RETURN.
    ELSE.
      " Mode OVERWRITE => Continuer avec suppression
    ENDIF.
  ELSE.
    " Pas de document existant
    IF is_file-replace_flag = abap_true.
    ENDIF.
  ENDIF.

  "========================================================
  " 10. DONNÉES EMPLOYÉ
  "========================================================
  IF is_file-pernr IS NOT INITIAL.
    CALL METHOD zcl_hr_fiori_offboarding_req=>get_employee_data
      EXPORTING
        iv_persno = is_file-pernr
      IMPORTING
        ev_nachn  = lv_nachn
        ev_vorna  = lv_vorna.

    IF sy-subrc <> 0 ##SUBRC_OK.
      lv_creator = 'UNKNOWN UPDATER'.
    ELSE.
      lv_creator = |{ lv_nachn } { lv_vorna }|.
    ENDIF.

    SELECT SINGLE bname INTO @lv_uname
      FROM usr21
      WHERE persnumber = @is_file-pernr ##WARN_OK.

    IF sy-subrc = 0.
      lv_creator = lv_uname.
    ENDIF.
  ELSE.
    lv_creator = sy-uname.
  ENDIF.

  "========================================================
  " 11. CONVERSION EN BINAIRE
  "========================================================
  DATA lv_content_xstring TYPE xstring.

  IF is_file-content IS INITIAL.
*    ev_message = 'File content is empty or invalid'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '071'
      INTO ev_message.
    RETURN.
  ENDIF.

  TRY.
      lv_content_xstring = is_file-content.
    CATCH cx_sy_move_cast_error.
*      ev_message = 'File content could not be cast to XSTRING'.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '072'
        INTO ev_message.
      RETURN.
  ENDTRY.

  CALL FUNCTION 'SCMS_XSTRING_TO_BINARY'
    EXPORTING
      buffer     = lv_content_xstring
    TABLES
      binary_tab = lt_binary_table
    EXCEPTIONS
      failed     = 1
      OTHERS     = 2 ##ARG_OK.

  IF sy-subrc <> 0.
*    ev_message = 'Error converting file content to binary format'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '073'
       INTO ev_message.
    RETURN.
  ENDIF.

  lv_size_num = xstrlen( lv_content_xstring ).
  lv_size     = lv_size_num.

  IF lv_size_num > 52428800.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '074'
      INTO ev_message WITH lv_size_num.
*    ev_message = |File too large: { lv_size_num } bytes (max 50MB)|.
    RETURN.
  ENDIF.

  "========================================================
  " 12. SUPPRESSION DE L'ANCIEN DOCUMENT (MODE OVERWRITE UNIQUEMENT)
  "========================================================
  IF lv_doc_exists = abap_true AND lv_old_arc_doc_id IS NOT INITIAL.

    " ⬅️ CRITIQUE: Suppression UNIQUEMENT en mode OVERWRITE
    IF is_file-replace_flag = abap_true.

      " Supprimer les liens ArchiveLink
      DELETE FROM toahr WHERE object_id  = @lv_object_id
                           AND ar_object  = @lv_ar_object
                           AND arc_doc_id = @lv_old_arc_doc_id.

      DELETE FROM toaat WHERE arc_doc_id = @lv_old_arc_doc_id.

      " Supprimer le document physique de l'archive
      CALL FUNCTION 'ARCHIVOBJECT_DELETE'
        EXPORTING
          archiv_id     = gc_archives-archive_id
          archiv_doc_id = lv_old_arc_doc_id
        EXCEPTIONS
          OTHERS        = 0.

      " Supprimer l'ancienne entrée dans notre table custom
      DELETE FROM zthrfiori_attac
        WHERE request_id     = @is_file-request_id
          AND file_type      = @lv_step_name
          AND archive_doc_id = @lv_old_arc_doc_id.

      COMMIT WORK AND WAIT.

    ENDIF.

  ENDIF.

  "========================================================
  " 13. CRÉATION DANS L'ARCHIVE SAP
  "========================================================
  DATA lv_length_int TYPE num12.
  lv_length_int = lv_size_num.

  CLEAR: lv_subrc.
  CALL FUNCTION 'ARCHIVOBJECT_CREATE_TABLE'
    EXPORTING
      archiv_id       = gc_archives-archive_id
      document_type   = lv_document_type
      length          = lv_length_int
    IMPORTING
      archiv_doc_id   = lv_arc_doc_id
    TABLES
      binarchivobject = lt_binary_table
    EXCEPTIONS
      error_archiv    = 1
      OTHERS          = 2.

  lv_subrc = sy-subrc.
  IF lv_subrc <> 0.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '075'
      INTO ev_message WITH lv_subrc.
    RETURN.
  ENDIF.

  "========================================================
  " 14. CRÉATION LIAISON ARCHIVELINK
  "========================================================
  CALL FUNCTION 'ARCHIV_CONNECTION_INSERT'
    EXPORTING
      archiv_id             = gc_archives-archive_id
      arc_doc_id            = lv_arc_doc_id
      ar_object             = lv_ar_object
      object_id             = lv_object_id
      sap_object            = gc_archives-sap_object
      doc_type              = lv_file_ext
      filename              = lv_file_name
      creator               = lv_creator
    EXCEPTIONS
      error_connectiontable = 1
      OTHERS                = 2.

  IF sy-subrc <> 0.
    CLEAR lv_subrc.
    CALL FUNCTION 'ARCHIVOBJECT_DELETE'
      EXPORTING
        archiv_id                = gc_archives-archive_id
        archiv_doc_id            = lv_arc_doc_id
      EXCEPTIONS
        error_archiv             = 1
        error_communicationtable = 2
        error_kernel             = 3
        OTHERS                   = 4.

    lv_subrc = sy-subrc.
    IF lv_subrc <> 0.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '035'
        INTO ev_message WITH lv_subrc.
    ELSE.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '076'
        INTO ev_message WITH lv_subrc.
    ENDIF.
    RETURN.
  ENDIF.

  "========================================================
  " 15. SAUVEGARDE DANS ZTHRFIORI_ATTAC
  "========================================================
  CLEAR ls_attac.

  ls_attac-mandt          = sy-mandt.
  ls_attac-request_id     = is_file-request_id.
  ls_attac-file_type      = lv_step_name.
  ls_attac-inc_nb         = lv_inc_nb.
  ls_attac-file_name      = lv_file_name.
  ls_attac-fileext        = lv_file_ext.
  ls_attac-filesize       = lv_size.
  ls_attac-mime_type      = is_file-mime_type.
  ls_attac-archive_doc_id = lv_arc_doc_id.
  ls_attac-last_upd_date  = sy-datum.
  ls_attac-last_upd_time  = sy-uzeit.
  ls_attac-upd_usr_id     = sy-uname.
  ls_attac-upd_pernr      = is_file-pernr.
  ls_attac-upd_lname      = lv_nachn.
  ls_attac-upd_fname      = lv_vorna.

  IF lv_doc_exists = abap_true.
    " Conserver les infos du créateur original
    ls_attac-creation_date  = ls_existing_attac-creation_date.
    ls_attac-creation_time  = ls_existing_attac-creation_time.
    ls_attac-creator_pernr  = ls_existing_attac-creator_pernr.
    ls_attac-creator_lname  = ls_existing_attac-creator_lname.
    ls_attac-creator_fname  = ls_existing_attac-creator_fname.
  ELSE.
    " Nouveau document
    ls_attac-creation_date  = sy-datum.
    ls_attac-creation_time  = sy-uzeit.
    ls_attac-creator_pernr  = is_file-pernr.
    ls_attac-creator_lname  = lv_nachn.
    ls_attac-creator_fname  = lv_vorna.
  ENDIF.

  " MODIFY va insérer ou mettre à jour selon la clé primaire
  CLEAR lv_subrc.
  MODIFY zthrfiori_attac FROM ls_attac.
  lv_subrc = sy-subrc.
  IF lv_subrc <> 0.
*    ev_message = |Error saving to ZTHRFIORI_ATTAC: MODIFY RC={ sy-subrc }|.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '077'
      INTO ev_message WITH lv_subrc.
    RETURN.
  ENDIF.

  COMMIT WORK AND WAIT.
  ev_success = abap_true.

  IF lv_doc_exists = abap_true AND is_file-replace_flag = abap_true.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '078'
      INTO DATA(lv_suc_str1) WITH lv_step_name lv_arc_doc_id.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '079'
      INTO DATA(lv_suc_str2) WITH lv_file_ext lv_inc_nb.
    CONCATENATE lv_suc_str1 lv_suc_str2 INTO ev_message SEPARATED BY space.
  ELSE.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '080'
      INTO DATA(lv_suc_str3) WITH lv_step_name lv_arc_doc_id.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '081'
      INTO DATA(lv_suc_str4) WITH lv_file_ext.
    CONCATENATE lv_suc_str3 lv_suc_str4 INTO ev_message SEPARATED BY space.
  ENDIF.

ENDMETHOD.
