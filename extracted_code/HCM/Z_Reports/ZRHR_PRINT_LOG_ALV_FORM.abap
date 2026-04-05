*&---------------------------------------------------------------------*
*& Include          ZRHR_PRINT_LOG_ALV_FORM
*&---------------------------------------------------------------------*
*&---------------------------------------------------------------------*
*& Form ALIM_FIELDCAT_9001
*&---------------------------------------------------------------------*
*& text
*&---------------------------------------------------------------------*
*& -->  p1        text
*& <--  p2        text
*&---------------------------------------------------------------------*
FORM ALIM_FIELDCAT_9001 .
  DATA: lw_fieldcat TYPE lvc_s_fcat.
  DATA : lv_max_len TYPE I,
        lv_pos TYPE I,
        lv_len TYPE I,
        lv_i TYPE I,
        lv_c(2),
        lv_name(20),
        lv_name2(20),
        lv_name3(20),
        lv_name4(20),
        lv_name5(20),
        lv_name6(20).
  REFRESH t_fieldcat_9001.
  Do gv_nbr_col times.
    clear : lv_name, lv_name2, lv_name3,
            lv_name4, lv_name5, lv_name6.
    ADD 1 to lv_i.
    move lv_i to lv_c.
    concatenate 'p_f' lv_c into lv_name.
    assign (lv_name) to field-symbol(<P_Fx>).
    concatenate 'p_l' lv_c into lv_name2.
    assign (lv_name2) to field-symbol(<P_Lx>).
    concatenate 'COL' lv_c into lv_name3.
    CONCATENATE 'p_reft' lv_c INTO lv_name4.
    ASSIGN (lv_name4) TO FIELD-SYMBOL(<P_REFT>).
    CONCATENATE 'p_reff' lv_c INTO lv_name5.
    ASSIGN (lv_name5) TO FIELD-SYMBOL(<P_REFF>).
    CONCATENATE 'p_chck' lv_c INTO lv_name6.
    ASSIGN (lv_name6) TO FIELD-SYMBOL(<P_chck>).
      CLEAR lw_fieldcat.
      if <P_Fx> is assigned and <P_Fx> is not initial.
        lw_fieldcat-fieldname = lv_name3.
        move <P_Fx> to lw_fieldcat-scrtext_l .
        move <P_Fx> to lw_fieldcat-COLTEXT .
        if <P_Lx> is assigned and <P_Lx> is not initial.
          move <P_Lx> to lw_fieldcat-outputlen .
          move <P_Lx> to lw_fieldcat-intlen .
        endif.
        move lv_i to lw_fieldcat-col_pos .
        if <P_REFT> is assigned and <P_REFT> is not initial.
          move <P_REFT> to lw_fieldcat-REF_TABLE  .
        endif.
        if <P_REFF> is assigned and <P_REFF> is not initial.
          move <P_REFF> to lw_fieldcat-REF_FIELD  .
        endif.
        "lw_fieldcat-HOTSPOT = 'X'.
        lw_fieldcat-col_opt = 'X'.
        if <P_chck> is assigned and <P_chck> is not initial.
          move <P_chck> to lw_fieldcat-CHECKBOX  .
          lw_fieldcat-EDIT = 'X'.
        endif.
        APPEND lw_fieldcat TO t_fieldcat_9001.
      endif.
  ENDDO.
  CLEAR lw_fieldcat.
  "lw_fieldcat-outputlen = 15.
  lw_fieldcat-fieldname = 'CELLTAB'.
  lw_fieldcat-no_out = 'X'.
  lw_fieldcat-col_opt = 'X'.
  lw_fieldcat-TECH = 'X'.
  lw_fieldcat-REF_FIELD = TEXT-T28.  "Cat. absence/prés.
  lw_fieldcat-col_pos = gv_nbr_col + 1.
  lw_fieldcat-ref_table   = 'ZHRWDB_TAB'.
  APPEND lw_fieldcat TO t_fieldcat_9001.
  CLEAR lw_fieldcat.
  "lw_fieldcat-outputlen = 15.
  lw_fieldcat-fieldname = 'CELL_COLOR'.
  lw_fieldcat-no_out = 'X'.
  lw_fieldcat-col_opt = 'X'.
  lw_fieldcat-TECH = 'X'.
  lw_fieldcat-REF_FIELD = 'CELL_COLOR'.  "CELL_COLOR
  lw_fieldcat-col_pos = gv_nbr_col + 2.
  lw_fieldcat-ref_table   = 'ZHR_LEA_GET'.
  APPEND lw_fieldcat TO t_fieldcat_9001.
  CLEAR lw_fieldcat.
  "lw_fieldcat-outputlen = 15.
  lw_fieldcat-fieldname = 'LINE_COLOR'.
  lw_fieldcat-no_out = 'X'.
  lw_fieldcat-col_opt = 'X'.
  lw_fieldcat-TECH = 'X'.
  lw_fieldcat-REF_FIELD = TEXT-T51.  "LINE_COLOR
  lw_fieldcat-col_pos = gv_nbr_col + 3.
  lw_fieldcat-ref_table   = 'ZHR_LEA_GET'.
  lw_fieldcat-REF_FIELD = 'LINE_COLOR'.
  APPEND lw_fieldcat TO t_fieldcat_9001.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form TRANSFER_DATA_9001
