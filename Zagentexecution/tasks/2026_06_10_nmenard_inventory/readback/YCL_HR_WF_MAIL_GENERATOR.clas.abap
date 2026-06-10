class YCL_HR_WF_MAIL_GENERATOR definition
  public
  create public .

public section.

  interfaces YIF_HR_WF_MAIL .

  methods CONSTRUCTOR
    importing
      !IV_NOTIF_TYPE type YE_WF_NOTIF
      !IV_NOTIF_HEADER type YE_WF_NOTIF_HEADER
      !IV_NOTIF_BODY type YE_WF_NOTIF_BODY
      !IV_NOTIF_ISTAT type ISTAT_D .
protected section.

  types:
    tty_email TYPE TABLE OF comm_id_long .

  data MV_LANGU type SYST_LANGU .
  data MV_FILE_NAME type SWR_FILENAME .
  data MV_ADD_PARAM_1 type TEXT40 .
  data MV_MASSG type MASSG .
  data MV_MASSN type MASSN .
  data MV_SYST_CATEGORY type CCCATEGORY .
  data MV_WF_STEP type YE_HRWF_STEP .
  data MV_SUBAT type ZEOMWF_SAT .
  data MV_PROTOCOL type TEXT6 .
  data MV_NOTIF_TYPE type YE_WF_NOTIF .
  data MV_NOTIF_HEADER type YE_WF_NOTIF_HEADER .
  data MV_NOTIF_BODY type YE_WF_NOTIF_BODY .
  data MV_ISTAT type ISTAT_D .
  data MV_DATE_REF type DATUM .
  data MV_CURRENT_ACTOR type SWHACTOR .
  data MT_REASON type SWFTVALUE .
  data MT_CONTAINER type YTTHR_FIELD_VALUE .
  data MT_ATT_CONTENT_HEX type SOLIX_TAB .
  data MT_ATT_CONTENT type SOLI_TAB .
  data MV_WI_FATHER type SWW_WIID .
  data MS_DOCUMENT_DATA type SOFOLENTI1 .
  data MO_DOCUMENT type ref to CL_DOCUMENT_BCS .
  data MO_SENDER type ref to CL_CAM_ADDRESS_BCS .
  data MO_RECIPIENT type ref to CL_CAM_ADDRESS_BCS .
  data MO_SEND_REQUEST type ref to CL_BCS .
  data MT_BODY type SOLI_TAB .
  data MT_LINES type TLINE_TAB .
  data MV_SUBJECT type STRING .
  data MV_OBJID type HROBJID .
  data MV_SHORT type SHORT_D .
  data MT_STREAM type STRING_TABLE .
  data MS_STREAM type STRING .
  data MV_ADD_PARAM_2 type TEXT40 .
  data MV_ADD_PARAM_3 type TEXT40 .
  data MV_ADD_PARAM_4 type TEXT80 .

  methods ADD_SUBSITUTED_MAIL
    changing
      !CS_MAIL type YTTHR_WF_ACTORS .
  methods FILTER_AUTHORIZED_EMAIL
    changing
      !CT_EMAIL type TTY_EMAIL .
  methods PUT_FORMAT .
  methods ADD_TEMPLATE_VARIANT .
  methods CONVERT_REASON_TO_STRING
    returning
      value(RV_STRING) type STRING .
  methods FILL_FEATURE_STRUCT
    changing
      !CV_STRUCT type YSWF1 .
  methods GET_DATA .
  methods GET_FEATURE
    importing
      !IV_FEATURE type MERK1
      !IV_STRUCT type ANY
    exporting
      value(EV_BACK) type ANY .
  methods GET_SUBAT_TEXT
    importing
      !IV_SUBAT type ZEOMWF_SAT
      !IV_SPRSL type SPRAS default SY-LANGU
    returning
      value(RV_TEXT) type ZEOMWF_SATXT .
  methods INITIALIZE_DATA .
  methods PUT_TO_CONTAINER
    importing
      !IV_FIELD type FIELDNAME
      !IV_VALUE type ANY .
  methods READ_NOTIF_VARIANT
    importing
      !IV_NOTIF_VAR type YE_NOTIF_VAR
    returning
      value(RV_TEMPLATE_VAR) type YE_WF_NOTIF_BODY .
  methods REPLACE_DATA_FROM_CONTAINER .
  methods SET_ATTACHMENT .
  methods REPLACE_IN_BODY .
  methods REPLACE_IN_HEADER
    changing
      !CV_STRING type STRING .
  methods SEND_MAIL
    importing
      !IT_MAIL type YTTHR_WF_ACTORS
      !IT_MAIL_COPY type YTTHR_WF_ACTORS optional
      !IV_SENDER type UNAME optional
    exporting
      !EV_SUBRC type SY-SUBRC .
  methods GET_TEMPLATE
    importing
      !IV_NAME type TDOBNAME
      !IV_LANGU type SPRAS default SY-LANGU
    returning
      value(RT_LINES) type TLINE_TAB .
  methods CONVERT_TO_TABLE_STRING .
