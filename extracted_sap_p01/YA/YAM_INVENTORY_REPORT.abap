REPORT ZAM_INVENTORY_REPORT.

TABLES: AGR_USERS, ANKA, ANLA, ANLZ, T499S, ZAMBCIF, ZAMROOMBC.

PARAMETERS: P_BUKRS LIKE T001-BUKRS DEFAULT 'UNES'.

SELECT-OPTIONS: P_DATE  FOR ZAMBCIF-EDATE NO-EXTENSION,
                P_INVNR FOR ZAMBCIF-INVNR,
                P_ANLKL FOR ANKA-ANLKL,
                P_STAND FOR T499S-STAND.

SELECTION-SCREEN SKIP.
PARAMETERS: P_DEACT AS CHECKBOX.


TYPE-POOLS: SLIS.


DATA: BEGIN OF T_ITAB OCCURS 0,
        CHK.
        INCLUDE STRUCTURE ZAMBCIF.
DATA:   OLD_STAND LIKE T499S-STAND,
        ANLN1 LIKE ANLA-ANLN1,
        ANLN2 LIKE ANLA-ANLN2,
*        sernr like anla-sernr,
        KOSTL LIKE ANLZ-KOSTL,
      END OF T_ITAB.


DATA: T_RTAB TYPE TABLE OF ZAM_INVREP_STR.
DATA: T_WTAB LIKE T_RTAB.

DATA: BEGIN OF T_FILTER OCCURS 0,
        INDX TYPE I,
      END OF T_FILTER.

DATA: W_BDATE TYPE D,
      W_RTAB LIKE ZAM_INVREP_STR,
      W_SORTSTR(255),
      W_INDEX TYPE I,
      W_QLINE.


INITIALIZATION.
  W_BDATE = SY-DATUM - 90.
  P_DATE-SIGN = 'I'.
  P_DATE-OPTION = 'BT'.
  P_DATE-LOW = W_BDATE.
  P_DATE-HIGH = SY-DATUM.
  APPEND P_DATE.

START-OF-SELECTION.

REFRESH T_ITAB.

CLEAR ZAMBCIF.
SELECT *
      FROM ZAMBCIF
      WHERE BUKRS = P_BUKRS
        AND EDATE IN P_DATE
        AND INVNR IN P_INVNR.
  CHECK ZAMBCIF-ANLKL IN P_ANLKL.
  CHECK ZAMBCIF-CUR_STAND IN P_STAND.

  CLEAR T_ITAB.
  MOVE-CORRESPONDING ZAMBCIF TO T_ITAB.
  CLEAR ANLA.
  SELECT *
        FROM ANLA
        WHERE BUKRS = ZAMBCIF-BUKRS
          AND INVNR = ZAMBCIF-INVNR.
    IF P_DEACT IS INITIAL.
      CHECK ANLA-DEAKT IS INITIAL.
    ENDIF. "p_deakt

    CLEAR ANLZ.
    SELECT *
          FROM ANLZ
          WHERE BUKRS = ZAMBCIF-BUKRS
            AND ANLN1 = ANLA-ANLN1
            AND ANLN2 = ANLA-ANLN2
          ORDER BY PRIMARY KEY.

      CHECK ANLZ-BDATU >= P_DATE-LOW
        AND ANLZ-ADATU <= P_DATE-HIGH.
      T_ITAB-OLD_STAND = ANLZ-STORT.
      T_ITAB-KOSTL = ANLZ-KOSTL.
      T_ITAB-ANLN1 = ANLA-ANLN1.
      T_ITAB-ANLN2 = ANLA-ANLN2.
*      t_itab-sernr = anla-sernr.
      APPEND T_ITAB.
    ENDSELECT. "anlz
  ENDSELECT. "anla
  IF SY-SUBRC <> 0.
    APPEND T_ITAB.
  ENDIF. "sy-subrc
ENDSELECT. "zambcif

END-OF-SELECTION.

CLEAR T_ITAB.
SORT T_ITAB.
LOOP AT T_ITAB.
*  write: /
*         t_itab-chk as checkbox,
*         t_itab-anlkl,
*         t_itab-invnr,
*         t_itab-atext,
*         t_itab-cur_stand,
*         t_itab-old_stand.
  CLEAR W_RTAB.
  MOVE-CORRESPONDING T_ITAB TO W_RTAB.
  W_RTAB-IVDAT = T_ITAB-EDATE.
  APPEND W_RTAB TO T_RTAB.
ENDLOOP. "t_itab

*t_rtab[] = t_itab[].

CALL SCREEN 100.

