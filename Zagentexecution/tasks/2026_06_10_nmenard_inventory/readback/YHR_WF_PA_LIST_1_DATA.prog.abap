*&---------------------------------------------------------------------*
*&  Include           YHR_WF_PA_LIST_1_DATA
*&---------------------------------------------------------------------*


TABLES: yshr_wf_report_2.

TYPE-POOLS: ypawf.

TYPES: BEGIN OF ty_gen_st,
         status TYPE sww_wistat,
       END OF ty_gen_st.
TYPES: BEGIN OF ty_sect,
         sect     TYPE t9sct_t-sect,
         sect_txt TYPE t9sct_t-sect_txt,
       END OF ty_sect.
DATA gt_sector TYPE TABLE OF ty_sect.
DATA gt_generic_status TYPE TABLE OF ty_gen_st.
DATA gv_duration TYPE i.
DATA gs_layout TYPE salv_s_layout_info.
DATA gs_key    TYPE salv_s_layout_key.

DATA gv_actty TYPE ze_actty.

DATA   go_hrwf_report TYPE REF TO ycl_hrwf_report_2_bl.