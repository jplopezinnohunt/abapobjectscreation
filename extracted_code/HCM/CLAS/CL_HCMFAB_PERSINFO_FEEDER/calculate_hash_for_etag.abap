METHOD calculate_hash_for_etag.

  DATA lv_ui_structure_xstr TYPE xstring.

  FIELD-SYMBOLS <lv_etag> TYPE hash160.

  CHECK NOT cs_entity_main IS INITIAL.

  ASSIGN COMPONENT 'PERS_INFO_ETAG' OF STRUCTURE cs_entity_main TO <lv_etag>.

  IF <lv_etag> IS ASSIGNED.

    EXPORT id = is_ui_record TO DATA BUFFER lv_ui_structure_xstr.
    CALL FUNCTION 'CALCULATE_HASH_FOR_RAW'
      EXPORTING
        data           = lv_ui_structure_xstr
      IMPORTING
        hash           = <lv_etag>
      EXCEPTIONS
        unknown_alg    = 1
        param_error    = 2
        internal_error = 3
        OTHERS         = 4.

    IF sy-subrc <> 0.
* Implement suitable error handling here
    ENDIF.

  ENDIF.

ENDMETHOD.
