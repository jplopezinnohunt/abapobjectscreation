  METHOD get_archive_doc_type.

    SELECT SINGLE archive_doc_type INTO ov_archive_doc_type
      FROM zthrfiori_att_ty
        where attach_type = iv_attachment_type ##WARN_OK.

*    CASE iv_attachment_type.
*      WHEN '001'.
*        ov_archive_doc_type = c_archive_doc_type01.
*      WHEN '002'.
*        ov_archive_doc_type = c_archive_doc_type02.
*      WHEN '003'.
*        ov_archive_doc_type = c_archive_doc_type01.
*      WHEN '004'.
*        ov_archive_doc_type = c_archive_doc_type04.
*      WHEN '005'.
*        ov_archive_doc_type = c_archive_doc_type05.
*      WHEN '006'.
*        ov_archive_doc_type = c_archive_doc_type06.
*      WHEN '007'.
*        ov_archive_doc_type = c_archive_doc_type07.
*      WHEN '008'.
*        ov_archive_doc_type = c_archive_doc_type08.
*      WHEN '009'.
*        ov_archive_doc_type = c_archive_doc_type09.
*      WHEN '010'.
*        ov_archive_doc_type = c_archive_doc_type10.
*      WHEN '011'.
*        ov_archive_doc_type = c_archive_doc_type11.
*      WHEN '012'.
*        ov_archive_doc_type = c_archive_doc_type12.
*    ENDCASE.

  ENDMETHOD.
