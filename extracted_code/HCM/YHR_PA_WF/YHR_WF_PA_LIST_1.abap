*&---------------------------------------------------------------------*
*& Report YHR_WF_PA_LIST_1
*&---------------------------------------------------------------------*
*&
*&---------------------------------------------------------------------*
REPORT yhr_wf_pa_list_1.


INCLUDE yhr_wf_pa_list_1_data.
INCLUDE yhr_wf_pa_list_1_sel.

START-OF-SELECTION.

  "Instance class
  go_hrwf_report = NEW ycl_hrwf_report_2_bl( ).

  go_hrwf_report->set_selection_values( iv_selname = 'P_SPA' iv_kind = 'P' iv_value = p_spa ).
  go_hrwf_report->set_selection_values( iv_selname = 'P_LWOP' iv_kind = 'P' iv_value = p_lwop ).
  go_hrwf_report->set_selection_values( iv_selname = 'P_S1' iv_kind = 'P' iv_value = p_s1 ).
  go_hrwf_report->set_selection_values( iv_selname = 'P_INT' iv_kind = 'P' iv_value = p_int ).
  go_hrwf_report->set_selection_values( iv_selname = 'P_I1' iv_kind = 'P' iv_value = p_i1 ).
  go_hrwf_report->set_selection_values( iv_selname = 'P_EVAL' iv_kind = 'P' iv_value = p_eval ).

  go_hrwf_report->set_selection_values( iv_selname = 'S_WF_BEG' iv_kind = 'S' it_value = s_wf_beg[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_WF_END' iv_kind = 'S' it_value = s_wf_end[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_WF_ST' iv_kind = 'S' it_value = s_wf_st[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_WF_DUR' iv_kind = 'S' it_value = s_wf_dur[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_PERNR' iv_kind = 'S' it_value = s_pernr[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_MASSN' iv_kind = 'S' it_value = s_massn[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_MASSG' iv_kind = 'S' it_value = s_massg[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_BEGDA' iv_kind = 'S' it_value = s_begda[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_CTEDT' iv_kind = 'S' it_value = s_ctedt[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_DUTY' iv_kind = 'S' it_value = s_duty[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_SECTOR' iv_kind = 'S' it_value = s_sector[] ).
  go_hrwf_report->set_selection_values( iv_selname = 'S_ORGEH' iv_kind = 'S' it_value = s_orgeh[] ).


  go_hrwf_report->get_data( ).
  go_hrwf_report->mv_repid = sy-repid.
  go_hrwf_report->init_alv( ).
  go_hrwf_report->set_alv_status( 'SALV_TABLE_STANDARD' ).
  go_hrwf_report->mv_layout = p_layout.
  go_hrwf_report->display_alv( ).