METHOD toaatset_get_entityset.
*--------------------------------------------------------------------
*" Objectif :
*"   Récupérer la liste des documents (EntitySet) associés à un
*"   REQUEST_ID (GUID) depuis les tables ZTHRFIORI_ATTAC
*" Contexte :
*"   Cette méthode est appelée par le service OData lors d'un appel
*"   GET_ENTITYSET sur l'entité TOAATSET. Le filtre REQUEST_ID (GUID)
*"   est obligatoire.
*--------------------------------------------------------------------

  FIELD-SYMBOLS: <ls_entity> TYPE any.                   " Ligne de l'EntitySet

*--------------------------------------------------------------------
*" Structure pour stocker les résultats de ZTHRFIORI_ATTAC
*--------------------------------------------------------------------
  TYPES: BEGIN OF ty_doc_result,
           request_id     TYPE zthrfiori_attac-request_id,
           file_type      TYPE zthrfiori_attac-file_type,
           inc_nb         TYPE zthrfiori_attac-inc_nb,
           file_name      TYPE zthrfiori_attac-file_name,
           fileext        TYPE zthrfiori_attac-fileext,
           filesize       TYPE zthrfiori_attac-filesize,
           mime_type      TYPE zthrfiori_attac-mime_type,
           archive_doc_id TYPE zthrfiori_attac-archive_doc_id,
           creation_date  TYPE zthrfiori_attac-creation_date,
           creation_time  TYPE zthrfiori_attac-creation_time,
           creator_pernr  TYPE zthrfiori_attac-creator_pernr,
           creator_lname  TYPE zthrfiori_attac-creator_lname,
           creator_fname  TYPE zthrfiori_attac-creator_fname,
           last_upd_date  TYPE zthrfiori_attac-last_upd_date,
           last_upd_time  TYPE zthrfiori_attac-last_upd_time,
           upd_usr_id     TYPE zthrfiori_attac-upd_usr_id,
           upd_pernr      TYPE zthrfiori_attac-upd_pernr,
           upd_lname      TYPE zthrfiori_attac-upd_lname,
           upd_fname      TYPE zthrfiori_attac-upd_fname,
         END OF ty_doc_result.

*--------------------------------------------------------------------
*" Déclaration des variables locales
*--------------------------------------------------------------------
  DATA: lv_err_msg         TYPE bapi_msg,
        lv_request_id      TYPE string,                     " GUID d'entrée (filtre)
        ls_filter          TYPE /iwbep/s_mgw_select_option, " Structure de filtre OData
        lt_doc_results     TYPE TABLE OF ty_doc_result,     " Table résultat
        lv_filename_full   TYPE string,                     " Nom complet du fichier
        lv_attach_type_txt TYPE string.                     " Texte du type d'attachement

*--------------------------------------------------------------------
*" 1. Extraction du filtre REQUEST_ID depuis la requête OData
*--------------------------------------------------------------------
  LOOP AT it_filter_select_options INTO ls_filter.
    IF ls_filter-property = 'REQUEST_ID' OR ls_filter-property = 'GUID'.
      READ TABLE ls_filter-select_options INTO DATA(ls_select) INDEX 1.
      IF sy-subrc = 0.
        lv_request_id = ls_select-low.
        EXIT.
      ENDIF.
    ENDIF.
  ENDLOOP.

*--------------------------------------------------------------------
*" 2. Vérification du filtre obligatoire
*--------------------------------------------------------------------
  IF lv_request_id IS INITIAL.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '101'
      INTO lv_err_msg.
    RAISE EXCEPTION TYPE /iwbep/cx_mgw_busi_exception
      EXPORTING
        textid  = /iwbep/cx_mgw_busi_exception=>business_error
        message = lv_err_msg.
  ENDIF.

*--------------------------------------------------------------------
*" 3. Normalisation du GUID (optionnelle selon format stocké)
*--------------------------------------------------------------------
  REPLACE ALL OCCURRENCES OF '-' IN lv_request_id WITH ''.
  TRANSLATE lv_request_id TO UPPER CASE.

