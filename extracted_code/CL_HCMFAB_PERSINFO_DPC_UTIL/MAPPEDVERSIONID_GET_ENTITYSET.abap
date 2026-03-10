METHOD MAPPEDVERSIONID_GET_ENTITYSET.
  DATA: ls_entity                TYPE hcmfab_s_pers_custz_vi,
        lv_infty                 TYPE hcmfab_application_id,
        lv_master_versionid      TYPE hcmfab_versionid,
        lv_versionid             TYPE hcmfab_versionid,
        lx_exception             TYPE REF TO cx_static_check,
        ls_filter                TYPE /iwbep/s_mgw_select_option,
        ls_select                TYPE /iwbep/s_cod_select_option,
        lt_filter_select_options TYPE /iwbep/t_mgw_select_option,
        lo_filter                TYPE REF TO /iwbep/if_mgw_req_filter.

  DATA: lo_super_object      TYPE REF TO cl_oo_object,
        lo_super_class       TYPE REF TO cl_oo_class,
        lv_result_class_name TYPE seoclsname,
        lo_ref_result        TYPE REF TO object,
        lc_clsname           TYPE seoclsname VALUE 'CL_HR_T582MAPITVERS',
        lc_mdname            TYPE seoclsname VALUE 'GET_MASTER_VERSIONID',
        lv_t582mapitvers     TYPE abap_bool VALUE abap_true.

  DATA: ls_t7xssreuseuisn TYPE t7xssreuseuisn,
        lv_offset      TYPE i,
        lv_name        TYPE string,
        lv_countrykey  TYPE intca,
        ls_t500l       TYPE t500l.

  lo_filter = io_tech_request_context->get_filter( ).
  lt_filter_select_options = lo_filter->get_filter_select_options( ).

  LOOP AT lt_filter_select_options INTO ls_filter.
    READ TABLE ls_filter-select_options INTO ls_select INDEX 1 TRANSPORTING low.
    CASE ls_filter-property.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-hcmfab_infty.
        lv_infty = ls_select-low.
      WHEN cl_hcmfab_persinfo_feeder=>gc_fname-versionid.
        lv_versionid = ls_select-low.
    ENDCASE.
  ENDLOOP.

*Check if class cl_hr_t582mapitvers exists.

  TRY.
      CALL METHOD cl_oo_class=>get_instance
        EXPORTING
          clsname = lc_clsname
        RECEIVING
          result  = lo_super_object.
    CATCH cx_class_not_existent.
      lv_t582mapitvers = abap_false.
  ENDTRY.

  IF lv_t582mapitvers <> abap_false.
    lo_super_class ?= lo_super_object.
    IF sy-subrc = 0.
      lv_result_class_name = lo_super_class->class-clsname.
      CREATE OBJECT lo_ref_result TYPE (lv_result_class_name).
    ELSE.
      lv_t582mapitvers = abap_false.
    ENDIF.
  ENDIF.

*Determine generic entry for master country version (if exists)
    IF lv_versionid IS NOT INITIAL AND lv_t582mapitvers <> abap_false.
*    lv_master_versionid = cl_hr_t582mapitvers=>get_master_versionid( lv_itvers ).
      CALL METHOD lo_ref_result->(lc_mdname)
        EXPORTING
          iv_versionid        = lv_versionid
        RECEIVING
          rv_master_versionid = lv_master_versionid.
    ENDIF.

    IF lv_master_versionid IS INITIAL.
*When no Customizing is maintained in t582mapitvers, we use default Version Id
      lv_master_versionid = lv_versionid.
    ENDIF.

    SELECT * FROM t7xssreuseuisn INTO ls_t7xssreuseuisn UP TO 1 ROWS "#EC CI_GENBUFF
             WHERE                                    "#EC CI_SGLSELECT
             infty     = lv_infty  AND
             stype     = 'MAIN' AND
             versionid = lv_master_versionid.
    ENDSELECT.

    IF sy-subrc = 0 AND ls_t7xssreuseuisn-sname IS NOT INITIAL.
      lv_name = ls_t7xssreuseuisn-sname.
      IF lv_name CP '*HCMT_BSP_PA*' ##no_text .
        lv_offset = sy-fdpos + 11.
        IF lv_name+lv_offset(1) = '_'.
*we get the Country Key from HCMP_BSP_PA* Structure
          lv_offset = lv_offset + 1.
          lv_countrykey = lv_name+lv_offset(2).
*we get Version Id using Country Key
          SELECT * FROM t500l INTO ls_t500l UP TO 1 ROWS
                   WHERE intca = lv_countrykey.
          ENDSELECT.
          IF sy-subrc = 0.
            lv_master_versionid = ls_t500l-molga.
          ELSE.
            lv_master_versionid = '99'.
          ENDIF.
        ENDIF.
      ENDIF.
    ENDIF.

    ls_entity-hcmfab_infty = lv_infty.
    ls_entity-versionid = lv_versionid.
    ls_entity-mapped_version_id = lv_master_versionid.

    APPEND ls_entity TO et_entityset.
ENDMETHOD.
