METHOD if_hrasr00_pobj_attachment~get_phy_for_log_doc_id.
  DATA lw_logical_key TYPE pobjs_doc_key.
  DATA lw_physical_key TYPE pobjs_physical_doc_key.
  DATA exception_obj TYPE REF TO cx_root.
  TRY.
      MOVE logical_doc_id TO lw_logical_key-logical_guid.
      MOVE '1'  TO lw_logical_key-logical_version.
      CALL METHOD cl_pobj_case=>get_doc_phkey_for_lokey
        EXPORTING
          logical_key  = lw_logical_key
        IMPORTING
          physical_key = lw_physical_key.
      physical_doc_id = lw_physical_key-guid.
    CATCH cx_root INTO exception_obj.
      CLEAR physical_doc_id.
      RETURN.
  ENDTRY.
ENDMETHOD.
