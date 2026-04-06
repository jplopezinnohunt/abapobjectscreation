  method IF_HRASR00GEN_SERVICE~INITIALIZE.

      DATA : init         TYPE hrasr00gensrv_dataset_init,
           lv_pernr     TYPE persno,
           lv_step      TYPE string,
           lv_begda     TYPE begda,
           lv_irdoa     TYPE pun_irdoa,
           lv_kdgbr     TYPE kdgbr,
           ls_pa0021    TYPE hcmt_bsp_pa_un_r0021,
           ls_srv_value TYPE hrasr00gensrv_dataset_init,
           lt_pa0021    TYPE TABLE OF pa0021,
           ls_ui_attr   TYPE LINE OF if_hrasr00_types=>ty_t_gensrv_init_ui_attribute,
           lo_common    TYPE REF TO zcl_hrfiori_pf_common.

    FIELD-SYMBOLS: <fs_ui_line> TYPE if_hrasr00_types=>ty_s_gensrv_init_ui_attribute.

    CREATE OBJECT lo_common.

    LOOP AT service_field_values INTO init WHERE fieldname EQ 'PERNR'.
      lv_pernr = init-fieldvalue.
    ENDLOOP.

    LOOP AT service_field_values INTO init WHERE fieldname EQ 'STEP'.
      lv_step = init-fieldvalue.
    ENDLOOP.

    CASE lv_step.
      WHEN 'REQUEST'.
        lo_common->set_form_ui_attributes( EXPORTING iv_form_scenario = 'ZHR_SPSE_UNES'
                                                     iv_step = 'REQUEST'
                                           CHANGING  ct_ui_visibility = ui_attributes ).

        SELECT SINGLE * INTO CORRESPONDING FIELDS OF @ls_pa0021
          FROM pa0021 AS p21
          INNER JOIN pa0959 AS p959
          ON p21~pernr EQ p959~pernr
          AND p21~subty EQ p959~subty
          AND p21~objps EQ p959~objps
          AND p21~begda EQ p959~begda
          AND p21~endda EQ p959~endda
          WHERE p21~pernr = @lv_pernr    AND
                  p21~subty = '10'       AND
                  p959~famst <> '3'      AND " différent de divorcé
                  p21~endda >= @sy-datum AND
                  p21~begda <= @sy-datum.

        IF sy-subrc EQ 0.
          lv_begda = ls_pa0021-begda.
        ENDIF.

        LOOP AT service_field_values INTO init WHERE fieldname EQ 'I0021_BEGDA'.
          IF lv_begda IS INITIAL. " Creation Spouse
            init-fieldvalue = sy-datum.

            LOOP AT ui_attributes INTO ls_ui_attr.
*              Date of death must be hidden for creation
              IF ls_ui_attr-fieldname = 'I0021_DEATH'.
                ls_ui_attr-ui_attribute = 'I'.
              ENDIF.
*              Marital status to be Hidden for creation
              IF ls_ui_attr-fieldname = 'I0021_FAMST'.
                ls_ui_attr-ui_attribute = 'I'.
              ENDIF.
              MODIFY TABLE ui_attributes FROM ls_ui_attr.
            ENDLOOP.
          ELSE.        " Change Spouse
            init-fieldvalue = lv_begda.
          ENDIF.
          MODIFY service_field_values FROM init.
        ENDLOOP.

        CLEAR init.

        LOOP AT service_field_values INTO init WHERE fieldname EQ 'I0021_FAMST'.
          IF lv_begda IS INITIAL. " Creation Spouse
*            Marital status to be Married by default for creation
            LOOP AT service_field_values INTO init WHERE fieldname EQ 'I0021_FAMST'.
              init-fieldvalue = 0. "Married
            ENDLOOP.
          ELSE.        " Change Spouse
            LOOP AT service_field_values INTO init WHERE fieldname EQ 'I0021_FAMST'.
              init-fieldvalue = ls_pa0021-famst.
            ENDLOOP.
          ENDIF.
          MODIFY service_field_values FROM init.
        ENDLOOP.

      WHEN 'APPROVE'.
        lo_common->set_form_ui_attributes( EXPORTING iv_form_scenario = 'ZHR_SPSE_UNES'
                                                     iv_step = 'APPROVE'
                                           CHANGING  ct_ui_visibility = ui_attributes ).

*       Field in receipt of allowance is mandatory if field financialy dependent
*       was set
        LOOP AT service_field_values INTO ls_srv_value.
          IF ls_srv_value-fieldname = 'I0021_KDGBR'.
            lv_kdgbr = ls_srv_value-fieldvalue.
          ENDIF.
          IF ls_srv_value-fieldname = 'I0021_IRDOA'.
            lv_irdoa = ls_srv_value-fieldvalue.
          ENDIF.
        ENDLOOP.

*       Field IRDOA is compsulory if KDGBR is
        IF lv_kdgbr IS NOT INITIAL AND lv_irdoa IS INITIAL.
          LOOP AT ui_attributes ASSIGNING <fs_ui_line>
            WHERE fieldname = 'I0021_IRDOA'.
            <fs_ui_line>-ui_attribute = 'M'.
          ENDLOOP.

        ENDIF.

      WHEN 'PROCESS'.
        lo_common->set_form_ui_attributes( EXPORTING iv_form_scenario = 'ZHR_SPSE_UNES'
                                                     iv_step = 'PROCESS'
                                           CHANGING  ct_ui_visibility = ui_attributes ).

      WHEN OTHERS.
    ENDCASE.


  endmethod.
