METHOD delete_file.

  DATA: lv_archiv_id      TYPE saearchivi,
        lv_error_text     TYPE string,
        lv_existing_doc   TYPE toahr-arc_doc_id ##NEEDED,
        lt_return         TYPE bapirettab,
        lwa_return        TYPE bapiret2,
        lv_deleted_custom TYPE i,
        lv_deleted_toahr  TYPE i ##NEEDED,
        lv_deleted_toaat  TYPE i,
        lv_subrc          TYPE sy-subrc.

  " ─────────────────────────────────────────────────────────────
  " 1. Initialisation
  " ─────────────────────────────────────────────────────────────
  CLEAR: ev_message, ev_success.
  ev_success = abap_false.

  " ─────────────────────────────────────────────────────────────
  " 2. Validation du paramètre
  " ─────────────────────────────────────────────────────────────
  IF iv_arc_doc_id IS INITIAL.
*    ev_message = 'Missing mandatory parameter: ARC_DOC_ID'.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '082'
      INTO ev_message.
    RETURN.
  ENDIF.

  " ─────────────────────────────────────────────────────────────
  " 3. Récupération de l'Archive ID depuis les constantes
  " ─────────────────────────────────────────────────────────────
  lv_archiv_id = gc_archives-archive_id.  " Ex: 'A2'

  IF lv_archiv_id IS INITIAL.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '083'
      INTO ev_message.
    RETURN.
  ENDIF.

  " ─────────────────────────────────────────────────────────────
  " 4. Vérifier l'existence du document dans TOAHR
  " ─────────────────────────────────────────────────────────────
  SELECT SINGLE arc_doc_id
    FROM toahr
    INTO @lv_existing_doc
    WHERE arc_doc_id = @iv_arc_doc_id ##WARN_OK.

  IF sy-subrc <> 0.
    MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '084'
      INTO ev_message WITH iv_arc_doc_id.
    RETURN.
  ENDIF.

  " ─────────────────────────────────────────────────────────────
  " 5. Appel de la fonction de suppression SAP ArchiveLink
  " ─────────────────────────────────────────────────────────────
  CALL FUNCTION 'ARCHIVOBJECT_DELETE'
    EXPORTING
      archiv_id                = lv_archiv_id
      archiv_doc_id            = iv_arc_doc_id
*    TABLES
*     return_tab               = lt_return
    EXCEPTIONS
      error_archiv             = 1
      error_communicationtable = 2
      error_kernel             = 3
      OTHERS                   = 4.

  lv_subrc = sy-subrc.

  " ─────────────────────────────────────────────────────────────
  " 6. Analyse du résultat
  " ─────────────────────────────────────────────────────────────
  CASE lv_subrc.
    WHEN 0.
      "  Succès
      ev_success = abap_true.

      " Supprimer les références dans les tables métadonnées
      DELETE FROM zthrfiori_attac WHERE archive_doc_id = @iv_arc_doc_id.
      lv_deleted_custom = sy-dbcnt.

      DELETE FROM toahr WHERE arc_doc_id = @iv_arc_doc_id.
      lv_deleted_toahr = sy-dbcnt.

      DELETE FROM toaat WHERE arc_doc_id = @iv_arc_doc_id.
      lv_deleted_toaat = sy-dbcnt.

      " Commit des modifications
      COMMIT WORK AND WAIT.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '085'
        INTO DATA(lv_str1) WITH iv_arc_doc_id.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '086'
        INTO DATA(lv_str2) WITH lv_deleted_custom lv_deleted_custom lv_deleted_toaat.
      CONCATENATE lv_str1 lv_str2 INTO ev_message.

    WHEN 1.
*      lv_error_text = 'Archive system error (error_archiv)'.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '087'
        INTO lv_error_text.
    WHEN 2.
*      lv_error_text = 'Communication table error (error_communicationtable)'.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '088'
        INTO lv_error_text.
    WHEN 3.
*      lv_error_text = 'SAP kernel error (error_kernel)'.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '089'
        INTO lv_error_text.
    WHEN OTHERS.
*      lv_error_text = 'Unknown error during deletion'.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '090'
        INTO lv_error_text.
  ENDCASE.

  " ─────────────────────────────────────────────────────────────
  " 7. En cas d'échec : construire le message d'erreur détaillé
  " ─────────────────────────────────────────────────────────────
  IF ev_success = abap_false.
    ev_message = |{ lv_error_text } (sy-subrc: { lv_subrc })|.

    " Ajouter les messages de la table RETURN si disponibles
    IF lt_return IS NOT INITIAL.
      LOOP AT lt_return INTO lwa_return WHERE type CA 'EAX'.  " Erreurs et Warnings
        ev_message = |{ ev_message } / { lwa_return-message }|.
      ENDLOOP.
    ENDIF.

    " Log pour debug (optionnel)
*    WRITE: / ' DELETE_FILE ERROR:', ev_message.
  ELSE.
    " Log succès (optionnel)
*    WRITE: / ' DELETE_FILE SUCCESS:', ev_message.
  ENDIF.

ENDMETHOD.
