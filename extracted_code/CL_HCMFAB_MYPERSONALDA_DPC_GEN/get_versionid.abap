  METHOD get_versionid.

    DATA lv_offset TYPE i.

    IF iv_entity_name CP '*#F#I*' ##no_text . "Function Import
      lv_offset = sy-fdpos + 2.
      rv_versionid = iv_entity_name+lv_offset(2).
    ELSEIF iv_entity_name CP '*ValueHelp*' ##no_text .
      lv_offset = sy-fdpos + 9.
      IF iv_entity_name+lv_offset(1) = '_'.
* we deal with a country-specific valuehelp like 'ValueHelp_10Comm'
        lv_offset = lv_offset + 1.
        rv_versionid = iv_entity_name+lv_offset(2).
      ELSE.
* we deal with a generic valuehelp like 'ValueHelpComm'
        rv_versionid = '99'.
      ENDIF.
    ELSEIF iv_entity_name CP '*PersonalData++' OR iv_entity_name CP '*PersonalData++Default'.
* sy-fdpos contains the offset of operand2 in operand1
      lv_offset = sy-fdpos + 12.
      rv_versionid = iv_entity_name+lv_offset(2).
    ELSEIF iv_entity_name = 'PersonalData'
      OR iv_entity_name CP '*PersonalData'
      OR iv_entity_name = 'PersonalDataDefault'
      OR iv_entity_name CP '*PersonalDataDefault'.
      rv_versionid = '99'.
    ENDIF.

  ENDMETHOD.
