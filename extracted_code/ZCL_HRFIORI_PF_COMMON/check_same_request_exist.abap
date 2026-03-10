  METHOD check_same_request_exist.

    DATA: lv_obj_key       TYPE asr_object_key,
          lv_field_name_fn TYPE fieldname,
          lv_field_name_ln TYPE fieldname,
          lv_first_name	   TYPE pad_vorna,
          lv_last_name     TYPE pad_nachn,
          lv_field_value   TYPE asr_field_value,
          ls_process       TYPE t5asrprocesses,
          ls_field_value   TYPE hrasr00_values_of_field,
          lt_processes     TYPE STANDARD TABLE OF t5asrprocesses,
          lt_fields_value  TYPE hrasr00_values_of_field_tab.

    IF iv_field_name_fn IS NOT INITIAL.
      lv_field_name_fn = iv_field_name_fn.
    ENDIF.
    IF iv_field_name_ln IS NOT INITIAL.
      lv_field_name_ln = iv_field_name_ln.
    ENDIF.

    MOVE iv_pernr TO lv_obj_key.
*   get all on going requests for personnel number
    SELECT * INTO TABLE lt_processes
      FROM t5asrprocesses
        WHERE process =  iv_process
          AND ( status = 'DRAFT' OR
                status = 'STARTED' )
          AND object_key = lv_obj_key.

*   Check each request
    LOOP AT lt_processes INTO ls_process.
      CLEAR: lv_field_value, lv_first_name, lv_last_name.

*     Avoid the ongoing request
      IF iv_process_guid IS NOT INITIAL.
        CHECK ls_process-case_guid <> iv_process_guid.
      ENDIF.

      get_request_form_data(
        EXPORTING iv_process = iv_process
                  iv_process_guid = ls_process-case_guid
        IMPORTING ot_fields_value = lt_fields_value ).

      SORT lt_fields_value BY fieldname ASCENDING.

*     Get first name and last name
      READ TABLE lt_fields_value INTO ls_field_value WITH KEY fieldname = lv_field_name_fn.
      READ TABLE ls_field_value-fieldvalues INTO lv_field_value INDEX 1.
      MOVE lv_field_value TO lv_first_name.

      CLEAR: lv_field_value.
      READ TABLE lt_fields_value INTO ls_field_value WITH KEY fieldname = lv_field_name_ln.
      READ TABLE ls_field_value-fieldvalues INTO lv_field_value INDEX 1.
      MOVE lv_field_value TO lv_last_name.

*     all names in uppercase and remove strange characters for comparaison
      TRANSLATE lv_first_name TO UPPER CASE.
      TRANSLATE lv_last_name TO UPPER CASE.
      CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'
        EXPORTING
          intext  = lv_first_name
        IMPORTING
          outtext = lv_first_name.
      CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'
        EXPORTING
          intext  = lv_last_name
        IMPORTING
          outtext = lv_last_name.

*     Check if identical
      IF lv_first_name = iv_first_name  AND lv_last_name = iv_last_name.
        ov_request_exist = abap_true.
        EXIT.
      ENDIF.

    ENDLOOP.

  ENDMETHOD.
