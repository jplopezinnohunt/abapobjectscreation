  method IF_HRASR00GEN_SERVICE~DO_OPERATIONS.

    DATA:
      lv_spods             TYPE pun_dstat,
      lv_pernr             TYPE persno,
      lv_serty             TYPE pun_serty,
      lv_irdoa             TYPE pun_irdoa,
      lv_amount            TYPE string,
      lv_amount2           TYPE pun_spoear,
      lv_new_amount        TYPE pun_spoear,
      lv_bapicurr          TYPE bapicurr-bapicurr,
      ls_return            TYPE bapireturn,
      lv_kdgbr             TYPE kdgbr,
      lv_fanam             TYPE fanam,
      lv_favor             TYPE pad_vorna,
      lv_curr              TYPE waers,
      lv_step              TYPE string,
      lv_famst             TYPE string,
      lv_sngpr             TYPE string,
      lv_guid              TYPE scmg_case_guid,
      lv_process_guid      TYPE asr_guid,
      lv_ref_number        TYPE asr_reference_number,
      lf_attachment_exists TYPE flag,
      lo_common            TYPE REF TO zcl_hrfiori_pf_common,
      ls_pa0001            TYPE pa0001,
      ls_pa0021            TYPE hcmt_bsp_pa_un_r0021,
      LV_EARNNGS           TYPE PUN_SPOEAR,
      ls_msg               TYPE symsg,
      ls_datasets          TYPE hrasr00gensrv_dataset,
      ls_ui_attribute      TYPE if_hrasr00_types=>ty_s_gensrv_ui_attribute.
    DATA main_record           TYPE REF TO data.
    DATA main_structurename    TYPE strukname.

    FIELD-SYMBOLS <field>         TYPE pun_spoear.
    FIELD-SYMBOLS <main_record>   TYPE ANY.
    FIELD-SYMBOLS <dataset_field_wa>    TYPE hrasr00gensrv_dataset.

    CASE event.
      WHEN 'CHECK'.

        LOOP AT service_datasets INTO DATA(ls_dataset_pernr) WHERE fieldname EQ 'I0021_SPEAR'.
          LV_EARNNGS = ls_dataset_pernr-fieldvalue.
        ENDLOOP.

        LOOP AT service_datasets INTO ls_dataset_pernr WHERE fieldname EQ 'PERNR'.
          lv_pernr = ls_dataset_pernr-fieldvalue.
        ENDLOOP.

*       Check for Mandatory fields and attachments
        LOOP AT service_datasets INTO DATA(serv_datasets) WHERE fieldname EQ 'STEP'.
          IF serv_datasets-fieldvalue IS NOT INITIAL.
            lv_step = serv_datasets-fieldvalue.
          ENDIF.
        ENDLOOP.

*       Get reference number of request
        LOOP AT service_datasets INTO ls_datasets
          WHERE fieldname EQ 'PROCESS_REFERENCE_NUMBER'.
          lv_ref_number = ls_datasets-fieldvalue.
        ENDLOOP.

*       Get Process GUID if not empty
        LOOP AT service_datasets INTO ls_datasets
          WHERE fieldname = 'PROCESS_GUID'.
          lv_process_guid = ls_datasets-fieldvalue.
        ENDLOOP.

        IF lv_step EQ 'REQUEST'.
*         On récupère la référence de la requête pour récupérer les pièces jointes
          CREATE OBJECT lo_common.
          IF lv_ref_number IS NOT INITIAL.
            lo_common->get_scenario_case_id( EXPORTING iv_ref_number = lv_ref_number
                                             IMPORTING ov_scenario_guid = lv_guid ).
          ENDIF.

          if LV_EARNNGS is not initial.
                  CLEAR: lf_attachment_exists.

                  lo_common->check_attachment(
                    EXPORTING iv_process = 'ZHR_SPSE_UNES'
                              iv_process_guid = lv_process_guid
                              iv_scenario_guid = lv_guid
                              iv_attachment_type = 'ZAGEARN'
                    IMPORTING ev_attachment_exist = lf_attachment_exists ).

                  IF lf_attachment_exists = abap_false.
                    ls_msg-msgid = 'ZHRFIORI'.
                    ls_msg-msgno = '133'.
                    ls_msg-msgty = 'E'.
                    message_handler->add_message( EXPORTING message = ls_msg ).
                  ENDIF.
            endif.

*           Check marital status change
            LOOP AT service_datasets INTO ls_datasets
              WHERE fieldname = 'I0021_FAMST'.
              lv_famst = ls_datasets-fieldvalue.
            ENDLOOP.


