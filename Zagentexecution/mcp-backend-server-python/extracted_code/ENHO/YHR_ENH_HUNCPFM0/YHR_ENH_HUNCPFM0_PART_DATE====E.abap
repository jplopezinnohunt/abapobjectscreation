ENHANCEMENT 1  .
  DATA yyhr_huncpfm0_addon TYPE REF TO ycl_hr_huncpfm0_addon.
  IF ycl_hr_huncpfm0_addon=>mv_skip_addon = abap_false.
    yyhr_huncpfm0_addon = ycl_hr_huncpfm0_addon=>get_instance( iv_begda = pn-begda
                                                               iv_endda = pn-endda ).
    gv_pfped = yyhr_huncpfm0_addon->get_participation_date( iv_date = l_fpbeg
                                                            iv_datar = l_pfped
                                                            it_p0041 = gt_p0041
                                                            it_p0000 = p0000[]
                                                            it_p0001 = p0001[]
                                                            it_p0961 = p0961[] ).
    EXIT.
  ENDIF.
ENDENHANCEMENT.
