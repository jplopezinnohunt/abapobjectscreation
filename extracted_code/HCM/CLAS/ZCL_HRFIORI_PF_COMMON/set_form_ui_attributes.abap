  METHOD set_form_ui_attributes.

    DATA: lv_fieldname    TYPE hrasr_fieldname,
          ls_ui_visibilty TYPE zthrfioform_visi,
          lt_ui_visibilty TYPE STANDARD TABLE OF zthrfioform_visi.

    SELECT * INTO TABLE lt_ui_visibilty
      FROM zthrfioform_visi
        WHERE asr_form_scenario = iv_form_scenario
          AND step = iv_step.
    SORT lt_ui_visibilty BY step ASCENDING fieldname ASCENDING.

*   UI visibility for BADI method IF_HRASR00GEN_SERVICE~INITIALIZE
    IF ct_ui_visibility[] IS NOT INITIAL.
      LOOP AT ct_ui_visibility ASSIGNING FIELD-SYMBOL(<fs_record>).
        CLEAR: ls_ui_visibilty, lv_fieldname.

        READ TABLE lt_ui_visibilty INTO ls_ui_visibilty
          WITH KEY step = iv_step fieldname = <fs_record>-fieldname.

*       case of key containning a space (example: SELECTED CHILD)
        IF sy-subrc <> 0.
          lv_fieldname  = <fs_record>-fieldname.
          REPLACE ALL OCCURRENCES OF ` ` IN lv_fieldname WITH '*'.
          LOOP AT lt_ui_visibilty INTO ls_ui_visibilty
            WHERE step = iv_step
              AND fieldname CP lv_fieldname.
            EXIT.
          ENDLOOP.
        ENDIF.

        IF sy-subrc = 0.
          <fs_record>-ui_attribute = ls_ui_visibilty-visibility.
        ENDIF.
      ENDLOOP.
    ENDIF.

*   UI visibility for BADI method IF_HRASR00GEN_SERVICE~DO_OPERATIONS
    IF ct_ui_op_visibility[] IS NOT INITIAL.
      LOOP AT ct_ui_op_visibility ASSIGNING FIELD-SYMBOL(<fs_record2>).
        CLEAR: ls_ui_visibilty, lv_fieldname.

        READ TABLE lt_ui_visibilty INTO ls_ui_visibilty
          WITH KEY step = iv_step fieldname = <fs_record2>-fieldname.

*       case of key containning a space (example: SELECTED CHILD)
        IF sy-subrc <> 0.
          lv_fieldname  = <fs_record2>-fieldname.
          REPLACE ALL OCCURRENCES OF ` ` IN lv_fieldname WITH '*'.
          LOOP AT lt_ui_visibilty INTO ls_ui_visibilty
            WHERE step = iv_step
              AND fieldname CP lv_fieldname.
            EXIT.
          ENDLOOP.
        ENDIF.

        IF sy-subrc = 0.
          <fs_record2>-ui_attribute = ls_ui_visibilty-visibility.
        ENDIF.
      ENDLOOP.
    ENDIF.

  ENDMETHOD.
