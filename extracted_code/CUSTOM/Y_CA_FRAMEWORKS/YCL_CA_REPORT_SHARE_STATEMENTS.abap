class YCL_CA_REPORT_SHARE_STATEMENTS definition
  public
  create public .

public section.

  methods DISPLAY_ALV .
  methods INIT_ALV
    importing
      !IV_REPID type SY-REPID default SY-REPID
    changing
      !CT_TABLE type ANY TABLE optional .
  methods SET_SELECTION_VALUES
    importing
      !IV_SELNAME type RSSCR_NAME
      !IV_KIND type RSSCR_KIND
      !IV_VALUE type ANY optional
      !IT_VALUE type ANY TABLE optional .
protected section.

  data MO_DISPLAY_SETTINGS type ref to CL_SALV_DISPLAY_SETTINGS .
  data MO_SALV_TABLE type ref to CL_SALV_TABLE .
  data MV_REPID type SY-REPID .
  data MO_SALV_FUNCTIONS_LIST type ref to CL_SALV_FUNCTIONS_LIST .
  data MO_SALV_COLUMNS_TABLE type ref to CL_SALV_COLUMNS_TABLE .
  data MO_SALV_LAYOUT type ref to CL_SALV_LAYOUT .

  methods SET_ALV_COLUMNS .
  methods SET_ALV_FUNCTIONS .
  methods SET_ALV_LAYOUT .
  methods SET_ALV_OTHERS .
  methods SET_DISPLAY_SETTINGS .
private section.
ENDCLASS.



CLASS YCL_CA_REPORT_SHARE_STATEMENTS IMPLEMENTATION.


  METHOD display_alv.

    "Display list
    mo_salv_table->display( ).

  ENDMETHOD.


  METHOD init_alv.

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

  ENDMETHOD.


  METHOD set_alv_columns.

    mo_salv_columns_table = mo_salv_table->get_columns( ).
    mo_salv_columns_table->set_optimize( abap_true ).

  ENDMETHOD.


  METHOD set_alv_functions.

    mo_salv_functions_list = mo_salv_table->get_functions( ).
    mo_salv_functions_list->set_all( ).

  ENDMETHOD.


  METHOD set_alv_layout.

    DATA ls_layout_key TYPE salv_s_layout_key.

    mo_salv_layout = mo_salv_table->get_layout( ).
    ls_layout_key-report = mv_repid.
    mo_salv_layout->set_key( ls_layout_key ).
    mo_salv_layout->set_save_restriction( if_salv_c_layout=>restrict_none ).

  ENDMETHOD.


  method SET_ALV_OTHERS.
  endmethod.


  METHOD set_display_settings.

    mo_display_settings = mo_salv_table->get_display_settings( ).

  ENDMETHOD.


  METHOD SET_SELECTION_VALUES.

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