*&---------------------------------------------------------------------*
*& text
*&---------------------------------------------------------------------*
*& -->  p1        text
*& <--  p2        text
*&---------------------------------------------------------------------*
FORM TRANSFER_DATA_9001 .
  DATA: s_variant  TYPE disvariant,
        s_save,
        t_excl_opt TYPE ui_functions,
        w_excl_opt TYPE ui_func.
  DATA : lw_celltab  TYPE lvc_s_styl.
  DATA : lt_celltab TYPE lvc_t_styl.
  DATA : lt_cell_color type LVC_T_SCOL,
         lw_cell       TYPE lvc_s_scol.
  DATA : lv_date type datum.
"Alimentation de la table output <t_data>
     if <t_data> is assigned and <t_data>[] is not initial.
     else.
      CALL METHOD cl_alv_table_create=>create_dynamic_table
      EXPORTING
        it_fieldcatalog = t_fieldcat_9001
      IMPORTING
        ep_table        = t_dyntable.
      ASSIGN:
        t_dyntable->*     TO <t_data>.
      ASSIGN:
        t_dyntable->*     TO <t_data>.
      CALL METHOD cl_alv_table_create=>create_dynamic_table
      EXPORTING
        it_fieldcatalog = t_fieldcat_9001
      IMPORTING
        ep_table        = t_dyntable.
      IF sy-subrc EQ 0.
          IF <t_data> IS ASSIGNED AND <fs_data> IS ASSIGNED.
            FREE : <t_data> , <fs_data>.
          ENDIF.
*       Créer structure dynamique
          CREATE DATA:
                w_dynline LIKE LINE OF <t_data>.
          ASSIGN:
                w_dynline->*      TO <fs_data>.
          LOOP AT pt_in.
            SPLIT pt_in-low AT p_separ INTO
                wa_columns-col1
                wa_columns-col2
                wa_columns-col3
                wa_columns-col4
                wa_columns-col5
                wa_columns-col6
                wa_columns-col7
                wa_columns-col8
                wa_columns-col9
                wa_columns-col10
                wa_columns-col11
                wa_columns-col12
                wa_columns-col13
                wa_columns-col14
                wa_columns-col15
                wa_columns-col16
                wa_columns-col17
                wa_columns-col18
                wa_columns-col19
                wa_columns-col20.
            move-corresponding wa_columns to  <fs_data>.
*            lw_celltab-fieldname = 'TRAITER'.
**            if <split>-no_modif = 'X'.
**             lw_celltab-style     = cl_gui_alv_grid=>mc_style_disabled.
**            else.
*             lw_celltab-style     = cl_gui_alv_grid=>mc_style_enabled.
**            endif.
*            APPEND lw_celltab TO lt_celltab.
*            PERFORM f_update_wa USING 'CELLTAB'  lt_celltab.
            APPEND <fs_data> TO <t_data>.
            "APPEND <fs_data> TO <t_data_copy>.
          ENDLOOP.
        endif.
     endif.
      CREATE OBJECT g_custom_container_9001
        EXPORTING
          container_name = g_container_9001.
