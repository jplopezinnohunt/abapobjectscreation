  METHOD update_doc_in_archive.

    DATA: lv_subrc       TYPE syst_subrc,
          lv_msg         TYPE string ##NEEDED,
          lv_arch_doc_id TYPE saeardoid.
*          lv_file_name   TYPE char_lg_60.
*          lv_size        TYPE num12,
*          lv_size_int    TYPE i,
*          lv_doc_type    TYPE saedoktyp,
*          lt_bin         TYPE STANDARD TABLE OF tbl1024.


*   Update file in archive
*   Standard FM doesn't work.
*   Solution: delete document, create new one

**   Get SAP document type from MIME
*    get_doc_type_by_mime_type( EXPORTING iv_mime_type = iv_mime_type
*                               IMPORTING ov_doc_type = lv_doc_type ).

**   Conversion of file into  table
*    CALL FUNCTION 'SCMS_XSTRING_TO_BINARY'
*      EXPORTING
*        buffer     = iv_content
*      TABLES
*        binary_tab = lt_bin.
**   Set file name
*    lv_file_name = iv_file_name.
*
**   Get file size
*    lv_size_int = xstrlen( iv_content ).
*    lv_size = lv_size_int.

*    CALL FUNCTION 'ARCHIVOBJECT_UPDATE'
*      EXPORTING
*        archive_id      = iv_archive_id
*        archivedoc_id   = iv_arch_doc_id
*        documentclass   = lv_doc_type
*        length          = lv_size
*        compid          = lv_file_name
*      TABLES
*        binarchivobject = lt_bin
*      EXCEPTIONS
*        error_archiv    = 1
*        OTHERS          = 2.
*    ov_subrc = sy-subrc.
    delete_doc_in_archive( EXPORTING iv_arch_doc_id = iv_arch_doc_id
                                     iv_archive_id  = c_inboarding_archive_id
                                     iv_sap_object =  c_inboarding_sap_object
                           IMPORTING ov_subrc = lv_subrc
                                     ov_message = lv_msg ).

    IF lv_subrc <> 0.
      ov_subrc = lv_subrc.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '033'
        WITH lv_subrc INTO ov_message.
      RETURN.
    ENDIF.

    create_doc_in_archive( EXPORTING iv_file_name = iv_file_name
                                     iv_content = iv_content
                                     iv_archive_id = c_inboarding_archive_id
                                     iv_sap_object = c_inboarding_sap_object
                                     iv_ar_object = iv_ar_object
                                     iv_object_id = iv_object_id
                                     iv_document_class = iv_document_class
                           IMPORTING ov_arch_doc_id = lv_arch_doc_id
                                     ov_subrc = lv_subrc
                                     ov_message = lv_msg  ).

    IF lv_subrc <> 0.
      ov_subrc = lv_subrc.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '033'
        WITH lv_subrc INTO ov_message.
      RETURN.
    ENDIF.

    ov_arch_doc_id = lv_arch_doc_id.

  ENDMETHOD.
