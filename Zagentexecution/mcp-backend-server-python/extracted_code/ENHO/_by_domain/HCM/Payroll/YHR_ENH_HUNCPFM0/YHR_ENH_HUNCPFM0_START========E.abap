ENHANCEMENT 1  .
  DATA yyhr_huncpfm0_addon TYPE REF TO ycl_hr_huncpfm0_addon.
  IF ycl_hr_huncpfm0_addon=>mv_skip_addon = abap_false.
    yyhr_huncpfm0_addon = ycl_hr_huncpfm0_addon=>get_instance( iv_begda = pn-begda
                                                               iv_endda = pn-endda ).
    gt_egsg = yyhr_huncpfm0_addon->get_excluded_emp_group( ).
  ENDIF.
ENDENHANCEMENT.
