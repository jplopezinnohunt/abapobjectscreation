  METHOD if_ex_hcmfab_persinfo_config~get_screen_versions.
*    ct_ui_screens
    CHECK iv_app_id = 'MYADDRESSES'.
    LOOP AT ct_ui_screens ASSIGNING FIELD-SYMBOL(<lfs_screen>).
      <lfs_screen>-display_screen = '99_Display_Default_V001'.
      <lfs_screen>-edit_screen = 	'99_Edit_Default_V001'.

    ENDLOOP.
  ENDMETHOD.
