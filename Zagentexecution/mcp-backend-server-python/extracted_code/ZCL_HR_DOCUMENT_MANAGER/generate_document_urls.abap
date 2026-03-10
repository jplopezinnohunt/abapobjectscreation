METHOD generate_document_urls.
  DATA: lv_base_url      TYPE string,
        lv_safe_reqid    TYPE string,
        lv_safe_doctype  TYPE string.

  " ATTENTION: remplacer par la vraie URL de service ou générer dynamiquement si possible
  lv_base_url = '/sap/opu/odata/sap/ZHRF_OFFBOARD_SRV'.

  IF iv_request_id IS NOT INITIAL.
    lv_safe_reqid = iv_request_id.
    CONDENSE lv_safe_reqid NO-GAPS.
  ENDIF.

  IF iv_doc_type IS NOT INITIAL.
    lv_safe_doctype = iv_doc_type.
    CONDENSE lv_safe_doctype NO-GAPS.
  ENDIF.

  " Échapper quotes simples pour éviter l'injection d'URL
  REPLACE ALL OCCURRENCES OF '''' IN lv_safe_reqid WITH ''''''.
  REPLACE ALL OCCURRENCES OF '''' IN lv_safe_doctype WITH ''''''.

  ev_upload_url = |{ lv_base_url }/TOAATSet|.

  IF lv_safe_reqid IS NOT INITIAL AND lv_safe_doctype IS NOT INITIAL.
    ev_download_url = |{ lv_base_url }/TOAATSet(RequestId='{ lv_safe_reqid }',DocumentType='{ lv_safe_doctype }')/$value|.
  ELSE.
    CLEAR ev_download_url.
  ENDIF.
ENDMETHOD.
