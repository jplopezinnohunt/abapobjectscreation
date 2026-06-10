class YCL_WF_CHECK_DATA definition
  public
  create public .

public section.

  interfaces YIF_WF_CHECK_DATA .

  aliases MT_OBJEC
    for YIF_WF_CHECK_DATA~MT_OBJEC .
  aliases MT_PARAMS
    for YIF_WF_CHECK_DATA~MT_PARAMS .
  aliases MV_ONLY_ERROR
    for YIF_WF_CHECK_DATA~MV_ONLY_ERROR .
  aliases MV_REPID
    for YIF_WF_CHECK_DATA~MV_REPID .

  class-methods GET_INSTANCE
    importing
      !IV_CLASS_NAME type CLASSNAME default 'YCL_WF_CHECK_DATA'
    returning
      value(RO_INSTANCE) type ref to YIF_WF_CHECK_DATA .
PROTECTED SECTION.

  DATA mv_title TYPE lvc_title VALUE 'Check Data for WF' ##NO_TEXT.
  DATA mo_salv_table TYPE REF TO cl_salv_table .
  DATA mv_date_ref TYPE datum .
  CLASS-DATA mo_instance TYPE REF TO yif_wf_check_data .
  DATA mo_columns TYPE REF TO cl_salv_columns_table .
  DATA mo_display_settings TYPE REF TO cl_salv_display_settings .
  DATA mo_footer TYPE REF TO cl_salv_form_layout_grid .
  DATA mo_functions TYPE REF TO cl_salv_functions_list .
  DATA mo_header TYPE REF TO cl_salv_form_layout_grid .
  DATA mo_layout TYPE REF TO cl_salv_layout .
  DATA mt_1000 TYPE TABLE OF hrp1000.

  METHODS get_1000_data .
  METHODS display .
  METHODS get_and_check_data .
  METHODS init_alv .
  METHODS set_alv_attributes .
  METHODS set_columns .
  METHODS set_display_settings .
  METHODS set_functions .
  METHODS set_layout .
  METHODS get_selection_data .
private section.
ENDCLASS.



CLASS YCL_WF_CHECK_DATA IMPLEMENTATION.


  METHOD display.

    IF mo_header IS NOT INITIAL.
      mo_salv_table->set_top_of_list( mo_header ).
    ENDIF.

    IF mo_footer IS NOT INITIAL.
      mo_salv_table->set_end_of_list( mo_footer ).
    ENDIF.

    mo_salv_table->display( ).

  ENDMETHOD.


  METHOD get_1000_data.

    "Get infotypes 1000 for objects
    SELECT * FROM hrp1000 AS p
        FOR ALL ENTRIES IN @mt_objec
          WHERE p~plvar = @mt_objec-plvar
          AND   p~otype = @mt_objec-otype
          AND   p~objid = @mt_objec-objid
          AND   p~istat = @mt_objec-istat
          AND   p~endda >= @mv_date_ref
          AND   p~langu = 'E'
        INTO TABLE @mt_1000.

    SORT mt_1000.

  ENDMETHOD.


  method GET_AND_CHECK_DATA.
  endmethod.


  METHOD get_instance.

    IF mo_instance IS INITIAL.
      CREATE OBJECT mo_instance TYPE (iv_class_name).
    ENDIF.

    ro_instance = mo_instance.

  ENDMETHOD.


  method GET_SELECTION_DATA.
  endmethod.


  METHOD init_alv.

*    TRY.
*        CALL METHOD cl_salv_table=>factory
**      EXPORTING
**        list_display   = IF_SALV_C_BOOL_SAP=>FALSE
**        r_container    =
**        container_name =
*          IMPORTING
*            r_salv_table = mo_salv_table
*          CHANGING
*            t_table      = it_table.
*      CATCH cx_salv_msg .
*    ENDTRY.

  ENDMETHOD.


  method SET_ALV_ATTRIBUTES.

    "ALV functions activation
    me->set_functions( ).

    "ALV columns
    me->set_columns( ).

    "ALV layout
    me->set_layout( ).

    "ALV display settings
    me->set_display_settings( ).

  endmethod.


  METHOD set_columns.

    mo_columns = mo_salv_table->get_columns( ).
    "Column width optimization
    mo_columns->set_optimize( abap_true ).

  ENDMETHOD.


  METHOD set_display_settings.

    mo_display_settings = mo_salv_table->get_display_settings( ).
    mo_display_settings->set_list_header( mv_title ).

  ENDMETHOD.


  METHOD set_functions.

    mo_functions = mo_salv_table->get_functions( ).
    mo_functions->set_all( ).

  ENDMETHOD.


  METHOD set_layout.

    DATA ls_layout_key TYPE salv_s_layout_key.

    mo_layout = mo_salv_table->get_layout( ).
    ls_layout_key-report = mv_repid.
    mo_layout->set_key( ls_layout_key ).
    mo_layout->set_save_restriction( if_salv_c_layout=>restrict_none ).
    mo_layout->set_default( abap_true ).

  ENDMETHOD.


  method YIF_WF_CHECK_DATA~CHECK_DATA.

    mv_date_ref = iv_date.
    me->get_selection_data( ).
    me->get_and_check_data( ).

  endmethod.


  METHOD yif_wf_check_data~display_alv.

    me->init_alv( ).
    me->set_alv_attributes( ).
    me->display( ).

  ENDMETHOD.


  METHOD yif_wf_check_data~set_params.

    DATA lt_range TYPE RANGE OF tvarv_val.
    DATA ls_params TYPE rsparams.
    FIELD-SYMBOLS <ls_data> TYPE any.

    ls_params-selname = iv_selname.
    ls_params-kind = iv_kind.

    CASE iv_kind.
      WHEN 'P'.
        ls_params-low = iv_data.
        APPEND ls_params TO mt_params.
      WHEN 'S'.
        LOOP AT it_data ASSIGNING <ls_data>.
          MOVE-CORRESPONDING <ls_data> TO ls_params.
          APPEND ls_params TO mt_params.
        ENDLOOP.
    ENDCASE.

  ENDMETHOD.
ENDCLASS.