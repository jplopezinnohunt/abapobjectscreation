  METHOD if_hrasr00gen_service~do_operations.

    DATA: lv_last_name         TYPE pad_nachn,
          lv_first_name        TYPE pad_vorna,
          lv_step              TYPE string,
          lv_pernr             TYPE pernr_d,
          lv_begda             TYPE begda,
          lv_endda             TYPE endda,
          lv_seqnr             TYPE seqnr,
          lv_obps              TYPE objps,
          lv_lgart             TYPE lgart,
          lv_process_guid      TYPE asr_guid,
          lv_guid              TYPE scmg_case_guid,
          lv_ref_number        TYPE asr_reference_number,
          lv_area              TYPE ben_area,
          lv_event             TYPE ben_event,
          lf_attachment_exists TYPE flag,
          lv_date_birth        TYPE dats,
          lv_year              TYPE i,
          lv_eduat             TYPE c,
          lv_amount            TYPE string, "PAD_AMT7S,
          lv_submission_date   TYPE dats,
          lv_computed_date     TYPE dats,
          lv_begda0378         TYPE dats,
          lv_endda0378         TYPE dats,
          lv_locking_user      TYPE syst_uname,
          lv_message           TYPE  string,
          lv_subrc             TYPE syst_subrc,
          lf_record_exists     TYPE flag,
          lf_request_exists    TYPE flag,
          ls_p0378             TYPE p0378,
          ls_return_lock       TYPE bapireturn1,
          ls_return_unlock     TYPE bapireturn1,
          ls_msg               TYPE symsg,
          ls_datasets          TYPE hrasr00gensrv_dataset,
          ls_return            TYPE  bapireturn1,
          lt_cont              TYPE TABLE OF swr_cont,
          ls_cont              TYPE swr_cont,
          ls_key               TYPE  bapipakey,
          lt_error_table       TYPE STANDARD TABLE OF rpbenerr,
          ls_p0021             TYPE p0021,
          lt_p0021             TYPE STANDARD TABLE OF p0021,
          lo_common            TYPE REF TO zcl_hrfiori_pf_common.

*    FIELD-SYMBOLS: <fs_uiattr> TYPE if_hrasr00_types=>ty_s_gensrv_ui_attribute.
    FIELD-SYMBOLS <fs_srv_data> TYPE hrasr00gensrv_dataset.



*   When user fills the form and send it, we check if data are correct: this is event 'CHECK'
*   We use this this event to make a field compulsory if neccessary
    CASE event.
      WHEN 'SAVE'.
        LOOP AT service_datasets ASSIGNING <fs_srv_data>.
          IF <fs_srv_data>-fieldname = 'PERNR'.
            MOVE <fs_srv_data>-fieldvalue TO lv_pernr.
          ENDIF.

          IF <fs_srv_data>-fieldname = 'I0378_BEGDA'.
            MOVE <fs_srv_data>-fieldvalue TO lv_begda.
          ENDIF.

          IF <fs_srv_data>-fieldname = 'I0378_ENDDA'.
            MOVE <fs_srv_data>-fieldvalue TO lv_endda.
          ENDIF.

          IF <fs_srv_data>-fieldname = 'I0378_EVENT'.
            MOVE <fs_srv_data>-fieldvalue TO lv_event.
          ENDIF.

          IF <fs_srv_data>-fieldname = 'I0378_BAREA'.
            MOVE <fs_srv_data>-fieldvalue TO lv_area.
          ENDIF.
        ENDLOOP.


        ls_cont-element = 'EmployeeNumber'.
        ls_cont-value = lv_pernr.
        APPEND ls_cont TO lt_cont.

        ls_cont-element = 'ValidityBegin'.
        ls_cont-value = lv_begda.
        APPEND ls_cont TO lt_cont.

        ls_cont-element = 'ValidityEnd'.
        ls_cont-value = lv_endda.
        APPEND ls_cont TO lt_cont.

        ls_cont-element = 'BenefitArea'.
        ls_cont-value = lv_area.
        APPEND ls_cont TO lt_cont.

        ls_cont-element = 'AdjustmentReason'.
        ls_cont-value = lv_event.
        APPEND ls_cont TO lt_cont.

