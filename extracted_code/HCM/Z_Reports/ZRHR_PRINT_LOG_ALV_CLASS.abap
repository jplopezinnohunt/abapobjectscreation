*&---------------------------------------------------------------------*
*& Include          ZRHR_PRINT_LOG_ALV_CLASS
*&---------------------------------------------------------------------*
* ==================
* EVENEMENT POUR ALV
* ==================
CLASS lcl_ils DEFINITION.
  PUBLIC SECTION.
    METHODS: on_dblclick FOR EVENT double_click
            OF cl_gui_alv_grid IMPORTING e_row e_column.
ENDCLASS.                    "lcl_ils DEFINITION
DATA alv_dblclick TYPE REF TO lcl_ils.
DATA alv_hotspot  TYPE REF TO lcl_ils.
*---------------------------------------------------------------------*
*       CLASS lcl_eventhandler DEFINITION
*---------------------------------------------------------------------*
*
*---------------------------------------------------------------------*
CLASS lcl_eventhandler DEFINITION.
  PUBLIC SECTION.
    CLASS-METHODS:
      handle_double_click_9001 FOR EVENT double_click OF cl_gui_alv_grid
        IMPORTING e_row e_column es_row_no,
      h_handle_toolbar  FOR EVENT toolbar
                    OF cl_gui_alv_grid
              IMPORTING e_object,
      h_handle_usr_comm FOR EVENT user_command
                          OF cl_gui_alv_grid
              IMPORTING e_ucomm,
      handle_data_changed for event data_changed of cl_gui_alv_grid
              importing er_data_changed,
      h_hotspot_click  for event hotspot_click of cl_gui_alv_grid
              importing e_row_id
                        e_column_id.
.
ENDCLASS.                    "lcl_eventhandler DEFINITION
*---------------------------------------------------------------------*
*       CLASS lcl_eventhandler IMPLEMENTATION
*---------------------------------------------------------------------*
CLASS lcl_eventhandler IMPLEMENTATION.
  METHOD handle_double_click_9001.
    IF e_row IS NOT INITIAL.
    ENDIF.
  ENDMETHOD.                    "handle_hotspot_click
  method h_hotspot_click.
    perform f_handle_hotspot using  e_row_id
                                    e_column_id.
  endmethod.                    "h_hotspot_click
* Méthode pour ajouter les boutons
  METHOD h_handle_toolbar.
*   Ajouter les boutons de commande pour le user
    PERFORM f_add_button CHANGING e_object->mt_toolbar.
  ENDMETHOD.                    "h_handle_toolbar
* Méthode pour gérer le fonctionnement des boutons
  METHOD h_handle_usr_comm.
    CASE e_ucomm.
    WHEN 'DESELALL'.   "DESELECT ALL.
    WHEN OTHERS.
    ENDCASE.
    CALL METHOD g_grid_9001->refresh_table_display
    EXCEPTIONS
      finished = 1.
  ENDMETHOD.                    "h_handle_usr_comm
  method handle_data_changed.
*   Event is triggered when data is changed in the output
    TYPES :     BEGIN OF ty_modif,
                  plafond   TYPE char2,
                  fieldname TYPE lvc_s_modi-fieldname,
                  VALUE     TYPE lvc_s_modi-VALUE,
                END OF ty_modif.
    data :
      lw_changed   type lvc_s_modi,
      lw_modif     type ty_modif,
      w_limj(2) type c.
    assign er_data_changed->mt_mod_cells to field-symbol(<lfs_changed_tab>) ."castin
    if <lfs_changed_tab> is assigned.
      loop at <lfs_changed_tab> into lw_changed.
*              call method er_data_changed->modify_cell
*                exporting
*                  i_row_id    = lw_changed-row_id
*                  i_fieldname = lw_changed-fieldname
*                  i_value     = w_limj.
          endloop.
      endif.
  endmethod.                    "handle_data_changed
ENDCLASS.                    "lcl_eventhandler IMPLEMENTATION
DATA : go_event_alv        TYPE REF TO lcl_eventhandler.
*---------------------------------------------------------------------*
*       CLASS lcl_ils IMPLEMENTATION
*---------------------------------------------------------------------*
CLASS  lcl_ils IMPLEMENTATION.
  METHOD on_dblclick.
