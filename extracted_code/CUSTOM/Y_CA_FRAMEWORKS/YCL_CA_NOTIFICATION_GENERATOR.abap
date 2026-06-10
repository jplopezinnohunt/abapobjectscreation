class YCL_CA_NOTIFICATION_GENERATOR definition
  public
  create protected .

public section.

  interfaces YIF_CA_NOTIFICATION .

  aliases DISPLAY_LIST
    for YIF_CA_NOTIFICATION~DISPLAY_LIST .
  aliases GET_DEFAULT_DATES
    for YIF_CA_NOTIFICATION~GET_DEFAULT_DATES .
  aliases GET_NOTIFICATION_LIST
    for YIF_CA_NOTIFICATION~GET_NOTIFICATION_LIST .
  aliases GET_PERIMETER
    for YIF_CA_NOTIFICATION~GET_PERIMETER .
  aliases SEND_NOTIFICATION
    for YIF_CA_NOTIFICATION~SEND_NOTIFICATION .
  aliases SET_SELECTION_VALUES
    for YIF_CA_NOTIFICATION~SET_SELECTION_VALUES .

  methods CONSTRUCTOR
    importing
      !IS_NOTIF_CRIT type YTCA_NOTIF .
protected section.

  aliases MT_NOTIFICATION
    for YIF_CA_NOTIFICATION~MT_NOTIFICATION .
  aliases MV_REPID
    for YIF_CA_NOTIFICATION~MV_REPID .

  data MP_YEAR type YE_CA_YEAR .
  data MV_NOTIF_TEXT type TEXT60 .
  data MP_BEGDAT type BEGDA .
  data MP_ENDDAT type ENDDA .
  data MS_NOTIF_CRIT type YTCA_NOTIF .
  data MV_PROD_SYSTEM type XFELD .
  constants C_LIST_TYPE_REPORT type CHAR1 value 'R' ##NO_TEXT.
  data MV_LIST_TYPE type CHAR1 .
  data MV_UNIQUE_ID type YE_BC_UNIQUE_ID_8 .
  data MP_DATE type DATUM .
  data MT_AUTHORIZED_MAIL type BCSY_SMTPA .
  data MO_DISPLAY_SETTINGS type ref to CL_SALV_DISPLAY_SETTINGS .
  data MO_SALV_TABLE type ref to CL_SALV_TABLE .
  data MO_SALV_FUNCTIONS_LIST type ref to CL_SALV_FUNCTIONS_LIST .
  data MO_SALV_COLUMNS_TABLE type ref to CL_SALV_COLUMNS_TABLE .
  data MO_SALV_LAYOUT type ref to CL_SALV_LAYOUT .
  data:
    mr_mailcc TYPE RANGE OF ad_smtpadr .

  methods ADD_MAIL_CC_FROM_SELECTION
    changing
      !CT_MAIL_CC type BCSY_SMTPA .
  methods ADD_TO_DATE
    importing
      !IV_DATE type DATUM
      !IV_NB_YEAR type YE_NBYEAR_2 optional
      !IV_NB_MONTH type YE_NBMONTH_2 optional
    exporting
      !EV_DATE type DATUM .
  methods SUBTRACT_TO_DATE
    importing
      !IV_DATE type DATUM
      !IV_NB_YEAR type YE_NBYEAR_2 optional
      !IV_NB_MONTH type YE_NBMONTH_2 optional
    exporting
      !EV_DATE type DATUM .
  methods PUT_REMINDER_IN_HEADER
    importing
      !IV_LANGU type SY-LANGU
    changing
      !CV_TEXT type STRING .
  methods NOTIFICATION_SENT
    importing
      !IV_UNIQUE_ID type YE_BC_UNIQUE_ID_8 .
  methods NOTIFICATION_NOT_SENT
    importing
      !IV_UNIQUE_ID type YE_BC_UNIQUE_ID_8
      !IV_MESSAGE type STRING optional .
  methods SET_ALV_COLUMNS .
  methods SET_ALV_FUNCTIONS .
  methods SET_ALV_LAYOUT .
  methods SET_ALV_OTHERS .
  methods SET_DISPLAY_SETTINGS .
  methods GET_FILTERED_MAILS .
  methods READ_TEMPLATE
    importing
      !IV_ID type TDID default 'ST'
      !IV_LANGUAGE type SPRAS default SY-LANGU
      !IV_TDNAME type TDOBNAME
      !IV_OBJECT type TDOBJECT default 'TEXT'
    returning
      value(RT_STREAM) type STRING_TABLE .
  methods SET_STREAM_TO_SOLI_TAB
    importing
      !IT_STREAM type STRING_TABLE
      !IV_CONVERT_TO_HTML type XFELD default ABAP_TRUE
    returning
      value(RT_SOLI) type SOLI_TAB .
  methods FILTER_MAIL_ADDRESS
    changing
      !CT_MAIL type BCSY_SMTPA .