*         Alimentation des champs
          SELECT SINGLE * INTO CORRESPONDING FIELDS OF @ls_pa0021
            FROM pa0021 AS p21
            INNER JOIN pa0959 AS p959
            ON p21~pernr EQ p959~pernr
            AND p21~subty EQ p959~subty
            AND p21~objps EQ p959~objps
            AND p21~begda EQ p959~begda
            AND p21~endda EQ p959~endda
            WHERE p21~pernr = @lv_pernr AND
                    p21~subty = '10' AND
                    p21~endda >= @sy-datum AND
                    p21~begda <= @sy-datum.

          IF sy-subrc EQ 0.
            LOOP AT service_datasets INTO ls_datasets
              WHERE fieldname = 'I0021_FANAM'.
              lv_fanam = ls_datasets-fieldvalue.
            ENDLOOP.
            LOOP AT service_datasets INTO ls_datasets
              WHERE fieldname = 'I0021_FAVOR'.
              lv_favor = ls_datasets-fieldvalue.
            ENDLOOP.
            IF sy-subrc = 0.
              "Compare to actual data
              IF ls_pa0021-fanam NE lv_fanam OR ls_pa0021-favor NE lv_favor.
*               Changement de Nom: passport/Id mandatory
                CLEAR: lf_attachment_exists.

                lo_common->check_attachment(
                  EXPORTING iv_process = 'ZHR_SPSE_UNES'
                            iv_process_guid = lv_process_guid
                            iv_scenario_guid = lv_guid
                            iv_attachment_type = 'ZPASPORTID'
                  IMPORTING ev_attachment_exist = lf_attachment_exists ).

                IF lf_attachment_exists = abap_false.
                  ls_msg-msgid = 'ZHRFIORI'.
                  ls_msg-msgno = '022'.
                  ls_msg-msgty = 'E'.
                  message_handler->add_message( EXPORTING message = ls_msg ).
                ENDIF.

              ENDIF.
            ENDIF.




              "compare to actual data
              IF ls_pa0021-famst NE lv_famst. "marital status change

                IF lv_famst EQ 0.
*                 Cas de mariage
                  CLEAR: lf_attachment_exists.

                  lo_common->check_attachment(
                    EXPORTING iv_process = 'ZHR_SPSE_UNES'
                              iv_process_guid = lv_process_guid
                              iv_scenario_guid = lv_guid
                              iv_attachment_type = 'ZPRTNRSHIP'
                    IMPORTING ev_attachment_exist = lf_attachment_exists ).

                  IF lf_attachment_exists = abap_false.
                    ls_msg-msgid = 'ZHRFIORI'.
                    ls_msg-msgno = '023'.
                    ls_msg-msgty = 'E'.
                    message_handler->add_message( EXPORTING message = ls_msg ).
                  ENDIF.

                ELSEIF lv_famst EQ 2 OR lv_famst EQ 3 OR lv_famst EQ 4.
*                 Cas de divorce / décés
                  CLEAR: lf_attachment_exists.

                  lo_common->check_attachment(
                    EXPORTING iv_process = 'ZHR_SPSE_UNES'
                              iv_process_guid = lv_process_guid
                              iv_scenario_guid = lv_guid
                              iv_attachment_type = 'ZPRTNRDIV'
                    IMPORTING ev_attachment_exist = lf_attachment_exists ).

                  IF lf_attachment_exists = abap_false.
                    ls_msg-msgid = 'ZHRFIORI'.
                    ls_msg-msgno = '024'.
                    ls_msg-msgty = 'E'.
                    message_handler->add_message( EXPORTING message = ls_msg ).
                  ENDIF.

                ENDIF.
              ENDIF.
            ELSE.
* mode creation
             IF lv_famst EQ 0.
*                 Cas de mariage
                  CLEAR: lf_attachment_exists.

                  lo_common->check_attachment(
                    EXPORTING iv_process = 'ZHR_SPSE_UNES'
                              iv_process_guid = lv_process_guid
                              iv_scenario_guid = lv_guid
                              iv_attachment_type = 'ZPRTNRSHIP'
                    IMPORTING ev_attachment_exist = lf_attachment_exists ).

                  IF lf_attachment_exists = abap_false.
                    ls_msg-msgid = 'ZHRFIORI'.
                    ls_msg-msgno = '023'.
                    ls_msg-msgty = 'E'.
                    message_handler->add_message( EXPORTING message = ls_msg ).
                  ENDIF.

                ELSEIF lv_famst EQ 2 OR lv_famst EQ 3 OR lv_famst EQ 4.
