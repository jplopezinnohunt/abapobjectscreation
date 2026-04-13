ENHANCEMENT 2  .

  DATA yylo_br_posting TYPE REF TO ycl_hr_rpcipp00_extend.

  yylo_br_posting = ycl_hr_rpcipp00_extend=>get_instance( ).
  "Store runid well posted
  IF status = g_set_end_status_noidoc.
    READ TABLE reject_mess_tab TRANSPORTING NO FIELDS WITH KEY evtyp = l_evtyp
                                                               runid = l_runid.
    IF sy-subrc <> 0.
      yylo_br_posting->put_posted_runid( iv_type = l_evtyp iv_runid = l_runid ).
    ENDIF.
  ENDIF.

ENDENHANCEMENT.
ENHANCEMENT 3  .

  "Do BR posting in FM from payroll runid
  DATA yylo_br_posting TYPE REF TO ycl_hr_rpcipp00_extend.

  yylo_br_posting = ycl_hr_rpcipp00_extend=>get_instance( ).

  IF p_rev = abap_false.
    yylo_br_posting->submit_br_posting_in_fm( iv_test = p_check ).
  ENDIF.

ENDENHANCEMENT.