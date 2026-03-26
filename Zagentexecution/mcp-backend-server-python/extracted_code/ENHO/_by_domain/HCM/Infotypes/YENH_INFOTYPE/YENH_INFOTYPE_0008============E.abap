ENHANCEMENT 1  .
  DATA lo_it0008_buffer TYPE REF TO ycl_hrpa_infotype_0008_buffer.
  lo_it0008_buffer = ycl_hrpa_infotype_0008_buffer=>get_instance( ).
  lo_it0008_buffer->set_buffer( iv_pernr = pernr
                                iv_begda = date
                                iv_endda = date
                                iv_trfar = trfar
                                iv_trfgb = trfgb
                                iv_trfgr = trfgr
                                iv_trfst = trfst
                                iv_cpind = cpind ).
ENDENHANCEMENT.