*                 Cas de divorce / décés
                  CLEAR: lf_attachment_exists.

                  lo_common->check_attachment(
                    EXPORTING iv_process = 'ZHR_SPSE_UNES'
                              iv_process_guid = lv_process_guid
                              iv_scenario_guid = lv_guid
                              iv_attachment_type = 'ZPRTNRDIV'
                    IMPORTING ev_attachment_exist = lf_attachment_exists ).

                  IF lf_attachment_exists = abap_false.
                    ls_msg-msgid = 'ZHRFIORI'.
                    ls_msg-msgno = '024'.
                    ls_msg-msgty = 'E'.
                    message_handler->add_message( EXPORTING message = ls_msg ).
                  ENDIF.

                ENDIF.




            LOOP AT service_datasets INTO ls_datasets WHERE fieldname = 'I0021_SPODS'.

              IF lv_spods IS INITIAL.


                SELECT SINGLE persg
                  INTO ls_pa0001
                  FROM pa0001
                  WHERE pernr EQ lv_pernr
                    AND endda EQ '99991231'.

                IF ls_pa0001-persg EQ '2'.
                  ls_msg-msgid = 'ZHRFIORI'.
                  ls_msg-msgno = '015'.
                  ls_msg-msgty = 'E'.
                  message_handler->add_message( EXPORTING message = ls_msg ).
                ENDIF.
              ENDIF.
            ENDLOOP.

*           GR: SPEAR and SPWAE mandatory if  SERTY='' (Provided)
            LOOP AT service_datasets INTO ls_datasets WHERE fieldname = 'I0021_SERTY'.
              lv_serty = ls_datasets-fieldvalue.
            ENDLOOP.

            LOOP AT service_datasets INTO ls_datasets WHERE fieldname = 'I0021_SPEAR' OR fieldname = 'I0021_SPWAE'.
              IF lv_serty IS INITIAL. "Provided
                IF ls_datasets-fieldname EQ 'I0021_SPEAR' AND ls_datasets-fieldvalue IS INITIAL.
                  ls_msg-msgid = 'ZHRFIORI'.
                  ls_msg-msgno = '016'.
                  ls_msg-msgty = 'E'.
                  message_handler->add_message( EXPORTING message = ls_msg ).
                ELSEIF ls_datasets-fieldname EQ 'I0021_SPWAE' AND ls_datasets-fieldvalue IS INITIAL.
                  ls_msg-msgid = 'ZHRFIORI'.
                  ls_msg-msgno = '017'.
                  ls_msg-msgty = 'E'.
                  message_handler->add_message( EXPORTING message = ls_msg ).
                ENDIF.
              ENDIF.
            ENDLOOP.

          ENDIF.
        ENDIF.

* Amount control

        LOOP AT service_datasets INTO ls_datasets
          WHERE fieldname = 'I0021_SPWAE'.
          lv_curr = ls_datasets-fieldvalue.
        ENDLOOP.

        IF sy-subrc EQ 0.

          LOOP AT service_datasets ASSIGNING <dataset_field_wa> "INTO ls_datasets
            WHERE fieldname = 'I0021_SPEAR'.
            "lv_amount = <dataset_field_wa>-fieldvalue.


             TRY. "These may be errors in some field with datatypes like DEC,INT if UI does not prevent then we catch
               lv_new_amount = <dataset_field_wa>-fieldvalue.

               CATCH cx_sy_conversion_no_number.
                    ls_msg-msgid = 'ZHRFIORI'.
                    ls_msg-msgno = '120'.
                    ls_msg-msgty = 'E'.
                    message_handler->add_message( EXPORTING message = ls_msg ).
                    ls_msg-msgid = 'ZHRFIORI'.
                    ls_msg-msgno = '122'.
                    ls_msg-msgty = 'E'.
                    message_handler->add_message( EXPORTING message = ls_msg ).
               CATCH cx_sy_conversion_overflow.
                    ls_msg-msgid = 'ZHRFIORI'.
                    ls_msg-msgno = '120'.
                    ls_msg-msgty = 'E'.
                    message_handler->add_message( EXPORTING message = ls_msg ).
                    ls_msg-msgid = 'ZHRFIORI'.
                    ls_msg-msgno = '122'.
                    ls_msg-msgty = 'E'.
                    message_handler->add_message( EXPORTING message = ls_msg ).
             ENDTRY.



          ENDLOOP.
        ENDIF.


    ENDCASE.

  endmethod.
