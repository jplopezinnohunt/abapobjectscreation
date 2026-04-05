*&---------------------------------------------------------------------*
*& Include          ZRHR_PRINT_LOG_ALV_DATA
*&---------------------------------------------------------------------*
DATA: ok_code_9001 LIKE sy-ucomm,
      ok_code      LIKE sy-ucomm.
DATA : g_container_9001        TYPE scrfname VALUE 'ALV_9001',
      g_grid_9001             TYPE REF TO cl_gui_alv_grid,
      g_layout_9001           TYPE lvc_s_layo,
      g_custom_container_9001 TYPE REF TO cl_gui_custom_container,
      t_fieldcat_9001         TYPE STANDARD TABLE OF lvc_s_fcat,
      w_layout_9001           TYPE lvc_s_layo,
      lt_celltab TYPE lvc_t_styl.
DATA : t_dyntable           TYPE REF TO DATA,
       w_dynline TYPE REF TO DATA.
DATA : lt_sort TYPE  LVC_T_SORT,
       wa_sort like line of lt_sort.
DATA : gv_nbr_col type i.
DATA : gv_col_name(6),
       gv_col_lenn(6).
FIELD-SYMBOLS : <t_data>  TYPE STANDARD TABLE,
                <fs_data>           TYPE any,
                <fs_fldval>         TYPE any,
                <t_data_copy> TYPE STANDARD TABLE .
TYPES : BEGIN OF t_output,
  LINE(150),
END OF t_output.
DATA : gt_output TYPE TABLE OF t_output WITH HEADER LINE.
TYPES : begin of t_columns,
          COL1(100),
          COL2(100),
          COL3(100),
          COL4(100),
          COL5(100),
          COL6(100),
          COL7(100),
          COL8(100),
          COL9(100),
          COL10(100),
          COL11(100),
          COL12(100),
          COL13(100),
          COL14(100),
          COL15(100),
          COL16(100),
          COL17(100),
          COL18(100),
          COL19(100),
          COL20(100),
        end of t_columns.
DATA : gt_columns type table of t_columns with header line.
DATA : wa_columns like line of gt_columns.