private section.
ENDCLASS.



CLASS YCL_HR_WF_MAIL_GENERATOR IMPLEMENTATION.


  METHOD add_subsituted_mail.

    DATA lt_subst TYPE TABLE OF sysid.
    DATA lt_pernr TYPE pernr_tab.
    DATA lt_mail_0105 TYPE tty_email.
    DATA ls_mail TYPE LINE OF ytthr_wf_actors.

    CHECK cs_mail IS NOT INITIAL.

    "Get delegated users
    SELECT rep_name FROM hrus_d2
                  FOR ALL ENTRIES IN @cs_mail
                  WHERE us_name = @cs_mail-objid
                  AND   begda <= @sy-datum
                  AND   endda >= @sy-datum
                  AND   active = @abap_true
             INTO TABLE @lt_subst.

    CHECK lt_subst IS NOT INITIAL.

    "get PERNR for these delegated users
    SELECT pernr FROM pa0105
           FOR ALL ENTRIES IN @lt_subst
           WHERE usrty = '0001'
           AND   usrid = @lt_subst-table_line
           AND   endda >= @sy-datum
           AND   begda <= @sy-datum
         INTO TABLE @lt_pernr.

    CHECK lt_pernr IS NOT INITIAL.

    "get mail for PERNR
    SELECT usrid_long FROM pa0105
           FOR ALL ENTRIES IN @lt_pernr
           WHERE pernr = @lt_pernr-table_line
           AND   subty = '0010'
           AND   endda >= @sy-datum
           AND   begda <= @sy-datum
         INTO TABLE @lt_mail_0105.

    CHECK lt_mail_0105 IS NOT INITIAL.

    IF mv_syst_category <> 'P'.
      me->filter_authorized_email( CHANGING ct_email = lt_mail_0105 ).
    ENDIF.

    LOOP AT lt_mail_0105 INTO DATA(lv_mail_0105).
      ls_mail-email = lv_mail_0105.
      APPEND ls_mail TO cs_mail.
    ENDLOOP.

  ENDMETHOD.


  METHOD add_template_variant.

    DATA lv_yswf1 TYPE yswf1.
    DATA lv_notif_var TYPE ye_notif_var.
    DATA ls_line TYPE tline.
    DATA lv_index TYPE sy-tabix.

    "Check if template variant is needed
    me->fill_feature_struct( CHANGING cv_struct = lv_yswf1 ).
    me->get_feature( EXPORTING iv_feature = 'YWFNF'
                               iv_struct = lv_yswf1
                     IMPORTING ev_back = lv_notif_var ).
    CHECK lv_notif_var IS NOT INITIAL.
    DATA(lv_template_var) = me->read_notif_variant( iv_notif_var = lv_notif_var ).
    DATA(lt_lines_en) = me->get_template( iv_name = lv_template_var
                                          iv_langu = 'E' ).
    DATA(lt_lines_fr) = me->get_template( iv_name = lv_template_var
                                          iv_langu = 'F' ).

    READ TABLE mt_lines INTO ls_line WITH KEY tdline = '<VARIANT_EN>'.
    IF sy-subrc = 0.
      lv_index = sy-tabix.
      DELETE mt_lines INDEX lv_index.
      INSERT LINES OF lt_lines_en INTO mt_lines INDEX lv_index.
    ENDIF.

    READ TABLE mt_lines INTO ls_line WITH KEY tdline = '<VARIANT_FR>'.
    IF sy-subrc = 0.
      lv_index = sy-tabix.
      DELETE mt_lines INDEX lv_index.
      INSERT LINES OF lt_lines_fr INTO mt_lines INDEX lv_index.
    ENDIF.

  ENDMETHOD.


  METHOD constructor.

    DATA lv_value TYPE tvarvc-low.

    mv_notif_type = iv_notif_type.
    mv_notif_header = iv_notif_header.
    mv_notif_body = iv_notif_body.
    mv_istat = iv_notif_istat.

    "Get http or https protocol
    SELECT SINGLE low INTO lv_value FROM tvarvc WHERE name = 'Y_HR_WF_HTTP_PROTOCOL'
                                                AND   type = 'P'.
    IF sy-subrc = 0 AND lv_value = abap_true.
      mv_protocol = 'http'.
    ELSE.
      mv_protocol = 'https'.
    ENDIF.

    SELECT SINGLE cccategory INTO mv_syst_category FROM t000 WHERE mandt = sy-mandt.

  ENDMETHOD.


  METHOD convert_reason_to_string.

    CALL FUNCTION 'SOTR_SERV_TABLE_TO_STRING'
      EXPORTING
        flag_no_line_breaks = space
        line_length         = '255'
