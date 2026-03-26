  METHOD get_doc_from_archive.

    DATA: lv_document_class  TYPE saedoktyp,
          lv_length          TYPE num12,
          lv_length_int      TYPE i,
          lt_binarchivobject TYPE STANDARD TABLE OF tbl1024.

*   Get SAP document type from MIME
    get_doc_type_by_mime_type( EXPORTING iv_mime_type = iv_mime_type
                               IMPORTING ov_doc_type = lv_document_class ).

*   Get file from archive
    CALL FUNCTION 'ARCHIVOBJECT_GET_TABLE'
      EXPORTING
        archiv_id                = iv_archive_id
        archiv_doc_id            = iv_arch_doc_id
        document_type            = lv_document_class
      IMPORTING
        length                   = lv_length
      TABLES
        binarchivobject          = lt_binarchivobject
      EXCEPTIONS
        error_archiv             = 1
        error_communicationtable = 2
        error_kernel             = 3
        OTHERS                   = 4 ##FM_SUBRC_OK.

*   Convert to xstring
    IF lt_binarchivobject[] IS  NOT INITIAL.
      lv_length_int = lv_length.
      CALL FUNCTION 'SCMS_BINARY_TO_XSTRING'
        EXPORTING
          input_length = lv_length_int
        IMPORTING
          buffer       = ov_content
        TABLES
          binary_tab   = lt_binarchivobject.
    ENDIF.

  ENDMETHOD.
