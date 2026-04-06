  METHOD delete_doc_in_archive.

    DATA: ls_source TYPE toav0,
          ls_target TYPE toav0,
          ls_toahr  TYPE toahr.

**   Get information on document
*    SELECT SINGLE * INTO ls_toahr
*      FROM toahr
*        WHERE arc_doc_id = iv_arch_doc_id
*          AND archiv_id = iv_archive_id
*          AND sap_object = iv_sap_object ##WARN_OK.
*    MOVE-CORRESPONDING ls_toahr TO ls_source.
*    MOVE-CORRESPONDING ls_toahr TO ls_target.
*
*    ls_target-del_date = sy-datum.
*
**   Delete connection to archiveLink
*    CALL FUNCTION 'ARCHIV_CONNECTION_UPDATE'
*      EXPORTING
*        source                = ls_source
*        target                = ls_target
*      EXCEPTIONS
*        error_connectiontable = 1
*        error_parameter       = 2
*        OTHERS                = 3.
*
*    ov_subrc = sy-subrc.
*    IF ov_subrc <> 0.
*      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '034'
*        WITH ov_subrc INTO ov_message.
*      RETURN.
*    ENDIF.

*   Delete technical tables
    DELETE FROM toahr WHERE arc_doc_id = iv_arch_doc_id.
    DELETE FROM toaat WHERE arc_doc_id = iv_arch_doc_id.

    COMMIT WORK.

*   Delete document in  archive
    CALL FUNCTION 'ARCHIVOBJECT_DELETE'
      EXPORTING
        archiv_id                = iv_archive_id
        archiv_doc_id            = iv_arch_doc_id
      EXCEPTIONS
        error_archiv             = 1
        error_communicationtable = 2
        error_kernel             = 3
        OTHERS                   = 4.

    ov_subrc = sy-subrc.
    IF ov_subrc <> 0.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '035'
        WITH ov_subrc INTO ov_message.
    ENDIF.

  ENDMETHOD.
