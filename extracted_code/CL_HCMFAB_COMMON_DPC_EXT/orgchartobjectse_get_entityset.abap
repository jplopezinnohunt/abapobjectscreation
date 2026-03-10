METHOD orgchartobjectse_get_entityset.


  DATA lv_regex TYPE string.
  DATA lt_result TYPE match_result_tab.
  DATA ls_result TYPE match_result.
  DATA ls_submatch1 TYPE submatch_result.
  DATA ls_submatch3 TYPE submatch_result.
  DATA lv_filter_name TYPE string.
  DATA lv_application_id TYPE hcmfab_application_id.
  DATA lv_object_id TYPE realo.
  DATA lv_object_type TYPE otype.
  DATA lo_badi_orgchart_settings TYPE REF TO hcmfab_b_orgchart_settings.
  DATA ls_root_object TYPE hcmfab_s_oc_orgchart_object.
  DATA lt_messages TYPE bapiret2_tab.
  DATA ls_message TYPE bapiret2.

* get the filter paramters from filter string
  lv_regex = '\(\s(\w+)\s(\w+)\s.(\w+).\s\)'.
  FIND ALL OCCURRENCES OF REGEX lv_regex IN iv_filter_string RESULTS lt_result.
  LOOP AT lt_result INTO ls_result.
    READ TABLE ls_result-submatches INDEX 1 INTO ls_submatch1.
    READ TABLE ls_result-submatches INDEX 3 INTO ls_submatch3.
    lv_filter_name = iv_filter_string+ls_submatch1-offset(ls_submatch1-length).
    CASE lv_filter_name.
      WHEN 'ApplicationId'.
        lv_application_id = iv_filter_string+ls_submatch3-offset(ls_submatch3-length).
      WHEN 'ObjectId' OR 'ParentObjectId'.
        lv_object_id = iv_filter_string+ls_submatch3-offset(ls_submatch3-length).
      WHEN 'ObjectType' OR 'ParentObjectType'.
        lv_object_type = iv_filter_string+ls_submatch3-offset(ls_submatch3-length).
    ENDCASE.
  ENDLOOP.

* get the settings BADI
  TRY.
      GET BADI lo_badi_orgchart_settings.
    CATCH cx_badi.
      CLEAR lo_badi_orgchart_settings.
  ENDTRY.

* get the subordinated objects
  CALL BADI lo_badi_orgchart_settings->get_child_objects
    EXPORTING
      iv_root_object_type = lv_object_type
      iv_root_object_id   = lv_object_id
      iv_application_id   = lv_application_id
    IMPORTING
      et_child_objects    = et_entityset
      et_messages         = lt_messages.
  IF lt_messages IS NOT INITIAL.
    READ TABLE lt_messages INTO ls_message INDEX 1.
    cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = ls_message
                iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDIF.

* add the root node as first object
  CALL BADI lo_badi_orgchart_settings->get_root_object
    EXPORTING
      iv_root_object_type = lv_object_type
      iv_root_object_id   = lv_object_id
      iv_application_id   = lv_application_id
    IMPORTING
      es_root_object      = ls_root_object
      et_messages         = lt_messages.
  IF lt_messages IS NOT INITIAL.
    READ TABLE lt_messages INTO ls_message INDEX 1.
    cl_hcmfab_utilities=>raise_gateway_error(
                is_message  = ls_message
                iv_entity   = io_tech_request_context->get_entity_type_name( )
      ).
  ENDIF.

  ls_root_object-num_children = lines( et_entityset ).
  INSERT ls_root_object INTO et_entityset INDEX 1.
ENDMETHOD.