*--------------------------------------------------------------------
*" 4. Sélection des documents depuis ZTHRFIORI_ATTAC
*--------------------------------------------------------------------
  SELECT request_id,
         file_type,
         inc_nb,
         file_name,
         fileext,
         filesize,
         mime_type,
         archive_doc_id,
         creation_date,
         creation_time,
         creator_pernr,
         creator_lname,
         creator_fname,
         last_upd_date,
         last_upd_time,
         upd_usr_id,
         upd_pernr,
         upd_lname,
         upd_fname
    FROM zthrfiori_attac
    INTO CORRESPONDING FIELDS OF TABLE @lt_doc_results
   WHERE request_id = @lv_request_id
   ORDER BY creation_date DESCENDING,
            creation_time DESCENDING.

*--------------------------------------------------------------------
*" 5. Vérification du résultat
*--------------------------------------------------------------------
  IF sy-subrc <> 0 OR lt_doc_results IS INITIAL.
    " Ne pas lever d'exception si aucun document n'est trouvé
    " Retourner simplement un EntitySet vide
    " raise exception type /iwbep/cx_mgw_busi_exception
    "   exporting
    "     textid  = /iwbep/cx_mgw_busi_exception=>business_error
    "     message = |No documents found for REQUEST_ID { lv_request_id }|.
    RETURN. " EntitySet vide
  ENDIF.