*       workflow to create it 378 in batch with lock employee handling
        CALL FUNCTION 'SAP_WAPI_START_WORKFLOW'
          EXPORTING
            task            = 'WS98100032'
          TABLES
            input_container = lt_cont.

* workflow to create it 378 in batch with lock employee handling

*        create_it0378_via_bi( EXPORTING iv_pernr = lv_pernr
*                                        iv_begda = lv_begda
*                                        iv_endda = lv_endda
*                                        iv_area  = lv_area
*                                        iv_event = lv_event
*                              IMPORTING ov_subrc = lv_subrc
*                                        ov_message = lv_message ).




*        IF lv_subrc <> 0.
*          ls_msg-msgid = 'ZHRFIORI'.
*          ls_msg-msgno = '019'.
*          ls_msg-msgty = 'E'.
*          message_handler->add_message( EXPORTING message = ls_msg ).
*        ENDIF.

*        ls_p0378-pernr = lv_pernr.
*        ls_p0378-infty = '0378'.
*        ls_p0378-subty = 'CHIL'.
*        ls_p0378-seqnr = lv_seqnr.
*        ls_p0378-objps = lv_obps.
*        ls_p0378-endda = lv_endda.
*        ls_p0378-begda = lv_begda.
*        ls_p0378-barea = lv_area.
*        ls_p0378-event = lv_event.
*
**       lock employee folder
*        CALL FUNCTION 'HR_EMPLOYEE_ENQUEUE'
*          EXPORTING
*            number       = lv_pernr
*          IMPORTING
*            return       = ls_return_lock
*            locking_user = lv_locking_user.
*
*        CALL FUNCTION 'HR_INFOTYPE_OPERATION'
*          EXPORTING
*            infty         = '0378'
*            number        = lv_pernr
*            subtype       = 'CHIL'
**           OBJECTID      =
**           LOCKINDICATOR =
*            validityend   = lv_endda
*            validitybegin = lv_begda
**           RECORDNUMBER  =
*            record        = ls_p0378
*            operation     = 'INS'
**           TCLAS         = 'A'
**           dialog_mode   = '0'
**           nocommit      =
**           VIEW_IDENTIFIER        =
**           SECONDARY_RECORD       =
*          IMPORTING
*            return        = ls_return
*            key           = ls_key.
*
**       unlock employee folder
*        CALL FUNCTION 'HR_EMPLOYEE_DEQUEUE'
*          EXPORTING
*            number = lv_pernr
*          IMPORTING
*            return = ls_return_unlock.


      WHEN 'CHECK'.

*       Get Process GUID if not empty
        LOOP AT service_datasets INTO ls_datasets
          WHERE fieldname = 'PROCESS_GUID'.
          lv_process_guid = ls_datasets-fieldvalue.
        ENDLOOP.

        LOOP AT service_datasets INTO ls_datasets
          WHERE fieldname EQ 'PROCESS_REFERENCE_NUMBER'.
          lv_ref_number = ls_datasets-fieldvalue.
        ENDLOOP.
        CREATE OBJECT lo_common.
        IF lv_ref_number IS NOT INITIAL.
          lo_common->get_scenario_case_id( EXPORTING iv_ref_number = lv_ref_number
                                           IMPORTING ov_scenario_guid = lv_guid ).
        ENDIF.

        LOOP AT service_datasets INTO ls_datasets
          WHERE fieldname = 'I0021_FGBDT'.
        ENDLOOP.
        IF sy-subrc = 0.
          MOVE ls_datasets-fieldvalue TO lv_date_birth.
        ENDIF.
        LOOP AT service_datasets INTO ls_datasets
          WHERE fieldname = 'I0021_EDUAT'.
        ENDLOOP.
        IF sy-subrc = 0.
          MOVE ls_datasets-fieldvalue TO lv_eduat.
        ENDIF.
        LOOP AT service_datasets INTO ls_datasets
          WHERE fieldname = 'I0021_LGART'.
        ENDLOOP.
        IF sy-subrc = 0.
          MOVE ls_datasets-fieldvalue TO lv_lgart.
        ENDIF.
        IF lv_lgart IS NOT INITIAL. " ticket 1598
          CLEAR: lf_attachment_exists.

          lo_common->check_attachment(
            EXPORTING iv_process = 'ZHR_BIRTH_CHILD'
             iv_process_guid = lv_process_guid
             iv_scenario_guid = lv_guid
             iv_attachment_type = 'ZOTHERS'
            IMPORTING ev_attachment_exist = lf_attachment_exists ).