*  *   Instantiate ALV grid control
      CREATE OBJECT g_grid_9001
        EXPORTING
          i_parent = g_custom_container_9001.
      IF cl_gui_alv_grid=>offline( ) IS INITIAL.
        CREATE OBJECT go_event_alv.
*        SET HANDLER:
*        go_event_alv->handle_double_click_9001 FOR g_grid_9001,
*
*        go_event_alv->handle_data_changed      FOR g_grid_9001,
*
*        go_event_alv->h_hotspot_click          FOR g_grid_9001,
*
*        go_event_alv->h_handle_usr_comm        FOR g_grid_9001,
*
*        go_event_alv->h_handle_toolbar         FOR g_grid_9001.
      ENDIF.
    CLEAR w_layout_9001.
    "w_layout_9001-col_opt = 'X'.
    w_layout_9001-STYLEFNAME = 'CELLTAB'.
    w_layout_9001-SEL_MODE = 'D'.
*    w_layout-no_hgridln = ' '.
    w_layout_9001-info_fname = 'LINE_COLOR'.
    w_layout_9001-ctab_fname = 'CELL_COLOR'.
*** Fonctionalités Ã  masquer
  PERFORM f_exclure_options CHANGING t_excl_opt.
**Sort
   PERFORM sort_rules changing lt_sort.
** Affichage ALV
    CALL METHOD g_grid_9001->set_table_for_first_display
      EXPORTING
        is_layout                     = w_layout_9001
        it_toolbar_excluding          = t_excl_opt
      CHANGING
        it_outtab                     = <t_data>
        it_fieldcatalog               = t_fieldcat_9001
        it_sort                       = lt_sort
      EXCEPTIONS
        invalid_parameter_combination = 1
        program_error                 = 2
        too_many_lines                = 3
        OTHERS                        = 4.
    IF sy-subrc NE 0.
      MESSAGE ID sy-msgid
      TYPE sy-msgty
      NUMBER sy-msgno
      WITH sy-msgv1 sy-msgv2 sy-msgv3 sy-msgv4.
    ENDIF.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form HOW_MANY_COLUMNS
*&---------------------------------------------------------------------*
*& text
*&---------------------------------------------------------------------*
*& -->  p1        text
*& <--  p2        text
*&---------------------------------------------------------------------*
FORM HOW_MANY_COLUMNS .
  DATA : lv_i type i.
  DATA : lv_c(2).
  "break rchafia.
  Do 15 times.
    add 1 to lv_i.
    move lv_i to lv_c.
    concatenate 'p_f' lv_c into gv_col_name.
    assign (gv_col_name) to field-symbol(<fs_col_name>).
    assign (gv_col_lenn) to field-symbol(<fs_col_lenn>).
*    if <fs_col_name> is assigned and <fs_col_name> is not initial.
      add 1 to gv_nbr_col.
      if <fs_col_lenn> is assigned and <fs_col_lenn> is initial.
         "move 10 to <fs_col_lenn>.
      endif.
*    else.
*      exit.
*    endif.
  enddo.
  IF P_TITRE IS INITIAL.
    P_titre = 'Titre à renseigner'.
  ENDIF.
  IF p_separ is initial.
    p_separ = '/'.
  ENDIF.
*Test fields
  IF SY-SYSID = 'D01'.
    pt_in-SIGN = 'I'. pt_in-OPTION = 'EQ'.
    IF p_line1 is not initial.
      pt_in-low = p_line1.
      append pt_in.
    endif.
    IF p_line2 IS NOT INITIAL.
      pt_in-low = p_line2.
      append pt_in.
    ENDIF.
    IF p_line3 IS NOT INITIAL.
      pt_in-low = p_line3.
      append pt_in.
    ENDIF.
    IF p_line4 IS NOT INITIAL.
      pt_in-low = p_line4.
      append pt_in.
    ENDIF.
  ENDIF.