private section.
ENDCLASS.



CLASS YCL_CA_NOTIFICATION_GENERATOR IMPLEMENTATION.


  METHOD ADD_MAIL_CC_FROM_SELECTION.

    DATA lt_mail_cc TYPE bcsy_smtpa.

    CHECK mr_mailcc IS NOT INITIAL.

    lt_mail_cc = ct_mail_cc.

    LOOP AT lt_mail_cc ASSIGNING FIELD-SYMBOL(<ls_mail_cc>).
      TRANSLATE <ls_mail_cc> TO UPPER CASE.
    ENDLOOP.

    LOOP AT mr_mailcc INTO DATA(ls_mailcc).
      TRANSLATE ls_mailcc-low TO UPPER CASE.
      READ TABLE lt_mail_cc TRANSPORTING NO FIELDS WITH KEY table_line = ls_mailcc-low.
      CHECK sy-subrc <> 0.
      APPEND ls_mailcc-low TO ct_mail_cc.
    ENDLOOP.

  ENDMETHOD.


  METHOD ADD_TO_DATE.

    DATA lv_month TYPE ye_nbmonth_2.

    ev_date = iv_date.

    IF iv_nb_year IS NOT INITIAL.
      ev_date(4) = ev_date(4) + iv_nb_year.
    ENDIF.

    IF iv_nb_month IS NOT INITIAL.
      lv_month = ev_date+4(2) + iv_nb_month.
      IF lv_month <= 12.
        ev_date+4(2) = lv_month.
      ELSE.
         ev_date(6) = ev_date(6) + 88 + iv_nb_month.
      ENDIF.
    ENDIF.

  ENDMETHOD.


  METHOD constructor.

    ms_notif_crit = is_notif_crit.

    "Get notification text
    SELECT SINGLE notif_text FROM ytca_notif_t WHERE sprsl = @sy-langu
                                               AND   yappl = @ms_notif_crit-yappl
                                               AND   notif_type = @ms_notif_crit-notif_type
                             INTO @mv_notif_text.

    mv_prod_system = ycl_ca_utilities=>is_production_system( ).

  ENDMETHOD.


  METHOD FILTER_MAIL_ADDRESS.

    DATA lv_mail TYPE LINE OF bcsy_smtpa.

    CHECK mv_prod_system = abap_false.

    "Filter mail
    LOOP AT ct_mail ASSIGNING FIELD-SYMBOL(<lv_mail>).
      lv_mail = <lv_mail>.
      TRANSLATE lv_mail TO UPPER CASE.
      READ TABLE mt_authorized_mail TRANSPORTING NO FIELDS WITH KEY table_line = lv_mail.
      CHECK sy-subrc <> 0.
      <lv_mail> = |{ <lv_mail> }TEST|.
    ENDLOOP.

  ENDMETHOD.


  METHOD GET_FILTERED_MAILS.

    CHECK ycl_ca_utilities=>is_production_system( ) = abap_false.

    "Get authorized mail
    SELECT ymail FROM ytbc_mail_auth WHERE yappl = @ms_notif_crit-yappl INTO TABLE @mt_authorized_mail.

  ENDMETHOD.


  method NOTIFICATION_NOT_SENT.
  endmethod.


  method NOTIFICATION_SENT.
  endmethod.


  METHOD PUT_REMINDER_IN_HEADER.

    CASE iv_langu.
      WHEN 'F'.
        cv_text = |Rappel: { cv_text }|.
      WHEN OTHERS.
        cv_text = |Reminder: { cv_text }|.
    ENDCASE.

  ENDMETHOD.


  METHOD read_template.

    DATA lt_lines TYPE tline_tab.

    CLEAR rt_stream.

    "Get mail content
    CALL FUNCTION 'READ_TEXT'
      EXPORTING
