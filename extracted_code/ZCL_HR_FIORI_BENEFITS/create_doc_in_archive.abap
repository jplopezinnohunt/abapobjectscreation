  METHOD create_doc_in_archive.

    DATA: lv_size_int     TYPE i,
          lv_size         TYPE num12,
          lv_file_name    TYPE toaat-filename,
          lv_arc_doc_id   TYPE saeardoid,
          lt_binary_table TYPE STANDARD TABLE OF tbl1024.

    ov_subrc = 0.

*   Preparation of data ----------------------------------------------------------
*   Get file name
    lv_file_name = iv_file_name.
*   Get file size
    lv_size_int = xstrlen( iv_content ).
    lv_size = lv_size_int.
    CONDENSE lv_size.

*   Conversion of file into  table
    CALL FUNCTION 'SCMS_XSTRING_TO_BINARY'
      EXPORTING
        buffer     = iv_content
      TABLES
        binary_tab = lt_binary_table.

*   Create file in archive -------------------------------------------------------
    CALL FUNCTION 'ARCHIVOBJECT_CREATE_TABLE'
      EXPORTING
        archiv_id                = iv_archive_id
        document_type            = iv_document_class
        length                   = lv_size
      IMPORTING
        archiv_doc_id            = lv_arc_doc_id
      TABLES
        binarchivobject          = lt_binary_table
      EXCEPTIONS
        error_archiv             = 1
        error_communicationtable = 2
        error_kernel             = 3
        blocked_by_policy        = 4
        OTHERS                   = 5.

    ov_subrc = sy-subrc.
    IF ov_subrc <> 0.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '031'
        WITH ov_subrc INTO ov_message.
      RETURN.
    ENDIF.

    ov_arch_doc_id = lv_arc_doc_id.

*   Create connection ArchiveLink----------------------------------------------------
    CALL FUNCTION 'ARCHIV_CONNECTION_INSERT'
      EXPORTING
        archiv_id             = iv_archive_id
        arc_doc_id            = lv_arc_doc_id
        ar_object             = iv_ar_object
        object_id             = iv_object_id
        sap_object            = iv_sap_object
        doc_type              = iv_document_class
        filename              = lv_file_name
      EXCEPTIONS
        error_connectiontable = 1
        OTHERS                = 2.

    ov_subrc = sy-subrc.
    IF ov_subrc <> 0.
      MESSAGE ID 'ZHRFIORI' TYPE 'E' NUMBER '032'
        WITH ov_subrc INTO ov_message.
      ROLLBACK WORK.
      RETURN.
    ENDIF.

    COMMIT WORK.

  ENDMETHOD.