ENDFORM.
*&---------------------------------------------------------------------*
*& Form F_ADD_BUTTON
*&---------------------------------------------------------------------*
*& text
*&---------------------------------------------------------------------*
*&      <-- E_OBJECT_>MT_TOOLBAR
*&---------------------------------------------------------------------*
FORM f_add_button  CHANGING  pt_toolbar TYPE ttb_button.
  DATA:
    lw_toolbar  TYPE stb_button.
  CLEAR lw_toolbar.
** Bouton de SELECT ALL
*  CLEAR lw_toolbar.
*  lw_toolbar-function = 'SELALL' . " SELECT ALL
*  lw_toolbar-icon     = ICON_SELECT_ALL.
*  lw_toolbar-text     = '' . " SELECT ALL.
*  APPEND lw_toolbar TO pt_toolbar.
*
*
*  CLEAR lw_toolbar.
*
** Bouton de DESELECT ALL
*  CLEAR lw_toolbar.
*  lw_toolbar-function = 'DESELALL' . " DESELECT ALL
*  lw_toolbar-icon     = ICON_DESELECT_ALL.
*  lw_toolbar-text     = '' . " DESELECT ALL.
*  APPEND lw_toolbar TO pt_toolbar.
ENDFORM.
*&---------------------------------------------------------------------*
*&      Form  F_HANDLE_HOTSPOT
*&---------------------------------------------------------------------*
*       Pour Case à cocher
*----------------------------------------------------------------------*
FORM f_handle_hotspot  USING  ip_e_row_id    TYPE lvc_s_row
                              ip_e_column_id TYPE lvc_s_col.
  DATA : l_valid       TYPE flag,
         lt_cell       TYPE lvc_t_cell,
         l_index       TYPE sy-tabix,
         lw_is_stable  TYPE lvc_s_stbl.
  FIELD-SYMBOLS:
    <lfs_cell>     TYPE lvc_s_cell,
    <lt_data_tmp>  TYPE STANDARD TABLE,
    <lfs_data>     TYPE any,
    <lfs_data_old>  TYPE any,
    <lfs_fldval_t> TYPE any,
    <lfs_data_tmp> TYPE any,
    <lfs_value>    TYPE ANY,
    <lfs_value_old>    TYPE ANY,
    <NO_MODIF>  TYPE ANY.
  CALL METHOD g_grid_9001->check_changed_data
    IMPORTING
      e_valid = l_valid.
  IF NOT l_valid IS INITIAL.
    CALL METHOD g_grid_9001->get_selected_cells
      IMPORTING
        et_cell = lt_cell.
    READ TABLE lt_cell ASSIGNING <lfs_cell> INDEX 1.
    IF SY-SUBRC IS INITIAL.
      MOVE <lfs_cell>-row_id TO l_index.
*      ASSIGN:
*        t_dyntable->*   TO <lt_data_tmp>.
*      READ TABLE <t_data_copy> assigning <lfs_data_old>
*           INDEX l_index.
*
*
*      READ TABLE <t_data> assigning <lfs_data>
*           INDEX l_index.
*      ASSIGN COMPONENT 'NO_MODIF'
*         of structure <lfs_data> to <NO_MODIF>.
*      check <NO_MODIF> is initial.
*
*      ASSIGN COMPONENT <lfs_cell>-COL_ID-FIELDNAME
*         of structure <lfs_data_old> to <lfs_value_old>.
*
*
*      ASSIGN COMPONENT <lfs_cell>-COL_ID-FIELDNAME
*         of structure <lfs_data> to <lfs_value>.
*
*      IF <lfs_value> is assigned and <lfs_value_old> is assigned.
*         if <lfs_value_old> is initial.
*            <lfs_value_old> = 'X'.
*         else.
*            clear <lfs_value_old>.
*         endif.
*         move-corresponding <lfs_data_old> to <lfs_data>.
*      ENDIF.
     ENDIF.
      CALL METHOD g_grid_9001->refresh_table_display
        EXPORTING
          is_stable = lw_is_stable.
  endif.
