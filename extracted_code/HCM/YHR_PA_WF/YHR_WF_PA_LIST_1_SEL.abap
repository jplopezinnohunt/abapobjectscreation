*&---------------------------------------------------------------------*
*&  Include           YHR_WF_PA_LIST_1_SEL
*&---------------------------------------------------------------------*

SELECTION-SCREEN BEGIN OF BLOCK b01 WITH FRAME TITLE TEXT-b01.
PARAMETERS p_spa RADIOBUTTON GROUP r001 DEFAULT 'X' USER-COMMAND rad.
PARAMETERS p_lwop RADIOBUTTON GROUP r001.
PARAMETERS p_s1 RADIOBUTTON GROUP r001.
PARAMETERS p_int RADIOBUTTON GROUP r001.
SELECTION-SCREEN BEGIN OF BLOCK b11 WITH FRAME TITLE TEXT-b11.
PARAMETERS p_i1 AS CHECKBOX DEFAULT 'X' MODIF ID int.
PARAMETERS p_eval AS CHECKBOX MODIF ID int.
SELECTION-SCREEN END OF BLOCK b11.
SELECTION-SCREEN END OF BLOCK b01.

SELECTION-SCREEN BEGIN OF BLOCK b03 WITH FRAME TITLE TEXT-b03.
SELECT-OPTIONS s_wf_beg FOR yshr_wf_report_2-wf_begda NO-EXTENSION.
SELECT-OPTIONS s_wf_end FOR yshr_wf_report_2-wf_endda NO-EXTENSION.
SELECT-OPTIONS s_wf_st FOR yshr_wf_report_2-wi_stat NO INTERVALS.
SELECT-OPTIONS s_wf_dur FOR gv_duration NO-EXTENSION.
SELECTION-SCREEN END OF BLOCK b03.

SELECTION-SCREEN BEGIN OF BLOCK b02 WITH FRAME TITLE TEXT-b02.
SELECT-OPTIONS s_pernr FOR yshr_wf_report_2-pernr MATCHCODE OBJECT prem.
SELECT-OPTIONS s_massn FOR yshr_wf_report_2-massn.
SELECT-OPTIONS s_massg FOR yshr_wf_report_2-massg.
SELECT-OPTIONS s_duty FOR yshr_wf_report_2-dstat.
SELECT-OPTIONS s_begda FOR yshr_wf_report_2-begda.
SELECT-OPTIONS s_ctedt FOR yshr_wf_report_2-ctedt.
SELECT-OPTIONS s_sector FOR yshr_wf_report_2-sector.
SELECT-OPTIONS s_orgeh FOR yshr_wf_report_2-orgeh.
SELECTION-SCREEN END OF BLOCK b02.

PARAMETERS p_layout LIKE disvariant-variant.


INITIALIZATION.
  "Get generic status
  gt_generic_status = ycl_hrwf_report_utilities=>get_wf_generic_status( ).
  "Get list of sectors
  SELECT sect, sect_txt FROM t9sct_t WHERE sprsl = @sy-langu INTO TABLE @gt_sector.

AT SELECTION-SCREEN ON VALUE-REQUEST FOR s_wf_st-low.
  ycl_hrwf_report_utilities=>value_request_popup( EXPORTING iv_retfield = 'STATUS'
                                                            iv_repid = sy-repid
                                                            iv_dynprofield = 'S_WF_ST-LOW'
                                                            it_value_tab = gt_generic_status ).

AT SELECTION-SCREEN ON VALUE-REQUEST FOR s_wf_st-high.
  ycl_hrwf_report_utilities=>value_request_popup( EXPORTING iv_retfield = 'STATUS'
                                                            iv_repid = sy-repid
                                                            iv_dynprofield = 'S_WF_ST-HIGH'
                                                            it_value_tab = gt_generic_status ).

AT SELECTION-SCREEN ON VALUE-REQUEST FOR p_layout.
  gs_key-report = sy-repid.
  gs_layout = cl_salv_layout_service=>f4_layouts( s_key    = gs_key
                                                  restrict = if_salv_c_layout=>restrict_none ).
  p_layout = gs_layout-layout.

AT SELECTION-SCREEN ON VALUE-REQUEST FOR s_orgeh-low.
  ycl_hr_utilities=>get_object_from_search_help( EXPORTING iv_otype = 'O'
                                                 IMPORTING ev_objid = s_orgeh-low ).

AT SELECTION-SCREEN ON VALUE-REQUEST FOR s_orgeh-high.
  ycl_hr_utilities=>get_object_from_search_help( EXPORTING iv_otype = 'O'
                                                 IMPORTING ev_objid = s_orgeh-high ).

AT SELECTION-SCREEN ON VALUE-REQUEST FOR s_sector-low.
  ycl_hrwf_report_utilities=>value_request_popup( EXPORTING iv_retfield = 'SECT'
                                                            iv_repid = sy-repid
                                                            iv_dynprofield = 'S_SECTOR-LOW'
                                                            it_value_tab = gt_sector ).

AT SELECTION-SCREEN ON VALUE-REQUEST FOR s_sector-high.
  ycl_hrwf_report_utilities=>value_request_popup( EXPORTING iv_retfield = 'SECT'
                                                            iv_repid = sy-repid
                                                            iv_dynprofield = 'S_SECTOR-HIGH'
                                                            it_value_tab = gt_sector ).

AT SELECTION-SCREEN ON BLOCK b01.
  IF p_int = abap_true AND p_i1 = abap_false AND p_eval = abap_false.
    MESSAGE e070(ywf_om).
  ENDIF.
  IF p_int = abap_false AND p_i1 = abap_false AND p_eval = abap_false.
    p_i1 = abap_true.
  ENDIF.

AT SELECTION-SCREEN OUTPUT.
  LOOP AT SCREEN.
    IF screen-group1 = 'INT'.
      IF p_int = abap_true.
        screen-active = 1.
      ELSE.
        screen-active = 0.
      ENDIF.
      MODIFY SCREEN.
    ENDIF.
  ENDLOOP.