METHOD get_status_text.                                     "#EC NEEDED

* code moved to CL_HCMFAB_FB_TCAL_SETTINGS

*  DATA: text_tab    TYPE TABLE OF textpool,
*        ls_text_row TYPE textpool.
*  FIELD-SYMBOLS: <wa_attributes> TYPE attabs_attributes_struc.
*
** Read status texts from the Program
*  READ TEXTPOOL 'SAPLPT_ARQ_REQUEST_UIA' INTO text_tab LANGUAGE sy-langu.
*
*  CASE iv_status.
*    WHEN cl_pt_req_const=>c_reqstat_deleted OR cl_pt_req_const=>c_reqstat_withdrawn.
*      READ TABLE text_tab WITH KEY key = 'S03' INTO ls_text_row. "Canceled
*    WHEN cl_pt_req_const=>c_reqstat_sent.
*      READ TABLE text_tab WITH KEY key = 'S04' INTO ls_text_row. "Sent
*    WHEN cl_pt_req_const=>c_reqstat_approved OR cl_pt_req_const=>c_reqstat_posted.
*      READ TABLE it_attabs_attributes WITH KEY subty = iv_subtype ASSIGNING <wa_attributes>.
*      IF sy-subrc EQ 0 AND ( <wa_attributes>-approval_process = cl_pt_req_const=>c_process_withwf_withapp
*                          OR <wa_attributes>-approval_process = cl_pt_req_const=>c_process_nowf_withapp ).
*        READ TABLE text_tab WITH KEY key = 'S05' INTO ls_text_row. "Approved
*      ELSE.
*        READ TABLE text_tab WITH KEY key = 'S08' INTO ls_text_row. "Informed
*      ENDIF.
*    WHEN cl_pt_req_const=>c_reqstat_rejected.
*      READ TABLE text_tab WITH KEY key = 'S06' INTO ls_text_row. "Rejected
*    WHEN OTHERS.
*  ENDCASE.
*  ev_status_text = ls_text_row-entry.
ENDMETHOD.