*       LANGU               = SY-LANGU
      IMPORTING
        text                = rv_string
      TABLES
        text_tab            = mt_reason.

  ENDMETHOD.


  METHOD convert_to_table_string.

    CLEAR mt_stream.
    CALL FUNCTION 'CONVERT_ITF_TO_STREAM_TEXT'
      EXPORTING
*       LANGUAGE     = SY-LANGU
        lf           = 'X'
      IMPORTING
        stream_lines = mt_stream
      TABLES
        itf_text     = mt_lines
*       TEXT_STREAM  =
      .
  ENDMETHOD.


  METHOD fill_feature_struct.

    cv_struct-notif_type = mv_notif_type.
    cv_struct-subat = mv_subat.

  ENDMETHOD.


  method FILTER_AUTHORIZED_EMAIL.
  endmethod.


  METHOD get_data.

    me->put_to_container( iv_field = '<OBJID>' iv_value = mv_objid ).
    me->put_to_container( iv_field = '<SHORT>' iv_value = mv_short ).

  ENDMETHOD.


  METHOD get_feature.

    CALL FUNCTION 'HR_FEATURE_BACKFIELD'
      EXPORTING
        feature                     = iv_feature
        struc_content               = iv_struct
*       KIND_OF_ERROR               =
      IMPORTING
        back                        = ev_back
*     CHANGING
*       STATUS                      =
      EXCEPTIONS
        dummy                       = 1
        error_operation             = 2
        no_backvalue                = 3
        feature_not_generated       = 4
        invalid_sign_in_funid       = 5
        field_in_report_tab_in_pe03 = 6
        OTHERS                      = 7.
    IF sy-subrc <> 0.
      CLEAR ev_back.
    ENDIF.

  ENDMETHOD.


  METHOD get_subat_text.

    DATA ls_satt TYPE ythromwf_satt.

    SELECT SINGLE * INTO ls_satt FROM ythromwf_satt WHERE subat = iv_subat
                                                    AND   sprsl = iv_sprsl.
    IF sy-subrc = 0.
      IF ls_satt-satxt_notif IS NOT INITIAL.
        rv_text = ls_satt-satxt_notif.
      ELSE.
        rv_text = ls_satt-satxt.
      ENDIF.
    ENDIF.

  ENDMETHOD.


  METHOD get_template.

    CALL FUNCTION 'READ_TEXT'
      EXPORTING
*       CLIENT                  = SY-MANDT
        id                      = 'ST'
        language                = iv_langu
        name                    = iv_name
        object                  = 'TEXT'
*       ARCHIVE_HANDLE          = 0
*       LOCAL_CAT               = ' '
*  IMPORTING
*       HEADER                  =
*       OLD_LINE_COUNTER        =
      TABLES
        lines                   = rt_lines
      EXCEPTIONS
        id                      = 1
        language                = 2
        name                    = 3
        not_found               = 4
        object                  = 5
        reference_check         = 6
        wrong_access_to_archive = 7
        OTHERS                  = 8.
    IF sy-subrc <> 0.