***
*----------------------------------------------------------------*
* ABAP List Viewer output
*----------------------------------------------------------------*
CLASS EVENT_RCV DEFINITION DEFERRED.

DATA: OK_CODE LIKE SY-UCOMM,
      G_CONTAINER TYPE SCRFNAME VALUE 'BCALV_GRID_DEMO_0100_CONT1',
      W_ALV_GRID TYPE REF TO CL_GUI_ALV_GRID,
      G_FCAT TYPE LVC_T_FCAT,
      W_FCAT TYPE LINE OF LVC_T_FCAT,
      G_CUSTOM_CONTAINER TYPE REF TO CL_GUI_CUSTOM_CONTAINER,
      GS_LAYOUT TYPE LVC_S_LAYO,
      TC_INDEX_ROWS TYPE LVC_T_ROW,
      TC_ROW_NO TYPE LVC_T_ROID,
      W_CIROWS TYPE LINE OF LVC_T_ROW,
      TC_SORT TYPE LVC_T_SORT,
      W_CSORT TYPE LINE OF LVC_T_SORT,
      TC_FILTERED TYPE LVC_T_FIDX,
      W_GRIDTITLE TYPE LVC_TITLE,
      EVENT_RECEIVER TYPE REF TO EVENT_RCV.

*data: begin of tc_index_rows.
*        include structure lvc_t_row.
*data: end of tc_index_rows.

*data: begin of tc_row_no.
*        include structure lvc_t_roid.
*data: end of tc_row_no.


CLASS EVENT_RCV DEFINITION.
  PUBLIC SECTION.
  PRIVATE SECTION.
ENDCLASS.



*&---------------------------------------------------------------------

*&      Module  PBO  OUTPUT
*&---------------------------------------------------------------------

*       text
*----------------------------------------------------------------------

MODULE PBO OUTPUT.
FIELD-SYMBOLS: <LS_FCAT> TYPE LVC_S_FCAT.

SET TITLEBAR 'Z0001'.

CLEAR AGR_USERS.
SELECT SINGLE *
      FROM AGR_USERS
      WHERE AGR_NAME = 'Y_FI_ASSET_MANAGEMENT_SPEC'
        AND UNAME = SY-UNAME
        AND FROM_DAT <= SY-DATUM
        AND TO_DAT >= SY-DATUM.

IF SY-SUBRC = 0.
  SET PF-STATUS 'ZS100'.
 ELSE.
   SET PF-STATUS 'ZS100' EXCLUDING 'CRNA'.
ENDIF. "sy-subrc

IF G_CUSTOM_CONTAINER IS INITIAL.
  CREATE OBJECT G_CUSTOM_CONTAINER
        EXPORTING CONTAINER_NAME = G_CONTAINER.
  CREATE OBJECT W_ALV_GRID
        EXPORTING I_PARENT = G_CUSTOM_CONTAINER.

  CALL FUNCTION 'LVC_FIELDCATALOG_MERGE'
   EXPORTING
     I_STRUCTURE_NAME             = 'ZAM_INVREP_STR'
    CHANGING
      CT_FIELDCAT                  = G_FCAT[]
   EXCEPTIONS
     INCONSISTENT_INTERFACE       = 1
     PROGRAM_ERROR                = 2
     OTHERS                       = 3.
  IF SY-SUBRC <> 0.
* MESSAGE ID SY-MSGID TYPE SY-MSGTY NUMBER SY-MSGNO
*         WITH SY-MSGV1 SY-MSGV2 SY-MSGV3 SY-MSGV4.
  ENDIF.

  LOOP AT G_FCAT INTO W_FCAT.
    CASE W_FCAT-FIELDNAME.
      WHEN 'BUKRS'.
        DELETE TABLE G_FCAT FROM W_FCAT.
      WHEN 'ANLN2'.
        DELETE TABLE G_FCAT FROM W_FCAT.
      WHEN 'CUR_STAND'.
        W_FCAT-SCRTEXT_S = 'CurrLocat.'.
        W_FCAT-SCRTEXT_M = 'Current Location'.
        W_FCAT-SCRTEXT_L = 'Current Location'.
        MODIFY G_FCAT FROM W_FCAT.
      WHEN 'OLD_STAND'.
        W_FCAT-SCRTEXT_S = 'PrevLocat.'.
        W_FCAT-SCRTEXT_M = 'Previous Location'.
        W_FCAT-SCRTEXT_L = 'Previous Location'.
        MODIFY G_FCAT FROM W_FCAT.
      WHEN 'KOSTL'.
        W_FCAT-SCRTEXT_S = 'SectorCode'.
        W_FCAT-SCRTEXT_M = 'Sector Code'.
        W_FCAT-SCRTEXT_L = 'Sector Code'.
        MODIFY G_FCAT FROM W_FCAT.
    ENDCASE.
  ENDLOOP.

  GS_LAYOUT-ZEBRA = 'X'.
  GS_LAYOUT-NO_ROWMARK = ' '.
  GS_LAYOUT-SEL_MODE = 'A'.

  W_GRIDTITLE = 'Inventory Results'.
  CALL METHOD W_ALV_GRID->SET_GRIDTITLE
      EXPORTING
        I_GRIDTITLE = W_GRIDTITLE.

  CALL METHOD W_ALV_GRID->SET_TABLE_FOR_FIRST_DISPLAY
      EXPORTING
        I_STRUCTURE_NAME = 'ZAM_INVREP_STR2'
        IS_LAYOUT        = GS_LAYOUT