*--------------------------------------------------------------------
*" 6. Construction de l'EntitySet de sortie
*--------------------------------------------------------------------
  LOOP AT lt_doc_results INTO DATA(ls_result).
    " Ajouter une nouvelle ligne dans l'EntitySet
    APPEND INITIAL LINE TO et_entityset ASSIGNING <ls_entity>.

    " REQUEST_ID
    ASSIGN COMPONENT 'GUID' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_request_id_out>).
    IF <lv_request_id_out> IS ASSIGNED.
      <lv_request_id_out> = ls_result-request_id.
    ENDIF.

    " ATTACH_TYPE (code brut)
    ASSIGN COMPONENT 'ATTACH_TYPE' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_attach_type>).
    IF <lv_attach_type> IS ASSIGNED.
      <lv_attach_type> = ls_result-file_type.
    ENDIF.

    " ATTACH_TYPE_TXT (texte descriptif)
    ASSIGN COMPONENT 'ATTACH_TYPE_TXT' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_attach_type_txt_out>).
    IF <lv_attach_type_txt_out> IS ASSIGNED.
      " Conversion du code FILE_TYPE en texte descriptif
      CLEAR lv_attach_type_txt.
      CASE ls_result-file_type.
        WHEN 'SEP_LETTER'.
          lv_attach_type_txt = text-001."'Separation Letter'.
        WHEN 'REPAT_TRAV'.
          lv_attach_type_txt = text-002."'Repatriation Travel'.
        WHEN 'EXIT_QUEST'.
          lv_attach_type_txt = text-003."'Exit Questionnaire'.
        WHEN 'REPAT_SHIP'.
          lv_attach_type_txt = text-004."'Repatriation Shipment'.
        WHEN OTHERS.
          " Si le type est inconnu, utiliser le code brut
          lv_attach_type_txt = ls_result-file_type.
      ENDCASE.
      <lv_attach_type_txt_out> = lv_attach_type_txt.
    ENDIF.

    " INC_NB
    ASSIGN COMPONENT 'INC_NB' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_inc_nb>).
    IF <lv_inc_nb> IS ASSIGNED.
      <lv_inc_nb> = ls_result-inc_nb.
    ENDIF.

    " FILENAME (nom complet = file_name + . + fileext)
    ASSIGN COMPONENT 'FILENAME' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_filename>).
    IF <lv_filename> IS ASSIGNED.
      CLEAR lv_filename_full.
      IF ls_result-fileext IS NOT INITIAL.
        " Construire le nom complet avec l'extension
        lv_filename_full = |{ ls_result-file_name }|.
      ELSE.
        " Pas d'extension, utiliser juste le nom
        lv_filename_full = ls_result-file_name.
      ENDIF.
      <lv_filename> = lv_filename_full.
    ENDIF.

    " FILEEXT (extension seule)
    ASSIGN COMPONENT 'FILEEXT' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_fileext>).
    IF <lv_fileext> IS ASSIGNED.
      <lv_fileext> = ls_result-fileext.
    ENDIF.

    " FILESIZE
    ASSIGN COMPONENT 'FILESIZE' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_filesize>).
    IF <lv_filesize> IS ASSIGNED.
      <lv_filesize> = ls_result-filesize.
    ENDIF.

    " MIME_TYPE
    ASSIGN COMPONENT 'MIME_TYPE' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_mime_type>).
    IF <lv_mime_type> IS ASSIGNED.
      <lv_mime_type> = ls_result-mime_type.
    ENDIF.

    " ARCHIVE_DOC_ID
    ASSIGN COMPONENT 'ARCHIVE_DOC_ID' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_archive_doc_id>).
    IF <lv_archive_doc_id> IS ASSIGNED.
      <lv_archive_doc_id> = ls_result-archive_doc_id.
    ENDIF.

    " CREATION_DATE
    ASSIGN COMPONENT 'CREATION_DATE' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_creation_date>).
    IF <lv_creation_date> IS ASSIGNED.
      <lv_creation_date> = ls_result-creation_date.
    ENDIF.

    " CREATION_TIME
    ASSIGN COMPONENT 'CREATION_TIME' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_creation_time>).
    IF <lv_creation_time> IS ASSIGNED.
      <lv_creation_time> = ls_result-creation_time.
    ENDIF.

    " CREATOR_PERNR
    ASSIGN COMPONENT 'CREATOR_PERNR' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_creator_pernr>).
    IF <lv_creator_pernr> IS ASSIGNED.
      <lv_creator_pernr> = ls_result-creator_pernr.
    ENDIF.

    " CREATOR_LNAME
    ASSIGN COMPONENT 'CREATOR_LNAME' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_creator_lname>).
    IF <lv_creator_lname> IS ASSIGNED.
      <lv_creator_lname> = ls_result-creator_lname.
    ENDIF.

    " CREATOR_FNAME
    ASSIGN COMPONENT 'CREATOR_FNAME' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_creator_fname>).
    IF <lv_creator_fname> IS ASSIGNED.
      <lv_creator_fname> = ls_result-creator_fname.
    ENDIF.

    " LAST_UPD_DATE
    ASSIGN COMPONENT 'LAST_UPD_DATE' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_last_upd_date>).
    IF <lv_last_upd_date> IS ASSIGNED.
      <lv_last_upd_date> = ls_result-last_upd_date.
    ENDIF.

    " LAST_UPD_TIME
    ASSIGN COMPONENT 'LAST_UPD_TIME' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_last_upd_time>).
    IF <lv_last_upd_time> IS ASSIGNED.
      <lv_last_upd_time> = ls_result-last_upd_time.
    ENDIF.

    " UPD_USR_ID
    ASSIGN COMPONENT 'UPD_USR_ID' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_upd_usr_id>).
    IF <lv_upd_usr_id> IS ASSIGNED.
      <lv_upd_usr_id> = ls_result-upd_usr_id.
    ENDIF.

    " UPD_PERNR
    ASSIGN COMPONENT 'UPD_PERNR' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_upd_pernr>).
    IF <lv_upd_pernr> IS ASSIGNED.
      <lv_upd_pernr> = ls_result-upd_pernr.
    ENDIF.

    " UPD_LNAME
    ASSIGN COMPONENT 'UPD_LNAME' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_upd_lname>).
    IF <lv_upd_lname> IS ASSIGNED.
      <lv_upd_lname> = ls_result-upd_lname.
    ENDIF.

    " UPD_FNAME
    ASSIGN COMPONENT 'UPD_FNAME' OF STRUCTURE <ls_entity> TO FIELD-SYMBOL(<lv_upd_fname>).
    IF <lv_upd_fname> IS ASSIGNED.
      <lv_upd_fname> = ls_result-upd_fname.
    ENDIF.

  ENDLOOP.

*--------------------------------------------------------------------
*" Fin de méthode
*" ET_ENTITYSET contient tous les documents associés au REQUEST_ID
*--------------------------------------------------------------------
ENDMETHOD.