*       CLIENT                  = SY-MANDT
        id                      = iv_id
        language                = iv_language
        name                    = iv_tdname
        object                  = iv_object
*       ARCHIVE_HANDLE          = 0
*       LOCAL_CAT               = ' '
*  IMPORTING
*       HEADER                  =
*       OLD_LINE_COUNTER        =
      TABLES
        lines                   = lt_lines
      EXCEPTIONS
        id                      = 1
        language                = 2
        name                    = 3
        not_found               = 4
        object                  = 5
        reference_check         = 6
        wrong_access_to_archive = 7
        OTHERS                  = 8.

    CALL FUNCTION 'CONVERT_ITF_TO_STREAM_TEXT'
      EXPORTING
*       LANGUAGE     = SY-LANGU
        lf           = 'X'
      IMPORTING
        stream_lines = rt_stream
      TABLES
        itf_text     = lt_lines
*       TEXT_STREAM  =
      .

    "Put special format for character
    REPLACE ALL OCCURRENCES OF '<BOLD>' IN TABLE rt_stream WITH '<b>'.
    REPLACE ALL OCCURRENCES OF '</BOLD>' IN TABLE rt_stream WITH '</b>'.
    REPLACE ALL OCCURRENCES OF '<ITALIC>' IN TABLE rt_stream WITH '<i>'.
    REPLACE ALL OCCURRENCES OF '</ITALIC>' IN TABLE rt_stream WITH '</i>'.
    REPLACE ALL OCCURRENCES OF '<ULINE>' IN TABLE rt_stream WITH '<u>'.
    REPLACE ALL OCCURRENCES OF '</ULINE>' IN TABLE rt_stream WITH '</u>'.

  ENDMETHOD.


  METHOD SET_ALV_COLUMNS.

    DATA lo_column TYPE REF TO cl_salv_column_table.

    mo_salv_columns_table = mo_salv_table->get_columns( ).
    mo_salv_columns_table->set_optimize( abap_true ).

    TRY.
        lo_column ?= mo_salv_columns_table->get_column( 'UNIQUE_ID' ).
        lo_column->set_technical( abap_true ).
      CATCH cx_salv_not_found.
    ENDTRY.

  ENDMETHOD.


  METHOD SET_ALV_FUNCTIONS.

    mo_salv_functions_list = mo_salv_table->get_functions( ).
    mo_salv_functions_list->set_all( ).

  ENDMETHOD.


  METHOD SET_ALV_LAYOUT.

    DATA ls_layout_key TYPE salv_s_layout_key.

    mo_salv_layout = mo_salv_table->get_layout( ).
    ls_layout_key-report = mv_repid.
    mo_salv_layout->set_key( ls_layout_key ).
    mo_salv_layout->set_save_restriction( if_salv_c_layout=>restrict_none ).

  ENDMETHOD.


  method SET_ALV_OTHERS.
  endmethod.


  METHOD set_display_settings.

    DATA lv_title TYPE lvc_title.

    mo_display_settings = mo_salv_table->get_display_settings( ).
    mo_display_settings->set_striped_pattern( abap_true ).

    lv_title = mv_notif_text.
    mo_display_settings->set_list_header( value = lv_title ).

  ENDMETHOD.


  METHOD SET_STREAM_TO_SOLI_TAB.

    DATA lt_soli TYPE soli_tab.

    LOOP AT it_stream INTO DATA(ls_stream).
      IF ls_stream IS INITIAL.
        APPEND space TO rt_soli.
      ELSE.
        CLEAR lt_soli.
        CALL FUNCTION 'SO_STRING_TO_TAB'
          EXPORTING
            content_str = ls_stream
          TABLES
            content_tab = lt_soli.

        APPEND LINES OF lt_soli TO rt_soli.
      ENDIF.
    ENDLOOP.

    CHECK iv_convert_to_html = abap_true.

    lt_soli = rt_soli.
    CLEAR rt_soli.

    LOOP AT lt_soli INTO DATA(lv_soli).
      AT FIRST.
        APPEND '<htm><br>' TO rt_soli.
      ENDAT.
      IF lv_soli+251 IS INITIAL.
        CONCATENATE lv_soli '<br>' INTO lv_soli.
      ENDIF.
      APPEND lv_soli TO rt_soli.
      AT LAST.
        APPEND '</htm><br>' TO rt_soli.
      ENDAT.
    ENDLOOP.

  ENDMETHOD.


  METHOD SUBTRACT_TO_DATE.

    ev_date = iv_date.

    IF iv_nb_year IS NOT INITIAL.
      ev_date(4) = ev_date(4) - iv_nb_year.
    ENDIF.

    IF iv_nb_month IS NOT INITIAL.
      IF ev_date+4(2) > iv_nb_month.
        ev_date+4(2) = ev_date+4(2) - iv_nb_month.
      ELSE.
        ev_date(6) = ev_date(6) - 88 - iv_nb_month.
      ENDIF.
    ENDIF.

  ENDMETHOD.


  METHOD yif_ca_notification~check_authorization.

    DATA lv_actvt TYPE activ_auth.

    rv_subrc = 0.

    CASE iv_action.
      WHEN 'D'.
        lv_actvt = '03'.
      WHEN 'G'.
        lv_actvt = '64'.
      WHEN OTHERS.
        rv_subrc = 8.
    ENDCASE.

    IF rv_subrc = 0.
      AUTHORITY-CHECK OBJECT 'Y_CA_NOTIF'
               ID 'YAPPL' FIELD iv_appl
               ID 'Y_NOTIF_TY' FIELD iv_notif_type
               ID 'ACTVT' FIELD lv_actvt.
      rv_subrc = sy-subrc.
    ENDIF.

    IF rv_subrc <> 0 AND iv_msgty IS NOT INITIAL.

    ENDIF.

  ENDMETHOD.


  METHOD yif_ca_notification~display_list.

    mv_repid = iv_repid.

    TRY.
        CALL METHOD cl_salv_table=>factory