**    IF e_row > 0.
*    IF e_row > 0 AND l_cvr <> 'KO'.
*
*      READ TABLE lt_report_aff INTO ls_report_out INDEX e_row.
*
*      IF sy-subrc = 0.
*
*        m_pernr = ls_report_out-pernr.
*
*** Début+JFG011015
*        ASSIGN ('e_column') TO <fs_jour>.
*        CHECK <fs_jour> IS ASSIGNED AND <fs_jour>(3) = 'DAY'.
*        CLEAR : wa_jour, m_date.
*        READ TABLE it_jour INTO wa_jour WITH KEY jour = <fs_jour>.
*        IF sy-subrc = 0.
*          m_date = wa_jour-DATE.
*        ENDIF.
*** Fin+JFG011015
*
*        IF m_pernr  IS NOT INITIAL AND
*        m_date   IS NOT INITIAL.
*
*          CLEAR sy-subrc.
*
*          IF it_pointages IS NOT INITIAL.
**            CALL FUNCTION 'GET_WEEK_INFO_BASED_ON_DATE'
**              EXPORTING
**                date   = m_date
**              IMPORTING
**                monday = lv_monday
**                sunday = lv_sunday.
*
**           Check for non-validated status in TVARVC for the current
**           employee number
*            SELECT COUNT(*)
*            FROM catsdb AS a
*            INNER JOIN @it_pointages AS b
*            ON ( a~counter EQ b~counter )
*            INNER JOIN tvarvc AS C
*            ON ( C~name    EQ 'YCTRCATS_STATLOCK'
*            AND   a~status  EQ C~low )
**             WHERE a~workdate BETWEEN @lv_monday AND @lv_sunday
**               AND b~pernr EQ @m_pernr.
*            WHERE b~pernr EQ @m_pernr.
*            IF sy-subrc EQ 0.
***             An error message is displayed to prevent the user from
***             navigating to CAT2 for further modification
**              MESSAGE TEXT-e06 TYPE 'S' DISPLAY LIKE 'E'.
*
**             change the access restriction to CAT2 for an access to CAT3
*              MESSAGE TEXT-w01 TYPE 'I' DISPLAY LIKE 'I'.
*              PERFORM call_cats3 USING m_pernr m_date m_profil.
*
*
**            ELSE.                                             "-KBU002
*            ENDIF.                                             "+KBU002
*          ENDIF.                                              "+KBU002
** End. modif KBU001 ---------------------------------- End. modif KBU001
*
*          IF sy-subrc IS NOT INITIAL                           "+KBU002
*          OR it_pointages IS INITIAL.                          "+KBU002
*
*            IF m_date < gv_lim_beg.                            "+RCH PRISM 8443
*              "pas de possibilité de modifier le pointage
*              PERFORM call_cats3 USING m_pernr m_date m_profil."+RCH PRISM 8443
*            ELSE.                                              "+RCH PRISM 8443
*              PERFORM call_cats USING m_pernr m_date m_profil.
*            ENDIF.                                             "+RCH PRISM 8443
*
*          ENDIF.                                             "+KBU001
**        ENDIF.                                               "+KBU001 "-KBU002
*
**      SET PARAMETER ID 'PER' FIELD m_pernr.
**      SET PARAMETER ID 'CVR' FIELD m_profil.
**      SET PARAMETER ID 'CID' FIELD m_date.
*
*          REFRESH : lt_report_out2, it_pointages2, lt_pernr2 .
*
*          ls_pernr = ls_report_out-pernr.
*          APPEND ls_pernr TO lt_pernr2.
*
*          IF p_visi IS NOT INITIAL.
*            CLEAR : w_visi.
*          ELSE.
*            w_visi = '0'.
*          ENDIF.
*
** Recuperation des heures théoriques/travaillées pour chaque matricule
*          CALL FUNCTION 'ZRFC_Q_HR_LEA_GET_TIME'
*          EXPORTING
*            pernr        = lt_pernr2
*            begda        = p_deb
*            endda        = p_fin
*            p_bukrs      = s_bukrs   "JFG030120
*            p_visi       = w_visi    "JFG030120
*          IMPORTING
*            lea_get_time = lt_report_out2
*            pointages    = it_pointages2
*          TABLES
*            lgart        = s_lgart
*            awart        = s_awart
*            except_qinfo = lt_except_qinfo.
*
*          LOOP AT it_pointages2 ASSIGNING  <fs_pointage> .
*            IF <fs_pointage>-longtext = 'X'.
*              PERFORM f_text USING   <fs_pointage>-counter
*              CHANGING <fs_pointage>-zztext.
*            ELSE.
*              <fs_pointage>-zztext = <fs_pointage>-ltxa1.
*            ENDIF.
*          ENDLOOP.
*
*          DELETE lt_report_out WHERE pernr = ls_report_out-pernr.
*          DELETE it_pointages  WHERE pernr = ls_report_out-pernr.
*
*          APPEND LINES OF lt_report_out2[] TO lt_report_out[].
*          APPEND LINES OF it_pointages2[]  TO it_pointages[].
*
*          SORT lt_report_out BY pernr.
*          SORT it_pointages  BY pernr.
*          PERFORM color_gestion.                               "+KBU003
*
*          IF zaffichage = 'ZH'.   "JFG
*            lt_report_aff[] = lt_report_out.
*            DELETE lt_report_aff WHERE zout NE 'DIF'.
**            PERFORM color_gestion.                            "-KBU003
*            LEAVE TO SCREEN 9001.
*        ELSEIF zaffichage = 'ZS'.   "JFG
*            lt_report_aff[] = lt_report_out.
*            DELETE lt_report_aff WHERE zout NE 'ACT'.
**            PERFORM color_gestion.                            "-KBU003
*            LEAVE TO SCREEN 9001.
*        ELSEIF zaffichage = 'ZT'.   "JFG
*            lt_report_aff[] = lt_report_out.
*            DELETE lt_report_aff WHERE zout NE 'TEO'.
**            PERFORM color_gestion.                            "-KBU003
*            LEAVE TO SCREEN 9001.
*** Début+JFG300120
*        ELSEIF zaffichage = 'ZV'.   "JFG
*            lt_report_aff[] = lt_report_out.
*            DELETE lt_report_aff WHERE zout NE 'PRI'.
**            PERFORM color_gestion.                            "-KBU003
*            LEAVE TO SCREEN 9001.
*** Fin+JFG300120
*          ENDIF.
*
*** Fin+JFG021015
*
*        ENDIF.
*
*      ENDIF.
*
*    ENDIF.
*************************************************************
  ENDMETHOD.                    "on_dblclick
ENDCLASS.                    "lcl_ils IMPLEMENTATION