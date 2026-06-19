class YCL_HRWF_INTERN_GOS definition
  public
  inheriting from YCL_CA_REPORT_SHARE_STATEMENTS
  final
  create public .

public section.

  data:
    mr_pernr TYPE RANGE OF p_pernr .
  data:
    mr_wf_beg TYPE RANGE OF begda .

  methods CONSTRUCTOR .
  methods GET_DATA .

  methods INIT_ALV
    redefinition .
protected section.

  methods SET_DISPLAY_SETTINGS
    redefinition .
  methods SET_ALV_COLUMNS
    redefinition .
private section.

  types:
    BEGIN OF ty_list,
      wf_id    TYPE sww_wiid,
      wi_cd    TYPE sww_cd,
      pernr    TYPE p_pernr,
      nachn    TYPE pad_nachn,
      vorna    TYPE pad_vorna,
      begda    TYPE begda,
      agrty    TYPE ye_hrint_agrty,
      wi_aed   TYPE sww_aed,
      descript TYPE sdok_descr,
      loio_id  TYPE bds_docid,
      status   TYPE p_99s_statu,
      message  TYPE bapi_msg,
    END OF ty_list .

  data:
    mt_doc_prefix TYPE TABLE OF ye_hr_intwf_attsh .
  data:
    mt_list TYPE TABLE OF ty_list .

  methods BUILD_NORMALIZED_NAME
    importing
      !IV_PERNR type P_PERNR
      !IV_BEGDA type BEGDA
    returning
      value(RV_NAME) type SDOK_DESCR .
  methods GET_DOCUMENT_KEY_FROM_ID
    importing
      !IV_LOIO_ID type BDS_DOCID
    returning
      value(RS_KEY) type YSCA_DO_DOCUMENT_ID_KEY .
  methods HANDLE_USER_COMMAND
    for event ADDED_FUNCTION of CL_SALV_EVENTS_TABLE
    importing
      !E_SALV_FUNCTION .
  methods REFRESH_ALV .
  methods UPDATE_FILE_NAME_IN_GOS .
  methods IS_ATTACHED_FILE
    importing
      !IV_DESCRIPT type SDOK_DESCR
    returning
      value(RV_IS_OK) type XFELD .
  methods GET_INTERN_AGREEMENT_FILE
    importing
      !IV_PERNR type P_PERNR
      !IV_BEGDA type BEGDA
      !IV_WF_AED type SWW_AED
    exporting
      !EV_DESCRIPT type SDOK_DESCR
      !EV_NUMBER type INT1
      !EV_LOIO_ID type BDS_DOCID .
ENDCLASS.



CLASS YCL_HRWF_INTERN_GOS IMPLEMENTATION.


  METHOD build_normalized_name.

    CLEAR rv_name.
    CHECK iv_pernr IS NOT INITIAL AND iv_begda IS NOT INITIAL.
    rv_name = |Internship agreement_{ iv_begda }_{ iv_pernr }|.

  ENDMETHOD.


  METHOD constructor.

    super->constructor( ).

    SELECT attsh FROM ythrintwf_attt WHERE sprsl = 'E' INTO TABLE @mt_doc_prefix.

  ENDMETHOD.


  METHOD get_data.

    DATA lt_wf_head TYPE TABLE OF swwwihead.
    DATA lv_return_code TYPE sy-subrc.
    DATA lt_container TYPE TABLE OF swr_cont.
    DATA ls_container TYPE swr_cont.
    DATA lv_norm_agr TYPE sdok_descr.
    DATA lv_norm_agr_r TYPE sdok_descr.
    DATA ls_list TYPE ty_list.

    "Get WF type for interns
    SELECT SINGLE wfid FROM ythrwf_type WHERE wftype = 'I1' INTO @DATA(mv_wfid).
    CHECK sy-subrc = 0.

    "Get completed WF interns
    SELECT * INTO TABLE lt_wf_head FROM swwwihead WHERE wi_type = 'F'   "Workflow
                                                  AND   top_task = mv_wfid
                                                  AND   wi_cd IN mr_wf_beg
                                                  AND   wi_stat = yomwf_c_stat_completed.

    CHECK lt_wf_head IS NOT INITIAL.

    LOOP AT lt_wf_head INTO DATA(ls_wf_head).

      CLEAR: ls_list, lv_return_code, lt_container.
      ls_list-wf_id = ls_wf_head-wi_id.
      ls_list-wi_cd = ls_wf_head-wi_cd.
      ls_list-wi_aed = ls_wf_head-wi_aed.

      CHECK ls_list-wi_cd IN mr_wf_beg.

      "Don't take cancelled workflows
      SELECT SINGLE * FROM swwwihead WHERE top_wi_id = @ls_wf_head-wi_id
                                     AND   wi_type = 'E'
                                     AND   wi_stat = @yomwf_c_stat_completed
                      INTO @DATA(ls_wi_cancelled).
      CHECK sy-subrc <> 0.

      "Get personnel number and begin date of the internship from WF container
      CALL FUNCTION 'SAP_WAPI_READ_CONTAINER'
        EXPORTING
          workitem_id      = ls_wf_head-wi_id
