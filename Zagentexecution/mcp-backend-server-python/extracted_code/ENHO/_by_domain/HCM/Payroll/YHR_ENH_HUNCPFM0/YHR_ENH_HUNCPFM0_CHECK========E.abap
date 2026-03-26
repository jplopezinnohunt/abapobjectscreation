ENHANCEMENT 1  .
  DATA yyhr_huncpfm0_addon TYPE REF TO ycl_hr_huncpfm0_addon.
  IF ycl_hr_huncpfm0_addon=>mv_skip_addon = abap_false.
    yyhr_huncpfm0_addon = ycl_hr_huncpfm0_addon=>get_instance( iv_begda = pn-begda
                                                               iv_endda = pn-endda ).
    IF yyhr_huncpfm0_addon->reject_pernr( iv_pernr = pernr-pernr
                                          it_p0001 = p0001[]
                                          it_p0961 = p0961[] ) = abap_true.
      REJECT.
    ENDIF.
  ENDIF.
ENDENHANCEMENT.
