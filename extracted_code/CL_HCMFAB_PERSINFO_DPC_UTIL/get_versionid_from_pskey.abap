METHOD get_versionid_from_pskey.

  DATA lr_pnnnn TYPE REF TO data.
  DATA lv_structure_name TYPE strukname.

  FIELD-SYMBOLS <lt_pnnnn> TYPE STANDARD TABLE.
  FIELD-SYMBOLS <ls_pnnnn> TYPE any.
  FIELD-SYMBOLS <lv_itbld> TYPE itbld.

  IF is_pskey IS INITIAL.
    RETURN.
  ENDIF.

  CONCATENATE 'P' is_pskey-hcmfab_infty INTO lv_structure_name.

  CREATE DATA lr_pnnnn TYPE TABLE OF (lv_structure_name).
  ASSIGN lr_pnnnn->* TO <lt_pnnnn>.

  TRY.
      CALL METHOD go_paitf_reader->if_hrpa_paitf_read~read
        EXPORTING
          tclas         = 'A'
          pernr         = is_pskey-hcmfab_pernr
          infty         = is_pskey-hcmfab_infty
          subty         = is_pskey-hcmfab_subty
          objps         = is_pskey-hcmfab_objps
          sprps         = is_pskey-hcmfab_sprps
          begda         = is_pskey-hcmfab_begda
          endda         = is_pskey-hcmfab_endda
          seqnr         = is_pskey-hcmfab_seqnr
          no_auth_check = abap_true
        IMPORTING
          pnnnn_tab     = <lt_pnnnn>.
    CATCH cx_hrpa_violated_assertion .
      CLEAR <lt_pnnnn>.
  ENDTRY.

  IF <lt_pnnnn> IS ASSIGNED.
    READ TABLE <lt_pnnnn> INDEX 1 ASSIGNING <ls_pnnnn>.
    IF sy-subrc EQ 0.
      ASSIGN COMPONENT cl_hcmfab_persinfo_feeder=>gc_fname-itbld OF STRUCTURE <ls_pnnnn> TO <lv_itbld>.
      IF <lv_itbld> IS ASSIGNED AND NOT <lv_itbld> IS INITIAL.
        rv_versionid = <lv_itbld>.
        RETURN.
      ENDIF.
    ENDIF.
  ENDIF.

  IF rv_versionid IS INITIAL.
    rv_versionid = cl_hcmfab_persinfo_feeder=>get_molga_of_pernr( is_pskey-hcmfab_pernr ).
  ENDIF.

ENDMETHOD.
