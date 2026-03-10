METHOD get_mapped_versionid.

  DATA lc_clsname TYPE seoclsname VALUE 'CL_HR_T582MAPITVERS'.
  DATA lc_mdname TYPE seoclsname VALUE 'GET_MASTER_VERSIONID'.
  DATA lo_reader_object TYPE REF TO cl_oo_object.
  DATA lo_reader_class TYPE REF TO cl_oo_class.
  DATA lv_exists TYPE boole_d VALUE abap_true.
  DATA lv_class_name TYPE seoclsname.
  DATA lo_reader TYPE REF TO object.
  DATA lv_structure_name TYPE strukname.
  DATA lo_feeder TYPE REF TO cl_hcmfab_persinfo_feeder.

*Check if class cl_hr_t582mapitvers exists.
  TRY.
      CALL METHOD cl_oo_class=>get_instance
        EXPORTING
          clsname = lc_clsname
        RECEIVING
          result  = lo_reader_object.
    CATCH cx_class_not_existent.
      lv_exists = abap_false.
  ENDTRY.

  IF lv_exists <> abap_false.
    lo_reader_class ?= lo_reader_object.
    IF sy-subrc = 0.
      lv_class_name = lo_reader_class->class-clsname.
      CREATE OBJECT lo_reader TYPE (lv_class_name).
    ELSE.
      lv_exists = abap_false.
    ENDIF.
  ENDIF.

*Determine generic entry for master country version (if exists)
  IF iv_versionid IS NOT INITIAL AND lv_exists <> abap_false.

    CALL METHOD lo_reader->(lc_mdname)
      EXPORTING
        iv_versionid        = iv_versionid
      RECEIVING
        rv_master_versionid = rv_mapped_versionid.
  ENDIF.

  IF rv_mapped_versionid IS INITIAL.   "2904969
    IF iv_pernr IS SUPPLIED AND iv_infty IS SUPPLIED.
*When no Customizing is maintained in t582mapitvers, we use versionid from sname
      lo_feeder =  cl_hcmfab_persinfo_feeder=>get_instance(
          iv_pernr      = iv_pernr
          iv_infty      = iv_infty ).

      CALL METHOD lo_feeder->get_sname_using_versionid
        EXPORTING
          iv_versionid         = iv_versionid
        RECEIVING
          rv_ui_structure_name = lv_structure_name.

      CALL METHOD get_versionid_from_sname
        EXPORTING
          iv_ui_structure_name = lv_structure_name
        RECEIVING
          rv_versionid         = rv_mapped_versionid.

    ELSE.
*When no Customizing is maintained in t582mapitvers, we use default Version Id
      rv_mapped_versionid = iv_versionid.
    ENDIF.
  ENDIF.

ENDMETHOD.
