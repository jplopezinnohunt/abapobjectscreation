METHOD is_delete_allowed.
* This method is (partly) copied from CL_HRPA_PERNR_INFTY_XSS;
* This is necessary as WDA ESS locks the PERNR when launched
* In the stateless context of Fiori this may fail because of several parallel (asynchronuos) requests
* In case the PERNR isn't locked property 'IS_DELETABLE' won't be evaluated
  DATA lt_subty_metadata TYPE if_hrpa_pernr_infty_xss=>subty_metadata_tab.
  DATA lr_ui_structure_tab TYPE REF TO data.
  DATA lv_unkey TYPE hcmt_bsp_pad_unkey.
  DATA ls_pskey TYPE pskey.
  DATA lv_subty_count TYPE i.

  FIELD-SYMBOLS <ls_subty_metadata> LIKE LINE OF lt_subty_metadata.
  FIELD-SYMBOLS <lt_ui_structure> TYPE ANY TABLE.
  FIELD-SYMBOLS <ls_ui_structure> TYPE any.
  FIELD-SYMBOLS <lv_object_key> TYPE hcm_object_key.

  TRY.
      CALL METHOD mo_xss_adapter->read_metadata
        IMPORTING
          metadata_tab = lt_subty_metadata.
*         country       =
*         default_begda = lv_default_begda.
*         today         =
*          messages      = lt_messages.

      CREATE DATA lr_ui_structure_tab TYPE TABLE OF (me->mv_xx_structure_name).
      ASSIGN lr_ui_structure_tab->* TO <lt_ui_structure>.

      CALL METHOD mo_xss_adapter->if_hrpa_pernr_infty_xss_ext~get_all_data
        IMPORTING
          main_records = <lt_ui_structure>.

* calculate amount of <subty>-records
      LOOP AT <lt_ui_structure> ASSIGNING <ls_ui_structure>.
        ASSIGN COMPONENT gc_fname-object_key OF STRUCTURE <ls_ui_structure> TO <lv_object_key>.
        go_tuid_mapper->read_mapping( EXPORTING tuid = <lv_object_key>
                                      IMPORTING unkey = lv_unkey ).
        ls_pskey = lv_unkey.
        IF ls_pskey-subty = is_pskey-hcmfab_subty.
          lv_subty_count = lv_subty_count + 1.
        ENDIF.

      ENDLOOP.

    CATCH cx_hrpa_violated_assertion.
      CLEAR lt_subty_metadata.
  ENDTRY.

  READ TABLE lt_subty_metadata WITH TABLE KEY subty = is_pskey-hcmfab_subty ASSIGNING <ls_subty_metadata>.
  IF sy-subrc EQ 0.
    rv_delete_allowed = abap_true.  " Following Logic Same as Java FcPersInfo.hasDeleteButtonCustomizedOverview

    IF <ls_subty_metadata>-case = 'B1' OR <ls_subty_metadata>-case = 'B4' OR <ls_subty_metadata>-case = 'A1' OR <ls_subty_metadata>-case = 'A4'.

      IF is_pskey-hcmfab_begda <= <ls_subty_metadata>-default_begda OR lv_subty_count = 1 . "IM 3665709/2009 A1 was deletable

        rv_delete_allowed = abap_false.

      ELSEIF  ( <ls_subty_metadata>-case = 'B1' OR <ls_subty_metadata>-case = 'B4' )
          AND   <ls_subty_metadata>-default_begda < me->mv_user_today
          AND ( is_pskey-hcmfab_begda <= me->mv_user_today AND is_pskey-hcmfab_endda >= me->mv_user_today ).        "Record spans over today

        rv_delete_allowed = abap_false.

      ENDIF.
    ENDIF.
  ENDIF.

ENDMETHOD.
