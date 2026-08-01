*&---------------------------------------------------------------------*
*& Report YFI_UPDATE_SALEFORCE_ID
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT YFI_CUSTOMER_UPDATE_SF_ID.

TYPES: BEGIN OF TY_SAP_SF_ID,
         KUNNR_C(10) TYPE C,
         SF_ID       TYPE BAHNS,
       END OF TY_SAP_SF_ID.

TYPES: BEGIN OF TY_RESULT,
         KUNNR_C(10) TYPE C,
         MESS_TYPE   TYPE SY-MSGTY,
         MESSAGE     TYPE STRING,
       END OF TY_RESULT.

DATA GT_SAP_SF_ID TYPE TABLE OF TY_SAP_SF_ID.
DATA GS_SAP_SF_ID TYPE TY_SAP_SF_ID.
DATA GT_DATA_FILE TYPE TABLE OF STRING.
DATA GX_ERROR TYPE REF TO YCX_FILE_ACCESS.
DATA GV_MESSAGE TYPE STRING.
DATA GV_SUBRC TYPE SY-SUBRC.
DATA GT_RESULT TYPE TABLE OF TY_RESULT.
DATA GS_RESULT TYPE TY_RESULT.
DATA GV_KUNNR TYPE KNA1-KUNNR.
DATA GS_MAIN_DATA TYPE YSFI_CUSTOMER_MAIN_1.
DATA GS_MAIN_UPD TYPE YSFI_CUSTOMER_MAIN_1_UPD.
DATA GO_ALV TYPE REF TO YCL_ALV.
DATA GT_MESSAGE TYPE BAPIRET2_T.
DATA GV_IS_OK TYPE XFELD.

SELECTION-SCREEN BEGIN OF BLOCK BUP WITH FRAME TITLE TEXT-BUP.
PARAMETERS P_EXCEL RADIOBUTTON GROUP RUP1 DEFAULT 'X' USER-COMMAND RUP.
PARAMETERS P_TEXT RADIOBUTTON GROUP RUP1.
SELECTION-SCREEN BEGIN OF BLOCK BSE WITH FRAME TITLE TEXT-BSE.
PARAMETERS P_TAB AS CHECKBOX MODIF ID RTX USER-COMMAND RTX.
PARAMETERS P_SEPA(1) TYPE C MODIF ID RTX.
SELECTION-SCREEN END OF BLOCK BSE.
PARAMETERS P_FILE TYPE STRING LOWER CASE.
PARAMETERS P_HEADER TYPE NUMC1 DEFAULT 0.
SELECTION-SCREEN END OF BLOCK BUP.
SELECTION-SCREEN BEGIN OF BLOCK B01 WITH FRAME TITLE TEXT-B01.
PARAMETERS P_TEST AS CHECKBOX DEFAULT 'X'.
SELECTION-SCREEN END OF BLOCK B01.

AT SELECTION-SCREEN ON P_FILE.
  CHECK P_FILE IS NOT INITIAL.
  IF CL_GUI_FRONTEND_SERVICES=>FILE_EXIST( EXPORTING FILE = P_FILE ) = ABAP_FALSE.
    MESSAGE 'File doesn''t exist' TYPE 'E'.
  ENDIF.

AT SELECTION-SCREEN OUTPUT.
  LOOP AT SCREEN.
    CASE SCREEN-GROUP1.
      WHEN 'RTX'.
        IF P_TEXT = ABAP_TRUE.
          SCREEN-ACTIVE = 1.
        ELSE.
          SCREEN-ACTIVE = 0.
        ENDIF.
        IF SCREEN-NAME = 'P_SEPA'.
          IF P_TAB = ABAP_TRUE.
            CLEAR P_SEPA.
            SCREEN-INPUT = 0.
          ELSE.
            SCREEN-INPUT = 1.
          ENDIF.
        ENDIF.
        MODIFY SCREEN.
    ENDCASE.
  ENDLOOP.

AT SELECTION-SCREEN ON VALUE-REQUEST FOR P_FILE.
  DATA: LT_FILE TYPE FILETABLE, LV_RC TYPE I.
  CL_GUI_FRONTEND_SERVICES=>FILE_OPEN_DIALOG( CHANGING FILE_TABLE =  LT_FILE
                                                       RC = LV_RC
                                              EXCEPTIONS FILE_OPEN_DIALOG_FAILED = 1
                                                         CNTL_ERROR              = 2
                                                         ERROR_NO_GUI            = 3
                                                         NOT_SUPPORTED_BY_GUI    = 4
                                                         OTHERS                  = 5 ).
  IF SY-SUBRC = 0 AND LV_RC = 1.
    READ TABLE LT_FILE INTO P_FILE INDEX 1.
  ENDIF.

