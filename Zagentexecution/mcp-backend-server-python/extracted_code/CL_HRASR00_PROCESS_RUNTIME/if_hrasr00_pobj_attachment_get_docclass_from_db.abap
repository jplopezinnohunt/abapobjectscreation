METHOD if_hrasr00_pobj_attachment~get_docclass_from_db.
  DATA : lw_logical_key TYPE pobjs_doc_key,
         lw_physical_key TYPE pobjs_physical_doc_key.
   DATA exception_obj TYPE REF TO cx_root.

try.
******* With the New POBJ Framework, derive the Physical Guid by the given Logical guid of the document.
  MOVE document_id TO lw_logical_key-logical_guid.
  MOVE '1'  TO lw_logical_key-logical_version.
  CALL METHOD cl_pobj_case=>get_doc_phkey_for_lokey
    EXPORTING
      logical_key  = lw_logical_key
    IMPORTING
      physical_key = lw_physical_key.

  SELECT SINGLE class FROM t5asrdocuments INTO document_class
    WHERE guid = lw_physical_key-guid.
  IF sy-subrc NE 0.
    CLEAR document_class.
  ENDIF.
  CATCH cx_root INTO exception_obj.
    CLEAR document_class.
    RETURN.
  ENDTRY.
ENDMETHOD.