*         LANGUAGE         = SY-LANGU
*         USER             = SY-UNAME
*         BUFFERED_ACCESS  = 'X'
        IMPORTING
          return_code      = lv_return_code
*         IFS_XML_CONTAINER              =
*         IFS_XML_CONTAINER_SCHEMA       =
        TABLES
          simple_container = lt_container.
*         MESSAGE_LINES    =
*         MESSAGE_STRUCT   =
*         SUBCONTAINER_BOR_OBJECTS       =
*         SUBCONTAINER_ALL_OBJECTS       =

      "Get personnel number
      READ TABLE lt_container INTO ls_container WITH KEY element = 'EMPLOYEE_INTERN'.
      IF sy-subrc = 0.
        ls_list-pernr = ls_container-value+20(8).
      ENDIF.
      CHECK ls_list-pernr IN mr_pernr.

      READ TABLE lt_container INTO ls_container WITH KEY element = 'BEGDA'.
      IF sy-subrc = 0.
        ls_list-begda = ls_container-value.
      ENDIF.

      READ TABLE lt_container INTO ls_container WITH KEY element = 'AGRTY'.
      IF sy-subrc = 0.
        ls_list-agrty = ls_container-value.
      ENDIF.

      IF ls_list-pernr IS NOT INITIAL AND ls_list-begda IS NOT INITIAL.
        SELECT SINGLE nachn, vorna FROM pa0002 WHERE pernr = @ls_list-pernr
                                               AND   begda <= @ls_list-begda
                                               AND   endda >= @ls_list-begda
                 INTO ( @ls_list-nachn, @ls_list-vorna ).
      ENDIF.

      me->get_intern_agreement_file( EXPORTING iv_pernr = ls_list-pernr
                                               iv_begda = ls_list-begda
                                               iv_wf_aed = ls_list-wi_aed
                                     IMPORTING ev_descript = ls_list-descript
                                               ev_number = DATA(lv_number)
                                               ev_loio_id = ls_list-loio_id ).

      CASE lv_number.
        WHEN 0.
          WRITE icon_led_red TO ls_list-status AS ICON.
          ls_list-message = 'No agreement found'.
        WHEN 1.
          "Set the name should be
          lv_norm_agr = me->build_normalized_name( iv_pernr = ls_list-pernr
                                                   iv_begda = ls_list-begda ).
          lv_norm_agr_r = |{ lv_norm_agr }R|.
          IF ls_list-descript = lv_norm_agr OR ls_list-descript = lv_norm_agr_r.
            WRITE icon_led_green TO ls_list-status AS ICON.
          ELSE.
            WRITE icon_led_yellow TO ls_list-status AS ICON.
            ls_list-message = |The file should be { lv_norm_agr }|.
          ENDIF.
        WHEN OTHERS.
          WRITE icon_led_red TO ls_list-status AS ICON.
          ls_list-message = 'More than one agreement found'.
      ENDCASE.

      APPEND ls_list TO mt_list.

    ENDLOOP.

  ENDMETHOD.


  METHOD get_document_key_from_id.

    FIELD-SYMBOLS <key> TYPE c.

    ASSIGN iv_loio_id TO <key> CASTING.
    rs_key = <key>.

  ENDMETHOD.


  METHOD get_intern_agreement_file.

    DATA lv_objkey TYPE swo_typeid.
    DATA lt_gos TYPE TABLE OF bdn_con.
    DATA lt_file TYPE TABLE OF sdok_descr.

    CLEAR: ev_descript, ev_number, ev_loio_id.

    "Read documents from GOS
    lv_objkey = iv_pernr.
    CALL FUNCTION 'BDS_GOS_CONNECTIONS_GET'
      EXPORTING
*       LOGICAL_SYSTEM     =
        classname          = 'BUS1065'
        objkey             = lv_objkey
