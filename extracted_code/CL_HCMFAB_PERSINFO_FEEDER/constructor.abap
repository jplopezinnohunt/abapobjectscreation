METHOD constructor.

  mv_infty = iv_infty.
  mv_pernr = iv_pernr.

  IF iv_user_today IS INITIAL.
    mv_user_today = sy-datlo.
  ELSE.
    mv_user_today = iv_user_today.
  ENDIF.

  CALL METHOD cl_hrpa_pernr_infty_xss=>get_instance
    EXPORTING
      pernr    = mv_pernr
      infty    = mv_infty
      userdate = mv_user_today
      iv_bol   = abap_false
    RECEIVING
      instance = mo_xss_adapter.

  mv_xx_structure_name = get_sname_using_versionid( iv_versionid = gc_versionid_xx ).

  IF mv_xx_structure_name IS INITIAL.                       "2709841
* this might be the case for country-specific Infotypes where no international IT-version is available
    mv_xx_structure_name = get_sname_using_versionid( iv_versionid = get_default_versionid( ) ).
  ENDIF.

ENDMETHOD.
