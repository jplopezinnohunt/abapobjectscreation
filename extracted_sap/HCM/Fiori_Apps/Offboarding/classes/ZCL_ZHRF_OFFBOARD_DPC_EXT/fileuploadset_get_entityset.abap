METHOD fileuploadset_get_entityset.

*  DATA: lt_documents TYPE ztt_document_entity,
*        ls_document  TYPE zstr_document_entity,
*        lv_requestid TYPE SAEARDOID,
*        lo_manager   TYPE REF TO zcl_hr_document_manager.
*
*  CLEAR et_entityset.
*
*  "--------------------------------------------------------
*  " 1. Extraire l'ID de la demande depuis filtres ou clés
*  "--------------------------------------------------------
*  IF it_filter_select_options IS NOT INITIAL.
*    READ TABLE it_filter_select_options ASSIGNING FIELD-SYMBOL(<fs_so>)
*      WITH KEY property = 'ID'.
*    IF sy-subrc = 0.
*      lv_requestid = <fs_so>-select_options[ 1 ]-low.
*    ENDIF.
*  ENDIF.
*
*  IF it_key_tab IS NOT INITIAL.
*    LOOP AT it_key_tab ASSIGNING FIELD-SYMBOL(<fs_keys>).
*      CASE <fs_keys>-name.
*        WHEN 'ID'.
*          lv_requestid = <fs_keys>-value.
*      ENDCASE.
*    ENDLOOP.
*  ENDIF.
*
*  "--------------------------------------------------------
*  " 2. Récupérer l'instance singleton du manager
*  "--------------------------------------------------------
*  lo_manager = zcl_hr_document_manager=>get_instance( ).
*
*  "--------------------------------------------------------
*  " 3. Récupérer la liste des documents via la méthode list_files
*  "--------------------------------------------------------
*  IF lv_requestid IS NOT INITIAL.
*    CALL METHOD lo_manager->list_files
*      EXPORTING
*        iv_request_id = lv_requestid
*      RECEIVING
*        rt_files      = lt_documents.
*  ENDIF.
*
*  "--------------------------------------------------------
*  " 4. Copier les documents dans et_entityset pour OData
*  "--------------------------------------------------------
*  LOOP AT lt_documents INTO ls_document.
*    APPEND ls_document TO et_entityset.
*  ENDLOOP.

ENDMETHOD.