*        i_default        = ' '
      CHANGING
        IT_OUTTAB        = T_RTAB
        IT_FIELDCATALOG  = G_FCAT.

  CREATE OBJECT EVENT_RECEIVER.
ENDIF. "g_c_c
ENDMODULE.                 " PBO  OUTPUT


*&---------------------------------------------------------------------

*&      Module  PAI  INPUT
*&---------------------------------------------------------------------

*       text
*----------------------------------------------------------------------

MODULE PAI INPUT.
  " to react on oi_custom_events:
  CALL METHOD CL_GUI_CFW=>DISPATCH.

  REFRESH: TC_INDEX_ROWS, TC_ROW_NO.
  CALL METHOD W_ALV_GRID->GET_SELECTED_ROWS
    IMPORTING
      ET_INDEX_ROWS = TC_INDEX_ROWS
      ET_ROW_NO     = TC_ROW_NO.

*  call method w_alv_grid->get_row_from_id
*      exporting is_row_info = tc_row_no
*      importing e_row       = w_crow.


****get sort
  CALL METHOD W_ALV_GRID->GET_SORT_CRITERIA
      IMPORTING  ET_SORT = TC_SORT.

  CLEAR: W_CSORT, W_SORTSTR.
  SORT TC_SORT BY SPOS.
*  loop at tc_sort into w_csort.
*    concatenate w_sortstr w_csort-fieldname into w_sortstr
*               separated by space.
*    if w_csort-up = 'X'.
*      concatenate w_sortstr 'ASCENDING' into w_sortstr
*                 separated by space.
*     else.
*       concatenate w_sortstr 'DESCENDING' into w_sortstr
*                  separated by space.
*    endif. "w_csort-down
*  endloop. "tc_sort
*  sort t_rtab by (w_sortstr).
  READ TABLE TC_SORT INDEX 1 INTO W_CSORT.
  IF W_CSORT-UP = 'X'.
    SORT T_RTAB BY (W_CSORT-FIELDNAME).
   ELSE.
     SORT T_RTAB BY (W_CSORT-FIELDNAME) DESCENDING.
  ENDIF. "w_csort-up

*****get filter
*  call method w_alv_grid->get_filtered_entries
*      importing
*        et_filtered_entries = tc_filtered.
*
*  refresh t_filter.
*  loop at tc_filtered into w_index.
*    t_filter-indx = w_index.
*    append t_filter.
*  endloop. "tc_fitered
**create temporary table for work
**delete filtered records from temp. table
*  refresh t_wtab.
*  loop at t_rtab into w_rtab.
*    read table t_filter with key indx = sy-tabix.
*    if sy-subrc <> 0.
*      append w_rtab to t_wtab.
*    endif. "sy-subrc
*  endloop. "t_rtab

  CASE OK_CODE.
    WHEN 'BACK' OR 'EXIT' OR 'CANC'.
      PERFORM PROG_EXIT.
    WHEN 'CRNA'.
    WHEN 'TRAN'.
    WHEN 'RTOL'.
      LOOP AT T_RTAB INTO W_RTAB.
*        zambcif
      ENDLOOP. "t_rtab
    WHEN OTHERS.
  ENDCASE.
  CLEAR OK_CODE.
*renew main data table after processing
*  refresh t_rtab.
*  t_rtab[] = t_wtab[].
ENDMODULE.                 " PAI  INPUT


FORM PROG_EXIT.
  CALL METHOD W_ALV_GRID->FREE.
  CALL METHOD G_CUSTOM_CONTAINER->FREE.
  CALL METHOD CL_GUI_CFW=>FLUSH.

  CLEAR G_CUSTOM_CONTAINER.
  CLEAR W_ALV_GRID.

  SET SCREEN 0.
  LEAVE SCREEN.
ENDFORM. "prog_exit