*       CLIENT             = SY-MANDT
      TABLES
        gos_connections    = lt_gos
      EXCEPTIONS
        no_objects_found   = 1
        internal_error     = 2
        internal_gos_error = 3
        OTHERS             = 4.

    LOOP AT lt_gos INTO DATA(ls_gos).

      "Only documents generated at the end of workflow
      CHECK ls_gos-crea_time(8) = iv_wf_aed.
      "Only for signed agreement, reject uploaded document
      CHECK me->is_attached_file( iv_descript = ls_gos-descript ) = abap_false.

      ev_descript = ls_gos-descript.
      ev_loio_id = ls_gos-loio_id.
      ADD 1 TO ev_number.

    ENDLOOP.

  ENDMETHOD.


  METHOD handle_user_command.

    DATA lv_answer TYPE char1.

    CASE e_salv_function.
      WHEN 'YUPDATE'.
        "Set popup to confirm
        lv_answer = ycl_ca_utilities=>popup_to_confirm( iv_title = 'Confirm update'
                                                        iv_text = 'Update with normalize file name (only for yellow)'
                                                        iv_cancel_button = abap_true ).
        IF lv_answer = '1'.  "Yes
          me->update_file_name_in_gos( ).
          "Refresh list
          me->refresh_alv( ).
        ELSE.
          MESSAGE 'Update cancelled' TYPE 'S'.
        ENDIF.
    ENDCASE.

  ENDMETHOD.


  METHOD init_alv.

    SORT mt_list BY wf_id.

    super->init_alv( EXPORTING iv_repid = iv_repid
                     CHANGING ct_table = mt_list ).

  ENDMETHOD.


  METHOD is_attached_file.

    DATA lv_length TYPE i.

    LOOP AT mt_doc_prefix INTO DATA(lv_prefix).
      lv_length = strlen( lv_prefix ).
      IF iv_descript(lv_length) = lv_prefix.
        rv_is_ok = abap_true.
        EXIT.
      ENDIF.
    ENDLOOP.

  ENDMETHOD.


  METHOD refresh_alv.

    TRY.
        mo_salv_table->set_data( CHANGING t_table = mt_list ).
      CATCH cx_salv_no_new_data_allowed.
    ENDTRY.

    mo_salv_table->refresh( ).

  ENDMETHOD.


  METHOD set_alv_columns.

    DATA lo_events TYPE REF TO cl_salv_events_table.

    super->set_alv_columns( ).

    mo_salv_table->set_screen_status( pfstatus      = 'SALV_STANDARD'
                                      report        = mv_repid
                                      set_functions = mo_salv_table->c_functions_all ).

    lo_events = mo_salv_table->get_event( ).
    SET HANDLER me->handle_user_command FOR lo_events.

  ENDMETHOD.


  METHOD set_display_settings.

    super->set_display_settings( ).

    mo_display_settings->set_striped_pattern( abap_true ).

  ENDMETHOD.


  METHOD update_file_name_in_gos.

    DATA lv_norm_agr TYPE sdok_descr.
    DATA ls_doc_key TYPE ysca_do_document_id_key.

    LOOP AT mt_list ASSIGNING FIELD-SYMBOL(<ls_list>) WHERE status = icon_led_yellow.
      "Get normalized name
      lv_norm_agr = me->build_normalized_name( iv_pernr = <ls_list>-pernr
                                               iv_begda = <ls_list>-begda ).
      IF lv_norm_agr IS INITIAL OR <ls_list>-loio_id IS INITIAL.
        WRITE icon_incomplete TO <ls_list>-status AS ICON.
        <ls_list>-message = |Unable to update the file description|.
        CONTINUE.
      ENDIF.

      lv_norm_agr = |{ lv_norm_agr }R|.   "Put R at the end for

      "Get document id key
      ls_doc_key = me->get_document_key_from_id( iv_loio_id = <ls_list>-loio_id ).

      "Check entry
      SELECT SINGLE objdes FROM sood WHERE objtp = @ls_doc_key-doctp
                                     AND   objyr = @ls_doc_key-docyr
                                     AND   objno = @ls_doc_key-docno
                           INTO @DATA(lv_objdes).
      IF sy-subrc <> 0.
        WRITE icon_incomplete TO <ls_list>-status AS ICON.
        <ls_list>-message = |Unable to update the file description, error in key|.
        CONTINUE.
      ENDIF.

      "Do update
      UPDATE sood SET objdes = lv_norm_agr
                  WHERE objtp = ls_doc_key-doctp
                  AND   objyr = ls_doc_key-docyr
                  AND   objno = ls_doc_key-docno.
      IF sy-subrc = 0.
        WRITE icon_led_green TO <ls_list>-status AS ICON.
        <ls_list>-message = |Update done, new name: { lv_norm_agr }|.
      ELSE.
        WRITE icon_incomplete TO <ls_list>-status AS ICON.
        <ls_list>-message = |Unable to update database|.
      ENDIF.

    ENDLOOP.

  ENDMETHOD.
ENDCLASS.