*      EXPORTING
*        list_display   = IF_SALV_C_BOOL_SAP=>FALSE
*        r_container    =
*        container_name =
          IMPORTING
            r_salv_table = mo_salv_table
          CHANGING
            t_table      = ct_table.
      CATCH cx_salv_msg .
    ENDTRY.

    "ALV functions activation
    me->set_alv_functions( ).

    "ALV columns
    me->set_alv_columns( ).

    "ALV layout
    me->set_alv_layout( ).

    "Display settings
    me->set_display_settings( ).

    "Others ALV proprties
    me->set_alv_others( ).

    "Display list
    mo_salv_table->display( ).

  ENDMETHOD.


  METHOD yif_ca_notification~get_default_dates.

    ev_date_ref = sy-datum.
    ev_begda_ref = sy-datum.
    ev_endda_ref = '99991231'.
    ev_year_ref = sy-datum(4).

  ENDMETHOD.


  METHOD yif_ca_notification~get_selection_data.

    CLEAR ev_per_comment.

  ENDMETHOD.


  METHOD yif_ca_notification~send_notification.

    DATA lo_send_request TYPE REF TO cl_bcs.
    DATA lo_document TYPE REF TO cl_document_bcs.
    DATA lo_sender TYPE REF TO cl_sapuser_bcs.
    DATA lo_recipient TYPE REF TO cl_cam_address_bcs.
    DATA lv_result TYPE xfeld.
    DATA lv_message TYPE string.

    me->get_filtered_mails( ).

    LOOP AT mt_notification INTO DATA(ls_notification).

      FREE: lo_send_request, lo_document, lo_sender, lo_recipient.

      me->add_mail_cc_from_selection( CHANGING ct_mail_cc = ls_notification-copy ).

      "Filter mails
      me->filter_mail_address( CHANGING ct_mail = ls_notification-dest ).
      me->filter_mail_address( CHANGING ct_mail = ls_notification-copy ).

      TRY.
          lo_send_request = cl_bcs=>create_persistent( ).
        CATCH cx_send_req_bcs.
          EXIT.
      ENDTRY.

      TRY.
          lo_document = cl_document_bcs=>create_document( i_type          = 'HTM'
                                                          i_subject       = ' '
                                                          i_importance    = '5'
                                                          i_text          = ls_notification-mail_body ).

          TRY.
              IF mv_prod_system = abap_false.
                ls_notification-mail_header = |TEST - { ls_notification-mail_header } - TEST|.
              ENDIF.
              lo_send_request->set_message_subject( ip_subject = ls_notification-mail_header ).
              lo_send_request->set_document( lo_document ).
              "Set sender
              IF ls_notification-sender IS NOT INITIAL.
                lo_send_request->set_sender( i_sender = cl_cam_address_bcs=>create_internet_address( ls_notification-sender ) ).
              ENDIF.

              "Mail recipient
              LOOP AT ls_notification-dest INTO DATA(lv_mail_address).
                lo_recipient = cl_cam_address_bcs=>create_internet_address( lv_mail_address ).
                lo_send_request->add_recipient(
                 EXPORTING
                   i_recipient  = lo_recipient
                   i_copy       = ' '
                   i_blind_copy = ' '
                   i_no_forward = ' ').
              ENDLOOP.

              "Mail copy
              LOOP AT ls_notification-copy INTO lv_mail_address.
                lo_recipient = cl_cam_address_bcs=>create_internet_address( lv_mail_address ).
                lo_send_request->add_recipient(
                 EXPORTING
                   i_recipient  = lo_recipient
                   i_copy       = 'X'
                   i_blind_copy = ' '
                   i_no_forward = ' ').
              ENDLOOP.

              "No delivery return
              lo_send_request->send_request->setu_requested_status( 'N' ).
              "Send mail immediately
              lo_send_request->set_send_immediately( 'X' ).

              lv_result = lo_send_request->send( EXPORTING i_with_error_screen = 'X' ).
              COMMIT WORK.

              me->notification_sent( iv_unique_id = ls_notification-unique_id ).

            CATCH cx_document_bcs INTO DATA(lx_bcs_exception).
              lv_message = lx_bcs_exception->get_text( ).
              me->notification_not_sent( iv_unique_id = ls_notification-unique_id
                                         iv_message = lv_message ).
            CATCH cx_send_req_bcs INTO DATA(lx_send_exception).
              lv_message = lx_send_exception->get_text( ).
              me->notification_not_sent( iv_unique_id = ls_notification-unique_id
                                         iv_message = lv_message ).
            CATCH cx_address_bcs INTO DATA(lx_addr_exception).
              lv_message = lx_addr_exception->get_text( ).
              me->notification_not_sent( iv_unique_id = ls_notification-unique_id
                                         iv_message = lv_message ).
          ENDTRY.

        CATCH cx_document_bcs INTO DATA(lx_document_bcs).
          lv_message = lx_document_bcs->get_text( ).
          me->notification_not_sent( iv_unique_id = ls_notification-unique_id
                                     iv_message = lv_message ).
      ENDTRY.

    ENDLOOP.

  ENDMETHOD.


  METHOD yif_ca_notification~set_selection_values.

    FIELD-SYMBOLS <lt_range> TYPE ANY TABLE.
    FIELD-SYMBOLS <lv_param> TYPE any.
    DATA lv_selname TYPE fieldname.

    lv_selname = iv_selname.
    CASE iv_kind.
      WHEN 'S'.   "SELECT-OPTIONS
        REPLACE 'S_' IN lv_selname WITH 'MR_'.
        ASSIGN (lv_selname) TO <lt_range>.
        CHECK <lt_range> IS ASSIGNED.
        <lt_range> = it_value.
      WHEN 'P'. "PARAMETERS
        REPLACE 'P_' IN lv_selname WITH 'MP_'.
        ASSIGN (lv_selname) TO <lv_param>.
        CHECK <lv_param> IS ASSIGNED.
        <lv_param> = iv_value.
    ENDCASE.

  ENDMETHOD.
ENDCLASS.