ENDFORM.                    " F_HANDLE_HOTSPOT
*&---------------------------------------------------------------------*
*& Form SORT_RULES
*&---------------------------------------------------------------------*
*& text
*&---------------------------------------------------------------------*
*&      <-- LT_SORT
*&---------------------------------------------------------------------*
FORM SORT_RULES  CHANGING P_LT_SORT TYPE  LVC_T_SORT.
*   wa_sort-SPOS = '1'.
*   wa_sort-FIELDNAME = 'PERNR'.
*   wa_sort-UP = 'X'.
**   wa_sort-DOWN = 'X'.
*   append wa_sort to lt_sort.
*   wa_sort-SPOS = '2'.
*   wa_sort-FIELDNAME = 'NACHN'.
*   wa_sort-UP = 'X'.
**   wa_sort-DOWN = 'X'.
*   append wa_sort to lt_sort.
*   wa_sort-SPOS = '3'.
*   wa_sort-FIELDNAME = 'VORNA'.
*   wa_sort-UP = 'X'.
**   wa_sort-DOWN = 'X'.
*   APPEND wa_sort TO lt_sort.
*   wa_sort-SPOS = '4'.
*   wa_sort-FIELDNAME = 'WORKDATE'.
*   wa_sort-UP = 'X'.
**   wa_sort-DOWN = 'X'.
*   APPEND wa_sort TO lt_sort.
ENDFORM.
*&---------------------------------------------------------------------*
*&      Form  F_UPDATE_WA
*&---------------------------------------------------------------------*
*       Update specific field of <FS_DATA>
*----------------------------------------------------------------------*
FORM f_update_wa USING ip_fieldname   TYPE ANY
                       ip_fieldvalue  TYPE ANY.
  ASSIGN COMPONENT  ip_fieldname
  OF STRUCTURE <fs_data> TO <fs_fldval>.
  IF sy-subrc EQ 0.
    MOVE ip_fieldvalue TO <fs_fldval>.
  ENDIF.
ENDFORM.                    " F_UPDATE_WA
*&---------------------------------------------------------------------*
*& Form DESABLE_TEST_PERAMETERS
*&---------------------------------------------------------------------*
*& text
*&---------------------------------------------------------------------*
*& -->  p1        text
*& <--  p2        text
*&---------------------------------------------------------------------*
FORM DESABLE_TEST_PERAMETERS .
IF SY-SYSID NE 'D01' OR SY-UNAME NE 'R_CHAFIA' .
  LOOP AT SCREEN .
    IF  SCREEN-name = 'P_LINE1' OR
        SCREEN-name = 'P_LINE2' OR
        SCREEN-name = 'P_LINE3' OR
        SCREEN-name = 'P_LINE4'.
      "SCREEN-invisible = '1'.
      screen-active = '0'.
      screen-input = '0'.
      MODIFY SCREEN.
    ENDIF.
  ENDLOOP.
ENDIF.
ENDFORM.
*&---------------------------------------------------------------------*
*&      Form  F_EXCLURE_OPTIONS
*&---------------------------------------------------------------------*
*       Exclure des options du toolbar
*----------------------------------------------------------------------*
FORM f_exclure_options  CHANGING pt_exclude TYPE ui_functions.
    DATA : w_excl_opt TYPE ui_func.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_subtot.
    APPEND w_excl_opt TO pt_exclude.
*    w_excl_opt = cl_gui_alv_grid=>mc_mb_sum.
*    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_graph.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_info.
    APPEND w_excl_opt TO pt_exclude.
*    w_excl_opt = cl_gui_alv_grid=>mc_fc_print_back.
*    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_detail.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_find_more.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_to_office.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_call_abc.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_view_grid.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_copy_row.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_delete_row.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_append_row.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_insert_row.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_move_row.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_copy.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_cut.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_paste.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_paste_new_row.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_loc_undo.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_graph.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_views.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_info.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_check.
    APPEND w_excl_opt TO pt_exclude.
    w_excl_opt = cl_gui_alv_grid=>mc_fc_refresh.
    APPEND w_excl_opt TO pt_exclude.
ENDFORM.                    " F_EXCLURE_OPTIONS