* Implement suitable error handling here
    ENDIF.

  ENDMETHOD.


  method INITIALIZE_DATA.

   "Get data initialization


  endmethod.


  method PUT_FORMAT.

    "Put special format for character
    REPLACE ALL OCCURRENCES OF '<BOLD>' IN TABLE mt_stream WITH '<b>'.
    REPLACE ALL OCCURRENCES OF '</BOLD>' IN TABLE mt_stream WITH '</b>'.
    REPLACE ALL OCCURRENCES OF '<ITALIC>' IN TABLE mt_stream WITH '<i>'.
    REPLACE ALL OCCURRENCES OF '</ITALIC>' IN TABLE mt_stream WITH '</i>'.
    REPLACE ALL OCCURRENCES OF '<ULINE>' IN TABLE mt_stream WITH '<u>'.
    REPLACE ALL OCCURRENCES OF '</ULINE>' IN TABLE mt_stream WITH '</u>'.

  endmethod.


  METHOD put_to_container.

    DATA ls_container TYPE yshr_field_value.

    ls_container-field = iv_field.
    ls_container-value = iv_value.
    APPEND ls_container TO mt_container.

  ENDMETHOD.


  METHOD read_notif_variant.

    SELECT SINGLE vbody INTO rv_template_var FROM ythrwf_notif_var WHERE notif_type = mv_notif_type
                                                                   AND   notif_var = iv_notif_var.

  ENDMETHOD.


  METHOD replace_data_from_container.

    DATA ls_container TYPE yshr_field_value.

    LOOP AT mt_container INTO ls_container.
      REPLACE ALL OCCURRENCES OF ls_container-field IN TABLE mt_stream WITH ls_container-value.
    ENDLOOP.

  ENDMETHOD.


  METHOD replace_in_body.

    me->get_data( ).
    me->replace_data_from_container( ).

  ENDMETHOD.


  METHOD replace_in_header.

    REPLACE '<OBJID>' WITH mv_objid INTO cv_string.
    REPLACE '<SHORT>' WITH mv_short INTO cv_string.

    CONDENSE cv_string.

  ENDMETHOD.


  METHOD send_mail.

    DATA : lv_result    TYPE boolean,
           lv_message   TYPE string,
           ls_mail      TYPE yshr_wf_actors,
           lv_text      TYPE soli,
           lt_att_head  TYPE soli_tab,
           lt_mail      TYPE ytthr_wf_actors,
           lt_mail_0105 TYPE tty_email.

    DATA lo_sender TYPE REF TO cl_sapuser_bcs.

    ev_subrc = 0.

    TRY.
        mo_send_request = cl_bcs=>create_persistent( ).
      CATCH cx_send_req_bcs.
        ev_subrc = 8.
        EXIT.
    ENDTRY.

    TRY.
        mo_document = cl_document_bcs=>create_document(
              i_type          = 'HTM'
              i_subject       = ' '"mois de 50
*             i_length        =
*             i_language      = SPACE
              i_importance    = '5'
*             i_sensitivity   =
              i_text          = mt_body
*             i_hex           =
*             i_header        =
*             i_sender        = lo_sender
*             iv_vsi_profile  =
                          ).
        TRY.
            "Attach document if necessary
            IF ms_document_data IS NOT INITIAL.
              IF mv_file_name IS NOT INITIAL.
                CONCATENATE '&SO_FILENAME=' mv_file_name INTO lv_text.
              ELSE.
                CONCATENATE '&SO_FILENAME=' ms_document_data-obj_descr INTO lv_text. "manage 4 digit extension note 1459896
              ENDIF.
              APPEND lv_text TO lt_att_head.
              TRY.
                  mo_document->add_attachment( i_attachment_type = ms_document_data-obj_type
                                               i_attachment_subject = ms_document_data-obj_descr
                                               i_attachment_size = ms_document_data-doc_size
                                               i_att_content_text = mt_att_content
                                               i_att_content_hex = mt_att_content_hex
                                               i_attachment_header = lt_att_head ).
                CATCH cx_document_bcs.
                  ev_subrc = 4.
              ENDTRY.
            ENDIF.

            mo_send_request->set_message_subject( ip_subject = mv_subject ).

            mo_send_request->set_document( mo_document ).

            IF iv_sender IS NOT INITIAL.
              lo_sender = cl_sapuser_bcs=>create( iv_sender ).
              mo_send_request->set_sender( lo_sender ).
            ENDIF.

            "Send to
            lt_mail = it_mail.
            me->add_subsituted_mail( CHANGING cs_mail = lt_mail ).
            LOOP AT lt_mail INTO ls_mail.
              APPEND ls_mail-email TO lt_mail_0105.
            ENDLOOP.
            IF mv_syst_category <> 'P'.
              me->filter_authorized_email( CHANGING ct_email = lt_mail_0105 ).
            ENDIF.