*
          IF lf_attachment_exists = abap_false.
            ls_msg-msgid = 'ZHRFIORI'.
            ls_msg-msgno = '137'.
            ls_msg-msgty = 'E'.
            message_handler->add_message( EXPORTING message = ls_msg ).
          ENDIF.
        ENDIF.

* <Field Educational attendent is now invisible " Jira 1034
        IF lv_date_birth IS NOT INITIAL AND lv_eduat IS INITIAL. "Educatoinal attendance field mandatory if +18yo
          CALL FUNCTION 'HR_SGPBS_YRS_MTHS_DAYS'
            EXPORTING
              beg_da  = lv_date_birth
              end_da  = sy-datum
            IMPORTING
              no_year = lv_year.
          IF lv_year >= 18.
*           Make compulsory the field EDUAT
*            LOOP AT ui_attributes ASSIGNING <fs_uiattr>
*              WHERE fieldname = 'I0021_EDUAT'.
*              <fs_uiattr>-ui_attribute = 'M'.
*            ENDLOOP.
            ls_msg-msgid = 'ZHRFIORI'.
            ls_msg-msgno = '001'.
            ls_msg-msgty = 'E'.
            message_handler->add_message( EXPORTING message = ls_msg ).
          ENDIF.
        ENDIF.
* Field Educational attendent is now invisible " Jira 1034>


*       Compute start date and end date for infotype 0378
        LOOP AT service_datasets INTO ls_datasets
            WHERE fieldname = 'FORM_SCENARIO_STAGE'.
        ENDLOOP.
        MOVE ls_datasets-fieldvalue TO lv_step.
        lv_submission_date = sy-datum.

        IF lv_step = 'REQUEST'.

          CALL FUNCTION 'RP_CALC_DATE_IN_INTERVAL'
            EXPORTING
              date      = lv_date_birth
              days      = '0'
              months    = '1'
              signum    = '+'
              years     = '0'
            IMPORTING
              calc_date = lv_computed_date.

          IF lv_submission_date <= lv_computed_date.
            lv_begda0378 = lv_date_birth.
*            lv_endda0378 = '99991231'.
*            lv_endda0378 = lv_begda0378.
*            lv_endda0378+0(4) = lv_endda0378+0(4) + 1.
          ELSE.
            lv_begda0378 = lv_submission_date.
*            lv_endda0378 = '99991231'.
*            lv_endda0378 = lv_begda0378.
*            lv_endda0378+0(4) = lv_endda0378+0(4) + 1.
          ENDIF.
          CALL FUNCTION 'HR_BEN_CALC_ENDDA_REASON'
            EXPORTING
              barea         = '11'
              adjust_reason = 'CHIL'
              begda         = lv_begda0378
              firsttime     = 'X'
              override      = 'X'
              reaction      = 'N'
*           IMPORTING
*             SUBRC         =
            TABLES
              error_table   = lt_error_table
            CHANGING
              endda         = lv_endda0378.


          LOOP AT service_datasets ASSIGNING <fs_srv_data>.
            IF <fs_srv_data>-fieldname = 'I0378_BEGDA'.
              MOVE lv_begda0378 TO <fs_srv_data>-fieldvalue.
            ENDIF.

            IF <fs_srv_data>-fieldname = 'I0378_ENDDA'.
              MOVE lv_endda0378 TO <fs_srv_data>-fieldvalue.
            ENDIF.

            IF <fs_srv_data>-fieldname = 'I0378_EVENT'.
              <fs_srv_data>-fieldvalue = 'CHIL'.
            ENDIF.

            IF <fs_srv_data>-fieldname = 'I0378_BAREA'.
              <fs_srv_data>-fieldvalue = '11'.
            ENDIF.
          ENDLOOP.