START-OF-SELECTION.

  PERFORM F_UPLOAD_FILE USING GV_SUBRC.
  CHECK GV_SUBRC = 0.

  LOOP AT GT_SAP_SF_ID INTO GS_SAP_SF_ID.
    "Check customer SAP id
    IF GS_SAP_SF_ID-KUNNR_C CN '0123456789 '.
      GS_RESULT-KUNNR_C = GS_SAP_SF_ID-KUNNR_C.
      GS_RESULT-MESS_TYPE = 'E'.
      GS_RESULT-MESSAGE = 'SAP id not conform'.
      APPEND GS_RESULT TO GT_RESULT.
      CONTINUE.
    ENDIF.
    DO 10 TIMES.
      IF GS_SAP_SF_ID-KUNNR_C(1) = SPACE.
        SHIFT GS_SAP_SF_ID-KUNNR_C BY 1 PLACES LEFT.
      ELSE.
        EXIT.
      ENDIF.
    ENDDO.
    CLEAR GV_KUNNR.
    CALL FUNCTION 'CONVERSION_EXIT_ALPHA_INPUT'
      EXPORTING
        INPUT  = GS_SAP_SF_ID-KUNNR_C
      IMPORTING
        OUTPUT = GV_KUNNR.
    "Check SAP customer id existence
    SELECT SINGLE * FROM KNA1 WHERE KUNNR = @GV_KUNNR INTO @DATA(LS_KNA1).
    IF SY-SUBRC <> 0.
      GS_RESULT-KUNNR_C = GS_SAP_SF_ID-KUNNR_C.
      GS_RESULT-MESS_TYPE = 'E'.
      GS_RESULT-MESSAGE = |Customer { GV_KUNNR } doesn't exist|.
      APPEND gs_result TO gt_result.
      CONTINUE.
    ENDIF.
    "Update SalesForce id
    CLEAR: gs_main_data, gs_main_upd, gt_message.
    gs_main_data-kunnr = gv_kunnr.
    gs_main_data-bahns = gs_sap_sf_id-sf_id.
    gs_main_upd-bahns = abap_true.
    ycl_fi_customer_bl=>update_customer( EXPORTING is_main = gs_main_data
                                                   is_main_upd = gs_main_upd
                                                   iv_test = p_test
                                         IMPORTING  ev_is_ok = gv_is_ok
                                                    et_message = gt_message ).
    IF gv_is_ok = abap_true.
      gs_result-kunnr_c = gv_kunnr.
      gs_result-mess_type = 'I'.
      gs_result-message = 'CUSTOMER UPDATED'.
      APPEND gs_result TO gt_result.
    ELSE.
      LOOP AT gt_message INTO DATA(ls_message).
        gs_result-kunnr_c = gv_kunnr.
        gs_result-mess_type = ls_message-type.
        gs_result-message = ls_message-message.
        APPEND gs_result TO gt_result.
      ENDLOOP.
    ENDIF.
  ENDLOOP.

  "Display messages
  go_alv = NEW ycl_alv( ).
  go_alv->yif_alv_display~init_alv( CHANGING it_table = gt_result ).
  go_alv->yif_alv_display~set_main_functions( iv_report = sy-repid ).
  go_alv->yif_alv_display~set_col_text( iv_field = 'KUNNR_C' iv_text = 'CUSTOMER ID' ).
  go_alv->yif_alv_display~set_col_text( iv_field = 'MESSAGE' iv_text = 'MESSAGE' ).
  go_alv->yif_alv_display~display_alv( ).


*&---------------------------------------------------------------------*
*&      Form  F_UPLOAD_FILE
*&---------------------------------------------------------------------*
FORM f_upload_file USING pv_subrc TYPE sy-subrc.

  DATA lv_file TYPE localfile.
  DATA lv_dummy TYPE c.

  CASE abap_true.
    WHEN p_excel.
      lv_file = p_file.
      TRY.
          ycl_bc_excel_tool=>upload_excel_worksheet_lc( EXPORTING iv_filename = lv_file
                                                                  iv_header = p_header
                                                                  iv_remove_filters = abap_true
                                                        IMPORTING et_tab = gt_sap_sf_id ).
        CATCH ycx_file_access INTO gx_error.
          gv_message = gx_error->get_text( ).
          pv_subrc = 1.
          MESSAGE gv_message TYPE 'I'.
      ENDTRY.
    WHEN p_text.
      IF p_tab = abap_true.
        cl_gui_frontend_services=>gui_upload( EXPORTING filename = p_file
                                                        filetype = 'ASC'
                                                        has_field_separator = abap_true
                                              CHANGING data_tab = gt_sap_sf_id
                                              EXCEPTIONS OTHERS = 1 ).
      ELSE.
        cl_gui_frontend_services=>gui_upload( EXPORTING filename = p_file
                                                        filetype = 'ASC'
                                              CHANGING data_tab = gt_data_file
                                              EXCEPTIONS OTHERS = 1 ).
      ENDIF.
      IF sy-subrc <> 0.
        pv_subrc = 1.
        MESSAGE 'UNABLE TO OPEN FILE' TYPE 'I'.
      ELSE.
        IF p_header IS NOT INITIAL.
          DELETE gt_data_file FROM 1 TO p_header.
          DELETE gt_sap_sf_id FROM 1 TO p_header.
        ENDIF.
        IF p_tab = abap_false.
          IF p_sepa IS NOT INITIAL.
            LOOP AT gt_data_file INTO DATA(ls_data_file).
              CLEAR gs_sap_sf_id.
              SPLIT ls_data_file AT p_sepa INTO gs_sap_sf_id-kunnr_c gs_sap_sf_id-sf_id lv_dummy.
              APPEND gs_sap_sf_id TO gt_sap_sf_id.
            ENDLOOP.
          ELSE.
            gt_sap_sf_id = gt_data_file.
          ENDIF.
        ENDIF.
      ENDIF.

  ENDCASE.

ENDFORM.