*          lo_send_request->set_sender( EXPORTING i_sender = lo_sender )."sender object
            LOOP AT lt_mail_0105 INTO DATA(lv_mail_0105).
              mo_recipient = cl_cam_address_bcs=>create_internet_address( lv_mail_0105 ).
              mo_send_request->add_recipient(
               EXPORTING
                 i_recipient  = mo_recipient
                 i_copy       = ' '
                 i_blind_copy = ' '
                 i_no_forward = ' ').
            ENDLOOP.

            "Copy to
            IF it_mail_copy IS NOT INITIAL.
              CLEAR lt_mail_0105.
              lt_mail = it_mail_copy.
              me->add_subsituted_mail( CHANGING cs_mail = lt_mail ).
              LOOP AT lt_mail INTO ls_mail.
                APPEND ls_mail-email TO lt_mail_0105.
              ENDLOOP.
              IF mv_syst_category <> 'P'.
                me->filter_authorized_email( CHANGING ct_email = lt_mail_0105 ).
              ENDIF.
*          lo_send_request->set_sender( EXPORTING i_sender = lo_sender )."sender object
              LOOP AT lt_mail_0105 INTO lv_mail_0105.
                mo_recipient = cl_cam_address_bcs=>create_internet_address( lv_mail_0105 ).
                mo_send_request->add_recipient(
                 EXPORTING
                   i_recipient  = mo_recipient
                   i_copy       = 'X'
                   i_blind_copy = ' '
                   i_no_forward = ' ').
              ENDLOOP.
            ENDIF.

            "No delivery return
            mo_send_request->send_request->setu_requested_status( 'N' ).

            mo_send_request->set_send_immediately( 'X' ).

            lv_result = mo_send_request->send( EXPORTING i_with_error_screen = 'X' ).
            COMMIT WORK.

          CATCH cx_document_bcs INTO DATA(v_bcs_exception).
            lv_message = v_bcs_exception->get_text( ).
            ev_subrc = 8.
            MESSAGE lv_message TYPE 'S'.
          CATCH cx_send_req_bcs INTO DATA(v_send_exception).
            lv_message = v_send_exception->get_text( ).
            ev_subrc = 8.
            MESSAGE lv_message TYPE 'S'.
          CATCH cx_address_bcs INTO DATA(v_addr_exception).
            lv_message = v_addr_exception->get_text( ).
            ev_subrc = 8.
            MESSAGE lv_message TYPE 'S'.
        ENDTRY.
      CATCH cx_document_bcs.
        ev_subrc = 8.
    ENDTRY.

  ENDMETHOD.


  method SET_ATTACHMENT.
  endmethod.


  METHOD yif_hr_wf_mail~send_wi_notification.

    DATA ls_lines TYPE tline.
    DATA lt_body  TYPE soli_tab.
    DATA lt_mail TYPE ytthr_wf_actors.

    mv_objid = iv_objid.

    mv_short = iv_short.
    mv_date_ref = iv_date_ref.
    mv_current_actor = iv_current_actor.
    mt_reason = it_reason.
    mv_subat = iv_subat.
    mv_wi_father = iv_wi_father.
    IF iv_istat IS NOT INITIAL.
      mv_istat = iv_istat.
    ENDIF.

    "Initialize data
    me->initialize_data( ).

    "get subject
    CLEAR: mt_lines, mt_stream, ms_stream, mt_body.
    mt_lines = me->get_template( iv_name = mv_notif_header ).

    me->convert_to_table_string( ).

    READ TABLE mt_stream INTO ms_stream INDEX 1.
    me->replace_in_header( CHANGING cv_string  = ms_stream ).
    mv_subject = ms_stream.

    CLEAR mt_lines.

    "get body
    mt_lines = me->get_template( iv_name = mv_notif_body ).
    me->add_template_variant( ).
    me->convert_to_table_string( ).
    "Manage attachments
    CLEAR: ms_document_data, mt_att_content, mt_att_content_hex.
    me->set_attachment( ).
    me->replace_in_body( ).
    LOOP AT mt_stream INTO ms_stream .
      CONCATENATE ms_stream '<br>' INTO ms_stream.
      REPLACE ALL OCCURRENCES OF cl_abap_char_utilities=>newline IN ms_stream WITH '<br>'.
      CLEAR lt_body.
      CALL FUNCTION 'SO_STRING_TO_TAB'
        EXPORTING
          content_str = ms_stream
        TABLES
          content_tab = lt_body.

      APPEND LINES OF lt_body TO mt_body.
    ENDLOOP.

    lt_mail  = it_actors.
    DELETE lt_mail WHERE email = space.
    IF lt_mail IS NOT INITIAL.
      me->send_mail(
        EXPORTING
          it_mail = lt_mail ).
    ENDIF.

  ENDMETHOD.


  METHOD yif_hr_wf_mail~send_wi_notification_pa.

    DATA lt_body  TYPE soli_tab.
    DATA lt_mail TYPE ytthr_wf_actors.
    DATA lt_mail_copy TYPE ytthr_wf_actors.
    DATA ls_mail TYPE LINE OF ytthr_wf_actors.

    mv_objid = iv_pernr.
    mv_date_ref = iv_date_action.
    mt_reason = it_reason.
    mv_wi_father = iv_wi_father.
    mv_massn = iv_massn.
    mv_massg = iv_massg.
    mv_wf_step = iv_wf_step.
    mv_current_actor-otype = 'US'.
    mv_current_actor-objid = iv_current_uname.
    mv_add_param_1 = iv_add_param_1.
    mv_add_param_2 = iv_add_param_2.
    mv_add_param_3 = iv_add_param_3.
    mv_add_param_4 = iv_add_param_4.

    "Initialize data
    me->initialize_data( ).

    "get subject
    CLEAR: mt_lines, mt_stream, ms_stream, mt_body.
    mt_lines = me->get_template( iv_name = mv_notif_header ).

    me->convert_to_table_string( ).

    READ TABLE mt_stream INTO ms_stream INDEX 1.
    me->replace_in_header( CHANGING cv_string  = ms_stream ).
    mv_subject = ms_stream.

    CLEAR mt_lines.
    "get body
    mt_lines = me->get_template( iv_name = mv_notif_body ).
    me->convert_to_table_string( ).
    "Manage attachments
    CLEAR: ms_document_data, mt_att_content, mt_att_content_hex.
    me->set_attachment( ).
    "Generate body
    me->replace_in_body( ).
    "Put bold, italic, underline
    me->put_format( ).
    LOOP AT mt_stream INTO ms_stream .
      CONCATENATE ms_stream '<br>' INTO ms_stream.
      REPLACE ALL OCCURRENCES OF cl_abap_char_utilities=>newline IN ms_stream WITH '<br>'.
      CLEAR lt_body.
      CALL FUNCTION 'SO_STRING_TO_TAB'
        EXPORTING
          content_str = ms_stream
        TABLES
          content_tab = lt_body.

      APPEND LINES OF lt_body TO mt_body.
    ENDLOOP.

    "Extract e-mails
    LOOP AT it_actors INTO DATA(ls_actors) WHERE email IS NOT INITIAL.
      MOVE-CORRESPONDING ls_actors TO ls_mail.
      APPEND ls_mail TO lt_mail.
    ENDLOOP.

    LOOP AT it_actors_copy INTO ls_actors WHERE email IS NOT INITIAL.
      MOVE-CORRESPONDING ls_actors TO ls_mail.
      APPEND ls_mail TO lt_mail_copy.
    ENDLOOP.

    IF lt_mail IS NOT INITIAL.
      me->send_mail( EXPORTING it_mail = lt_mail
                               it_mail_copy = lt_mail_copy
                               iv_sender = iv_sender
                     IMPORTING ev_subrc = ev_subrc ).
    ELSE.
      ev_subrc = 4.
    ENDIF.

  ENDMETHOD.
ENDCLASS.