*         Prevent submission  if child already exist in system
          IF lv_ref_number IS INITIAL.
            CREATE OBJECT lo_common.
            LOOP AT service_datasets INTO ls_datasets
              WHERE fieldname = 'PERNR'.
              MOVE ls_datasets-fieldvalue TO lv_pernr.
            ENDLOOP..

            LOOP AT service_datasets INTO ls_datasets
                WHERE fieldname = 'I0021_FANAM'.
              MOVE ls_datasets-fieldvalue TO  lv_last_name.
            ENDLOOP.

            LOOP AT service_datasets INTO ls_datasets
                WHERE fieldname = 'I0021_FAVOR'.
              MOVE ls_datasets-fieldvalue TO  lv_first_name.
            ENDLOOP.

            CALL FUNCTION 'HR_READ_INFOTYPE'
              EXPORTING
                pernr         = lv_pernr
                infty         = '0021'
                begda         = sy-datum
                endda         = sy-datum
                bypass_buffer = abap_true
              TABLES
                infty_tab     = lt_p0021.

*         all names in uppercase and remove strange characters for comparaison
            TRANSLATE lv_first_name TO UPPER CASE.
            TRANSLATE lv_last_name TO UPPER CASE.
            CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'
              EXPORTING
                intext  = lv_first_name
              IMPORTING
                outtext = lv_first_name.
            CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'
              EXPORTING
                intext  = lv_last_name
              IMPORTING
                outtext = lv_last_name.

            LOOP AT lt_p0021 INTO ls_p0021
              WHERE subty ='14'.
*           all names in uppercase and remove strange characters for comparaison
              TRANSLATE ls_p0021-favor TO UPPER CASE.
              TRANSLATE ls_p0021-fanam TO UPPER CASE.
              CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'
                EXPORTING
                  intext  = ls_p0021-favor
                IMPORTING
                  outtext = ls_p0021-favor.
              CALL FUNCTION 'SCP_REPLACE_STRANGE_CHARS'
                EXPORTING
                  intext  = ls_p0021-fanam
                IMPORTING
                  outtext = ls_p0021-fanam.

              IF lv_first_name = ls_p0021-favor  AND lv_last_name = ls_p0021-fanam.
                lf_record_exists = abap_true.
                EXIT.
              ENDIF.
            ENDLOOP.

            IF lf_record_exists = abap_true.
              ls_msg-msgid = 'ZHRFIORI'.
              ls_msg-msgno = '135'.
              ls_msg-msgty = 'E'.
              message_handler->add_message( EXPORTING message = ls_msg ).
            ENDIF.

*         If necessary, prevent submission if request on same child data already exist
            IF lf_record_exists = abap_false.
              lo_common->check_same_request_exist(
                EXPORTING
                  iv_process = 'ZHR_BIRTH_CHILD'
                  iv_process_guid = lv_process_guid
                  iv_pernr = lv_pernr
                  iv_field_name_fn = 'I0021_FAVOR'
                  iv_field_name_ln = 'I0021_FANAM'
                  iv_first_name = lv_first_name
                  iv_last_name = lv_last_name
                IMPORTING
                  ov_request_exist = lf_request_exists ).
              IF lf_request_exists = abap_true.
                ls_msg-msgid = 'ZHRFIORI'.
                ls_msg-msgno = '134'.
                ls_msg-msgty = 'E'.
                message_handler->add_message( EXPORTING message = ls_msg ).
              ENDIF.
            ENDIF.
          ENDIF.

        ENDIF.

*       Amount control
        LOOP AT service_datasets INTO ls_datasets
          WHERE fieldname = 'I0021_BETR3'.

          MOVE ls_datasets-fieldvalue TO lv_amount.
          IF lv_amount CS ','.
            IF lv_amount CS '.'.
              REPLACE ALL OCCURRENCES OF SUBSTRING ',' IN lv_amount WITH ''.
            ELSE.
              REPLACE ALL OCCURRENCES OF SUBSTRING ',' IN lv_amount WITH '.'.
            ENDIF.

            MOVE lv_amount TO ls_datasets-fieldvalue.
            MODIFY service_datasets FROM ls_datasets.
          ENDIF.
        ENDLOOP.

    ENDCASE.

  ENDMETHOD.
